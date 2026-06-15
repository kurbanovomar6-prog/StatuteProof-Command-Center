#!/usr/bin/env python3
"""Validate Source Activation Platform invariants.

This validator checks that the source activation platform exposes the core
building blocks needed to avoid fake readiness claims.
"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "product/regradar/app/dom_investigator.py",
    "product/regradar/app/adapters/adapter_platform.py",
    "product/regradar/app/source_intake.py",
    "product/regradar/run.py",
    "product/regradar/web/src/components/app/SourceLabPage.jsx",
    "product/regradar/tests/test_dom_investigator.py",
    "product/regradar/tests/test_adapter_platform.py",
]

REQUIRED_ADAPTERS = [
    "static_html",
    "playwright_selector",
    "custom_element",
    "listing",
    "table",
    "pdf_document",
    "pdf_listing",
    "register",
    "sitemap_feed",
    "public_json_api",
    "rendered_dom_evidence",
    "sca_listing",
    "dfsa_rulebook",
    "dfsa_notice_listing",
    "cbuae_document_listing",
    "adgm_fsra_listing",
    "fiu_eocn_document_listing",
    "eocn_news_listing",
    "vara_pdf_listing",
]

REQUIRED_FAILURE_CODES = [
    "URL_STALE",
    "SELECTOR_NOT_FOUND",
    "JS_REQUIRED",
    "PDF_ONLY_SOURCE",
    "LISTING_ADAPTER_REQUIRED",
    "TABLE_ADAPTER_REQUIRED",
    "REGISTER_ADAPTER_REQUIRED",
    "RULEBOOK_ADAPTER_REQUIRED",
    "NAV_SHELL_ONLY",
    "ACCESS_BLOCKED",
    "LIKELY_WAF_403",
    "HIGH_NOISE_RISK",
    "DUPLICATE_BOILERPLATE_HASH",
    "SHALLOW_CONTENT",
    "SOURCE_STRUCTURE_CHANGED",
    "MANUAL_CHECK_REQUIRED",
    "DISCOVERY_FOUND_BETTER_ENDPOINT",
    "SITEMAP_DISCOVERY_REQUIRED",
    "NETWORK_ENDPOINT_DISCOVERY_REQUIRED",
]

REQUIRED_SOURCE_LAB_FIELDS = [
    "dom_investigation",
    "failure_code",
    "can_save_evidence",
    "meaningful_content",
    "shallow_content",
    "noise_risk",
    "source_health_risk",
]

CUSTOMER_FACING_PATHS = [
    ROOT / "README.md",
    ROOT / "START_HERE.md",
    ROOT / "product/regradar/web/src",
]

FORBIDDEN_PUBLIC_CLAIMS = [
    "any website can be parsed",
    "perfect parsing",
    "95% of all websites",
    "60 validated sources",
    "guaranteed compliance",
    "official regulator certified",
]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def scan_customer_files() -> list[Path]:
    files: list[Path] = []
    for path in CUSTOMER_FACING_PATHS:
        if path.is_dir():
            files.extend(child for child in path.rglob("*") if child.is_file())
        elif path.exists():
            files.append(path)
    return files


def main() -> int:
    errors: list[str] = []

    for file_name in REQUIRED_FILES:
        if not (ROOT / file_name).exists():
            errors.append(f"Missing required file: {file_name}")

    adapter_text = read("product/regradar/app/adapters/adapter_platform.py")
    source_intake_text = read("product/regradar/app/source_intake.py")
    run_text = read("product/regradar/run.py")
    source_lab_text = read("product/regradar/web/src/components/app/SourceLabPage.jsx")
    dom_text = read("product/regradar/app/dom_investigator.py")

    if "def investigate_html" not in dom_text:
        errors.append("Auto DOM Investigator must expose investigate_html().")
    for adapter in REQUIRED_ADAPTERS:
        if adapter not in adapter_text:
            errors.append(f"Adapter catalog missing {adapter}.")
    for code in REQUIRED_FAILURE_CODES:
        if code not in source_intake_text:
            errors.append(f"Source intake missing failure code {code}.")
    for field in REQUIRED_SOURCE_LAB_FIELDS:
        if field not in source_intake_text or field not in run_text:
            errors.append(f"Source Lab contract missing field {field}.")
    if "investigate-source" not in run_text:
        errors.append("CLI must expose investigate-source command.")
    if "discover-source" not in run_text or "source-discovery-lab" not in run_text:
        errors.append("CLI must expose source discovery commands.")
    for label in ("Retry with JS", "Try listing adapter", "Try PDF listing", "Mark remediation", "Save baseline"):
        if label not in source_lab_text:
            errors.append(f"Source Lab UI missing remediation control: {label}")

    for path in scan_customer_files():
        try:
            text = path.read_text(encoding="utf-8").lower()
        except UnicodeDecodeError:
            continue
        for claim in FORBIDDEN_PUBLIC_CLAIMS:
            if claim in text:
                errors.append(f"Forbidden customer-facing claim in {path.relative_to(ROOT)}: {claim}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Source activation pipeline validation passed.")
    print(f"Adapter families checked: {len(REQUIRED_ADAPTERS)}")
    print(f"Failure codes checked: {len(REQUIRED_FAILURE_CODES)}")
    print("Auto DOM Investigator, Source Lab fields, and remediation UI controls are present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
