# 10/10 Agent And Tool Use Plan

Date: 2026-06-14

## Agents Used Conceptually

The local agent roster defines exactly 10 active agents. No new active agent was added.

| Agent | Used for | Influence on this task |
| --- | --- | --- |
| Product Manager | Product strategy, MLRO next-action clarity, demo/pilot readiness. | Blocks changes that make the product look more mature than the operational state. |
| Code Architect | Backend/frontend implementation scope, parser/API safety. | Keeps fixes localized; avoids broad rewrites or big dependencies. |
| Source Monitor | Source registry, source readiness, DFSA remediation, Source Lab status language. | Enforces 13 enabled / 9 readiness-supported / 4 remediation unless new evidence proves otherwise. |
| Evidence Trail | Proof artifact checks, sample brief evidence, no-save/save distinction. | Blocks evidence claims without proof paths and hashes. |
| QA / Critic | Broken routes, dead CTAs, sample labeling, validation gates. | Requires build/lint/routes/tests before commit. |
| Legal Language | Customer-facing copy, pricing claims, brief/sample labels. | Blocks legal advice, guarantees, regulator certification, and "any website" claims. |
| Risk + Brief Pipeline | Proof-backed sample brief and brief-delivery boundaries. | Keeps sample brief as non-delivered, human-review-required demo output. |
| ICP Lead Research | MLRO/compliance buyer relevance. | Used only for demo/pilot readiness framing. |
| Outreach Writer | Not used for outreach execution. | Only relevant if public/customer copy needs anti-slop review. |
| Chief of Staff | Multi-step coordination. | Used conceptually to keep gates ordered and avoid mixing deployment/live checks. |

## Repo Skills Used

| Skill | Status | How used |
| --- | --- | --- |
| `statuteproof-project-review` | Used | Sets broad audit structure: separate real, sample, roadmap, and next task. |
| `source-monitoring-review` | Used | Defines source-readiness, no-save, activation, and DFSA/remediation constraints. |
| `evidence-readiness-review` | Used | Defines proof artifact and evidence-level requirements. |
| `custom-source-parser` | Used | Defines Source Lab result review and customer-facing status boundaries. |
| `legal-safe-copy-review` | Used | Defines forbidden legal/compliance/certification claims and sample-label requirements. |
| `webapp-testing` | Used | Guides browser smoke approach if local Playwright/server setup is available. |
| `test-driven-development` | Used | Any code behavior fix should get a targeted test first unless limited to docs. |
| `verification-before-completion` | Used | No success/completion claim without fresh validation output. |
| `prompt-injection-review` | Planned if skills/workflows change | Review any agent/skill changes for unsafe instruction override patterns. |
| `anti-slop-b2b-copy` / `mlro-homepage-review` | Planned if public copy changes | Keep public copy concrete, MLRO-specific, and legally safe. |

## Tools Used

- `rg`, `sed`, `git`, Python tests, frontend build/lint, route validator, workspace validator, parser quality validator.
- Web search will be used for GitHub/open-source research because the task explicitly asks for internet/GitHub research.
- Browser/Playwright smoke will be attempted only if local tooling is available and safe.

## Tools Or Subagents Unavailable

- Dedicated local subagent execution was not invoked as a separate runtime in this plan. The agent gates are applied manually/conceptually and documented.
- Codex Sites/deployment tools are intentionally not used because deployment is forbidden.

## Required Gates

| Gate | Pass criteria |
| --- | --- |
| Product Manager | MLRO next action is clear and product state is not overstated. |
| Source Monitor | Readiness counts, source states, and DFSA remediation labels are true. |
| Evidence Trail | Evidence/proof claims cite real artifacts; no-save remains preview only. |
| QA / Critic | Routes/buttons/sample labels are safe; validation commands pass. |
| Legal Language | No legal advice, guaranteed compliance, regulator certification, or universal parsing claims. |
| Security | No secrets/runtime data/reference repos staged. |
| Webapp Testing | Critical routes/flows are tested or clearly documented as not possible. |
| Verification | Final response and commit only after fresh validation. |

## What The Gates Block

- Promoting DFSA to ready without saved baseline.
- Replacing 13/9/4 with 13/10/3 without DIFC release evidence.
- Calling a no-save extraction evidence-backed.
- Treating paid plan selection as active subscription/monitoring.
- Showing sample brief as customer-ready output.
- Shipping claims such as "any website", "guaranteed compliance", "certified monitoring", or "13 validated sources".
