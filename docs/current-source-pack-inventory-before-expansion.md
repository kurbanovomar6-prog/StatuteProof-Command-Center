# Current Source Pack Inventory Before Expansion

## 1. Executive Summary

Current customer-facing truth remains:

**13 enabled UAE sources; 9 readiness-supported in the current registry; 4 under extraction remediation.**

Do not use “13 validated sources,” “13 confirmed sources,” or “fully validated UAE pack.”

## 2. Registry Counts

| Metric | Count | Basis |
|---|---:|---|
| Total records in `product/regradar/sources.json` | 150 | Registry parse |
| UAE-related records | 22 | `jurisdiction: AE` or `AE-` source ID |
| Enabled UAE records | 13 | `enabled: true` and `jurisdiction: AE` |
| Readiness-supported enabled UAE records | 9 | `status: active` among enabled UAE sources |
| Enabled UAE remediation records | 4 | `status: remediation` among enabled UAE sources |
| Disabled/duplicate UAE records | 9 | Existing inactive/duplicate/remediation backlog rows |

## 3. Enabled UAE Sources

| Source ID | Name | URL | Category | Status | Current issue / note |
|---|---|---|---|---|---|
| `AE-central-bank-of-the-uae` | Central Bank of the UAE | `https://www.centralbank.ae/` | central_bank | active | Readiness-supported, but homepage is broad. Prefer subpages for regulatory signals. |
| `AE-dubai-virtual-assets-regulatory-authority-vara` | Dubai Virtual Assets Regulatory Authority (VARA) | `https://www.vara.ae/` | financial_regulator | active | Readiness-supported with JS/PDF caveats. |
| `AE-dubai-financial-services-authority-dfsa` | Dubai Financial Services Authority (DFSA) | `https://www.dfsa.ae/rules-and-standards` | financial_regulator | remediation | Current URL renders page-not-found/nav-shell. Should become explicit DFSA rulebook model only after validation. |
| `AE-abu-dhabi-global-market-adgm` | Abu Dhabi Global Market (ADGM) | `https://www.adgm.com/fsra` | financial_regulator | active | Readiness-supported with low-content caveat. |
| `AE-uae-ministry-of-finance` | UAE Ministry of Finance | `https://mof.gov.ae/` | finance_ministry | active | Readiness-supported. Broad homepage; targeted MoF/FTA pages should supplement it. |
| `AE-uae-legislation-portal` | UAE Legislation Portal | `https://uaelegislation.gov.ae/` | legal_acts | active | Readiness-supported with WAF/access and aggregate-page noise caveat. |
| `AE-uae-financial-intelligence-unit-uaefiu` | UAE Financial Intelligence Unit (UAEFIU) | `https://www.uaefiu.gov.ae/` | aml | remediation | Homepage too shallow. Circulars/publications source is preferred. |
| `AE-difc-laws-and-regulations` | DIFC Laws and Regulations | `https://www.difc.com/business/laws-and-regulations/` | legal_database | remediation | Meaningful extraction exists, but registry hold remains pending Source Monitor and Evidence Trail review. |
| `AE-uae-ministry-of-economy` | UAE Ministry of Economy | `https://www.moet.gov.ae/en/` | company_registry | active | Readiness-supported but broad. AML/commercial-control subpages should be more useful. |
| `AE-vara-enforcement` | VARA Enforcement Notices | `https://www.vara.ae/en/enforcement/` | financial_regulator | active | Readiness-supported and strong for enforcement-list monitoring. |
| `AE-cbuae-regulations` | CBUAE Regulations Sub-page | `https://www.centralbank.ae/en/regulations/` | central_bank | active | Readiness-supported with known rating-counter change noise. |
| `AE-uaefiu-circulars` | UAE FIU Circulars and Notices | `https://www.uaefiu.gov.ae/en/Publications/` | aml | active | Readiness-supported; preferred FIU monitoring source. |
| `AE-dfsa-notices` | DFSA Regulatory Notices | `https://www.dfsa.ae/regulation/notices-public-registers` | financial_regulator | remediation | Current URL is 404/nav-shell and collides with DFSA main source. Intended notice class must be clarified. |

## 4. Disabled / Duplicate UAE Rows Already In Registry

| Source ID | Name | URL | Status | Recommendation |
|---|---|---|---|---|
| blank | UAE Securities and Commodities Authority (SCA) | `https://www.sca.gov.ae/` | disabled_navigation_only | Keep disabled. Replace with specific SCA laws/decisions/circulars candidates after validation. |
| blank | UAE Federal Tax Authority (FTA) | `https://tax.gov.ae/` | disabled_external_access | Keep disabled until specific public guide/clarification pages are tested. |
| blank | UAE e-Laws Portal (Ministry of Justice) | `https://elaws.moj.gov.ae/` | disabled_external_access | Keep disabled; use official legislation portal candidates where accessible. |
| `AE-vara-rulebook` | VARA Virtual Assets Regulation | `https://www.vara.ae/en/regulatory-framework/` | duplicate_url | Keep as disabled candidate/backlog until VARA source model is split deliberately. |
| `AE-adgm-fsra-rules` | ADGM FSRA Rulebook | `https://www.fsra.adgm.com/rules-and-regulations/rulebooks` | disabled_external_access | Keep disabled/remediation until live access and official URL model is confirmed. |
| `AE-cbuae-circulars` | CBUAE Circulars | `https://www.centralbank.ae/en/regulations/` | duplicate_url | Replace with a real circulars/notices URL if discovered; do not duplicate regulations. |
| `AE-uaefiu-guidance` | UAE FIU AML Guidance | `https://www.uaefiu.gov.ae/en/Publications/` | duplicate_url | Replace with a specific guidance/typology URL if available. |
| `AE-difc-legislation` | DIFC Laws Portal | `https://www.difc.ae/business/laws-regulations/legislation/` | disabled_navigation_only | Keep disabled; may be merged or replaced by better DIFC legislation source. |
| `AE-sca-decisions` | SCA Board Decisions | `https://www.sca.gov.ae/en/legislation/sca-decisions.aspx` | disabled_navigation_only | High-value candidate, but requires selector/source-specific remediation. |

## 5. Source IDs That Should Stay

- `AE-central-bank-of-the-uae`
- `AE-cbuae-regulations`
- `AE-dubai-virtual-assets-regulatory-authority-vara`
- `AE-vara-enforcement`
- `AE-abu-dhabi-global-market-adgm`
- `AE-uae-ministry-of-finance`
- `AE-uae-legislation-portal`
- `AE-uae-ministry-of-economy`
- `AE-uaefiu-circulars`

These remain useful as current readiness-supported or important broad anchors, though several need better subpage/source modeling over time.

## 6. Source IDs That Should Be Split / Renamed / Deprecated

| Current source ID | Action |
|---|---|
| `AE-dubai-financial-services-authority-dfsa` | Split/migrate to `AE-dfsa-rulebook` after approved source-model migration and saved baseline. |
| `AE-dfsa-notices` | Deprecate ambiguous label or replace with explicit `AE-dfsa-enforcement-regulatory-actions` and/or `AE-dfsa-aml-mlro-notices`. |
| `AE-uae-financial-intelligence-unit-uaefiu` | Demote to homepage/reference or replace customer-facing FIU primary with `AE-uaefiu-circulars`. |
| `AE-difc-laws-and-regulations` | Keep remediation until hold is resolved; do not claim ready. |

## 7. Sources That Should Not Be Counted As Professional Coverage Today

- Disabled SCA homepage.
- Disabled FTA homepage.
- Disabled UAE e-Laws portal.
- Duplicate VARA rulebook URL.
- Duplicate CBUAE circulars URL.
- Duplicate UAE FIU guidance URL.
- DFSA main/notices remediation rows.
- UAE FIU homepage remediation row.
- DIFC Laws remediation row until hold is resolved.

## 8. Expansion Implication

The professional source pack should not simply enable the disabled rows. It should build a separate candidate list with official, specific, non-duplicative endpoints and then validate those endpoints through Source Lab before any source count is marketed.
