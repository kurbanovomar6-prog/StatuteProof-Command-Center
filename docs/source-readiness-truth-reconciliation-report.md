# Source Readiness Truth Reconciliation Report

Date: 2026-06-15
Updated: 2026-06-18

## Executive Decision

The canonical customer-facing truth for the current StatuteProof UAE source pack is:

**147 enabled UAE sources; 146 monitoring-active in the current registry; 1 remediation source.**

2026-06-18 update: the dirty **87 enabled / 86 active / 1 remediation** claim was rejected. Two ADGM rows (`AE-adgm-fsra-supervision-circulars` and `AE-adgm-data-protection-regulations-2021-pdf`) passed no-save, proof, 2/2 baseline, mass-monitor `MONITOR_OK`, and agent gates. Five FTA rows plus `AE-adgm-fsra-regulatory-alerts` were demoted to disabled candidates because they did not pass meaningful extraction gates.

2026-06-18 later update: the weak-family bulk activation sprint tested 213 candidate runs, held nav-shell/quality-drop/drift/duplicate candidates, and activated 41 proof-backed sources after no-save, two baseline runs, mass-monitor `MONITOR_OK`, no hash drift, and review gates. A later FTA PDF sprint tested 27 official FTA PDFs, held 2 weak/problematic documents, and activated 25 proof-backed direct official FTA tax PDFs after no-save, two stable baseline runs, mass-monitor `MONITOR_OK`, no hash drift, and review gates. Current truth is now **147 enabled / 146 monitoring-active / 1 remediation**. This is not a complete UAE coverage claim; weak families remain visible in the source-family scorecard.

The earlier **13 enabled / 10 confirmed / 3 remediation** story is not safe today. The later activation history advanced through proof-backed CBUAE, DFSA, VARA, DIFC, ADGM, UAE FIU, EOCN, SCA, and Ministry of Economy batches. The weak-family bulk sprint activated 41 additional DFSA/DIFC/Ministry of Economy sources from stable proof-backed runs, advancing the truth to **122 / 121 / 1**. The FTA PDF sprint then activated 25 direct official FTA tax PDFs from stable proof-backed runs and mass-monitor `MONITOR_OK`, advancing the truth to **147 / 146 / 1**. The UAE FIU homepage remains remediation because its live extraction is a navigation/search/language shell and tested replacements were shallow, blocked, stale, or duplicate-prone.

## Canonical Counts

| Count | Value | Basis |
| --- | ---: | --- |
| Total records in `sources.json` | 291 | Registry file parse after FTA PDF activation. |
| Enabled UAE sources | 147 | `enabled: true` and `jurisdiction: AE`. |
| Monitoring-active | 146 | Enabled UAE registry rows with `status: active`, excluding held/remediation rows. |
| Under extraction remediation | 1 | Enabled UAE registry row with `status: remediation`. |
| Blocked / failed | 0 | Current registry uses remediation rather than blocked for the one not-ready enabled source. |

## Readiness-Supported Sources

| Source ID used in reports/UI | Source name | Reason it remains readiness-supported |
| --- | --- | --- |
| `AE-central-bank-of-the-uae` | Central Bank of the UAE | Current readiness report lists proof/hash/run artifacts and registry support. |
| `AE-dubai-virtual-assets-regulatory-authority-vara` | Dubai Virtual Assets Regulatory Authority (VARA) | Current readiness report lists proof/hash/run artifacts and meaningful extraction. |
| `AE-abu-dhabi-global-market-adgm` | Abu Dhabi Global Market (ADGM) | Current readiness report keeps main ADGM source readiness-supported with caveats. |
| `AE-uae-ministry-of-finance` | UAE Ministry of Finance | Current readiness report lists meaningful extraction and evidence artifacts. |
| `AE-uae-legislation-portal` | UAE Legislation Portal | Current readiness report lists meaningful extraction and evidence artifacts. |
| `AE-uae-ministry-of-economy` | UAE Ministry of Economy | Current readiness report lists meaningful extraction and evidence artifacts. |
| `AE-vara-enforcement` | VARA Enforcement Notices | Current readiness report lists meaningful extraction and unique hash. |
| `AE-cbuae-regulations` | CBUAE Regulations Sub-page | Current readiness report lists meaningful extraction with known counter-change noise caveat. |
| `AE-uaefiu-circulars` | UAE FIU Circulars and Notices | Current readiness report treats publications/circulars as the readiness-supported FIU source. |
| `AE-sca-circulars-rules-procedures` | SCA Circulars, Rules and Procedures | Promoted from activation-ready queue after proof-backed repeat baseline and mass-monitor dry-run. |
| `AE-sca-regulations-listing` | SCA Regulations Listing | Promoted after SCA listing extraction, invalid pseudo-link cleanup, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-dfsa-financial-crime-mlro-letters` | DFSA Financial Crime Prevention Notices and MLRO Letters | Promoted from activation-ready queue after proof-backed repeat baseline and mass-monitor dry-run. |
| `AE-dfsa-aml-rulebook-module` | DFSA AML Rulebook Module | Promoted from activation-ready queue after proof-backed repeat baseline and a scoped monitor-path dry-run reproduced the stored hash. |
| `AE-adgm-fsra-financial-crime-prevention` | ADGM FSRA Financial and Cyber Crime Prevention | Promoted from activation-ready queue after focused custom-element extraction, proof-backed repeat baseline, and mass-monitor dry-run. |
| `AE-adgm-fsra-rulebooks` | ADGM FSRA Rules and Regulations | Promoted from activation-ready queue after proof-backed repeat baseline and mass-monitor dry-run on the current ADGM legal-framework URL. |
| `AE-adgm-fsra-consultations` | ADGM Public Consultations | Promoted from activation-ready queue after focused custom-element extraction, proof-backed repeat baseline, and mass-monitor dry-run. |
| `AE-adgm-fsra-guidance-policy` | ADGM FSRA Guidance and Policy Statements | Promoted after custom-element extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-eocn-laws-regulations-en` | EOCN AML/CFT Laws and Regulations | Promoted after listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-adgm-fsra-waivers` | ADGM FSRA Waivers and Modifications Register | Promoted after custom-element extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-adgm-ra-circulars` | ADGM Registration Authority Circulars | Promoted after custom-element extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-uaefiu-typology-reports` | UAE FIU Trends and Typology Reports | Promoted after FIU/EOCN document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-eocn-news-en` | EOCN News and Sanctions Updates | Promoted after source-specific EOCN news listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-sca-fatca-crs` | SCA FATCA and CRS Guidance | Promoted after SCA listing extraction was expanded for FATCA/CRS document links, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-adgm-listing-rules` | ADGM FSRA Listing Authority Rules and Guidance | Promoted after ADGM web-component document listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-sca-corporate-governance` | SCA Corporate Governance Regulations | Promoted after table adapter header normalization, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-adgm-dp-guidance` | ADGM Data Protection Guidance | Promoted after focused custom-element extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-adgm-fsra-enforcement` | ADGM FSRA Enforcement | Promoted after focused custom-element extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-sca-aml-cft` | UAE SCA Anti-Money Laundering and Terrorist Financing | Promoted after `sca_listing` extraction isolated AML/CFT document links, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-dfsa-rulebook-thomsonreuters` | DFSA Rulebook Modules | Promoted after officially linked Thomson Reuters rulebook module extraction with `article` selector, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-uaefiu-aml-cft-laws` | UAE FIU AML/CFT Laws and Related Decisions | Promoted after weak-zone FIU listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-uaefiu-publications-hub` | UAE FIU Publications Hub | Promoted after FIU/EOCN document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-rulebook-revision-updates` | CBUAE Rulebook Revision Updates | Promoted after official Central Bank rulebook subdomain extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-vara-rulebook-updates` | VARA Rulebook Revision Updates | Promoted after official VARA rulebook update extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-vara-compliance-risk-rulebook-pdf` | VARA Compliance and Risk Management Rulebook PDF | Promoted after direct official VARA PDF extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-vara-technology-information-rulebook-pdf` | VARA Technology and Information Rulebook PDF | Promoted after direct official VARA PDF extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-vara-va-issuance-rulebook-pdf` | VARA Virtual Asset Issuance Rulebook PDF | Promoted after direct official VARA PDF extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-vara-broker-dealer-rulebook-pdf` | VARA Broker-Dealer Services Rulebook PDF | Promoted after direct official VARA PDF extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-vara-lending-borrowing-rulebook-pdf` | VARA Lending and Borrowing Services Rulebook PDF | Promoted after direct official VARA PDF extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-vara-va-regulations-2023-pdf` | VARA Virtual Assets and Related Activities Regulations 2023 PDF | Promoted after direct official VARA PDF extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-dfsa-consultation-current` | DFSA Consultation Papers Current | Promoted after current official DFSA consultation listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-dfsa-enforcement-decisions-current` | DFSA Published Enforcement Decisions | Promoted after official DFSA enforcement decision listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-dfsa-regulatory-actions-current` | DFSA Enforcement Regulatory Actions | Promoted after official DFSA regulatory action listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-retail-payment-services-rulebook` | CBUAE Retail Payment Services and Card Schemes Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-dfsa-consultation-paper-165` | DFSA Consultation Paper No.165 | Promoted after official-linked Thomson Reuters DFSA consultation listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-dfsa-notice-supervisory-review` | DFSA Supervisory Review Rulebook | Promoted after official-linked Thomson Reuters DFSA rulebook extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-amlcft-rulebook-doclist` | CBUAE AML/CFT Rulebook Document Links | Promoted after stable CBUAE document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-amlcft-entire-section-doclist` | CBUAE AML/CFT Entire Section Document Links | Promoted after stable CBUAE document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-consumer-protection-rulebook-doclist` | CBUAE Consumer Protection Regulation Document Links | Promoted after stable CBUAE document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-open-finance-rulebook` | CBUAE Open Finance Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-payment-token-services-rulebook` | CBUAE Payment Token Services Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-risk-management-rulebook` | CBUAE Risk Management Rulebook | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-stored-value-facilities-doclist` | CBUAE Stored Value Facilities Regulation | Promoted after exact official CBUAE rulebook URL remediation, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-operational-risk-regulation-doclist` | CBUAE Operational Risk Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-market-risk-regulation-doclist` | CBUAE Market Risk Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-large-exposures-regulation-doclist` | CBUAE Large Exposures Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-exchange-business-regulation-doclist` | CBUAE Exchange Business Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-capital-adequacy-doclist` | CBUAE Capital Adequacy | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-large-value-payment-systems-doclist` | CBUAE Large Value Payment Systems Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-federal-decree-law-6-2025-doclist` | Federal Decree Law No. 6 of 2025 Regarding the Central Bank | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-country-transfer-risk-regulation-doclist` | CBUAE Country and Transfer Risk Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-interest-rate-risk-regulation-doclist` | CBUAE Interest Rate and Rate of Return Risk Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-model-management-standards-doclist` | CBUAE Model Management Standards | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-retail-payment-systems-regulation-doclist` | CBUAE Retail Payment Systems Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-sme-customer-protection-regulation-doclist` | CBUAE SME Customer Protection Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-islamic-banks-risk-management-doclist` | CBUAE Islamic Banks Risk Management Standard | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-market-conduct-consumer-protection-doclist` | CBUAE Market Conduct and Consumer Protection | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-proliferation-finance-guidance-doclist` | CBUAE Proliferation Finance Guidance | Promoted after official CBUAE AML guidance extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-tbml-transshipment-guidance-doclist` | CBUAE TBML and Transshipment Guidance | Promoted after official CBUAE AML guidance extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-difc-laws-and-regulations` | DIFC Laws and Regulations | Converted from remediation after `difc_legal_database` extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-difc-legal-database` | DIFC Legal Database | Promoted after source-specific DIFC legal/PDF listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-difc-data-protection-commissioner` | DIFC Commissioner of Data Protection | Promoted after DIFC data-protection listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-difc-data-protection-guidance` | DIFC Data Protection Guidance | Promoted after DIFC data-protection guidance extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-difc-data-protection-regulation-10` | DIFC Data Protection Regulation 10 | Promoted after official DIFC Commissioner page extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-difc-data-protection-supervision-enforcement` | DIFC Data Protection Supervision and Enforcement | Promoted after DIFC supervision/enforcement listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-difc-data-protection-law-2020` | DIFC Data Protection Law 2020 | Promoted after rendered official DIFC legal database detail extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-difc-companies-law-2018` | DIFC Companies Law 2018 | Promoted after rendered official DIFC legal database detail extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-dfsa-annual-reports` | DFSA Annual Reports | Replaced stale DFSA main remediation endpoint after official DFSA PDF-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-dfsa-annual-aml-reports` | DFSA Annual Anti-Money Laundering Reports | Replaced stale DFSA notices remediation endpoint after official DFSA AML report PDF-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-adgm-fsra-supervision-circulars` | ADGM FSRA Supervision Circulars | Activated after official ADGM listing extraction, proof-backed repeat baseline, mass-monitor dry-run `MONITOR_OK`, and agent gates. |
| `AE-adgm-data-protection-regulations-2021-pdf` | ADGM Data Protection Regulations 2021 PDF | Activated after line-preserving PDF extraction, proof-backed repeat baseline, mass-monitor dry-run `MONITOR_OK`, and agent gates. |
| `AE-moet-aml-170b7988` | Ministry of Economy — AML | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-moet-auditing-accounts-legislations-84d91bc4` | Ministry of Economy — Auditing Accounts Legislations | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-moet-economic-substance-regulations-a5b9825b` | Ministry of Economy — Economic Substance Regulations | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-moet-registering-companies-in-goaml-c83375da` | Ministry of Economy — Registering Companies In goAML | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-moet-regulation-of-business-fd17959e` | Ministry of Economy — Regulation Of Business | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-moet-regulation-of-competition-ba53cc4c` | Ministry of Economy — Regulation Of Competition | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-moet-targeted-financial-sanctions-586d6f96` | Ministry of Economy — Targeted Financial Sanctions | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-amendment-dfsa-forms-3-5b23279e` | DFSA — News Notice Amendment DFSA Forms 3 | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-amendment-dfsa-forms-4-238b095a` | DFSA — News Notice Amendment DFSA Forms 4 | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-amendment-dfsa-forms-5-87f5ab7b` | DFSA — News Notice Amendment DFSA Forms 5 | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-amendment-dfsa-forms-6-516f99a2` | DFSA — News Notice Amendment DFSA Forms 6 | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-amendments-1-c8efa9bf` | DFSA — News Notice Amendments 1 | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-amendments-3fadbb97` | DFSA — News Notice Amendments | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-amendments-dfsa-forms-1-7eb3ddbd` | DFSA — News Notice Amendments DFSA Forms 1 | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-amendments-dfsa-forms-2-26da0ea8` | DFSA — News Notice Amendments DFSA Forms 2 | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-amendments-dfsa-forms-3-6a085fc2` | DFSA — News Notice Amendments DFSA Forms 3 | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-amendments-dfsa-forms-4-871a906a` | DFSA — News Notice Amendments DFSA Forms 4 | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-amendments-dfsa-forms-fdd4d828` | DFSA — News Notice Amendments DFSA Forms | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-amendments-legislation-b5739a79` | DFSA — News Notice Amendments Legislation | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dubai-financial-services-authority-dfsa` | DFSA Rules and Standards | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-difc-business-aml-cft-991d9543` | DIFC — Business AML CFT | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-difc-business-economic-substance-regulations-05c9f19b` | DIFC — Business Economic Substance Regulations | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-difc-whats-on-insights-difc-data-protection-law-pioneers-6615d880` | DIFC — Whats On Insights DIFC Data Protection Law Pioneers | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-difc-whats-on-news-difc-arbitration-law-consultation-684af25c` | DIFC — Whats On News DIFC Arbitration Law Consultation | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-rulebook-official` | DFSA — Rulebook Official | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-consultation-papers` | DFSA — Consultation Papers | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-relation-cp90-1ea4f448` | DFSA — News Notice Relation CP90 | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-discussion-paper-67ac395d` | DFSA — News Notice Discussion Paper | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-consultation-paper-26232647` | DFSA — News Notice Consultation Paper | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-amendments-rulebook-f3b17fd6` | DFSA — News Notice Amendments Rulebook | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-consultation-paper-1-0fd2727d` | DFSA — News Notice Consultation Paper 1 | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-consultation-paper-2-ce31d49f` | DFSA — News Notice Consultation Paper 2 | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-consultation-release-128d0518` | DFSA — News Notice Consultation Release | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-amendments-rulebook-1-a3b7e98d` | DFSA — News Notice Amendments Rulebook 1 | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-amendments-rulebook-2-51efcaf3` | DFSA — News Notice Amendments Rulebook 2 | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-amendments-rulebook-3-5fb25116` | DFSA — News Notice Amendments Rulebook 3 | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-amendments-rulebook-4-532da6ec` | DFSA — News Notice Amendments Rulebook 4 | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-amendments-rulebook-5-2fceb723` | DFSA — News Notice Amendments Rulebook 5 | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-amendments-rulebook-6-077b65fb` | DFSA — News Notice Amendments Rulebook 6 | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-call-evidence-release-0e8f9854` | DFSA — News Notice Call Evidence Release | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |
| `AE-dfsa-news-notice-consultation-release-1-f752cf93` | DFSA — News Notice Consultation Release 1 | Activated in weak-family bulk sprint after no-save, two proof-backed baselines, mass-monitor `MONITOR_OK`, no dry-run hash drift, and review gates. |

## Sources Under Extraction Remediation

| Source ID used in reports/UI | Source name | Reason |
| --- | --- | --- |
| `AE-uae-financial-intelligence-unit-uaefiu` | UAE FIU Homepage | Homepage extraction is a navigation/search/language shell with quality score 0. Tested replacement candidates did not pass: NRA page was single-document/limited, direct NRA PDF returned HTTP 403, strategic-analysis route returned Error404/nav-shell, and the annual-report route looked duplicate-prone against existing FIU publication sources. UAE FIU Circulars and Publications remain the readiness-supported FIU endpoints. |

## Disabled Or Replaced Endpoints

| Source ID | Status | Replacement | Reason |
| --- | --- | --- | --- |
| `AE-dubai-financial-services-authority-dfsa` | Reactivated / active | None | Later weak-family bulk sprint proved a stable DFSA Rules and Standards extraction with proof, repeat baseline, and MONITOR_OK. |
| `AE-dfsa-notices` | Replaced / disabled | `AE-dfsa-annual-aml-reports` | Current URL rendered the same page-not-found/nav-shell output and was not safe to keep customer-visible as readiness remediation. |
| `AE-fta-tax-legislation-listing` | Candidate / disabled | None | Listing-page extraction is now understood via `fta_tax_listing`, but monitoring-active FTA coverage came from direct PDF endpoints. Keep listing pages candidate until pagination/filter item-level extraction is fully gated. |
| `AE-fta-vat-guides-references` | Candidate / disabled | None | Listing-page extraction is now understood via `fta_tax_listing`, but direct official PDF endpoints are the active monitored objects. |
| `AE-fta-corporate-tax-guides-references` | Candidate / disabled | None | Listing-page extraction is now understood via `fta_tax_listing`, but direct official PDF endpoints are the active monitored objects. |
| `AE-fta-media-centre` | Candidate / disabled | None | Media centre remains candidate-only because press-release pages need relevance/noise filtering before activation. |
| `AE-fta-corporate-tax-legislation` | Candidate / disabled | None | Listing-page extraction is now understood via `fta_tax_listing`, but direct official PDF endpoints are the active monitored objects. |
| `AE-adgm-fsra-regulatory-alerts` | Candidate / disabled | None | Official/public page, but current selector isolated no alert rows and remained nav-shell-like. |

## Which Story Is Correct?

**Correct today:** 147 enabled / 146 monitoring-active / 1 remediation.

**Not correct today:** 13 enabled / 10 confirmed / 3 under extraction remediation.

Reason: the final-8 sprint moved the registry and work queue over the 50-source gate using proof-backed, repeat-baseline-complete, mass-monitor-checked official CBUAE/DFSA sources. The VARA source-depth sprint then added six direct official VARA rulebook PDFs after direct-PDF extraction, two proof-backed baselines, mass-monitor `MONITOR_OK`, and agent gates. The DIFC remediation sprint then moved DIFC Laws and Regulations out of remediation and added seven further official DIFC legal/data-protection sources after proof, repeat baseline, and dry-run gates. The final remediation sprint replaced two stale DFSA configured sources with official DFSA report listings that passed proof, baseline, mass-monitor, and review gates. The FTA/ADGM eight-row repair activated two proof-backed ADGM sources and demoted six unvalidated dirty active rows. The UAE FIU homepage remains held/remediation. A source may have meaningful extraction while still not being customer-visible ready if its registry hold, source model, evidence baseline, or activation review is incomplete.

## Allowed Customer-Facing Wording

- "147 enabled UAE sources."
- "146 monitoring-active in the current registry."
- "50 activation-ready UAE official source endpoints."
- "Each activation-ready source passed proof, baseline, source-health, noise, and review gates."
- "1 remediation source."
- "Source readiness in progress."
- "DFSA source model under remediation."
- "DIFC coverage improved, but StatuteProof does not claim end-to-end DIFC source scope."
- "UAE FIU Circulars and Notices is the readiness-supported FIU source; the UAE FIU homepage remains under remediation."
- "Evidence-backed monitoring requires proof artifacts and baseline review before activation."

## Forbidden Wording

- "All 147 sources are validated."
- "All 147 sources are confirmed."
- "All 147 sources are ready."
- "87 enabled / 86 active."
- "DFSA ready."
- "End-to-end DIFC source coverage."
- "Certified monitoring."
- "Flawless parser."
- "Any website can be parsed."
- "Guaranteed regulatory outcome."

## Code And UI Result

Current public/app source tables should use the 147/146/1 model:

- `product/regradar/web/src/components/SourceCoverageTable.jsx`
- `product/regradar/web/src/data/appMockData.js`
- Pricing and billing surfaces use "147 enabled" with 146 monitoring-active and 1 remediation only where public truth is intentionally surfaced.

This sprint changes `sources.json` only for proof-backed, repeat-baseline-complete, mass-monitor-checked activation-ready sources. Future changes should derive source IDs and counts from one generated registry summary rather than duplicating constants in frontend/docs.

## Next Required Source Readiness Work

1. Add 7/30/90-day source reliability charts for readiness-supported sources.
2. Find ADGM alternate component selectors or replacement URLs for data-protection regulatory actions and listing announcements.
3. Add bulk review/export workflows for MLRO operations.
4. Add a generated source-readiness summary artifact consumed by validators and frontend source tables.
