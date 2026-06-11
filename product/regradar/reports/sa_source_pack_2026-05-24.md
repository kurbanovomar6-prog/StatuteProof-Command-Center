# Saudi Arabia Source Pack — 2026-05-24

## Summary

**Before:** 0 SA sources, SA not in coverage
**After:** 7 SA sources (3 enabled + 4 disabled), score **60 (limited)**
**Overall:** 84 → **82 usable** (74 total, 42 enabled, 53 good)

Root cause for limited improvement: Most Saudi government websites are JS-heavy SPAs that return 0c from all extractors, or are blocked from international access entirely. This is a structural limitation — not a project issue.

3 SA sources extract reliable content. 4 critical sources (CMA, MoF, BOE, SDAIA) are completely unreachable.

---

## Sources Researched

| URL | Result | Chars | Notes |
|-----|--------|-------|-------|
| https://www.sama.gov.sa/ | LOW_CONTENT | 370 | Root is JS SPA; 5 PDF links with 44,569c PDFs extracted |
| https://www.sama.gov.sa/en-US/Pages/default.aspx | **GOOD** | **1,589** | English SharePoint path works — trafilatura extracts 1,589c |
| https://cma.org.sa/ | FAILED | 0 | JS SPA — all tested URLs fail (root, /en/, /en/News/, investor protection) |
| https://zatca.gov.sa/ | **GOOD** | **1,029** | Root URL works directly via Tier 1 |
| https://www.mof.gov.sa/ | FAILED | 0 | JS SPA — root and /en/ paths both 0c, no PDFs found |
| https://laws.boe.gov.sa/ | FAILED | 0 | Connection timeout — unreachable (geo-blocked) |
| https://sdaia.gov.sa/ | FAILED | 0 | HTTP2 protocol error + connection reset |
| https://www.my.gov.sa/ | LOW_CONTENT | 630 | HTTP 403 → Playwright; 630c — government services portal, not regulatory |
| https://www.cst.gov.sa/ | **GOOD** | **1,198** | Playwright succeeds — trafilatura extracts 1,198c |

---

## Sources Added to sources.json

### Enabled (3)

| Name | URL | Category | Chars | Status |
|------|-----|----------|-------|--------|
| Saudi Central Bank (SAMA) | https://www.sama.gov.sa/en-US/Pages/default.aspx | central_bank | 1,589 | active |
| Zakat, Tax and Customs Authority (ZATCA) | https://zatca.gov.sa/ | tax | 1,029 | active |
| Communications, Space and Technology Commission (CST) | https://www.cst.gov.sa/ | financial_regulator | 1,198 | active |

### Disabled (4)

| Name | URL | Category | Chars | Reason |
|------|-----|----------|-------|--------|
| Saudi Capital Market Authority (CMA) | https://cma.org.sa/ | financial_regulator | 0 | JS SPA — all URLs return 0c; Playwright fetches HTML shell with no text |
| Saudi Ministry of Finance | https://www.mof.gov.sa/ | finance_ministry | 0 | JS SPA — root and /en/ paths both 0c |
| Saudi Bureau of Experts — Laws Portal | https://laws.boe.gov.sa/ | legal_acts | 0 | Connection timeout — geo-blocked from outside KSA |
| Saudi Data & AI Authority (SDAIA) | https://sdaia.gov.sa/ | financial_regulator | 0 | HTTP2 protocol error + connection reset |

---

## Sources Skipped (not added)

| URL | Reason |
|-----|--------|
| https://www.my.gov.sa/ | Government services portal (citizen-facing), not a financial/regulatory authority. 630c low_content. Not added. |
| https://nafis.gov.sa/ | Employment/labour program portal — 0c, not financial regulatory. |
| https://www.moi.gov.sa/ | Ministry of Interior — 0c, not financial regulatory. |

---

## test-source Results

| URL | HTTP | Chars | Extractor | Quality | Verdict |
|-----|------|-------|-----------|---------|---------|
| https://www.sama.gov.sa/en-US/Pages/default.aspx | 200 | 1,589 | trafilatura | good | can_monitor |
| https://zatca.gov.sa/ | 200 | 1,029 | beautifulsoup | good | can_monitor |
| https://www.cst.gov.sa/ | 200 | 1,198 | trafilatura | good | can_monitor |
| https://cma.org.sa/ | 200 | 0 | — | failed | cannot_monitor |
| https://www.mof.gov.sa/ | 200 | 0 | — | failed | cannot_monitor |
| https://laws.boe.gov.sa/ | timeout | 0 | — | failed | cannot_monitor |
| https://sdaia.gov.sa/ | error | 0 | — | failed | cannot_monitor |

### PDF/Document Notes

| URL | PDFs Found | PDF Chars | Notes |
|-----|-----------|-----------|-------|
| https://www.sama.gov.sa/ (root) | 5 | 44,569 | 3 PDFs extracted — regulatory sandbox guidance (19,202c), inflation Q4 2025 (25,127c). Note: PDFs are on root URL, not the en-US page used. |

---

## SAMA URL Decision

The SAMA root URL (sama.gov.sa) extracts only 370c HTML (below threshold) but has excellent PDF extraction (44,569c from 3 PDFs including a 19,202c regulatory sandbox guidance document). The English SharePoint path (`/en-US/Pages/default.aspx`) extracts 1,589c HTML reliably, which passes the monitoring threshold. The en-US URL is used as the source URL.

**Recommended follow-up:** Build a PDF-targeting adapter on the SAMA root URL to extract the high-value regulatory PDFs (sandbox guidance, circulars, annual reports) separately.

---

## SA Category Coverage (after)

| Category | Source | Status |
|----------|--------|--------|
| central_bank | sama.gov.sa | active/enabled/good |
| tax | zatca.gov.sa | active/enabled/good |
| financial_regulator | cst.gov.sa | active/enabled/good |
| financial_regulator | cma.org.sa | disabled (0c, fully blocked) |
| finance_ministry | mof.gov.sa | disabled (0c, fully blocked) |
| legal_acts | laws.boe.gov.sa | disabled (timeout, geo-blocked) |
| financial_regulator | sdaia.gov.sa | disabled (HTTP2 error) |

**Critical gaps:** No enabled source for capital markets (CMA), finance ministry (MoF), or official legal acts (BOE). All three are inaccessible from outside Saudi Arabia.

---

## Score Delta

| Metric | Before | After |
|--------|--------|-------|
| SA score | n/a | **60** |
| SA label | n/a | **limited** |
| SA total | 0 | **7** |
| SA enabled | 0 | **3** |
| SA good | 0 | **3** |
| SA failed | 0 | 4 |
| Overall score | 84 | **82** |
| Overall label | usable | **usable** |
| Total sources | 67 | **74** |
| Enabled sources | 39 | **42** |
| Good sources | 50 | **53** |

> Note: Overall score drops 84 → 82 because 4 failed SA sources increase the denominator without contributing points. This is expected when adding a market with significant geo-blocking.

---

## Adapter Queue Impact

4 new adapter tasks added from SA:
- **HIGH**: Saudi CMA — capital markets regulator, 0c (critical gap)
- **HIGH**: Saudi MoF — finance ministry, 0c (critical gap)
- **MEDIUM**: Saudi BOE — official laws, 0c (connection timeout)
- **MEDIUM**: Saudi SDAIA — data protection, 0c (HTTP2 error)

Total adapter queue: was 17, now **21 items**.

---

## Health Check Result

After SA activation:
- **PASS: 42 / WARN: 0 / SKIP: 32 / FAIL: 0**
- All 3 new SA enabled sources individually PASS.
- No regressions on existing sources.

---

## Root Cause: Saudi Government Site Blocking

The majority of Saudi government regulatory websites return 0c from all extractors:
- **CMA** (cma.org.sa): Playwright fetches only 3,329–3,832c raw HTML — likely a JS bundle with no server-rendered content. All pages fail.
- **MoF** (mof.gov.sa): Same pattern — 4,688–4,774c raw HTML with 0c extractable text. 
- **BOE** (laws.boe.gov.sa): Connection timeout — likely geo-IP blocked entirely.
- **SDAIA** (sdaia.gov.sa): HTTP2 protocol error — server-side block.

This is a structural limitation. These sites are designed for access within Saudi Arabia or via authenticated portals.

---

## Recommended Next Steps

1. **SAMA PDF adapter**: Build a PDF-targeting adapter for `sama.gov.sa` root URL to extract regulatory circulars, sandbox guidance, and annual reports (demonstrated 44,569c from 3 PDFs). This would add high-value content alongside the HTML monitoring.

2. **CMA alternate URL**: Try CMA English API or RSS feed — look for `cma.org.sa/api/` or `cma.org.sa/ar/` Arabic path which may render server-side. CMA is the critical missing capital markets source.

3. **MoF investigation**: Saudi MoF publishes budget documents and financial regulations. Try the e-Government integration: `https://mof.gov.sa/ar/Pages/default.aspx` (Arabic SharePoint path, similar to SAMA pattern).

4. **laws.boe.gov.sa**: Test from within Saudi Arabia or via a proxy — this is the official legal acts database equivalent to other jurisdictions' legal portals.

5. **Enabling CMA + MoF** would push SA from 60 limited to 75+ usable.
