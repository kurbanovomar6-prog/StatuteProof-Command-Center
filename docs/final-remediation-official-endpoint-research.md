# Final Remediation Official Endpoint Research

Date: 2026-06-17

Research scope: public official or officially linked DFSA and UAE FIU endpoints only. No login, CAPTCHA, paywall, private portal, or private-data access was attempted.

## DFSA Endpoint Research

| Candidate | Official URL | Type | Why official/public | Commercial relevance | Extraction strategy | Risk | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `AE-dfsa-rulebook-thomsonreuters` | `https://dfsaen.thomsonreuters.com/rulebook/rulebook-modules` | Official-linked rulebook | Already active and official-linked from DFSA rulebook ecosystem. | High for DFSA firms. | Existing article/rulebook extraction. | Duplicate if reused. | Do not use as replacement because already active. |
| `AE-dfsa-laws-rules` | `https://www.dfsa.ae/your-resources/regulatory/laws-and-rules` | Regulatory hub | Official DFSA public page. | Useful but hub-like. | Generic/listing extraction. | Quality 59 and preview-only. | Hold. |
| `AE-dfsa-policy-statements` | `https://www.dfsa.ae/laws-rules/legal-resources/policy-statements` | Policy statements listing | Official DFSA public page. | Useful to compliance/legal buyers. | Listing/PDF listing tested. | Broad/noisy listing; PDF listing found no useful PDF links. | Hold. |
| `AE-dfsa-guides-handbooks` | `https://www.dfsa.ae/your-resources/regulatory/guides-handbooks` | Guidance listing | Official DFSA public page. | Useful for compliance teams. | Listing/PDF listing tested. | Quality below activation confidence; broad content. | Hold. |
| `AE-dfsa-reports` | `https://www.dfsa.ae/your-resources/publications-reports/dfsa-reports` | Reports hub | Official DFSA public page. | Useful, but broad. | Listing tested. | Too broad/noisy for a replacement endpoint. | Hold. |
| `AE-dfsa-annual-reports` | `https://www.dfsa.ae/your-resources/publications-reports/annual-report` | Annual report PDF listing | Official DFSA public page. | Useful for regulator annual context, compliance horizon scanning, and audit files. | `pdf_listing` with `main` container, sorted items. | Medium source-health risk due dynamic site; mitigated by stable hash/baseline. | Activate as replacement for stale DFSA main remediation endpoint. |
| `AE-dfsa-annual-aml-reports` | `https://www.dfsa.ae/your-resources/publications-reports/annual-anti-money-laundering-reports` | AML annual report PDF listing | Official DFSA public page. | High relevance to MLRO/AML teams. | `pdf_listing` with `main` container, sorted items. | Medium source-health risk; mitigated by stable hash/baseline. | Activate as replacement for stale DFSA notices remediation endpoint. |

## UAE FIU Endpoint Research

| Candidate | Official URL | Type | Why official/public | Commercial relevance | Extraction strategy | Risk | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `AE-uae-financial-intelligence-unit-uaefiu` | `https://www.uaefiu.gov.ae/` | Homepage | Official FIU public website. | Low as a monitoring endpoint because it is generic. | Generic extraction / Playwright fallback. | `NAV_SHELL_ONLY`, quality 0, shell/search/language content. | Keep remediation. |
| `AE-uaefiu-nra-2024` | FIU NRA 2024 page | Publication detail/listing | Official FIU public page. | High if extractable because NRA is important MLRO context. | FIU document-listing adapter. | Single-document limited preview; direct PDF returned HTTP 403. | Hold. |
| `AE-uaefiu-strategic-analysis` | FIU strategic-analysis route | Publication route | Official FIU domain. | Potentially useful. | FIU document-listing adapter. | Returned Error404/nav-shell. | Reject current URL. |
| `AE-uaefiu-annual-reports` | FIU annual-report route | Publication route | Official FIU domain. | Useful if distinct. | FIU document-listing adapter. | Appeared duplicate-prone against active FIU publications/typology sources. | Hold until distinctness is proven. |

## Research Verdict

- DFSA remediation can be improved honestly by replacing two stale URLs with two official, proof-backed DFSA report listings.
- UAE FIU homepage cannot be honestly activated today. Its best next source work is not a homepage retry; it is finding a stable, distinct official FIU document listing or PDF endpoint that avoids 403 and duplicate-publication alias risk.
