# Mass Source Activation Agent Gate Plan

Date: 2026-06-15

## Agents / Skills Used Or Emulated

Executable subagent tools were not available as direct callable StatuteProof agents in this Codex session, so the 10 official agents are emulated manually. No 11th active agent is added.

Skills consulted:

- `source-monitoring-review`
- `evidence-readiness-review`
- `custom-source-parser`
- `legal-safe-copy-review`
- `test-driven-development`
- `verification-before-completion`
- `systematic-debugging`
- `prompt-injection-review`

## Gate Ownership

| Gate | Owner | Blocks |
|---|---|---|
| Scope control | Chief of Staff | Broad monitoring, infrastructure changes, 11th agent, unrelated staging |
| Buyer relevance | Product Manager | Vanity source padding, weak MLRO/CCO relevance |
| Architecture safety | Code Architect | Broad rewrites, unsafe dependencies, breaking evidence pipeline |
| Parser/source truth | Source Monitor | Unofficial/private sources, stale URLs, weak selectors, bad source-health |
| Evidence readiness | Evidence Trail | Missing proof, hashes, paths, source runs, repeat baseline |
| QA honesty | QA / Critic | Fake-ready states, no-save evidence claims, one-run monitoring-ready claims |
| Legal-safe wording | Legal Language | Legal advice, guaranteed compliance, regulator partnership/certification |
| Brief eligibility | Risk + Brief Pipeline | Brief/risk use without complete evidence |
| ICP relevance | ICP Lead Research | Sources irrelevant to UAE compliance buyers |
| Outreach wording | Outreach Writer | Only if public/customer copy changes; must pass Legal Language |

## Required Per-Source Signoff Fields

Every mass activation queue source must carry these gate fields:

- `source_monitor_gate`
- `evidence_trail_gate`
- `qa_critic_gate`
- `legal_language_gate`
- `product_manager_gate`
- `code_architect_gate`
- `final_activation_gate`

Each gate must include:

- `status`: `pass`, `hold`, or `fail`
- `reason`
- `reviewed_at`
- `blocking_issues`

## Required Per-Adapter Signoff Fields

Adapter work must document:

- adapter family and adapter name
- input config
- output contract
- failure modes
- source-health/noise behavior
- tests added
- Code Architect gate
- Source Monitor gate
- QA/Critic gate

## Activation Rule

A source cannot be `activation_ready` unless:

1. source is official or officially linked;
2. source is public and permitted to monitor;
3. adapter/selector strategy is explicit;
4. no-save test passed;
5. proof paths exist;
6. repeat baseline requirement is satisfied;
7. nav-shell/shallow/duplicate hash checks pass;
8. unresolved high noise/source-health risk is absent;
9. Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, and Code Architect gates pass.

## Forbidden Overclaims

- “50 working sources” unless validator proves it.
- “60 validated sources”.
- “Any website can be parsed”.
- “Perfect parsing”.
- “95% of websites” as public copy.
- Legal advice or guaranteed compliance.
- Official regulator partnership/certification.
