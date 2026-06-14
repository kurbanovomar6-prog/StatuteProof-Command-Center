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
custom source parser/intake  → Source Monitor (#6) + Code Architect (#3) + Evidence Trail (#7)
parser quality gate          → Source Monitor (#6) + Evidence Trail (#7) + QA / Critic (#4)
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
6. Custom source activation requires public-source legality confirmation, proof artifacts, and baseline/activation-readiness checks.

## What Agents Cannot Do

- Make legal advice decisions (route to Legal Language Agent, then qualified counsel)
- Certify compliance (not in scope)
- Claim a source is monitoring-ready from a no-save test or one successful extraction
- Bypass login pages, CAPTCHA, paywalls, private portals, or access controls
- Claim any website can be parsed or that parsing is guaranteed
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
## Codex Skills

Codex should use repo-scoped skills from:

`.agents/skills/`

Use skills when the task matches:
- project review
- evidence readiness
- source monitoring
- parser/source intake
- legal-safe copy
- MLRO homepage review
- custom source monitoring
- anti-slop B2B copy
- skills marketplace research

Parser/source-intake tasks must keep these states separate:
- no-save test = preview only
- saved test = evidence-backed only if proof artifacts exist
- source confirmed = readiness checks passed with failure reasons cleared
- monitoring-ready = baseline and activation-readiness requirements passed

Parser task handoff order:
1. Source Monitor reviews URL/source spec and blocked-source policy.
2. Code Architect reviews API/provider implementation if code changes are needed.
3. Source Intake Engine runs only the approved single-source test.
4. Evidence Trail verifies proof, hashes, paths, and baseline history.
5. QA / Critic blocks false ready/confirmed states.
6. Legal Language reviews any customer-facing source status wording.

Custom source work is limited to public sources that are technically accessible
and permitted to be monitored. Protected, private, login-gated, CAPTCHA-gated,
or paywalled sources must be blocked or marked needs review.

Do not add skills without:
1. reviewing the skill source
2. checking scripts/commands
3. documenting attribution
4. confirming it is useful for StatuteProof

Do not install broad skill packs blindly.
