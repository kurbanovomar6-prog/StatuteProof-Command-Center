# Mass Monitoring Agent Gate Plan

## Agents / Skills Used Or Emulated

Actual subagent execution tools were not invoked in this sprint; the project agents are emulated manually from `AGENTS.md`, `.claude/agents/`, `agents/`, `TOOL_ROUTER.md`, and repo skills. This does not create an 11th active agent.

Skills reviewed and applied:

- `source-monitoring-review`
- `evidence-readiness-review`
- `custom-source-parser`
- `custom-source-monitoring-spec`
- `legal-safe-copy-review`
- `test-driven-development`
- `verification-before-completion`
- `systematic-debugging`
- `prompt-injection-review`
- `evidence-audit`

## Agent Gates

| Agent | Gate Ownership | Can Block |
|---|---|---|
| Chief of Staff | Scope control, no 11th agent, execution sequencing | Broad monitoring, unrelated scope, unsafe sprint expansion |
| Product Manager | Buyer relevance and no vanity source padding | Low-value pages, generic homepages, source-count padding |
| Code Architect | Adapter/runner design, maintainability, dependency risk | Broad rewrites, unsafe dependencies, brittle architecture |
| QA / Critic | False-ready prevention, regression risk, tests | No-save activation, weak tests, fake readiness |
| Legal Language | Customer-facing claims | Legal advice, guarantees, regulator certification, “any website” claims |
| Source Monitor | Official source status, URL, selector, extraction, source health | Unofficial URLs, wrong endpoint, nav-shell extraction, unresolved source-health risk |
| Evidence Trail | Proof paths, hashes, baselines, append-only evidence | Missing proof, one-run activation, hash/path gaps |
| Risk + Brief Pipeline | Future brief eligibility from evidence | Brief/risk workflows without complete evidence |
| ICP Lead Research | MLRO/CCO relevance | Sources with unclear UAE compliance buyer value |
| Outreach Writer | Public/outreach copy only if touched | Sloppy or unsafe public messaging |

## Required Signoff Fields Per Source

Each source proposed for activation must have:

- `source_monitor_gate.status`: `pass` / `hold` / `fail`
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
- `code_architect_gate.reason`
- `final_activation_gate.status`
- `final_activation_gate.reason`

## Required Signoff Fields Per Monitoring Run

Each mass-monitoring run must record:

- source id, URL, adapter, final URL
- run mode: dry-run/no-alerts/save-proof
- source state before run
- source-health status
- normalized hash and previous hash when available
- proof/run paths when saved
- skipped reason for non-activation-ready sources
- alert delivery status, which must remain disabled by default

## Mandatory Blocks

- No source can activate from no-save only.
- No source can be monitoring-ready from one saved run.
- Candidate/remediation/blocked/rejected sources must not be monitored by default.
- High noise or high source-health risk blocks activation unless an explicit filter/remediation is recorded.
- `sources.json` must not receive unproven active sources.
- Public truth remains `13 enabled / 9 readiness-supported / 4 remediation` unless proof, registry state, and validators prove a change.

## No 11th Active Agent

This sprint uses the existing 10-agent roster only. Additional labels such as “runner”, “validator”, or “DOM investigator” are implementation components, not new active agents.
