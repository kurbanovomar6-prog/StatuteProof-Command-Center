# Design Sprint 3 — Client Workspace Trust Polish

## 1. Verdict

Implemented logged-in workspace trust polish without touching backend auth, profile persistence, Telegram backend, source monitoring, pricing, deployment, secrets, or source activation.

The workspace now reads as a founding pilot client workspace with source-readiness and profile setup context, rather than a demo dashboard with fake live status.

## 2. Files changed

- `web/src/App.jsx`
- `web/src/components/app/AppShell.jsx`
- `web/src/components/app/AppSidebar.jsx`
- `web/src/components/app/AppTopbar.jsx`
- `web/src/components/app/DashboardHome.jsx`
- `web/src/components/app/IntegrationsPage.jsx`
- `web/src/components/app/SettingsPage.jsx`
- `web/src/components/app/SourcesPage.jsx`
- `web/src/data/workspaceProfile.js`
- `reports/design_sprint_3_client_workspace_polish.md`

## 3. Workspace trust improvements

- Removed visible dashboard/topbar framing that implied fake live monitoring status.
- Replaced `Demo Workspace` fallback language with `Profile workspace`.
- Added authenticated account context to the app shell so sidebar/topbar can use the current user when available.
- Sidebar now shows company/account context, `Founding pilot`, and source-map setup state.
- Topbar now shows profile workspace context and source-validation framing instead of fake last-check/test-alert controls.

## 4. Dashboard/profile improvements

- Reworked dashboard home into a pilot workspace overview.
- Added profile-aware header with company, selected markets, and regulatory profile.
- Added `Pilot setup checklist`:
  - Account created
  - Profile saved
  - Telegram connected
  - Source map reviewed
  - First reviewed brief
- Sample signals and sample brief content are clearly labeled as previews, not live customer alerts.

## 5. Telegram UX polish

- Dashboard checklist reads real Telegram connection status from the Auth C pairing API.
- Integrations copy now says personalized alert delivery is configured in the next pilot step.
- No claim was added that production alerts, weekly briefs, or personalized delivery are active.

## 6. Source readiness improvements

- Added dashboard source-readiness card with safe status badges:
  - Validated
  - Under validation
  - Needs adapter
  - Limited
- Sources page now reads as a source-map workspace.
- Source additions are framed as validation requests, not production activation.
- Existing `Active` mock source status is displayed as `Validated` in the workspace UI.

## 7. Claims safety result

No fake live data was added.

No claims were added for:

- personalized delivery being active;
- production delivery being active;
- real-time alerts;
- complete UAE coverage;
- guaranteed compliance;
- all UAE regulators.

The required unsafe-claims grep returned pre-existing `legal advice` disclaimer phrases in files not introduced by this sprint. This sprint did not add those claims, and the edited Settings disclaimer was changed to avoid that phrase.

## 8. What was deliberately not changed

- Auth D personalized delivery was not implemented.
- Backend/auth/profile persistence code was not touched.
- Telegram backend and Telegram secrets were not touched.
- Source monitoring behavior was not changed.
- `sources.json` was not touched.
- Pricing and landing components were not changed.
- No fake live alerts or fake client data were added.

## 9. Validation result

Validation performed:

- `cd web && npm run build` passed.
- `git diff --check` passed.
- Unsafe-claims grep was run; matches were pre-existing disclaimer text outside this sprint's changes.

## 10. Remaining follow-ups

- Auth D should implement actual personalized alert/brief delivery before the workspace can show delivery as active.
- Alerts, AI Briefs, and Reports pages still contain older sample-data views and should receive a later app-polish pass.
- A future workspace view should load source readiness directly from backend profile/source validation records once those records exist.
