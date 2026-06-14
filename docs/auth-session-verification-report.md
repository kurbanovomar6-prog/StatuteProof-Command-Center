# Auth Session Verification Report

Date: 2026-06-14

## Executive Result

Auth/session P0 was fixed at the API cookie-contract level.

The previous risk was that the API always set `Secure` session cookies, while local Vite development uses HTTP. That could make local login/register appear successful while the browser refuses to persist the session cookie.

## Fix Made

Updated `product/regradar/app/api.py`:

- Added `_session_cookie_secure_for_host(host)`.
- Local hosts default to non-secure cookies:
  - `localhost`
  - `127.0.0.1`
  - `[::1]`
  - `::1`
- Non-local hosts default to `Secure` cookies.
- Added `STATUTEPROOF_COOKIE_SECURE=true|false` override for deployment-specific control.
- Logout/clear cookie uses the same secure-cookie decision as login/register.

## Flows Covered By Scripted Validation

| Flow / contract | Result | Evidence |
| --- | --- | --- |
| Localhost cookie is not `Secure` by default | Pass | `test_auth_plan_contracts.py` |
| `127.0.0.1` cookie is not `Secure` by default | Pass | `test_auth_plan_contracts.py` |
| IPv6 loopback cookie is not `Secure` by default | Pass | `test_auth_plan_contracts.py` |
| Non-local host remains `Secure` by default | Pass | `test_auth_plan_contracts.py` |
| Environment override can force secure on local | Pass | `test_auth_plan_contracts.py` |
| Environment override can force non-secure for a host | Pass | `test_auth_plan_contracts.py` |

Command run:

`python3 -m pytest product/regradar/tests/test_auth_plan_contracts.py -q`

Result:

`5 passed`

## Browser Flow Status

Full browser registration/login/logout was not run in this sprint because the P0 fix is a low-level cookie contract and final frontend validation is still run through build, lint, and route validation. A follow-up browser smoke should still verify:

- unauthenticated `/login` stays `/login`;
- unauthenticated `/register` stays `/register`;
- unauthenticated `/app/dashboard` redirects to `/login`;
- register creates session and lands in onboarding/workspace flow;
- login persists after reload;
- logout clears the session;
- protected pages do not render data after logout;
- plan intent query parameters still survive registration.

## Remaining Risk

- Production deployment should explicitly set or verify `STATUTEPROOF_COOKIE_SECURE=true` if the API is served behind HTTPS and same-origin cookies are expected.
- The current server remains an MVP `http.server` stack, not a production auth framework.
- Password reset and OAuth remain intentionally disabled placeholders.

## Next Exact Task

Run a local browser auth smoke with API + Vite dev server before any customer demo.
