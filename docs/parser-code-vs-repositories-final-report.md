# Parser Code vs Repositories Final Report

## 1. Executive Verdict

- Score: 7.5/10 for internal demo; 5.5/10 for customer-facing use.
- What improved: `app.extractors.extract_best_text()` now uses the provider-layer `best_html_extract()` cascade; custom-source API returns the missing readiness/provider/evidence/legal fields; backend save requires legal confirmation and reruns readiness before saving; UI fallback no longer marks local-only saved sources as validated.
- What remains weak: full evidence creation is still not part of the no-save test flow; DFSA Playwright extraction is still not live-verified; full backend suite and frontend lint are not clean.
- Safe for demo: yes, if framed as public-source readiness testing with limitations.
- Safe for customer use: no.

## 2. Repository Usage Table

| Repo/tool | Link | Status | Implementation file | Active/fallback/optional/rejected | Why |
|---|---|---|---|---|---|
| Playwright Python | https://github.com/microsoft/playwright-python | Used | `app/scraper.py` | Active fetch fallback/config path | Required for JS-rendered regulator sites, but local sandbox launch failed. |
| Crawlee Python | https://github.com/apify/crawlee-python | Not used | N/A | Optional later | Too heavy for current official-source MVP. |
| browser-use | https://github.com/browser-use/browser-use | Not used | N/A | Rejected for now | Agentic browser control is not deterministic enough for evidence monitoring. |
| Trafilatura | https://github.com/adbar/trafilatura | Used | `app/providers/html_extraction.py`, `app/extractors.py` | Active provider | Main content extraction. |
| readability-lxml | https://github.com/buriy/python-readability | Used | `app/providers/html_extraction.py` | Active fallback | Article/main-content fallback. |
| selectolax | https://github.com/rushter/selectolax | Used if installed | `app/providers/html_extraction.py` | Active optional provider | Fast selector extraction; graceful missing-dep handling. |
| BeautifulSoup | https://www.crummy.com/software/BeautifulSoup/ | Used | `app/parser.py`, `app/providers/html_extraction.py` | Active fallback | Required final HTML fallback. |
| lxml | https://github.com/lxml/lxml | Indirect | readability dependency path | Optional/indirect | Useful via readability; no direct custom layer needed now. |
| PyMuPDF | https://github.com/pymupdf/PyMuPDF | Provider exists | `app/providers/pdf_extraction.py` | Optional PDF provider | Not fully wired into source intake evidence path. |
| pdfplumber | https://github.com/jsvine/pdfplumber | Provider exists | `app/providers/pdf_extraction.py` | Optional PDF provider | Useful for table-heavy PDFs; table metadata not surfaced yet. |
| pypdf | https://github.com/py-pdf/pypdf | Provider exists | `app/providers/pdf_extraction.py` | Optional fallback | Safe text-only PDF fallback. |
| htmldate | https://github.com/adbar/htmldate | Provider exists | `app/providers/optional_tools.py` | Optional metadata | Not yet written into evidence metadata. |
| courlan | https://github.com/adbar/courlan | Provider exists | `app/providers/optional_tools.py` | Optional URL helper | Not yet integrated into URL safety/source canonicalization. |
| DeepDiff | https://github.com/seperman/deepdiff | Provider exists | `app/providers/optional_tools.py` | Optional structured diff | Existing evidence diff path still uses local chunk diff. |
| Scrapy | https://github.com/scrapy/scrapy | Not used | N/A | Rejected for now | Broad crawler framework is unnecessary for limited official-source monitoring. |
| Firecrawl | https://github.com/mendableai/firecrawl | Not used | N/A | Rejected for now | External service/API dependency is inappropriate for deterministic evidence MVP. |
| crw | https://github.com/us/crw | Not used | N/A | Optional reference only | No reason to vendor or depend on it now. |
| Crawl4AI | https://github.com/unclecode/crawl4ai | Optional legacy path | `app/extractors.py` | Optional opt-in fallback | Existing opt-in fallback remains, but provider layer is primary. |
| skills.sh | https://www.skills.sh/ | Planning only | docs/skills context | Rejected for parser runtime | Skill marketplace, not parser runtime dependency. |
| skillhub.club | https://skillhub.club/ | Planning only | docs/skills context | Rejected for parser runtime | Skill marketplace, not parser runtime dependency. |
| skillsmp.com | https://skillsmp.com/ | Planning only | docs/skills context | Rejected for parser runtime | Skill marketplace, not parser runtime dependency. |

## 3. Provider Integration

`best_html_extract()` is now wired into the actual extraction path:

- `app/extractors.extract_best_text()` calls `app.providers.html_extraction.best_html_extract()`.
- Existing return shape is preserved: `text`, `method`, `extracted_chars`, `quality`, `candidates`.
- New metadata is returned: `provider_used`, `confidence`, `warnings`.
- The old extractor cascade remains as a safe fallback if provider wrappers fail.
- Tests prove `extract_best_text()` calls `best_html_extract()`.

Provider cascade now follows safer order:

1. explicit selector via selectolax when `content_selector` is supplied
2. trafilatura
3. readability
4. selectolax generic selector fallback
5. BeautifulSoup
6. best available fallback with warning

## 4. Custom Source Flow

Frontend:

- `SourcesPage.jsx` calls `/api/custom-sources/test`.
- Save posts to `/api/custom-sources`.
- Legal confirmation checkbox is required before save.
- LocalStorage fallback is now explicitly fallback and marks the source `Under validation`, not `Validated`.
- UI says "Test passed - save required for evidence record" when no evidence was written.

Backend:

- `/api/custom-sources/test` returns readiness status, provider, normalized hash, preview, evidence flags, failure reason, remediation hint, and legal policy status.
- `/api/custom-sources` now requires legal confirmation.
- `/api/custom-sources` reruns source intake and refuses save unless readiness is `CONFIRMED_ACCESSIBLE`.
- Saved custom sources remain disabled with `pending_validation`; monitoring is not auto-activated.

## 5. Evidence Readiness

No-save test:

- Does not write evidence.
- Returns `evidence_written: false`, `evidence_required: true`, and `proof_path: null`.
- UI correctly avoids saying evidence records exist.

Save:

- Saves only as a disabled pending-validation custom source.
- Does not create a full source-run proof artifact.

Confirmed rule:

- Product should only say "Confirmed accessible with evidence records" when a full monitoring/evidence run produced proof artifacts. A no-save test can only say "Test passed - save required for evidence record."

## 6. DFSA Status

DFSA config in `sources.json` includes:

- `fetch_method: playwright`
- `wait_for_selector: main`
- `content_selector: main`
- `expected_min_length: 3000`

Live verification result: not verified. The two-source DFSA test was run with `write_evidence=False`, but Playwright failed to launch in the local sandbox. Both sources returned `NEEDS_SELECTOR_REVIEW`, normalized length `0`, no hash, no provider, and no false confirmation.

Manual verification command:

```bash
cd /Users/kurbnovomar/StatuteProof-Command-Center/product/regradar
python3 -c 'import json; from pathlib import Path; from app.source_intake import run_source_intake; sources=json.loads(Path("sources.json").read_text()); ids={"AE-dubai-financial-services-authority-dfsa","AE-dfsa-notices"}; [print(s["source_id"], run_source_intake(s, all_sources=sources, write_evidence=False)) for s in sources if s.get("source_id") in ids]'
```

## 7. Tests

Passed:

- `python3 -m compileall product/regradar/app product/regradar/run.py -q`
- `python3 -m pytest product/regradar/tests/test_source_intake.py -q` -> 52 passed.
- `npm run build` -> passed.
- `python3 tools/validate_workspace.py` -> passed.
- `python3 tools/validate_codex_skills.py` -> passed.
- `git diff --check` -> passed.

Failed:

- `python3 -m pytest product/regradar/tests -q` -> 95 passed, 2 failed. Both failures are in `test_weekly_brief.py` and relate to expected wording for disclaimer/no-change text.
- `npm run lint` -> failed with existing frontend lint issues in `App.jsx`, `DiffViewer.jsx`, `EvidenceCard.jsx`, `Pricing.jsx`, `PricingPage.jsx`, `SourceCoverageTable.jsx`, `IntegrationsPage.jsx`, `PlanBanner.jsx`, `SettingsPage.jsx`, and `usePlan.js`.

## 8. Remaining Limitations

1. DFSA selector extraction remains unproven until Playwright runs outside this sandbox.
2. PDF provider cascade exists but is not fully wired into source evidence runs.
3. htmldate/courlan metadata is not written into evidence metadata.
4. Custom-source save still writes to `sources.json`, not workspace-scoped storage.
5. Login/CAPTCHA/paywall detection is basic and cannot be treated as exhaustive.
6. Full backend suite is not clean because weekly-brief tests are stale or the generator wording changed.
7. Frontend lint is not clean due unrelated existing issues.

## 9. Customer-Safe Claims

Safe:

- "StatuteProof can test public official-source URLs for technical accessibility and extraction quality."
- "Custom sources are saved for validation; monitoring does not activate automatically."
- "A no-save source test does not create an evidence record."
- "Evidence records are created by monitoring runs, not by the preview test."
- "Source limitations and failure reasons are shown."

## 10. Unsafe Claims

Do not say:

- "Any website can be parsed."
- "Confirmed accessible with evidence records" after only `/api/custom-sources/test`.
- "DFSA extraction is fixed" until the two DFSA Playwright checks succeed.
- "Full parser validation is clean" while full pytest and lint still fail.
- "Custom sources are production-ready multi-tenant" while they are stored globally in `sources.json`.

## 11. Next Exact Task

Run the two DFSA source intake checks outside the sandbox where Playwright can launch, with `write_evidence=False`, and record normalized length, normalized hash, provider, selector used, nav-shell flag, collision flag, readiness status, and a short official-content preview.
