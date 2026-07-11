# StatuteProof — Deployment Runbook (fresh Ubuntu 24.04, target ≤ 30 min)

Every command below is meant to be run in order, as root unless stated.
Time estimates assume a 2 vCPU / 4 GB droplet and a registered domain with
DNS A records (`statuteproof.com`, `www.statuteproof.com`) already pointing
at the droplet — set DNS **before** droplet day, propagation is not counted.

## 0. Precondition gate (ABORT if any item fails)

Patched 2026-07-05 after the first droplet-day abort (unexplained host-key
change on the old IP). App code deploys from **origin/main** — the converged,
gate-green build (HEAD `679c0a3` at time of writing). The previous `c1ddb8a`
pin was **56 commits stale and pre-convergence** (missing the loader-status,
false-HIGH signal, relevance-scope, and claims fixes); do **not** deploy it.

1. **Telegram token**: rotated via @BotFather; old token revoked; new token
   staged in a local secret file (never chat, never git).
2. **DNS**: `dig +short` for apex + www via **8.8.8.8 and 9.9.9.9** (1.1.1.1
   is blocked on the operator network) both return the NEW droplet IP.
3. **Email — real SMTP required on prod** (`local_outbox` is NOT acceptable;
   the smoke test requires a real external delivery): Zoho app-specific
   password; host `smtp.zoho.eu` or `smtp.zoho.com` per account region;
   port 465 SSL; SMTP user = the alerts mailbox;
   `STATUTEPROOF_EMAIL_FROM` matching it. Credentials entered only at the
   .env step.
4. **Host trust — no trust-on-first-use**: the operator captures the
   expected fingerprint out-of-band from the DigitalOcean web console at
   droplet creation (`ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub`).
   The first SSH connection must match it exactly; any mismatch = ABORT.
5. **Old IP retired**: operator confirms 207.154.250.157 is destroyed (if
   owned) or abandoned (if foreign) and no DNS record anywhere still
   references it. **Zoho MX records stay untouched.**
6. Repository reachable from the droplet: pin present on origin/main.

Smoke-test addition: `dig TXT _dmarc.statuteproof.com` must return the new
DMARC record — paste it in the deploy report.

## 1. Base system + user (≈4 min)

```bash
apt-get update && apt-get install -y python3.12 python3.12-venv python3-pip \
    git curl ufw fail2ban debian-keyring debian-archive-keyring apt-transport-https
useradd -r -m -d /srv/regradar -s /usr/sbin/nologin regradar
```

## 2. Hardening: firewall, ssh, fail2ban (≈3 min)

```bash
ufw default deny incoming && ufw default allow outgoing
ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp
ufw --force enable
# ssh: key-only auth
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
systemctl reload ssh
systemctl enable --now fail2ban
# journald cap — the 438MB-log lesson, applied globally
mkdir -p /etc/systemd/journald.conf.d
printf '[Journal]\nSystemMaxUse=500M\n' > /etc/systemd/journald.conf.d/statuteproof.conf
systemctl restart systemd-journald
```

## 3. App code + Python env (≈6 min)

```bash
# as root — clean clone of the converged main branch (never rsync a working tree)
git clone https://github.com/kurbanovomar6-prog/StatuteProof-Command-Center.git /srv/regradar-src
git -C /srv/regradar-src checkout main   # converged gate-green build (was: stale pin c1ddb8a)
cp -r /srv/regradar-src/product/regradar/. /srv/regradar/
cd /srv/regradar
python3.12 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt          # ~3-4 min
chown -R regradar:regradar /srv/regradar
```

> Playwright/chromium is only needed for JS-rendered sources. Install later
> if required: `.venv/bin/playwright install chromium --with-deps` (adds ~5
> min; NOT part of the 30-minute path).

## 4. Configuration (≈4 min)

```bash
cd /srv/regradar
cp .env.example .env
.venv/bin/python run.py generate-secret-key   # paste output into .env SECRET_KEY
nano .env    # fill: SECRET_KEY, ENVIRONMENT=production, NEW telegram tokens,
             # email: STATUTEPROOF_EMAIL_PROVIDER=smtp + Zoho app password
             # (precondition 3 — local_outbox is NOT acceptable on prod)
chown regradar:regradar .env && chmod 600 .env
```

## 5. Frontend build (≈3 min)

```bash
# Ubuntu 24.04's apt nodejs is 18.x — TOO OLD for our Vite (needs Node 20+;
# apt node fails with "ReferenceError: CustomEvent is not defined").
# Install Node 22 LTS from NodeSource instead:
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt-get install -y nodejs
cd /srv/regradar/web && npm ci && npm run build
# Same-origin deployment: do NOT set VITE_API_URL.
```

## 6. deploy-check gate (≈1 min)

```bash
cd /srv/regradar && sudo -u regradar bash deploy/deploy-check.sh
```

**Do not continue until it prints `DEPLOY-CHECK PASSED`.** Every ✗ names the
exact missing var/file.

## 7. Services (≈3 min)

```bash
cp /srv/regradar/deploy/systemd/statuteproof-*.{service,timer} /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now statuteproof-api statuteproof-scheduler \
    statuteproof-telegram-bot statuteproof-compaction.timer \
    statuteproof-backup.timer statuteproof-heartbeat.timer \
    statuteproof-verify.timer
systemctl status statuteproof-api --no-pager | head -5   # expect: active (running)
curl -s http://127.0.0.1:5001/api/health                  # expect: {"ok": true, ...}
```

Notes:
- The API performs **zero** monitoring sweeps — sweeps come only from
  `statuteproof-scheduler` (first full sweep starts immediately and takes
  10–20 min in the background; you do not wait for it).
- Startup logs will print `BASELINE DIVERGENCE` errors for legacy pre-2026-07
  records — expected documented history; new runs realign the derived index.

## 8. Reverse proxy + TLS (≈4 min)

```bash
apt-get install -y caddy
cp /srv/regradar/deploy/Caddyfile /etc/caddy/Caddyfile
systemctl reload caddy
# Caddy fetches Let's Encrypt certificates automatically (~30-60 s)
curl -sI https://statuteproof.com | head -3          # expect HTTP/2 200
curl -s https://statuteproof.com/api/health          # expect {"ok": true, ...}
```

## 9. Log rotation + backups (≈2 min)

```bash
cp /srv/regradar/deploy/logrotate.d/statuteproof /etc/logrotate.d/statuteproof
logrotate -d /etc/logrotate.d/statuteproof   # dry-run parse check
# Nightly backup runs via statuteproof-backup.timer (enabled in step 7, ~02:30 UTC).
sudo -u regradar bash /srv/regradar/deploy/backup.sh   # first backup now
systemctl list-timers statuteproof-backup.timer --no-pager   # confirm scheduled
```

**Off-box copies (STRONGLY RECOMMENDED — survives droplet loss).** Backups
above are kept only on the droplet, so a lost droplet loses the entire evidence
trail. An off-box remote is the single most important backup setting. Set
`STATUTEPROOF_BACKUP_REMOTE` in `/srv/regradar/.env` (mode 600) to push the
newest archive off-box each run. It stays env-driven (no hardcoded remote), so
the push is a no-op when the var is unset — but `backup.sh` then **warns loudly
on stderr / in the journal every run** that backups are local-only and the
evidence trail is not protected against droplet loss. Point the remote at object
storage (S3/B2 via rclone) or a separate host (scp):

```bash
# rclone remote (preferred; e.g. an S3/B2 bucket) — install rclone + configure it first
echo 'STATUTEPROOF_BACKUP_REMOTE=s3remote:statuteproof-backups' >> /srv/regradar/.env
# ...or an scp target with key-based auth
echo 'STATUTEPROOF_BACKUP_REMOTE=backups@offbox.example:/srv/statuteproof-backups/' >> /srv/regradar/.env
systemctl restart statuteproof-backup.timer   # timer re-reads EnvironmentFile on next run
```

**Total: ≈30 min.**

## First-hour smoke-test checklist

1. `https://statuteproof.com` loads; login page renders; no console errors
2. `https://statuteproof.com/api/health` → `{"ok": true, ...}`
3. Register a test account → verification payload appears in
   `/srv/regradar/data/outbox/` (or real inbox if a provider is enabled) →
   verify → login works
4. `journalctl -u statuteproof-scheduler -n 50` shows sources being checked;
   after the first sweep `data/source_runs/source_runs.jsonl` grows with
   heartbeat + changed records carrying `normalized_hash`
5. `journalctl -u statuteproof-api -n 50` shows **no** fetch/pipeline lines
6. Telegram: send `/start` to @statuteproofalerts_bot → reply arrives
   (NEW token only)
7. `systemctl restart statuteproof-api` → health returns 200 within 10 s
8. Reboot the droplet once: all three services + both timers come back
   (`systemctl list-timers | grep statuteproof` — expect compaction + backup +
   heartbeat + verify)
9. Email dry-run (if a provider is configured):
   set `STATUTEPROOF_EMAIL_DRY_RUN=true`, restart api, trigger a test brief
   → `data/email_outbox/delivery_status.jsonl` gains a `dry_run` row → set
   back to false
10. `ufw status` shows only 22/80/443; `ssh` password login refused

## Restore from backup

If the droplet was lost, first pull the newest archive back from the off-box
remote (`STATUTEPROOF_BACKUP_REMOTE`) into `/srv/regradar/backups/` — e.g.
`rclone copy <remote> /srv/regradar/backups/` — then restore it locally:

```bash
systemctl stop statuteproof-api statuteproof-scheduler statuteproof-telegram-bot
cd /srv/regradar
mkdir -p /tmp/restore
tar -xzf backups/statuteproof-backup-<STAMP>.tar.gz -C /tmp/restore
rsync -a /tmp/restore/data/ data/
cp /tmp/restore/regradar.db "$(.venv/bin/python -c 'import sys; sys.path.insert(0,"."); from app.config import DB_PATH; print(DB_PATH)')"
chown -R regradar:regradar /srv/regradar
systemctl start statuteproof-api statuteproof-scheduler statuteproof-telegram-bot
# Verify: /api/health 200, then check startup logs — BASELINE DIVERGENCE
# beyond the known legacy set means trail/index mismatch from the restore.
```

## Operational notes

- **Evidence retention**: `statuteproof-compaction.timer` runs daily; job is
  idempotent. Manual run: `run.py compact-heartbeats --days 30`.
- **Evidence backups**: `statuteproof-backup.timer` runs daily (~02:30 UTC);
  keeps the newest 14 archives in `backups/`. Manual run:
  `bash deploy/backup.sh`. Set `STATUTEPROOF_BACKUP_REMOTE` in `.env` to also
  push each archive off-box (see § 9, strongly recommended); unset means on-box
  copies only and the script warns loudly on every run.
- **Evidence integrity self-check**: `statuteproof-verify.timer` runs daily
  (~04:20 UTC, after backup + compaction). It re-hashes every snapshot against
  its stored evidence hash and re-verifies the tamper-evident chain
  (read-only); on any divergence it pages the founder via the admin Telegram
  bot (best-effort) and the oneshot exits non-zero. Manual run:
  `run.py verify-trail-watch` (silent + exit 0 when clean). Confirm scheduled:
  `systemctl list-timers statuteproof-verify.timer --no-pager`.
- **Scheduler cadence**: change `--interval` in
  `statuteproof-scheduler.service`, then `systemctl daemon-reload && restart`.
- **Never** run two schedulers against the same data dir.
- **Secrets rotation**: tokens live only in `/srv/regradar/.env` (mode 600).
  After rotating, `systemctl restart` the affected service.
