# StatuteProof — Update & Rollback Runbook (live droplet)

Routine code update of a live droplet deployed per `DEPLOY.md` (DigitalOcean
droplet, Caddy reverse proxy, systemd units, app installed at `/srv/regradar`
from the source clone at `/srv/regradar-src`). For fresh installs use
`DEPLOY.md`; for the normalization-v2 baseline reset use `RESET_RUNBOOK.md`.

All commands run on the droplet as root unless stated.

## Update procedure

1. **Backup first** — never update without a fresh archive:

   ```bash
   sudo -u regradar bash /srv/regradar/deploy/backup.sh
   ```

   Confirm the `off-box copy` line in the output. If the script prints the
   `LOCAL-ONLY` warning instead, STOP and fix `STATUTEPROOF_BACKUP_REMOTE`
   in `/srv/regradar/.env` before updating (see `DEPLOY.md` § 9).

2. **Snapshot current code for rollback** (code-only; data/DB rollback comes
   from the backup archive; `.env` is excluded so secrets are not duplicated —
   the live `.env` stays in place through the whole update; `/evidence` is
   excluded because the sealed trail is append-only — it is never rolled back
   and a second copy of it under `/srv/regradar.prev/` only burns disk):

   ```bash
   rsync -a --exclude /data --exclude /backups --exclude /.venv --exclude /.env \
       --exclude /evidence /srv/regradar/ /srv/regradar.prev/
   ```

3. **Pull the gate-green main into the source clone:**

   ```bash
   git -C /srv/regradar-src fetch origin
   git -C /srv/regradar-src checkout main
   git -C /srv/regradar-src pull --ff-only
   ```

4. **Copy files over the install** — code only. Do NOT use the plain
   `cp -r` from `DEPLOY.md` § 3 here: that step is for an empty fresh
   install. The repo tracks seed files under `data/` (alert queue entries,
   the canonical evidence-review journal), so a bare `cp -r` onto a LIVE
   tree would overwrite runtime data with stale repo copies. Use the same
   rsync-with-excludes pattern as the snapshot in step 2. The excludes are
   anchored with a leading `/` (transfer-root-relative) on purpose: a bare
   `--exclude data` matches `data` at ANY depth and would silently skip the
   repo-tracked frontend source `web/src/data/` (source counts, plan data,
   payment-link constants), so the live site would keep rebuilding from stale
   sources with no error. Anchored `/data` protects only the top-level
   runtime `data/` tree:

   ```bash
   rsync -a --exclude /data --exclude /backups --exclude /.venv --exclude /.env \
       /srv/regradar-src/product/regradar/ /srv/regradar/
   chown -R regradar:regradar /srv/regradar
   ```

5. **Rebuild what changed:**

   ```bash
   # only if requirements.txt changed:
   /srv/regradar/.venv/bin/pip install -r /srv/regradar/requirements.txt
   # only if web/ changed:
   cd /srv/regradar/web && npm ci && npm run build
   ```

6. **GATE — deploy-check.** Do not restart anything until it prints
   `DEPLOY-CHECK PASSED` (it now also fails when `STATUTEPROOF_BACKUP_REMOTE`
   is unset):

   ```bash
   cd /srv/regradar && sudo -u regradar bash deploy/deploy-check.sh
   ```

7. **Refresh units + restart services:**

   ```bash
   cp /srv/regradar/deploy/systemd/statuteproof-*.{service,timer} /etc/systemd/system/
   systemctl daemon-reload
   systemctl restart statuteproof-api statuteproof-scheduler statuteproof-telegram-bot
   ```

8. **Verify:**

   ```bash
   curl -s https://statuteproof.com/api/health     # expect {"ok": true, ...}
   # one sealed-evidence verification pass (silent + exit 0 when the sealed
   # trail verifies clean):
   cd /srv/regradar && sudo -u regradar .venv/bin/python run.py verify-trail-watch
   journalctl -u statuteproof-scheduler -n 20      # loop progressing
   ```

## Rollback procedure

1. Stop the services:

   ```bash
   systemctl stop statuteproof-api statuteproof-scheduler statuteproof-telegram-bot
   ```

2. Restore the pre-update code snapshot (same excludes as the snapshot: the
   live `.env`, `data/`, `backups/` and the sealed `evidence/` tree stay in
   place):

   ```bash
   rsync -a --exclude /data --exclude /backups --exclude /.venv --exclude /.env \
       --exclude /evidence /srv/regradar.prev/ /srv/regradar/
   chown -R regradar:regradar /srv/regradar
   ```

3. **Restore the pre-update systemd units.** Step 2 has just put the old tree
   back, so `deploy/systemd/` now holds the OLD unit files — reinstall them,
   otherwise the droplet keeps running the NEW unit definitions against the
   old code (deploy-check inspects the tree, not `/etc/systemd/system`, so it
   would still pass while a service fails to start):

   ```bash
   cp /srv/regradar/deploy/systemd/statuteproof-*.service /etc/systemd/system/
   cp /srv/regradar/deploy/systemd/statuteproof-*.timer /etc/systemd/system/
   systemctl daemon-reload
   ```

   Required for any release that changed a `.service` or `.timer`; harmless
   (a no-op re-copy) for every other release, so always run it.

4. If the data/DB must also roll back, restore the newest pre-update archive
   per `DEPLOY.md` § "Restore from backup" (`tar -xzf` into `/tmp/restore`,
   `rsync` the `data/` tree back, `cp` `regradar.db` to `DB_PATH`).

5. Re-run the gate: `cd /srv/regradar && sudo -u regradar bash deploy/deploy-check.sh`.

6. Start the three services again (`systemctl start statuteproof-api
   statuteproof-scheduler statuteproof-telegram-bot`).

7. Verify exactly as in update step 8: `/api/health` returns
   `{"ok": true, ...}` and `run.py verify-trail-watch` exits 0.

## Notes

- Never run two schedulers against one data dir.
- Alert-affecting releases (normalization, alert format) follow the
  suppression rules in `RESET_RUNBOOK.md` — do not restart the scheduler
  mid-window without them.
- The timers (compaction/backup/heartbeat/verify) need no restart on update —
  the oneshots re-read `/srv/regradar/.env` on each run.
