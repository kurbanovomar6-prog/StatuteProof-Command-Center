# Sprint 3B — UAE 35-Source Candidate Registry

## 1. Verdict

- This was registry-only and report-only.
- No sources were activated.
- No production source monitoring behavior was changed.
- 44 UAE official source layers were mapped in `data/uae_source_candidates.json`.
- Priority breakdown: P0 = 17, P1 = 19, P2 = 8.
- Proposed status breakdown: active_candidate = 8, under_validation = 24, needs_adapter = 4, limited = 4, blocked = 1, avoid_for_now = 3.
- Every candidate has `should_activate_now: false`.

## 2. Candidate summary table

| Priority | Candidate ID | Source layer | Category | Commercial value | Proposed status | Adapter need | Should activate now |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0 | `ae-cbuae-main-publications` | CBUAE main regulatory publications | banking_payments_insurance | Critical | active_candidate | item_level | false |
| P0 | `ae-cbuae-rulebook` | CBUAE Rulebook | banking_payments_insurance | Critical | under_validation | item_level | false |
| P0 | `ae-cbuae-aml-cft` | CBUAE AML/CFT materials | aml_sanctions | Critical | under_validation | manual_mapping | false |
| P0 | `ae-cbuae-payments` | CBUAE payment systems and retail payment services | banking_payments_insurance | Critical | under_validation | manual_mapping | false |
| P1 | `ae-cbuae-insurance` | CBUAE insurance supervision and insurance rulebook | banking_payments_insurance | Medium | under_validation | manual_mapping | false |
| P1 | `ae-cbuae-sanctions` | CBUAE targeted financial sanctions page | aml_sanctions | High | under_validation | manual_mapping | false |
| P0 | `ae-vara-main-publications` | VARA main publications | virtual_assets_vasp | Critical | active_candidate | item_level | false |
| P0 | `ae-vara-rulebooks` | VARA rulebooks | virtual_assets_vasp | Critical | needs_adapter | item_level | false |
| P1 | `ae-vara-notices-guidance` | VARA regulatory notices and guidance | virtual_assets_vasp | High | under_validation | item_level | false |
| P1 | `ae-vara-enforcement-market-conduct` | VARA enforcement and market conduct publications | virtual_assets_vasp | High | under_validation | manual_mapping | false |
| P0 | `ae-dfsa-rulebook` | DFSA Rulebook | difc_dfsa | Critical | active_candidate | item_level | false |
| P1 | `ae-dfsa-consultations` | DFSA consultation papers | difc_dfsa | High | under_validation | item_level | false |
| P1 | `ae-dfsa-notices-media` | DFSA notices and media releases | difc_dfsa | High | under_validation | item_level | false |
| P0 | `ae-difc-laws` | DIFC Laws | difc_dfsa | Critical | active_candidate | item_level | false |
| P1 | `ae-difc-data-protection` | DIFC Data Protection Law and Commissioner materials | data_protection | High | under_validation | manual_mapping | false |
| P1 | `ae-difc-crypto-token-regulations` | DIFC crypto token and digital assets materials | virtual_assets_vasp | Medium | under_validation | manual_mapping | false |
| P0 | `ae-adgm-fsra-main` | ADGM/FSRA main regulatory publications | adgm_fsra | Critical | active_candidate | item_level | false |
| P0 | `ae-adgm-fsra-rulebook` | ADGM/FSRA rulebook | adgm_fsra | Critical | under_validation | manual_mapping | false |
| P1 | `ae-adgm-fsra-consultations` | ADGM/FSRA consultation papers | adgm_fsra | High | under_validation | manual_mapping | false |
| P1 | `ae-adgm-fsra-circulars-notices` | ADGM/FSRA circulars and notices | adgm_fsra | High | needs_adapter | item_level | false |
| P1 | `ae-adgm-data-protection-guidance` | ADGM Office of Data Protection guidance | data_protection | Medium | under_validation | manual_mapping | false |
| P1 | `ae-adgm-data-protection-regulations` | ADGM Data Protection Regulations | data_protection | Medium | under_validation | manual_mapping | false |
| P0 | `ae-fta-legislation` | FTA legislation | tax_fiscal | Critical | limited | waf_workaround | false |
| P1 | `ae-fta-tax-guides` | FTA tax guides | tax_fiscal | High | limited | waf_workaround | false |
| P1 | `ae-fta-public-clarifications` | FTA public clarifications | tax_fiscal | High | limited | waf_workaround | false |
| P1 | `ae-fta-corporate-tax-decisions` | FTA decisions and corporate tax updates | tax_fiscal | High | limited | waf_workaround | false |
| P0 | `ae-mof-tax-fiscal-notices` | Ministry of Finance selected tax and fiscal notices | tax_fiscal | Critical | active_candidate | item_level | false |
| P0 | `ae-uaefiu-publications` | UAE FIU publications and typologies | aml_sanctions | Critical | active_candidate | item_level | false |
| P1 | `ae-uaefiu-annual-risk-materials` | UAE FIU annual reports and risk materials | aml_sanctions | High | under_validation | pdf | false |
| P0 | `ae-eocn-sanctions` | Executive Office targeted financial sanctions materials | aml_sanctions | Critical | under_validation | manual_mapping | false |
| P1 | `ae-eocn-aml-national-strategy` | Executive Office AML/CFT national strategy materials | aml_sanctions | High | under_validation | manual_mapping | false |
| P0 | `ae-moet-aml-dnfbp` | Ministry of Economy AML / DNFBP guidance | aml_sanctions | Critical | active_candidate | item_level | false |
| P1 | `ae-moet-sanctions` | Ministry of Economy targeted financial sanctions page | aml_sanctions | High | under_validation | manual_mapping | false |
| P0 | `ae-uae-legislation-federal-laws` | UAE Legislation Portal federal laws and decrees | laws_legislation | Critical | needs_adapter | item_level | false |
| P1 | `ae-dubai-legislation-portal` | Dubai Official Gazette and Dubai legislation portal | laws_legislation | High | under_validation | manual_mapping | false |
| P2 | `ae-moj-federal-law-references` | Ministry of Justice / UAE federal law references | laws_legislation | Medium | blocked | waf_workaround | false |
| P0 | `ae-sca-cma-regulations-circulars` | SCA / CMA regulations and circulars | capital_markets_exchanges | Critical | needs_adapter | js | false |
| P2 | `ae-dfm-market-notices` | DFM market notices and issuer rules | capital_markets_exchanges | Medium | under_validation | manual_mapping | false |
| P2 | `ae-adx-market-notices` | ADX market notices and issuer rules | capital_markets_exchanges | Medium | under_validation | manual_mapping | false |
| P2 | `ae-nasdaq-dubai-rules` | Nasdaq Dubai / DIFC market rules | capital_markets_exchanges | Medium | under_validation | manual_mapping | false |
| P2 | `ae-det-commercial-licensing` | Dubai DET commercial licensing notices | commercial_licensing | Low | avoid_for_now | manual_mapping | false |
| P2 | `ae-cabinet-prime-minister-decisions` | UAE Cabinet and Prime Minister Office decisions | laws_legislation | Medium | under_validation | manual_mapping | false |
| P2 | `ae-tdra-digital-regulation` | TDRA digital regulation materials | digital_regulation | Low | avoid_for_now | waf_workaround | false |
| P2 | `ae-customs-icp` | Customs / ICP notices | customs_identity | Low | avoid_for_now | manual_mapping | false |

## 3. P0 candidates for validation-first work

Best 15 candidates to test before any future activation decision:

1. `ae-cbuae-main-publications` — baseline CBUAE monitoring, but item-level circular precision is still required.
2. `ae-cbuae-rulebook` — high-value obligations source for banks, payments, and fintech.
3. `ae-cbuae-payments` — direct payment services relevance.
4. `ae-vara-main-publications` — VASP client priority source.
5. `ae-vara-rulebooks` — likely the most valuable VASP item-level adapter target.
6. `ae-dfsa-rulebook` — core DIFC-regulated firm source.
7. `ae-difc-laws` — corrected URL needs extraction validation.
8. `ae-adgm-fsra-main` — first ADGM/FSRA dedicated page to validate.
9. `ae-adgm-fsra-rulebook` — critical for ADGM-regulated firms if stable source structure exists.
10. `ae-mof-tax-fiscal-notices` — accessible federal tax/fiscal fallback.
11. `ae-uaefiu-publications` — core AML source across profiles.
12. `ae-eocn-sanctions` — critical sanctions layer if sections can be mapped.
13. `ae-moet-aml-dnfbp` — corrected domain and high AML/DNFBP value.
14. `ae-uae-legislation-federal-laws` — high-value but needs item-level adapter validation.
15. `ae-sca-cma-regulations-circulars` — capital markets gap, but likely adapter work.

## 4. Sources that should NOT be activated yet

- FTA layers (`ae-fta-*`) — current source is limited by external access/WAF behavior; validate before any activation.
- UAE Legislation Portal federal laws (`ae-uae-legislation-federal-laws`) — active aggregate source exists, but item-level legal monitoring needs an adapter and repeated-run stability checks.
- SCA/CMA (`ae-sca-cma-regulations-circulars`) — current repo entry is disabled navigation-only; authority/domain transition must be validated.
- ADGM/FSRA circulars and notices (`ae-adgm-fsra-circulars-notices`) — exact official listing must be located.
- Ministry of Justice / e-Laws (`ae-moj-federal-law-references`) — blocked from current infrastructure.
- TDRA (`ae-tdra-digital-regulation`) — avoid for now due weaker financial-regulatory fit and likely access issues.
- Dubai DET (`ae-det-commercial-licensing`) — avoid for now unless a client profile requires commercial licensing.
- Customs / ICP (`ae-customs-icp`) — avoid for now; not core financial-regulatory monitoring.

## 5. Recommended Sprint 3C speed/reliability checks

Run validation-only checks for these 15 URLs/layers. Do not activate during Sprint 3C.

| Candidate ID | URL to test | Checks |
| --- | --- | --- |
| `ae-cbuae-main-publications` | `https://www.centralbank.ae/` | HTTP status, response time, extracted chars, JS dependency, repeated-run stability, item-level links |
| `ae-cbuae-rulebook` | `https://rulebook.centralbank.ae/` | HTTP status, response time, extracted chars, item-level potential, repeated-run stability |
| `ae-cbuae-payments` | `https://www.centralbank.ae/` | payment-specific section mapping, PDF dependency, item-level potential |
| `ae-vara-main-publications` | `https://www.vara.ae/` | HTTP status, response time, extracted chars, PDF dependency, item-level links |
| `ae-vara-rulebooks` | `https://www.vara.ae/` | rulebook URL discovery, PDF dependency, item-level potential, repeated-run stability |
| `ae-dfsa-rulebook` | `https://www.dfsa.ae/` | rulebook URL discovery, extracted chars, item-level structure |
| `ae-difc-laws` | `https://www.difc.com/business/laws-and-regulations/` | corrected URL validation, extracted chars, item links, repeated-run stability |
| `ae-adgm-fsra-main` | `https://www.adgm.com/financial-services-regulatory-authority` | HTTP status, response time, extracted chars, FSRA item links |
| `ae-adgm-fsra-rulebook` | `https://www.adgm.com/financial-services-regulatory-authority` | rulebook link discovery, PDF dependency, item-level potential |
| `ae-mof-tax-fiscal-notices` | `https://mof.gov.ae/` | tax/fiscal section mapping, PDF dependency, repeated-run stability |
| `ae-uaefiu-publications` | `https://www.uaefiu.gov.ae/` | JS dependency, extracted chars, publication/typology page discovery |
| `ae-eocn-sanctions` | `https://www.uaeiec.gov.ae/en-us` | HTTP status, response time, section mapping, sanctions/publications index discovery |
| `ae-moet-aml-dnfbp` | `https://www.moet.gov.ae/en/` | corrected domain validation, PDF dependency, AML/DNFBP page discovery |
| `ae-uae-legislation-federal-laws` | `https://uaelegislation.gov.ae/` | WAF/403 risk, item-level law/decree URLs, repeated-run stability |
| `ae-sca-cma-regulations-circulars` | `https://www.sca.gov.ae/` | JS dependency, extracted chars beyond navigation, current authority/URL transition |

Each check should record HTTP status, response time, text extraction chars, PDF dependency, JS dependency, WAF/403 risk, repeated-run stability, and item-level potential.

## 6. Coverage messaging

Safe future wording:

- "35+ official UAE source layers mapped."
- "Only validated sources enter client monitoring profiles."
- "Additional sources are under technical validation."
- "Limitations are disclosed before every pilot."

Unsafe wording to avoid:

- "35 active monitored sources"
- "complete UAE coverage"
- "all UAE regulators"
- "never miss"
- "real-time alerts"
- "guaranteed compliance"
