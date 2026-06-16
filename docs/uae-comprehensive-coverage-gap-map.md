# UAE Comprehensive Coverage Gap Map

Date: 2026-06-17
Based on: uae_source_universe_candidates.json (203 records, 79 already-active, 92 new candidates, 32 rejected)

This document maps current monitoring coverage against the known UAE official regulatory universe and identifies gaps by buyer archetype, regulator, and regulatory domain.

---

## 1. Coverage Matrix by Regulator

| Regulator | Known Endpoints | Currently Active | Gap (Not Active) | Gap % |
|-----------|----------------|-----------------|-----------------|-------|
| CBUAE | 40 | 27 | 13 | 33% |
| DFSA | 19 | 10 | 9 | 47% |
| ADGM/FSRA | 22 | 10 | 12 | 55% |
| VARA | 20 | 9 | 11 | 55% |
| UAE FIU/EOCN | 16 | 7 | 9 | 56% |
| SCA | 15 | 5 | 10 | 67% |
| DIFC | 13 | 8 | 5 | 38% |
| Federal/Legislation | 11 | 3 | 8 | 73% |
| FTA | 7 | 0 | 7 | 100% |
| Free Zone/Other | 8 | 0 | 8 | 100% |
| **TOTAL** | **171** | **79** | **92** | **54%** |

Reading: 54% of the known UAE regulatory source universe is not yet actively monitored. This is the maximum activation ceiling — not all 92 gaps need activation; some are P2/P3 or require Playwright.

---

## 2. Critical Gaps by Buyer Archetype

### VASP / MLRO (Primary Target Buyer)

Current VARA coverage: 9 active sources, mostly PDFs (6) + enforcement + homepage + rulebook-updates.

**Critical VARA gaps:**
- `AE-vara-regulatory-framework` — Main VARA regulatory framework hub. URL broken (404). High risk of MLRO missing framework-level changes.
- `AE-vara-company-rulebook` — Company-level rulebook (applies to all VASPs). URL broken; superseded by PDF version but no live page monitoring.
- `AE-vara-aml-cft-rulebook` — VARA AML/CFT rulebook page. URL broken; AML monitoring is the #1 MLRO need.
- `AE-vara-guidance` — VARA regulatory guidance. Not in any active source. New regulatory interpretations not captured.
- `AE-vara-administrative-orders` — Administrative orders to specific VASPs. High-signal enforcement monitoring gap.
- `AE-vara-activity-rulebooks-hub` — Main rulebooks hub at rulebooks.vara.ae (not the PDF versions). Hub page changes not tracked.

**Impact on sales pitch:** Any VASP MLRO buyer will ask "can you monitor the VARA regulatory framework hub?" — current answer is no (404 status). This is the most damaging gap.

**FIU gaps affecting MLROs:**
- `AE-uaefiu-nra-2024` — NRA 2024 not monitored. This is the most important single document for MLRO risk assessment.
- `AE-uaefiu-strategic-analysis` — Strategic analysis guidelines not monitored.
- `AE-uaefiu-mutual-evaluation` — UAE FATF MER not monitored.

### CBUAE Bank / Payments CCO

Current CBUAE coverage is strong at 27 sources (strongest regulator by volume).

**Remaining gaps:**
- `AE-cbuae-aml-cft` — CBUAE AML/CFT operations page (work queue candidate, not yet activated).
- `AE-cbuae-consultations` — CBUAE consultations page (not active). Horizon scanning gap.
- `AE-cbuae-publications` — CBUAE publications hub (not active). Reports and working papers not tracked.
- `AE-cbuae-circular-bank-supervision` — Bank supervision circulars not active. Targeted guidance to banks missed.
- `AE-cbuae-insurance-supervision` — Insurance regulation gap.
- `AE-cbuae-net-stable-funding-doclist` — NSFR regulation section not added to rulebook pack.

**Assessment:** CBUAE coverage is the strongest. Remaining gaps are P1–P2 and addressable.

### DFSA / DIFC Firm CCO

Current DFSA coverage: 10 active sources including AML rulebook, enforcement, consultation papers.

**Remaining gaps:**
- `AE-dfsa-guidance-notes` — DFSA guidance notes not monitored. This is a common practitioner reference source.
- `AE-dfsa-policy-statements` — Policy statements not monitored.
- `AE-dfsa-publications` — Publications hub not active (umbrella for guidance notes, policy statements, annual reports).
- `AE-dfsa-annual-reports` — Annual reports not tracked.

**Assessment:** DFSA coverage is solid. Guidance notes and policy statements are the main gap.

### SCA / Securities CCO

Current SCA coverage: 5 sources (AML/CFT, regulations listing, FATCA/CRS, corporate governance, circulars).

**Critical SCA gaps:**
- `AE-sca-laws` — SCA securities laws not active. Primary legislation monitoring gap.
- `AE-sca-decisions` — SCA board decisions not active. Rule-making decisions not tracked.
- `AE-sca-regulations-amendments` — Regulation amendments not tracked.
- `AE-sca-market-rules` — Exchange market rules not tracked.
- `AE-sca-investment-funds` — Fund regulation not tracked.
- `AE-sca-disclosure` — Disclosure obligations not tracked.

**Assessment:** SCA is the second most under-covered major regulator after FTA. Securities CCO buyers would find the current pack weak.

### ADGM Firm CCO

Current ADGM coverage: 10 active sources.

**Remaining gaps:**
- `AE-adgm-fsra-notices` — FSRA regulatory notices not active.
- `AE-adgm-media-announcements` — Media/regulatory announcements not active.
- `AE-adgm-ra-notices` — Registration authority notices not active.
- `AE-adgm-ra-aml-guides` — RA AML/CFT guides for DNFBPs not active.
- `AE-adgm-dp-hub` — Data protection hub not active.
- `AE-adgm-co-circulars` — Companies Office circulars not active.

**Assessment:** ADGM coverage is moderate. The missing RA notices and DNFBP AML guides are the most commercially relevant gaps.

---

## 3. Domain Coverage Gaps

### AML/CFT Monitoring Domain

| Domain Component | Coverage Status |
|-----------------|----------------|
| CBUAE AML/CFT rulebook | ✅ Active |
| DFSA AML rulebook | ✅ Active |
| ADGM FSRA financial crime | ✅ Active |
| UAE FIU AML laws | ✅ Active |
| UAE FIU typologies | ✅ Active |
| EOCN AML laws | ✅ Active |
| VARA AML/CFT rulebook (live page) | ❌ 404 gap |
| SCA AML/CFT | ✅ Active |
| UAE NRA 2024 | ❌ Not monitored |
| FATF Mutual Evaluation Report | ❌ Not monitored |
| ADGM RA DNFBP AML guides | ❌ Not monitored |
| MoE AML DNFBP hub | ❌ Not monitored |

### Enforcement Monitoring Domain

| Domain Component | Coverage Status |
|-----------------|----------------|
| DFSA enforcement decisions | ✅ Active |
| DFSA regulatory actions | ✅ Active |
| ADGM FSRA enforcement | ✅ Active |
| VARA enforcement | ✅ Active |
| SCA violations register | ❌ Not monitored |
| DIFC data protection enforcement | ❌ Not monitored |
| ADGM data protection regulatory actions | ❌ Not monitored |

### Consultation / Horizon Scanning Domain

| Domain Component | Coverage Status |
|-----------------|----------------|
| DFSA consultation papers | ✅ Active |
| ADGM FSRA consultations | ✅ Active |
| CBUAE consultations | ❌ Not monitored (candidate) |
| SCA consultations | ❌ Not tracked in universe |
| DIFC consultation papers | ❌ Not monitored |

### Data Protection Domain

| Domain Component | Coverage Status |
|-----------------|----------------|
| DIFC data protection (full pack) | ✅ Active (8 sources) |
| ADGM data protection guidance | ✅ Active |
| ADGM data protection enforcement | ❌ Not monitored |
| UAE Federal Data Office (PDPL) | ❌ Not monitored |
| TDRA digital regulations | ❌ Not monitored |

### Tax / Corporate Domain

| Domain Component | Coverage Status |
|-----------------|----------------|
| FTA corporate tax guides | ❌ Not monitored |
| FTA VAT clarifications | ❌ Not monitored |
| UAE Legislation Portal | ✅ Active |
| Ministry of Finance | ✅ Active |
| Ministry of Economy | ✅ Active |
| MoJ e-laws | ❌ Not monitored |
| Ministry of Economy AML DNFBP | ❌ Not monitored |

---

## 4. Gap Severity Ranking

### Severity 1 — Business-Critical Gaps (Fix First)

1. **VARA AML/CFT rulebook page** — Most important single gap for VASP MLRO buyers. URL broken; needs Playwright + URL update.
2. **UAE FIU NRA 2024** — Single most cited MLRO document; not tracked at all.
3. **VARA regulatory framework hub** — Framework-level VARA monitoring gap; URL broken.
4. **CBUAE consultations page** — Horizon scanning gap for the bank/payments buyer.
5. **SCA laws and board decisions** — Primary securities legislation not monitored.

### Severity 2 — High Commercial Value, Low Technical Risk

6. AE-cbuae-aml-cft (work queue candidate, just needs activation)
7. AE-adgm-ra-aml-guides (DNFBP MLRO gap)
8. AE-dfsa-guidance-notes
9. AE-uaefiu-strategic-analysis
10. AE-sca-regulations-amendments

### Severity 3 — Useful But Not Urgent

11. AE-fta-corporate-tax-guides
12. AE-adgm-media-announcements
13. AE-moec-aml-dnfbp
14. AE-uaefiu-mutual-evaluation
15. AE-adgm-fsra-notices

### Severity 4 — Niche / Low Priority

16–30: Free zone sources, emirate-level sources, TDRA, social media-adjacent monitoring

---

## 5. Technical Gap Analysis

### Gaps Due to JS-Heavy Pages (Playwright Required)

These sources exist in the universe but cannot be activated with bs4/requests:
- AE-vara-regulatory-framework (404 in bs4, needs Playwright)
- AE-vara-company-rulebook (404 in bs4, may be accessible in Playwright)
- AE-cbuae-aml-cft (Umbraco CMS, 403 to bs4)
- AE-cbuae-consultations (Umbraco CMS)
- AE-cbuae-publications (Umbraco CMS)
- AE-dfsa-publications (JS-heavy)
- AE-dfm-market-rules (JS SPA timeout)

### Gaps Due to URL Changes (Need Re-Research)

- AE-vara-aml-cft-rulebook — Old URL 404; may exist at new path
- AE-vara-company-rulebook — Old URL 404; may exist at new path
- AE-vara-rulebooks-overview — Old URL 404; replaced by rulebooks.vara.ae hub

### Gaps Due to Access Restrictions

- AE-adx-regulation — 403 blocked
- AE-dfm-market-rules — timeout (WAF likely)
- AE-moec-aml-dnfbp — Unknown status; site may block automated access

### Gaps Due to No Prior Research

- All 7 FTA sources — never attempted; likely accessible (FTA site is public)
- AE-uae-data-office — Federal Data Office; new domain, no prior testing
- AE-dld-aml — Dubai Land Department; new, no prior testing

---

## 6. Priority Activation Queue (Top 15)

Based on this gap analysis, the following should enter the activation queue in the next sprint:

| Rank | Source ID | Priority | Reason |
|------|-----------|----------|--------|
| 1 | AE-vara-activity-rulebooks-hub | P1 | VARA rulebook hub accessible at rulebooks.vara.ae |
| 2 | AE-vara-guidance | P1 | VARA guidance — domain crawl candidate; needs no-save |
| 3 | AE-uaefiu-nra-2024 | P1 | UAE NRA — likely static PDF page; easy activation |
| 4 | AE-cbuae-aml-cft | P1 | Already in work queue; needs activation gate |
| 5 | AE-adgm-ra-aml-guides | P1 | DNFBP gap; ADGM RA PDF listing — known adapter |
| 6 | AE-dfsa-guidance-notes | P1 | DFSA guidance; low technical risk |
| 7 | AE-uaefiu-strategic-analysis | P1 | Static FIU page; low technical risk |
| 8 | AE-sca-laws | P1 | SCA primary legislation; known SCA adapter pattern |
| 9 | AE-sca-decisions | P1 | SCA board decisions; known pattern |
| 10 | AE-fta-corporate-tax-guides | P2 | FTA new coverage; likely accessible |
| 11 | AE-adgm-media-announcements | P1 | ADGM custom_element; confirmed accessible |
| 12 | AE-adgm-ra-notices | P1 | ADGM RA notices; same adapter pattern |
| 13 | AE-moec-aml-dnfbp | P1 | MoE AML DNFBP; new coverage |
| 14 | AE-uaefiu-mutual-evaluation | P1 | UAE FATF MER; static PDF |
| 15 | AE-difc-consultation-papers | P1 | DIFC consultations; horizon scanning |

---

## 7. What Would Close the Most Important Gaps

To go from 79 active to a 100-source pack that covers all critical buyer archetypes:

1. Resolve VARA URL paths (regulatory-framework, company-rulebook, aml-cft) via Playwright verification — adds 3 high-value VARA sources
2. Activate top 15 from priority queue above — adds ~15 sources
3. FTA coverage (corporate tax, VAT) — adds 3–4 sources
4. SCA laws, decisions, amendments — adds 3 sources
5. ADGM RA notices, AML guides, media announcements — adds 3 sources

Achievable total: **~105–110 active sources** within the next 2 activation sprints without requiring new adapter development.

---

## 8. Disclaimer

This coverage map is based on publicly known UAE official regulatory endpoints as of 2026-06-17. It represents research-level estimates of the monitoring universe. StatuteProof does not claim comprehensive UAE regulatory coverage and does not guarantee any specific level of completeness. Regulatory websites change structure, URLs, and access policies. Source monitoring may be affected by website changes, access restrictions, PDF formatting changes, and publication delays.
