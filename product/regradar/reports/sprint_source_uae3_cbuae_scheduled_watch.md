# Sprint Source UAE-3 — CBUAE Scheduled Proof Watch

## 1. Verdict

Implemented a safe scheduled watcher wrapper and systemd timer templates for CBUAE Rulebook proof/diff validation. CBUAE remains under validation.

## 2. What was implemented

- `scripts/run_cbuae_rulebook_watch.py`
- `deploy/systemd/statuteproof-cbuae-rulebook-watch.service`
- `deploy/systemd/statuteproof-cbuae-rulebook-watch.timer`
- `docs/cbuae_rulebook_watch_scheduler.md`

## 3. What the watcher does

The watcher runs the existing proof/diff pipeline, saves snapshots and proof reports, and writes `reports/cbuae_rulebook_proof/cbuae_rulebook_watch_last_run.json` with run status, row count, diff counts, report path, snapshot path, and error details when applicable.

If real added or changed rows are detected, the underlying proof/diff pipeline can create a draft-only candidate held for review.

## 4. What it does not do

- It does not mark CBUAE active.
- It does not modify `sources.json`.
- It does not change production source monitoring behavior.
- It does not send Telegram messages.
- It does not enable automatic client delivery.
- It does not approve alerts.
- It does not fabricate rows or force row count growth.

## 5. Why row count does not automatically grow

The current 10 rows are real extracted rows from the official CBUAE Rulebook revision updates source. The scheduler should not try to increase this number. Row count should change only if the official source publishes new rows/items, the adapter is deliberately expanded to another official page or section, or the source page structure changes.

## 6. Hourly vs 6-hour cadence explanation

Hourly cadence reduces detection delay for validation runs and creates more frequent proof/diff checkpoints. A 6-hour cadence produces fewer snapshots and less network load. Neither cadence increases source coverage or row count by itself.

## 7. Systemd files

- Service: `deploy/systemd/statuteproof-cbuae-rulebook-watch.service`
- Timer: `deploy/systemd/statuteproof-cbuae-rulebook-watch.timer`
- Timer cadence: hourly with `RandomizedDelaySec=300` and `Persistent=true`

The files are templates only. They were not installed automatically.

## 8. Validation

Validation commands:

```bash
python3 -m compileall app run.py scripts -q
python3 scripts/run_cbuae_rulebook_watch.py
git diff --check
```

Claims-safety grep was run against the CBUAE proof reports, this sprint report, and the scheduler documentation. The only expected hit is the negative caveat that CBUAE is not active production monitoring.

## 9. Deployment instructions

See `docs/cbuae_rulebook_watch_scheduler.md`. Before installing, confirm the VPS path and service user. If the deployment user is not `regradar`, update the systemd service template.

## 10. Remaining limitations

- CBUAE is not active production monitoring.
- This is scheduled proof/diff under validation.
- No Telegram sends are enabled.
- No automatic client delivery is enabled.
- No source activation occurred.
- Activation requires scheduled repeated validation and human-reviewed alert flow.
