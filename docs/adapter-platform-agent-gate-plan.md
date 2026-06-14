# Adapter Platform Agent Gate Plan

## 1. Agent Use

The 10 official StatuteProof agents from `AGENTS.md` are used as manual review gates. No 11th active agent is added.

Actual subagent execution tools are not exposed in this Codex session, so each gate is **emulated manually** and recorded in docs, tests, validators, and work-queue fields.

## 2. Skills Used

- `source-monitoring-review`: source officialness, URL safety, extraction route, source health.
- `evidence-readiness-review`: proof paths, hashes, baseline rules.
- `custom-source-parser`: no-save/save/activation distinctions.
- `legal-safe-copy-review`: forbidden claims and customer-safe language.
- `test-driven-development`: tests before/with code changes.
- `systematic-debugging`: root-cause before fixes.
- `verification-before-completion`: fresh validation before completion claims.

## 3. Agent Gate Responsibilities

| Agent | Adapter Gate | Can Block |
|---|---|---|
| Chief of Staff | Scope and sequencing | Broad monitoring, deployment, or adding an 11th agent. |
| Product Manager | Buyer relevance | Vanity sources that do not matter to UAE MLRO/CCO users. |
| Code Architect | Adapter architecture | Broad rewrite, unsafe dependency, evidence-pipeline breakage. |
| QA / Critic | False-ready prevention | Nav-shell, shallow text, duplicate hashes, fake 50-source claims. |
| Legal Language | Claim safety | Legal advice, guarantee, certification, “any website,” “60 validated.” |
| Source Monitor | Official-source monitoring | Wrong URL, private/protected source, unstable selector, high source-health risk. |
| Evidence Trail | Proof/baseline | Missing proof, one-run activation, incomplete baseline, broken hash chain. |
| Risk + Brief Pipeline | Future brief eligibility | Brief path without complete evidence or human review. |
| ICP Lead Research | Compliance buyer relevance | Sources that are official but not useful for the default UAE pack. |
| Outreach Writer | Only if copy changed | Generic or overclaiming outbound/source-pack language. |

## 4. Required Adapter Signoff Fields

Each adapter family should be documented with:

- `adapter_family`
- `adapter_name`
- `adapter_version`
- `supported_source_types`
- `input_config`
- `output_schema`
- `failure_modes`
- `noise_risk_controls`
- `source_health_controls`
- `tests`
- `code_architect_gate`
- `source_monitor_gate`
- `qa_critic_gate`

## 5. Required Source Signoff Fields

Each candidate source in the work queue should include:

- `adapter_family`
- `adapter_name`
- `adapter_version`
- `adapter_config`
- `extraction_strategy`
- `last_adapter_test_at`
- `adapter_status`
- `adapter_failure_reason`
- `adapter_remediation_hint`
- `source_monitor_gate`
- `evidence_trail_gate`
- `qa_critic_gate`
- `legal_language_gate`
- `code_architect_gate`
- `product_manager_gate`
- `final_activation_gate`

## 6. Non-Negotiable Blocking Rules

- No no-save result becomes evidence.
- No one-run evidence becomes monitoring-ready.
- No high-noise/high-source-health source activates without remediation/filter notes.
- No blocked/private/login/CAPTCHA/paywalled source is monitored.
- No customer-facing count changes unless validators and source-readiness docs prove it.
- No “any website can be parsed,” “perfect parsing,” “guaranteed compliance,” or regulator-certified claims.
