# StatuteProof Mega Project Code Map

Date: 2026-06-14

## 1. Top-Level Structure

StatuteProof is organized as an operating workspace with the product implementation under `product/regradar`.

| Path | Purpose |
| --- | --- |
| `product/regradar/app/` | Python backend, parser/source-intake, evidence, auth, delivery, risk and brief modules. |
| `product/regradar/run.py` | CLI entrypoint for health, source readiness, Source Lab, source testing, API server, alert review, weekly brief, and operational commands. |
| `product/regradar/sources.json` | Source registry for all configured sources. Current registry has 13 enabled UAE sources, with 9 marked active and 4 marked remediation. |
| `product/regradar/tests/` | Python tests for source intake, parser benchmarks, alert review, proof/diff, weekly briefs, and text normalization. |
| `product/regradar/web/` | React/Vite frontend for public site, auth screens, and logged-in app. |
| `tools/` | Workspace validators and packaging scripts. |
| `.agents/skills/`, `agents/`, `workflows/`, `prompts/` | Repo-scoped agent, skill, and workflow operating system. |
| `docs/` | Product, parser, source-readiness, visual-upgrade, deployment, cleanup, and audit reports. |

Generated/runtime data is under `product/regradar/data/`. Runtime alert queue JSON, source runs, snapshots, and local database files are ignored by `.gitignore` and should not be committed.

## 2. Backend Modules

| Module | Role |
| --- | --- |
| `api.py` | Dependency-light HTTP API server for auth, profile, plan, Telegram pairing, delivery previews, source status/readiness, evidence, briefs, contact, and Source Lab endpoints. |
| `auth.py` | Email/password auth, PBKDF2 hashing, server-side sessions, and session-cookie parsing. |
| `db.py` | SQLite persistence, document table migrations, auth/profile/session/delivery-log table setup. |
| `source_tester.py` | URL safety checks, public URL validation, basic source testing, source JSON append helpers. |
| `scraper.py` | Two-tier fetcher: requests first, Playwright fallback, plus per-source `wait_for_selector` and `content_selector`. |
| `extractors.py` | Main HTML extraction utilities. |
| `providers/html_extraction.py` | Provider cascade: selector via selectolax, trafilatura, readability, selectolax fallback, BeautifulSoup. |
| `providers/pdf_extraction.py` | PDF provider cascade: PyMuPDF, pdfplumber, pypdf. |
| `source_intake.py` | Source Lab/source-intake orchestration, quality scoring, nav-shell/collision detection, no-save vs evidence write, activation-readiness contract, batch readiness summary. |
| `source_quality.py` | Strict quality scorecard and policy warnings for login/CAPTCHA/paywall/private-source signals. |
| `source_certification.py` | Internal activation-readiness model. It still uses technical `certification` naming internally, while customer-facing UI maps this to safer activation/readiness language. |
| `source_readiness.py` | Market readiness reporting from `sources.json`, audits, source runs, and optional record-run mode. |
| `source_runs.py` | Append-only JSONL source run history, snapshots, proof artifacts, diff artifacts, and alert-queue creation for changed runs. |
| `proof.py` | Source proof block builder and proof-quality classification. |
| `chunk_diff.py`, `diff.py` | Structured diff generation and legacy diff support. |
| `risk.py` | Offline rule-based risk scoring for diffs. |
| `ai_brief.py` | AI-assisted brief generation with rule-based fallback and legal-safe prompt constraints. |
| `alert_drafts.py` | Draft-only alert artifact generation from proof/diff. |
| `alert_review.py` | Human review workflow, review records, and safety gates before delivery. |
| `weekly_brief.py` | Weekly brief generator from human-approved alert drafts only. |
| `plan.py` | Plan state and capability definitions. No Stripe/payment processing. |
| `profile.py`, `client_profiles.py` | Workspace and client profile persistence/scoring helpers. |
| `telegram_*`, `user_delivery.py`, `alert_routing.py` | Telegram pairing, delivery logs, sample brief/test delivery, and preview routing. |

## 3. Frontend Routes And Components

Routes are centralized in `product/regradar/web/src/routeMap.js`.

| Route | Component / View |
| --- | --- |
| `/` | Public landing page via `App.jsx` and sections in `components/`. |
| `/pricing` | `components/PricingPage.jsx`. |
| `/source-readiness-review` | `components/SourceReadinessReviewPage.jsx`. |
| `/login` | `components/auth/LoginPage.jsx`. |
| `/register` | `components/auth/RegisterPage.jsx`. |
| `/terms` | `components/legal/TermsPage.jsx`. |
| `/privacy` | `components/legal/PrivacyPage.jsx`. |
| `/disclaimer` | `components/legal/DisclaimerPage.jsx`. |
| `/app/dashboard` | `components/app/DashboardHome.jsx` inside `AppShell.jsx`. |
| `/app/sources` | `components/app/SourcesPage.jsx`. |
| `/app/source-lab` and `/app/sources/new` | `components/app/SourceLabPage.jsx`. |
| `/app/evidence` | `components/app/EvidencePage.jsx`. |
| `/app/alerts` | `components/app/AlertsPage.jsx`. |
| `/app/briefs` | `components/app/AIBriefPage.jsx`. |
| `/app/reports` | `components/app/ReportsPage.jsx`. |
| `/app/integrations` | `components/app/IntegrationsPage.jsx`. |
| `/app/billing` | `components/app/BillingPage.jsx`. |
| `/app/settings` | `components/app/SettingsPage.jsx`. |
| `/app/choose-plan` | `components/app/ChoosePlanPage.jsx`. |

The frontend uses mock/sample data for many app surfaces (`data/appMockData.js`) but also calls live API endpoints for auth, profile, plan, source status, delivery preview/logs, Telegram pairing, Source Lab, and evidence when available.

## 4. API Endpoints

`product/regradar/app/api.py` exposes:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/auth/register` | Create user, session cookie, and default profile/plan. |
| `POST` | `/api/auth/login` | Authenticate and set session cookie. |
| `POST` | `/api/auth/logout` | Delete session and clear cookie. |
| `GET` | `/api/auth/me` | Return current authenticated user. |
| `GET` / `PUT` | `/api/profile` | Load/update workspace profile. |
| `GET` / `POST` | `/api/plan` | Load or record plan intent. This does not process payment. |
| `GET` | `/api/sources/status?market=AE` | Authenticated source status from `sources.json` merged with latest source runs. |
| `GET` | `/api/sources/readiness` | Authenticated readiness summary from stored runs and registry. |
| `POST` | `/api/source-test` | Legacy/compat source test endpoint. |
| `POST` | `/api/custom-sources/test` | No-save Source Lab test. Returns readiness, quality, provider, hash preview, evidence level, activation readiness, warnings, and remediation hints. |
| `GET` / `POST` | `/api/custom-sources` | List custom sources or save a tested public source for validation. Save does not activate monitoring. |
| `GET` | `/api/evidence` | Authenticated source run/evidence list from local JSONL, if present. |
| `GET` | `/api/briefs` | Authenticated alert queue brief list, if present. |
| `GET` / `POST` | `/api/settings/telegram` | Legacy Telegram settings API. |
| `POST` | `/api/telegram/pair/generate`, `/api/telegram/pair/unlink`, `/api/telegram/test` | Account-level Telegram pairing and test message handling. |
| `GET` / `POST` | `/api/delivery/*` | Delivery logs, preview routing, sample brief, and reviewed preview alert delivery. |
| `POST` | `/api/contact` | Contact/source-review intake, queues locally and optionally delivers if configured. |
| `GET` | `/api/health` | Health check. |

## 5. Parser / Source-Intake Flow

1. User or CLI submits a source URL/spec.
2. `source_tester.validate_public_url()` blocks non-http(s), credentials, localhost/private networks, and restricted patterns.
3. `scraper.fetch_page_with_config()` fetches via Playwright when forced or when selectors are configured; otherwise `fetch_page()` tries requests then Playwright fallback.
4. `source_intake.run_source_intake()` extracts text from HTML/PDF providers, normalizes text, computes hash, checks expected length, detects nav-shell content, and checks collisions against configured sources.
5. `source_quality.build_quality_score()` creates a score, warnings, and penalties. No proof/no-save penalizes the score.
6. `source_intake.build_source_lab_contract()` separates preview, evidence, baseline, and monitoring activation readiness.
7. No-save Source Lab tests return `PREVIEW_ONLY` evidence level and cannot activate monitoring.
8. Evidence write mode creates snapshots, provider/quality reports, proof artifacts, source run JSONL entries, and activation-readiness metadata.

## 6. Evidence / Proof Flow

1. `source_runs.record_from_source_result()` builds a run record from fetch/extract output.
2. `_write_snapshots()` writes raw, normalized, metadata, and optional PDF text snapshots under `product/regradar/data/source_snapshots/`.
3. `append_run()` classifies change status against the previous run and appends to `data/source_runs/source_runs.jsonl`.
4. Changed runs write diff artifacts and proof artifacts.
5. `proof.build_source_proof()` creates a proof block with official/final URL, hashes, paths, change status, extraction quality, limitations, and disclaimer.
6. `alert_drafts.py` can build draft alerts from changed runs, but only human-approved alerts are eligible for weekly briefs or delivery.

## 7. Risk / Brief Flow

The risk/brief stack is deliberately gated:

1. Source change/diff produces a local alert draft.
2. `alert_drafts.py` classifies change type and conservative risk from diff/proof.
3. `client_profiles.py` scores relevance to a profile.
4. `alert_review.py` requires explicit review actions and blocks unsafe urgent approval when proof/diff/relevance checks fail.
5. `weekly_brief.py` includes only approved weekly/urgent alerts and applies legal/QA gates before rendering.
6. Frontend brief/evidence/alert pages still show sample/demo material unless live API data is present.

## 8. Auth / Account Flow

Registration and login call `/api/auth/register` and `/api/auth/login`; both create server-side sessions. Frontend requests use `credentials: include` and dispatch `auth:expired` on 401.

Security notes:

- Password hashing uses PBKDF2-SHA256 with 600,000 iterations.
- Session cookies are `HttpOnly`, `SameSite=Strict`, and currently set as `Secure`.
- Vite proxies `/api` to `http://127.0.0.1:5001`, so local HTTP auth behavior should be tested carefully because secure cookies may not persist over HTTP.
- Password reset and Google OAuth are intentionally disabled placeholders.

## 9. Pricing / Billing Flow

`plan.py` and `data/planCapabilities.js` define:

- Source Readiness Review: free, no live monitoring.
- Founding Pilot: $199/month, manually activated, up to 3 official UAE sources.
- UAE Monitor: $399/month, manually activated, 13 enabled UAE source scope under readiness review.
- Compliance Consultant: talk to us, custom/manual scope.

There is no Stripe checkout in the current flow. `/api/plan` records plan intent only. Billing copy correctly says manual activation/no payment method stored, but the plan state itself marks selected paid plans as `active`, which can read stronger than the operational reality.

## 10. Agents / Skills / Workflows

The project keeps exactly 10 agent roles in `AGENTS.md`, with parser/source tasks routed through:

- Source Monitor
- Evidence Trail
- Code Architect
- QA / Critic
- Legal Language
- Product Manager for customer-facing readiness
- Chief of Staff only for multi-step coordination

Repo-scoped skills live in `.agents/skills/`, including source monitoring, evidence readiness, custom source parser, legal-safe copy, webapp testing, TDD, systematic debugging, prompt-injection review, and project review. `workflows/08-parser-source-intake-review.md` documents the source URL to evidence/legal/QA review path.

## 11. Tests / Validators

| Command / File | Purpose |
| --- | --- |
| `python3 -m pytest product/regradar/tests/test_source_intake.py` | Source-intake safety, no-save/evidence/activation behavior, nav-shell/collision tests. |
| `python3 -m pytest product/regradar/tests/test_parser_benchmark_suite.py` | Parser benchmark behavior. |
| `python3 -m pytest product/regradar/tests/test_chunk_diff_and_proof.py` | Diff/proof artifact behavior. |
| `python3 -m pytest product/regradar/tests/test_alert_review.py` | Human review and safety gates. |
| `python3 -m pytest product/regradar/tests/test_weekly_brief.py` | Weekly brief gate behavior. |
| `tools/validate_parser_quality.py` | Parser/source-intake structural and claim-safety gate. |
| `tools/validate_workspace.py` | Workspace structure/secrets/runtime-data gate. |
| `tools/validate_codex_skills.py` | Repo-scoped skill validation. |
| `product/regradar/web/scripts/validate-routes.mjs` | Required route/deep-link validation. |
| `npm run build`, `npm run lint` in `product/regradar/web` | Frontend build/lint. |

## 12. Deployment / Hosting Clues

The repo contains deployment/hosting docs but this audit did not deploy. Current operational clues point to a Python API behind a frontend build/proxy arrangement, with Cloudflare/DigitalOcean excluded from this task. README and older docs contain some stale path/location language that should be corrected before future handoff.

## 13. Generated / Runtime Data Paths

Do not commit:

- `product/regradar/data/source_runs/*.jsonl`
- `product/regradar/data/source_snapshots/`
- `product/regradar/data/alert_queue/*.json`
- `product/regradar/data/alert_reviews/*.jsonl`
- local SQLite databases
- `.env` and `.env.*`
- `.reference_parser_repos/`
- `node_modules/`, `dist/`, caches, and `__pycache__/`

## 14. Current Known Risks

1. Canonical source-readiness truth is split: current user instruction says 13 enabled / 10 confirmed / 3 remediation, while committed registry/validator/docs/frontend currently represent 13 enabled / 9 readiness-supported / 4 remediation.
2. DFSA current source URLs remain in remediation; the deeper rulebook/AML page candidates produced better no-save extraction but are not yet saved, baselined, or modeled.
3. Evidence surfaces mix sample data and API data. The labels are visible, but a customer demo still needs a strict script to avoid implying live evidence where none exists.
4. Auth/session behavior needs local/prod browser verification because cookies are `Secure` while Vite development is HTTP.
5. Paid plan selection records intent but marks non-free plans as `active`; this is operationally different from manual billing activation.
6. Source Lab and Sources pages both expose custom-source testing flows; Source Lab is stronger, while the older modal in Sources has less advanced control and could diverge.
7. Several older docs/specs contain stale wording from previous product states and should be archived or reconciled before external review.
