#!/usr/bin/env python3
"""Validate that newly promoted UAE rows are not unvalidated active sources."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGRADAR_ROOT = ROOT / "product/regradar"
SOURCES_FILE = REGRADAR_ROOT / "sources.json"
BULK_ACTIVATION_SET = ROOT / "docs/weak-family-final-activation-set.json"
WEAK_FAMILY_25_SET = ROOT / "docs/weak-family-25-each-final-activation-set.json"

STRICT_EIGHT_SOURCE_IDS = {
    "AE-fta-tax-legislation-listing",
    "AE-fta-vat-guides-references",
    "AE-fta-corporate-tax-guides-references",
    "AE-fta-media-centre",
    "AE-fta-corporate-tax-legislation",
    "AE-adgm-fsra-supervision-circulars",
    "AE-adgm-fsra-regulatory-alerts",
    "AE-adgm-data-protection-regulations-2021-pdf",
}

EXPECTED_ACTIVE = {
    "AE-adgm-fsra-supervision-circulars": {
        "hash": "6c1e3f3f4634f70efc0e61fd627649059dd23ea6fcd4f53ab23240e7bfdeef00",
        "adapter": "adgm_fsra_listing",
    },
    "AE-adgm-data-protection-regulations-2021-pdf": {
        "hash": "cdaa340d5523440c1b15bb8b3d11f78b0e330e0a7c53fb68c01606ff8b44d6d5",
        "adapter": "pdf_document",
    },
}

EXPECTED_CANDIDATES = STRICT_EIGHT_SOURCE_IDS - set(EXPECTED_ACTIVE)

EXPECTED_COUNTS = (147, 146, 1)

CLAIM_SCAN_PATHS = [
    ROOT / "README.md",
    ROOT / "START_HERE.md",
    ROOT / "product/regradar/web/src",
    ROOT / "docs/fta-adgm-eight-source-truth-repair-final-report.md",
    ROOT / "docs/unvalidated-active-source-row-audit.md",
]

FORBIDDEN_POSITIVE = (
    "complete uae coverage",
    "guaranteed compliance",
    "perfect parsing",
    "never miss updates",
    "official regulator certified",
)


def _load_sources() -> list[dict]:
    with SOURCES_FILE.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("sources.json must be a list")
    return [item for item in data if isinstance(item, dict)]


def _sid(source: dict) -> str:
    return str(source.get("source_id") or source.get("id") or "")


def _artifact_exists(path_value: str) -> bool:
    if not path_value:
        return False
    path = Path(path_value)
    if path.is_absolute():
        return path.exists()
    return (REGRADAR_ROOT / path).exists()


def _scan_files() -> list[Path]:
    files: list[Path] = []
    for path in CLAIM_SCAN_PATHS:
        if path.is_dir():
            files.extend(child for child in path.rglob("*") if child.is_file())
        elif path.exists():
            files.append(path)
    return files


def _safe_context(line: str) -> bool:
    lowered = line.lower()
    safe_markers = (
        "do not",
        "not claim",
        "does not claim",
        "forbidden",
        "blocked",
        "candidate",
        "not counted",
        "not monitoring-active",
        "not legal advice",
    )
    return any(marker in lowered for marker in safe_markers)


def main() -> int:
    errors: list[str] = []
    sources = _load_sources()
    by_id = {_sid(source): source for source in sources}
    bulk_final_ids: set[str] = set()
    if BULK_ACTIVATION_SET.exists():
        bulk_data = json.loads(BULK_ACTIVATION_SET.read_text(encoding="utf-8"))
        bulk_final_ids = {
            str(row.get("source_id"))
            for row in bulk_data.get("final", [])
            if isinstance(row, dict) and row.get("source_id")
        }
    fta_final_ids: set[str] = set()
    if WEAK_FAMILY_25_SET.exists():
        fta_data = json.loads(WEAK_FAMILY_25_SET.read_text(encoding="utf-8"))
        fta_final_ids = {
            str(row.get("source_id"))
            for row in fta_data.get("specs", [])
            if isinstance(row, dict) and row.get("source_id")
        }

    enabled_ae = [
        source for source in sources
        if source.get("jurisdiction") == "AE" and source.get("enabled") is True
    ]
    active = [source for source in enabled_ae if source.get("status") == "active"]
    remediation = [source for source in enabled_ae if source.get("status") == "remediation"]
    counts = (len(enabled_ae), len(active), len(remediation))
    if counts != EXPECTED_COUNTS:
        errors.append(f"Expected source truth {EXPECTED_COUNTS}, got {counts}")

    for source in active:
        sid = _sid(source)
        if not sid:
            errors.append(f"Active source lacks source_id: {source.get('name')}")
        if not source.get("url"):
            errors.append(f"Active source lacks official URL: {sid or source.get('name')}")
        notes = str(source.get("notes") or "").lower()
        if "no-save" in notes and "candidate" not in notes and "activated" not in notes:
            errors.append(f"Active source appears no-save-only: {sid}")

    for sid, expected in EXPECTED_ACTIVE.items():
        source = by_id.get(sid)
        if not source:
            errors.append(f"Missing expected active repaired source: {sid}")
            continue
        if source.get("enabled") is not True or source.get("status") != "active":
            errors.append(f"{sid} must be enabled active after proof-backed repair")
        if source.get("adapter_name") != expected["adapter"] or source.get("adapter_family") != expected["adapter"]:
            errors.append(f"{sid} adapter mismatch")
        if source.get("normalized_hash") != expected["hash"]:
            errors.append(f"{sid} normalized_hash mismatch")
        if int(source.get("baseline_runs_completed") or 0) < 2:
            errors.append(f"{sid} requires baseline_runs_completed >= 2")
        if source.get("last_monitor_status") != "MONITOR_OK":
            errors.append(f"{sid} requires last_monitor_status=MONITOR_OK")
        if not _artifact_exists(str(source.get("proof_path") or "")):
            errors.append(f"{sid} proof_path missing or nonexistent")
        if not _artifact_exists(str(source.get("normalized_text_path") or "")):
            errors.append(f"{sid} normalized_text_path missing or nonexistent")
        notes = str(source.get("notes") or "").lower()
        for marker in ("monitoring intelligence only", "not legal advice", "monitor_ok"):
            if marker not in notes:
                errors.append(f"{sid} notes missing legal/gate marker: {marker}")

    if len(bulk_final_ids) != 41:
        errors.append(f"Expected 41 weak-family bulk activations, got {len(bulk_final_ids)}")
    if len(fta_final_ids) != 25:
        errors.append(f"Expected 25 FTA weak-family 25-each activations, got {len(fta_final_ids)}")

    for sid in sorted(bulk_final_ids):
        source = by_id.get(sid)
        if not source:
            errors.append(f"Missing weak-family bulk active source: {sid}")
            continue
        if source.get("enabled") is not True or source.get("status") != "active":
            errors.append(f"{sid} must be enabled active after proof-backed bulk activation")
        if int(source.get("baseline_runs_completed") or 0) < 2:
            errors.append(f"{sid} requires baseline_runs_completed >= 2")
        if source.get("last_monitor_status") != "MONITOR_OK":
            errors.append(f"{sid} requires last_monitor_status=MONITOR_OK")
        if not source.get("normalized_hash"):
            errors.append(f"{sid} requires normalized_hash")
        if not _artifact_exists(str(source.get("proof_path") or "")):
            errors.append(f"{sid} proof_path missing or nonexistent")
        if not _artifact_exists(str(source.get("normalized_text_path") or "")):
            errors.append(f"{sid} normalized_text_path missing or nonexistent")
        notes = str(source.get("notes") or "").lower()
        for marker in ("monitoring intelligence only", "not legal advice", "monitor_ok"):
            if marker not in notes:
                errors.append(f"{sid} notes missing legal/gate marker: {marker}")

    for sid in sorted(fta_final_ids):
        source = by_id.get(sid)
        if not source:
            errors.append(f"Missing FTA weak-family active source: {sid}")
            continue
        if source.get("enabled") is not True or source.get("status") != "active":
            errors.append(f"{sid} must be enabled active after proof-backed FTA activation")
        if source.get("adapter_name") != "pdf_document" or source.get("adapter_family") != "pdf_document":
            errors.append(f"{sid} must use pdf_document adapter")
        if int(source.get("baseline_runs_completed") or 0) < 2:
            errors.append(f"{sid} requires baseline_runs_completed >= 2")
        if source.get("last_monitor_status") != "MONITOR_OK":
            errors.append(f"{sid} requires last_monitor_status=MONITOR_OK")
        if not source.get("normalized_hash"):
            errors.append(f"{sid} requires normalized_hash")
        if not _artifact_exists(str(source.get("proof_path") or "")):
            errors.append(f"{sid} proof_path missing or nonexistent")
        if not _artifact_exists(str(source.get("normalized_text_path") or "")):
            errors.append(f"{sid} normalized_text_path missing or nonexistent")
        notes = str(source.get("notes") or "").lower()
        for marker in ("monitoring intelligence only", "not legal advice", "monitor_ok"):
            if marker not in notes:
                errors.append(f"{sid} notes missing legal/gate marker: {marker}")

    for sid in sorted(EXPECTED_CANDIDATES):
        source = by_id.get(sid)
        if not source:
            errors.append(f"Missing demoted candidate source: {sid}")
            continue
        if source.get("status") == "active" or source.get("enabled") is True:
            errors.append(f"{sid} must not remain enabled active after failed gates")
        notes = str(source.get("notes") or "").lower()
        if "candidate" not in notes or "not legal advice" not in notes:
            errors.append(f"{sid} candidate notes must explain held status and legal boundary")
        if sid.startswith("AE-fta") and "nav-shell" not in notes:
            errors.append(f"{sid} notes must explain FTA nav-shell blocker")

    scan_texts: list[tuple[Path, str]] = []
    for path in _scan_files():
        try:
            scan_texts.append((path, path.read_text(encoding="utf-8", errors="ignore")))
        except OSError:
            continue

    for path, text in scan_texts:
        for line_no, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            for claim in FORBIDDEN_POSITIVE:
                if claim in lowered and not _safe_context(line):
                    errors.append(f"Unsafe claim {claim!r} in {path.relative_to(ROOT)}:{line_no}")
            if re.search(r"FTA\s+tax\s+legislation\s+and\s+guides", line, flags=re.I) and not _safe_context(line):
                errors.append(f"FTA tax pages must not be claimed active in {path.relative_to(ROOT)}:{line_no}")
            if re.search(r"FTA.*status:\s*['\"]active['\"]", line):
                errors.append(f"FTA source-family card marks FTA active in {path.relative_to(ROOT)}:{line_no}")

    if errors:
        print("validate_no_unvalidated_active_sources: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("validate_no_unvalidated_active_sources: PASS")
    print("Source truth: 147 enabled / 146 monitoring-active / 1 remediation")
    print("Eight-row repair: 2 active, 6 candidates, 0 unvalidated active rows")
    print("Weak-family bulk activation: 41 active, 0 unvalidated active rows")
    print("FTA weak-family activation: 25 active, 0 unvalidated active rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
