# StatuteProof 10/10 Execution Plan

Date: 2026-06-14

## 1. Current State Summary

Latest clean-state gate:

- `git status --short`: clean.
- `git diff --stat`: no diff.
- Latest commit: `64eea4f fix: resolve StatuteProof P0 readiness blockers`.

Current known project state:

- Visual/site upgrade completed and pushed.
- Parser/agent/source-intake strengthening completed and pushed.
- Mega-audit and P0 sprint completed and pushed.
- Source-readiness truth is **13 enabled UAE sources, 9 readiness-supported, 4 under extraction remediation**.
- DFSA model is decided in docs, but DFSA remains remediation.
- First proof-backed sample brief exists and is labeled sample/demo.
- Auth/session cookie behavior is fixed at focused-test level; browser smoke remains pending.
- Plan intent/manual activation is fixed at API/UI level; founder/admin activation workflow remains pending.

## 2. What 10/10 Means For StatuteProof

10/10 means the product is honest, comprehensible, and operationally disciplined:

- The product never lies about source readiness, evidence, activation, billing, or legal/compliance outcomes.
- The UI is premium and makes the next action obvious for an MLRO or compliance lead.
- Source Lab separates preview, evidence, and monitoring activation.
- Parser failures are explicit and useful.
- Evidence-backed claims require proof artifacts.
- Sample/demo content is unmistakably labeled.
- Risk/brief outputs remain human-reviewed and not legal advice.
- Tests and validators block unsafe claims and broken critical flows.
- Agents/skills/workflows prevent regressions.

## 3. What Cannot Honestly Be 10/10 Yet

- DFSA cannot be readiness-supported until model migration, no-save checks, saved evidence, and baseline gates pass.
- Broad parser robustness cannot be proven without a larger benchmark corpus and live history.
- Evidence is not enterprise-grade until rendered DOM/screenshot/WARC/external timestamp options and stronger artifact validation exist.
- Paid billing is not self-serve; it must remain manual until founder/admin activation, audit log, and Stripe readiness are built.
- Browser auth is not fully proven until API + Vite smoke runs.
- Customer/pilot readiness cannot be 10/10 before live pilot feedback and 30-day source stability history.

## 4. Highest-Leverage Tasks For This Run

1. Verify current truth and UX surfaces after the P0 sprint.
2. Run a full website/app/source-lab/parser/evidence/security/agent review and document precise 10/10 gaps.
3. Use GitHub/internet research to identify practical ideas, not blindly add dependencies.
4. Run browser auth/plan smoke if safely possible.
5. Harden validators/tests for high-risk honesty regressions if clear and scoped.
6. Create missing workflows for pre-demo, first paid pilot, source baseline/evidence save, and safe GitHub adoption.
7. Implement only localized P0/P1 fixes that have clear evidence and validation.

## 5. Agents / Skills / Tools To Use

Conceptual agent gates:

- Product Manager: MLRO problem, next action, demo/pilot readiness.
- Code Architect: small safe implementation choices.
- Source Monitor: source readiness, DFSA/remediation truth.
- Evidence Trail: proof-backed claims and sample brief evidence.
- QA / Critic: broken routes, sample labels, validation gaps.
- Legal Language: no legal advice, guarantees, regulator certification, or unsafe copy.
- Risk + Brief Pipeline: proof-backed sample brief boundaries.
- ICP Lead Research / Outreach Writer: only if copy/customer-facing positioning is touched.

Repo skills used:

- `statuteproof-project-review`
- `source-monitoring-review`
- `evidence-readiness-review`
- `custom-source-parser`
- `legal-safe-copy-review`
- `webapp-testing`
- `test-driven-development`
- `verification-before-completion`
- `prompt-injection-review` if agent/skill changes are made.

Tools:

- Shell/rg/sed for local inspection.
- Web search for GitHub/open-source research.
- Playwright/browser smoke only if available and safe.
- Existing validators and targeted tests.

## 6. Files To Inspect

Root and routing:

- `README.md`, `START_HERE.md`, `CLAUDE.md`, `AGENTS.md`, `TOOL_ROUTER.md`, `STATUTEPROOF_CONTEXT.md`, `CHANGELOG.md`, `.gitignore`

Recent reports:

- P0 sprint reports, source readiness reports, DFSA reports, mega-audit reports, parser reports, visual reports, pricing reports, parser quality gates.

Backend:

- `product/regradar/app/`
- `product/regradar/run.py`
- `product/regradar/sources.json`
- `product/regradar/requirements.txt`
- `product/regradar/tests/`

Frontend:

- `product/regradar/web/src/`
- `product/regradar/web/package.json`
- `product/regradar/web/scripts/`
- `product/regradar/web/vite.config.js`

Agents/skills/workflows:

- `agents/`, `.agents/skills/`, `skills/`, `workflows/`, `prompts/`

## 7. Files Likely To Change

Expected docs:

- `docs/ten-out-of-ten-agent-tool-use-plan.md`
- `docs/ten-out-of-ten-context-review.md`
- `docs/ten-out-of-ten-scorecard.md`
- `docs/website-app-ux-10-10-review.md`
- `docs/parser-source-lab-10-10-review.md`
- `docs/ten-out-of-ten-github-research.md`
- `docs/dfsa-10-10-remediation-plan.md`
- `docs/dfsa-10-10-remediation-report.md`
- `docs/proof-backed-sample-brief-10-10-qa.md`
- `docs/browser-auth-plan-smoke-report.md`
- `docs/billing-manual-activation-10-10-review.md`
- `docs/security-data-hygiene-10-10-review.md`
- `docs/test-validator-10-10-upgrade-report.md`
- `docs/agents-workflows-10-10-review.md`
- `docs/ten-out-of-ten-final-gate-review.md`
- `docs/ten-out-of-ten-execution-final-report.md`

Possible workflow docs:

- `workflows/09-pre-demo-readiness-gate.md`
- `workflows/10-first-paid-pilot-readiness.md`
- `workflows/11-source-baseline-and-evidence-save.md`
- `workflows/12-github-research-and-safe-adoption.md`

Possible code/tests only if safe:

- `tools/validate_parser_quality.py`
- `tools/validate_workspace.py`
- `product/regradar/tests/`
- Small frontend/API fixes if a concrete bug is found.

## 8. Validation Plan

From project root:

- `git status --short`
- `python3 -m compileall product/regradar`
- Targeted parser/auth/brief tests affected by the run.
- `python3 tools/validate_parser_quality.py`
- `python3 tools/validate_workspace.py`
- `python3 tools/validate_codex_skills.py`
- `git diff --check`

From frontend if touched:

- `npm run build`
- `npm run lint`
- `node scripts/validate-routes.mjs`

Browser smoke if possible:

- API + frontend local smoke for login/register/dashboard/logout/plan intent.

## 9. GitHub / Open-Source Research Plan

Use web search, not dependency installation, to evaluate:

- change detection systems;
- regulatory/source monitoring patterns;
- source health dashboards;
- Playwright extraction practices;
- main-content extraction libraries;
- WARC/screenshot evidence;
- PDF/document extraction;
- parser quality scoring;
- compliance SaaS UX;
- manual activation/pilot billing flows.

Known references include changedetection.io, ArchiveBox, Browsertrix, shot-scraper, Playwright, Crawlee, Scrapy, trafilatura, selectolax, PyMuPDF, pdfplumber, warcio, OpenTimestamps, MarkItDown, Unstructured, Docling, Crawl4AI, Firecrawl, and browser-use.

No code will be copied without license review and attribution. Prefer independent implementation of ideas.

## 10. Commit Plan

If validation passes and safe fixes are made:

`git commit -m "fix: improve StatuteProof 10-10 readiness blockers"`

If mostly docs/reports/workflows are made:

`git commit -m "docs: add StatuteProof 10-10 readiness plan"`

Stage only files from this task. Do not stage runtime data, reference repos, secrets, `.env`, source snapshots, or unrelated changes.

## 11. What This Task Will Not Touch

- No deployment.
- No Cloudflare or DigitalOcean changes.
- No broad/all-source monitoring.
- No customer delivery or Telegram/email send.
- No live Stripe or fake payment success.
- No source readiness promotion without evidence.
- No DFSA readiness claim unless strict gates pass.
- No major parser rewrite or large dependency install.
- No 11th active agent.
- No private/login/CAPTCHA/paywall bypass.
