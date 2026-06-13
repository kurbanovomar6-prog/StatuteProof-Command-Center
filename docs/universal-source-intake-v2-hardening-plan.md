# Universal Source Intake V2 — Hardening Plan

**Date:** 2026-06-13  
**Based on:** docs/universal-source-intake-verification-report.md (score 6/10)  
**Scope:** Harden custom source UI, API response fields, provider wrappers, tests, readiness wording

---

## 1. Verification Score and Exact Failures

**Score:** 6/10

| Failure | Severity | Root cause |
|---|---|---|
| Frontend still POSTs to `/api/source-test` not `/api/custom-sources/test` | CRITICAL | SourcesPage.jsx `handleTest()` not updated |
| Frontend saves custom sources to localStorage not backend | HIGH | `handleSaveSource()` uses `persistCustomSource()` only |
| No legal confirmation checkbox on activation | HIGH | No gate before save |
| `can_activate=false` sources: save button still visible | HIGH | UI doesn't check `can_activate` |
| API response missing `extraction_method`, `content_hash`, `evidence_written`, `proof_path` | MEDIUM | Handler omits fields that exist in result dict |
| No `selectolax`, PyMuPDF (available), pdfplumber (available) providers wired | MEDIUM | extractors.py doesn't use installed PyMuPDF/pdfplumber |
| Readiness wording says 13 sources when 3 are unconfirmed | LOW | Dashboard text not updated |
| Tests cover 26 cases but not all 24 required new cases | LOW | Gap in test matrix |
| DFSA live extraction unverified | INFO | Playwright sandbox limitation — not a code bug |

---

## 2. What Must Be Fixed Now

### Priority 1 — Frontend (CRITICAL)
- `handleTest()`: change fetch target to `/api/custom-sources/test`
- Map new response fields: `status`, `status_label`, `can_activate`, `failure_reason`, `remediation_hint`, `quality`, `nav_shell_detected`, `hash_collision`, `chars`, `extraction_method`
- Activation button: disabled unless `can_activate === true` AND legal confirmation checkbox checked
- `handleSaveSource()`: POST to `/api/custom-sources` (keep localStorage as fallback for dev mode)
- Remove "Confirmed accessible with evidence records" — use "Test passed — save required for evidence record"
- Show `failure_reason` + `remediation_hint` prominently in result panel

### Priority 2 — API response completeness
- Add `extraction_method`, `content_hash` (first 12 chars), `evidence_written`, `evidence_required`, `proof_path` to `/api/custom-sources/test` response

### Priority 3 — Provider wrappers
- `app/providers/html_extraction.py`: selectolax (optional), trafilatura, readability, BS4 wrappers
- `app/providers/pdf_extraction.py`: PyMuPDF (available), pdfplumber (available), pypdf wrappers
- `app/providers/optional_tools.py`: deepdiff, htmldate, courlan — all gracefully degraded
- Keep existing `extractors.py` unchanged; providers are additive

### Priority 4 — Requirements
- Add `PyMuPDF`, `pdfplumber` as optional (already installed, just not in requirements)
- Note selectolax, htmldate, courlan, deepdiff as optional installs

### Priority 5 — Tests
- Add tests: credentials URL blocked, legal confirmation required, can_activate=false blocks save, FAILED never UNCHANGED, QUALITY_DROP not confirmed, DeepDiff fallback, htmldate fallback, courlan fallback, provider info in result, PDF detection

### Priority 6 — Readiness wording honesty
- Update dashboard or readiness summary text to say honest numbers

---

## 3. What Should NOT Be Touched

- `app/scraper.py` — working, no changes needed
- `app/extractors.py` — working multi-strategy extraction, keep as-is
- `app/source_tester.py` — working, no changes
- `app/pipeline.py` — production pipeline, do not touch
- Evidence pipeline (source_runs.py, proof.py, diff.py) — do not touch
- `.env`, any secrets
- Telegram/email delivery
- Live monitoring pipeline

---

## 4. Files to Edit

| File | Change |
|---|---|
| `web/src/components/app/SourcesPage.jsx` | Rewrite handleTest + handleSaveSource + result panel |
| `app/api.py` | Add fields to `/api/custom-sources/test` response |
| `app/providers/html_extraction.py` | New — optional provider wrappers |
| `app/providers/pdf_extraction.py` | New — PyMuPDF + pdfplumber wrappers |
| `app/providers/optional_tools.py` | New — deepdiff/htmldate/courlan wrappers |
| `requirements.txt` | Add PyMuPDF, pdfplumber as optional noted deps |
| `tests/test_source_intake.py` | Expand to 30+ tests |
| `docs/multi-provider-parser-dependency-plan.md` | New — provider matrix |
| `docs/universal-source-intake-v2-hardening-report.md` | Final report |

---

## 5. Validation Commands

```bash
cd product/regradar
python3 -m compileall app -q
python3 -m pytest tests/test_source_intake.py -v
python3 -m pytest tests/ -q
cd web && npm run build
python3 tools/validate_workspace.py  # from workspace root
```

---

## 6. Rollback Plan

All changes are additive:
- Frontend: change two functions, add fields to display. Can revert individual functions.
- API: add fields to response. No logic change, only additions.
- Provider wrappers: new files. Remove directory if needed.
- requirements.txt: add optional deps with `# optional:` comment. Remove if needed.
- Tests: new test file additions. Remove if needed.
- No DB schema changes.
- No existing function signatures changed.
- No source_intake.py logic changed (already hardened by verification pass).
