# Final Remediation No-Save Investigation Report

Date: 2026-06-17

All tests were controlled no-save Source Lab or equivalent live checks. No evidence was saved from failing candidates.

## Existing Remediation Sources

| Source ID | URL | Adapter | Normalized length | Normalized hash | Quality | Nav shell | Shallow | Duplicate risk | Access blocked | Noise / health risk | No-save status | Can save evidence | Failure / recommendation |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `AE-dubai-financial-services-authority-dfsa` | `https://www.dfsa.ae/rules-and-standards` | Playwright + `main` selector | 77 | page-not-found shell hash | 0 / POOR | Yes | Yes | Yes with DFSA notices shell | No | High | `NAV_SHELL_ONLY` | No | Disable/replace. |
| `AE-dfsa-notices` | `https://www.dfsa.ae/regulation/notices-public-registers` | Playwright + `main` selector | 77 | page-not-found shell hash | 0 / POOR | Yes | Yes | Yes with DFSA main shell | No | High | `NAV_SHELL_ONLY` | No | Disable/replace. |
| `AE-uae-financial-intelligence-unit-uaefiu` | `https://www.uaefiu.gov.ae/` | Generic extraction after Playwright fallback | 4,722 | `78710958e78b30edc3185f7cd3e8373fa284a43bd97ac5616839cad649fe56d0` | 0 / POOR | Yes | No | Low hash collision, high shell risk | Requests 403; Playwright public render worked | Medium / unknown | `NAV_SHELL_ONLY` | No | Keep remediation; homepage is not a monitoring-ready endpoint. |

## DFSA Replacement Candidates

| Source ID | URL | Adapter | Normalized length | Normalized hash | Quality | Item count | Can save evidence | Decision |
| --- | --- | --- | ---: | --- | --- | ---: | --- | --- |
| `AE-dfsa-rulebook-thomsonreuters` | `https://dfsaen.thomsonreuters.com/rulebook/rulebook-modules` | Existing rulebook extraction | 10,634 | `352dcfd27d1bf437bccb879df1546c6bb44239b4c4cf53486b614a1c19e8ea61` | 59 / LIMITED | n/a | No-save only | Already active; not used as replacement. |
| `AE-dfsa-laws-rules` | `https://www.dfsa.ae/your-resources/regulatory/laws-and-rules` | Listing | 3,263 | `ef96a4afd476b4b3071e5427f309a4be111c5f65d6bf75dce4a1eecc34d414f4` | 59 / LIMITED | n/a | No | Held below activation confidence. |
| `AE-dfsa-policy-statements` | `https://www.dfsa.ae/laws-rules/legal-resources/policy-statements` | DFSA listing | 16,288 | `80f14fd1ab68860a0ecd1ff1262b04f35526e63e6ee4c45d805496d8929aa2d4` | 65 / ACCEPTABLE | 108 | Yes | Held as too broad/noisy; PDF-listing variant found no PDF links. |
| `AE-dfsa-guides-handbooks` | `https://www.dfsa.ae/your-resources/regulatory/guides-handbooks` | DFSA listing / PDF listing | 18,042 / 1,600 | `5f8fae077276b8ef8d86aeced6e75c6828d3585e6ba1c3f9c19c2c524f48f42e` | 65 / 52 | 114 / 5 | No for PDF variant | Held below activation confidence. |
| `AE-dfsa-reports` | `https://www.dfsa.ae/your-resources/publications-reports/dfsa-reports` | DFSA listing | 18,238 | `9238756621bf2c30ee35495a3cfa47d94bf471a5b86cf098711a72d3fb1c17ef` | 65 / ACCEPTABLE | broad | Yes | Held as too broad/noisy for replacement. |
| `AE-dfsa-annual-reports` | `https://www.dfsa.ae/your-resources/publications-reports/annual-report` | `pdf_listing` | 4,566 | `5ac1b92a2d6cb782b2f5ec076c39866019568b99c712299662d0e36b8c17348e` | 65 / ACCEPTABLE | 16 | Yes | Strong pass; saved evidence and activated. |
| `AE-dfsa-annual-aml-reports` | `https://www.dfsa.ae/your-resources/publications-reports/annual-anti-money-laundering-reports` | `pdf_listing` | 1,457 | `693cf380283f665545f0a20de732d6363efbdcf7fa3abba9fab782dfbc9f98b1` | 62 / ACCEPTABLE | 4 | Yes | Strong pass; saved evidence and activated. |

## UAE FIU Replacement Candidates

| Source ID | URL | Result | Decision |
| --- | --- | --- | --- |
| `AE-uaefiu-nra-2024` | FIU NRA 2024 page | Quality 59 / LIMITED, 562 normalized chars, single-document style extraction. | Held; not enough for activation. |
| `AE-uaefiu-nra-2024-pdf` | FIU NRA 2024 direct PDF | HTTP 403 for direct PDF. | Held/access-blocked. |
| `AE-uaefiu-strategic-analysis` | FIU strategic-analysis route | Error404/nav-shell. | Rejected current URL. |
| `AE-uaefiu-annual-reports` | FIU annual-report route | Quality 65 but appeared alias/duplicate-prone against active FIU publication/typology sources. | Held until distinctness is proven. |

## Summary

- Existing remediation sources tested: 3.
- Replacement candidates tested: 11.
- Strong no-save passes: 2.
- Evidence eligibility from strong passes: 2.
- No-save-only sources activated: 0.
