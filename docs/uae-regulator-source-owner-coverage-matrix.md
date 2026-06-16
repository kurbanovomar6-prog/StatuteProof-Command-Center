# UAE Regulator / Source Owner Coverage Matrix

Date: 2026-06-17
Based on: uae_source_universe_candidates.json (203 records), sources.json (79 enabled)

All counts are as of 2026-06-17. "Active" = enabled and readiness-supported in sources.json. "Candidate" = in universe JSON but not yet enabled.

---

## How to Read This Matrix

- **Coverage verdict:** strong (7+ active sources covering all major types), adequate (4–6 active, major types represented), partial (1–3 active or missing critical types), weak (1 active, few types covered), not covered (0 active)
- **Required for comprehensive:** means the buyer segment demands at least one source from this owner
- **Required for complete:** means the claim cannot be made without active coverage from this owner
- **Next proof needed:** the single most important next action to advance coverage for this owner

---

## 1. CBUAE — Central Bank of the UAE

| Field | Value |
|-------|-------|
| Official domain | centralbank.ae, rulebook.centralbank.ae |
| Category | Central bank / banking / payments / AML/CFT |
| Active readiness-supported | 27 |
| Candidates not yet active | 13 |
| P0 candidates | 3 (AML/CFT page, consultations, circular-bank-supervision) |
| P1 candidates | 5 (publications, consumer protection, licensing, fintech, NSFR) |
| P2 candidates | 5 (insurance, financial stability, news, payment systems, open data) |
| Rejected in category | 2 |
| Missing critical source types | Consultations (horizon scanning gap); AML/CFT operations page; bank supervision circulars |
| Official-source confidence | Very high (official UAE regulator, government domain) |
| Buyer relevance | Bank CCO, Payments CCO, MLRO, Fintech CCO, Insurance Compliance |
| Current coverage verdict | **Strong** — 27 active; dominant in pack; rulebook depth is strongest of any regulator |
| Required for comprehensive UAE coverage | YES |
| Required for complete UAE coverage | YES |
| Next proof needed | Activate AE-cbuae-consultations via no-save preview (already in work queue as candidate). This closes the CBUAE horizon-scanning gap. |

**Commentary:** CBUAE is the strongest-covered regulator. 27 active sources cover AML/CFT, consumer protection, payments, capital adequacy, liquidity, market risk, operational risk, Islamic banking, open finance, and more. The remaining gaps (consultations, AML/CFT operations page) are addressable in the next sprint. CBUAE concentration (35.5% of pack) is commercially useful but should not be inflated further without adding breadth elsewhere first.

---

## 2. SCA — Securities and Commodities Authority

| Field | Value |
|-------|-------|
| Official domain | sca.gov.ae |
| Category | Securities / capital markets |
| Active readiness-supported | 5 |
| Candidates not yet active | 10 |
| P0 candidates | 2 (SCA laws, SCA decisions) |
| P1 candidates | 3 (market rules, violations, investment funds) |
| P2 candidates | 3 (disclosure, regulations amendments, news) |
| P3 candidates | 2 (sustainable finance, fintech sandbox) |
| Rejected in category | 2 |
| Missing critical source types | Primary securities legislation (laws + decisions); regulation amendments; investment fund rules |
| Official-source confidence | High (official UAE government regulator) |
| Buyer relevance | Securities CCO, Asset Manager, Broker, MLRO (for securities firms) |
| Current coverage verdict | **Partial** — 5 active sources cover AML/CFT, FATCA/CRS, corporate governance, circulars, and regulations listing. BUT primary securities laws (the foundation of SCA obligation) are not active. |
| Required for comprehensive UAE coverage | YES — securities CCO buyer has no primary legislation monitoring |
| Required for complete UAE coverage | YES |
| Next proof needed | No-save preview on AE-sca-laws (sca.gov.ae/en/legislation/laws.aspx) and AE-sca-decisions. Known SCA listing adapter pattern. Low technical risk. |

**Commentary:** SCA is the second-most-underserved major regulator (after FTA). The 5 active sources are the right types (AML, FATCA, corporate governance) but the foundational securities law layer is missing. Any securities-focused buyer will ask "can you monitor SCA laws and board decisions?" — current answer is no. This should be in the P0 sprint.

---

## 3. DFSA — Dubai Financial Services Authority

| Field | Value |
|-------|-------|
| Official domain | dfsa.ae, dfsaen.thomsonreuters.com |
| Category | Financial free-zone regulator (DIFC) |
| Active readiness-supported | 10 |
| Candidates not yet active | 9 |
| P0 candidates | 3 (guidance notes, rulebook official page, AML/CTF hub) |
| P1 candidates | 3 (policy statements, annual reports, consultation papers) |
| P2 candidates | 2 (public register, supervisory risk appetite) |
| P3 candidates | 1 (crowdfunding) |
| Rejected in category | 2 |
| Missing critical source types | Guidance notes; policy statements; publications hub (umbrella for all above) |
| Official-source confidence | Very high (official UAE financial services regulator) |
| Buyer relevance | DFSA Firm CCO, MLRO, Legal Counsel, Compliance Manager |
| Current coverage verdict | **Adequate** — 10 active sources cover AML rulebook (via Thomson Reuters), enforcement decisions, regulatory actions, MLRO financial crime letters, notices, consultation papers. Core compliance monitoring is covered. |
| Required for comprehensive UAE coverage | YES |
| Required for complete UAE coverage | YES |
| Next proof needed | No-save preview on AE-dfsa-guidance-notes (dfsa.ae/your-resources/publications/guidance-notes). Guidance notes are the most frequently referenced practitioner resource not yet monitored. |

**Commentary:** DFSA coverage is solid and commercially ready for DFSA firm prospects. Guidance notes and policy statements are the meaningful gap — these are the interpretive documents DFSA-regulated compliance managers rely on. The existing Thomson Reuters AML rulebook source is the strongest single source in the pack.

---

## 4. DIFC — Dubai International Financial Centre

| Field | Value |
|-------|-------|
| Official domain | difc.com, difccourts.ae |
| Category | Financial free-zone legal framework / data protection / courts |
| Active readiness-supported | 8 |
| Candidates not yet active | 5 |
| P0 candidates | 1 (consultation papers) |
| P1 candidates | 2 (data protection hub, financial crime authority) |
| P2 candidates | 2 (insurance, courts decisions) |
| P3 candidates | 0 |
| Rejected in category | 3 |
| Missing critical source types | Consultation papers (horizon scanning); financial crime authority section |
| Official-source confidence | Very high (official UAE free-zone authority) |
| Buyer relevance | DIFC Firm CCO, Legal Counsel, MLRO, Compliance Manager |
| Current coverage verdict | **Adequate** — 8 active sources include legal database, data protection law (2020), Companies Law (2018), data protection commissioner, supervision and enforcement, guidance, and regulation 10. Data protection coverage is the deepest of any regulator in the pack. |
| Required for comprehensive UAE coverage | YES |
| Required for complete UAE coverage | YES |
| Next proof needed | No-save preview on AE-difc-consultation-papers (difc.com/business/laws-and-regulations/consultation-papers/). DIFC consultations are the horizon-scanning mechanism for the DIFC legal framework. |

**Commentary:** DIFC coverage is a strength, especially data protection. The DIFC data protection pack (8 sources) makes StatuteProof commercially competitive for DIFC data protection clients. The missing piece is consultation papers for upcoming law changes.

---

## 5. ADGM / FSRA — Abu Dhabi Global Market

| Field | Value |
|-------|-------|
| Official domain | adgm.com, fsra.adgm.com |
| Category | Financial free-zone regulator (Abu Dhabi) |
| Active readiness-supported | 10 |
| Candidates not yet active | 12 |
| P0 candidates | 4 (FSRA notices, media announcements, RA notices, RA AML guides) |
| P1 candidates | 5 (RA regulations, DP regulatory actions, DP hub, public register, CO circulars) |
| P2 candidates | 3 (federal legislation, FSRA reports, listing announcements) |
| Rejected in category | 2 |
| Missing critical source types | FSRA regulatory notices; RA AML guides for DNFBPs; media/regulatory announcements |
| Official-source confidence | Very high (official UAE financial free-zone regulator) |
| Buyer relevance | ADGM Firm CCO, MLRO, Legal Counsel, DNFBP Compliance |
| Current coverage verdict | **Adequate** — 10 active sources cover financial crime, rulebooks, consultations, guidance, waivers, RA circulars, listing rules, enforcement. Good breadth. |
| Required for comprehensive UAE coverage | YES |
| Required for complete UAE coverage | YES |
| Next proof needed | No-save preview on AE-adgm-ra-aml-guides (adgm.com/registration-authority/aml-cft-guides). ADGM RA AML guides for DNFBPs are a known gap for DNFBP buyer segment (real estate, law firms, accounting firms). PDF listing adapter pattern is known. |

**Commentary:** ADGM coverage is adequate and commercially usable. The RA AML guides for DNFBPs (law firms, accounting, real estate) are the highest-value gap — they represent the non-financial-services buyer segment that ADGM serves. FSRA regulatory notices and media announcements would significantly improve timely-alert value.

---

## 6. VARA — Virtual Assets Regulatory Authority

| Field | Value |
|-------|-------|
| Official domain | vara.ae, rulebooks.vara.ae |
| Category | Virtual assets / cryptocurrency |
| Active readiness-supported | 9 |
| Candidates not yet active | 7 |
| Remediation (active but broken) | 4 |
| P0 candidates | 5 (activity rulebooks hub, guidance, administrative orders + 2 more) |
| P1 candidates | 2 (public register, licensing conditions) |
| P2 candidates | 2 (market oversight, news) |
| P3 candidates | 0 |
| Rejected in category | 4 (3 broken URLs, 1 social media) |
| Missing critical source types | Regulatory guidance (vara.ae/en/regulatory-guidance/) — not active; VARA AML/CFT rulebook live page — URL broken; VARA regulatory framework hub — URL broken |
| Official-source confidence | Very high (official Dubai regulator for virtual assets) |
| Buyer relevance | VASP MLRO, VASP CCO, Legal Counsel (crypto firms) |
| Current coverage verdict | **Partial** — 9 active sources (mostly PDFs + enforcement + homepage + rulebook-updates) cover specific rulebook versions and enforcement notices. BUT the VARA regulatory guidance hub, framework hub, and AML/CFT rulebook LIVE page are not active. This is the most critical gap for the primary VASP buyer. |
| Required for comprehensive UAE coverage | YES — VASP is the primary buyer segment |
| Required for complete UAE coverage | YES |
| Next proof needed | Investigate vara.ae/en/regulatory-guidance/ via Playwright to find the correct current URL for VARA guidance. If accessible, run no-save preview. This is the single highest-priority gap fix. |

**Commentary:** VARA is the most commercially important gap. The 9 active VARA sources are mostly PDF snapshots — they are valid, proof-backed, and commercially useful, but they miss the live monitoring of VARA's guidance and regulatory framework pages. The 4 remediation entries represent broken URLs (after a VARA site redesign) that have not been updated. A VASP MLRO buyer asking "can you monitor the VARA regulatory guidance hub?" will get a "no" answer today. This must be fixed before VASP-focused outreach.

---

## 7. UAE FIU — Financial Intelligence Unit

| Field | Value |
|-------|-------|
| Official domain | uaefiu.gov.ae |
| Category | AML / FIU / suspicious transaction reporting |
| Active readiness-supported | 5 |
| Candidates not yet active | 9 |
| P0 candidates | 3 (NRA 2024, strategic analysis, mutual evaluation) |
| P1 candidates | 2 (annual reports, press releases) |
| P2 candidates | 2 (goAML public guidance, awareness) |
| P3 candidates | 1 (open data) |
| Rejected in category | 1 (goAML login portal) |
| Missing critical source types | NRA 2024 (most cited MLRO document, not monitored); FATF mutual evaluation; strategic analysis guidelines |
| Official-source confidence | Very high (official UAE federal authority) |
| Buyer relevance | MLRO (primary), AML Officer, CCO (all regulated entities) |
| Current coverage verdict | **Adequate-Partial** — 5 active sources cover circulars, AML/CFT laws, typology reports, publications hub, and main homepage. Core AML publication monitoring is covered. But the NRA 2024, mutual evaluation, and strategic analysis are the 3 highest-value documents not monitored. |
| Required for comprehensive UAE coverage | YES |
| Required for complete UAE coverage | YES |
| Next proof needed | No-save preview on AE-uaefiu-nra-2024. The UAE NRA is a static page with a PDF link — low technical risk, high commercial value. Should take one session to activate. |

---

## 8. EOCN — Executive Office of Anti-Money Laundering and Counter Terrorism Financing

| Field | Value |
|-------|-------|
| Official domain | eocn.gov.ae |
| Category | AML / sanctions / CFT |
| Active readiness-supported | 2 |
| Candidates not yet active | 1 (TFS page) |
| Missing critical source types | Targeted Financial Sanctions framework page |
| Official-source confidence | Very high (official UAE executive office) |
| Buyer relevance | MLRO, AML Officer, Sanctions Compliance |
| Current coverage verdict | **Adequate** — 2 active sources (AML/CFT laws and regulations + news). Core regulatory framework is covered. |
| Required for comprehensive UAE coverage | YES |
| Required for complete UAE coverage | YES |
| Next proof needed | Evaluate AE-eocn-tfs (eocn.gov.ae/en-us/un-page). Caution: TFS list may change with high velocity. Monitor noise risk before activating. |

---

## 9. UAE Legislation Portal

| Field | Value |
|-------|-------|
| Official domain | uaelegislation.gov.ae |
| Category | Federal law / legislation |
| Active readiness-supported | 1 |
| Candidates not yet active | 2 (financial laws subject page, AML/CFT decrees subject page) |
| Missing critical source types | AML/CFT decree tracking; financial legislation subject tracking |
| Official-source confidence | Very high (official UAE federal government) |
| Buyer relevance | Legal Counsel, CCO, MLRO (for legislative changes) |
| Current coverage verdict | **Weak** — 1 active source (main homepage anchor). Subject-specific legislative monitoring is not active. |
| Required for comprehensive UAE coverage | YES — AML/CFT legislative changes must be detectable |
| Required for complete UAE coverage | YES |
| Next proof needed | No-save preview on AE-uae-legislation-aml (uaelegislation.gov.ae/en/legislations?subject=16). AML/CFT decrees and cabinet resolutions are the highest-priority federal legislative category. |

---

## 10. Ministry of Finance

| Field | Value |
|-------|-------|
| Official domain | mof.gov.ae |
| Category | Federal / public finance |
| Active readiness-supported | 1 |
| Candidates | 0 distinct additional (homepage is the active source) |
| Missing critical source types | Budget circulars; FATF-related financial policy |
| Official-source confidence | Very high |
| Buyer relevance | CFO, Finance Director, Compliance (for financial reporting obligations) |
| Current coverage verdict | **Weak** — Homepage anchor only. No publication-level monitoring. |
| Required for comprehensive UAE coverage | Partial — relevant but not a primary compliance obligation source |
| Required for complete UAE coverage | NO — MoF is not a primary compliance regulator for most target buyer segments |
| Next proof needed | Low priority. MoF circulars and guidance are not primary MLRO/CCO monitoring targets. |

---

## 11. Federal Tax Authority (FTA)

| Field | Value |
|-------|-------|
| Official domain | tax.gov.ae |
| Category | Tax / VAT / corporate tax |
| Active readiness-supported | 0 |
| Candidates | 7 |
| P0 candidates | 0 |
| P1 candidates | 0 |
| P2 candidates | 5 (homepage, corporate tax guides, VAT clarifications, VAT guides, CBC reporting) |
| P3 candidates | 2 (excise tax, news) |
| Missing critical source types | ALL — FTA is entirely absent from active pack |
| Official-source confidence | Very high (official UAE federal tax authority) |
| Buyer relevance | Tax Compliance, CFO, Legal Counsel, any entity subject to UAE VAT or corporate tax |
| Current coverage verdict | **Not covered** — 0 active sources. FTA is a universal compliance obligation for all UAE-licensed entities with taxable turnover. |
| Required for comprehensive UAE coverage | YES — VAT and corporate tax compliance is required for almost all target buyers |
| Required for complete UAE coverage | YES |
| Next proof needed | Run no-save preview batch on the 3 most important FTA pages: AE-fta-corporate-tax-guides, AE-fta-vat-public-clarifications, AE-federal-tax-authority-homepage. Expected low technical friction. |

---

## 12. Ministry of Economy

| Field | Value |
|-------|-------|
| Official domain | moet.gov.ae |
| Category | Federal / commercial regulation / AML for DNFBPs |
| Active readiness-supported | 1 |
| Candidates | 3 (AML DNFBP page, regulations, media publications) |
| Missing critical source types | AML DNFBP supervision hub; economic regulations |
| Official-source confidence | Very high |
| Buyer relevance | MLRO (for DNFBPs), CCO, compliance consultants |
| Current coverage verdict | **Weak** — Homepage anchor only. MoE AML/DNFBP supervision page (used by law firms, real estate, accounting firms) is a candidate, not active. |
| Required for comprehensive UAE coverage | YES — DNFBPs must monitor MoE AML/CFT guidance |
| Required for complete UAE coverage | YES |
| Next proof needed | No-save preview on AE-moec-aml-dnfbp (moet.gov.ae/en/anti-money-laundering). DNFBPs are a growing buyer segment. |

---

## 13. Ministry of Justice

| Field | Value |
|-------|-------|
| Official domain | moj.gov.ae, elaws.moj.gov.ae |
| Category | Federal law / legal database |
| Active readiness-supported | 0 |
| Candidates | 2 (federal laws page, e-laws portal) |
| Missing critical source types | Federal law database; judicial circulars |
| Official-source confidence | Very high |
| Buyer relevance | Legal Counsel, CCO (for statutory obligation research) |
| Current coverage verdict | **Not covered** — 0 active sources. |
| Required for comprehensive UAE coverage | Partial — MoJ e-laws supplements other legislative sources |
| Required for complete UAE coverage | YES |
| Next proof needed | Test AE-uae-elaws-moj (elaws.moj.gov.ae/). If accessible without JS, low activation cost. |

---

## 14. Ministry of Foreign Affairs

| Field | Value |
|-------|-------|
| Official domain | mofa.gov.ae |
| Category | Sanctions / export control (if relevant) |
| Active readiness-supported | 0 |
| In universe | No |
| Buyer relevance | Sanctions Compliance (niche) |
| Coverage verdict | **Not covered** — MoFA sanctions lists are typically republished by EOCN; monitoring MoFA directly may be redundant |
| Required for comprehensive UAE coverage | NO — EOCN covers the UAE sanctions/TFS framework |
| Required for complete UAE coverage | NO |
| Next proof needed | None required. EOCN is the authoritative UAE TFS source. |

---

## 15. TDRA / UAE Data Office

| Field | Value |
|-------|-------|
| Official domain | tdra.gov.ae, uaedp.gov.ae |
| Category | Data protection / privacy / telecommunications |
| Active readiness-supported | 0 |
| Candidates | 2 (TDRA regulations, UAE Data Office) |
| Missing critical source types | UAE Personal Data Protection Law (PDPL) guidance and implementation rules |
| Official-source confidence | High |
| Buyer relevance | Data processors, fintech, bank (for federal PDPL compliance) |
| Coverage verdict | **Not covered** — 0 active sources. Note: DIFC data protection (8 sources) covers DIFC-specific DP law. UAE federal DP is a different framework (PDPL 2021). |
| Required for comprehensive UAE coverage | YES — PDPL applies to all UAE entities processing personal data |
| Required for complete UAE coverage | YES |
| Next proof needed | No-save preview on AE-uae-data-office (uaedp.gov.ae). Federal PDPL guidance is increasingly important for fintech/bank CCOs. |

---

## 16. Dubai Customs / Federal Customs Authority

| Field | Value |
|-------|-------|
| Official domain | dubaicustoms.gov.ae, fcagov.ae |
| Category | Customs / trade compliance / export control |
| Active readiness-supported | 0 |
| In universe | No (not included in 200-source universe) |
| Buyer relevance | Trade compliance, commodities firms |
| Coverage verdict | **Not covered and not mapped** |
| Required for comprehensive UAE coverage | Partial — relevant for commodities/trade buyers; not primary for MLRO/CCO target segment |
| Required for complete UAE coverage | YES for trade-facing entities |
| Next proof needed | Add to universe candidates in next research cycle. Needs domain investigation first. |

---

## 17. DMCC / DFM / ADX / Free Zone Regulators

| Field | Value |
|-------|-------|
| Official domains | dmcc.ae, dfm.ae, adx.ae |
| Category | Emirate-level / exchange / free zone |
| Active readiness-supported | 0 |
| Candidates | 2 (DMCC compliance, DFM market rules) |
| Rejected | 5 (URL 404s, 403, timeouts) |
| Coverage verdict | **Not covered** — DMCC URL was verified accessible but not yet activated. DFM has a timeout. ADX is 403-blocked. |
| Required for comprehensive UAE coverage | Partial — relevant for listed company compliance, commodities, free-zone businesses |
| Required for complete UAE coverage | YES for exchange-regulated buyers |
| Next proof needed | DMCC compliance page no-save test (most accessible). |

---

## Coverage Matrix Summary

| Source Owner | Active | Coverage Verdict | Required for Comprehensive | Required for Complete |
|-------------|--------|-----------------|--------------------------|----------------------|
| CBUAE | 27 | **Strong** | YES | YES |
| DFSA | 10 | **Adequate** | YES | YES |
| ADGM/FSRA | 10 | **Adequate** | YES | YES |
| DIFC | 8 | **Adequate** | YES | YES |
| VARA | 9 (partial) | **Partial** ⚠️ | YES | YES |
| UAE FIU | 5 | **Adequate-Partial** | YES | YES |
| EOCN | 2 | **Adequate** | YES | YES |
| SCA | 5 | **Partial** ⚠️ | YES | YES |
| UAE Legislation | 1 | **Weak** | YES | YES |
| Ministry of Finance | 1 | **Weak** | Partial | NO |
| Ministry of Economy | 1 | **Weak** | YES (DNFBP) | YES |
| Federal Tax Authority | 0 | **Not covered** ❌ | YES | YES |
| Ministry of Justice | 0 | **Not covered** | Partial | YES |
| MoFA | 0 | N/A | NO | NO |
| TDRA / UAE Data Office | 0 | **Not covered** ❌ | YES | YES |
| Dubai/Federal Customs | 0 | **Not mapped** ❌ | Partial | YES |
| DMCC/DFM/ADX | 0 | **Not covered** | Partial | YES |

**Comprehensive UAE coverage requires:** VARA gap fixed, SCA laws active, FTA ≥1 active, MoE AML active, UAE legislation AML active. Total: ~5 targeted activations.

**Complete UAE coverage requires:** All of the above + Customs/trade + MoJ active + TDRA/Data Office active + 3 months monitoring data + recall rate measurement. Not achievable in under 3 months.
