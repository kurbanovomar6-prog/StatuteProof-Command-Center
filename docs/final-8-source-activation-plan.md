# Final-8 Source Activation Plan

Date: 2026-06-16

## Current Truth

- Current public truth: **46 enabled UAE sources / 42 readiness-supported / 4 remediation**.
- Exact gap to 50 readiness-supported sources: **8**.
- Latest pushed commit before this run: `2cc35b1`.
- This sprint is a final targeted activation sprint, not a broad discovery sprint.

## Strongest Remaining Candidate Groups

1. **VARA official rulebook/PDF endpoints**: highest chance if direct PDF extraction and static drift can be controlled.
2. **CBUAE rulebook variants**: official `rulebook.centralbank.ae` pages worked in the previous cycle; more rulebook sections may activate if document-list extraction is stable.
3. **DFSA/official-linked leftovers**: DFSA current pages performed well after `dfsa_notice_listing` improvements.
4. **ADGM alternate components**: official but still component/selector-sensitive.
5. **DIFC legal/data-protection pages**: useful if public selectors or official alternates are accessible.
6. **UAE FIU leftovers**: only useful if unique document pages can be found; duplicate hub aliases must remain held.

## Top 30 Candidates To Test

| # | Source ID | Regulator | URL / expected URL | Expected fix |
| ---: | --- | --- | --- | --- |
| 1 | `AE-vara-aml-cft-controls` | VARA | `https://rulebooks.vara.ae/rulebook/c-amlcft-controls` | Stable rulebook/static extraction or PDF route. |
| 2 | `AE-vara-compliance-risk-rulebook` | VARA | `https://rulebooks.vara.ae/rulebook/compliance-and-risk-management-rulebook` | Fix static drift / hold if noisy. |
| 3 | `AE-vara-aml-cft-rulebook-pdf` | VARA | official VARA PDF file-store URL | Direct PDF extraction. |
| 4 | `AE-vara-company-rulebook-pdf` | VARA | official VARA PDF file-store URL | Direct PDF extraction. |
| 5 | `AE-vara-market-conduct-rulebook-pdf` | VARA | official VARA PDF file-store URL | Direct PDF extraction. |
| 6 | `AE-vara-technology-information-rulebook-pdf` | VARA | official VARA PDF file-store URL | Direct PDF extraction. |
| 7 | `AE-vara-transfer-settlement-rulebook-pdf` | VARA | official VARA PDF file-store URL | Direct PDF extraction. |
| 8 | `AE-cbuae-stored-value-facilities-rulebook` | CBUAE | official `rulebook.centralbank.ae` section | `cbuae_document_listing`. |
| 9 | `AE-cbuae-complaints-management-rulebook` | CBUAE | official `rulebook.centralbank.ae` section | `cbuae_document_listing`. |
| 10 | `AE-cbuae-open-finance-rulebook` | CBUAE | official `rulebook.centralbank.ae` section | `cbuae_document_listing`. |
| 11 | `AE-cbuae-payment-token-services-rulebook` | CBUAE | official `rulebook.centralbank.ae` section | `cbuae_document_listing`. |
| 12 | `AE-cbuae-risk-management-rulebook` | CBUAE | official `rulebook.centralbank.ae` section | `cbuae_document_listing`. |
| 13 | `AE-dfsa-published-decisions` | DFSA | `https://www.dfsa.ae/what-we-do/enforcement/published-decisions` | `dfsa_notice_listing`. |
| 14 | `AE-dfsa-publications` | DFSA | `https://www.dfsa.ae/your-resources/publications` | Listing/noise gate. |
| 15 | `AE-dfsa-aml-ctf-sanctions` | DFSA | `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance` | Listing or hold as duplicate/broad page. |
| 16 | `AE-dfsa-public-register` | DFSA | `https://www.dfsa.ae/public-register` | Register adapter or hold if search-only. |
| 17 | `AE-difc-data-protection` | DIFC | `https://www.difc.com/business/laws-and-regulations/data-protection/` | Selector/access remediation. |
| 18 | `AE-difc-consultation-papers` | DIFC | `https://www.difc.com/business/laws-and-regulations/consultation-papers/` | Selector/access remediation. |
| 19 | `AE-difc-legal-database` | DIFC | `https://www.difc.com/business/laws-and-regulations/legal-database/` | Selector/access remediation. |
| 20 | `AE-adgm-dp-regulatory-actions` | ADGM | `https://www.adgm.com/operating-in-adgm/office-of-data-protection/regulatory-actions` | Alternate component selector. |
| 21 | `AE-adgm-media-announcements` | ADGM | `https://www.adgm.com/media/announcements` | Card/listing extraction. |
| 22 | `AE-adgm-listing-announcements` | ADGM | ADGM listing authority announcements URL | Alternate component selector. |
| 23 | `AE-adgm-abu-dhabi-legislation` | ADGM | ADGM legal framework subpage | Custom element/static extraction. |
| 24 | `AE-adgm-federal-legislation` | ADGM | ADGM legal framework subpage | Custom element/static extraction. |
| 25 | `AE-uaefiu-press-releases` | UAE FIU | `https://uaefiu.gov.ae/en/more/media/press-releases/` | Only activate if regulatory and not noisy. |
| 26 | `AE-uaefiu-strategic-analysis` | UAE FIU | FIU strategic analysis route | Find unique document endpoint or hold. |
| 27 | `AE-uaefiu-nra-2024` | UAE FIU | FIU national risk assessment route | Find unique document endpoint or hold. |
| 28 | `AE-fta-corporate-tax-guides` | FTA | FTA corporate tax guides | Regulatory/public guide listing if accessible. |
| 29 | `AE-fta-vat-public-clarifications` | FTA | FTA VAT public clarifications | Regulatory/public clarification listing if accessible. |
| 30 | `AE-moec-aml-dnfbp` | Ministry of Economy | MOEC/MOET AML page | Public AML/DNFBP guidance extraction if accessible. |

## Batch Order

1. **Batch 1: closest to activation**: VARA held/near-pass, DFSA current leftovers, CBUAE rulebook variants.
2. **Batch 2: VARA PDF/static drift**: direct official PDF paths and static rulebook pages.
3. **Batch 3: CBUAE variants**: stored value, complaints, open finance, payment token, risk-management rulebooks.
4. **Batch 4: DIFC/DFSA leftovers**: public legal/data-protection/notices pages only.
5. **Batch 5: ADGM alternate components**: media, data protection, listing authority, legislation subpages.
6. **Batch 6: FIU/FTA/MOEC leftovers**: only if unique, public, and MLRO-relevant.

## Likely Fixes

- Add a direct PDF no-save path if existing `pdf_document` still returns shallow text for public PDF URLs.
- Prefer `cbuae_document_listing` over static CBUAE rulebook body extraction where static pages drift.
- Extend listing/document title inference where links say only "Download", "Read more", or "View".
- Keep DIFC/CBUAE main-site blocks as access remediation if public unauthenticated access still fails.
- Keep FIU aliases held if they duplicate activated FIU hub hashes.

## Activation Rules

No candidate can enter `sources.json` unless it has:

- official/public URL;
- strong no-save pass;
- meaningful content, not nav-shell, not shallow;
- no duplicate/shell hash collision;
- acceptable noise and source-health risk;
- saved proof;
- two stable baseline runs;
- mass-monitor dry-run `MONITOR_OK` or clearly documented non-noisy stability;
- six agent gates passed;
- validators passed.

## Validation Plan

Run:

- `git status --short`
- `python3 -m compileall product/regradar`
- `python3 -m pytest product/regradar/tests -q`
- `python3 tools/validate_source_discovery_engine.py` if present
- `python3 tools/validate_source_activation_pipeline.py` if present
- `python3 tools/validate_mass_source_activation_pipeline.py` if present
- `python3 tools/validate_mass_monitoring_runner.py` if present
- `python3 tools/validate_batch_onboarding.py` if present
- `python3 tools/validate_uae_source_pack.py`
- `python3 tools/validate_uae_50_working_sources.py`
- `python3 tools/validate_parser_quality.py`
- `python3 tools/validate_workspace.py`
- `python3 tools/validate_codex_skills.py`
- `git diff --check`

## Commit Policy

- Stage only files from this task.
- Do not stage runtime junk, secrets, broad evidence artifacts, or unrelated files.
- If 50 is reached and validation passes, commit with:
  `feat: reach gated UAE 50-source monitoring pack`.
- If fewer than 50 but real progress is made, commit with:
  `feat: advance final UAE source activation sprint`.

## Hard Stop Conditions

- 8 new sources become activation-ready and validators pass.
- 30 candidates are tested.
- 5 weak-zone batches are attempted.
- A hard access/legal/control blocker prevents safe progress.
- Context is low and a precise continuation prompt is updated.
