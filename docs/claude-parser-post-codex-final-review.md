# Claude Post-Codex Parser Review

**Date:** 2026-06-14
**Reviewer:** Claude (independent post-Codex audit)

---

## 1. Executive Verdict

- **Current score: 8.5/10** for internal demo (up from Codex's reported 8/10 — bugs fixed).
- **Demo safe: yes**, with honest wording.
- **Customer safe: no** — not yet for self-serve active monitoring without supervised pilot.
- **Biggest blocker:** DFSA Playwright extraction unverified. No source reaches MONITORING_CERTIFIED without repeat baseline runs. PDF evidence path incomplete.
- **Two bugs found and fixed** by this review: `snapshots` NameError on `write_evidence=True` and `extracted` potentially unbound.

---

## 2. Codex Claims Verified

| Claim | Verified | Evidence | Fix |
|-------|----------|----------|-----|
| `source_quality.py` — 0-100 quality scorecard | Yes | File exists, 146 lines, correct scoring model, 10 components, 8 penalties. |  |
| `source_certification.py` — 6 statuses, 4 evidence levels | Yes | File exists, 205 lines. Correct logic for TEST_PASSED, BASELINE_PENDING, MONITORING_CERTIFIED. |  |
| `run.py source-lab` CLI | Yes | Lines 1915-1996 in run.py. Flags: `--no-save`, `--save`, `--json`, `--certify`, `--providers-report`, `--content-selector`, `--wait-for-selector`, `--js`, `--pdf`. |  |
| `SourceLabPage.jsx` Source Lab UI | Yes | New component, 195 lines. Wired in AppShell.jsx and AppSidebar.jsx. |  |
| Provider cascade wired into extractors.py | Yes | Lines 334-381 in extractors.py call `best_html_extract()` from providers. Legacy fallback retained. |  |
| source_intake.py exposes quality/cert/evidence fields | Yes | All fields present in result dict. |  |
| Benchmark fixtures (12 HTML files) | Yes | `tests/fixtures/source_intake/` — 12 files confirmed. |  |
| `test_parser_benchmark_suite.py` — 21 tests | Yes | 21/21 pass. |  |
| API returns full test response | Yes | 25+ fields at `/api/custom-sources/test`. |  |
| `snapshots` NameError | **Not caught by Codex** | Bug in `_write_intake_evidence`. Crashes `write_evidence=True`. | Fixed: `snapshots = _write_snapshots(...)` |
| `extracted` unbound risk | **Not caught by Codex** | `extracted: dict = {}` missing before try block. | Fixed. |
| 52 source_intake tests pass | Yes | 52/52 pass after fixes. |  |
| Frontend build clean | Yes | `npm run build` → built in 341ms. |  |
| "73 passed" parser + benchmark combined | Yes | 52 + 21 = 73. Confirmed. |  |

---

## 3. Source Certification Review

**Statuses implemented:**
- `TEST_PASSED` — one no-save test passed. Score ≤70.
- `EVIDENCE_CONFIRMED` — not auto-generated; would appear after evidence write with higher score.
- `BASELINE_PENDING` — ≥1 successful run but fewer than `baseline_runs_required` (default 2).
- `MONITORING_CERTIFIED` — ≥2 successful runs with proof_block_path and normalized_hash.
- `CERTIFICATION_FAILED` — fetch/quality/collision/policy gate failed. Score ≤39.
- `NEEDS_HUMAN_REVIEW` — NEEDS_SELECTOR_REVIEW status. Score ≤50.

**Evidence requirements correctly enforced:**
- No-save test → `PREVIEW_ONLY`, `TEST_PASSED`, `evidence_written=False`. Cannot claim evidence records.
- Save mode → `BASIC_EVIDENCE` if raw+normalized+proof+hash exist, `FULL_EVIDENCE` if metadata also present.
- MONITORING_CERTIFIED requires `baseline_runs_completed >= baseline_runs_required`.

**Gap:** No built-in source currently reaches `MONITORING_CERTIFIED` because `data/source_runs.jsonl` has insufficient baseline history. This is expected and honest.

---

## 4. Quality Score Review

**Model:** 0–100 composite score from `build_quality_score()`.

**Components (max 100 points):**
| Component | Max |
|-----------|-----|
| url_safety | 10 |
| fetch_success | 10 |
| extraction_length | 10 |
| paragraph_heading_structure | 10 |
| regulatory_content_density | 10 |
| nav_shell_risk_low | 15 |
| hash_uniqueness | 10 |
| metadata_extraction | 5 |
| provider_confidence | 10 |
| evidence_completeness | 10 |

**Penalties:**
| Penalty | Amount |
|---------|--------|
| nav_shell | -50 |
| hash_collision | -40 |
| selector_timeout | -30 |
| shallow_content (0-500 chars) | -25 |
| pdf_text_too_shallow | -30 |
| no_proof | -25 |
| missing_official_or_canonical_url | -10 |
| source_policy_warning | -20 |

**Labels:** EXCELLENT (90+), GOOD (75+), ACCEPTABLE (60+), LIMITED (40+), POOR (below 40).

**Assessment:** Score is transparent, computable, and affects certification. CONFIRMED_ACCESSIBLE sources with no proof file score 25 lower than those with evidence. This is correct product behavior.

---

## 5. Provider Matrix Review

**Active providers (installed):**
- Playwright — fetch layer for JS-rendered sites. Not verified live outside sandbox.
- trafilatura — primary HTML extractor. Installed, tested.
- readability-lxml — HTML fallback. Installed, tested.
- BeautifulSoup4 — required final fallback. Always available.
- PyMuPDF — primary PDF extractor. Installed, tested.
- pdfplumber — PDF table fallback. Installed, tested.
- pypdf — PDF text fallback. Installed, tested.

**Optional providers (not installed — graceful degradation confirmed):**
- selectolax — CSS selector extraction. ImportError handled.
- deepdiff — structured diff. ImportError handled, shallow fallback used.
- htmldate — date extraction. ImportError handled, returns empty.
- courlan — URL canonicalization. ImportError handled, urllib fallback.

**Future/research (not installed, not blocking):**
- Crawl4AI — opt-in flag required, correctly not used unless `ENABLE_CRAWL4AI_EXTRACTOR=true`.
- Browsertrix Crawler, Crawlee, Scrapy, Firecrawl — documented as rejected or future only.

**Provider cascade order verified:**
HTML: selectolax (if content_selector) → trafilatura → readability → BS4
PDF: PyMuPDF → pdfplumber → pypdf
Every ImportError → graceful degradation, not crash.

---

## 6. Evidence Levels Review

| Level | Triggers When | Correct |
|-------|--------------|---------|
| PREVIEW_ONLY | No-save test or extraction-only | Yes. No evidence record claimed. |
| BASIC_EVIDENCE | raw+normalized+proof+hash paths exist | Yes. write_evidence=True required. |
| FULL_EVIDENCE | basic + metadata path | Yes. |
| CERTIFIED_EVIDENCE | full + baseline_complete | Yes. Requires ≥2 successful runs. |

**UI correctness:**
- SourceLabPage.jsx shows `evidence_level` in metric grid.
- Wording: "Test passed — save evidence to confirm source. This is not monitoring certification." — correct.
- No-save test never shows "with evidence records" — verified in API response (`evidence_written: false`).

---

## 7. CLI Review

**Available command:** `python run.py source-lab <url> [options]`

| Flag | Implemented |
|------|-------------|
| `--no-save` | Yes (default) |
| `--save` | Yes |
| `--json` | Yes |
| `--certify` | Yes (`--baseline-runs N`) |
| `--providers-report` | Yes |
| `--content-selector` | Yes |
| `--wait-for-selector` | Yes |
| `--js` | Yes |
| `--pdf` | Yes |

**Output fields:** readiness_status, certification_status, evidence_level, quality_score, provider_used, normalized_length, normalized_hash, failure_reason, remediation_hint.

**Smoke check confirmed by Codex:** `python3 run.py source-lab http://localhost:1234 --no-save --json` blocks localhost and returns CERTIFICATION_FAILED, PREVIEW_ONLY, BLOCKED. Not re-run in this review to avoid sandbox Playwright issues.

---

## 8. Source Lab UI Review

**User flow:**
1. Paste URL — input field present.
2. Optional content selector, wait selector — fields present.
3. Optional Playwright rendering — checkbox present.
4. Run test — POSTs to `/api/custom-sources/test`.
5. Shows: readiness status icon, failure reason, remediation hint, quality score, evidence level, provider, normalized chars, hash (12 chars), legal policy status, normalized preview, certification status + score, baseline progress, quality breakdown components and penalties.

**Activation rules:** Save and legal confirmation are in SourcesPage.jsx, not SourceLabPage. SourceLab is read-only (test only). Correct separation.

**Wording check:**
- "Test passed — save evidence to confirm source. This is not monitoring certification." ✓
- "Evidence and baseline runs are required before active monitoring can be certified." ✓
- No "validated", "certified", or "with evidence records" on test-only flow. ✓

---

## 9. Built-in Source Honesty

**Source count:** comes from `sources.json` `enabled` field — correct.
**Evidence count:** `readiness_summary()` returns `evidence_confirmed` count based on actual run records.
**Certification count:** `monitoring_certified` count — currently 0 (no baseline history exists).

**DashboardHome wording:**
- "Mapped does not mean certified." — line 164. ✓
- "Monitoring certification requires evidence and baseline runs." — line 178. ✓
- No "13 validated sources" claim found. ✓

**Readiness page:** Shows `evidence_confirmed`, `monitoring_certified`, `baseline_pending`, `blocked` as separate counts from `readiness_summary()`. Separation is honest.

---

## 10. Tests and Validation

```
python3 -m compileall app -q           → PASSED (no output)
pytest test_parser_benchmark_suite.py  → 21/21 PASSED
pytest test_source_intake.py           → 52/52 PASSED
pytest tests/                          → 116 passed, 2 failed
  Failures: test_weekly_brief.py (pre-existing, unrelated to parser)
npm run build                          → ✓ built in 341ms
python3 tools/validate_workspace.py    → Validation PASSED
python3 tools/validate_codex_skills.py → Codex skills validation PASSED
```

---

## 11. Remaining Limitations (Brutally Honest)

1. **DFSA Playwright not live-verified.** Config (`wait_for_selector: main`) is in sources.json but has never been confirmed to extract meaningful non-nav-shell content. The DFSA hash collision fix is code-only; it cannot be verified without a live Playwright session.

2. **No built-in source reaches MONITORING_CERTIFIED.** The readiness summary will show 0 monitoring-certified sources because there are not 2+ successful evidence runs with proof_block_path and normalized_hash per source. This is honest but means the product cannot currently claim "certified monitoring" for any source.

3. **PDF extraction not in live evidence pipeline.** `best_pdf_extract()` works and is tested, but source intake does not fetch and extract PDF bytes during monitoring runs. `pdf_chars` is read from static source config, not from a live PDF fetch. PDF certification path is not implemented.

4. **Custom source save is global.** Saved custom sources go into `sources.json` — not workspace-scoped or user-scoped. Multi-user use would cause conflicts.

5. **test_weekly_brief.py failures pre-exist.** The weekly brief generator's wording changed but the tests were not updated. Not a parser bug but visible in the full suite.

6. **Frontend lint is not clean.** `npm run lint` fails on pre-existing issues in non-parser files (App.jsx, DiffViewer.jsx, etc.). Parser-critical files are clean.

7. **MONITORING_CERTIFIED is unreachable today without repeat monitoring runs.** The baseline_runs_required default is 2. No source has 2 successful runs with proofs. This is correct, not a bug, but it means the certification pipeline is structurally valid but not yet exercised end-to-end.

---

## 12. What We Can Claim

Safe claims (verified honest):

- "StatuteProof tests public sources for technical accessibility and extraction quality."
- "Custom sources are saved for validation; monitoring does not activate automatically."
- "A no-save source test is a readiness preview — it does not create an evidence record."
- "Evidence records are created by monitoring runs, not by the preview test."
- "Source quality scores are transparent: components, penalties, and labels are shown."
- "Sources with login, CAPTCHA, paywall, or private-portal detection are blocked, not monitored."
- "Provider cascade uses trafilatura, readability, and BeautifulSoup — the best result is selected."
- "Active monitoring certification requires evidence records and baseline runs."
- "StatuteProof shows failure reasons and remediation hints for every blocked source."
- "StatuteProof does not guarantee compliance, prevent fines, or certify regulatory coverage."

---

## 13. What We Cannot Claim

Do not say:

- "Any website can be parsed."
- "DFSA extraction is fixed and verified." (config is in place; live run has not been confirmed)
- "13 sources are validated." (none are MONITORING_CERTIFIED today)
- "Confirmed accessible with evidence records" after a no-save test.
- "One successful test means certified monitoring."
- "Full parser validation is completely clean." (2 weekly-brief failures, lint issues remain)
- "PDF sources are fully supported." (PDF provider exists; live PDF evidence path not implemented)
- "Customer data is isolated." (custom sources go into shared sources.json)

---

## 14. Next Exact Task

Run the two DFSA source lab checks outside the sandbox where Playwright can launch (`python3 run.py source-lab https://www.dfsa.ae --js --wait-for-selector main --content-selector main --no-save --json`), verify normalized content is not nav-shell, and update DFSA source certification status only if hash is unique and meaningful content is confirmed.

---

## Bugs Fixed in This Review

| Bug | File | Line | Fix |
|-----|------|------|-----|
| `snapshots` NameError in `_write_intake_evidence` | `app/source_intake.py` | ~465 | `snapshots = _write_snapshots(...)` |
| `extracted` possibly unbound | `app/source_intake.py` | ~264 | `extracted: dict = {}` before try |
