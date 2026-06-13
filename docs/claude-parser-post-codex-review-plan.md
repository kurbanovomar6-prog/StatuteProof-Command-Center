# Claude Post-Codex Parser Review Plan

**Date:** 2026-06-14
**Reviewer:** Claude (post-Codex independent audit)
**Scope:** StatuteProof product/regradar parser, certification, quality, UI, CLI, tests

---

## 1. Codex Reports Found

| File | Present | Summary |
|------|---------|---------|
| `docs/parser-10-10-readiness-report.md` | Yes | Claims 8/10 internal, 6.5/10 customer-facing. Lists what was built. |
| `docs/parser-code-vs-repositories-final-report.md` | Yes | Supersedes v2 hardening. Claims provider cascade wired, API complete, 52 tests pass. |
| `docs/parser-provider-matrix.md` | Yes | Provider matrix doc. |
| `docs/live-source-verification-runbook.md` | Yes | DFSA verification runbook. |
| `docs/multi-provider-parser-dependency-plan.md` | Yes | Dependency plan. |
| `docs/universal-source-intake-v2-hardening-report.md` | Yes | V2 report (now marked superseded). |
| `docs/parser-10-10-realistic-roadmap.md` | Yes | Realistic roadmap to 10/10. |

---

## 2. Claimed Work Completed (from Codex reports)

- `app/source_quality.py` — transparent 0-100 quality scorecard ✓
- `app/source_certification.py` — certification model with 6 statuses + 4 evidence levels ✓
- `run.py source-lab` — CLI for one-URL source lab ✓
- `web/src/components/app/SourceLabPage.jsx` — Source Lab UI ✓
- `app/extractors.py` updated to call `best_html_extract()` from provider layer ✓
- `app/source_intake.py` updated with quality, certification, evidence fields ✓
- `app/providers/html_extraction.py` wired into extractors ✓
- Benchmark fixture files (12) in `tests/fixtures/source_intake/` ✓
- `tests/test_parser_benchmark_suite.py` — 21 benchmark tests ✓
- API `/api/custom-sources/test` returns full response with certification, quality ✓

---

## 3. Files Verified

- `app/source_intake.py` — inspected, has 2 real bugs
- `app/source_quality.py` — correct, no bugs found
- `app/source_certification.py` — correct, no bugs found
- `app/extractors.py` — provider cascade wired correctly
- `app/providers/html_extraction.py` — OK
- `app/providers/pdf_extraction.py` — OK
- `app/providers/optional_tools.py` — OK
- `app/api.py` — handler returns complete response, routes correctly
- `run.py` — source-lab command implemented
- `web/.../SourceLabPage.jsx` — uses `readiness_status` correctly (API aliases it)
- `web/.../AppShell.jsx` + `AppSidebar.jsx` — Source Lab route wired
- `tests/fixtures/source_intake/` — 12 fixture files exist
- `tests/test_parser_benchmark_suite.py` — 21 tests, all passing

---

## 4. Bugs Found

### Bug 1 — Critical: `snapshots` NameError in `_write_intake_evidence`

**File:** `product/regradar/app/source_intake.py`
**Line:** ~465

```python
# WRONG — return value not captured:
_write_snapshots(...)
snapshot_base = (Path(...) / str(snapshots["snapshot_metadata_path"])).parent
```

`snapshots` is never defined. `_write_snapshots()` return value is discarded. This crashes with `NameError` whenever `write_evidence=True`.

**Fix:** `snapshots = _write_snapshots(...)`

### Bug 2 — Medium: `extracted` possibly unbound

**File:** `product/regradar/app/source_intake.py`
**Line:** ~306

If `extract_best_text(...)` raises, `extracted` is never assigned, but line 306 does `if isinstance(extracted, dict):` which raises `NameError`.

**Fix:** Set `extracted: dict = {}` before the try block.

---

## 5. What Will Not Be Touched

- `sources.json` — no structure changes
- Evidence paths or run record schema
- Pricing, billing, auth, Telegram, or any non-parser code
- Live monitoring runs or `run.py all`
- Cloudflare, DigitalOcean, VPS deployment
- Customer-facing copy that is already legally safe

---

## 6. Validation Commands

After fixes:
```bash
python3 -m compileall product/regradar/app -q
python3 -m pytest product/regradar/tests/test_parser_benchmark_suite.py product/regradar/tests/test_source_intake.py -q
npm run build (in product/regradar/web/)
python3 tools/validate_workspace.py
```

---

## 7. Risk List

| Risk | Severity | Notes |
|------|----------|-------|
| `snapshots` NameError on write_evidence=True | High | Crashes save path |
| `extracted` NameError on extractor exception | Medium | Unlikely in practice but real |
| DFSA Playwright still unverified | High | Config present, live test not run |
| Benchmark tests mock write path | Low | Mock bypasses Bug 1 |
| test_weekly_brief.py 2 failures | Low | Pre-existing, unrelated |

---

## 8. Criteria for "Done"

- Bug 1 fixed: `snapshots = _write_snapshots(...)` 
- Bug 2 fixed: `extracted: dict = {}` before try
- All benchmark tests pass: 21/21
- All source intake tests pass: 48/48
- Frontend build clean
- Workspace validation clean
- Final review report written
- Commit pushed
