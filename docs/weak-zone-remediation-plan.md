# Weak-Zone Remediation Plan

Date: 2026-06-16

## Current Truth

- Current source truth: **33 enabled UAE sources / 29 readiness-supported / 4 remediation**.
- Goal: **50 readiness-supported monitored UAE sources**.
- Remaining gap: **21** proof-backed, baseline-stable, gate-passing sources.
- Latest pushed commit verified before work: `81ab229`.
- Worktree clean before start: yes.

## Why This Sprint Exists

The project has enough candidate volume. The blocker is not discovery. The blocker is weak-zone remediation:

- JS-heavy pages that return nav shell.
- Stale or ambiguous official URLs.
- Official document/listing pages that need source-specific selectors.
- Duplicate aliases that pass no-save but collide with an already-active source.
- Access-blocked domains where StatuteProof must not bypass protection.

This sprint should improve adapters and activate only sources that pass no-save, evidence, repeat baseline, mass-monitor dry-run, and agent gates.

## Top 20 Candidates To Test

| Priority | Source ID | Weak zone | URL | Expected work |
| ---: | --- | --- | --- | --- |
| 1 | `AE-adgm-dp-regulatory-actions` | ADGM alternate components | `https://www.adgm.com/operating-in-adgm/office-of-data-protection/regulatory-actions` | Find cards/listing selector beyond basic `adgm-page`. |
| 2 | `AE-adgm-media-announcements` | ADGM alternate components | `https://www.adgm.com/media/announcements` | Build stricter announcement-card extraction or hold as high-noise. |
| 3 | `AE-adgm-listing-announcements` | ADGM alternate components | `https://www.adgm.com/financial-services-regulatory-authority/listing-authority/listing-authority-announcements` | Listing authority announcement selector. |
| 4 | `AE-adgm-ra-notices` | ADGM RA stale/alternate | `https://www.adgm.com/registration-authority/notices` | Determine if stale URL or alternate component. |
| 5 | `AE-adgm-ra-aml-guides` | ADGM RA stale/alternate | `https://www.adgm.com/registration-authority/aml-cft-quick-guides` | Determine replacement URL or selector. |
| 6 | `AE-uaefiu-aml-cft-laws` | UAE FIU SPA/XHR/docs | `https://uaefiu.gov.ae/en/more/knowledge-centre/aml-cft-laws-related-decisions/` | Playwright XHR/direct document discovery. |
| 7 | `AE-uaefiu-annual-reports` | UAE FIU SPA/XHR/docs | `https://uaefiu.gov.ae/en/more/knowledge-centre/publications/annual-report/` | Document listing extraction. |
| 8 | `AE-uaefiu-publications-hub` | UAE FIU SPA/XHR/docs | `https://uaefiu.gov.ae/en/more/knowledge-centre/publications/` | Hub/document extraction or hold if duplicate shell. |
| 9 | `AE-uaefiu-strategic-analysis` | UAE FIU SPA/XHR/docs | `https://uaefiu.gov.ae/en/more/knowledge-centre/publications/strategic-analysis-guidelines/` | Direct document endpoint or XHR. |
| 10 | `AE-uaefiu-nra-2024` | UAE FIU SPA/XHR/docs | `https://uaefiu.gov.ae/en/more/knowledge-centre/publications/national-risk-assessment-report-2024/` | Direct document endpoint or XHR. |
| 11 | `AE-vara-rulebooks-overview` | VARA PDF/rulebooks | `https://www.vara.ae/en/regulatory-framework/rulebooks/` | PDF/rulebook links or not-found shell detection. |
| 12 | `AE-vara-aml-cft-rulebook` | VARA PDF/rulebooks | `https://www.vara.ae/en/regulatory-framework/aml-cft-rulebook/` | PDF/rulebook remediation. |
| 13 | `AE-vara-company-rulebook` | VARA PDF/rulebooks | `https://www.vara.ae/en/regulatory-framework/company-rulebook/` | PDF/rulebook remediation. |
| 14 | `AE-vara-public-register` | VARA register | `https://www.vara.ae/en/public-register/` | Public register extraction only if official/useful and not nav shell. |
| 15 | `AE-vara-news` | VARA updates | `https://www.vara.ae/en/news/` | Only activate if regulatory update/PDF listing, not marketing news. |
| 16 | `AE-dfsa-published-decisions` | DFSA/DIFC selectors | `https://www.dfsa.ae/what-we-do/enforcement/published-decisions` | Enforcement listing selector. |
| 17 | `AE-dfsa-enforcement-regulatory-actions` | DFSA/DIFC selectors | `https://www.dfsa.ae/what-we-do/enforcement/regulatory-actions` | Enforcement listing selector or access hold. |
| 18 | `AE-dfsa-consultation-papers` | DFSA/DIFC selectors | `https://www.dfsa.ae/your-resources/publications/consultation-papers` | Consultation listing selector. |
| 19 | `AE-cbuae-publications` | CBUAE access/docs | `https://www.centralbank.ae/en/publications/` | Official alternate/document links; no WAF bypass. |
| 20 | `AE-cbuae-circulars` | CBUAE access/docs | `https://www.centralbank.ae/en/regulations/` | Regulation/circular document listing if accessible. |

## Batch Order

1. **ADGM alternate components**: highest chance because ADGM already has working Playwright/custom-element patterns.
2. **UAE FIU**: high MLRO relevance; needs XHR/direct document discovery.
3. **VARA**: high buyer relevance for VASP compliance; needs PDF/rulebook remediation.
4. **DFSA/DIFC**: important but many pages are selector/access blocked.
5. **CBUAE**: official but frequently access-blocked; use only safe public alternates.

## Adapter / Selector Plan

- Add fixture tests before adapter changes where behavior changes.
- Improve or add targeted adapters only:
  - ADGM alternate listing/card extraction.
  - UAE FIU document/knowledge-centre extraction.
  - VARA PDF/rulebook shell detection and document extraction.
  - CBUAE document listing/access classification.
  - DFSA/DIFC listing selector support.
- Keep the existing evidence/proof pipeline intact.

## Validation Plan

Run after implementation and registry updates:

```bash
git status --short
python3 -m compileall product/regradar
python3 -m pytest product/regradar/tests -q
python3 tools/validate_source_discovery_engine.py
python3 tools/validate_source_activation_pipeline.py
python3 tools/validate_mass_source_activation_pipeline.py
python3 tools/validate_mass_monitoring_runner.py
python3 tools/validate_batch_onboarding.py
python3 tools/validate_uae_source_pack.py
python3 tools/validate_uae_50_working_sources.py
python3 tools/validate_parser_quality.py
python3 tools/validate_workspace.py
python3 tools/validate_codex_skills.py
git diff --check
```

## Commit Policy

- Stage only task files.
- Do not stage runtime junk, secrets, or unrelated files.
- Commit only if validation passes.
- Commit message: `feat: remediate weak UAE source zones toward 50-source pack`.

## What Will Not Be Touched

- Cloudflare, DigitalOcean, deployment, secrets, `.env`, customer emails, Telegram, and private portals.
- No CAPTCHA/paywall/login bypass.
- No fake evidence or no-save-only activation.
