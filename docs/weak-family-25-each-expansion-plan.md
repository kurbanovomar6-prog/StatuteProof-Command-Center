# Weak-Family 25-Each Expansion Plan

Date: 2026-06-19

## 1. Current Truth

Canonical starting truth is **122 enabled UAE sources / 121 monitoring-active / 1 remediation** from `sources.json` and the latest source-readiness reconciliation report.

The target weak families and starting monitoring-active counts are:

| Family | Starting active | Target | Deficit |
| --- | ---: | ---: | ---: |
| DIFC | 12 | 25 | 13 |
| ADGM/FSRA | 12 | 25 | 13 |
| VARA | 9 | 25 | 16 |
| Ministry of Economy / DNFBP AML | 7 | 25 | 18 |
| SCA | 5 | 25 | 20 |
| UAE FIU | 4 active + 1 remediation | 25 | 21 active, or remediation conversion +20 |
| EOCN / sanctions / TFS | 3 | 25 | 22 |
| FTA / Tax | 0 | 25 | 25 |

Minimum net-new activation target is 148 sources, but only proof-backed, repeat-baseline-tested, `MONITOR_OK` sources may be counted.

## 2. Why This Sprint Exists

The product is no longer blocked by basic source infrastructure, but customer trust is still held back by uneven family depth. CBUAE and DFSA are strong; FTA, FIU, EOCN, SCA, VARA, MoE/DNFBP, DIFC, and ADGM/FSRA need stronger official-source breadth before StatuteProof can credibly feel like a robust $399 UAE Monitor.

This sprint is not a source-count inflation sprint. Candidate URLs, no-save passes, and one-run evidence are not active monitoring.

## 3. Official-Source Discovery Strategy

Research and activation will be family-specific:

- DIFC: laws/regulations, document hub, data protection guidance, legal updates, consultations, and compliance-relevant publications.
- ADGM/FSRA: FSRA rulebooks, circulars, consultations, guidance, public notices, enforcement, RA AML/company-law material, data protection and courts only where compliance-relevant.
- VARA: direct rulebook PDFs, regulatory notices, admin/enforcement orders, activity rulebook pages, guidance pages, and public registers where public.
- Ministry of Economy / DNFBP AML: AML/DNFBP guidance, financial crime pages, beneficial ownership, auditors, commercial companies, competition, consumer protection, economic substance, and TFS material.
- SCA: laws, board decisions, regulations, circulars, market rules, enforcement/violations, public notices, AML/FATCA/CRS and listing-related official pages.
- UAE FIU: publications, typologies, NRA documents, circulars/notices, official reports, and public awareness documents. The goAML portal remains out of scope.
- EOCN / sanctions / TFS: AML/CFT laws, TFS guidance, proliferation financing material, public updates, list update pages only with noise controls, and publications.
- FTA / Tax: tax legislation, VAT/corporate/excise guides, public clarifications, tax procedures, VAT refunds, decisions, media releases only when tax-regulatory relevant, and document/PDF listings.

Only official or officially linked public sources may proceed. Private, login-gated, CAPTCHA, paywalled, or personal-data sources are rejected.

## 4. Adapter Strategy

Generic extraction is not enough for the remaining weak families. Expected adapter work:

- FTA listing/document card adapter with PDF/link extraction and nav-shell rejection.
- SCA laws/decisions/regulations adapter with English/Arabic duplicate handling.
- FIU publication/NRA/typology adapter and homepage shell rejection.
- EOCN sanctions/TFS adapter with noise controls and safe designation-list handling.
- MoE/DNFBP legal/document listing adapter.
- DIFC legal/document hub adapter refinements.
- ADGM/FSRA web-component/listing adapter refinements.
- VARA rulebook/guidance/admin-order adapter refinements.

Fixture tests will be added or extended before implementation behavior is relied upon.

## 5. No-Save / Evidence / Baseline Plan

The activation loop for every candidate is:

1. Controlled no-save investigation.
2. Reject nav-shell, shallow, blocked, private, duplicate, or low-value pages.
3. Save evidence only for strong no-save passes.
4. Run two repeat baselines.
5. Run mass-monitor dry-run.
6. Require `MONITOR_OK`.
7. Require no hash drift unless a safe non-noisy diff is explicitly documented.
8. Run or emulate Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, and Code Architect gates.
9. Only then update `sources.json` and queues.

## 6. Expected Blockers

- FTA pages previously returned title-only/nav-shell extraction and likely need item-level listing extraction.
- EOCN/TFS pages can be noisy because sanctions/designation pages may change frequently or include dynamic counters.
- FIU public material may be sparse; the homepage currently remains remediation because it extracts as a nav/search/language shell.
- SCA and MoJ-adjacent pages may have Arabic/English duplicates, shallow pages, and PDF/document listing quirks.
- VARA official depth may be limited if official public pages concentrate material into a small number of rulebooks.
- Some families may not honestly have 25 commercially useful public endpoints. If so, the final report must prove exhaustion rather than pretending.

## 7. Validation Plan

Run unit tests, source validators, no-overclaim validators, and new sprint validators:

- `python3 -m compileall -q product/regradar`
- `python3 -m pytest product/regradar/tests -q`
- `python3 tools/validate_weak_family_25_each.py`
- `python3 tools/validate_weak_family_bulk_activation.py`
- `python3 tools/validate_no_unvalidated_active_sources.py`
- `python3 tools/validate_uae_1000_source_universe.py`
- `python3 tools/validate_balanced_source_family_coverage.py`
- existing source, parser, workspace, codex-skill, and pricing validators
- `git diff --check`

Frontend validation runs only if frontend/customer copy changes.

## 8. Commit Policy

Commit only if validation passes. Stage only files changed for this sprint. Do not stage runtime junk, secrets, unrelated work, or generated artifacts outside the intended reports/configs/evidence paths.

Commit message:

- If every target family reaches 25: `feat: bring weak UAE source families to 25 active endpoints`
- If some families remain below 25 with documented blockers: `feat: expand weak UAE source families with proof-backed gates`

## 9. What Will Not Be Claimed

This sprint will not claim:

- complete UAE coverage
- complete regulator/family coverage
- guaranteed compliance
- legal advice
- perfect parsing
- never-miss monitoring
- regulator certification
- active monitoring for candidate-only or no-save-only sources

Safe positioning remains: StatuteProof monitors selected public official or officially linked UAE sources that pass technical and evidence gates. Monitoring intelligence only. Not legal advice.
