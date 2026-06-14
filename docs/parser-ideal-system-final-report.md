# Parser Ideal System Final Report

## 1. Executive Verdict

**Parser score before:** 7.2 / 10

**Parser score after:** 7.9 / 10

**Customer-facing readiness before:** 5.8 / 10

**Customer-facing readiness after:** 7.4 / 10

**Agent/skill readiness before:** 7.4 / 10

**Agent/skill readiness after:** 8.6 / 10

**Can StatuteProof claim perfect parsing?** No.

**What StatuteProof can honestly claim:** StatuteProof can test and monitor public sources that are technically accessible and permitted to be monitored. It shows extraction quality, evidence readiness, hashes, diffs, activation readiness, and failure reasons clearly.

The system is materially safer after this pass. The Source Lab contract now separates preview, evidence, and monitoring activation; the parser gate blocks high-risk customer-facing overclaims; the agent workflow tells Source Monitor, Evidence Trail, QA, and Legal what to block; and the frontend is aligned to the current source-readiness story. The system is not yet a 10/10 parser because DFSA still fails live no-save checks, there is no long-lived baseline history for every hard source, and optional evidence layers such as WARC, screenshot capture, and external timestamping remain future work.

## 2. Current Architecture

The current source-intake path is:

1. Source specification: public URL, jurisdiction, regulator/entity, source type, legal confirmation, optional selector, wait selector, JS rendering, PDF mode, and minimum expected text length.
2. Source Intake Engine: validates URL safety, blocks private/local/protected patterns, fetches content through configured providers, normalizes text, computes hashes, and produces quality warnings.
3. Provider cascade: explicit selector/source adapter where available, HTML extraction providers, safe fallback, PDF extraction providers when applicable, and Playwright for JavaScript-rendered checks when requested.
4. Quality and activation logic: classifies shallow text, nav shells, blocked sources, selector failures, hash collisions, and provider failures as not ready rather than confirmed.
5. Evidence layer: save mode can write proof artifacts; no-save checks are preview only.
6. API/CLI contract: Source Lab returns provider, extraction method, normalized length/hash, quality score/label, evidence level, activation readiness, warnings, failure reason, remediation hint, and save/activation gates.
7. Frontend: Source Lab, Sources, Dashboard, Pricing/Billing, and reports surface source readiness without claiming regulator certification or universal parsing.

## 3. Agent / Skill Upgrades

Updated operating-system files:

- `AGENTS.md`
- `TOOL_ROUTER.md`
- `STATUTEPROOF_CONTEXT.md`
- `.agents/skills/source-monitoring-review/SKILL.md`
- `.agents/skills/evidence-readiness-review/SKILL.md`
- `.agents/skills/custom-source-monitoring-spec/SKILL.md`
- `.agents/skills/custom-source-parser/SKILL.md`
- `skills/custom-source-parser/SKILL.md`
- `workflows/08-parser-source-intake-review.md`

Parser tasks now route through this review order:

1. Source Monitor reviews URL/source spec and source-health facts.
2. Source Intake Engine runs no-save or saved tests.
3. Evidence Trail verifies proof artifacts before any evidence-backed claim.
4. QA/Critic blocks false confirmed states, stale labels, and dead CTAs.
5. Legal Language reviews customer-facing wording.
6. Founder approval is required before remediation sources move to customer-visible ready status if live verification is incomplete.

Key rules now explicit in skills and workflow:

- No-save is preview only.
- One successful test is not monitoring-ready.
- Evidence confirmed requires proof artifacts.
- Activation readiness requires baseline/activation gates.
- Protected, login, CAPTCHA, paywall, private, and local sources are blocked.
- DFSA/JS pages require live Playwright verification.
- Confirmed, evidence, and activation readiness are separate states.
- Do not claim universal parsing, guaranteed parsing, legal advice, or regulator certification.

## 4. Reference Repositories

Known reference repositories reviewed or attempted:

- `microsoft/playwright-python`
- `apify/crawlee-python`
- `browser-use/browser-use`
- `adbar/trafilatura`
- `buriy/python-readability`
- `rushter/selectolax`
- `lxml/lxml`
- `chatnoir-eu/chatnoir-resiliparse`
- `miso-belica/jusText`
- `scrapy/extruct`
- `pymupdf/PyMuPDF`
- `jsvine/pdfplumber`
- `py-pdf/pypdf`
- `pdfminer/pdfminer.six`
- `adbar/htmldate`
- `adbar/courlan`
- `seperman/deepdiff`
- `webrecorder/warcio`
- `opentimestamps/opentimestamps-client`
- `scrapy/scrapy`
- `mendableai/firecrawl`
- `us/crw`
- `unclecode/crawl4ai`
- `webrecorder/browsertrix-crawler`
- `Unstructured-IO/unstructured`
- `docling-project/docling`
- `mherrmann/helium`
- `pyppeteer/pyppeteer`
- `psf/requests-html`
- `vercel-labs/skills`
- `coreyhaines31/marketingskills`
- `hardikpandya/stop-slop`
- `nextlevelbuilder/ui-ux-pro-max-skill`
- `emilkowalski/skill`
- `pbakaus/impeccable`
- `leonxlnx/taste-skill`

Reference repos are research-only under `.reference_parser_repos/`, are gitignored, and are not vendored into product runtime. The inventory is in `docs/parser-reference-repositories-inventory.md`.

## 5. New GitHub Repositories Found

Additional candidates evaluated:

- `dgtlmoon/changedetection.io`
- `ArchiveBox/ArchiveBox`
- `microsoft/markitdown`
- `simonw/shot-scraper`
- `alexwlchan/changes`
- `huginn/huginn`
- `WebScrapingAPI/cssselect2`
- `landakram/hyperlink`
- `gruns/furl`
- `python-hyper/uritemplate`
- `wention/BeautifulSoup4`
- `davidteather/TikTok-Api`
- `news-please/news-please`
- `Dragory/pdf-diff`
- `jazzband/prettytable`
- `miso-belica/sumy`
- `mozilla/readability`
- `cleanlab/cleanlab`
- `great-expectations/great_expectations`
- `fullhunt/spring4shell-scan`
- `google/gumbo-parser`
- `CommonCrawl/cc-index-server`
- `internetarchive/heritrix3`

The most useful inspiration came from `changedetection.io` for change-watch UX and failure states, `ArchiveBox` for snapshot/evidence thinking, `markitdown` for document-to-markdown normalization, and `shot-scraper` for screenshot evidence. None were copied into runtime. The discovery report is in `docs/parser-github-discovery-report.md`.

## 6. What Was Improved

Code improvements:

- Added a Source Lab contract builder that separates save eligibility from monitoring activation.
- Added `can_save_for_validation`, `can_activate_monitoring`, `activation_readiness`, `evidence_level`, and baseline fields to API/CLI output.
- Preserved `can_activate` as a backward-compatible alias for `can_activate_monitoring`.
- Added normalized preview to CLI JSON output for no-save checks.
- Strengthened fetch-exception output so failures still include quality/certification-style fields and safe remediation data.
- Changed customer-facing status label from "Ready" to "Readiness threshold met" for confirmed-accessible parser results.
- Added parser contract tests for readiness labels and Source Lab activation separation.
- Added `tools/validate_parser_quality.py` as a strict parser/source-intake gate.
- Updated `tools/validate_workspace.py` so ignored `.reference_*` research libraries do not fail nested repo/env-template checks while real workspace `.env` files remain blocked.

Frontend and copy improvements:

- Source Lab no longer treats preview results as activation-ready.
- Save and activate actions are driven by separate API fields.
- Public/app source tables now use the current 13 enabled, 9 readiness-supported, 4 under extraction remediation story.
- DFSA, DIFC, and UAE FIU homepage remediation states are no longer shown as customer-ready.
- Customer-facing copy avoids regulator certification, legal advice, universal parsing, and guaranteed monitoring claims.

Docs and runbooks created or updated:

- `docs/agent-parser-system-audit.md`
- `docs/parser-system-full-audit-before-improvement.md`
- `docs/parser-reference-repositories-inventory.md`
- `docs/parser-github-discovery-report.md`
- `docs/parser-reference-comparison-report.md`
- `docs/parser-agent-system-upgrade-report.md`
- `docs/parser-quality-gates.md`
- `docs/dfsa-live-source-lab-verification-report.md`
- `docs/current-uae-source-readiness-validation-report.md`

## 7. DFSA Live Check

Two no-save DFSA Source Lab checks were run outside the sandbox:

1. `https://www.dfsa.ae/rules-and-standards`
2. `https://www.dfsa.ae/regulation/notices-public-registers`

Common result:

- Playwright launched: yes.
- `main` selector matched, but it matched a page-not-found shell.
- Provider used: `bs4`.
- Extraction method: `bs4`.
- Normalized length: 77.
- Normalized hash: `aaaffe59c59c09e66f5bd79fb59e0fdcf978e0ad2294e917d053521a0b918e9f`.
- Quality score: 0.
- Quality label: `POOR`.
- Readiness status: `NAV_SHELL_ONLY`.
- Activation readiness: `NEEDS_REMEDIATION`.
- Evidence level: `PREVIEW_ONLY`.
- Nav shell/page shell detected: yes.
- Cross-source hash uniqueness: no.
- Monitoring activation allowed: no.

DFSA cannot leave remediation based on these checks. DFSA must not be shown as ready in customer-facing UI until the exact live route/selector problem is fixed and rerun as no-save first, then saved only if strict evidence criteria pass.

## 8. Quality Gates

Completed validation:

- `python3 tools/validate_parser_quality.py` - passed.
- `python3 -m pytest product/regradar/tests/test_source_intake.py -q` - 54 passed, 5 third-party warnings.
- `python3 -m pytest product/regradar/tests/test_parser_benchmark_suite.py -q` - 21 passed.
- `cd product/regradar/web && npm run lint` - 0 errors, 1 existing TanStack/React compiler warning in `DashboardPreview.jsx`.
- `cd product/regradar/web && npm run build` - passed.
- `cd product/regradar/web && node scripts/validate-routes.mjs` - passed.
- `python3 -m compileall product/regradar` - passed.
- `python3 tools/validate_workspace.py` - passed.
- `python3 tools/validate_codex_skills.py` - passed.
- `git diff --check` - passed after whitespace cleanup.

The parser quality gate is now part of the safe release checklist. It is intentionally not a replacement for human Source Monitor, Evidence Trail, QA, and Legal review.

## 9. What We Can Claim

Approved statements:

- StatuteProof supports public source testing for technically accessible and permitted sources.
- StatuteProof shows extraction quality, evidence readiness, hashes, diffs, activation readiness, warnings, failure reasons, and remediation hints.
- No-save Source Lab checks are previews only.
- Saved evidence claims require proof artifacts.
- Monitoring activation requires activation-readiness criteria and baseline checks.
- Current UAE source pack status: 13 enabled UAE sources, 9 readiness-supported in the current registry, 4 under extraction remediation.
- DFSA remains under extraction remediation after live no-save Source Lab checks.

## 10. What We Cannot Claim

Forbidden statements:

- Perfect parsing.
- Universal parsing.
- Guaranteed parsing.
- Guaranteed compliance.
- Legal advice.
- Regulator certification.
- Official regulator partnership.
- Never-miss monitoring.
- 100 percent accuracy.
- DFSA ready or confirmed based on the current live check.
- One successful no-save test means monitoring-ready.

## 11. Remaining Limits

- DFSA routes currently return page-not-found shell text through Source Lab checks.
- DIFC remains in remediation by registry hold even though prior extraction looked meaningful.
- Evidence proof quality is still limited for some historical source records.
- WARC capture is not implemented as a first-class evidence artifact.
- Screenshot and rendered DOM evidence are not yet consistently saved.
- External timestamping is optional research, not productized.
- OCR/scanned-PDF handling is not complete.
- No 30-day stability history exists for every high-value source.
- Source-specific adapters are still needed for difficult regulator sites.
- Multi-tenant custom source storage and activation governance still need hardening before broad customer-facing use.

## 12. Path to 10/10

1. Fix DFSA route/selector discovery with live browser inspection, then rerun no-save Source Lab checks.
2. Add source-specific adapters for DFSA and other hard regulator sites.
3. Require at least two successful baseline runs before customer-visible monitoring-ready status.
4. Save rendered HTML and screenshot artifacts for JS-rendered sources.
5. Add WARC capture as optional evidence for high-value sources.
6. Add external timestamping as optional proof strengthening.
7. Improve PDF/OCR detection for scanned regulatory documents.
8. Add source-history stability dashboards and quality-drop alerts.
9. Run a 30-day UAE source pack stability period.
10. Harden multi-tenant custom source storage, audit logs, and activation approvals.
11. Collect pilot feedback from MLRO/compliance users and tighten remediation language.

## 13. Next Exact Task

Investigate the two DFSA live URLs in a browser/Playwright session to find the correct reachable pages and content selectors, then rerun the two no-save Source Lab checks only.
