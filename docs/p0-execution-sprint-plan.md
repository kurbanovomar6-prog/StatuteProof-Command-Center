# P0 Execution Sprint Plan

Date: 2026-06-14

## 1. P0 Blockers

| Blocker | Current state | Sprint decision |
| --- | --- | --- |
| Source-readiness truth mismatch | The mega-audit found a conflict between 13/10/3 business wording and the committed registry/docs/frontend truth of 13 enabled, 9 readiness-supported, 4 remediation. | Resolve to the evidence-backed truth unless a reviewed source can leave remediation. DIFC remains held, so the safe truth is 13/9/4. |
| DFSA source model ambiguity | Current DFSA URLs fail strict checks; deeper rulebook and AML/MLRO candidates passed no-save extraction but are not saved/baselined. | Document an exact source model. Do not mark DFSA ready or edit readiness counts. |
| First proof-backed demo brief | Public/app screens are labeled as sample/demo, but no deliberate real proof-backed demo brief is established for customer demos. | Create a clearly labeled sample/demo brief only if a real proof/run record and proof artifact are available. Otherwise create a blocker report. |
| Auth/session browser behavior | API cookies are `Secure`, while local Vite proxy is HTTP, risking local login/register failure. | Fix local/prod cookie behavior if safe and add focused validation. |
| Plan intent vs manual activation | Paid plan selection records intent but plan state can read as active, stronger than manual activation reality. | Separate requested plan from activation wording/status where safe. No checkout or paid activation. |

## 2. Fixes In This Sprint

- Reconcile the customer-facing source-readiness truth to one canonical statement.
- Decide the DFSA source model in documentation without promoting unbaselined DFSA sources.
- Create a proof-backed sample brief or a precise blocker report.
- Fix safe auth/session behavior for local browser testing while keeping production secure by default.
- Fix paid plan intent semantics so selected paid plans remain pending manual activation.
- Update the bug register, roadmap, mega-audit final report, and create a final sprint report.

## 3. Only Documented In This Sprint

- Full DFSA evidence baseline and source registry promotion.
- Broad parser rewrite, WARC/screenshot evidence, OCR/scanned PDF detection.
- Multi-tenant billing/admin console.
- Production deployment, Cloudflare, DigitalOcean, or live source monitoring.

## 4. Files To Change

Planned docs:

- `docs/source-readiness-truth-reconciliation-report.md`
- `docs/dfsa-source-model-decision.md`
- `docs/first-proof-backed-sample-brief-report.md`
- `docs/samples/first-proof-backed-sample-brief.md` if evidence is suitable
- `docs/auth-session-verification-report.md`
- `docs/plan-intent-manual-activation-report.md`
- `docs/bug-and-logic-error-register.md`
- `docs/next-30-actions-roadmap.md`
- `docs/statuteproof-mega-audit-final-report.md`
- `docs/p0-execution-sprint-final-report.md`

Possible code/tests:

- `product/regradar/app/api.py`
- `product/regradar/app/plan.py`
- `product/regradar/web/src/components/app/BillingPage.jsx`
- `product/regradar/web/src/components/app/ChoosePlanPage.jsx`
- `product/regradar/tests/`

Files not planned for update unless strict evidence supports it:

- `product/regradar/sources.json`

## 5. Validation Commands

- `git status --short`
- `python -m compileall product/regradar` if available
- `python3 -m compileall product/regradar`
- Targeted Python tests for changed parser/auth/plan/brief behavior
- `python3 tools/validate_parser_quality.py`
- `npm run build` in `product/regradar/web` if frontend code changes
- `npm run lint` in `product/regradar/web` if frontend code changes
- `node product/regradar/web/scripts/validate-routes.mjs`
- `python3 tools/validate_workspace.py`
- `python3 tools/validate_codex_skills.py`
- `git diff --check`

## 6. Commit Plan

If validation passes, stage only files changed by this P0 sprint and commit:

`fix: resolve StatuteProof P0 readiness blockers`

If only docs are changed, commit:

`docs: reconcile StatuteProof P0 readiness plan`

No runtime data, source snapshots, alert queue JSON, reference repositories, `.env`, credentials, or unrelated files will be staged.

## 7. What This Sprint Will Not Touch

- No deployment.
- No Cloudflare or DigitalOcean changes.
- No broad monitoring or all-source runs.
- No Telegram/email/customer delivery.
- No DFSA promotion to ready without saved evidence and baseline.
- No claim that StatuteProof parses any website, guarantees compliance, or provides legal advice.
- No automatic paid plan activation or fake checkout success.
