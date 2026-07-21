"""
G5 evidence-ops bug-hunt regression tests.

Covers four confirmed defects:

1. Circuit breaker non-functional — a raising source never persists a FAILED
   run record, so _consecutive_failures() always returns 0 and the breaker
   never opens (app/monitor.py).
2. Retention/append inode race — append_run() must land the record in the file
   readers see even when a retention rewrite swapped the inode out mid-append
   (app/source_runs.py _locked_append_line).
3. Retention json.loads unguarded — a single malformed JSONL line must not
   abort compaction (app/retention.py).
4. Hash-collision detection inert — _check_hash_collision must compare against
   other sources' stored content hashes from the run trail, not a content_hash
   key that sources.json never carries (app/source_intake.py).

All tests are hermetic: no live network, run trail redirected to tmp_path.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── module guard: tests must never mutate LIVE product data ─────────────────
@pytest.fixture(autouse=True)
def live_data_untouched(tmp_path, monkeypatch):
    """Assert this module leaves product/regradar/data byte-identical.

    monitor_all_sources() is called from several tests here WITHOUT patching
    the ops-state files, so the suite rewrote the real data/deadman_state.json
    on every run (its md5 changed run to run). That is live product data, and
    the same code path fires the founder Telegram alert on the degraded->OK
    transition edge — a test run must never be able to send that.

    Redirect the ops state into tmp_path (same convention as the neighbouring
    tests/test_monitor_circuit.py::_isolate_breaker), then prove it worked by
    comparing the live files byte-for-byte around every test.
    """
    import app.monitor as monitor
    import app.source_runs as sr

    live = [
        monitor._DEADMAN_STATE_FILE,
        monitor._SEAL_DEADMAN_STATE_FILE,
        monitor._CIRCUIT_STATE_FILE,
        sr._RUN_FILE,
    ]
    before = [p.read_bytes() if p.exists() else None for p in live]

    monkeypatch.setattr(monitor, "_DEADMAN_STATE_FILE", tmp_path / "deadman_state.json")
    monkeypatch.setattr(
        monitor, "_SEAL_DEADMAN_STATE_FILE", tmp_path / "seal_deadman_state.json"
    )
    monkeypatch.setattr(monitor, "_maybe_alert_catastrophic_cycle", lambda *_a, **_k: None)
    monkeypatch.setattr(monitor, "_maybe_alert_seal_failures", lambda *_a, **_k: None)

    yield

    after = [p.read_bytes() if p.exists() else None for p in live]
    assert after == before, (
        "tests must not mutate live product data: "
        f"{[str(p) for p, b, a in zip(live, before, after) if b != a]}"
    )


# ── shared fixture: redirect the run trail to a tmp dir ──────────────────────
@pytest.fixture
def trail(tmp_path, monkeypatch):
    import app.source_runs as sr

    run_dir = tmp_path / "data" / "source_runs"
    monkeypatch.setattr(sr, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(sr, "_RUN_DIR", run_dir)
    monkeypatch.setattr(sr, "_RUN_FILE", run_dir / "source_runs.jsonl")
    monkeypatch.setattr(sr, "_SNAPSHOT_DIR", tmp_path / "data" / "source_snapshots")
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None
    run_dir.mkdir(parents=True, exist_ok=True)
    return sr


# ══════════════════════════════════════════════════════════════════════════
# Bug 1 — circuit breaker: failed sources must persist a FAILED trail record
# ══════════════════════════════════════════════════════════════════════════
def test_raising_source_persists_failed_record_and_opens_circuit(trail, tmp_path, monkeypatch):
    import app.monitor as monitor

    source = {
        "name": "Always-Fails Source",
        "url": "https://fails.example/always",
        "jurisdiction": "AE",
        "category": "banking",
        "status": "active",
        "enabled": True,
    }

    # A source whose pipeline always raises a timeout (403/timeout classify path).
    def _always_raises(_src):
        raise TimeoutError("connection timed out")

    monkeypatch.setattr(monitor, "run_pipeline_for_source", _always_raises)
    monkeypatch.setattr(monitor, "get_enabled_sources", lambda: [source])
    monkeypatch.setattr(monitor, "init_pipeline", lambda *_a, **_k: None)
    # Do not actually sleep on the retry.
    monkeypatch.setattr(monitor.time, "sleep", lambda *_a, **_k: None)
    # Redirect breaker state to tmp and start with a clean registry.
    monkeypatch.setattr(monitor, "_CIRCUIT_STATE_FILE", tmp_path / "circuit_state.json")
    monkeypatch.setattr(monitor, "_circuit_open", set())

    run_file = trail.source_run_path()

    # ── Pre-fix behaviour: no FAILED record is ever written, so consecutive
    #    failures stays 0 forever. Post-fix: each cycle appends one FAILED row.
    for _ in range(monitor._CIRCUIT_OPEN_THRESHOLD):
        monitor.monitor_all_sources(verbose=False)

    assert run_file.exists(), "a FAILED run record must be persisted"
    records = [json.loads(ln) for ln in run_file.read_text().splitlines() if ln.strip()]
    failed = [r for r in records if r.get("change_status") == "FAILED"]
    assert len(failed) == monitor._CIRCUIT_OPEN_THRESHOLD, (
        f"expected {monitor._CIRCUIT_OPEN_THRESHOLD} FAILED records, got {len(failed)}"
    )
    assert all(r.get("url") == source["url"] for r in failed)

    # _consecutive_failures now sees the real failures (was always 0 pre-fix).
    assert monitor._consecutive_failures(source["url"]) >= monitor._CIRCUIT_OPEN_THRESHOLD

    # The breaker has opened for this source (keyed by URL, matching the failure
    # counter — see test_circuit_breaker_keys_on_url_not_shared_name).
    assert source["url"] in monitor._circuit_open

    # Next cycle short-circuits: pipeline is NOT invoked (source is skipped).
    def _must_not_be_called(_src):  # pragma: no cover - asserts non-invocation
        raise AssertionError("open circuit must skip the source, not fetch it")

    monkeypatch.setattr(monitor, "run_pipeline_for_source", _must_not_be_called)
    results = monitor.monitor_all_sources(verbose=False)
    assert results[0]["access_status"] == "circuit_open"


# ══════════════════════════════════════════════════════════════════════════
# Audit 07-20 HIGH — the breaker window must survive FLEET-SCALE dilution.
# ══════════════════════════════════════════════════════════════════════════
def test_circuit_opens_at_fleet_scale(trail, tmp_path, monkeypatch):
    """Audit 07-20 HIGH: with a ~139-source fleet appending ~139 trail records
    per cycle, a 200-LINE history window spans barely one cycle, so a single
    always-failing URL never accumulates _CIRCUIT_OPEN_THRESHOLD consecutive
    records inside the window and the breaker can never open in production.
    The 1-source tests above cannot catch this — the whole file fits their
    window. Red before the byte-bounded per-URL scan; green after."""
    import uuid as _uuid

    import app.monitor as monitor

    fleet_size = 139
    failing = {
        "name": "Fleet Failing Source", "url": "https://fails.example/fleet",
        "jurisdiction": "AE", "category": "banking", "status": "active", "enabled": True,
    }
    healthy = [
        {"name": f"Healthy {i}", "url": f"https://ok.example/src-{i}",
         "jurisdiction": "AE", "category": "banking", "status": "active", "enabled": True}
        for i in range(fleet_size - 1)
    ]
    # Failing source FIRST: by breaker-check time its newest FAILED record is
    # maximally diluted by the 138 records appended after it each cycle.
    sources = [failing] + healthy

    # Healthy sources append REAL trail records — that is exactly what dilutes
    # the window in production (classify_change sees access "ok" + GOOD quality
    # → non-FAILED change_status).
    def _fake_pipeline(src):
        if src["url"] == failing["url"]:
            raise TimeoutError("connection timed out")
        trail.append_run({
            "run_id": _uuid.uuid4().hex[:8],
            "source_id": trail.make_source_id(src),
            "source_name": src["name"],
            "official_url": src["url"], "url": src["url"],
            "market": "AE", "jurisdiction": "AE", "category": "banking",
            "access_status": "ok", "extraction_quality": "GOOD",
            "extracted_chars": 1200, "normalized_chars": 1200,
            "raw_hash": "r-" + src["url"], "normalized_hash": "n-" + src["url"],
            "content_hash": "c-" + src["url"],
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "pipeline_version": "4.2",
        })
        return {"changed": False, "status": "unchanged", "url": src["url"]}

    monkeypatch.setattr(monitor, "run_pipeline_for_source", _fake_pipeline)
    monkeypatch.setattr(monitor, "get_enabled_sources", lambda: sources)
    monkeypatch.setattr(monitor, "init_pipeline", lambda *_a, **_k: None)
    monkeypatch.setattr(monitor.time, "sleep", lambda *_a, **_k: None)
    monkeypatch.setattr(monitor, "_CIRCUIT_STATE_FILE", tmp_path / "circuit_state.json")
    monkeypatch.setattr(monitor, "_DEADMAN_STATE_FILE", tmp_path / "deadman_state.json")
    monkeypatch.setattr(monitor, "_circuit_open", set())
    monkeypatch.setattr(monitor, "_circuit_skip_counts", {})

    for _ in range(monitor._CIRCUIT_OPEN_THRESHOLD):
        monitor.monitor_all_sources(verbose=False)

    assert monitor._consecutive_failures(failing["url"]) >= monitor._CIRCUIT_OPEN_THRESHOLD
    assert failing["url"] in monitor._circuit_open, (
        "breaker must open for a URL that failed every cycle at fleet scale"
    )


# ══════════════════════════════════════════════════════════════════════════
# WARN-6 — circuit breaker must AUTO-RESET on a successful probe/run so a
#          transient outage does not skip a source forever.
# ══════════════════════════════════════════════════════════════════════════
def test_circuit_auto_resets_after_successful_probe(trail, tmp_path, monkeypatch):
    import app.monitor as monitor

    source = {
        "name": "Flaky Source",
        "url": "https://flaky.example/probe",
        "jurisdiction": "AE",
        "category": "banking",
        "status": "active",
        "enabled": True,
    }

    monkeypatch.setattr(monitor, "get_enabled_sources", lambda: [source])
    monkeypatch.setattr(monitor, "init_pipeline", lambda *_a, **_k: None)
    monkeypatch.setattr(monitor.time, "sleep", lambda *_a, **_k: None)
    monkeypatch.setattr(monitor, "_CIRCUIT_STATE_FILE", tmp_path / "circuit_state.json")
    monkeypatch.setattr(monitor, "_circuit_open", set())
    monkeypatch.setattr(monitor, "_circuit_skip_counts", {})

    # ── Phase 1: N failing cycles trip the breaker ────────────────────────────
    def _always_raises(_src):
        raise TimeoutError("connection timed out")

    monkeypatch.setattr(monitor, "run_pipeline_for_source", _always_raises)
    for _ in range(monitor._CIRCUIT_OPEN_THRESHOLD):
        monitor.monitor_all_sources(verbose=False)
    assert source["url"] in monitor._circuit_open, "breaker should be open"

    # ── Phase 2: the source recovers. Advance cycles: the open circuit skips
    #    during cooldown, then a half-open probe is allowed through and succeeds,
    #    which must AUTO-RESET the breaker.
    def _succeeds(_src):
        return {
            "source_name":  source["name"],
            "url":          source["url"],
            "jurisdiction": source["jurisdiction"],
            "category":     source["category"],
            "changed":      False,
            "status":       "ok",
        }

    monkeypatch.setattr(monitor, "run_pipeline_for_source", _succeeds)

    resumed = False
    # Enough cycles to cross the cooldown and probe (cadence + slack).
    for _ in range(monitor._CIRCUIT_PROBE_EVERY_N_CYCLES + 2):
        results = monitor.monitor_all_sources(verbose=False)
        if not results[0].get("circuit_open") and results[0].get("status") == "ok":
            resumed = True
            break

    assert resumed, "a successful half-open probe must resume monitoring"
    # Breaker is cleared and stays cleared on subsequent successful cycles.
    assert source["url"] not in monitor._circuit_open
    follow_up = monitor.monitor_all_sources(verbose=False)
    assert follow_up[0].get("status") == "ok"
    assert not follow_up[0].get("circuit_open")


# ══════════════════════════════════════════════════════════════════════════
# G4 — the circuit breaker must key on the URL (the failure-count key), NOT the
#      display name. Two enabled sources sharing a name but with different URLs
#      must have INDEPENDENT breakers: one tripping must not dark the other.
# ══════════════════════════════════════════════════════════════════════════
def test_circuit_breaker_keys_on_url_not_shared_name(trail, tmp_path, monkeypatch):
    import app.monitor as monitor

    failing = {
        "name": "Shared Name", "url": "https://a.example/fails",
        "jurisdiction": "AE", "category": "banking", "status": "active", "enabled": True,
    }
    healthy = {
        "name": "Shared Name", "url": "https://b.example/works",
        "jurisdiction": "AE", "category": "banking", "status": "active", "enabled": True,
    }

    monkeypatch.setattr(monitor, "get_enabled_sources", lambda: [failing, healthy])
    monkeypatch.setattr(monitor, "init_pipeline", lambda *_a, **_k: None)
    monkeypatch.setattr(monitor.time, "sleep", lambda *_a, **_k: None)
    monkeypatch.setattr(monitor, "_CIRCUIT_STATE_FILE", tmp_path / "circuit_state.json")
    monkeypatch.setattr(monitor, "_circuit_open", set())
    monkeypatch.setattr(monitor, "_circuit_skip_counts", {})

    def _dispatch(src):
        if src["url"] == failing["url"]:
            raise TimeoutError("connection timed out")
        return {
            "source_name": src["name"], "url": src["url"],
            "jurisdiction": src["jurisdiction"], "category": src["category"],
            "changed": False, "status": "ok",
        }

    monkeypatch.setattr(monitor, "run_pipeline_for_source", _dispatch)

    # Trip the breaker on the failing twin only.
    for _ in range(monitor._CIRCUIT_OPEN_THRESHOLD):
        monitor.monitor_all_sources(verbose=False)

    # Only the failing URL's breaker is open — the shared name did NOT dark both.
    assert failing["url"] in monitor._circuit_open
    assert healthy["url"] not in monitor._circuit_open

    # The healthy twin is STILL fetched and reports ok (it is not skipped).
    fetched_healthy = {"hit": False}

    def _dispatch2(src):
        if src["url"] == failing["url"]:
            raise AssertionError("open circuit must skip the FAILING source")
        fetched_healthy["hit"] = True
        return {
            "source_name": src["name"], "url": src["url"],
            "jurisdiction": src["jurisdiction"], "category": src["category"],
            "changed": False, "status": "ok",
        }

    monkeypatch.setattr(monitor, "run_pipeline_for_source", _dispatch2)
    results = monitor.monitor_all_sources(verbose=False)
    assert fetched_healthy["hit"], "the healthy twin must not be skipped by the twin's breaker"
    healthy_result = next(r for r in results if r.get("url") == healthy["url"])
    assert healthy_result.get("access_status") != "circuit_open"


# ══════════════════════════════════════════════════════════════════════════
# Bug 2 — inode race: append must land in the live file after an os.replace
# ══════════════════════════════════════════════════════════════════════════
def test_locked_append_survives_inode_swap(trail, monkeypatch):
    """
    Simulate a retention rewrite that swaps the run-file inode out from under
    an in-progress append. The appended record must end up in the LIVE file,
    not a now-unlinked inode.
    """
    sr = trail
    run_file = sr.source_run_path()

    # Seed the file with an initial record so it exists on a real inode.
    run_file.write_text(
        json.dumps({"source_id": "S1", "change_status": "FIRST_SEEN", "n": 0}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    original_ino = os.stat(run_file).st_ino

    real_open = Path.open
    swapped = {"done": False}

    def _open_then_swap(self, *args, **kwargs):
        fh = real_open(self, *args, **kwargs)
        # On the FIRST append-mode open of the run file, replace the file with a
        # fresh inode BEFORE the caller flocks/writes — exactly the retention
        # os.replace() race. The helper must detect the inode mismatch and retry.
        if (
            not swapped["done"]
            and Path(self) == run_file
            and args
            and "a" in str(args[0])
        ):
            swapped["done"] = True
            tmp = run_file.with_suffix(".swap-tmp")
            tmp.write_text(
                json.dumps({"source_id": "S1", "change_status": "FIRST_SEEN", "n": 0}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            os.replace(tmp, run_file)  # new inode Y now backs the path
        return fh

    monkeypatch.setattr(Path, "open", _open_then_swap)

    sr._locked_append_line(
        json.dumps({"source_id": "S1", "change_status": "CHANGED", "n": 1}, sort_keys=True) + "\n"
    )

    monkeypatch.undo()  # restore Path.open before reading

    # The path must now point at a different inode (the swap happened) ...
    assert os.stat(run_file).st_ino != original_ino
    # ... AND the appended CHANGED record must be present in that live file.
    live_records = [json.loads(ln) for ln in run_file.read_text().splitlines() if ln.strip()]
    assert any(r.get("change_status") == "CHANGED" and r.get("n") == 1 for r in live_records), (
        "appended record was written to the dead inode and lost"
    )


# ══════════════════════════════════════════════════════════════════════════
# Bug 3 — retention must survive a malformed JSONL line
# ══════════════════════════════════════════════════════════════════════════
def _hb(source_id: str, ts: datetime, run_id: str) -> dict:
    return {
        "record_type": "heartbeat",
        "run_id": run_id,
        "source_id": source_id,
        "official_url": f"https://example.gov.ae/{source_id}",
        "change_status": "UNCHANGED",
        "normalized_hash": "a" * 64,
        "timestamp_utc": ts.isoformat(),
    }


def test_compact_heartbeats_survives_malformed_line(trail):
    import app.retention as retention

    sr = trail
    run_file = sr.source_run_path()
    now = datetime(2026, 7, 5, 12, 0, 0, tzinfo=timezone.utc)
    old = now - timedelta(days=45)

    good_lines = [
        json.dumps(_hb("src-a", old.replace(hour=1), "h1"), sort_keys=True),
        json.dumps(_hb("src-a", old.replace(hour=6), "h2"), sort_keys=True),
        json.dumps(_hb("src-a", old.replace(hour=12), "h3"), sort_keys=True),
    ]
    # A truncated partial write from a killed process (what _read_runs tolerates).
    malformed = '{"source_id": "src-a", "change_stat'
    run_file.write_text("\n".join(good_lines) + "\n" + malformed + "\n", encoding="utf-8")

    # Pre-fix: json.loads on the malformed line raised JSONDecodeError and
    # aborted the whole job. Post-fix: it compacts and leaves the corrupt line.
    res = retention.compact_heartbeats(days_threshold=30, now=now)
    assert res["removed"] == 2, res  # 3 old same-day heartbeats -> last survives

    remaining = run_file.read_text().splitlines()
    # The malformed line must be preserved verbatim (evidence — never discarded).
    assert malformed in remaining
    # The surviving heartbeat is the last-of-day (h3).
    parsed = [json.loads(ln) for ln in remaining if ln.strip() and not ln.startswith('{"source_id": "src-a", "change_stat')]
    assert [r["run_id"] for r in parsed] == ["h3"]

    # Idempotent: a second run with the corrupt line still present is a no-op.
    res2 = retention.compact_heartbeats(days_threshold=30, now=now)
    assert res2["removed"] == 0, res2


def test_compact_quality_drop_survives_malformed_line(trail):
    import app.retention as retention

    sr = trail
    run_file = sr.source_run_path()
    now = datetime(2026, 7, 5, 12, 0, 0, tzinfo=timezone.utc)
    old = now - timedelta(days=45)

    def _qd(ts, run_id):
        rec = _hb("src-b", ts, run_id)
        rec["record_type"] = "run"
        rec["change_status"] = "QUALITY_DROP"
        return rec

    lines = [
        json.dumps(_qd(old.replace(hour=1), "t1"), sort_keys=True),   # transition — forever
        json.dumps(_qd(old.replace(hour=6), "r1"), sort_keys=True),   # old repeat
        json.dumps(_qd(old.replace(hour=12), "r2"), sort_keys=True),  # old repeat (last-of-day)
    ]
    malformed = '{"source_id": "src-b", "change_stat'
    run_file.write_text("\n".join(lines) + "\n" + malformed + "\n", encoding="utf-8")

    res = retention.compact_quality_drop_repeats(days_threshold=30, now=now)
    assert res["removed"] == 1, res  # r1 dropped; t1 (transition) + r2 (last-of-day) kept
    assert malformed in run_file.read_text().splitlines()


# ══════════════════════════════════════════════════════════════════════════
# Bug 4 — hash-collision detection must consult the run trail
# ══════════════════════════════════════════════════════════════════════════
def test_hash_collision_uses_trail_when_sources_lack_content_hash(trail, monkeypatch):
    import app.source_intake as si

    shared_hash = "deadbeefcafe0001"

    # sources.json-shaped entries: NO content_hash key (as in production).
    all_sources = [
        {"source_id": "AE-1", "enabled": True, "url": "https://a.example"},
        {"source_id": "AE-2", "enabled": True, "url": "https://b.example"},
    ]

    # The run trail carries AE-1's stored content hash (intake evidence-write path).
    def _fake_latest_runs():
        return {"AE-1": {"content_hash": shared_hash, "source_id": "AE-1"}}

    monkeypatch.setattr("app.source_runs.latest_runs", _fake_latest_runs)

    # AE-2 extracts the same content T -> must collide with AE-1 via the trail.
    collision, cid = si._check_hash_collision(shared_hash, "AE-2", all_sources)
    assert collision is True, "duplicate content must be detected via the run trail"
    assert cid == "AE-1"

    # A unique hash still does not collide.
    no_collision, none_id = si._check_hash_collision("uniquehash00000000", "AE-2", all_sources)
    assert no_collision is False
    assert none_id is None


def test_hash_collision_ignores_disabled_and_self(trail, monkeypatch):
    import app.source_intake as si

    shared_hash = "deadbeefcafe0002"

    all_sources = [
        {"source_id": "AE-self", "enabled": True, "url": "https://self.example"},
        {"source_id": "AE-disabled", "enabled": False, "url": "https://dis.example"},
    ]
    monkeypatch.setattr(
        "app.source_runs.latest_runs",
        lambda: {
            "AE-self": {"content_hash": shared_hash},
            "AE-disabled": {"content_hash": shared_hash},
        },
    )
    # Same hash as self and a disabled source -> no collision.
    collision, cid = si._check_hash_collision(shared_hash, "AE-self", all_sources)
    assert collision is False
    assert cid is None
