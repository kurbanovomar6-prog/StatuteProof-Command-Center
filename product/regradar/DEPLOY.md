# StatuteProof — Deployment Runbook (fresh Ubuntu 24.04, target ≤ 30 min)

Every command below is meant to be run in order, as root unless stated.
Time estimates assume a 2 vCPU / 4 GB droplet and a registered domain with
DNS A records (`statuteproof.com`, `www.statuteproof.com`) already pointing
at the droplet — set DNS **before** droplet day, propagation is not counted.

## 0. Prerequisites (before droplet day)

- DNS A records for `statuteproof.com` + `www` → droplet IP
- A **fresh** Telegram alerts-bot token (the old one leaked into a local log
  and must be rotated via @BotFather before it ever touches prod)
- Email provider decision: `local_outbox` (pilot-safe default) or
  postmark/sendgrid/smtp credentials
- This repository reachable from the droplet (git remote or rsync)

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
# as root; adjust the clone source to your remote
git clone <YOUR_REPO_REMOTE> /srv/regradar-src
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
             # email provider block (leave local_outbox for the pilot)
chown regradar:regradar .env && chmod 600 .env
```

## 5. Frontend build (≈3 min)

```bash
apt-get install -y nodejs npm       # Ubuntu 24.04 ships Node 18+
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
    statuteproof-telegram-bot statuteproof-compaction.timer
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
# nightly backup at 02:30 UTC
( crontab -u regradar -l 2>/dev/null; \
  echo '30 2 * * * cd /srv/regradar && bash deploy/backup.sh >> logs/backup.log 2>&1' ) \
  | crontab -u regradar -
sudo -u regradar bash /srv/regradar/deploy/backup.sh   # first backup now
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
8. Reboot the droplet once: all three services + timer come back
   (`systemctl list-timers | grep statuteproof`)
9. Email dry-run (if a provider is configured):
   set `STATUTEPROOF_EMAIL_DRY_RUN=true`, restart api, trigger a test brief
   → `data/email_outbox/delivery_status.jsonl` gains a `dry_run` row → set
   back to false
10. `ufw status` shows only 22/80/443; `ssh` password login refused

## Restore from backup

```bash
systemctl stop statuteproof-api statuteproof-scheduler statuteproof-telegram-bot
cd /srv/regradar
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
- **Scheduler cadence**: change `--interval` in
  `statuteproof-scheduler.service`, then `systemctl daemon-reload && restart`.
- **Never** run two schedulers against the same data dir.
- **Secrets rotation**: tokens live only in `/srv/regradar/.env` (mode 600).
  After rotating, `systemctl restart` the affected service.
