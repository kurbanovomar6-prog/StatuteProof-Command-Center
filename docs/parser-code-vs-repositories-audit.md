# Parser Code vs Repositories Audit

## 1. Executive Verdict

- Parser score: 7/10 for internal demo, 5/10 for customer-facing use.
- Strong enough for demo: yes, if described as a public-source readiness tester with limitations.
- Strong enough for customer-facing use: no.
- Biggest blocker: `app.providers.html_extraction.best_html_extract()` exists and is tested, but the actual extraction path used by monitoring/custom-source intake still calls the older cascade inside `app/extractors.py`.

The implementation is real and better than a basic BeautifulSoup scraper. It has URL safety, Playwright fetch support, source-intake statuses, provider wrappers, custom-source UI/API wiring, and evidence-aware wording. It is not yet a fully integrated multi-provider parser because the provider abstraction is not the active extraction backend.

## 2. Current Implementation Summary

Current backend pieces found:

- `app/scraper.py`: requests + Playwright fetcher with `fetch_page_with_config()`, `wait_for_selector`, and `content_selector`.
- `app/extractors.py`: active extraction path used by pipeline, source tester, source intake, health, discovery, and adapter research. It has its own cascade: BeautifulSoup baseline, trafilatura, readability, optional Crawl4AI.
- `app/providers/html_extraction.py`: provider-wrapper cascade for trafilatura, readability, selectolax, and bs4. Not yet wired into `extract_best_text()`.
- `app/providers/pdf_extraction.py`: provider wrappers for PyMuPDF, pdfplumber, and pypdf.
- `app/providers/optional_tools.py`: htmldate, courlan, and DeepDiff wrappers with graceful fallback.
- `app/source_intake.py`: readiness/status layer for custom source tests and source readiness summary.
- `app/api.py`: `/api/custom-sources/test`, `/api/custom-sources`, `/api/sources/readiness`.
- `web/src/components/app/SourcesPage.jsx`: frontend custom-source modal calls `/api/custom-sources/test`, requires legal confirmation, and posts to `/api/custom-sources`.

Current reports/docs found:

- `docs/universal-source-intake-verification-report.md`
- `docs/custom-source-parser-runbook.md`
- `docs/universal-source-parser-architecture.md`
- `docs/universal-source-intake-implementation-report.md`

Expected but not found in current scan:

- `docs/parser-tooling-github-research.md`
- `.agents/skills/custom-source-parser/SKILL.md`

## 3. Repository Comparison Matrix

| Repository/tool | What it provides | Used/adapted here | Where | Gap | Recommendation |
|---|---|---:|---|---|---|
| Playwright Python | JS rendering and selector waits | Yes | `app/scraper.py` | Browser launch can fail in sandbox; no shared-browser pool for high concurrency. | Keep; improve operational checks later. |
| Crawlee Python | Managed crawling, queues, retries, browser pools | No | N/A | Would be too heavy for current MVP. | Optional later. |
| browser-use | Browser agent automation | No | N/A | Not appropriate for deterministic regulatory monitoring. | Reject for now. |
| Trafilatura | Main-content extraction | Yes | `app/extractors.py`, `app/providers/html_extraction.py` | Provider version not active in monitoring path. | Improve now. |
| readability-lxml | Article/main-content extraction | Yes | `app/extractors.py`, `app/providers/html_extraction.py` | Provider version not active in monitoring path. | Improve now. |
| selectolax | Fast selector parsing | Partial | `app/providers/html_extraction.py` | Not used by active `extract_best_text()`. | Improve now. |
| BeautifulSoup | General fallback parser | Yes | `app/parser.py`, `app/extractors.py`, `app/providers/html_extraction.py` | Good fallback, not enough alone. | Keep. |
| lxml | Parser backend used by readability ecosystem | Indirect | dependency path | Not directly controlled. | Keep indirect. |
| PyMuPDF | Strong PDF text extraction | Provider exists | `app/providers/pdf_extraction.py` | Not clearly wired into source intake/pipeline PDF path. | Optional later. |
| pdfplumber | PDF text/tables | Provider exists | `app/providers/pdf_extraction.py` | Table metadata not surfaced. | Optional later. |
| pypdf | PDF fallback | Provider exists | `app/providers/pdf_extraction.py` | Fallback only. | Keep. |
| htmldate | Publication date extraction | Provider exists | `app/providers/optional_tools.py` | Date result not written into intake metadata. | Optional later. |
| courlan | URL cleanup/canonicalization | Provider exists | `app/providers/optional_tools.py` | Not integrated into URL safety/source IDs. | Optional later. |
| DeepDiff | Structured diff | Provider exists | `app/providers/optional_tools.py` | Not active in evidence diff path. | Optional later. |
| Scrapy | Full crawler framework | No | N/A | Too broad/heavy for official-source MVP. | Reject for now. |
| Firecrawl | Web-to-markdown/crawling API | No | N/A | External service/API risk; not needed for deterministic evidence. | Reject for now. |
| crw | Lightweight crawl/web text ideas | No | N/A | Not needed as dependency. | Optional reference only. |
| Crawl4AI | AI-ready web crawler/markdown | Optional in old extractor | `app/extractors.py` | Re-fetches URL and is opt-in; not provider-layer controlled. | Optional later. |
| skills.sh | Skill marketplace | Docs/planning only | Command Center docs | Not runtime parser technology. | Reject for parser runtime. |
| skillhub.club | Skill marketplace | Docs/planning only | Command Center docs | Not runtime parser technology. | Reject for parser runtime. |
| skillsmp.com | Skill marketplace | Docs/planning only | Command Center docs | Not runtime parser technology. | Reject for parser runtime. |

## 4. Provider Layer Review

Provider files found:

- `app/providers/html_extraction.py`
- `app/providers/pdf_extraction.py`
- `app/providers/optional_tools.py`
- `app/providers/__init__.py`

Active providers:

- In active monitoring path: `app/extractors.py` currently runs its own BeautifulSoup/trafilatura/readability/Crawl4AI cascade.
- In provider layer tests: `best_html_extract()`, `trafilatura_extract()`, `readability_extract()`, `selectolax_extract()`, `bs4_extract()`, and PDF/optional wrappers are tested.

Optional providers:

- trafilatura, readability, selectolax, PyMuPDF, pdfplumber, pypdf, htmldate, courlan, DeepDiff all degrade safely on missing imports.

Stubs:

- No dedicated Crawlee, Scrapy, Firecrawl, crw, or browser-use provider was found. This is acceptable; these should not be hard dependencies for the MVP.

Dependency handling:

- Missing imports generally return structured failure instead of crashing. This is good.

## 5. Critical Gap Review

- Is `best_html_extract()` wired into `extract_best_text()`? No.
- Is provider cascade used by actual monitoring path? No; monitoring imports `app.extractors.extract_best_text()`, which uses a separate internal cascade.
- Does custom source test use provider cascade? Indirectly no; it uses `run_source_intake()`, which calls `extract_best_text()`, not provider `best_html_extract()`.
- Does source readiness use provider cascade? Stored readiness summary does not fetch/extract; source-run paths use `extract_best_text()`, not provider `best_html_extract()`.
- Does dashboard use honest readiness status? Better than before. It displays readiness and evidence notes more honestly, but it still uses mock/source-map UI in places and is not a complete live evidence dashboard.

## 6. Safety Review

URL safety:

- `validate_public_url()` blocks non-http(s), localhost, loopback/private/reserved/unspecified IPs, and credential URLs.

Private/restricted sources:

- The system does not bypass login, CAPTCHA, private portals, or paywalls. It does not yet robustly detect all such pages from fetched content.

No customer delivery:

- No customer delivery path was run during this audit.

Secrets:

- `.env` was not printed. API keys/tokens were not inspected or exposed.

## 7. Evidence Review

No-save behavior:

- `/api/custom-sources/test` uses `write_evidence=False`, so it should not create evidence artifacts.

Save behavior:

- `/api/custom-sources` saves a disabled custom source for validation. It does not activate monitoring automatically.

Proof/evidence fields:

- API now includes evidence-related fields such as `evidence_written`, `evidence_required`, and `proof_path`, but the custom-source test response still lacks the full required response contract: `readiness_status`, `source_type`, `provider_used`, `normalized_preview`, and `legal_policy_status`.

Confirmed wording:

- UI correctly says "Test passed - save required for evidence record" when no evidence was written. That is the right product-safe wording.

## 8. Recommended Fixes

P0:

- Wire `app.providers.html_extraction.best_html_extract()` into `app.extractors.extract_best_text()` while preserving the existing return shape.
- Add API fields required by the custom-source response contract: `readiness_status`, `source_type`, `provider_used`, `normalized_preview`, and `legal_policy_status`.
- Require legal confirmation in `POST /api/custom-sources`, not only in the frontend.

P1:

- Add tests proving `extract_best_text()` calls the provider cascade.
- Add tests proving custom source response metadata includes provider/evidence/legal fields.
- Add stronger nav-shell quality handling in provider scoring so long boilerplate is not selected purely by length.

P2:

- Integrate htmldate/courlan metadata into evidence metadata.
- Wire PDF provider cascade into real PDF monitoring path.
- Add a manual DFSA selector verification run outside the sandbox where Playwright can launch.
