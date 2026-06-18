# UAE Complete Coverage Proof Dossier — Final Report

Date: 2026-06-17
Analyst roles: CTO + QA/Critic + Legal Language + Product Manager + Source Monitor
Input files: sources.json (81 enabled after 2026-06-18 FTA/ADGM repair), uae_source_universe_candidates.json (203 records), 7 dossier analysis docs
Mission: Turn the UAE source universe roadmap into an evidence-grade coverage proof. No source activation. No sources.json edits. No false claims.

2026-06-18 update: the dirty 87 enabled / 86 active claim was rejected. Two ADGM sources passed no-save, proof, 2/2 baseline, mass-monitor `MONITOR_OK`, and agent gates. Five FTA sub-pages and the ADGM dedicated regulatory-alerts page were demoted to candidates because they did not pass meaningful extraction gates. Current source truth is therefore 81 enabled / 80 monitoring-active / 1 remediation.

---

## 1. Current Source Truth (Canonical — Do Not Contradict)

| Metric | Value | Source |
|--------|-------|--------|
| Enabled sources | **81** | sources.json enabled=true |
| Monitoring-active sources | **80** | sources.json status=active or readiness_supported |
| Remediation sources | **1** | sources.json status=remediation |
| Universe candidates mapped | **171** | uae_source_universe_candidates.json candidates array |
| Rejected and documented | **32** | uae_source_universe_candidates.json rejected array |
| Grand total universe records | **203** | uae_source_universe_candidates.json |

These numbers are the authoritative source of truth as of 2026-06-18. Any public claim about source counts must use exactly these numbers or a subset. Round numbers are not acceptable as standalone figures ("80+" or "100+" is not acceptable — "81" and "80" are the only safe exact counts).

---

## 2. Coverage Claim Level Achieved Today

| Tier | Claim | Safe Today? |
|------|-------|------------|
| Tier 0 | "81 enabled / 80 monitoring-active UAE official-source endpoints" | **YES — use now** |
| Tier 1 | "200+ official-source candidates mapped" | **YES — use now** |
| Tier 2 | "Major UAE regulator coverage" (with disclaimer) | **YES — conditional, requires disclaimer** |
| Tier 3 | "Comprehensive UAE official-source monitoring" | **NO — 6 specific P0 activations required first** |
| Tier 4 | "Complete UAE coverage" | **NO — never claimable in current state; 6+ months minimum** |

**Current safe positioning statement:**
> "StatuteProof monitors selected public official UAE regulatory sources — 81 enabled endpoints, including 80 monitoring-active sources across major UAE financial regulators — and provides evidence-backed monitoring intelligence, source-health visibility, and compliance review support. Monitoring intelligence only. Not legal advice. Not a guarantee of regulatory completeness."

---

## 3. Regulator Coverage Verdicts

| Regulator | Active Sources | Coverage Verdict | Gap |
|-----------|---------------|-----------------|-----|
| CBUAE | 27 | **Strong** ✅ | Consultations, AML/CFT ops page not active |
| DFSA | 12 | **Adequate** ✅ | Guidance notes, policy statements not active |
| ADGM/FSRA | 12 | **Adequate** ✅ | RA AML guides, dedicated regulatory alerts not active |
| DIFC | 8 | **Adequate** ✅ | Financial Crime Authority, courts not active |
| VARA | 9 | **Partial** ⚠️ | Guidance hub + AML/CFT live page broken URLs |
| UAE FIU | 5 | **Partial** ⚠️ | NRA 2024 not active (most cited MLRO doc) |
| EOCN | 2 | **Partial** ⚠️ | TFS live designation page not active (noise risk) |
| SCA | 5 | **Partial** ⚠️ | Primary securities laws not active |
| FTA | 0 | **Not covered** ❌ | Zero active sources (VAT, corporate tax gap) |
| Ministry of Justice | 0 | **Not covered** ❌ | Zero active sources |
| Ministry of Economy | 1 | **Weak** | DNFBP AML supervision not active |
| UAE Data Office / PDPL | 0 | **Not covered** ❌ | Federal PDPL has zero coverage |
| Customs / FCA | 0 | **Not mapped** ❌ | Not in universe at all |

**Verdict on "major UAE financial regulator coverage":** YES — with mandatory disclaimer. All 8 major financial regulators (CBUAE, DFSA, ADGM, DIFC, VARA, UAE FIU, EOCN, SCA) have at least 5 active sources. Disclaimer required: "Selected sources from major UAE regulators. Not comprehensive. Users must verify directly."

---

## 4. Source Type Coverage Verdicts

| Source Type | Active | Strength | Key Gap |
|-------------|--------|----------|---------|
| Rulebooks / Modules | ~37 | **Strong** | VARA AML/CFT live page (broken URL) |
| AML/CFT Guidance | ~10 | **Strong** | VARA AML gap; ADGM RA AML guides not active |
| Regulations / Secondary | ~15 | **Adequate** | VARA regulatory framework hub broken |
| Laws / Primary Legislation | ~13 | **Partial** | SCA primary laws; MoJ not active |
| Circulars / Notices | ~7 | **Adequate** | CBUAE direct circulars not active |
| Enforcement / Admin Orders | 5 | **Adequate** | SCA violations; VARA admin orders not active |
| Data Protection | 8 (DIFC only) | **Partial** | UAE federal PDPL = 0 active |
| Consultations | 3 | **Partial** ⚠️ | CBUAE consultations (largest gap) |
| Regulatory Guidance | ~4 | **Weak** ⚠️ | VARA guidance; DFSA guidance notes not active |
| Market Rules | 1 | **Weak** | SCA market rules; DFM not active |
| Licensing Conditions | ~3 | **Partial** | VARA licensing conditions not active |
| Public Registers | 1 | **Weak** | DFSA, VARA, SCA registers not active |
| Sanctions / TFS | 1 | **Weak** ⚠️ | Live TFS designation page blocked (noise risk) |
| Annual Reports / NRA | 2 | **Partial** ⚠️ | DFSA annual/AML reports active; FIU NRA 2024 is still not active |
| Tax Guidance | 0 | **Not covered** ❌ | Entire FTA category uncovered |
| Courts / Legal Database | 1 | **Partial** | DIFC only; MoJ not active |

**Most commercially critical type gaps:** Regulatory guidance (Type 4), Tax guidance (Type 14), Annual Reports/NRA (Type 12), CBUAE consultations (Type 6), Sanctions live monitoring (Type 8).

---

## 5. Buyer Coverage Assessment

### Well-covered buyer types (strong demo case today)

| Buyer | Why Well-Covered |
|-------|----------------|
| Bank MLRO / CCO | CBUAE AML/CFT, proliferation finance, TBML, consumer protection, payments (27 active CBUAE sources) |
| DFSA-regulated firm CCO | AML rulebook, MLRO letters, enforcement decisions, regulatory actions |
| ADGM/FSRA-regulated firm CCO | Financial crime, rulebooks, consultations, guidance, waivers, enforcement |
| DIFC Data Protection Officer | 8 active DIFC DP sources — deepest single-type pack |
| AML/CFT Officer (any regulated entity) | FIU, EOCN, CBUAE, DFSA, ADGM, SCA AML sources all active |

### Not well-covered buyer types (do not demo without gap disclosure)

| Buyer | Gap | P0 Fix |
|-------|-----|--------|
| VASP MLRO | VARA guidance and AML/CFT live page broken — cannot demo VARA regulatory guidance monitoring | AE-vara-guidance, AE-vara-activity-rulebooks-hub |
| Securities CCO (SCA-licensed) | Primary securities legislation not active | AE-sca-laws, AE-sca-decisions |
| Tax compliance / CFO | Zero FTA sources — cannot offer any tax monitoring | AE-fta-corporate-tax-guides, AE-fta-vat-public-clarifications |
| DNFBP MLRO | ADGM RA AML guides and MoE AML DNFBP not active | AE-adgm-ra-aml-guides, AE-moec-aml-dnfbp |
| Legal counsel | MoJ e-laws not active; consultation papers incomplete | AE-uaefiu-nra-2024 (NRA is primary MLRO research doc) |
| Free zone entity compliance | Zero active free zone sources (DMCC, DFM, ADX) | P1 items; not blocking for core use case |

---

## 6. Roadmap Quality Audit Summary

**Roadmap quality score before audit:** 7.5/10
**Issues identified and resolved in this dossier sprint:**

| Issue | Severity | Resolution |
|-------|----------|-----------|
| "Full AML/CFT monitoring across all major regulatory families" in commercial section | HIGH | Removed. Replaced with safe wording scoped to specific regulators. |
| P0 list oversized at 25 sources — 10 not truly P0 | HIGH | Reduced to 15 items. 10 moved to P1/P2. 2 FTA sources added as new P0. |
| P1 timeline "4–6 weeks" too aggressive (Playwright required) | MEDIUM | Revised to "8–12 weeks" with Playwright caveat. |
| EOCN TFS noise-risk not flagged | HIGH | Warning added: TFS page must NOT be activated with raw hash monitoring. Sanctions-specific parser required first. |
| "This is the commercial threshold for $399" — unvalidated product commitment | MEDIUM | Replaced with conditional language: "provides credible foundation for $399 positioning; pricing is a commercial decision separate from source count." |
| P2 section vague — "75 sources, activate when capacity allows" | MEDIUM | Top-10 P2 mini-batch list added with explicit source IDs and adapter estimates. |
| AE-uaefiu-press-releases in P0 — high churn, low compliance signal | LOW | Moved to P2. |

---

## 7. Unsafe Claims Removed or Corrected

The following claims were found in prior versions of roadmap documents and have been corrected or explicitly flagged as unsafe in the dossier:

| Unsafe Claim | Where Found | Status |
|-------------|------------|--------|
| "Full AML/CFT monitoring across all major regulatory families" | Roadmap Section 5 | **REMOVED** — replaced with scoped safe wording |
| Implied "$399 automatic once 100 sources reached" | Roadmap Section 5 | **REVISED** — caveat added |
| P0 count "25 sources" implying all truly P0-worthy | Roadmap P0 header | **REVISED** — reduced to 15 with audit justification |
| P1 duration "4–6 weeks" without Playwright caveat | Roadmap timeline | **REVISED** — 8–12 weeks + Playwright caveat |
| EOCN TFS in P1 without noise-risk flag | Roadmap P1 list | **REVISED** — moved; explicit noise-risk warning added |

---

## 8. Safe Wording Library (Use These Exactly)

### Always-safe phrases (no modification needed):
1. "81 enabled UAE official-source endpoints. 80 monitoring-active."
2. "Monitoring intelligence only. Not legal advice."
3. "Not a guarantee of regulatory completeness."
4. "StatuteProof has mapped 200+ official UAE regulatory source candidates across major financial, AML/CFT, virtual asset, securities, and financial free-zone regulatory domains."
5. "Source monitoring may be affected by access restrictions, website changes, and publication delays."
6. "Users should verify official source material directly."
7. "StatuteProof does not replace qualified legal counsel, MLROs, or compliance professionals."
8. "Source readiness, extraction quality, and known gaps are shown transparently."
9. "Selected official UAE regulatory sources — not all publications from each body."

### Conditional phrases (safe only with the accompanying disclaimer):
- "Major UAE regulator coverage" → requires: "Selected sources only. Not comprehensive. Users must verify directly."
- "AML/CFT monitoring across CBUAE, DFSA, ADGM/FSRA, UAE FIU, EOCN, and SCA" → requires: "VARA AML/CFT live guidance monitoring pending URL resolution."
- "Broad UAE compliance monitoring" → requires full scope qualifier and "monitoring intelligence only" suffix.

### Never-use phrases (forbidden, remove immediately if found):
| Phrase | Reason |
|--------|--------|
| Complete UAE coverage | Absolute, not achievable |
| Never miss an update | Absolute, not achievable |
| All UAE regulations | "All" not supportable |
| Full AML/CFT monitoring across all major regulatory families | VARA AML gap; overclaim |
| Guaranteed compliance | Absolute, forbidden |
| Certified by [any regulator] | False certification |
| Prevent fines / avoid penalties | Causal claim, forbidden |
| Replace lawyers | False, forbidden |
| 100% accurate | Absolute, forbidden |
| Perfect parsing | Absolute, forbidden |
| Comprehensive UAE regulatory monitoring | Tier 3 criteria not yet met |

---

## 9. Next Codex Activation Batch (5 Sources — Lowest Risk, Highest Value)

Run in this exact order. Each requires: no-save preview → quality score ≥60 → evidence save → repeat baseline → mass-monitor dry-run → 6-agent review gate. No source bypasses the gate.

| Rank | Source ID | Adapter | Why First |
|------|-----------|---------|-----------|
| 1 | AE-uaefiu-nra-2024 | pdf_listing | Most cited single MLRO document; static page; very low friction |
| 2 | AE-vara-activity-rulebooks-hub | listing | rulebooks.vara.ae — known domain from active VARA PDF sources |
| 3 | AE-adgm-ra-aml-guides | pdf_listing | Known ADGM PDF listing pattern; closes DNFBP MLRO gap |
| 4 | AE-sca-laws | listing | SCA listing adapter known; closes primary securities legislation gap |
| 5 | AE-fta-corporate-tax-guides | listing | FTA site accessible; closes zero-FTA coverage gap |

**After this batch:** AE-vara-guidance (Playwright needed — medium risk), AE-cbuae-consultations (Playwright needed — medium risk). Run both only after the 5-source batch is stable.

---

## 10. What Activating These 5 Sources Enables

| Claim (post-batch, if all 5 pass gates) | Safe? |
|-----------------------------------------|-------|
| "84 enabled UAE official-source endpoints" | **YES** |
| "UAE FIU National Risk Assessment 2024 monitored" | **YES** |
| "VARA regulatory rulebooks monitored at rulebooks.vara.ae" | **YES** |
| "ADGM RA AML/CFT guides for DNFBPs monitored" | **YES** |
| "SCA primary securities laws monitored" | **YES** |
| "FTA corporate tax guidance monitored" | **NO TODAY** — only safe after a future FTA endpoint passes proof, repeat baseline, and MONITOR_OK gates |
| "Monitoring across all major UAE financial regulators including FTA" | **CONDITIONAL** — still requires disclaimer |
| "Comprehensive UAE coverage" | **NO — still not achievable** |
| "Complete UAE coverage" | **NO — never achievable with current state** |

---

## 11. What Remains Before "Comprehensive" Is Safe

Six specific activations are required before "comprehensive" can be used (even with disclaimer):

1. AE-vara-guidance — VARA regulatory guidance hub (Playwright required)
2. AE-sca-laws — SCA primary securities laws
3. AE-fta-corporate-tax-guides — any FTA source
4. AE-cbuae-consultations — CBUAE consultation papers (horizon scanning)
5. AE-moec-aml-dnfbp — Ministry of Economy AML for DNFBPs
6. AE-uaefiu-nra-2024 — UAE FIU National Risk Assessment 2024

**Estimated timeline:** 2–3 weeks with focused activation sprint (all 6 are in P0 batch). All 6 must pass the full gate sequence.

After those 6, the safe Tier 3 wording is:
> "StatuteProof monitors selected official sources across all major UAE regulatory families, including AML/CFT, banking, virtual asset, securities, tax, and financial free-zone compliance. Monitoring intelligence only. Selected sources — not all publications from each body. Not legal advice."

---

## 12. What Will Never Enable "Complete" Coverage

"Complete UAE coverage" as a standalone claim is not achievable in 2026. Requirements beyond the 6 above:
1. Customs/trade compliance mapped and at least 1 source active (not in universe)
2. UAE PDPL federal data protection at least 1 source active
3. Ministry of Justice e-laws active
4. At least 3 months of monitoring data with documented source-health history
5. Recall rate measured (% of regulatory publications detected within 48 hours)
6. Qualified legal review of coverage claim wording
7. No major source-type blind spots (annual reports, public registers, guidance all need coverage)

**Timeline:** 6+ months minimum. "Complete UAE coverage" is a 2027 story at earliest.

---

## 13. Source-Health Risk Register

| Source | Risk Type | Severity | Notes |
|--------|-----------|----------|-------|
| AE-eocn-tfs | Noise risk | **HIGH** | TFS live list updates daily/weekly; raw hash monitoring = excessive alerts; sanctions-specific parser required before any activation |
| AE-vara-guidance | Technical risk | **MEDIUM** | vara.ae is JS-heavy; Playwright required; quality gate may fail at first attempt |
| AE-vara-administrative-orders | Technical risk | **MEDIUM** | Same VARA site; Playwright likely needed |
| AE-cbuae-aml-cft | Technical risk | **MEDIUM** | Umbraco CMS blocks standard bs4 adapter; custom selector or Playwright required |
| AE-cbuae-consultations | Technical risk | **MEDIUM** | Playwright needed; do not attempt with generic listing adapter |
| AE-vara-regulatory-framework | Broken URL | **HIGH** | 404; URL path changed in VARA site redesign; find new URL before attempting |
| AE-vara-company-rulebook | Broken URL | **HIGH** | 404; may be at rulebooks.vara.ae subpage |
| AE-vara-aml-cft-rulebook | Broken URL | **HIGH** | 404; may be PDF at rulebooks.vara.ae |

---

## 14. Regulatory Coverage Blind Spots (Not in Universe)

These source owners have zero candidates in the universe — not just zero active sources:

| Source Owner | Coverage Gap | Why It Matters |
|-------------|-------------|----------------|
| Dubai/Federal Customs Authority | Not mapped | Trade-facing buyers have zero coverage |
| Ministry of Labour (MOHRE) | Not mapped | Employment compliance is a standard CCO need |
| Ministry of Foreign Affairs (sanctions export) | Not mapped | Export control compliance gap |
| RAK, Sharjah, Ajman free zones | Partially mapped (SAIF Zone only) | Emirate-level free zone compliance |
| Court systems beyond DIFC | Not mapped | Regulatory precedent research |
| Health/pharma regulatory compliance | Not mapped | Relevant for medical device and pharma entities |

These are P3 research items — not blocking for the current UAE financial compliance use case, but represent genuine completeness gaps if "comprehensive UAE coverage" is ever claimed.

---

## 15. Dossier Documents Produced (Full List)

| Document | Purpose | Status |
|----------|---------|--------|
| uae-complete-coverage-proof-dossier-plan.md | Mission plan and gate document | ✅ Created |
| uae-coverage-claim-levels.md | 5-tier claim framework with criteria | ✅ Created |
| uae-regulator-source-owner-coverage-matrix.md | 17 source owners evaluated | ✅ Created |
| uae-source-type-coverage-matrix.md | 16 source types evaluated | ✅ Created |
| uae-source-universe-roadmap-quality-audit.md | Roadmap audit — 7.5/10 score | ✅ Created |
| uae-complete-coverage-gap-verdict.md | 12 Q&A verdicts (YES/PARTIAL/NO) | ✅ Created |
| uae-coverage-public-claim-safety-table.md | 20 claims evaluated | ✅ Created |
| uae-source-universe-prioritized-activation-roadmap.md | Updated — P0 revised to 15 | ✅ Updated |
| uae-complete-coverage-proof-dossier-final-report.md | This document — synthesis | ✅ Created |

Validator: tools/validate_uae_coverage_claims.py — checks all docs, forbidden phrases, source truth.

---

## 16. Product and Sales Next Steps

### Immediate (this week):
1. Run next Codex activation batch (5 sources — see Section 9 above)
2. Use Tier 0 and Tier 1 safe claims in any customer outreach
3. Do not send any UAE coverage claims without the standard short disclaimer
4. Run `python3 tools/validate_uae_coverage_claims.py` before any new coverage claim document is drafted

### After P0 batch (2–4 weeks):
1. Reassess Tier 2 claim strength — if VARA guidance and FTA activate, the bank/VASP demo case improves substantially
2. Update product landing page with exact source count ("84 enabled" or whatever passes gates)
3. Prepare a source-health transparency page or appendix showing status of each monitored source

### Before $399 tier positioning:
1. All 6 "comprehensive" prerequisites must pass gates (see Section 11)
2. Source-health trend documented for 30+ days
3. Pricing decision made by founder separately from source count metric
4. Legal language agent must review all $399 tier copy before publishing

---

## 17. Standard Disclaimer (Required on All Customer-Facing Output)

**Short form (outreach, subject lines, brief headers):**
> Monitoring intelligence only. Not legal advice. Not a guarantee of regulatory completeness.

**Full form (briefs, reports, product descriptions):**
> StatuteProof reports are generated from monitored official-source records and are provided for information and compliance review support only. StatuteProof reports do not constitute legal advice, regulatory advice, compliance certification, or a legal opinion. StatuteProof does not replace qualified legal counsel, compliance professionals, MLROs, or other professional advisers. StatuteProof does not guarantee compliance, prevent fines, or certify that all regulatory updates have been captured. Source monitoring may be affected by publication delays, website changes, PDF formatting, access limits, or source structure changes. Users should verify official source material directly and review evidence records, hashes, timestamps, and diffs before relying on a report. Users should consult qualified legal or compliance professionals before making regulatory, filing, operational, or customer decisions based on a report.

---

*Original dossier completed on 2026-06-17 without source activation. Updated on 2026-06-18 after FTA/ADGM truth repair: sources.json now records 81 enabled / 80 monitoring-active / 1 remediation. FTA remains candidate-only until a future endpoint passes proof, repeat baseline, and MONITOR_OK gates.*
