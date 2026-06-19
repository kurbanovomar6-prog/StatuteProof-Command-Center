#!/usr/bin/env python3
"""Block old/static detail pages from customer fresh-alert counts."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "product/regradar/sources.json"
FRONTEND_AUDIT = ROOT / "product/regradar/web/src/data/sourceQualityAudit.ts"


STATIC_PATTERNS = (
    "/whats-on/",
    "/media/announcements/",
    "/news/notice-",
)


def is_ae_source(source: dict) -> bool:
    source_id = str(source.get("source_id") or "")
    return source.get("jurisdiction") == "AE" or source_id.startswith("AE-")


def main() -> int:
    sources = json.loads(SOURCES.read_text())
    failures: list[str] = []

    for source in sources:
        if not source.get("enabled") or not is_ae_source(source):
            continue
        url = str(source.get("url") or "").lower()
        if not any(pattern in url for pattern in STATIC_PATTERNS):
            continue
        source_id = source.get("source_id") or source.get("url")
        if source.get("monitoring_mode") == "fresh_alert" or source.get("alert_eligible") is True:
            failures.append(f"{source_id}: static/detail URL is still alert eligible")
        if source.get("monitoring_mode") != "evidence_library":
            failures.append(
                f"{source_id}: static/detail URL should be evidence_library, got {source.get('monitoring_mode')!r}"
            )

    frontend = FRONTEND_AUDIT.read_text() if FRONTEND_AUDIT.exists() else ""
    risky_positive_claims = (
        "226 monitored uae regulatory sources",
        "complete uae coverage",
        "full sca coverage",
        "complete uae sanctions/tfs monitoring",
        "cbuae rulebook monitoring is live",
    )
    folded = frontend.lower()
    for claim in risky_positive_claims:
        if claim in folded and "forbidden_claims" not in folded:
            failures.append(f"frontend audit appears to contain risky positive claim: {claim!r}")

    if failures:
        print("validate_no_static_sources_as_alerts: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("validate_no_static_sources_as_alerts: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
