# UAE Complete Coverage Gap Verdict

Date: 2026-06-17
Analyst role: Brutally honest CTO + QA/Critic
No softening. Verdicts are YES, PARTIAL, or NO.

---

## Question 1: Can StatuteProof claim complete UAE coverage today?

**Verdict: NO**

Reasons — every one of these would need to be false for "complete" to be defensible:
1. FTA (Federal Tax Authority) has 0 active sources. VAT and corporate tax are universal UAE compliance obligations.
2. VARA regulatory guidance and regulatory framework hub are not active (broken URLs from site redesign).
3. VARA AML/CFT rulebook live monitoring page is not active (broken URL).
4. Ministry of Justice e-laws has 0 active sources.
5. UAE federal Personal Data Protection Law (PDPL) guidance has 0 active sources (DIFC DP is a separate law).
6. Customs/trade compliance has 0 sources and is not mapped.
7. CBUAE consultations are not active — horizon scanning is unavailable for the most important UAE banking regulator.
8. SCA primary securities laws and board decisions are not active.
9. Annual reports: 0 active sources across all regulators.
10. Recall rate (updates published vs. updates detected): never measured. Cannot claim completeness without this metric.
11. Source-health trend data: <3 months of monitoring history.

"Complete UAE coverage" is not achievable in under 3 months from today regardless of activation sprint results. It requires sustained monitoring data, recall rate measurement, and coverage across trade/customs, all federal legislation, all tax guidance, and all regulatory guidance types.

---

## Question 2: Can StatuteProof claim comprehensive UAE official-source universe mapped?

**Verdict: PARTIAL**

What supports YES:
- 203 candidate records across 10 regulatory categories, 18+ source owners.
- All major UAE financial regulators are represented.
- Taxonomy covers laws, rulebooks, guidance, enforcement, consultation, AML/CFT.
- 32 entries documented as rejected with explicit reasons.

What prevents full YES:
- Customs/trade compliance: 0 candidates, not in universe (Dubai Customs, Federal Customs Authority).
- MENAFATF is in universe as "adjacent" only.
- Ministry of Foreign Affairs / sanctions export control: 0 candidates.
- Some emirate-level sources (Ajman, Sharjah, Ras Al Khaimah free zones) not investigated.
- Court systems beyond DIFC Courts: absent.
- Labour regulation (MOHRE): absent.
- Health/pharma/medical compliance: absent (relevant for some regulated entities).

Safe claim: "StatuteProof has mapped 200+ official UAE regulatory source candidates across the major financial, AML/CFT, virtual asset, securities, free-zone, and federal compliance domains." This is accurate and defensible. Do not extend to "complete universe."

---

## Question 3: Can StatuteProof claim major UAE financial/compliance regulator coverage?

**Verdict: YES (with mandatory disclaimer)**

All major UAE financial and compliance regulators have at least 5 active sources:
- CBUAE: 27 active ✅
- DFSA: 10 active ✅
- ADGM/FSRA: 10 active ✅
- DIFC: 8 active ✅
- VARA: 9 active (but framework hub broken) ✅⚠️
- UAE FIU: 5 active ✅
- EOCN: 2 active ✅
- SCA: 5 active ✅

But this claim requires the disclaimer: "Selected sources from major UAE regulators. Does not represent comprehensive coverage of all regulatory publications. Users must verify directly with official sources."

And it must NOT be used in isolation without the disclaimer. "Major regulator coverage" + no disclaimer = overclaim.

---

## Question 4: What is missing before "comprehensive" is fair?

**Required minimum for "comprehensive" to be used in marketing:**

1. **VARA guidance** — vara.ae/en/regulatory-guidance/ must be active. VARA is the primary buyer segment.
2. **SCA securities laws** — sca.gov.ae/en/legislation/laws.aspx must be active. Securities legislation is foundational.
3. **FTA at least 1 source** — tax.gov.ae corporate tax or VAT clarifications must be active. Tax is universal.
4. **CBUAE consultations** — centralbank.ae/en/consultations/ must be active. Horizon scanning for largest regulator.
5. **Ministry of Economy AML DNFBP** — moet.gov.ae/en/anti-money-laundering must be active. DNFBP buyer gap.
6. **UAE FIU NRA 2024** — Most cited single MLRO document must be active.

**Estimated timeline to close these 6 gaps:** 2–3 weeks with focused Codex activation sprint. These are the minimum gates.

After those 6: add disclaimer and use "comprehensive" carefully: "StatuteProof monitors selected official sources across all major UAE regulatory families, including comprehensive AML/CFT, banking, virtual asset, securities, and financial free-zone coverage. Tax guidance and customs are partially covered."

---

## Question 5: What is missing before "complete" is even discussable?

**Required for "complete" to ever be discussable:**

Beyond the 6 items above, also needed:
1. Customs/trade compliance mapped and at least 1 source active.
2. UAE PDPL (federal data protection) at least 1 source active.
3. Ministry of Justice e-laws active.
4. At least 3 months of monitoring data with documented source-health history.
5. Recall rate measured: what % of regulatory publications were detected within 48 hours.
6. A qualified legal review confirming the coverage claim wording.
7. No major source-type blind spots (guidance, annual reports, public registers all need at least some coverage).
8. Source failure rate documented and within acceptable bounds.

**Estimated timeline:** 6+ months from today under current development pace. "Complete UAE coverage" is a 2027 story, not a 2026 story.

---

## Question 6: Which source owners are blind spots?

| Source Owner | Why It's a Blind Spot |
|-------------|----------------------|
| FTA | 0 active. VAT/corporate tax = universal obligation. First buyer asked will find this gap. |
| VARA guidance | Live guidance URL broken. Primary buyer segment (VASP MLRO) notices this first. |
| Ministry of Justice | 0 active. Federal law research is foundational for legal counsel buyers. |
| UAE Data Office (PDPL) | 0 active. Federal data protection law is growing in enforcement. |
| Dubai/Federal Customs | Not in universe. Trade-facing buyers have zero coverage. |
| Labour (MOHRE) | Not in universe. Employment compliance is a standard CCO need. |
| CBUAE consultations | 0 active. Horizon scanning gap for the most-represented regulator. |

---

## Question 7: Which source types are weak?

Weakest by type (from source type coverage matrix):

1. **Regulatory guidance** — 4 active sources. Most commercially cited type. Most important gap.
2. **Tax guidance** — 0 active. Universal compliance obligation.
3. **Annual reports / NRA** — 0 active. NRA 2024 is the single most important unmonitored document.
4. **Public registers** — 1 active. Counterparty due diligence is an unanswered use case.
5. **Consultations** — 3 active (missing CBUAE, DIFC).
6. **Sanctions / TFS live monitoring** — 1 active (legislative framework only; live list not active).

---

## Question 8: Which buyer types are well-covered?

| Buyer | Coverage Assessment |
|-------|-------------------|
| Bank MLRO / CCO | **Well-covered** — CBUAE AML/CFT, proliferation finance, TBML, consumer protection, payments. Strong demo case. |
| DFSA Firm CCO | **Well-covered** — AML rulebook, MLRO letters, enforcement decisions, regulatory actions, consultation papers. |
| ADGM Firm CCO | **Well-covered** — Financial crime, rulebooks, consultations, guidance, waivers, enforcement. |
| DIFC Data Protection | **Well-covered** — 8 active DIFC DP sources including supervision, enforcement, guidance, Regulation 10. |
| AML/CFT Officer (any regulated entity) | **Well-covered** — FIU, EOCN, CBUAE, DFSA, ADGM, SCA AML sources all active. |

---

## Question 9: Which buyer types are not well-covered?

| Buyer | Coverage Gap |
|-------|-------------|
| VASP MLRO | **Partial** — VARA guidance and AML/CFT live page not active. Cannot credibly demo VARA regulatory guidance monitoring. |
| Securities CCO (SCA-licensed) | **Weak** — Primary securities legislation not active. Only circulars, AML, FATCA/CRS monitored. |
| Tax compliance / CFO | **Not covered** — 0 FTA sources. Cannot offer any tax compliance monitoring. |
| DNFBP MLRO (law firm, real estate, accounting) | **Partial** — ADGM RA AML guides not active. Ministry of Economy DNFBP supervision not active. |
| Legal counsel | **Partial** — MoJ e-laws not active. Consultation papers incomplete. |
| Free zone entity (DMCC, DFM, ADX) | **Not covered** — 0 active free zone sources. |

---

## Question 10: What evidence would change the verdict?

To upgrade from "PARTIAL" to "YES" on comprehensive claim:

1. Activate AE-vara-guidance (VARA guidance hub) — changes VASP verdict from partial to adequate.
2. Activate AE-sca-laws (SCA securities laws) — changes securities CCO verdict from weak to partial.
3. Activate AE-fta-corporate-tax-guides — changes tax coverage from not-covered to covered.
4. Activate AE-uaefiu-nra-2024 — changes FIU publications from adequate to strong.
5. Activate AE-cbuae-consultations — changes bank horizon scanning from missing to present.
6. Document 30 days of stable monitoring history with source-health logs.

None of these require new infrastructure. All 6 are activation-sprint work.

---

## Question 11: What must Codex activate next?

**Codex next activation batch (5 sources, lowest technical risk, highest commercial value):**

| Priority | Source ID | Estimated Adapter | Risk |
|----------|-----------|------------------|------|
| 1 | AE-uaefiu-nra-2024 | pdf_listing (static page with PDF link) | Low |
| 2 | AE-vara-activity-rulebooks-hub | listing (rulebooks.vara.ae subdomain, known pattern) | Low |
| 3 | AE-adgm-ra-aml-guides | pdf_listing (ADGM RA pattern known) | Low |
| 4 | AE-sca-laws | listing (sca_listing pattern known) | Low |
| 5 | AE-fta-corporate-tax-guides | listing (FTA site expected accessible) | Low |

After this batch: try AE-vara-guidance (Playwright needed — medium risk) and AE-cbuae-consultations (Playwright needed — medium risk).

---

## Question 12: What must remain legal-safe copy?

**Wording that must appear on every customer-facing output:**

Short form:
> "Monitoring intelligence only. Not legal advice. Not a guarantee of regulatory completeness."

Full form (for briefs and reports):
> "StatuteProof reports are generated from monitored official-source records and are provided for information and compliance review support only. StatuteProof does not constitute legal advice, regulatory advice, compliance certification, or a legal opinion. StatuteProof does not replace qualified legal counsel or compliance professionals. Coverage is based on selected official sources and does not guarantee capture of all regulatory updates."

**Forbidden phrases (none of these may appear in any customer-facing material):**
- Complete UAE coverage
- All UAE regulations
- Never miss an update
- Guaranteed compliance
- Prevent fines
- Full regulatory monitoring
- Comprehensive UAE regulatory monitoring (without Tier 3 criteria met)
- Certified by any regulator
- Full AML/CFT monitoring across all major regulatory families (currently inaccurate)
