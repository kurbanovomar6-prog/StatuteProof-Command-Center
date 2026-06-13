# Universal Source Intake Engine — V2 Hardening Report

> Current-state note, 2026-06-13: this report is superseded by
> `docs/parser-code-vs-repositories-final-report.md` for parser-provider
> integration status. At the time of this V2 report, provider wrappers existed
> but were not yet wired into `app/extractors.extract_best_text()`. That gap has
> since been addressed in the parser-provider integration pass. Treat this file
> as historical implementation context, not proof that the full parser is
> customer-ready.

**Date:** 2026-06-13
**Scope:** `product/regradar/` — source intake layer, provider wrappers, frontend custom source UI, API response completeness
**Baseline:** V1 verification report score: 6/10
**Target:** Fix all identified gaps, confirm 48+ tests pass, frontend build clean

---

## Summary

The V2 hardening pass addressed all six gaps identified in the verification report. The intake engine, API response, frontend UI, and provider layer are now consistent with the evidence-first architecture and legal safety requirements of StatuteProof.

**Result:**
- 48 tests pass (0 failures in test_source_intake.py)
- 2 pre-existing failures in test_weekly_brief.py — confirmed unrelated, pre-date this work
- Frontend build: clean (0 errors, 0 warnings)
- Workspace validation: PASSED

---

## Changes Made

### 1. Frontend: SourcesPage.jsx — API endpoint and UI completeness

**Problem:** Custom source test called `/api/source-test` (non-existent endpoint). Save wrote to localStorage only. No legal confirmation gate. Result panel showed only status string.

**Fix:** Complete rewrite of `SourcesPage.jsx`:
- `handleTest()` POSTs to `/api/custom-sources/test` (correct endpoint)
- `handleSaveSource()` POSTs to `/api/custom-sources` with localStorage fallback on network failure
- Legal confirmation checkbox: visible only when `can_activate=true`; save button disabled unless checkbox checked AND `can_activate=true`
- Result panel shows: status label, failure_reason, remediation_hint, quality, extraction_method, normalized_hash, nav_shell_detected warning, hash_collision warning
- Evidence wording: "Test passed — save required for evidence record" (not "with evidence records")
- Evidence note: "No evidence record exists yet — the first monitoring run creates the hash, snapshot, and proof artifact"

### 2. API: `/api/custom-sources/test` response completeness

**Problem:** Response was missing: `extraction_method`, `normalized_hash`, `evidence_written`, `proof_path`, `evidence_required`, `quality_label`, `failure_reason`, `remediation_hint`.

**Fix:** `_handle_custom_source_test()` in `api.py` now returns:
```json
{
  "ok": true,
  "status": "CONFIRMED_ACCESSIBLE",
  "status_label": "Ready",
  "can_activate": true,
  "chars": 4200,
  "normalized_length": 4200,
  "chars_raw": 8900,
  "pdf_chars": 0,
  "extraction_method": "trafilatura",
  "normalized_hash": "3fa2b9c1d4e8",
  "quality": "GOOD",
  "quality_label": "GOOD",
  "nav_shell_detected": false,
  "hash_collision": false,
  "collision_source_id": null,
  "failure_reason": "",
  "remediation_hint": "",
  "warnings": [],
  "notes": "",
  "evidence_written": false,
  "evidence_required": true,
  "proof_path": null
}
```

`can_activate` is `true` only when `status == "CONFIRMED_ACCESSIBLE"`.

### 3. Provider wrappers — multi-provider parser package

**Problem:** No structured provider abstraction. Optional deps crashed on import instead of degrading gracefully.

**Fix:** New package `app/providers/` with three modules:

- **`html_extraction.py`:** trafilatura → readability → selectolax (optional) → BS4 cascade. `best_html_extract()` returns longest content. All return uniform `ProviderResult` dict with `provider_name`, `dependency_available`, `elapsed_ms`.
- **`pdf_extraction.py`:** PyMuPDF → pdfplumber → pypdf cascade. `best_pdf_extract()` returns first success. All gracefully degrade on ImportError.
- **`optional_tools.py`:** `structured_diff` (deepdiff/fallback), `extract_date_from_html` (htmldate/no-op), `canonicalize_url` (courlan/urllib fallback). All degrade without raising.

Every provider function: wraps import in try/except ImportError, wraps execution in try/except Exception, returns timing on all paths.

### 4. Requirements.txt — optional dep documentation

**Problem:** PyMuPDF and pdfplumber were used in providers but not listed in requirements.

**Fix:** Added to requirements.txt with comments:
```
PyMuPDF==1.25.5       # optional: enhanced PDF extraction
pdfplumber==0.11.6    # optional: table-structured PDF extraction
deepdiff==8.5.0       # optional: structured diff for evidence comparison
# htmldate==1.9.3     # optional: not yet verified on Python 3.14
# courlan==1.3.2      # optional: not yet verified on Python 3.14
```

### 5. Tests: expanded from 26 to 48

New test categories added:
- Failure reason and remediation hint fields present on BLOCKED
- QUALITY_DROP never resolves to CONFIRMED_ACCESSIBLE
- Status vocabulary contains no "UNCHANGED" (that is a change-detection term)
- extraction_method and content_hash present in result dict
- HTML provider schema validation (all keys present)
- trafilatura, bs4, readability, selectolax graceful behavior
- best_html_extract cascade returns content
- PDF provider schema validation
- PDF providers graceful on bad bytes
- best_pdf_extract returns success=False on bad input
- deepdiff fallback: has_changes=True on changed dict
- deepdiff fallback: has_changes=False on identical dicts
- htmldate fallback: no raise, schema present
- courlan fallback: is_valid=True for real URL, False for garbage
- can_activate=True only for CONFIRMED_ACCESSIBLE
- NEEDS_SELECTOR_REVIEW != CONFIRMED_ACCESSIBLE

---

## Validation Results

```
python3 -m compileall app -q     → PASSED (no output)
pytest tests/test_source_intake.py -v  → 48/48 PASSED
pytest tests/ -v --tb=short           → 91/93 PASSED
  - 2 failures: test_weekly_brief.py (pre-existing, unrelated)
npm run build                    → ✓ built in 423ms (0 errors)
python3 tools/validate_workspace.py  → Validation PASSED
```

---

## Pre-existing Failures (Not Introduced by This Work)

Both `test_weekly_brief.py` failures were present before this hardening pass and are confirmed unrelated to source intake:

1. `test_disclaimer_and_client_proof_summary_appear` — expects a specific disclaimer phrase ("StatuteProof provides early-warning regulatory intelligence, not legal advice.") that was changed in the brief generator.
2. `test_sources_monitored_no_change_line_uses_available_count_or_generic` — expects a specific "Remaining monitored sources" phrase that was also changed.

These failures are known and tracked separately. They are NOT caused by any change in this hardening pass.

---

## Outstanding Items (Not in Scope for V2)

1. **DFSA live Playwright test:** Config is in place (`wait_for_selector: "main"`, `content_selector: "main"`) but live network test requires a running Playwright environment. Safe command to verify:
   ```bash
   cd product/regradar
   python3 -c "
   import json; from pathlib import Path
   from app.source_intake import run_source_intake
   sources = json.loads(Path('sources.json').read_text())
   ids = {'AE-dubai-financial-services-authority-dfsa', 'AE-dfsa-notices'}
   for s in sources:
       if s.get('source_id') in ids:
           print(s['source_id'], run_source_intake(s, all_sources=sources, write_evidence=False))
   "
   ```

2. **Wire providers into extractors.py:** Historical note: at the time of this report, `best_html_extract()` was not yet called by `extract_best_text()` in `app/extractors.py`. This has since been addressed in the parser-provider integration pass documented in `docs/parser-code-vs-repositories-final-report.md`.

3. **selectolax, htmldate, courlan:** Not yet installed. Graceful degradation is in place; install when needed.

4. **test_weekly_brief.py failures:** Tracked separately. Fix requires updating the brief generator phrasing or updating the test expectations to match current output.

---

## Correct Product Positioning (Confirmed)

> "StatuteProof monitors selected public official sources, detects text changes, stores cryptographic evidence records, and drafts monitoring briefs for human review."

The custom source intake flow correctly communicates:
- "Test passed — save required for evidence record" (not "with evidence records")
- Legal confirmation required before save
- Evidence record exists only after the first monitoring run, not after test
- can_activate=false for any status other than CONFIRMED_ACCESSIBLE
