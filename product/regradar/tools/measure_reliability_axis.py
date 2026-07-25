"""Reproducible measurement for the RELIABILITY axis.

The question: if one source hangs, does the sweep abandon it and carry on, or does
monitoring go dark?

    python3 tools/measure_reliability_axis.py
    python3 tools/measure_reliability_axis.py --json

This drives the real ``monitor_all_sources`` against two fake sources — the first
sleeps far past any sane cap, the second is healthy — and reports whether the
second was ever reached. Everything runs in a temp tree; no network, no working
artifacts touched.

Behavioural on purpose. Grepping for the word "timeout" tells you whether someone
wrote a feature; only running a hung source tells you whether it works.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

HANG_SECONDS = 30.0   # far past any cap a sweep should allow
CAP_SECONDS = 2.0     # the cap under test
GIVE_UP_SECONDS = 12.0  # if we are still blocked here, the sweep has wedged


def _fake_source(name: str, url: str) -> dict:
    return {
        "id": name.lower().replace(" ", "-"),
        "source_id": name.lower().replace(" ", "-"),
        "name": name,
        "url": url,
        "jurisdiction": "AE",
        "category": "financial_regulator",
        "enabled": True,
    }


def measure() -> dict:
    report: dict = {"cap_seconds": CAP_SECONDS, "hang_seconds": HANG_SECONDS}

    import app.monitor as monitor
    import app.scheduler as scheduler

    report["per_source_timeout_exists"] = hasattr(scheduler, "per_source_timeout")
    report["run_source_with_timeout_exists"] = hasattr(scheduler, "run_source_with_timeout")
    report["progress_marker_exists"] = hasattr(scheduler, "_PROGRESS_FILE")

    import app.ops_alert as ops_alert

    report["heartbeat_state_exists"] = hasattr(ops_alert, "heartbeat_state")
    report["describe_progress_exists"] = hasattr(ops_alert, "describe_progress")

    watchdog = ROOT / "deploy" / "scheduler-watchdog.sh"
    report["watchdog_script_present"] = watchdog.exists()
    if watchdog.exists():
        text = watchdog.read_text(encoding="utf-8", errors="replace")
        needed = [n for n in ("heartbeat_state", "describe_progress") if n in text]
        report["watchdog_calls"] = needed
        report["watchdog_callables_all_exist"] = all(
            hasattr(ops_alert, n) for n in needed
        )
    else:
        report["watchdog_calls"] = []
        report["watchdog_callables_all_exist"] = None

    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        hung = _fake_source("Hangs Forever", "https://hang.example/regs")
        healthy = _fake_source("Healthy Next", "https://next.example/regs")
        reached: list[str] = []

        def _pipeline(source):
            reached.append(source["url"])
            if source["url"] == hung["url"]:
                time.sleep(HANG_SECONDS)
            return {
                "url": source["url"], "final_url": source["url"], "status": "ok",
                "extracted_text": "Regulatory text " * 80, "extracted_chars": 1200,
                "fetch_method": "probe", "reason": "",
            }

        original_pipeline = monitor.run_pipeline_for_source
        # monitor_all_sources reads get_enabled_sources(), not a parameter —
        # patching the wrong name is how a probe silently measures the real
        # registry and reports a meaningless 0.0s.
        original_load = monitor.get_enabled_sources
        monitor.run_pipeline_for_source = _pipeline
        monitor.get_enabled_sources = lambda *a, **k: [hung, healthy]

        import app.source_runs as source_runs

        original_base = source_runs._BASE_DIR
        source_runs._BASE_DIR = tmp
        source_runs._RUN_DIR = tmp / "data" / "source_runs"
        source_runs._RUN_FILE = tmp / "data" / "source_runs" / "source_runs.jsonl"
        source_runs._SNAPSHOT_DIR = tmp / "data" / "source_snapshots"
        source_runs._CACHE_VALID = False
        source_runs._RUNS_CACHE = None

        started = time.monotonic()
        results = None
        error = None
        try:
            if report["per_source_timeout_exists"]:
                with scheduler.per_source_timeout(timeout_s=CAP_SECONDS):
                    results = monitor.monitor_all_sources(verbose=False)
            else:
                # No cap exists. Do not actually block for HANG_SECONDS to prove it —
                # the absence of the mechanism IS the finding.
                error = "no per-source cap exists to exercise"
        except Exception as exc:  # noqa: BLE001 — the probe reports, never raises
            error = f"{type(exc).__name__}: {exc}"
        elapsed = time.monotonic() - started

        monitor.run_pipeline_for_source = original_pipeline
        monitor.get_enabled_sources = original_load
        source_runs._BASE_DIR = original_base

        report["elapsed_seconds"] = round(elapsed, 1)
        report["error"] = error
        report["second_source_reached"] = healthy["url"] in reached
        report["sweep_wedged"] = (
            error is not None or elapsed >= GIVE_UP_SECONDS or healthy["url"] not in reached
        )
        if results:
            first = results[0] if results else {}
            report["hung_source_recorded_as"] = {
                "status": first.get("status"),
                "access_status": first.get("access_status"),
            }
        # The in-memory result is the easy half. Whether the abandoned source left
        # a DURABLE trail record is what decides if the circuit breaker can ever
        # learn that this source hangs every sweep — an earlier version of the cap
        # returned a plausible error dict and wrote nothing.
        try:
            report["breaker_sees_the_abandoned_source"] = (
                monitor._consecutive_failures(hung["url"]) >= 1
            )
        except Exception as exc:  # noqa: BLE001 — the probe reports, never raises
            report["breaker_sees_the_abandoned_source"] = f"unreadable: {exc}"
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = measure()

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    print("mechanisms present")
    for key in (
        "per_source_timeout_exists", "run_source_with_timeout_exists",
        "progress_marker_exists", "heartbeat_state_exists", "describe_progress_exists",
    ):
        print(f"  {key:34} {report[key]}")
    print(f"  watchdog_script_present            {report['watchdog_script_present']}")
    print(f"  watchdog callables all exist       {report['watchdog_callables_all_exist']} "
          f"(calls: {report['watchdog_calls']})")
    print("\nbehaviour with one hung source")
    print(f"  second source reached              {report['second_source_reached']}")
    print(f"  elapsed                            {report['elapsed_seconds']}s "
          f"(hang was {HANG_SECONDS}s, cap {CAP_SECONDS}s)")
    print(f"  hung source recorded as            {report.get('hung_source_recorded_as')}")
    print(f"  breaker sees the abandoned source  {report.get('breaker_sees_the_abandoned_source')}")
    if report.get("error"):
        print(f"  error                              {report['error']}")
    print(f"\n>> SWEEP WEDGES ON A HUNG SOURCE:    {report['sweep_wedged']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
