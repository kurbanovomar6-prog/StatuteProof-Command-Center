# DEFECT LOG — QA session 2026-07-05

Phase 0 ground truth (all outputs real, this session):
- Backend: `pytest tests -q` → **598 passed, 0 failed, 0 skipped** (53.18s)
- Frontend: `npm run build` → ✓ built in 631ms · `vitest run` → **43 passed (43)** · `eslint src` → **12 errors, 3 warnings**
- Backend `run.py api` (AUTO_MONITOR_INTERVAL=0) alive 5m40s, `/api/health` 200 in 66ms; all dashboard endpoints 200 (summary 56ms, evidence 23ms, reviews 38ms, canonical 45ms, briefs 21ms)
- E2E 3× Tier-A pipeline pass executed (output below)

## D1 — S0 — Monitor pipeline loses hashes; real changes recorded as UNCHANGED; alert chain silently broken
- Location: `app/pipeline.py` `run_pipeline` (hash computed line ~225, never attached to result) → `run_pipeline_for_source` run_record (no `normalized_hash`/`raw_hash`/`content_hash`/`normalized_chars`/`raw_chars`) → `app/source_runs.py` `classify_change` (hash comparison gets None → falls through to UNCHANGED) → `_write_proof_artifact` (null hashes → `proof_quality: INCOMPLETE`) → alert-draft gate (`change_status == "CHANGED"`) never fires.
- Evidence (live run, 2026-07-05T12:39Z):
  `AE-dubai-virtual-assets-regulatory-authority-vara`: pipeline `changed: True` → **recorded change_status: UNCHANGED**, normalized_hash None, diff_json_path None, proof_quality INCOMPLETE.
  `AE-dfsa-financial-crime-mlro-letters`: same pattern.
  `/api/evidence?limit=100`: **100/100 rows** normalized_hash=None, 0 diff paths.
- Impact: evidence-trail integrity broken end to end; changes detected by fetch/diff never become CHANGED records, alert drafts, or review-queue items.
- Status: OPEN

## D2 — S0 — extraction_quality case mismatch produces false QUALITY_DROP / misses real failures
- Location: `app/pipeline.py:_extraction_quality` returns lowercase `good|low_content|failed`; `app/source_runs.py:classify_change` compares against uppercase `_GOOD_ORDER = {FAILED,THIN,MEDIUM,GOOD}` and literal `"FAILED"`.
- Evidence: `_GOOD_ORDER.get('good', 0) == 0` → any pipeline run following an uppercase intake record (`GOOD`) triggers `QUALITY_DROP`. Matches the 59 QUALITY_DROP rows with `extraction_quality: good` seen in `/api/sources/status` (2026-07-04 sweep). Lowercase `failed` ≠ `FAILED` → real failures not classified FAILED.
- Status: OPEN

## D3 — S1 — ESLint: 12 errors, 3 warnings
- App pages: `ActionLogPanel.jsx:23` set-state-in-effect; `SettingsPage.jsx:116` unused `setEmailEnabled`.
- Landing: `AIAnalyst.jsx:68` set-state-in-effect; unused imports/vars in `AIInsightSection` (3), `AuditBinderSample` (2), `EvidenceCard` (1), `Footer` (3).
- Warnings (3): exhaustive-deps ×2, compiler skip ×1.
- Status: OPEN

## D4 — S2 — Backend process "death" root cause + heavy startup
- Root cause of prior-session deaths: background shells are killed when the Claude Code session process exits (harness teardown). Task output files show the API mid-sweep with no traceback, no crash. NOT an app crash.
- Contributing: `run_server` auto-starts `run_watch_loop` (default 60 min) which runs a **full 116-source network sweep immediately at startup** (`app/scheduler.py`, "runs immediately on startup" by design). Any supervisor restart re-triggers a sweep.
- Status: ROOT-CAUSED (documented); persistence beyond a session requires nohup/systemd — PROD-ONLY.

## D5 — S2 — telegram_bot.log at 438MB, unbounded
- Location: `logs/telegram_bot.log` (438,676,115 bytes, growing since Jun 21). The `nohup ... > logs/telegram_bot.log` pipe bypasses RotatingFileHandler.
- Status: OPEN (investigate what spams it; cap or rotate)

## D6 — S2 — UNCHANGED monitor runs write no run record
- Evidence: E2E run 3 (`AE-dfsa-aml-rulebook-module`): `changed: False` → no JSONL record, no snapshot. Evidence trail has gaps between change events; landing copy promises "CHANGED and UNCHANGED runs" both recorded.
- Status: OPEN — needs product decision (recording 116×24 unchanged runs/day grows JSONL unboundedly). Not fixing silently this session.

## D7 — S3 — workspace hygiene (out of scope this session)
- `.claude/agents/` third-party dump (hundreds of files) untracked; `.github/` untracked; two stray «Без названия» files at repo root.
