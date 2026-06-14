# UAE Source Readiness Validation Report

**Date:** 2026-06-13  
**Run data from:** 2026-06-12 (UTC)  
**Run batch ID:** AE-20260612T125401Z-c427013a  
**Validator:** StatuteProof source-monitor + evidence-trail agents  
**Disclaimer:** Monitoring intelligence only. Not legal advice. This report documents source extraction quality and evidence artifacts — it does not certify regulatory coverage or guarantee compliance.

---

## Summary

| Metric | Value |
|---|---|
| Total sources in sources.json | 150 |
| Enabled sources | **13** |
| Sources with run record | 13 / 13 |
| Sources with raw snapshot on disk | 13 / 13 |
| Sources with normalized snapshot on disk | 13 / 13 |
| Sources with proof block on disk | 13 / 13 |
| Sources with content hash | 13 / 13 |
| Proof quality | ALL `LIMITED` (not `COMPLETE`) |
| Sources readiness-supported in current UAE registry | **9** |
| Sources needing remediation in current UAE registry | **4** |
| Sources blocked / inaccessible | **0** |

**Can we describe all 13 enabled UAE sources as fully validated? NO.**
Honest claim: "13 UAE regulatory sources in our source pack — 9 readiness-supported in the current registry, 4 under extraction remediation."

---

## Source Readiness Table

| # | source_id | Name | URL | Enabled | Run exists | Raw exists | Normalized | Hash | Proof | Change status | Extracted chars | Quality | READY | Issue |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | AE-central-bank-of-the-uae | Central Bank of the UAE | centralbank.ae | ✓ | ✓ | ✓ | ✓ | `514682f3c3d8` | ✓ | CHANGED | 26,676 | GOOD | ✓ YES | General homepage. Prefer AE-cbuae-regulations for regulatory content. |
| 2 | AE-dubai-virtual-assets-regulatory-authority-vara | VARA | vara.ae | ✓ | ✓ | ✓ | ✓ | `b423d626358b` | ✓ | CHANGED | 2,576 raw / 44,769 norm | GOOD | ✓ YES (caveat) | Raw HTML shallow (JS SPA). Content comes from PDF augmentation (45,471 PDF chars). New AML/CTF guidance PDF detected. |
| 3 | AE-dubai-financial-services-authority-dfsa | DFSA Rules & Standards | dfsa.ae/rules-and-standards | ✓ | ✓ | ✓ | ✓ | `3021317a497a` | ✓ | UNCHANGED | 4,701 | GOOD | ⚠ REMEDIATION | **CRITICAL: Identical hash to AE-dfsa-notices.** Both URLs extract the same nav-shell content via Playwright. Actual regulatory content not reached. |
| 4 | AE-abu-dhabi-global-market-adgm | ADGM / FSRA | adgm.com/fsra | ✓ | ✓ | ✓ | ✓ | `c7c6e57833bb` | ✓ | UNCHANGED | 2,742 | GOOD | ✓ YES (caveat) | Low char count. No PDFs found. Consistent with prior validation (2,742c noted in sources.json). Unique hash. |
| 5 | AE-uae-ministry-of-finance | UAE Ministry of Finance | mof.gov.ae | ✓ | ✓ | ✓ | ✓ | `d3d0cff4700e` | ✓ | UNCHANGED | 13,389 raw / 44,131 norm | GOOD | ✓ YES | Good extraction. 6 PDFs, 78,266 PDF chars. |
| 6 | AE-uae-legislation-portal | UAE Legislation Portal | uaelegislation.gov.ae | ✓ | ✓ | ✓ | ✓ | `ae996b5574cc` | ✓ | UNCHANGED | 14,694 raw / 5,176 norm | GOOD | ✓ YES (caveat) | Notes flag WAF/access constraints and aggregate-page change noise. No PDFs extracted. |
| 7 | AE-uae-financial-intelligence-unit-uaefiu | UAE FIU Homepage | uaefiu.gov.ae | ✓ | ✓ | ✓ | ✓ | `5f77f00c7bbb` | ✓ | UNCHANGED | 2,026 raw / 1,601 norm | GOOD | ⚠ REMEDIATION | **LOW CHARS: 2,026.** Homepage-only extraction. No PDFs. Too shallow for reliable regulatory monitoring. Recommend switching monitoring to AE-uaefiu-circulars (already enabled). |
| 8 | AE-difc-laws-and-regulations | DIFC Laws & Regulations | difc.com/business/laws-and-regulations | ✓ | ✓ | ✓ | ✓ | `fb108f2e7625` | ✓ | UNCHANGED | 9,150 raw / 11,202 norm | GOOD | ⚠ REMEDIATION | Registry hold: source structure/access remediation remains open before customer-visible ready status. |
| 9 | AE-uae-ministry-of-economy | UAE Ministry of Economy | moet.gov.ae/en | ✓ | ✓ | ✓ | ✓ | `f88791e8d578` | ✓ | CHANGED | 21,374 raw / 6,906 norm | GOOD | ✓ YES | Meaningful change detected (link removal). No PDFs — may miss PDF-heavy regulatory publications. |
| 10 | AE-vara-enforcement | VARA Enforcement Notices | vara.ae/en/enforcement | ✓ | ✓ | ✓ | ✓ | `707b3094d76f` | ✓ | UNCHANGED | 12,677 raw / 10,560 norm | GOOD | ✓ YES | Best source for sample brief. Clean, unique, well-extracted enforcement listing. |
| 11 | AE-cbuae-regulations | CBUAE Regulations Sub-page | centralbank.ae/en/regulations | ✓ | ✓ | ✓ | ✓ | `985856733f95` | ✓ | CHANGED | 27,509 raw / 38,131 norm | GOOD | ✓ YES (caveat) | **CHANGE NOISE:** 69 changed chunks are page rating counters ("Rated by 1009 People") not regulatory content. Needs counter-change filter. 20 PDFs, 20,893 PDF chars. |
| 12 | AE-uaefiu-circulars | UAE FIU Circulars & Notices | uaefiu.gov.ae/en/Publications | ✓ | ✓ | ✓ | ✓ | `0bb1771e80a5` | ✓ | UNCHANGED | 4,102 raw / 3,458 norm | GOOD | ✓ YES | Publications listing page. Preferred over homepage for AML/CFT monitoring. |
| 13 | AE-dfsa-notices | DFSA Regulatory Notices | dfsa.ae/regulation/notices-public-registers | ✓ | ✓ | ✓ | ✓ | `3021317a497a` | ✓ | UNCHANGED | 4,701 raw / 2,653 norm | GOOD | ⚠ REMEDIATION | **CRITICAL: Identical hash to AE-dubai-financial-services-authority-dfsa.** Same nav-shell content extracted from both DFSA URLs. Scraper not reaching actual notices content. |

---

## Readiness-Supported Sources In Current Registry (9)

These sources passed all checks: accessible, raw snapshot on disk, normalized snapshot on disk, proof block on disk, hash computed, extraction quality GOOD, unique content hash, no critical anomalies.

1. **AE-central-bank-of-the-uae** — CBUAE homepage. 26,676 chars + 31,083 PDF chars. Changed (meaningful).
2. **AE-dubai-virtual-assets-regulatory-authority-vara** — VARA homepage. JS SPA with PDF augmentation — 44,769 normalized chars, new AML/CTF guidance detected.
3. **AE-abu-dhabi-global-market-adgm** — ADGM/FSRA. 2,742 chars, low but unique and consistent.
4. **AE-uae-ministry-of-finance** — MoF. 13,389 chars + 78,266 PDF chars. Strong.
5. **AE-uae-legislation-portal** — UAE legislation portal. 14,694 chars. WAF constraint noted.
6. **AE-uae-ministry-of-economy** — MoEcT. 21,374 chars. Meaningful change detected.
7. **AE-vara-enforcement** — VARA enforcement notices. 12,677 chars. Clean, stable.
8. **AE-cbuae-regulations** — CBUAE regulations sub-page. 27,509 chars + 20,893 PDF chars. Change noise present (rating counters) — needs filter before alert delivery.
9. **AE-uaefiu-circulars** — UAE FIU publications. 4,102 chars. Preferred FIU monitoring source.

---

## Sources Needing Remediation In Current Registry (4)

### 1. AE-dubai-financial-services-authority-dfsa — CRITICAL: Hash collision

**Issue:** `dfsa.ae/rules-and-standards` and `dfsa.ae/regulation/notices-public-registers` produce **identical** raw hash, normalized hash, and content hash (`3021317a497a76b0...`). Both URLs extract only the DFSA site navigation shell (first 200 chars: "About us Go Back Who we are The DFSA Governance..."). Actual regulatory content (rules text, notices list) is not being extracted.

**Root cause:** DFSA site appears to use client-side rendering. Playwright is fetching the HTML shell before content renders. `fetch_method: playwright` confirmed on both — the renderer is not waiting for content injection.

**Impact:** Two enabled sources effectively produce zero unique regulatory monitoring signal. One is indistinguishable from the other. No regulatory content being tracked.

**Recommended fix:**
1. Add explicit Playwright wait selector (e.g., wait for `[data-content]` or main content element)
2. Or switch `AE-dubai-financial-services-authority-dfsa` URL to DFSA rulebook PDF index page
3. If DFSA site cannot be rendered: mark source status as `limited` with documented access constraint
4. Remove or consolidate one of the two DFSA sources until extraction is fixed

---

### 2. AE-dfsa-notices — CRITICAL: Hash collision (same as above)

Same issue as above. The DFSA notices URL (`dfsa.ae/regulation/notices-public-registers`) produces identical content to the DFSA rules URL. See remediation above.

---

### 3. AE-difc-laws-and-regulations — REGISTRY HOLD

**Issue:** The 2026-06-12 evidence run extracted meaningful text, but the current source registry keeps this source under remediation. Treat it as a hold until the source structure/access concern is resolved and reviewed.

**Impact:** Do not display DIFC Laws and Regulations as customer-visible ready until Source Monitor and Evidence Trail review the registry hold.

**Recommended fix:**
- Re-run a no-save Source Lab check with the current URL and selector strategy
- Verify the normalized content is meaningful, hash-unique, and stable
- Move the source only after evidence-readiness review and founder approval

---

### 4. AE-uae-financial-intelligence-unit-uaefiu — LOW CHAR COUNT

**Issue:** UAE FIU homepage extraction yields only 2,026 chars (1,601 normalized). No PDF links found. This is a homepage-level shell — not regulatory content monitoring.

**Impact:** Changes to this source's monitoring signal would reflect homepage UI updates, not regulatory publications. Unreliable for AML/CFT compliance monitoring.

**Recommended fix:**
- Demote `AE-uae-financial-intelligence-unit-uaefiu` from primary to reference
- Promote `AE-uaefiu-circulars` (already enabled, 4,102 chars, publications listing page) as the primary UAE FIU monitoring source
- Alternatively: update the URL to the FIU circulars/publications page directly and deprecate the homepage entry

---

## Proof Quality Assessment

**All 13 sources have `proof_quality: LIMITED`.**

This is the current pipeline tier. LIMITED means:
- Run record exists ✓
- Raw snapshot saved ✓
- Normalized snapshot saved ✓
- Content hash computed ✓
- Proof block JSON created ✓
- Diff computed where applicable ✓

LIMITED does NOT mean:
- Timestamped cryptographic signature (external timestamp authority)
- Multi-run baseline establishment (requires 3+ run cycles)
- Human review of extracted content quality
- Regulatory content classification (verified that extracted text is regulatory, not nav/header noise)

For audit-grade evidence (`proof_quality: COMPLETE`), the pipeline would need: external timestamp, multi-run baseline, and content classification.

---

## Change Detection Results (2026-06-12 vs 2026-06-11)

Change detection is **deterministic hash comparison only** — no LLM used.

| Source | Change status | Meaningful | Description |
|---|---|---|---|
| AE-central-bank-of-the-uae | CHANGED | Yes | Financial rate updates and site content changes |
| AE-dubai-virtual-assets-regulatory-authority-vara | CHANGED | Yes | **New AML/CTF document detected:** `vara-amlctf-business-risk-assessment-guidance.pdf` published. 170 added chunks, 34 removed. |
| AE-uae-ministry-of-economy | CHANGED | Yes | Link removal: "Ministry of Economy Publications" section removed from page |
| AE-cbuae-regulations | CHANGED | Yes (noisy) | 69 changed chunks — primarily page rating counter ("Rated by 1009 People" → "Rated by 1009 People"). Regulatory content unchanged. **Needs counter-change filter.** |
| All others | UNCHANGED | — | No changes detected |

---

## Recommended Wording for Pricing / Homepage

**DO NOT USE:** language that describes all 13 enabled UAE sources as validated.

**DO NOT USE:** language that describes all 13 enabled UAE regulatory sources as confirmed.

**USE (honest):**
- "UAE regulatory source pack — 13 sources enabled, evidence-readiness review in progress"
- "13 enabled UAE sources — 9 readiness-supported in the current registry, 4 under extraction remediation"
- "Latest readiness run artifacts available for sources that completed proof validation"
- "Covers VARA, CBUAE, DFSA, ADGM, UAE FIU, DIFC and more — source readiness validation in progress"
- "13 UAE regulatory sources under evidence-readiness review" (acceptable during validation period)

**After remediation fixes are confirmed:**
- Update the source count only after live checks, evidence review, and registry status are aligned.

---

## Best Source for First SAMPLE / FAKE Brief

**Recommended: AE-vara-enforcement (VARA Enforcement Notices)**

Reasons:
- 12,677 chars, unique hash, GOOD extraction quality
- Clean enforcement listing page — no duplicate hash issues
- UNCHANGED — stable baseline, no change noise
- VARA is the highest-profile UAE regulatory brand for virtual assets
- Enforcement content (notices, actions) is unambiguous regulatory material
- No PDFs required — full content from HTML extraction

**Alternative for a "change detected" brief: AE-dubai-virtual-assets-regulatory-authority-vara**

The 2026-06-12 run detected a new VARA AML/CTF guidance PDF (`vara-amlctf-business-risk-assessment-guidance.pdf`). This is an ideal basis for a CHANGED event brief showing the pipeline detecting a new regulatory publication. Label any generated brief `SAMPLE / FAKE — not an actual customer brief` per CLAUDE.md rules.

---

## What Must Be Fixed Before Claiming Full UAE Source-Pack Readiness

| Fix | Source(s) affected | Priority |
|---|---|---|
| Resolve DFSA hash collision — extract actual page content | AE-dfsa-notices, AE-dubai-financial-services-authority-dfsa | HIGH |
| Resolve current DIFC registry hold | AE-difc-laws-and-regulations | HIGH |
| Upgrade UAE FIU monitoring URL to publications page | AE-uae-financial-intelligence-unit-uaefiu | MEDIUM |
| Add counter-change noise filter for CBUAE regulations | AE-cbuae-regulations | LOW |
| Establish 3-run baseline for all sources (multi-run validation) | All 13 | MEDIUM |
| Promote proof_quality from LIMITED to COMPLETE for at least 3 sources | Top 3 priority sources | LOW |

---

## Evidence Artifact Locations

All run-batch artifacts are at:
```
data/source_snapshots/2026-06-12/AE/{source_id}/AE-20260612T125401Z-c427013a/
  raw.txt          — raw extracted text
  normalized.txt   — normalized clean text
  proof.json       — evidence record with hashes, timestamps, diff paths
  diff.json        — structured diff (CHANGED sources only)
  diff.md          — human-readable diff (CHANGED sources only)
  pdf_text.txt     — extracted PDF text (sources with PDFs only)
```

Run records consolidated in:
```
data/source_runs/source_runs.jsonl  — 198 records, 22 unique source IDs
```

---

## Next Exact Task

**Fix the DFSA hash collision (highest priority).**

1. Open `product/regradar/app/` — find the scraper/fetch module that handles Playwright extraction
2. Add a wait-for-content mechanism for the DFSA site (wait for selector that confirms page content has loaded beyond the nav shell)
3. Re-run extraction for AE-dubai-financial-services-authority-dfsa and AE-dfsa-notices
4. Confirm the two sources now produce **different** content hashes
5. Verify extracted content includes regulatory text (rules, notices) not just navigation
6. Update the run records and proof blocks
7. Then: upgrade AE-uae-financial-intelligence-unit-uaefiu URL to the publications page

Until these fixes are reviewed, the honest source count for customer-facing claims is **9 readiness-supported and 4 under remediation, not 13 ready.**
