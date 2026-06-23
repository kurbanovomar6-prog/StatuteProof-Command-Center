"""
Extended tests for app/alert_drafts.py — covers remaining uncovered branches:
  - affected_entities_for() — all source-specific branches
  - recommended_action_for() — all source-specific branches
  - build_alert_draft() — key dict structure, alert_id format, field types
  - _why_it_matters() — all branch paths
  - render_alert_markdown() — changed_chunks and removed_chunks rendering
  - write_alert_artifacts() — via tmp_path (no production file writes)
  - snapshot_dir_from_proof() and load_json_artifact() edge cases
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from app.alert_drafts import (
    affected_entities_for,
    recommended_action_for,
    build_alert_draft,
    render_alert_markdown,
    write_alert_artifacts,
    snapshot_dir_from_proof,
    load_json_artifact,
    _why_it_matters,
    REVIEW_STATUS,
    SEND_DECISION,
)
from app.proof import DISCLAIMER


# ── helpers ───────────────────────────────────────────────────────────────────

def _run(source_name: str = "Test Source", source_id: str = "AE-test") -> dict:
    return {
        "run_id": "run-xyz",
        "source_id": source_id,
        "source_name": source_name,
        "market": "AE",
        "jurisdiction": "AE",
        "timestamp_utc": "2026-06-23T08:00:00+00:00",
        "change_status": "CHANGED",
        "official_url": "https://example.gov.ae/",
    }


def _diff(added: list[str] | None = None, quality: str = "GOOD") -> dict:
    added = added or ["Updated compliance guidance for regulated firms."]
    return {
        "diff_quality": quality,
        "meaningful_change_detected": True,
        "added_chunks": added,
        "removed_chunks": [],
        "changed_chunks": [],
        "added_count": len(added),
        "removed_count": 0,
        "changed_count": 0,
        "diff_summary": f"{len(added)} added",
    }


def _proof(quality: str = "GOOD") -> dict:
    return {
        "official_url": "https://example.gov.ae/",
        "final_url": "https://example.gov.ae/",
        "normalized_hash": "cafebabe01234567",
        "proof_quality": quality,
        "limitations_notes": "",
    }


# ── affected_entities_for ─────────────────────────────────────────────────────

def test_affected_entities_for_vara_source_returns_vasp_text():
    run = _run("Dubai Virtual Assets Regulatory Authority (VARA)", "AE-vara")
    result = affected_entities_for(run, "LICENSING")
    assert "VASP" in result or "VASPs" in result


def test_affected_entities_for_cbuae_source_returns_payment_provider_text():
    run = _run("Central Bank of the UAE", "AE-cbuae")
    result = affected_entities_for(run, "CIRCULAR_UPDATE")
    assert "Payment service providers" in result or "payment" in result.lower()


def test_affected_entities_for_dfsa_source_returns_difc_text():
    run = _run("DFSA Publications", "AE-dfsa")
    result = affected_entities_for(run, "GUIDANCE_UPDATE")
    assert "DIFC" in result


def test_affected_entities_for_difc_source_returns_difc_text():
    run = _run("DIFC Courts", "AE-difc")
    result = affected_entities_for(run, "GENERAL_UPDATE")
    assert "DIFC" in result


def test_affected_entities_for_adgm_source_returns_adgm_text():
    run = _run("ADGM Regulatory Authority", "AE-adgm")
    result = affected_entities_for(run, "GUIDANCE_UPDATE")
    assert "ADGM" in result


def test_affected_entities_for_fsra_source_returns_adgm_or_fsra_text():
    run = _run("FSRA Notices", "AE-fsra")
    result = affected_entities_for(run, "CIRCULAR_UPDATE")
    assert "ADGM" in result or "FSRA" in result


def test_affected_entities_for_aml_cft_change_type_returns_mlro_text():
    run = _run("Generic Source", "AE-generic")
    result = affected_entities_for(run, "AML_CFT")
    assert "MLRO" in result or "AML" in result


def test_affected_entities_for_tax_change_type_returns_finance_teams_text():
    run = _run("Ministry of Finance", "AE-finance")
    result = affected_entities_for(run, "TAX")
    assert "tax" in result.lower() or "finance" in result.lower()


def test_affected_entities_for_unknown_source_returns_fallback_text():
    run = _run("Obscure Regulatory Body", "AE-unknown")
    result = affected_entities_for(run, "GENERAL_UPDATE")
    assert "manual classification" in result.lower() or "regulated firms" in result.lower()


# ── recommended_action_for ────────────────────────────────────────────────────

def test_recommended_action_for_review_risk_level_returns_manual_review():
    run = _run()
    result = recommended_action_for(run, "AML_CFT", "REVIEW")
    assert "Manual compliance" in result or "manual" in result.lower()


def test_recommended_action_for_vara_source_returns_vasp_guidance():
    run = _run("Dubai VARA Authority", "AE-vara")
    result = recommended_action_for(run, "LICENSING", "HIGH")
    assert "custody" in result.lower() or "licensing" in result.lower() or "vara" in result.lower()


def test_recommended_action_for_cbuae_source_returns_payment_guidance():
    run = _run("Central Bank UAE", "AE-cbuae")
    result = recommended_action_for(run, "CIRCULAR_UPDATE", "MEDIUM")
    assert "payment" in result.lower() or "licensing" in result.lower()


def test_recommended_action_for_dfsa_source_returns_rulebook_guidance():
    run = _run("DFSA Rulebook", "AE-dfsa")
    result = recommended_action_for(run, "RULEBOOK_UPDATE", "MEDIUM")
    assert "DFSA" in result or "rulebook" in result.lower()


def test_recommended_action_for_adgm_source_returns_fsra_guidance():
    run = _run("ADGM FSRA", "AE-adgm")
    result = recommended_action_for(run, "CIRCULAR_UPDATE", "MEDIUM")
    assert "FSRA" in result or "ADGM" in result


def test_recommended_action_for_aml_change_type_returns_aml_guidance():
    run = _run("Generic Body", "AE-generic")
    result = recommended_action_for(run, "AML_CFT", "MEDIUM")
    assert "AML" in result or "suspicious transaction" in result.lower()


def test_recommended_action_for_unknown_change_type_returns_fallback():
    run = _run("Unknown Source", "AE-unknown")
    result = recommended_action_for(run, "GENERAL_UPDATE", "LOW")
    assert len(result) > 10


# ── _why_it_matters ───────────────────────────────────────────────────────────

def test_why_it_matters_returns_review_message_for_review_risk_level():
    result = _why_it_matters("AML_CFT", "REVIEW")
    assert "human review" in result.lower() or "reliable" in result.lower()


def test_why_it_matters_returns_regulatory_impact_for_aml_cft():
    result = _why_it_matters("AML_CFT", "HIGH")
    assert "obligation" in result.lower() or "regulatory" in result.lower()


def test_why_it_matters_returns_regulatory_impact_for_rulebook_update():
    result = _why_it_matters("RULEBOOK_UPDATE", "MEDIUM")
    assert "obligation" in result.lower() or "licensing" in result.lower()


def test_why_it_matters_returns_future_signal_for_consultation():
    result = _why_it_matters("CONSULTATION", "MEDIUM")
    assert "future" in result.lower() or "supervisory" in result.lower()


def test_why_it_matters_returns_future_signal_for_guidance_update():
    result = _why_it_matters("GUIDANCE_UPDATE", "MEDIUM")
    assert "future" in result.lower() or "supervisory" in result.lower()


def test_why_it_matters_returns_generic_fallback_for_enforcement():
    result = _why_it_matters("ENFORCEMENT", "LOW")
    assert len(result) > 10


# ── build_alert_draft — required keys and types ───────────────────────────────

def test_build_alert_draft_returns_dict_with_all_required_keys():
    required_keys = {
        "alert_id", "review_status", "send_decision", "source_id",
        "source_name", "change_type", "risk_level", "risk_rationale",
        "what_changed", "added_chunks", "removed_chunks", "changed_chunks",
        "affected_entities", "why_it_matters", "recommended_action",
        "confidence", "limitations", "proof_block", "not_legal_advice_disclaimer",
    }
    alert = build_alert_draft(_run("VARA Regulator", "AE-vara"), _diff(), _proof())
    for key in required_keys:
        assert key in alert, f"Missing key: {key}"


def test_build_alert_draft_alert_id_is_non_empty_string():
    alert = build_alert_draft(_run(), _diff(), _proof())
    assert isinstance(alert["alert_id"], str)
    assert len(alert["alert_id"]) > 0


def test_build_alert_draft_alert_id_starts_with_draft_prefix():
    alert = build_alert_draft(_run(), _diff(), _proof())
    assert alert["alert_id"].startswith("draft-")


def test_build_alert_draft_alert_id_is_deterministic_for_same_inputs():
    run = _run("VARA Regulator", "AE-vara-001")
    proof = _proof()
    proof["normalized_hash"] = "fixed-hash-for-test"
    diff = _diff()
    alert1 = build_alert_draft(run, diff, proof)
    alert2 = build_alert_draft(run, diff, proof)
    assert alert1["alert_id"] == alert2["alert_id"]


def test_build_alert_draft_review_status_is_draft():
    alert = build_alert_draft(_run(), _diff(), _proof())
    assert alert["review_status"] == REVIEW_STATUS


def test_build_alert_draft_send_decision_is_hold_for_review():
    alert = build_alert_draft(_run(), _diff(), _proof())
    assert alert["send_decision"] == SEND_DECISION


def test_build_alert_draft_risk_level_is_one_of_known_values():
    alert = build_alert_draft(_run(), _diff(), _proof())
    assert alert["risk_level"] in {"HIGH", "MEDIUM", "LOW", "REVIEW"}


def test_build_alert_draft_limitations_is_list():
    alert = build_alert_draft(_run(), _diff(), _proof())
    assert isinstance(alert["limitations"], list)


def test_build_alert_draft_includes_disclaimer():
    alert = build_alert_draft(_run(), _diff(), _proof())
    assert DISCLAIMER in alert["not_legal_advice_disclaimer"]


def test_build_alert_draft_what_changed_uses_diff_summary_when_available():
    diff = _diff()
    diff["diff_summary"] = "5 new regulatory obligations detected."
    alert = build_alert_draft(_run(), diff, _proof())
    assert "5 new regulatory obligations" in alert["what_changed"]


def test_build_alert_draft_what_changed_falls_back_when_no_summary():
    diff = _diff()
    diff.pop("diff_summary", None)
    alert = build_alert_draft(_run(), diff, _proof())
    assert isinstance(alert["what_changed"], str)
    assert len(alert["what_changed"]) > 0


def test_build_alert_draft_includes_proof_block():
    proof = _proof()
    alert = build_alert_draft(_run(), _diff(), proof)
    assert alert["proof_block"] is proof


def test_build_alert_draft_source_id_matches_run():
    run = _run("CBUAE", "AE-cbuae-test")
    alert = build_alert_draft(run, _diff(), _proof())
    assert alert["source_id"] == "AE-cbuae-test"


def test_build_alert_draft_limitations_from_proof_included():
    proof = _proof()
    proof["limitations_notes"] = "PDF rendering was partial."
    alert = build_alert_draft(_run(), _diff(), proof)
    assert "PDF rendering was partial." in alert["limitations"]


def test_build_alert_draft_limitations_from_diff_included():
    diff = _diff()
    diff["limitations"] = ["Diff truncated at 200 chunks."]
    alert = build_alert_draft(_run(), diff, _proof())
    assert "Diff truncated at 200 chunks." in alert["limitations"]


# ── render_alert_markdown — changed/removed chunk rendering ───────────────────

def test_render_alert_markdown_includes_removed_excerpt_when_removed_chunks_present():
    diff = _diff()
    diff["removed_chunks"] = ["Old compliance obligation text."]
    alert = build_alert_draft(_run(), diff, _proof())
    md = render_alert_markdown(alert)
    assert "Removed Excerpt" in md
    assert "Old compliance obligation text." in md


def test_render_alert_markdown_includes_changed_excerpt_when_changed_chunks_present():
    diff = _diff()
    diff["changed_chunks"] = [{"before": ["old text here"], "after": ["new text here"]}]
    diff["added_count"] = 0
    alert = build_alert_draft(_run(), diff, _proof())
    md = render_alert_markdown(alert)
    assert "Changed Excerpt" in md
    assert "old text here" in md
    assert "new text here" in md


def test_render_alert_markdown_limitations_section_present_when_empty():
    alert = build_alert_draft(_run(), _diff(), _proof())
    alert["limitations"] = []
    md = render_alert_markdown(alert)
    assert "Limitations" in md
    assert "None recorded" in md


# ── write_alert_artifacts ─────────────────────────────────────────────────────

def test_write_alert_artifacts_creates_json_and_md_files(tmp_path):
    alert = build_alert_draft(_run(), _diff(), _proof())
    snapshot_dir = tmp_path / "snapshot"
    result = write_alert_artifacts(alert, snapshot_dir)
    assert Path(result["alert_draft_json_path"]).exists() or (snapshot_dir / "alert_draft.json").exists()
    assert (snapshot_dir / "alert_draft.md").exists()


def test_write_alert_artifacts_json_is_valid_json(tmp_path):
    alert = build_alert_draft(_run(), _diff(), _proof())
    snapshot_dir = tmp_path / "snapshot2"
    write_alert_artifacts(alert, snapshot_dir)
    json_file = snapshot_dir / "alert_draft.json"
    data = json.loads(json_file.read_text(encoding="utf-8"))
    assert data["review_status"] == "DRAFT"


def test_write_alert_artifacts_md_contains_draft_banner(tmp_path):
    alert = build_alert_draft(_run(), _diff(), _proof())
    snapshot_dir = tmp_path / "snapshot3"
    write_alert_artifacts(alert, snapshot_dir)
    md_content = (snapshot_dir / "alert_draft.md").read_text(encoding="utf-8")
    assert "DRAFT" in md_content


# ── snapshot_dir_from_proof ───────────────────────────────────────────────────

def test_snapshot_dir_from_proof_returns_parent_of_normalized_path(tmp_path):
    proof = {
        "snapshot_normalized_path": str(tmp_path / "snapshots" / "norm.txt"),
    }
    result = snapshot_dir_from_proof(proof, tmp_path)
    assert result is not None
    assert "snapshots" in str(result)


def test_snapshot_dir_from_proof_returns_parent_of_raw_path_when_no_normalized(tmp_path):
    proof = {
        "snapshot_normalized_path": None,
        "snapshot_raw_path": str(tmp_path / "snapshots" / "raw.html"),
    }
    result = snapshot_dir_from_proof(proof, tmp_path)
    assert result is not None


def test_snapshot_dir_from_proof_returns_none_when_no_paths():
    proof = {}
    result = snapshot_dir_from_proof(proof, Path("/tmp"))
    assert result is None


# ── load_json_artifact ────────────────────────────────────────────────────────

def test_load_json_artifact_returns_empty_dict_when_path_is_none():
    result = load_json_artifact(None, Path("/tmp"))
    assert result == {}


def test_load_json_artifact_returns_empty_dict_when_file_does_not_exist(tmp_path):
    result = load_json_artifact(str(tmp_path / "nonexistent.json"), tmp_path)
    assert result == {}


def test_load_json_artifact_returns_parsed_dict_when_file_exists(tmp_path):
    data = {"key": "value", "count": 42}
    artifact = tmp_path / "artifact.json"
    artifact.write_text(json.dumps(data), encoding="utf-8")
    result = load_json_artifact(str(artifact), tmp_path)
    assert result == data


def test_load_json_artifact_resolves_relative_paths_against_base_dir(tmp_path):
    data = {"source_id": "AE-test"}
    artifact = tmp_path / "data" / "result.json"
    artifact.parent.mkdir()
    artifact.write_text(json.dumps(data), encoding="utf-8")
    result = load_json_artifact("data/result.json", tmp_path)
    assert result["source_id"] == "AE-test"
