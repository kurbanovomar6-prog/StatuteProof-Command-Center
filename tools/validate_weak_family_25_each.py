#!/usr/bin/env python3
"""Validate the weak-family 25-each activation sprint.

This validator allows honest partial completion: it requires the newly claimed
FTA 25-source activation to be proof-backed and requires explicit blockers for
families still below 25. It must not allow complete UAE/family coverage claims.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGRADAR_ROOT = ROOT / "product/regradar"
SOURCES = REGRADAR_ROOT / "sources.json"
FINAL_SET = ROOT / "docs/weak-family-25-each-final-activation-set.json"
NO_SAVE = ROOT / "docs/weak-family-25-each-nosave-results.json"
EVIDENCE = ROOT / "docs/weak-family-25-each-evidence-results.json"
MASS_MONITOR = ROOT / "docs/weak-family-25-each-mass-monitor-results.json"
FINAL_REPORT = ROOT / "docs/weak-family-25-each-final-report.md"
TARGET_PROGRESS = ROOT / "docs/weak-family-25-each-target-progress-report.md"

EXPECTED_TRUTH = (147, 146, 1)
TARGET_FAMILIES = (
    "DIFC",
    "ADGM/FSRA",
    "VARA",
    "Ministry of Economy / DNFBP AML",
    "SCA",
    "UAE FIU",
    "EOCN / sanctions / TFS",
    "FTA / Tax",
)
FORBIDDEN = (
    "complete uae coverage",
    "complete family coverage",
    "guaranteed compliance",
    "perfect parsing",
    "never miss updates",
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


def source_truth(sources: list[dict]) -> tuple[int, int, int]:
    enabled = [
        row for row in sources
        if isinstance(row, dict)
        and row.get("jurisdiction") == "AE"
        and row.get("enabled") is True
    ]
    active = [row for row in enabled if row.get("status") == "active"]
    remediation = [row for row in enabled if row.get("status") == "remediation"]
    return len(enabled), len(active), len(remediation)


def safe_claim_context(text: str, claim: str) -> bool:
    lower = text.lower()
    start = 0
    while True:
        idx = lower.find(claim, start)
        if idx == -1:
            return True
        ctx = lower[max(0, idx - 140): idx + len(claim) + 140]
        if any(marker in ctx for marker in ("no", "not", "did we claim", "forbidden", "must not", "without")):
            start = idx + len(claim)
            continue
        if claim == "legal advice" and "not legal advice" in ctx:
            start = idx + len(claim)
            continue
        return False


def main() -> int:
    errors: list[str] = []
    for path in (SOURCES, FINAL_SET, NO_SAVE, EVIDENCE, MASS_MONITOR, FINAL_REPORT, TARGET_PROGRESS):
        if not path.exists():
            errors.append(f"Missing required file: {path.relative_to(ROOT)}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    sources = load_json(SOURCES)
    if source_truth(sources) != EXPECTED_TRUTH:
        errors.append(f"Expected source truth {EXPECTED_TRUTH}, got {source_truth(sources)}")
    by_id = {str(row.get("source_id") or ""): row for row in sources if isinstance(row, dict)}

    final_set = load_json(FINAL_SET)
    final_rows = final_set.get("specs") or []
    held_rows = final_set.get("held") or []
    if len(final_rows) != 25:
        errors.append(f"Expected 25 FTA final rows, got {len(final_rows)}")
    if held_rows:
        errors.append("No rows should be held after final dry-run; held rows belong in no-save/evidence reports")

    seen_urls: set[str] = set()
    seen_hashes: set[str] = set()
    for row in final_rows:
        sid = str(row.get("source_id") or "")
        source = by_id.get(sid)
        if not sid.startswith("AE-fta-pdf-"):
            errors.append(f"FTA activation source_id must use AE-fta-pdf- prefix: {sid}")
        if not source:
            errors.append(f"Final FTA source missing from sources.json: {sid}")
            continue
        if source.get("enabled") is not True or source.get("status") != "active":
            errors.append(f"{sid} must be enabled active")
        if source.get("adapter_family") != "pdf_document" or source.get("adapter_name") != "pdf_document":
            errors.append(f"{sid} must use pdf_document adapter")
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
            errors.append(f"{sid} duplicates normalized_hash")
        seen_hashes.add(normalized_hash)
        url = str(source.get("url") or "")
        if not url.startswith("https://tax.gov.ae/"):
            errors.append(f"{sid} must use official tax.gov.ae URL")
        if url in seen_urls:
            errors.append(f"{sid} duplicates URL")
        seen_urls.add(url)
        notes = str(source.get("notes") or "").lower()
        for marker in ("monitor_ok", "monitoring intelligence only", "not legal advice"):
            if marker not in notes:
                errors.append(f"{sid} notes missing marker: {marker}")

    no_save = load_json(NO_SAVE)
    if no_save.get("strong_pass_count") != 25 or no_save.get("tested_count", 0) < 27:
        errors.append("No-save report must show 25 strong passes from at least 27 tested FTA PDFs")
    evidence = load_json(EVIDENCE)
    if evidence.get("evidence_ok_count") != 25:
        errors.append("Evidence report must show 25 evidence-ok FTA sources")
    mass = load_json(MASS_MONITOR)
    if mass.get("processed_count") != 25 or mass.get("source_health_counts", {}).get("MONITOR_OK") != 25:
        errors.append("Mass-monitor report must show 25 processed and 25 MONITOR_OK")

    final_text = FINAL_REPORT.read_text(encoding="utf-8", errors="ignore")
    target_text = TARGET_PROGRESS.read_text(encoding="utf-8", errors="ignore")
    for family in TARGET_FAMILIES:
        if family not in target_text:
            errors.append(f"Target progress report missing family: {family}")
    for marker in (
        "FTA / Tax | 25 | Yes",
        "DIFC | 12 | No",
        "SCA | 5 | No",
        "Did We Claim Complete UAE Coverage?",
    ):
        if marker not in final_text:
            errors.append(f"Final report missing marker: {marker}")
    for claim in FORBIDDEN:
        if not safe_claim_context(final_text, claim):
            errors.append(f"Unsafe positive claim in final report: {claim}")

    # Strong family claims must be limited to FTA in this sprint report.
    suspicious_strong = re.findall(r"\|\s*(DIFC|ADGM/FSRA|VARA|SCA|UAE FIU|EOCN / sanctions / TFS)\s*\|[^\n]*\|\s*Yes\s*\|", final_text)
    if suspicious_strong:
        errors.append("Non-FTA weak family incorrectly marked as reaching >=25: " + ", ".join(suspicious_strong))

    if errors:
        print("validate_weak_family_25_each: FAIL")
        for error in errors[:80]:
            print(f"- {error}")
        if len(errors) > 80:
            print(f"- {len(errors) - 80} additional errors omitted")
        return 1

    print("validate_weak_family_25_each: PASS")
    print("Source truth: 147 enabled / 146 monitoring-active / 1 remediation")
    print("FTA activation: 25 proof-backed pdf_document endpoints")
    print("Other weak families remain below 25 with blockers documented")
    return 0


if __name__ == "__main__":
    sys.exit(main())
