#!/usr/bin/env python3
"""Validate the active Source Signal Quality Audit against sources.json truth."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AUDIT_JSON = ROOT / "product" / "regradar" / "reports" / "source_signal_quality_audit.json"
AUDIT_MD = ROOT / "product" / "regradar" / "reports" / "source_signal_quality_audit.md"
FRONTEND_AUDIT = ROOT / "product" / "regradar" / "web" / "src" / "data" / "sourceQualityAudit.ts"
SOURCES_JSON = ROOT / "product" / "regradar" / "sources.json"

AUDIT_FAMILY_TO_VALIDATOR_FAMILY = {
    "CBUAE": "CBUAE",
    "VARA": "VARA",
    "DFSA": "DFSA",
    "DIFC": "DIFC",
    "ADGM/FSRA": "ADGM/FSRA",
    "UAE FIU": "UAE FIU",
    "EOCN / sanctions / TFS": "EOCN/TFS",
    "SCA": "SCA",
    "Ministry of Justice / UAE Legislation / Gazette": "MoJ/Gazette",
    "Ministry of Finance": "MoF",
    "FTA": "FTA",
    "FTA / Tax": "FTA",
    "Ministry of Economy / DNFBP AML": "MoE/DNFBP AML",
    # Catch-all row so the family table partitions the FULL enabled register:
    # every enabled source that matches none of the named families above.
    "Other / international official sources": "Other",
}

# The four allowed monitoring modes. Every ENABLED source must carry exactly
# one of these; an enabled source with no monitoring_mode is unclassified and
# invisible to the coverage accounting, which is how count drift starts.
MONITORING_MODES = ("fresh_alert", "evidence_library", "candidate", "remediation")

_KNOWN_FAMILIES = tuple(
    family
    for family in dict.fromkeys(AUDIT_FAMILY_TO_VALIDATOR_FAMILY.values())
    if family != "Other"
)

# The five family-row keys that must partition-sum to the headline truth.
FAMILY_PARTITION_KEYS = (
    "total_enabled",
    "fresh_alert_eligible",
    "evidence_library",
    "candidate",
    "remediation",
)

REQUIRED_TRUTH_FIELDS = {
    "total_enabled",
    "fresh_alert_eligible",
    "evidence_library",
    "candidate",
    "remediation",
    "source_level_monitor_ok",
    "with_proof_path",
}

FORBIDDEN_STALE_FRAGMENTS = (
    "226 enabled",
    "226 monitored",
    "149 confirmed-live",
    "216 of 226",
    "138 UAE official",
    "157 commercially meaningful",
    "SCA has no MONITOR_OK",
    "EOCN has no MONITOR_OK",
    "0 MONITOR_OK on rulebook",
    "2026-06-19",
    "Source Quality Auditor v1",
    "confirmed-live",
    "174 commercially meaningful",
    "commerciallyMeaningful",
)


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Missing required audit file: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def _enabled_uae_sources() -> list[dict]:
    sources = _load_json(SOURCES_JSON)
    if not isinstance(sources, list):
        raise SystemExit("sources.json must contain a list")
    return [
        source
        for source in sources
        if source.get("jurisdiction") == "AE" and source.get("enabled") is True
    ]


def _expected_truth(sources: list[dict]) -> dict:
    return {
        "total_enabled": len(sources),
        "fresh_alert_eligible": sum(
            1
            for source in sources
            if source.get("monitoring_mode") == "fresh_alert"
            and source.get("alert_eligible") is True
        ),
        "evidence_library": sum(
            1 for source in sources if source.get("monitoring_mode") == "evidence_library"
        ),
        "candidate": sum(1 for source in sources if source.get("monitoring_mode") == "candidate"),
        "remediation": sum(1 for source in sources if source.get("monitoring_mode") == "remediation"),
        "source_level_monitor_ok": sum(
            1 for source in sources if source.get("last_monitor_status") == "MONITOR_OK"
        ),
        "with_proof_path": sum(1 for source in sources if source.get("proof_path")),
    }


def _haystack(source: dict) -> str:
    return " ".join(
        str(source.get(key) or "")
        for key in ("source_id", "name", "url", "official_url", "family", "category", "notes")
    ).lower()


def _belongs_to(source: dict, family: str) -> bool:
    text = _haystack(source)
    source_id = str(source.get("source_id") or "").lower()
    url = str(source.get("url") or "").lower()
    name = str(source.get("name") or "").lower()
    if family == "Other":
        return not any(_belongs_to(source, known) for known in _KNOWN_FAMILIES)
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
            or "uaeiec.gov.ae" in url
            or "eocn" in source_id
            or "uaeiec" in source_id
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
        # A source that already belongs to EOCN/TFS (e.g. the MoE-owned targeted
        # financial sanctions page) is counted there, never twice — the family
        # table must PARTITION the register, not overlap it.
        if _belongs_to(source, "EOCN/TFS"):
            return False
        # Same partition rule for MoJ-owned DNFBP-supervisor sources (e.g. the
        # MoJ AML/CFT legislation page whose notes mention DNFBPs): counted
        # under MoJ/Gazette, never twice.
        if _belongs_to(source, "MoJ/Gazette"):
            return False
        return "moec.gov.ae" in url or "moet" in source_id or "dnfbp" in text or "ministry of economy" in name
    return False


def _fresh_alert_eligible(source: dict) -> bool:
    # Same definition as the headline current_source_truth.fresh_alert_eligible
    # (mode + alert_eligible), so family rows SUM to the headline exactly.
    # Full readiness-gate caveats (proof/baseline sync) stay in the row notes.
    return (
        source.get("monitoring_mode") == "fresh_alert"
        and source.get("alert_eligible") is True
    )


def _expected_family_readiness(sources: list[dict], family: str) -> dict:
    rows = [source for source in sources if _belongs_to(source, family)]
    fresh = [source for source in rows if _fresh_alert_eligible(source)]
    return {
        "total_enabled": len(rows),
        "fresh_alert_eligible": len(fresh),
        "evidence_library": sum(
            1 for source in rows if source.get("monitoring_mode") == "evidence_library"
        ),
        "candidate": sum(1 for source in rows if source.get("monitoring_mode") == "candidate"),
        "remediation": sum(1 for source in rows if source.get("monitoring_mode") == "remediation"),
    }


def _check(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    failures: list[str] = []
    audit = _load_json(AUDIT_JSON)
    sources = _enabled_uae_sources()
    expected = _expected_truth(sources)

    # Every ENABLED source must sit inside the monitoring_mode vocabulary, and
    # the four modes must PARTITION the enabled total — no unclassified sources.
    outside_vocabulary = [
        f"{source.get('source_id') or source.get('name') or 'unknown'}"
        f" (monitoring_mode={source.get('monitoring_mode')!r})"
        for source in sources
        if source.get("monitoring_mode") not in MONITORING_MODES
    ]
    _check(
        not outside_vocabulary,
        failures,
        "enabled sources outside the monitoring_mode vocabulary "
        f"{MONITORING_MODES}: {outside_vocabulary}",
    )
    mode_partition_total = sum(
        1 for source in sources if source.get("monitoring_mode") in MONITORING_MODES
    )
    _check(
        mode_partition_total == expected["total_enabled"],
        failures,
        f"monitoring_mode partition sums to {mode_partition_total}, "
        f"expected the enabled total {expected['total_enabled']}",
    )

    truth = audit.get("current_source_truth")
    _check(isinstance(truth, dict), failures, "audit must contain current_source_truth object")

    if isinstance(truth, dict):
        missing = sorted(REQUIRED_TRUTH_FIELDS - set(truth))
        _check(not missing, failures, f"current_source_truth missing fields: {missing}")
        for key, expected_value in expected.items():
            actual_value = truth.get(key)
            _check(
                actual_value == expected_value,
                failures,
                f"{key}={actual_value!r}, expected {expected_value!r} from sources.json",
            )

    safe_claims = audit.get("safe_claims", [])
    forbidden_claims = audit.get("forbidden_claims", [])
    _check(isinstance(safe_claims, list) and safe_claims, failures, "safe_claims must be non-empty")
    _check(
        isinstance(forbidden_claims, list) and forbidden_claims,
        failures,
        "forbidden_claims must be non-empty",
    )

    family_readiness = audit.get("family_readiness")
    _check(
        isinstance(family_readiness, list) and family_readiness,
        failures,
        "family_readiness must be non-empty",
    )
    if isinstance(family_readiness, list):
        for family_row in family_readiness:
            family_name = family_row.get("family")
            validator_family = AUDIT_FAMILY_TO_VALIDATOR_FAMILY.get(str(family_name))
            _check(
                validator_family is not None,
                failures,
                f"unknown family_readiness family: {family_name!r}",
            )
            if not validator_family:
                continue
            expected_family = _expected_family_readiness(sources, validator_family)
            for key, expected_value in expected_family.items():
                actual_value = family_row.get(key)
                _check(
                    actual_value == expected_value,
                    failures,
                    f"{family_name} {key}={actual_value!r}, expected {expected_value!r} from sources.json",
                )

        # The family table must partition the enabled register: summing every
        # family row (including "Other / international official sources") must reproduce
        # the headline truth exactly — no gap, no double counting.
        for key in FAMILY_PARTITION_KEYS:
            family_sum = sum(int(row.get(key) or 0) for row in family_readiness)
            _check(
                family_sum == expected[key],
                failures,
                f"family_readiness rows sum to {key}={family_sum}, "
                f"expected headline {expected[key]} from sources.json",
            )

    audit_text = AUDIT_MD.read_text(encoding="utf-8") if AUDIT_MD.exists() else ""
    frontend_text = FRONTEND_AUDIT.read_text(encoding="utf-8") if FRONTEND_AUDIT.exists() else ""
    serialized = json.dumps(audit, sort_keys=True)
    for stale in FORBIDDEN_STALE_FRAGMENTS:
        _check(stale not in audit_text, failures, f"stale fragment in markdown: {stale}")
        _check(stale not in serialized, failures, f"stale fragment in json: {stale}")
        _check(stale not in frontend_text, failures, f"stale fragment in frontend audit: {stale}")

    # Derive the expected auditDate from the audit JSON itself so the frontend
    # drift-guard checks frontend↔JSON consistency without pinning a literal date
    # that goes stale on every legitimate re-audit.
    audit_date = str(audit.get("audit_date") or "").strip()
    _check(bool(audit_date), failures, "audit JSON missing audit_date")

    _check(frontend_text, failures, f"missing frontend audit export: {FRONTEND_AUDIT}")
    if frontend_text:
        _check(
            bool(audit_date)
            and (
                f"auditDate: '{audit_date}'" in frontend_text
                or f'auditDate: "{audit_date}"' in frontend_text
            ),
            failures,
            f"frontend audit auditDate must match audit JSON audit_date ({audit_date!r})",
        )
        _check(
            "StatuteProof Source Quality Auditor v2" in frontend_text,
            failures,
            "frontend audit must expose auditor v2",
        )
        for key, expected_value in expected.items():
            frontend_key = {
                "total_enabled": "totalEnabled",
                "fresh_alert_eligible": "freshAlertEligible",
                "evidence_library": "evidenceLibraryOnly",
                "candidate": "candidate",
                "remediation": "remediation",
                "source_level_monitor_ok": "sourceLevelMonitorOk",
                "with_proof_path": "withProofPath",
            }[key]
            _check(
                f"{frontend_key}: {expected_value}" in frontend_text,
                failures,
                f"frontend audit {frontend_key} does not match sources.json truth {expected_value}",
            )
        for claim in safe_claims:
            _check(
                claim in frontend_text,
                failures,
                f"frontend audit missing safe claim from JSON: {claim}",
            )

    if failures:
        print("Source signal quality audit validation FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Source signal quality audit validation PASSED")
    print(
        "Current truth: "
        f"{expected['total_enabled']} enabled / "
        f"{expected['fresh_alert_eligible']} fresh-alert / "
        f"{expected['evidence_library']} evidence-library / "
        f"{expected['candidate']} candidate / "
        f"{expected['remediation']} remediation"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
