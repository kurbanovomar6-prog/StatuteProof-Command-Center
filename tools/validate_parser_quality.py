#!/usr/bin/env python3
"""Strict parser/source-intake quality gate for StatuteProof.

This validator is intentionally lightweight and stdlib-only. It checks for
structural parser requirements and the highest-risk customer-facing overclaims.
It is not a replacement for live Source Lab checks or human Source Monitor,
Evidence Trail, QA, and Legal review.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "product/regradar/app/source_intake.py",
    "product/regradar/app/source_certification.py",
    "product/regradar/app/source_quality.py",
    "product/regradar/app/source_tester.py",
    "product/regradar/app/scraper.py",
    "product/regradar/app/extractors.py",
    "product/regradar/app/api.py",
    "product/regradar/app/proof.py",
    "product/regradar/app/source_runs.py",
    "product/regradar/app/diff.py",
    "product/regradar/app/text_normalization.py",
    "product/regradar/app/source_readiness.py",
    "product/regradar/run.py",
    "product/regradar/sources.json",
    "product/regradar/web/src/components/app/SourceLabPage.jsx",
    "product/regradar/web/src/components/app/SourcesPage.jsx",
    "docs/parser-quality-gates.md",
]

REQUIRED_PROVIDER_FILES = [
    "product/regradar/app/providers/html_extraction.py",
    "product/regradar/app/providers/pdf_extraction.py",
    "product/regradar/app/providers/optional_tools.py",
]

SOURCE_LAB_FIELDS = [
    "can_save_for_validation",
    "can_activate_monitoring",
    "activation_readiness",
    "baseline_runs_completed",
    "baseline_runs_required",
    "evidence_level",
    "provider_used",
    "quality_score",
    "normalized_preview",
    "failure_reason",
    "remediation_hint",
]

CURRENT_PROMISE = (
    "StatuteProof can test and monitor public sources that are technically "
    "accessible and permitted to be monitored."
)

FORBIDDEN_POSITIVE_PHRASES = [
    "13 validated sources",
    "13 validated UAE sources",
    "fully validated source pack",
    "certified monitoring",
    "regulator certified",
    "DFSA validated",
    "ADGM validated",
    "FSRA validated",
    "any website can be parsed",
    "guarantee compliance",
    "guaranteed parsing",
    "never miss an update",
    "100% accurate",
    "always up to date",
]

CUSTOMER_FACING_PATHS = [
    "product/regradar/web/src",
    "docs/current-uae-source-readiness-validation-report.md",
    "docs/statuteproof-homepage-copy-v2.md",
    "docs/statuteproof-pricing-strategy.md",
    "docs/parser-quality-gates.md",
]

CUSTOMER_TABLE_FILES = [
    "product/regradar/web/src/components/SourceCoverageTable.jsx",
    "product/regradar/web/src/components/DashboardPreview.jsx",
    "product/regradar/web/src/data/mockData.js",
]

NEGATIVE_CONTEXT_MARKERS = [
    "do not",
    "don't",
    "never",
    "no ",
    "not ",
    "cannot",
    "must not",
    "forbidden",
    "blocked",
]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def is_negative_context(line: str) -> bool:
    lower = line.lower()
    return any(marker in lower for marker in NEGATIVE_CONTEXT_MARKERS)


def tracked_files() -> set[str]:
    proc = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return set()
    return set(proc.stdout.splitlines())


def collect_customer_files() -> list[Path]:
    files: list[Path] = []
    for rel in CUSTOMER_FACING_PATHS:
        path = ROOT / rel
        if path.is_dir():
            files.extend(p for p in path.rglob("*") if p.is_file())
        elif path.exists():
            files.append(path)
    return files


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED_FILES + REQUIRED_PROVIDER_FILES:
        if not (ROOT / rel).exists():
            fail(errors, f"Missing required file: {rel}")

    api_text = read("product/regradar/app/api.py")
    run_text = read("product/regradar/run.py")
    source_intake_text = read("product/regradar/app/source_intake.py")

    if "/api/custom-sources/test" not in api_text:
        fail(errors, "Source Lab API endpoint /api/custom-sources/test not found.")
    if "source-lab" not in run_text:
        fail(errors, "Source Lab CLI command not found in run.py.")
    if "build_source_lab_contract" not in source_intake_text:
        fail(errors, "Source Lab contract builder is missing.")

    for field in SOURCE_LAB_FIELDS:
        if field not in api_text or field not in run_text:
            fail(errors, f"Source Lab field missing from API or CLI output: {field}")

    if ".reference_parser_repos/" not in read(".gitignore"):
        fail(errors, ".reference_parser_repos/ is not gitignored.")

    tracked = tracked_files()
    forbidden_tracked = [
        path for path in tracked
        if path == ".env"
        or path.startswith(".env.")
        or path.startswith(".reference_parser_repos/")
        or path.endswith((".sqlite", ".sqlite3", ".db"))
    ]
    if forbidden_tracked:
        fail(errors, "Forbidden tracked files: " + ", ".join(sorted(forbidden_tracked)))

    current_docs = "\n".join(
        read(path)
        for path in [
            "docs/parser-quality-gates.md",
            "docs/parser-system-full-audit-before-improvement.md",
        ]
        if (ROOT / path).exists()
    )
    if CURRENT_PROMISE not in current_docs:
        fail(errors, "Current customer-safe parser promise is missing from parser docs.")

    for file_path in collect_customer_files():
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for idx, line in enumerate(text.splitlines(), start=1):
            lower = line.lower()
            for phrase in FORBIDDEN_POSITIVE_PHRASES:
                if phrase.lower() in lower and not is_negative_context(line):
                    fail(errors, f"Forbidden customer-facing phrase in {file_path.relative_to(ROOT)}:{idx}: {phrase}")

    for rel in CUSTOMER_TABLE_FILES:
        if not (ROOT / rel).exists():
            continue
        text = read(rel)
        if "13 enabled" in text and ("10 confirmed" in text or "3 under extraction remediation" in text):
            fail(errors, f"Stale 10/3 source readiness count in {rel}.")
        if "DIFC Laws Portal" in text and "CONFIRMED" in text:
            fail(errors, f"DIFC Laws appears confirmed in customer-facing table: {rel}")
        if "PASS" in text and "Evidence confirmed" not in text:
            fail(errors, f"Raw PASS label may be customer-facing in {rel}.")

    if errors:
        print("Parser quality validation FAILED")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Parser quality validation PASSED")
    print("- Required parser/source files present")
    print("- Source Lab API/CLI contract fields present")
    print("- Reference repositories ignored")
    print("- Customer-facing overclaim scan passed")
    print("- Current parser promise present in docs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
