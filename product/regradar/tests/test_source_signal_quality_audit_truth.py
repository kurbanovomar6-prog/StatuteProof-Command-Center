import json
import importlib.util
import subprocess
import sys
from pathlib import Path
from unittest import mock


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


# Import the audit validator as a module so a stale-audit rejection can be
# exercised by monkeypatching its AUDIT_JSON path — no subprocess, no mutation
# of the real report file. (Importing does NOT run main(): the module guards it
# behind ``if __name__ == "__main__"``.)
_validator_spec = importlib.util.spec_from_file_location("validate_audit", VALIDATOR_PATH)
_audit_validator = importlib.util.module_from_spec(_validator_spec)
assert _validator_spec and _validator_spec.loader
_validator_spec.loader.exec_module(_audit_validator)


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
        # Catch-all row: every enabled source outside the named families.
        "Other UAE official sources": "Other",
    }
    known_families = tuple(
        family for family in dict.fromkeys(family_key.values()) if family != "Other"
    )

    def belongs(source, validator_family):
        if validator_family == "Other":
            return not any(
                _family_validator.belongs_to(source, known) for known in known_families
            )
        return _family_validator.belongs_to(source, validator_family)

    for family in audit["family_readiness"]:
        validator_family = family_key[family["family"]]
        rows = [source for source in sources if belongs(source, validator_family)]
        # Same mode + alert-eligible definition as the audit headline, so the
        # family rows sum exactly to current_source_truth. Readiness-gate
        # caveats (proof/baseline sync) are disclosed in the row notes.
        fresh_alert = [
            source
            for source in rows
            if source.get("monitoring_mode") == "fresh_alert"
            and source.get("alert_eligible") is True
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


def test_source_signal_quality_family_rows_partition_headline_totals():
    """Family rows (including "Other UAE official sources") must sum exactly to
    the headline current_source_truth — no unclassified remainder, no double
    counting across families."""
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    truth = audit["current_source_truth"]
    rows = audit["family_readiness"]
    for key in (
        "total_enabled",
        "fresh_alert_eligible",
        "evidence_library",
        "candidate",
        "remediation",
    ):
        assert sum(int(row.get(key) or 0) for row in rows) == truth[key], key


def test_every_enabled_source_has_a_monitoring_mode_in_vocabulary():
    """LOW-1 guard: every enabled UAE source must carry one of the four
    monitoring modes; an enabled source with no mode is invisible to the
    coverage accounting."""
    allowed = {"fresh_alert", "evidence_library", "candidate", "remediation"}
    sources = _enabled_uae_sources()
    outside = [
        (source.get("source_id") or source.get("name"), source.get("monitoring_mode"))
        for source in sources
        if source.get("monitoring_mode") not in allowed
    ]
    assert outside == [], outside
    assert sum(
        1 for source in sources if source.get("monitoring_mode") in allowed
    ) == len(sources)


def test_source_signal_quality_audit_validator_accepts_current_truth():
    """Happy path: the validator PASSES (exit 0) against the shipped, in-sync audit."""
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_source_signal_quality_audit_validator_rejects_stale_counts(tmp_path):
    """Feed a DELIBERATELY-stale audit and assert the validator REJECTS it.

    The previous version of this test only re-ran the validator against the good,
    shipped audit and asserted exit 0 — it proved acceptance, never rejection,
    despite its name. Here we corrupt the enabled-source count so it no longer
    matches ``sources.json`` truth and assert a non-zero exit, so the guard
    actually proves the validator catches drift.
    """
    stale_audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    # Corrupt a checked count so it diverges from the sources.json-derived truth.
    stale_audit["current_source_truth"]["total_enabled"] += 4242
    stale_path = tmp_path / "stale_source_signal_quality_audit.json"
    stale_path.write_text(json.dumps(stale_audit), encoding="utf-8")

    # Point the validator at the stale file (real sources.json / frontend paths
    # stay in place, so the ONLY discrepancy is the injected stale count).
    with mock.patch.object(_audit_validator, "AUDIT_JSON", stale_path):
        return_code = _audit_validator.main()

    assert return_code == 1, (
        "validator must REJECT (non-zero exit) an audit whose counts drift from "
        "sources.json truth"
    )


def test_frontend_source_quality_export_matches_safe_audit_claims():
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    frontend = FRONTEND_AUDIT_PATH.read_text(encoding="utf-8")

    # Drift-guard WITHOUT a stale literal: the frontend auditDate must equal the
    # audit JSON's own audit_date — whatever it is — so this guards frontend↔JSON
    # drift but never goes stale when the audit is legitimately re-dated.
    audit_date = str(audit["audit_date"]).strip()
    assert audit_date, "audit JSON must declare a non-empty audit_date"
    assert (
        f"auditDate: '{audit_date}'" in frontend
        or f'auditDate: "{audit_date}"' in frontend
    ), f"frontend auditDate must match audit JSON audit_date ({audit_date!r})"
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
