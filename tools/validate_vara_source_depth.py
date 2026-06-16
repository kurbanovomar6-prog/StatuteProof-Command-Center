#!/usr/bin/env python3
"""Validate VARA official PDF/rulebook source-depth activation.

This validator is intentionally strict: it checks the activated VARA PDF
sources are official/public VARA rulebook PDFs, proof-backed, baseline-backed,
and not marketed as complete VARA coverage.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES_FILE = ROOT / "product/regradar/sources.json"
SOURCE_RUNS_FILE = ROOT / "product/regradar/data/source_runs/source_runs.jsonl"

REQUIRED_VARA_PDF_SOURCES = {
    "AE-vara-compliance-risk-rulebook-pdf",
    "AE-vara-technology-information-rulebook-pdf",
    "AE-vara-va-issuance-rulebook-pdf",
    "AE-vara-broker-dealer-rulebook-pdf",
    "AE-vara-lending-borrowing-rulebook-pdf",
    "AE-vara-va-regulations-2023-pdf",
}

CLAIM_SCAN_PATHS = [
    ROOT / "README.md",
    ROOT / "START_HERE.md",
    ROOT / "product/regradar/web/src",
    ROOT / "docs/vara-source-depth-final-report.md",
    ROOT / "docs/post-50-proof-backed-demo-script.md",
]

FORBIDDEN_CLAIMS = {
    "complete vara coverage",
    "full vara coverage",
    "all vara rulebooks",
    "guaranteed compliance",
    "we provide legal advice",
    "perfect parsing",
    "never miss updates",
    "official regulator certified",
}

NEGATION_MARKERS = (
    "do not claim",
    "does not claim",
    "must not claim",
    "not ",
    "no claim",
    "not claim",
    "never claim",
)


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_scan_files() -> list[Path]:
    files: list[Path] = []
    for path in CLAIM_SCAN_PATHS:
        if path.is_dir():
            files.extend(child for child in path.rglob("*") if child.is_file())
        elif path.exists():
            files.append(path)
    return files


def read_runs() -> list[dict]:
    if not SOURCE_RUNS_FILE.exists():
        return []
    rows: list[dict] = []
    with SOURCE_RUNS_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def has_forbidden_claim(text: str, claim: str) -> bool:
    """Return true for positive overclaims, ignoring explicit warnings/negations."""
    start = 0
    while True:
        idx = text.find(claim, start)
        if idx == -1:
            return False
        prefix = text[max(0, idx - 80):idx]
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

    for source_id in sorted(REQUIRED_VARA_PDF_SOURCES):
        source = by_id.get(source_id)
        if not source:
            errors.append(f"{source_id} missing from sources.json")
            continue
        url = str(source.get("url") or "")
        if not source.get("enabled"):
            errors.append(f"{source_id} must be enabled after activation")
        if source.get("status") != "active":
            errors.append(f"{source_id} must be status=active")
        if not url.startswith("https://rulebooks.vara.ae/sites/default/files/") or not url.lower().endswith(".pdf"):
            errors.append(f"{source_id} must use an official rulebooks.vara.ae PDF URL")
        if source.get("adapter_name") != "pdf_document":
            errors.append(f"{source_id} must use pdf_document adapter")
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

    active_vara = [
        item for item in sources
        if item.get("jurisdiction") == "AE"
        and item.get("enabled") is True
        and str(item.get("source_id") or "").lower().startswith("ae-vara")
        and item.get("status") == "active"
    ]
    if len(active_vara) < 7:
        errors.append(f"Expected VARA active source depth to be at least 7 after this sprint, found {len(active_vara)}")

    for path in iter_scan_files():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        for claim in FORBIDDEN_CLAIMS:
            if has_forbidden_claim(text, claim):
                errors.append(f"Forbidden VARA/customer-facing claim in {path.relative_to(ROOT)}: {claim}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("VARA source-depth validation PASSED")
    print(f"- Required official VARA PDF sources: {len(REQUIRED_VARA_PDF_SOURCES)}")
    print(f"- Active VARA sources in registry: {len(active_vara)}")
    print("- Proof paths, repeat baseline runs, hashes, and customer claim safety checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
