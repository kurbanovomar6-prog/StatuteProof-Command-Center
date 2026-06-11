# UAE Source Pack — 2026-05-24

## Summary

**Before:** 0 AE sources, AE not in coverage
**After:** 10 AE sources (7 enabled + 1 limited + 2 disabled), score **82 (usable)**
**Overall:** 84 usable → **84 usable** (67 total, 39 enabled, 50 good)

7 UAE enabled sources extract good content and pass health checks.
3 UAE sources are disabled/limited due to JS SPA extraction failures or connection timeouts.

---

## Sources Researched

| URL | Result | Chars | Notes |
|-----|--------|-------|-------|
| https://www.centralbank.ae/ | GOOD | 26,796 | Central Bank — HTTP 403 to Tier 1, Playwright succeeds; PDFs work (31,083c) |
| https://www.sca.gov.ae/ | LOW_CONTENT | 944 | SPA — all pages return identical 944–1,056c navigation text; needs adapter |
| https://www.vara.ae/ | GOOD | 2,705 | VARA crypto regulator — PDFs also good (37,085c) |
| https://www.dfsa.ae/ | GOOD | 5,627 | DFSA Dubai free zone financial regulator |
| https://www.adgm.com/ | GOOD | 2,135 | ADGM Abu Dhabi free zone financial hub |
| https://www.adgm.com/operating-in-adgm/financial-services-regulatory-authority | SKIP | — | 404 page — content is error page, not FSRA regulatory content |
| https://mof.gov.ae/ | GOOD | 13,326 | Ministry of Finance — PDFs good (97,393c) |
| https://tax.gov.ae/ | FAILED | 0 | JS SPA — Playwright renders 2,000c raw HTML, zero extractable text |
| https://uaelegislation.gov.ae/ | GOOD | 15,644 | Legislation portal — HTTP 403 to Tier 1, Playwright succeeds |
| https://www.uaefiu.gov.ae/ | GOOD | 2,026 | UAE Financial Intelligence Unit — HTTP 403 to Tier 1, Playwright succeeds |
| https://elaws.moj.gov.ae/ | FAILED | 0 | Connection timeout — unreachable (possible geo-block) |

---

## Sources Added to sources.json

### Enabled (7)

| Name | URL | Category | Chars | Status |
|------|-----|----------|-------|--------|
| Central Bank of the UAE | https://www.centralbank.ae/ | central_bank | 26,796 | active |
| Dubai Virtual Assets Regulatory Authority (VARA) | https://www.vara.ae/ | financial_regulator | 2,705 | active |
| Dubai Financial Services Authority (DFSA) | https://www.dfsa.ae/ | financial_regulator | 5,627 | active |
| Abu Dhabi Global Market (ADGM) | https://www.adgm.com/ | financial_regulator | 2,135 | active |
| UAE Ministry of Finance | https://mof.gov.ae/ | finance_ministry | 13,326 | active |
| UAE Legislation Portal | https://uaelegislation.gov.ae/ | legal_acts | 15,644 | active |
| UAE Financial Intelligence Unit (UAEFIU) | https://www.uaefiu.gov.ae/ | aml | 2,026 | active |

### Limited / Disabled (3)

| Name | URL | Category | Chars | Reason |
|------|-----|----------|-------|--------|
| UAE Securities and Commodities Authority (SCA) | https://www.sca.gov.ae/ | financial_regulator | 944 | SPA — all pages return identical 944–1,056c navigation text; needs adapter |
| UAE Federal Tax Authority (FTA) | https://tax.gov.ae/ | tax | 0 | JS SPA — zero extractable text; needs custom adapter |
| UAE e-Laws Portal (Ministry of Justice) | https://elaws.moj.gov.ae/ | legal_acts | 0 | Connection timeout — possible geo-block from outside UAE |

---

## Sources Skipped

| URL | Reason |
|-----|--------|
| https://www.adgm.com/operating-in-adgm/financial-services-regulatory-authority | Returns 404; content extracted is error page text, not FSRA content. ADGM root (adgm.com) covers the same domain. |
| https://ai.gov.ae/ | Not tested — UAE Data Office is not a financial regulator; out of scope for financial/AML monitoring. |

---

## test-source Results

| URL | HTTP | Chars | Extractor | Quality | Verdict |
|-----|------|-------|-----------|---------|---------|
| https://www.centralbank.ae/ | 403→Playwright | 26,796 | beautifulsoup | good | can_monitor |
| https://www.vara.ae/ | 200 | 2,705 | beautifulsoup | good | can_monitor |
| https://www.dfsa.ae/ | 200 | 5,627 | beautifulsoup | good | can_monitor |
| https://www.adgm.com/ | 200 | 2,135 | beautifulsoup | good | can_monitor |
| https://mof.gov.ae/ | 200 | 13,326 | beautifulsoup | good | can_monitor |
| https://uaelegislation.gov.ae/ | 403→Playwright | 15,644 | beautifulsoup | good | can_monitor |
| https://www.uaefiu.gov.ae/ | 403→Playwright | 2,026 | beautifulsoup | good | can_monitor |
| https://www.sca.gov.ae/ | 200 | 944 | trafilatura | low_content | needs_adapter |
| https://tax.gov.ae/ | 200 | 0 | — | failed | cannot_monitor |
| https://elaws.moj.gov.ae/ | timeout | 0 | — | failed | cannot_monitor |

### PDF/Document Notes

| URL | PDFs Found | PDF Chars | Notes |
|-----|-----------|-----------|-------|
| https://www.centralbank.ae/ | 60 | 31,083 | 3 PDFs extracted — CBUAE guidelines and press releases |
| https://www.vara.ae/ | 2 | 37,085 | 2 VARA circulars extracted — travel rule, VASP implementation |
| https://mof.gov.ae/ | 5 | 97,393 | 3 PDFs extracted — procurement manual and newsletters |

---

## AE Category Coverage (after)

| Category | Source | Status |
|----------|--------|--------|
| central_bank | centralbank.ae | active/enabled/good |
| financial_regulator | vara.ae | active/enabled/good (crypto/VASP) |
| financial_regulator | dfsa.ae | active/enabled/good (DIFC free zone) |
| financial_regulator | adgm.com | active/enabled/good (ADGM free zone) |
| finance_ministry | mof.gov.ae | active/enabled/good |
| legal_acts | uaelegislation.gov.ae | active/enabled/good |
| aml | uaefiu.gov.ae | active/enabled/good |
| financial_regulator | sca.gov.ae | limited/disabled (944c SPA, needs adapter) |
| tax | tax.gov.ae | disabled (0c, SPA) |
| legal_acts | elaws.moj.gov.ae | disabled (timeout) |

**Missing:** No enabled source for tax authority or SCA capital markets regulator. No ADGM FSRA-specific URL (covered by ADGM root).

---

## Score Delta

| Metric | Before | After |
|--------|--------|-------|
| AE score | n/a | **82** |
| AE label | n/a | **usable** |
| AE total | 0 | **10** |
| AE enabled | 0 | **7** |
| AE good | 0 | **7** |
| AE low_content | 0 | 1 (SCA) |
| AE failed | 0 | 2 (FTA, elaws) |
| Overall score | 84 | **84** |
| Overall label | usable | **usable** |
| Total sources | 57 | **67** |
| Enabled sources | 32 | **39** |
| Good sources | 43 | **50** |

> Note: Overall score holds at 84 — adding AE (82 usable) with 2 failed sources slightly offsets the gains from the 7 new good enabled sources in the global scoring formula.

---

## Adapter Queue Impact

3 new adapter tasks from AE:
- **MEDIUM**: UAE SCA (sca.gov.ae) — 944c low_content — needs custom adapter targeting announcement/regulation endpoints
- **MEDIUM**: UAE FTA (tax.gov.ae) — 0c failed — needs custom adapter for JS SPA
- **MEDIUM**: UAE e-Laws (elaws.moj.gov.ae) — 0c failed — investigate geo-block/alternate URL

Total adapter queue: **17 MEDIUM priority items** (was 14 before AE pack).

---

## Health Check Result

After AE activation:
- **PASS: 39 / WARN: 0 / SKIP: 28 / FAIL: 0**
- All 7 new AE enabled sources individually PASS.
- No regressions on existing sources.

---

## Remaining Gaps

1. **SCA adapter** (capital markets): sca.gov.ae is a JS SPA — all pages return identical navigation text (~944–1,056c). Need to find and target the `/en/regulatory-framework/` listing page API or use a sitemap-based approach to extract actual regulatory circulars/decisions.

2. **UAE FTA adapter** (tax): tax.gov.ae renders a shell page with 0c extractable content. The FTA publishes circulars, decisions, and guides — these may be accessible via a dedicated publications subpage or API endpoint. Try `https://tax.gov.ae/en/resources/legislation.aspx` or similar.

3. **ADGM FSRA dedicated URL**: The ADGM root covers the entire ADGM hub. The FSRA (Financial Services Regulatory Authority) subpage returns 404 at the tested URL. Check current official FSRA URL under adgm.com to add a dedicated FSRA source.

4. **elaws.moj.gov.ae**: Connection timeout suggests geo-blocking from outside UAE. Monitor whether this changes or find a CDN-accessible mirror.

5. **No dedicated payments/crypto VASP registry**: CBUAE handles payment system oversight; VARA covers Dubai crypto VASPs. A dedicated ADGM FSRA source for crypto activities under ADGM would complement VARA for Abu Dhabi crypto coverage.

---

## Recommended Next Steps

1. **SCA adapter**: Build a source-specific adapter targeting `sca.gov.ae/en/regulatory-framework/regulations.aspx` or the SCA API endpoint for press releases. SCA is the primary capital markets regulator — enabling it would push AE to strong (90+).
2. **UAE FTA**: Test `https://tax.gov.ae/en/resources/legislation.aspx` as an alternate URL. FTA publishes VAT circulars and CT decisions that are highly relevant for RegRadar clients.
3. **ADGM FSRA subpage**: Locate the current official ADGM FSRA regulations page URL and test it as a separate source entry.
4. Run `python run.py coverage-plan --jurisdiction AE` monthly to track improvement.
5. Enabling SCA + FTA would push AE from 82 usable to 90+ strong.
