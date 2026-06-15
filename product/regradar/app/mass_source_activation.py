"""Mass source activation queue safety helpers.

This module does not fetch websites, save evidence, update sources.json, or send
alerts. It only normalizes queue entries and evaluates whether a source can move
through the activation state machine.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any


CANDIDATE = "candidate"
DISCOVERED = "discovered"
NO_SAVE_PASSED = "no_save_passed"
PROOF_SAVED = "proof_saved"
BASELINE_PENDING = "baseline_pending"
ACTIVATION_READY = "activation_ready"
REMEDIATION = "remediation"
BLOCKED = "blocked"
REJECTED = "rejected"

SOURCE_STATES = {
    CANDIDATE,
    DISCOVERED,
    NO_SAVE_PASSED,
    PROOF_SAVED,
    BASELINE_PENDING,
    ACTIVATION_READY,
    REMEDIATION,
    BLOCKED,
    REJECTED,
}

REQUIRED_GATES = (
    "source_monitor_gate",
    "evidence_trail_gate",
    "qa_critic_gate",
    "legal_language_gate",
    "product_manager_gate",
    "code_architect_gate",
)

PASSING_NO_SAVE_STATUSES = {
    "passed",
    "pass",
    "confirmed_accessible",
    "readiness_supported",
    "no_save_passed",
}

PROOF_STATUSES = {
    "proof_saved",
    "saved",
    "certified_evidence",
    "full_evidence",
}

OFFICIAL_STATUSES = {
    "official",
    "official_domain",
    "officially_linked",
    "confirmed_official",
}


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _gate(status: str, reason: str, blocking_issues: list[str] | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "reason": reason,
        "reviewed_at": "",
        "blocking_issues": blocking_issues or [],
    }


def _hold_gate(reason: str, blocking_issues: list[str] | None = None) -> dict[str, Any]:
    return _gate("hold", reason, blocking_issues)


def build_queue_entry(
    *,
    source_id: str,
    url: str,
    regulator: str,
    source_type: str,
    official_status: str = "unknown",
    discovery_status: str = CANDIDATE,
    adapter_family: str = "",
    adapter_name: str = "",
    adapter_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an inactive mass activation queue entry with strict default gates."""
    reason = "Candidate only; no no-save, proof, baseline, or activation gate has passed."
    entry = {
        "source_id": source_id,
        "url": url,
        "regulator": regulator,
        "source_type": source_type,
        "official_status": official_status,
        "discovery_status": discovery_status,
        "adapter_family": adapter_family,
        "adapter_name": adapter_name,
        "adapter_config": adapter_config or {},
        "no_save_status": "not_run",
        "quality_score": 0,
        "noise_risk": "unknown",
        "source_health_risk": "unknown",
        "evidence_status": "none",
        "baseline_status": "not_started",
        "activation_status": CANDIDATE,
        "failure_code": "",
        "failure_reason": "",
        "remediation_hint": "Run discovery, DOM investigation, no-save test, proof save, repeat baseline, and agent gates before activation.",
        "agent_gate_status": "hold",
        "current_state": CANDIDATE,
        "proof_path": "",
        "normalized_text_path": "",
        "raw_artifact_path": "",
        "rendered_artifact_path": "",
        "normalized_hash": "",
        "baseline_runs_completed": 0,
        "baseline_runs_required": 2,
        "can_activate": False,
        "nav_shell": False,
        "shallow_content": False,
        "duplicate_hash": False,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "source_monitor_gate": _hold_gate("Officialness and source quality require Source Monitor review.", ["source_monitor_review_required"]),
        "evidence_trail_gate": _hold_gate("Proof and repeat baseline are missing.", ["proof_missing", "baseline_missing"]),
        "qa_critic_gate": _hold_gate("No no-save/proof/baseline QA gate has passed.", ["qa_review_required"]),
        "legal_language_gate": _hold_gate("Candidate must not be described as ready or validated.", ["ready_claim_forbidden"]),
        "product_manager_gate": _hold_gate("MLRO/CCO relevance requires review.", ["buyer_relevance_review_required"]),
        "code_architect_gate": _hold_gate("Adapter strategy has not been tested.", ["adapter_test_required"]),
        "final_activation_gate": _gate(CANDIDATE, reason, ["no_save_not_run", "proof_missing", "baseline_incomplete"]),
    }
    return evaluate_activation(entry)


def _status(value: Any) -> str:
    return str(value or "").strip().lower()


def _has_completed_baseline(entry: dict[str, Any]) -> bool:
    completed = int(entry.get("baseline_runs_completed") or 0)
    required = int(entry.get("baseline_runs_required") or 2)
    return _status(entry.get("baseline_status")) == "complete" or completed >= required


def _has_proof(entry: dict[str, Any]) -> bool:
    return bool(entry.get("proof_path")) and _status(entry.get("evidence_status")) in PROOF_STATUSES


def _required_gates_pass(entry: dict[str, Any]) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    for gate_name in REQUIRED_GATES:
        gate = entry.get(gate_name) or {}
        if _status(gate.get("status")) != "pass":
            blockers.append(f"{gate_name}_not_passed")
    return not blockers, blockers


def _derive_hold_status(entry: dict[str, Any], blockers: list[str]) -> str:
    current_state = _status(entry.get("current_state"))
    existing_activation = _status(entry.get("activation_status"))
    if current_state == REJECTED or existing_activation == REJECTED or "source_rejected" in blockers:
        return REJECTED
    if current_state == BLOCKED or existing_activation == BLOCKED or "access_blocked" in blockers:
        return BLOCKED
    if _has_proof(entry) and not _has_completed_baseline(entry):
        return BASELINE_PENDING
    if _status(entry.get("evidence_status")) in PROOF_STATUSES:
        return PROOF_SAVED
    if _status(entry.get("no_save_status")) in PASSING_NO_SAVE_STATUSES:
        return NO_SAVE_PASSED
    if current_state in SOURCE_STATES:
        return current_state
    return CANDIDATE


def evaluate_activation(entry: dict[str, Any]) -> dict[str, Any]:
    """Evaluate activation readiness without mutating the input entry."""
    evaluated = deepcopy(entry)
    blockers: list[str] = []

    current_state = _status(evaluated.get("current_state"))
    official_status = _status(evaluated.get("official_status"))
    no_save_status = _status(evaluated.get("no_save_status"))
    quality_score = float(evaluated.get("quality_score") or 0)

    if current_state == REJECTED or official_status in {"rejected", "unofficial", "off_domain"}:
        blockers.append("source_rejected")
    elif official_status not in OFFICIAL_STATUSES:
        blockers.append("official_status_unconfirmed")

    if current_state == BLOCKED or _status(evaluated.get("failure_code")) in {"access_blocked", "likely_waf_403"}:
        blockers.append("access_blocked")

    if no_save_status not in PASSING_NO_SAVE_STATUSES:
        blockers.append("no_save_not_passed")

    if not evaluated.get("adapter_family") or not evaluated.get("adapter_name"):
        blockers.append("adapter_strategy_missing")

    if quality_score < 60:
        blockers.append("quality_below_threshold")

    if evaluated.get("nav_shell") is True:
        blockers.append("nav_shell")
    if evaluated.get("shallow_content") is True:
        blockers.append("shallow_content")
    if evaluated.get("duplicate_hash") is True:
        blockers.append("duplicate_hash")

    if _status(evaluated.get("noise_risk")) == "high":
        blockers.append("high_noise_risk")
    if _status(evaluated.get("source_health_risk")) == "high":
        blockers.append("high_source_health_risk")

    if not _has_proof(evaluated):
        blockers.append("proof_missing")
    if not _has_completed_baseline(evaluated):
        blockers.append("baseline_incomplete")

    gates_pass, gate_blockers = _required_gates_pass(evaluated)
    if not gates_pass:
        blockers.extend(gate_blockers)

    unique_blockers = list(dict.fromkeys(blockers))
    if not unique_blockers:
        evaluated["activation_status"] = ACTIVATION_READY
        evaluated["current_state"] = ACTIVATION_READY
        evaluated["can_activate"] = True
        evaluated["agent_gate_status"] = "pass"
        evaluated["final_activation_gate"] = {
            "status": ACTIVATION_READY,
            "reason": "Proof, repeat baseline, source quality, risk review, and required agent gates passed.",
            "reviewed_at": _now_iso(),
            "blocking_issues": [],
        }
    else:
        hold_status = _derive_hold_status(evaluated, unique_blockers)
        evaluated["activation_status"] = hold_status
        evaluated["can_activate"] = False
        evaluated["agent_gate_status"] = "hold"
        evaluated["final_activation_gate"] = {
            "status": hold_status,
            "reason": "Activation is blocked until all proof, baseline, source-health, quality, and agent gates pass.",
            "reviewed_at": _now_iso(),
            "blocking_issues": unique_blockers,
        }

    evaluated["updated_at"] = _now_iso()
    return evaluated
