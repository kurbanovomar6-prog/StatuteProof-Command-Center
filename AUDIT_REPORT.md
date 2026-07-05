# AUDIT_REPORT — StatuteProof, 2026-07-04

Auditor mode: read-only for source code. All findings below were verified by running commands on this machine on 2026-07-04. Test artifacts created during the audit (one test user, one outbox file) were removed afterwards.

---

## 1. EXECUTIVE VERDICT

Roughly **70% of the codebase works as engineering; roughly 0% of it is operating as a service.** Fetch, extract, hash, diff, evidence storage, API, auth, and dashboard all run and pass their tests. But: **the production site statuteproof.com is completely down** (all ports dead), monitoring has not run since **2026-06-21** (13 days), there is **no scheduler anywhere** so it never runs unless the founder types a command, **no email provider is configured** so new signups can never verify and never log in, and **zero alerts have ever been delivered to any user** (`user_delivery_log` = 0 rows, all 43 queued alerts stuck in PENDING_REVIEW).

**The single biggest lie:** the landing page and dashboard say *"checks each configured official source every 24 hours"* / *"Monitoring active"* (pulsing green dot). There is no cron job, no launchd agent, no systemd timer, no watch process — nothing schedules monitoring, and the badge renders unconditionally whenever the API responds.

**Is there a demonstrable core?** YES — the local pipeline (`run.py test-source`, evidence records, diffs) plus the local dashboard is a genuinely good founder-driven demo. It is not a running service and cannot be sold as one today.

---

## 2. WORKS (proven, with evidence)

- **Backend test suite**: `python3.14 -m pytest tests -q` → **598 passed, 0 failed, 17.45s**. Sampled tests are real assertions (normalization, hashing, quality gates), not `assert True`. All offline/fixture-based — none exercise live sources or a live server.
- **Frontend build**: `npm run build` → ✓ built in 490ms. Code-split; main bundle 229KB / **72KB gzip** (within budget).
- **Frontend tests**: `npm run test:run` → **43 passed (3 files)**.
- **Live fetching of active sources — works right now.** Tested 5 enabled Tier-A sources with `run.py test-source` on 2026-07-04; **all 5 fetched with extraction quality "good"**: vara.ae (46,852 PDF chars incl. OCR), dfsa.ae MLRO letters (33 PDFs found), DFSA Thomson Reuters rulebook, and 2× rulebook.centralbank.ae (58–60 PDFs found, OCR fallback working). One sub-PDF returned HTTP 403, correctly flagged.
- **API server**: `run.py api` boots (ThreadingHTTPServer), `/api/health` → 200 in 36ms. Auth (register/login/logout/session cookie), profile, sources, evidence, briefs, reviews, plan, delivery-status endpoints all returned 200 with real data (timed: 4ms–37ms, except `sources/status` — see §6).
- **Auth flow**: register → verification token → `/api/auth/verify-email` → login works end-to-end (I completed it by reading the token from the DB, because the email itself is never sent — see §3).
- **Dashboard**: renders **real backend data** (83 fresh-alert eligible, 17 changes needing review, honest "Brief delivery: Blocked" gate). No mock data in the logged-in app; onboarding wizard (4 steps) and plan-selection work.
- **Evidence trail**: 502 files under `evidence/` (raw, normalized, metadata, evidence-record.json, hashes). 866 run records in `data/source_runs/source_runs.jsonl` with SHA-256 hashes, timestamps, artifact paths.
- **Diff meaningfulness**: of 66 CHANGED runs, **60 have `diff_quality: GOOD` and `meaningful_change_detected: true`**; normalization strips noise before hashing. Diffing is not noisy junk.
- **Telegram (admin bot)**: `run.py env-check` → getMe OK for @StatuteProof_bot; a `telegram-listen` process for customer pairing has been running since 21 Jun. Both bot tokens are SET in `.env`.

## 3. BROKEN (with exact break point)

1. **Production site is DOWN — not "laggy", dead.** `curl https://statuteproof.com/` → timeout after 75s, HTTP 000. TCP to 207.154.250.157 (DigitalOcean VPS, per `docs/actual-hosting-location-audit.md`): ports **443, 80, and 22 all unreachable, 100% packet loss** (control probes to example.com / digitalocean.com / vara.ae all fine from this machine). The VPS is offline, suspended, or firewalled. Every downstream claim ("the site lags") is moot until this is fixed.
2. **No scheduler exists.** `crontab -l` → "no crontab". No LaunchAgents, no running `run.py watch` process. Last monitoring run: **2026-06-21T21:45:18Z**. 0 runs since 2026-06-24. Monitoring happens only when run by hand.
3. **New users can never log in.** Email provider is `local_outbox` (default; `SMTP_HOST` / `RESEND_API_KEY` / `EMAIL_PROVIDER` all MISSING from `.env`). Registration succeeds, but the verification email is written to `data/outbox/*.json` on disk and **never sent**. Login is blocked until verified → every real signup dead-ends. Verified live during audit.
4. **Alert chain breaks at human review + delivery.** Trace of one change end-to-end: pipeline → run record → evidence → alert draft → **[BREAK 1]** all **43/43** queue items are `PENDING_REVIEW` (only 1 review record ever) → routing (`app/alert_routing.py`, self-described *"dry-run"*; nothing in `pipeline.py`/`monitor.py` calls it) → **[BREAK 2]** delivery: email in test mode, **no user has Telegram paired** (all `user_profiles.telegram_chat_id` NULL) → **`user_delivery_log`: 0 rows. Nothing has ever reached a customer.**
5. **Local dev requires an unadvertised Python.** `run.py` demands ≥3.11; system python3 is 3.9.6. Works only via the 3.14 framework install at `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3` — not documented anywhere in the repo.

## 4. FAKE OR MISLEADING

- **"Monitoring active" badge (dashboard + landing hero)** — `web/src/components/app/DashboardHome.jsx:417` and `Hero.jsx:318` (with pulsing "live dot"). Rendered unconditionally whenever the sources API loads; still shows green with monitoring 13 days dead. Never checks `last_run_at`.
- **"Checks each configured source every 24 hours… twice daily for high-priority"** — `HowItWorks.jsx:14`, `PricingPage.jsx:159`, "Daily automated monitoring" in `MonitoringProfile.jsx:316`. FALSE: no scheduling mechanism exists in the repo or on this machine, and the run log proves multi-day gaps then total stop.
- **Permanent "System status: degraded" banner — the opposite fake.** `AppTopbar.jsx:44` checks `d.status === 'ok'` but `/api/health` returns `{"ok": true, …}` with **no `status` field**, so every app page always shows "degraded. Data may be incomplete." even when healthy. (Note: the *production* health payload recorded in June returned `{"status": "ok"}` — a different, older backend than this repo. Prod and repo had diverged even before prod died.)
- **`/api/health` reports `"sources_active": 116, "changed_count": 66`** with a 13-day-old `last_run_at` — technically present in the payload but every consumer ignores staleness.
- **Landing demo components** (`InteractiveDemo.jsx`, `DemoReport.jsx`) render invented regulatory content with **no SAMPLE/FAKE label** (0 matches), violating the workspace's own CLAUDE.md legal-safety rule. `DashboardPreview.jsx` has exactly 1 label.
- Honest bits, credit where due: brief delivery is genuinely gated "Blocked", alerts page says "manual/test-mode", pricing says "no automatic charges". The scaffolding of honesty exists; the monitoring-cadence claims and the badge undercut it.

## 5. DEAD CODE / OVERBUILD

- **`product/` top level (everything except `regradar/`)** — an abandoned earlier build: `main.py` (NiceGUI+FastAPI), `mvp_core.py` (Crawl4AI pipeline v2), `app.py`, `celery_app.py`, `scheduler_workers.py`, `database.py`, `app/` (DDD scaffold: api/application/core/infrastructure/presentation), `src/pages`, `services/`, `snapshots/`, its own Dockerfile/Makefile/Procfile/docker-compose. Nothing in `product/regradar/` imports any of it. Ironically it contains the Celery scheduler the real product lacks. Delete or archive.
- **`product/regradar/StatuteProof-Command-Center_SAFE_2026-06-11.zip` (92MB)** — a zip of the repo inside the repo. Delete.
- **`product/regradar/repopack-output.txt`, `demo_output.txt`, `coverage.json`** — generated artifacts committed to the tree.
- **`web/src/data/appMockData.js`** — imported by nothing (grep: 0 usages).
- **`.claude/agents/`** — hundreds of untracked claude-flow agent definitions (swarm/hive-mind/neural/consensus/payments…) dumped into the workspace; unrelated to StatuteProof's 10 documented roles.
- **`data/` is 140MB** growing station_corpus/diagnostics with no retention policy.

## 6. DASHBOARD VERDICT

**ONLY A 2-MINUTE HAPPY PATH.** Justification:

- All 11 app pages render without crashes; Dashboard, Evidence (94KB of real records), Briefs, Reports show real backend data; Alerts/Review Queue/Sources render honest empty-or-thin states for a new user.
- But every page carries the false red "System status: degraded" banner (bug, §4) next to a false "Monitoring active" badge — a compliance customer will ask about that contradiction within the first minute.
- Data is frozen at 2026-06-21; "17 changes needing review" never changes.
- Lag: **not a frontend problem locally** — dev landing DCL ~153ms, build 72KB gzip, no polling loops, only `/api/sources/status` is slow (~1.1s over 3 runs, 90KB, rebuilt from `sources.json` + 866-line JSONL on every request, no cache). The owner's "site lags" is the production VPS dying, not this code.
- A demo works only if: run locally, logged in as a pre-verified user, and stays away from questions about live delivery ("send me this alert" cannot be honored — email test-mode, no Telegram pairing).

## 7. TOP 5 FIXES (ranked by "needed to demo core value to one customer")

1. **Bring statuteproof.com back or redeploy.** Check the DigitalOcean droplet (207.154.250.157) — restore, or redeploy `web/dist` + `run.py api` behind nginx (`deploy/nginx.conf.example` already exists) on a fresh host / Railway (`railway.toml` ready). **Effort: M.** Proof: `curl https://statuteproof.com/api/health` → 200 and homepage TTFB < 1s from a cold client, and the deployed backend is *this* repo's code (health payload contains `"ok": true` and `last_run_at`).
2. **Make monitoring actually recur.** One systemd timer / cron entry on the server running `run.py all` daily (files for systemd already exist in `deploy/systemd/` — wire them up). **Effort: S.** Proof: `data/source_runs/source_runs.jsonl` gains new `timestamp_utc` entries on 3 consecutive days with no human action.
3. **Configure a real email provider** (`STATUTEPROOF_EMAIL_PROVIDER` + SMTP/Postmark/SendGrid keys) so verification emails send and signups can log in. **Effort: S.** Proof: register with a real mailbox → receive link → verify → log in, with zero manual DB touches.
4. **Kill the two false status signals**: fix `AppTopbar.jsx:44` to read the actual health payload, and gate "Monitoring active" (`DashboardHome.jsx:417`, `Hero.jsx:318`) on `last_run_at` freshness (< 48h), showing a stale state otherwise. Also align `HowItWorks.jsx:14` / `PricingPage.jsx:159` cadence copy with whatever schedule fix #2 actually implements. **Effort: S.** Proof: with a fresh run, banner is green; stop the scheduler 2 days → dashboard says monitoring is stale.
5. **Deliver one real alert to one real channel.** Review the 43 pending queue items, approve the genuine ones, pair one Telegram account via the existing `/start SP-XXXXXX` flow, and send one approved alert. **Effort: M.** Proof: `user_delivery_log` has ≥1 row with `status=sent` and the message is visible in a Telegram client.

## 8. UNVERIFIED

- **Why the VPS is down** (billing, crash, firewall) — no server access from this audit; SSH port also filtered.
- **Which code version production ran** before dying — June health payload differs from this repo; can't diff a dead server.
- **Customer alerts bot (@statuteproofalerts_bot) end-to-end pairing/sending** — token SET and listener process alive since 21 Jun, but no paired user exists and sending a test would message a real founder chat; not exercised.
- **AI analysis / AI briefs** — `ENABLE_AI_ANALYSIS=false`, no `ANTHROPIC_API_KEY`; code paths untested.
- **Google OAuth** — `GOOGLE_CLIENT_ID` missing; untestable.
- **Production-scale performance of the full 116-source run** (duration, ban risk) — only 5 sources fetched live to avoid hammering regulators from a residential IP.
- **Payment/billing** — by design there is none ("manually activated"); nothing to test.
- **`.env` contents beyond presence booleans** — deliberately not read.
