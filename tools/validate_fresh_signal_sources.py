#!/usr/bin/env python3
"""Validate fresh-alert source integrity."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "product/regradar/sources.json"


def is_ae_source(source: dict) -> bool:
    source_id = str(source.get("source_id") or "")
    return source.get("jurisdiction") == "AE" or source_id.startswith("AE-")


def is_static_detail_url(url: str) -> bool:
    folded = url.lower()
    return any(
        token in folded
        for token in (
            "/whats-on/",
            "/media/announcements/",
            "/news/notice-",
        )
    )


def main() -> int:
    sources = json.loads(SOURCES.read_text())
    failures: list[str] = []
    fresh = [
        source
        for source in sources
        if source.get("enabled")
        and is_ae_source(source)
        and source.get("monitoring_mode") == "fresh_alert"
    ]

    for source in fresh:
        source_id = source.get("source_id") or source.get("url")
        url = str(source.get("url") or "")
        if source.get("last_monitor_status") != "MONITOR_OK":
            failures.append(f"{source_id}: fresh_alert lacks MONITOR_OK")
        if not source.get("proof_path"):
            failures.append(f"{source_id}: fresh_alert lacks proof_path")
        if not source.get("normalized_text_path"):
            failures.append(f"{source_id}: fresh_alert lacks normalized_text_path")
        if not source.get("normalized_hash"):
            failures.append(f"{source_id}: fresh_alert lacks normalized_hash")
        if source.get("recommended_check_frequency") != "daily":
            failures.append(f"{source_id}: fresh_alert lacks recommended_check_frequency=daily")
        if not source.get("fresh_signal_type"):
            failures.append(f"{source_id}: fresh_alert lacks fresh_signal_type")
        if not source.get("expected_update_pattern"):
            failures.append(f"{source_id}: fresh_alert lacks expected_update_pattern")
        if not source.get("customer_alert_policy"):
            failures.append(f"{source_id}: fresh_alert lacks customer_alert_policy")
        baseline_completed = int(source.get("baseline_runs_completed") or 0)
        baseline_required = int(source.get("baseline_runs_required") or 2)
        if baseline_completed < baseline_required:
            failures.append(
                f"{source_id}: baseline {baseline_completed}/{baseline_required} is incomplete"
            )
        if source.get("alert_eligible") is not True:
            failures.append(f"{source_id}: fresh_alert must be alert_eligible")
        if source.get("commercial_signal_tier") not in {"A", "B"}:
            failures.append(
                f"{source_id}: fresh_alert must be Tier A/B, got {source.get('commercial_signal_tier')!r}"
            )
        if is_static_detail_url(url):
            failures.append(f"{source_id}: static detail URL cannot be fresh_alert ({url})")
        if url.rstrip("/").count("/") <= 2:
            failures.append(f"{source_id}: generic root URL cannot be fresh_alert ({url})")

    if failures:
        print("validate_fresh_signal_sources: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("validate_fresh_signal_sources: PASS")
    print(f"fresh_alert_count={len(fresh)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
