# Premium Website + Auth + Dashboard Upgrade — Implementation Plan

## 1. Current frontend location and framework

- Location: `product/regradar/web/`
- Framework: React 19 + Vite 8 + Tailwind v4 (via @tailwindcss/vite plugin)
- State management: local useState, localStorage for workspace profile
- Routing: view-state machine in App.jsx (no react-router — single SPA with setState)
- Build: `npm run build` in `product/regradar/web/`

## 2. Current backend/auth status

- Backend: Python stdlib HTTPServer in `app/api.py` (no framework)
- Auth: session cookie (httponly, samesite=Strict), bcrypt passwords via `app/auth.py`
- Endpoints working: POST /api/auth/register, POST /api/auth/login, POST /api/auth/logout, GET /api/auth/me
- Profile: GET/PUT /api/profile
- Sources: GET /api/sources/status?market=AE — returns real data from sources.json merged with run records
- Contact: POST /api/contact — wires to Telegram, queues to JSONL
- Source test: POST /api/source-test — real URL compatibility check

## 3. Current API endpoints

| Endpoint | Method | Auth | Status |
|---|---|---|---|
| /api/auth/register | POST | No | Working |
| /api/auth/login | POST | No | Working |
| /api/auth/logout | POST | No | Working |
| /api/auth/me | GET | Session | Working |
| /api/profile | GET/PUT | Session | Working |
| /api/sources/status?market=AE | GET | Session | Working — returns 12 AE sources |
| /api/contact | POST | No | Working — Telegram + JSONL |
| /api/source-test | POST | Session | Working |
| /api/delivery/test-brief | POST | Session | Working |
| /api/delivery/logs | GET | Session | Working |
| /api/delivery/preview | GET | Session | Working |

No /api/evidence endpoint exists. Evidence data is sample-only.
No /api/briefs endpoint exists. Brief data is sample-only.

## 4. Design system plan

Already established:
- Background: #07111F (dark navy)
- Accent: #16D9F5 (cyan)
- Secondary bg: #0D1B2E, #0A1628
- Border: slate-800
- Text: white / slate-300 / slate-400 / slate-500
- Tailwind v4 via CSS import — no tailwind.config.js to extend

Status badge colors to use (already partially used):
- CHANGED: emerald-400 (#22C55E)
- FAILED: red-400 (#EF4444)
- QUALITY_DROP: amber-400 (#F59E0B)
- UNCHANGED: slate-400 (#64748B)
- FIRST_SEEN: blue-400 (#3B82F6)
- NOT_RUN: slate-600

## 5. Routes to add/change

App.jsx view-state machine (not react-router):
- `landing` → homepage (upgrade Hero copy, add Source Readiness CTA)
- `login` → LoginPage (exists, minor copy upgrade)
- `register` → RegisterPage (upgrade: add job title, company type, jurisdiction, disclaimer fields)
- `onboarding` → OnboardingPage (exists, no change)
- `app` → AppShell (upgrade Dashboard to fetch real sources/status)
- `source-readiness-review` → NEW public page

Inside AppShell page map:
- `dashboard` → DashboardHome (upgrade: real API widgets for sources/status)
- `sources` → SourcesPage (upgrade: merge real API data with mock)
- `evidence` → NEW EvidencePage (SAMPLE labeled)
- `briefs` → AIBriefPage (upgrade: add legal disclaimers per spec)
- `reports` → ReportsPage (exists)
- `integrations` → IntegrationsPage (exists)
- `settings` → SettingsPage (upgrade: legal acknowledgement section)

## 6. Files to edit

### New files:
- `web/src/components/SourceReadinessReviewPage.jsx`
- `web/src/components/app/EvidencePage.jsx`

### Edit files:
- `web/src/App.jsx` — add source-readiness-review view state
- `web/src/components/Hero.jsx` — exact copy from spec
- `web/src/components/Header.jsx` — add Source Review button + nav link
- `web/src/components/auth/RegisterPage.jsx` — add job title, company type, jurisdiction, disclaimer fields
- `web/src/components/app/AppShell.jsx` — add evidence page to PAGE map + sidebar
- `web/src/components/app/AppSidebar.jsx` — add Evidence nav item
- `web/src/components/app/AppTopbar.jsx` — add Evidence label
- `web/src/components/app/DashboardHome.jsx` — fetch real /api/sources/status, show 8 real widgets
- `web/src/components/app/AIBriefPage.jsx` — add legal disclaimer per spec
- `web/src/components/app/SettingsPage.jsx` — add legal acknowledgement section
- `web/src/api.js` — add evidence stub (for future use)
- `web/src/components/Footer.jsx` — full legal disclaimer

## 7. What will be real vs SAMPLE fallback

| Feature | Data source |
|---|---|
| Auth (login/register) | Real backend |
| Dashboard source table | Real: /api/sources/status |
| Dashboard widget counts | Real: derived from sources/status response |
| Evidence page | SAMPLE (labeled) — no /api/evidence endpoint |
| Brief page | SAMPLE (labeled) — no /api/briefs endpoint |
| Source readiness form | Real: /api/contact |
| Telegram status | Real: /api/telegram/pair/status |

## 8. Risks

1. /api/sources/status returns data only when authenticated — DashboardHome must handle 401 gracefully
2. sources.json has no `regulator` field for some sources — use `category` as fallback display
3. RegisterPage field additions may trip backend validation (backend only validates email, password, name, company, industry) — extra fields are UI-only; send only supported fields to backend
4. Tailwind v4 uses CSS import not config extend — status badge colors must be inline or CSS variables
5. AppShell page map uses string keys — adding `evidence` key must match sidebar id exactly

## 9. Validation commands

```bash
cd /Users/kurbnovomar/StatuteProof-Command-Center/product/regradar
python -m compileall app run.py -q

cd web
npm run build
npm run lint
```

Also: grep for no secrets, no .env committed, all SAMPLE labels present.

## 10. Rollback plan

All changes are frontend-only (new JSX components and edits to existing ones). Backend is untouched.
Rollback = `git checkout` of any modified file. No DB migrations, no schema changes, no server restarts needed.
