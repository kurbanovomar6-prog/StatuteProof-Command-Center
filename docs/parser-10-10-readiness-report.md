# Parser 10/10 Readiness Report

## 1. Executive Verdict

- Current score: 8/10 for internal demo, 6.5/10 for customer-facing use.
- What score means: the system now has real parser quality gates, certification states, evidence levels, Source Lab CLI/UI, and benchmark tests. It still lacks live DFSA verification and repeat baseline history.
- Demo safe: yes, with honest wording.
- Customer safe: not yet for self-serve active monitoring.

## 2. What Was Built

- `app/source_quality.py`: transparent 0-100 source quality scorecard.
- `app/source_certification.py`: source certification model and evidence levels.
- `run.py source-lab`: one-URL source lab CLI.
- `web/src/components/app/SourceLabPage.jsx`: Source Lab UI.
- Dashboard copy updated from validation wording to certification/evidence wording.
- Source intake now exposes quality score, quality breakdown, evidence level, certification status, provider candidates, normalized preview, and proof/evidence paths.
- Saved source intake uses the existing append-only source run/proof path instead of inventing fake evidence.
- Benchmark fixtures and `test_parser_benchmark_suite.py`.
- Provider matrix and live-source verification runbook.

## 3. Source Certification Model

Statuses:

- `TEST_PASSED`: one no-save test passed, no evidence claim.
- `EVIDENCE_CONFIRMED`: evidence exists, but baseline may not be complete.
- `BASELINE_PENDING`: first proof run exists; repeat baseline still required.
- `MONITORING_CERTIFIED`: baseline requirement met.
- `CERTIFICATION_FAILED`: fetch, quality, collision, policy, or evidence gate failed.
- `NEEDS_HUMAN_REVIEW`: selector/source ambiguity remains.

One test cannot create monitoring certification.

## 4. Provider Matrix

Documented in `docs/parser-provider-matrix.md`.

Active/fallback:

- Playwright, trafilatura, readability-lxml, selectolax, BeautifulSoup, PyMuPDF, pdfplumber, pypdf, htmldate, courlan, DeepDiff.

Optional/future:

- Resiliparse, jusText, extruct, warcio, Browsertrix, Crawlee, Crawl4AI, Scrapy, OpenTimestamps.

Rejected for core runtime:

- Firecrawl, crw, browser-use.

## 5. Evidence Levels

- `PREVIEW_ONLY`: no-save test; no evidence record claim.
- `BASIC_EVIDENCE`: raw/normalized/proof/hash artifacts exist.
- `FULL_EVIDENCE`: basic evidence plus metadata/provider/quality/certification reports.
- `CERTIFIED_EVIDENCE`: full evidence plus baseline certification.

Only `BASIC_EVIDENCE` or above can support “with evidence records.”

## 6. Quality Score

Score components:

- URL safety, fetch success, extraction length, paragraph/heading structure, regulatory density, nav-shell risk, hash uniqueness, metadata, provider confidence, evidence completeness.

Penalties:

- nav shell, hash collision, selector timeout, shallow content, shallow PDF, no proof, missing official/canonical URL, policy warning.

Labels:

- `EXCELLENT`, `GOOD`, `ACCEPTABLE`, `LIMITED`, `POOR`.

## 7. UI Source Lab

Source Lab flow:

1. Paste one URL.
2. Optional content selector and wait selector.
3. Optional Playwright rendering.
4. Run one source test.
5. Display readiness, quality score, evidence level, provider, normalized preview, certification state, components, penalties, failure reason, and remediation hint.

Safe copy:

- “Test passed - save evidence to confirm source.”
- “Evidence and baseline runs are required before active monitoring can be certified.”

## 8. CLI

Added:

```bash
python run.py source-lab <URL> --no-save --json
python run.py source-lab <URL> --save --json
python run.py source-lab <URL> --certify --baseline-runs 2
python run.py source-lab <URL> --providers-report
python run.py source-lab <URL> --content-selector "main"
python run.py source-lab <URL> --wait-for-selector "main"
python run.py source-lab <URL> --js
python run.py source-lab <URL> --pdf
```

Smoke check:

- `python3 product/regradar/run.py source-lab http://localhost:1234 --no-save --json` blocks localhost and returns `CERTIFICATION_FAILED`, `PREVIEW_ONLY`, and `BLOCKED`.

## 9. Tests

Passed:

- `python3 -m compileall product/regradar/app product/regradar/run.py -q`
- `python3 -m pytest product/regradar/tests/test_parser_benchmark_suite.py product/regradar/tests/test_source_intake.py -q` -> 73 passed.
- `npm run build` -> passed.
- `python3 tools/validate_workspace.py` -> passed.
- `python3 tools/validate_codex_skills.py` -> passed.

Known failures:

- Full backend suite: 116 passed, 2 failed in `test_weekly_brief.py`; both are existing weekly-brief wording expectation failures.
- Frontend lint: fails with existing unrelated lint errors in `App.jsx`, `DiffViewer.jsx`, `EvidenceCard.jsx`, `Pricing.jsx`, `PricingPage.jsx`, `SourceCoverageTable.jsx`, `IntegrationsPage.jsx`, `PlanBanner.jsx`, `SettingsPage.jsx`, and `usePlan.js`.

## 10. Built-in Sources

Built-in source readiness summary now includes:

- `evidence_confirmed`
- `monitoring_certified`
- `baseline_pending`
- `blocked`
- per-source `certification_status`
- per-source `evidence_level`
- baseline run counts

Current certification status cannot honestly be called 10/10 until live source runs and repeat baseline history are reviewed.

## 11. What We Can Claim

Safe claims:

- StatuteProof tests public sources for technical accessibility and extraction quality.
- StatuteProof shows quality score, extraction provider, normalized hash, evidence status, and failure reasons.
- A passing source test is not the same as monitoring certification.
- Monitoring certification requires evidence and baseline runs.
- Blocked/login/CAPTCHA/paywall/private sources are not supported.

## 12. What We Cannot Claim

Unsafe claims:

- Any website can be parsed.
- DFSA is fixed and verified.
- A no-save test has evidence records.
- One successful test means certified monitoring.
- Full validation is clean.
- StatuteProof guarantees compliance, coverage, or detection.

## 13. Remaining Gaps

1. DFSA Playwright verification still pending outside sandbox.
2. Real source certification requires repeat baseline history.
3. PDF provider cascade exists but needs deeper integration into live source evidence paths.
4. Optional WARC/timestamp proof is documented, not implemented.
5. Custom source storage is still file-backed, not multi-tenant database-backed.
6. Existing unrelated full-suite and lint failures remain.

## 14. Path To True 10/10

True 10/10 requires:

- live DFSA selector verification;
- 30-day source history across built-in UAE pack;
- repeat baseline evidence for each source;
- customer pilot feedback on failure states and remediation;
- hardened source storage/auth tenancy;
- no unresolved parser-critical validation failures;
- evidence export review by a real MLRO/compliance user.

## 15. Next Exact Task

Run the two DFSA Source Lab no-save checks outside the sandbox where Playwright can launch, record the JSON outputs, and update source certification status only if normalized content is meaningful, hash-unique, and not nav-shell.
