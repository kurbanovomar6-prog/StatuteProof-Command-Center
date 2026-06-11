# Design E2 — Auth Page Polish + Landing Dark Consistency

## 1. Verdict

Design E2 removed the most visible fake/demo and stale pilot wording from the auth and integrations experience, converted the remaining light `Problem` landing section to the dark StatuteProof visual system, simplified unsupported language settings, and improved the source readiness report template for mobile/table overflow.

The product now reads more like a real founding pilot workspace instead of a demo/mock dashboard.

## 2. Files changed

- `web/src/components/auth/RegisterPage.jsx`
- `web/src/components/auth/LoginPage.jsx`
- `web/src/components/Problem.jsx`
- `web/src/components/app/IntegrationsPage.jsx`
- `web/src/components/app/OnboardingPage.jsx`
- `web/src/components/app/SettingsPage.jsx`
- `web/src/components/TelegramSettings.jsx`
- `app/templates/source_readiness_report.html`
- `reports/design_e2_auth_landing_consistency.md`

## 3. P0 auth-page fixes

Removed visible fake/demo wording from Register/Login:

- `demo workspace`
- production-auth-not-enabled language
- demo continuation link

Replaced with truthful founding-pilot account copy:

- secure StatuteProof pilot workspace;
- saved UAE source readiness profile;
- saved Telegram connection;
- sample brief delivery and reviewed alert previews.

Login left-panel framing is now UAE-first and source-readiness focused.

## 4. Landing dark consistency changes

`Problem.jsx` no longer uses the light `bg-slate-50` / white-card design.

Updated to:

- dark `#07111F` section background;
- dark `#0A1628` cards;
- slate/cyan borders;
- cyan/amber/emerald accents;
- slate text hierarchy consistent with the rest of the landing page.

No new unsupported product claims were added.

## 5. Integrations/onboarding/settings copy fixes

Integrations:

- Removed stale “next pilot step” Telegram wording.
- Copy now states Telegram is connected for test messages, sample brief delivery, and manual reviewed alert previews.
- Copy still clearly says automatic scheduled delivery is not enabled.

Onboarding:

- Replaced “will connect to official sources, extract regulatory updates, and generate AI compliance briefs” with safer profile/source-map language.
- Copy now says only validated sources enter monitoring and limitations are disclosed before pilot delivery.

Settings:

- Removed visible Russian / Both language options from the active UI.
- Brief language now presents English as the MVP language.
- Arabic is shown as planned, not an active production option.

## 6. Source readiness responsive polish

`app/templates/source_readiness_report.html` now has stronger responsive CSS:

- `@media (max-width: 900px)` breakpoint;
- single-column metadata/stat grids on smaller screens;
- reduced mobile padding;
- horizontal table containment with explicit table min-width;
- print CSS kept intact.

No report data logic was changed.

## 7. Dead code cleanup

Deleted unused `web/src/components/TelegramSettings.jsx`.

It was not imported anywhere and contained legacy global Telegram settings flow copy, including the old `@regradar_alerts_bot` reference.

## 8. Claims safety result

Bad-copy grep returned no matches:

```bash
grep -R "demo workspace|demo account|any password|fake workspace|Turkey|Kazakhstan|Georgia|CIS|Caucasus|@regradar_alerts_bot" web/src app/templates --exclude-dir=node_modules || true
```

Unsafe-claims grep returned no matches:

```bash
grep -R "35 active|complete UAE coverage|all UAE regulators|never miss|guaranteed compliance|real-time alerts|production delivery active|trusted by|live client data|delivered to your team|personalized alerts active|weekly briefs delivered" web/src app/templates --exclude-dir=node_modules || true
```

## 9. What was deliberately not changed

- Backend behavior was not changed.
- Auth/Profile/Telegram/Delivery APIs were not changed.
- Automatic production delivery was not enabled.
- Source monitoring behavior was not changed.
- No source was activated.
- Pricing was not changed.
- No fake testimonials, logos or clients were added.
- No localStorage key migration was performed.

## 10. Validation result

Passed:

- `cd web && npm run build`
- `python3 -m compileall app run.py -q`
- `git diff --check`
- P0/P1 bad-copy grep
- unsafe claims grep
- `grep -R "TelegramSettings" web/src --exclude-dir=node_modules || true`

Notes:

- The Vite build still emits the existing Node `module.register()` deprecation warning, but the build passes.

## 11. Remaining follow-ups

- `regradar_*` localStorage keys remain as internal compatibility keys; migration to `statuteproof_*` is deferred to avoid breaking cached workspace/profile state.
- Alerts/AI Brief preview pages still contain “Personalized delivery is coming in the next pilot step” copy. This was outside the specific IntegrationsPage copy fix and should be cleaned up in the next preview UX pass.
- Source readiness reports should still receive human review before being sent to prospects.
