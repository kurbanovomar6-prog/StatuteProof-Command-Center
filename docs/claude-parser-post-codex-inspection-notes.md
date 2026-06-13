# Claude Post-Codex Parser Inspection Notes

**Date:** 2026-06-14
**Status:** Inspection complete. Two bugs found and fixed.

---

## Files Inspected

### Backend

| File | Exists | Notes |
|------|--------|-------|
| `app/source_intake.py` | Yes | 685 lines. Contains 2 bugs (fixed in this review). |
| `app/source_certification.py` | Yes | New. Correct implementation, no bugs. |
| `app/source_quality.py` | Yes | New. 0-100 quality scorecard with components/penalties. |
| `app/source_tester.py` | Yes | SSRF/URL safety validation. OK. |
| `app/scraper.py` | Yes | `fetch_page_with_config` with per-source selector support. OK. |
| `app/extractors.py` | Yes | Now calls `best_html_extract()` from providers. Wired correctly. |
| `app/providers/html_extraction.py` | Yes | Cascade: trafilatura→readability→selectolax→BS4. OK. |
| `app/providers/pdf_extraction.py` | Yes | Cascade: PyMuPDF→pdfplumber→pypdf. OK. |
| `app/providers/optional_tools.py` | Yes | deepdiff/htmldate/courlan with graceful fallbacks. OK. |
| `app/api.py` | Yes | `/api/custom-sources/test` returns full response with certification, quality, evidence fields. OK. |
| `app/source_runs.py` | Yes | `_write_snapshots` returns dict. `_read_runs` exists. OK. |
| `app/proof.py` | Exists | Not modified by Codex, not inspected. |
| `app/diff.py` | Exists | Not modified by Codex, not inspected. |
| `app/text_normalization.py` | Yes | `normalize_for_change_hash`, `stable_normalized_hash` exist. OK. |
| `run.py` | Yes | `source-lab` command implemented at line 1915. Full CLI. OK. |
| `sources.json` | Yes | DFSA entries have `wait_for_selector: main`, `content_selector: main`. |
| `requirements.txt` | Yes | PyMuPDF, pdfplumber added. |

### Frontend

| Component | Exists | Notes |
|-----------|--------|-------|
| `SourceLabPage.jsx` | Yes | New. Uses `result?.readiness_status` — correct (API aliases it). |
| `AppShell.jsx` | Yes | Routes `source-lab` to `SourceLabPage`. OK. |
| `AppSidebar.jsx` | Yes | Source Lab in nav with `FlaskConical` icon. OK. |
| `SourcesPage.jsx` | Yes | Uses `/api/custom-sources/test` and `/api/custom-sources`. OK. |
| `DashboardHome.jsx` | Yes | Shows "Evidence confirmed" as status pill. No overclaiming. |

### Tests

| File | Tests | Status |
|------|-------|--------|
| `tests/test_source_intake.py` | 52 | All pass |
| `tests/test_parser_benchmark_suite.py` | 21 | All pass |
| `tests/test_weekly_brief.py` | 2 failing | Pre-existing, unrelated to parser |
| `tests/fixtures/source_intake/` | 12 files | All expected fixtures present |

---

## What Exists

- **Source Certification model** with 6 statuses (TEST_PASSED, EVIDENCE_CONFIRMED, BASELINE_PENDING, MONITORING_CERTIFIED, CERTIFICATION_FAILED, NEEDS_HUMAN_REVIEW) and 4 evidence levels (PREVIEW_ONLY, BASIC_EVIDENCE, FULL_EVIDENCE, CERTIFIED_EVIDENCE). Real code, not just docs.
- **Source Quality Score** 0-100 with 10 components and 8 penalty categories. Real code with transparent scoring.
- **Provider cascade** wired into `extract_best_text()` — trafilatura → readability → selectolax → BS4 for HTML; PyMuPDF → pdfplumber → pypdf for PDF. All with graceful ImportError degradation.
- **Source Lab CLI** (`python run.py source-lab <url>`) with `--no-save`, `--save`, `--json`, `--certify`, `--providers-report`, `--content-selector`, `--wait-for-selector`, `--js`, `--pdf` flags.
- **Source Lab UI** at `/app/source-lab` — URL input, selector inputs, JS rendering toggle, quality breakdown, certification status, normalized preview, evidence level display.
- **Benchmark fixtures** — 12 HTML fixture files covering: good regulatory, nav shell, DFSA nav shell, VARA rulebook, CBUAE guidance, listing page, login page, CAPTCHA page, paywall, JS shell, legal database, short homepage.
- **API response completeness** — `/api/custom-sources/test` returns 25+ fields including quality_score, quality_breakdown, evidence_level, certification_status, certification dict, legal_policy_status, provider_used, normalized_preview.

---

## What Is Missing / Weak

1. **DFSA live Playwright verification**: Config in place but never live-tested. Playwright fails to launch in sandbox. DFSA config uses `wait_for_selector: main`, `content_selector: main`. Cannot confirm hash collision is resolved until run outside sandbox.

2. **PDF source evidence path**: PDF providers exist and are tested, but not wired into the live monitoring evidence path. PDF bytes are not fetched/extracted during source intake. The `pdf_chars` field comes from `source.get("pdf_chars", 0)` — a static config value, not a live extraction result.

3. **htmldate/courlan not installed**: These optional tools degrade gracefully but provide no actual metadata enrichment. Publication dates are not written into evidence metadata.

4. **DeepDiff not installed**: The structured diff fallback is available but the shallow comparison is used. `deepdiff==8.5.0` is in requirements.txt but not confirmed installed.

5. **Custom source save still writes to sources.json**: Not multi-tenant, not workspace-scoped. Fine for MVP, not production-ready.

6. **MONITORING_CERTIFIED is unreachable**: There are zero monitoring runs stored (data/source_runs.jsonl is empty or minimal). `build_certification_from_runs` requires 2 successful runs with proof_block_path. No built-in source currently reaches MONITORING_CERTIFIED in the readiness summary.

7. **readiness_summary() baseline_runs_required import bug risk**: At line 641-642 in source_intake.py, `build_certification_from_runs` is imported inside a loop for each enabled source. This works but is inefficient and unusual. Not a functional bug.

---

## Suspicious Overclaims in Codex Reports

None found in customer-facing copy. The Codex readiness report (8/10, 6.5/10 customer) is honest about remaining gaps. The frontend does not say "any website can be parsed" or "guaranteed compliance." Source Lab wording is honest: "A passing test is not monitoring certification."

---

## P0 Bugs Fixed in This Review

### Bug 1 — `snapshots` NameError in `_write_intake_evidence`

**Before:**
```python
_write_snapshots(...)
snapshot_base = (.../ str(snapshots["snapshot_metadata_path"])).parent  # NameError
```

**After:**
```python
snapshots = _write_snapshots(...)
snapshot_base = (... / str(snapshots["snapshot_metadata_path"])).parent
```

This crashed `write_evidence=True` in every case.

### Bug 2 — `extracted` possibly unbound

**Before:**
```python
try:
    extracted = extract_best_text(...)  # might raise
    ...
except:
    text = ""
# later:
if isinstance(extracted, dict):  # NameError if above raised
```

**After:**
```python
extracted: dict = {}  # safe default before try
try:
    extracted = extract_best_text(...)
```

---

## Immediate Risk Rating

| Item | Risk |
|------|------|
| `snapshots` NameError (fixed) | Was HIGH — now fixed |
| `extracted` unbound (fixed) | Was MEDIUM — now fixed |
| DFSA not live-verified | HIGH — config in place, untested |
| test_weekly_brief failures | LOW — pre-existing, unrelated |
| PDF evidence path incomplete | MEDIUM — functional limitation |
| MONITORING_CERTIFIED unreachable | LOW — by design, needs baseline runs |
