# StatuteProof Premium Visual Upgrade Report

Date: 2026-06-14

## What Changed

StatuteProof was upgraded from a mixed early-stage SaaS UI into a darker, more coherent compliance product surface. The work focused on visual polish, honest source-readiness language, safer sample/demo labeling, and route/CTA correctness across the public website and authenticated app.

## Pages Upgraded

- Homepage
- Pricing
- Source readiness review
- Login
- Register
- Dashboard
- Public evidence/demo section
- Public dashboard preview
- Sources
- Source Lab
- Evidence
- Brief previews
- Billing
- Settings label normalization
- Legal pages for terms/privacy/disclaimer

## Design System Changes

- Refined global dark navy background, surface, elevated card, border, text, cyan accent, success, warning, danger, and quality/status styling.
- Added reusable product UI classes for buttons, panels, badges, mono text, and tables.
- Tightened typography, spacing, borders, focus states, inputs, cards, badges, tables, and app shell surfaces.
- Preserved the current StatuteProof logo and octopus mark.

## Button And Routing Fixes

- Added route mapping for required public and app paths.
- Login routes to `/login`.
- Register routes to `/register`.
- Request Source Review routes to `/source-readiness-review`.
- Start Founding Pilot routes to `/register?plan=founding_pilot`.
- Upgrade to UAE Monitor routes to `/register?plan=uae_monitor`.
- Add custom source routes to `/app/source-lab`.
- Sources, Source Lab, Evidence, Billing, Settings, and dashboard app routes now update browser history.
- Authenticated `/login` and `/register` visits redirect to `/app/dashboard`.
- Unauthenticated app routes redirect to `/login`.

## Visual QA Result

- Sites used: no, unavailable in this environment.
- Hosted Sites preview URL: not available.
- Local preview URL: `http://127.0.0.1:5174/`
- Desktop QA completed for homepage, pricing, source readiness review, login, register, dashboard, sources, source lab, evidence, briefs, and billing.
- Parser/source registry follow-up now supersedes the earlier source-count wording: public source-readiness surfaces should show 13 enabled, 9 readiness-supported, and 4 under extraction remediation.
- Public dashboard-preview source counts are static sample/readiness-pack counts, not raw API totals.
- Authenticated source-map mock data now uses the same canonical 13-source model, with DFSA Rulebook, DFSA Regulatory Notices, and UAE FIU Homepage marked as remediation/review.
- Public source-matrix, source-pack, sample-report, and alert-profile copy now separate DIFC Laws readiness from DFSA remediation and UAE FIU homepage remediation.
- Readiness-supported source identities were corrected against the registry: UAE Ministry of Finance and UAE FIU Circulars are shown as readiness-supported; disabled aliases CBUAE Circulars and ADGM FSRA Rules are not shown as ready.
- ADGM/FSRA copy now treats the main ADGM/FSRA source as readiness-supported with caveats while keeping FSRA rulebook/circular layers outside readiness-supported scope until readiness checks clear.
- Source registry statuses, generated/static readiness reports, metadata, and public samples now align to 13 enabled UAE sources, 9 readiness-supported, and 4 under extraction remediation.
- Mobile viewport QA was not feasible because the in-app browser exposed no viewport resize capability.

## Gate Results

- Legal Language: PASS.
- QA / Critic: PASS.
- Source Monitor: PASS.

## Validation Results

Initial validation after implementation:

- `node scripts/validate-routes.mjs` - passed
- `npm run lint` - passed with one existing TanStack Table React compiler warning in `DashboardPreview.jsx`
- `npm run build` - passed
- `python3 -m compileall product/regradar` - passed
- `python3 tools/validate_workspace.py` - passed
- `python3 tools/validate_codex_skills.py` - passed

Final validation after the last auth-route and report-doc patches:

- `node scripts/validate-routes.mjs` - passed
- `npm run lint` - passed with one existing TanStack Table React compiler warning in `DashboardPreview.jsx`
- `npm run build` - passed
- `python3 -m compileall product/regradar` - passed
- `python3 tools/validate_workspace.py` - passed
- `python3 tools/validate_codex_skills.py` - passed
- `git diff --check` - passed

Final validation after the public source-readiness table and dashboard-preview fixes:

- `node scripts/validate-routes.mjs` - passed
- `npm run lint` - passed with the same existing TanStack Table React compiler warning in `DashboardPreview.jsx`
- `npm run build` - passed
- `python3 -m compileall product/regradar` - passed
- `python3 tools/validate_workspace.py` - passed
- `python3 tools/validate_codex_skills.py` - passed
- `git diff --check` - passed
- Browser retest confirmed no stale source readiness count, no old DFSA/UAE FIU confirmed demo rows, and no light cards in the corrected public evidence/source readiness components.
- Source readiness lists were aligned across `Coverage.jsx`, `SourceCoverageTable.jsx`, `DashboardPreview.jsx`, and `mockData.js` to one canonical 13-source model.
- Final source-claim scan found no UI-code matches for stale readiness counts, disabled aliases (`CBUAE Circulars`, `ADGM FSRA Rules`), DFSA confirmed overclaims, or UAE FIU Homepage confirmed overclaims.
- Browser retest should confirm the homepage and `/app/sources` render UAE Ministry of Finance and UAE FIU Circulars as readiness-supported identities, omit disabled aliases, and keep DFSA Rulebook, DFSA Regulatory Notices, DIFC Laws, and UAE FIU Homepage as `Needs remediation` / `Review`.

Final validation after gate-blocker fixes:

- `npm run lint` - passed with 0 errors and the known TanStack Table React compiler warning in `DashboardPreview.jsx`.
- `npm run build` - passed.
- `node scripts/validate-routes.mjs` - passed.
- `python -m compileall product/regradar` - could not run because `python` is not installed.
- `python3 -m compileall product/regradar` - passed.
- `python3 tools/validate_workspace.py` - passed.
- `python3 tools/validate_codex_skills.py` - passed.
- `git diff --check` - passed.

## Remaining Visual Issues

- Run a mobile/device-emulation review before replacing the production site.
- Older secondary app areas can receive a follow-up polish review: Integrations, Sample Alerts, Source Reports, and Settings internals.
- App screenshot artifacts were not committed because the in-app browser runtime could inspect screenshots but could not write screenshot files to the workspace.
- Sites preview was unavailable; no production deploy, Cloudflare change, or DigitalOcean change was made.

## Next Exact Task

DFSA live Playwright verification outside sandbox.
