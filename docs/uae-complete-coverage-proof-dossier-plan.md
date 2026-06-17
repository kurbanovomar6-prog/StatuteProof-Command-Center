# UAE Complete Coverage Proof Dossier — Plan

Date: 2026-06-17
Sprint: Coverage Proof Dossier

This document is the plan gate. No code was edited before this plan existed.

---

## 1. Current Truth (Source of Record: sources.json + uae_source_universe_candidates.json)

| Metric | Count |
|--------|------:|
| Total sources.json records | 216 |
| Enabled UAE sources | 79 |
| Readiness-supported | 76 |
| Under extraction remediation | 3 |
| Universe candidate records | 203 |
| Already-active in universe | 79 |
| New candidates in universe | 88 |
| Remediation in universe | 4 |
| Rejected with reason | 32 |

---

## 2. What "Complete UAE Coverage" Would Actually Require

"Complete UAE coverage" is a strong and legally-dangerous claim. To make it defensible, the following would be required:

**A. All Relevant UAE Official Source Owners Identified and Categorised**
Every UAE regulatory authority and officially linked entity relevant to the target buyer segments (MLRO, CCO, legal counsel, fintech, bank, VASP, consultant) must be identified. Missing owners = incomplete coverage.

**B. All Major Source Types Mapped per Owner**
For each source owner, all regulatory-publication surface types must be evaluated: laws, regulations, rulebooks, guidance, circulars, consultations, enforcement, registers, sanctions/TFS. A source owner where only one type is covered (e.g., only rulebooks, not circulars or guidance) is partially covered, not completely.

**C. All Critical Sources Either Active or Explicitly Marked Inaccessible**
Any source that is identified as required but not accessible must be documented with a reason (403, login required, JS SPA without Playwright, site down). "We tried and cannot access it" is defensible. "We never looked" is not.

**D. Proof-Backed Evidence for All Active Sources**
Complete coverage requires that every active source has: SHA-256 hash of normalized content, timestamp, proof_block_path, evidence_record_id, at least two stable baselines, and passing mass-monitor dry-run. Pending evidence = partial credit.

**E. Source-Health Monitoring Demonstrated Over Time**
A single activation check does not prove coverage. Coverage requires demonstrated monitoring cadence, source-health trend data, and documented response to source failures.

**F. No Material Blind Spots for Target Buyers**
Each buyer archetype must have at least one source covering their primary regulatory obligation framework. A blind spot is a regulator that a buyer MUST comply with, where StatuteProof has zero active sources.

**G. Legal-Safe Wording Approved**
Any public "coverage" claim must pass the legal language agent review. No "all," "complete," "guaranteed," "never miss," or "perfect" qualifiers.

---

## 3. Why Current Evidence Does NOT Support "Complete UAE Coverage"

Current evidence supports Tier 1 and Tier 2 claims (see PART 1). It does not support Tier 3 ("Comprehensive") without caveats. It does not support Tier 4 ("Complete") at all.

**Reasons:**
1. FTA (Federal Tax Authority) — 0 active sources. Tax compliance is a legal obligation for almost all UAE entities.
2. VARA guidance and regulatory framework hub — URL broken. VASP buyers need this.
3. VARA AML/CFT rulebook live page — URL broken. MLRO obligation source gap.
4. Ministry of Justice e-laws — candidate only, 0 active. Federal law research gap.
5. ADGM RA notices and AML guides for DNFBPs — candidates only. DNFBP buyer gap.
6. SCA primary securities laws and board decisions — 0 active.
7. CBUAE consultations and publications hub — candidates only.
8. Customs/trade compliance — 0 sources, not in universe.
9. Annual reports — 0 active sources (none monitoring regulatory publication history).
10. Source-health trend data — not yet demonstrated over multi-week period.
11. Public registers — DFSA/VARA/SCA public registers 0 active.

---

## 4. Source Universe Inputs

| Input | Records | Status |
|-------|---------|--------|
| sources.json enabled | 79 | Ground truth |
| uae_source_candidates.json | 69 candidates | Prior sprint data |
| uae_source_work_queue.json | 127 entries | Gate tracking |
| uae-official-endpoint-discovery-150-report.md | 151 endpoints | Discovery sprint |
| uae_source_universe_candidates.json | 203 records | This sprint |

---

## 5. Coverage Dimensions to Verify

1. **Regulator/source owner completeness** — Are all relevant UAE official source owners in the universe?
2. **Source type completeness** — Are all source types covered per owner?
3. **Priority calibration** — Are P0/P1/P2 assignments commercially accurate?
4. **Proof backing** — Do all 78 readiness-supported sources have documented evidence?
5. **Claim safety** — Does any existing document contain unsafe coverage claims?
6. **Buyer coverage** — Does each target buyer have at least one primary obligation source active?
7. **Gap documentation** — Are all known gaps explicitly documented?

---

## 6. Validation Plan

This sprint creates:
- Coverage claim levels (safe tiers)
- Regulator/source owner coverage matrix
- Source type coverage matrix
- Roadmap quality audit
- Complete coverage gap verdict
- Public claim safety table
- Updated roadmap (safe copy only)
- Validator script (docs/claim safety checker)
- Final report

Then runs all existing validators + new claim safety validator.

---

## 7. Commit Policy

- Stage only docs/ and tools/ files from this sprint
- Do not stage sources.json
- Do not stage product/ code unless explicitly changed
- Do not stage __pycache__ or .env
- Commit message: `docs: build UAE coverage proof dossier`
