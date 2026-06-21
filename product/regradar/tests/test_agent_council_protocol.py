import copy
import importlib.util
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR_PATH = REPO_ROOT / "tools" / "validate_agent_council_protocol.py"
PROTOCOL_PATH = REPO_ROOT / "product" / "regradar" / "config" / "agent_council_protocol.json"
BLACKBOARD_PATH = REPO_ROOT / "product" / "regradar" / "config" / "agent_council_blackboard.json"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_agent_council_protocol", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _valid_protocol() -> dict:
    return {
        "schema_version": "1.0",
        "max_active_agents": 10,
        "active_agents": [
            {"agent_id": "chief-of-staff", "role": "Chief of Staff", "modes": ["Council Router / Orchestrator"]},
            {"agent_id": "product-manager", "role": "Product Manager", "modes": ["Pilot/Beta/Production Readiness Gate"]},
            {"agent_id": "code-architect", "role": "Code Architect", "modes": ["Agent Systems Architect"]},
            {"agent_id": "qa-critic", "role": "QA / Critic", "modes": ["External CTO Scorer"]},
            {"agent_id": "legal-language", "role": "Legal Language", "modes": ["Claims Gate"]},
            {"agent_id": "source-monitor", "role": "Source Monitor", "modes": ["Source Truth Gate"]},
            {"agent_id": "evidence-trail", "role": "Evidence Trail", "modes": ["Evidence Corpus Auditor"]},
            {
                "agent_id": "risk-brief-pipeline",
                "role": "Risk + Brief Pipeline",
                "modes": ["Customer Delivery Gate"],
            },
            {"agent_id": "icp-lead-research", "role": "ICP Lead Research", "modes": ["Market/GTM Scorer"]},
            {"agent_id": "outreach-writer", "role": "Outreach Writer", "modes": ["Prompt Router / Handoff Scribe"]},
        ],
        "allowed_task_statuses": ["proposed", "in_progress", "review", "blocked", "done"],
        "allowed_verdicts": ["PASS", "HOLD", "FAIL"],
        "required_task_fields": [
            "task_id",
            "owner_agent",
            "reviewer_agents",
            "current_phase",
            "score_before",
            "target_score",
            "actual_score_after",
            "evidence_required",
            "validation_commands",
            "handoff_packets",
            "prompt_packets",
            "blockers",
            "stop_condition",
        ],
        "required_packet_fields": [
            "verdict",
            "score_impact",
            "evidence_found",
            "files_inspected",
            "commands_run",
            "findings",
            "blocker_reason",
            "prompt_for_next_agent",
            "questions_for_next_agent",
            "stop_continue_recommendation",
        ],
        "domain_gates": {
            "evidence": ["Evidence Trail"],
            "customer_copy": ["Legal Language"],
            "brief_delivery": ["Risk + Brief Pipeline"],
            "source_activation": ["Source Monitor"],
            "done": ["QA / Critic"],
        },
        "autonomy_limits": {
            "max_agents_per_wave": 3,
            "max_implementation_loops_per_commit": 2,
            "background_loops_allowed": False,
        },
        "safety_rules": [
            "No deploy.",
            "No secrets print.",
            "No access-control bypass.",
            "No fake MONITOR_OK.",
            "No complete coverage claim.",
        ],
        "scoring_dimensions": [
            {"dimension": "evidence_integrity", "max_score": 100},
            {"dimension": "source_monitoring_truth", "max_score": 100},
            {"dimension": "customer_delivery_readiness", "max_score": 100},
        ],
    }


def _packet(agent: str, verdict: str = "PASS", score: int = 75) -> dict:
    return {
        "packet_id": f"packet-{agent.lower().replace(' ', '-')}",
        "from_agent": agent,
        "to_agent": "QA / Critic" if agent != "QA / Critic" else "Chief of Staff",
        "verdict": verdict,
        "task_score": score,
        "score_impact": {"before": 35, "after": score, "delta": score - 35},
        "evidence_found": ["protocol fixture evidence"],
        "files_inspected": ["product/regradar/config/agent_council_protocol.json"],
        "commands_run": [{"command": "python3 tools/validate_agent_council_protocol.py", "exit_code": 0}],
        "findings": {"P0": [], "P1": [], "P2": []},
        "blocker_reason": "" if verdict == "PASS" else "Exact blocker reason.",
        "prompt_for_next_agent": "Review the governed agent council packet and answer every required gate question.",
        "questions_for_next_agent": ["Does this packet satisfy the required gate schema?"],
        "stop_continue_recommendation": "continue" if verdict == "PASS" else "stop",
    }


def _prompt_packet() -> dict:
    return {
        "packet_id": "prompt-001",
        "from_agent": "Outreach Writer",
        "to_agent": "Evidence Trail",
        "task_id": "agent-os-protocol-simulation",
        "context": "Dry-run protocol simulation only.",
        "hard_rules": ["No deploy.", "No secrets print."],
        "questions": ["Can this evidence gate be verified from files and commands?"],
        "expected_output_format": ["verdict", "evidence_found", "prompt_for_next_agent"],
    }


def _valid_blackboard() -> dict:
    return {
        "schema_version": "1.0",
        "protocol_version": "1.0",
        "current_wave": "simulation",
        "tasks": [
            {
                "task_id": "agent-os-protocol-simulation",
                "status": "done",
                "owner_agent": "Chief of Staff",
                "reviewer_agents": ["Evidence Trail", "QA / Critic"],
                "domains": ["evidence"],
                "current_phase": "review_qa",
                "score_before": 35,
                "target_score": 70,
                "actual_score_after": 76,
                "evidence_required": ["protocol fixture evidence"],
                "validation_commands": [
                    {
                        "command": "python3 tools/validate_agent_council_protocol.py",
                        "exit_code": 0,
                        "run_at": "2026-06-21T00:00:00Z",
                    }
                ],
                "handoff_packets": [_packet("Evidence Trail"), _packet("QA / Critic", score=76)],
                "prompt_packets": [_prompt_packet()],
                "blockers": [],
                "proof": ["product/regradar/config/agent_council_protocol.json"],
                "stop_condition": "Stop if any required packet is missing or incomplete.",
            }
        ],
    }


def test_default_agent_council_protocol_files_validate():
    validator = _load_validator()

    assert validator.validate_files(PROTOCOL_PATH, BLACKBOARD_PATH) == []


def test_protocol_rejects_unsupported_eleventh_active_agent():
    validator = _load_validator()
    protocol = _valid_protocol()
    protocol["active_agents"].append({"agent_id": "security-tooling-auditor", "role": "Security/Tooling Auditor", "modes": []})

    errors = validator.validate_payloads(protocol, _valid_blackboard())

    assert any("max_active_agents" in error for error in errors)
    assert any("unsupported active agent role" in error for error in errors)


def test_done_task_requires_qa_score():
    validator = _load_validator()
    blackboard = _valid_blackboard()
    for packet in blackboard["tasks"][0]["handoff_packets"]:
        if packet["from_agent"] == "QA / Critic":
            packet.pop("task_score")

    errors = validator.validate_payloads(_valid_protocol(), blackboard)

    assert any("QA / Critic packet must include task_score" in error for error in errors)


def test_pass_packet_requires_files_commands_and_next_prompt():
    validator = _load_validator()
    blackboard = _valid_blackboard()
    packet = blackboard["tasks"][0]["handoff_packets"][0]
    packet["files_inspected"] = []
    packet["commands_run"] = []
    packet["prompt_for_next_agent"] = ""

    errors = validator.validate_payloads(_valid_protocol(), blackboard)

    assert any("PASS packet must include files_inspected" in error for error in errors)
    assert any("PASS packet must include commands_run" in error for error in errors)
    assert any("prompt_for_next_agent" in error for error in errors)


def test_evidence_domain_done_task_requires_evidence_trail_pass():
    validator = _load_validator()
    blackboard = _valid_blackboard()
    blackboard["tasks"][0]["handoff_packets"] = [_packet("QA / Critic", score=76)]

    errors = validator.validate_payloads(_valid_protocol(), blackboard)

    assert any("missing required gate packet from Evidence Trail" in error for error in errors)


def test_blocked_task_with_hold_packet_and_exact_blocker_is_valid():
    validator = _load_validator()
    blackboard = _valid_blackboard()
    task = blackboard["tasks"][0]
    task["status"] = "blocked"
    task["actual_score_after"] = 44
    task["blockers"] = ["Agent runtime thread limit reached; fresh subagents unavailable."]
    task["handoff_packets"] = [_packet("QA / Critic", verdict="HOLD", score=44)]

    errors = validator.validate_payloads(_valid_protocol(), blackboard)

    assert errors == []


def test_done_task_without_validation_result_is_rejected():
    validator = _load_validator()
    blackboard = _valid_blackboard()
    blackboard["tasks"][0]["validation_commands"][0]["exit_code"] = 1

    errors = validator.validate_payloads(_valid_protocol(), blackboard)

    assert any("validation command did not pass" in error for error in errors)


def test_missing_prompt_packet_blocks_done_task():
    validator = _load_validator()
    blackboard = _valid_blackboard()
    blackboard["tasks"][0]["prompt_packets"] = []

    errors = validator.validate_payloads(_valid_protocol(), blackboard)

    assert any("prompt_packets" in error for error in errors)
