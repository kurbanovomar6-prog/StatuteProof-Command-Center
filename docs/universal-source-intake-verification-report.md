# Universal Source Intake Verification Report

## 0. Files Inspected

- `product/regradar/app/source_intake.py`
- `product/regradar/app/scraper.py`
- `product/regradar/app/api.py`
- `product/regradar/run.py`
- `product/regradar/sources.json`
- `product/regradar/app/text_normalization.py`
- `product/regradar/app/source_runs.py`
- `product/regradar/app/proof.py`
- `product/regradar/app/diff.py`
- `product/regradar/app/source_tester.py`
- `product/regradar/tests/test_source_intake.py`
- `product/regradar/tests/`
- `product/regradar/requirements.txt`
- `product/regradar/data/source_runs/`
- `product/regradar/data/source_snapshots/`
- `product/regradar/web/src/components/app/SourcesPage.jsx`
- `product/regradar/web/src/components/app/DashboardHome.jsx`
- `product/regradar/web/src/components/app/EvidencePage.jsx`
- `docs/universal-parser-current-state-audit.md`
- `docs/universal-source-parser-architecture.md`
- `docs/custom-source-parser-runbook.md`
- `docs/universal-source-intake-implementation-report.md`

Not found during inspection: `docs/parser-tooling-github-research.md` and `.agents/skills/custom-source-parser/SKILL.md`.

## 1. Executive Verdict

- Score: 6/10 after hardening fixes.
- Safe for demo: yes, only if presented as a source-readiness tester with limitations, not as a universal parser.
- Safe for customer-facing use: no.
- Main blocker: the backend intake is real, but the frontend custom-source flow is not wired to the new `/api/custom-sources/test` endpoint and live DFSA selector extraction was not proven in this sandbox because Playwright could not launch.

The implementation exists and is not a fake stub. However, the original claim "Universal Source Intake Engine - complete" was too strong. Before fixes, a source could be treated as activatable too easily, selector failures could fall back to full-page HTML, URL credentials were not blocked, and readiness aggregation could mark sources confirmed based on a weak length check. Those issues have been minimally hardened.

## 2. Claimed Features Verification Table

| Claimed feature | Verified | Evidence | Issue | Fix |
|---|---:|---|---|---|
| `source_intake.py` added with 8-status vocabulary | Partial | `product/regradar/app/source_intake.py` | 8 intake statuses exist, but no explicit `FAILED` or `SOURCE_STRUCTURE_CHANGED` intake status. Source-run statuses remain separate. | Reported as gap. |
| `is_nav_shell_only()` added | Yes | `source_intake.py` and `tests/test_source_intake.py` | Logic is heuristic and still not a full regulatory-density classifier. | Added stronger nav-shell tests. |
| Hash collision checker added | Partial | `_check_hash_collision()` and `readiness_summary()` | Original helper only checked `content_hash` fields in `sources.json`, which are not normal source records. | Added latest-run normalized-hash collision blocking in `readiness_summary()`. |
| `readiness_summary()` added for dashboard | Yes, hardened | `source_intake.py` | Original version read nonexistent `chars` field and confirmed readiness by length only. | Now requires acceptable run status, access status, quality, normalized hash, proof path, no nav-shell/collision. |
| DFSA config fixed with `main` selector | Config yes, live proof no | `sources.json` entries for `AE-dubai-financial-services-authority-dfsa` and `AE-dfsa-notices` | Live selector test could not complete because Playwright cannot launch in sandbox. | Selector failures now return `NEEDS_SELECTOR_REVIEW`, not false confirmation. |
| `fetch_page_with_config()` added | Yes, hardened | `app/scraper.py` | Original selector miss silently fell back to full-page HTML. | Selector timeout/miss now raises and intake marks review needed. |
| API endpoints added | Yes, partial product readiness | `app/api.py` | Custom source add enabled sources without proof; PDF-needed result was activatable. | Custom sources now save as disabled pending validation; only `CONFIRMED_ACCESSIBLE` can activate. |
| 18 tests pass | Superseded | `tests/test_source_intake.py` | Intake tests now 26 pass. Full suite still has unrelated weekly-brief expectation failures. | Reported validation gap. |
| Docs/runbook/operator skill added | Partial | Docs found, skill not found | `.agents/skills/custom-source-parser/SKILL.md` was not present in inspected tree. | Reported as gap. |
| Live DFSA verification still needed | Yes | Two-source live attempt run | Playwright launch failed due sandbox permission. | Must rerun outside sandbox or approved local terminal. |

## 3. Parser Logic Review

Statuses: `CONFIRMED_ACCESSIBLE`, `JS_RENDERING_NEEDED`, `PDF_EXTRACTION_NEEDED`, `NAV_SHELL_ONLY`, `QUALITY_DROP`, `NEEDS_SELECTOR_REVIEW`, `UNSUPPORTED`, and `BLOCKED` exist. These are intake-readiness statuses, not identical to source-run statuses such as `FIRST_SEEN`, `UNCHANGED`, `CHANGED`, `FAILED`, `QUALITY_DROP`, and `SOURCE_STRUCTURE_CHANGED`.

URL safety: `validate_public_url()` blocks non-http(s) schemes, localhost aliases, loopback/private/reserved IPs, and now blocks URLs with embedded credentials. It does not reliably detect login/CAPTCHA/paywall pages before fetch; that remains a content-detection gap.

Extraction cascade: `run_source_intake()` now uses actual extracted text from dict/tuple extractors and hashes normalized text. Before the fix it could hash the string representation of an extraction dict.

Quality scoring: `CONFIRMED_ACCESSIBLE` now returns `GOOD` or `ACCEPTABLE`, not `LIMITED`. Thin extraction maps to JS rendering, selector review, PDF needed, or quality drop.

Hash collision: live intake collision checking still depends on `content_hash` in source entries when `all_sources` is passed. Dashboard readiness now also blocks duplicate latest-run normalized hashes.

DFSA fix: both DFSA sources contain `fetch_method: playwright`, `wait_for_selector: main`, `content_selector: main`, and `expected_min_length: 3000`. The selector is now strict: missing selector does not silently use the full page.

## 4. API Review

Endpoints inspected:
- `GET /api/sources/readiness`
- `GET /api/custom-sources`
- `POST /api/custom-sources/test`
- `POST /api/custom-sources`
- older `POST /api/source-test`

The new endpoints require `require_auth(self)`. Input validation exists through URL validation for custom source tests/adds. `/api/custom-sources/test` now returns `failure_reason` and `remediation_hint`. `/api/custom-sources` no longer enables a custom source immediately; it saves as disabled with `pending_validation`.

Remaining API risk: custom sources are stored globally in `sources.json`, not workspace-scoped storage. The add endpoint does not cryptographically bind a prior passed test result to the add request. This is acceptable for a prototype, not customer-facing multi-tenant use.

## 5. UI Review

Frontend inspected under `product/regradar/web/src/components/app/`.

The custom source UI in `SourcesPage.jsx` is not wired to the new `/api/custom-sources/test` or `/api/custom-sources` endpoints. It still posts to `/api/source-test` and stores custom sources locally/profile-side. It separates built-in and user sources visually, but it does not expose the new `readiness_status`, `failure_reason`, `remediation_hint`, normalized preview, or proof/evidence artifact status from source intake.

The exact phrase "Confirmed accessible with evidence records" was not found in frontend code. The UI is safer than that exact overclaim, but it still is not a real frontend for the new Universal Source Intake Engine.

## 6. Evidence Review

No-save mode: `run_source_intake(..., write_evidence=False)` does not write snapshots; verified by test.

Save mode: `run_source_intake(..., write_evidence=True)` writes raw and normalized snapshots through `_write_snapshots()` only when status is `CONFIRMED_ACCESSIBLE`. It does not append a source run JSONL record and does not build the same full proof/diff artifacts as the production source-run pipeline.

Evidence gap: source intake preview is not equivalent to complete evidence readiness. The product must not claim "with evidence records" from a no-save intake test. Full evidence should come from the source-run/proof pipeline.

## 7. Tests and Validation

Commands run:

- `python3 -m compileall product/regradar` - passed, but noisy because it traversed `node_modules`.
- `python3 -m compileall app run.py -q` - passed.
- `python3 -m pytest tests/test_source_intake.py -q` - passed, 26 tests.
- `python3 -m pytest tests -q` - failed, 68 passed and 2 failed in `tests/test_weekly_brief.py`; failures are weekly brief wording expectations unrelated to source intake.
- `npm run build` in `product/regradar/web` - passed.
- `npm run lint` in `product/regradar/web` - failed with pre-existing frontend lint errors in `App.jsx`, `DiffViewer.jsx`, `EvidenceCard.jsx`, `Pricing.jsx`, `PricingPage.jsx`, `SourceCoverageTable.jsx`, `IntegrationsPage.jsx`, `PlanBanner.jsx`, `SettingsPage.jsx`, and `usePlan.js`.
- `python3 tools/validate_workspace.py` - passed.
- `python3 tools/validate_codex_skills.py` - passed.

Targeted tests added:
- URL safety blocks `file://`, `127.0.0.1`, `0.0.0.0`, and credential URLs.
- Repeated nav-shell text is detected.
- Mixed regulatory article text is not rejected as nav-shell.
- Intake uses extracted dict text, not dict representation.
- Readiness summary requires hash, quality, length, and proof path.

## 8. Live DFSA Verification

Live two-source DFSA intake was attempted with `write_evidence=False` only:

- `AE-dubai-financial-services-authority-dfsa`
- `AE-dfsa-notices`

Result: not verified. Playwright failed to launch in the sandbox with Chromium permission errors. Both sources returned `NEEDS_SELECTOR_REVIEW`, `chars_normalized=0`, no hash, and no false confirmation.

Exact safe command to rerun outside the sandbox:

```bash
cd /Users/kurbnovomar/StatuteProof-Command-Center/product/regradar
python3 -c 'import json; from pathlib import Path; from app.source_intake import run_source_intake; sources=json.loads(Path("sources.json").read_text()); ids={"AE-dubai-financial-services-authority-dfsa","AE-dfsa-notices"}; [print(s["source_id"], run_source_intake(s, all_sources=sources, write_evidence=False)) for s in sources if s.get("source_id") in ids]'
```

## 9. Remaining Gaps

1. Live DFSA selector extraction is not proven.
2. Source intake save mode is not the same as complete evidence/proof/diff record creation.
3. Frontend custom source flow is not wired to the new custom-source endpoints.
4. No workspace-scoped custom source storage.
5. No reliable login/CAPTCHA/paywall/private-portal page classifier.
6. Intake hash collision helper still depends on source entries having `content_hash`; only readiness summary now checks latest-run normalized hash collisions.
7. Full backend tests and frontend lint do not pass.
8. Missing `.agents/skills/custom-source-parser/SKILL.md` if that was part of the claimed implementation.

## 10. Next Exact Task

Run the DFSA selector verification outside the sandbox in a local terminal where Playwright can launch, then capture for both DFSA source IDs: status, normalized length, normalized hash, extraction method, nav-shell flag, collision flag, and a short official-content preview. Do not run all sources and do not write evidence during that test.
