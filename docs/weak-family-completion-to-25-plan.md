# Weak-Family Completion To 25 Plan

Date: 2026-06-19

## Current Truth

Current verified truth before this sprint: **147 enabled UAE sources / 146 monitoring-active / 1 remediation**.

FTA / Tax already reached 25 monitoring-active direct official FTA PDF endpoints in the prior sprint. FTA is out of scope for new activation here except for validation and count reconciliation.

Correct product promise remains: StatuteProof monitors selected public official or officially linked UAE sources that are technically accessible and permitted to be monitored. Monitoring intelligence only. Not legal advice.

## Target Families And Deficits

| Family | Current active | Target | Deficit |
| --- | ---: | ---: | ---: |
| DIFC | 12 | 25 | 13 |
| ADGM/FSRA | 12 | 25 | 13 |
| VARA | 9 | 25 | 16 |
| Ministry of Economy / DNFBP AML | 7 | 25 | 18 |
| SCA | 5 | 25 | 20 |
| UAE FIU | 4 active + 1 remediation | 25 active | 21 active, or remediation conversion +20 |
| EOCN / sanctions / TFS | 3 | 25 | 22 |

Minimum net-new active target across these seven families is 123 proof-backed sources.

## Execution Order

1. SCA
2. Ministry of Economy / DNFBP AML
3. EOCN / sanctions / TFS
4. UAE FIU
5. VARA
6. DIFC
7. ADGM/FSRA

This order prioritizes the weakest commercial families first, then fills the better but still under-25 regulatory families.

## Official-Source Discovery Strategy

- Use existing mapped universe files first: `uae_1000_source_universe_candidates.json`, `uae_top_250_activation_queue.json`, `uae_source_universe_candidates.json`, and `uae_source_work_queue.json`.
- Use public internet research only for gaps.
- Prefer official regulator/government domains, public legal databases, official document hubs, PDF stores, regulatory notices, circulars, rulebooks, consultations, enforcement notices, public sanctions/TFS publications, and official unauthenticated XHR/API endpoints.
- Reject private portals, login/CAPTCHA/paywall paths, private APIs, social media, generic marketing pages when a stronger regulatory endpoint exists, duplicate pages, nav-shell-only pages, and non-UAE sources unless officially linked to UAE regulation.

## Adapter Strategy By Family

| Family | Adapter work expected |
| --- | --- |
| SCA | Download/document adapter for `/assets/download/...`, laws/decisions/regulations extraction, circular/rules/procedures extraction, enforcement/violations extraction, Arabic/English duplicate handling. |
| Ministry of Economy / DNFBP AML | MoE document/listing adapter, DNFBP AML guidance extraction, beneficial ownership/company-law document extraction, MoE PDF/document link extraction. |
| EOCN / sanctions / TFS | EOCN laws/regulations adapter, TFS/sanctions publications adapter, designation-list noise controls, PDF/document listing extraction. |
| UAE FIU | Publication/NRA/typology adapter, PDF/document listing extraction, homepage nav-shell rejection, goAML private portal blocker, duplicate publication hash handling. |
| VARA | Guidance/admin-order adapter, document hub/listing adapter, enforcement/admin-order listing adapter, direct PDF/rulebook expansion. |
| DIFC | Legal database/listing adapter, document/PDF listing adapter, consultation/legal update adapter, nav-shell and duplicate-shell rejection. |
| ADGM/FSRA | ADGM web-component listing adapter, FSRA circulars/alerts/consultations adapter, ADGM legal/PDF listing adapter, RA notices/publication adapter. |

## No-Save / Evidence / Baseline / MONITOR_OK Loop

For every candidate:

1. Run no-save intake.
2. Require meaningful extraction, quality score, stable normalized hash, no nav-shell, no shallow content, no access block, no duplicate shell hash.
3. Save proof/evidence only for strong passes.
4. Run repeat baseline twice.
5. Run mass-monitor dry-run.
6. Require `MONITOR_OK`.
7. Require `change_detected=false`, unless a safe non-noisy diff is explicitly documented and approved.
8. Emulate/record Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, and Code Architect gates.
9. Update `sources.json` only through a strict activation spec with `source_id`, `proof_path`, `normalized_text_path`, `normalized_hash`, `baseline_runs_completed >= 2`, and `last_monitor_status: MONITOR_OK`.

## Hard Blockers That Justify Not Reaching 25

A family may remain below 25 only if the final report documents hard evidence for one or more of:

- Official/public source universe is smaller than the target after serious research.
- Candidate endpoints are private, login/CAPTCHA/paywall, or private portal only.
- Endpoints are generic marketing pages or nav shells.
- Endpoints duplicate already active sources by URL, meaning, or normalized hash.
- Source returns unsupported binaries without a safe extractor.
- Source has high unresolved noise or source-health risk.
- Source cannot pass repeat baseline or mass-monitor dry-run.
- Activation would mislead buyers about depth, usefulness, or reliability.

“Could not find sources quickly” is not a blocker.

## Validators To Update

- `tools/validate_weak_family_completion_25.py`
- `tools/validate_no_unvalidated_active_sources.py`
- `tools/validate_balanced_source_family_coverage.py`
- `tools/validate_uae_coverage_claims.py`
- `tools/validate_uae_source_pack.py`
- `tools/validate_uae_50_working_sources.py`
- Existing family validators where source truth counts change.

## Commit Policy

- Do not stage runtime junk or secrets.
- Do not stage unrelated files.
- Commit only after compile, tests, validators, and frontend validation if touched.
- If every family reaches 25, use `feat: complete weak UAE source families to 25 active endpoints`.
- If any family remains below 25 with hard blockers, use `feat: expand weak UAE source families toward 25 active endpoints`.

## What Will Not Be Claimed

- No complete UAE coverage claim.
- No complete family coverage claim unless the family is actually proven.
- No legal advice.
- No guaranteed compliance.
- No perfect parsing.
- No “never miss updates.”
- No regulator certification.
- No all-source coverage.
