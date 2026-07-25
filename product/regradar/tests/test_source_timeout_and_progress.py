"""One hung source must cost one source, not the whole sweep.

`monitor_all_sources` iterates sources and calls `run_pipeline_for_source` with a
2-attempt retry and no wall-clock cap. A source that never returns — a Playwright
navigation that hangs rather than erroring — therefore stopped the entire sweep,
and systemd saw a process that was still alive, so `Restart=on-failure` never
fired. Monitoring was silently dead for four days in exactly this way.

Measured with tools/measure_reliability_axis.py before this landed: the second of
two sources was never reached. After: reached, in 2s against a 30s hang, with the
first recorded as a timeout.

Two mechanisms are tested here and they answer different questions:
the CAP keeps the sweep moving; the PROGRESS MARKER lets an outside watchdog tell
"working slowly" from "stopped", which a heartbeat alone cannot.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.monitor as monitor  # noqa: E402
import app.ops_alert as ops_alert  # noqa: E402
import app.scheduler as scheduler  # noqa: E402

CAP_S = 1.0
HANG_S = 20.0


def _source(name: str, url: str) -> dict:
    return {
        "id": name, "source_id": name, "name": name, "url": url,
        "jurisdiction": "AE", "category": "financial_regulator", "enabled": True,
    }


@pytest.fixture()
def isolated_sweep(tmp_path, monkeypatch):
    """A sweep that writes nowhere real and loads only the sources we give it."""
    import app.source_runs as source_runs

    monkeypatch.setattr(source_runs, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(source_runs, "_RUN_DIR", tmp_path / "data" / "source_runs")
    monkeypatch.setattr(source_runs, "_RUN_FILE", tmp_path / "data" / "source_runs" / "runs.jsonl")
    monkeypatch.setattr(source_runs, "_SNAPSHOT_DIR", tmp_path / "data" / "snapshots")
    monkeypatch.setattr(scheduler, "_PROGRESS_FILE", tmp_path / "progress.json")
    monkeypatch.setattr(ops_alert, "_PROGRESS_FILE", tmp_path / "progress.json")
    # The real teardown closes a shared browser; irrelevant here and slow.
    monkeypatch.setattr(scheduler, "_recover_after_source_timeout", lambda _label: None)
    # Abandonment raises, so monitor.py's retry policy applies: without this the
    # suite would sleep the real 5s between attempts for every hung-source test.
    monkeypatch.setattr(monitor, "_RETRY_DELAY_SECONDS", 0)
    source_runs._CACHE_VALID = False
    source_runs._RUNS_CACHE = None
    return tmp_path


# ── the cap ─────────────────────────────────────────────────────────────────


def test_a_hung_source_does_not_stop_the_sweep(isolated_sweep, monkeypatch):
    hung, healthy = _source("Hangs", "https://hang.example"), _source("Healthy", "https://ok.example")
    reached: list[str] = []

    def _pipeline(source):
        reached.append(source["url"])
        if source["url"] == hung["url"]:
            time.sleep(HANG_S)
        return {"url": source["url"], "status": "ok", "extracted_text": "x" * 900,
                "extracted_chars": 900, "fetch_method": "test", "reason": ""}

    monkeypatch.setattr(monitor, "get_enabled_sources", lambda *a, **k: [hung, healthy])
    monkeypatch.setattr(monitor, "run_pipeline_for_source", _pipeline)

    started = time.monotonic()
    with scheduler.per_source_timeout(timeout_s=CAP_S):
        results = monitor.monitor_all_sources(verbose=False)
    elapsed = time.monotonic() - started

    assert healthy["url"] in reached, "source 2 was never reached — the sweep wedged"
    assert elapsed < HANG_S / 2, f"the sweep waited {elapsed:.1f}s on a {HANG_S}s hang"
    assert len(results) == 2


def test_the_abandoned_source_leaves_a_durable_failure_not_silence(isolated_sweep, monkeypatch):
    """A source that stops being checked must look WORSE than one that fails.

    The in-memory result is the easy half. The half that actually matters is the
    TRAIL record: without it the run history reads as though the source was fine
    and the circuit breaker never learns that this source hangs every sweep. An
    earlier version of this returned a synthetic error dict, which satisfied the
    first two assertions and failed the third.
    """
    hung = _source("Hangs", "https://hang.example")

    monkeypatch.setattr(monitor, "get_enabled_sources", lambda *a, **k: [hung])
    monkeypatch.setattr(monitor, "run_pipeline_for_source", lambda s: time.sleep(HANG_S))

    with scheduler.per_source_timeout(timeout_s=CAP_S):
        results = monitor.monitor_all_sources(verbose=False)

    assert results[0]["status"] == "error"
    assert results[0]["access_status"] == "timeout"
    assert monitor._consecutive_failures(hung["url"]) >= 1, (
        "the abandoned source left no durable FAILED trail record — "
        "the breaker cannot see it"
    )


def test_abandonment_is_classified_as_a_timeout_not_a_generic_error(isolated_sweep):
    """monitor._classify_access_status reads str(exc), not the exception type.

    If the message ever stops saying "timeout", the trail silently starts
    recording these as access_status "error" and the distinction between "the
    regulator refused us" and "we gave up" is lost.
    """
    with pytest.raises(TimeoutError) as caught:
        scheduler.run_source_with_timeout(
            lambda _s: time.sleep(HANG_S), _source("X", "https://x.example"), CAP_S
        )

    assert monitor._classify_access_status(caught.value) == "timeout"


def test_a_healthy_source_is_untouched_by_the_cap(isolated_sweep, monkeypatch):
    healthy = _source("Healthy", "https://ok.example")
    monkeypatch.setattr(monitor, "get_enabled_sources", lambda *a, **k: [healthy])
    monkeypatch.setattr(
        monitor, "run_pipeline_for_source",
        lambda s: {"url": s["url"], "status": "ok", "extracted_text": "x" * 900,
                   "extracted_chars": 900, "fetch_method": "test", "reason": ""},
    )

    with scheduler.per_source_timeout(timeout_s=CAP_S):
        results = monitor.monitor_all_sources(verbose=False)

    assert results[0]["status"] == "ok"
    assert results[0].get("timed_out") is None


def test_the_original_runner_is_restored_even_when_the_body_raises():
    """A leaked wrapper would cap every later caller, including tests."""
    original = monitor.run_pipeline_for_source
    with pytest.raises(RuntimeError):
        with scheduler.per_source_timeout(timeout_s=CAP_S):
            raise RuntimeError("boom")
    assert monitor.run_pipeline_for_source is original


def test_a_raising_source_still_raises_through_the_cap(isolated_sweep, monkeypatch):
    """The cap must not swallow a real error into a fake timeout."""
    def _boom(_source):
        raise ValueError("the source blew up")

    with scheduler.per_source_timeout(timeout_s=CAP_S):
        with pytest.raises(ValueError, match="blew up"):
            scheduler.run_source_with_timeout(_boom, _source("X", "https://x.example"), CAP_S)


# ── the cap's size ──────────────────────────────────────────────────────────


def test_the_cap_exceeds_what_a_slow_but_healthy_source_may_take():
    """A cap below the fetch timeouts would sever healthy sources and fill the
    trail with failures that look like the regulator's fault.

    The cap is PER ATTEMPT — it wraps run_pipeline_for_source, which monitor.py
    calls once per retry — so it is one attempt's budget that must clear the
    fetch timeouts, and the whole-source budget is twice that.
    """
    from app.config import HTTP_TIMEOUT_S, PAGE_TIMEOUT_MS

    one_attempt = HTTP_TIMEOUT_S + PAGE_TIMEOUT_MS / 1000.0
    derived = scheduler._derived_source_timeout_seconds()

    assert derived > one_attempt, "a single slow-but-healthy fetch would be severed"
    assert derived * 2 > one_attempt * 2


def test_an_override_below_the_floor_is_clamped(monkeypatch):
    monkeypatch.setenv("STATUTEPROOF_SOURCE_TIMEOUT_S", "5")
    assert scheduler.source_timeout_seconds() == scheduler._derived_source_timeout_seconds()


def test_a_larger_override_is_honoured(monkeypatch):
    monkeypatch.setenv("STATUTEPROOF_SOURCE_TIMEOUT_S", "9999")
    assert scheduler.source_timeout_seconds() == 9999


def test_a_nonsense_override_falls_back_rather_than_crashing(monkeypatch):
    monkeypatch.setenv("STATUTEPROOF_SOURCE_TIMEOUT_S", "soon")
    assert scheduler.source_timeout_seconds() == scheduler._derived_source_timeout_seconds()


# ── the progress marker ─────────────────────────────────────────────────────


def test_progress_advances_for_every_source_the_sweep_starts(isolated_sweep, monkeypatch):
    a, b = _source("A", "https://a.example"), _source("B", "https://b.example")
    monkeypatch.setattr(monitor, "get_enabled_sources", lambda *a_, **k: [a, b])
    monkeypatch.setattr(
        monitor, "run_pipeline_for_source",
        lambda s: {"url": s["url"], "status": "ok", "extracted_text": "x" * 900,
                   "extracted_chars": 900, "fetch_method": "test", "reason": ""},
    )

    with scheduler.per_source_timeout(timeout_s=CAP_S):
        monitor.monitor_all_sources(verbose=False)

    progress = ops_alert.read_progress()
    assert progress["index"] == 2
    assert progress["label"] == "B"


def test_progress_is_recorded_before_a_source_hangs(isolated_sweep, monkeypatch):
    """The case the marker exists for: a frozen marker on the PREVIOUS source
    would make a hang look exactly like a stop."""
    hung = _source("Hangs", "https://hang.example")
    monkeypatch.setattr(monitor, "get_enabled_sources", lambda *a, **k: [hung])
    monkeypatch.setattr(monitor, "run_pipeline_for_source", lambda s: time.sleep(HANG_S))

    with scheduler.per_source_timeout(timeout_s=CAP_S):
        monitor.monitor_all_sources(verbose=False)

    assert ops_alert.read_progress()["label"] == "Hangs"


def test_a_retry_does_not_advance_the_progress_counter(isolated_sweep, monkeypatch):
    """monitor.py calls the wrapper again on retry. Counting attempts would report
    a 140-source sweep as being on source 200, and a watchdog reading that cannot
    tell real progress from one source failing twice."""
    flaky, healthy = _source("Flaky", "https://flaky.example"), _source("B", "https://b.example")
    calls: list[str] = []

    def _pipeline(source):
        calls.append(source["url"])
        if source["url"] == flaky["url"] and calls.count(flaky["url"]) == 1:
            raise ValueError("transient")
        return {"url": source["url"], "status": "ok", "extracted_text": "x" * 900,
                "extracted_chars": 900, "fetch_method": "test", "reason": ""}

    monkeypatch.setattr(monitor, "get_enabled_sources", lambda *a, **k: [flaky, healthy])
    monkeypatch.setattr(monitor, "run_pipeline_for_source", _pipeline)

    with scheduler.per_source_timeout(timeout_s=CAP_S):
        monitor.monitor_all_sources(verbose=False)

    assert calls.count(flaky["url"]) == 2, "the retry did not happen — test is vacuous"
    assert ops_alert.read_progress()["index"] == 2


def test_an_unknown_total_is_not_rendered_as_a_wrong_denominator(isolated_sweep):
    scheduler.record_progress(3, 0, "Some Source")
    assert "/0" not in ops_alert.describe_progress()
    assert "source 3" in ops_alert.describe_progress()


def test_a_missing_marker_reads_as_missing_not_as_zero(isolated_sweep):
    assert ops_alert.read_progress() is None
    assert ops_alert.describe_progress() == "no progress marker"


# ── heartbeat state, without paging anyone ──────────────────────────────────


def test_heartbeat_state_never_notifies(isolated_sweep, monkeypatch):
    """It is called on a timer; a status read that pages the founder is a bug."""
    paged: list[str] = []
    monkeypatch.setattr(ops_alert, "notify_founder", lambda text: paged.append(text) or True)
    monkeypatch.setattr(ops_alert, "ping_external_heartbeat", lambda: paged.append("ping") or True)

    ops_alert.heartbeat_state()

    assert paged == []


def test_a_stale_heartbeat_with_a_moving_sweep_reads_as_working(isolated_sweep, monkeypatch):
    """Restarting a long-but-advancing sweep would abort real work."""
    heartbeat = isolated_sweep / "monitor_heartbeat"
    heartbeat.write_text("x", encoding="utf-8")
    monkeypatch.setattr(ops_alert, "_HEARTBEAT_FILE", heartbeat)
    monkeypatch.setattr(ops_alert, "_heartbeat_stale_seconds", lambda: 60)
    # The marker must be fresh RELATIVE TO the reference time, or this models a
    # stalled sweep rather than a slow one — which is the other test below.
    reference = time.time() + 600
    recent = datetime.fromtimestamp(reference - 10, tz=timezone.utc).isoformat(timespec="seconds")
    (isolated_sweep / "progress.json").write_text(
        f'{{"index": 7, "total": 0, "label": "Still Going", "at": "{recent}"}}', encoding="utf-8",
    )

    state = ops_alert.heartbeat_state(now=reference)

    assert state["state"] == "working"
    assert state["ok"] is True


def test_a_stale_heartbeat_with_a_stale_sweep_reads_as_stale(isolated_sweep, monkeypatch):
    heartbeat = isolated_sweep / "monitor_heartbeat"
    heartbeat.write_text("x", encoding="utf-8")
    monkeypatch.setattr(ops_alert, "_HEARTBEAT_FILE", heartbeat)
    monkeypatch.setattr(ops_alert, "_heartbeat_stale_seconds", lambda: 60)
    old = (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat(timespec="seconds")
    (isolated_sweep / "progress.json").write_text(
        f'{{"index": 7, "total": 0, "label": "Stuck", "at": "{old}"}}', encoding="utf-8",
    )

    state = ops_alert.heartbeat_state(now=time.time() + 600)

    assert state["state"] == "stale"
    assert state["ok"] is False


def test_a_missing_heartbeat_reads_as_missing(isolated_sweep, monkeypatch):
    monkeypatch.setattr(ops_alert, "_HEARTBEAT_FILE", isolated_sweep / "nope")

    state = ops_alert.heartbeat_state()

    assert state["state"] == "missing"
    assert state["ok"] is False
