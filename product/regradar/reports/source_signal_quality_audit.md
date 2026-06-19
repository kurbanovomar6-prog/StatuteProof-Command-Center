# StatuteProof Source Signal Quality Audit
**Audit Date:** 2026-06-19
**Auditor:** StatuteProof Source Quality Auditor v1
**Scope:** All 226 enabled UAE sources in sources.json

---

## Executive Summary

**Total enabled sources:** 226

| Tier | Count | Meaning |
|------|-------|---------|
| Tier A — Commercially critical | 136 | Primary regulations, rulebooks, circulars, enforcement, AML/CFT documents |
| Tier B — Useful official context | 21 | Listing pages, annual reports, discovery indexes, sub-pages |
| Tier C — Low signal / static | 60 | Individual static notice pages, homepages, duplicates |
| Remediation — Important but broken | 9 | SCA (5), EOCN (2), UAE FIU homepage (1), UAE Legislation Portal (1) |
| Exclude/Review | 0 | None classified as fully excludable |
| **Commercially meaningful (A+B)** | **157** | |

Of the 226 enabled sources, 138 are Tier A — genuinely actionable regulatory text that a paying client would care about. The 60 Tier C sources are individual static notice pages, homepages, and near-duplicates that create monitoring volume but not monitoring value. Nine sources are in remediation: SCA has no MONITOR_OK yet despite having proof paths, EOCN has direct access constraints, the UAE FIU homepage remains a generic placeholder, and the UAE Legislation Portal has WAF issues. This is a solid UAE regulatory coverage set, but the 60 Tier C entries inflate the count by 27% without contributing commercial value. Removing or demoting those entries would produce a cleaner claim of approximately 157 commercially meaningful monitored sources.

---

## Brutal Truth

Of the 226 sources claimed as monitoring-active, 60 (27%) are individual static pages (DFSA notice pages, DIFC news pages, ADGM announcement pages) that will never meaningfully change once published, plus three generic homepages. A real MLRO, VASP compliance officer, or tax director would not pay for monitoring of "DFSA News Notice Amendments Rulebook 4" — they expect monitoring of the DFSA rulebook itself, which is already covered by better sources. The meaningful commercial coverage is 157 sources (138 Tier A + 19 Tier B).

More seriously: SCA has 5 sources with proof paths but zero MONITOR_OK runs. Until those confirm, SCA — a major securities and capital markets regulator — has no verified live coverage. The EOCN, which manages UAE targeted financial sanctions lists (a daily MLRO concern), has 2 sources with no MONITOR_OK. For a product selling to MLROs and VASPs in the UAE, unconfirmed SCA and EOCN monitoring are material gaps.

The 149 sources with MONITOR_OK are the real product. The additional 77 sources with only proof paths or hashes but no MONITOR_OK are baselines-in-progress, not live monitoring.

---

## Tier A Sources — Most Commercially Valuable (138 sources)

### CBUAE Rulebook (25 sources)
All 25 are `rulebook.centralbank.ae` specific regulation pages — the canonical source for UAE Central Bank regulation for licensed financial institutions (banks, payment service providers, fintech). These are Tier A because any text change triggers a direct compliance obligation review.

| URL (abbreviated) | Regulation |
|---|---|
| rulebook.centralbank.ae/en/rulebook/amlcft | AML/CFT Rulebook |
| rulebook.centralbank.ae/en/rulebook/payment-token-services-regulation | Payment Token Services |
| rulebook.centralbank.ae/en/rulebook/retail-payment-services-and-card-schemes-regulation | Retail Payment Services |
| rulebook.centralbank.ae/en/rulebook/open-finance-regulation | Open Finance |
| rulebook.centralbank.ae/en/rulebook/consumer-protection-regulation | Consumer Protection |
| rulebook.centralbank.ae/en/rulebook/capital-adequacy | Capital Adequacy |
| rulebook.centralbank.ae/en/rulebook/stored-value-facilities | Stored Value Facilities |
| rulebook.centralbank.ae/en/rulebook/exchange-business-regulation | Exchange Business |
| rulebook.centralbank.ae/en/rulebook/risk-management | Risk Management |
| rulebook.centralbank.ae/en/rulebook/market-risk-regulation | Market Risk |
| rulebook.centralbank.ae/en/rulebook/operational-risk-regulation | Operational Risk |
| rulebook.centralbank.ae/en/rulebook/large-exposures-regulation | Large Exposures |
| rulebook.centralbank.ae/en/rulebook/country-and-transfer-risk-regulation | Country/Transfer Risk |
| rulebook.centralbank.ae/en/rulebook/interest-rate-and-rate-return-risk-banking-book-regulation | Interest Rate/Return Risk |
| rulebook.centralbank.ae/en/rulebook/model-management-standards | Model Management |
| rulebook.centralbank.ae/en/rulebook/retail-payment-systems-regulation | Retail Payment Systems |
| rulebook.centralbank.ae/en/rulebook/small-medium-sized-enterprises-sme-customer-protection-regulation | SME Protection |
| rulebook.centralbank.ae/en/rulebook/standard-re-risk-management-requirements-islamic-banks | Islamic Banks Risk |
| rulebook.centralbank.ae/en/rulebook/market-conduct-consumer-protection | Market Conduct |
| rulebook.centralbank.ae/en/rulebook/guidance-licensed-financial-institutions-risks-related-proliferation-finance | Proliferation Finance |
| rulebook.centralbank.ae/en/rulebook/guidance-licensed-financial-institutions-risks-related-trade-based-money-laundering-... | TBML Guidance |
| rulebook.centralbank.ae/en/rulebook/large-value-payment-systems-regulation | Large Value Payments |
| rulebook.centralbank.ae/en/rulebook/federal-decree-law-no-6-2025-... | Federal Decree Law 6/2025 |
| rulebook.centralbank.ae/en/view-revision-updates | CBUAE Revision Updates Index |
| rulebook.centralbank.ae/en/entiresection/644 | AML/CFT Entire Section |

**Note:** None of the 25 CBUAE rulebook sources have a MONITOR_OK recorded yet (0/25). All have proof paths and hashes. They are baselines-in-progress, not confirmed live monitoring. This is a critical gap for the product's core claim.

### VARA (24 sources)
VARA rulebook PDFs (all major service rulebooks: Compliance/Risk, Technology, VA Issuance, Broker-Dealer, Lending, Exchange, VA Management/Investment, Company, Advisory, Transfer/Settlement, Custody, Market Conduct), plus the revision updates listing and enforcement notices page. 16/24 have MONITOR_OK.

### DFSA (11 sources)
- DFSA Rules and Standards listing
- DFSA Financial Crime Prevention Notices and MLRO Letters
- DFSA AML Rulebook Module (Thomson Reuters)
- DFSA Rulebook Modules listing (Thomson Reuters)
- DFSA Consultation Papers listing
- DFSA Consultation Papers Current
- DFSA Published Enforcement Decisions
- DFSA Enforcement Regulatory Actions
- DFSA Consultation Paper No.165 (individual)
- DFSA Supervisory Review Rulebook (Thomson Reuters)
- DFSA Rulebook Official

### ADGM/FSRA (10 sources)
- ADGM FSRA Rules and Regulations
- ADGM Public Consultations
- ADGM FSRA Guidance and Policy Statements
- ADGM FSRA Financial and Cyber Crime Prevention (AML)
- ADGM FSRA Enforcement
- ADGM Registration Authority Circulars
- ADGM FSRA Listing Authority Rules and Guidance
- ADGM FSRA Supervision Circulars
- ADGM Data Protection Guidance
- ADGM Data Protection Regulations 2021 Official PDF

### DIFC (9 sources)
- DIFC Legal Database (listing)
- DIFC Legal Notices
- DIFC Data Protection Law 2020 (specific law page)
- DIFC Companies Law 2018 (specific law page)
- DIFC Commissioner of Data Protection (4 pages: main, supervision/enforcement, guidance, Regulation 10)
- DIFC AML-CFT page
- DIFC Economic Substance Regulations page

### FTA (22 sources)
22 FTA PDF sources covering UAE Cabinet Decisions, FTA Decisions, Ministerial Decisions, and interpretive clarifications/guides on VAT, Corporate Tax, and Excise Tax. All 22 have MONITOR_OK. 3 FTA sources are Tier B (procedural user manuals).

### MoE DNFBP (35 sources)
35 official MoE documents: DNFBP circulars (2021-2026), supplemental guidance for real estate, DPMS, TCSPs, accountants, and direct PDF links for cabinet decisions on AML penalties, TFS thresholds, Federal Decree-Law 10/2025 on AML/CFT. 42/43 MoE sources have MONITOR_OK. This is the strongest family by monitoring confirmation count.

### UAE FIU (0 Tier A sources)
No UAE FIU sources are confirmed Tier A. The typology reports page and AML/CFT laws page are important content but have no MONITOR_OK — they are classified Tier B pending live monitoring confirmation. Annual reports and press releases have MONITOR_OK but are Tier B by content type. See Tier B section and UAE FIU Limitations section.

---

## Tier B Sources — Useful Official Context (19 sources)

These are official sources worth monitoring but do not directly trigger compliance actions on their own. Changes are informative rather than immediately actionable.

| Source | URL | Reason |
|---|---|---|
| CBUAE Regulations Sub-page | centralbank.ae/en/regulations/ | Listing index; prefer specific rulebook pages |
| ADGM FSRA Waivers and Modifications Register | adgm.com/fsra/waivers-and-modifications | Regulatory intelligence, not primary signal |
| DFSA Annual Reports | dfsa.ae/your-resources/publications-reports/annual-report | Annual cadence, contextual |
| DFSA Annual AML Reports | dfsa.ae/.../annual-anti-money-laundering-reports | Annual cadence, contextual |
| DIFC Laws and Regulations root | difc.com/business/laws-and-regulations/ | Discovery index |
| DIFC Legal Database (near-dup) | difc.com/business/laws-and-regulations/legal-database | Near-duplicate URL; de-duplicate |
| UAE FIU Publications Hub | uaefiu.gov.ae/en/more/knowledge-centre/publications/ | Discovery index |
| UAE FIU AML/CFT Laws and Notices sub-pages (3) | Various uaefiu.gov.ae sub-pages | Partial access; useful but constrained |
| UAE FIU Annual Reports | uaefiu.gov.ae/.../annual-report | Annual cadence (MONITOR_OK) |
| UAE FIU Press Releases | uaefiu.gov.ae/.../press-releases | General announcements (MONITOR_OK) |
| MoE AML sub-page | moet.gov.ae/aml | Discovery index |
| MoE Auditing Accounts | moet.gov.ae/auditing-accounts-legislations | Discovery index |
| MoE Economic Substance | moet.gov.ae/economic-substance-regulations | Discovery index |
| MoE goAML | moet.gov.ae/registering-companies-in-goaml | Discovery index |
| MoE Regulation of Business | moet.gov.ae/regulation-of-business | Discovery index |
| MoE Regulation of Competition | moet.gov.ae/regulation-of-competition | Discovery index |
| MoE Targeted Financial Sanctions | moet.gov.ae/targeted-financial-sanctions | Discovery index |
| FTA User Manuals / Registration PDFs (3) | tax.gov.ae PDFs | Procedural documents; low change frequency |

---

## Tier C Sources — Low Signal / Static (60 sources)

These sources should not be advertised in commercial coverage claims. They add monitoring volume without monitoring value.

### DFSA Individual News/Notice Pages (27 sources)
All `dfsa.ae/news/notice-*` URLs: individual DFSA published notice pages that are static documents after publication. The DFSA rules-and-standards listing and the Thomson Reuters rulebook platform already capture regulatory changes. These 27 individual pages are redundant, static, and inflate source count.

Examples:
- dfsa.ae/news/notice-amendment-dfsa-forms-3
- dfsa.ae/news/notice-amendments-rulebook-6
- dfsa.ae/news/notice-consultation-paper-2
(27 total)

### DIFC Individual News/Consultation Pages (13 sources)
All `difc.com/whats-on/*` URLs: published consultation announcements and news articles. Static after publication. The DIFC Legal Notices and Legal Database listing already capture live changes.

### ADGM Individual Consultation Announcement Pages (13 sources)
All `adgm.com/media/announcements/*` URLs: published ADGM consultation announcements. Static after publication. The ADGM Public Consultations listing already covers live consultation activity.

### Generic Homepages / Low-Signal Entry Points (4 sources)
- `centralbank.ae/` — CBUAE homepage; no substantive regulatory content
- `vara.ae/` — VARA homepage; JS SPA degrades to 62c; no substantive content
- `adgm.com/fsra` — ADGM FSRA landing page; generic entry point
- `moet.gov.ae/en/` — MoE homepage; generic government portal
- `mof.gov.ae/` — MoF homepage; no regulatory monitoring value

### Near-Duplicate URLs (1 source)
- `difc.com/business/laws-and-regulations/legal-database` (without trailing slash) — near-duplicate of the `legal-database/` version

---

## Remediation Sources — Important but Currently Unreliable (9 sources)

These sources represent commercially important regulatory bodies where monitoring is not yet confirmed working. They must NOT be counted in commercial coverage claims until MONITOR_OK is verified.

### SCA — Securities and Commodities Authority (5 sources)
**Status: REMEDIATION**

All 5 SCA sources have proof paths and normalized hashes but zero MONITOR_OK runs. The SCA regulates UAE capital markets, securities, and investment funds — a major audience for any UAE regulatory monitoring product. The known history includes 403 errors and robot restrictions.

| Source | URL |
|---|---|
| SCA Circulars, Rules and Procedures | sca.gov.ae/en/regulations/circulars-rules-and-procedures |
| SCA Regulations Listing | sca.gov.ae/en/regulations/regulations-listing |
| SCA FATCA and CRS Guidance | sca.gov.ae/en/regulations/automatic-exchange-of-information-fatca-and-crs |
| SCA Corporate Governance | sca.gov.ae/en/regulations/corporate-governance |
| SCA AML/CFT | sca.gov.ae/en/regulations/anti-money-laundering-and-terrorist-financing |

**Impact:** Cannot sell SCA monitoring to securities firms or fund managers until MONITOR_OK is confirmed.

### EOCN — Executive Office for Control of Non-Banking Financial Activities (2 sources)
**Status: REMEDIATION**

EOCN maintains UAE targeted financial sanctions lists and AML/CFT legislation — critical for every MLRO in the country. Two sources enabled, both with proof paths, neither with MONITOR_OK. Direct access constraints have been noted. TFS is partially covered via MoE DNFBP document PDFs, but EOCN's own portal is the authoritative source.

| Source | URL |
|---|---|
| EOCN AML/CFT Laws and Regulations | eocn.gov.ae/en-us/laws-regulations-listing |
| EOCN News and Sanctions Updates | eocn.gov.ae/en-us/news |

### UAE FIU Homepage (1 source)
**Status: REMEDIATION**

`uaefiu.gov.ae/` — confirmed under remediation; generic homepage with no content monitoring value. Replaced by specific FIU sub-page monitors.

### UAE Legislation Portal (1 source)
**Status: REMEDIATION**

`uaelegislation.gov.ae/` — high-value source for UAE federal legislation but WAF/access validation is ongoing. No MONITOR_OK. Cannot claim federal gazette/legislation monitoring until confirmed.

---

## SCA Limitations

The Securities and Commodities Authority (SCA) is UAE's primary capital markets regulator, covering listed companies, investment funds, and securities brokers. StatuteProof has 5 SCA sources enabled with proof paths and baseline hashes, but none have achieved a MONITOR_OK status.

**Root cause:** SCA operates a WAF that has returned 403 and robot-restriction errors during earlier testing. The `sca_listing` adapter was activated on 2026-06-15 after a proof-backed baseline, but live monitoring confirmation is pending.

**Commercial impact:** Any pilot client operating as an investment manager, securities broker, listed company, or SCA-regulated fund cannot be told their SCA regulatory exposure is monitored by StatuteProof. This is a gap.

**What can be said:** "SCA regulatory pages are in our monitoring pipeline. We have confirmed baseline snapshots for 5 SCA regulatory pages. Live monitoring confirmation is in progress."

**What cannot be said:** "We monitor the SCA" or "SCA regulatory changes are covered."

---

## UAE FIU Limitations

The UAE Financial Intelligence Unit is the national AML/CFT authority responsible for goAML, suspicious transaction reporting, typology guidance, and high-risk jurisdiction lists. All MLROs and DNFBPs are directly subject to FIU guidance.

**What works:** 2 of 7 FIU sources have MONITOR_OK — annual reports and press releases. 3 more have proof paths without MONITOR_OK. The homepage is in remediation.

**What does not work:** The FIU Circulars and Notices page (`uaefiu.gov.ae/en/Publications/`) and the AML/CFT Laws page have no MONITOR_OK. These are the highest-value FIU pages for MLROs.

**Partial coverage note:** The MoE DNFBP document set partially covers FIU-adjacent content (high-risk jurisdiction circulars, AML/CFT laws via MoE portal), but the FIU is the authoritative source.

**Commercial impact:** An MLRO cannot be told FIU circulars are monitored until MONITOR_OK is confirmed on the circulars page.

---

## EOCN / TFS Limitations

The Executive Office for Control of Non-Banking Financial Activities (EOCN) administers UAE targeted financial sanctions (TFS) and UN sanctions implementation. Any VASP, DNFBP, or financial institution must screen against EOCN lists.

**What exists:** 2 EOCN sources enabled with proof paths but no MONITOR_OK. 16 MoE DNFBP document PDFs in the `eocn_tfs` category have MONITOR_OK and cover cabinet decisions, circulars, and supplemental guidance related to TFS implementation.

**What is missing:** Live monitoring of EOCN's own sanctions and news portal. The EOCN portal is the authoritative real-time source for TFS updates; MoE documents are after-the-fact official publications.

**Commercial impact:** TFS/sanctions monitoring is partially covered (via MoE documents) but EOCN direct portal access is unconfirmed. This should be disclosed to any MLRO or VASPs relying on StatuteProof for sanctions compliance monitoring.

---

## Safe Product Claims

The following phrases are factually grounded and legally safe to use in pilot sales and marketing:

1. "StatuteProof monitors 138 UAE official regulatory sources at the regulation, rulebook, and circular level — including CBUAE rulebook modules, VARA rulebook PDFs, DFSA enforcement notices, ADGM guidance, MoE DNFBP circulars, and FTA tax legislation."

2. "We have confirmed live monitoring (MONITOR_OK status with proof-backed evidence records) on 149 UAE official regulatory sources as of June 2026."

3. "StatuteProof maintains cryptographic evidence records — including SHA-256 hashes and timestamped proof files — for 216 of 226 enabled UAE regulatory source snapshots."

4. "Our VARA monitoring covers the full suite of VARA rulebook PDFs — Compliance/Risk, Technology, VA Issuance, Broker-Dealer, Lending, Exchange, Advisory, Custody, Market Conduct, and Transfer/Settlement — plus the VARA revision updates index and enforcement notices."

5. "Our MoE DNFBP monitoring covers 43 sources including DNFBP guidelines, AML circulars from 2021 to 2026, high-risk jurisdiction updates, TFS-related cabinet decisions, and sector-specific supplemental guidance for real estate agents, DPMS, TCSPs, and accountants."

---

## Forbidden Claims

Do not use any of the following:

1. "226 monitored UAE regulatory sources" — This implies all 226 are producing live monitoring intelligence. 60 are static pages that will never meaningfully change, and 9 are in remediation.

2. "Full SCA coverage" or "We monitor the SCA" — SCA has no MONITOR_OK on any source. This would be a false claim.

3. "Complete UAE sanctions/TFS monitoring" or "EOCN monitoring is live" — EOCN has no MONITOR_OK on its direct portal. Partial coverage via MoE documents is not complete TFS monitoring.

4. "We never miss a regulatory update" — No source monitoring product can make this claim. Source access is subject to WAF changes, PDF format changes, publication delays, and JS SPA issues.

5. "UAE FIU circulars are monitored" — The UAE FIU circulars page has no MONITOR_OK. Only press releases and annual reports are confirmed working.

---

## Recommended Honest Source Count for Sales

**For pilot conversations:** "We have 149 confirmed-live UAE regulatory monitoring sources — with cryptographic evidence records and at least one MONITOR_OK run — across CBUAE, VARA, DFSA, ADGM, DIFC, MoE DNFBP, and FTA. An additional 77 sources are in baseline or validation phase."

**For detailed proposals:** "Our UAE monitoring universe covers 138 Tier A regulatory sources (primary regulations, rulebooks, circulars, enforcement actions) and 19 Tier B sources (official context and indexes). SCA, EOCN direct portal, and UAE Legislation Portal are in active remediation and not yet included in our confirmed coverage count."

**For VASP clients:** "We have 25 selected-source VARA fresh-alert monitors, including rulebook PDFs, revision updates, publications, and the official enforcement table. This is selected-source monitoring, not complete VARA coverage."

**For MLRO clients:** "We monitor MoE DNFBP circulars (42 MONITOR_OK), DFSA AML notices (MONITOR_OK), ADGM financial crime prevention (MONITOR_OK), and UAE FIU annual reports and press releases. FIU circulars page is in validation."

**For tax clients:** "22 FTA sources are confirmed-live with MONITOR_OK, covering UAE Cabinet Decisions, FTA Decisions, Ministerial Decisions, VAT and Corporate Tax guides, and interpretive clarifications."

---

## By-Family Summary

| Family | Tier A | Tier B | Tier C | Remediation | Total | Notes |
|---|---|---|---|---|---|---|
| CBUAE | 25 | 1 | 1 | 0 | 27 | 0 MONITOR_OK on rulebook pages — all baselines |
| VARA | 24 | 0 | 1 | 0 | 25 | 16 MONITOR_OK; strongest VASP coverage |
| DFSA | 11 | 2 | 27 | 0 | 40 | 32 MONITOR_OK but 27 are static news pages |
| DIFC | 9 | 1 | 15 | 0 | 25 | 17 MONITOR_OK; 13 are static news pages + 1 near-dup |
| ADGM/FSRA | 10 | 1 | 14 | 0 | 25 | 15 MONITOR_OK; 13 static announcement pages |
| MoE DNFBP | 35 | 7 | 1 | 0 | 43 | 42 MONITOR_OK; strongest by confirmation count |
| FTA | 22 | 3 | 0 | 0 | 25 | 25 MONITOR_OK; all confirmed live |
| SCA | 0 | 0 | 0 | 5 | 5 | Zero MONITOR_OK — full remediation |
| UAE FIU | 0 | 6 | 0 | 1 | 7 | 2 MONITOR_OK; circulars, typology, AML-laws pages downgraded to B pending confirmation |
| EOCN | 0 | 0 | 0 | 2 | 2 | Zero MONITOR_OK — full remediation |
| MoF | 0 | 0 | 1 | 0 | 1 | Homepage only; no regulatory value |
| UAE Legislation | 0 | 0 | 0 | 1 | 1 | WAF-blocked; remediation |
| **TOTAL** | **136** | **21** | **60** | **9** | **226** | |

---

*StatuteProof reports are generated from monitored official-source records and are provided for information and compliance review support only. This audit does not constitute legal advice, regulatory advice, compliance certification, or a legal opinion.*
