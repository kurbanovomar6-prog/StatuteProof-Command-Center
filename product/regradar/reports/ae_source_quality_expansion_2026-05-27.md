# UAE Source Quality Audit and Expansion
**Date:** 2026-05-27  
**Jurisdiction:** AE — United Arab Emirates  
**Audit basis:** Individual `run.py test-source` validation per source  

---

## Executive Summary

**Before:** 10 entries (7 active, 3 disabled). Score: 100 (strong) — based on 7 GOOD sources.  
**After:** 12 entries (9 active, 3 disabled). Score: 89 (strong) — 7 confirmed GOOD + 2 new unknown quality.

Two new active sources added: DIFC Laws and Regulations + UAE Ministry of Economy.  
All 7 pre-existing active sources revalidated — all confirmed GOOD, no changes required.  
Three disabled sources remain disabled; FTA notes updated to document all failed URL attempts.

Note: Score shows 89 because 2 new sources have "unknown quality" in audit file (health audit not yet run on them). After `python run.py health`, expected score: 100 (strong) — all 9 sources GOOD.

---

## Part 1 — Revalidation of Existing 7 Active Sources

| Source | URL | Category | HTTP | Chars | Verdict | Decision |
|--------|-----|----------|------|-------|---------|----------|
| Central Bank of UAE (CBUAE) | https://www.centralbank.ae/ | central_bank | 403 | 26,804c | GOOD | **KEEP** |
| Dubai Virtual Assets Regulatory Authority (VARA) | https://www.vara.ae/ | financial_regulator | 200 | 2,705c | GOOD | **KEEP** |
| Dubai Financial Services Authority (DFSA) | https://www.dfsa.ae/ | financial_regulator | 200 | 5,627c | GOOD | **KEEP** |
| Abu Dhabi Global Market (ADGM) | https://www.adgm.com/ | financial_regulator | 200 | 2,135c | GOOD | **KEEP** |
| UAE Ministry of Finance | https://mof.gov.ae/ | finance_ministry | 200 | 13,340c | GOOD | **KEEP** |
| UAE Legislation Portal | https://uaelegislation.gov.ae/ | legal_acts | 403 | 14,808c | GOOD | **KEEP** |
| UAE Financial Intelligence Unit (UAEFIU) | https://www.uaefiu.gov.ae/ | aml | 403 | 2,026c | GOOD | **KEEP** |

All 7 existing active sources confirmed GOOD. HTTP 403 on CBUAE, UAE Legislation Portal, and UAEFIU is expected behavior — Playwright extracts full content from these despite the HTTP response code.

---

## Part 2 — New Candidate Testing Results

### Activated

| Source | URL | HTTP | Chars | Category | Decision |
|--------|-----|------|-------|----------|----------|
| DIFC Laws and Regulations | https://www.difc.ae/business/laws-regulations/ | 200 | 9,150c | legal_database | **ACTIVATED** |
| UAE Ministry of Economy | https://www.moec.gov.ae/en/ | 200 | 14,646c | company_registry | **ACTIVATED** |

### Not Activated — Geo-blocked / Connection failure

| Source | URL | Reason |
|--------|-----|--------|
| UAE Official Gazette | https://uag.gov.ae/ | Connection failure — unreachable outside UAE |
| TDRA (data protection) | https://tdra.gov.ae/en/data-management | Connection timeout — geo-blocked |
| GCA Customs | https://gca.gov.ae/en/ | Connection failure — unreachable outside UAE |
| UAE Government Portal (u.ae) | https://u.ae/en/about-the-uae/digital-uae/government-portals | Connection timeout — Playwright also failed |

### Not Activated — SPA zero-content

| Source | URL | Chars | Reason |
|--------|-----|-------|--------|
| FTA root | https://tax.gov.ae/ | 0–42c | JS SPA renders nothing for external clients |
| FTA /en/default.aspx | https://tax.gov.ae/en/default.aspx | 0c | HTTP 200 but 0c extracted |
| FTA /en/laws.and.guides/laws/ | https://tax.gov.ae/en/laws.and.guides/laws/ | 0c | Unknown status, 0c extracted |
| SCA root | https://www.sca.gov.ae/ | 944c | Navigation-only app-shell |
| SCA /en/regulatory-framework/ | https://www.sca.gov.ae/en/regulatory-framework/ | 1,056c | Navigation-only, identical to root |
| VARA /news-events | https://www.vara.ae/en/news-events/ | 62c | HTTP 404, 0c content |

### Not Activated — Duplicate of existing source

| Source | URL | Chars | Reason |
|--------|-----|-------|--------|
| FSRA via adgm.com/fsra | https://www.adgm.com/fsra | 2,742c | Content overlap with active adgm.com entry |
| ADGM Registration Authority | https://rara.adgm.com/ | 1,283c | SPA 404; content is sub-scope of active adgm.com |

### Not Activated — Connection failure (subdomain)

| Source | URL | Reason |
|--------|-----|--------|
| FSRA (direct subdomain) | https://www.fsra.adgm.com/ | Complete connection failure |
| DIFC incorporating sub-page | https://www.difc.ae/business/setting-up/incorporating/ | HTTP 404, 0c |
| CBUAE insurance sub-page | https://www.centralbank.ae/en/regulation/insurance | 391c — too thin |
| CBUAE payment systems sub-page | https://www.centralbank.ae/en/regulation/payment-systems | 391c — too thin |

---

## Part 3 — Active Source Table (Post-Audit, All 9 Sources)

| Source | URL | Category | HTTP | Chars | Quality |
|--------|-----|----------|------|-------|---------|
| Central Bank of UAE (CBUAE) | https://www.centralbank.ae/ | central_bank | 403 | 26,804c | GOOD |
| Dubai Virtual Assets Regulatory Authority (VARA) | https://www.vara.ae/ | financial_regulator | 200 | 2,705c | GOOD |
| Dubai Financial Services Authority (DFSA) | https://www.dfsa.ae/ | financial_regulator | 200 | 5,627c | GOOD |
| Abu Dhabi Global Market (ADGM) | https://www.adgm.com/ | financial_regulator | 200 | 2,135c | GOOD |
| UAE Ministry of Finance | https://mof.gov.ae/ | finance_ministry | 200 | 13,340c | GOOD |
| UAE Legislation Portal | https://uaelegislation.gov.ae/ | legal_acts | 403 | 14,808c | GOOD |
| UAE Financial Intelligence Unit (UAEFIU) | https://www.uaefiu.gov.ae/ | aml | 403 | 2,026c | GOOD |
| DIFC Laws and Regulations | https://www.difc.ae/business/laws-regulations/ | legal_database | 200 | 9,150c | GOOD* |
| UAE Ministry of Economy | https://www.moec.gov.ae/en/ | company_registry | 200 | 14,646c | GOOD* |

\* Tested GOOD individually via test-source. Shows "unknown quality" in coverage score until `python run.py health` is run (same pattern as HK sources). Expected score after health: 100 (strong).

---

## Part 4 — Categories Covered vs Missing

### Covered (9 active sources across 8 categories)

| Category | Source |
|----------|--------|
| central_bank / banking_regulator | CBUAE |
| financial_regulator / VARA / crypto_vasp | VARA, DFSA, ADGM |
| finance_ministry | UAE Ministry of Finance |
| legal_acts / legislation | UAE Legislation Portal |
| legal_database / DIFC | DIFC Laws and Regulations *(new)* |
| aml / CFT | UAEFIU |
| company_registry / government | UAE Ministry of Economy *(new)* |

### Missing / Blocked

| Category | Status | Blocker |
|----------|--------|---------|
| tax / FTA | disabled — SPA zero-content | FTA renders nothing for non-UAE IP clients |
| securities / capital markets (SCA) | disabled — navigation SPA | SCA app-shell only, no regulatory content extractable |
| official_gazette | disabled — geo-blocked | uag.gov.ae unreachable outside UAE |
| data_protection / TDRA | disabled — geo-blocked | tdra.gov.ae connection timeout outside UAE |
| customs / GCA | disabled — geo-blocked | gca.gov.ae unreachable outside UAE |
| insurance_regulator (dedicated) | partial | CBUAE covers insurance via central bank; no standalone IA source |
| ADGM FSRA (dedicated) | partial | ADGM main site covers FSRA; dedicated fsra.adgm.com fails |

---

## Part 5 — Commercial Value of New Sources

**DIFC Laws and Regulations:**  
The Dubai International Financial Centre is the primary international financial free zone in the region. DIFC has its own legal system based on English common law with its own courts and legislation. The DIFC Laws page covers the full corpus of DIFC legislation including the DIFC Law (No. 1 of 2004), Financial Services Regulations, Employment Law, Companies Law, Insolvency Law, and Data Protection Law. Any legal/compliance team advising clients operating within DIFC needs to monitor this source. 9,150c of genuine regulatory content extracted.

**UAE Ministry of Economy:**  
The federal MoECT regulates commercial activities outside the free zones, including: commercial registries, trade licence policy, competition regulation, consumer protection, foreign ownership rules, and intellectual property. For B2B companies expanding into mainland UAE (not DIFC/ADGM free zones), MoECT is the primary federal commercial regulator. 14,646c of genuine policy and regulatory content extracted.

---

## Part 6 — Known Limitations

1. **FTA is fully blocked.** Tax monitoring for UAE mainland is not possible with current extraction. FTA renders an empty JS shell for all external clients. All three tested URL variants return 0c. Needs a UAE-IP VPS adapter or official API endpoint if FTA publishes one.

2. **SCA remains navigation-only.** Securities and Commodities Authority is important for capital markets monitoring but the website is a pure SPA returning identical 944–1,056c navigation text on all pages. Cannot differentiate regulatory circular content from navigation. Needs a dedicated adapter targeting the SCA publications API.

3. **Geo-blocked sources (Official Gazette, TDRA, GCA) cannot be activated from outside UAE.** A UAE-IP deployment node would unlock these three sources.

4. **New sources show score 89 instead of 100.** The 2 new sources have no entry in `source_audit_2026-05-25.json` so coverage scoring shows them as "unknown quality." Run `python run.py health` to register them and update the score to reflect actual GOOD quality.

5. **ADGM/DFSA overlap.** ADGM main site and DFSA are both active. ADGM covers FSRA regulatory activities in addition to registration/company matters. DFSA covers DIFC financial services. These are complementary, not duplicate — different financial free zones with different regulatory bodies.

---

## Files Modified

| File | Action |
|------|--------|
| `sources.json` | Added 2 new active AE entries (DIFC Laws, UAE Ministry of Economy); updated FTA disabled notes |
| `reports/ae_source_quality_expansion_2026-05-27.md` | Created — this file |
