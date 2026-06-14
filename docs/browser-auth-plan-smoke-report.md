# Browser Auth, Session, Plan Flow Smoke Report

## 1. Scope

Focused local browser smoke for:

- homepage
- login/register
- protected dashboard redirect
- register and onboarding
- plan intent/manual activation
- dashboard
- Source Lab
- billing
- evidence route
- logout/protected-route behavior

No deployment, live source checks, broad monitoring, Telegram/email, or customer delivery was run.

## 2. Environment

- API: `python3 run.py api --port 5001`
- Frontend: `npm run dev -- --host 127.0.0.1 --port 5173`
- Browser: Playwright Chromium, headless

The first Playwright launch was blocked by the macOS sandbox (`MachPortRendezvousServer` permission denied). The smoke was rerun with elevated permission for local browser launch only.

## 3. Final Corrected Smoke Results

| Check | Result | Detail |
|---|---:|---|
| Homepage renders | Pass | `http://127.0.0.1:5173/` |
| `/login` stays login | Pass | `http://127.0.0.1:5173/login` |
| `/register` stays register | Pass | `http://127.0.0.1:5173/register` |
| Unauthenticated `/app/dashboard` redirects | Pass | Redirected to `/login` |
| Register creates onboarding session | Pass | Landed on `/app/dashboard` onboarding view |
| Onboarding completes to choose-plan | Pass | Landed on `/app/choose-plan` |
| Plan intent remains manual activation | Pass | `requested=professional`, `active=evidence_preview`, `activation=pending_manual_activation` |
| Dashboard route renders | Pass | `/app/dashboard` showed Source readiness |
| Source Lab route renders | Pass | `/app/source-lab` |
| Billing manual activation copy renders | Pass | `/app/billing` showed Manual activation |
| Evidence route renders | Pass | `/app/evidence` showed Evidence Records |
| Logout clears protected access | Pass | After logout, `/app/dashboard` redirected to `/login` |

## 4. Console Findings

The final smoke captured 12 console errors, all `401 Unauthorized` resource responses caused by expected unauthenticated auth/profile checks during public/protected route probing. No duplicate React key warning appeared after the Evidence page key fix.

During an earlier pre-fix smoke, Vite reported duplicate React keys for repeated evidence run IDs on the Evidence page. This was fixed by including the row index in the Evidence card key.

## 5. Product Findings

Pass:

- Auth redirect behavior works.
- Register creates a session and lands in onboarding.
- Onboarding can be completed.
- Plan request does not activate the paid plan.
- Source Lab, billing, and evidence pages render after onboarding.
- Logout clears protected access.

Limitations:

- Smoke was local-only and did not verify production deployment.
- Smoke created local test users in the development database.
- No Stripe/payment flow was tested because live self-serve billing is intentionally not enabled.

## 6. Next Exact Task

Convert this local smoke into a committed repeatable script that can run in CI or pre-demo validation without requiring hand-written Playwright snippets.
