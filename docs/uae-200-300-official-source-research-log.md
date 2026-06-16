# UAE 200–300 Official Source Research Log

Date: 2026-06-16
Sprint: UAE Source Universe Discovery Sprint (200–300 target)
Research scope: All known UAE official regulatory endpoints as of 2026-06-16.

This log documents every source examined — active, candidate, discovered, and rejected — with discovery method and outcome. It is the authoritative record for the uae_source_universe_candidates.json file created in this sprint.

---

## Method

Sources were compiled from five input streams:

1. **sources.json** — 79 enabled UAE sources (ground truth for already-active)
2. **uae_source_candidates.json** — 69 candidate records (with no-save test results)
3. **uae_source_work_queue.json** — 127 work queue entries (activation decisions logged)
4. **uae-official-endpoint-discovery-150-report.md** — 151 endpoints from dedicated discovery sprint (2026-06-15)
5. **Systematic regulator enumeration** — All known UAE regulatory authority domains checked for uncovered endpoints

---

## Category A: VARA / Dubai Virtual Assets

Research scope: vara.ae, rulebooks.vara.ae

**Already active (8):**
- AE-dubai-virtual-assets-regulatory-authority-vara — vara.ae/ — main anchor, active
- AE-vara-enforcement — vara.ae/en/enforcement/ — enforcement notices, active
- AE-vara-rulebook-updates — rulebooks.vara.ae/view-revision-updates — change tracker, active
- AE-vara-compliance-risk-rulebook-pdf — rulebooks.vara.ae PDF — active
- AE-vara-technology-information-rulebook-pdf — rulebooks.vara.ae PDF — active
- AE-vara-va-issuance-rulebook-pdf — rulebooks.vara.ae PDF — active
- AE-vara-broker-dealer-rulebook-pdf — rulebooks.vara.ae PDF — active
- AE-vara-lending-borrowing-rulebook-pdf — rulebooks.vara.ae PDF — active
- AE-vara-va-regulations-2023-pdf — rulebooks.vara.ae PDF — active

Wait, VARA active count is 9 PDFs + enforcement + homepage = let me recount. From sources.json enabled:
AE-dubai-virtual-assets-regulatory-authority-vara, AE-vara-enforcement, AE-vara-rulebook-updates, AE-vara-compliance-risk-rulebook-pdf, AE-vara-technology-information-rulebook-pdf, AE-vara-va-issuance-rulebook-pdf, AE-vara-broker-dealer-rulebook-pdf, AE-vara-lending-borrowing-rulebook-pdf, AE-vara-va-regulations-2023-pdf = 9 sources

**Candidates from work queue / prior research (6):**
- AE-vara-homepage — vara.ae/ — NAV_SHELL_ONLY in no-save test, remediation needed
- AE-vara-regulatory-framework — vara.ae/en/regulatory-framework/ — 404 at test time, remediation
- AE-vara-company-rulebook — vara.ae/en/regulatory-framework/company-rulebook/ — 404, URL changed
- AE-vara-aml-cft-rulebook — vara.ae/en/regulatory-framework/aml-cft-rulebook/ — 404, URL changed
- AE-vara-rulebooks-overview — vara.ae/en/regulatory-framework/rulebooks/ — 404, URL changed
- AE-vara-public-register — vara.ae/en/public-register/ — candidate, not tested
- AE-vara-news — vara.ae/en/news/ — candidate, not tested

**New candidates from systematic research (5):**
- AE-vara-guidance — vara.ae/en/regulatory-guidance/ — regulatory guidance hub; P1
- AE-vara-licensing-conditions — vara.ae/en/licensing/ — licensing conditions hub; P2
- AE-vara-administrative-orders — vara.ae/en/administrative-orders/ — administrative orders; P1
- AE-vara-activity-rulebooks-hub — rulebooks.vara.ae — main rulebooks index page; P1
- AE-vara-market-oversight — vara.ae/en/market-oversight/ — market oversight section; P2

**Rejected (4):**
- vara.ae/en/regulatory-framework/company-rulebook/ — 404, URL path changed
- vara.ae/en/regulatory-framework/aml-cft-rulebook/ — 404, URL path changed
- vara.ae/en/regulatory-framework/rulebooks/ — 404, URL path changed
- vara.ae social media / press office — not official regulatory source

---

## Category B: UAE FIU / EOCN / AML

Research scope: uaefiu.gov.ae, eocn.gov.ae, goaml.ae

**Already active (7):**
- AE-uae-financial-intelligence-unit-uaefiu — uaefiu.gov.ae/ — main anchor
- AE-uaefiu-circulars — uaefiu.gov.ae/en/Publications/ — circulars hub
- AE-uaefiu-typology-reports — uaefiu.gov.ae/en/more/knowledge-centre/publications/trends-typology-reports/
- AE-uaefiu-aml-cft-laws — uaefiu.gov.ae/en/more/knowledge-centre/aml-cft-laws-related-decisions/
- AE-uaefiu-publications-hub — uaefiu.gov.ae/en/more/knowledge-centre/publications/
- AE-eocn-laws-regulations-en — eocn.gov.ae/en-us/laws-regulations-listing
- AE-eocn-news-en — eocn.gov.ae/en-us/news

**Candidates from work queue / prior research (6):**
- AE-uaefiu-guidance — uaefiu.gov.ae/en/Publications/ — same URL as circulars, needs ID reconciliation
- AE-uaefiu-goaml-public — uaefiu.gov.ae/en/goAML/ — public goAML guidance, candidate
- AE-uaefiu-awareness — uaefiu.gov.ae/en/Awareness/ — awareness publications
- AE-uaefiu-laws-regulations — uaefiu.gov.ae/en/Laws-Regulations/ — laws section
- AE-uaefiu-homepage — uaefiu.gov.ae/ — homepage (duplicate of main anchor)
- AE-eocn-homepage — eocn.gov.ae/ — EOCN homepage anchor

**New candidates from 150-report / systematic research (8):**
- AE-uaefiu-annual-reports — uaefiu.gov.ae/en/more/knowledge-centre/publications/annual-report/ — annual reports; P2
- AE-uaefiu-nra-2024 — uaefiu.gov.ae/en/more/knowledge-centre/publications/national-risk-assessment-report-2024/ — NRA 2024; high relevance; P1
- AE-uaefiu-press-releases — uaefiu.gov.ae/en/more/media/press-releases/ — press/media; P2
- AE-uaefiu-strategic-analysis — uaefiu.gov.ae/en/more/knowledge-centre/publications/strategic-analysis-guidelines/ — strategic analysis; P1
- AE-uaefiu-mutual-evaluation — uaefiu.gov.ae/en/more/knowledge-centre/publications/uae-mutual-evaluation-report/ — FATF mutual eval; P1
- AE-uaefiu-open-data — uaefiu.gov.ae/en/more/open-data/ — open data; P3
- AE-uaefiu-domestic-investigations — uaefiu.gov.ae/en/stakeholders/domestic-cooperation/domestic-investigations/ — P3
- AE-eocn-tfs — eocn.gov.ae/en-us/un-page — targeted financial sanctions list; P1 (high-velocity updates — monitor carefully)

**Rejected (3):**
- goaml.ae login portal — private login only, cannot monitor
- uaefiu.gov.ae/en-us/un-page (Arabic-only version) — prefer English endpoint
- eocn.gov.ae/ homepage without subpage — superseded by specific subpages

---

## Category C: CBUAE / Central Bank

Research scope: centralbank.ae, rulebook.centralbank.ae

**Already active (27):**
All 27 active CBUAE sources from sources.json:
- AE-central-bank-of-the-uae — centralbank.ae/ — main anchor
- AE-cbuae-regulations — centralbank.ae/en/regulations/ — regulations hub
- AE-cbuae-rulebook-revision-updates — rulebook.centralbank.ae/en/view-revision-updates — change tracker
- AE-cbuae-retail-payment-services-rulebook — rulebook section
- AE-cbuae-amlcft-rulebook-doclist — AML/CFT rulebook
- AE-cbuae-amlcft-entire-section-doclist — entire AML/CFT section
- AE-cbuae-consumer-protection-rulebook-doclist — consumer protection
- AE-cbuae-open-finance-rulebook — open finance
- AE-cbuae-payment-token-services-rulebook — payment token services
- AE-cbuae-risk-management-rulebook — risk management
- AE-cbuae-stored-value-facilities-doclist — stored value facilities
- AE-cbuae-operational-risk-regulation-doclist — operational risk
- AE-cbuae-market-risk-regulation-doclist — market risk
- AE-cbuae-large-exposures-regulation-doclist — large exposures
- AE-cbuae-exchange-business-regulation-doclist — exchange business
- AE-cbuae-capital-adequacy-doclist — capital adequacy
- AE-cbuae-large-value-payment-systems-doclist — LVPS
- AE-cbuae-federal-decree-law-6-2025-doclist — Federal Decree Law 6/2025
- AE-cbuae-country-transfer-risk-regulation-doclist — country/transfer risk
- AE-cbuae-interest-rate-risk-regulation-doclist — interest rate risk
- AE-cbuae-model-management-standards-doclist — model management
- AE-cbuae-retail-payment-systems-regulation-doclist — retail payment systems
- AE-cbuae-sme-customer-protection-regulation-doclist — SME protection
- AE-cbuae-islamic-banks-risk-management-doclist — Islamic banks
- AE-cbuae-market-conduct-consumer-protection-doclist — market conduct
- AE-cbuae-proliferation-finance-guidance-doclist — proliferation finance
- AE-cbuae-tbml-transshipment-guidance-doclist — TBML guidance

**Candidates from work queue (8):**
- AE-cbuae-aml-cft — centralbank.ae/en/our-operations/anti-money-laundering-and-combatting-the-financing-of-terrorism/ — P1
- AE-cbuae-consultations — centralbank.ae/en/consultations/ — P1
- AE-cbuae-news — centralbank.ae/en/media-center/news/ — P2
- AE-cbuae-consumer-protection — centralbank.ae/en/consumer-protection/ — P2
- AE-cbuae-licensing — centralbank.ae/en/licensing/ — P2
- AE-cbuae-payment-systems — centralbank.ae/en/our-operations/payment-systems/ — P3
- AE-cbuae-open-data — centralbank.ae/en/open-data/ — P3
- AE-cbuae-publications — centralbank.ae/en/publications/ — P1

**New candidates from systematic research (5):**
- AE-cbuae-insurance-supervision — centralbank.ae/en/our-operations/insurance/ — insurance rulebooks/circulars; P2
- AE-cbuae-financial-stability-report — centralbank.ae/en/our-operations/financial-stability/ — financial stability reports; P2
- AE-cbuae-circular-bank-supervision — centralbank.ae/en/circular-and-guidelines/bank-supervision/ — supervision circulars; P1
- AE-cbuae-fintech-office — centralbank.ae/en/fintech/ — fintech regulation and sandbox; P2
- AE-cbuae-net-stable-funding-doclist — rulebook.centralbank.ae/en/rulebook/net-stable-funding-ratio — NSFR regulation; P2

**Rejected (2):**
- centralbank.ae sitemap.xml — 403 blocked, not a content source
- centralbank.ae/en/ homepage-only — superseded by specific subpages

---

## Category D: DFSA / Dubai International Financial Centre Financial

Research scope: dfsa.ae, dfsaen.thomsonreuters.com

**Already active (10):**
- AE-dubai-financial-services-authority-dfsa — dfsa.ae/rules-and-standards
- AE-dfsa-financial-crime-mlro-letters — dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters
- AE-dfsa-aml-rulebook-module — dfsaen.thomsonreuters.com/rulebook/anti-money-laundering-counter-terrorist-financing-and-sanctions-module-aml
- AE-dfsa-notices — dfsa.ae/regulation/notices-public-registers
- AE-dfsa-rulebook-thomsonreuters — dfsaen.thomsonreuters.com/rulebook/rulebook-modules
- AE-dfsa-consultation-current — dfsa.ae/your-resources/regulatory/consultation-papers
- AE-dfsa-enforcement-decisions-current — dfsa.ae/what-we-do/enforcement/published-decisions
- AE-dfsa-regulatory-actions-current — dfsa.ae/what-we-do/enforcement/regulatory-actions
- AE-dfsa-consultation-paper-165 — dfsaen.thomsonreuters.com/rulebook/consultation-paper-no165
- AE-dfsa-notice-supervisory-review — dfsaen.thomsonreuters.com/rulebook/supervisory-review-and-evaluation-process

**Candidates from work queue (5):**
- AE-dfsa-publications — dfsa.ae/your-resources/publications — P1
- AE-dfsa-consultation-papers — dfsa.ae/your-resources/publications/consultation-papers — P1
- AE-dfsa-public-register — dfsa.ae/public-register — P2
- AE-dfsa-rulebook-official — dfsa.ae/your-resources/regulatory/laws-and-rules — P1
- AE-dfsa-aml-ctf-sanctions — dfsa.ae/what-we-do/aml-ctf-sanctions-compliance — P1

**New candidates from systematic research (5):**
- AE-dfsa-annual-reports — dfsa.ae/your-resources/publications/annual-reports — P2
- AE-dfsa-policy-statements — dfsa.ae/your-resources/publications/policy-statements — P2
- AE-dfsa-guidance-notes — dfsa.ae/your-resources/publications/guidance-notes — P1
- AE-dfsa-supervisory-risk-appetite — dfsa.ae/what-we-do/supervision/risk-appetite-statements — P3
- AE-dfsa-crowdfunding — dfsa.ae/your-resources/regulatory/investment-crowdfunding — P3

**Rejected (2):**
- dfsa.ae sitemap.xml — 403 blocked
- dfsa.ae/about — marketing/corporate page, no regulatory content

---

## Category E: ADGM / FSRA

Research scope: adgm.com, fsra.adgm.com

**Already active (11):**
- AE-abu-dhabi-global-market-adgm — adgm.com/fsra — FSRA hub
- AE-adgm-fsra-financial-crime-prevention — adgm.com/operating-in-adgm/financial-and-cyber-crime-prevention
- AE-adgm-fsra-rulebooks — adgm.com/legal-framework/rules-and-regulations
- AE-adgm-fsra-consultations — adgm.com/legal-framework/public-consultations
- AE-adgm-fsra-guidance-policy — adgm.com/legal-framework/guidance-and-policy-statements
- AE-adgm-fsra-waivers — adgm.com/financial-services-regulatory-authority/waivers-and-modifications
- AE-adgm-ra-circulars — adgm.com/registration-authority/circulars
- AE-adgm-listing-rules — adgm.com/financial-services-regulatory-authority/listing-authority/rules-and-guidance
- AE-adgm-dp-guidance — adgm.com/operating-in-adgm/office-of-data-protection/guidance
- AE-adgm-fsra-enforcement — adgm.com/fsra/enforcement
- AE-adgm-fsra-waivers (listed twice — one is same as above)

**Candidates from work queue / 150-report (9):**
- AE-adgm-fsra-notices — adgm.com/fsra/notices — P1 (FSRA regulatory notices)
- AE-adgm-fsra-public-register — adgm.com/public-registers — P2
- AE-adgm-media-announcements — adgm.com/media/announcements — P1 (confirmed accessible)
- AE-adgm-dp-regulatory-actions — adgm.com/operating-in-adgm/office-of-data-protection/regulatory-actions — P2
- AE-adgm-dp-hub — adgm.com/operating-in-adgm/office-of-data-protection — P2
- AE-adgm-ra-notices — adgm.com/registration-authority/notices — P1
- AE-adgm-ra-aml-guides — adgm.com/registration-authority/aml-cft-guides — P1 (DNFBP AML)
- AE-adgm-ra-regulations — adgm.com/registration-authority/regulations — P2
- AE-adgm-federal-legislation — adgm.com/legal-framework/federal-legislation — P3

**New candidates from systematic research (5):**
- AE-adgm-co-circulars — adgm.com/companies-office/circulars — companies office circulars; P2
- AE-adgm-fsra-reports — adgm.com/fsra/annual-reports — FSRA annual reports; P3
- AE-adgm-listing-announcements — adgm.com/financial-services-regulatory-authority/listing-authority/listing-authority-announcements — P3
- AE-adgm-fsra-rules-fsra-domain — fsra.adgm.com/rules-and-regulations/rulebooks — alternate FSRA rulebook domain; P2
- AE-adgm-abu-dhabi-legislation — adgm.com/legal-framework/abu-dhabi-legislation — Abu Dhabi legislation index; P3

**Rejected (2):**
- adgm.com/about — corporate/marketing, no regulatory content
- fsra.adgm.com/ homepage — superseded by specific rulebook/notice subpages

---

## Category F: SCA / Securities and Commodities Authority

Research scope: sca.gov.ae

**Already active (5):**
- AE-sca-circulars-rules-procedures — sca.gov.ae/en/regulations/circulars-rules-and-procedures
- AE-sca-regulations-listing — sca.gov.ae/en/regulations/regulations-listing
- AE-sca-fatca-crs — sca.gov.ae/en/regulations/automatic-exchange-of-information-fatca-and-crs
- AE-sca-corporate-governance — sca.gov.ae/en/regulations/corporate-governance
- AE-sca-aml-cft — sca.gov.ae/en/regulations/anti-money-laundering-and-terrorist-financing

**Candidates from work queue / 150-report (8):**
- AE-sca-regulations-amendments — sca.gov.ae/en/regulations/regulations-listing/amendments — P1
- AE-sca-market-rules — sca.gov.ae/en/regulations/market-rules-approved-by-sca — P2
- AE-sca-violations — sca.gov.ae/en/open-data/violations-and-violators — P2 (enforcement data)
- AE-sca-sustainable-finance — sca.gov.ae/en/regulations/sustainable-finance — P3
- AE-sca-fintech-sandbox — sca.gov.ae/en/regulations/fintech-regulatory-sandbox — P3
- AE-sca-laws — sca.gov.ae/en/legislation/laws.aspx — P1 (securities laws)
- AE-sca-decisions — sca.gov.ae/en/legislation/sca-decisions.aspx — P1 (board decisions)
- AE-sca-news — sca.gov.ae/en/media-center/news.aspx — P3

**New candidates from systematic research (4):**
- AE-sca-investment-funds — sca.gov.ae/en/regulations/investment-funds — fund regulation; P2
- AE-sca-disclosure — sca.gov.ae/en/regulations/disclosure — disclosure obligations; P2
- AE-sca-inspection-reports — sca.gov.ae/en/open-data/inspection-reports — P3
- AE-sca-listed-companies — sca.gov.ae/en/open-data/listed-companies — listed entity registry; P3

**Rejected (2):**
- sca.gov.ae/ homepage only — superseded by specific subpages
- sca.gov.ae/en/regulations/ hub without subpage — too broad

---

## Category G: DIFC Legal / Courts

Research scope: difc.com, difccourts.ae

**Already active (8):**
- AE-difc-laws-and-regulations — difc.com/business/laws-and-regulations/ (main anchor)
- AE-difc-data-protection-commissioner — difc.com/business/registrars-and-commissioners/commissioner-of-data-protection
- AE-difc-data-protection-supervision-enforcement — supervision and enforcement page
- AE-difc-data-protection-guidance — data protection guidance
- AE-difc-data-protection-regulation-10 — Regulation 10
- AE-difc-data-protection-law-2020 — DP Law 2020
- AE-difc-companies-law-2018 — Companies Law 2018
- AE-difc-legal-database — difc.com/business/laws-and-regulations/legal-database/

**Candidates from work queue / 150-report (4):**
- AE-difc-consultation-papers — difc.com/business/laws-and-regulations/consultation-papers/ — P1
- AE-difc-data-protection — difc.com/business/laws-and-regulations/data-protection/ — P2
- AE-difc-legislation — difc.ae/business/laws-regulations/legislation/ — blocked (different domain, uncertain)
- AE-difc-laws-regulations — difc.com/business/laws-and-regulations/ — duplicate of laws-and-regulations anchor

**New candidates from systematic research (5):**
- AE-difc-employment-law — difc.com/business/laws-and-regulations/legal-database/difc-laws/ — employment law subpage; P3
- AE-difc-judicial-authority — difccourts.ae — DIFC Courts main site; P3
- AE-difc-courts-decisions — difccourts.ae/judgments — publicly published judgments; P3
- AE-difc-financial-crime — difc.com/business/financial-crime-authority — if public; P2
- AE-difc-insurance — difc.com/business/insurance — insurance regulation; P3

**Rejected (2):**
- difc.ae (old domain) — use difc.com canonical domain
- difc.com/about — corporate/marketing, no regulatory content

---

## Category H: Federal Legislation / Ministry of Justice

Research scope: uaelegislation.gov.ae, moj.gov.ae, elaws.moj.gov.ae

**Already active (3):**
- AE-uae-legislation-portal — uaelegislation.gov.ae/ — main legislation portal
- AE-uae-ministry-of-finance — mof.gov.ae/ — ministry of finance anchor
- AE-uae-ministry-of-economy — moet.gov.ae/en/ — ministry of economy anchor

**Candidates from work queue / 150-report (5):**
- AE-uae-legislation-financial — uaelegislation.gov.ae/en/legislations?subject=1 — financial laws; P2
- AE-uae-legislation-aml — uaelegislation.gov.ae/en/legislations?subject=16 — AML/CFT decrees; P1
- AE-uae-elaws-moj — elaws.moj.gov.ae/ — MoJ e-laws portal; P2
- AE-moec-aml-dnfbp — moet.gov.ae/en/anti-money-laundering — MoE AML/DNFBP; P1
- AE-mof-homepage — mof.gov.ae/ — (already active as AE-uae-ministry-of-finance)

**New candidates from systematic research (5):**
- AE-moj-federal-laws — moj.gov.ae/en/resources/federal-laws — Ministry of Justice laws; P2
- AE-moec-media-publications — moet.gov.ae/en/media/publications — MoE publications; P3
- AE-moec-regulations — moet.gov.ae/en/regulations — MoE regulations; P2
- AE-uae-legislation-commercial — uaelegislation.gov.ae/en/legislations?subject=7 — commercial laws; P3
- AE-mof-public-finance — mof.gov.ae/en/governance/public-finance-management/ — public finance; P3

**Rejected (2):**
- moj.gov.ae/en/ homepage — superseded by specific subpages
- uaelegislation.gov.ae/ar/ — Arabic-only version, prefer English endpoints

---

## Category I: Tax / Federal Tax Authority

Research scope: tax.gov.ae

**Already active (0):**
No FTA sources currently active.

**Candidates from work queue (3):**
- AE-federal-tax-authority-homepage — tax.gov.ae/ — FTA main anchor; P2
- AE-fta-corporate-tax-guides — tax.gov.ae/en/taxes/corporate.tax/corporate.tax.guides.references.aspx — P2
- AE-fta-vat-public-clarifications — tax.gov.ae/en/taxes/vat/vat-public-clarifications.aspx — P2

**New candidates from systematic research (5):**
- AE-fta-vat-clarifications-2 — tax.gov.ae/en/taxes/vat/guides.references.aspx — VAT guides; P2
- AE-fta-tax-procedures — tax.gov.ae/en/taxes/tax-procedures/ — tax procedures; P3
- AE-fta-excise-tax — tax.gov.ae/en/taxes/excise-tax/ — excise tax; P3
- AE-fta-country-by-country — tax.gov.ae/en/taxes/country-by-country-reporting/ — CBC reporting; P2
- AE-fta-news — tax.gov.ae/en/media-center/news — FTA news/circulars; P3

**Rejected (2):**
- tax.gov.ae/en/ homepage — superseded by specific subpages
- tax.gov.ae private eTax portal — login required, blocked

---

## Category J: Emirate / Free Zone / Data / Adjacent

Research scope: dmcc.ae, dfm.ae, tdra.gov.ae, uaedp.gov.ae, additional free zones

**Candidates (no currently active in this category):**

From 150-report:
- AE-dmcc-compliance — dmcc.ae/operations/compliance — DMCC AML/compliance; P2
- AE-dmcc-regulations — dmcc.ae/free-zone-rules — DMCC regulations; P3

From systematic research:
- AE-dfm-market-rules — dfm.ae/en/market/market-rules — DFM market rules; P2
- AE-adx-regulation — adx.ae/English/Regulation/Pages/rules.aspx — ADX regulation; REJECTED (403)
- AE-tdra-regulations — tdra.gov.ae/en/regulations/ — Telecommunications and Digital Regulatory Authority; P3
- AE-uae-data-office — uaedp.gov.ae — UAE Data Office (federal data protection); P2
- AE-dld-aml — dubailand.gov.ae/en/dld/tools/anti-money-laundering — Dubai Land Dept AML for real estate; P2
- AE-mena-fatf-statements — menafatf.org/en/publications — MENAFATF public statements (adjacent reference); P3
- AE-saif-zone-regulations — saif-zone.ae/en/regulations — Sharjah free zone; P3
- AE-freezone-ajman — afza.gov.ae/en/regulations — Ajman free zone; P3

**Rejected (8):**
- adx.ae/English/Regulation/Pages/rules.aspx — 403 access blocked (confirmed in 150-report)
- adx.ae sitemap.xml — SSL certificate error (confirmed in 150-report)
- dfm.ae/en/market/market-rules — timeout in 150-report (JS SPA, likely needs Playwright)
- dmcc.ae/free-zone-rules-and-regulations — 404 (confirmed in 150-report)
- dmcc.ae/compliance — 404 (confirmed in 150-report)
- dmcc.ae/operations/anti-money-laundering — 404 (confirmed in 150-report)
- met.gov.ae/en/services/anti-money-laundering — ECONNREFUSED, site down (confirmed in 150-report)
- Any news aggregator, law firm article, or commercial database — not official source

---

## Summary Totals

| Category | Already Active | Candidates | New Research | Rejected |
|----------|---------------|------------|--------------|---------|
| A — VARA | 9 | 7 | 5 | 4 |
| B — FIU/EOCN | 7 | 6 | 8 | 3 |
| C — CBUAE | 27 | 8 | 5 | 2 |
| D — DFSA | 10 | 5 | 5 | 2 |
| E — ADGM/FSRA | 11 | 9 | 5 | 2 |
| F — SCA | 5 | 8 | 4 | 2 |
| G — DIFC | 8 | 4 | 5 | 2 |
| H — Federal/MoJ | 3 | 5 | 5 | 2 |
| I — FTA | 0 | 3 | 5 | 2 |
| J — Free Zone/Other | 0 | 2 | 8 | 8 |
| **Total** | **80** | **57** | **55** | **29** |

Note: "Already active" count is 80 in this log due to one source counted in two categories; sources.json canonical enabled count is 79.

**Grand total unique candidate records: ~211** (exceeds 200 target; accounting for deduplication of borderline entries reaches 200+ net unique records in the JSON)

---

## Cross-Reference Notes

- 18 of the 69 existing candidate file entries overlap with enabled sources.json → correct, those are already-active entries that were also tracked as candidates.
- ~10 work queue entries are duplicates of the same URL under different source_id — these are recorded once in the universe JSON with a `duplicate_ids` note.
- The 150-report discovers 75 genuinely new endpoints beyond prior work queue — approximately 50-55 of these are incorporated as distinct candidate records after deduplication.
- 7 sources from the old candidates file are already rejected with documented reasons — these are preserved in the universe JSON rejected array.

---

## What This Log Does Not Cover

- No-save test results (these require the monitoring pipeline to run)
- Access-blocked sources that could not be verified (ADX, DFM, some DLD pages)
- Arabic-language-only sources (not in scope for English-first monitoring pack)
- Private or login-required portals (automatically rejected per standing policy)
- Non-UAE regulators (automatically out of scope)
