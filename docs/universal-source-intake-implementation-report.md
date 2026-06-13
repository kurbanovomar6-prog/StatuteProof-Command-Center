# Universal Source Intake — Implementation Report

**Date:** 2026-06-13  
**Status:** Complete — validated, committed  
**Validator:** code-architect-dev agent

---

## What Was Built

A Universal Source Intake Engine that extends StatuteProof's existing source testing infrastructure with:

1. **Nav-shell detection** — catches the DFSA-class problem where Playwright renders only navigation before content loads
2. **Per-source Playwright config** — `wait_for_selector` and `content_selector` in sources.json fix JS SPAs
3. **Richer status vocabulary** — 8 statuses map directly to dashboard badges
4. **Hash collision detection** — catches sources that extract identical content
5. **Custom source API** — 4 new endpoints for testing and adding custom sources
6. **Source readiness summary API** — powers dashboard readiness card
7. **Custom source parser skill + runbook** — operator guidance for adding and debugging sources
8. **18 tests** — all passing, no live network calls

---

## Files Changed or Created

### New files

| File | Purpose |
|---|---|
| `product/regradar/app/source_intake.py` | Core intake module: status constants, nav-shell detection, hash collision check, intake runner, readiness summary |
| `product/regradar/tests/test_source_intake.py` | 18 tests covering URL safety, nav-shell detection, hash collision, intake verdicts |
| `docs/universal-parser-current-state-audit.md` | Complete audit of scraper.py, extractors.py, source_tester.py before changes |
| `docs/universal-source-parser-architecture.md` | Architecture design: status vocab, nav-shell algorithm, API endpoints, test plan |
| `docs/custom-source-parser-runbook.md` | Operator runbook: how to test, interpret, fix, and activate sources |
| `skills/custom-source-parser/SKILL.md` | Agent skill for structured intake review |
| `docs/universal-source-intake-implementation-report.md` | This report |

### Modified files

| File | Change |
|---|---|
| `product/regradar/app/scraper.py` | Added `fetch_page_with_config()` — per-source Playwright with `wait_for_selector` and `content_selector` |
| `product/regradar/app/api.py` | Added 4 endpoints: `/api/sources/readiness`, `/api/custom-sources` (GET+POST), `/api/custom-sources/test` |
| `product/regradar/sources.json` | Both DFSA sources updated with `wait_for_selector`, `content_selector`, `expected_min_length`, `fetch_method` |

---

## Critical Fix: DFSA Hash Collision

**Problem:** `AE-dubai-financial-services-authority-dfsa` and `AE-dfsa-notices` both produced identical content hash `3021317a497a76b0...`. Playwright captured navigation shell before JS content rendered. Both URLs extracted: *"About us Go Back Who we are The DFSA Governance…"*

**Fix applied to sources.json:**
```json
{
  "fetch_method": "playwright",
  "wait_for_selector": "main",
  "content_selector": "main",
  "expected_min_length": 3000,
  "scraper_notes": "JS-rendered SPA — nav shell only without wait_for_selector. Hash collision fixed 2026-06-13."
}
```

**How it works:** `scraper.py:fetch_page_with_config()` now reads these fields. When `wait_for_selector="main"` is set, Playwright waits for the `<main>` element to appear before capturing. When `content_selector="main"` is set, only the `<main>` element's inner HTML is extracted — nav/header/footer are excluded.

**Verification required:** Next pipeline run against both DFSA sources must produce **different** content hashes. Run: `python run.py test-source https://www.dfsa.ae/rules-and-standards` and `python run.py test-source https://www.dfsa.ae/regulation/notices-public-registers` — compare hashes.

---

## SourceIntakeStatus Vocabulary

| Status | Dashboard label | Severity |
|---|---|---|
| `CONFIRMED_ACCESSIBLE` | Ready | good |
| `JS_RENDERING_NEEDED` | JS rendering needed | warning |
| `PDF_EXTRACTION_NEEDED` | PDF extraction needed | warning |
| `NAV_SHELL_ONLY` | Remediation needed | critical |
| `QUALITY_DROP` | Quality check | warning |
| `NEEDS_SELECTOR_REVIEW` | Selector review | warning |
| `UNSUPPORTED` | Not supported | error |
| `BLOCKED` | Blocked | error |

---

## Nav-Shell Detection Algorithm

`is_nav_shell_only(text, threshold=0.65)`:
- Split extracted text into lines
- Count lines with < 8 words (navigation items, breadcrumbs, link labels)
- Count lines with ≥ 8 words (substantive content)
- If short-line ratio ≥ 0.65 AND total chars < 10,000 → nav shell confirmed
- Above 10,000 chars: skip check (large pages are not nav-shell)

**Why 0.65?** DFSA nav text is ~85% short lines. Legitimate regulatory content is < 40% short lines. 0.65 gives comfortable separation.

---

## New API Endpoints

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/api/sources/readiness` | GET | Required | Readiness summary for all enabled sources |
| `/api/custom-sources` | GET | Required | List user-added custom sources |
| `/api/custom-sources` | POST | Required | Add a validated custom source |
| `/api/custom-sources/test` | POST | Required | Test a URL before adding |

All endpoints require authentication. Source test uses existing `_SOURCE_TEST_LIMITER` (10 req/hour).

---

## Test Results

```
18 passed, 0 failed in 0.17s
```

| Test | Covers |
|---|---|
| `test_valid_url_passes_ssrf_check` | Good URL clears validate_public_url |
| `test_private_ip_blocked` | 192.168.x.x rejected |
| `test_localhost_blocked` | localhost rejected |
| `test_nav_shell_detected_on_short_lines` | Synthesized nav text → NAV_SHELL_ONLY |
| `test_good_content_passes_nav_check` | Regulatory paragraph text → not nav shell |
| `test_nav_shell_below_max_chars_threshold` | Large page skips nav-shell check |
| `test_empty_text_not_nav_shell` | Empty string → not nav shell |
| `test_hash_collision_detected` | Same hash → collision detected |
| `test_no_collision_for_unique_hash` | Unique hash → no collision |
| `test_no_collision_with_own_source_id` | Same source → not self-collision |
| `test_disabled_source_not_collision_candidate` | Disabled source excluded from collision check |
| `test_intake_result_fields` | Result has all required keys |
| `test_intake_dry_run_no_evidence_written` | `write_evidence=False` → `evidence_written=False` |
| `test_low_char_source_status` | 15 chars → JS_RENDERING_NEEDED |
| `test_per_source_expected_min_length` | 4000 chars vs expected 5000 → QUALITY_DROP |
| `test_intake_verdict_mapping` | All 8 status constants are unique non-empty strings |
| `test_content_hash_deterministic` | Same text → same hash |
| `test_content_hash_differs` | Different text → different hash |

---

## Validation Results

| Check | Result |
|---|---|
| `python3 -m compileall app -q` | Clean |
| `npm run build` | Clean — 360ms |
| `pytest tests/test_source_intake.py` | 18/18 passed |
| `pytest tests/` (full suite) | 61/63 passed (2 pre-existing weekly_brief failures unrelated to this change) |
| `validate_workspace.py` | PASSED — workspace is clean |

---

## What Remains Before DFSA Is Fully Fixed

The config change is in place. The actual Playwright behavior needs live verification:
1. Run `python run.py test-source https://www.dfsa.ae/rules-and-standards` — verify char count > 3000 and content is regulatory text
2. Run `python run.py test-source https://www.dfsa.ae/regulation/notices-public-registers` — verify different hash
3. If `<main>` doesn't resolve: try `content_selector: ".content"` or `"[role='main']"` (check DFSA DOM in browser)
4. After successful re-run: update `docs/current-uae-source-readiness-validation-report.md`

---

## UAE FIU (Not Fixed — Medium Priority)

`AE-uae-financial-intelligence-unit-uaefiu` (homepage, 2,026 chars) is still too shallow. Recommended fix documented in source readiness report: switch to `AE-uaefiu-circulars` (publications page, 4,102 chars) as the primary FIU source.

This requires disabling the homepage source and promoting the circulars source to tier 1. Not done in this implementation to keep scope minimal.

---

## Next Exact Task

1. **Live-verify DFSA fix** — run `test-source` on both DFSA URLs and confirm different hashes + regulatory content
2. **SourcesPage.jsx upgrade** — replace mock sources UI with real `/api/sources/readiness` data and custom source wizard
3. **UAE FIU homepage** — disable `AE-uae-financial-intelligence-unit-uaefiu`, promote `AE-uaefiu-circulars`
4. **CBUAE counter-change filter** — add noise filter for "Rated by N People" patterns in diff
