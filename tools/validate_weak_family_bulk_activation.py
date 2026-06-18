#!/usr/bin/env python3
"""Validate proof-backed weak-family bulk source activation."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGRADAR_ROOT = ROOT / "product/regradar"
SOURCES = REGRADAR_ROOT / "sources.json"
FINAL_SET = ROOT / "docs/weak-family-final-activation-set.json"
SUMMARY = ROOT / "docs/weak-family-bulk-activation-summary.json"
FINAL_REPORT = ROOT / "docs/weak-family-bulk-activation-final-report.md"

MIN_CURRENT_TRUTH = (147, 146, 1)
EXPECTED_FINAL_COUNT = 41
FORBIDDEN_POSITIVE_CLAIMS = (
    "complete uae coverage",
    "guaranteed compliance",
    "perfect parsing",
    "never miss updates",
    "regulator certification",
    "regulator certified",
)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def artifact_exists(value: str) -> bool:
    if not value:
        return False
    path = Path(value)
    if path.is_absolute():
        return path.exists()
    return (REGRADAR_ROOT / path).exists()


def unsafe_claim(text: str, claim: str) -> bool:
    lower = text.lower()
    start = 0
    while True:
        index = lower.find(claim, start)
        if index == -1:
            return False
        context = lower[max(0, index - 140): index + len(claim) + 140]
        safe_markers = ("do not", "not claim", "did not claim", "did we claim", "forbidden", "no ", "not ")
        if any(marker in context for marker in safe_markers):
            start = index + len(claim)
            continue
        return True


def main() -> int:
    errors: list[str] = []
    for path in (SOURCES, FINAL_SET, SUMMARY, FINAL_REPORT):
        if not path.exists():
            errors.append(f"Missing required file: {path.relative_to(ROOT)}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    sources = load_json(SOURCES)
    if not isinstance(sources, list):
        errors.append("sources.json must be a JSON list")
        sources = []
    by_id = {str(row.get("source_id") or row.get("id") or ""): row for row in sources if isinstance(row, dict)}
    enabled = [
        row for row in sources
        if isinstance(row, dict)
        and row.get("jurisdiction") == "AE"
        and row.get("enabled") is True
    ]
    active = [row for row in enabled if row.get("status") == "active"]
    remediation = [row for row in enabled if row.get("status") == "remediation"]
    truth = (len(enabled), len(active), len(remediation))
    if truth[0] < MIN_CURRENT_TRUTH[0] or truth[1] < MIN_CURRENT_TRUTH[1] or truth[2] != MIN_CURRENT_TRUTH[2]:
        errors.append(f"Expected current source truth at least {MIN_CURRENT_TRUTH}, got {truth}")

    final_set = load_json(FINAL_SET)
    final_rows = final_set.get("final") or []
    held_rows = final_set.get("holds") or []
    duplicate_holds = final_set.get("duplicate_holds") or []
    if len(final_rows) != EXPECTED_FINAL_COUNT:
        errors.append(f"Expected {EXPECTED_FINAL_COUNT} final active rows, got {len(final_rows)}")
    if len(held_rows) < 20:
        errors.append("Expected at least 20 held rows documenting drift/nav-shell/quality failures")
    if len(duplicate_holds) < 1:
        errors.append("Expected at least one duplicate-hash hold")

    seen_hashes: dict[str, str] = {}
    seen_urls: dict[str, str] = {}
    for row in final_rows:
        sid = str(row.get("source_id") or "")
        source = by_id.get(sid)
        if not source:
            errors.append(f"Final active source missing from registry: {sid}")
            continue
        if source.get("enabled") is not True or source.get("status") != "active":
            errors.append(f"{sid} must be enabled active")
        if int(source.get("baseline_runs_completed") or 0) < 2:
            errors.append(f"{sid} requires repeat baseline metadata")
        if source.get("last_monitor_status") != "MONITOR_OK":
            errors.append(f"{sid} requires last_monitor_status=MONITOR_OK")
        for field in ("proof_path", "normalized_text_path"):
            if not artifact_exists(str(source.get(field) or "")):
                errors.append(f"{sid} missing artifact for {field}")
        normalized_hash = str(source.get("normalized_hash") or "")
        if not normalized_hash:
            errors.append(f"{sid} missing normalized_hash")
        elif normalized_hash in seen_hashes:
            errors.append(f"{sid} duplicates normalized_hash with {seen_hashes[normalized_hash]}")
        else:
            seen_hashes[normalized_hash] = sid
        url = str(source.get("url") or "")
        if not url.startswith("https://"):
            errors.append(f"{sid} must have HTTPS official URL")
        elif url in seen_urls:
            errors.append(f"{sid} duplicates URL with {seen_urls[url]}")
        else:
            seen_urls[url] = sid
        notes = str(source.get("notes") or "").lower()
        for marker in ("monitor_ok", "monitoring intelligence only", "not legal advice"):
            if marker not in notes:
                errors.append(f"{sid} notes missing marker: {marker}")

    for row in held_rows:
        reason = str(row.get("reason") or "").lower()
        if not any(marker in reason for marker in ("nav_shell", "quality_drop", "changed_on_dry_run")):
            errors.append(f"Held row lacks concrete blocker: {row.get('source_id')}")

    report = FINAL_REPORT.read_text(encoding="utf-8", errors="ignore")
    required_report_markers = (
        "Starting truth: 81 enabled / 80 monitoring-active / 1 remediation",
        "Ending truth: 122 enabled / 121 monitoring-active / 1 remediation",
        "Newly active sources: 41",
        "Did we claim complete UAE coverage? No.",
    )
    for marker in required_report_markers:
        if marker not in report:
            errors.append(f"Final report missing marker: {marker}")
    for claim in FORBIDDEN_POSITIVE_CLAIMS:
        if unsafe_claim(report, claim):
            errors.append(f"Unsafe positive claim in final report: {claim}")

    if errors:
        for error in errors[:80]:
            print(f"ERROR: {error}")
        if len(errors) > 80:
            print(f"ERROR: {len(errors) - 80} additional errors omitted")
        return 1

    print("Weak-family bulk activation validation PASSED")
    print("- Current source truth is at least 147 enabled / 146 monitoring-active / 1 remediation")
    print("- Final active rows: 41")
    print("- Held rows documented:", len(held_rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
