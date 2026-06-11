# CBUAE Rulebook Proof Watch Scheduler

## Purpose

This scheduler runs the CBUAE Rulebook proof/diff validation script on a repeatable cadence. It is designed for VPS systemd timer or cron use while the CBUAE Rulebook source remains under validation.

## What the watcher does

- Runs `scripts/run_cbuae_rulebook_watch.py`.
- Calls the existing CBUAE proof/diff pipeline.
- Saves snapshots under `data/source_snapshots/cbuae_rulebook_proof`.
- Updates reports under `reports/cbuae_rulebook_proof`.
- Writes `reports/cbuae_rulebook_proof/cbuae_rulebook_watch_last_run.json`.
- Creates a draft-only candidate only if real added or changed rows are detected by the proof/diff pipeline.

## What the watcher does not do

- It does not mark CBUAE active.
- It does not modify `sources.json`.
- It does not change production source monitoring behavior.
- It does not send Telegram messages.
- It does not enable automatic client delivery.
- It does not approve alerts.
- It does not fabricate source rows or force row count growth.

## Cadence

The recommended default cadence is hourly. Hourly execution reduces detection delay if the official source changes, but it does not increase row count. Row count changes only when the official source publishes rows, the adapter scope is deliberately expanded to another official source section, or the source structure changes.

## Systemd templates

Template files:

- `deploy/systemd/statuteproof-cbuae-rulebook-watch.service`
- `deploy/systemd/statuteproof-cbuae-rulebook-watch.timer`

The service uses placeholder deployment values:

- `WorkingDirectory=/srv/regradar`
- `ExecStart=/srv/regradar/.venv/bin/python scripts/run_cbuae_rulebook_watch.py`
- `User=regradar`
- `Group=regradar`

If the VPS uses another service user, edit `User=` and `Group=` before installing.

## Install on VPS

```bash
sudo cp deploy/systemd/statuteproof-cbuae-rulebook-watch.service /etc/systemd/system/
sudo cp deploy/systemd/statuteproof-cbuae-rulebook-watch.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now statuteproof-cbuae-rulebook-watch.timer
systemctl list-timers --all | grep cbuae
sudo systemctl status statuteproof-cbuae-rulebook-watch.service --no-pager
journalctl -u statuteproof-cbuae-rulebook-watch.service -n 100 --no-pager
```

## Disable on VPS

```bash
sudo systemctl disable --now statuteproof-cbuae-rulebook-watch.timer
```

## Manual run

```bash
python3 scripts/run_cbuae_rulebook_watch.py
```

## Safety language

CBUAE is not active production monitoring. This is scheduled proof/diff under validation. Activation requires scheduled repeated validation and a human-reviewed alert flow.
