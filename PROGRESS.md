# PROGRESS — production readiness sprint (2026-07-05)

## Current phase
Cycle 1 — heartbeats + canonical baseline + D8 (TDD, red first)

## Owner decisions locked
1. D6 heartbeats: every run writes a record; unchanged = compact heartbeat
   {timestamp, source_id, normalized_hash, status, proof_url, run_id};
   CHANGED kept forever; heartbeats >30 days compacted to 1/day/source
   (idempotent job, TDD).
2. Canonical baseline = JSONL normalized_hash; SQLite `documents` = derived
   index updated same step, same hash; startup consistency check, loud log,
   no silent auto-heal.
3. D8: base dir from config/env only, sane default, tested.
4. API startup must trigger zero sweeps; scheduler is its own entrypoint.

## Plan
- Cycle 1: decisions 1+2+3 (TDD)
- Cycle 2: email provider layer (SMTP + Resend, outbox default, loud
  failure, DRY_RUN) + decision 4
- Cycle 3: deploy/ kit (systemd, Caddy, logrotate, .env.example,
  deploy-check, backups, DEPLOY.md ≤30 min)
- Phase 2 verification gate → Phase 3 adversarial review → final report

## Completed
- Phase 0 baseline (no regressions): backend 608 passed / frontend 43 passed,
  build 433ms, eslint 0 errors 3 warnings. E2E 3× Tier-A: D1/D2 hold (hashes
  + GOOD proofs recorded; DFSA CHANGED with diff); target defects reproduce:
  VARA pipeline changed:True vs trail UNCHANGED (dual baseline — SQLite
  save_document hashes raw content, pipeline hashes normalized text);
  unchanged rulebook run writes NO record (D6).

## Open items
- All cycles

## Next action
Write RED tests: tests/test_canonical_baseline_and_heartbeats.py +
tests/test_heartbeat_compaction.py; then implement source_runs.record_heartbeat,
pipeline canonical-baseline step, save_document(content_hash=...),
app/retention.py, app/consistency.py, D8 env base dir.
