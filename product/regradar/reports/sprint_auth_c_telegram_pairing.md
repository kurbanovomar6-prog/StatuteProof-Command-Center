# Sprint Auth C — Telegram Pairing

## 1. Verdict

Implemented real account-owned Telegram pairing for authenticated StatuteProof users.

Authenticated users can now generate a one-time pairing code, send `/start CODE` or `/connect CODE` to the Telegram bot, link the resulting Telegram chat to their own profile, refresh status in the dashboard, send an account-scoped test message, and unlink Telegram.

## 2. Files changed

- `app/telegram_pairing.py`
- `app/api.py`
- `app/config.py`
- `app/db.py`
- `app/telegram.py`
- `app/telegram_onboarding.py`
- `app/telegram_clients.py`
- `web/src/api.js`
- `web/src/components/app/IntegrationsPage.jsx`
- `reports/sprint_auth_c_telegram_pairing.md`

## 3. Database schema changes

Added nullable Telegram-managed fields to `user_profiles`:

- `telegram_chat_id`
- `telegram_username`
- `telegram_first_name`
- `telegram_paired_at`
- `telegram_last_test_at`

Added `telegram_pairing_codes`:

- `id`
- `user_id`
- `code`
- `created_at`
- `expires_at`
- `used_at`
- `used_chat_id`
- `invalidated_at`

Added indexes on `user_id`, `code`, and `expires_at`.

## 4. Pairing code design

Pairing codes use `SP-XXXXXX` format with a safe uppercase alphabet excluding ambiguous characters. Codes expire after 15 minutes, are one-time use, and generating a new code invalidates prior active unused codes for that user.

The dashboard never receives the full Telegram chat ID. It receives only masked status.

## 5. Backend endpoints added

- `POST /api/telegram/pair/generate`
- `GET /api/telegram/pair/status`
- `POST /api/telegram/pair/unlink`
- `POST /api/telegram/test`

All new endpoints require the Auth A session cookie. No endpoint accepts `user_id` or `telegram_chat_id` from the request body.

The legacy global admin endpoint `/api/settings/telegram/test` remains separate and unchanged.

## 6. Bot handler changes

`app/telegram_onboarding.py` now parses command arguments and supports:

- `/start`
- `/start CODE`
- `/connect`
- `/connect CODE`
- `/id`
- commands with bot username suffix, such as `/start@BotName CODE`

Valid pairing codes link the incoming Telegram `chat_id` to the correct authenticated account profile. Bot replies do not include user email, company name, user ID, tokens, or internal errors.

The bot listener must be restarted to pick up `/start CODE` pairing behavior.

## 7. Frontend UX changes

The Integrations Telegram card now uses the account pairing API instead of the previous fake manual Chat ID form.

The card supports:

- loading real connection status;
- generating a one-time pairing code;
- displaying `/start CODE`;
- copying the command;
- refreshing status;
- showing connected username, masked chat ID, paired time, and last test time;
- sending a test message to the linked chat;
- unlinking Telegram.

The UI explicitly says production alert routing is the next sprint.

## 8. Test/smoke results

Validation performed:

- `python3 -m compileall app run.py -q` passed.
- `python3 -c 'from app.db import ensure_auth_tables; ensure_auth_tables(); print("Migration OK")'` passed.
- Temporary DB pairing smoke test passed:
  - generated `SP-XXXXXX` code;
  - consumed code successfully;
  - stored chat ID internally;
  - returned masked chat ID;
  - rejected reused code;
  - rejected invalid code;
  - unlinked Telegram.
- `cd web && npm run build` passed.

Final `git diff --check` was run before commit.

## 9. What is now real

- Account-owned Telegram pairing code generation.
- One-time code consumption by the Telegram bot.
- Per-user Telegram chat storage in `user_profiles`.
- Connected/not connected dashboard status from backend.
- Unlink/relink behavior.
- Account-scoped Telegram test message endpoint.

## 10. What is still not implemented

- Personalized alert/brief delivery is NOT implemented.
- Monitoring pipeline still uses global/admin Telegram until Auth D.
- Weekly brief delivery is NOT changed.
- Telegram pairing does not activate production alerts.
- Rate limiting and CSRF hardening remain pending.
- Team/workspace accounts are not implemented.

## 11. Operational notes

- Global Telegram settings remain separate from account pairing.
- A real end-to-end Telegram test requires `TELEGRAM_BOT_TOKEN` and a real Telegram account.
- `TELEGRAM_BOT_USERNAME` is optional; if absent, the API returns generic bot instructions.
- The bot listener and API server can initialize pairing tables independently.

## 12. Next sprint recommendation

Auth D should implement personalized delivery:

- route eligible alerts and briefs to `user_profiles.telegram_chat_id`;
- respect user profile markets, sources, thresholds, and delivery preferences;
- keep admin/contact Telegram notifications separate;
- add user isolation tests for delivery routing;
- add operational controls for disabled users and unlinked Telegram accounts.
