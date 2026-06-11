# Sprint Auth E1 — Security & Endpoint Hardening

## 1. Verdict

Sprint Auth E1 hardened the current MVP account surface without changing source monitoring, deployment, Telegram secrets, pricing, scheduler behavior, or personalized production delivery.

Global legacy Telegram settings endpoints are now unavailable to clients, selected abuse-prone endpoints have minimal in-memory rate limiting, profile PUT routing now parses the URL path consistently, and public contact submissions are truncated before queueing/admin delivery.

## 2. Files changed

- `app/api.py`
- `scripts/smoke_user_isolation.py`
- `reports/sprint_auth_e1_security_hardening.md`

Unrelated untracked report/doc files were present before this sprint and were left untouched.

## 3. Global Telegram settings endpoints

These legacy/global endpoints now return HTTP 403 JSON:

- `GET /api/settings/telegram`
- `POST /api/settings/telegram`
- `POST /api/settings/telegram/test`

Response:

```json
{ "ok": false, "message": "This endpoint is not available." }
```

They were disabled, not admin-protected. No admin system or `is_admin` column was added.

Per-user Telegram account pairing endpoints remain available behind the authenticated session cookie.

## 4. Rate limiting implemented

Added a small module-level, thread-safe, in-memory rate limiter in `app/api.py`.

Limits:

- Register: 5/hour/IP
- Login: 10/hour/IP
- Contact: 3/hour/IP
- Source test: 10/hour/IP
- Telegram pair generation: 10/hour/IP
- Telegram account test: 5/hour/IP
- Delivery sample brief: 5/hour/IP
- Delivery preview alert send: 10/hour/IP

Blocked requests return:

```json
{ "ok": false, "message": "Too many requests. Please wait before trying again." }
```

The limiter is intentionally minimal and resets on process restart.

## 5. PUT path matching fix

`do_PUT` now routes using:

```python
path = urlparse(self.path).path
```

This keeps `/api/profile` matching stable if query strings are present.

## 6. Contact truncation

The public contact endpoint remains public, but is now rate-limited and truncates user-provided fields before queueing/admin delivery:

- name: 120 characters
- email: 200 characters
- company: 160 characters
- industry: 160 characters
- message: 1000 characters
- markets: 500 characters
- watchlist context values: 500 characters

No frontend contact behavior was changed.

## 7. User isolation smoke results

Added `scripts/smoke_user_isolation.py`.

The script uses a temporary SQLite database under the system temp directory and does not write test users into the project database.

Checks passed:

- User A and B profiles are keyed to their own `user_id`.
- User B delivery logs do not include User A entries.
- Pairing status does not expose raw `telegram_chat_id`.
- User B cannot see User A active pairing code.
- Alert routing sent IDs are isolated by user.

## 8. Validation performed

Passed:

- `python3 -m compileall app run.py -q`
- DB init smoke via `ensure_auth_tables()`
- `python3 scripts/smoke_user_isolation.py`
- `cd web && npm run build`
- `git diff --check`
- Safety grep for production delivery / real-time / guaranteed / bulk-send claims

Notes:

- The isolation smoke emitted a local Python `requests` dependency warning, but all checks passed.
- The frontend build emitted a Node deprecation warning for `module.register()`, but the build passed.

## 9. What was deliberately not changed

- No deployment, `.env`, nginx, or systemd files were touched.
- No Telegram secrets were exposed or changed.
- No source monitoring behavior was changed.
- No source was activated.
- No pricing was changed.
- No automatic personalized delivery was enabled.
- No scheduler was added.
- No email delivery was added.
- No team account model was added.
- No admin UI or admin authorization model was added.
- `app/telegram.py send_telegram_alert()` was not changed.
- `app/pipeline.py` was not changed.

## 10. Remaining security limitations

- Rate limiting is in-memory and resets on process restart.
- Rate limiting is keyed by direct client IP; proxy-aware IP handling still needs production review.
- CSRF tokens are not implemented; `SameSite=Strict` remains the MVP defense.
- The session cookie `Secure` flag still requires HTTPS/production review.
- `source-test` remains public, though rate-limited and still uses existing URL safety checks.
- `contact` remains public, though rate-limited and truncated.
- No admin system exists yet for safely restoring global/admin Telegram settings management.
- Broader endpoint classification and abuse testing should continue before external pilots.

## 11. Next sprint recommendation

Auth E2 should add production-grade security hardening around sessions and public endpoints:

- production cookie `Secure` behavior;
- explicit allowed-origin review;
- CSRF plan or token implementation for state-changing endpoints;
- proxy-aware rate-limit keys;
- audit logging for sensitive account actions;
- documented admin-only replacement for disabled global Telegram settings if still needed.
