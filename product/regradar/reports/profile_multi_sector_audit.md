# Profile Multi-Sector Audit

## 1. Verdict

Multi-sector profiles are supported by the backend and reviewed alert routing layer.

The audit found one frontend/profile-mapping gap: onboarding saved source-layer selections into `topics`, but the shared localStorage profile helper did not expose `topics`, and Settings did not allow viewing or editing source layers after onboarding.

That gap was fixed without changing backend schema, delivery automation, Telegram pairing, or source monitoring behavior.

## 2. Does multi-sector already work?

Mostly yes.

Before this cleanup:

- Onboarding allowed selecting multiple industries.
- Onboarding allowed selecting multiple UAE source layers.
- Backend profile persistence stored `industries`, `markets`, `topics`, and `custom_sources` as JSON arrays.
- `app/profile.py` sanitized and returned arrays correctly.
- `app/alert_routing.py` converted profile arrays into routing terms and scored against all selected `industries` and `topics`.

The missing part was frontend consistency after onboarding:

- `workspaceProfile.js` ignored `topics`.
- Settings could edit `industries` and `markets` but not source-layer `topics`.
- Dashboard/Sources/Alerts did not show selected source layers clearly.

## 3. Questions answered

1. Does `OnboardingPage` allow selecting multiple sectors/industries/source layers?

Yes. It supports multiple industry chips and multiple source-layer chips.

2. Does `SettingsPage` preserve multiple sectors or collapse to one industry?

It preserved multiple `industries` arrays already. It did not expose source-layer `topics`; this is now fixed.

3. Does `profile.update()` store industries/topics as arrays?

Yes. `PUT /api/profile` passes arrays to `app.profile.update_profile()`, which JSON-serializes allowed list fields.

4. Does `app/profile.py` sanitize and return arrays correctly?

Yes. `industries`, `markets`, `topics`, and `custom_sources` are parsed and returned as arrays. Unknown fields, `user_id`, and Telegram fields are ignored.

5. Does `app/alert_routing.py` use multiple industries/topics when scoring?

Yes. `user_profile_to_routing_profile()` includes all selected `industries` and `topics`. `score_alert_for_user()` builds a normalized set from both arrays and scores overlap against alert topics, change type and source name.

6. Does `RegisterPage` industry field conflict with later multi-sector onboarding?

No. Register keeps a single primary industry for quick account creation. Auth/profile seeding can use it as an initial value, but onboarding and settings support multi-sector arrays afterward.

7. Does localStorage compatibility cache preserve arrays?

Yes for `industries`, `markets`, and `customSources`. `topics` is now also preserved and exposed through `workspaceProfile.js`.

8. Does Dashboard/Sources/Alerts display multiple selected sectors clearly?

Improved in this cleanup:

- Dashboard now shows source layers alongside markets and regulatory profile.
- Sources page now includes selected source layers in the saved-profile summary.
- Alerts page now includes markets, industries and source layers in the preview heading.

9. Are buyer source packs connected conceptually to profile sectors?

Conceptually yes: buyer source packs mirror the same categories that users can select during onboarding/settings. There is not yet a formal internal enum mapping buyer pack IDs to profile values.

10. What is missing for true multi-sector delivery?

- A canonical sector taxonomy shared across landing packs, onboarding, settings, routing and approved alert metadata.
- Stronger alias mapping, for example `VASP / Crypto` matching `VARA`, `virtual assets`, `AML`, `sanctions`, and source-specific alert terms.
- Admin/review tooling to tag approved alert artifacts with canonical sectors/source layers.
- More explicit delivery-readiness tests for multi-sector profiles like VASP + AML + Payments + Tax.

## 4. Files changed

- `web/src/data/workspaceProfile.js`
- `web/src/components/app/SettingsPage.jsx`
- `web/src/components/app/DashboardHome.jsx`
- `web/src/components/app/SourcesPage.jsx`
- `web/src/components/app/AlertsPage.jsx`

No backend schema change was needed.

## 5. Changes made

Frontend/profile mapping:

- Added `topics` to shared `getWorkspaceProfile()`.
- Preserved `topics` in the localStorage compatibility cache.
- Added source-layer chip editing to `SettingsPage`.
- Saved `topics` through the existing `/api/profile` update path.
- Displayed source layers in dashboard profile summary.
- Included source layers in Sources and Alerts profile headings.

## 6. Validation result

Commands run:

```bash
python3 -m compileall app run.py -q
cd web && npm run build
git diff --check
```

Results:

- Backend compile: PASS
- Frontend build: PASS
- Diff whitespace check: PASS

## 7. Remaining limitations

- Routing uses transparent string-overlap scoring. It handles multiple sectors, but it is not yet a robust ontology.
- Source-layer labels are still free-form strings, not canonical IDs.
- Settings and onboarding duplicate the source-layer option list.
- Buyer source packs are not yet programmatically tied to profile sector values.
- No delivery automation was added; reviewed alert preview delivery remains manual.
