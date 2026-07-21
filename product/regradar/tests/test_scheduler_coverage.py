"""Behavioral coverage for app/scheduler.py — the watch-mode core loop.

These tests exercise logic that was previously uncovered:

* ``get_sources_by_priority`` — priority filtering + error handling when
  sources.json is missing / not a list / has junk entries.
* ``_print_cycle_summary`` / ``_print_cycle_header`` — the per-source status
  classification and the aggregate count line (asserted on captured stdout).
* ``run_digest_dispatch_pass`` / ``run_deadline_reminder_pass`` — best-effort
  wrappers must never raise and must surface the delegate's result.
* ``run_watch_loop`` — orchestrator-level error recovery (a broken full cycle
  never kills the loop) and, most importantly, per-source error isolation in
  the critical sub-cycle (one failing source must not abort the sweep).

All network / pipeline / digest / telegram I/O is mocked — nothing here hits a
live endpoint. The loop is broken deterministically by raising
KeyboardInterrupt from a patched ``time.sleep``.
"""
from __future__ import annotations

import json

import pytest

import app.scheduler as scheduler


# ── get_sources_by_priority ──────────────────────────────────────────────────

def _write_sources(tmp_path, data):
    path = tmp_path / "sources.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_priority_filter_matches_requested_tier(tmp_path, monkeypatch):
    data = [
        {"enabled": True, "monitoring_priority": "critical", "name": "A"},
        {"enabled": True, "monitoring_priority": "standard", "name": "B"},
        {"enabled": True, "monitoring_priority": "critical", "name": "C"},
    ]
    monkeypatch.setattr(scheduler, "_SOURCES_JSON", _write_sources(tmp_path, data))

    matched = scheduler.get_sources_by_priority("critical")

    assert [s["name"] for s in matched] == ["A", "C"]


def test_priority_defaults_missing_field_to_standard(tmp_path, monkeypatch):
    data = [
        {"enabled": True, "name": "no-field"},          # implicit standard
        {"enabled": True, "monitoring_priority": "standard", "name": "explicit"},
    ]
    monkeypatch.setattr(scheduler, "_SOURCES_JSON", _write_sources(tmp_path, data))

    matched = scheduler.get_sources_by_priority("standard")

    assert {s["name"] for s in matched} == {"no-field", "explicit"}


def test_priority_excludes_disabled_and_non_dict(tmp_path, monkeypatch):
    data = [
        {"enabled": False, "monitoring_priority": "critical", "name": "off"},
        "junk-string",
        {"enabled": True, "monitoring_priority": "critical", "name": "on"},
    ]
    monkeypatch.setattr(scheduler, "_SOURCES_JSON", _write_sources(tmp_path, data))

    matched = scheduler.get_sources_by_priority("critical")

    assert [s["name"] for s in matched] == ["on"]


def test_priority_missing_file_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(scheduler, "_SOURCES_JSON", tmp_path / "absent.json")

    assert scheduler.get_sources_by_priority("critical") == []


def test_priority_non_list_json_returns_empty(tmp_path, monkeypatch):
    path = tmp_path / "sources.json"
    path.write_text(json.dumps({"not": "a list"}), encoding="utf-8")
    monkeypatch.setattr(scheduler, "_SOURCES_JSON", path)

    assert scheduler.get_sources_by_priority("standard") == []


def test_log_priority_summary_runs(tmp_path, monkeypatch):
    """_log_priority_summary must iterate every tier without raising even when
    a tier has enabled sources (exercises the info-log branch)."""
    data = [{"enabled": True, "monitoring_priority": "critical", "name": "X"}]
    monkeypatch.setattr(scheduler, "_SOURCES_JSON", _write_sources(tmp_path, data))

    # Returns None; the assertion is that it completes without raising.
    assert scheduler._log_priority_summary() is None


# ── _print_cycle_header ──────────────────────────────────────────────────────

def test_cycle_header_shows_number_and_plural_interval(capsys):
    scheduler._print_cycle_header(3, 60)
    out = capsys.readouterr().out
    assert "watch cycle #3" in out
    assert "60 minutes" in out


def test_cycle_header_singular_interval(capsys):
    scheduler._print_cycle_header(1, 1)
    out = capsys.readouterr().out
    assert "1 minute" in out
    assert "1 minutes" not in out


# ── _print_cycle_summary ─────────────────────────────────────────────────────

def test_summary_empty_results_prints_placeholder(capsys):
    scheduler._print_cycle_summary([])
    assert "No results returned" in capsys.readouterr().out


def test_summary_classifies_each_status_and_aggregates(capsys):
    results = [
        {"source_name": "err-src", "status": "error"},
        {"source_name": "same-src", "changed": False, "extraction_quality": "good",
         "extracted_chars": 1234},
        {"source_name": "new-src", "changed": True, "is_new": True},
        {"source_name": "chg-src", "changed": True, "is_new": False,
         "risk_level": "HIGH", "added_count": 4, "removed_count": 1,
         "extraction_quality": "low_content", "source_status": "limited"},
    ]

    scheduler._print_cycle_summary(results)
    out = capsys.readouterr().out

    # Per-source classification landed.
    assert "error" in out
    assert "unchanged" in out
    assert "baseline" in out
    assert "changed" in out
    assert "HIGH" in out
    assert "[limited]" in out

    # Aggregate footer counts are computed from the results, not hardcoded.
    assert "Total: 4" in out
    assert "high-risk: 1" in out
    assert "low-content: 1" in out
    assert "errors: 1" in out
    # 3 of 4 are not error status.
    assert "ok: 3" in out
    # Exactly one changed-not-new and one new.
    assert "changed: 1" in out
    assert "new: 1" in out


# ── best-effort dispatch wrappers ────────────────────────────────────────────

def test_digest_dispatch_passes_through_delegate_result(monkeypatch):
    import app.digest_cadence as dc
    monkeypatch.setattr(
        dc, "run_scheduled_digests",
        lambda: {"digests_sent": 2, "heartbeats_sent": 1, "instant_sent": 3},
    )

    result = scheduler.run_digest_dispatch_pass()

    assert result["digests_sent"] == 2
    assert result["instant_sent"] == 3


def test_digest_dispatch_never_raises_on_delegate_failure(monkeypatch):
    import app.digest_cadence as dc

    def _boom():
        raise RuntimeError("delegate exploded")

    monkeypatch.setattr(dc, "run_scheduled_digests", _boom)

    result = scheduler.run_digest_dispatch_pass()

    assert result["status"] == "error"
    assert "delegate exploded" in result["error"]


def test_deadline_pass_passes_through_and_forwards_base_dir(monkeypatch, tmp_path):
    import app.deadline_radar as dr
    seen = {}

    def _fake(base_dir=None):
        seen["base_dir"] = base_dir
        return {"status": "ok", "sent": ["30-day"]}

    monkeypatch.setattr(dr, "send_due_reminders", _fake)

    result = scheduler.run_deadline_reminder_pass(base_dir=tmp_path)

    assert result["sent"] == ["30-day"]
    assert seen["base_dir"] == tmp_path


def test_deadline_pass_never_raises_on_delegate_failure(monkeypatch):
    import app.deadline_radar as dr

    def _boom(base_dir=None):
        raise ValueError("radar down")

    monkeypatch.setattr(dr, "send_due_reminders", _boom)

    result = scheduler.run_deadline_reminder_pass()

    assert result["status"] == "error"
    assert "radar down" in result["error"]


# ── run_watch_loop — shared harness ──────────────────────────────────────────

def _quiet_loop_env(monkeypatch, tmp_path):
    """Silence side-channels of a full cycle so tests can assert the branch
    under test. Returns nothing; callers patch what they need on top."""
    monkeypatch.setattr(scheduler, "_HEARTBEAT_FILE", tmp_path / "data" / "hb")
    monkeypatch.setattr(scheduler, "_log_priority_summary", lambda: None)
    monkeypatch.setattr(scheduler, "_print_cycle_header", lambda *_a, **_k: None)
    monkeypatch.setattr(scheduler, "run_deadline_reminder_pass", lambda *_a, **_k: {})
    monkeypatch.setattr(scheduler, "run_digest_dispatch_pass", lambda *_a, **_k: {})


def test_full_cycle_orchestrator_error_recovers(tmp_path, monkeypatch, capsys):
    """A full cycle that raises at the orchestrator level must be caught,
    logged, and recovered from — the loop must not die."""
    _quiet_loop_env(monkeypatch, tmp_path)
    monkeypatch.setattr(scheduler, "get_sources_by_priority", lambda _p: [])
    monkeypatch.setattr(scheduler, "get_sources_with_custom_interval", lambda: [])
    monkeypatch.setattr(scheduler, "_print_cycle_summary", lambda *_a, **_k: None)

    def _monitor(**_k):
        raise RuntimeError("orchestrator boom")

    monkeypatch.setattr(scheduler, "monitor_all_sources", _monitor)

    # Let the 30s recovery sleep pass; break on the next (bottom-of-loop) sleep.
    sleeps = {"n": 0}

    def _sleep(*_a, **_k):
        sleeps["n"] += 1
        if sleeps["n"] >= 2:
            raise KeyboardInterrupt

    monkeypatch.setattr(scheduler.time, "sleep", _sleep)

    scheduler.run_watch_loop(interval_minutes=60)  # returns cleanly on Ctrl+C

    out = capsys.readouterr().out
    assert "unexpected error" in out
    assert "Recovering" in out
    # Both the recovery sleep(30) and the normal bottom sleep ran → recovered.
    assert sleeps["n"] == 2


def test_subcycle_isolates_one_failing_source(tmp_path, monkeypatch):
    """Core reliability guarantee: in the critical sub-cycle a single source
    that raises must NOT abort the sweep — the remaining sources still run and
    the failure is recorded as an error result, not propagated.

    The sub-cycle now routes each source through monitor._run_one_source (the
    same helper the full cycle uses), so the failing source is retried once and
    recorded as a durable error result before the sweep moves on to the next."""
    import app.monitor as monitor
    import app.source_runs as sr

    _quiet_loop_env(monkeypatch, tmp_path)

    # Isolate the breaker + run trail so the helper's durable FAILED record and
    # circuit state stay hermetic (never touch real data).
    monkeypatch.setattr(monitor, "_CIRCUIT_STATE_FILE", tmp_path / "circuit_state.json")
    monkeypatch.setattr(monitor, "_circuit_open", set())
    monkeypatch.setattr(monitor, "_circuit_skip_counts", {})
    run_dir = tmp_path / "data" / "source_runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(sr, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(sr, "_RUN_DIR", run_dir)
    monkeypatch.setattr(sr, "_RUN_FILE", run_dir / "source_runs.jsonl")
    monkeypatch.setattr(sr, "_SNAPSHOT_DIR", tmp_path / "data" / "source_snapshots")
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None

    src_bad = {"name": "bad", "url": "https://x/bad", "jurisdiction": "AE"}
    src_good = {"name": "good", "url": "https://x/good", "jurisdiction": "AE"}

    # Two critical sources so a sub-cycle has work; no custom-cadence sources.
    monkeypatch.setattr(
        scheduler, "get_sources_by_priority",
        lambda p: [src_bad, src_good] if p == "critical" else [],
    )
    monkeypatch.setattr(scheduler, "get_sources_with_custom_interval", lambda: [])

    # First full cycle is a no-op sweep.
    monkeypatch.setattr(scheduler, "monitor_all_sources", lambda **_k: [])

    pipeline_calls = []

    def _pipeline(src):
        pipeline_calls.append(src["name"])
        if src["name"] == "bad":
            raise RuntimeError("fetch failed hard")
        return {"source_name": src["name"], "changed": False, "status": "ok"}

    # The sub-cycle drives the pipeline through monitor._run_one_source, so the
    # seam to patch is monitor.run_pipeline_for_source, not scheduler's.
    monkeypatch.setattr(monitor, "run_pipeline_for_source", _pipeline)

    # Capture every results list the loop hands to the summary printer; the
    # full cycle passes [] first, the sub-cycle passes the per-source results.
    summary_calls = []

    def _capture_summary(results):
        summary_calls.append(results)

    monkeypatch.setattr(scheduler, "_print_cycle_summary", _capture_summary)

    # monitor and scheduler share the `time` module, so the helper's short retry
    # sleep and the loop's long cadence sleep hit the same patched function.
    # Gate on duration: swallow the retry sleep, count only the cadence sleep.
    # iter1 = full cycle (cadence sleep #1); iter2 = sub-cycle (cadence sleep
    # #2 → stop) — the failing source finishes its retry + record first.
    sleeps = {"n": 0}

    def _sleep(secs=0, *_a, **_k):
        if secs and secs >= 60:
            sleeps["n"] += 1
            if sleeps["n"] >= 2:
                raise KeyboardInterrupt

    monkeypatch.setattr(scheduler.time, "sleep", _sleep)

    scheduler.run_watch_loop(interval_minutes=60)

    # The good source ran even though the bad one raised first; the bad source
    # is attempted twice (initial + one retry) by the shared helper.
    assert pipeline_calls == ["bad", "bad", "good"]

    # The sub-cycle's results are the non-empty call carrying both sources.
    sub_results = next(r for r in summary_calls if r)
    by_name = {r["source_name"]: r for r in sub_results}
    assert by_name["bad"]["status"] == "error"
    assert "fetch failed hard" in by_name["bad"]["error"]
    assert by_name["good"]["status"] == "ok"


def test_digest_dispatch_output_printed_on_full_cycle(tmp_path, monkeypatch, capsys):
    """When the digest pass reports deliveries, the full cycle prints the
    customer-delivery line — verifying digest dispatch is wired into the loop."""
    _quiet_loop_env(monkeypatch, tmp_path)
    monkeypatch.setattr(scheduler, "get_sources_by_priority", lambda _p: [])
    monkeypatch.setattr(scheduler, "get_sources_with_custom_interval", lambda: [])
    monkeypatch.setattr(scheduler, "monitor_all_sources", lambda **_k: [])
    monkeypatch.setattr(scheduler, "_print_cycle_summary", lambda *_a, **_k: None)
    monkeypatch.setattr(
        scheduler, "run_digest_dispatch_pass",
        lambda *_a, **_k: {"digests_sent": 2, "heartbeats_sent": 1, "instant_sent": 4},
    )

    def _stop(*_a, **_k):
        raise KeyboardInterrupt

    monkeypatch.setattr(scheduler.time, "sleep", _stop)

    scheduler.run_watch_loop(interval_minutes=60)

    out = capsys.readouterr().out
    assert "Customer delivery: 4 instant, 2 digest(s), 1 heartbeat(s)" in out


def test_deadline_reminders_output_printed_on_full_cycle(tmp_path, monkeypatch, capsys):
    """When the daily deadline pass reports sent stages, the loop prints the
    deadline-reminder line — verifying that wiring too."""
    _quiet_loop_env(monkeypatch, tmp_path)
    monkeypatch.setattr(scheduler, "get_sources_by_priority", lambda _p: [])
    monkeypatch.setattr(scheduler, "get_sources_with_custom_interval", lambda: [])
    monkeypatch.setattr(scheduler, "monitor_all_sources", lambda **_k: [])
    monkeypatch.setattr(scheduler, "_print_cycle_summary", lambda *_a, **_k: None)
    monkeypatch.setattr(
        scheduler, "run_deadline_reminder_pass",
        lambda *_a, **_k: {"sent": ["30-day", "7-day"]},
    )

    def _stop(*_a, **_k):
        raise KeyboardInterrupt

    monkeypatch.setattr(scheduler.time, "sleep", _stop)

    scheduler.run_watch_loop(interval_minutes=60)

    out = capsys.readouterr().out
    assert "Deadline reminders sent: 2 stage(s)" in out
