# Design E3 — Alerts and Briefs Preview Copy Polish

## 1. Verdict

Design E3 updated stale preview-delivery copy on Alerts and AI Brief pages without changing backend behavior, API wiring, button behavior, delivery logic, source monitoring, or dashboard structure.

The pages now accurately describe current capability:

- manual reviewed alert preview delivery exists where approved routing previews are available;
- sample brief delivery can be tested from Integrations after Telegram pairing;
- automatic scheduled delivery is not enabled yet;
- weekly brief delivery remains a pilot roadmap item.

## 2. Files changed

- `web/src/components/app/AlertsPage.jsx`
- `web/src/components/app/AIBriefPage.jsx`
- `reports/design_e3_alerts_briefs_copy_polish.md`

## 3. Copy fixes

Alerts page:

- Replaced stale “next pilot step” wording.
- Clarified that manual preview delivery is available for reviewed alert previews when Telegram is connected.
- Clarified that sample cards remain preview-only.
- Kept automatic scheduled delivery explicitly disabled.

AI Brief page:

- Replaced stale “next pilot step” tooltip/helper text.
- Clarified that sample brief delivery is tested from Integrations after Telegram pairing.
- Clarified that weekly brief delivery remains a pilot roadmap item.

No button behavior was changed.

## 4. Validation result

Passed:

- `cd web && npm run build`
- `python3 -m compileall app run.py -q`
- `git diff --check`
- Required grep for stale/unsafe copy returned no matches.

Notes:

- Vite still emits the existing Node `module.register()` deprecation warning; build succeeds.

## 5. What was deliberately not changed

- No backend files were changed.
- No auth/profile/Telegram/delivery logic was changed.
- No new API wiring was added.
- No fake live delivery or sent states were added.
- No automatic production delivery was enabled.
- No scheduled weekly briefs were enabled.
- Source monitoring behavior was not changed.
