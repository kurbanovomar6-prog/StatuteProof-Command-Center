#!/usr/bin/env python3
"""Validate Source Discovery Engine invariants."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "product/regradar/app/source_discovery.py",
    "product/regradar/app/dom_investigator.py",
    "product/regradar/app/source_intake.py",
    "product/regradar/run.py",
    "product/regradar/tests/test_source_discovery_engine.py",
]

REQUIRED_FUNCTIONS = [
    "parse_robots_sitemaps",
    "parse_sitemap_xml",
    "discover_feed_links_from_html",
    "parse_feed_xml",
    "extract_document_links_from_html",
    "discover_same_domain_links",
    "classify_network_response",
    "capture_playwright_network_candidates",
    "score_endpoint_candidate",
    "generate_source_candidate",
    "build_discovery_report_from_html",
    "discover_source",
]

REQUIRED_OUTPUT_FIELDS = [
    "input_url",
    "final_url",
    "official_domain",
    "robots_status",
    "sitemap_urls",
    "feed_urls",
    "document_links",
    "pdf_links",
    "public_json_candidates",
    "xhr_candidates",
    "listing_candidates",
    "table_candidates",
    "rulebook_candidates",
    "register_candidates",
    "same_domain_candidate_urls",
    "rejected_urls",
    "recommended_activation_paths",
]

REQUIRED_FAILURE_CODES = [
    "TABLE_ADAPTER_REQUIRED",
    "REGISTER_ADAPTER_REQUIRED",
    "RULEBOOK_ADAPTER_REQUIRED",
    "DISCOVERY_FOUND_BETTER_ENDPOINT",
    "SITEMAP_DISCOVERY_REQUIRED",
    "NETWORK_ENDPOINT_DISCOVERY_REQUIRED",
]

FORBIDDEN_PUBLIC_CLAIMS = [
    "any website can be parsed",
    "perfect parsing",
    "95% of all websites",
    "50 working sources",
    "60 validated sources",
    "guaranteed compliance",
    "official regulator certified",
]

CUSTOMER_FACING_PATHS = [
    ROOT / "README.md",
    ROOT / "START_HERE.md",
    ROOT / "product/regradar/web/src",
]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def source_function_names(text: str) -> set[str]:
    tree = ast.parse(text)
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


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

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    discovery_text = read("product/regradar/app/source_discovery.py")
    run_text = read("product/regradar/run.py")
    source_intake_text = read("product/regradar/app/source_intake.py")
    source_lab_text = read("product/regradar/web/src/components/app/SourceLabPage.jsx")
    function_names = source_function_names(discovery_text)

    for name in REQUIRED_FUNCTIONS:
        if name not in function_names:
            errors.append(f"Source Discovery Engine missing function: {name}")

    for field in REQUIRED_OUTPUT_FIELDS:
        if field not in discovery_text:
            errors.append(f"Source Discovery Engine output missing field: {field}")

    for code in REQUIRED_FAILURE_CODES:
        if code not in source_intake_text:
            errors.append(f"Source intake missing discovery failure code: {code}")

    if "discover-source" not in run_text or "source-discovery-lab" not in run_text:
        errors.append("CLI must expose discover-source and source-discovery-lab commands.")
    if "--network" not in run_text or "--max-links" not in run_text:
        errors.append("CLI discovery command must expose network and max-links flags.")

    for ui_label in ("Discover endpoints", "Discovery mode"):
        if ui_label not in source_lab_text:
            errors.append(f"Source Lab UI missing discovery label/control: {ui_label}")

    candidate_bad_patterns = [
        '"current_state": "activation_ready"',
        '"can_activate_monitoring": True',
        '"evidence_level": "CERTIFIED_EVIDENCE"',
    ]
    generator_section = discovery_text[discovery_text.find("def generate_source_candidate") :]
    for pattern in candidate_bad_patterns:
        if pattern in generator_section:
            errors.append(f"Generated candidates must not default to active/evidence state: {pattern}")

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

    print("Source discovery engine validation passed.")
    print(f"Functions checked: {len(REQUIRED_FUNCTIONS)}")
    print(f"Output fields checked: {len(REQUIRED_OUTPUT_FIELDS)}")
    print("Generated candidates remain inactive by default.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
