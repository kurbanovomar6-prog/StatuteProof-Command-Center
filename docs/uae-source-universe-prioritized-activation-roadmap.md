# UAE Source Universe Prioritized Activation Roadmap

Date: 2026-06-17
Based on: uae_source_universe_candidates.json (203 records)
Current state: 79 active / 76 readiness-supported / 3 remediation

This roadmap lists all non-active source candidates ranked by activation priority. No source should be activated without passing the full gate sequence: no-save preview → evidence save → repeat baseline → mass-monitor dry-run → 6-agent review gate.

---

## Tier P0 — Activate as Soon as Possible (Top 25)

These are the highest commercial value, lowest technical risk candidates. Most can be activated with existing adapter families.

| # | Source ID | Regulator | Why P0 | Adapter Estimate | Gate Risk |
|---|-----------|-----------|--------|-----------------|-----------|
| 1 | AE-vara-activity-rulebooks-hub | VARA | Main VARA rulebook hub at rulebooks.vara.ae — supplements active PDFs | listing | Low |
| 2 | AE-vara-guidance | VARA | Regulatory guidance — VASP MLRO need #1 | custom_element | Medium |
| 3 | AE-vara-administrative-orders | VARA | Administrative orders — high-signal enforcement monitoring | listing | Medium |
| 4 | AE-uaefiu-nra-2024 | UAE FIU | UAE NRA 2024 — most cited single MLRO document | pdf_listing | Low |
| 5 | AE-uaefiu-strategic-analysis | UAE FIU | FIU strategic analysis guidelines — MLRO awareness | listing | Low |
| 6 | AE-uaefiu-mutual-evaluation | UAE FIU | UAE FATF MER — top-level compliance context | pdf_listing | Low |
| 7 | AE-cbuae-aml-cft | CBUAE | AML/CFT operations page — bank MLRO gap | custom_element | Medium |
| 8 | AE-cbuae-consultations | CBUAE | CBUAE consultations — horizon scanning gap | listing | Medium |
| 9 | AE-cbuae-circular-bank-supervision | CBUAE | Bank supervision circulars — targeted guidance | listing | Medium |
| 10 | AE-adgm-ra-aml-guides | ADGM | RA AML/CFT guides for DNFBPs — DNFBP MLRO gap | pdf_listing | Low |
| 11 | AE-adgm-ra-notices | ADGM | RA notices — registered entity compliance | custom_element | Low |
| 12 | AE-adgm-media-announcements | ADGM | ADGM FSRA regulatory announcements — confirmed accessible | custom_element | Low |
| 13 | AE-adgm-fsra-notices | ADGM | FSRA regulatory notices — formal supervisory comms | custom_element | Low |
| 14 | AE-dfsa-guidance-notes | DFSA | DFSA guidance notes — common practitioner reference | listing | Medium |
| 15 | AE-dfsa-rulebook-official | DFSA | DFSA laws and rules official page | listing | Medium |
| 16 | AE-dfsa-aml-ctf-sanctions | DFSA | DFSA AML/CTF hub page | custom_element | Medium |
| 17 | AE-sca-laws | SCA | SCA securities laws — primary legislation gap | listing | Low |
| 18 | AE-sca-decisions | SCA | SCA board decisions — rule-making decisions | listing | Low |
| 19 | AE-sca-regulations-amendments | SCA | SCA regulation amendments — change tracking | listing | Low |
| 20 | AE-moec-aml-dnfbp | MoE | Ministry of Economy AML for DNFBPs | custom_element | Medium |
| 21 | AE-difc-consultation-papers | DIFC | DIFC consultations — horizon scanning | listing | Medium |
| 22 | AE-uaefiu-annual-reports | UAE FIU | FIU annual reports — statistics and trends | listing | Low |
| 23 | AE-uaefiu-press-releases | UAE FIU | FIU press releases — regulatory announcements | listing | Low |
| 24 | AE-dfsa-publications | DFSA | DFSA publications hub | listing | Medium |
| 25 | AE-cbuae-publications | CBUAE | CBUAE publications hub | listing | Medium |

**Estimated outcome of P0 activation:** 79 + 25 = ~104 active sources. Closes VARA guidance, FIU NRA, CBUAE consultations, and SCA primary legislation gaps.

---

## Tier P1 — High Priority, Activate Next (50 sources)

These are commercially valuable but have moderate technical complexity or lower immediate need compared to P0.

| # | Source ID | Regulator | Category | Notes |
|---|-----------|-----------|----------|-------|
| 26 | AE-cbuae-consumer-protection | CBUAE | C-CBUAE | Consumer protection page (work queue candidate) |
| 27 | AE-cbuae-licensing | CBUAE | C-CBUAE | CBUAE licensed entities (work queue candidate) |
| 28 | AE-cbuae-fintech-office | CBUAE | C-CBUAE | CBUAE fintech regulation |
| 29 | AE-cbuae-net-stable-funding-doclist | CBUAE | C-CBUAE | NSFR rulebook section |
| 30 | AE-dfsa-policy-statements | DFSA | D-DFSA | DFSA policy statements |
| 31 | AE-dfsa-annual-reports | DFSA | D-DFSA | DFSA annual reports |
| 32 | AE-dfsa-consultation-papers | DFSA | D-DFSA | DFSA consultation papers subpage |
| 33 | AE-dfsa-public-register | DFSA | D-DFSA | DFSA public register |
| 34 | AE-adgm-ra-regulations | ADGM | E-ADGM | ADGM RA regulations |
| 35 | AE-adgm-dp-regulatory-actions | ADGM | E-ADGM | Data protection enforcement actions |
| 36 | AE-adgm-dp-hub | ADGM | E-ADGM | ADGM data protection hub |
| 37 | AE-adgm-fsra-public-register | ADGM | E-ADGM | ADGM public entity register |
| 38 | AE-adgm-co-circulars | ADGM | E-ADGM | Companies Office circulars |
| 39 | AE-sca-market-rules | SCA | F-SCA | SCA market rules |
| 40 | AE-sca-violations | SCA | F-SCA | SCA violations register |
| 41 | AE-sca-investment-funds | SCA | F-SCA | Fund regulation |
| 42 | AE-sca-disclosure | SCA | F-SCA | Disclosure obligations |
| 43 | AE-sca-news | SCA | F-SCA | SCA news |
| 44 | AE-difc-data-protection | DIFC | G-DIFC | DIFC DP regulatory hub |
| 45 | AE-difc-financial-crime | DIFC | G-DIFC | DIFC Financial Crime Authority |
| 46 | AE-uae-legislation-aml | Legislation | H-Federal | AML/CFT federal legislation |
| 47 | AE-uae-legislation-financial | Legislation | H-Federal | Financial laws |
| 48 | AE-uae-elaws-moj | MoJ | H-Federal | MoJ e-laws portal |
| 49 | AE-moj-federal-laws | MoJ | H-Federal | MoJ federal laws |
| 50 | AE-moec-regulations | MoE | H-Federal | MoE regulations |
| 51 | AE-fta-corporate-tax-guides | FTA | I-Tax | Corporate tax guides |
| 52 | AE-fta-vat-public-clarifications | FTA | I-Tax | VAT clarifications |
| 53 | AE-fta-vat-guides | FTA | I-Tax | VAT guides |
| 54 | AE-fta-country-by-country | FTA | I-Tax | CBC reporting |
| 55 | AE-federal-tax-authority-homepage | FTA | I-Tax | FTA anchor |
| 56 | AE-vara-public-register | VARA | A-VARA | VARA public entity register |
| 57 | AE-vara-licensing-conditions | VARA | A-VARA | VARA licensing conditions |
| 58 | AE-uaefiu-goaml-public | UAE FIU | B-FIU-EOCN | goAML public guidance |
| 59 | AE-uaefiu-awareness | UAE FIU | B-FIU-EOCN | FIU awareness publications |
| 60 | AE-uaefiu-open-data | UAE FIU | B-FIU-EOCN | FIU open data |
| 61 | AE-eocn-tfs | EOCN | B-FIU-EOCN | TFS framework page (high-velocity caution) |
| 62 | AE-cbuae-insurance-supervision | CBUAE | C-CBUAE | Insurance regulation |
| 63 | AE-cbuae-financial-stability-report | CBUAE | C-CBUAE | Financial stability reports |
| 64 | AE-adgm-federal-legislation | ADGM | E-ADGM | Federal legislation in ADGM |
| 65 | AE-adgm-listing-announcements | ADGM | E-ADGM | Listing authority announcements |
| 66 | AE-adgm-fsra-rules-fsra-domain | ADGM | E-ADGM | FSRA rulebooks alternate domain |
| 67 | AE-sca-corporate-governance (already active) | SCA | — | Already active |
| 68 | AE-dfsa-supervisory-risk-appetite | DFSA | D-DFSA | Risk appetite statements |
| 69 | AE-difc-insurance | DIFC | G-DIFC | Insurance regulation |
| 70 | AE-difc-courts-decisions | DIFC | G-DIFC | DIFC courts judgments |
| 71 | AE-uae-data-office | UAE Data | J-FreeZone | Federal data protection |
| 72 | AE-dld-aml | DLD | J-FreeZone | Dubai Land Dept AML |
| 73 | AE-dmcc-compliance | DMCC | J-FreeZone | DMCC AML/compliance |
| 74 | AE-moec-media-publications | MoE | H-Federal | MoE publications |
| 75 | AE-uae-legislation-commercial | Legislation | H-Federal | Commercial laws |

---

## Tier P2 — Useful, Lower Urgency (75 sources)

These sources add breadth or serve niche buyer segments. Activate only when P0 and P1 are complete and stable.

**Categories included:**
- CBUAE open data, payment systems (low commercial signal)
- CBUAE news (high churn, low compliance signal)
- SCA sustainable finance, fintech sandbox (niche)
- VARA news (high churn, low compliance signal)
- VARA market oversight (new, unverified)
- ADGM abu dhabi legislation (context only)
- DFSA crowdfunding (niche)
- FTA excise tax, tax procedures (niche)
- TDRA telecommunications (niche)
- MENAFATF statements (adjacent reference)
- Free zone sources: SAIF Zone, Ajman FZ (very niche)
- DFM market rules (timeout in testing, needs Playwright)
- DIFC employment law (niche)
- All additional CBUAE and SCA subpages beyond P0/P1 set

**Note:** Many P2 sources need no-save testing before gate evaluation. Do not skip the gate sequence even for P2.

---

## Tier REMEDIATION — Fix Before Activating

These are known broken/blocked sources that need investigation before activation attempts:

| Source ID | Issue | Remediation Action Needed |
|-----------|-------|--------------------------|
| AE-vara-regulatory-framework | 404 — URL path changed | Find new VARA framework URL via browser; update candidate record |
| AE-vara-company-rulebook | 404 — URL path changed | Find new URL; may be at rulebooks.vara.ae subpage |
| AE-vara-aml-cft-rulebook | 404 — URL path changed | Find new URL; may be PDF at rulebooks.vara.ae |
| AE-vara-rulebooks-overview | 404 — URL path changed | Replace with AE-vara-activity-rulebooks-hub |
| AE-uaefiu-guidance | Same URL as AE-uaefiu-circulars | Verify if distinct content; merge or close |
| AE-difc-legislation | Old difc.ae domain | Verify if accessible; use difc.com canonical |
| AE-adgm-fsra-rules-fsra-domain | Needs URL verification | Check if same content as adgm.com rulebooks |

---

## Tier REJECTED — Do Not Activate

32 sources are in the rejected array of uae_source_universe_candidates.json. These must not be added to sources.json. See the deduplication report for documented reasons.

Key rejected categories:
- URL 404 / path changed (7)
- 403 access blocked (3)
- Login/private portal (3)
- Duplicate of existing active source (5)
- Homepage-only superseded (5)
- Wrong country / non-UAE (2)
- Not official source (4)
- Site down (1)
- JS SPA timeout with no Playwright path (2)

---

## Activation Gate Reminder

**Every source, regardless of priority, must pass:**
1. No-save preview — extract content, check quality score (must be ≥60 for most sources), confirm not NAV_SHELL_ONLY
2. Evidence save — save proof artifact with hash and timestamp
3. Repeat baseline — run second check, confirm hash stability
4. Mass-monitor dry-run — batch test without saving new data
5. Agent review gate — Source Monitor, Evidence Trail, QA, Legal Language, Product Manager, Code Architect must all approve

No source bypasses any gate. P0 priority means "attempt activation first," not "skip gates."

---

## Roadmap Timeline Estimate

| Phase | Sources | Estimated Sprint Duration |
|-------|---------|--------------------------|
| P0 activation (25 sources) | ~104 total active | 2–3 weeks |
| P1 activation (50 sources) | ~145 total active | 4–6 weeks |
| P2 activation (subset) | ~160–170 total active | 8–12 weeks |
| Remediation resolution | 3–7 additional | 1–2 weeks per source |

These estimates assume one person working part-time on source activation. Each source requires ~2–4 hours of no-save testing, evidence review, and gate processing.

---

## What 100 Active Sources Enables Commercially

At 100 active sources (P0 complete), StatuteProof can credibly position as:
- "100+ official UAE regulatory endpoints monitored with evidence"
- All major UAE regulators covered: CBUAE, DFSA, ADGM, VARA, UAE FIU, SCA, DIFC
- Full AML/CFT monitoring across all major regulatory families
- VARA regulatory guidance monitoring (P0 priority)
- SCA primary legislation monitoring
- CBUAE consultation horizon scanning

This is the commercial threshold for the $399 UAE Monitor tier upgrade from the $199 founding pilot.
