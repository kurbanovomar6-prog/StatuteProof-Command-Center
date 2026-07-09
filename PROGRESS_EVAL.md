# PROGRESS_EVAL — hostile due-diligence evaluation (2026-07-06)

Branch `eval-fixes` off main `1e10e9f`. All verifications run in THIS
session (isolated STATUTEPROOF_BASE_DIR; real trail read-only; one
throwaway UI user registered on the local API — precedent qa-e2e).

## SCORE_BEFORE = 46.5 / 100 (FROZEN before any fix)

| Dim | Weight | Score | Evidence (this session) |
|---|---|---|---|
| A. Data & evidence integrity | 15 | 6 | 654 tests green + dedup 8/8 w/ env; trail 1,406 lines 0 corrupt; JSONL==SQLite 0 divergences; SIGKILL mid-run → 0 partial lines. Caveats: NEW stale cross-process run cache (proven: briefs 404 → restart → 200); chrome-contaminated baselines + error-page baselines KNOWN (signal-max) |
| B. Alert & signal quality | 15 | 4 | Title-flips regenerate LOW/no-send but still CHANGED queue noise; CBUAE counter delta still scores HIGH today via ban⊂bank (pasted); content layer truthful (matched terms, no boilerplate); 0/63 historical CHANGED genuine |
| C. End-to-end product function | 15 | 5 | Full path walked: register→verify(outbox)→login→onboarding 4 steps→plan→dashboard→evidence→forced diff→1 alert→rerun 0→brief. CAP AT 5: briefs/generate returned "No CHANGED run record found" for an existing record until API restart (stale cache) — a dead end on the canonical two-process demo path |
| D. Design & UX | 10 | 6 | 11 screens, 0 console errors, honest states ("Pending activation", disclaimers, Google "not configured"); 320px app 0 overflow; landing 10px overflow + 46,373px tall (liability grew from 24,926px); excellence state/retry fixes unmerged |
| E. Source portfolio value | 10 | 3 | 116 enabled / 83 eligible but 0/63 historical CHANGED runs are genuine regulatory changes (replay judged in this session); 44% self-inflicted extraction noise; honest tiering + 8,252 snapshots keep it off the floor |
| F. Code quality & tests | 10 | 5 | Backend 1 failed/654 passed OUT OF BOX (.env-dependent test); frontend 43/43, build ✓, eslint 0 errors; pip-audit 10 findings + npm 1 HIGH on main (fixes unmerged on excellence); CI file exists but UNTRACKED → no CI; ~232KB dead frontend cluster (KNOWN, janitor-locked) |
| G. Security | 10 | 6 | Live burst: login 429 after ~9, register after 5, health 200 throughout; full header set incl. HSTS/Permissions-Policy; HttpOnly+SameSite=Strict+conditional Secure; PBKDF2-600k. Gaps: no Cache-Control:no-store on auth (fix unmerged); alerts-bot token rotation still pending after 438MB log leak |
| H. Production operations | 10 | 2 | NOTHING serves customers: DNS→207.154.250.157 with 443 refused; new droplet 138.68.70.215 SSH-only; no scheduler running anywhere; telegram listener dead since Jul 5 18:27 (stale pid). Deploy kit + runbook exist; deploy session in flight |
| I. Commercial readiness & claims truth | 5 | 4 | Copy heavily disclaimered; "prevent fines" only in negation; honest pilot gating. BUT hero "Monitoring active" is a hardcoded badge while zero monitoring runs (S0 truth); market evidence: 1 contact request, 0 customers |

Composite = 6×1.5 + 4×1.5 + 5×1.5 + 6×1 + 3×1 + 5×1 + 6×1 + 2×1 + 4×0.5
          = 9 + 6 + 7.5 + 6 + 3 + 5 + 6 + 2 + 2 = **46.5**

## NEW findings (discovery credit)
- N1 S1: stale cross-process run cache — `app/source_runs.py:_read_runs`
  caches forever, no mtime check; API never sees scheduler-written runs
  (proven by controlled restart experiment). Deployed topology = frozen
  dashboard/briefs.
- N2 S1 (latent): split-brain base dir — `app/config.py:30 BASE_DIR` and
  `app/email_delivery.py:33 _BASE_DIR` ignore STATUTEPROOF_BASE_DIR while
  `source_runs` honors it; `.env.example:138` exposes the variable.
  Verification email + dashboard reads land in the wrong tree.
- N3 S0 (truth): `web/src/components/Hero.jsx:318` "Monitoring active" +
  pulsing dot is hardcoded; no monitoring runs anywhere.
- N4 S3: verification emails written as `brief_unknown_*.json` (mislabeled
  outbox artifacts); `/api/alerts/action-log` 400 without params (unchecked
  minor).

## KNOWN items re-confirmed (cost points, no discovery credit)
- ban⊂bank false HIGH + chrome noise + error-page baselines (signal-max, unmerged)
- pip/npm CVEs + Cache-Control + state/retry gaps (excellence, unmerged)
- dead frontend cluster + dead routes (janitor, locked)
- dedup test .env dependency (fix exists on signal-max: 8cc4ce2)
- bot token rotation pending (D5)

## Phase 2 plan (gated)
Fix (new, unowned, small, outside rails): N1 (cache mtime), N2 (env-aware
base dirs), N3 (truthful monitoring badge). File the rest.


## Phase 2 — fixed with proof
- N1 (f4e3131): _read_runs mtime+size stamp. 3 TDD tests red→green; live
  re-verify: cross-process CHANGED run → /api/briefs/generate 200 with NO
  restart (the SCORE_BEFORE dead end).
- N2 (52d34ef): config.BASE_DIR + email_delivery honor STATUTEPROOF_BASE_DIR.
  3 TDD tests; live re-verify: verification email lands in the configured
  base dir.
- N3 (e1f97aa): MonitoringStatusBadge — "Monitoring active" only when
  /api/health last_run_at < 24h; honest fallback otherwise. 4 vitest tests;
  frontend 47/47, build clean, eslint 0 errors.
Suite state per commit: backend 660 passed / 1 failed (the KNOWN
.env-dependent dedup test, fix exists on signal-max 8cc4ce2 — not
double-fixed here to avoid a merge conflict).

## Filed items (owner + effort)
- Merge excellence branch (owner: founder): pip 10 CVE findings + npm 1
  HIGH, Cache-Control no-store, state/retry gaps, hero hardcoded
  count/cadence. Effort: merge + gate re-run (hours).
- Merge signal-max branch + schedule RESET_RUNBOOK (owner: founder):
  ban⊂bank false HIGH, chrome noise, error-page baselines, detected facts,
  Arabic lane, dedup-test env fix. Effort: merge + Update Day.
- Commit .github/workflows/test.yml and turn on CI (owner: founder). S1,
  minutes.
- Rotate alerts-bot token (owner: founder, D5 follow-up). S1.
- Restart telegram listener locally or accept prod-only (owner: founder).
- N4 (S3): verification emails written as brief_unknown_*.json;
  /api/alerts/action-log 400 without params. Effort: small.
- Janitor Phase 1 deletions remain locked (dead landing cluster, dead routes).

## SCORE_AFTER = 51.5 / 100

| Dim | Before | After | Why changed |
|---|---|---|---|
| A | 6 | 7 | stale-cache defect fixed + verified; remaining caveats owned/unmerged |
| B | 4 | 4 | unchanged (owned by signal-max) |
| C | 5 | 7 | dead end removed (verified restart-free brief); full path clean |
| D | 6 | 6 | unchanged |
| E | 3 | 3 | unchanged |
| F | 5 | 5 | unchanged (CI still absent, CVEs unmerged) |
| G | 6 | 6 | unchanged |
| H | 2 | 2 | still nothing serving customers |
| I | 4 | 5 | hero badge now truthful; market evidence still ~zero |

Composite after = 7×1.5 + 4×1.5 + 7×1.5 + 6 + 3 + 5 + 6 + 2 + 5×0.5
               = 10.5 + 6 + 10.5 + 6 + 3 + 5 + 6 + 2 + 2.5 = **51.5**
