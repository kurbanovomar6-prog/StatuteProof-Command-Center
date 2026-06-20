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


def _check(condition: bool, failures: list[str], message: str) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    failures: list[str] = []
    audit = _load_json(AUDIT_JSON)
    sources = _enabled_uae_sources()
    expected = _expected_truth(sources)

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

    audit_text = AUDIT_MD.read_text(encoding="utf-8") if AUDIT_MD.exists() else ""
    frontend_text = FRONTEND_AUDIT.read_text(encoding="utf-8") if FRONTEND_AUDIT.exists() else ""
    serialized = json.dumps(audit, sort_keys=True)
    for stale in FORBIDDEN_STALE_FRAGMENTS:
        _check(stale not in audit_text, failures, f"stale fragment in markdown: {stale}")
        _check(stale not in serialized, failures, f"stale fragment in json: {stale}")
        _check(stale not in frontend_text, failures, f"stale fragment in frontend audit: {stale}")

    _check(frontend_text, failures, f"missing frontend audit export: {FRONTEND_AUDIT}")
    if frontend_text:
        _check(
            "auditDate: '2026-06-20'" in frontend_text,
            failures,
            "frontend audit must expose auditDate 2026-06-20",
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
