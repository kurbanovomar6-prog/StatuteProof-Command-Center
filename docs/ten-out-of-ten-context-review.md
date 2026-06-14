# StatuteProof 10/10 Context Review

Date: 2026-06-14

## 1. What Exists Now

StatuteProof has a working Command Center and product implementation under `product/regradar/`.

Current real product layers:

- Python API server in `product/regradar/app/api.py`.
- Multi-user auth/session MVP in `auth.py`, `db.py`, `profile.py`, and browser-facing React auth pages.
- Source intake/parser stack in `source_intake.py`, `source_tester.py`, `scraper.py`, `extractors.py`, `providers/`, `source_quality.py`, and `source_certification.py`.
- Evidence/proof/run history in `source_runs.py`, `proof.py`, `diff.py`, and `data/source_snapshots/`.
- Alert review and weekly brief modules in `alert_review.py`, `alert_drafts.py`, `weekly_brief.py`, and `user_delivery.py`.
- Polished dark navy React website/app in `product/regradar/web/src/`.
- Source Lab UI that calls `/api/custom-sources/test` and separates no-save preview, save-for-validation, and monitoring activation.
- Plan intent/manual activation model in `plan.py`, `ChoosePlanPage.jsx`, `BillingPage.jsx`, and `SourceLabPage.jsx`.
- Parser, workspace, route, and skill validators under `tools/` and `product/regradar/web/scripts/`.

## 2. What Is Real

- `sources.json` has 13 enabled UAE sources.
- Current canonical source-readiness truth is 13 enabled / 9 readiness-supported / 4 under extraction remediation.
- Auth API can register/login/logout with server-side sessions.
- Plan selection records intent; paid plans stay pending manual activation.
- Source Lab no-save tests are real and return quality, provider, hash, warnings, evidence level, activation readiness, failure reason, and remediation hint.
- Evidence records exist locally for prior source runs.
- The first proof-backed sample brief references real VARA evidence, normalized text, hash, and diff artifacts.
- Parser quality validation and targeted parser/auth/brief tests passed in the previous P0 sprint.

## 3. What Is Sample / Demo

- Homepage evidence card and public sample brief sections are demo previews.
- `appMockData.js` powers sample alerts, sample reports, and fallback source rows.
- `EvidencePage.jsx` falls back to sample records when `GET /api/evidence` is unavailable.
- `AIBriefPage.jsx` currently shows sample brief previews and does not merge live briefs yet.
- Some app dashboard panels combine live API data with static readiness constants.
- The proof-backed sample brief is real-evidence-backed but still a `SAMPLE / FAKE DEMO` artifact, not a customer-delivered report.

## 4. What Is Roadmap

- DFSA source model migration and saved baseline.
- Founder/admin manual paid-plan activation workflow.
- Browser smoke test for auth/session/plan flow.
- API-backed Sources page as the primary mode.
- Generated canonical source-readiness summary consumed by frontend and validators.
- Rendered DOM/screenshot evidence for Playwright sources.
- WARC/external timestamping evidence options.
- Scanned-PDF/OCR-needed detection.
- Reviewed non-delivered weekly brief preview from the proof-backed VARA sample.
- Multi-workspace consultant workflow, roles, audit binder export, and production deployment hardening.

## 5. What Must Not Be Claimed

- Any website can be parsed.
- Perfect or guaranteed parsing.
- 13 validated or confirmed sources.
- DFSA ready.
- Regulator certification, regulator partnership, or official endorsement.
- Legal advice, compliance determination, or guaranteed compliance.
- Paid monitoring activated after plan selection.
- Stripe checkout or payment success.
- Sample/demo briefs as customer-ready reports.

## 6. Current Known P0 / P1 / P2 Problems

P0 / near-P0:

- DFSA remains remediation; current configured URLs/selectors are not ready.
- Browser auth/session/plan smoke is still pending.
- Source-readiness constants are duplicated and can drift again.
- The first proof-backed sample brief has not been converted into a reviewed weekly brief preview.
- No founder/admin manual activation workflow exists.

P1:

- Sources page still contains an older modal custom-source flow alongside Source Lab.
- Sources page is mostly mock/static rather than API-backed.
- Evidence page comment is stale and says no API exists.
- Registration legal acknowledgement is not persisted.
- Delivery/test-send endpoints need stronger demo-mode confirmations before customer demos.
- Rendered DOM/screenshot evidence is not saved for Playwright sources.
- PDF OCR-needed detection is not explicit.

P2:

- Internal `certification` vocabulary remains in parser/API contracts.
- Some older docs are historical and should be marked superseded before future agents rely on them.
- Deployment/hosting state is documented but not freshly verified in this pass.

## 7. Best Next Execution Path

This run should not attempt a full rewrite. The highest leverage path is:

1. Keep 13/9/4 as the canonical truth.
2. Create the 10/10 scorecard and system reviews.
3. Run focused GitHub/web research and map ideas to future tasks.
4. Run or attempt browser smoke for auth/plan if local servers cooperate.
5. Fix safe truth/copy/comment/validator/workflow gaps.
6. Do not promote DFSA or change `sources.json` without strict no-save and saved baseline evidence.
7. Validate with parser tests, build/lint/routes, workspace/skills/parser validators, and diff check.

## 8. Agents / Skills By Area

| Area | Owner agents / skills |
| --- | --- |
| Product and buyer clarity | Product Manager, `statuteproof-project-review`, `mlro-homepage-review` |
| Source readiness / DFSA | Source Monitor, `source-monitoring-review`, `custom-source-parser` |
| Evidence/proof | Evidence Trail, `evidence-readiness-review`, `evidence-audit` |
| Parser/API architecture | Code Architect, `systematic-debugging`, `test-driven-development` |
| Customer-facing copy | Legal Language, `legal-safe-copy-review`, `anti-slop-b2b-copy` |
| UX/browser smoke | QA/Critic, Product Manager, `webapp-testing` |
| Final verification | QA/Critic, Security review, `verification-before-completion` |
