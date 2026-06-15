# Autonomous 50-Source Current State

Date: 2026-06-15

## Current Counts

- Activation-ready/current active sources: 22
- Enabled UAE sources: 26
- Readiness-supported: 22
- Remediation: 4
- Remaining to 50: 28

## Current Activation-Ready Sources

| source_id | regulator | title | adapter | proof |
| --- | --- | --- | --- | --- |
| AE-adgm-fsra-waivers | ADGM Financial Services Regulatory Authority (FSRA) | ADGM FSRA Waivers and Modifications Register | custom_element | yes |
| AE-adgm-ra-circulars | ADGM Registration Authority (RA) | ADGM Registration Authority Circulars | custom_element | yes |
| AE-adgm-fsra-consultations | ADGM/FSRA | ADGM FSRA Consultations | custom_element | yes |
| AE-adgm-fsra-financial-crime-prevention | ADGM/FSRA | ADGM FSRA Financial Crime Prevention | custom_element | yes |
| AE-adgm-fsra-guidance-policy | ADGM/FSRA | ADGM FSRA Guidance and Policy Statements | custom_element | yes |
| AE-adgm-fsra-rulebooks | ADGM/FSRA | ADGM FSRA Rulebooks | custom_element | yes |
| AE-abu-dhabi-global-market-adgm | Abu Dhabi Global Market (ADGM) | Abu Dhabi Global Market (ADGM) |  | legacy/queue |
| AE-cbuae-regulations | CBUAE | CBUAE Regulations | cbuae_document_listing | legacy/queue |
| AE-central-bank-of-the-uae | Central Bank of the UAE | Central Bank of the UAE |  | legacy/queue |
| AE-dfsa-aml-rulebook-module | DFSA / DIFC | DFSA AML Rulebook Module | static_html | yes |
| AE-dfsa-financial-crime-mlro-letters | DFSA / DIFC | DFSA Financial Crime Prevention Notices and MLRO Letters | dfsa_notice_listing | yes |
| AE-dubai-virtual-assets-regulatory-authority-vara | Dubai Virtual Assets Regulatory Authority (VARA) | Dubai Virtual Assets Regulatory Authority (VARA) |  | legacy/queue |
| AE-eocn-laws-regulations-en | Executive Office for Control and Non-Proliferation (EOCN) | EOCN AML/CFT Laws and Regulations | listing | yes |
| AE-eocn-news-en | EOCN | EOCN News and Sanctions Updates | eocn_news_listing | yes |
| AE-uaefiu-typology-reports | UAE FIU | UAE FIU Trends and Typology Reports | fiu_eocn_document_listing | yes |
| AE-uaefiu-circulars | UAE FIU Circulars and Notices | UAE FIU Circulars and Notices | fiu_eocn_document_listing | legacy/queue |
| AE-uae-legislation-portal | UAE Legislation | UAE Legislation Portal |  | legacy/queue |
| AE-uae-ministry-of-economy | UAE Ministry of Economy | UAE Ministry of Economy |  | legacy/queue |
| AE-uae-ministry-of-finance | UAE Ministry of Finance | UAE Ministry of Finance |  | legacy/queue |
| AE-sca-circulars-rules-procedures | UAE Securities and Commodities Authority | SCA Circulars, Rules and Procedures | sca_listing | yes |
| AE-sca-regulations-listing | SCA | SCA Regulations Listing | sca_listing | yes |
| AE-vara-enforcement | VARA | VARA Enforcement Notices | vara_pdf_listing | legacy/queue |

## Candidates Closest To Activation

| source_id | regulator | quality | status | blocker | next_action |
| --- | --- | --- | --- | --- | --- |
| AE-adgm-legal-framework-rules | ADGM | 56 | readiness_supported_no_save | Not activation-ready under agent-gated standard. | dedupe_with_adgm_fsra_rulebooks_before_save |
| AE-adgm-ra-aml-guides | ADGM RA | 0 | target | not yet tested | run_no_save_with_adapter_hint |
| AE-adgm-ra-notices | ADGM RA | 0 | target | not yet tested | run_no_save_with_adapter_hint |
| AE-adgm-listing-rules | ADGM/FSRA | 0 | target | not yet tested | run_no_save_with_adapter_hint |
| AE-dfsa-aml-mlro-notices | DFSA | 59 | readiness_supported_no_save | Extracted content is a navigation shell or collides with another source hash. | continue_source_remediation_or_validation |
| AE-dfsa-rulebook-thomsonreuters | DFSA | 59 | readiness_supported_no_save | Extracted content is a navigation shell or collides with another source hash. | continue_source_remediation_or_validation |
| AE-sca-aml-cft | SCA | 55 | remediation | Saved run extracted only carousel/navigation text: Previous / Next. | no_save_retest_or_remediate |
| AE-uae-fiu-publications | UAE FIU | 55 | blocked | HTTP 403 on UAE FIU publications path; Playwright fallback fetched content but access/sour | run_no_save |
| AE-uaefiu-aml-cft-laws | UAE FIU | 0 | target | not yet tested | run_no_save_with_adapter_hint |
| AE-uaefiu-mutual-evaluation | UAE FIU | 65 | remediation | Duplicate normalized hash with active AE-uaefiu-typology-reports. | find_specific_mutual_evaluation_document_url |
| AE-uaefiu-nra-2024 | UAE FIU | 0 | target | not yet tested | run_no_save_with_adapter_hint |
| AE-uaefiu-strategic-analysis | UAE FIU | 0 | target | not yet tested | run_no_save_with_adapter_hint |

## Blocked / Remediation Groups

- FIU: AML/CFT laws near threshold, several route variants duplicate typology output.
- SCA: JS-filtered regulation pages remain nav/filter shell.
- ADGM: alternate media/data-protection components need selectors beyond `adgm-page`.
- DFSA/DIFC/CBUAE: access/nav-shell/source model blockers remain.

## Fastest Path To 50

1. Convert the next FIU/ADGM/SCA near-ready batch into 3-5 more proof-backed active sources.
2. Build SCA filter/listing or XHR extraction to unlock regulation/amendments/market-rules pages.
3. Add ADGM alternate component selector map.
4. Use scoreboard-driven batch runner to process accepted candidates 5-10 at a time.

## Fastest Path To Batch-Onboarding Factory

- Treat `uae_50_activation_scoreboard.json` as the master queue.
- Add a validator that ensures scoreboard active states cannot diverge from `sources.json` proof/baseline/gates.
- Add a batch runner mode that writes no-save results back to the scoreboard without activating.
