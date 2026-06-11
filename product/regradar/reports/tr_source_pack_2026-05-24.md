# Turkey Source Pack — 2026-05-24

## Summary

**Before:** 0 TR sources, TR not in coverage
**After:** 9 TR sources (7 enabled + 2 mapped), score **100 (strong)**
**Overall:** 81 usable → **84 usable** (57 total, 32 enabled, 43 good)

All 7 enabled TR sources extract good content and pass health checks.
No TR sources failed. No adapter needed for any enabled TR source.

---

## Sources Researched

| URL | Result | Chars | Notes |
|-----|--------|-------|-------|
| https://www.tcmb.gov.tr/ | GOOD | 4,988 | Central Bank — Playwright required (JS-rendered); PDFs also work (37,913c) |
| https://www.bddk.org.tr/ | GOOD | 2,638 | Banking regulator — Tier 1 SSL cert fails, Playwright succeeds |
| https://masak.hmb.gov.tr/ | GOOD | 14,259 | AML/financial crimes — best extractor: beautifulsoup |
| https://www.spk.gov.tr/ | GOOD | 2,056 | Capital Markets Board — Tier 1 SSL cert fails, Playwright succeeds |
| https://www.resmigazete.gov.tr/ | GOOD | 43,875 | Official Gazette — best extractor: trafilatura; excellent content |
| https://www.gib.gov.tr/ | GOOD | 3,238 | Revenue Administration — Playwright required |
| https://www.hmb.gov.tr/ | GOOD | 12,085 | Ministry of Treasury — Playwright required; PDF also yields 291,237c |
| https://www.kvkk.gov.tr/ | GOOD | 1,835 | Data Protection Authority — fintech/payment provider relevant |
| https://www.rekabet.gov.tr/ | GOOD | 2,248 | Competition Authority — secondary relevance to financial regulation |

---

## Sources Added to sources.json

### Enabled (7)

| Name | URL | Category | Chars | Status |
|------|-----|----------|-------|--------|
| Central Bank of the Republic of Türkiye | https://www.tcmb.gov.tr/ | central_bank | 4,988 | active |
| Banking Regulation and Supervision Agency of Türkiye (BDDK) | https://www.bddk.org.tr/ | financial_regulator | 2,638 | active |
| MASAK — Financial Crimes Investigation Board of Türkiye | https://masak.hmb.gov.tr/ | aml | 14,259 | active |
| Capital Markets Board of Türkiye (SPK) | https://www.spk.gov.tr/ | financial_regulator | 2,056 | active |
| Official Gazette of Türkiye (Resmî Gazete) | https://www.resmigazete.gov.tr/ | legal_acts | 43,875 | active |
| Revenue Administration of Türkiye (GİB) | https://www.gib.gov.tr/ | tax | 3,238 | active |
| Ministry of Treasury and Finance of Türkiye | https://www.hmb.gov.tr/ | finance_ministry | 12,085 | active |

### Mapped / Disabled (2)

| Name | URL | Category | Chars | Reason |
|------|-----|----------|-------|--------|
| Personal Data Protection Authority of Türkiye (KVKK) | https://www.kvkk.gov.tr/ | financial_regulator | 1,835 | Tested good. Relevant for fintech/payment data compliance. Enable when TR fintech coverage is prioritised. |
| Competition Authority of Türkiye (Rekabet Kurumu) | https://www.rekabet.gov.tr/ | financial_regulator | 2,248 | Tested good. Secondary relevance — fintech/banking M&A and market practice enforcement. |

---

## Sources Skipped

None. All 9 tested candidates returned GOOD quality (≥1,000c).

---

## test-source Results

| URL | HTTP | Chars | Extractor | Quality | Verdict |
|-----|------|-------|-----------|---------|---------|
| https://www.tcmb.gov.tr/ | 200 | 4,988 | beautifulsoup | good | can_monitor |
| https://www.bddk.org.tr/ | unknown (SSL → Playwright) | 2,638 | readability | good | can_monitor |
| https://masak.hmb.gov.tr/ | 200 | 14,259 | beautifulsoup | good | can_monitor |
| https://www.spk.gov.tr/ | unknown (SSL → Playwright) | 2,056 | beautifulsoup | good | can_monitor |
| https://www.resmigazete.gov.tr/ | 200 | 43,875 | trafilatura | good | can_monitor |
| https://www.gib.gov.tr/ | 200 | 3,238 | beautifulsoup | good | can_monitor |
| https://www.hmb.gov.tr/ | 200 | 12,085 | beautifulsoup | good | can_monitor |
| https://www.kvkk.gov.tr/ | 200 | 1,835 | beautifulsoup | good | can_monitor |
| https://www.rekabet.gov.tr/ | 200 | 2,248 | beautifulsoup | good | can_monitor |

### PDF/Document Notes

| URL | PDFs Found | PDF Chars | Notes |
|-----|-----------|-----------|-------|
| https://www.tcmb.gov.tr/ | 6 | 37,913 | 3 PDFs extracted (pypdf) — recent TCMB presentations |
| https://www.hmb.gov.tr/ | 1 | 291,237 | PDF extraction excellent (291K chars) |
| https://www.bddk.org.tr/ | 1 | 0 | PDF download blocked by SSL |
| https://www.spk.gov.tr/ | 4 | 0 | PDFs blocked by SSL (Tier 1 download fails) |
| https://www.resmigazete.gov.tr/ | 1 | 0 | Daily gazette PDF too large (>10MB limit) |

---

## TR Category Coverage (after)

| Category | Source | Status |
|----------|--------|--------|
| central_bank | tcmb.gov.tr | active/enabled/good |
| financial_regulator | bddk.org.tr | active/enabled/good |
| aml | masak.hmb.gov.tr | active/enabled/good |
| financial_regulator | spk.gov.tr | active/enabled/good |
| legal_acts | resmigazete.gov.tr | active/enabled/good |
| tax | gib.gov.tr | active/enabled/good |
| finance_ministry | hmb.gov.tr | active/enabled/good |
| financial_regulator | kvkk.gov.tr | mapped/disabled (tested good) |
| financial_regulator | rekabet.gov.tr | mapped/disabled (tested good) |

**Missing:** No separate payments/fintech regulator URL — covered by TCMB and BDDK.

---

## Score Delta

| Metric | Before | After |
|--------|--------|-------|
| TR score | n/a | **100** |
| TR label | n/a | **strong** |
| TR total | 0 | **9** |
| TR enabled | 0 | **7** |
| TR good | 0 | **9** |
| Overall score | 81 | **84** |
| Overall label | usable | **usable** |
| Total sources | 48 | **57** |
| Enabled sources | 25 | **32** |
| Good sources | 34 | **43** |

---

## Adapter Queue Impact

No new adapter tasks created by TR sources — all 9 TR sources extract good content without adapters.
Total adapter queue remains: **14 MEDIUM priority items** (same as before TR pack).

TR sources that use Playwright fallback (BDDK, SPK — SSL cert fails at Tier 1):
- Not adapter issues — Playwright handles them reliably.
- PDF download from these domains is blocked by SSL; HTML extraction is sufficient.

---

## Health Check Result

After TR activation:
- **PASS: 32 / WARN: 0 / SKIP: 25 / FAIL: 0**
- All 7 new TR enabled sources individually PASS.
- No regressions on existing sources.

---

## Remaining Gaps

1. **BDDK/SPK PDF extraction**: SSL certificate prevents direct PDF downloads from these domains. PDFs are accessible via Playwright browser session but not via requests. A custom adapter using Playwright-based PDF download could resolve this.

2. **Resmi Gazete daily PDF**: The official gazette PDF is >10MB — file size limit reached. The HTML extraction (43,875c) is excellent and sufficient for monitoring.

3. **KVKK/Rekabet**: Both tested good and are ready for activation. Enable when TR fintech/competition coverage is explicitly prioritised.

4. **No dedicated payments/fintech source**: Turkey does not have a separate official payments regulator. TCMB and BDDK jointly cover payment system oversight.

---

## Recommended Next Steps

1. **Enable KVKK** when Turkey fintech/payment data compliance monitoring is needed.
2. **Enable Rekabet** when Turkey competition/M&A monitoring for banking/fintech is needed.
3. **SPK/BDDK PDF adapter**: Build a Playwright-based PDF download adapter for `.spk.gov.tr` and `.bddk.org.tr` to access regulatory circulars directly.
4. Run `python run.py coverage-plan --jurisdiction TR` monthly to track improvement.
