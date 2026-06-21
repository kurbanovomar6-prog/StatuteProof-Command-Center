# Agent Council Autonomy Protocol

Date: 2026-06-21

## Purpose

This protocol defines bounded autonomy for the StatuteProof Agent Council. Agents may propose prompts, handoffs, scores, blockers, and next tasks. They may not run unbounded loops, bypass gates, or claim completion without evidence.

## Roles And Modes

The only active roles are the 10 roles in `AGENTS.md`. Modes such as Prompt Router, External CTO Scorer, Agent Systems Architect, Evidence Corpus Auditor, Source Truth Gate, and Security/Tooling Auditor do not create extra active agents.

## Council Loop

1. Chief of Staff selects one eligible task from the blackboard or legacy task board.
2. Prompt Router mode writes a prompt packet for the next agent.
3. Owner agent works within the allowed file scope and produces a handoff packet.
4. Required reviewer agents inspect files, run commands, and file PASS/HOLD/FAIL packets.
5. QA / Critic scores from 1-100 before any done state.
6. Chief of Staff marks done only when validator passes and required gates are satisfied.
7. If a gate returns HOLD or FAIL, the task is blocked with an exact reason and next prompt.

## Autonomy Limits

- Maximum 3 agents per wave.
- Maximum 2 implementation loops per commit.
- No background loops.
- No daemon.
- No hooks.
- No MCP memory auto-sync.
- No automatic source activation.
- No automatic customer delivery.

## Human Approval Gates

Human review remains required for:

- Customer delivery.
- Any risk >= 70 or confidence < 0.70.
- Any legal-sensitive claim.
- Any source activation where public-source legality is unclear.
- Any tool install that changes hooks, daemon behavior, MCP config, secrets, or infrastructure.

## Routing Rules

- Source monitoring task -> Source Monitor.
- Parser/source-intake task -> Source Monitor, Code Architect, Evidence Trail, QA / Critic.
- Evidence task -> Evidence Trail.
- Risk/brief task -> Risk + Brief Pipeline, Evidence Trail, QA / Critic, Legal Language.
- Customer copy -> Product Manager, Legal Language, QA / Critic.
- Agent OS/task routing -> Chief of Staff, Prompt Router mode, QA / Critic.
- Tooling intake -> Code Architect in Security/Tooling Auditor mode, QA / Critic, Chief of Staff.

## Scoring Loop

QA / Critic in External CTO Scorer mode must provide:

- `task_score`: 1-100
- score_before
- score_after
- score delta
- P0 blockers
- evidence supporting the score
- exact reason any category is under 90

No task can be marked done with missing QA score.

## Stop Conditions

Stop rather than continue when:

- A required packet is missing.
- A PASS packet has no files inspected or commands run.
- A blocker is vague.
- A validation command fails.
- A source is no-save-only, one-run-only, static, duplicate, nav-shell, private, access-blocked, or missing proof.
- A prompt asks for deployment, secrets, customer email, access-control bypass, or Ruflo full mode.
- A task requires an 11th active agent.

## What Is Not Automated

- Legal advice.
- Compliance certification.
- Complete UAE coverage claims.
- Complete family coverage claims.
- Customer outreach sending.
- Customer brief delivery.
- Cloudflare/DigitalOcean deployment.
- Secret handling.
- Access-control bypass.
- Production source activation without evidence gates.

## Ruflo Boundary

Ruflo and agency-agent repositories are reference material only. This protocol does not install Ruflo full mode, register MCP memory, enable hooks, start daemons, or run background workers. Autonomy is implemented as a local schema plus validator.

## Validator

Run:

```bash
python3 tools/validate_agent_council_protocol.py
```

The validator rejects missing handoff packets, missing prompt packets, missing QA score, unsupported roles, missing Evidence Trail gate for evidence tasks, failed validation commands, fake PASS packets, and done tasks with unresolved blockers.
