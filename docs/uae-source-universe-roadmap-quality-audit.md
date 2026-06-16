# UAE Source Universe Roadmap Quality Audit

Date: 2026-06-17
Input: docs/uae-source-universe-prioritized-activation-roadmap.md
Auditor role: QA/Critic + Legal Language + Product Manager + Source Monitor + CTO

---

## 1. Overall Roadmap Quality Verdict

**Score: 7.5/10**

The roadmap is honest and detailed. It correctly identifies P0 through remediation tiers and includes the gate sequence. No obviously fake sources. No fraudulent evidence claims.

**Strengths:**
- Gate reminder is prominent and clear.
- Rejected tier is documented with 32 entries and explicit reasons.
- Remediation items are actionable.
- 203 total records is accurate.
- Timeline estimates are honest (not aggressive).

**Weaknesses:**
- One overclaim in Section 5 ("What 100 Active Sources Enables Commercially"): the phrase "Full AML/CFT monitoring across all major regulatory families" is not safe.
- P0 list includes some items that are already active or that have gaps in justification.
- "Activate as Soon as Possible" framing for all 25 P0 items overpromises delivery speed.
- P2 is too vague — "Activate when capacity allows" with 75 items listed is not actionable.
- $399 tier positioning is linked to 100 sources without adequate caveats.

---

## 2. Are P0 Priorities Truly P0?

**Review of the 25 P0 items:**

| # | Source ID | P0 Justified? | Verdict |
|---|-----------|--------------|---------|
| 1 | AE-vara-activity-rulebooks-hub | YES — VARA hub, fills rulebook coverage gap | ✅ KEEP P0 |
| 2 | AE-vara-guidance | YES — critical VASP MLRO gap | ✅ KEEP P0 |
| 3 | AE-vara-administrative-orders | YES — enforcement monitoring gap | ✅ KEEP P0 |
| 4 | AE-uaefiu-nra-2024 | YES — most cited single MLRO document | ✅ KEEP P0 |
| 5 | AE-uaefiu-strategic-analysis | P0 is borderline — this is important but not as urgent as NRA | ⚠️ MOVE TO P1 |
| 6 | AE-uaefiu-mutual-evaluation | P1 is more appropriate — FATF MER is significant but static | ⚠️ MOVE TO P1 |
| 7 | AE-cbuae-aml-cft | YES — bank MLRO gap, work queue candidate | ✅ KEEP P0 |
| 8 | AE-cbuae-consultations | YES — horizon scanning gap for largest regulator | ✅ KEEP P0 |
| 9 | AE-cbuae-circular-bank-supervision | P1 is appropriate — circulars are valuable but not more urgent than VARA/FIU NRA | ⚠️ MOVE TO P1 |
| 10 | AE-adgm-ra-aml-guides | YES — DNFBP MLRO gap, low technical risk | ✅ KEEP P0 |
| 11 | AE-adgm-ra-notices | P1 is appropriate — RA notices are important but secondary to AML guides | ⚠️ MOVE TO P1 |
| 12 | AE-adgm-media-announcements | YES — confirmed accessible, high commercial signal | ✅ KEEP P0 |
| 13 | AE-adgm-fsra-notices | P1 appropriate — FSRA notices important but secondary to media announcements | ⚠️ MOVE TO P1 |
| 14 | AE-dfsa-guidance-notes | YES — most commonly referenced DFSA practitioner resource | ✅ KEEP P0 |
| 15 | AE-dfsa-rulebook-official | P1 — DFSA official rulebook page has low additional value vs. Thomson Reuters source | ⚠️ MOVE TO P1 |
| 16 | AE-dfsa-aml-ctf-sanctions | YES — AML/CTF hub page, fills navigation gap | ✅ KEEP P0 |
| 17 | AE-sca-laws | YES — primary SCA legislation, most important SCA gap | ✅ KEEP P0 |
| 18 | AE-sca-decisions | YES — SCA board decisions complete the legislative picture | ✅ KEEP P0 |
| 19 | AE-sca-regulations-amendments | P1 appropriate — amendments are useful but secondary to primary legislation | ⚠️ MOVE TO P1 |
| 20 | AE-moec-aml-dnfbp | YES — Ministry of Economy AML for DNFBPs, emerging buyer segment | ✅ KEEP P0 |
| 21 | AE-difc-consultation-papers | P1 appropriate — DIFC consultations are valuable but DFSA/CBUAE consultations are more urgent | ⚠️ MOVE TO P1 |
| 22 | AE-uaefiu-annual-reports | P1 appropriate — annual reports are useful but not P0 urgency | ⚠️ MOVE TO P1 |
| 23 | AE-uaefiu-press-releases | P2 — press releases are high-churn, low compliance-signal | ⚠️ MOVE TO P2 |
| 24 | AE-dfsa-publications | P1 — publications hub is an umbrella; activate specific subpages first | ⚠️ MOVE TO P1 |
| 25 | AE-cbuae-publications | P1 — publications hub useful but secondary to AML/CFT and consultations | ⚠️ MOVE TO P1 |

**Revised P0 list (15 items, down from 25):**
1. AE-vara-activity-rulebooks-hub
2. AE-vara-guidance
3. AE-vara-administrative-orders
4. AE-uaefiu-nra-2024
5. AE-cbuae-aml-cft
6. AE-cbuae-consultations
7. AE-adgm-ra-aml-guides
8. AE-adgm-media-announcements
9. AE-dfsa-guidance-notes
10. AE-dfsa-aml-ctf-sanctions
11. AE-sca-laws
12. AE-sca-decisions
13. AE-moec-aml-dnfbp
14. AE-fta-corporate-tax-guides (missing from P0 — FTA gap is too important)
15. AE-fta-vat-public-clarifications (missing from P0 — universal UAE obligation)

---

## 3. Are Already-Active Sources Incorrectly Listed?

Scanning P0/P1 lists...

| Source ID | Listed In Roadmap As | Correct Status |
|-----------|---------------------|----------------|
| AE-sca-corporate-governance | Listed in P1 as "already active" | ✅ Correct — is active in sources.json |
| AE-mof-homepage | Listed in P1 as candidate | AE-uae-ministry-of-finance IS active; mof.gov.ae is the same URL → ✅ Collapsed correctly |
| AE-dfsa-consultation-papers | Listed separately from AE-dfsa-consultation-current | AE-dfsa-consultation-current IS active; the work-queue entry AE-dfsa-consultation-papers is a subpage → ⚠️ CLARIFY — note the active source covers the parent; subpage may add value |

**Verdict:** No already-active sources are incorrectly listed as needing activation. One clarification needed for DFSA consultation pages overlap.

---

## 4. Are Any P0 Sources Too Risky?

| Source | Risk Assessment |
|--------|----------------|
| AE-vara-guidance | Medium risk — vara.ae URL needs Playwright verification. Do not activate without no-save quality ≥60. |
| AE-vara-administrative-orders | Medium risk — VARA site is JS-heavy. Same caveat. |
| AE-eocn-tfs | HIGH RISK — TFS page may update very frequently (sanctions designations). Raw hash monitoring will generate excessive alerts. Needs smart parsing before activation. **Should NOT be in P0 or P1 without noise-risk validation.** |
| AE-cbuae-aml-cft | Medium risk — Umbraco CMS blocks bs4. Needs Playwright or custom selector. Do not activate with generic adapter. |

**Action required:** Remove AE-eocn-tfs from P1 or add explicit noise-risk warning. This source needs a sanctions-specific adapter before any activation.

---

## 5. Is "Full AML/CFT Monitoring Across All Major Regulatory Families" Safe?

**Verdict: NO — this phrase is an overclaim.**

Current AML/CFT monitoring:
- CBUAE: Strong (AML/CFT rulebook, TBML, proliferation finance guidance active)
- DFSA: Strong (AML rulebook, MLRO letters, enforcement active)
- ADGM: Adequate (financial crime prevention, enforcement active)
- UAE FIU: Adequate (AML/CFT laws, typology reports, publications hub active)
- EOCN: Partial (laws active, TFS page not active)
- VARA: Weak (AML/CFT rulebook live page is broken URL — not active)
- SCA: Partial (AML/CFT regulation active; no AML guidance)
- DIFC: Partial (no DIFC Financial Crime Authority active)

"Full AML/CFT monitoring across all major regulatory families" implies VARA AML is covered. It is not.

**Safe replacement:**
> "AML/CFT monitoring across CBUAE, DFSA, ADGM/FSRA, UAE FIU, EOCN, and SCA regulatory sources. VARA AML/CFT live guidance monitoring pending URL resolution."

---

## 6. Is "100 Active Sources Enables $399" Safe?

**Verdict: CONDITIONAL — needs caveat.**

The current wording:
> "This is the commercial threshold for the $399 UAE Monitor tier upgrade from the $199 founding pilot."

Issues:
1. It implies 100 sources automatically justifies $399 pricing. The pricing decision requires business judgment, not just a source count.
2. It makes a product commitment about pricing thresholds not established in plan.py.
3. A buyer reading this could claim the price should be $199 until 100 sources are active.

**Safe replacement:**
> "At 100 active sources, StatuteProof has a credible foundation for the $399 UAE Monitor tier positioning. Pricing is a commercial decision made by the founder separately from source count alone."

---

## 7. Are Activation Timelines Realistic?

| Estimate | Verdict |
|----------|---------|
| "P0 activation (25 sources) — 2–3 weeks" | Optimistic. After revising P0 to 15 sources, 2–3 weeks is achievable for 10–12 sources. Full 15 may take 3–4 weeks. |
| "P1 activation (50 sources) — 4–6 weeks" | Aggressive. P1 has medium-to-high technical complexity (Umbraco CMS, custom_element adapters, Playwright needed). 8–12 weeks is more realistic. |
| "P2 activation (subset) — 8–12 weeks" | Only achievable if P1 is done and adapters are reusable. |
| "2–4 hours per source" | Accurate for easy sources. For JS-heavy CBUAE/DFSA pages, 4–8 hours is realistic. |

**Action required:** Soften P1 timeline or add a caveat: "Assumes existing adapter families apply and no new Playwright extraction is required."

---

## 8. Is P2 Too Vague?

**Verdict: YES — P2 is too vague.**

The current P2 section is a narrative paragraph with "many P2 sources need no-save testing." This is not actionable for Codex execution.

**Required addition:** A P2 mini-batch list with at least the top 10 P2 targets in priority order, with adapter estimate per source.

**Top 10 P2 targets to add explicitly:**
1. AE-uaefiu-strategic-analysis (moved from P0 — still high value)
2. AE-uaefiu-mutual-evaluation (moved from P0 — static document)
3. AE-adgm-ra-notices (moved from P0 — ADGM RA pattern)
4. AE-difc-consultation-papers (moved from P0 — DIFC HTML pattern)
5. AE-cbuae-publications (moved from P0 — Playwright needed)
6. AE-dfsa-publications (moved from P0 — JS-heavy)
7. AE-adgm-fsra-notices (moved from P0 — custom_element pattern)
8. AE-uaefiu-annual-reports (moved from P0 — FIU listing pattern)
9. AE-sca-regulations-amendments (moved from P0 — SCA listing pattern)
10. AE-cbuae-consumer-protection (work queue candidate — Playwright needed)

---

## 9. Are Rejected Reasons Sufficient?

**Review of 32 rejected entries:**

All 32 have `url`, `source_id`, `reject_reason`, and `category` fields. Reasons are specific (404, 403, login, duplicate, wrong country). No rejected entry says only "not useful" without a specific reason.

**Verdict: ADEQUATE.** No changes needed.

---

## 10. Are Remediation Items Actionable?

| Source | Current Hint | Actionable? |
|--------|-------------|-------------|
| AE-vara-regulatory-framework | "Find new VARA framework URL via browser" | ✅ Yes — specific action described |
| AE-vara-company-rulebook | "Find new URL; may be at rulebooks.vara.ae subpage" | ✅ Yes |
| AE-vara-aml-cft-rulebook | "Find new URL; may be PDF at rulebooks.vara.ae" | ✅ Yes |
| AE-vara-rulebooks-overview | "Replace with AE-vara-activity-rulebooks-hub" | ✅ Yes |
| AE-uaefiu-guidance | "Verify if distinct content; merge or close" | ✅ Yes |
| AE-difc-legislation | "Verify if accessible; use difc.com canonical" | ✅ Yes |
| AE-adgm-fsra-rules-fsra-domain | "Check if same content as adgm.com rulebooks" | ✅ Yes |

**Verdict: ALL ACTIONABLE.** No changes needed.

---

## 11. Next Best P0 Activation Batch for Codex

Based on this audit, the recommended **next Codex activation batch** (max 5 sources, lowest technical risk):

| Rank | Source ID | Adapter | Why First |
|------|-----------|---------|-----------|
| 1 | AE-uaefiu-nra-2024 | pdf_listing | Static page, expected low friction, highest commercial value |
| 2 | AE-vara-activity-rulebooks-hub | listing | rulebooks.vara.ae domain — known pattern from active update source |
| 3 | AE-adgm-ra-aml-guides | pdf_listing | Known ADGM PDF listing pattern; DNFBP gap |
| 4 | AE-sca-laws | listing (sca_listing pattern) | Known SCA adapter; primary legislation gap |
| 5 | AE-fta-corporate-tax-guides | listing | New FTA coverage; expected accessible; high commercial value |

Run in order. Each requires: no-save preview → quality check ≥60 → evidence save → repeat baseline → mass-monitor dry-run → 6-agent gate.

---

## 12. Summary of Required Roadmap Edits

| Change | Priority |
|--------|----------|
| Revise P0 to 15 items (remove 10, add FTA) | HIGH |
| Soften "Full AML/CFT monitoring across all major regulatory families" | HIGH |
| Add caveat to 100-sources/$399 positioning | MEDIUM |
| Soften P1 timeline from 4–6 weeks to 8–12 weeks | MEDIUM |
| Add explicit top-10 P2 mini-batch | MEDIUM |
| Add EOCN TFS noise-risk warning | HIGH |
| Add next Codex activation batch (5 sources) | HIGH |
