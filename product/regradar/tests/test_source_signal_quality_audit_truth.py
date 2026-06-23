import json
import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCES_PATH = ROOT / "product" / "regradar" / "sources.json"
AUDIT_PATH = ROOT / "product" / "regradar" / "reports" / "source_signal_quality_audit.json"
FRONTEND_AUDIT_PATH = ROOT / "product" / "regradar" / "web" / "src" / "data" / "sourceQualityAudit.ts"
VALIDATOR_PATH = ROOT / "product" / "regradar" / "reports" / "validate_audit.py"
FAMILY_VALIDATOR_PATH = ROOT / "tools" / "validate_fresh_signal_25_per_family.py"


_family_spec = importlib.util.spec_from_file_location(
    "validate_fresh_signal_25_per_family",
    FAMILY_VALIDATOR_PATH,
)
_family_validator = importlib.util.module_from_spec(_family_spec)
assert _family_spec and _family_spec.loader
_family_spec.loader.exec_module(_family_validator)


def _enabled_uae_sources() -> list[dict]:
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    return [
        source
        for source in sources
        if source.get("jurisdiction") == "AE" and source.get("enabled") is True
    ]


def test_source_signal_quality_audit_matches_current_registry_truth():
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    sources = _enabled_uae_sources()

    expected_modes = {
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
        "remediation": sum(
            1 for source in sources if source.get("monitoring_mode") == "remediation"
        ),
    }

    truth = audit["current_source_truth"]
    assert truth["total_enabled"] == len(sources)
    assert truth["fresh_alert_eligible"] == expected_modes["fresh_alert_eligible"]
    assert truth["evidence_library"] == expected_modes["evidence_library"]
    assert truth["candidate"] == expected_modes["candidate"]
    assert truth["remediation"] == expected_modes["remediation"]


def test_source_signal_quality_family_readiness_matches_registry_truth():
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    sources = _enabled_uae_sources()
    family_key = {
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
    }

    for family in audit["family_readiness"]:
        validator_family = family_key[family["family"]]
        rows = [
            source
            for source in sources
            if _family_validator.belongs_to(source, validator_family)
        ]
        fresh_alert = [
            source
            for source in rows
            if source.get("monitoring_mode") == "fresh_alert"
            and source.get("alert_eligible") is True
            and source.get("last_monitor_status") == "MONITOR_OK"
            and source.get("proof_path")
            and source.get("normalized_text_path")
            and source.get("normalized_hash")
            and int(source.get("baseline_runs_completed") or 0)
            >= int(source.get("baseline_runs_required") or 2)
            and source.get("recommended_check_frequency") == "daily"
        ]

        assert family["total_enabled"] == len(rows), family["family"]
        assert family["fresh_alert_eligible"] == len(fresh_alert), family["family"]
        assert family["evidence_library"] == sum(
            1 for source in rows if source.get("monitoring_mode") == "evidence_library"
        ), family["family"]
        assert family["candidate"] == sum(
            1 for source in rows if source.get("monitoring_mode") == "candidate"
        ), family["family"]
        assert family["remediation"] == sum(
            1 for source in rows if source.get("monitoring_mode") == "remediation"
        ), family["family"]


def test_source_signal_quality_audit_validator_rejects_stale_counts():
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_frontend_source_quality_export_matches_safe_audit_claims():
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    frontend = FRONTEND_AUDIT_PATH.read_text(encoding="utf-8")

    assert "auditDate: '2026-06-21'" in frontend or 'auditDate: "2026-06-21"' in frontend
    assert "StatuteProof Source Quality Auditor v2" in frontend
    assert "2026-06-19" not in frontend
    assert "confirmed-live" not in frontend
    assert "174 commercially meaningful" not in frontend
    assert "commerciallyMeaningful" not in frontend

    truth = audit["current_source_truth"]
    assert f"totalEnabled: {truth['total_enabled']}" in frontend
    assert f"freshAlertEligible: {truth['fresh_alert_eligible']}" in frontend
    assert f"evidenceLibraryOnly: {truth['evidence_library']}" in frontend
    assert f"candidate: {truth['candidate']}" in frontend
    assert f"remediation: {truth['remediation']}" in frontend
    for claim in audit["safe_claims"]:
        assert claim in frontend
