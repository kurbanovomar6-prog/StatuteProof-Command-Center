# Bahrain Validated Source Pack
**Date:** 2026-05-27  
**Jurisdiction:** BH — Bahrain  
**Audit basis:** Individual `run.py test-source` validation per source  

---

## Executive Summary

**Before:** 0 BH sources (0 enabled).  
**After:** 14 BH entries (12 enabled, 2 disabled).  

Bahrain moves from zero coverage to **12 active official sources**, completing the GCC4 commercial bundle: UAE + Saudi Arabia + Qatar + Bahrain.

Sources tested: 17 official Bahrain regulatory URLs (+ alternate AML domains)  
Sources activated: 12 (enabled=true, status=active in sources.json)  
Sources not activated: 2 documented as disabled (3 AML domains dead/blocked, 1 MoJ limited)  

**Coverage score (current):** 50 — unknown quality  
Score reflects "unknown quality" because health audit has not run on new sources. Individual validation confirms 10 sources extract GOOD text content; TRA and iGA are PDF-primary sources with low HTML text but strong document extraction. Expected score after `python run.py health`: **85–95 (strong)** if PDF-primary quality is reflected correctly.

**8–12 target:** ACHIEVED — 12 official validated sources.  

**Demo-ready:** Yes for source-backed demos, with AML/FIU and cybersecurity gaps disclosed. Run `python run.py health` before relying on coverage scores.

---

## Source Table

| Source | URL | Category | HTTP | Chars | Docs/PDF | Decision | Notes |
|--------|-----|----------|------|-------|----------|----------|-------|
| Central Bank of Bahrain (CBB) | https://www.cbb.gov.bh/ | central_bank | 200 | 2,972c | 4 PDFs / 10,496c | **ACTIVATED** | Primary banking, payments, insurance, capital markets regulator |
| CBB — Fintech & Innovation | https://www.cbb.gov.bh/fintech/ | fintech | 200 | 24,241c | 6 PDFs / 37,873c | **ACTIVATED** | Sandbox, open banking, crypto licensing; distinct from CBB root |
| Bahrain Bourse | https://www.bahrainbourse.com/ | capital_markets | 200 | 10,090c (Playwright) | 9 PDFs / 29,782c | **ACTIVATED** | Official stock exchange and securities market |
| Ministry of Finance and National Economy (MoFNE) | https://www.mofne.gov.bh/ | finance_ministry | 200 | 3,086c | 2 PDFs / 36,381c | **ACTIVATED** | Fiscal policy, budget, economic policy |
| National Bureau for Revenue (NBR) | https://www.nbr.gov.bh/ | tax | 200 | 5,093c (Playwright) | 1 PDF / 34,523c | **ACTIVATED** | VAT authority; mandatory for all VAT-registered businesses |
| Legislation and Legal Opinion Commission (LLOC) | https://www.lloc.gov.bh/ | legal_database | 200 | 2,358c | 12 PDFs / 5,003c | **ACTIVATED** | Official legislation portal; K-series PDFs are gazette entries |
| Personal Data Protection Authority (PDPA) | https://www.pdp.gov.bh/ | data_protection | 200 | 3,633c | 2 PDFs / 19,699c | **ACTIVATED** | Enforces PDPL; critical for fintech, banks, digital firms |
| Bahrain Customs Affairs | https://www.customs.gov.bh/ | customs | 200 | 1,802c | 1 PDF / 9,485c | **ACTIVATED** | Trade compliance and customs enforcement |
| Sijilat — Commercial Registration Portal | https://www.sijilat.bh/ | company_registry | 200 | 3,554c (Playwright) | 0 | **ACTIVATED** | Official company registration and CR data portal |
| Ministry of Industry and Commerce (MOIC) | https://www.moic.gov.bh/ | commerce | 200 | 1,104c | 1 PDF / 34,492c | **ACTIVATED** | Trade licensing, consumer protection, regulatory policy |
| Telecommunications Regulatory Authority (TRA) | https://www.tra.org.bh/ | digital_regulation | 200 | 746c (PDF-primary) | 2 PDFs / 84,352c | **ACTIVATED** | Telecoms, digital services, data localisation regulation |
| Information & eGovernment Authority (iGA) | https://www.iga.gov.bh/ | digital_government | 200 | 323c (PDF-primary) | 3 PDFs / 195,616c | **ACTIVATED** | AI regulation framework, digital governance policy |
| Bahrain FIU (fiu.gov.bh) | https://www.fiu.gov.bh/ | aml | DNS FAILURE | 0c | 0 | **NOT ACTIVATED** | DNS does not resolve |
| Ministry of Justice (moj.gov.bh) | https://www.moj.gov.bh/ | official_gazette | 200 | 1,460c | judiciary PDFs | **NOT ACTIVATED** | PDF content is court procedures, not gazette/legislation; LLOC preferred |

### Additional AML domains tested (all failed)

| Domain | Failure type |
|--------|-------------|
| https://www.fid.gov.bh/ | DNS failure — does not resolve |
| https://www.amlu.gov.bh/ | Connection timeout — geo-blocked or inactive |
| https://nac.gov.bh/ | DNS failure — does not resolve |

### Other candidates tested and rejected

| Source | URL | Chars | Reason |
|--------|-----|-------|--------|
| Bahrain EDB | https://www.bahrainedb.com/ | 596c LOW_CONTENT, 0 PDFs | Marketing content; below threshold |
| Tender Board | https://www.tenderboard.gov.bh/ | 1,217c (Playwright), PDFs are Vision2030 | Procurement-only; not regulatory compliance |
| legalaffairs.gov.bh | https://www.legalaffairs.gov.bh/ | SSL hostname mismatch; Playwright failed | SSL error on all URLs |
| Ministry of Justice (English) | https://www.moj.gov.bh/en/pages/default.aspx | 188c LOW_CONTENT | Below threshold on English path |

---

## Categories Covered

| Category | Source | Quality |
|----------|--------|---------|
| central_bank / monetary authority | CBB | GOOD — 2,972c + 10,496c PDF |
| banking_regulator | CBB | GOOD — covers all CBB-licensed banks |
| payments / open banking | CBB | GOOD — CBB is payments regulator for Bahrain |
| insurance_regulator | CBB | GOOD — CBB regulates insurance sector |
| capital_markets / securities | Bahrain Bourse | GOOD — 10,090c + 29,782c PDF |
| fintech / crypto / digital banking | CBB Fintech | GOOD — 24,241c + 37,873c PDF (strongest single-page) |
| finance_ministry | MoFNE | GOOD — 3,086c + 36,381c PDF |
| tax (VAT) | NBR | GOOD — 5,093c + 34,523c PDF |
| legal_database / official_gazette | LLOC | GOOD — 2,358c + K-series gazette PDFs |
| data_protection | PDPA | GOOD — 3,633c + 19,699c (regulations.pdf) |
| customs | Bahrain Customs Affairs | GOOD — 1,802c + 9,485c PDF |
| company_registry | Sijilat | GOOD — 3,554c |
| commerce / trade regulation | MOIC | GOOD — 1,104c + 34,492c PDF |
| digital_regulation / telecoms | TRA | PDF-primary — 84,352c |
| digital_government / AI regulation | iGA | PDF-primary — 195,616c |

---

## Missing Categories

| Category | Status | Reason | Priority |
|----------|--------|--------|----------|
| AML / FIU (standalone) | disabled — all domains dead | fiu.gov.bh, fid.gov.bh DNS failure; amlu.gov.bh connection timeout | HIGH — AML is table-stakes. CBB partially covers financial-sector AML supervision. |
| official_gazette (dedicated) | partial — LLOC covers it | LLOC K-series PDFs are gazette entries; MoJ gazette-specific pages failed | LOW — LLOC serves as de-facto gazette source |
| securities_regulator (CBB) | partial — CBB covers it | CBB regulates capital markets via Volume 6 of CBB Rulebook; no separate securities commission | LOW — Bahrain has unified CBB regulation |
| insurance_regulator (dedicated) | partial — CBB covers it | CBB regulates insurance sector; no dedicated insurance authority | LOW — Bahrain unified model |
| banking_regulator (dedicated) | partial — CBB covers it | CBB is the banking regulator | LOW — unified regulator |
| public_consultations | not tested | No confirmed official Bahrain public consultations portal | LOW |
| cybersecurity (NCSC) | not tested | Bahrain NCSC may exist; not in initial source list | MEDIUM |

---

## Adapter Tasks

| Source | Issue | Priority | Estimated effort |
|--------|-------|----------|-----------------|
| TRA | HTML 746c (below 1,000c threshold); PDF-primary. A lightweight SPA/rendering adapter could improve HTML extraction to 2,000–5,000c. | LOW — PDFs are strong at 84,352c | Low (1–2 hours) |
| iGA | HTML 323c. PDF-primary with 195,616c. HTML adapter could surface news/announcements between PDF publications. | LOW — PDFs are very strong | Low (1–2 hours) |
| Bahrain AML/FIU | All known domains dead or blocked. No standalone AML source accessible. | HIGH — AML category missing | Hard: requires domain discovery or alternative authority URL |

---

## 8–12 Target Reality Check

**Target achieved: YES — 12 active official sources.**

| Category | Source | Result |
|----------|--------|--------|
| central_bank | CBB | ✅ ACTIVE (2,972c GOOD) |
| banking_regulator | CBB | ✅ ACTIVE (unified regulator) |
| fintech / crypto / sandbox | CBB Fintech | ✅ ACTIVE (24,241c GOOD — strongest) |
| capital_markets / securities | Bahrain Bourse | ✅ ACTIVE (10,090c GOOD) |
| finance_ministry | MoFNE | ✅ ACTIVE (3,086c GOOD) |
| tax (VAT) | NBR | ✅ ACTIVE (5,093c GOOD) |
| legal_database / gazette | LLOC | ✅ ACTIVE (2,358c GOOD + K-series gazette) |
| data_protection | PDPA | ✅ ACTIVE (3,633c GOOD) |
| customs | Bahrain Customs Affairs | ✅ ACTIVE (1,802c GOOD) |
| company_registry | Sijilat | ✅ ACTIVE (3,554c GOOD) |
| commerce | MOIC | ✅ ACTIVE (1,104c + PDF) |
| digital_regulation | TRA | ✅ ACTIVE (PDF-primary: 84,352c) |
| digital_government / AI | iGA | ✅ ACTIVE (PDF-primary: 195,616c) |
| AML / FIU | — | ❌ All domains dead/blocked |

**12 sources is the current realistic maximum from the tested official URLs.** Most commercially important Bahrain financial, tax, company, data protection, legal, and digital-policy categories are covered. The important open gaps are standalone AML/FIU and a confirmed cybersecurity/NCSC source. CBB AML supervision content is accessible via the CBB root, but it is not a substitute for a dedicated FIU source.

Note on CBB consolidation: Bahrain uses a unified regulatory model where CBB acts as central_bank + banking_regulator + payments_regulator + insurance_regulator + capital_markets_regulator. The CBB root and CBB fintech entries together cover all these sub-categories. This is accurate — Bahrain does not have separate authorities for banking, insurance, and capital markets like UAE's CBUAE/SCA/IA split.

---

## Commercial Value

### CBB — The core GCC financial regulator
The Central Bank of Bahrain is one of the most progressive financial regulators in the GCC, operating a unified regulatory framework for banking, insurance, capital markets, payments, and fintech. Any firm operating in Bahrain's financial sector must monitor CBB regulatory updates, rulebook changes, and circular publications. CBB's fintech regulatory sandbox (FinHub 973) has attracted regional and international firms, making CBB monitoring commercially essential for fintech compliance teams.

### CBB Fintech / Crypto — Leading GCC digital assets regulator
Bahrain was the first GCC country to introduce a full crypto-asset regulatory framework (2019). The CBB's Volume 8 (Crypto-asset Module) governs all crypto exchange and custodian activities in Bahrain. Bahrain-licensed crypto exchanges include Rain Financial and others. Any compliance team working on crypto/digital assets in the GCC must monitor CBB fintech publications — commercially critical for digital asset firms, payment institutions, and fintech investors.

### Bahrain Bourse — Capital markets and listed company compliance
The Bahrain Bourse is the official securities market. Listed companies, investment managers, and securities brokers in Bahrain must monitor exchange rules, disclosure requirements, and market circulars. Combined with CBB capital markets supervision, this covers the full capital markets compliance stack.

### NBR — VAT compliance
Bahrain introduced VAT at 5% in 2019, raised to 10% in 2022. NBR is the mandatory monitoring source for all VAT-registered entities in Bahrain. With Bahrain's VAT exemptions and special regimes relevant to financial services, tax advisory teams working on Bahrain engagements must monitor NBR.

### PDPA — Data protection compliance
Bahrain's Personal Data Protection Law (PDPL, Law 30 of 2018) applies to all data processing activities within Bahrain. Enforcement intensified in 2023–2024. The PDPA publishes regulations.pdf (19,637c confirmed) — directly actionable compliance content.

### LLOC — Legal database
Official repository for all Bahrain legislation including banking laws, financial services legislation, company law, and commercial regulations. Legal teams advising on Bahrain law and compliance advisors tracking regulatory change use this as the primary legislative reference.

### GCC bundle commercial value
Bahrain's addition completes the GCC4 bundle: UAE + Saudi Arabia + Qatar + Bahrain. This is a compelling commercial story for international law firms, consulting firms (Big 4, McKinsey, etc.), and financial institutions with GCC operations. The four jurisdictions together represent:
- ~$1.5T+ combined GDP
- 3 of the world's largest SWFs (ADIA, PIF, QIA)
- Major Islamic finance, fintech, and capital markets hubs
- Bahrain as the GCC's leading fintech regulatory hub

RegRadar can market: "GCC4 regulatory intelligence across UAE, Saudi Arabia, Qatar, and Bahrain — with source-backed coverage and documented limitations."

---

## Next Recommendation

**Immediate (run health audit):**  
`python run.py health` — registers all new sources (8 HK + 2 AE + 9 QA + 12 BH) and updates Bahrain coverage from 50 (unknown) to an actual quality-based score. Run before relying on BH or GCC coverage scores in a demo.

**Short-term:**
1. Identify Bahrain NCSC (National Cyber Security Centre) domain — add cybersecurity category if accessible.
2. Investigate Bahrain AML/FIU alternative domain — all tested domains are DNS-dead; try Bahrain Ministry of Interior AML directorate sub-page.
3. TRA/iGA HTML adapters — low effort, would strengthen HTML-level monitoring for digital regulation categories.

**Next commercial country:**  
**Malaysia (MY)** or **Turkey (TR)** — both have commercial priority. Turkey already has 9 sources (score 83 usable). Malaysia has 0 active sources and is listed as a commercial priority market.

---

## Files Modified

| File | Action |
|------|--------|
| `sources.json` | Added 14 BH entries (12 enabled, 2 disabled) |
| `reports/bh_validated_source_pack_2026-05-27.md` | Created — this file |
