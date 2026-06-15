# Mass Source Onboarding Architecture Spec

Date: 2026-06-15

## Goal

StatuteProof needs a repeatable batch pipeline for official public regulatory sources:

official URL discovery -> adapter/selector selection -> no-save test -> quality gate -> evidence save -> repeat baseline -> source-health/noise review -> agent gates -> activation decision -> `sources.json` update only if proven.

This architecture does not claim any website can be parsed. It makes failure reasons explicit and prevents fake-ready source counts.

## Source States

| State | Meaning | Can Be Customer-Facing As Ready |
|---|---|---|
| `candidate` | Source proposed but not tested. | No |
| `discovered` | Discovery found possible endpoint(s). | No |
| `no_save_passed` | Preview extraction passed without evidence write. | No |
| `proof_saved` | Evidence/proof artifact exists from a scoped save. | No |
| `baseline_pending` | Proof exists but repeat baseline/gates are incomplete. | No |
| `activation_ready` | Proof, baseline, gates, risks, and activation decision passed. | Only as part of current truthful count after validators pass |
| `remediation` | Fix selector/adapter/noise/source-health. | No |
| `blocked` | Access/technical/legal policy blocks monitoring. | No |
| `rejected` | Not official/relevant/useful/safe enough. | No |

## Batch Pipeline

1. Candidate discovery batch
   - Inputs: official regulator URLs, sitemap/feed/API/PDF/link candidates, manually curated candidates.
   - Output: inactive queue entries.

2. Official/public/access check
   - Reject private portals, login/CAPTCHA/paywalls, private/personal data, unsafe URLs, off-domain pages without official linkage.

3. Auto DOM investigation
   - Detect content type, selectors, tables, listings, PDF links, custom elements, nav-shell risk, noise risk, source-health risk.

4. Adapter recommendation
   - Static HTML, Playwright selector, custom element, listing, table, PDF document, PDF listing, rulebook/module, register, feed, public JSON/API, or source-specific adapter.

5. No-save batch test
   - No evidence write.
   - No alert/customer delivery.
   - Records quality, hash, preview, failure code, remediation hint.

6. Quality gate
   - Blocks nav-shell, shallow content, duplicate boilerplate hash, high unresolved noise/source-health, unsupported content, blocked access.

7. Evidence save batch
   - Only for strong no-save passes.
   - Records proof path, normalized text/hash, raw/rendered artifacts when available.

8. Repeat baseline
   - Default requirement: 2 successful baseline runs.
   - One saved run is evidence, not monitoring-ready.

9. Noise/source-health scoring
   - Blocks high unresolved alert-fatigue risk.
   - Blocks high unresolved maintenance/source-health risk.

10. Agent gates
   - Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, Code Architect.

11. Activation decision
   - `activation_ready` only if all required conditions pass.

12. `sources.json` update
   - Only activation-ready sources can be proposed for active registry update.
   - New public counts require registry + readiness summary + validators.

13. Customer-facing count update
   - Never from candidate/no-save/proof-only states.

## Required Queue Entry Fields

Each mass source queue entry must include:

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

## Required Gate Fields

Each entry must include:

- `source_monitor_gate`
- `evidence_trail_gate`
- `qa_critic_gate`
- `legal_language_gate`
- `product_manager_gate`
- `code_architect_gate`
- `final_activation_gate`

Each gate includes `status`, `reason`, `reviewed_at`, and `blocking_issues`.

## Activation-Ready Rule

A source can be `activation_ready` only when:

- official/public status is accepted;
- adapter and selector/API/PDF/listing strategy are explicit;
- no-save passed;
- proof path exists;
- normalized text/hash exists or evidence metadata documents why not;
- baseline is complete;
- no nav-shell;
- no shallow content;
- no duplicate boilerplate hash;
- high noise risk is resolved;
- high source-health risk is resolved;
- Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, and Code Architect gates pass.

## What This Does Not Do Yet

- It does not activate 50 sources.
- It does not rewrite all parsers.
- It does not run broad monitoring.
- It does not change customer-facing source truth.
- It does not delete legacy discovery code until parity is proven.
