"""Tests for mass source activation queue safety.

These tests are local only. They do not fetch live websites or write evidence.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.mass_source_activation import (
    ACTIVATION_READY,
    BASELINE_PENDING,
    CANDIDATE,
    NO_SAVE_PASSED,
    PROOF_SAVED,
    build_queue_entry,
    evaluate_activation,
)


def _pass_gate(reason: str = "Reviewed and acceptable.") -> dict:
    return {
        "status": "pass",
        "reason": reason,
        "reviewed_at": "2026-06-15T00:00:00Z",
        "blocking_issues": [],
    }


def _activation_ready_entry() -> dict:
    entry = build_queue_entry(
        source_id="AE-test-official-regulation",
        url="https://www.example.gov.ae/en/regulations/aml",
        regulator="Example UAE Regulator",
        source_type="regulation",
        official_status="official",
        discovery_status="discovered",
        adapter_family="static_html",
        adapter_name="static_html",
        adapter_config={"content_selector": "main"},
    )
    entry.update(
        {
            "current_state": PROOF_SAVED,
            "no_save_status": "passed",
            "quality_score": 92,
            "noise_risk": "low",
            "source_health_risk": "low",
            "evidence_status": "proof_saved",
            "proof_path": "product/regradar/data/source_runs/example/proof.json",
            "normalized_text_path": "product/regradar/data/source_runs/example/normalized.txt",
            "normalized_hash": "a" * 64,
            "baseline_status": "complete",
            "baseline_runs_completed": 2,
            "baseline_runs_required": 2,
            "nav_shell": False,
            "shallow_content": False,
            "duplicate_hash": False,
            "source_monitor_gate": _pass_gate(),
            "evidence_trail_gate": _pass_gate(),
            "qa_critic_gate": _pass_gate(),
            "legal_language_gate": _pass_gate(),
            "product_manager_gate": _pass_gate(),
            "code_architect_gate": _pass_gate(),
        }
    )
    return entry


def test_candidate_queue_entry_is_inactive_by_default():
    entry = build_queue_entry(
        source_id="AE-test-source",
        url="https://www.example.gov.ae/source",
        regulator="Example UAE Regulator",
        source_type="guidance",
    )

    evaluated = evaluate_activation(entry)

    assert evaluated["current_state"] == CANDIDATE
    assert evaluated["activation_status"] == CANDIDATE
    assert evaluated["can_activate"] is False
    assert evaluated["final_activation_gate"]["status"] == CANDIDATE
    assert "proof_missing" in evaluated["final_activation_gate"]["blocking_issues"]


def test_no_save_passed_cannot_claim_evidence_or_activation():
    entry = build_queue_entry(
        source_id="AE-test-no-save",
        url="https://www.example.gov.ae/source",
        regulator="Example UAE Regulator",
        source_type="guidance",
        official_status="official",
    )
    entry.update(
        {
            "current_state": NO_SAVE_PASSED,
            "no_save_status": "passed",
            "quality_score": 88,
            "noise_risk": "low",
            "source_health_risk": "low",
            "evidence_status": "none",
            "baseline_status": "not_started",
        }
    )

    evaluated = evaluate_activation(entry)

    assert evaluated["activation_status"] != ACTIVATION_READY
    assert evaluated["can_activate"] is False
    assert "proof_missing" in evaluated["final_activation_gate"]["blocking_issues"]
    assert "baseline_incomplete" in evaluated["final_activation_gate"]["blocking_issues"]


def test_proof_saved_without_repeat_baseline_blocks_activation():
    entry = _activation_ready_entry()
    entry["baseline_runs_completed"] = 1
    entry["baseline_status"] = BASELINE_PENDING

    evaluated = evaluate_activation(entry)

    assert evaluated["activation_status"] == BASELINE_PENDING
    assert evaluated["can_activate"] is False
    assert "baseline_incomplete" in evaluated["final_activation_gate"]["blocking_issues"]


def test_activation_ready_requires_all_gates_and_proof_paths():
    entry = _activation_ready_entry()

    evaluated = evaluate_activation(entry)

    assert evaluated["activation_status"] == ACTIVATION_READY
    assert evaluated["can_activate"] is True
    assert evaluated["final_activation_gate"]["status"] == ACTIVATION_READY


def test_high_noise_or_source_health_risk_blocks_activation():
    noisy = _activation_ready_entry()
    noisy["noise_risk"] = "high"
    unhealthy = _activation_ready_entry()
    unhealthy["source_health_risk"] = "high"

    evaluated_noisy = evaluate_activation(noisy)
    evaluated_unhealthy = evaluate_activation(unhealthy)

    assert evaluated_noisy["activation_status"] != ACTIVATION_READY
    assert "high_noise_risk" in evaluated_noisy["final_activation_gate"]["blocking_issues"]
    assert evaluated_unhealthy["activation_status"] != ACTIVATION_READY
    assert "high_source_health_risk" in evaluated_unhealthy["final_activation_gate"]["blocking_issues"]


def test_rejected_source_cannot_activate_even_with_other_fields_present():
    entry = _activation_ready_entry()
    entry["official_status"] = "rejected"
    entry["current_state"] = "rejected"

    evaluated = evaluate_activation(entry)

    assert evaluated["activation_status"] == "rejected"
    assert evaluated["can_activate"] is False
    assert "source_rejected" in evaluated["final_activation_gate"]["blocking_issues"]
