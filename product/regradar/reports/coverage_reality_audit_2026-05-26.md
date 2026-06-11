# RegRadar — Coverage Reality Audit
**Date:** 2026-05-26  
**Sources inspected:** sources.json, data/source_candidates.json, data/market_strategy.json, reports/coverage_2026-05-26.json

---

## Executive Summary

**56 active enabled sources across 9 of 12 audited countries.**  
3 countries (BH, HK, MY) have zero sources — not usable for demos.  
1 country (AZ) has 1 active source — too thin for meaningful monitoring.  
4 countries are strong enough for first pilot demos right now (AE, SG, KZ, TR).

The most important finding: Azerbaijan has 4 pre-mapped sources with one marked `status=active` that could be enabled immediately after validation. It is the fastest path to meaningful coverage improvement.

Saudi Arabia's official coverage score is 54 (limited) despite 7 enabled sources — two are `status=limited` with poor extraction quality. This country needs quality remediation before it can anchor a pilot demo.

---

## Country Coverage Table

| # | Country | Enabled | Total | Score | Label | Good | Low | Fail | Adapter | Restricted | Demo Ready |
|---|---------|---------|-------|-------|-------|------|-----|------|---------|-----------|------------|
| 1 | **AE** | 7 | 10 | **100** | strong | 7 | 0 | 0 | 0 | 3 | ✅ YES |
| 2 | **SG** | 8 | 8 | **100** | strong | 8 | 0 | 0 | 0 | 0 | ✅ YES |
| 3 | **KZ** | 7 | 8 | **93** | strong | 7 | 0 | 1 | 1 | 0 | ✅ YES |
| 4 | **UZ** | 4 | 6 | **90** | strong* | 5 | 0 | 1 | 1 | 0 | ⚠️ PARTIAL |
| 5 | **GE** | 4 | 5 | **89** | strong | 4 | 1 | 0 | 1 | 0 | ✅ YES |
| 6 | **TR** | 9 | 9 | **83** | usable | 7 | 2 | 0 | 2 | 0 | ✅ YES |
| 7 | **AZ** | 1 | 5 | **67** | usable* | 3 | 1 | 1 | 2 | 0 | ❌ NO |
| 8 | **SA** | 7 | 10 | **54** | limited | 1 | 1 | 0 | 1 | 4 | ⚠️ PARTIAL |
| 9 | **BH** | 0 | 0 | — | — | — | — | — | — | — | ❌ NO |
| 10 | **QA** | 0 | 0 | — | — | — | — | — | — | — | ❌ NO |
| 11 | **HK** | 0 | 0 | — | — | — | — | — | — | — | ❌ NO |
| 12 | **MY** | 0 | 0 | — | — | — | — | — | — | — | ❌ NO |

> **Score notes:**  
> UZ score of 90 reflects extraction quality, not category breadth. Only 4 categories covered (central_bank + legal_acts only). Do not use UZ score as a proxy for commercial readiness.  
> AZ score of 67 reflects audit of all 5 sources including disabled ones. Operationally only 1 source is active.

---

## Tier Ranking (Commercial Priority × Technical Readiness)

### Tier 1 — Ready for demos and outreach

| Country | Score | Commercial | Enabled Sources | Notes |
|---------|-------|-----------|----------------|-------|
| UAE | 100 | High | 7 | Best demo country. All key categories. VARA, DFSA, ADGM, CBUAE, FIU. |
| Singapore | 100 | High | 8 | Best technical coverage. MAS, AML, tax, data, competition, company reg. |
| Kazakhstan | 93 | Medium | 7 | Strong Tier 1 Central Asia anchor. AIFC + full regulatory stack. |
| Turkey | 83 | High | 9 | 9 sources, 7 good quality. Minor quality issues on MASAK + Official Gazette. |

### Tier 2 — Usable as bundle additions; not standalone pilots

| Country | Score | Commercial | Enabled Sources | Notes |
|---------|-------|-----------|----------------|-------|
| Georgia | 89 | Medium | 4 | Good extraction, missing AML (disabled). Bundle with AZ. |
| Uzbekistan | 90 | Medium | 4 | Extraction quality high but category coverage too narrow for B2B compliance. Missing finance_ministry, tax, AML. |

### Tier 3 — Needs activation work before any demo

| Country | Score | Commercial | Enabled Sources | Notes |
|---------|-------|-----------|----------------|-------|
| Saudi Arabia | 54 | High | 7 | 2 limited-quality sources, 3 disabled key sources, AML missing entirely. High commercial value — must fix. |
| Azerbaijan | 67 | Medium | 1 | 1 active source only. 4 pre-mapped sources waiting for activation. Quick win. |

### Tier 4 — No sources yet; planning only

| Country | Sources | Commercial | Notes |
|---------|---------|-----------|-------|
| Bahrain | 0 | Medium | 4 candidates. GCC bundle add-on. |
| Qatar | 0 | Medium | 5 candidates. GCC bundle add-on. |
| Hong Kong | 0 | High | 1 candidate only. Evaluate after Tier 2 complete. |
| Malaysia | 0 | Medium | 4 candidates. Low priority. |

---

## Active Categories by Country

### AE — United Arab Emirates
| Category | Status |
|----------|--------|
| central_bank | ✅ Active (CBUAE) |
| financial_regulator | ✅ Active (VARA, DFSA, ADGM) |
| finance_ministry | ✅ Active |
| legal_acts | ✅ Active |
| aml | ✅ Active (UAEFIU) |
| tax | ❌ Disabled (FTA — external access restricted) |
| capital_markets / securities | ❌ Disabled (SCA — JS SPA, adapter needed) |
| data_protection | ❌ Missing (no validated source) |
| official_gazette | ❌ Missing (not available in extractable format) |
| company_registry | ❌ Missing |

### SA — Saudi Arabia
| Category | Status |
|----------|--------|
| central_bank | ✅ Active (SAMA) |
| tax | ✅ Active (ZATCA) |
| capital_markets | ✅ Active (CMA — but SPA adapter issue) |
| government | ✅ Active (MISA) |
| commerce | ✅ Active |
| cyber | ⚠️ Active but limited extraction (NCA) |
| financial_regulator / telecom | ⚠️ Active but limited extraction (CST) |
| finance_ministry | ❌ Disabled |
| legal_acts | ❌ Disabled (Laws Portal — external access) |
| aml / FIU | ❌ Missing entirely |
| data_protection | ❌ Missing (SDAIA disabled) |
| official_gazette | ❌ Missing (Umm Al-Qura not validated) |

### TR — Turkey
| Category | Status |
|----------|--------|
| central_bank | ✅ Active (TCMB) |
| financial_regulator | ✅ Active (BDDK, SPK, KVKK, Rekabet) |
| aml | ✅ Active (MASAK — some session issues) |
| legal_acts | ✅ Active (Official Gazette — PDF extraction limited) |
| tax | ✅ Active (GİB) |
| finance_ministry | ✅ Active (Hazine ve Maliye) |
| data_protection | ✅ Active (KVKK covers this) |
| crypto/VASP | ⚠️ Covered via BDDK/SPK but no dedicated VASP source |
| company_registry | ❌ Missing |
| draft_regulation | ❌ Missing (no centralized portal) |

### KZ — Kazakhstan
| Category | Status |
|----------|--------|
| central_bank | ✅ Active (NBK) |
| financial_regulator | ✅ Active (ARDFM, AIFC) |
| finance_ministry | ✅ Active |
| tax | ✅ Active (State Revenue Committee) |
| legal_acts | ✅ Active (Ministry of Justice) |
| aml | ✅ Active (Financial Monitoring Committee) |
| data_protection | ❌ Missing |
| company_registry | ❌ Missing |
| crypto/VASP | ❌ Missing (AIFC covers some but no dedicated source) |
| draft_regulation | ❌ Missing (regulation.gov.kz pending) |

### UZ — Uzbekistan
| Category | Status |
|----------|--------|
| central_bank | ✅ Active (CBU) |
| legal_acts | ✅ Active (Lex.uz, MoJ, Draft Portal) |
| finance_ministry | ❌ Disabled (status=limited) |
| tax | ❌ Disabled |
| aml / FIU | ❌ Missing entirely |
| financial_regulator | ❌ Missing (no capital markets regulator source) |
| capital_markets | ❌ Missing |

**UZ reality:** Extraction quality is high but category depth is too narrow for a standalone compliance monitoring product. Useful as a Central Asia bundle add-on only.

### GE — Georgia
| Category | Status |
|----------|--------|
| central_bank | ✅ Active (NBG) |
| tax | ✅ Active (Revenue Service) |
| legal_acts | ✅ Active (Matsne) |
| finance_ministry | ✅ Active |
| aml | ❌ Disabled (status=limited) |
| financial_regulator | ❌ Missing (NBG covers some but no dedicated regulator source) |
| crypto/VASP | ❌ Missing |
| competition | ❌ Missing |

### AZ — Azerbaijan
| Category | Status |
|----------|--------|
| central_bank | ✅ Active (CBA) |
| finance_ministry | ⛔ Disabled but `status=active` — ready for testing/enabling |
| tax | ⛔ Disabled `status=mapped` |
| aml | ⛔ Disabled `status=mapped` |
| legal_acts | ⛔ Disabled `status=mapped` (e-Qanun — adapter may be needed) |
| capital_markets | ❌ Missing |
| data_protection | ❌ Missing |

**AZ critical note:** Ministry of Finance AZ is `enabled=false` but `status=active` — it has been mapped and appears functionally accessible. This is the highest-priority single action for AZ: validate and enable it.

---

## Missing Categories by Country (High-Priority Gaps)

| Country | Critical Missing |
|---------|-----------------|
| AE | tax (FTA disabled), securities (SCA adapter needed), data_protection |
| SA | aml/FIU, finance_ministry, legal_acts, data_protection |
| TR | No critical gaps — minor: dedicated crypto/VASP, draft_regulation |
| KZ | No critical gaps — minor: data_protection, company_registry |
| UZ | finance_ministry, tax, aml/FIU, financial_regulator |
| GE | aml (disabled/limited) |
| AZ | finance_ministry (can enable), tax, aml, legal_acts — all pre-mapped |
| BH | ALL (zero sources) |
| QA | ALL (zero sources) |
| SG | No critical gaps — minor: dedicated crypto/DPT source |
| HK | ALL (zero sources) |
| MY | ALL (zero sources) |

---

## Sources Requiring Adapters or Remediation

| Source | Country | Issue | Category |
|--------|---------|-------|----------|
| SCA | AE | JS SPA — navigation-only, no HTML extraction | securities |
| UAE FTA | AE | External access restricted | tax |
| CMA | SA | SPA adapter needed for reliable extraction | capital_markets |
| CST | SA | Limited extraction (`status=limited`) | financial_regulator |
| NCA | SA | Limited extraction (`status=limited`) | cyber |
| SAMA (some sections) | SA | Potential geo-restriction on some pages | central_bank |
| MASAK | TR | Session-based navigation on some sections | aml |
| Official Gazette TR | TR | PDF parsing reliability | legal_acts |
| ARDFM PDFs | KZ | Filename-pattern detection needed | financial_regulator |
| Adilet | KZ | Pagination handling needed | legal_acts |
| Lex.uz | UZ | Session navigation on filter sections | legal_acts |
| Financial Monitoring GE | GE | Status=limited — content extraction issues | aml |
| e-Qanun AZ | AZ | Navigation handling likely needed | legal_acts |
| Ministry of Finance AZ | AZ | Unmapped — test first | finance_ministry |

---

## Countries to Activate Next (Prioritized)

### Priority 1 — Azerbaijan (fastest path to usable coverage)
- **Action:** Enable `Ministry of Finance Azerbaijan` (status=active, enabled=false)
- **Action:** Test and enable `State Tax Service of Azerbaijan` (status=mapped)
- **Action:** Test and enable `Financial Monitoring Service of Azerbaijan` (status=mapped)
- **Action:** Test `e-Qanun` (may need adapter for navigation)
- **Effort:** Low — 3 sources are pre-mapped, 1 is already status=active
- **Impact:** Goes from 1 active source to 4–5, covering all critical categories

### Priority 2 — Saudi Arabia (high commercial value, quality issues)
- **Action:** Fix CMA SPA extraction — most critical enabled source with quality problems
- **Action:** Test and enable Saudi Ministry of Finance (currently disabled_external_access)
- **Action:** Find and validate an AML/FIU source (Saudi FIU / GASTAT) — currently absent entirely
- **Action:** Test Saudi Bureau of Experts Laws Portal
- **Effort:** Medium — SPA adapter work + source validation
- **Impact:** Brings score from 54 to potentially 80+; critical for GCC pilot

### Priority 3 — Uzbekistan (fill category gaps)
- **Action:** Test and enable Ministry of Economy and Finance UZ (status=limited)
- **Action:** Test and enable State Tax Committee UZ
- **Action:** Research and add Uzbekistan FIU source
- **Effort:** Low-medium
- **Impact:** Adds 2–3 categories; makes UZ viable as a standalone offering

### Priority 4 — Georgia (fix AML)
- **Action:** Fix Financial Monitoring Service of Georgia extraction (status=limited)
- **Effort:** Low — single source fix
- **Impact:** Completes critical AML gap

### Priority 5 — Bahrain (new market)
- **Action:** Validate 4 candidates from source_candidates.json
- **Effort:** Medium (new source testing cycle)
- **Impact:** Adds first GCC bundle extension beyond AE and SA

---

## Recommended Order of Work

1. **AZ activation sprint** — 4 pre-mapped sources, low effort, high relative impact. Ministry of Finance already marked active.
2. **SA quality fix** — fix CST, NCA limited extraction, CMA SPA adapter. Find AML/FIU source. Enable Finance Ministry.
3. **UZ category expansion** — enable Finance Ministry + Tax. Add AML/FIU.
4. **GE AML fix** — re-test Financial Monitoring Service; fix or replace.
5. **BH source pack** — 4 known candidates; add as GCC bundle extension.
6. **QA source pack** — 5 known candidates; add after BH.
7. **AE secondary sources** — FTA tax source (if access issue resolved), SCA adapter.
8. **HK/MY** — evaluate after Tier 2 complete.

---

## Demo Readiness Summary

| Country | Demo Ready | Best Use Case |
|---------|-----------|---------------|
| UAE | ✅ Strong | Primary demo. VARA + CBUAE + DFSA + ADGM — crypto, banking, payments |
| Singapore | ✅ Strong | APAC demo. MAS + AML + data protection + competition — complete stack |
| Kazakhstan | ✅ Strong | Central Asia demo. AIFC focus for fintech/crypto clients |
| Turkey | ✅ Strong | Turkish compliance demo. Full regulatory stack |
| Georgia | ✅ Adequate | Caucasus bundle add-on. Missing AML is notable gap |
| Uzbekistan | ⚠️ Limited | Central Asia bundle only. Category breadth too narrow solo |
| Saudi Arabia | ⚠️ Partial | Use carefully — note limited extraction on 2 sources, no AML |
| Azerbaijan | ❌ Not ready | Only 1 active source. Do not use in demos |
| Bahrain | ❌ Not started | No sources |
| Qatar | ❌ Not started | No sources |
| Hong Kong | ❌ Not started | No sources |
| Malaysia | ❌ Not started | No sources |

---

## Files Inspected

| File | Purpose |
|------|---------|
| `sources.json` | Primary source of truth for active coverage |
| `reports/coverage_2026-05-26.json` | Extraction quality scores per jurisdiction |
| `data/source_candidates.json` | Planning data — not active coverage |
| `data/market_strategy.json` | Commercial tier and strategy context |

> **Reminder:** Only sources in `sources.json` with `enabled: true` count as active coverage. `source_candidates.json` is planning-only. Scores in this report are extracted from the last health audit run (2026-05-25 source audit, coverage computed 2026-05-26). Run `python run.py health` to refresh.

---

## Exact Next Country to Process

**Azerbaijan (AZ)** — Ministry of Finance AZ has `status=active, enabled=false`. This is the single highest-priority action: test the source URL with `python run.py test-source <url>`, validate extraction quality, then enable it. This alone adds a critical missing category. Follow with Tax Service and Financial Monitoring Service (both mapped).

Estimated work: 1–2 hours for full AZ pack activation (test + enable 3–4 sources, update HANDOFF).
