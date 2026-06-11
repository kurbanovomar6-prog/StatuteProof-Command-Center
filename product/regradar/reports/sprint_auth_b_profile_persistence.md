# Sprint Auth B — Profile Persistence

## 1. Verdict

Sprint Auth B adds account-owned profile persistence for authenticated StatuteProof users.

Each authenticated user now has an isolated backend profile stored by `user_id`. Dashboard profile data is saved to SQLite, and localStorage is used only as a compatibility cache for existing dashboard components.

Telegram pairing is NOT implemented.
`telegram_chat_id` is NOT accepted or stored.
Personalized delivery is NOT implemented.

## 2. Files changed

- `app/profile.py`
- `app/api.py`
- `app/db.py`
- `web/src/api.js`
- `web/src/App.jsx`
- `web/src/components/auth/RegisterPage.jsx`
- `web/src/components/app/OnboardingPage.jsx`
- `web/src/components/app/SettingsPage.jsx`
- `web/src/components/app/SourcesPage.jsx`
- `reports/sprint_auth_b_profile_persistence.md`

## 3. Backend table/endpoints

Added SQLite table:

- `user_profiles`

Added authenticated endpoints:

- `GET /api/profile`
- `PUT /api/profile`

Both endpoints require the Auth A session cookie. Unauthenticated requests return `401`.

## 4. Profile fields persisted

- `company_name`
- `industries`
- `markets`
- `topics`
- `licence_type`
- `custom_sources`
- `alert_threshold`
- `brief_language`
- `weekly_brief_enabled`
- `ai_enabled`
- `telegram_alerts_enabled`
- `email_alerts_enabled`
- `onboarding_completed`

Array/object fields are stored as JSON strings and returned as parsed arrays/objects.

## 5. Frontend integration

- `web/src/api.js` now exposes `profile.get()` and `profile.update()`.
- `App.jsx` loads `/api/profile` after `/api/auth/me`.
- `OnboardingPage.jsx` saves onboarding completion and profile setup to the backend.
- `SettingsPage.jsx` saves workspace, market, industry, alert, and brief preferences to the backend.
- `SourcesPage.jsx` syncs custom source additions to the backend profile without activating production sources.
- `RegisterPage.jsx` no longer writes fake profile data to localStorage.

## 6. LocalStorage cache strategy

`regradar_workspace_profile` remains as a cache for existing dashboard components. It is populated from backend profile responses and is no longer the profile source of truth.

`regradar_onboarding_complete` is derived from backend `profile.onboarding_completed`.

## 7. User isolation result

Smoke tests confirmed:

- user A profile update did not affect user B
- user B profile was created from user B account seed data
- unauthenticated profile read returned `401`
- request body `telegram_chat_id` was ignored and not returned

## 8. Validation performed

- `python3 -m compileall app run.py -q` passed.
- `cd web && npm run build` passed.
- `git diff --check` passed.
- Manual profile smoke tests passed on temporary SQLite DB and local API port `5014`.

## 9. Remaining limitations

- Telegram pairing is NOT implemented.
- `telegram_chat_id` is NOT accepted/stored.
- Personalized alert/brief delivery is NOT implemented.
- Rate limiting remains pending.
- CSRF hardening remains pending.
- Existing global Telegram settings endpoints remain separate and unauthenticated.
- Team accounts, password reset, and email verification are not implemented.

## 10. Next sprint recommendation

Proceed with Auth C: implement Telegram pairing codes, `/start CODE` bot linking, connected status, unlink/relink, and per-user Telegram connection state. Do not implement personalized delivery until pairing is verified.
