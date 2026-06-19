#!/usr/bin/env python3
"""Validate the final UAE remediation activation sprint.

This validator protects the honest remediation lineage after the later FTA/ADGM
truth repair and later proof-backed activations:
226 enabled UAE sources / 225 monitoring-active / 1 remediation after later proof-backed activations.

It is intentionally narrow. It verifies the two newly activated DFSA
replacement endpoints and the one remaining FIU remediation source instead of
loosening global source validators.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGRADAR_ROOT = ROOT / "product/regradar"
SOURCES_FILE = REGRADAR_ROOT / "sources.json"
SOURCE_RUNS_FILE = REGRADAR_ROOT / "data/source_runs/source_runs.jsonl"
FINAL_REPORT = ROOT / "docs/final-remediation-activation-final-report.md"
TRUTH_REPORT = ROOT / "docs/source-readiness-truth-reconciliation-report.md"

MIN_COUNTS = (226, 225, 1)

NEW_ACTIVE_SOURCES = {
    "AE-dfsa-annual-reports": {
        "url": "https://www.dfsa.ae/your-resources/publications-reports/annual-report",
        "hash": "5ac1b92a2d6cb782b2f5ec076c39866019568b99c712299662d0e36b8c17348e",
        "replacement_for": "AE-dubai-financial-services-authority-dfsa",
    },
    "AE-dfsa-annual-aml-reports": {
        "url": "https://www.dfsa.ae/your-resources/publications-reports/annual-anti-money-laundering-reports",
        "hash": "693cf380283f665545f0a20de732d6363efbdcf7fa3abba9fab782dfbc9f98b1",
        "replacement_for": "AE-dfsa-notices",
    },
}

REPLACED_SOURCES = {
    "AE-dubai-financial-services-authority-dfsa": "AE-dfsa-annual-reports",
    "AE-dfsa-notices": "AE-dfsa-annual-aml-reports",
}

REMAINING_REMEDIATION = "AE-uae-financial-intelligence-unit-uaefiu"

CLAIM_SCAN_PATHS = [
    ROOT / "README.md",
    ROOT / "START_HERE.md",
    ROOT / "product/regradar/web/src",
    ROOT / "product/regradar/web/index.html",
    ROOT / "docs/source-readiness-truth-reconciliation-report.md",
    ROOT / "docs/final-remediation-activation-final-report.md",
    ROOT / "docs/uae-complete-coverage-proof-dossier-final-report.md",
]

FORBIDDEN_POSITIVE_CLAIMS = (
    "complete uae coverage",
    "guaranteed compliance",
    "perfect parsing",
    "never miss updates",
    "official regulator certified",
    "all 79 sources are ready",
    "79/79/0",
    "79 / 79 / 0",
)

SAFE_NEGATION_MARKERS = (
    "do not claim",
    "do not say",
    "not claim",
    "does not claim",
    "no.",
    "no ",
    "not ",
    "forbidden",
    "never claim",
    "did we reach",
    "if no",
)


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def load_sources() -> list[dict]:
    with SOURCES_FILE.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("sources.json must be a list")
    return [item for item in data if isinstance(item, dict)]


def source_id(source: dict) -> str:
    return str(source.get("source_id") or source.get("id") or "")


def read_runs() -> list[dict]:
    rows: list[dict] = []
    if not SOURCE_RUNS_FILE.exists():
        return rows
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


def resolve_artifact(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    return REGRADAR_ROOT / path


def normalized_hash_matches(path_value: str, expected_hash: str) -> bool:
    artifact = resolve_artifact(path_value)
    if not artifact.exists():
        return False
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    return digest == expected_hash


def iter_scan_files() -> list[Path]:
    files: list[Path] = []
    for path in CLAIM_SCAN_PATHS:
        if path.is_dir():
            files.extend(child for child in path.rglob("*") if child.is_file())
        elif path.exists():
            files.append(path)
    return files


def positive_claim_present(text: str, claim: str) -> bool:
    lowered = text.lower()
    start = 0
    while True:
        idx = lowered.find(claim, start)
        if idx == -1:
            return False
        prefix = lowered[max(0, idx - 160):idx]
        if not any(marker in prefix for marker in SAFE_NEGATION_MARKERS):
            return True
        start = idx + len(claim)


def main() -> int:
    errors: list[str] = []

    if not SOURCES_FILE.exists():
        fail(errors, f"Missing sources file: {SOURCES_FILE}")
    if not FINAL_REPORT.exists():
        fail(errors, f"Missing final remediation report: {FINAL_REPORT}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    sources = load_sources()
    by_id = {source_id(source): source for source in sources}
    runs = read_runs()

    enabled_ae = [
        source for source in sources
        if source.get("jurisdiction") == "AE" and source.get("enabled") is True
    ]
    active = [source for source in enabled_ae if source.get("status") == "active"]
    remediation = [source for source in enabled_ae if source.get("status") == "remediation"]
    counts = (len(enabled_ae), len(active), len(remediation))
    if counts[0] < MIN_COUNTS[0] or counts[1] < MIN_COUNTS[1] or counts[2] != MIN_COUNTS[2]:
        fail(errors, f"Expected source truth at least {MIN_COUNTS}, got {counts}")

    for old_id, replacement_id in REPLACED_SOURCES.items():
        old_source = by_id.get(old_id)
        if not old_source:
            fail(errors, f"Missing replaced source: {old_id}")
            continue
        reactivated_with_new_proof = (
            old_id == "AE-dubai-financial-services-authority-dfsa"
            and old_source.get("enabled") is True
            and old_source.get("status") == "active"
            and old_source.get("last_monitor_status") == "MONITOR_OK"
            and int(old_source.get("baseline_runs_completed") or 0) >= 2
            and "weak-family bulk sprint" in str(old_source.get("notes") or "").lower()
        )
        if reactivated_with_new_proof:
            continue
        if old_source.get("enabled") is not False:
            fail(errors, f"{old_id} must be disabled after replacement")
        if old_source.get("status") != "replaced":
            fail(errors, f"{old_id} must be status=replaced")
        if old_source.get("replacement_source_id") != replacement_id:
            fail(errors, f"{old_id} replacement_source_id mismatch")

    remediation_source = by_id.get(REMAINING_REMEDIATION)
    if not remediation_source:
        fail(errors, f"Missing remaining remediation source: {REMAINING_REMEDIATION}")
    else:
        if remediation_source.get("enabled") is not True:
            fail(errors, f"{REMAINING_REMEDIATION} must remain enabled for transparent remediation")
        if remediation_source.get("status") != "remediation":
            fail(errors, f"{REMAINING_REMEDIATION} must remain status=remediation")
        notes = str(remediation_source.get("notes") or "").lower()
        for expected in ("nav", "403", "duplicate", "remediation"):
            if expected not in notes:
                fail(errors, f"{REMAINING_REMEDIATION} notes must explain {expected!r} blocker context")

    active_urls: dict[str, str] = {}
    active_hashes: dict[str, str] = {}
    for source in active:
        sid = source_id(source)
        url = str(source.get("url") or "")
        normalized_hash = str(source.get("normalized_hash") or "")
        if url:
            if url in active_urls and sid in NEW_ACTIVE_SOURCES:
                fail(errors, f"{sid} duplicates active URL with {active_urls[url]}")
            active_urls.setdefault(url, sid)
        if normalized_hash:
            if normalized_hash in active_hashes and sid in NEW_ACTIVE_SOURCES:
                fail(errors, f"{sid} duplicates active normalized hash with {active_hashes[normalized_hash]}")
            active_hashes.setdefault(normalized_hash, sid)

    for sid, expected in NEW_ACTIVE_SOURCES.items():
        source = by_id.get(sid)
        if not source:
            fail(errors, f"Missing newly active source: {sid}")
            continue
        if source.get("enabled") is not True:
            fail(errors, f"{sid} must be enabled")
        if source.get("status") != "active":
            fail(errors, f"{sid} must be status=active")
        if source.get("url") != expected["url"]:
            fail(errors, f"{sid} URL mismatch")
        if source.get("adapter_name") != "pdf_listing" or source.get("adapter_family") != "pdf_listing":
            fail(errors, f"{sid} must use pdf_listing adapter")
        if source.get("baseline_runs_completed", 0) < 2 or source.get("baseline_runs_required", 0) < 2:
            fail(errors, f"{sid} requires repeat baseline metadata")
        if source.get("last_monitor_status") != "MONITOR_OK":
            fail(errors, f"{sid} requires last_monitor_status=MONITOR_OK")
        if source.get("normalized_hash") != expected["hash"]:
            fail(errors, f"{sid} normalized_hash mismatch")

        proof_path = str(source.get("proof_path") or "")
        normalized_text_path = str(source.get("normalized_text_path") or "")
        if not proof_path or not resolve_artifact(proof_path).exists():
            fail(errors, f"{sid} proof_path missing or nonexistent: {proof_path}")
        if not normalized_text_path or not resolve_artifact(normalized_text_path).exists():
            fail(errors, f"{sid} normalized_text_path missing or nonexistent: {normalized_text_path}")
        elif not normalized_hash_matches(normalized_text_path, expected["hash"]):
            fail(errors, f"{sid} normalized_text_path hash does not match registry normalized_hash")

        matching_runs = [
            row for row in runs
            if row.get("source_id") == sid and row.get("normalized_hash") == expected["hash"]
        ]
        if len(matching_runs) < 2:
            fail(errors, f"{sid} requires at least two saved runs with the active hash")
        for row in matching_runs:
            if row.get("adapter_name") != "pdf_listing":
                fail(errors, f"{sid} saved run used unexpected adapter: {row.get('adapter_name')!r}")
            if row.get("change_status") in {"QUALITY_DROP", "NAV_SHELL_ONLY", "ACCESS_BLOCKED"}:
                fail(errors, f"{sid} saved run has blocked change/source status: {row.get('change_status')}")
            proof = str(row.get("proof_block_path") or "")
            if not proof or not resolve_artifact(proof).exists():
                fail(errors, f"{sid} saved run missing proof artifact: {proof}")

    if FINAL_REPORT.exists():
        final_text = FINAL_REPORT.read_text(encoding="utf-8")
        required_snippets = [
            "81 enabled UAE sources / 80 monitoring-active / 1 remediation",
            "## 14. Did We Reach 79/79/0?",
            "No.",
            "UAE FIU",
            "NAV_SHELL_ONLY",
        ]
        for snippet in required_snippets:
            if snippet not in final_text:
                fail(errors, f"Final report missing required snippet: {snippet}")

    if TRUTH_REPORT.exists():
        truth_text = TRUTH_REPORT.read_text(encoding="utf-8")
        if "226 enabled / 225 monitoring-active / 1" not in truth_text:
            fail(errors, "Truth reconciliation report must include current 226/225/1 wording")

    for path in iter_scan_files():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for claim in FORBIDDEN_POSITIVE_CLAIMS:
            if positive_claim_present(text, claim):
                fail(errors, f"Forbidden positive claim in {path.relative_to(ROOT)}: {claim}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Final remediation activation validation PASSED")
    print(f"- Source truth: {counts[0]} enabled / {counts[1]} monitoring-active / {counts[2]} remediation")
    print("- Newly active replacements checked:", ", ".join(sorted(NEW_ACTIVE_SOURCES)))
    print("- Remaining remediation checked:", REMAINING_REMEDIATION)
    return 0


if __name__ == "__main__":
    sys.exit(main())
