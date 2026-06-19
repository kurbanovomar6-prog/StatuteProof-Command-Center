#!/usr/bin/env python3
"""Validate the fresh-source expansion sprint.

This validator is intentionally narrow: it verifies that newly added sources
from the expansion are real fresh-alert monitors and that families below 25 are
disclosed instead of overclaimed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "product/regradar/sources.json"
FINAL_REPORT = ROOT / "docs/fresh-source-expansion-to-25-final-report.md"
NO_SAVE_RESULTS = ROOT / "docs/fresh-source-expansion-nosave-results.json"
EVIDENCE_RESULTS = ROOT / "docs/fresh-source-expansion-evidence-results.json"
MONITOR_RESULTS = ROOT / "docs/fresh-source-expansion-mass-monitor-results.json"

NEW_SOURCE_IDS = {
    "AE-dfsa-laws-rules-legal-resources-3dc15494",
    "AE-dfsa-innovation-59c1dc61",
    "AE-dfsa-what-we-do-enforcement-1a837c50",
    "AE-sca-fintech-sandbox",
    "AE-uaeiec-en-us-laws-regulations-listing-00a71863",
    "AE-eocn-tfs",
}

FORBIDDEN_COPY = (
    "complete uae coverage",
    "complete sca coverage",
    "complete eocn/tfs coverage",
    "complete family coverage",
    "guaranteed compliance",
    "legal advice",
    "perfect parsing",
    "never miss",
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def is_static_or_homepage(url: str) -> bool:
    folded = url.lower().rstrip("/")
    if folded.count("/") <= 2:
        return True
    return any(
        token in folded
        for token in (
            "/whats-on/",
            "/news/notice-",
            "/media/announcements/",
            "/test/",
            "/signup",
            "/login",
            "goaml",
        )
    )


def main() -> int:
    failures: list[str] = []

    for path in (FINAL_REPORT, NO_SAVE_RESULTS, EVIDENCE_RESULTS, MONITOR_RESULTS):
        if not path.exists():
            failures.append(f"missing required report: {path.relative_to(ROOT)}")

    sources = load_json(SOURCES)
    by_id = {source.get("source_id"): source for source in sources}
    missing = sorted(NEW_SOURCE_IDS - set(by_id))
    if missing:
        failures.append(f"new source IDs missing from sources.json: {missing}")

    monitor = load_json(MONITOR_RESULTS) if MONITOR_RESULTS.exists() else {"results": []}
    monitor_by = {row.get("source_id"): row for row in monitor.get("results", [])}

    for source_id in sorted(NEW_SOURCE_IDS):
        source = by_id.get(source_id)
        if not source:
            continue
        if source.get("monitoring_mode") != "fresh_alert":
            failures.append(f"{source_id}: not monitoring_mode=fresh_alert")
        if source.get("alert_eligible") is not True:
            failures.append(f"{source_id}: not alert_eligible")
        if source.get("last_monitor_status") != "MONITOR_OK":
            failures.append(f"{source_id}: lacks MONITOR_OK")
        if monitor_by.get(source_id, {}).get("source_health_status") != "MONITOR_OK":
            failures.append(f"{source_id}: mass-monitor result is not MONITOR_OK")
        for field in ("proof_path", "normalized_text_path", "normalized_hash"):
            if not source.get(field):
                failures.append(f"{source_id}: missing {field}")
        baseline_done = int(source.get("baseline_runs_completed") or 0)
        baseline_required = int(source.get("baseline_runs_required") or 2)
        if baseline_done < baseline_required:
            failures.append(f"{source_id}: baseline incomplete {baseline_done}/{baseline_required}")
        if source.get("recommended_check_frequency") != "daily":
            failures.append(f"{source_id}: not daily-checkable")
        if source.get("commercial_signal_tier") not in {"A", "B"}:
            failures.append(f"{source_id}: not Tier A/B")
        if is_static_or_homepage(str(source.get("url") or "")):
            failures.append(f"{source_id}: static/detail/homepage URL cannot be fresh_alert")

    # The no-save marathon must include held failures, otherwise the task is
    # just cherry-picking easy wins without documenting blockers.
    if NO_SAVE_RESULTS.exists():
        no_save = load_json(NO_SAVE_RESULTS)
        held = [row for row in no_save if row.get("recommendation") != "fresh_monitoring_candidate"]
        if len(no_save) < 50:
            failures.append(f"no-save test count too low: {len(no_save)}")
        if not held:
            failures.append("no-save report does not document held/rejected candidates")

    if FINAL_REPORT.exists():
        text = FINAL_REPORT.read_text(encoding="utf-8", errors="ignore").lower()
        for phrase in FORBIDDEN_COPY:
            if phrase in text and "forbidden" not in text:
                failures.append(f"final report contains unsafe positive claim: {phrase}")
        for family in ("VARA", "DFSA", "DIFC", "ADGM/FSRA", "UAE FIU", "EOCN/TFS", "SCA", "MoJ/Gazette", "MoF"):
            if family.lower() not in text:
                failures.append(f"final report missing family disclosure: {family}")
        if "families still below 25" not in text:
            failures.append("final report must disclose families still below 25")

    if failures:
        print("validate_fresh_source_expansion_to_25: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("validate_fresh_source_expansion_to_25: PASS")
    print(f"new_fresh_sources={len(NEW_SOURCE_IDS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
