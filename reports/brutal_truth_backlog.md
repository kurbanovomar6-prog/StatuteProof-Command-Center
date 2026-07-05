# StatuteProof Brutal Truth Backlog
Audit date: 2026-06-24

---

## P0 — Blocks paid pilot / trust / legal safety

### P0-1: Fix stale source counts across all surfaces
**Why it matters**: The sourceQualityAudit.ts file claims 246 enabled sources and 180 fresh-alert eligible. The actual sources.json has 116 enabled sources. This is a 2.1x inflation of every monitoring claim. If a sales conversation references this number, it is a false claim.

**Files involved**:
- `product/regradar/web/src/data/sourceQualityAudit.ts` (claims totalEnabled: 246)
- `product/regradar/reports/source_signal_quality_audit.md` (claims 246 enabled, 180 fresh-alert)
- `product/regradar/reports/source_signal_quality_audit.json` (source of the wrong numbers)
- `product/regradar/tests/test_source_signal_quality_audit_truth.py` (5 failing tests referencing 246)
- `product/regradar/tests/test_ideal_product_workflow.py` (1 failing test expecting 246)

**Acceptance criteria**:
- `python3 -m pytest tests/test_source_signal_quality_audit_truth.py tests/test_ideal_product_workflow.py -v` passes all tests
- `sourceQualityAudit.ts` totalEnabled reflects the actual sources.json enabled count
- `source_signal_quality_audit.md` counts match sources.json

**Validation command**:
```bash
cd product/regradar
python3 -c "import json; s=json.load(open('sources.json')); print(sum(1 for x in s if x.get('enabled')))"
python3 -m pytest tests/test_source_signal_quality_audit_truth.py tests/test_ideal_product_workflow.py -v
```

**Owner role**: Source Monitor Agent + Engineer
**Difficulty**: Medium — the audit regeneration script exists (`reports/validate_audit.py`), needs to be run and committed

---

### P0-2: Fix per-family source count inconsistencies in SourceTransparencyMatrix.jsx
**Why it matters**: The VARA row says "24 fresh-alert eligible" (audit says 25). ADGM says "10" (audit says 11). DIFC/DFSA says "26" (audit has 16+11=27). A prospect who looks at both Coverage and SourceTransparencyMatrix sees contradictions.

**Files involved**:
- `product/regradar/web/src/components/SourceTransparencyMatrix.jsx` (wrong per-family counts)

**Acceptance criteria**:
- All counts in SourceTransparencyMatrix match the regenerated source_signal_quality_audit.json
- No count in SourceTransparencyMatrix is higher than in the audit

**Validation command**:
Manual comparison of SourceTransparencyMatrix vs regenerated audit JSON

**Owner role**: Engineer + QA Critic
**Difficulty**: Low — data fix only

---

### P0-3: Resolve BuyerSourcePacks vs SourceTransparencyMatrix legislation contradiction
**Why it matters**: BuyerSourcePacks.jsx says "UAE Legislation Portal and Dubai Legislation Portal are fresh-alert eligible." SourceTransparencyMatrix shows "0 fresh-alert eligible" for legislation/gazettes. These are opposite claims about the same sources in the same deployed product.

**Files involved**:
- `product/regradar/web/src/components/BuyerSourcePacks.jsx` (line ~167)
- `product/regradar/web/src/components/SourceTransparencyMatrix.jsx` (line 62-67)

**Acceptance criteria**:
- Both components agree on the status of UAE Legislation Portal
- If fresh-alert eligible: both say so with the same caveats
- If not: BuyerSourcePacks removes the claim

**Validation command**:
Visual inspection of both components rendered in browser

**Owner role**: Product + Legal Language Agent
**Difficulty**: Low — copy fix

---

### P0-4: Wire Stripe payment links
**Why it matters**: Users who click "Start founding pilot" ($199/mo) or "UAE Monitor" ($399/mo) get no payment flow. The CTA silently falls back to workspace registration. A prospect who wants to pay has no way to do so.

**Files involved**:
- `product/regradar/web/src/data/constants.js` (STRIPE_LINK_FOUNDING_PILOT and STRIPE_LINK_UAE_MONITOR are empty strings)

**Acceptance criteria**:
- Both Stripe links point to real, tested Stripe Payment Link URLs
- Clicking "Start founding pilot" opens the Stripe checkout
- After payment, the user is directed to registration or workspace activation

**Validation command**:
Manual test: click both CTAs and confirm they reach Stripe checkout

**Owner role**: Founder (requires Stripe account action)
**Difficulty**: Low (Stripe side: create payment link in dashboard, copy URL, add to constants.js)

---

### P0-5: Complete at least one human-reviewed alert delivery
**Why it matters**: There are 7+ CHANGED alerts in the queue from June 11-15 with delivery_approved: False and human_reviewed: False. The product claims to deliver human-reviewed briefs. No brief has ever been delivered. The review workflow has never been executed in production.

**Files involved**:
- `product/regradar/data/alert_queue/` (7 PENDING_REVIEW items)
- `product/regradar/app/alert_review.py`
- `product/regradar/app/alert_actions.py`
- `product/regradar/tools/generate_internal_non_customer_brief.py`

**Acceptance criteria**:
- At least 1 alert queue item has human_reviewed: True and a review decision
- At least 1 internal brief is generated and delivered to the founder's email/Telegram
- The review log shows the reviewer name, decision, and timestamp

**Validation command**:
```bash
python3 -c "import json,os; q=[f for f in os.listdir('product/regradar/data/alert_queue') if f.endswith('.json')]; [print(json.load(open('product/regradar/data/alert_queue/'+f))['human_reviewed']) for f in q[:3]]"
```

**Owner role**: Founder + Source Monitor Agent
**Difficulty**: Medium — requires active founder review of a real diff

---

### P0-6: Fix rate limiter to per-IP
**Why it matters**: The current `_RateLimiter` uses a single in-memory counter keyed by a label (e.g., "auth_register"). All users share the same counter. 5 registration attempts from any IPs exhausts the register limit for all users until the hour resets. Conversely, an attacker can probe the login endpoint from one IP and block legitimate users.

**Files involved**:
- `product/regradar/app/api.py` (class `_RateLimiter`, `_rate_limited()` method, all limiter calls)

**Acceptance criteria**:
- Rate limiter keys on IP address (extract from `X-Forwarded-For` if behind nginx, else `client_address[0]`)
- Burst from one IP does not affect other IPs
- Rate limit state is still in-memory (persistence is a future improvement)

**Validation command**:
```python
# Manual test: open 6 browser tabs, attempt registration 5 times → confirm 6th returns 429
# Open a different IP session → confirm registration still works
```

**Owner role**: Engineer
**Difficulty**: Low-Medium

---

### P0-7: Add email verification before dashboard access
**Why it matters**: Users can register with any email address and immediately access the full dashboard. A compliance-grade product should verify email ownership before granting access to evidence records and source configurations.

**Files involved**:
- `product/regradar/app/auth.py` (create_user function — email_verified defaults to 0 but is never enforced)
- `product/regradar/app/api.py` (registration and login handlers)
- `product/regradar/app/email_delivery.py` (email infrastructure exists)

**Acceptance criteria**:
- After registration, a verification email is sent
- Dashboard access is gated on `email_verified = 1`
- A resend verification link exists
- Google OAuth users are considered verified (they go through Google's own verification)

**Validation command**:
```bash
# Register a new test account, confirm dashboard access is denied until email clicked
```

**Owner role**: Engineer
**Difficulty**: Medium

---

### P0-8: Document nginx / SSL setup in the repo
**Why it matters**: The systemd service binds to `0.0.0.0:5001`. If no nginx sits in front, the API is unprotected HTTP on a public IP. There is no nginx.conf or SSL termination documentation in the codebase. A new deployment would not know how to set this up.

**Files involved**:
- `product/regradar/deploy/` (add nginx config here)
- README or deployment.md (none exists)

**Acceptance criteria**:
- An `nginx.conf` or `nginx.conf.example` exists in `deploy/`
- It includes: SSL termination, proxy_pass to 127.0.0.1:5001, rate limiting headers, HSTS
- A deployment README exists listing all steps from a clean Ubuntu VPS

**Validation command**:
```bash
# Can a new engineer follow the deploy docs and have a working HTTPS deployment in under 2 hours?
```

**Owner role**: Engineer + DevOps
**Difficulty**: Medium

---

### P0-9: Clarify "24h Check cycle" metric in hero
**Why it matters**: The hero shows "24h — Check cycle — every source, every day." The default WATCH_INTERVAL_MINUTES is 60 (hourly). "24h" implies once per day. This is either wrong (if the system runs hourly) or misleading (if it means "within a 24-hour window"). Either way it needs to be accurate.

**Files involved**:
- `product/regradar/web/src/components/Hero.jsx` (trust metrics section)

**Acceptance criteria**:
- The metric accurately describes the actual check frequency
- If hourly: change to "1h" or "60-min" with label "Check cycle — every source, every hour"
- If daily: confirm the VPS is configured with daily runs and update docs accordingly

**Validation command**:
```bash
grep "WATCH_INTERVAL_MINUTES\|watchInterval\|watch_interval" product/regradar/app/config.py product/regradar/.env.example
```

**Owner role**: Founder + Product
**Difficulty**: Trivial (copy change)

---

### P0-10: Ensure SECRET_KEY is not the placeholder in production
**Why it matters**: If the VPS was ever started without a properly configured .env, the SECRET_KEY defaults to `change-me-to-a-random-64-char-string`. All sessions signed with this key are insecure. Anyone who knows the placeholder can forge session tokens.

**Files involved**:
- `product/regradar/.env` on the VPS (NOT checked into git)
- `product/regradar/app/config.py` (validate_config function warns about this)

**Acceptance criteria**:
- Running `python3 run.py validate-config` on the VPS shows zero warnings about SECRET_KEY
- The SECRET_KEY in production is at least 64 random characters

**Validation command**:
```bash
cd /srv/regradar && python3 run.py validate-config
```

**Owner role**: Founder
**Difficulty**: Trivial

---

## P1 — Blocks strong demo / repeatability

### P1-1: Replace hand-rolled http.server with gunicorn or uvicorn
**Why it matters**: Under any real load (multiple concurrent dashboard users, monitoring thread + API requests), the raw http.server will stall. The monitoring background thread competes with API handlers for the GIL.

**Files involved**: `product/regradar/run.py`, `product/regradar/app/api.py`, systemd service files

**Acceptance criteria**:
- API runs behind gunicorn with 2-4 workers
- Monitoring thread runs in a separate process (or use gunicorn --preload with proper shutdown)
- Response times under 10 concurrent users remain under 500ms for simple GET requests

**Validation command**:
```bash
ab -n 100 -c 10 http://localhost:5001/api/health
```

**Owner role**: Engineer
**Difficulty**: Medium-High

---

### P1-2: Add a frontend test suite
**Why it matters**: Zero frontend tests. Any UI regression is invisible until a customer reports it. Especially risky given the source count inconsistencies that currently exist.

**Files involved**: `product/regradar/web/` (add test infrastructure)

**Acceptance criteria**:
- Vitest configured and runs at least 10 unit tests for data transforms and component logic
- One Playwright E2E test covers: landing page loads → register → dashboard visible

**Validation command**:
```bash
cd product/regradar/web && npm test && npm run e2e
```

**Owner role**: Engineer
**Difficulty**: Medium

---

### P1-3: Add CSRF protection
**Why it matters**: Cookie-based auth without CSRF protection means a malicious website can make authenticated requests to the API on behalf of a logged-in user (e.g., to update Telegram settings, trigger source scans).

**Files involved**: `product/regradar/app/api.py`

**Acceptance criteria**:
- All state-changing endpoints (POST, PUT) require a CSRF token in the request body or header
- Or: set SameSite=Strict on the session cookie (simpler but requires all flows to be same-origin)

**Validation command**:
```bash
# Test: make a cross-origin POST to /api/settings/telegram without CSRF token → expect 403
```

**Owner role**: Engineer
**Difficulty**: Medium

---

### P1-4: Add source reliability dashboard metric
**Why it matters**: Customers need to see how reliable their source monitoring is. "116 UAE official sources monitored" is a count. "114/116 sources accessible in the last 7 days" is a trust signal.

**Files involved**:
- `product/regradar/data/source_runs/source_runs.jsonl` (data exists)
- `product/regradar/app/source_health_timeline.py` (may already support this)
- Dashboard frontend components

**Acceptance criteria**:
- Dashboard shows 7-day access success rate per source
- "Last checked" timestamp visible for each enabled source
- Failed sources highlighted with reason

**Validation command**: Visual inspection of dashboard with data loaded

**Owner role**: Engineer + Product
**Difficulty**: Medium

---

### P1-5: Complete canonical evidence record for at least one CHANGED source
**Why it matters**: The evidence record design is the product's core differentiator. No canonical evidence record with a completed human review exists (as far as local files show). Without one, the "evidence trail" claim is unproven in production.

**Files involved**:
- `product/regradar/tools/generate_canonical_evidence.py`
- `product/regradar/app/evidence_records.py`
- `product/regradar/data/evidence_reviews/`

**Acceptance criteria**:
- At least 1 canonical evidence record exists in `data/evidence/` with a review decision
- `data/evidence_reviews/canonical_evidence_reviews.jsonl` has at least 1 "approved" entry

**Validation command**:
```bash
ls product/regradar/data/evidence/ 2>/dev/null | head -5
python3 tools/review_canonical_evidence.py --help
```

**Owner role**: Founder + Evidence Trail Agent
**Difficulty**: Medium

---

## P2 — Important but not urgent

### P2-1: Add customer onboarding documentation
Customer-facing START_HERE that explains what they get, how monitoring works, what proof files are, and what to do when they receive a brief. No such document exists.

**Owner**: Product + Doc Updater | **Difficulty**: Low

---

### P2-2: Migrate from SQLite to PostgreSQL
For any realistic multi-user scenario, SQLite will hit concurrency limits. PostgreSQL is the production-ready choice. The schema is small and migration is straightforward.

**Owner**: Engineer | **Difficulty**: High

---

### P2-3: Add database backup procedure
No backup cron job, no restore procedure, no documentation. A single disk failure loses all evidence records and user data.

**Owner**: DevOps | **Difficulty**: Low-Medium

---

### P2-4: Add log rotation configuration
The systemd service logs to journal. Application logs go to the LOG_DIR. Neither has rotation configured. Disk can fill.

**Owner**: DevOps | **Difficulty**: Low

---

### P2-5: Remediate SCA AML/CFT parser/noise issue
SCA monitoring is noted as "needs adapter remediation" in multiple places. This blocks broader UAE CMA/SCA coverage claims.

**Owner**: Source Monitor Agent | **Difficulty**: Medium

---

### P2-6: Remove disabled non-AE sources from sources.json or document their purpose
432 total records but only 116 are AE and enabled. The remaining 316 include RU, KZ, AZ, BY, UZ, INT, GE, AM, TR, QA, SA, SG, HK, BH, MY jurisdictions — all disabled. They add noise and could confuse any script that iterates sources.json.

**Owner**: Source Monitor Agent | **Difficulty**: Low

---

### P2-7: Add ICP targeting to sales and product pages
The landing page speaks to all compliance teams without prioritizing. VASP/crypto firms (VARA), DFSA-regulated firms (DFSA/DIFC), and ADGM-regulated firms (ADGM/FSRA) are the clearest ICPs given source depth. Add explicit ICP targeting.

**Owner**: Product + Marketing | **Difficulty**: Low

---

### P2-8: Add health check endpoint that includes monitoring pipeline status
Current `/health` returns basic process health. It should include last monitoring run timestamp, source success rate, and alert queue depth.

**Owner**: Engineer | **Difficulty**: Low

---

## P3 — Polish / future

### P3-1: Replace "Most Popular" badge on UAE Monitor plan
No customer data to support this claim. Remove until there is one paying customer who chose that plan.

**Owner**: Product | **Difficulty**: Trivial

---

### P3-2: Add geo-block mitigation strategy for Official Gazette
The Official Gazette and UAE e-Laws Portal are geo-IP blocked from outside UAE. Consider a UAE-based proxy, a partner integration, or a disclosure that UAE-based customers could access these via a client-side integration.

**Owner**: Product + Source Monitor Agent | **Difficulty**: High (requires UAE infrastructure)

---

### P3-3: Add ADGM FSRA dedicated regulatory-alerts page
Currently a candidate pending selector remediation. This would add a high-value source for ADGM-regulated firms.

**Owner**: Source Monitor Agent | **Difficulty**: Medium

---

### P3-4: Add performance test
No load test exists. Need to know the breaking point of the http.server before adding customers.

**Owner**: Engineer | **Difficulty**: Medium

---

### P3-5: Multi-workspace / white-label for consultants
Currently an email CTA only. The Consultant plan at $999/mo is described but not buildable yet.

**Owner**: Product + Engineer | **Difficulty**: High

---
*Backlog generated by multi-role audit. No code changed.*
