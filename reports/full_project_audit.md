# StatuteProof Full Project Audit
Audit date: 2026-06-24
Auditor: CTO / Product / QA / Legal / Sales / Security multi-role audit
Coverage: All areas A through N

---

## 1. Executive Summary

StatuteProof is a UAE-first regulatory monitoring tool in early internal alpha. The pipeline is real and runs. Source runs, SHA-256 hashes, diffs, and proof files are generated for 116 genuinely enabled sources (all AE jurisdiction). The frontend is built, well-styled, and mostly legally safe. The backend is a raw-socket Python HTTP server (not WSGI/ASGI), which is functional but fragile at scale.

The biggest structural problem is a divergence between the internal source-quality audit document (claiming 246 enabled, 180 fresh-alert eligible) and the actual sources.json at runtime (116 enabled, all sources have status=active, no candidate status). Five pytest tests fail because test truth-tables were never updated after sources were disabled. The frontend `sourceQualityAudit.ts` hardcodes counts of 246/180 that are stale by 130 sources.

No paying customers exist. No production SQLite database file is present on the development machine. No Stripe payment links are wired. The product is pre-revenue but has legitimate evidence of real regulatory monitoring work.

**Current stage: Internal Alpha. Not yet paid-pilot-ready. Conditionally close.**

---

## 2. Brutal Truth

1. The source count shown in `sourceQualityAudit.ts` (totalEnabled: 246, freshAlertEligible: 180) is wrong. The actual JSON has 116 enabled sources. This is the most important single error in the product — it inflates every monitoring claim by 2.1x.
2. Five tests fail because truth tables inside tests still reference 246 as the enabled count. Tests are out of date, not wrong about the requirement.
3. The "Legislation / gazettes" SourceTransparencyMatrix row says "0 fresh-alert eligible" while BuyerSourcePacks.jsx says "UAE Legislation Portal and Dubai Legislation Portal are fresh-alert eligible" — direct contradiction in the same deployed UI.
4. The `SourceTransparencyMatrix.jsx` VARA row says "24 fresh-alert eligible" but the internal audit says 25. ADGM row says "10" but audit says 11. DIFC/DFSA row says "26" but audit has DFSA=16 and DIFC=11 (27 total). None of these numbers match.
5. No customer users exist in the database (the DB file doesn't exist on the dev machine — it lives on the VPS). No paid plans are active. Stripe links are empty strings.
6. The rate limiter is in-memory and global, not per-IP. Every request from any IP increments the same shared counter. On restart, all counters reset. A distributed attack would bypass it completely.
7. The API server is a hand-rolled `BaseHTTPRequestHandler` — it has no async, no connection pool, no graceful shutdown, and is subject to head-of-line blocking under concurrent load.
8. Alert queue contains 7+ PENDING_REVIEW records from June 11-15 that have never been human-reviewed (delivery_approved: False, human_reviewed: False). No evidence of review workflow being completed.
9. The `sourceQualityAudit.ts` file has a comment saying "Do not hand-edit. Regenerate from product/regradar/reports/source_signal_quality_audit.json" but the report file also shows 246 total enabled — both are stale/wrong.
10. There is no nginx reverse proxy config in the codebase. The systemd service binds directly to port 5001 on `0.0.0.0`. If this is the production setup, the API is exposed without SSL termination or a proper reverse proxy layer.

---

## 3. Current Project State

- Backend: Python 3.x, raw http.server, SQLite, Playwright for JS-heavy sources
- Frontend: React 19 + Vite + Tailwind CSS v4, builds successfully in 387ms
- Monitoring: 866 source runs logged, 289 unique sources run at least once, 39 sources CHANGED
- Evidence: SHA-256 normalized hash + proof.json + snapshot artifacts per run
- Auth: PBKDF2-SHA256 password hashing, 600k iterations, Google OAuth supported
- Delivery: Telegram alerts (2 bots: admin/founder + customer alerts), email delivery framework
- Tests: 598 collected, 593 passing, 5 failing (all stale truth-table assertions)
- Stripe: Not configured (empty payment links)
- Production DB: Not present on dev machine (expected on VPS)
- Customers: Zero paying customers confirmed from local evidence

---

## 4. What Is Genuinely Strong

1. **Pipeline integrity**: SHA-256 hashing, diff generation, proof files, snapshot artifacts — the evidence chain design is solid and genuinely differentiating.
2. **Evidence record schema**: `evidence_records.py` enforces hash verification before canonical evidence creation. Blocked statuses (FAILED, QUALITY_DROP) cannot produce customer briefs. This is exactly correct.
3. **Legal copy**: The Hero, Coverage, Features, LegalPage, and Pricing components all use appropriately hedged language. "Monitoring intelligence only. Not legal advice." appears where it should. SAMPLE/FAKE labels are on demo content. This is above average for a pre-revenue tool.
4. **Test coverage breadth**: 54 test files, 598 tests, covering adapter platform, auth, evidence records, canonical review workflow, pipeline utils, alert drafts, diff classification, parser benchmarks, and more. Impressive for the stage.
5. **Source transparency**: The Coverage and SourceTransparencyMatrix components disclose exactly what is NOT monitored (geo-blocked sources, static PDFs, nav-shell-only pages). This is honest marketing.
6. **Rate limiting on auth endpoints**: Register (5/hr), Login (10/hr), Contact (3/hr) are all rate-limited. Not per-IP, but present.
7. **Security headers**: All API responses include X-Content-Type-Options, X-Frame-Options, HSTS, Referrer-Policy, Permissions-Policy.
8. **PBKDF2 at 600k iterations**: Password hashing is current-best-practice strength.
9. **Two-bot Telegram architecture**: Clean separation of founder admin bot from customer alerts bot, with clear environment variable segregation.
10. **Circuit breaker**: Per-source circuit breaker prevents a single broken source from blocking the monitoring run. Persists to disk across restarts.

---

## 5. What Is Weak

1. **Stale source counts everywhere**: sourceQualityAudit.ts, source_signal_quality_audit.md, and SourceTransparencyMatrix.jsx all have wrong counts that don't match sources.json.
2. **Rate limiter is global/in-memory**: Cannot distinguish legitimate users from attackers. Resets on restart. One legitimate heavy user can block all others.
3. **No nginx/SSL config in codebase**: Deployment is missing the reverse proxy layer documentation. Security relies entirely on the VPS network setup being correct.
4. **Hand-rolled HTTP server**: No middleware, no proper routing, no async, no connection pooling. The `do_GET` / `do_POST` switch-case in api.py will become unmaintainable at scale.
5. **No email verification**: Users can register with any email and immediately access the dashboard without confirming ownership.
6. **Alert queue reviews are never completed**: 7 CHANGED alerts from June 11-15 sit in PENDING_REVIEW with delivery_approved=False. No evidence of a review workflow being executed in production.
7. **Stripe payment links are empty**: Users who click "Start founding pilot" or "UAE Monitor" get no payment flow. The CTA fires a blank link or falls back to the workspace flow.
8. **Frontend mock data mismatch**: mockData.js `coverage` array shows only 13 sources while the actual Coverage component pulls from its own hardcoded data — the two arrays are not synced.
9. **No frontend tests**: Zero frontend test files. No Playwright E2E, no Vitest unit tests.
10. **sourceQualityAudit.ts is marked "auto-generated" but is stale**: It was last generated for a 246-source registry that no longer exists.

---

## 6. What Is Missing

1. Stripe payment link integration (empty strings in constants.js)
2. Email verification flow for new registrations
3. Per-IP rate limiting (current is global in-memory)
4. nginx / SSL termination configuration documented in the repo
5. Frontend test suite (zero tests)
6. Completed human review workflow for any alert queue item (0 reviewed)
7. A completed customer delivery (end-to-end brief delivery to a real user)
8. A production-ready WSGI/ASGI server (gunicorn, uvicorn, or equivalent)
9. Customer onboarding documentation (no START_HERE for the pilot user)
10. SCA AML/CFT parser/noise remediation (noted as blocking in multiple places)
11. MoJ/Gazette monitoring (explicitly held at 0 fresh-alert eligible)
12. ADGM FSRA dedicated regulatory-alerts page (candidate, pending selector remediation)

---

## 7. What Is Misleading or Inflated

1. **sourceQualityAudit.ts**: `totalEnabled: 246` is 2.1x the actual 116. This flows into any UI that reads this file.
2. **SourceTransparencyMatrix VARA**: "24 fresh-alert eligible" — actual audit says 25. Minor but wrong.
3. **SourceTransparencyMatrix ADGM/FSRA**: "10 fresh-alert eligible" — audit says 11. Minor but wrong.
4. **SourceTransparencyMatrix DIFC/DFSA**: "26 fresh-alert eligible across DIFC/DFSA" — audit says DFSA=16, DIFC=11 (27 total). Wrong.
5. **BuyerSourcePacks.jsx vs SourceTransparencyMatrix**: One says legislation portal is fresh-alert eligible; the other says "0 fresh-alert eligible" for legislation/gazettes. Direct contradiction.
6. **"Monitoring active" live indicator on hero**: The live dot implies continuous real-time monitoring. The reality is a scheduled batch process (default: every 60 minutes) and the most recent run was June 21 — 3 days before this audit date.
7. **Hero metric "116 UAE official sources monitored"**: Technically accurate for enabled sources, but the `sourceQualityAudit.ts` (read by any UI component that imports it) says 246. Mixed signals.
8. **source_signal_quality_audit.md**: Claims 246 enabled, 180 fresh-alert eligible. Reality: 116 enabled.

---

## 8. Source Quality Assessment

### Actual Counts from sources.json (authoritative)
- Total records: 432
- Enabled: 116 (all AE jurisdiction)
- Active + enabled: 116 (status=active for all enabled sources)
- Candidate count: 0 (zero — all candidates have been resolved)
- Geo-blocked: 18
- Disabled subtypes: disabled_non_uae (86), disabled_static_pdf (48), disabled_covered_by_hub (56), disabled_static_doc (35), disabled_path_moved (15), disabled_external_access (13), disabled_duplicate (3), disabled_navigation_only (4), disabled_needs_playwright (2), disabled_geo_blocked (1), disabled (6)

### Active Sources by Family (from URL analysis)
- CBUAE: 25 sources
- DFSA: 16 sources
- ADGM/FSRA: 14 sources
- DIFC: 12 sources (including DIFC Courts, DIFCCOURTS.ae)
- MoE: 9 sources
- MoF: 8 sources (includes some non-MoF misclassified)
- FTA: 6 sources (actual from URL: tax.gov.ae / fta.gov.ae)
- VARA: 6 sources (direct vara.ae)
- UAE CMA/SCA: 6 sources
- EOCN: 5 sources
- Other (DLP, DFM, ICP, TDRA, MOCCAE, JAFZA, DMCC): 9 sources
- MoJ: 2 sources

### Family Strength Assessment
- **Strong**: CBUAE (25), DFSA (16), ADGM/FSRA (14) — core financial regulators well covered
- **Good**: DIFC (12), MoE (9) — reasonable depth
- **Partial**: VARA (6 direct — other VARA sources may be counted via PDF/adapter approach), FTA (6 direct, PDF-heavy), SCA (6), UAE CMA (6)
- **Weak**: MoJ (2 — 0 fresh-alert eligible per transparency matrix), UAE FIU (limited circulars coverage)
- **Missing entirely**: Official Gazette (geo-blocked), UAE e-Laws (geo-blocked), federal PDPL/TDRA (geo-blocked)

---

## 9. Evidence Trail Assessment

**Design is correct.** The evidence chain (fetch → extract → hash → diff → proof.json → canonical evidence record → human review gate) follows industry best practice for regulatory monitoring evidence.

**Implementation gaps:**
- 866 source runs exist but 0 have `monitor_ok` flag (this field exists in the schema but is not set by the intake pipeline — it's set by a separate validation step)
- 7 CHANGED alert queue items from June 11-15 have `human_reviewed: False` and `delivery_approved: False` — never processed
- Canonical evidence record creation requires proof.json + normalized snapshot + metadata path + hash verification. This is enforced in code.
- `internal_briefs/` directory contains 40 subdirectories, suggesting internal brief generation has been run for key sources
- No completed customer-grade canonical evidence records with a review decision are visible from local files

The evidence trail design is the product's biggest genuine differentiator. The execution has the right structure but zero completed review cycles visible locally.

---

## 10. Monitoring Reliability Assessment

- 866 runs over approximately 3.5 weeks (May 29 - June 21)
- 289 unique sources run at least once
- 116 currently enabled, suggesting many of the 289 were disabled after testing
- 51 FAILED runs (5.9%)
- 10 QUALITY_DROP runs (1.2%)
- 41 restricted access runs (4.7%)
- 453 UNCHANGED (52.3%) — expected for stable regulatory text
- 286 FIRST_SEEN (33%) — expected during source activation phase
- 66 CHANGED (7.6%) — real regulatory text changes detected across 39 sources

**Reliability concern**: Most recent runs are June 21 (3 days ago as of audit). If the server is running, the monitoring has been quiet for 3 days. If the server is not running, that's a reliability gap.

**No 7-day, 30-day, or 90-day reliability metrics are tracked or displayed.** This is a P1 gap for customer trust.

---

## 11. Backend Architecture Assessment

**Framework**: Raw Python `http.server.BaseHTTPRequestHandler`. This is a toy-grade HTTP server. It:
- Has no async capability (blocking I/O)
- Has no proper routing framework (giant if/elif chain in `do_GET` / `do_POST`)
- Has no connection pooling
- Has no graceful shutdown
- Has no middleware architecture

**What works well**:
- SQLite with WAL mode + busy_timeout is correct for single-server low-concurrency workloads
- PBKDF2 at 600k iterations is correct
- Security headers on every response
- Rate limiting present (global, not per-IP)
- Circuit breaker for monitoring (persists to disk)
- Adapter registry with per-URL adapter dispatch

**Production risk**: Under any meaningful load (10+ concurrent users, or a burst from a compliance team sending the dashboard to colleagues), the http.server will stall. The monitoring background thread + multiple API requests will compete. No concurrency controls.

**SQLite concurrency**: WAL mode + busy_timeout handles low-concurrency well. For a 5-user pilot it is fine. For anything more it needs migration to PostgreSQL.

---

## 12. Frontend / UI Assessment

**Build**: Passes clean. 387ms build time. Main chunk 229KB gzipped to 72KB — acceptable.

**Design quality**: Above average for a pre-revenue B2B compliance tool. Dark mode with intentional navy/cyan palette. Evidence dossier panel with rotating SAMPLE/FAKE cards is effective. The ChainStrip process visualization is clear.

**Claims in UI**:
- Hero: "116 UAE official sources monitored" — accurate for enabled count
- Hero: "24h Check cycle — every source, every day" — the default WATCH_INTERVAL_MINUTES is 60 (hourly), not every 24h. This is misleading: "every 24h" implies a once-per-day cycle but the system can run hourly. However it could also be read as "within a 24h period". Ambiguous.
- sourceQualityAudit.ts: totalEnabled 246 (wrong — 116)
- SourceTransparencyMatrix: multiple per-family counts are wrong (see section 7)
- BuyerSourcePacks: "UAE Legislation Portal and Dubai Legislation Portal are fresh-alert eligible" — contradicts SourceTransparencyMatrix "0 fresh-alert eligible"

**Dashboard**: App dashboard reads live from the API. Source counts, profile settings, Telegram pairing, alert queue are all wired. The `DashboardHome` hardcodes `REMEDIATION_SOURCE_IDS` with `AE-uae-legislation-portal` — correct.

**Demo/sample data**: All sample briefs, evidence records, and alert cards have SAMPLE/FAKE labels. This is correct.

**Stripe**: Payment CTAs fire blank (`STRIPE_LINK_FOUNDING_PILOT = ''`) — the button falls through to `onSelectPlan` but there's no Stripe checkout on that path. Dead-end for a paying customer.

---

## 13. Legal / Copy Claims Assessment

**Strong**:
- "Monitoring intelligence only. Not legal advice." — present in Hero
- SAMPLE/FAKE labeling on all demo content
- Coverage component discloses NOT_AVAILABLE_SOURCES and CAVEAT_SOURCES
- LegalPage has comprehensive service terms, evidence disclaimers, and the standard disclaimer
- Pricing uses hedged language ("Manually activated after source readiness review")

**Weak / needs fix**:
- "Monitoring active" live indicator with green dot — implies real-time; should clarify "batch monitoring" or "scheduled monitoring"
- sourceQualityAudit.ts totalEnabled 246 — if this ever reaches a customer-facing surface, it inflates the claim
- BuyerSourcePacks legislation claim contradicts SourceTransparencyMatrix
- SourceTransparencyMatrix per-family counts are wrong (see above)

**No forbidden claims found**: No "guarantee compliance", "prevent fines", "AI lawyer", "never miss an update", "100% accurate", "automated compliance decisions". The copy discipline is good.

---

## 14. Sales Readiness Assessment

**Pre-conditions for a paid pilot:**
1. Stripe payment links configured — NOT DONE
2. Email verification for account registration — NOT DONE
3. At least one completed human-reviewed alert delivered to a real user — NOT DONE
4. Source count claims corrected — NOT DONE (wrong by 2.1x in stale files)
5. Customer onboarding documentation — NOT DONE

**What IS ready:**
- Registration and login functional
- Telegram pairing functional (customer bot flow documented in CLAUDE.md)
- Source readiness review page exists and correctly shows source status
- Pricing page exists with realistic tiers ($0 readiness review, $199 Founding Pilot, $399 UAE Monitor)
- Sample brief, audit binder sample, and demo reports are labeled correctly
- Legal terms and privacy policy are present

**Verdict**: Conditionally ready for 1-3 hand-held founder pilots at $0 (source readiness review tier), but NOT ready for self-serve paid pilots. The founder needs to manually complete the payment collection and activation.

---

## 15. Security / Ops Assessment

**Positive**:
- PBKDF2 at 600k iterations — strong
- Security headers on all responses
- SESSION_COOKIE_NAME with 7-day TTL
- Google OAuth PKCE flow with state validation
- Rate limiting on auth endpoints
- No secrets in the frontend (Stripe links are empty, not leaking live keys)
- .env.example clearly documents required vs optional vars
- `validate_config()` warns about default SECRET_KEY

**Negative**:
- Rate limiter is global in-memory (not per-IP). A single bursty legitimate user can block all other users from registering/logging in.
- No nginx reverse proxy config in the repo — SSL termination and production hardening are undocumented
- SECRET_KEY defaults to a placeholder string. If a VPS was ever started without the .env correctly configured, sessions would be insecure.
- No CSRF protection. The API uses cookies for auth; a CSRF attack could send authenticated requests. CORS is set via env var but is not a CSRF protection.
- No rate limiting on source test endpoint (`/api/sources/test`) beyond 10/hr global — could be used to probe external sites at the server's expense.
- No monitoring of the SQLite DB file size — could grow unbounded with 866+ runs and snapshots.

---

## 16. Testing / Validator Assessment

**593/598 tests passing** is strong for this stage.

**5 failing tests**:
1. `test_ideal_product_workflow.py::test_source_summary_reads_current_registry_truth` — expects 246 enabled, gets 116
2. `test_source_signal_quality_audit_truth.py::test_source_signal_quality_audit_matches_current_registry_truth` — stale truth table
3. `test_source_signal_quality_audit_truth.py::test_source_signal_quality_family_readiness_matches_registry_truth` — stale truth table
4. `test_source_signal_quality_audit_truth.py::test_source_signal_quality_audit_validator_rejects_stale_counts` — stale truth table
5. `test_source_signal_quality_audit_truth.py::test_frontend_source_quality_export_matches_safe_audit_claims` — missing SCA safe claim string in sourceQualityAudit.ts

All 5 failures are caused by the sourceQualityAudit.ts / source_signal_quality_audit files not being regenerated after sources were disabled. The 116 vs 246 discrepancy is the root cause.

**Test coverage gaps**:
- No frontend tests (0 files)
- No E2E tests (no Playwright)
- No load/performance tests
- No integration tests against the live VPS API
- No test for the rate limiter behavior (global vs per-IP)

---

## 17. Documentation Assessment

**Strong**:
- CLAUDE.md is detailed and accurate about Telegram architecture, two-bot setup, and product positioning
- docs/ has 80+ files covering adapter specs, council reports, activation plans, baseline reports
- .env.example is comprehensive and clearly annotated

**Weak**:
- No START_HERE document for a new pilot customer
- No deployment runbook (nginx config, SSL setup, VPS onboarding steps)
- source_signal_quality_audit.md and sourceQualityAudit.ts are stale and marked as authoritative
- Many docs in docs/ are internal spec documents, not user-facing documentation
- No public-facing help/FAQ

**Contradictions**:
- docs/ contains docs claiming 246 sources while sources.json has 116
- Multiple docs reference counts that were valid at the time of writing but are now stale

---

## 18. Deployment Readiness Assessment

**What exists**:
- systemd service files for API, Telegram bot, CBUAE rulebook watch
- .env.example template with all variables documented
- `run.py` dispatch for api / watch / all / telegram-listen subcommands
- `validate-config` subcommand to check config before deployment

**What is missing**:
- nginx configuration (no nginx.conf in the codebase)
- SSL certificate management instructions
- Database backup/restore procedure
- Log rotation configuration
- Health check endpoint documentation (there is `/health` but it's not documented externally)
- Capacity planning (what's the expected load? how many concurrent users before http.server breaks?)
- Rollback procedure
- Zero-downtime deployment procedure

**Deployment risk**: The API server is a single-process http.server. Any unhandled exception could bring it down. The systemd `Restart=always` provides recovery, but there's a gap window. Playwright processes from the monitoring thread could leak if not properly terminated.

---

## 19. Top 10 Critical Blockers (P0)

1. **Regenerate sourceQualityAudit.ts from actual sources.json** — all 5 failing tests and multiple UI inconsistencies stem from this single stale file
2. **Fix SourceTransparencyMatrix per-family source counts** — VARA, ADGM, DIFC/DFSA counts are wrong
3. **Resolve BuyerSourcePacks vs SourceTransparencyMatrix legislation contradiction** — same product, opposite claims about UAE Legislation Portal
4. **Wire Stripe payment links** — current CTAs are dead-ends
5. **Complete at least one human-reviewed alert delivery** — the review queue has 7 un-reviewed items from 13 days ago; no evidence of a working delivery pipeline
6. **Fix rate limiter to be per-IP** — current global counter can be trivially abused or accidentally denied
7. **Add nginx config + SSL setup to deployment docs** — production is currently running without documented SSL termination
8. **Update the 5 failing tests** to reflect actual source counts (or regenerate the truth files)
9. **Add email verification** before granting dashboard access
10. **Document source reliability SLA** — "24h" in the hero metric is ambiguous; define what check frequency means for customers

---

## 20. Top 10 Product Improvements

1. Display real-time source reliability stats (7-day success %, last run timestamp) on the dashboard
2. Show alert queue review status to the logged-in customer (not just internal)
3. Add a source health timeline widget to the dashboard
4. Build a completed brief delivery flow end-to-end (at least one real customer delivery)
5. Add email verification at registration
6. Build a proper "Evidence Pack" download for a completed review cycle
7. Add a "Why this alert" explanation tied to the diff content and source family
8. Build the consultant/multi-workspace plan onboarding (currently just an email CTA)
9. Add the "30-day reliability report" as a product feature (the data exists in source_runs.jsonl)
10. Replace the "Monitoring active" live dot with "Last scan: [timestamp]" showing the actual freshness

---

## 21. Top 10 Engineering Improvements

1. Replace http.server with gunicorn + a proper WSGI app (or FastAPI + uvicorn) — current server will fail under any real load
2. Make rate limiter per-IP by extracting client IP from X-Forwarded-For (behind nginx)
3. Add CSRF protection (double-submit cookie or SameSite=Strict cookie policy)
4. Add an nginx config file to the repo with SSL termination, rate limiting, and proxy headers
5. Migrate from SQLite to PostgreSQL when more than 5 concurrent users are expected
6. Add a frontend test suite (Vitest for unit tests, Playwright for E2E)
7. Add a health check that returns monitoring pipeline status, not just "ok"
8. Add log rotation configuration to the deployment docs
9. Add database backup cron job to the deployment docs
10. Replace the manual api.py routing (giant if/elif) with a proper router

---

## 22. Top 10 Source / Evidence Improvements

1. Regenerate source_signal_quality_audit.json from actual sources.json and commit the correct counts everywhere
2. Complete human review for the 7 pending alert queue items from June 11-15
3. Complete at least one canonical evidence record with a review decision
4. Add monitor_ok flag tracking to the intake pipeline run record
5. Activate UAE CMA broader adapter remediation (SCA AML/CFT noise review is blocking)
6. Remediate ADGM FSRA dedicated regulatory-alerts page (candidate, selector issue)
7. Add 7-day reliability metrics to the source registry (% accessible, % failed, % CHANGED)
8. Activate MoJ/UAE Legislation Portal fresh-alert eligible path (currently at 0)
9. Fix FTA portal/listing extraction (5 pages failed nav-shell check on June 18)
10. Add geo-block mitigation plan for Official Gazette (proxy, UAE-based server, or partnership)

---

## 23. Top 10 Sales / Positioning Improvements

1. Fix all source count inconsistencies before any external sales deck is built
2. Build a sample "source readiness report" PDF that can be shared with prospects before sign-up
3. Add a concrete case study: "On [date], CBUAE page X changed, here is the diff, here is the brief" — even one real example is worth more than 10 features
4. Define and publish the SLA: "Sources are checked every [X] hours. Evidence is retained for [Y] days."
5. Define which UAE licence types are the best-fit ICP (VASP, DFSA-regulated, ADGM-regulated, bank, payment service provider) — the product currently speaks to all without prioritizing
6. Create a 1-page pilot scope document for the founding pilot ($199) — what exactly do they get?
7. Add a "Disclosure before pilot" document that lists all known access limitations up front — this is a sales tool, not just a legal protection
8. Wire Stripe so interested users can actually pay
9. Add a testimonial slot on the landing page — even one beta user quote helps
10. Add "Used by compliance teams at [industry type]" social proof even if anonymized

---

## 24. What to Remove or Downgrade

1. **sourceQualityAudit.ts** "totalEnabled: 246" — replace with correct count
2. **"Monitoring active" live green dot** — downgrade to "Scheduled monitoring" or show last scan timestamp
3. **"24h Check cycle — every source, every day"** — clarify this is a scheduled batch, default 60-minute interval
4. **BuyerSourcePacks UAE Legislation Portal "fresh-alert eligible" claim** — remove or caveat; contradicts SourceTransparencyMatrix
5. **source_signal_quality_audit.md** stale counts — must be regenerated before use
6. **mockData.js coverage array** (13 items) — stale and no longer used by Coverage component, should be removed or updated to prevent confusion
7. The **"Most Popular" badge on UAE Monitor plan** — not justified by any customer data yet
8. Remove non-AE jurisdictions from sources.json or at minimum document why they are there (RU, KZ, AZ, BY, UZ, INT, GE, AM, TR, QA, SA, SG, HK, BH, MY are all disabled_non_uae but still in the file)

---

## 25. What to Add

1. Per-IP rate limiting
2. Email verification on registration
3. nginx config with SSL termination
4. Stripe payment links (both plans)
5. At least one completed canonical evidence record with human review
6. Source reliability dashboard (7-day / 30-day access success %)
7. Frontend test suite (Vitest + Playwright)
8. START_HERE onboarding doc for pilot customers
9. Completed brief delivery to at least one user
10. "Last scan" timestamp display instead of "Monitoring active" animation

---

## 26. What to Validate Next

1. Run a fresh `python3 run.py all` on the VPS and confirm MONITOR_OK status for all 116 sources
2. Complete one full human review cycle: pick a CHANGED alert, write the brief, deliver to an internal email
3. Verify that the VPS API is running with the correct SECRET_KEY (not the placeholder)
4. Confirm that nginx is running with SSL termination on the VPS
5. Run the audit regeneration script to produce a correct source_signal_quality_audit.json
6. Verify Google OAuth redirect URI is configured correctly for production domain

---

## 27. Safe Pilot Scope

For a founding pilot at $199/mo:
- 3 manually selected UAE sources from a strong family (e.g., CBUAE AML/CFT rulebook module, DFSA AML module, VARA compliance rulebook)
- Daily check cycle
- Evidence records with SHA-256 hash + timestamp per run
- Human-reviewed brief when CHANGED is detected (founder reviews before delivery)
- Delivery via email or Telegram
- 30-day evidence retention
- Source readiness report before activation
- Full disclosure: which sources are in scope, which are out of scope, all known limitations

This scope is achievable with current infrastructure today.

---

## 28. Unsafe Claims to Avoid

- "246 UAE sources monitored" — wrong, actual is 116
- "180 fresh-alert eligible" — wrong, this was the stale audit count
- Any claim implying real-time monitoring (the system runs on a schedule)
- "Never miss a regulatory update"
- "Complete UAE regulatory coverage"
- "Guarantee compliance"
- "AI-powered compliance" — AI analysis is disabled by default (ENABLE_AI_ANALYSIS=false) and limited to 3 calls per run when enabled
- "UAE Legislation Portal is fresh-alert eligible" — it is in remediation
- "FIU circulars are monitored" — the circulars endpoint resolves to the general publications index

---

## 29. 30-Day Action Plan

**Week 1 (fix blockers)**
- Regenerate source_signal_quality_audit.json from actual sources.json
- Update sourceQualityAudit.ts with correct counts
- Fix SourceTransparencyMatrix per-family counts
- Remove or caveat BuyerSourcePacks legislation claim
- Fix 5 failing tests
- Wire Stripe payment links (both plans)

**Week 2 (operations)**
- Complete at least 1 human-reviewed alert delivery
- Add nginx config to the repo
- Add per-IP rate limiting
- Add email verification to registration flow
- Add "last scan" timestamp to hero metric

**Week 3 (pilot prep)**
- Write the 1-page pilot scope document
- Write the "before pilot" disclosure document
- Contact 3-5 compliance professionals for source readiness review sessions
- Produce one real sample brief from a CHANGED alert (labeled REAL or SAMPLE/FAKE as appropriate)

**Week 4 (first revenue)**
- Activate first paid pilot with full manual activation
- Deliver first weekly brief
- Collect feedback
- Fix any blocking UX issues

---

## 30. Final Scorecard

| Dimension | Score | Reasoning |
|---|---|---|
| Product clarity | 6/10 | The concept is clear, the positioning is honest, but source count inconsistencies undermine trust |
| Commercial value | 7/10 | Genuine compliance problem, clear workflow, honest pricing — weak only on missing payment flow |
| Source quality | 6/10 | 116 real enabled sources with proof records is solid for a pre-revenue tool, but several families are partial |
| Evidence integrity | 8/10 | Hash chain design is correct, canonical evidence gates are enforced, proof files exist — pending completed review cycles |
| Monitoring reliability | 5/10 | 866 runs, 5.9% failure rate, 0 reliability metrics surfaced, last run 3 days ago, 7 un-reviewed alerts |
| Backend maturity | 4/10 | Hand-rolled HTTP server, global rate limiter, no WSGI, no CSRF — functional but fragile |
| Frontend maturity | 7/10 | Builds clean, well-styled, legally safe copy, but wrong counts in 3 places and no tests |
| Legal claim safety | 7/10 | Better than average. No forbidden claims. SAMPLE/FAKE labels present. Stale counts are the main risk. |
| Sales readiness | 4/10 | No Stripe, no completed delivery, no paying customers, no pilot scope document |
| Production readiness | 4/10 | No nginx config documented, SECRET_KEY warning, global rate limiter, no DB on dev machine |
| **Overall readiness** | **5.8/10** | |

**Current stage**: Internal Alpha  
**Closest to**: Pilot-ready once Stripe, email verification, first review cycle, and count corrections are done  
**Time to paid-pilot-ready**: 2-3 weeks of focused execution on the P0 blockers

---

*Audit conducted by multi-role audit process. No code changes were made. No production systems were touched.*
