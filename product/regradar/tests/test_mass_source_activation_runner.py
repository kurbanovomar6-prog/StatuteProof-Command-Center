"""Tests for the safe mass source activation batch runner.

The runner tests use injected functions only. They do not fetch websites, save
evidence, update sources.json, or send messages.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.mass_source_activation_runner import run_mass_source_activation_batch


def _queue(path: Path) -> Path:
    payload = {
        "schema_version": "mass-source-activation-1.0",
        "summary": {
            "queue_entries": 2,
            "activation_ready_count": 0,
            "proof_backed_count": 0,
            "baseline_complete_count": 0,
            "did_reach_50_working_sources": False,
            "sources_json_changed": False,
        },
        "sources": [
            {
                "source_id": "AE-sca-test",
                "url": "https://www.sca.gov.ae/en/regulations/regulations",
                "regulator": "SCA",
                "source_type": "regulations_listing",
                "official_status": "official",
                "discovery_status": "candidate",
                "adapter_family": "listing",
                "adapter_name": "sca_listing",
                "adapter_config": {},
                "no_save_status": "not_run",
                "quality_score": 0,
                "noise_risk": "unknown",
                "source_health_risk": "unknown",
                "evidence_status": "none",
                "baseline_status": "not_started",
                "activation_status": "candidate",
                "failure_code": "",
                "failure_reason": "",
                "remediation_hint": "",
                "agent_gate_status": "hold",
                "current_state": "candidate",
                "proof_path": "",
                "normalized_text_path": "",
                "normalized_hash": "",
                "baseline_runs_completed": 0,
                "baseline_runs_required": 2,
                "can_activate": False,
                "nav_shell": False,
                "shallow_content": False,
                "duplicate_hash": False,
                "source_monitor_gate": {"status": "hold", "reason": "pending", "reviewed_at": "", "blocking_issues": []},
                "evidence_trail_gate": {"status": "hold", "reason": "pending", "reviewed_at": "", "blocking_issues": []},
                "qa_critic_gate": {"status": "hold", "reason": "pending", "reviewed_at": "", "blocking_issues": []},
                "legal_language_gate": {"status": "hold", "reason": "pending", "reviewed_at": "", "blocking_issues": []},
                "product_manager_gate": {"status": "hold", "reason": "pending", "reviewed_at": "", "blocking_issues": []},
                "code_architect_gate": {"status": "hold", "reason": "pending", "reviewed_at": "", "blocking_issues": []},
                "final_activation_gate": {"status": "candidate", "reason": "pending", "reviewed_at": "", "blocking_issues": []},
            },
            {
                "source_id": "AE-dfsa-test",
                "url": "https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/summary",
                "regulator": "DFSA",
                "source_type": "aml_notices_listing",
                "official_status": "official",
                "discovery_status": "candidate",
                "adapter_family": "listing",
                "adapter_name": "dfsa_notice_listing",
                "adapter_config": {},
                "no_save_status": "not_run",
                "quality_score": 0,
                "noise_risk": "unknown",
                "source_health_risk": "unknown",
                "evidence_status": "none",
                "baseline_status": "not_started",
                "activation_status": "candidate",
                "failure_code": "",
                "failure_reason": "",
                "remediation_hint": "",
                "agent_gate_status": "hold",
                "current_state": "candidate",
                "proof_path": "",
                "normalized_text_path": "",
                "normalized_hash": "",
                "baseline_runs_completed": 0,
                "baseline_runs_required": 2,
                "can_activate": False,
                "nav_shell": False,
                "shallow_content": False,
                "duplicate_hash": False,
                "source_monitor_gate": {"status": "hold", "reason": "pending", "reviewed_at": "", "blocking_issues": []},
                "evidence_trail_gate": {"status": "hold", "reason": "pending", "reviewed_at": "", "blocking_issues": []},
                "qa_critic_gate": {"status": "hold", "reason": "pending", "reviewed_at": "", "blocking_issues": []},
                "legal_language_gate": {"status": "hold", "reason": "pending", "reviewed_at": "", "blocking_issues": []},
                "product_manager_gate": {"status": "hold", "reason": "pending", "reviewed_at": "", "blocking_issues": []},
                "code_architect_gate": {"status": "hold", "reason": "pending", "reviewed_at": "", "blocking_issues": []},
                "final_activation_gate": {"status": "candidate", "reason": "pending", "reviewed_at": "", "blocking_issues": []},
            },
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def test_runner_default_no_save_does_not_save_evidence(tmp_path):
    queue_path = _queue(tmp_path / "queue.json")
    calls = []

    def fake_discovery(url, **kwargs):
        return {
            "access_status": "public_candidate",
            "failure_code": "",
            "warnings": [],
            "dom_investigation": {
                "recommended_adapter_family": "listing",
                "recommended_adapter_name": "sca_listing",
                "content_selector": "main",
                "wait_selector": "main",
                "noise_risk": "medium",
                "source_health_risk": "medium",
            },
            "recommended_activation_paths": [{"candidate_url": url}],
        }

    def fake_intake(source, *, write_evidence):
        calls.append(write_evidence)
        return {
            "readiness_status": "CONFIRMED_ACCESSIBLE",
            "status": "CONFIRMED_ACCESSIBLE",
            "quality_score": 84,
            "quality_label": "GOOD",
            "noise_risk": "low",
            "source_health_risk": "low",
            "failure_code": "",
            "failure_reason": "",
            "remediation_hint": "",
            "normalized_hash": "b" * 64,
            "can_save_evidence": True,
            "can_activate_monitoring": False,
            "nav_shell_detected": False,
            "shallow_content": False,
            "duplicate_hash": False,
            "evidence_paths": {},
        }

    summary = run_mass_source_activation_batch(
        queue_path=queue_path,
        regulator="SCA",
        limit=1,
        mode="no-save-only",
        discovery_func=fake_discovery,
        intake_func=fake_intake,
    )

    updated = json.loads(queue_path.read_text(encoding="utf-8"))
    source = updated["sources"][0]
    assert summary["processed_count"] == 1
    assert calls == [False]
    assert source["no_save_status"] == "passed"
    assert source["evidence_status"] == "none"
    assert source["activation_status"] == "no_save_passed"
    assert source["can_activate"] is False


def test_runner_respects_regulator_and_limit(tmp_path):
    queue_path = _queue(tmp_path / "queue.json")
    seen = []

    def fake_discovery(url, **kwargs):
        return {"warnings": [], "recommended_activation_paths": [], "dom_investigation": {}}

    def fake_intake(source, *, write_evidence):
        seen.append(source["source_id"])
        return {"readiness_status": "BLOCKED", "status": "BLOCKED", "quality_score": 0, "failure_code": "ACCESS_BLOCKED"}

    summary = run_mass_source_activation_batch(
        queue_path=queue_path,
        regulator="DFSA",
        limit=1,
        mode="no-save-only",
        discovery_func=fake_discovery,
        intake_func=fake_intake,
    )

    assert seen == ["AE-dfsa-test"]
    assert summary["processed_count"] == 1


def test_runner_refuses_save_when_no_save_fails(tmp_path):
    queue_path = _queue(tmp_path / "queue.json")
    calls = []

    def fake_discovery(url, **kwargs):
        return {"warnings": [], "recommended_activation_paths": [], "dom_investigation": {}}

    def fake_intake(source, *, write_evidence):
        calls.append(write_evidence)
        return {
            "readiness_status": "NAV_SHELL_ONLY",
            "status": "NAV_SHELL_ONLY",
            "quality_score": 20,
            "failure_code": "NAV_SHELL_ONLY",
            "failure_reason": "Navigation shell only.",
            "remediation_hint": "Review selector.",
            "nav_shell_detected": True,
            "evidence_paths": {},
        }

    summary = run_mass_source_activation_batch(
        queue_path=queue_path,
        source_id="AE-sca-test",
        mode="save-passing",
        discovery_func=fake_discovery,
        intake_func=fake_intake,
    )

    updated = json.loads(queue_path.read_text(encoding="utf-8"))
    source = updated["sources"][0]
    assert calls == [False]
    assert summary["saved_evidence_count"] == 0
    assert source["activation_status"] == "remediation"
    assert source["evidence_status"] == "none"


def test_runner_does_not_modify_sources_json(tmp_path):
    queue_path = _queue(tmp_path / "queue.json")
    sources_json = Path(__file__).parent.parent / "sources.json"
    before = sources_json.read_text(encoding="utf-8")

    run_mass_source_activation_batch(
        queue_path=queue_path,
        source_id="AE-sca-test",
        mode="discover-only",
        discovery_func=lambda url, **kwargs: {"warnings": [], "recommended_activation_paths": [], "dom_investigation": {}},
        intake_func=lambda source, *, write_evidence: {},
    )

    assert sources_json.read_text(encoding="utf-8") == before
