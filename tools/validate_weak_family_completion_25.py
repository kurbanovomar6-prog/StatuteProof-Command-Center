#!/usr/bin/env python3
"""Validate the weak-family completion sprint toward 25 active endpoints.

This validator allows honest partial completion. It requires proof-backed
activation for every newly active row and requires explicit blockers for
families that still remain below 25.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGRADAR_ROOT = ROOT / "product/regradar"
SOURCES = REGRADAR_ROOT / "sources.json"
FINAL_SET = ROOT / "docs/weak-family-completion-final-activation-set.json"
FINAL_REPORT = ROOT / "docs/weak-family-completion-25-final-report.md"
TARGET_PROGRESS = ROOT / "docs/weak-family-completion-target-progress-report.md"
NO_SAVE = ROOT / "docs/weak-family-completion-nosave-results.json"

EXPECTED_TRUTH = (232, 231, 1)
TARGET = 25
EXPECTED_FAMILY_COUNTS = {
    "DIFC": 25,
    "ADGM/FSRA": 25,
    "VARA": 25,
    "Ministry of Economy / DNFBP AML": 26,
    "SCA": 6,
    "UAE FIU": 6,
    "EOCN / sanctions / TFS": 23,
}
BELOW_TARGET_BLOCKERS = {
    "SCA": ("robots", "blocked", "download"),
    "UAE FIU": ("403", "cloudflare", "project fetch"),
    "EOCN / sanctions / TFS": ("robots", "duplicate", "noise"),
}
FORBIDDEN_POSITIVE = (
    "complete uae coverage",
    "complete family coverage",
    "guaranteed compliance",
    "perfect parsing",
    "never miss updates",
    "regulator certified",
    "legal advice",
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def artifact_exists(value: str) -> bool:
    if not value:
        return False
    path = Path(value)
    if path.is_absolute():
        return path.exists()
    return (REGRADAR_ROOT / path).exists()


def source_id(row: dict) -> str:
    return str(row.get("source_id") or row.get("id") or "")


def source_truth(rows: list[dict]) -> tuple[int, int, int]:
    enabled = [
        row for row in rows
        if isinstance(row, dict)
        and row.get("jurisdiction") == "AE"
        and row.get("enabled") is True
    ]
    active = [row for row in enabled if row.get("status") == "active"]
    remediation = [row for row in enabled if row.get("status") == "remediation"]
    return len(enabled), len(active), len(remediation)


def family_counts(rows: list[dict]) -> dict[str, int]:
    active = [
        row for row in rows
        if isinstance(row, dict)
        and row.get("jurisdiction") == "AE"
        and row.get("enabled") is True
        and row.get("status") == "active"
    ]

    def sid(row: dict) -> str:
        return source_id(row).lower()

    eocn_tfs_ids = {
        "ae-moet-targeted-financial-sanctions-586d6f96",
        "ae-moet-dnfbp-circular-2025-sanctions-screening",
        "ae-moet-dnfbp-circular-2025-iran-un-sanctions",
        "ae-moet-dnfbp-circular-2022-tfs-requirements",
    }
    counts = {
        "DIFC": sum(1 for row in active if sid(row).startswith("ae-difc")),
        "ADGM/FSRA": sum(1 for row in active if "adgm" in sid(row) or "adgm" in str(row.get("name", "")).lower()),
        "VARA": sum(
            1 for row in active
            if sid(row).startswith("ae-vara") or "vara" in sid(row) or "vara" in str(row.get("name", "")).lower()
        ),
        "Ministry of Economy / DNFBP AML": sum(
            1 for row in active
            if sid(row).startswith("ae-moet") and row.get("category") == "dnfbp_aml"
        ),
        "SCA": sum(1 for row in active if sid(row).startswith("ae-sca")),
        "UAE FIU": sum(1 for row in active if sid(row).startswith("ae-uaefiu")),
        "EOCN / sanctions / TFS": sum(
            1 for row in active
            if sid(row).startswith("ae-eocn")
            or row.get("category") == "eocn_tfs"
            or sid(row) in eocn_tfs_ids
        ),
    }
    return counts


def safe_context(text: str, claim: str) -> bool:
    lower = text.lower()
    start = 0
    while True:
        idx = lower.find(claim, start)
        if idx == -1:
            return True
        context = lower[max(0, idx - 140): idx + len(claim) + 140]
        if claim == "legal advice" and "not legal advice" in context:
            start = idx + len(claim)
            continue
        if any(marker in context for marker in ("no", "not", "did we claim", "must not", "forbidden")):
            start = idx + len(claim)
            continue
        return False


def main() -> int:
    errors: list[str] = []
    for path in (SOURCES, FINAL_SET, FINAL_REPORT, TARGET_PROGRESS, NO_SAVE):
        if not path.exists():
            errors.append(f"Missing required file: {path.relative_to(ROOT)}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    sources = load_json(SOURCES)
    if not isinstance(sources, list):
        print("ERROR: sources.json must be a list")
        return 1
    by_id = {source_id(row): row for row in sources if isinstance(row, dict)}
    truth = source_truth(sources)
    if truth != EXPECTED_TRUTH:
        errors.append(f"Expected source truth {EXPECTED_TRUTH}, got {truth}")

    counts = family_counts(sources)
    for family, expected in EXPECTED_FAMILY_COUNTS.items():
        if counts.get(family) != expected:
            errors.append(f"{family} count mismatch: expected {expected}, got {counts.get(family)}")

    final_set = load_json(FINAL_SET)
    newly_active = final_set.get("newly_active") or {}
    flat_rows: list[dict] = []
    for family, rows in newly_active.items():
        if not isinstance(rows, list):
            errors.append(f"newly_active[{family}] must be a list")
            continue
        flat_rows.extend(row for row in rows if isinstance(row, dict))
    if len(flat_rows) != 79:
        errors.append(f"Expected 79 newly active rows in final activation set, got {len(flat_rows)}")

    for row in flat_rows:
        sid = str(row.get("source_id") or "")
        source = by_id.get(sid)
        if not source:
            errors.append(f"Newly active source missing from sources.json: {sid}")
            continue
        if source.get("enabled") is not True or source.get("status") != "active":
            errors.append(f"{sid} must be enabled active")
        if int(source.get("baseline_runs_completed") or 0) < 2:
            errors.append(f"{sid} requires baseline_runs_completed >= 2")
        if source.get("last_monitor_status") != "MONITOR_OK":
            errors.append(f"{sid} requires last_monitor_status=MONITOR_OK")
        if not source.get("normalized_hash"):
            errors.append(f"{sid} requires normalized_hash")
        for field in ("proof_path", "normalized_text_path"):
            if not artifact_exists(str(source.get(field) or "")):
                errors.append(f"{sid} missing artifact for {field}")
        notes = str(source.get("notes") or "").lower()
        for marker in ("monitoring intelligence only", "not legal advice", "monitor_ok"):
            if marker not in notes:
                errors.append(f"{sid} notes missing {marker}")

    final_text = FINAL_REPORT.read_text(encoding="utf-8", errors="ignore")
    target_text = TARGET_PROGRESS.read_text(encoding="utf-8", errors="ignore")
    combined = final_text + "\n" + target_text
    for family, blocker_terms in BELOW_TARGET_BLOCKERS.items():
        if f"| {family} |" not in target_text:
            errors.append(f"Target progress report missing {family}")
        context = combined.lower()
        if family.lower() not in context:
            errors.append(f"Final docs missing blocker family: {family}")
        for term in blocker_terms:
            if term not in context:
                errors.append(f"Final docs for {family} missing blocker term: {term}")
    for family, count in counts.items():
        if count < TARGET and family not in BELOW_TARGET_BLOCKERS:
            errors.append(f"{family} below 25 without approved blocker: {count}")

    no_save = load_json(NO_SAVE)
    if int(no_save.get("documented_probe_rows") or 0) < 250:
        errors.append("No-save completion summary should document at least 250 probe rows")
    if int(no_save.get("documented_strong_pass_rows") or 0) < 79:
        errors.append("No-save completion summary should document at least 79 strong-pass rows")

    for claim in FORBIDDEN_POSITIVE:
        if not safe_context(final_text, claim):
            errors.append(f"Unsafe positive claim in final report: {claim}")

    if errors:
        print("validate_weak_family_completion_25: FAIL")
        for error in errors[:100]:
            print(f"- {error}")
        if len(errors) > 100:
            print(f"- {len(errors) - 100} additional errors omitted")
        return 1

    print("validate_weak_family_completion_25: PASS")
    print(f"Source truth: {truth[0]} enabled / {truth[1]} monitoring-active / {truth[2]} remediation")
    for family, count in counts.items():
        print(f"- {family}: {count}")
    print("- Newly active proof-backed rows: 79")
    print("- Below-target families have explicit blockers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
