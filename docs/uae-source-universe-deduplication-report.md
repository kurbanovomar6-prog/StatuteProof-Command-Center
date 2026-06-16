# UAE Source Universe Deduplication Report

Date: 2026-06-17
Sprint: UAE Source Universe Discovery (200–300 target)
Input files:
- product/regradar/sources.json (216 total, 79 enabled)
- product/regradar/config/uae_source_candidates.json (69 candidates, 7 rejected)
- product/regradar/config/uae_source_work_queue.json (127 entries)
- docs/uae-official-endpoint-discovery-150-report.md (151 endpoints)
- product/regradar/config/uae_source_universe_candidates.json (THIS SPRINT — 171 candidates, 32 rejected)

---

## 1. Summary

| Input Stream | Records | Unique After Dedup |
|-------------|---------|-------------------|
| sources.json enabled | 79 | 79 (ground truth) |
| uae_source_candidates.json | 69 | 51 unique (18 overlap with enabled) |
| uae_source_work_queue.json | 127 | ~58 overlap with enabled; 69 non-active |
| 150-report discovery | 151 | ~75 genuinely new beyond prior files |
| New systematic research (this sprint) | ~55 | ~55 genuinely new |
| **Universe candidates JSON (final)** | **203** | **203 unique by source_id** |

Key finding: **0 duplicate source_ids** in the universe candidates JSON. All 203 records have unique IDs confirmed by validator.

---

## 2. Overlap Analysis by Input Stream

### 2a. sources.json → universe_candidates.json

All 79 enabled sources from sources.json are present in universe_candidates.json with `activation_status: already_active`.

Method: Matched on source_id. All 79 matched exactly.

Enabled sources NOT in prior candidate file (uae_source_candidates.json):
- All 27 CBUAE rulebook subpages (AE-cbuae-*-doclist) — added directly in this sprint
- All 8 DIFC data protection sources (AE-difc-data-protection-*)
- All 6 VARA PDF sources (AE-vara-*-pdf)
- The 3 DIFC law-specific pages added in the DIFC remediation sprint

These were active in sources.json but not tracked in the prior candidate research file. Universe candidates JSON now covers all of them.

### 2b. uae_source_candidates.json → universe_candidates.json

Prior candidate file: 69 candidates (18 already-active overlap + 51 not-yet-active)
Of the 51 not-yet-active candidates:
- 34 are included in universe_candidates.json candidates array
- 17 were dropped due to:
  - Duplicate URL under different source_id (resolved by keeping canonical ID)
  - Superseded by better subpage (homepage-only entries collapsed)
  - URL confirmed 404 (documented in rejected array)

### 2c. uae_source_work_queue.json → universe_candidates.json

Work queue: 127 entries (58 activation_ready + 27 candidate + 21 blocked + 19 remediation + 2 baseline_pending)

- 58 activation_ready → all appear in universe_candidates.json as `already_active` (matching sources.json)
- 27 candidates → 22 included in universe_candidates.json candidates; 5 collapsed as duplicates of enabled URLs
- 21 blocked → 10 key entries included as `blocked` or `remediation` status candidates; 11 dropped as duplicate or clearly inaccessible
- 19 remediation → 8 included as `remediation` status; rest collapsed or documented in rejected
- 2 baseline_pending → included as candidates

### 2d. 150-report → universe_candidates.json

150-report: 151 endpoints (75 new beyond prior work queue + 63 existing + 13 supplementary)
- 75 genuinely new endpoints: ~55 included in universe_candidates.json; 20 dropped as P3-niche or duplicate
- Supplementary 12 endpoints: 8 included; 4 documented as rejected (404, 403, unreachable)

---

## 3. Resolved Duplicates

The following duplicate URL situations were resolved in the universe_candidates.json:

| Duplicate Situation | Resolution |
|--------------------|-----------|
| AE-uaefiu-guidance (same URL as AE-uaefiu-circulars) | Kept AE-uaefiu-circulars (already active); marked guidance as note |
| AE-difc-laws-regulations vs AE-difc-laws-and-regulations | Kept AE-difc-laws-and-regulations (already active); rejected duplicate |
| AE-cbuae-homepage vs AE-central-bank-of-the-uae | Kept AE-central-bank-of-the-uae (already active) |
| AE-vara-homepage vs AE-dubai-virtual-assets-regulatory-authority-vara | Kept VARA homepage variant from work queue as separate candidate (different URL) |
| AE-adgm-fsra-public-register vs AE-adgm-fsra-public-register (two different URLs) | adgm.com/public-registers kept; adgm.com/fsra/public-register documented separately |
| AE-mof-homepage vs AE-uae-ministry-of-finance | AE-uae-ministry-of-finance is the active source; mof homepage collapsed |
| AE-sca-decisions vs AE-sca-regulations (same URL) | AE-sca-decisions kept with correct URL |

---

## 4. Coverage Gaps Identified During Deduplication

The deduplication process revealed the following gaps not present in any prior file:

**Gap 1: FTA entirely absent from active pack**
All 7 FTA candidate entries in universe_candidates.json are new. No FTA sources in sources.json.

**Gap 2: Free zone / emirate level entirely absent from active pack**
All 8 J-FreeZone candidates are new. DMCC, DFM, TDRA, UAE Data Office, Dubai Land Dept AML not monitored.

**Gap 3: ADGM RA AML guides not tracked**
AE-adgm-ra-aml-guides (adgm.com/registration-authority/aml-cft-guides) was in 150-report but not in prior candidate file.

**Gap 4: DFSA guidance notes and policy statements not tracked**
AE-dfsa-guidance-notes and AE-dfsa-policy-statements were not in any prior file.

**Gap 5: CBUAE insurance and fintech subpages uncovered**
AE-cbuae-insurance-supervision, AE-cbuae-fintech-office not in any prior file.

---

## 5. Rejected Entries with Documented Reasons

32 entries in the rejected array with explicit reasons. Categories:

| Reject Category | Count |
|----------------|------:|
| URL 404 / path changed | 7 |
| 403 access blocked | 3 |
| Timeout / SPA needs Playwright | 2 |
| Login/private portal | 3 |
| Duplicate of existing active source | 5 |
| Homepage-only (superseded) | 5 |
| Wrong country / non-UAE | 2 |
| Not official source (social media, news) | 4 |
| Site down / ECONNREFUSED | 1 |
| **Total** | **32** |

---

## 6. Deduplication Confidence

| Metric | Status |
|--------|--------|
| source_id uniqueness | ✅ Confirmed (0 duplicates) |
| URL uniqueness (canonical) | ✅ High confidence (some subpage URL variants expected) |
| All 79 active sources covered | ✅ Confirmed |
| All 32 rejected entries have reason | ✅ Confirmed |
| No fake or invented source IDs | ✅ All sources traceable to official UAE regulatory domains |

---

## 7. What This Report Does Not Verify

- Whether all candidate URLs are currently accessible (no-save tests not run in this sprint)
- Whether activated source content has changed since last baseline
- Whether the 3 remediation sources in sources.json have been resolved
- Whether new VARA PDF URLs have updated since 2026-05-19 (the PDF URL contains version date)
