# Parser 10/10 Realistic Roadmap

## 1. Current Score And Why

Current honest score: 7.5/10 for internal demo and 5.5/10 for customer-facing use.

Why:

- Provider cascade is wired into the main extraction path.
- Custom source testing uses the safer `/api/custom-sources/test` path.
- No-save tests do not claim evidence exists.
- URL safety blocks obvious SSRF classes.
- The system still lacks a formal source certification layer, evidence levels, benchmark fixtures, baseline-run certification, and live DFSA verification.
- Full validation is not clean because unrelated weekly-brief tests and frontend lint still fail.

## 2. What 10/10 Means Realistically

10/10 means StatuteProof is honest and evidence-grade, not magical:

- Monitorable public sources extract well.
- Non-monitorable sources fail clearly with reasons.
- “Confirmed” requires proof artifacts.
- “Certified for monitoring” requires repeat baseline success.
- Source quality is scored with a transparent breakdown.
- Evidence artifacts are complete enough to audit.
- Failures are surfaced as product states.

## 3. What Cannot Be Promised

StatuteProof cannot promise:

- Any website can be parsed.
- CAPTCHA, login, private portal, or paywall bypass.
- 100% detection.
- Guaranteed compliance.
- Legal advice.
- Regulator affiliation or certification.
- Monitoring certification from one no-save test.

## 4. Architecture Upgrades Needed

Required upgrades:

- Source certification model with baseline runs.
- Quality scorecard with transparent component scores and penalties.
- Evidence levels: preview, basic, full, certified.
- Provider matrix documentation and safe optional provider reporting.
- CLI Source Lab for single-URL testing.
- Benchmark fixture suite for known parser failure modes.
- UI Source Lab states that separate test pass, evidence confirmation, and monitoring certification.

## 5. Source Certification Model

Certification statuses:

- `TEST_PASSED`: one no-save test passed.
- `EVIDENCE_CONFIRMED`: proof/evidence artifacts exist.
- `BASELINE_PENDING`: first evidence run exists, repeat baseline still needed.
- `MONITORING_CERTIFIED`: baseline requirement met with stable successful runs.
- `CERTIFICATION_FAILED`: quality, fetch, collision, or evidence requirements failed.
- `NEEDS_HUMAN_REVIEW`: selector/source ambiguity remains.

Rule: customer-facing active monitoring certification requires `MONITORING_CERTIFIED`, not `TEST_PASSED`.

## 6. Benchmark Suite Design

Fixtures should cover:

- Good regulator page.
- Nav shell only.
- JS shell.
- Listing page.
- Legal database page.
- Login page.
- CAPTCHA page.
- Paywall page.
- Short homepage.
- PDF good/shallow/table-like cases.
- DFSA-like nav shell.
- VARA/CBUAE-like regulatory content.

Tests must prove quality scoring, status mapping, no-save evidence limits, save evidence minimums, hash collision blocking, and optional provider safety.

## 7. Evidence-Grade Artifacts

Evidence should evolve toward:

- raw response.
- rendered HTML if Playwright used.
- screenshot if safe and configured.
- normalized text.
- metadata.
- proof block.
- source run JSONL.
- provider report.
- quality report.
- certification report.
- diff artifacts when changed.
- hash chain.
- optional WARC when enabled.

Evidence levels:

- `PREVIEW_ONLY`
- `BASIC_EVIDENCE`
- `FULL_EVIDENCE`
- `CERTIFIED_EVIDENCE`

## 8. Open-Source Tools To Use

Core/active:

- Playwright Python.
- trafilatura.
- readability-lxml.
- selectolax.
- BeautifulSoup.
- lxml indirectly.
- PyMuPDF/pdfplumber/pypdf for PDF cascade.
- htmldate/courlan/DeepDiff as optional helpers.

Optional/future:

- Resiliparse and jusText for boilerplate removal.
- extruct for structured metadata.
- warcio/Browsertrix/OpenTimestamps for stronger evidence provenance.
- Crawlee/Scrapy/Crawl4AI only if scale or experiments justify them.

Rejected for core runtime now:

- Firecrawl/browser-use/crw as dependencies; keep as references only.

## 9. Implementation Phases

Phase 1:

- Add certification and quality modules.
- Add source-lab CLI.
- Add benchmark fixtures and parser tests.
- Expose quality/certification fields in API.

Phase 2:

- Upgrade saved source-intake artifacts.
- Add provider/quality/certification reports.
- Add dashboard certification counters.
- Add Source Lab UI panels.

Phase 3:

- Live DFSA verification outside sandbox.
- Baseline-run certification for built-in UAE source pack.
- Optional metadata/WARC/timestamp enhancements.

## 10. Risks And Mitigations

- Risk: false “ready” labels. Mitigation: certification status requires evidence and baseline.
- Risk: noisy boilerplate hashes. Mitigation: quality score, nav-shell detection, collision blocking.
- Risk: Playwright environment failures. Mitigation: explicit `NEEDS_SELECTOR_REVIEW` and runbook.
- Risk: dependency bloat. Mitigation: optional providers must degrade safely.
- Risk: legal overclaim. Mitigation: safe copy and certification wording rules.

## 11. Acceptance Criteria

8/10:

- Provider cascade active.
- Quality score visible.
- Source certification statuses exist.
- No-save test cannot claim evidence.
- Targeted benchmark tests pass.

9/10:

- Saved intake writes basic evidence artifacts.
- Built-in sources show evidence/certification counters.
- Source Lab CLI and UI expose provider/quality/certification results.
- DFSA manual verification path is documented.

10/10:

- Built-in UAE source pack has repeat baseline history.
- Evidence levels are backed by real proof paths and hash chains.
- Live Playwright sources verified outside sandbox.
- Parser benchmarks include representative UAE regulatory pages.
- Customer-facing UI only claims certification where baseline evidence proves it.
