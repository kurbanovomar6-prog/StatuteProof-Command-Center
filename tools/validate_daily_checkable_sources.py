#!/usr/bin/env python3
"""Validate daily-check metadata for fresh-alert UAE sources."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from tools.fresh_alert_validator_common import (
        validate_baseline_runs,
        validate_fresh_alert_artifacts,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from fresh_alert_validator_common import (
        validate_baseline_runs,
        validate_fresh_alert_artifacts,
    )


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "product/regradar/sources.json"
REGRADAR_ROOT = ROOT / "product/regradar"


def is_ae_source(source: dict) -> bool:
    source_id = str(source.get("source_id") or "")
    return source.get("jurisdiction") == "AE" or source_id.startswith("AE-")


STATIC_OR_HOMEPAGE_TOKENS = (
    "/whats-on/",
    "/media/announcements/",
    "/news/notice-",
    "/test/",
    "/login",
    "/signup",
)


def is_static_or_homepage_url(url: str) -> bool:
    folded = url.lower()
    if folded.rstrip("/").count("/") <= 2:
        return True
    return any(token in folded for token in STATIC_OR_HOMEPAGE_TOKENS)


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
            failures.append(f"{source_id}: daily fresh_alert lacks MONITOR_OK")
        failures.extend(validate_fresh_alert_artifacts(source, REGRADAR_ROOT))
        failures.extend(validate_baseline_runs(source, str(source_id)))
        if source.get("alert_eligible") is not True:
            failures.append(f"{source_id}: daily fresh_alert must be alert_eligible")
        if is_static_or_homepage_url(url):
            failures.append(f"{source_id}: static/detail/homepage URL cannot be daily fresh_alert")
        if source.get("recommended_check_frequency") != "daily":
            failures.append(f"{source_id}: expected recommended_check_frequency=daily")
        for field in ("fresh_signal_type", "expected_update_pattern", "customer_alert_policy"):
            value = str(source.get(field) or "").strip()
            if not value:
                failures.append(f"{source_id}: missing {field}")
        policy = str(source.get("customer_alert_policy") or "").lower()
        if "alert" not in policy:
            failures.append(f"{source_id}: customer_alert_policy must describe alert behavior")
        if "suppress" not in policy:
            failures.append(f"{source_id}: customer_alert_policy must describe noise suppression")
        pattern = str(source.get("expected_update_pattern") or "").lower()
        if "daily" not in pattern and "checked" not in pattern:
            failures.append(f"{source_id}: expected_update_pattern must mention daily checking")

    if failures:
        print("validate_daily_checkable_sources: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("validate_daily_checkable_sources: PASS")
    print(f"daily_checkable_fresh_alert={len(fresh)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
