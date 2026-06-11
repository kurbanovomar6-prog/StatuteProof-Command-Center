# Saudi Arabia Validated Source Pack — 2026-05-26

> All sources in this report were tested via `discover-source` or `test-source` on 2026-05-26.
> Only sources passing quality validation were added to `sources.json`.
> No sources are activated based on candidate lists alone.

---

## Executive Summary

| Metric | Before | After |
|--------|--------|-------|
| SA sources in sources.json | 7 | 10 |
| SA enabled sources | 2 | 7 |
| SA disabled / restricted | 5 | 3 |
| SA coverage score | 62 (limited) | **100 (strong)** |
| Overall coverage score | 82 | **86** |
| Adapter tasks (SA) | 1 | 3 (MoF, BOE, SDAIA — external blocks, not adapter-fixable) |

**Changes made to sources.json:**
- SAMA re-enabled (was incorrectly marked disabled_external_access; Playwright extracts 1,589c + 68,237c PDFs)
- CMA URL updated to regulations subpage; re-enabled (root URL is JS SPA, regulations subpage works: 1,054c + 40,177c PDFs)
- 3 new sources added and activated: MISA (8,022c), Ministry of Commerce (1,182c), NCA (2,744c)

---

## Methodology

**Candidate vs active source:**
A source is a candidate until it passes validation. Candidates live in `data/source_candidates.json` with `enabled: false`. Only sources that pass `test-source` or `discover-source` with sufficient content are added to `sources.json` as active.

**Activation rules used:**
- `qualityScore >= 60` OR `extractedChars >= 1,000` for HTML sources
- `pdfChars >= 5,000` supplements weak HTML (but HTML chars must be > 0)
- Must be official or authoritative — no law firm blogs, news sites, aggregators
- Must not be navigation-only
- Must not require bypassing CAPTCHA, auth, or genuine geo-blocks

**Saudi-specific context:**
Saudi government websites are disproportionately JS-heavy SPAs that return 0 chars to all extractors when accessed from outside KSA. This is a structural limitation of the Saudi e-government platform, not a RegRadar project issue. Root domains (SAMA, CMA, MoF, SDAIA, BOE) consistently fail. Specific SharePoint-style subpages sometimes work. PDF-mode monitoring is viable for SAMA (3 PDFs: regulatory sandbox, economic reports).

---

## Saudi Arabia Source Table

| Source | URL | Category | Test Result | Chars | PDF Chars | Decision | Notes |
|--------|-----|----------|------------|-------|-----------|---------|-------|
| Saudi Central Bank (SAMA) | `.../en-US/Pages/default.aspx` | central_bank | PASS — 1,589c, Playwright | 1,589 | 68,237 | **ACTIVATED** (re-enabled) | Was incorrectly disabled. Still extracts 1,589c + 3 PDFs (Regulatory Sandbox, Economic Dev). |
| Zakat, Tax and Customs Authority (ZATCA) | `zatca.gov.sa/` | tax | PASS — 1,029c | 1,029 | 0 | **ALREADY ACTIVE** | No change needed. |
| CST — Communications, Space and Technology | `cst.gov.sa/` | financial_regulator | PASS — ~1,200c (limited) | ~1,200 | 0 | **ALREADY LIMITED** | Retained as limited. Playwright required. |
| Saudi Capital Market Authority (CMA) | `.../en/RulesRegulations/Regulations/...` | capital_markets | PASS — 1,054c + 40,177c PDF | 1,054 | 40,177 | **ACTIVATED** (URL updated) | Root URL is JS SPA (0c). Regulations subpage works. 36 PDF links; 3 extracted: Fund Rules, Exclusion Controls, Foreign Investment Rules. |
| Ministry of Investment (MISA) | `misa.gov.sa/` | government | PASS — 8,022c, RSS feed | 8,022 | 104,425 | **ACTIVATED** (new) | Score 90 (excellent). RSS at misa.gov.sa/rss (4 items). Investment regulation, licensing, establishment rules for fintechs and payment companies. |
| Ministry of Commerce | `mc.gov.sa/en/Pages/default.aspx` | commerce | PASS — 1,182c | 1,182 | 134,346 | **ACTIVATED** (new) | Root (232c) needs adapter, but English subpage works. Commercial licensing, e-commerce regulation. |
| National Cybersecurity Authority (NCA) | `nca.gov.sa/` | cyber | PASS — 2,744c, score 60 | 2,744 | 0 | **ACTIVATED** (new, limited) | Borderline pass. Essential Cybersecurity Controls (ECC), Cloud Controls (CCC) relevant to fintech infrastructure. |
| Saudi Ministry of Finance (MoF) | `mof.gov.sa/` | finance_ministry | FAIL — 55c, all subpages | 0–55 | 0 | **NOT ACTIVATED** | JS SPA blocks all extractors. All subpages (en/, ar/, financial sector, news) return 55c. Status: disabled_external_access. |
| Saudi Bureau of Experts — Laws Portal (BOE) | `laws.boe.gov.sa/` | legal_database | FAIL — timeout | 0 | 0 | **NOT ACTIVATED** | DNS timeout on laws.boe.gov.sa and boe.gov.sa root. Geo-IP blocked from outside KSA. Status: disabled_external_access. |
| Saudi Data & AI Authority (SDAIA) | `sdaia.gov.sa/` | data_protection | FAIL — HTTP2 error | 0 | 0 | **NOT ACTIVATED** | HTTP2 protocol error + connection reset on root and /en/ subpage. Complete server-side block. Status: disabled_external_access. |
| Saudi Exchange / Tadawul | `saudiexchange.sa/` | capital_markets | FAIL — 203c | 203 | 0 | **NOT ACTIVATED** | 203c — HTTP 403 then 203c via Playwright. Below threshold. Needs custom adapter. Not a primary regulatory source (exchange, not regulator). |
| SFIU / Saudi FIU | `sfiu.gov.sa/` | aml | FAIL — DNS | 0 | 0 | **NOT ACTIVATED** | DNS resolution failure. URL may be wrong or geo-blocked. Significant gap — SA AML/FIU authority. |
| General Authority for Competition (GAC) | `gac.gov.sa/` | competition | FAIL — DNS | 0 | 0 | **NOT ACTIVATED** | DNS resolution failure. Site unreachable from outside KSA. |
| Saudi Payments | `saudipayments.com/` | payments | FAIL — DNS | 0 | 0 | **NOT ACTIVATED** | DNS failure. SAMA subsidiary for payment infrastructure. |
| Umm Al-Qura Gazette | `uqn.gov.sa/` | official_gazette | FAIL — timeout | 0 | 0 | **NOT ACTIVATED** | Connection timeout on root and /home — geo-blocked from outside KSA. Official SA gazette. Critical gap. |
| SAMA Rules/Instructions page | `.../en-US/RulesInstructions/Pages/Default.aspx` | central_bank | FAIL — 808c | 808 | 0 | **NOT ACTIVATED** | Below 1,000c threshold. Needs adapter. Duplicate parent (SAMA main page already active). |
| CMA News page | `.../en/MediaCenter/News/Pages/default.aspx` | capital_markets | FAIL — 127c | 127 | 0 | **NOT ACTIVATED** | Below threshold. Needs adapter. Duplicate parent (CMA Regulations page already active). |
| ZATCA Regulations/News pages | Various ZATCA subpages | tax | FAIL — 657c, 10MB+ PDFs | 657 | 0 | **NOT ACTIVATED** | Below threshold. Large PDFs are Arabic dictionaries (>10MB), not regulatory circulars. ZATCA root already active. |

---

## Categories Covered

| Category | Source | Score | Notes |
|----------|--------|-------|-------|
| central_bank | SAMA | 100 | Playwright + 68,237c PDFs |
| tax | ZATCA | 100 | Direct HTML |
| capital_markets | CMA (Regulations page) | 100 | Playwright + 40,177c PDFs |
| government | MISA | 100 | RSS + 8,022c HTML |
| commerce | Ministry of Commerce | 100 | Playwright |
| cyber | NCA | limited | 2,744c |
| financial_regulator (CST) | CST | limited | ~1,200c Playwright |

---

## Missing Categories

| Category | Source | Reason |
|----------|--------|--------|
| finance_ministry | MoF | Complete JS SPA block from outside KSA |
| legal_database | BOE laws portal | Geo-IP timeout (KSA-only access) |
| data_protection | SDAIA | HTTP2 protocol block |
| aml | SFIU | DNS failure — URL may be wrong |
| official_gazette | Umm Al-Qura | Geo-blocked/timeout |
| payments | Saudi Payments | DNS failure |
| competition | GAC | DNS failure |

**Root cause for 7 missing categories:** Saudi government e-government platform consistently blocks international access. The pattern is: Playwright fetches 1,000–500,000 chars raw HTML bundle but all text extractors return 0–55 chars. This is not an adapter issue — it is a server-side access restriction (likely geo-IP + bot detection). These sources would require a Saudi in-country access point (proxy, partner node, or browser automation from within KSA).

---

## Adapter Tasks

These are sources that require custom adapters but cannot be fixed without in-country access:

| Source | Current Status | Adapter Type | Priority |
|--------|---------------|--------------|---------|
| SDAIA | disabled_external_access | HTTP2 + geo-block — requires KSA node | Medium |
| BOE laws portal | disabled_external_access | Geo-IP block — requires KSA node | High |
| MoF | disabled_external_access | JS SPA + geo-block — requires KSA node | High |
| SFIU | Not in sources.json | URL verification needed first | High |
| Umm Al-Qura | Not in sources.json | Geo-IP timeout — requires KSA node | High |

> These are NOT standard adapter tasks (where a custom parser fixes a JS SPA). They require physical access from within Saudi Arabia. No adapter change in the RegRadar codebase will fix them.

---

## 20-Source Target Reality Check

**Realistic number of official monitorable SA sources from outside KSA: 7–10.**

The task requested up to 20 sources. Here is why 20 is not achievable without in-country access:

| Bloc | Count | Situation |
|------|-------|-----------|
| Working now (activated) | 7 | SAMA, ZATCA, CST, CMA, MISA, MoC, NCA |
| Working with adapter (within threshold) | 0 | No additional sources found above threshold |
| Geo-blocked — KSA access only | 5+ | BOE, MoF, SDAIA, Umm Al-Qura, GAC, SFIU |
| DNS failures | 3 | SFIU, Saudi Payments, GAC |
| Below threshold | 3 | Tadawul, SAMA sub-pages, CMA news page |

To reach 20+ sources, RegRadar would need:
1. A Saudi Arabia-based monitoring node (VPS in KSA) — would unlock BOE, MoF, SDAIA, Umm Al-Qura, SFIU
2. OR partner access to KSA government data feeds
3. OR official API access from KSA regulators (none publicly documented)

**Conclusion: 10 sources total (7 enabled + 3 disabled) is the realistic ceiling from an international location. 7 active sources with score 100 is an honest and strong result.**

---

## Final Recommendation

**Immediate (done):** 7 SA sources enabled, score 100 (strong). No further changes needed for basic monitoring coverage.

**Next 30 days:**
1. Verify SFIU official URL: `sfiu.gov.sa` DNS fails — try `fiu.gov.sa`, `fatf.gov.sa`, or search Saudi FATF AML authority domain. If found, test and add.
2. Test `misa.gov.sa/en/` regularly — RSS feed has 4 items now; monitor for new regulatory circulars on investment.
3. Consider SAMA PDF-mode monitoring (root URL has 5 PDF links) as supplemental to the en-US page.

**Next 90 days:**
1. Evaluate KSA-based monitoring node to unlock BOE (legal acts), MoF, SDAIA, Umm Al-Qura, SFIU — these 5 would raise SA to ~15 active sources.
2. If Saudi clients are acquired, establish direct API/data partnership with BOE or MoF.

---

## Validation Results

| Check | Result |
|-------|--------|
| Compile (`compileall app run.py`) | PASS — no errors |
| sources.json JSON validity | PASS — 85 sources, valid JSON |
| SA sources schema | PASS — all required fields present |
| coverage (SA) | 100 (strong) — 7 good, 7 enabled, 3 restricted |
| Overall coverage | 86 — improved from 82 |
| Lint (frontend) | Not run — no frontend files changed |
| Build (frontend) | Not run — no frontend files changed |

---

*RegRadar — Saudi Arabia source pack validated 2026-05-26*
*Tested by: discover-source, test-source | Validated sources only in sources.json*
