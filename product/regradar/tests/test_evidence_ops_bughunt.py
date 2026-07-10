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

    # The breaker has opened for this source.
    assert source["name"] in monitor._circuit_open

    # Next cycle short-circuits: pipeline is NOT invoked (source is skipped).
    def _must_not_be_called(_src):  # pragma: no cover - asserts non-invocation
        raise AssertionError("open circuit must skip the source, not fetch it")

    monkeypatch.setattr(monitor, "run_pipeline_for_source", _must_not_be_called)
    results = monitor.monitor_all_sources(verbose=False)
    assert results[0]["access_status"] == "circuit_open"


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
