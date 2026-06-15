# UAE JS-Heavy Current Blocker Inventory

Date: 2026-06-15

## Current Truth

- Public truth at sprint start: **23 enabled / 19 readiness-supported / 4 under extraction remediation**.
- Source gap to 50 enabled/readiness-supported: **27 additional proven sources**.
- Discovery inventory is sufficient for the next wave; extraction is the blocker.

## UAE FIU NAV_SHELL / SPA Candidates

| Source ID | URL | Current Failure | Suspected DOM Cause | Suspected Adapter | Priority | Next Action |
| --- | --- | --- | --- | --- | --- | --- |
| `AE-uaefiu-aml-cft-laws` | `https://uaefiu.gov.ae/en/more/knowledge-centre/aml-cft-laws-related-decisions/` | `NAV_SHELL_ONLY` | Knowledge-centre SPA content not isolated by generic selectors | `fiu_eocn_document_listing` or FIU-specific listing | P1 | Playwright DOM/XHR inspect, then no-save retest |
| `AE-uaefiu-typology-reports` | `https://uaefiu.gov.ae/en/more/knowledge-centre/publications/trends-typology-reports/` | `NAV_SHELL_ONLY` | Publication listing rendered behind SPA shell | FIU listing/PDF listing | P1 | Inspect links/XHR/PDF anchors |
| `AE-uaefiu-publications-hub` | `https://uaefiu.gov.ae/en/more/knowledge-centre/publications/` | `NAV_SHELL_ONLY` | Hub content not isolated | FIU listing | P1 | Inspect rendered publication cards |
| `AE-uaefiu-annual-reports` | `https://uaefiu.gov.ae/en/more/knowledge-centre/publications/annual-report/` | `NAV_SHELL_ONLY` | Document listing not isolated | FIU document listing | P2 | Inspect PDF/document anchors |
| `AE-uaefiu-nra-2024` | `https://uaefiu.gov.ae/en/more/knowledge-centre/publications/national-risk-assessment-report-2024/` | `NAV_SHELL_ONLY` | Static/detail content behind SPA shell | static/custom FIU selector | P1 | Inspect rendered detail page |
| `AE-uaefiu-press-releases` | `https://uaefiu.gov.ae/en/more/media/press-releases/` | `NAV_SHELL_ONLY` | News listing behind SPA shell | FIU listing | P2 | Retest after selector discovery |

## SCA JS_RENDERING / Listing Candidates

| Source ID | URL | Current Failure | Suspected DOM Cause | Suspected Adapter | Priority | Next Action |
| --- | --- | --- | --- | --- | --- | --- |
| `AE-sca-regulations-listing` | `https://www.sca.gov.ae/en/regulations/regulations-listing` | `JS_RENDERING_NEEDED` / no strong pass | ASP.NET/card listing needs exact item selectors | `sca_listing` | P1 | Inspect rendered `.aegov-card` / `[data-icms-list]` |
| `AE-sca-regulations-amendments` | `https://www.sca.gov.ae/en/regulations/regulations-listing/amendments` | `JS_RENDERING_NEEDED` | Filtered listing / cards | `sca_listing` | P1 | Same as above |
| `AE-sca-fatca-crs` | `https://www.sca.gov.ae/en/regulations/automatic-exchange-of-information-fatca-and-crs` | `JS_RENDERING_NEEDED` | Thin rendered page or documents not isolated | static/listing | P1 | Inspect content selector and documents |
| `AE-sca-corporate-governance` | `https://www.sca.gov.ae/en/regulations/corporate-governance` | `JS_RENDERING_NEEDED` | Card/listing chrome | `sca_listing` | P2 | Retest with exact listing selector |
| `AE-sca-market-rules` | `https://www.sca.gov.ae/en/regulations/market-rules-approved-by-sca` | `JS_RENDERING_NEEDED` | Listing cards/details | `sca_listing` | P2 | Inspect item titles/links |
| `AE-sca-latest-regulations` | `https://www.sca.gov.ae/en/regulations/regulations` | `LISTING_ADAPTER_REQUIRED` | Previous listing extraction too noisy | `sca_listing` | P1 | Retest with improved selectors |
| `AE-sca-aml-cft` | `https://www.sca.gov.ae/en/regulations/anti-money-laundering-and-terrorist-financing` | `NAV_SHELL_ONLY` | Content block not isolated from shell | static/listing selector | P1 | Inspect rendered body and content component |

## ADGM Alternate-Component Candidates

| Source ID | URL | Current Failure | Suspected DOM Cause | Suspected Adapter | Priority | Next Action |
| --- | --- | --- | --- | --- | --- | --- |
| `AE-adgm-media-announcements` | `https://www.adgm.com/media/announcements` | `NAV_SHELL_ONLY` | Different component from existing `adgm-page` pages | ADGM alternate listing/custom selector | P1 | Inspect rendered component and links |
| `AE-adgm-dp-regulatory-actions` | `https://www.adgm.com/operating-in-adgm/office-of-data-protection/regulatory-actions` | `NAV_SHELL_ONLY` | Data-protection component structure not mapped | custom/static/listing | P2 | Inspect content selector |
| `AE-adgm-dp-guidance` | `https://www.adgm.com/operating-in-adgm/office-of-data-protection/guidance` | `NAV_SHELL_ONLY` | Guidance listing/detail selector unknown | custom/static/listing | P2 | Inspect content selector |

## Access-Blocked Or High-Health-Risk Candidates

| Source ID | URL | Current Failure | Suspected Cause | Priority | Next Action |
| --- | --- | --- | --- | --- | --- |
| `AE-cbuae-regulations` | `https://www.centralbank.ae/en/our-operations/regulations/` | `NAV_SHELL_ONLY` / blocked variants | Heavy site/WAF/selector unknown | P2 | Playwright only, no bypass; keep blocked if access policy triggers |
| `AE-cbuae-publications` | `https://www.centralbank.ae/en/publications/` | blocked in work queue | Access or selector risk | P2 | Try official public endpoint only |
| `AE-dfsa-rulebook-thomsonreuters` | `https://dfsaen.thomsonreuters.com/` | `NAV_SHELL_ONLY` root, module URL active elsewhere | Wrong root endpoint | P3 | Prefer already active module endpoint |
| `AE-dfsa-aml-mlro-notices` | `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance` | `NAV_SHELL_ONLY` root, child URL active elsewhere | Root page shell/noise | P3 | Prefer already active notice path |
| `AE-difc-laws-and-regulations` | `https://www.difc.com/business/laws-and-regulations/` | quality below strong threshold | Content meaningful but too thin/noisy | P3 | Hold unless exact listing/detail improves |

## Fastest Honest Route

1. Try to convert UAE FIU knowledge-centre pages with rendered/XHR selectors.
2. Try to convert SCA listings with exact item/card extraction.
3. Try ADGM media/data-protection alternate selectors.
4. Save evidence only for strong passes and activate only after repeat baseline plus dry-run.
