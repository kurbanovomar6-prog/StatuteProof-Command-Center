# Agent Council Handoff Packet Spec

Date: 2026-06-21

## Purpose

Handoff packets make agents useful to each other. A packet must let the next agent start without reconstructing context from prose notes.

## Roles And Modes

Packets must use one of the 10 active roles from `AGENTS.md` in `from_agent` and `to_agent`. Modes such as Prompt Router, External CTO Scorer, and Security/Tooling Auditor belong to those roles and must not appear as active agents.

## Routing Rules

- Source activation packets route to Source Monitor, Evidence Trail, and QA / Critic.
- Evidence packets route to Evidence Trail, then Risk + Brief Pipeline or QA / Critic.
- Customer copy packets route to Legal Language, then QA / Critic.
- Brief/customer delivery packets route to Risk + Brief Pipeline, Evidence Trail, Legal Language, and QA / Critic.
- Prompt quality packets route to Outreach Writer in Prompt Router mode.

## Agent Packet Fields

Every handoff packet must include:

```json
{
  "packet_id": "packet-evidence-trail-001",
  "from_agent": "Evidence Trail",
  "to_agent": "QA / Critic",
  "verdict": "PASS",
  "task_score": 76,
  "score_impact": {"before": 35, "after": 76, "delta": 41},
  "evidence_found": ["..."],
  "files_inspected": ["..."],
  "commands_run": [{"command": "...", "exit_code": 0}],
  "findings": {"P0": [], "P1": [], "P2": []},
  "blocker_reason": "",
  "prompt_for_next_agent": "...",
  "questions_for_next_agent": ["..."],
  "stop_continue_recommendation": "continue"
}
```

## Prompt Packet Fields

Every prompt packet must include:

```json
{
  "packet_id": "prompt-router-001",
  "from_agent": "Outreach Writer",
  "to_agent": "Evidence Trail",
  "task_id": "agent-os-protocol-simulation",
  "context": "...",
  "hard_rules": ["No deploy.", "No secrets print."],
  "questions": ["Can this gate be verified from files and commands?"],
  "expected_output_format": ["verdict", "task_score", "evidence_found"]
}
```

## Valid Verdicts

- `PASS`: gate is satisfied. Requires files inspected, commands run, evidence found, and next prompt.
- `HOLD`: task is not safe to complete yet. Requires exact blocker and next prompt.
- `FAIL`: task is unsafe or wrong. Requires exact blocker and next prompt.

## Scoring Rules

QA / Critic packets for done tasks must include `task_score` from 1-100. The score must cite files, commands, findings, and blockers. A packet with no score cannot complete a task.

## Validation Gates

The validator enforces required domain gates:

- Evidence tasks require Evidence Trail.
- Customer copy tasks require Legal Language.
- Brief/customer delivery tasks require Risk + Brief Pipeline.
- Source activation tasks require Source Monitor.
- Done tasks require QA / Critic.

## Stop Conditions

Return HOLD or FAIL instead of PASS when a packet lacks evidence, files, commands, next prompt, exact blocker, validation result, or required reviewer.

## What Agents Cannot Do

Packets cannot authorize deployment, infrastructure changes, secret printing, `.env` printing, customer emails, access-control bypass, Ruflo full mode, fake MONITOR_OK, source activation without evidence, customer briefs without approved canonical evidence, complete coverage claims, legal advice claims, perfect parsing claims, or never-miss-updates claims.

## Bad Handoffs

Bad:

```text
Continue with DFSA.
```

Why bad: no role, no source truth, no question, no hard rules, no output format.

Bad:

```text
Looks good. PASS.
```

Why bad: no files inspected, no commands run, no score, no next prompt.

## Good Handoff

Good:

```text
TASK: canonical-evidence-review
TO: Evidence Trail
CONTEXT: 11 local canonical evidence records validate but remain review_status=pending.
YOUR QUESTIONS:
1. Do all records recompute current_hash from disk?
2. Can any pending record enter customer brief inputs?
HARD RULES:
- No customer brief without complete approved canonical evidence.
EXPECTED OUTPUT:
verdict, task_score, files_inspected, commands_run, blockers, next_prompt.
```

## Validator

Run:

```bash
python3 tools/validate_agent_council_protocol.py
```

The validator blocks empty prompt packets, missing next-agent prompt, fake PASS, missing QA score, and unsupported agent roles.

## Ruflo Boundary

This packet spec is inspired by swarm/router handoff ideas, but it does not enable Ruflo full mode, hooks, daemon, MCP memory, or background workers. It is a local file contract.
