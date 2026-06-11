# Singapore Source Pack — 2026-05-24

## Overview

Singapore was added as the 12th RegRadar jurisdiction. All 8 sources are enabled, all pass
the good-quality threshold (≥1,000c), and all 8 health checks PASS.

SG coverage score: **100 (strong)** — 8/8 good, 0 restricted, 0 failed.

---

## Sources Added

| # | Name | URL | Category | Status | Chars | Extractor | Decision |
|---|------|-----|----------|--------|-------|-----------|----------|
| 1 | MAS — Regulation | mas.gov.sg/regulation | financial_regulator | active | 7,204c | beautifulsoup | **enabled** |
| 2 | MAS — AML/CFT | mas.gov.sg/regulation/anti-money-laundering | aml | active | 12,891c | beautifulsoup | **enabled** |
| 3 | IRAS — Tax Newsroom | iras.gov.sg/news-events/newsroom | tax | active | 6,986c | beautifulsoup | **enabled** |
| 4 | Singapore Statutes Online | sso.agc.gov.sg/Browse/Act/Current | legal_acts | active | 2,653c | beautifulsoup | **enabled** |
| 5 | PDPC — Guidelines | pdpc.gov.sg/guidelines-and-consultation | data_protection | active | 3,507c | beautifulsoup (Playwright) | **enabled** |
| 6 | ACRA | acra.gov.sg | company_regulator | active | 3,497c | beautifulsoup | **enabled** |
| 7 | CSA | csa.gov.sg | cyber | active | 5,124c | beautifulsoup | **enabled** |
| 8 | CCCS | cccs.gov.sg | competition | active | 4,268c | beautifulsoup | **enabled** |

**Total: 8 enabled / 0 mapped / 0 restricted / 0 adapter_required**

---

## URL Selection Notes

- **MAS**: Chose `/regulation` (7,204c) as the primary financial regulator page — covers Payment Services Act, SFA, Banking Act, Insurance Act, and digital asset licensing under a single URL. AML added separately (12,891c) due to its importance for compliance monitoring.
- **SSO**: Root `sso.agc.gov.sg/` is a SPA search interface returning only 950c. `/Browse/Act/Current` returns 2,653c reliably — used that path instead.
- **PDPC**: Site is a React SPA; Tier 1 returns <500c. Playwright fetches 328K chars and BeautifulSoup extracts 3,507c. Marked `active` because the two-tier scraper handles it correctly.
- **CSA `/Legislation-and-Regulation`**: Returned HTTP 404 — used root `csa.gov.sg/` instead (5,124c, good).
- **CCCS `/legislation-guidelines`**: Returned HTTP 404 — used root `cccs.gov.sg/` instead (4,268c, good).
- **MoneySense**: Tested (2,731c), passed — not added. MoneySense is a financial literacy portal, not a primary regulatory authority; out of scope for RegRadar.

---

## URLs Tested but Not Added

| URL | Result | Reason not added |
|-----|--------|-----------------|
| https://www.csa.gov.sg/Legislation-and-Regulation | 404, 213c | URL dead — root used instead |
| https://www.cccs.gov.sg/legislation-guidelines | 404, 213c | URL dead — root used instead |
| https://sso.agc.gov.sg/ | 950c low_content | SPA search page — Browse/Act/Current used |
| https://www.moneysense.gov.sg/ | 2,731c good | Consumer education portal — not a regulator |
| https://www.mas.gov.sg/regulation/notices | 8,537c good (Playwright) | Covered under /regulation |
| https://www.mas.gov.sg/regulation/enforcement | 5,867c good | Covered under /regulation |
| https://www.iras.gov.sg/taxes | 1,160c good | Newsroom has more signal (6,986c) |

---

## New Category Labels Added

Four new categories registered in `app/coverage.py`:

| Category key | Display label |
|-------------|--------------|
| `data_protection` | Data Protection / Privacy |
| `company_regulator` | Business / Company Regulator |
| `cyber` | Cyber & Digital Regulation |
| `competition` | Competition & Consumer Authority |

---

## Coverage Results After Adding SG

| Jurisdiction | Score | Label | Good | Low | Fail | Restricted |
|-------------|-------|-------|------|-----|------|-----------|
| **SG** | **100** | **strong** | **8** | **0** | **0** | **0** |
| AE | 100 | strong | 7 | 0 | 0 | 3 |
| KZ | 93 | strong | 7 | 0 | 1 | 0 |
| UZ | 90 | strong | 5 | 0 | 1 | 0 |
| GE | 89 | strong | 4 | 1 | 0 | 0 |
| BY | 86 | strong | 3 | 1 | 0 | 0 |
| TR | 83 | usable | 7 | 2 | 0 | 0 |
| RU | 75 | usable | 3 | 1 | 1 | 0 |
| INT | 75 | usable | 7 | 3 | 0 | 0 |
| SA | 62 | limited | 1 | 1 | 0 | 5 |
| AZ | 67 | usable | 3 | 1 | 1 | 0 |
| AM | 8 | weak | 0 | 1 | 4 | 0 |

**Overall: 83 (limited)** — 82 sources total, 51 enabled, 8 restricted, 19 need adapters.

*(Overall label "limited" is driven by AML and Legal Acts categories below 85, not by SG.)*

---

## Health Check Result

```
PASS: 48   WARN: 3   SKIP: 31   FAIL: 0
```

All 8 SG sources: PASS. No regressions in any other jurisdiction.

WARNs remain the same 3 pre-existing sources: BDDK (TR, 158c), CST (SA, 266c), ARLIS (AM, 33c).

---

## Recommended Future Adapters for SG

None urgently needed — all 8 sources extract reliably. However:

1. **PDPC** currently requires Playwright — consider building a lightweight adapter for Tier 1 access if Playwright availability becomes a bottleneck.
2. **Singapore Statutes Online** (`/Browse/Act/Current`) — the Act index page is useful for detecting new legislation, but per-Act full text is not extracted. A link-following adapter could significantly improve SG legal monitoring depth.

---

## Files Changed

| File | Change |
|------|--------|
| `sources.json` | +8 SG source entries |
| `app/coverage.py` | +SG in `_JURISDICTION_NAME` and `_REGION`; +4 new category labels |
| `reports/source_audit_2026-05-24.json` | Refreshed — 82 sources |
| `reports/coverage_2026-05-24.json` | Refreshed — SG included |
| `reports/coverage_2026-05-24.html` | Refreshed — SG included |
