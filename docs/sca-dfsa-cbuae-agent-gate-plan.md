# SCA / DFSA / CBUAE Agent Gate Plan

Date: 2026-06-15

## Agents / Skills Used Or Emulated

Executable StatuteProof subagents were not directly callable in this Codex session, so the official 10-agent roster is emulated manually. No 11th active agent is added.

Inspected:

- `AGENTS.md`
- `TOOL_ROUTER.md`
- `.claude/agents/`
- `agents/`
- `.agents/skills/`
- `skills/`
- `workflows/`

Skills consulted:

- `source-monitoring-review`
- `evidence-readiness-review`
- `custom-source-parser`
- `custom-source-monitoring-spec`
- `legal-safe-copy-review`
- `systematic-debugging`
- `test-driven-development`
- `verification-before-completion`
- `prompt-injection-review`

## Gate Ownership

| Agent | Gate | Blocks |
|---|---|---|
| Chief of Staff | Scope control | Broad monitoring, all-source runs, infrastructure, unrelated staging, 11th agent |
| Product Manager | Buyer relevance | Vanity sources, weak MLRO/CCO value, source-count padding |
| Code Architect | Architecture safety | Broad rewrites, unsafe dependencies, source registry mutation without gates |
| QA / Critic | Truth gate | Fake-ready states, no-save evidence claims, one-run monitoring-ready claims |
| Legal Language | Customer-safe wording | Legal advice, guaranteed compliance, regulator certification/partnership, 50/60 overclaims |
| Source Monitor | Source health | Unofficial URLs, wrong endpoints, weak selectors/adapters, source-health/noise risks |
| Evidence Trail | Proof/baseline | Missing proof paths, missing hashes, missing repeat baseline, incomplete source runs |
| Risk + Brief Pipeline | Brief eligibility | Any brief/risk workflow without complete evidence |
| ICP Lead Research | Relevance | Non-UAE or low-compliance-value sources |
| Outreach Writer | Public messaging | Only used if customer-facing copy changes; must pass Legal Language |

## Required SCA / DFSA / CBUAE Per-Source Fields

Every candidate must keep:

- `source_id`
- `url`
- `regulator`
- `source_type`
- `official_status`
- `discovery_status`
- `adapter_family`
- `adapter_name`
- `adapter_config`
- `no_save_status`
- `quality_score`
- `noise_risk`
- `source_health_risk`
- `evidence_status`
- `baseline_status`
- `activation_status`
- `failure_code`
- `failure_reason`
- `remediation_hint`
- `agent_gate_status`
- `final_activation_gate`

## Required Gate Fields

Every gate object must include:

- `status`: `pass`, `hold`, or `fail`
- `reason`
- `reviewed_at`
- `blocking_issues`

## Gate Rules

SCA:

- Source Monitor blocks generic About/Services/Open Data pages unless a clear register/public-data monitoring purpose is documented.
- QA blocks malformed doubled paths unless normalized or explicitly accepted.
- Code Architect blocks activation until listing/table extraction is deterministic.

DFSA:

- Source Monitor blocks unknown DOM outputs from becoming ready.
- Code Architect requires selector/module fixture coverage for rulebook/listing paths.
- Evidence Trail blocks activation without proof and repeat baseline.

CBUAE:

- Source Monitor maps HTTP 403 to access/source-health remediation, not readiness.
- Code Architect allows only safe official alternate discovery, not WAF bypass.
- Legal Language blocks wording that implies blocked CBUAE pages are monitored.

## Activation Gate

A candidate can become `activation_ready` only when all of the following pass:

1. official/public/access policy check;
2. adapter/selector/API/PDF/listing strategy;
3. no-save Source Lab pass;
4. no nav-shell/shallow/duplicate-shell hash;
5. acceptable noise/source-health risk or documented resolved filter;
6. saved proof/evidence exists;
7. repeat baseline passes;
8. Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, and Code Architect gates pass;
9. activation decision recorded.

This sprint must not use no-save or discovery to claim monitoring readiness.
