"""Circuit-breaker regression tests: QUALITY_DROP must count as a failure.

Production reality (trail census 2026-07-20): 123 QUALITY_DROP records against
51 FAILED. A bot-walled source or one served an error page does NOT raise — the
pipeline guard aborts cleanly, writes a baseline-safe QUALITY_DROP trail record
and returns ``status="quality_drop"``. That is exactly the chronic-failure
signal the breaker exists to detect, yet the breaker counted only "FAILED" and
the guard-abort took the monitor's SUCCESS path, which auto-cleared the breaker.
Net effect: a source that is permanently dark was probed every cycle forever and
never tripped the breaker.

These tests pin the fixed semantics:
  * QUALITY_DROP counts toward the same consecutive-failure counter as FAILED
    (one shared threshold — see _UNUSABLE_RUN_STATUSES in app/monitor.py).
  * a guard-abort never auto-resets the breaker.
  * a genuinely healthy source never trips it.
  * alternating quality-drop / success never trips it (a real success resets).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def trail(tmp_path, monkeypatch):
    """Redirect the run trail to a tmp dir (hermetic, no live network)."""
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


def _isolate_breaker(monitor, tmp_path, monkeypatch, sources):
    monkeypatch.setattr(monitor, "get_enabled_sources", lambda: sources)
    monkeypatch.setattr(monitor, "init_pipeline", lambda *_a, **_k: None)
    monkeypatch.setattr(monitor.time, "sleep", lambda *_a, **_k: None)
    monkeypatch.setattr(monitor, "_CIRCUIT_STATE_FILE", tmp_path / "circuit_state.json")
    monkeypatch.setattr(monitor, "_circuit_open", set())
    monkeypatch.setattr(monitor, "_circuit_skip_counts", {})
    # Ops-state isolation (MANDATORY): a cycle in which every fake source is
    # guard-aborted has sources_ok + sources_unchanged == 0, which satisfies
    # _is_catastrophic_cycle — so without these patches the tests rewrite the
    # REAL data/deadman_state.json and POST a founder alert to Telegram using
    # the admin bot token from the environment. Same convention as
    # tests/test_deadman_self_monitoring.py.
    monkeypatch.setattr(monitor, "_DEADMAN_STATE_FILE", tmp_path / "deadman_state.json")
    monkeypatch.setattr(
        monitor, "_SEAL_DEADMAN_STATE_FILE", tmp_path / "seal_deadman_state.json"
    )
    monkeypatch.setattr(monitor, "_maybe_alert_catastrophic_cycle", lambda *_a, **_k: None)
    monkeypatch.setattr(monitor, "_maybe_alert_seal_failures", lambda *_a, **_k: None)


def _bot_walled(source):
    """Behave exactly like pipeline's bot-wall guard: durable QUALITY_DROP
    trail record, no hash, clean (non-raising) return."""
    from app.source_runs import record_quality_drop

    record_quality_drop(
        source,
        reason="Fetched content is an anti-bot / JS-challenge wall",
        alert_suppressed_reason="bot_wall",
        observed_raw_chars=87,
        failure_code="BOT_WALL",
        access_status="blocked",
    )
    return {
        "source_name":  source["name"],
        "url":          source["url"],
        "changed":      False,
        "status":       "quality_drop",
        "access_status": "blocked",
        "failure_code": "BOT_WALL",
        "extraction_quality": "failed",
    }


def _healthy(source):
    """A real successful run: normal trail record, usable content."""
    from app.source_runs import append_run

    append_run({
        "source_id":     source["url"],
        "source_name":   source["name"],
        "official_url":  source["url"],
        "url":           source["url"],
        "market":        "AE",
        "access_status": "ok",
        "extraction_quality": "good",
        "extracted_chars": 4200,
        "normalized_chars": 4100,
        "content_hash":  "a" * 64,
        "normalized_hash": "a" * 64,
        "raw_hash":      "b" * 64,
    })
    return {
        "source_name": source["name"],
        "url":         source["url"],
        "changed":     False,
        "status":      "ok",
    }


def _shrink_suppressed(source):
    """Behave exactly like pipeline's content-shrink guard: the source is
    REACHABLE, its content genuinely shrank, the alert is suppressed and the
    baseline is deliberately left intact — so the guard fires again on every
    later cycle until a human re-baselines."""
    from app.source_runs import record_quality_drop

    record_quality_drop(
        source,
        reason="Raw content shrank 4200 -> 900 chars (78%)",
        alert_suppressed_reason="content_shrink",
        observed_raw_chars=900,
        prev_raw_chars=4200,
        prev_normalized_chars=4100,
    )
    return {
        "source_name":  source["name"],
        "url":          source["url"],
        "changed":      False,
        "status":       "quality_drop",
        "shrink_suppressed": True,
        "shrink_reason": "Raw content shrank 4200 -> 900 chars (78%)",
        "alert_suppressed_reason": "content_shrink",
        # pipeline.py's shrink return carries the chars actually retrieved.
        # 900 is a plausible page: the source demonstrably answered.
        "extracted_chars": 900,
        "extraction_quality": "failed",
    }


def _thin(source):
    """A run that does NOT abort in a guard: it fetches, extracts a thin page
    and returns status "ok" — classify_change stamps the trail record
    QUALITY_DROP. This is the class that dominates the production trail."""
    from app.source_runs import append_run

    record = append_run({
        "source_id":     source["url"],
        "source_name":   source["name"],
        "official_url":  source["url"],
        "url":           source["url"],
        "market":        "AE",
        "access_status": "ok",
        "extraction_quality": "thin",
        "extracted_chars": 62,
        "normalized_chars": 58,
        "content_hash":  "c" * 64,
        "normalized_hash": "c" * 64,
        "raw_hash":      "d" * 64,
    })
    return {
        "source_name": source["name"],
        "url":         source["url"],
        "changed":     False,
        "status":      "ok",
        "run_record":  record,
    }


def _src(name, url):
    return {
        "name": name, "url": url, "jurisdiction": "AE",
        "category": "banking", "status": "active", "enabled": True,
    }


# ══════════════════════════════════════════════════════════════════════════
# 1 — a source that is QUALITY_DROP every cycle must open the breaker
# ══════════════════════════════════════════════════════════════════════════
def test_chronic_quality_drop_opens_circuit(trail, tmp_path, monkeypatch):
    import app.monitor as monitor

    walled = _src("Bot-Walled Source", "https://walled.example/regs")
    _isolate_breaker(monitor, tmp_path, monkeypatch, [walled])
    monkeypatch.setattr(monitor, "run_pipeline_for_source", _bot_walled)

    for _ in range(monitor._CIRCUIT_OPEN_THRESHOLD):
        monitor.monitor_all_sources(verbose=False)

    assert monitor._consecutive_failures(walled["url"]) >= monitor._CIRCUIT_OPEN_THRESHOLD, (
        "QUALITY_DROP records must count toward the consecutive-failure counter"
    )
    assert walled["url"] in monitor._circuit_open, (
        "a source dark with QUALITY_DROP every cycle must trip the breaker"
    )

    # And the next cycle actually skips it instead of re-probing.
    def _must_not_run(_src_):
        raise AssertionError("open circuit must skip the source, not fetch it")

    monkeypatch.setattr(monitor, "run_pipeline_for_source", _must_not_run)
    results = monitor.monitor_all_sources(verbose=False)
    assert results[0].get("circuit_open") is True


# ══════════════════════════════════════════════════════════════════════════
# 2 — a guard-abort must not silently CLEAR an already-open breaker
# ══════════════════════════════════════════════════════════════════════════
def test_quality_drop_does_not_clear_open_circuit(trail, tmp_path, monkeypatch):
    import app.monitor as monitor

    walled = _src("Flapping Walled Source", "https://walled.example/flap")
    _isolate_breaker(monitor, tmp_path, monkeypatch, [walled])
    monkeypatch.setattr(monitor, "_circuit_open", {walled["url"]})
    monkeypatch.setattr(monitor, "run_pipeline_for_source", _bot_walled)

    # Advance past the cooldown so a half-open probe runs; the probe is a
    # QUALITY_DROP, so the breaker must stay open.
    for _ in range(monitor._CIRCUIT_PROBE_EVERY_N_CYCLES + 2):
        monitor.monitor_all_sources(verbose=False)

    assert walled["url"] in monitor._circuit_open, (
        "a QUALITY_DROP probe is not a recovery signal — breaker must stay open"
    )


# ══════════════════════════════════════════════════════════════════════════
# 3 — a genuinely healthy source must NEVER open the breaker
# ══════════════════════════════════════════════════════════════════════════
def test_healthy_source_never_opens_circuit(trail, tmp_path, monkeypatch):
    import app.monitor as monitor

    healthy = _src("Healthy Source", "https://healthy.example/regs")
    _isolate_breaker(monitor, tmp_path, monkeypatch, [healthy])
    monkeypatch.setattr(monitor, "run_pipeline_for_source", _healthy)

    for _ in range(monitor._CIRCUIT_OPEN_THRESHOLD + 3):
        monitor.monitor_all_sources(verbose=False)

    assert monitor._consecutive_failures(healthy["url"]) == 0
    assert healthy["url"] not in monitor._circuit_open


# ══════════════════════════════════════════════════════════════════════════
# 4 — alternating QUALITY_DROP / success stays closed (documented behaviour)
# ══════════════════════════════════════════════════════════════════════════
def test_alternating_quality_drop_and_success_stays_closed(trail, tmp_path, monkeypatch):
    import app.monitor as monitor

    flaky = _src("Flaky Source", "https://flaky.example/regs")
    _isolate_breaker(monitor, tmp_path, monkeypatch, [flaky])

    state = {"n": 0}

    def _alternating(source):
        state["n"] += 1
        return _bot_walled(source) if state["n"] % 2 else _healthy(source)

    monkeypatch.setattr(monitor, "run_pipeline_for_source", _alternating)

    for _ in range(2 * monitor._CIRCUIT_OPEN_THRESHOLD + 4):
        monitor.monitor_all_sources(verbose=False)
        assert flaky["url"] not in monitor._circuit_open, (
            "an intermittent source still yields usable content — a real "
            "success must reset the counter and keep the breaker closed"
        )


# ══════════════════════════════════════════════════════════════════════════
# 5 — mixed FAILED + QUALITY_DROP across cycles still trips the breaker
#     (the real bot-wall pattern: 403 one cycle, challenge page the next)
# ══════════════════════════════════════════════════════════════════════════
def test_mixed_failed_and_quality_drop_opens_circuit(trail, tmp_path, monkeypatch):
    import app.monitor as monitor

    mixed = _src("Mixed Failure Source", "https://mixed.example/regs")
    _isolate_breaker(monitor, tmp_path, monkeypatch, [mixed])

    def _raises(_source):
        raise TimeoutError("connection timed out")

    # Alternate WHOLE cycles (not retry attempts): 403-style hard failure one
    # cycle, challenge-page QUALITY_DROP the next.
    for cycle in range(monitor._CIRCUIT_OPEN_THRESHOLD):
        monkeypatch.setattr(
            monitor, "run_pipeline_for_source",
            _raises if cycle % 2 == 0 else _bot_walled,
        )
        monitor.monitor_all_sources(verbose=False)

    assert mixed["url"] in monitor._circuit_open, (
        "separate counters for FAILED and QUALITY_DROP would let an "
        "alternating dark source stay under both thresholds forever"
    )


# ══════════════════════════════════════════════════════════════════════════
# 6 — these tests must never touch LIVE ops state or send a founder alert
# ══════════════════════════════════════════════════════════════════════════
def test_breaker_cycles_never_touch_live_ops_state(trail, tmp_path, monkeypatch):
    """A cycle where every source guard-aborts has ok + unchanged == 0, which
    satisfies _is_catastrophic_cycle — so an unisolated test rewrites the real
    data/deadman_state.json and POSTs a founder Telegram alert with the admin
    bot token. Both are test-harness defects, not product behaviour."""
    import app.ops_alert as ops_alert
    import app.monitor as monitor

    live_dir = Path(monitor.__file__).parent.parent / "data"
    live = [live_dir / "deadman_state.json", live_dir / "seal_deadman_state.json"]
    before = [p.read_bytes() if p.exists() else None for p in live]

    sent: list = []
    monkeypatch.setattr(ops_alert, "notify_founder", lambda *a, **k: sent.append(a))

    walled = _src("Leaky Source", "https://leaky.example/regs")
    _isolate_breaker(monitor, tmp_path, monkeypatch, [walled])
    monkeypatch.setattr(monitor, "run_pipeline_for_source", _bot_walled)

    # The isolation helper MUST bind both ops state files inside tmp_path.
    # Asserting the binding (not just the file bytes) keeps this test honest
    # regardless of what the live flag happens to hold on this machine.
    assert tmp_path in monitor._DEADMAN_STATE_FILE.parents
    assert tmp_path in monitor._SEAL_DEADMAN_STATE_FILE.parents

    for _ in range(monitor._CIRCUIT_OPEN_THRESHOLD):
        monitor.monitor_all_sources(verbose=False)

    after = [p.read_bytes() if p.exists() else None for p in live]
    assert after == before, "tests must not write the live ops state files"
    assert sent == [], "tests must not reach the live founder-alert path"


# ══════════════════════════════════════════════════════════════════════════
# 7 — sticky content-shrink suppression must NOT open the breaker
# ══════════════════════════════════════════════════════════════════════════
def test_content_shrink_suppression_never_opens_circuit(trail, tmp_path, monkeypatch):
    """The shrink guard is sticky BY DESIGN (baseline intentionally not
    updated), so it re-fires every cycle until a human re-baselines. The source
    is reachable and its content genuinely changed — exactly the HIGH-risk
    event the product exists to catch. Letting that trip the breaker would stop
    fetching the page for 5 of every 6 cycles."""
    import app.monitor as monitor

    shrunk = _src("Shrunk Source", "https://shrunk.example/regs")
    _isolate_breaker(monitor, tmp_path, monkeypatch, [shrunk])
    monkeypatch.setattr(monitor, "run_pipeline_for_source", _shrink_suppressed)

    for _ in range(monitor._CIRCUIT_OPEN_THRESHOLD + 3):
        monitor.monitor_all_sources(verbose=False)
        assert shrunk["url"] not in monitor._circuit_open, (
            "a reachable source whose content shrank is not a dark source — "
            "the breaker must stay closed so the page keeps being fetched"
        )


# ══════════════════════════════════════════════════════════════════════════
# 8 — a skipped (circuit-open) cycle must still leave a durable trail record
# ══════════════════════════════════════════════════════════════════════════
def test_circuit_open_skip_writes_trail_record(trail, tmp_path, monkeypatch):
    """An evidence product must be able to prove when it could NOT see a
    source. Silently skipping 5 of every 6 cycles would leave the coverage
    certificate with no record — and no reason text — for those cycles."""
    import json as _json

    import app.monitor as monitor

    walled = _src("Chronically Walled", "https://walled.example/chronic")
    _isolate_breaker(monitor, tmp_path, monkeypatch, [walled])
    monkeypatch.setattr(monitor, "run_pipeline_for_source", _bot_walled)

    for _ in range(monitor._CIRCUIT_OPEN_THRESHOLD):
        monitor.monitor_all_sources(verbose=False)
    assert walled["url"] in monitor._circuit_open

    def _must_not_run(_src_):
        raise AssertionError("open circuit must skip the source, not fetch it")

    monkeypatch.setattr(monitor, "run_pipeline_for_source", _must_not_run)
    monitor.monitor_all_sources(verbose=False)

    run_file = tmp_path / "data" / "source_runs" / "source_runs.jsonl"
    records = [
        _json.loads(line)
        for line in run_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    skip_records = [r for r in records if r.get("failure_code") == "CIRCUIT_OPEN"]
    assert skip_records, (
        "a cycle skipped by an open circuit must still write a durable "
        "'could not see this source' trail record"
    )
    last = skip_records[-1]
    assert last["change_status"] == "QUALITY_DROP"
    assert last["url"] == walled["url"]
    # Baseline safety: the record must carry no usable hash.
    assert not last.get("normalized_hash") and not last.get("content_hash")


# ══════════════════════════════════════════════════════════════════════════
# 9 — a chronically THIN source (trail-classified QUALITY_DROP, status "ok")
#     must open the breaker too — that is prod's dominant QUALITY_DROP class
# ══════════════════════════════════════════════════════════════════════════
def test_chronic_thin_run_opens_circuit(trail, tmp_path, monkeypatch):
    import app.monitor as monitor

    vara = _src("Thin Source", "https://thin.example/regulatory-framework")
    _isolate_breaker(monitor, tmp_path, monkeypatch, [vara])

    state = {"n": 0}

    def _good_then_thin(source):
        state["n"] += 1
        return _healthy(source) if state["n"] == 1 else _thin(source)

    monkeypatch.setattr(monitor, "run_pipeline_for_source", _good_then_thin)

    for _ in range(monitor._CIRCUIT_OPEN_THRESHOLD + 1):
        monitor.monitor_all_sources(verbose=False)

    assert monitor._consecutive_failures(vara["url"]) >= monitor._CIRCUIT_OPEN_THRESHOLD, (
        "trail records classified QUALITY_DROP by extraction quality must "
        "count toward the consecutive-failure counter"
    )
    assert vara["url"] in monitor._circuit_open, (
        "a source that keeps returning a thin page is chronically dark even "
        "though the pipeline never aborts in a guard"
    )


# ══════════════════════════════════════════════════════════════════════════
# 9 — an open breaker must be CLEARED by a reachable, shrink-suppressed probe
# ══════════════════════════════════════════════════════════════════════════
def test_shrink_suppressed_probe_clears_open_circuit(trail, tmp_path, monkeypatch):
    """The shrink guard is sticky by design: it re-fires every cycle until a
    human re-baselines. If a shrink-suppressed probe cannot clear the breaker,
    a source that went dark and then came back RESTRUCTURED (outage, then site
    rebuild — the common pair) is pinned at a 1-in-6 fetch cadence forever, on
    exactly the page whose content just changed."""
    import app.monitor as monitor

    shrunk = _src("Recovered But Shrunk", "https://shrunk.example/recovered")
    _isolate_breaker(monitor, tmp_path, monkeypatch, [shrunk])
    monkeypatch.setattr(monitor, "_circuit_open", {shrunk["url"]})
    monkeypatch.setattr(monitor, "run_pipeline_for_source", _shrink_suppressed)

    for _ in range(monitor._CIRCUIT_PROBE_EVERY_N_CYCLES + 2):
        monitor.monitor_all_sources(verbose=False)

    assert shrunk["url"] not in monitor._circuit_open, (
        "the source demonstrably answered the half-open probe — a reachable "
        "source must be able to self-recover from an open breaker"
    )


# ══════════════════════════════════════════════════════════════════════════
# 10 — a skipped cycle must not be reported as the source's last check
# ══════════════════════════════════════════════════════════════════════════
def test_skipped_cycle_is_not_reported_as_the_last_check(trail, tmp_path, monkeypatch):
    """The CIRCUIT_OPEN trail record exists to prove the source was NOT seen.
    Surfacing it as the newest run makes the dashboard read "Last check 2
    minutes ago" for a source nothing has fetched in days."""
    import app.monitor as monitor
    from app.source_runs import latest_runs

    walled = _src("Chronically Walled", "https://walled.example/lastcheck")
    _isolate_breaker(monitor, tmp_path, monkeypatch, [walled])
    monkeypatch.setattr(monitor, "run_pipeline_for_source", _bot_walled)

    for _ in range(monitor._CIRCUIT_OPEN_THRESHOLD):
        monitor.monitor_all_sources(verbose=False)
    assert walled["url"] in monitor._circuit_open

    def _must_not_run(_src_):
        raise AssertionError("open circuit must skip the source, not fetch it")

    monkeypatch.setattr(monitor, "run_pipeline_for_source", _must_not_run)
    monitor.monitor_all_sources(verbose=False)

    codes = [str(r.get("failure_code") or "") for r in latest_runs().values()]
    assert "CIRCUIT_OPEN" in codes, "the skip record must stay in the trail"

    visible = latest_runs(include_skipped=False)
    assert visible, "the real (fetched) runs must still be reported"
    assert all(
        str(r.get("failure_code") or "") != "CIRCUIT_OPEN"
        and str(r.get("access_status") or "") != "circuit_open"
        for r in visible.values()
    ), "a cycle in which nothing was fetched must not be reported as a check"


# ══════════════════════════════════════════════════════════════════════════
# 11 — an UNRECOGNISED wall page must not be able to steer the breaker
# ══════════════════════════════════════════════════════════════════════════
def _unrecognised_wall(source):
    """A short block/maintenance page the marker guards do NOT recognise.

    'Access to this resource is restricted by the site administrator.' matches
    neither looks_like_error_page nor looks_like_bot_wall, so pipeline falls
    through to the content-shrink path and labels it alert_suppressed_reason
    ="content_shrink" — the same label a genuine live-page shrink gets. The
    ONLY thing separating them is how much content actually came back: 88 chars
    against a 4.2k baseline is not a page, it is a wall.
    """
    from app.source_runs import record_quality_drop

    record_quality_drop(
        source,
        reason="extracted content shrank to 88 chars (< 40% of previous 4200)",
        alert_suppressed_reason="content_shrink",
        observed_raw_chars=88,
        observed_normalized_chars=80,
        prev_raw_chars=4200,
        prev_normalized_chars=4100,
    )
    return {
        "source_name":  source["name"],
        "url":          source["url"],
        "changed":      False,
        "status":       "quality_drop",
        "shrink_suppressed": True,
        "alert_suppressed_reason": "content_shrink",
        "extracted_chars": 88,
        "extraction_quality": "failed",
    }


def test_unrecognised_wall_page_cannot_clear_the_breaker(trail, tmp_path, monkeypatch):
    """Remotely-supplied content must never reset a failure counter.

    Which guard a response lands in is decided entirely by the bytes the
    monitored host returns. If falling through to the shrink path counts as
    recovery, the host we are monitoring controls our own reliability control:
    it can hold the breaker permanently CLOSED by serving 88 chars of wall text
    on every half-open probe. That inverts the control.
    """
    import app.monitor as monitor

    walled = _src("Novel Wall", "https://walled.example/novel-clear")
    _isolate_breaker(monitor, tmp_path, monkeypatch, [walled])
    monkeypatch.setattr(monitor, "_circuit_open", {walled["url"]})
    monkeypatch.setattr(monitor, "run_pipeline_for_source", _unrecognised_wall)

    for _ in range(monitor._CIRCUIT_PROBE_EVERY_N_CYCLES + 2):
        monitor.monitor_all_sources(verbose=False)

    assert walled["url"] in monitor._circuit_open, (
        "a remote host serving a short unrecognised wall page must not be able "
        "to clear an open breaker"
    )


def test_unrecognised_wall_page_still_opens_the_breaker(trail, tmp_path, monkeypatch):
    """The chronic-darkness class the breaker exists to catch must trip it even
    when the wall text is novel enough to miss both marker guards (the DIFC
    incident: 87 chars the markers did not match)."""
    import app.monitor as monitor

    walled = _src("Novel Wall 2", "https://walled.example/novel-open")
    _isolate_breaker(monitor, tmp_path, monkeypatch, [walled])
    monkeypatch.setattr(monitor, "run_pipeline_for_source", _unrecognised_wall)

    for _ in range(monitor._CIRCUIT_OPEN_THRESHOLD):
        monitor.monitor_all_sources(verbose=False)

    assert walled["url"] in monitor._circuit_open, (
        "consecutive cycles behind an unrecognised wall are darkness — the "
        "breaker must open instead of re-probing the wall forever"
    )


def test_genuine_shrink_of_a_real_page_is_still_treated_as_reachable(
    trail, tmp_path, monkeypatch
):
    """The narrowing must not swallow the legitimate case: a page that still
    returns a plausible amount of content (900 chars) is demonstrably alive and
    its content genuinely changed — the HIGH-risk event the product exists to
    catch. It must never trip the breaker."""
    import app.monitor as monitor

    shrunk = _src("Real But Shrunk", "https://shrunk.example/still-alive")
    _isolate_breaker(monitor, tmp_path, monkeypatch, [shrunk])
    monkeypatch.setattr(monitor, "run_pipeline_for_source", _shrink_suppressed)

    for _ in range(monitor._CIRCUIT_OPEN_THRESHOLD + 3):
        monitor.monitor_all_sources(verbose=False)

    assert shrunk["url"] not in monitor._circuit_open


# ══════════════════════════════════════════════════════════════════════════
# 12 — the breaker must not feed on its OWN skip records
# ══════════════════════════════════════════════════════════════════════════
def test_circuit_open_skip_records_are_not_counted_as_failures(
    trail, tmp_path, monkeypatch
):
    """A CIRCUIT_OPEN record proves the source was NEVER CONTACTED. Counting it
    as consecutive evidence that the source is dark makes the breaker feed on
    its own output: the operator log reports an inflated 'consecutive unusable
    runs' count, and the documented 3-run threshold stops being what is
    enforced."""
    import app.monitor as monitor

    walled = _src("Chronically Walled", "https://walled.example/selfcount")
    _isolate_breaker(monitor, tmp_path, monkeypatch, [walled])
    monkeypatch.setattr(monitor, "run_pipeline_for_source", _bot_walled)

    for _ in range(monitor._CIRCUIT_OPEN_THRESHOLD):
        monitor.monitor_all_sources(verbose=False)
    assert walled["url"] in monitor._circuit_open
    fetched_failures = monitor._consecutive_failures(walled["url"])
    assert fetched_failures == monitor._CIRCUIT_OPEN_THRESHOLD

    def _must_not_run(_src_):
        raise AssertionError("open circuit must skip the source, not fetch it")

    monkeypatch.setattr(monitor, "run_pipeline_for_source", _must_not_run)
    for _ in range(4):
        monitor.monitor_all_sources(verbose=False)

    assert monitor._consecutive_failures(walled["url"]) == fetched_failures, (
        "cycles in which the source was never contacted must not be counted as "
        "consecutive evidence that the source is dark"
    )


# ══════════════════════════════════════════════════════════════════════════
# 13 — a skipped cycle must never be shown to a CUSTOMER as a check
# ══════════════════════════════════════════════════════════════════════════
def _open_breaker_then_skip_one_cycle(monitor, tmp_path, monkeypatch, source):
    """Drive one source into an open breaker, then run one SKIPPED cycle.
    Returns nothing; the trail under tmp_path holds both classes of record."""
    _isolate_breaker(monitor, tmp_path, monkeypatch, [source])
    monkeypatch.setattr(monitor, "run_pipeline_for_source", _bot_walled)
    for _ in range(monitor._CIRCUIT_OPEN_THRESHOLD):
        monitor.monitor_all_sources(verbose=False)
    assert source["url"] in monitor._circuit_open

    def _must_not_run(_src_):
        raise AssertionError("open circuit must skip the source, not fetch it")

    monkeypatch.setattr(monitor, "run_pipeline_for_source", _must_not_run)
    monitor.monitor_all_sources(verbose=False)


def test_skipped_cycle_is_not_shown_as_a_run_on_the_customer_timeline(
    trail, tmp_path, monkeypatch
):
    """GET /api/sources/timeline is the one artefact whose entire value is
    proving WHEN the product did and did not see a source. A skipped cycle
    rendered as 'MONITOR_RUN — Extraction quality changed' asserts both that a
    run happened and that an extraction happened and degraded. Neither is true:
    no request was issued."""
    import app.monitor as monitor
    from app.source_health_timeline import build_source_timeline
    from app.source_runs import make_source_id

    walled = _src("Chronically Walled", "https://walled.example/timeline")
    _open_breaker_then_skip_one_cycle(monitor, tmp_path, monkeypatch, walled)

    timeline = build_source_timeline(make_source_id(walled), base_dir=tmp_path)
    events = timeline["events"]
    assert events, "the timeline must still show the real (fetched) runs"

    skipped = [e for e in events if e.get("source_health_status") == "NOT_CHECKED"]
    assert skipped, "the skipped cycle must appear with its own honest state"
    for event in skipped:
        assert event["event_type"] != "MONITOR_RUN", (
            "a cycle in which no request was issued must not be presented as a "
            "monitoring run"
        )
        message = event["customer_safe_message"]
        assert "Extraction quality changed" not in message, (
            "nothing was extracted — the extraction-quality wording is a claim "
            f"the run cannot back: {message!r}"
        )
        assert "not fetched" in message.lower()


def test_skipped_cycle_does_not_enter_the_customer_review_queue(
    trail, tmp_path, monkeypatch
):
    """QUALITY_DROP records are retained for 30 days, so one chronically walled
    source at production cadence contributes ~600 phantom pending rows to the
    gate the product's own rules require a human to clear. A skip carries no
    hash and no diff — there is nothing to review."""
    import app.monitor as monitor
    from app.review_queue import build_review_queue

    walled = _src("Chronically Walled", "https://walled.example/queue")
    _open_breaker_then_skip_one_cycle(monitor, tmp_path, monkeypatch, walled)

    queue = build_review_queue(market="AE", status="pending", base_dir=tmp_path)
    assert queue["queue"], "real quality drops must still be reviewable"
    for row in queue["queue"]:
        assert "not fetched" not in str(row.get("customer_safe_message") or "").lower()
    assert all(
        "CIRCUIT_OPEN" not in str(row.get("blocked_reason") or "") for row in queue["queue"]
    )
    # The skip record itself must not be a pending review item.
    run_file = tmp_path / "data" / "source_runs" / "source_runs.jsonl"
    import json as _json
    skip_ids = {
        _json.loads(line)["run_id"]
        for line in run_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and _json.loads(line).get("failure_code") == "CIRCUIT_OPEN"
    }
    assert skip_ids, "the skip record must stay in the trail"
    queued_ids = {row["evidence_record_id"] for row in queue["queue"]}
    assert not (skip_ids & queued_ids), (
        "a cycle we deliberately skipped must not be queued for human review as "
        "though it were a failed extraction"
    )


def test_evidence_listing_labels_a_skipped_cycle_as_not_fetched(
    trail, tmp_path, monkeypatch
):
    """GET /api/evidence lists every trail record. A skip appears as an evidence
    row with extraction_quality FAILED and no hash, and the payload omitted the
    one field (limitations_notes) that says the source was not fetched — so the
    explanation never reached the customer."""
    from io import BytesIO
    from unittest.mock import MagicMock

    import app.api as api
    import app.monitor as monitor

    walled = _src("Chronically Walled", "https://walled.example/evidence")
    _open_breaker_then_skip_one_cycle(monitor, tmp_path, monkeypatch, walled)

    monkeypatch.setattr(api, "BASE_DIR", tmp_path)
    monkeypatch.setattr(api, "require_auth", lambda handler: {"id": 1, "email": "u@x.io"})

    handler = api._Handler.__new__(api._Handler)
    handler.command = "GET"
    handler.path = "/api/evidence?market=AE"
    handler.request = MagicMock()
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(b"")
    handler.wfile = BytesIO()
    handler.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": {"Content-Length": "0"}.get(key, default)
    handler.headers = hdrs
    sent: list = []
    handler._send_json = lambda data, status=200, **kw: sent.append((data, status))
    handler._rate_limited = lambda *_a, **_k: False
    handler._denied_custom_source_ids = lambda _user: set()

    handler._handle_evidence_list()
    payload = sent[-1][0]
    rows = payload["evidence"]
    skips = [r for r in rows if r.get("not_fetched_this_cycle")]
    assert skips, (
        "a cycle in which nothing was fetched must be flagged as such, not "
        "listed as an ordinary failed-extraction evidence row"
    )
    for row in skips:
        assert "not fetched" in str(row.get("limitations_notes") or "").lower()
