# Fresh Source Expansion To 25 Plan

Date: 2026-06-19

## Current Truth

- Latest pushed commit before this task: `bdbcfb0`.
- Enabled UAE sources: 226.
- Fresh-alert eligible sources: 156.
- Evidence-library-only sources: 61.
- Candidate/pending sources: 6.
- Remediation sources: 3.
- Strong fresh-signal families already at or above 25: CBUAE, FTA, MoE/DNFBP AML.

## Weak Families And Deficits

| Family | Current Fresh Alert MONITOR_OK | Target | Deficit |
|---|---:|---:|---:|
| VARA | 23 | 25 | 2 |
| DFSA | 12 | 25 | 13 |
| DIFC | 10 | 25 | 15 |
| ADGM/FSRA | 8 | 25 | 17 |
| UAE FIU | 5 | 25 | 20 |
| EOCN/TFS | 22 | 25 | 3 |
| SCA | 4 | 25 | 21 |
| MoJ/Gazette | 0 | 25 | 25 |
| MoF | 0 | 25 | 25 |

## Sources That Count As Fresh Signal

Count only official/public endpoints that can produce future customer-relevant updates:

- update/listing pages for laws, regulations, rulebooks, circulars, notices, consultations, enforcement, administrative orders, sanctions/TFS publications, official gazette/legal changes, and official publications;
- rulebook revision pages;
- official document/PDF hubs when the listing changes as new documents are added;
- versioned official PDF/rulebook files only where hash monitoring can detect amendments;
- official unauthenticated public XHR/API endpoints only if technically public and permitted.

## Sources That Do Not Count

Do not use these to fill family counts:

- generic homepages;
- marketing pages;
- old individual article/news/detail pages;
- static archived consultation details;
- duplicate URLs or duplicate normalized hashes;
- login, CAPTCHA, paywall, private portal, private API, or credentialed URLs;
- nav-shell-only or shallow pages;
- pages that cannot realistically produce useful future alerts.

## Family Research Strategy

- VARA: target enforcement/admin orders, regulatory notices, rulebook revision pages, additional versioned rulebooks or guidance.
- DFSA: target rulebook modules, consultation listings, enforcement/publication listings, financial crime/AML publications, regulatory action listings. Static notice details remain evidence-library.
- DIFC: target legal database/listings, legal notices, consultations, data protection updates, official law/PDF/document listings. Static news/whats-on pages remain evidence-library.
- ADGM/FSRA: target circulars, regulatory alerts, consultations, guidance, policy statements, enforcement, waivers, listing authority updates, Registration Authority circulars, legal framework updates, and data protection listings.
- UAE FIU: target publications, typologies, NRA, AML/CFT laws, annual reports, press releases, and public circulars if accessible. Do not use goAML.
- EOCN/TFS: target direct EOCN laws/regulations, TFS guidance, sanctions guidance, publications, notices, news, and designation pages with noise controls. MoE substitutes must be labelled partial.
- SCA: target laws, decisions, regulations, circulars, procedures, AML/CFT, enforcement/violations, market notices, investor alerts, and public PDF/download endpoints.
- MoJ/Gazette: target UAE legislation portal, official gazette, federal laws/decrees, legal database, Ministry of Justice legal updates, and official PDF/document listings. Respect WAF/access controls.
- MoF: target specific decision/news/document/publication pages for federal finance decisions, tax treaties, fiscal policy, budget publications, and official announcements. Generic homepage does not count.

## Adapter Plan

Use existing configured adapters first: `dfsa_notice_listing`, `difc_legal_database`, `adgm_fsra_listing`, `fiu_eocn_document_listing`, `eocn_news_listing`, `sca_listing`, `vara_pdf_listing`, `pdf_document`, `document_listing`, `listing`, and `playwright_selector`.

If generic extraction fails but the source is official and useful, add or refine the smallest source-specific adapter needed. New adapter behavior must include fixture tests for meaningful extraction, nav-shell rejection, duplicate/static detail rejection, and MONITOR_OK readiness gates.

## Proof / Baseline / MONITOR_OK Plan

For each candidate:

1. Run no-save intake first.
2. Reject if nav-shell, shallow, access-blocked, duplicate, static-detail, generic homepage, high-noise unresolved, or high source-health unresolved.
3. Save evidence only for strong no-save passes.
4. Require proof path, normalized text path, normalized hash, and repeat baseline completion.
5. Run mass-monitor dry-run and require `MONITOR_OK`.
6. Mark as `fresh_alert` only after Source Monitor, Evidence Trail, QA/Critic, Legal Language, Product Manager, and Code Architect gates are satisfied.

## Validator Plan

Create or update:

- `tools/validate_fresh_source_expansion_to_25.py`
- `tools/validate_fresh_signal_25_per_family.py`
- `tools/validate_fresh_signal_sources.py`
- `tools/validate_daily_checkable_sources.py`
- `tools/validate_no_static_sources_as_alerts.py`
- `tools/validate_source_monitoring_modes.py`
- `tools/validate_uae_coverage_claims.py`

Validators must fail if static pages, generic homepages, evidence-library sources, remediation sources, no-save-only sources, or unproven sources are counted as fresh monitoring.

## Commit Policy

- Do not stage unrelated files.
- Do not stage runtime junk or secrets.
- Do not commit unless tests and validators pass.
- If every weak family reaches 25, use `feat: complete UAE fresh source families to 25 monitors`.
- If some families remain below 25 with hard blockers, use `feat: expand UAE fresh source monitoring with proven blockers`.

## What Will Not Be Claimed

- Complete UAE coverage.
- Complete family coverage unless validator-proven.
- Legal advice.
- Guaranteed compliance.
- Perfect parsing.
- Never-miss updates.
- Regulator certification or partnership.
