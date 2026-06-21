# Agent Council Scoring Rubric

Date: 2026-06-21

## Purpose

Scores exist to stop self-deception. A score is not a vibe. It must cite files, tests, commands, evidence, and blockers.

## Roles And Modes

QA / Critic owns External CTO Scorer mode and must score every done task from 1-100. Product Manager may score pilot/beta/production readiness. Evidence Trail scores evidence integrity. ICP Lead Research may score market/GTM readiness. These are modes inside the 10-agent roster, not new active agents.

## Routing And Gates

- Evidence score -> Evidence Trail, then QA / Critic.
- Source truth score -> Source Monitor, Evidence Trail, then QA / Critic.
- Customer copy score -> Product Manager, Legal Language, then QA / Critic.
- Brief/customer delivery score -> Risk + Brief Pipeline, Evidence Trail, Legal Language, then QA / Critic.
- Overall project score -> QA / Critic as External CTO Scorer, with file/test evidence.

## Dimensions

Every project score and major task score should consider:

1. Product readiness
2. Evidence integrity
3. Source monitoring truth
4. Parser/adapter reliability
5. Risk brief readiness
6. Legal-safe claims
7. Test coverage
8. Operational readiness
9. Maintainability
10. GTM readiness
11. Customer delivery readiness

## Task Score Rules

- 0-39: unsafe or unproven; must be blocked.
- 40-59: partial implementation; must be HOLD or blocked.
- 60-74: internally useful but not customer-ready.
- 75-84: ship candidate for internal governed workflows.
- 85-89: strong internal readiness, still must list remaining blockers.
- 90-100: due-diligence grade; requires end-to-end evidence for that category.

No category can score 90+ if its main workflow has never run end to end.

## Required Score Evidence

Each score must cite:

- exact files reviewed
- commands run and exit codes
- tests or validators passed
- P0/P1/P2 findings
- unresolved blockers
- whether customer-facing claims changed
- whether a human gate remains

## Packet Requirements

Scores must appear in a handoff packet with `task_score`, `score_impact`, `evidence_found`, `files_inspected`, `commands_run`, P0/P1/P2 findings, blocker reason, next-agent prompt, and questions for the next agent.

## 90+ Rule

StatuteProof cannot honestly claim 90+ overall from engineering alone if GTM/customer evidence is missing. Scores above 90 require real pilot/customer evidence unless the scored category is narrowly technical and has an end-to-end test or production artifact.

## Anti-Inflation Rules

- Do not average away a P0 blocker.
- The task score is capped by the weakest required gate.
- A PASS without files inspected and commands run is not a PASS.
- A done claim without QA / Critic score is invalid.
- A source activation claim without proof, normalized path, normalized hash, baseline, and MONITOR_OK is invalid.
- A brief-readiness claim without complete approved canonical evidence is invalid.

## Stop Conditions

Stop scoring and return HOLD or FAIL when evidence is missing, a validator fails, a human gate is required, the task implies customer delivery without approval, or the only path requires creating an 11th active agent.

## What Agents Cannot Do

Agents cannot claim legal advice, guaranteed compliance, complete coverage, regulator certification, perfect parsing, never-miss updates, or all-source coverage. Scores must not reward those claims.

## Report Scores

Any report containing `N/100` must include:

- rubric version
- category breakdown
- file/test evidence
- P0 blockers
- exact score blockers to 80+
- exact score blockers to 90+

If these are missing, the score is an unverified claim.

## Validator

Run:

```bash
python3 tools/validate_agent_council_protocol.py
```

The validator rejects done tasks without QA score and rejects fake PASS packets without files and commands.

## Ruflo Boundary

Ruflo-style background autonomy is not part of scoring. No hooks, daemon, MCP memory, or full mode is enabled. Scoring is local, file-cited, and validator-backed.

## Example

If canonical evidence records exist but all are `review_status=pending`, evidence integrity may improve, but customer delivery readiness cannot score 90+. The main customer delivery workflow has not completed with approved evidence and human review.
