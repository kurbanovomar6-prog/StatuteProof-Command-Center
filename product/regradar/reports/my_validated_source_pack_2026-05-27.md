# Malaysia Validated Source Pack
**Date:** 2026-05-27  
**Jurisdiction:** MY — Malaysia  
**Audit basis:** Individual `run.py test-source` validation per source  

---

## Executive Summary

**Before:** 0 MY sources (0 enabled).  
**After:** 14 MY entries (11 enabled, 3 disabled).  

Malaysia moves from zero coverage to **11 active official sources**, adding a major Southeast Asia regulatory market to RegRadar alongside Singapore.

Sources tested: 22 official Malaysia regulatory URLs (+ 4 alternate domains)  
Sources activated: 11 (enabled=true, status=active in sources.json)  
Sources not activated: 3 documented as disabled (MoF SPA, Federal Gazette DNS-dead, Customs SPA)  

**Coverage score (current):** 50 — unknown quality  
Score reflects "unknown quality" because health audit has not run on new sources. Individual test-source validation confirms 11 sources extract GOOD quality content. Expected score after `python run.py health`: **85–95 (strong)**.  

**8–12 target:** ACHIEVED — 11 official validated sources.  

**Demo-ready:** Yes, after `python run.py health` refreshes quality scores. Standalone AML/FIU, customs, and official gazette gaps should be disclosed in demos. BNM covers AML/CFT policy for BNM-licensed financial institutions, but it is not a replacement for a dedicated FIU source.

---

## Source Table

| Source | URL | Category | HTTP | Chars | Docs/PDF | Decision | Notes |
|--------|-----|----------|------|-------|----------|----------|-------|
| Bank Negara Malaysia (BNM) | https://www.bnm.gov.my/ | central_bank | 202 | 2,046c (Playwright) | 0 accessible PDFs | **ACTIVATED** | Central bank + banking + payments + insurance/takaful supervisor; FIU gap remains |
| Securities Commission Malaysia (SC) | https://www.sc.com.my/ | securities_regulator | 200 | 9,128c | 0 PDFs on root | **ACTIVATED** | Regulates capital markets, DAX (crypto), investment funds |
| Bursa Malaysia | https://www.bursamalaysia.com/ | capital_markets | 403 surface / rendered | 14,029c (Playwright) | 6 PDF links (403 auth) | **ACTIVATED** | Official stock exchange and market operator; monitorable via Playwright-rendered content |
| Inland Revenue Board (HASiL / LHDN) | https://www.hasil.gov.my/ | tax | 200 | 7,351c | 13 PDFs (partial extraction) | **ACTIVATED** | Tax authority for income tax, WHT, real property gains |
| Malaysia Budget Portal (Belanjawan) | https://belanjawan.mof.gov.my/ | finance_ministry | 200 | 9,618c | 14 PDFs / 194,422c | **ACTIVATED** | Federal budget portal; best accessible MoF content |
| Laws of Malaysia — AGC Portal (LOM) | https://lom.agc.gov.my/ | legal_database | 200 | 6,310c | 0 PDFs on root | **ACTIVATED** | Official federal legislation database (AGC) |
| Dept of Personal Data Protection (JPDP) | https://www.pdp.gov.my/ | data_protection | 200 | 13,248c | 0 PDFs on root | **ACTIVATED** | Enforces PDPA 2010; critical for fintech, banks |
| Malaysian Comms & Multimedia Commission (MCMC) | https://www.mcmc.gov.my/ | digital_regulation | 200 | 3,758c (Playwright) | 13 PDFs / 38,685c | **ACTIVATED** | Telecom, internet, digital services regulator |
| National Cyber Security Agency (NACSA) | https://www.nacsa.gov.my/ | cybersecurity | 200 | 12,890c | 6 PDFs / 13,911c | **ACTIVATED** | National cybersecurity standards and policy |
| Malaysia Competition Commission (MyCC) | https://www.mycc.gov.my/ | competition | 200 | 9,054c | 5 PDFs / 9,904c | **ACTIVATED** | Competition Act enforcement; M&A and antitrust |
| Companies Commission of Malaysia (SSM) | https://www.ssm.com.my/Pages/Legal_Framework/Guidelines.aspx | company_registry | 200 | 2,607c (Playwright) | 30 PDF links / 11,834c sampled | **ACTIVATED** | Company registry; guidelines page > root (1,341c) |
| Ministry of Finance Malaysia (MoF) | https://www.mof.gov.my/ | finance_ministry | SPA | < 500c all paths | 0 | **NOT ACTIVATED** | All URL paths fail; belanjawan portal covers budget content |
| Federal Gazette Malaysia | https://www.federalgazette.agc.gov.my/ | official_gazette | DNS FAILURE | 0c | 0 | **NOT ACTIVATED** | DNS does not resolve; gazette.gov.my also DNS failure |
| Royal Malaysian Customs Department | https://www.customs.gov.my/ | customs | SPA | 307c max | 0 | **NOT ACTIVATED** | SPA portal; all sub-paths return 404 or 0c |

### Additional URLs tested and rejected

| URL | Result | Reason |
|-----|--------|--------|
| https://www.mof.gov.my/en/ | 460c LOW_CONTENT | SPA — English path also fails |
| https://www.mof.gov.my/en/news/press-release | HTTP 404 | Sub-path not accessible |
| https://www.treasury.gov.my/ | SSL error + 174c | SSL hostname mismatch; Playwright fails |
| https://gazette.gov.my/ | DNS failure | Alternative gazette domain also dead |
| https://www.agc.gov.my/ | 276c LOW_CONTENT | AGC root SPA; LOM sub-portal is preferred |
| https://mdec.my/ | 1,326c GOOD | Investment promotion body; not a regulatory source |
| https://www.nccml.gov.my/ | DNS failure | AML coordination body — domain inactive |
| https://www.bnm.gov.my/fintech | 0c FAILED | Sub-page not accessible; BNM root covers fintech |
| https://www.sc.com.my/development/digital-assets | 283c LOW_CONTENT | SPA sub-page; SC root covers digital assets |

---

## Categories Covered

| Category | Source | Quality |
|----------|--------|---------|
| central_bank / monetary authority | BNM | GOOD — 2,046c (Playwright) |
| banking_regulator | BNM | GOOD — unified regulator under Financial Services Act |
| payments | BNM | GOOD — BNM regulates payment systems via Payment Systems Act |
| insurance / takaful | BNM | GOOD — BNM regulates insurance and takaful |
| securities_regulator | SC Malaysia | GOOD — 9,128c (strongest HTML source) |
| capital_markets | Bursa Malaysia | GOOD — 14,029c (Playwright) |
| crypto / digital assets | SC Malaysia | GOOD — SC regulates DAX (digital asset exchange) operators |
| tax | HASiL / LHDN | GOOD — 7,351c |
| finance_ministry / fiscal policy | Belanjawan (Budget Portal) | GOOD — 9,618c + 194,422c PDF |
| legal_database | AGC/LOM | GOOD — 6,310c |
| data_protection | JPDP/PDP | GOOD — 13,248c |
| digital_regulation / telecom | MCMC | GOOD — 3,758c + 38,685c PDF |
| cybersecurity | NACSA | GOOD — 12,890c + 13,911c PDF |
| competition | MyCC | GOOD — 9,054c + 9,904c PDF |
| company_registry | SSM | GOOD — 2,607c + 11,834c sampled PDFs |

---

## Missing Categories

| Category | Status | Reason | Priority |
|----------|--------|--------|----------|
| AML / FIU (standalone) | missing — BNM only partially covers FI AML/CFT policy | nccml.gov.my DNS failure; no standalone AML/FIU source found | HIGH — dedicated AML/FIU monitoring is not active |
| official_gazette | disabled — DNS dead | federalgazette.agc.gov.my and gazette.gov.my both DNS failure | MEDIUM — LOM covers enacted legislation; gazette publication changes not directly monitored |
| customs / enforcement | disabled — SPA | customs.gov.my SPA; all sub-paths return 404 or 0c | MEDIUM — GST/customs compliance monitoring not possible without adapter |
| finance_ministry (general MoF) | partial — Belanjawan covers budget | mof.gov.my is a SPA (all paths < 500c) | LOW — Belanjawan Budget Portal provides fiscal policy content; MoF policy circulars not covered |
| public_consultations | not tested | No confirmed official Malaysia public consultation portal identified | LOW |

---

## Adapter Tasks

| Source | Issue | Priority | Estimated effort |
|--------|-------|----------|-----------------|
| MoF Malaysia (mof.gov.my) | Deep SPA; all paths < 500c. Finance ministry policy circulars inaccessible. | MEDIUM — Belanjawan provides budget coverage | Hard: requires SPA navigation adapter targeting press-release or policy publication pages |
| Customs (customs.gov.my) | SharePoint SPA; all sub-paths 404. | MEDIUM — important for trade compliance | Medium: try SharePoint API or publication anchor page |
| Federal Gazette | DNS failure on all known gazette domains. | MEDIUM — official gazette is primary source for new regulations | Hard: requires domain discovery or alternative AGC publication URL |
| BNM PDF extraction | BNM root has no direct PDF links accessible; publications page (3,661c) has 6 PDFs but same as root content. | LOW — BNM HTML monitoring is functional | Low: locate BNM regulatory publications direct URL |

---

## 8–12 Target Reality Check

**Target achieved: YES — 11 active official sources.**

| Category | Source | Result |
|----------|--------|--------|
| central_bank | BNM | ✅ ACTIVE (2,046c GOOD) |
| securities_regulator | SC Malaysia | ✅ ACTIVE (9,128c GOOD) |
| capital_markets | Bursa Malaysia | ✅ ACTIVE (14,029c GOOD) |
| tax | HASiL / LHDN | ✅ ACTIVE (7,351c GOOD) |
| finance_ministry | Belanjawan Budget Portal | ✅ ACTIVE (9,618c + 194,422c PDF) |
| legal_database | AGC/LOM | ✅ ACTIVE (6,310c GOOD) |
| data_protection | JPDP/PDP | ✅ ACTIVE (13,248c GOOD) |
| digital_regulation | MCMC | ✅ ACTIVE (3,758c + 38,685c PDF) |
| cybersecurity | NACSA | ✅ ACTIVE (12,890c + 13,911c PDF) |
| competition | MyCC | ✅ ACTIVE (9,054c + 9,904c PDF) |
| company_registry | SSM | ✅ ACTIVE (2,607c GOOD + 11,834c sampled PDFs) |
| AML / FIU | — | ⚠️ MISSING — BNM publishes FI AML/CFT policy, but no standalone FIU source is active |
| official_gazette | — | ❌ DNS dead — both gazette domains inactive |
| customs | — | ❌ SPA — all custom portal paths fail |
| general MoF portal | — | ❌ SPA — all mof.gov.my paths fail |

11 sources honestly achieves the 8–12 target and covers most commercially critical Malaysia categories. Important gaps remain: standalone AML/FIU, official gazette publication monitoring, customs/trade enforcement, and the general MoF portal are not active. BNM, LOM, Belanjawan, and MCMC provide partial adjacent coverage only; they should not be presented as replacements for those missing sources.

---

## Commercial Value

### BNM — The most commercially critical Malaysia source
Bank Negara Malaysia is the unified regulator for all banks, insurance companies, takaful operators, payment service providers, fintech firms, and money service businesses in Malaysia. All licensed financial institutions must monitor BNM regulatory updates, policy documents, and financial reporting requirements. BNM is the single most important regulatory source for any compliance team operating in Malaysia. BNM also regulates Malaysia's Islamic finance sector — the world's largest — making this commercially critical for Islamic banking, sukuk, and takaful compliance teams.

### SC Malaysia — Crypto and capital markets
The Securities Commission Malaysia was one of the first regulators globally to provide a formal framework for digital asset exchanges (2019). SC regulates all capital markets activities, unit trusts, investment advisers, and cryptocurrency exchanges. For fintech and crypto compliance teams operating in Southeast Asia, SC monitoring is mandatory. SC's regular guidance updates, enforcement actions, and digital asset policy releases are high-priority signals.

### Bursa Malaysia — Listed company compliance
Malaysia's official stock exchange serves as the listing and trading venue for 900+ companies. Listed companies, investment banks, and asset managers must monitor Bursa disclosure requirements, listing rules, and regulatory announcements. Combined with SC capital markets supervision, this covers the full securities compliance stack.

### HASiL / LHDN — Tax compliance
Malaysia's income tax system, with a 24% corporate tax rate and specific regimes for Islamic finance, digital services (6% SST), and e-invoicing mandates, requires active monitoring. HASiL is mandatory for all businesses with Malaysian tax obligations. The recent implementation of mandatory e-invoicing (Peppol standard) has created new compliance monitoring requirements.

### Belanjawan / MoF Budget Portal — Fiscal policy
Malaysia's annual budget is one of the most commercially important regulatory documents in the country, introducing tax changes, new incentives, and industry-specific policies. The Budget portal at 194,422c of PDF content covers Budget 2026 documents including tax appendix. Critical for tax advisory, investment planning, and public sector compliance.

### PDP / JPDP — Data protection
Malaysia's Personal Data Protection Act (PDPA) 2010 is being significantly amended (Personal Data Protection Amendment Bill passed 2024) to strengthen enforcement, introduce data breach notification, and increase penalties. Compliance teams in fintech, banking, and digital services must monitor PDPA developments. Malaysia's PDPA is increasingly aligned with international standards.

### MCMC — Digital regulation
MCMC regulates internet services, spectrum allocation, digital communications, and increasingly AI/digital platform governance in Malaysia. Its SRSP (spectrum) and policy documents are critical for telcos, digital payment providers, and cloud service operators.

### NACSA — Cybersecurity
Malaysia's cybersecurity regulatory framework under NACSA is expanding. The Cyber Security Act 2024 came into force and imposes mandatory requirements on national critical information infrastructure (NCII) operators, including banks, payment operators, and digital services. NACSA monitoring is now mandatory for financial institutions in Malaysia.

### MyCC — Competition law
The Competition Act 2010 enforces prohibitions on anti-competitive agreements and abuse of dominant position. MyCC has been increasingly active in fintech, payments, and digital markets. Competition monitoring is essential for M&A due diligence and market conduct reviews.

### Southeast Asia commercial context
Malaysia completes RegRadar's Southeast Asia pair: Singapore (100 score, 8 sources) + Malaysia (11 sources). Together these cover two major SEA financial markets by institutional depth. Law firms, consulting firms, and financial institutions operating in SEA need both. RegRadar can market Singapore and Malaysia regulatory intelligence with the disclosed Malaysia source limitations above.

---

## Next Recommendation

**Immediate (run health audit):**  
`python run.py health` — registers all new sources (8 HK + 2 AE + 9 QA + 12 BH + 11 MY = 42 new sources) and updates coverage scores from 50 (unknown) to actual quality-based scores. Run before any demo involving these jurisdictions.

**Short-term:**
1. Identify Malaysia AML/FIU dedicated domain — investigate whether the Financial Intelligence Unit of BNM has a public-facing publication URL, or whether Malaysia's Suspicious Transaction Reporting authority has a standalone site.
2. Customs adapter — investigate SharePoint/REST API for customs.gov.my to access regulatory publications.
3. Federal Gazette domain — check if AGC has moved gazette to a new domain.

**Next commercial country:**  
The core commercial priority markets are now covered (UAE, Saudi Arabia, Qatar, Bahrain, Hong Kong, Singapore, Malaysia). Turkey is already at 9 sources (score 83 usable). Remaining options:
- **Armenia (AM)** — already has sources but score is limited; could benefit from a quality audit
- **Azerbaijan (AZ)** — 1 active source; pre-mapped sources ready for activation
- **Georgia (GE)** / **Kazakhstan (KZ)** / **Uzbekistan (UZ)** — already have good coverage
- Or pivot to **deployment** (all commercial markets now have solid coverage)

---

## Files Modified

| File | Action |
|------|--------|
| `sources.json` | Added 14 MY entries (11 enabled, 3 disabled) |
| `reports/my_validated_source_pack_2026-05-27.md` | Created — this file |
