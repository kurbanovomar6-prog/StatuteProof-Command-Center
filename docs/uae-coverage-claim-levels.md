# UAE Coverage Claim Levels

Date: 2026-06-17
Purpose: Define safe claim tiers for UAE regulatory source monitoring coverage.
Legal safety: Every claim tier must be used exactly as written, without embellishment.

---

## Tier 0 — Source Count Claim (SAFE — use today)

**Definition:** A factual count of enabled and readiness-supported sources.

**Safe wording:**
> "79 enabled UAE official-source endpoints. 76 readiness-supported. 3 under extraction remediation."

**Why it is safe:**
- These are exact counts directly verifiable in sources.json.
- No implication of completeness or comprehensive coverage.
- Counts of a specific status category, not a claim about the regulatory universe.

**When to use:**
- All customer-facing materials.
- Demo slides, pilot proposals, outreach.
- Any time a prospect asks "how many sources?"

**Never embellish with:**
- "over 100 sources" (not true)
- "all major regulators" (VARA guidance gap)
- "never miss" (not supported)

**Current status:** SAFE. Use now.

---

## Tier 1 — Source Universe Mapping Claim (SAFE — use today)

**Definition:** A claim about the scope of source universe research and candidate documentation, not about active monitoring.

**Safe wording:**
> "StatuteProof has mapped 200+ official or officially linked UAE regulatory and compliance source candidates across 10 regulatory categories."

**Or:**
> "Our documented source universe covers 200+ official UAE regulatory endpoints from 18+ source owners, including CBUAE, DFSA, ADGM/FSRA, VARA, UAE FIU, EOCN, SCA, DIFC, Ministry of Finance, Ministry of Economy, UAE Legislation Portal, Federal Tax Authority, Ministry of Justice, DMCC, and others."

**Why it is safe:**
- "Mapped" and "candidates" are accurate words — these are research records, not active sources.
- "200+" is accurate (203 records confirmed by validator).
- "10 regulatory categories" is accurate (A–J taxonomy).
- Makes no claim about activation status, proof backing, or completeness.

**When to use:**
- Investor materials showing pipeline depth.
- Sales conversations with "what's in your roadmap?"
- Coverage expansion slide in a pitch deck.

**Never embellish with:**
- "200+ sources monitored" (only 79 are active)
- "complete UAE coverage mapped" (18 owners mapped but not all critical gaps closed)

**Current status:** SAFE. Use now. Clearly distinguish "mapped candidates" from "active sources."

---

## Tier 2 — Major Regulator Coverage Claim (SAFE WITH CAVEATS)

**Definition:** A claim that major UAE regulatory families are represented in the active monitoring pack.

**Safe wording:**
> "StatuteProof monitors selected official sources across major UAE regulatory bodies including CBUAE, DFSA, ADGM/FSRA, VARA, UAE FIU, EOCN, SCA, and DIFC."

**Or:**
> "Coverage across UAE's major financial, AML/CFT, virtual asset, securities, and financial free-zone regulatory source families."

**Why it is conditionally safe:**
- All named regulators have at least 5 active sources each (CBUAE: 27, DFSA: 10, ADGM: 10, VARA: 9, FIU/EOCN: 7+, SCA: 5, DIFC: 8).
- "Selected official sources" hedges against completeness claims.
- "Major" is hedged — does not say "all" or "complete."

**Caveats required:**
- Do not say "all CBUAE/DFSA/ADGM regulations" — only selected endpoints are monitored.
- VARA has a gap: regulatory framework hub URL is broken. Cannot say VARA guidance is covered.
- SCA has a gap: primary securities laws and board decisions are not active.
- Must accompany with: "Source selection does not represent complete regulatory coverage. Users must verify directly with official sources and consult qualified professionals."

**Required disclaimer:**
> "Monitoring selected public official sources. Not guaranteed to capture all regulatory updates. Not legal advice."

**When to use:**
- Demo conversations with MLRO/CCO buyers.
- Pilot proposal deck "coverage overview" slide.
- Prospect emails after first call.

**Current status:** SAFE WITH CAVEAT. Add disclaimer on every use.

---

## Tier 3 — Comprehensive UAE Official-Source Monitoring Claim (CONDITIONAL — NOT YET SAFE)

**Definition:** A claim that StatuteProof provides broad, systematic, buyer-relevant coverage of the UAE official regulatory source universe.

**Would require all of the following:**
1. All major UAE regulatory source owners have at least one active source covering their primary regulatory publication type.
2. All critical regulatory domains have active coverage: laws, rulebooks, AML/CFT guidance, enforcement, consultations.
3. VARA guidance and regulatory framework hub are active (currently broken URL).
4. SCA primary securities legislation is active.
5. FTA has at least one active source (currently 0 active).
6. CBUAE consultations are active.
7. All 76 readiness-supported sources have documented proof records.
8. Source-health trend monitoring is demonstrated.
9. Legal-safe wording is in place.

**Current status:** NOT YET SAFE. Missing:
- VARA guidance (broken URL)
- SCA laws and decisions (candidates only)
- FTA (0 active)
- CBUAE consultations (candidate only)
- ADGM RA AML guides for DNFBPs (candidate only)

**Earliest this could be used:** After P0 activation sprint resolves the top 5 gaps above.

**Provisional safe wording (for use only after P0 sprint):**
> "StatuteProof monitors selected official sources across all major UAE financial regulatory authorities, including CBUAE, DFSA, ADGM/FSRA, VARA, UAE FIU, EOCN, SCA, and DIFC, as well as federal legislation and tax authority sources. Source selection is based on MLRO, CCO, and compliance manager relevance."

**Still required with this wording:**
> "Coverage is based on publicly accessible official sources. StatuteProof does not guarantee completeness or capture of all regulatory updates. Not legal advice."

---

## Tier 4 — Complete UAE Coverage Claim (DEFAULT: NO)

**Definition:** A claim that StatuteProof captures all or essentially all UAE regulatory updates relevant to compliance professionals.

**Would require all of the following:**
1. Every relevant UAE official source owner identified and evaluated.
2. Every major source type mapped per owner.
3. All critical sources either active or explicitly documented as inaccessible.
4. No material blind spots for any target buyer segment.
5. Source-health trend data over minimum 3 months.
6. Legal-safe wording approved by qualified legal review.
7. Demonstrated recall rate (updates published vs. updates detected — measurable).

**Current verdict:** NO. Tier 4 cannot be claimed. Reasons:
- FTA 0 active.
- VARA framework hub broken.
- Customs/trade compliance: not in universe.
- Annual reports: 0 active.
- Source-health trend: less than 3 months of data.
- Recall rate: not measured.
- Ministry of Justice: 0 active.
- SCA primary legislation: 0 active.
- Public registers: 1 active (ADGM waivers) — DFSA, VARA, SCA registers 0 active.

**This claim must never appear in any StatuteProof document, marketing, pitch, or email.**

**Forbidden phrases (all imply Tier 4):**
- "Complete UAE coverage"
- "All UAE regulations"
- "Never miss an update"
- "Comprehensive UAE regulatory monitoring" (without Tier 3 criteria met)
- "Covers all major regulations"
- "Full compliance coverage"
- "Monitor everything"

---

## Current Claim Level Assessment

| Claim Level | Currently Safe | Next Gate |
|-------------|---------------|-----------|
| Tier 0 — Source count | ✅ YES | None — use now |
| Tier 1 — Universe mapping | ✅ YES | None — use now |
| Tier 2 — Major regulator coverage | ✅ CONDITIONAL | Add disclaimer always |
| Tier 3 — Comprehensive UAE monitoring | ❌ NOT YET | P0 activation sprint + VARA URL fix |
| Tier 4 — Complete UAE coverage | ❌ NO | 3+ months data + Customs + MoJ + FTA active + recall rate |

---

## Correct Positioning Statement (Use This)

> "StatuteProof monitors selected public official UAE regulatory sources — 79 active endpoints across major UAE financial regulators — and provides evidence-backed monitoring intelligence, source-health visibility, and compliance review support. Monitoring intelligence only. Not legal advice. Not a guarantee of regulatory completeness."
