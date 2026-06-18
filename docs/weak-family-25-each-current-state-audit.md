# Weak-Family 25-Each Current State Audit

Date: 2026-06-19

Starting canonical truth: **122 enabled UAE sources / 121 monitoring-active / 1 remediation**. Monitoring intelligence only. Not legal advice.

This audit separates strict registry matching from the commercial scorecard counts supplied by the latest reports. `sources.json` does not yet have a normalized `source_family` field, so family classification is currently inferred from source IDs, names, URLs, and source-family queue metadata.

## DIFC

- Scorecard starting active count: 12
- Strict registry heuristic active count: 12
- Enabled remediation count by heuristic: 0
- Target active count: 25
- Scorecard deficit: 13
- Universe candidates: 98
- Universe rejected: 18
- Top-250 queue entries: 28
- Work queue related entries: 53
- Mass activation related entries: 11

### Active Source IDs
- `AE-difc-laws-and-regulations` — DIFC Laws and Regulations — https://www.difc.com/business/laws-and-regulations/
- `AE-difc-legal-database` — DIFC Legal Database — https://www.difc.com/business/laws-and-regulations/legal-database/
- `AE-difc-data-protection-commissioner` — DIFC Commissioner of Data Protection — https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection
- `AE-difc-data-protection-supervision-enforcement` — DIFC Data Protection Supervision and Enforcement — https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/supervision-enforcement
- `AE-difc-data-protection-guidance` — DIFC Data Protection Guidance — https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/guidance
- `AE-difc-data-protection-regulation-10` — DIFC Data Protection Regulation 10 — https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/regulation-10
- `AE-difc-data-protection-law-2020` — DIFC Data Protection Law 2020 — https://www.difc.com/business/laws-and-regulations/legal-database/difc-laws/data-protection-law-difc-law-no-5-2020
- `AE-difc-companies-law-2018` — DIFC Companies Law 2018 — https://www.difc.com/business/laws-and-regulations/legal-database/difc-laws/companies-law-difc-law-no-5-2018
- `AE-difc-business-aml-cft-991d9543` — DIFC — Business AML CFT — https://www.difc.com/business/aml-cft
- `AE-difc-business-economic-substance-regulations-05c9f19b` — DIFC — Business Economic Substance Regulations — https://www.difc.com/business/economic-substance-regulations
- `AE-difc-whats-on-insights-difc-data-protection-law-pioneers-6615d880` — DIFC — Whats On Insights DIFC Data Protection Law Pioneers — https://www.difc.com/whats-on/insights/difc-data-protection-law-pioneers
- `AE-difc-whats-on-news-difc-arbitration-law-consultation-684af25c` — DIFC — Whats On News DIFC Arbitration Law Consultation — https://www.difc.com/whats-on/news/difc-arbitration-law-consultation

### Top Candidate / Queue IDs
- `AE-difc-business-economic-substance-regulations-05c9f19b` — active — https://www.difc.com/business/economic-substance-regulations
- `AE-difc-business-services-document-hub-2020-0604-consent-guidance-b53de442` — candidate — https://www.difc.com/business/services/document-hub/2020-0604-consent-guidance
- `AE-difc-business-services-document-hub-difc-marketing-support-guide-4107283e` — candidate — https://www.difc.com/business/services/document-hub/difc-marketing-support-guide
- `AE-difc-business-services-document-hub-english-common-law-brochure-a90a7017` — candidate — https://www.difc.com/business/services/document-hub/english-common-law--brochure
- `AE-difc-business-services-document-hub-guidance-on-dual-license-c91f3c13` — candidate — https://www.difc.com/business/services/document-hub/guidance-on-dual-license
- `AE-difc-business-services-document-hub-security-breach-guidance-e0e1dc17` — candidate — https://www.difc.com/business/services/document-hub/security-breach-guidance
- `AE-difc-business-services-document-hub-security-breach-guidance-1-9b5b9369` — candidate — https://www.difc.com/business/services/document-hub/security-breach-guidance---1
- `AE-difc-whats-on-insights-difc-data-protection-law-pioneers-6615d880` — active — https://www.difc.com/whats-on/insights/difc-data-protection-law-pioneers
- `AE-difc-whats-on-insights-why-regulation-essential-fintech-success-99d7bb19` — held — https://www.difc.com/whats-on/insights/why-regulation-essential-fintech-success
- `AE-difc-business-difc-private-and-family-wealth-offering-af464f38` — candidate — https://www.difc.com/business/difc-private-and-family-wealth-offering
- `AE-dfsa-consultation-papers` — active — https://www.dfsa.ae/your-resources/publications/consultation-papers
- `AE-dfsa-rulebook-official` — active — https://www.dfsa.ae/your-resources/regulatory/laws-and-rules
- `AE-difc-consultation-papers` — candidate — https://www.difc.com/business/laws-and-regulations/consultation-papers/
- `AE-difc-data-protection` — candidate — https://www.difc.com/business/laws-and-regulations/data-protection/
- `AE-difc-laws-and-regulations` — activation_ready — https://www.difc.com/business/laws-and-regulations/
- `AE-difc-laws-regulations` — blocked — https://www.difc.com/business/laws-and-regulations/
- `AE-difc-legal-database` — activation_ready — https://www.difc.com/business/laws-and-regulations/legal-database/
- `AE-difc-legislation` — candidate — https://www.difc.ae/business/laws-regulations/legislation/
- `AE-dubai-financial-services-authority-dfsa` — active — https://www.dfsa.ae/rules-and-standards
- `AE-difc-data-protection-commissioner` — activation_ready — https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection
- `AE-difc-data-protection-supervision-enforcement` — already_active — https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/supervision-enforcement
- `AE-difc-data-protection-guidance` — already_active — https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/guidance
- `AE-difc-data-protection-regulation-10` — already_active — https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/regulation-10
- `AE-difc-data-protection-law-2020` — already_active — https://www.difc.com/business/laws-and-regulations/legal-database/difc-laws/data-protection-law-difc-law-no-5-2020
- `AE-difc-companies-law-2018` — already_active — https://www.difc.com/business/laws-and-regulations/legal-database/difc-laws/companies-law-difc-law-no-5-2018

### Known Risks / Missing Adapter Coverage
- DIFC legal/document hub candidates need item-level extraction; generic news/insights pages must be held if not compliance-relevant.

## ADGM/FSRA

- Scorecard starting active count: 12
- Strict registry heuristic active count: 12
- Enabled remediation count by heuristic: 0
- Target active count: 25
- Scorecard deficit: 13
- Universe candidates: 107
- Universe rejected: 18
- Top-250 queue entries: 13
- Work queue related entries: 19
- Mass activation related entries: 3

### Active Source IDs
- `AE-abu-dhabi-global-market-adgm` — Abu Dhabi Global Market (ADGM) — https://www.adgm.com/fsra
- `AE-adgm-fsra-financial-crime-prevention` — ADGM FSRA Financial and Cyber Crime Prevention — https://www.adgm.com/operating-in-adgm/financial-and-cyber-crime-prevention
- `AE-adgm-fsra-rulebooks` — ADGM FSRA Rules and Regulations — https://www.adgm.com/legal-framework/rules-and-regulations
- `AE-adgm-fsra-consultations` — ADGM Public Consultations — https://www.adgm.com/legal-framework/public-consultations
- `AE-adgm-fsra-guidance-policy` — ADGM FSRA Guidance and Policy Statements — https://www.adgm.com/legal-framework/guidance-and-policy-statements
- `AE-adgm-fsra-waivers` — ADGM FSRA Waivers and Modifications Register — https://www.adgm.com/financial-services-regulatory-authority/waivers-and-modifications
- `AE-adgm-ra-circulars` — ADGM Registration Authority Circulars — https://www.adgm.com/registration-authority/circulars
- `AE-adgm-listing-rules` — ADGM FSRA Listing Authority Rules and Guidance — https://www.adgm.com/financial-services-regulatory-authority/listing-authority/rules-and-guidance
- `AE-adgm-dp-guidance` — ADGM Data Protection Guidance — https://www.adgm.com/operating-in-adgm/office-of-data-protection/guidance
- `AE-adgm-fsra-enforcement` — ADGM FSRA Enforcement — https://www.adgm.com/fsra/enforcement
- `AE-adgm-fsra-supervision-circulars` — ADGM FSRA Supervision Circulars — https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities/supervision/circulars
- `AE-adgm-data-protection-regulations-2021-pdf` — ADGM Data Protection Regulations 2021 — Official PDF — https://www.adgm.com/documents/office-of-data-protection/resources/adgm-data-protection-regulations-2021-updated.pdf

### Top Candidate / Queue IDs
- `AE-adgm-adgm-courts-english-common-law-4fef1515` — held — https://www.adgm.com/adgm-courts/english-common-law
- `AE-adgm-adgm-courts-legislation-and-procedures-66abfd89` — candidate — https://www.adgm.com/adgm-courts/legislation-and-procedures
- `AE-adgm-legal-framework-abu-dhabi-legislation-c796b669` — candidate — https://www.adgm.com/legal-framework/abu-dhabi-legislation
- `AE-adgm-registration-authority-lpa-risk-report-de50d051` — held — https://www.adgm.com/registration-authority/lpa-risk-report
- `AE-adgm-spotlight-adfw-market-report-2025-ecf93a3e` — candidate — https://www.adgm.com/spotlight/adfw-market-report-2025
- `AE-adgm-media-announcements-adgm-amends-founding-law-64b8b408` — held — https://www.adgm.com/media/announcements/adgm-amends-founding-law
- `AE-adgm-operating-in-adgm-monitoring-and-enforcement-bf47a626` — held — https://www.adgm.com/operating-in-adgm/monitoring-and-enforcement
- `AE-adgm-operating-in-adgm-tax-services-5d62f306` — held — https://www.adgm.com/operating-in-adgm/tax-services
- `AE-adgm-registration-authority-public-notices-fc53df30` — candidate — https://www.adgm.com/registration-authority/public-notices
- `AE-adgm-business-areas-capital-markets-3ce15bcf` — held — https://www.adgm.com/business-areas/capital-markets
- `AE-abu-dhabi-global-market-adgm` — candidate — https://www.adgm.com/fsra
- `AE-adgm-data-protection` — candidate — https://www.adgm.com/operating-in-adgm/office-of-data-protection
- `AE-adgm-fsra-consultations` — activation_ready — https://www.adgm.com/legal-framework/public-consultations
- `AE-adgm-fsra-enforcement` — activation_ready — https://www.adgm.com/fsra/enforcement
- `AE-adgm-fsra-financial-crime-prevention` — activation_ready — https://www.adgm.com/operating-in-adgm/financial-and-cyber-crime-prevention
- `AE-adgm-fsra-guidance-policy` — activation_ready — https://www.adgm.com/legal-framework/guidance-and-policy-statements
- `AE-adgm-fsra-homepage` — blocked — https://www.adgm.com/fsra
- `AE-adgm-fsra-notices` — remediation — https://www.adgm.com/fsra/notices
- `AE-adgm-fsra-public-register` — remediation — https://www.adgm.com/public-registers
- `AE-adgm-fsra-rulebooks` — activation_ready — https://www.adgm.com/legal-framework/rules-and-regulations
- `AE-adgm-fsra-waivers` — already_active — https://www.adgm.com/financial-services-regulatory-authority/waivers-and-modifications
- `AE-adgm-ra-circulars` — already_active — https://www.adgm.com/registration-authority/circulars
- `AE-adgm-listing-rules` — already_active — https://www.adgm.com/financial-services-regulatory-authority/listing-authority/rules-and-guidance
- `AE-adgm-dp-guidance` — already_active — https://www.adgm.com/operating-in-adgm/office-of-data-protection/guidance

### Known Risks / Missing Adapter Coverage
- ADGM web components and listing pages have prior quality/drop/hash-drift holds; selectors need source-specific testing.

## VARA

- Scorecard starting active count: 9
- Strict registry heuristic active count: 9
- Enabled remediation count by heuristic: 0
- Target active count: 25
- Scorecard deficit: 16
- Universe candidates: 31
- Universe rejected: 3
- Top-250 queue entries: 7
- Work queue related entries: 11
- Mass activation related entries: 1

### Active Source IDs
- `AE-dubai-virtual-assets-regulatory-authority-vara` — Dubai Virtual Assets Regulatory Authority (VARA) — https://www.vara.ae/
- `AE-vara-enforcement` — VARA Enforcement Notices — https://www.vara.ae/en/enforcement/
- `AE-vara-rulebook-updates` — VARA Rulebook Revision Updates — https://rulebooks.vara.ae/view-revision-updates?f_days=onchanged%3D-30+day
- `AE-vara-compliance-risk-rulebook-pdf` — VARA Compliance and Risk Management Rulebook PDF — https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_123_VER20250519.pdf
- `AE-vara-technology-information-rulebook-pdf` — VARA Technology and Information Rulebook PDF — https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_169_VER20250519.pdf
- `AE-vara-va-issuance-rulebook-pdf` — VARA Virtual Asset Issuance Rulebook PDF — https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_293_VER20250519.pdf
- `AE-vara-broker-dealer-rulebook-pdf` — VARA Broker-Dealer Services Rulebook PDF — https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_226_VER20250519.pdf
- `AE-vara-lending-borrowing-rulebook-pdf` — VARA Lending and Borrowing Services Rulebook PDF — https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_279_VER20250519.pdf
- `AE-vara-va-regulations-2023-pdf` — VARA Virtual Assets and Related Activities Regulations 2023 PDF — https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_18_VER992_2.pdf

### Top Candidate / Queue IDs
- `AE-vara-en-notice-regarding-endorsements-5e60d62d` — candidate — https://www.vara.ae/en/notice-regarding-endorsements
- `AE-vara-en-regulations-regulatory-notices-e922bca2` — held — https://www.vara.ae/en/regulations/regulatory-notices
- `AE-vara-activity-rulebooks-hub` — candidate — https://rulebooks.vara.ae/
- `AE-vara-aml-cft-rulebook` — candidate — https://www.vara.ae/en/regulatory-framework/aml-cft-rulebook
- `AE-vara-company-rulebook` — candidate — https://www.vara.ae/en/regulatory-framework/company-rulebook
- `AE-vara-rulebooks-overview` — candidate — https://www.vara.ae/en/regulatory-framework/rulebooks
- `AE-vara-guidance` — candidate — https://www.vara.ae/en/regulatory-guidance
- `AE-dubai-virtual-assets-regulatory-authority-vara` — candidate — https://www.vara.ae/
- `AE-vara-enforcement` — remediation — https://www.vara.ae/en/enforcement/
- `AE-vara-homepage` — remediation — https://www.vara.ae/
- `AE-vara-news` — candidate — https://www.vara.ae/en/news/
- `AE-vara-public-register` — remediation — https://www.vara.ae/en/public-register/
- `AE-vara-regulatory-framework` — remediation — https://www.vara.ae/en/regulatory-framework/
- `AE-vara-rulebook` — candidate — https://www.vara.ae/en/regulatory-framework/
- `AE-vara-rulebook-updates` — already_active — https://rulebooks.vara.ae/view-revision-updates?f_days=onchanged%3D-30+day
- `AE-vara-compliance-risk-rulebook-pdf` — already_active — https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_123_VER20250519.pdf
- `AE-vara-technology-information-rulebook-pdf` — already_active — https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_169_VER20250519.pdf
- `AE-vara-va-issuance-rulebook-pdf` — already_active — https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_293_VER20250519.pdf
- `AE-vara-broker-dealer-rulebook-pdf` — already_active — https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_226_VER20250519.pdf
- `AE-vara-lending-borrowing-rulebook-pdf` — already_active — https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_279_VER20250519.pdf
- `AE-vara-va-regulations-2023-pdf` — already_active — https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_18_VER992_2.pdf

### Known Risks / Missing Adapter Coverage
- Existing VARA active set is direct-PDF heavy; public depth may be limited unless official notices/admin-order/listing pages pass.

## Ministry of Economy / DNFBP AML

- Scorecard starting active count: 7
- Strict registry heuristic active count: 8
- Enabled remediation count by heuristic: 0
- Target active count: 25
- Scorecard deficit: 18
- Universe candidates: 35
- Universe rejected: 18
- Top-250 queue entries: 20
- Work queue related entries: 9
- Mass activation related entries: 0

### Active Source IDs
- `AE-uae-ministry-of-economy` — UAE Ministry of Economy — https://www.moet.gov.ae/en/
- `AE-moet-aml-170b7988` — Ministry of Economy — AML — https://www.moet.gov.ae/aml
- `AE-moet-auditing-accounts-legislations-84d91bc4` — Ministry of Economy — Auditing Accounts Legislations — https://www.moet.gov.ae/auditing-accounts-legislations
- `AE-moet-economic-substance-regulations-a5b9825b` — Ministry of Economy — Economic Substance Regulations — https://www.moet.gov.ae/economic-substance-regulations
- `AE-moet-registering-companies-in-goaml-c83375da` — Ministry of Economy — Registering Companies In goAML — https://www.moet.gov.ae/registering-companies-in-goaml
- `AE-moet-regulation-of-business-fd17959e` — Ministry of Economy — Regulation Of Business — https://www.moet.gov.ae/regulation-of-business
- `AE-moet-regulation-of-competition-ba53cc4c` — Ministry of Economy — Regulation Of Competition — https://www.moet.gov.ae/regulation-of-competition
- `AE-moet-targeted-financial-sanctions-586d6f96` — Ministry of Economy — Targeted Financial Sanctions — https://www.moet.gov.ae/targeted-financial-sanctions

### Top Candidate / Queue IDs
- `AE-moet-auditing-accounts-legislations-84d91bc4` — active — https://www.moet.gov.ae/auditing-accounts-legislations
- `AE-moet-commercial-agency-and-auditors-legislations-c45fd9b6` — candidate — https://www.moet.gov.ae/commercial-agency-and-auditors-legislations
- `AE-moet-commercial-transaction-legislations-3049acbc` — candidate — https://www.moet.gov.ae/commercial-transaction-legislations
- `AE-moet-companies-legislations-58e47c0d` — candidate — https://www.moet.gov.ae/companies-legislations
- `AE-moet-consumer-protection-legislations-df9cdeb7` — held_duplicate — https://www.moet.gov.ae/consumer-protection-legislations
- `AE-moet-cooperative-associations-and-strategic-stock-of-food-commodities-legislations-ce0ef43e` — candidate — https://www.moet.gov.ae/cooperative-associations-and-strategic-stock-of-food-commodities-legislations
- `AE-moet-economic-substance-regulations-a5b9825b` — active — https://www.moet.gov.ae/economic-substance-regulations
- `AE-moet-financial-crimes-legislations-4383d1a8` — candidate — https://www.moet.gov.ae/financial-crimes-legislations
- `AE-moet-intellectual-property-legislations-1292dcd7` — candidate — https://www.moet.gov.ae/intellectual-property-legislations
- `AE-moet-laws-3a6e33da` — candidate — https://www.moet.gov.ae/laws
- `AE-moec-aml` — blocked — https://www.moec.gov.ae/en/anti-money-laundering
- `AE-uae-ministry-of-economy` — candidate — https://www.moet.gov.ae/en/
- `AE-moet-aml-170b7988` — active — https://www.moet.gov.ae/aml
- `AE-moet-registering-companies-in-goaml-c83375da` — active — https://www.moet.gov.ae/registering-companies-in-goaml
- `AE-moet-regulation-of-business-fd17959e` — active — https://www.moet.gov.ae/regulation-of-business
- `AE-moet-regulation-of-competition-ba53cc4c` — active — https://www.moet.gov.ae/regulation-of-competition
- `AE-moet-targeted-financial-sanctions-586d6f96` — active — https://www.moet.gov.ae/targeted-financial-sanctions
- `AE-moet-innovation-caf50f99` — candidate — https://www.moet.gov.ae/innovation
- `AE-moet-econsultation-652b9b9e` — candidate — https://www.moet.gov.ae/econsultation
- `AE-moet-publications1-f2b6ce37` — candidate — https://www.moet.gov.ae/publications1
- `AE-moet-annual-reports-5b37fb52` — candidate — https://www.moet.gov.ae/annual-reports
- `AE-moet-economic-report-06000ef9` — candidate — https://www.moet.gov.ae/economic-report
- `AE-moet-open-data-policy-9720ce8e` — candidate — https://www.moet.gov.ae/open-data-policy
- `AE-moet-our-publications-5ffd7bfd` — candidate — https://www.moet.gov.ae/our-publications
- `AE-moet-governance-policy-0d32d693` — candidate — https://www.moet.gov.ae/governance-policy

### Known Risks / Missing Adapter Coverage
- Family needs source-specific extraction and duplicate filtering before any new active count is safe.

## SCA

- Scorecard starting active count: 5
- Strict registry heuristic active count: 6
- Enabled remediation count by heuristic: 0
- Target active count: 25
- Scorecard deficit: 20
- Universe candidates: 15
- Universe rejected: 0
- Top-250 queue entries: 3
- Work queue related entries: 12
- Mass activation related entries: 3

### Active Source IDs
- `AE-uae-ministry-of-finance` — UAE Ministry of Finance — https://mof.gov.ae/
- `AE-sca-circulars-rules-procedures` — SCA Circulars, Rules and Procedures — https://www.sca.gov.ae/en/regulations/circulars-rules-and-procedures
- `AE-sca-regulations-listing` — SCA Regulations Listing — https://www.sca.gov.ae/en/regulations/regulations-listing
- `AE-sca-fatca-crs` — SCA FATCA and CRS Guidance — https://www.sca.gov.ae/en/regulations/automatic-exchange-of-information-fatca-and-crs
- `AE-sca-corporate-governance` — SCA Corporate Governance Regulations — https://www.sca.gov.ae/en/regulations/corporate-governance
- `AE-sca-aml-cft` — UAE SCA Anti-Money Laundering and Terrorist Financing — https://www.sca.gov.ae/en/regulations/anti-money-laundering-and-terrorist-financing

### Top Candidate / Queue IDs
- `AE-sca-laws` — candidate — https://www.sca.gov.ae/en/legislation/laws.aspx
- `AE-sca-decisions` — candidate — https://www.sca.gov.ae/en/legislation/sca-decisions.aspx
- `AE-sca-regulations-amendments` — candidate — https://www.sca.gov.ae/en/regulations/regulations-listing/amendments
- `AE-sca-aml-cft` — activation_ready — https://www.sca.gov.ae/en/regulations/anti-money-laundering-and-terrorist-financing
- `AE-sca-circulars` — remediation — https://www.sca.gov.ae/en/regulations/circulars-rules-and-procedures
- `AE-sca-homepage` — remediation — https://www.sca.gov.ae/
- `AE-sca-latest-regulations` — remediation — https://www.sca.gov.ae/en/regulations/regulations
- `AE-sca-legislation` — blocked — https://www.sca.gov.ae/en/legislation.aspx
- `AE-sca-news` — remediation — https://www.sca.gov.ae/en/media-center/news.aspx
- `AE-sca-regulations` — remediation — https://www.sca.gov.ae/en/regulations/regulations
- `AE-sca-regulations-listing` — activation_ready — https://www.sca.gov.ae/en/regulations/regulations-listing
- `AE-sca-circulars-rules-procedures` — already_active — https://www.sca.gov.ae/en/regulations/circulars-rules-and-procedures
- `AE-sca-fatca-crs` — already_active — https://www.sca.gov.ae/en/regulations/automatic-exchange-of-information-fatca-and-crs
- `AE-sca-corporate-governance` — already_active — https://www.sca.gov.ae/en/regulations/corporate-governance
- `AE-sca-market-rules` — candidate — https://www.sca.gov.ae/en/regulations/market-rules-approved-by-sca
- `AE-sca-violations` — candidate — https://www.sca.gov.ae/en/open-data/violations-and-violators

### Known Risks / Missing Adapter Coverage
- SCA pages may contain duplicate Arabic/English or pseudo-link rows; duplicate and shallow detection must stay strict.

## UAE FIU

- Scorecard starting active count: 4
- Strict registry heuristic active count: 4
- Enabled remediation count by heuristic: 1
- Target active count: 25
- Scorecard deficit: 21
- Universe candidates: 16
- Universe rejected: 0
- Top-250 queue entries: 1
- Work queue related entries: 12
- Mass activation related entries: 2

### Active Source IDs
- `AE-uaefiu-circulars` — UAE FIU Circulars and Notices — https://www.uaefiu.gov.ae/en/Publications/
- `AE-uaefiu-typology-reports` — UAE FIU Trends and Typology Reports — https://uaefiu.gov.ae/en/more/knowledge-centre/publications/trends-typology-reports/
- `AE-uaefiu-aml-cft-laws` — UAE FIU AML/CFT Laws and Related Decisions — https://uaefiu.gov.ae/en/more/knowledge-centre/aml-cft-laws-related-decisions/
- `AE-uaefiu-publications-hub` — UAE FIU Publications Hub — https://uaefiu.gov.ae/en/more/knowledge-centre/publications/

### Remediation Source IDs
- `AE-uae-financial-intelligence-unit-uaefiu` — UAE Financial Intelligence Unit (UAEFIU) — https://www.uaefiu.gov.ae/

### Top Candidate / Queue IDs
- `AE-uaefiu-nra-2024` — candidate — https://uaefiu.gov.ae/en/more/knowledge-centre/publications/national-risk-assessment-report-2024
- `AE-eocn-homepage` — blocked — https://www.eocn.gov.ae/
- `AE-uae-financial-intelligence-unit-uaefiu` — remediation — https://www.uaefiu.gov.ae/
- `AE-uaefiu-awareness` — candidate — https://www.uaefiu.gov.ae/en/Awareness/
- `AE-uaefiu-circulars` — candidate — https://www.uaefiu.gov.ae/en/Publications/
- `AE-uaefiu-goaml-public` — blocked — https://www.uaefiu.gov.ae/en/goAML/
- `AE-uaefiu-guidance` — candidate — https://www.uaefiu.gov.ae/en/Publications/
- `AE-uaefiu-homepage` — candidate — https://www.uaefiu.gov.ae/
- `AE-uaefiu-laws-regulations` — blocked — https://www.uaefiu.gov.ae/en/Laws-Regulations/
- `AE-uaefiu-publications` — blocked — https://www.uaefiu.gov.ae/en/Publications/
- `AE-uaefiu-typology-reports` — activation_ready — https://uaefiu.gov.ae/en/more/knowledge-centre/publications/trends-typology-reports/
- `AE-uaefiu-aml-cft-laws` — already_active — https://uaefiu.gov.ae/en/more/knowledge-centre/aml-cft-laws-related-decisions
- `AE-uaefiu-publications-hub` — already_active — https://uaefiu.gov.ae/en/more/knowledge-centre/publications
- `AE-eocn-laws-regulations-en` — already_active — https://www.eocn.gov.ae/en-us/laws-regulations-listing
- `AE-eocn-news-en` — already_active — https://www.eocn.gov.ae/en-us/news
- `AE-uaefiu-annual-reports` — candidate — https://uaefiu.gov.ae/en/more/knowledge-centre/publications/annual-report
- `AE-uaefiu-press-releases` — candidate — https://uaefiu.gov.ae/en/more/media/press-releases

### Known Risks / Missing Adapter Coverage
- UAE FIU homepage remains remediation because it extracts as a navigation/search/language shell; goAML private portal is out of scope.

## EOCN / sanctions / TFS

- Scorecard starting active count: 3
- Strict registry heuristic active count: 5
- Enabled remediation count by heuristic: 0
- Target active count: 25
- Scorecard deficit: 22
- Universe candidates: 20
- Universe rejected: 18
- Top-250 queue entries: 4
- Work queue related entries: 16
- Mass activation related entries: 7

### Active Source IDs
- `AE-dfsa-financial-crime-mlro-letters` — DFSA Financial Crime Prevention Notices and MLRO Letters — https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters
- `AE-dfsa-aml-rulebook-module` — DFSA AML Rulebook Module — https://dfsaen.thomsonreuters.com/rulebook/anti-money-laundering-counter-terrorist-financing-and-sanctions-module-aml-ver3004-26
- `AE-eocn-laws-regulations-en` — EOCN AML/CFT Laws and Regulations — https://www.eocn.gov.ae/en-us/laws-regulations-listing
- `AE-eocn-news-en` — EOCN News and Sanctions Updates — https://www.eocn.gov.ae/en-us/news
- `AE-moet-targeted-financial-sanctions-586d6f96` — Ministry of Economy — Targeted Financial Sanctions — https://www.moet.gov.ae/targeted-financial-sanctions

### Top Candidate / Queue IDs
- `AE-uaeiec-en-us-laws-regulations-listing-00a71863` — candidate — https://www.uaeiec.gov.ae/en-us/laws-regulations-listing
- `AE-uaeiec-en-us-laws-regulations-listing-federal-decree-by-law-no-10-of-2025-regarding-anti-money-laundering-and-combating-eb6b0d05` — candidate — https://www.uaeiec.gov.ae/en-us/laws-regulations-listing/federal-decree-by-law-no-10-of-2025-regarding-anti-money-laundering-and-combating-the-financing-of-terrorism-and-proliferation-financing
- `AE-uaeiec-en-us-laws-regulations-listing-134-2025-0724b13a` — candidate — https://www.uaeiec.gov.ae/en-us/laws-regulations-listing/قرار-مجلس-الوزراء-رقم-134-لسنة-2025-في-شأن-اللائحة-التنفيذية-للمرسوم-بقانون-اتحادي-رقم-10-لسنة-2025-ف
- `AE-uaeiec-en-us-news-the-namlcftc-approves-the-public-edition-of-the-uae-proliferation-financing-national-risk-assessment-r-cf32d3e9` — candidate — https://www.uaeiec.gov.ae/en-us/news/the-namlcftc-approves-the-public-edition-of-the-uae-proliferation-financing-national-risk-assessment-report
- `AE-adgm-fsra-financial-crime-prevention` — activation_ready — https://www.adgm.com/operating-in-adgm/financial-and-cyber-crime-prevention
- `AE-dfsa-aml-ctf-sanctions` — candidate — https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance
- `AE-dfsa-aml-mlro-notices` — baseline_pending — https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters
- `AE-eocn-homepage` — blocked — https://www.eocn.gov.ae/
- `AE-uaefiu-awareness` — candidate — https://www.uaefiu.gov.ae/en/Awareness/
- `AE-uaefiu-circulars` — candidate — https://www.uaefiu.gov.ae/en/Publications/
- `AE-uaefiu-goaml-public` — blocked — https://www.uaefiu.gov.ae/en/goAML/
- `AE-uaefiu-guidance` — candidate — https://www.uaefiu.gov.ae/en/Publications/
- `AE-uaefiu-homepage` — candidate — https://www.uaefiu.gov.ae/
- `AE-uaefiu-laws-regulations` — blocked — https://www.uaefiu.gov.ae/en/Laws-Regulations/
- `AE-uaeiec-en-us-faqs-listing-51f14556` — candidate — https://www.uaeiec.gov.ae/en-us/faqs-listing
- `AE-uaeiec-en-us-our-partners-listing-af2bc35f` — candidate — https://www.uaeiec.gov.ae/en-us/our-partners-listing
- `AE-uaeiec-en-us-our-industries-listing-2632a9f6` — candidate — https://www.uaeiec.gov.ae/en-us/our-Industries-listing
- `AE-uaeiec-en-us-our-industries-listing-66be4793` — candidate — https://www.uaeiec.gov.ae/en-us/our-industries-listing
- `AE-uaeiec-our-industries-listing-armor-companies-9c6d588d` — candidate — https://www.uaeiec.gov.ae/our-industries-listing/armor-companies
- `AE-uaeiec-our-industries-listing-defense-companies-14e9ecab` — candidate — https://www.uaeiec.gov.ae/our-industries-listing/defense-companies
- `AE-uaeiec-our-industries-listing-aerospace-companies-4fab0852` — candidate — https://www.uaeiec.gov.ae/our-industries-listing/aerospace-companies
- `AE-uaeiec-en-us-news-conclusion-of-the-42nd-general-meeting-of-the-menafatf-group-in-rebat-75364520` — candidate — https://www.uaeiec.gov.ae/en-us/news/conclusion-of-the-42nd-general-meeting-of-the-menafatf-group-in-rebat

### Known Risks / Missing Adapter Coverage
- Sanctions/TFS list pages may have high noise; designation churn must be treated as source-health/noise risk, not automatic regulatory alert.

## FTA / Tax

- Scorecard starting active count: 0
- Strict registry heuristic active count: 1
- Enabled remediation count by heuristic: 0
- Target active count: 25
- Scorecard deficit: 25
- Universe candidates: 77
- Universe rejected: 18
- Top-250 queue entries: 70
- Work queue related entries: 4
- Mass activation related entries: 0

### Active Source IDs
- `AE-uae-ministry-of-finance` — UAE Ministry of Finance — https://mof.gov.ae/

### Top Candidate / Queue IDs
- `AE-tax-ar-legislation-archive-aspx-bac58b7d` — candidate — https://tax.gov.ae/ar/Legislation.archive.aspx
- `AE-tax-ar-legislation-aspx-acca1c80` — candidate — https://tax.gov.ae/ar/Legislation.aspx
- `AE-tax-en-legislation-aspx-310662a3` — candidate — https://tax.gov.ae/en/Legislation.aspx
- `AE-tax-en-legislation-aspx-98313c15` — candidate — https://tax.gov.ae/en/legislation.aspx
- `AE-eservices-4d5d7acf` — candidate — https://eservices.tax.gov.ae/
- `AE-eservices-en-us-a00af984` — candidate — https://eservices.tax.gov.ae/en-us
- `AE-tax-ar-d6d033c1` — candidate — https://tax.gov.ae/ar
- `AE-tax-ar-about-fta-aspx-e6e7428f` — candidate — https://tax.gov.ae/ar/about.fta.aspx
- `AE-tax-ar-about-fta-labaih-aspx-e329e015` — candidate — https://tax.gov.ae/ar/about.fta/labaih.aspx
- `AE-tax-ar-about-fta-zgb-aspx-a4f8e8de` — candidate — https://tax.gov.ae/ar/about.fta/zgb.aspx
- `AE-federal-tax-authority-homepage` — candidate — https://tax.gov.ae/
- `AE-fta-corporate-tax-guides` — candidate — https://tax.gov.ae/en/taxes/corporate.tax/corporate.tax.guides.references.aspx
- `AE-fta-vat-public-clarifications` — candidate — https://tax.gov.ae/en/taxes/vat/vat-public-clarifications.aspx
- `AE-mof-homepage` — blocked — https://mof.gov.ae/
- `AE-fta-vat-guides` — candidate — https://tax.gov.ae/en/taxes/vat/guides.references.aspx
- `AE-fta-country-by-country` — candidate — https://tax.gov.ae/en/taxes/country-by-country-reporting
- `AE-fta-excise-tax` — candidate — https://tax.gov.ae/en/taxes/excise-tax
- `AE-fta-news` — candidate — https://tax.gov.ae/en/media-center/news
- `AE-tax-en-ac9788cc` — candidate — https://tax.gov.ae/en

### Known Risks / Missing Adapter Coverage
- Prior FTA rows were demoted because no-save returned title-only/nav-shell extraction. Needs item-level FTA listing/document adapter before activation.

## Cross-Family Held Candidates From Previous Bulk Sprint

## 5. Sources Held And Why

- `AE-dfsa-ar-what-we-do-enforcement-f0487f7a` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-dfsa-news-notice-amendment-dfsa-forms-adabf2e1` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-dfsa-news-reminder-rulebook-amendments-e6e4718a` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-dfsa-what-we-do-enforcement-1a837c50` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-adgm-adgm-courts-english-common-law-4fef1515` — QUALITY_DROP,changed_on_dry_run,monitor_hash_mismatch
- `AE-adgm-business-areas-capital-markets-3ce15bcf` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-adgm-media-announcements-adgm-amends-founding-law-64b8b408` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-adgm-operating-in-adgm-it-risk-management-dd67c9de` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-adgm-operating-in-adgm-monitoring-and-enforcement-bf47a626` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-adgm-operating-in-adgm-tax-services-5d62f306` — QUALITY_DROP,changed_on_dry_run,monitor_hash_mismatch
- `AE-adgm-registration-authority-lpa-risk-report-de50d051` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-difc-whats-on-insights-why-regulation-essential-fintech-success-99d7bb19` — changed_on_dry_run,monitor_hash_mismatch
- `AE-vara-en-regulations-regulatory-notices-e922bca2` — QUALITY_DROP,changed_on_dry_run,monitor_hash_mismatch
- `AE-added-en-grow-regulations-63dfab49` — changed_on_dry_run,monitor_hash_mismatch
- `AE-dfsa-aml-ctf-sanctions` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-dfsa-guidance-notes` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-dfsa-ar-data-protection-00f21b77` — QUALITY_DROP,changed_on_dry_run,monitor_hash_mismatch
- `AE-dfsa-what-we-do-supervision-5fba6a56` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-dfsa-news-dfsa-signs-mou-amlscu-uae-d443a85d` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-dfsa-ar-what-we-do-about-supervision-adddadb1` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-dfsa-news-dfsa-host-cyber-risk-forum-08a4afd4` — NAV_SHELL_ONLY,changed_on_dry_run,monitor_hash_mismatch
- `AE-moet-consumer-protection-legislations-df9cdeb7` — duplicate latest monitor hash with `AE-moet-auditing-accounts-legislations-84d91bc4`

## Implementation Path

1. Use current universe/top-250/work queue to build a weak-family no-save marathon list.
2. Add missing adapters first for FTA/SCA/FIU/EOCN where prior failures show generic extraction is inadequate.
3. Run no-save tests and save evidence only for strong passes.
4. Activate only after proof, 2/2 baseline, mass-monitor `MONITOR_OK`, no drift or approved safe diff, and review gates.
5. If a family cannot reach 25, document official-source exhaustion and exact blocker instead of inflating active counts.
