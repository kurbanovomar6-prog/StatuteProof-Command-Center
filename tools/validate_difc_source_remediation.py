#!/usr/bin/env python3
"""Validate DIFC official source remediation and activation.

The validator is intentionally narrow: it checks only the DIFC sources activated
by the remediation sprint and claim-safety around DIFC coverage.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES_FILE = ROOT / "product/regradar/sources.json"
SOURCE_RUNS_FILE = ROOT / "product/regradar/data/source_runs/source_runs.jsonl"

REQUIRED_DIFC_SOURCES = {
    "AE-difc-laws-and-regulations": "https://www.difc.com/business/laws-and-regulations/",
    "AE-difc-legal-database": "https://www.difc.com/business/laws-and-regulations/legal-database/",
    "AE-difc-data-protection-commissioner": "https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection",
    "AE-difc-data-protection-guidance": "https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/guidance",
    "AE-difc-data-protection-regulation-10": "https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/regulation-10",
    "AE-difc-data-protection-supervision-enforcement": "https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/supervision-enforcement",
    "AE-difc-data-protection-law-2020": "https://www.difc.com/business/laws-and-regulations/legal-database/difc-laws/data-protection-law-difc-law-no-5-2020",
    "AE-difc-companies-law-2018": "https://www.difc.com/business/laws-and-regulations/legal-database/difc-laws/companies-law-difc-law-no-5-2018",
}

CLAIM_SCAN_PATHS = [
    ROOT / "README.md",
    ROOT / "START_HERE.md",
    ROOT / "product/regradar/web/src",
    ROOT / "docs/difc-remediation-final-report.md",
    ROOT / "docs/source-readiness-truth-reconciliation-report.md",
]

FORBIDDEN_CLAIMS = {
    "complete difc coverage",
    "full difc coverage",
    "all difc sources",
    "difc certified",
    "guaranteed compliance",
    "we provide legal advice",
    "perfect parsing",
    "never miss updates",
    "official regulator certified",
}

NEGATION_MARKERS = (
    "do not claim",
    "does not claim",
    "not claim",
    "not ",
    "no claim",
    "without claiming",
    "forbidden",
)


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_runs() -> list[dict]:
    if not SOURCE_RUNS_FILE.exists():
        return []
    rows: list[dict] = []
    with SOURCE_RUNS_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def iter_scan_files() -> list[Path]:
    files: list[Path] = []
    for path in CLAIM_SCAN_PATHS:
        if path.is_dir():
            files.extend(child for child in path.rglob("*") if child.is_file())
        elif path.exists():
            files.append(path)
    return files


def has_forbidden_claim(text: str, claim: str) -> bool:
    start = 0
    while True:
        idx = text.find(claim, start)
        if idx == -1:
            return False
        prefix = text[max(0, idx - 100):idx]
        if not any(marker in prefix for marker in NEGATION_MARKERS):
            return True
        start = idx + len(claim)


def main() -> int:
    errors: list[str] = []
    if not SOURCES_FILE.exists():
        print(f"ERROR: Missing {SOURCES_FILE}")
        return 1

    sources = load_json(SOURCES_FILE)
    if not isinstance(sources, list):
        print("ERROR: sources.json must be a list")
        return 1

    by_id = {str(item.get("source_id") or ""): item for item in sources if isinstance(item, dict)}
    runs = read_runs()

    for source_id, expected_url in sorted(REQUIRED_DIFC_SOURCES.items()):
        source = by_id.get(source_id)
        if not source:
            errors.append(f"{source_id} missing from sources.json")
            continue
        if not source.get("enabled"):
            errors.append(f"{source_id} must be enabled after remediation")
        if source.get("status") != "active":
            errors.append(f"{source_id} must be status=active")
        if source.get("url") != expected_url:
            errors.append(f"{source_id} URL mismatch: expected {expected_url}, got {source.get('url')!r}")
        if source.get("adapter_name") != "difc_legal_database":
            errors.append(f"{source_id} must use difc_legal_database adapter")
        proof_path = str(source.get("proof_path") or "")
        if not proof_path:
            errors.append(f"{source_id} missing proof_path")
        elif not (ROOT / "product/regradar" / proof_path).exists():
            errors.append(f"{source_id} proof_path does not exist: {proof_path}")
        normalized_hash = str(source.get("normalized_hash") or "")
        if len(normalized_hash) != 64:
            errors.append(f"{source_id} normalized_hash must be a 64-character SHA-256 hash")

        matching_runs = [
            row for row in runs
            if row.get("source_id") == source_id and row.get("normalized_hash") == normalized_hash
        ]
        if len(matching_runs) < 2:
            errors.append(f"{source_id} requires at least two saved baseline runs with the active normalized_hash")
        if any(row.get("source_health_status") in {"QUALITY_DROP", "NAV_SHELL_ONLY", "REMEDIATION_REQUIRED"} for row in matching_runs):
            errors.append(f"{source_id} has unresolved source-health issue in saved runs")

    enabled_ae = [
        source for source in sources
        if source.get("jurisdiction") == "AE" and source.get("enabled") is True
    ]
    active = [source for source in enabled_ae if source.get("status") == "active"]
    remediation = [source for source in enabled_ae if source.get("status") == "remediation"]
    if (len(enabled_ae), len(active), len(remediation)) != (79, 78, 1):
        errors.append(
            "Source truth mismatch after DIFC remediation: "
            f"{len(enabled_ae)} enabled / {len(active)} active / {len(remediation)} remediation"
        )

    for path in iter_scan_files():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        for claim in FORBIDDEN_CLAIMS:
            if has_forbidden_claim(text, claim):
                errors.append(f"Forbidden DIFC/customer-facing claim in {path.relative_to(ROOT)}: {claim}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("DIFC source remediation validation PASSED")
    print(f"- Required DIFC sources: {len(REQUIRED_DIFC_SOURCES)}")
    print("- Proof paths, repeat baseline runs, hashes, source truth, and claim safety checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
