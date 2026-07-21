"""Sub-cycle resilience regression tests.

Before the fix, the scheduler critical/per-cadence *sub-cycle* called
``run_pipeline_for_source`` directly in a bare ``try/except`` that only fed a
printed summary. When a source raised:

  * NO durable FAILED trail record was written,
  * ``_consecutive_failures`` never saw the failure,
  * ``_maybe_open_circuit`` never fired, and
  * an already-OPEN circuit was re-probed on every sub-cycle tick.

The full-cycle path (``monitor_all_sources``) already wrapped each source with
circuit-breaker skip, a 2-attempt retry, a durable FAILED/QUALITY_DROP trail
record, and a breaker open/clear. The fix extracts that per-source body into the
shared ``_run_one_source`` helper and routes BOTH the full cycle and the
scheduler sub-cycle through it.

These tests pin:
  (a) a raising source routed through ``_run_one_source`` (what the sub-cycle
      now calls) writes a durable FAILED record, increments the
      consecutive-failure count, and opens the breaker;
  (b) an OPEN-circuit source is SKIPPED via ``_persist_circuit_open_record``
      and never fetched;
  (c) the actual scheduler sub-cycle writes a durable FAILED record for a
      raising source (integration through ``run_watch_loop``);
  (d) the full-cycle behaviour is unchanged after the extraction.
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


def _isolate_circuit(monitor, tmp_path, monkeypatch):
    """Isolate breaker state + neutralise the retry sleep."""
    monkeypatch.setattr(monitor.time, "sleep", lambda *_a, **_k: None)
    monkeypatch.setattr(monitor, "_CIRCUIT_STATE_FILE", tmp_path / "circuit_state.json")
    monkeypatch.setattr(monitor, "_circuit_open", set())
    monkeypatch.setattr(monitor, "_circuit_skip_counts", {})


def _isolate_full_cycle(monitor, tmp_path, monkeypatch, sources):
    """Full-cycle isolation, mirroring tests/test_monitor_circuit.py."""
    _isolate_circuit(monitor, tmp_path, monkeypatch)
    monkeypatch.setattr(monitor, "get_enabled_sources", lambda: sources)
    monkeypatch.setattr(monitor, "init_pipeline", lambda *_a, **_k: None)
    # Ops-state isolation: an all-fail cycle satisfies _is_catastrophic_cycle,
    # which would otherwise rewrite the REAL deadman state and POST a founder
    # Telegram alert. Same convention as tests/test_monitor_circuit.py.
    monkeypatch.setattr(monitor, "_DEADMAN_STATE_FILE", tmp_path / "deadman_state.json")
    monkeypatch.setattr(
        monitor, "_SEAL_DEADMAN_STATE_FILE", tmp_path / "seal_deadman_state.json"
    )
    monkeypatch.setattr(monitor, "_maybe_alert_catastrophic_cycle", lambda *_a, **_k: None)
    monkeypatch.setattr(monitor, "_maybe_alert_seal_failures", lambda *_a, **_k: None)


def _src(name, url):
    return {
        "name": name, "url": url, "jurisdiction": "AE",
        "category": "banking", "status": "active", "enabled": True,
    }


def _raise(_source):
    raise RuntimeError("boom fetch")


# ══════════════════════════════════════════════════════════════════════════
# (a) a raising source through _run_one_source leaves a durable FAILED trail
#     record, counts toward the failure counter, and opens the breaker.
# ══════════════════════════════════════════════════════════════════════════
def test_run_one_source_raising_writes_durable_failed_and_opens_breaker(
    trail, tmp_path, monkeypatch
):
    import app.monitor as monitor

    src = _src("Sub Raiser", "https://raise.example/regs")
    _isolate_circuit(monitor, tmp_path, monkeypatch)
    monkeypatch.setattr(monitor, "run_pipeline_for_source", _raise)

    counter = monitor._new_cycle_counter()
    for _ in range(monitor._CIRCUIT_OPEN_THRESHOLD):
        res = monitor._run_one_source(src, 1, 1, False, counter)
        assert res["status"] == "error"
        assert res["url"] == src["url"]

    # The bare sub-cycle loop wrote NO trail record; the shared helper does.
    assert monitor._consecutive_failures(src["url"]) >= monitor._CIRCUIT_OPEN_THRESHOLD, (
        "a raising source must leave a durable FAILED trail record the "
        "consecutive-failure counter can see"
    )
    assert src["url"] in monitor._circuit_open, (
        "repeated raises must open the breaker in the sub-cycle path"
    )
    assert counter["failed"] == monitor._CIRCUIT_OPEN_THRESHOLD


# ══════════════════════════════════════════════════════════════════════════
# (b) an OPEN-circuit source is SKIPPED with a durable circuit-open record and
#     is never fetched.
# ══════════════════════════════════════════════════════════════════════════
def test_run_one_source_open_circuit_is_skipped_and_persisted(
    trail, tmp_path, monkeypatch
):
    import app.monitor as monitor

    src = _src("Open Circuit Source", "https://open.example/regs")
    _isolate_circuit(monitor, tmp_path, monkeypatch)
    monkeypatch.setattr(monitor, "_circuit_open", {src["url"]})
    monkeypatch.setattr(monitor, "_circuit_skip_counts", {})

    persisted: list[dict] = []
    monkeypatch.setattr(
        monitor, "_persist_circuit_open_record", lambda s: persisted.append(s)
    )

    def _must_not_run(_s):
        raise AssertionError("an OPEN circuit must skip the source, not fetch it")

    monkeypatch.setattr(monitor, "run_pipeline_for_source", _must_not_run)

    counter = monitor._new_cycle_counter()
    res = monitor._run_one_source(src, 1, 1, False, counter)

    assert res.get("circuit_open") is True
    assert res["access_status"] == "circuit_open"
    assert len(persisted) == 1, (
        "the sub-cycle must write a durable circuit-open record when skipping"
    )
    assert counter["failed"] == 1


# ══════════════════════════════════════════════════════════════════════════
# (c) integration: the actual scheduler sub-cycle writes a durable FAILED
#     record for a raising critical source (drives run_watch_loop).
# ══════════════════════════════════════════════════════════════════════════
def test_scheduler_sub_cycle_writes_durable_failed_record(
    trail, tmp_path, monkeypatch
):
    import app.monitor as monitor
    import app.scheduler as scheduler

    _isolate_circuit(monitor, tmp_path, monkeypatch)

    raiser = _src("Critical Raiser", "https://subraise.example/regs")
    monkeypatch.setattr(monitor, "run_pipeline_for_source", _raise)

    # Full cycle is a no-op so ONLY the sub-cycle touches our source; the
    # source is critical so the sub-cycle branch picks it up.
    monkeypatch.setattr(scheduler, "monitor_all_sources", lambda **_k: [])
    monkeypatch.setattr(
        scheduler, "get_sources_by_priority",
        lambda p: [raiser] if p == "critical" else [],
    )
    monkeypatch.setattr(scheduler, "get_sources_with_custom_interval", lambda: [])
    monkeypatch.setattr(scheduler, "write_heartbeat", lambda *_a, **_k: True)
    monkeypatch.setattr(scheduler, "_log_priority_summary", lambda: None)
    monkeypatch.setattr(
        scheduler, "run_deadline_reminder_pass", lambda *_a, **_k: {"sent": []}
    )
    monkeypatch.setattr(scheduler, "run_digest_dispatch_pass", lambda *_a, **_k: {})

    # NOTE: monitor and scheduler share the same `time` module object, so the
    # in-loop cadence sleep and _run_one_source's 5s retry sleep hit the SAME
    # patched function. Gate on duration: swallow the short retry sleep (so the
    # sub-cycle can finish and write its FAILED record) and only count the long
    # cadence sleep. Iteration 1 = full cycle -> cadence sleep (count 1);
    # iteration 2 = sub-cycle -> cadence sleep (count 2) ends the loop.
    _RETRY_CEILING_SECONDS = 60
    calls = {"n": 0}

    def _sleep(secs):
        if secs and secs >= _RETRY_CEILING_SECONDS:
            calls["n"] += 1
            if calls["n"] >= 2:
                raise KeyboardInterrupt

    monkeypatch.setattr(scheduler.time, "sleep", _sleep)

    scheduler.run_watch_loop(interval_minutes=60)

    assert monitor._consecutive_failures(raiser["url"]) >= 1, (
        "the scheduler sub-cycle must write a durable FAILED trail record for "
        "a raising source (the old bare loop wrote none)"
    )


# ══════════════════════════════════════════════════════════════════════════
# (d) the full-cycle behaviour is unchanged after the extraction.
# ══════════════════════════════════════════════════════════════════════════
def test_full_cycle_behavior_unchanged(trail, tmp_path, monkeypatch):
    import app.monitor as monitor

    raiser = _src("Full-Cycle Raiser", "https://fullraise.example/regs")
    _isolate_full_cycle(monitor, tmp_path, monkeypatch, [raiser])
    monkeypatch.setattr(monitor, "run_pipeline_for_source", _raise)

    for _ in range(monitor._CIRCUIT_OPEN_THRESHOLD):
        results = monitor.monitor_all_sources(verbose=False)
        assert len(results) == 1
        assert results[0]["status"] == "error"
        assert results[0]["url"] == raiser["url"]

    assert monitor._consecutive_failures(raiser["url"]) >= monitor._CIRCUIT_OPEN_THRESHOLD
    assert raiser["url"] in monitor._circuit_open

    # Once open, the next full cycle SKIPS the source instead of re-probing.
    def _must_not_run(_s):
        raise AssertionError("open circuit must skip the source, not fetch it")

    monkeypatch.setattr(monitor, "run_pipeline_for_source", _must_not_run)
    results = monitor.monitor_all_sources(verbose=False)
    assert results[0].get("circuit_open") is True
