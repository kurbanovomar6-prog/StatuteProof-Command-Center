# Source Discovery Agent Gate Plan

## Agents / Skills Used Or Emulated

Subagent execution tools were not available in this Codex session, so the official StatuteProof agent roster is applied manually and documented as emulated. No 11th active agent is added.

Skills applied from `.agents/skills/`:

- `source-monitoring-review`
- `evidence-readiness-review`
- `custom-source-parser`
- `legal-safe-copy-review`
- `test-driven-development`
- `verification-before-completion`
- `systematic-debugging`
- `webapp-testing` if frontend validation is needed
- `evidence-audit`
- `anti-slop-b2b-copy`
- `statuteproof-project-review`

## Agent Gates

| Agent | Gate | Can Block |
|---|---|---|
| Chief of Staff | Scope and roster control | Broad monitoring, deployment, adding an 11th agent, unrelated work |
| Product Manager | Buyer relevance | Vanity URLs, generic homepages, sources not useful to UAE MLRO/CCO buyers |
| Code Architect | Architecture safety | Broad parser rewrites, unsafe dependencies, duplicated discovery pipeline |
| QA / Critic | Truth and regression gate | Fake-ready states, no-save evidence claims, weak validators, broken CLI/UI |
| Legal Language | Public wording | Any website/perfect parsing/50 or 60 validated/legal advice/guarantee/certification claims |
| Source Monitor | Source validity | Non-official pages, wrong-country regulators, private/paywalled/login/CAPTCHA pages |
| Evidence Trail | Evidence semantics | Evidence-ready or monitoring-ready claims without proof/baseline |
| Risk + Brief Pipeline | Future brief eligibility | Any brief/risk use before evidence is complete |
| ICP Lead Research | ICP relevance | Sources that do not matter to UAE compliance buyers |
| Outreach Writer | Public copy only | Any outreach/copy not evidence-backed and legal-safe |

## Required Signoff Fields Per Discovered Endpoint

Each generated endpoint candidate must carry or be mappable to:

- `source_monitor_gate`: `pass` / `hold` / `fail`, reason, blocking issues.
- `evidence_trail_gate`: usually `hold` until proof/baseline exists.
- `qa_critic_gate`: fake-ready/nav-shell/noise/hash collision review.
- `legal_language_gate`: safe status wording and forbidden wording.
- `product_manager_gate`: MLRO/CCO relevance.
- `code_architect_gate`: adapter/discovery implementation risk.
- `final_activation_gate`: candidate / no_save_pending / no_save_passed / proof_saved / baseline_pending / activation_ready / remediation / blocked / rejected.

## Required Signoff Fields Per Adapter

- `adapter_family`
- `adapter_name`
- `adapter_version`
- `input_config`
- `output_schema`
- `failure_modes`
- `noise_source_health_policy`
- `tests_present`
- `code_architect_gate`
- `qa_critic_gate`

## Forbidden Overclaims

- “Any website can be parsed.”
- “Perfect parsing.”
- “95% of all websites.”
- “50 working sources” unless 50 activation-ready sources pass proof/baseline/gates.
- “60 validated sources.”
- “Guaranteed compliance.”
- “Legal advice.”
- “Official regulator certified.”

