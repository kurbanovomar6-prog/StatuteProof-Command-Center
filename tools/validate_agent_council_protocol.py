#!/usr/bin/env python3
"""Validate the governed StatuteProof Agent Council protocol and blackboard."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL_PATH = ROOT / "product" / "regradar" / "config" / "agent_council_protocol.json"
DEFAULT_BLACKBOARD_PATH = ROOT / "product" / "regradar" / "config" / "agent_council_blackboard.json"

CANONICAL_AGENT_ROLES = frozenset(
    {
        "Chief of Staff",
        "Product Manager",
        "Code Architect",
        "QA / Critic",
        "Legal Language",
        "Source Monitor",
        "Evidence Trail",
        "Risk + Brief Pipeline",
        "ICP Lead Research",
        "Outreach Writer",
    }
)

DONE_STATUS = "done"
BLOCKED_STATUS = "blocked"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _is_int_in_range(value: Any, lower: int = 0, upper: int = 100) -> bool:
    return isinstance(value, int) and lower <= value <= upper


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def _packet_agent(packet: dict[str, Any]) -> str:
    value = packet.get("from_agent")
    return value if isinstance(value, str) else ""


def _packet_verdict(packet: dict[str, Any]) -> str:
    value = packet.get("verdict")
    return value if isinstance(value, str) else ""


def _task_label(task: dict[str, Any]) -> str:
    return str(task.get("task_id", "<missing-task-id>"))


def validate_protocol(protocol: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    max_agents = protocol.get("max_active_agents")
    active_agents = _as_list(protocol.get("active_agents"))

    if max_agents != 10:
        errors.append("protocol.max_active_agents must be exactly 10")
    if len(active_agents) > 10:
        errors.append(f"active_agents count {len(active_agents)} exceeds max_active_agents=10")

    seen_ids: set[str] = set()
    seen_roles: set[str] = set()
    for index, agent in enumerate(active_agents):
        if not isinstance(agent, dict):
            errors.append(f"active_agents[{index}] must be an object")
            continue
        agent_id = agent.get("agent_id")
        role = agent.get("role")
        if not isinstance(agent_id, str) or not agent_id.strip():
            errors.append(f"active_agents[{index}].agent_id is required")
        elif agent_id in seen_ids:
            errors.append(f"duplicate active agent id: {agent_id}")
        else:
            seen_ids.add(agent_id)
        if role not in CANONICAL_AGENT_ROLES:
            errors.append(f"unsupported active agent role: {role}")
        elif role in seen_roles:
            errors.append(f"duplicate active agent role: {role}")
        else:
            seen_roles.add(role)
        modes = agent.get("modes", [])
        if not isinstance(modes, list):
            errors.append(f"active_agents[{index}].modes must be a list because modes are not active agents")

    if len(seen_roles) != len(CANONICAL_AGENT_ROLES):
        missing = sorted(CANONICAL_AGENT_ROLES - seen_roles)
        extra = sorted(seen_roles - CANONICAL_AGENT_ROLES)
        if missing:
            errors.append(f"active roster is missing canonical roles: {', '.join(missing)}")
        if extra:
            errors.append(f"active roster has extra roles: {', '.join(extra)}")

    if not _string_list(protocol.get("allowed_verdicts")):
        errors.append("protocol.allowed_verdicts must be a non-empty string list")
    if not _string_list(protocol.get("required_task_fields")):
        errors.append("protocol.required_task_fields must be a non-empty string list")
    if not _string_list(protocol.get("required_packet_fields")):
        errors.append("protocol.required_packet_fields must be a non-empty string list")
    if not isinstance(protocol.get("domain_gates"), dict):
        errors.append("protocol.domain_gates must be an object")

    limits = protocol.get("autonomy_limits", {})
    if not isinstance(limits, dict):
        errors.append("protocol.autonomy_limits must be an object")
    else:
        if limits.get("background_loops_allowed") is not False:
            errors.append("autonomy_limits.background_loops_allowed must be false")
        if limits.get("max_agents_per_wave") != 3:
            errors.append("autonomy_limits.max_agents_per_wave must be 3")
        if limits.get("max_implementation_loops_per_commit") != 2:
            errors.append("autonomy_limits.max_implementation_loops_per_commit must be 2")

    if not _string_list(protocol.get("safety_rules")):
        errors.append("protocol.safety_rules must list enforced safety rules")
    if not _as_list(protocol.get("scoring_dimensions")):
        errors.append("protocol.scoring_dimensions must be non-empty")

    return errors


def _validate_packet(
    task_id: str,
    packet: dict[str, Any],
    *,
    allowed_verdicts: set[str],
    required_packet_fields: list[str],
) -> list[str]:
    errors: list[str] = []
    for field in required_packet_fields:
        if field not in packet:
            errors.append(f"{task_id}: handoff packet missing required field {field}")

    agent = _packet_agent(packet)
    if agent not in CANONICAL_AGENT_ROLES:
        errors.append(f"{task_id}: packet from unsupported agent {agent!r}")

    verdict = _packet_verdict(packet)
    if verdict not in allowed_verdicts:
        errors.append(f"{task_id}: packet verdict {verdict!r} is not allowed")

    score_impact = packet.get("score_impact")
    if not isinstance(score_impact, dict) or not _is_int_in_range(score_impact.get("after")):
        errors.append(f"{task_id}: packet score_impact.after must be 0-100")

    prompt = packet.get("prompt_for_next_agent")
    if not isinstance(prompt, str) or len(prompt.strip()) < 50:
        errors.append(f"{task_id}: packet prompt_for_next_agent must be at least 50 characters")

    questions = packet.get("questions_for_next_agent")
    if not _string_list(questions):
        errors.append(f"{task_id}: packet questions_for_next_agent must be a non-empty string list")

    recommendation = packet.get("stop_continue_recommendation")
    if recommendation not in {"stop", "continue"}:
        errors.append(f"{task_id}: packet stop_continue_recommendation must be stop or continue")

    if verdict == "PASS":
        if not _string_list(packet.get("files_inspected")):
            errors.append(f"{task_id}: PASS packet must include files_inspected")
        commands = _as_list(packet.get("commands_run"))
        if not commands:
            errors.append(f"{task_id}: PASS packet must include commands_run")
        for command in commands:
            if not isinstance(command, dict) or command.get("exit_code") != 0 or not command.get("command"):
                errors.append(f"{task_id}: PASS packet command results must have command and exit_code=0")

    if verdict in {"HOLD", "FAIL"} and not str(packet.get("blocker_reason", "")).strip():
        errors.append(f"{task_id}: {verdict} packet must include blocker_reason")

    return errors


def _validate_prompt_packets(task_id: str, prompt_packets: Any) -> list[str]:
    errors: list[str] = []
    packets = _as_list(prompt_packets)
    if not packets:
        errors.append(f"{task_id}: prompt_packets must contain at least one prompt packet")
        return errors
    required = {"packet_id", "from_agent", "to_agent", "task_id", "context", "hard_rules", "questions", "expected_output_format"}
    for packet in packets:
        if not isinstance(packet, dict):
            errors.append(f"{task_id}: prompt packet must be an object")
            continue
        missing = sorted(required - set(packet))
        if missing:
            errors.append(f"{task_id}: prompt packet missing fields: {', '.join(missing)}")
        if packet.get("from_agent") not in CANONICAL_AGENT_ROLES:
            errors.append(f"{task_id}: prompt packet from_agent is not in the 10-agent roster")
        if packet.get("to_agent") not in CANONICAL_AGENT_ROLES:
            errors.append(f"{task_id}: prompt packet to_agent is not in the 10-agent roster")
        if not _string_list(packet.get("questions")):
            errors.append(f"{task_id}: prompt packet questions must be non-empty")
        if not _string_list(packet.get("hard_rules")):
            errors.append(f"{task_id}: prompt packet hard_rules must be non-empty")
    return errors


def _required_gates_for_task(task: dict[str, Any], domain_gates: dict[str, Any]) -> set[str]:
    required: set[str] = set()
    for domain in _as_list(task.get("domains")):
        gates = domain_gates.get(domain, [])
        if isinstance(gates, list):
            required.update(gate for gate in gates if isinstance(gate, str))
    required.update(gate for gate in _as_list(task.get("reviewer_agents")) if isinstance(gate, str))
    if task.get("status") == DONE_STATUS:
        done_gates = domain_gates.get("done", [])
        if isinstance(done_gates, list):
            required.update(gate for gate in done_gates if isinstance(gate, str))
    return required


def _validate_task(task: dict[str, Any], protocol: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    task_id = _task_label(task)
    required_task_fields = _as_list(protocol.get("required_task_fields"))
    for field in required_task_fields:
        if field not in task:
            errors.append(f"{task_id}: task missing required field {field}")

    role_fields = ["owner_agent", "reviewer_agents"]
    if task.get("owner_agent") not in CANONICAL_AGENT_ROLES:
        errors.append(f"{task_id}: owner_agent is not in the 10-agent roster")
    for reviewer in _as_list(task.get("reviewer_agents")):
        if reviewer not in CANONICAL_AGENT_ROLES:
            errors.append(f"{task_id}: reviewer_agent is not in the 10-agent roster: {reviewer}")

    for field in ["score_before", "target_score", "actual_score_after"]:
        if not _is_int_in_range(task.get(field)):
            errors.append(f"{task_id}: {field} must be an integer from 0 to 100")

    if not _string_list(task.get("evidence_required")):
        errors.append(f"{task_id}: evidence_required must be a non-empty list")
    if not str(task.get("stop_condition", "")).strip():
        errors.append(f"{task_id}: stop_condition is required")

    status = task.get("status")
    allowed_statuses = set(_as_list(protocol.get("allowed_task_statuses")))
    if status not in allowed_statuses:
        errors.append(f"{task_id}: unsupported status {status!r}")

    validation_commands = _as_list(task.get("validation_commands"))
    if not validation_commands:
        errors.append(f"{task_id}: validation_commands must be non-empty")
    if status == DONE_STATUS:
        for command in validation_commands:
            if not isinstance(command, dict) or command.get("exit_code") != 0:
                errors.append(f"{task_id}: validation command did not pass")

    handoff_packets = _as_list(task.get("handoff_packets"))
    if not handoff_packets:
        errors.append(f"{task_id}: handoff_packets must contain at least one agent packet")
    allowed_verdicts = set(_as_list(protocol.get("allowed_verdicts")))
    required_packet_fields = _as_list(protocol.get("required_packet_fields"))
    for packet in handoff_packets:
        if not isinstance(packet, dict):
            errors.append(f"{task_id}: handoff packet must be an object")
            continue
        errors.extend(
            _validate_packet(
                task_id,
                packet,
                allowed_verdicts=allowed_verdicts,
                required_packet_fields=required_packet_fields,
            )
        )

    errors.extend(_validate_prompt_packets(task_id, task.get("prompt_packets")))

    packets_by_agent = {_packet_agent(packet): packet for packet in handoff_packets if isinstance(packet, dict)}
    blockers = _as_list(task.get("blockers"))
    if status == BLOCKED_STATUS:
        if not _string_list(blockers):
            errors.append(f"{task_id}: blocked task must include exact blockers")
        if not any(_packet_verdict(packet) in {"HOLD", "FAIL"} for packet in handoff_packets if isinstance(packet, dict)):
            errors.append(f"{task_id}: blocked task must include a HOLD or FAIL packet")
        return errors

    if blockers and status == DONE_STATUS:
        errors.append(f"{task_id}: done task must not have unresolved blockers")

    if status == DONE_STATUS:
        if not _as_list(task.get("proof")):
            errors.append(f"{task_id}: done task must include exact proof")
        required_gates = _required_gates_for_task(task, protocol.get("domain_gates", {}))
        for gate in sorted(required_gates):
            packet = packets_by_agent.get(gate)
            if not packet or _packet_verdict(packet) != "PASS":
                errors.append(f"{task_id}: missing required gate packet from {gate}")
        qa_packet = packets_by_agent.get("QA / Critic")
        if not qa_packet:
            errors.append(f"{task_id}: done task requires QA / Critic packet")
        elif not _is_int_in_range(qa_packet.get("task_score"), 1, 100):
            errors.append(f"{task_id}: QA / Critic packet must include task_score 1-100")

    for field in role_fields:
        if field not in task:
            errors.append(f"{task_id}: task missing role field {field}")

    return errors


def validate_blackboard(blackboard: dict[str, Any], protocol: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    tasks = _as_list(blackboard.get("tasks"))
    if not tasks:
        return ["blackboard.tasks must be a non-empty list"]
    if blackboard.get("protocol_version") != protocol.get("schema_version"):
        errors.append("blackboard.protocol_version must match protocol.schema_version")
    for task in tasks:
        if not isinstance(task, dict):
            errors.append("blackboard.tasks entries must be objects")
            continue
        errors.extend(_validate_task(task, protocol))
    return errors


def _normalize_sha256(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    if len(text) == 64 and all(char in "0123456789abcdef" for char in text):
        return f"sha256:{text}"
    return text


def _resolve_proof_path(value: Any, root: Path) -> Path | None:
    text = str(value or "").strip()
    if not text:
        return None
    path = Path(text)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def validate_proof_artifacts(blackboard: dict[str, Any], root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for task in _as_list(blackboard.get("tasks")):
        if not isinstance(task, dict) or task.get("status") != DONE_STATUS:
            continue
        task_id = _task_label(task)
        artifacts = _as_list(task.get("proof_artifacts"))
        if not artifacts:
            errors.append(f"{task_id}: done task must include proof_artifacts with path and sha256")
            continue
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                errors.append(f"{task_id}: proof_artifacts[{index}] must be an object")
                continue
            path = _resolve_proof_path(artifact.get("path"), root)
            expected = _normalize_sha256(artifact.get("sha256"))
            if path is None:
                errors.append(f"{task_id}: proof_artifacts[{index}].path is required")
                continue
            try:
                path.relative_to(root.resolve())
            except ValueError:
                errors.append(f"{task_id}: proof_artifacts[{index}] path is outside workspace")
                continue
            if not path.exists() or path.is_dir():
                errors.append(f"{task_id}: proof_artifacts[{index}] path does not exist or is not a file")
                continue
            actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != expected:
                errors.append(f"{task_id}: proof_artifacts hash mismatch for {artifact.get('path')}")
    return errors


def validate_payloads(protocol: dict[str, Any], blackboard: dict[str, Any]) -> list[str]:
    errors = validate_protocol(protocol)
    errors.extend(validate_blackboard(blackboard, protocol))
    return errors


def validate_files(protocol_path: Path = DEFAULT_PROTOCOL_PATH, blackboard_path: Path = DEFAULT_BLACKBOARD_PATH) -> list[str]:
    protocol = load_json(protocol_path)
    blackboard = load_json(blackboard_path)
    errors = validate_payloads(protocol, blackboard)
    protocol_resolved = protocol_path.resolve()
    repo_root = ROOT.resolve()
    proof_root = repo_root if protocol_resolved.is_relative_to(repo_root) else protocol_path.parent.resolve()
    errors.extend(validate_proof_artifacts(blackboard, root=proof_root))
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the governed StatuteProof Agent Council protocol.")
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL_PATH)
    parser.add_argument("--blackboard", type=Path, default=DEFAULT_BLACKBOARD_PATH)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        errors = validate_files(args.protocol, args.blackboard)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"validate_agent_council_protocol: FAILED: {exc}", file=sys.stderr)
        return 1
    if errors:
        print("validate_agent_council_protocol: FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("validate_agent_council_protocol: PASS")
    print(f"protocol={args.protocol}")
    print(f"blackboard={args.blackboard}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
