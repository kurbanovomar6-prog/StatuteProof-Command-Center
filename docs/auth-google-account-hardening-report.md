# StatuteProof Auth + Google Account Hardening Report

Report date: 2026-06-21

## Starting Auth Behavior

- Password registration and login existed.
- Email input was normalized before insertion for new password users, but the database did not have an explicit `normalized_email` contract.
- `users.email` was unique, but legacy/migration safety for case variants was weaker than ideal.
- Google sign-in was a disabled frontend placeholder.
- No Google OAuth backend endpoints existed.

## Ending Auth Behavior

- Password registration still works.
- Password login still works with case-insensitive and whitespace-normalized email lookup.
- Registered accounts persist in SQLite through the existing `users` table.
- `users.normalized_email` is now backfilled and enforced by a unique index.
- Google OAuth registration/login backend primitives exist.
- Google OAuth endpoints exist and are disabled gracefully when credentials are missing.
- Frontend login/register pages now query Google OAuth availability from the backend.
- No Google client secret is exposed to the frontend.

## Duplicate Email Prevention

Status: implemented.

Rules:
- Incoming email is trimmed.
- `normalized_email` is lowercased and used for uniqueness.
- Display email is stored separately in `users.email`.
- Registration rejects exact duplicates, casing variants, and leading/trailing whitespace variants.
- Login lookup uses `normalized_email`, so users can sign in with different casing.

Legacy migration behavior:
- `ensure_auth_tables()` adds `normalized_email`, `auth_provider`, and `email_verified` idempotently.
- Existing users are backfilled with `lower(trim(email))`.
- If legacy duplicate normalized emails are found, later duplicates are quarantined by assigning a non-login normalized marker and setting `is_active=0`; the first account remains the canonical login target.

## Database Migration Status

Changed:
- `users.normalized_email`
- `users.auth_provider`
- `users.email_verified`
- `oauth_identities`
- `oauth_states`
- unique index `idx_users_normalized_email_unique`

Runtime DB files were not staged.

## Google OAuth Status

Status: implemented behind env-gated config.

Required env vars:
- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`
- `GOOGLE_OAUTH_REDIRECT_URI`

Backend endpoints:
- `GET /api/auth/google/status`
- `GET /api/auth/google/start`
- `GET /api/auth/google/callback`

Security behavior:
- OAuth is unavailable when env vars are missing.
- Start endpoint creates a cryptographic server-side state.
- State is single-use and expires after 10 minutes.
- Callback validates state before exchanging the code.
- Server exchanges code with Google; frontend never sees the client secret.
- Userinfo must include a valid verified email.
- Unverified Google emails are rejected.
- Existing password account with the same normalized verified email is linked instead of duplicated.
- Repeated login with the same Google `sub` is idempotent.
- Session creation remains server-side cookie based.

## Secrets

- No `.env` file was read into the report.
- No env values were printed.
- No Google credentials were created.
- No Google credentials were committed.
- No customer emails were sent.

## Tests Added

New file:
- `product/regradar/tests/test_auth_accounts_google.py`

Coverage:
1. Duplicate registration blocks case and whitespace variants.
2. Login lookup is case-insensitive and persists through SQLite.
3. Auth schema migration is idempotent.
4. Google OAuth is unavailable when env vars are missing.
5. Google OAuth state is single-use and authorization URL has expected OpenID scopes.
6. Verified Google email creates a user and is idempotent.
7. Verified Google email links an existing password account without duplicate user creation.
8. Unverified Google email is rejected.
9. `normalize_email()` trims and lowercases.

Focused validation:
- `python3 -m pytest product/regradar/tests/test_auth_accounts_google.py product/regradar/tests/test_auth_plan_contracts.py -q` -> 14 passed.

## Frontend Changes

Changed:
- `product/regradar/web/src/api.js`
- `product/regradar/web/src/components/auth/LoginPage.jsx`
- `product/regradar/web/src/components/auth/RegisterPage.jsx`

UX behavior:
- Login and registration pages call `/api/auth/google/status`.
- If Google OAuth is not configured, the button is disabled and labeled as not configured.
- If configured, the button redirects to `/api/auth/google/start`.
- Copy explains that StatuteProof uses the verified work Google email to create or find the account.

## Security Limitations

- Real Google credentials were not configured in this sprint.
- The OAuth callback path was not exercised against live Google.
- CI/CD is still not configured by this task.
- Password reset remains pending.
- There is no account-management UI for unlinking Google identity yet.

## Next Exact Auth Task

Configure Google OAuth credentials in the deployment environment, then run a non-production live OAuth smoke test:
1. Confirm `/api/auth/google/status` returns `available=true`.
2. Register a new test account through Google.
3. Log out.
4. Log back in with Google.
5. Confirm no duplicate user row is created.
6. Confirm password login still works for existing password users.
