# DIFC DOM / Access Investigation Report

Date: 2026-06-16

## Method

- Used controlled public HTTP checks against official `difc.com` URLs.
- Used no-save `run_source_intake(...)` checks only; no evidence was saved in this phase.
- Did not broad crawl, bypass login/CAPTCHA/paywalls, or use private endpoints.

## HTTP / Public Access Findings

| URL | HTTP | Content type | Raw size | Finding |
| --- | ---: | --- | ---: | --- |
| `https://www.difc.com/business/laws-and-regulations/` | 200 | `text/html` | 175,086 | Public official overview. |
| `https://www.difc.com/business/laws-and-regulations/legal-database/` | 200 | `text/html` | 1,038,273 | Public official legal database; very large listing. |
| `https://www.difc.com/business/laws-and-regulations/consultation-papers/` | 200 | `text/html` | 143,192 | Public official consultation page. |
| `https://www.difc.com/business/laws-and-regulations/data-protection/` | 404 | `text/html` | 5,206 | Rejected stale route. |
| `https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection` | 200 | `text/html` | 217,343 | Public official Data Protection Commissioner hub. |
| `https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/guidance` | 200 | `text/html` | 299,060 | Public official guidance page. |
| `https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/regulation-10` | 200 | `text/html` | 181,730 | Public official Regulation 10 page. |
| `https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/supervision-enforcement` | 200 | `text/html` | 160,995 | Public official supervision/enforcement page. |
| `https://www.difc.com/business/laws-and-regulations/legal-database/difc-laws/data-protection-law-difc-law-no-5-2020` | 200 | `text/html` | 159,807 | Public official law detail page; Playwright fallback succeeded. |
| `https://www.difc.com/business/laws-and-regulations/legal-database/difc-laws/digital-assets-law-difc-law-no-2-of-2024` | 200 | `text/html` | 152,213 | Public official law detail page; Playwright fallback succeeded. |

## Legal Database DOM Findings

`https://www.difc.com/business/laws-and-regulations/legal-database/`:

- Rendered title: `DIFC Legal Database`.
- `main` visible text length: about 22,099 characters.
- Anchor count: 578.
- Contains direct official PDF links from `assets.difc.com`, including:
  - `data-protection-law.pdf`
  - `digital_assets_law_2_of_2024.pdf`
  - `companies_law.pdf`
  - `common_reporting_standards_law_no_2_of_2018_final.pdf`
- The title/detail anchor and PDF anchor are adjacent but not always the same anchor. Generic document-listing extraction therefore misses useful law-title/PDF pairings.

## Initial No-Save Findings

Initial generic no-save tests for 10 official DIFC candidates remained held:

- Generic static/document adapters extracted some meaningful text, but quality stayed below evidence threshold.
- Public pages were incorrectly classified with access-control language because visible text includes terms like `DIFC Client Portal`.
- Detail pages were often short under static extraction and marked nav-shell even though they include useful legal metadata and document links.

## Final No-Save Findings After Remediation

After the `difc_legal_database` adapter and public-page policy fix, 8 of 10 official DIFC candidates passed the preview gate strongly enough for proof/baseline work:

- `AE-difc-laws-and-regulations`
- `AE-difc-legal-database`
- `AE-difc-data-protection-commissioner`
- `AE-difc-data-protection-guidance`
- `AE-difc-data-protection-regulation-10`
- `AE-difc-data-protection-supervision-enforcement`
- `AE-difc-data-protection-law-2020`
- `AE-difc-companies-law-2018`

Two candidates remained held:

- `AE-difc-consultation-papers` scored 59 and stayed below strict activation threshold.
- `AE-difc-digital-assets-law-2024` scored 59 and stayed below strict activation threshold.

## Recommended Adapter / Config

Create a DIFC source-specific legal database adapter:

- adapter family/name: `difc_legal_database`
- default container: `main`
- extract title/detail links and adjacent PDF/document links;
- include law/regulation/consultation/data-protection tokens;
- infer titles from neighboring cards/list items when link text is generic or empty;
- produce deterministic row hashes;
- expose medium source-health risk unless baseline proves stable.

## Access / Source-Health Risk

- Source is public and technically accessible.
- Source-health risk remains medium because DIFC pages are large, JS-heavy, and legal detail pages may need rendered fallback.
- No private or access-controlled route should be activated.
- Stale/404 routes stay rejected or remediation.
