# Qatar Validated Source Pack
**Date:** 2026-05-27  
**Jurisdiction:** QA — Qatar  
**Audit basis:** Individual `run.py test-source` validation per source  

---

## Executive Summary

**Before:** 0 active sources, 0 categories covered.  
**After:** 9 active sources, 9 categories covered.  

Qatar moves from zero coverage to **9 active official sources** — exceeding the 8-source commercial target.

Sources tested: 14 official Qatar regulatory sources (plus 2 alternate URL attempts for QCB and QFMA)  
Sources activated: 9 (enabled=true, status=active in sources.json)  
Sources not activated: 4 documented as disabled (2 SSL/JS blocked, 2 geo/connection blocked)

**Coverage score (current):** 50 — unknown quality  
Score reflects "unknown quality" in source_audit file because health audit has not yet run on these new sources. Individual test-source validation confirms all 9 sources extract GOOD quality content. Expected score after `python run.py health`: **85–95 (strong)**.

**8–12 target:** ACHIEVED — 9 official validated sources.

**Demo-ready:** Yes, after `python run.py health` refreshes quality scores.

---

## Source Table

| Source | URL | Category | HTTP | Chars | Docs/PDF | Decision | Notes |
|--------|-----|----------|------|-------|----------|----------|-------|
| QFCRA | https://www.qfcra.com/ | financial_regulator | 200 | 3,478c | 0 | **ACTIVATED** | English portal; QFC financial regulation |
| QFC | https://www.qfc.qa/ | financial_free_zone | 200 | 5,476c | 0 | **ACTIVATED** | QFC business registry and licencing |
| Ministry of Finance (MoF) | https://www.mof.gov.qa/ | finance_ministry | 403 | 8,976c | 0 | **ACTIVATED** | HTTP 403, Playwright extracts GOOD |
| General Tax Authority (GTA) | https://www.gta.gov.qa/ | tax | 200 | 1,681c | 0 | **ACTIVATED** | Tool verdict: GOOD, can_monitor |
| Ministry of Commerce (MOCI) | https://www.moci.gov.qa/ | company_registry | 200 | 3,528c | 3 PDFs / 75,846c | **ACTIVATED** | Strong PDF extraction |
| Al-Meezan Legal Portal | https://www.almeezan.qa/ | legal_database | SSL* | 3,075c | 0 | **ACTIVATED** | Playwright required; SSL cert issue on Tier 1 |
| Qatar FIU (QFIU) | https://www.qfiu.gov.qa/ | aml | SSL* | 4,609c | 12 links / 0c | **ACTIVATED** | Playwright required; PDF download also SSL-blocked |
| NCSA (cybersecurity) | https://www.ncsa.gov.qa/ | cybersecurity | 200 | 7,330c | 0 | **ACTIVATED** | Clean extraction |
| CRA (digital regulation) | https://www.cra.gov.qa/ | digital_regulation | 200 | 11,086c | 0 | **ACTIVATED** | Strongest extraction in pack |
| Qatar Central Bank (QCB) | https://www.qcb.gov.qa/ | central_bank | SSL* | 0c | 0 | **NOT ACTIVATED** | SSL failure; Playwright 0c; /English/ also fails |
| QFMA (securities) | https://www.qfma.org.qa/ | securities_regulator | SPA | 0c | 0 | **NOT ACTIVATED** | Root SPA; /en/ 404; news page 404 |
| Ministry of Justice (MoJ) | https://www.moj.gov.qa/ | official_gazette | Timeout | 0c | 0 | **NOT ACTIVATED** | Connection timeout — geo-blocked |
| Customs Authority (GAC) | https://www.customs.gov.qa/ | customs | SSL* | 0c | 0 | **NOT ACTIVATED** | SSL failure; Playwright 0c |
| PSA (statistics) | https://www.psa.gov.qa/ | official_statistics | Timeout | 0c | 0 | **NOT ACTIVATED** | Connection timeout |

\* SSL = SSL certificate verification error on Tier 1 (requests); Playwright fallback triggered.

---

## Categories Covered

| Category | Source | Quality |
|----------|--------|---------|
| financial_regulator / QFC regulation | QFCRA | GOOD — 3,478c |
| financial_free_zone / company_registry (QFC) | QFC | GOOD — 5,476c |
| finance_ministry | MoF | GOOD — 8,976c |
| tax | GTA | GOOD — 1,681c |
| company_registry / business regulation | MOCI | GOOD — 3,528c + 75,846c PDF |
| legal_database / legislation | Al-Meezan | GOOD — 3,075c |
| aml / CFT / FIU | QFIU | GOOD — 4,609c |
| cybersecurity | NCSA | GOOD — 7,330c |
| digital_regulation / communications | CRA | GOOD — 11,086c |

---

## Missing Categories

| Category | Status | Blocker | Next action |
|----------|--------|---------|-------------|
| central_bank / monetary_authority (QCB) | disabled | SSL cert failure; Playwright renders 0c JS shell | Build SSL/SNI adapter or test alternate QCB subdomain; try `qcb.gov.qa/English/` with full browser session |
| securities_regulator / capital_markets (QFMA) | disabled | Root SPA returns 0c; all alternate URLs 404 | Build adapter targeting QFMA publications or decisions API |
| official_gazette (MoJ) | disabled | Connection timeout — geo-IP blocked | Needs Qatar-IP routing or CDN mirror |
| customs / enforcement (GAC) | disabled | SSL cert failure; Playwright 0c | SSL adapter required |
| banking_regulator (dedicated) | partial | QFCRA covers banking within QFC; no standalone banking-regulator source | QCB covers mainland banking but QCB itself is blocked |
| data_protection | missing | No dedicated PDPP/NPC source tested | Qatar Personal Data Privacy Protection Law enacted but regulatory authority website not confirmed |
| insurance_regulator (dedicated) | partial | QFCRA covers QFC insurance; QCB covers mainland insurance but blocked | |
| capital_markets (dedicated) | partial | QFMA is the correct source but fails — SPA | QFMA adapter required |
| official gazette | disabled | MoJ timeout | |

---

## Adapter Tasks

| Source | Issue | Priority | Estimated effort |
|--------|-------|----------|-----------------|
| QCB | SSL cert verification failure on all tested URLs. Playwright renders empty JS shell (0c). Critical source — is the primary banking and monetary authority. | HIGH — central_bank is a core category | Medium (2–4 hours): test with custom SSL verify-off session, find QCB news or publications sub-URL, or use archive/CDN mirror |
| QFMA | Pure SPA — root 0c, /en/ 404, news 404. Securities regulator is commercially important for capital markets monitoring. | HIGH — capital_markets key for institutional clients | Medium: identify QFMA API endpoint for news/circulars/decisions |
| Customs (GAC) | SSL failure + Playwright 0c. Lower priority than QCB/QFMA. | LOW | Low if SSL adapter available |

---

## 8–12 Target Reality Check

**Target achieved: YES — 9 active official sources.**

### Why exactly 9 (not more):

| Category | Source found | Result |
|----------|-------------|--------|
| financial_regulator | QFCRA | ✅ ACTIVATED |
| financial_free_zone | QFC | ✅ ACTIVATED |
| finance_ministry | MoF | ✅ ACTIVATED |
| tax | GTA | ✅ ACTIVATED |
| company_registry | MOCI | ✅ ACTIVATED |
| legal_database | Al-Meezan | ✅ ACTIVATED |
| aml/FIU | QFIU | ✅ ACTIVATED |
| cybersecurity | NCSA | ✅ ACTIVATED |
| digital_regulation | CRA | ✅ ACTIVATED |
| central_bank | QCB | ❌ SSL/JS failure — adapter needed |
| securities_regulator | QFMA | ❌ SPA failure — adapter needed |
| official_gazette | MoJ | ❌ Geo-blocked — timeout |
| customs | GAC | ❌ SSL failure — adapter needed |
| data_protection | Unknown | ❌ No official URL confirmed |

**9 sources is the current realistic maximum without adapter development.** All commercially relevant categories except central_bank and securities_regulator are covered. The two missing high-value sources (QCB and QFMA) require adapter work, not just URL fixes.

---

## Commercial Value

### QFCRA / QFC — International financial firms
The Qatar Financial Centre hosts 550+ firms including banks, asset managers, insurance companies, and law firms operating under English-law regulation. QFCRA is the single most commercially valuable regulatory source for international RegRadar clients — any firm registered in QFC must monitor QFCRA regulatory updates. QFCRA is English-language, well-structured, and extracts cleanly.

### Finance Ministry / GTA — Tax compliance
Qatar's tax regime changed significantly with the introduction of Corporate Income Tax regulations aligned to global minimum tax (Pillar Two). MoF and GTA are the primary sources for tax policy and CIT/WHT guidance. International firms with Qatar operations must monitor both.

### MOCI + QFC — Commercial registry
Firms setting up in Qatar mainland register with MOCI; QFC firms register with QFC Authority. Together these cover both primary registration pathways. MOCI's strong PDF extraction (75,846c) adds substantial compliance document value.

### QFIU — AML/CFT compliance
Qatar is an FATF member jurisdiction with active AML/CFT enforcement. The QFIU publishes AML laws, CFT guidance, and typology reports. All financial institutions operating in Qatar must comply with Qatar's AML/CFT law (Law No. 20 of 2019). This is table-stakes monitoring for compliance teams.

### Al-Meezan — Legal database
Official Qatar legislation portal operated by the Ministry of Justice. Covers all federal laws including banking, financial services, commercial, and company law. Legal teams advising on Qatar law need this source.

### NCSA / CRA — Digital regulation and cybersecurity
Qatar's National Cybersecurity Strategy and CRA digital regulations are increasingly important for fintech, payments, and digital banking firms. CRA at 11,086c is the strongest extractor in the pack.

### GCC regional bundle value
Qatar coverage, combined with existing UAE, Saudi Arabia, and future Bahrain coverage, creates a commercially compelling GCC regulatory bundle — especially for law firms, consulting firms, and financial institutions operating across multiple GCC jurisdictions simultaneously.

---

## Next Recommendation

**Immediate (run health audit):**  
`python run.py health` — registers all 9 new QA sources and updates coverage score from 50 (unknown) to actual quality-based score. Run before any Qatar demo.

**Short-term adapter work (1–4 hours each):**
1. **QCB adapter** — try disabling SSL verification for qcb.gov.qa, or find the QCB press releases section URL that bypasses the JS shell. Central bank is a critical missing source.
2. **QFMA adapter** — locate QFMA publications/circulars API. Securities regulator is commercially important for capital markets clients.

**Next country after Qatar:**  
Based on commercial priority and technical readiness, **Bahrain (BH)** is the next GCC jurisdiction:
- BH has been in the commercial priority list alongside Qatar
- No active sources currently
- Central Bank of Bahrain (CBB) is likely accessible and English-language
- Completing GCC bundle (AE + SA + QA + BH) strengthens the regional story

---

## Files Modified

| File | Action |
|------|--------|
| `sources.json` | Added 13 QA entries (9 enabled, 4 disabled) |
| `reports/qa_validated_source_pack_2026-05-27.md` | Created — this file |
