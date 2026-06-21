# StatuteProof Frontend UX and Dashboard Hardening Report

Report date: 2026-06-21

## Correction: Technical UX Hardening, Not Visible Redesign

This report describes the earlier technical UX hardening sprint. It should not be read as proof that the product received a materially visible redesign.

The visible redesign pass is documented separately in:

- `docs/frontend-visible-redesign-report.md`

What changed in the earlier sprint:

- safer copy
- mobile viewport/touch improvements
- clearer helper panels
- reduced-motion guard
- unused starter asset cleanup

What did not change enough in that sprint:

- homepage first viewport composition
- auth page visual system
- source readiness page layout
- dashboard command-center feel
- mobile review/evidence experience

The later visible redesign sprint corrected that gap. Do not overclaim the earlier hardening work as a full redesign.

## 1. Starting Frontend / UX State

Preflight passed before edits. The frontend already had a credible dark RegTech visual system, legal-safe disclaimers, source transparency, Google-auth availability states, and real app surfaces for sources, evidence, review queue, reports, billing, settings, and integrations.

Starting issues found:

- Agent launch was blocked by `agent thread limit reached`; no fresh subagent packet should be claimed for this sprint.
- Public auth copy still used stronger "evidence-backed compliance briefs" phrasing than the current delivery state safely supports.
- App shell and auth pages used `h-screen` / `min-h-screen`, which is weaker on mobile browsers than `dvh`.
- Source readiness review explained source counts but did not clearly say what the review returns before the form.
- Source readiness mobile labels had touch targets that were smaller than ideal.
- Dashboard home showed many metrics, but the first operator question was not obvious: "what needs attention now?"
- Unused Vite starter artifacts remained in `src`.

## 2. Ending Frontend / UX State

The sprint shipped a narrow, verified UX hardening batch:

- Public auth and footer copy now says "hash-verified evidence" and "human review" instead of implying production-delivered evidence-backed compliance briefs.
- Source readiness review now explains the expected output: source map, fresh-alert eligible sources, evidence-library sources, known blockers, adapter/access remediation, and no legal opinion.
- Source readiness review mobile cards stack cleanly and keep regulator chips as larger touch targets.
- The app dashboard now has a "What needs attention now" operator panel before the profile and metrics grid.
- App shell, sidebar, auth, onboarding, pricing, and legal pages now use `dvh`-safe viewport sizing where touched.
- Global reduced-motion handling was added.
- Unused `App.css`, `react.svg`, and `vite.svg` were removed.

## 3. Agents Launched

Fresh agent launch attempted:

- Product Manager subagent: failed with `agent thread limit reached`.

No additional fresh agents were launched after the runtime blocker. Codex proceeded with locally verified checks rather than inventing agent packets.

## 4. References Reviewed

Read-only references:

- Local `design-taste-frontend` skill: applied trust-first regulated B2B design read, restrained motion, anti-generic SaaS rules.
- Local `ui-ux-pro-max` skill: applied accessibility, touch target, responsive layout, reduced motion, form feedback, and dashboard usability rules.
- `https://github.com/leonxlnx/taste-skill`: reviewed read-only as external design reference.
- `https://github.com/nextlevelbuilder/ui-ux-pro-max-skill`: reviewed read-only as external UI/UX reference.
- YouTube motion-site reference was not reliably reviewed during this earlier hardening sprint. In the later visible redesign sprint, metadata and Russian subtitles were retrieved with `yt-dlp`, but full frame-by-frame review was still not performed.

No external package was installed.

## 5. Bugs Found

- Mobile viewport sizing used `screen` units in multiple shell/auth surfaces.
- Public auth/footer copy risked overstating evidence-backed brief delivery.
- Source readiness form needed clearer pre-form expectation setting.
- Source readiness mobile select became too long during the first pass and was corrected by moving MLRO/CCO definitions into helper text.
- Unused starter assets were present.
- Auth bootstrap produces expected unauthenticated `401` network console entries when API is mocked as unauthenticated; no frontend page error was found.

## 6. Bugs Fixed

- Replaced touched `h-screen` / `min-h-screen` shells with `h-dvh` / `min-h-dvh`.
- Added `prefers-reduced-motion` CSS handling.
- Removed unused starter CSS and SVG files.
- Corrected source readiness mobile select copy after screenshot review.
- Added larger touch targets on sidebar, topbar, auth buttons, and source-readiness regulator chips.

## 7. Trash / Dead Code Removed

Removed:

- `product/regradar/web/src/App.css`
- `product/regradar/web/src/assets/react.svg`
- `product/regradar/web/src/assets/vite.svg`

These had no references in `product/regradar/web/src`.

## 8. Public Site Improvements

- Footer language now avoids implying delivered evidence-backed compliance briefs.
- Legal page opening wording now says official-source monitoring intelligence, hash-verified source evidence, and review-support summaries.
- Landing page viewport wrapper uses `dvh` where touched.

## 9. Auth Page Improvements

- Login/register left-panel claim now emphasizes hash-verified evidence and human review.
- Login/register subcopy now describes source monitoring, canonical evidence records, and draft brief workflows more accurately.
- Disabled password reset is now static explanatory text instead of a dead disabled button.
- Auth layout uses `dvh` and scroll-safe right panel spacing.
- Google auth button remains env-gated and no secrets are exposed.

## 10. Source Readiness Review Improvements

- Added a pre-form "What this review returns" panel.
- Added explicit wording that selected regulators do not mean complete regulator coverage.
- Added MLRO/CCO helper text without overloading mobile select labels.
- Stacked source-count tiles on mobile.
- Increased regulator chip touch targets.

## 11. Dashboard Improvements

- Added "What needs attention now" as a task-first operator panel:
  - source-health flags
  - changes needing review
  - coverage limits
  - brief delivery gate
- The panel routes users to the relevant surfaces rather than leaving them to infer from metrics.
- Dashboard language keeps operator tasks separate from customer-facing conclusions.

## 12. Evidence / Review UI Improvements

No evidence workflow logic was changed. The dashboard now points users toward review queue and evidence gates more clearly.

## 13. Mobile Improvements

Checked at mobile width 390px:

- Login: no horizontal overflow.
- Source readiness review: no horizontal overflow; select copy fixed after screenshot review.
- Dashboard with mocked authenticated API: no horizontal overflow.

## 14. Motion Improvements

No new animation dependency was added.

Implemented:

- Global reduced-motion guard.
- Existing transitions remain short and restrained.

Not implemented:

- No decorative parallax, no heavy dashboard motion, no motion-video imitation.

## 15. Legal / Copy Changes

Changed unsafe or potentially premature wording:

- "evidence-backed compliance briefs" -> "hash-verified evidence and human review" in auth.
- Footer now says "hash-verified evidence records and human-review workflows."
- Legal copy now says "hash-verified source evidence" and "review-support summaries."

Claims explicitly not made:

- complete UAE coverage
- legal advice
- guaranteed compliance
- perfect parsing
- never-miss updates
- all-source coverage
- regulator certification
- production-delivered evidence-backed briefs

## 16. Screenshots Reviewed

Saved outside the repo under `/tmp/statuteproof-ui-screens/`:

- `login-desktop-1440-clean.png`
- `login-mobile-390-clean.png`
- `source-readiness-desktop-1440-clean.png`
- `source-readiness-mobile-390-clean.png`
- `source-readiness-mobile-390-final.png`
- `dashboard-desktop-mocked-1440-clean.png`
- `dashboard-mobile-mocked-390-clean.png`

Dashboard screenshots used mocked API responses only for visual QA. No fake data was saved to the product.

## 17. Validation Results

Focused validation during the sprint:

- `npm run build`: pass
- `npm run lint`: pass with existing non-blocking TanStack React Compiler warning in `DashboardPreview.jsx`
- `node scripts/validate-routes.mjs`: pass
- Browser/Playwright visual checks: no horizontal overflow on checked desktop/mobile pages

Final full validation is recorded in the final response for this task.

## 18. Frontend Validation Result

Frontend validation passed in focused runs. The existing TanStack Table lint warning remains unchanged and non-blocking.

## 19. Remaining Blockers

- Fresh subagent launch blocked by thread limit; no autonomous agent council packets were produced.
- This was fixed in the later visible redesign sprint by skipping protected auth bootstrap on public/auth routes.
- Dashboard visual QA for authenticated state used mocked API responses because no real local authenticated session was created in this sprint.
- Larger dashboard IA work remains: source health remediation drilldown, evidence chain timeline, and a clearer "brief blocked because..." path.

## 20. Next Exact Design Task

Create a dedicated evidence chain component for the dashboard and review queue:

`source run -> canonical evidence -> review decision -> alert link -> draft brief -> delivery gate`

It should be usable on mobile without horizontal tables.

## 21. Next Exact Product Task

Define the first-login operator journey:

1. review source map
2. inspect source-health flags
3. approve or reject canonical evidence
4. inspect blocked/draft brief state
5. configure delivery only after gates pass

## 22. Next Exact Technical Debt Task

Reduce the authenticated dashboard's dependence on wide tables by adding mobile card views for:

- Sources
- Review Queue
- Evidence Records
- Reports
