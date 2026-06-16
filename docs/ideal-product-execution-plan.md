# Ideal Product Execution Plan

Date: 2026-06-16

## Current State

StatuteProof is at the current honest UAE source truth:

- 66 enabled UAE sources
- 62 readiness-supported UAE sources
- 4 sources under extraction remediation

The source-health timeline and review-history MVP is implemented. Acknowledge & Assess exists for saved evidence records only. Audit export exists as Markdown/HTML. Email delivery is safe test-mode/local outbox only. Real production email and real PDF export are not implemented and must not be claimed.

## Validated Issues From The Claude Master Plan

The Claude master plan identifies trust-killing prototype surfaces that are still more commercially urgent than adding more sources:

1. Authenticated pages still depend on mock alert/report/brief data.
2. Dashboard source counts are hardcoded instead of API-driven.
3. Plan/pricing capability metadata is inconsistent with the current 62-source readiness-supported product story.
4. Onboarding does not disclose source readiness by regulatory body before plan choice.
5. There is no global MLRO Review Queue to manage pending and assessed evidence records.
6. PDF export and production email delivery are not ready and should remain honestly framed.

## Execution Order

1. Remove unauthenticated-looking mock data from authenticated app pages:
   - `AlertsPage.jsx`
   - `ReportsPage.jsx`
   - `AIBriefPage.jsx`
   - sidebar/routing labels if needed
2. Add an API-backed `/api/sources/summary` endpoint and drive dashboard source truth from it.
3. Reconcile backend and frontend plan/pricing capability metadata around the actual $199 / $399 / custom product.
4. Add source readiness preview to onboarding so buyer expectations are set before plan selection.
5. Build the Global Review Queue:
   - backend `/api/reviews/queue`
   - frontend `ReviewQueuePage.jsx`
   - route/sidebar entry
   - tests and validator
6. Keep PDF as Markdown/HTML unless Playwright PDF can be added safely without new fragile dependencies.
7. Keep production email in safe test-mode unless a provider abstraction can be added without sending external email.

## Files Likely To Change

- `product/regradar/app/api.py`
- `product/regradar/app/plan.py`
- `product/regradar/app/source_health_timeline.py` or a new review queue helper if needed
- `product/regradar/web/src/api.js`
- `product/regradar/web/src/components/app/AlertsPage.jsx`
- `product/regradar/web/src/components/app/ReportsPage.jsx`
- `product/regradar/web/src/components/app/AIBriefPage.jsx`
- `product/regradar/web/src/components/app/DashboardHome.jsx`
- `product/regradar/web/src/components/app/OnboardingPage.jsx`
- `product/regradar/web/src/components/app/AppSidebar.jsx`
- `product/regradar/web/src/components/app/AppShell.jsx`
- `product/regradar/web/src/routeMap.js`
- `product/regradar/web/src/data/planCapabilities.js`
- `product/regradar/web/src/components/PricingPage.jsx`
- `product/regradar/web/src/components/app/BillingPage.jsx`
- `product/regradar/web/src/components/app/ChoosePlanPage.jsx`
- `product/regradar/web/src/components/app/PlanBanner.jsx`
- `product/regradar/tests/`
- `tools/validate_no_authenticated_mock_data.py`
- `tools/validate_plan_pricing_consistency.py`
- `tools/validate_review_queue.py`
- `docs/ideal-product-execution-final-report.md`

## What Will Remain Future Work

- Real production email delivery.
- Real PDF export if Playwright PDF generation is not already safe in the local stack.
- VARA source-depth expansion.
- DIFC remediation.
- Multi-user, RBAC, SSO, enterprise procurement features.
- 7/30/90-day source health trend charts.
- Bulk acknowledge/assess workflow.

## Validation Plan

Run backend, validator, and frontend checks after implementation:

- `python3 -m compileall product/regradar`
- `python3 -m pytest product/regradar/tests -q`
- `python3 tools/validate_no_authenticated_mock_data.py`
- `python3 tools/validate_plan_pricing_consistency.py`
- `python3 tools/validate_review_queue.py`
- `python3 tools/validate_source_health_timeline.py`
- `python3 tools/validate_mvp_trust_workflow.py`
- `python3 tools/validate_uae_source_pack.py`
- `python3 tools/validate_uae_50_working_sources.py`
- `python3 tools/validate_parser_quality.py`
- `python3 tools/validate_workspace.py`
- `python3 tools/validate_codex_skills.py`
- `git diff --check`
- `npm run build`
- `npm run lint`
- `node scripts/validate-routes.mjs`
- `node scripts/pre-demo-smoke.mjs` if present

## Commit Policy

Only stage files changed for this task. Do not stage runtime junk, secrets, or unrelated files. Commit only after validation passes:

`feat: execute ideal product trust workflow plan`

Push to `origin/main`.
