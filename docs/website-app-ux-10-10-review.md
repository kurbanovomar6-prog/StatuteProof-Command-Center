# Website And App UX 10/10 Review

Date: 2026-06-14

## Executive UX Verdict

The public site and app now look credible for a serious compliance SaaS. The visual direction is dark navy, evidence-first, and MLRO-focused. The biggest UX risk is not visual polish; it is truth boundaries: users must always know whether they are seeing live API data, static readiness framing, sample/demo content, or roadmap capability.

## Page Scores

| Surface | Score | Notes |
| --- | ---: | --- |
| Homepage hero | 8.8 | Strong proof-first headline, current 13/9/4 count, clear CTA. Sample visual is clearly labeled. |
| Source coverage | 8.5 | Separates readiness-supported, remediation, constrained, blocked, and under-validation. Good honesty. |
| Pricing page | 8.5 | Manual activation and no-payment language are clear. UAE Monitor is correctly framed as 13 enabled / 9 readiness-supported / 4 remediation. |
| Login/register | 8.0 | Premium visual style and legal boundaries. Registration acknowledgement is UI-only, not persisted. |
| Dashboard | 8.0 | Clear readiness banner and next actions. Mixes live source status with static readiness constants. |
| Sources page | 7.2 | Good readiness labels, but still has a legacy custom-source modal and mostly static source map rows. |
| Source Lab | 8.5 | Strongest product screen. No-save, evidence, baseline, remediation, and activation are mostly clear. |
| Evidence page | 7.6 | Falls back to clearly labeled sample data and uses live endpoint when available. Header comment is stale. |
| Brief previews | 7.4 | Sample/demo labels are clear. Needs real reviewed non-delivered weekly preview. |
| Billing/settings | 7.8 | Plan intent vs active plan is clearer. Founder/admin activation workflow is missing. |

## Bugs Found

| ID | Severity | Problem | Evidence | Safe fix now |
| --- | --- | --- | --- | --- |
| UX-001 | P1 | Evidence page header comment says no `/api/evidence` endpoint exists. | `EvidencePage.jsx` fetches `/api/evidence?market=AE`; API implements `_handle_evidence_list`. | Yes, comment-only. |
| UX-002 | P1 | Sources page still contains a smaller legacy custom-source modal alongside Source Lab. | `SourcesPage.jsx` fallback opens modal if `onAddCustomSource` absent; AppShell routes button to Source Lab. | Defer removal; primary app path is safe. |
| UX-003 | P1 | Sources page uses static mock rows as primary source map. | `MOCK_SOURCES` import and filtering. | Defer API-backed table; document. |
| UX-004 | P1 | Dashboard readiness constants are duplicated. | `SOURCE_READINESS_SUMMARY` in `DashboardHome.jsx`; also source tables and pricing. | Add future canonical summary; do not broad refactor now unless small. |
| UX-005 | P1 | Browser auth/plan smoke has not been run in this task yet. | P0 report says browser smoke pending. | Attempt local smoke. |

## Copy Issues

- Active UI copy is mostly safe: no "13 validated sources", no universal parsing, no guaranteed compliance, no DFSA-ready claim.
- `SourceLabPage.jsx` still contains internal keys such as `MONITORING_CERTIFIED` and `CERTIFICATION_FAILED`, but display labels map these to "Monitoring ready" and "Activation readiness failed". This is acceptable for now.
- Sample/demo copy is frequent and visible. This protects trust, though it also reminds us that a real reviewed weekly preview is still needed.

## Button / Routing Issues

- Public Login, Register, Pricing, and Source Readiness Review routes exist.
- `/app/sources/new` maps to `/app/source-lab`.
- AppShell `Add custom source` opens Source Lab, not the legacy modal.
- Disabled buttons use clear titles for password reset, Google OAuth, activation, delivery, and export.
- A browser smoke is still required to verify redirects/cookies/end-to-end.

## Quick Wins

1. Fix EvidencePage stale header comment.
2. Create browser auth/plan smoke report.
3. Add pre-demo workflow so sample/live boundaries are checked before demos.
4. Add first paid pilot readiness workflow.
5. Track API-backed Sources page and canonical source summary as next implementation tasks.

## P0 / P1 / P2 UX Actions

P0:

- Run browser smoke before prospect demo.
- Keep 13/9/4 source truth everywhere.

P1:

- Make Sources page API-backed by default.
- Persist registration legal acknowledgement.
- Convert proof-backed sample into reviewed non-delivered weekly preview.
- Add founder/admin plan activation.

P2:

- Add rendered DOM/screenshot evidence display for JS sources.
- Add audit binder export design.
- Add customer-facing source readiness portal with current limitations and proof links.

## Agents / Skills Applied

- Product Manager: checked buyer clarity and next action.
- QA/Critic: checked labels, buttons, sample/demo boundaries.
- Legal Language: checked legal-safe claims.
- Source Monitor: checked source-readiness truth and DFSA status.
- `mlro-homepage-review`, `legal-safe-copy-review`, `webapp-testing`, and `verification-before-completion` were applied conceptually.
