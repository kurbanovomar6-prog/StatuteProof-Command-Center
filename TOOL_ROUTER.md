# StatuteProof Tool Router

Use this file to decide which agent, skill, or workflow to invoke for any task.

## By Task Type

| Task | Primary Tool | Secondary Tool | Workflow |
|------|-------------|----------------|---------|
| Source monitoring | Source Monitor Agent | `docs/source-monitor-spec-guide.md` | `workflows/02-first-source-spec.md` |
| Source spec creation | Source Monitor Agent | `prompts/source-spec-prompt.md` | `workflows/02-first-source-spec.md` |
| Evidence verification | Evidence Trail Agent + `#evidence-audit` | `docs/evidence-record-spec.md` | `workflows/03-evidence-dry-run.md` |
| Evidence dry run | Evidence Trail Agent | `prompts/evidence-dry-run-prompt.md` | `workflows/03-evidence-dry-run.md` |
| Risk scoring | Risk + Brief Pipeline | `docs/risk-scoring-guide.md` | `workflows/04-monitoring-to-brief.md` |
| Brief drafting | Risk + Brief Pipeline | `prompts/sample-brief-prompt.md` | `workflows/04-monitoring-to-brief.md` |
| Brief review (SHIP/NO-SHIP) | `#risk-brief-review` skill | QA / Critic Agent | `workflows/04-monitoring-to-brief.md` |
| Legal copy review | Legal Language Agent | `docs/forbidden-phrases-reference.md` | — |
| Legal-safe copy rewrite | `prompts/legal-safe-copy-review-prompt.md` | Legal Language Agent | — |
| QA / final gate | QA / Critic Agent | `#risk-brief-review` (for briefs) | — |
| Landing page review | `#ui-ux-review` skill | `docs/landing-page-review.md` | `workflows/06-landing-page-review.md` |
| Landing page conversion | `#landing-page-conversion-review` | `#ui-ux-review` | — |
| Dashboard UX review | `#ui-ux-review` skill | Product Manager Agent | `workflows/06-landing-page-review.md` |
| Design taste / AI slop check | `#design-taste-review` | `#design-polish` | — |
| High-stakes decision | `#agent-council-review` | Chief of Staff Agent | `workflows/07-agent-council-review.md` |
| Outreach message | Outreach Writer Agent | `#marketing-outreach-review` | `workflows/05-brief-to-outreach.md` |
| Outreach QA | `#anti-slop-writing-review` | `#marketing-outreach-review` | `workflows/05-brief-to-outreach.md` |
| Outreach review prompt | `prompts/outreach-review-prompt.md` | Outreach Writer Agent | — |
| Weekly planning | Chief of Staff + `#weekly-founder-plan` | — | `workflows/01-weekly-planning.md` |
| ICP profiling | ICP Lead Research Agent | `docs/icp-definition.md` (in AI-Company-Agent-OS) | — |
| Pipeline / API work | Code Architect Agent | `docs/github-workflow.md` | — |
| Roadmap decision | Product Manager Agent | `docs/statuteproof-mvp-plan.md` | — |

## By Question

| Question | Answer |
|----------|--------|
| Is this source spec ready? | `checklists/before-source-spec.md` |
| Is this evidence record complete? | `checklists/before-evidence-brief.md` + `#evidence-audit` |
| Is this outreach message safe to send? | `checklists/before-outreach.md` + `#anti-slop-writing-review` |
| Is this website copy legal-safe? | `checklists/before-website-copy.md` + Legal Language Agent |
| Is this ready to push to GitHub? | `checklists/before-github-push.md` |
| Is this decision high-stakes / irreversible? | `checklists/before-agent-council-decision.md` + `workflows/07-agent-council-review.md` |
| Does this design look like AI slop? | `#design-taste-review` (slop test runs first) |
| Which agent handles this? | `AGENTS.md` → routing rules |

## Decision Tree for Briefs

```
Brief request received
    ↓
Evidence record complete?
    No → Block. Go to Evidence Trail Agent.
    Yes ↓
Confidence >= 0.70?
    No → Flag for founder review.
    Yes ↓
Risk score >= 70?
    Yes → Human review required before delivery.
    No ↓
Legal Language Agent reviewed copy?
    No → Route to Legal Language Agent.
    Yes ↓
QA / Critic approved?
    No → Return for fixes.
    Yes → SHIP
```

## Skill Invocation

| Skill | Invoke with | Context required |
|-------|-------------|-----------------|
| `#evidence-audit` | Type `#evidence-audit` in Claude Code | evidence_record_id, source path, diff path |
| `#risk-brief-review` | Type `#risk-brief-review` | draft brief, evidence_record_id, risk score, confidence |
| `#weekly-founder-plan` | Type `#weekly-founder-plan` | week date, current pipeline status |
| `#marketing-outreach-review` | Type `#marketing-outreach-review` | draft message, lead context |
| `#anti-slop-writing-review` | Type `#anti-slop-writing-review` | any prose to review |
| `#ui-ux-review` | Type `#ui-ux-review` | page URL or screenshot, target audience |
| `#design-taste-review` | Type `#design-taste-review` | component or page, register (brand/product), specific concern |
| `#landing-page-conversion-review` | Type `#landing-page-conversion-review` | landing page URL or screenshot |
| `#agent-council-review` | Type `#agent-council-review` | decision statement, options A/B/C, stakes description |
