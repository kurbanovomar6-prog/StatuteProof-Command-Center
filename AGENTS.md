# StatuteProof Agent Roster

## Rule: 10 Agents Maximum

StatuteProof operates exactly 10 agent roles. Do not create an 11th active agent.

## Agent Definitions

Agent system prompts are in `.claude/agents/` (Claude Code subagent format) and `agents/` (human-readable docs).

## Roster

| # | Role | Files | Trigger Conditions |
|---|------|-------|-------------------|
| 1 | Chief of Staff | `.claude/agents/chief-of-staff.md` | Multi-agent routing, weekly planning, coordination |
| 2 | Product Manager | `agents/product-manager.md` | Roadmap decisions, feature scoping, MVP questions |
| 3 | Code Architect | `agents/code-architect-dev.md` | Pipeline design, API changes, technical specs |
| 4 | QA / Critic | `agents/qa-critic.md` | Final gate before any delivery or commit |
| 5 | Legal Language | `agents/legal-language.md` | Any customer-facing copy, disclaimer review |
| 6 | Source Monitor | `agents/source-monitor.md` | Source specs, fetch config, source health |
| 7 | Evidence Trail | `agents/evidence-trail.md` | Evidence record verification, hash checks |
| 8 | Risk + Brief Pipeline | `agents/risk-brief-pipeline.md` | Risk scoring, brief drafting |
| 9 | ICP Lead Research | `agents/icp-lead-research.md` | Lead profiling, ICP matching |
| 10 | Outreach Writer | `agents/outreach-writer.md` | Outreach messages, pitch notes |

## Routing Rules

```
source monitoring task       → Source Monitor Agent (#6)
evidence verification task   → Evidence Trail Agent (#7)
risk scoring / brief task    → Risk + Brief Pipeline (#8)
legal copy review            → Legal Language Agent (#5)
QA before delivery           → QA / Critic (#4)
pipeline architecture        → Code Architect (#3)
roadmap / feature question   → Product Manager (#2)
lead research / ICP          → ICP Lead Research (#9)
outreach message             → Outreach Writer (#10) + anti-slop review
multi-agent coordination     → Chief of Staff (#1)
```

## Handoff Rules

1. No brief is delivered without QA / Critic (#4) approval.
2. No customer-facing copy is finalized without Legal Language Agent (#5) review.
3. No brief is drafted without evidence_record_status = complete.
4. Any risk >= 70 or confidence < 0.70 requires founder review before delivery.
5. Evidence Trail Agent (#7) blocks any brief when evidence is incomplete.

## What Agents Cannot Do

- Make legal advice decisions (route to Legal Language Agent, then qualified counsel)
- Certify compliance (not in scope)
- Create outreach before evidence exists
- Bypass the QA gate for "quick" deliveries
- Invent source URLs or evidence records

## Skills Available to Agents

| Skill | For Agent |
|-------|-----------|
| `#evidence-audit` | Evidence Trail (#7) |
| `#risk-brief-review` | Risk + Brief Pipeline (#8), QA / Critic (#4) |
| `#weekly-founder-plan` | Chief of Staff (#1) |
| `#marketing-outreach-review` | Outreach Writer (#10) |
| `#anti-slop-writing-review` | Outreach Writer (#10), Legal Language (#5) |
| `#ui-ux-review` | Product Manager (#2), Code Architect (#3) |
