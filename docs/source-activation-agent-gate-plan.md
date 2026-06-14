# Source Activation Agent Gate Plan

Date: 2026-06-15

## Agents / Skills Used Or Emulated

Actual subagent execution was not available in this Codex turn, so the StatuteProof agents are applied as manual review gates. Repo skills were read and applied:

- `source-monitoring-review`
- `evidence-readiness-review`
- `custom-source-parser`
- `custom-source-monitoring-spec`
- `legal-safe-copy-review`
- `test-driven-development`
- `verification-before-completion`
- `statuteproof-project-review`

No 11th active agent is added.

## Gate Ownership

| Gate | Owner | Can Block |
|---|---|---|
| Chief of Staff | Scope control | Broad monitoring, unrelated edits, 11th active agent |
| Product Manager | Buyer relevance | Vanity sources, irrelevant endpoints, fake source-count padding |
| Code Architect | Architecture | Broad rewrites, unsafe dependencies, broken evidence pipeline changes |
| QA / Critic | Readiness truth | Fake-ready states, broken routes, shallow tests, overclaims |
| Legal Language | Copy safety | Legal advice, guaranteed compliance, regulator certification, "any website" claims |
| Source Monitor | Source correctness | Unofficial, stale, nav-shell, high-health-risk sources |
| Evidence Trail | Proof discipline | Evidence claims without proof paths and repeat baseline |
| Risk + Brief Pipeline | Future brief eligibility | Brief/risk outputs without evidence-complete source records |
| ICP Lead Research | MLRO relevance | Low-value or wrong-buyer source choices |
| Outreach Writer | Customer-facing language only | Sloppy or over-broad public wording |

## Required Source Signoff Fields

Every source moving toward activation should have:

- `source_monitor_gate.status`
- `source_monitor_gate.reason`
- `evidence_trail_gate.status`
- `evidence_trail_gate.reason`
- `qa_critic_gate.status`
- `qa_critic_gate.reason`
- `legal_language_gate.status`
- `legal_language_gate.allowed_wording`
- `legal_language_gate.forbidden_wording`
- `product_manager_gate.status`
- `product_manager_gate.buyer_relevance_reason`
- `code_architect_gate.status`
- `code_architect_gate.adapter_or_code_notes`
- `final_activation_gate.status`
- `final_activation_gate.reason`

## Required Adapter Signoff Fields

Every adapter family should document:

- adapter name and version;
- source types it supports;
- required config fields;
- output schema;
- failure modes;
- source-health risk;
- noise risk;
- fixture coverage;
- when not to use the adapter.

## Forbidden Overclaims

- "Any website can be parsed."
- "Perfect parsing."
- "50 working sources" unless validator proves 50 activation-ready sources.
- "60 validated sources."
- "Guaranteed compliance."
- "Legal advice."
- "Regulator certified" or partnership implication.

## Gate Decision Rule

If Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, or Code Architect is `hold` or `fail`, the source cannot become activation-ready.
