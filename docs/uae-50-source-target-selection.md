# UAE 50 Source Target Selection

## Executive Result

Selected target count: **55**.

This is a target and work-queue selection, not a claim that 55 sources are working. The activation-ready count after this sprint is **2**.

Current public truth remains:

**13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation.**

## Selected 55 Targets

| # | source_id | regulator | priority | gate status | strategy | next action |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | AE-adgm-fsra-financial-crime-prevention | ADGM/FSRA | P0 | activation_ready | playwright_selector | source_monitor_founder_review_then_sources_json_candidate_activation |
| 2 | AE-adgm-fsra-rulebooks | ADGM/FSRA | P0 | activation_ready | playwright_selector | source_monitor_founder_review_then_sources_json_candidate_activation |
| 3 | AE-adgm-fsra-guidance-policy | ADGM/FSRA | P0 | baseline_pending | playwright_selector | add_item_level_noise_filters_then_save_baseline |
| 4 | AE-dfsa-aml-mlro-notices | DFSA | P0 | baseline_pending | listing_adapter | continue_source_remediation_or_validation |
| 5 | AE-dfsa-rulebook-thomsonreuters | DFSA | P0 | baseline_pending | static_html | continue_source_remediation_or_validation |
| 6 | AE-adgm-fsra-consultations | ADGM/FSRA | P1 | baseline_pending | playwright_selector | build_consultation_item_diff_filter_then_save_baseline |
| 7 | AE-adgm-fsra-enforcement | ADGM/FSRA | P1 | baseline_pending | playwright_selector | save_baseline_only_if_source_label_is_broadened_or_split |
| 8 | AE-adgm-legal-framework-rules | ADGM | P1 | baseline_pending | playwright_selector | dedupe_with_adgm_fsra_rulebooks_before_save |
| 9 | AE-adgm-fsra-notices | ADGM/FSRA | P0 | remediation | listing_adapter | continue_source_remediation_or_validation |
| 10 | AE-dfsa-notices | DFSA Regulatory Notices | P0 | remediation | static_html | continue_source_remediation_or_validation |
| 11 | AE-difc-laws-and-regulations | DIFC Laws and Regulations | P0 | remediation | static_html | continue_source_remediation_or_validation |
| 12 | AE-dubai-financial-services-authority-dfsa | Dubai Financial Services Authority (DFSA) | P0 | remediation | static_html | continue_source_remediation_or_validation |
| 13 | AE-sca-aml-cft | SCA | P0 | remediation | playwright_selector | selector_adapter_remediation_before_save |
| 14 | AE-sca-latest-regulations | SCA | P0 | remediation | playwright_selector | build_sca_listing_adapter_then_repeat_activation_review |
| 15 | AE-uae-financial-intelligence-unit-uaefiu | UAE Financial Intelligence Unit (UAEFIU) | P0 | remediation | static_html | continue_source_remediation_or_validation |
| 16 | AE-vara-aml-cft-rulebook | VARA | P0 | remediation | pdf_extractor | continue_source_remediation_or_validation |
| 17 | AE-vara-company-rulebook | VARA | P0 | remediation | pdf_extractor | continue_source_remediation_or_validation |
| 18 | AE-vara-enforcement | VARA | P0 | remediation | playwright_selector | continue_source_remediation_or_validation |
| 19 | AE-vara-regulatory-framework | VARA | P0 | remediation | pdf_extractor | continue_source_remediation_or_validation |
| 20 | AE-vara-rulebooks-overview | VARA | P0 | remediation | pdf_extractor | continue_source_remediation_or_validation |
| 21 | AE-adgm-fsra-public-register | ADGM/FSRA | P1 | remediation | playwright_selector | build_register_adapter_before_activation |
| 22 | AE-adgm-legal-framework-legislation | ADGM | P1 | remediation | playwright_selector | keep_remediation_until_specific_legislation_page_passes |
| 23 | AE-sca-circulars | SCA | P1 | remediation | playwright_selector | build_card_listing_adapter_then_retest |
| 24 | AE-sca-regulations | SCA | P1 | remediation | playwright_selector | keep_legacy_candidate_replaced_by_split_source_id |
| 25 | AE-uae-legislation-portal | UAE Legislation | P1 | remediation | static_html | continue_source_remediation_or_validation |
| 26 | AE-vara-homepage | VARA | P1 | remediation | playwright_selector | continue_source_remediation_or_validation |
| 27 | AE-vara-public-register | VARA | P1 | remediation | listing_adapter | continue_source_remediation_or_validation |
| 28 | AE-sca-homepage | SCA | P2 | remediation | playwright_selector | do_not_activate_homepage_use_specific_sources |
| 29 | AE-sca-news | SCA | P2 | remediation | playwright_selector | defer |
| 30 | AE-abu-dhabi-global-market-adgm | Abu Dhabi Global Market (ADGM) | P0 | candidate | static_html | continue_source_remediation_or_validation |
| 31 | AE-central-bank-of-the-uae | Central Bank of the UAE | P0 | candidate | static_html | continue_source_remediation_or_validation |
| 32 | AE-dubai-virtual-assets-regulatory-authority-vara | Dubai Virtual Assets Regulatory Authority (VARA) | P0 | candidate | static_html | continue_source_remediation_or_validation |
| 33 | AE-uae-ministry-of-economy | UAE Ministry of Economy | P0 | candidate | static_html | continue_source_remediation_or_validation |
| 34 | AE-uae-ministry-of-finance | UAE Ministry of Finance | P0 | candidate | static_html | continue_source_remediation_or_validation |
| 35 | AE-uaefiu-circulars | UAE FIU Circulars and Notices | P0 | candidate | static_html | continue_source_remediation_or_validation |
| 36 | AE-adgm-fsra-rules | ADGM FSRA Rulebook | P1 | candidate | static_html | continue_source_remediation_or_validation |
| 37 | AE-cbuae-circulars | CBUAE Circulars | P1 | candidate | static_html | continue_source_remediation_or_validation |
| 38 | AE-dfsa-aml-ctf-sanctions | DFSA | P1 | candidate | playwright_selector | continue_source_remediation_or_validation |
| 39 | AE-dfsa-public-register | DFSA | P1 | candidate | listing_adapter | continue_source_remediation_or_validation |
| 40 | AE-difc-legal-database | DIFC | P1 | candidate | static_html | continue_source_remediation_or_validation |
| 41 | AE-difc-legislation | DIFC Laws Portal | P1 | candidate | static_html | continue_source_remediation_or_validation |
| 42 | AE-uaefiu-guidance | UAE FIU AML Guidance | P1 | candidate | static_html | continue_source_remediation_or_validation |
| 43 | AE-vara-rulebook | VARA Virtual Assets Regulation | P1 | candidate | static_html | continue_source_remediation_or_validation |
| 44 | AE-adgm-data-protection | ADGM | P2 | candidate | static_html | continue_source_remediation_or_validation |
| 45 | AE-cbuae-consumer-protection | CBUAE | P2 | candidate | static_html | continue_source_remediation_or_validation |
| 46 | AE-cbuae-news | CBUAE | P2 | candidate | listing_adapter | continue_source_remediation_or_validation |
| 47 | AE-cbuae-open-data | CBUAE | P2 | candidate | table_adapter | continue_source_remediation_or_validation |
| 48 | AE-dfsa-publications | DFSA | P2 | candidate | listing_adapter | continue_source_remediation_or_validation |
| 49 | AE-difc-consultation-papers | DIFC | P2 | candidate | listing_adapter | continue_source_remediation_or_validation |
| 50 | AE-difc-data-protection | DIFC | P2 | candidate | static_html | continue_source_remediation_or_validation |
| 51 | AE-federal-tax-authority-homepage | Federal Tax Authority | P2 | candidate | static_html | continue_source_remediation_or_validation |
| 52 | AE-fta-corporate-tax-guides | Federal Tax Authority | P2 | candidate | static_html | continue_source_remediation_or_validation |
| 53 | AE-fta-vat-public-clarifications | Federal Tax Authority | P2 | candidate | static_html | continue_source_remediation_or_validation |
| 54 | AE-uae-elaws-moj | UAE Ministry of Justice | P2 | candidate | static_html | continue_source_remediation_or_validation |
| 55 | AE-uaefiu-awareness | UAE FIU | P2 | candidate | static_html | continue_source_remediation_or_validation |

## Backup Candidates

| source_id | regulator | priority | status | blocker |
| --- | --- | --- | --- | --- |
| AE-cbuae-aml-cft | CBUAE | P0 | blocked | Source appears to require login, CAPTCHA, paywall access, or a private portal. |
| AE-cbuae-regulations | CBUAE | P0 | blocked | Source appears to require login, CAPTCHA, paywall access, or a private portal. |
| AE-dfsa-enforcement-regulatory-actions | DFSA | P0 | blocked | Source appears to require login, CAPTCHA, paywall access, or a private portal. |
| AE-dfsa-rulebook-official | DFSA | P0 | blocked | Source appears to require login, CAPTCHA, paywall access, or a private portal. |
| AE-eocn-homepage | Executive Office for Control and Non-Proliferation | P0 | blocked | Source appears to require login, CAPTCHA, paywall access, or a private portal. |
| AE-uaefiu-goaml-public | UAE FIU | P0 | blocked | Source appears to require login, CAPTCHA, paywall access, or a private portal. |
| AE-uaefiu-publications | UAE FIU | P0 | blocked | Source appears to require login, CAPTCHA, paywall access, or a private portal. |
| AE-adgm-fsra-homepage | ADGM/FSRA | P1 | blocked | Official page is useful for discovery but too broad for default monitoring. |
| AE-cbuae-consultations | CBUAE | P1 | blocked | Source appears to require login, CAPTCHA, paywall access, or a private portal. |
| AE-cbuae-homepage | CBUAE | P1 | blocked | Source appears to require login, CAPTCHA, paywall access, or a private portal. |
| AE-cbuae-licensing | CBUAE | P1 | blocked | Source appears to require login, CAPTCHA, paywall access, or a private portal. |
| AE-cbuae-payment-systems | CBUAE | P1 | blocked | Source appears to require login, CAPTCHA, paywall access, or a private portal. |
| AE-cbuae-publications | CBUAE | P1 | blocked | Source appears to require login, CAPTCHA, paywall access, or a private portal. |
| AE-dfsa-consultation-papers | DFSA | P1 | blocked | Source appears to require login, CAPTCHA, paywall access, or a private portal. |
| AE-difc-laws-regulations | DIFC | P1 | blocked | Source appears to require login, CAPTCHA, paywall access, or a private portal. |
| AE-moec-aml | Ministry of Economy | P1 | blocked | Source appears to require login, CAPTCHA, paywall access, or a private portal. |
| AE-mof-homepage | Ministry of Finance | P1 | blocked | Source appears to require login, CAPTCHA, paywall access, or a private portal. |
| AE-sca-decisions | SCA | P1 | blocked | Legacy decisions URL returned service-shell output; current decision items appe… |
| AE-sca-laws | SCA | P1 | blocked | Legacy laws URL returned service-shell output; regulations-listing remains CAPT… |
| AE-sca-legislation | SCA | P1 | blocked | Legacy /en/legislation.aspx redirects through a 404 handler to the home/service… |

## Rejected Candidates

No candidates were newly rejected in this sprint. The queue still preserves blocked and remediation candidates rather than deleting useful official-source research.

## Agent Gate Summary

- Source Monitor rejected/blocked access-risk sources from counting as working.
- Evidence Trail allowed only proof-backed and baseline-complete candidates to progress.
- QA/Critic blocked high source-health SCA listing output from activation.
- Legal Language preserved cautious wording and blocked `validated`, `certified`, and `50 working` claims.
- Product Manager accepted only official/relevant UAE compliance sources as targets, not vanity padding.
