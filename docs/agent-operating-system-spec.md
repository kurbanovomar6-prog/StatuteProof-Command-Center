# Agent Operating System Spec

Date: 2026-06-21

## Purpose

The StatuteProof Agent Operating System is a governed council protocol for RegTech work. Its job is not to make agents louder or more autonomous. Its job is to make agents route work, score work, pass prompts, enforce evidence gates, and stop false done claims.

The implementation is intentionally small:

- `product/regradar/config/agent_council_protocol.json`
- `product/regradar/config/agent_council_blackboard.json`
- `tools/validate_agent_council_protocol.py`
- `product/regradar/tests/test_agent_council_protocol.py`

It is a protocol and validator, not a daemon.

## Active Agent Roles

There are exactly 10 active roles:

1. Chief of Staff
2. Product Manager
3. Code Architect
4. QA / Critic
5. Legal Language
6. Source Monitor
7. Evidence Trail
8. Risk + Brief Pipeline
9. ICP Lead Research
10. Outreach Writer

Do not create an 11th active agent. Modes do not count as active agents.

## Approved Modes

- Chief of Staff: Council Router / Orchestrator
- Product Manager: Pilot/Beta/Production Readiness Gate
- Code Architect: Agent Systems Architect, Adapter Worker, Validator Worker, Test Fixture Worker, Security/Tooling Auditor
- QA / Critic: External CTO Scorer
- Legal Language: Claims Gate
- Source Monitor: Source Truth Gate, Source Discovery Worker, Browser/Access Investigator
- Evidence Trail: Evidence Corpus Auditor
- Risk + Brief Pipeline: Customer Delivery Gate
- ICP Lead Research: Market/GTM Scorer
- Outreach Writer: Prompt Router / Handoff Scribe

## Core Architecture

The system has four layers:

1. Role registry: the canonical 10-agent roster and allowed modes.
2. Protocol schema: required task fields, packet fields, gate mapping, safety rules, scoring dimensions, and autonomy limits.
3. Blackboard: a shared dry-run state file containing governed tasks, handoff packets, prompt packets, scores, validation results, proof, and blockers.
4. Validator: a deterministic gate that rejects incomplete packets, unsupported roles, fake PASS, missing QA score, missing evidence gates, missing prompt packets, and failed validation commands.

## Task Schema

Every governed task must include:

- `task_id`
- `owner_agent`
- `reviewer_agents`
- `current_phase`
- `score_before`
- `target_score`
- `actual_score_after`
- `evidence_required`
- `validation_commands`
- `handoff_packets`
- `prompt_packets`
- `blockers`
- `stop_condition`

Done tasks must also include `proof`, passing validation command results, QA / Critic score, and all required gate PASS packets.

## Packet Schema

Every agent handoff packet must include:

- `verdict`: `PASS`, `HOLD`, or `FAIL`
- `task_score`: required for QA / Critic before done
- `score_impact`
- `evidence_found`
- `files_inspected`
- `commands_run`
- `findings` split by `P0`, `P1`, `P2`
- `blocker_reason`
- `prompt_for_next_agent`
- `questions_for_next_agent`
- `stop_continue_recommendation`

PASS packets require non-empty files inspected and command results. HOLD and FAIL packets require exact blocker reasons.

## Validation Gates

- Evidence tasks require Evidence Trail PASS.
- Customer copy requires Legal Language PASS.
- Brief/customer delivery tasks require Risk + Brief Pipeline PASS.
- Source activation requires Source Monitor PASS.
- Done tasks always require QA / Critic PASS and a 1-100 score.

Chief of Staff may route work and mark blockers, but cannot override Evidence Trail, QA / Critic, Legal Language, Source Monitor, or Risk + Brief Pipeline gates.

## Safety Rules

The protocol encodes these rules:

- No deploy.
- No infra touch.
- No secrets print.
- No `.env` printing.
- No customer emails.
- No access-control bypass.
- No Ruflo full mode.
- No hooks, daemon, or MCP memory auto-sync.
- No fake MONITOR_OK.
- No source activation without evidence gates.
- No customer brief without complete approved canonical evidence.
- No complete coverage claim.
- No legal advice claim.
- No perfect parsing claim.
- No never-miss-updates claim.
- No unrelated staging.

## Stop Conditions

Agents must stop when:

- A validator fails and cannot be safely fixed in scope.
- Public-source legality or access status is unclear.
- A secret or `.env` risk appears.
- Customer-delivery risk appears.
- A task grows beyond the current commit scope.
- A required reviewer packet is missing.
- A done claim lacks QA score, proof, prompt packet, or validation result.
- Fresh subagent runtime is unavailable and the only option is to touch old stuck agents.

## Difference From Ruflo Full Mode

Ruflo is useful as a reference for swarms, routing, memory, and background workers. Full Ruflo mode is not enabled here. The GitHub readme describes full mode as including MCP server registration, hooks, daemon/background behavior, memory, and large agent swarms. StatuteProof does not enable those features in this implementation.

This implementation is a local validator-backed protocol. It has no daemon, no hooks, no MCP memory auto-sync, no background worker loop, and no source activation automation.

## How To Run

```bash
python3 tools/validate_agent_council_protocol.py
python3 tools/agent_council.py validate-protocol
python3 -m pytest product/regradar/tests/test_agent_council_protocol.py -q
```

## Example

A source activation task cannot be done until Source Monitor, Evidence Trail, and QA / Critic all return PASS packets with files inspected, commands run, next-agent prompts, and proof. A no-save test cannot become a PASS packet for activation because it lacks proof, baseline, and MONITOR_OK.
