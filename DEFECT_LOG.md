# DEFECT LOG — QA session 2026-07-05

Phase 0 ground truth (all outputs real, this session):
- Backend: `pytest tests -q` → **598 passed, 0 failed, 0 skipped** (53.18s)
- Frontend: `npm run build` → ✓ built in 631ms · `vitest run` → **43 passed (43)** · `eslint src` → **12 errors, 3 warnings**
- Backend `run.py api` (AUTO_MONITOR_INTERVAL=0) alive 5m40s, `/api/health` 200 in 66ms; all dashboard endpoints 200 (summary 56ms, evidence 23ms, reviews 38ms, canonical 45ms, briefs 21ms)
- E2E 3× Tier-A pipeline pass executed (output below)

## D1 — S0 — **FIXED** (commit b44023d) — Monitor pipeline loses hashes; real changes recorded as UNCHANGED; alert chain silently broken
- Location: `app/pipeline.py` `run_pipeline` (hash computed line ~225, never attached to result) → `run_pipeline_for_source` run_record (no `normalized_hash`/`raw_hash`/`content_hash`/`normalized_chars`/`raw_chars`) → `app/source_runs.py` `classify_change` (hash comparison gets None → falls through to UNCHANGED) → `_write_proof_artifact` (null hashes → `proof_quality: INCOMPLETE`) → alert-draft gate (`change_status == "CHANGED"`) never fires.
- Evidence (live run, 2026-07-05T12:39Z):
  `AE-dubai-virtual-assets-regulatory-authority-vara`: pipeline `changed: True` → **recorded change_status: UNCHANGED**, normalized_hash None, diff_json_path None, proof_quality INCOMPLETE.
  `AE-dfsa-financial-crime-mlro-letters`: same pattern.
  `/api/evidence?limit=100`: **100/100 rows** normalized_hash=None, 0 diff paths.
- Impact: evidence-trail integrity broken end to end; changes detected by fetch/diff never become CHANGED records, alert drafts, or review-queue items.
- Fix proof: 2nd post-fix E2E run — DFSA MLRO recorded CHANGED, normalized_hash 2be6fc54…, diff.json written (diff_quality GOOD, meaningful=True), alert_draft.json/md created; VARA identical hash → truthful UNCHANGED. tests/test_run_record_integrity.py 6/6. Full suite 608 passed.
- Status: FIXED

## D2 — S0 — **FIXED** (commit b44023d) — extraction_quality case mismatch produces false QUALITY_DROP / misses real failures
- Location: `app/pipeline.py:_extraction_quality` returns lowercase `good|low_content|failed`; `app/source_runs.py:classify_change` compares against uppercase `_GOOD_ORDER = {FAILED,THIN,MEDIUM,GOOD}` and literal `"FAILED"`.
- Evidence: `_GOOD_ORDER.get('good', 0) == 0` → any pipeline run following an uppercase intake record (`GOOD`) triggers `QUALITY_DROP`. Matches the 59 QUALITY_DROP rows with `extraction_quality: good` seen in `/api/sources/status` (2026-07-04 sweep). Lowercase `failed` ≠ `FAILED` → real failures not classified FAILED.
- Fix: _canonical_quality normalization (good→GOOD, low_content→THIN, ok→MEDIUM), case-insensitive. Legacy misclassified rows are historical data — not rewritten.
- Status: FIXED

## D3 — S1 — **FIXED** (commit f5ec41c) — ESLint: 12 errors, 3 warnings
- App pages: `ActionLogPanel.jsx:23` set-state-in-effect; `SettingsPage.jsx:116` unused `setEmailEnabled`.
- Landing: `AIAnalyst.jsx:68` set-state-in-effect; unused imports/vars in `AIInsightSection` (3), `AuditBinderSample` (2), `EvidenceCard` (1), `Footer` (3).
- Warnings (3): exhaustive-deps ×2, compiler skip ×1.
- Fix proof: `eslint src` → 0 errors, 3 warnings (2 exhaustive-deps in landing animation hooks — adding deps changes animation restart semantics, left deliberately; 1 informational compiler-skip). Note: Settings email-alerts value has no UI toggle (round-tripped unchanged) — S3, out of scope.
- Status: FIXED

## D4 — S2 — Backend process "death" root cause + heavy startup
- Root cause of prior-session deaths: background shells are killed when the Claude Code session process exits (harness teardown). Task output files show the API mid-sweep with no traceback, no crash. NOT an app crash.
- Contributing: `run_server` auto-starts `run_watch_loop` (default 60 min) which runs a **full 116-source network sweep immediately at startup** (`app/scheduler.py`, "runs immediately on startup" by design). Any supervisor restart re-triggers a sweep.
- Status: ROOT-CAUSED (documented); persistence beyond a session requires nohup/systemd — PROD-ONLY.

## D5 — S1 — **FIXED** (commit e349a33) — upgraded severity: log leaked bot token — telegram_bot.log at 438MB, unbounded
- Location: `logs/telegram_bot.log` (438,676,115 bytes, growing since Jun 21). The `nohup ... > logs/telegram_bot.log` pipe bypasses RotatingFileHandler.
- Found worse: every failure line contained the getUpdates URL **with the bot token in plaintext**; failures retried with no backoff (~1,200 identical lines per burst while offline).
- Fix: token scrubbed from failure logs; fetch_updates returns None on transport error; poll loop backs off 1s→60s. Log truncated 438MB→0; listener restarted on fixed code (PID via logs/telegram_bot.pid). tests/test_telegram_listener_reliability.py 4/4.
- PROD-ONLY follow-up: **rotate the alerts-bot token** — it sat in a local 438MB log for two weeks.
- Status: FIXED (rotation pending, founder action)

## D6 — S2 — **FIXED** (commit 63fa726, sprint 2026-07-05) — UNCHANGED monitor runs write no run record
- Owner decision: every run writes a record; unchanged runs append a compact ~916-byte heartbeat (verified live: fresh-clone run 2, `AE-dfsa-financial-crime-mlro-letters` heartbeat UNCHANGED with matching hash). Retention: `run.py compact-heartbeats` (idempotent, TDD; daily systemd timer) compacts >30-day heartbeats to last-of-day per source. Proof: fixture demo kept=4/removed=9 then kept=4/removed=0 byte-identical.
- Note (policy follow-up): heartbeats that classify as QUALITY_DROP (thin-but-stable sources, normalized <500 chars, e.g. `AE-dfsa-aml-rulebook-module`) are kept forever by the defensive keep rule — ~8 MB/yr per permanently-thin source at hourly cadence.
- Status: FIXED

## D7 — S3 — workspace hygiene (out of scope this session)
- `.claude/agents/` third-party dump (hundreds of files) untracked; `.github/` untracked; two stray «Без названия» files at repo root.


## D8 — S2 — **FIXED** (commit 63fa726) — pipeline alert-artifact writer hardcodes repo base dir
- Base dir now resolves from STATUTEPROOF_BASE_DIR (default: app root); alert writer goes through it. Test proves artifacts stay inside the configured base and the repo data dir stays untouched.
- Status: FIXED

## Phase 2 verification gate (2026-07-05, all outputs real)
- Backend suite: **608 passed, 0 failed, 0 skipped** (10.31s). Frontend: **43/43**, build ✓ 376ms, eslint **0 errors**.
- API alive through session on port 5001 (restart after fix; >2 min, serving throughout screen sweep). Vite up on 5173.
- All 11 app screens opened via Playwright: **0 console errors**.
- E2E auth: register qa-e2e@example.com → outbox JSON with subject "Verify your StatuteProof email address" + token → verify-email 200 → login ok → /api/auth/me returns session user id 12.
- E2E monitoring (Tier-A): VARA / DFSA MLRO / DFSA rulebook. Every written record has proof URL, GST-consistent UTC timestamp, normalized hash, baseline comparison, change status; DFSA MLRO produced CHANGED + diff.json (GOOD) + alert draft. Unchanged rulebook run writes no record (D6, OPEN by design decision needed).
- Counter cross-check (must match, three ways):
  UI badge/headline: "Last check 2 min ago" · "83 sources eligible" — API: summary enabled_count=116, readiness_supported=83, last_run_at=2026-07-05T12:54:44 = health sources_active=116 — Files: sources.json enabled=116, newest JSONL run 2026-07-05T12:54:44. **All three agree.**


## D-dual-baseline — S0 — **FIXED** (commit 63fa726) — JSONL trail vs SQLite documents could disagree on CHANGED
- Root cause: save_document hashed raw content while the pipeline hashed normalized text — different values by construction (the VARA changed:True-every-run case).
- Fix (owner decision 2): JSONL normalized_hash is canonical for classification; save_document(content_hash=...) stores the same hash in the same step; divergent index rows realigned with loud WARNING; check_baseline_consistency() at API+scheduler startup logs BASELINE DIVERGENCE, never heals.
- Proof: fresh-clone e2e — all 3 sources JSONL hash == SQLite hash (values pasted in final report); seeded divergence on a data COPY detected (17th alongside 16 known legacy) and loudly logged; legacy divergences remain visible by design.
- Status: FIXED

## D9 — S1 — **FIXED** (commit 89e4365) — .env.example empty-value inline comments became variable values
- python-dotenv keeps `# comment` as the VALUE for `VAR=   # comment` lines. Fresh install: REGRADAR_DB_PATH literally contained the comment string; sqlite unreachable (caught by deploy-check on the fresh clone). 18 lines rewritten; DB_PATH uses `or` fallback; verified zero comment-valued vars remain.
- Status: FIXED

## Sprint verification gate (2026-07-05, second pass — all outputs real)
- Suites: backend **627 passed, 0 failed, 0 skipped**; frontend **43/43**; build ✓; eslint 0 errors / 3 known warnings.
- Fresh-clone sim (/tmp/sp-fresh, removed after): venv+deps, .env from template only, deploy-check PASSED, API on :5002 health 200 with **0 sweep lines**, real-network e2e ×2 on 3 Tier-A sources → FIRST_SEEN baselines then 1×CHANGED + 2×heartbeats, JSONL==SQLite for all 3 (hashes identical).
- Scheduler SIGKILL mid-sweep: trail 6→15 records, **0 corrupt/partial lines**.
- deploy-check with blanked SECRET_KEY: exit code **1**.
- All 11 app screens: **0 console errors**.
- Adversarial diff grep (1,256 added lines): no weakened/removed assertions, no skips, no TODOs, no secrets, no debug prints.

# ALERT QUALITY SPRINT — 2026-07-05 (branch alert-quality)

## Phase 0 forensics: today's two live Telegram alerts (16:54 / 17:28 GST)
- Trail records: run 17d38737 (12:54:44Z, CHANGED, hash 2be6fc54…) and run
  4bc2127d (13:28:51Z, CHANGED, hash b80825e8…). Note: 4bc2127d's hash equals
  the hash recorded at 12:54:12Z — the source OSCILLATES between two variants.
- diff.json both runs: added=0 removed=0 changed=1 — the single changed chunk
  is the page TITLE flipping between "…| DFSA" and "…| DFSA | THE INDEPENDENT
  REGULATOR OF FINANCIAL SERVICES". Zero regulatory content changed.
- Verdict per alert: (c) operator re-runs (this machine's e2e passes at those
  exact timestamps; no scheduler process exists locally — pgrep empty) on top
  of (b)-style churn (server-side title A/B). NOT a real regulatory change.
- Why HIGH: pipeline diffs paragraph BLOCKS; the changed block = title + full
  nav menu. Nav contains "Sanctions" (strong keyword) + "Compliance" (context
  amplifier) → HIGH path 2. Reproduced: title-only diff scores MEDIUM; the
  nav words are what upgraded it. The HIGH reason text ("deadline, penalty,
  or mandatory obligation") describes context that was NEVER detected.
- Sender: pipeline step-10 immediate Telegram send (ENABLE_TELEGRAM_ALERTS=
  True in local .env, admin chat). The parallel alert-DRAFT layer scored the
  same run MEDIUM / HOLD_FOR_REVIEW — two content layers disagree about the
  same event, in customer-visible ways.

## A1..A5 defect register — all FIXED on branch alert-quality
- A1 FIXED (72ce88a): app/alert_dedup.py — never re-alert an already-alerted
  hash per source; ALERT_COOLDOWN_HOURS (default 24) between alerts; dedup
  state = alert_sent in the trail itself. 8 TDD tests; pipeline-level
  once-then-zero proven. Gate: forced diff → 1 alert, re-run → 0, trail
  records FIRST_SEEN/CHANGED/UNCHANGED.
- A2 FIXED (71b24ae): shared layer app/alert_content.py — severity names
  matched rule+keywords; ≤400-char excerpt of the real diff; risk reasons
  rewritten to name actual matches (boilerplate 'deadline, penalty, or
  mandatory obligation' removed). Both channels (Telegram + alert_draft.md +
  outbox email) render the same block — proven in gate output.
- A3 FIXED (71b24ae): absent fields omitted entirely; regression tests forbid
  'Not specified' and '—' scaffolding.
- A4 FIXED (71b24ae): severity rubric documented in app/risk.py (rule ids
  HIGH_MULTIPLE_STRONG / HIGH_STRONG_PLUS_CONTEXT / MEDIUM_* / LOW / NON_
  MATERIAL); HIGH without recorded matches states 'severity basis not
  recorded' and claims nothing.
- A5 FIXED (71b24ae, c75abe8): double periods cleaned, consistent title,
  human timestamps (YYYY-MM-DD HH:MM UTC).
- KEEP guards: footer/proof-URL/timestamp mandatory — regression-tested.

## Alert-quality open items (owner decisions needed)
- Keyword scan runs over the whole changed BLOCK including site navigation —
  the nav words ('Sanctions', 'Compliance') are what made today's title-flip
  HIGH. Scoring only the intra-block delta would fix it but changes scoring
  semantics — owner call.
- Keyword list is US-English only ('license'); DFSA/DIFC write UK English
  ('licence', 'authorisation', 'penalise') — real changes phrased in UK
  spelling can only reach MEDIUM via moderate keywords. Owner call.
- Suites at gate: backend 649 passed / frontend 43 passed / eslint 0 errors
  (3 known warnings). Branch NOT merged — merge is the owner's decision.
