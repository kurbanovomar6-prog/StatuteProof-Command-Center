# Sprint Auth D1 — User Telegram Sample Brief Delivery

## 1. Verdict

Implemented the first safe user-specific delivery step: an authenticated, linked user can manually send one sample reviewed brief to their own Telegram chat, and the attempt is logged per user.

This sprint does not route real monitoring alerts or scheduled briefs to users.

## 2. Files changed

- `app/db.py`
- `app/user_delivery.py`
- `app/api.py`
- `web/src/api.js`
- `web/src/components/app/IntegrationsPage.jsx`
- `reports/sprint_auth_d1_sample_brief_delivery.md`

## 3. Database schema added

Added `user_delivery_log` with:

- user ownership via `user_id`
- delivery type/channel/status
- title and message preview
- optional source/alert/brief identifiers
- error message
- unique `idempotency_key`
- created/sent timestamps
- metadata JSON

Indexes were added for `user_id`, `created_at`, and `idempotency_key`.

## 4. Backend delivery module

Added `app/user_delivery.py` with:

- eligibility checks for onboarding completion, Telegram pairing, and Telegram-alert preference;
- honest sample brief message generation;
- per-user delivery log creation;
- sent/failed log updates;
- once-per-day idempotency for sample brief sends;
- safe per-user delivery log reads.

The module uses `send_telegram_message(chat_id, text)` and never uses global `TELEGRAM_CHAT_ID` or `send_telegram_alert()`.

## 5. API endpoints added

- `POST /api/delivery/test-brief`
- `GET /api/delivery/logs`

Both endpoints require the Auth A session cookie and use the current authenticated user only. They do not accept `user_id` from body or query string.

## 6. Frontend UX changes

In the connected Telegram state on Integrations:

- added `Send sample brief`;
- added sending/success/error status feedback;
- kept pairing, refresh, test-message and unlink flows intact;
- added helper copy that real alert routing is still the next pilot step.

## 7. Delivery log / idempotency

Sample brief sends use an idempotency key:

`{user_id}:sample_brief:{YYYY-MM-DD}`

If the same user attempts a second sample brief on the same day, the API returns a duplicate response instead of inserting or sending again.

Delivery logs are queried only by authenticated `user_id`, so User A cannot read User B logs through the API.

## 8. Validation performed

Validation passed:

- `python3 -m compileall app run.py -q`
- `python3 - <<'PY' ... ensure_auth_tables() ... PY`
- Auth D1 smoke base script for profile setup and delivery log reads
- `cd web && npm run build`
- `git diff --check`

The smoke script did not send Telegram messages.

## 9. What is now real

- User-owned delivery log table.
- User-triggered Telegram sample brief endpoint.
- Delivery eligibility checks.
- Per-user delivery log reads.
- Daily duplicate prevention for sample brief sends.
- Connected-state dashboard action to send the sample brief.

## 10. What is still not implemented

- Real monitoring pipeline alerts are NOT routed to users yet.
- Weekly scheduled brief delivery is NOT implemented.
- Personalized source/profile matching is NOT implemented.
- Automatic personalized alert delivery is NOT implemented.
- Email delivery is NOT implemented.

This sprint only sends a user-triggered sample brief to a linked Telegram chat.

## 11. Operational notes

- Global admin/contact Telegram remains separate.
- Existing monitoring pipeline Telegram behavior remains unchanged.
- A real end-to-end send requires a paired Telegram account, completed onboarding, enabled Telegram alerts, and a configured bot token.
- If Telegram token/runtime is unavailable, backend schema and endpoint logic can still be validated without sending.

## 12. Next sprint recommendation

Auth D2 should implement real approved-alert routing in dry-run mode:

- consume reviewed/approved alert payloads only;
- match user profiles against source/market/topic preferences;
- write delivery decisions to logs without sending first;
- keep global admin/contact notifications separate;
- add user-isolation tests before enabling live sends.
