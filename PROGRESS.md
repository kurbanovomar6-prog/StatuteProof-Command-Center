# PROGRESS — production readiness sprint (2026-07-05)

## Current phase
EXCELLENCE sprint COMPLETE on branch excellence (unmerged; deploy pin
c1ddb8a + deploy/ untouched). All cycles C1-C7 + Phase 2 gate + Phase 3
adversarial done, evidence in DEFECT_LOG.md. Ready for owner review/merge.

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

## Completed cycles
- Cycle 1 (63fa726): D6 heartbeats + canonical JSONL baseline + derived
  SQLite index + consistency check + retention compaction + D8 env base dir.
  14 TDD tests red→green; suite 622.
- Cycle 2 (2457137): email guardrails (loud misconfig failure, DRY_RUN,
  attempt recording; 5 TDD tests) + decision 4 (API zero sweeps — proven,
  2 restarts, 0 fetch lines). E2E alert→outbox delivery PASS. Suite 627.
- Cycle 3 (f7688fb): deploy kit — systemd×5 (statically validated), Caddy,
  logrotate, deploy-check (verified failing loudly), backup (44MB archive
  verified), DEPLOY.md ≤30min, CORS allowlist, VITE_API_URL. Frontend 43/43.

## Open items
- Phase 2 gate: fresh-clone sim, JSONL/SQLite agreement demo, compaction
  double-run demo, divergence seeding on a copy, scheduler kill test
- Phase 3 adversarial review, final report

## Next action
Fresh-clone: configure .env from example, deploy-check, start API on :5002,
3× Tier-A real-network e2e, show JSONL+SQLite hashes side by side.
