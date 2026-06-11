# Sprint Auth A — Real Auth Foundation

## 1. Verdict

Sprint Auth A replaces fake/localStorage authentication with a real backend account foundation.

Telegram pairing is NOT implemented yet.
Profile persistence is NOT implemented yet.
Personalized alert/brief delivery is NOT implemented yet.
This sprint only replaces fake/localStorage auth with real account foundation.

## 2. Files changed

- `app/auth.py`
- `app/api.py`
- `app/db.py`
- `web/src/api.js`
- `web/src/App.jsx`
- `web/src/components/auth/LoginPage.jsx`
- `web/src/components/auth/RegisterPage.jsx`
- `reports/sprint_auth_a_real_auth_foundation.md`

## 3. Backend auth endpoints added

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

Existing public contact, health, source-test, and Telegram settings endpoints were not protected or repurposed in this sprint.

## 4. Database schema added

Added additive SQLite auth tables with `CREATE TABLE IF NOT EXISTS`:

- `users`
- `sessions`

The existing `documents` monitoring table and source-monitoring storage were not altered.

## 5. Password hashing method

Password hashing uses standard-library PBKDF2:

- algorithm: `pbkdf2_hmac`
- digest: `sha256`
- iterations: `300000`
- random salt: 16 bytes
- stored format: `pbkdf2_sha256$iterations$salt_hex$hash_hex`

Plaintext passwords are not stored or returned.

## 6. Session/cookie strategy

Sessions are server-side rows in SQLite with 7-day expiry.

Cookie:

- name: `statuteproof_session`
- `HttpOnly`
- `SameSite=Strict`
- `Path=/`
- `Max-Age=604800`

The cookie intentionally omits `Secure` for local development. Code includes a TODO to add `Secure` in production when same-origin HTTPS is guaranteed.

## 7. Frontend integration

- Added `web/src/api.js` with fetch-based auth helpers and `credentials: "include"`.
- `LoginPage.jsx` now calls `POST /api/auth/login`.
- `RegisterPage.jsx` now calls `POST /api/auth/register`.
- `App.jsx` now checks `GET /api/auth/me` and gates dashboard access by backend session state.
- LocalStorage is still used temporarily for onboarding/profile compatibility only, not as the source of auth truth.

## 8. Validation performed

- `python3 -m compileall app run.py -q` passed.
- `cd web && npm run build` passed.
- `git diff --check` passed.
- Smoke tests passed against a temporary SQLite DB on local API port `5014`:
  - register user returned `201`
  - duplicate register returned `409`
  - wrong-password login returned `401`
  - correct login returned `200`
  - `/api/auth/me` returned authenticated user with session cookie
  - logout returned `200` and cleared the cookie
  - `/api/auth/me` after logout returned `401`

## 9. Security limitations still remaining

- No rate limiting yet.
- No CSRF token layer yet.
- Existing Telegram settings endpoints remain unauthenticated/global.
- Existing source/contact endpoints remain public as requested.
- Profile data is still localStorage-backed until Auth B.
- No per-user Telegram pairing or alert routing exists yet.
- Production cookie `Secure` flag needs deployment-aware enablement.

## 10. Next sprint recommendation

Proceed with Sprint Auth B: persist workspace/profile settings server-side per authenticated user and replace localStorage as the dashboard profile source of truth.
