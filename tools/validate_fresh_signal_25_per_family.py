#!/usr/bin/env python3
"""Validate Strong Fresh Signal family counts and blocker disclosure."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "product/regradar/sources.json"
FINAL_REPORT = ROOT / "docs/fresh-signal-25-per-family-final-report.md"
FRONTEND_AUDIT = ROOT / "product/regradar/web/src/data/sourceQualityAudit.ts"

TARGET_FAMILIES = (
    "CBUAE",
    "VARA",
    "DFSA",
    "DIFC",
    "ADGM/FSRA",
    "UAE FIU",
    "EOCN/TFS",
    "SCA",
    "MoJ/Gazette",
    "MoF",
    "FTA",
    "MoE/DNFBP AML",
)


def is_ae_source(source: dict) -> bool:
    source_id = str(source.get("source_id") or "")
    return source.get("jurisdiction") == "AE" or source_id.startswith("AE-")


def haystack(source: dict) -> str:
    return " ".join(
        str(source.get(key) or "")
        for key in ("source_id", "name", "url", "official_url", "family", "category", "notes")
    ).lower()


def belongs_to(source: dict, family: str) -> bool:
    text = haystack(source)
    source_id = str(source.get("source_id") or "").lower()
    url = str(source.get("url") or "").lower()
    name = str(source.get("name") or "").lower()
    if family == "CBUAE":
        return "centralbank.ae" in url or "cbuae" in source_id or "central bank" in name
    if family == "VARA":
        return "vara.ae" in url or source_id.startswith("ae-vara") or "virtual assets regulatory authority" in name
    if family == "DFSA":
        return "dfsa.ae" in url or "dfsaen.thomsonreuters.com" in url or source_id.startswith("ae-dfsa") or "dubai financial services authority" in name
    if family == "DIFC":
        return "difc.com" in url or "assets.difc.com" in url or source_id.startswith("ae-difc")
    if family == "ADGM/FSRA":
        return "adgm.com" in url or source_id.startswith("ae-adgm") or "fsra" in source_id or "fsra" in name
    if family == "UAE FIU":
        return "uaefiu.gov.ae" in url or source_id.startswith("ae-uaefiu") or "financial intelligence unit" in name
    if family == "EOCN/TFS":
        return (
            "eocn.gov.ae" in url
            or "eocn" in source_id
            or source_id.startswith("ae-moet-targeted-financial-sanctions")
            or ("moet-dnfbp" in source_id and ("tfs" in text or "sanction" in text))
        )
    if family == "SCA":
        return "sca.gov.ae" in url or source_id.startswith("ae-sca") or "securities and commodities authority" in name
    if family == "MoJ/Gazette":
        return "uaelegislation.gov.ae" in url or "moj.gov.ae" in url or "official gazette" in text or "legislation portal" in name
    if family == "MoF":
        return "mof.gov.ae" in url or source_id.startswith("ae-mof") or name == "uae ministry of finance"
    if family == "FTA":
        return "tax.gov.ae" in url or source_id.startswith("ae-fta") or "federal tax authority" in name
    if family == "MoE/DNFBP AML":
        return "moec.gov.ae" in url or "moet" in source_id or "dnfbp" in text or "ministry of economy" in name
    return False


def main() -> int:
    sources = json.loads(SOURCES.read_text())
    enabled_ae = [source for source in sources if source.get("enabled") and is_ae_source(source)]
    failures: list[str] = []
    family_counts: dict[str, int] = {}

    for family in TARGET_FAMILIES:
        rows = [source for source in enabled_ae if belongs_to(source, family)]
        fresh = [
            source for source in rows
            if source.get("monitoring_mode") == "fresh_alert"
            and source.get("alert_eligible") is True
            and source.get("last_monitor_status") == "MONITOR_OK"
            and source.get("proof_path")
            and source.get("normalized_text_path")
            and source.get("normalized_hash")
            and int(source.get("baseline_runs_completed") or 0) >= int(source.get("baseline_runs_required") or 2)
            and source.get("recommended_check_frequency") == "daily"
        ]
        family_counts[family] = len(fresh)

    final_text = FINAL_REPORT.read_text(encoding="utf-8", errors="ignore") if FINAL_REPORT.exists() else ""
    lower_final = final_text.lower()

    for family, count in family_counts.items():
        if count >= 25:
            continue
        family_key = family.lower()
        if family_key not in lower_final:
            failures.append(f"{family}: below 25 ({count}) and missing final-report section")
        if "blocker" not in lower_final and "remaining gap" not in lower_final:
            failures.append(f"{family}: below 25 ({count}) and final report lacks blocker/gap language")

    frontend = FRONTEND_AUDIT.read_text(encoding="utf-8", errors="ignore").lower()
    for family, count in family_counts.items():
        if count < 25 and f"{family.lower()} strong" in frontend:
            failures.append(f"{family}: frontend appears to label family Strong despite count {count}")

    if failures:
        print("validate_fresh_signal_25_per_family: FAIL")
        for failure in failures:
            print(f"- {failure}")
        print("family_counts=" + json.dumps(family_counts, sort_keys=True))
        return 1

    print("validate_fresh_signal_25_per_family: PASS")
    print("family_counts=" + json.dumps(family_counts, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
