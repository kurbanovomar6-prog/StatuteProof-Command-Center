# All-In-One UAE Source Activation Plan

Date: 2026-06-15

## 1. Current Repo State

- Latest pushed commit reported by the task: `78e913b`.
- Clean state gate passed before this plan: no modified files were present.
- Product code is under `product/regradar`.
- Mass source activation, source discovery, Auto DOM Investigator, adapter platform, Source Lab remediation UI, safe batch activation runner, and mass-monitor dry-run runner already exist.

## 2. Current Public Source Truth

Current customer-facing UAE source truth before this sprint:

`13 enabled / 9 readiness-supported / 4 remediation`

This sprint may change the truth only if `sources.json`, evidence paths, repeat baseline state, agent gates, mass-monitor dry-run, and validators all support the change.

## 3. What Previous Sprint Completed

- Built the safe mass-monitor runner.
- Proved two queue entries are activation-ready after proof, repeat baseline, and agent gates:
  - `AE-sca-circulars-rules-procedures`
  - `AE-dfsa-financial-crime-mlro-letters`
- Held `AE-dfsa-aml-rulebook-module` despite proof/repeat baseline because monitor dry-run produced hash drift.
- Left `sources.json` unchanged.

## 4. Why Sources Still Do Not Activate

- Some sources pass no-save but are not evidence-backed.
- Some sources are evidence-backed but fail monitor stability.
- Some sources are blocked by noisy listing extraction, unknown DOM shape, WAF/403, 404, or weak quality scores.
- Validators intentionally hard-stop public truth changes unless registry/readiness evidence is reconciled.

## 5. Exact Goal For This Sprint

1. Activate only the two proven queue-ready sources in `sources.json` if schema and validators allow it.
2. Update queue/validator truth only when the registry state proves it.
3. Investigate and, if feasible, stabilize `AE-dfsa-aml-rulebook-module` hash drift.
4. Run controlled high-priority candidate checks only where safe.
5. Save evidence and repeat baseline only for strong no-save passes.
6. Leave weak sources in hold/remediation/blocked with exact reasons.
7. Commit only after validation passes.

## 6. Source Groups To Prioritize

1. Proven activation-ready queue entries.
2. DFSA AML rulebook module hash-drift remediation.
3. ADGM/FSRA near-ready candidates.
4. SCA regulations/AML/listing candidates.
5. DFSA official-linked rulebooks/notices/enforcement.
6. VARA and FIU/EOCN if official endpoints are already clear.
7. CBUAE only through official public alternate endpoints; no access bypassing.

## 7. Agent / Skill Gate Plan

Agents are emulated manually using the approved 10-agent roster:

- Chief of Staff: scope control and no 11th active agent.
- Product Manager: buyer relevance and no vanity source padding.
- Code Architect: registry/adapter/runner safety.
- QA / Critic: no fake-ready, no no-save-only activation.
- Legal Language: no legal advice, guarantee, or regulator certification claim.
- Source Monitor: official URL, selector/adapter, source-health.
- Evidence Trail: proof paths, hashes, repeat baseline.
- Risk + Brief Pipeline: no brief without complete evidence.
- ICP Lead Research: UAE MLRO/CCO relevance.
- Outreach Writer: unused unless public copy changes.

Skills used/emulated: source monitoring review, evidence readiness review, custom source parser review, legal-safe copy review, test-driven development, and verification before completion.

## 8. Files To Inspect

- `docs/mass-monitoring-war-room-final-report.md`
- `docs/mass-monitoring-agent-gated-activation-decision.md`
- `docs/mass-monitoring-saved-evidence-baseline-report.md`
- `docs/mass-monitoring-live-validation-report.md`
- `product/regradar/config/mass_source_activation_queue.json`
- `product/regradar/config/uae_source_work_queue.json`
- `product/regradar/config/uae_source_candidates.json`
- `product/regradar/sources.json`
- `product/regradar/app/mass_monitoring_runner.py`
- `product/regradar/app/mass_source_activation.py`
- `product/regradar/app/source_intake.py`
- `product/regradar/run.py`
- `tools/validate_mass_monitoring_runner.py`
- `tools/validate_mass_source_activation_pipeline.py`
- `tools/validate_uae_source_pack.py`
- `tools/validate_uae_50_working_sources.py`

## 9. Files Likely To Change

- `product/regradar/sources.json`
- `product/regradar/config/mass_source_activation_queue.json`
- `product/regradar/config/uae_source_candidates.json` only if public truth metadata must be reconciled.
- `tools/validate_mass_monitoring_runner.py`
- `tools/validate_mass_source_activation_pipeline.py`
- `tools/validate_uae_source_pack.py`
- sprint reports under `docs/`

Code changes are allowed only if needed to fix deterministic extraction or validation logic.

## 10. Live Validation Plan

- Run no-save only for scoped candidates.
- Save proof only after strong no-save pass.
- Repeat baseline only for saved candidates.
- Run mass-monitor dry-run with `--activation-ready-only --dry-run --no-alerts`.
- Do not run broad monitoring or customer alerts.

## 11. Commit Plan

If validation passes:

`git commit -m "feat: activate proof-backed UAE monitoring sources"`

Then push to `main`.

If validation fails, do not commit code. Commit docs only if useful and safe.

## 12. What Will Not Be Touched

- Cloudflare.
- DigitalOcean.
- `.env` or secrets.
- Telegram/email/customer messaging.
- Paywalled/login/CAPTCHA/private portals.
- Unproven source activation.
- Runtime evidence artifacts unless project policy explicitly allows them.
