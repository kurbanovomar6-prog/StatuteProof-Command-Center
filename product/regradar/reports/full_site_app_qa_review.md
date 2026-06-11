# Full Site / App QA Review
**Date:** 2026-06-02
**Branch:** main
**Head commit:** f2267e2
**Scope:** Post Auth A–E1 + Design 1–4A + Source Readiness generator

---

## 1. Verdict

**Status: Pilot-ready with two must-fix issues before showing to a serious prospect.**

The product is substantially further along than most pre-pilot B2B SaaS. The landing, dashboard, auth flow, Telegram pairing, sample delivery, and source readiness generator are all functioning and correctly scoped. Claims safety is clean. UAE-first positioning is consistent.

**Two items must be fixed before any external prospect sees the product:**

1. **RegisterPage and LoginPage contain a notice that says "This is a demo workspace. Production authentication will be enabled before client onboarding."** This is factually wrong — production auth IS implemented (Auth A–D). A prospect seeing this at the first screen will immediately question whether anything in the product is real.

2. **The stale module docstring in `app/api.py` says "Provides 3 endpoints for Telegram settings management"** — visible in error messages and logs, but more importantly it signals the product identity is not fully updated.

Everything else is P1 or P2 — important but not show-stoppers for a controlled first demo.

---

## 2. Validation Results

| Check | Result | Notes |
|---|---|---|
| `python3 -m compileall app run.py -q` | **PASS** | Zero errors |
| `cd web && npm run build` | **PASS** | 1776 modules, 467 kB JS, 75 kB CSS. Node deprecation warning for `module.register()` — harmless |
| `git diff --check` | **PASS** | No whitespace issues |

---

## 3. Brand Consistency Findings

### Client-facing problems (must fix before demo)

| Location | Problem | Classification |
|---|---|---|
| `RegisterPage.jsx:69` | "Start with a demo workspace to see StatuteProof in action." | **Visible client-facing** — real auth is implemented, not a demo |
| `RegisterPage.jsx:144` | "This is a demo workspace. Production authentication will be enabled before client onboarding." | **Incorrect and damaging** — Auth A–D already implemented |
| `LoginPage.jsx:127` | Same "demo workspace / production auth pending" notice | **Incorrect and damaging** |

### Internal compatibility — acceptable before pilot

| Location | Item | Classification |
|---|---|---|
| `App.jsx`, `SettingsPage.jsx`, `OnboardingPage.jsx`, `SourcesPage.jsx`, etc. | `regradar_workspace_profile`, `regradar_onboarding_complete`, `regradar_user_registered` localStorage keys | **Internal** — not visible to users. Does appear in browser dev tools. Should rename to `statuteproof_*` before public launch. |
| `Header.jsx`, `Footer.jsx`, `AppSidebar.jsx`, auth pages | Asset path `/brand/regradar-logo-navbar.png` — alt text is "StatuteProof" | **Internal asset path only** — `alt` is correct. Rename asset before public launch. |
| `app/api.py:2` | Module docstring: "RegRadar minimal API server" | **Internal** — only visible in logs/errors |
| `app/config.py:2` | Docstring: "RegRadar v3", env var `REGRADAR_DB_PATH` | **Internal** |
| `run.py:53810` | CLI print: `RegRadar v4` | **CLI-only** — not client-facing |
| `app/report.py` | Output files named `regradar_report_YYYY-MM-DD.md/html` | **Would be visible** if a client receives a compliance report — fix before use |
| `TelegramSettings.jsx` | Contains `@regradar_alerts_bot` and old admin endpoint | **Dead code** — not imported anywhere. Does NOT render. Safe to ignore short term, delete eventually. |

### Historical reports — acceptable

- `reports/sample_compliance_brief_en.md` — says "RegRadar Sample Compliance Briefs" and includes non-UAE briefs (MASAK Turkey, ARDFM Kazakhstan). **Do not share with pilot clients.** Replace with current StatuteProof UAE sample.
- Various coverage/validation reports in `reports/` — historical, not shown to clients.

### Summary

No "RegRadar" branding is visible to users in the current rendered app. The `regradar_*` localStorage keys appear in browser dev tools but not in the product UI. The auth pages problem ("demo workspace") is the only externally visible brand/confidence issue.

---

## 4. UAE-First Findings

**`grep` across `web/src` for Turkey, Kazakhstan, Georgia, Azerbaijan, Saudi Arabia, Armenia, TCMB, MASAK, ARDFM, National Bank KZ, Matsne, Revenue Service, CBAR, CBA Armenia, SAMA, CIS, Caucasus:**

- **Zero matches in `web/src`.** The product UI is clean.

Backend internal files (`coverage_plan.py`, `coverage.py`, `language.py`, `app/ai.py`) reference CIS/GCC jurisdictions — these are internal pipeline modules, not client-facing. Acceptable.

`app/ai.py` AI prompt includes "Turkey, Central Asia, Caucasus" — internal prompt context for multi-jurisdiction analysis. Not visible to users.

**UAE-first verdict: CLEAN.** No non-UAE default data in any landing or dashboard component.

---

## 5. Claims Safety Findings

All "legal advice" matches (17 found across `web/src`, `app/`, `scripts/`, generated reports) are disclaimers or negations:
- "Not legal advice" — correct disclaimer
- "does not provide legal advice" — correct
- "No automated legal advice" — correct

**Zero unsafe positive claims found for:**
- "35 active sources" — not found
- "complete UAE coverage" — not found
- "all UAE regulators" — not found
- "never miss" — not found
- "guaranteed compliance" — not found
- "real-time alerts" — not found
- "production delivery active" — not found
- "trusted by" — not found
- "live client data" — not found
- "personalized alerts active" — not found
- "weekly briefs delivered" — not found

Hero component correctly says "Validated layer configured — 9 sources" — accurate count.

**Claims safety verdict: CLEAN.**

---

## 6. Landing Page Review

### Design consistency

| Section | Background | Status |
|---|---|---|
| Header (fixed) | `#0f172a/90` dark | Consistent |
| Hero | `#07111F` dark | Consistent |
| Problem | `bg-slate-50` **LIGHT** | **Inconsistent — stands out as a white section in a dark landing** |
| WithoutWith | dark | Consistent |
| HowItWorks | dark | Consistent |
| SampleBrief | dark | Consistent |
| Coverage | dark | Consistent |
| SourceTransparencyMatrix | dark | Consistent |
| BuyerSourcePacks | dark | Consistent |
| TrustLayer | `#07111F` dark | Consistent |
| Pricing | `#07111F` dark | Consistent |
| Contact | dark | Consistent |
| Footer | dark | Consistent |

**Problem.jsx is the only white section.** It uses `bg-slate-50` with light text and light borders. This visually breaks the dark premium experience and makes the landing feel inconsistent. Should be converted to dark theme before any prospect demo.

### Header and navigation

- "Request Source Review" CTA in header — clear and correct
- "Sign in" link — visible
- Mobile hamburger menu — present, opens full-screen menu with Sign in + Request Source Review CTA
- Five nav links: How It Works, Source Coverage, Alert Profiles, Evidence, Pricing — reasonable set

### Hero quality

- "Validated layer configured — 9 sources" — accurate
- Floating badge "Limitations disclosed" — strong trust signal
- Mock dashboard shows CBUAE + VARA samples, UAE-only, "Review gate" badge on alerts
- Honest product preview — no fake "live" states

### Source transparency

- `SourceTransparencyMatrix` — "Mapped does not mean active" — excellent positioning
- "Broad source map. Strict activation standard." — clear and defensible
- "Get a free UAE Source Readiness Review" CTA — clear lead generation action
- `BuyerSourcePacks` — 7 buyer profile cards with Validated/Under validation/Needs adapter chips — honest

### Pricing

- "Founding Pilot Terms" framing — honest
- "early access", "lower than our eventual standard rates" — correct expectations
- Founding pilot pricing disclosure footer — good

### Issues

1. **Problem section is light background** — breaks visual consistency.
2. **No `<meta property="og:image">` in `index.html`** — social sharing will have no preview image.
3. `index.html` favicon references `regradar-favicon-512.png` — old brand asset filename (but not visible to users, only browser tab icon).

---

## 7. Dashboard / App Review

### App shell

- `AppShell.jsx` — clean structure: sidebar + topbar + main content area
- Mobile overlay + slide-in sidebar with `translate-x` transition — mobile support present
- Sidebar nav labels: "Dashboard", "Sources", **"Sample Alerts"**, **"Brief Previews"**, **"Source Reports"**, "Integrations", "Settings" — all correctly labeled as sample/preview

### Sidebar

- "Founding pilot" status pill in sidebar footer — correct
- Company name and email from backend via localStorage cache — correct
- No "Demo Workspace" label — correct

### Topbar

- Reads from localStorage (`regradar_workspace_profile`) for company name — internal
- No fake live monitoring status shown

### Dashboard Home

- "UAE-first pilot workspace" — correct
- "Founding pilot" status pill — correct
- "Sample signal preview" section — correctly labeled
- Source readiness card: "35+ source layers mapped" — consistent with 44 candidates in source candidates file. Phrasing is defensible.
- Pilot setup checklist — good onboarding guide
- Telegram status loaded from real backend API — correct
- "Brief delivery: Pending" stat card — honest

### Onboarding

- Calls real `PUT /api/profile` — correct
- Step 4 review screen says: "StatuteProof will connect to official sources, extract regulatory updates, and generate AI compliance briefs based on this profile." — **slightly forward-looking for a pilot**. Should say "...and deliver reviewed briefs matched to your profile." to avoid implying automatic production AI briefs are active.

### Settings

- Saves to real `PUT /api/profile` via API — correct
- Language options include "Russian" and "Both (EN + RU)" — legacy CIS options. Confusing for a UAE-first product. A pilot client selecting "Russian" gets a preference that has no meaningful effect right now.

### Sources

- All sources are UAE-market mock data — clean
- "Source validation request saved" message after test — honest
- Custom source test calls `/api/source-test` — public rate-limited endpoint (acceptable for client UX)
- Correctly shows "Needs adapter", "Validated", "Limited" status taxonomy

### Alerts

- "Reviewed alert routing preview" panel — honest disclaimer: "Automatic production delivery is not enabled."
- "No approved reviewed alerts found in the last 14 days" empty state — **correct — no fake approved alerts created**
- Sample format preview cards below — clearly labeled
- Manual send button only shows when routing preview has matches

### Brief Previews (AIBriefPage)

- "Reviewed Brief Previews" title — correct
- "AI assists drafting. Human review gates client delivery." — excellent framing
- Tags: "Source proof", "Human review gate", "Limitation note", "Delivery pending" — all honest
- Based on `MOCK_ALERTS` sample data — correctly labeled as previews

### Source Reports (ReportsPage)

- "Sample report outputs" title — correct
- Tags: "Available sample", "Generated manually", "Requires pilot setup", "Proof artifact" — honest
- No live/production report claims

### Integrations

- Uses real `telegramPair` API (new account-scoped system) — correct
- Pairing code generation, status, unlink, test message — all wired to real backend
- Sample brief trigger — wired to real backend
- **Stale copy still present:** "Personalized alert delivery is configured in the next pilot step." — This has been true since before D2. D2 manual preview delivery now exists in Alerts. Should say: "Manual reviewed alert preview delivery is available in Alerts. Automatic production routing is the next pilot step."

### Issues found

1. **RegisterPage says "demo workspace"** — critical confidence problem (covered in §3)
2. **Onboarding Step 4** slightly over-promises automatic AI brief generation
3. **Settings shows Russian/Both language options** — dead feature path for UAE-first
4. **IntegrationsPage stale copy** — "next pilot step" text doesn't reflect D2 manual preview delivery
5. No `currentUser` prop passed to most app pages (only DashboardHome gets it from AppShell) — logged-in user's name/email is only shown in sidebar, not in individual pages. Acceptable for pilot.

---

## 8. Auth / Account UX Review

### Flow: landing → register → onboarding → dashboard

| Step | Working | Notes |
|---|---|---|
| Landing "Sign in" → LoginPage | Yes | Clean auth layout |
| LoginPage → `POST /api/auth/login` | Yes | Calls real endpoint |
| RegisterPage → `POST /api/auth/register` | Yes | Calls real endpoint |
| Auth success → profile fetch → dashboard/onboarding | Yes | `handleAuthenticated` does full bootstrap |
| Bootstrap: `auth.me()` + `profile.get()` | Yes | `syncProfileToLocalStorage()` writes cache |
| Expired auth → `auth:expired` event → landing | Yes | Correct fallback |
| Logout → `POST /api/auth/logout` + clear localStorage | Yes | Correct |

### Critical issue

**`RegisterPage.jsx:69`:** `"Start with a demo workspace to see StatuteProof in action."`

**`RegisterPage.jsx:144` + `LoginPage.jsx:127`:**
```
This is a demo workspace. Production authentication will be enabled before client onboarding.
```

This text is displayed as a notice box to every user during signup and login. It is **factually incorrect** — Auth A–D implemented real PBKDF2 password hashing, server-side sessions, backend profile persistence, and Telegram account pairing. The product has moved beyond demo status. A pilot prospect seeing this will assume the whole auth system is fake.

**Must be updated before any external prospect sees the product.**

### Other auth observations

- `LoginPage` left-panel quote: "Regulatory monitoring for undercovered and fast-changing markets." — the "undercovered" framing feels like old multi-jurisdiction positioning. UAE is a well-covered regulatory market. Consider: "UAE regulatory intelligence from official sources — not newsletters."
- No "Forgot password" link — acceptable for invite-only pilot if disclosed
- No email verification flow — acceptable for pilot
- RegisterPage still collects single `industry` on registration but onboarding collects multiple `industries`. Both are passed to the API which normalizes them. Not a user-visible bug.

---

## 9. Telegram / Delivery UX Review

### Integrations page (pairing flow)

- Pairing code generation: `POST /api/telegram/pair/generate` — auth-required ✓
- Pairing code display + clipboard copy — works
- Bot link generated from `bot_username` returned by backend — correct
- Pairing status polling — real backend state ✓
- Unlink — `POST /api/telegram/pair/unlink` — auth-required ✓
- Test message — `POST /api/telegram/test` — auth-required ✓
- Sample brief trigger — `POST /api/delivery/test-brief` — auth-required ✓

**No manual chat ID input as source of truth** — correct. Old `TelegramSettings.jsx` component with manual chat ID input is dead code and not rendered anywhere.

### Alerts page (D2 routing preview)

- `GET /api/delivery/preview?days=14` called on load — auth-required ✓
- Empty state: "No approved reviewed alerts found in the last 14 days. No fake approved alerts are created for this empty state." — **excellent honest empty state**
- "Automatic production delivery is not enabled." — prominent correct disclaimer
- Manual send: `POST /api/delivery/send-preview-alert` — auth-required ✓
- Idempotency: duplicate sends blocked server-side ✓

### Issues

1. **IntegrationsPage stale copy** — "Personalized alert delivery is configured in the next pilot step." Outdated since D2 manual preview delivery exists. Fix: "Manual reviewed alert preview delivery is available in the Alerts tab. Automatic production routing requires pilot setup."
2. `TelegramSettings.jsx` dead code file still exists — contains `@regradar_alerts_bot` and old public endpoint. Not rendered, but should be deleted before code is shared.
3. Delivery logs (`GET /api/delivery/logs`) are available from the API but not exposed in the UI. The client can't see their own delivery history from the dashboard. Not critical for pilot but a gap.

---

## 10. Source Readiness Generator Review

### Script: `scripts/generate_source_readiness.py`

- Docstring: "Generate a manual StatuteProof Source Readiness Review HTML report." — correct branding ✓
- 7 buyer profiles: VASP/Crypto, Payments/Fintech, DIFC/DFSA, ADGM/FSRA, AML/FIU, Tax/Corporate, Data Protection — complete set ✓
- `data_protection` profile empty state: script returns `'<p class="muted">No active source recommendation is made for this profile until validation improves.</p>'` when `active_items` is empty — graceful empty-state ✓
- All 7 profiles have `sample_title` fallback for the sample brief section ✓
- Status derivation: Active / Under technical validation / Access limited / Navigation-only / Needs extraction adapter / Blocked — all mapped to clear client labels ✓
- Limitation notes: `_limitation()` combines candidate limitation, source limitation, under-validation notes — thorough ✓
- "Not a coverage guarantee" explicitly stated in summary text ✓

### Template: `app/templates/source_readiness_report.html`

- Title: "StatuteProof — Source Readiness Review" ✓
- Dark brand colors: `#07111F` background, `#16D9F5` accent ✓
- Status badges: `.status-active` (green), `.status-validation` (amber), `.status-limited` (red), `.status-mapped` (slate) — visually distinct ✓
- "Not legal advice. Source statuses reflect current technical validation state and may change." — disclaimer present ✓
- Four-column responsive grid for stats — may overflow on mobile (see §12)

### Generated report: `reports/source_readiness_vasp_crypto_sample.html`

- Title: "StatuteProof — Source Readiness Review" ✓
- Generated: 2026-06-02 ✓
- "Not legal advice" in yellow stamp box ✓
- "This report does not constitute legal advice and should not be relied upon as a substitute for qualified legal counsel." — full disclaimer present ✓
- "StatuteProof does not guarantee detection of all regulatory changes." ✓
- Sample brief clearly labeled — "This illustrative sample shows how a reviewed StatuteProof brief would describe a regulatory update format. It is not real data." ✓

### Issues

1. **Source readiness report uses `.grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }`** for the stats bar — will overflow on mobile (4 columns of stats). No responsive breakpoint for small screens in the template CSS.
2. **Report generation requires manual operator run** (`python scripts/generate_source_readiness.py --profile vasp_crypto`) — no automated endpoint or CTA flow yet. For the pilot this means: Contact form → operator generates and emails HTML. Acceptable but should be documented.
3. The generated `.html` file in `reports/` is good to share. The VASP crypto sample (`reports/source_readiness_vasp_crypto_sample.html`) is ready as a demo artifact.

---

## 11. Endpoint / Client-Readiness Audit

### Complete endpoint classification

**Public safe:**
| Endpoint | Notes |
|---|---|
| `GET /api/health` | Safe |
| `GET /api/` | Safe |
| `POST /api/auth/register` | Public required |
| `POST /api/auth/login` | Public required |
| `POST /api/auth/logout` | Safe — deletes session if present |

**Public, rate-limited (acceptable risk for invite-only pilot):**
| Endpoint | Rate limit | Risk |
|---|---|---|
| `POST /api/contact` | 3/hr per IP | Low for pilot — needs abuse protection before public launch |
| `POST /api/source-test` | 10/hr per IP | Medium — triggers outbound connection; no auth required. Not exploitable for mass damage but still unauthenticated. |

**Auth-required user endpoints:**
All working correctly with `require_auth()`. Verified:
- `GET /api/auth/me`, `GET /api/profile`, `PUT /api/profile`
- `POST /api/telegram/pair/generate`, `GET /api/telegram/pair/status`, `POST /api/telegram/pair/unlink`, `POST /api/telegram/test`
- `POST /api/delivery/test-brief`, `GET /api/delivery/logs`, `GET /api/delivery/preview`, `POST /api/delivery/send-preview-alert`

**Disabled (calls `_disabled_endpoint()`):**
| Endpoint | Status |
|---|---|
| `GET /api/settings/telegram` | Disabled ✓ |
| `POST /api/settings/telegram` | Disabled ✓ |
| `POST /api/settings/telegram/test` | Disabled ✓ |

These were the highest-risk endpoints from previous QA. Now disabled. **Auth E1 correctly addressed these.**

### Remaining security gaps

| Issue | Severity | Notes |
|---|---|---|
| `/api/source-test` public (rate-limited) | Medium | No auth required. Triggers outbound connection. Rate limited at 10/hr per IP. |
| No CSRF protection | Medium | Cookie auth without CSRF. `SameSite=Strict` reduces risk on modern browsers but not complete mitigation. |
| `_ALLOWED_ORIGIN` hardcoded `http://localhost:5173` | Low | Deploy would need code change. Move to env var. |
| `validate_password()` only checks `len >= 8` | Low | No complexity requirement. |
| `Secure` cookie flag not set | Low | TODO comment present. Only matters if HTTP access reaches the backend. |
| In-memory rate limiters (per-process) | Low | Reset on server restart. Not Redis. Acceptable for single-server pilot. |
| Dead code `_handle_save()`, `_handle_test()` | Cosmetic | Unreachable methods in `api.py`. |

### Delivery/routing safety confirmed

- No automatic scheduler or cron found
- No bulk send endpoint
- `send_telegram_alert()` (global admin pipeline path) unchanged — confirmed separate from per-user delivery
- Per-user delivery: all sends go through authenticated user's pairing only
- `_is_still_approved()` re-checks at send time before delivery ✓

---

## 12. Mobile / Responsive Risks

Code inspection reveals the following likely mobile issues:

| Component | Risk | Detail |
|---|---|---|
| `Problem.jsx` | Wide 2-column grid | `sm:grid-cols-2` — falls to 1 on mobile. OK. |
| `DashboardHome.jsx` — stats row | OK | `grid-cols-2 lg:grid-cols-4` — 2 columns on mobile |
| `DashboardHome.jsx` — sample signal table | **High** | Full table with 6 columns (Risk, Market, Source, Title, Affected, Status). On mobile, horizontal scroll required but container may clip. `overflow-x-auto` is on the wrapper — should be OK, but dense. |
| `DashboardHome.jsx` — outer layout | **Medium** | `xl:grid-cols-[1fr_360px]` — fine on xl, but stacks at lg. 360px right panel as full-width column may look dense on tablet. |
| `AlertsPage.jsx` inner table | **High** | Multiple columns without overflow-x-auto noted in the component. Dense on mobile. |
| `AIBriefPage.jsx` + `ReportsPage.jsx` | **Medium** | `lg:grid-cols-[300px_1fr]` — stacks below lg. OK on mobile but vertical scroll may be long. |
| `Source Readiness HTML report` | **High** | CSS `.grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }` for stats — no responsive breakpoint. 4 columns will overflow on mobile screens. `.meta { grid-template-columns: repeat(4, minmax(0, 1fr)); }` same issue. `.table-wrap { overflow-x: auto; }` on source table — correct. |
| `SourceTransparencyMatrix.jsx` | **Medium** | 8-row table. Has `overflow-x-auto` wrapper. OK but headers may clip. |
| `Hero.jsx` mockup | Low | Dashboard mockup hidden elements at `hidden sm:flex`. Mobile shows simplified view. |
| `AppShell.jsx` mobile sidebar | OK | Slide-in drawer with overlay — correct mobile pattern |

**Summary:** The dashboard pages are dense on mobile. The most critical mobile issue is the source readiness HTML report (4-column grid stats, no responsive breakpoints). For a B2B product shown on desktop or tablet, these are acceptable. If the source readiness report is to be emailed and opened on phones, the template CSS needs `@media` breakpoints.

---

## 13. Client Demo Readiness

### Can landing be shown to a serious prospect?

**Yes, with one caveat.** The landing is honest, dark-premium, and UAE-first. The one issue is the `Problem.jsx` section breaking the dark theme with a white background. Fix this before a polished demo.

### Can dashboard be shown live?

**Yes, once RegisterPage/LoginPage demo-workspace text is removed.** After that fix, the dashboard is clean: pilot framing, sample labels, real backend connections, no fake live states.

### Can Telegram pairing be shown live?

**Yes.** Pairing is real, account-scoped, and functional. Requires an active bot with the pairing handler running.

### Can sample brief delivery be shown live?

**Yes.** D1 delivery is user-triggered, auth-required, idempotent (once/day). Requires bot running and user Telegram paired.

### Can approved alert routing preview be shown live?

**Conditionally.** Requires at least one approved reviewed alert artifact in `data/alert_reviews/reviews.jsonl`. If no artifacts exist, the empty state is clean and honest ("No approved reviewed alerts found in the last 14 days. No fake approved alerts are created for this empty state."). This can be shown as-is and framed as "the preview is ready — we need approved alert artifacts to populate it."

### Can Source Readiness Review be sent?

**Yes.** `reports/source_readiness_vasp_crypto_sample.html` is ready. StatuteProof branded, dark theme, honest limitations, "not legal advice" prominently displayed. The VASP sample is the strongest of the 7 profiles.

### What must be avoided

- Do not show RegisterPage or LoginPage until the "demo workspace" text is removed.
- Do not share `reports/sample_compliance_brief_en.md` — it says "RegRadar" and includes non-UAE content.
- Do not show the `TelegramSettings.jsx` page (it's dead code, but if somehow reached it would expose old bot name).
- Do not show or mention `run.py` CLI output — it still says "RegRadar v4".
- Do not show admin endpoints (all disabled, but the module docstring still lists them).
- Do not demonstrate email delivery, scheduled delivery, team accounts, or password reset — none exist.

---

## 14. P0 / P1 / P2 Fixes

### P0 — Must fix before showing to any prospect

| # | File | Fix |
|---|---|---|
| P0-1 | `web/src/components/auth/RegisterPage.jsx:69` | Change "Start with a demo workspace to see StatuteProof in action." to "Create your founding pilot workspace." |
| P0-2 | `web/src/components/auth/RegisterPage.jsx:144` | Remove or replace the notice box saying "This is a demo workspace. Production authentication will be enabled before client onboarding." — Auth IS real. Replace with: "Founding pilot workspace. Source coverage and brief delivery are validated per client." |
| P0-3 | `web/src/components/auth/LoginPage.jsx:127` | Same fix as P0-2 |

### P1 — Fix before serious pilot

| # | File | Fix |
|---|---|---|
| P1-1 | `web/src/components/Problem.jsx` | Convert `bg-slate-50` section to dark theme (`bg-[#07111F]` or `bg-slate-900`) to match rest of landing |
| P1-2 | `web/src/components/app/IntegrationsPage.jsx` | Update stale copy "Personalized alert delivery is configured in the next pilot step." → "Manual reviewed alert preview delivery is available in Alerts. Automatic production routing is the next pilot step." |
| P1-3 | `web/src/components/app/OnboardingPage.jsx:44644` | Step 4: Reword "StatuteProof will connect to official sources, extract regulatory updates, and generate AI compliance briefs based on this profile." → "StatuteProof monitors official UAE sources and delivers reviewed briefs matched to your regulatory profile. Coverage and delivery expand as sources are validated." |
| P1-4 | `web/src/components/app/SettingsPage.jsx` | Remove "Russian" and "Both (EN + RU)" language options from `languageLabel`/`languageCode` functions. UAE-first product. |
| P1-5 | `web/src/components/auth/LoginPage.jsx` left-panel quote | Change "Regulatory monitoring for undercovered and fast-changing markets." → "Official-source regulatory intelligence for UAE financial firms." |
| P1-6 | `web/src/App.jsx`, all affected components | Rename `regradar_workspace_profile`, `regradar_onboarding_complete`, `regradar_user_registered` localStorage keys to `statuteproof_workspace_profile`, etc. (affects: App.jsx, SettingsPage.jsx, OnboardingPage.jsx, SourcesPage.jsx, AppSidebar.jsx, AppTopbar.jsx, workspaceProfile.js) |
| P1-7 | `app/report.py:583-584` | Change output filenames from `regradar_report_YYYY-MM-DD.md/html` to `statuteproof_report_YYYY-MM-DD.md/html` |
| P1-8 | `app/api.py` module docstring | Update "RegRadar minimal API server" → "StatuteProof API server", update endpoint list |
| P1-9 | `app/templates/source_readiness_report.html` | Add `@media (max-width: 768px)` breakpoints for `.meta`, `.grid` to collapse 4-column layouts to 2-column or 1-column on mobile |
| P1-10 | `app/api.py` | Add `require_auth` check to `/api/source-test` handler |

### P2 — Nice to have

| # | File | Fix |
|---|---|---|
| P2-1 | `web/src/components/TelegramSettings.jsx` | Delete dead code file (never imported, contains old bot name) |
| P2-2 | `app/api.py` | Remove dead code `_handle_save()` and `_handle_test()` methods |
| P2-3 | `app/api.py` | Move `_ALLOWED_ORIGIN = "http://localhost:5173"` to `os.getenv("ALLOWED_ORIGIN", "http://localhost:5173")` |
| P2-4 | `app/auth.py` | Strengthen `validate_password()` to require at least one digit or symbol |
| P2-5 | `app/auth.py`, `app/db.py` | Add `is_admin` column and `require_admin()` for future admin endpoints |
| P2-6 | `app/api.py` | Add CSRF double-submit or `X-Requested-With` header check for cookie-authenticated mutations |
| P2-7 | `app/config.py` | Update "RegRadar v3" docstring, add `STATUTEPROOF_DB_PATH` as alias for `REGRADAR_DB_PATH` |
| P2-8 | `run.py` docstring | Update "RegRadar v10/v4" → "StatuteProof" |
| P2-9 | `web/index.html` | Add `<meta property="og:image">` for social sharing preview |
| P2-10 | `web/index.html` | Rename favicon asset from `regradar-favicon-512.png` to `statuteproof-favicon.png` |
| P2-11 | `reports/sample_compliance_brief_en.md` | Rebrand to StatuteProof, remove non-UAE briefs (MASAK Turkey, ARDFM Kazakhstan) |
| P2-12 | `web/src/components/app/DashboardHome.jsx` | Add delivery logs link in dashboard (API exists, no UI surface yet) |
| P2-13 | `app/auth.py` | Add `Secure` cookie flag when `HTTPS_ENABLED=true` env var |

---

## 15. Recommended Next Sprint

### Sprint: Design E2 — Auth Page Polish + Landing Dark Consistency

**Scope:** 1–2 days. Pure frontend, no backend changes.

**Why this sprint first:** The P0 issues are all frontend copy. The P1 design issues (Problem.jsx dark theme, onboarding copy, IntegrationsPage copy, auth page language) are also frontend. This sprint unblocks showing the product to a prospect without any embarrassing text. Zero backend risk.

**Tasks:**

1. Fix RegisterPage and LoginPage demo-workspace notice boxes (P0-1 through P0-3).
2. Convert Problem.jsx to dark theme (P1-1).
3. Update IntegrationsPage stale copy (P1-2).
4. Reword onboarding Step 4 text (P1-3).
5. Remove Russian/Both language options from SettingsPage (P1-4).
6. Update LoginPage left-panel quote (P1-5).
7. Rename `regradar_*` localStorage keys to `statuteproof_*` (P1-6) — do all affected files in one sweep.
8. Add `@media` breakpoints to source readiness HTML template for 4-column grids (P1-9) — affects only `app/templates/source_readiness_report.html`.
9. Delete dead code `TelegramSettings.jsx` (P2-1).

**Validation:**
- `cd web && npm run build`
- `git diff --check`
- Visual walkthrough: landing → register → onboarding → dashboard → integrations → alerts → source readiness report on mobile viewport

**After this sprint:** Product is ready to demo to a first pilot prospect.

**Sprint after that:** Auth E2 (P1-10 + P2-3 through P2-8) — security hardening remaining items.
