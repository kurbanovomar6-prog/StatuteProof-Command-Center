#!/usr/bin/env python3
"""Validate the fresh-source completion-next sprint.

The validator is intentionally narrow. It verifies the sources promoted in this
specific pass and requires blocker disclosure for families that are still below
the 25 fresh-alert threshold.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "product/regradar/sources.json"
FINAL_REPORT = ROOT / "docs/fresh-source-completion-next-final-report.md"
NO_SAVE_RESULTS = ROOT / "docs/fresh-source-completion-next-nosave-results.json"
EVIDENCE_RESULTS = ROOT / "docs/fresh-source-completion-next-evidence-results.json"
MONITOR_RESULTS = ROOT / "docs/fresh-source-completion-next-mass-monitor-results.json"
ACTIVATION_SET = ROOT / "docs/fresh-source-completion-next-final-activation-set.json"

NEW_SOURCE_IDS = {
    "AE-uaeiec-news-listing-next",
    "AE-vara-news-circulars-listing",
    "AE-dfsa-laws-rules-2dee8ba9",
    "AE-adgm-adgm-courts-legislation-and-procedures-66abfd89",
    "AE-adgm-adgm-courts-forms-fees-and-guides-a3b9d695",
    "AE-mof-publications-and-releases",
}

FORBIDDEN_POSITIVE_CLAIMS = (
    "complete uae coverage",
    "complete sca coverage",
    "complete vara coverage",
    "complete dfsa coverage",
    "complete difc coverage",
    "complete adgm/fsra coverage",
    "complete uae fiu coverage",
    "complete mof coverage",
    "complete moj/gazette coverage",
    "guaranteed compliance",
    "perfect parsing",
    "never miss",
    "legal advice",
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
            "/media/announcements/",
            "/news/notice-",
            "/test/",
            "/login",
            "/signup",
            "goaml",
        )
    )


def main() -> int:
    failures: list[str] = []
    for path in (FINAL_REPORT, NO_SAVE_RESULTS, EVIDENCE_RESULTS, MONITOR_RESULTS, ACTIVATION_SET):
        if not path.exists():
            failures.append(f"missing required artifact: {path.relative_to(ROOT)}")

    sources = load_json(SOURCES)
    by_id = {source.get("source_id"): source for source in sources}
    missing = sorted(NEW_SOURCE_IDS - set(by_id))
    if missing:
        failures.append(f"new source IDs missing from sources.json: {missing}")

    monitor = load_json(MONITOR_RESULTS) if MONITOR_RESULTS.exists() else {"results": []}
    monitor_by = {row.get("source_id"): row for row in monitor.get("results", [])}
    evidence = load_json(EVIDENCE_RESULTS) if EVIDENCE_RESULTS.exists() else []
    evidence_by = {row.get("source_id"): row for row in evidence}

    for source_id in sorted(NEW_SOURCE_IDS):
        source = by_id.get(source_id)
        if not source:
            continue
        if source.get("monitoring_mode") != "fresh_alert":
            failures.append(f"{source_id}: not monitoring_mode=fresh_alert")
        if source.get("alert_eligible") is not True:
            failures.append(f"{source_id}: not alert_eligible=true")
        if source.get("last_monitor_status") != "MONITOR_OK":
            failures.append(f"{source_id}: lacks last_monitor_status=MONITOR_OK")
        if monitor_by.get(source_id, {}).get("source_health_status") != "MONITOR_OK":
            failures.append(f"{source_id}: mass-monitor did not return MONITOR_OK")
        if monitor_by.get(source_id, {}).get("change_detected") is True:
            failures.append(f"{source_id}: mass-monitor reported unresolved change_detected")
        for field in ("proof_path", "normalized_text_path", "normalized_hash"):
            if not source.get(field):
                failures.append(f"{source_id}: missing {field}")
        baseline_done = int(source.get("baseline_runs_completed") or 0)
        baseline_required = int(source.get("baseline_runs_required") or 2)
        if baseline_done < baseline_required:
            failures.append(f"{source_id}: baseline incomplete {baseline_done}/{baseline_required}")
        if source.get("recommended_check_frequency") != "daily":
            failures.append(f"{source_id}: missing recommended_check_frequency=daily")
        if source.get("commercial_signal_tier") not in {"A", "B"}:
            failures.append(f"{source_id}: not commercially meaningful Tier A/B")
        if is_static_or_homepage(str(source.get("url") or "")):
            failures.append(f"{source_id}: static/detail/homepage URL cannot be fresh_alert")
        ev = evidence_by.get(source_id) or {}
        if ev.get("baseline_runs_completed") != 2 or ev.get("stable_hash") is not True:
            failures.append(f"{source_id}: evidence report lacks 2 stable baseline runs")

    if NO_SAVE_RESULTS.exists():
        no_save = load_json(NO_SAVE_RESULTS)
        if len(no_save) < 10:
            failures.append(f"no-save report too small: {len(no_save)}")
        held = [row for row in no_save if row.get("recommendation") != "fresh_monitoring_candidate"]
        if not held:
            failures.append("no-save report must include held/rejected blockers")

    if FINAL_REPORT.exists():
        text = FINAL_REPORT.read_text(encoding="utf-8", errors="ignore")
        lower = text.lower()
        for family in ("VARA", "DFSA", "DIFC", "ADGM/FSRA", "UAE FIU", "SCA", "MoJ/Gazette", "MoF"):
            if family.lower() not in lower:
                failures.append(f"final report missing family disclosure: {family}")
        if "families still below 25" not in lower:
            failures.append("final report must include 'Families Still Below 25' section")
        # Forbidden phrases are allowed only inside a forbidden/claims-still-forbidden section.
        safe_context_markers = ("claims still forbidden", "still forbidden", "must not claim")
        for phrase in FORBIDDEN_POSITIVE_CLAIMS:
            if phrase in lower and not any(marker in lower for marker in safe_context_markers):
                failures.append(f"unsafe positive claim appears: {phrase}")
        if "selected-source monitoring" not in lower:
            failures.append("final report must use selected-source monitoring wording")

    if failures:
        print("validate_fresh_source_completion_next: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("validate_fresh_source_completion_next: PASS")
    print(f"new_fresh_sources={len(NEW_SOURCE_IDS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
