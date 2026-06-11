# RegRadar Production Deployment Checklist

Reference: `docs/vps_deployment_runbook.md` — full commands for each step.

---

## 1. Pre-deployment requirements

- [ ] VPS selected — Hetzner CX11 (~$6/mo) or DigitalOcean Basic recommended
- [ ] Ubuntu 22.04 LTS or 24.04 LTS
- [ ] Public IP confirmed; SSH key-based access working
- [ ] Domain name pointed to VPS IP (or IP-only HTTP testing accepted for now)
- [ ] GitHub repo accessible from server (HTTPS clone, no deploy key needed)
- [ ] `TELEGRAM_BOT_TOKEN` obtained from @BotFather
- [ ] `TELEGRAM_CHAT_ID` confirmed (run `/start` with the bot; or use `@userinfobot`)
- [ ] `.env` does NOT exist in the repo and is in `.gitignore`
- [ ] `data/` directory will be persistent (VPS disk — survives reboots ✓)
- [ ] **Do NOT deploy to Vercel/Netlify/GitHub Pages** — `/api/contact` will 404 silently

---

## 2. Server setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y git nginx python3 python3-venv python3-pip curl ufw

# Install Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify
python3 --version   # 3.10+
node --version      # v20.x
nginx -v
```

- [ ] System packages installed
- [ ] Node.js 20.x confirmed
- [ ] Python 3.10+ confirmed

```bash
# Create app user
sudo useradd --system --shell /usr/sbin/nologin --home /srv/regradar regradar

# Clone repo
sudo mkdir -p /srv/regradar
sudo git clone https://github.com/kurbanovomar6-prog/regradar.git /srv/regradar
sudo chown -R regradar:regradar /srv/regradar
sudo chmod -R g+w /srv/regradar
```

- [ ] `regradar` user created
- [ ] Repo cloned to `/srv/regradar`

```bash
# Python venv
cd /srv/regradar
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

- [ ] `.venv` created
- [ ] `requirements.txt` installed (full install — includes scraper packages needed even for API-only mode)

```bash
# Frontend build
cd /srv/regradar/web
npm ci
npm run build
ls dist/   # must show index.html and assets/
```

- [ ] `web/dist/` created and contains `index.html`

---

## 3. Environment

```bash
sudo -u regradar nano /srv/regradar/.env
```

Contents:

```
TELEGRAM_BOT_TOKEN=YOUR_REAL_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_REAL_CHAT_ID
```

```bash
sudo chown regradar:regradar /srv/regradar/.env
sudo chmod 600 /srv/regradar/.env
```

- [ ] `.env` created at `/srv/regradar/.env`
- [ ] `TELEGRAM_BOT_TOKEN` set to real token
- [ ] `TELEGRAM_CHAT_ID` set to real chat ID
- [ ] `REGRADAR_CONTACT_DELIVERY_DISABLED` is **unset or 0** (not 1) in production
- [ ] File permissions: `600` (owner-read only)
- [ ] Verify `.env` not git-tracked: `git ls-files .env` → must return nothing

---

## 4. systemd service

```bash
sudo nano /etc/systemd/system/regradar-api.service
```

Contents:

```ini
[Unit]
Description=RegRadar API Server
After=network.target

[Service]
Type=simple
User=regradar
Group=regradar
WorkingDirectory=/srv/regradar
EnvironmentFile=/srv/regradar/.env
ExecStart=/srv/regradar/.venv/bin/python run.py api --host 127.0.0.1 --port 5001
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable regradar-api
sudo systemctl start regradar-api
sudo systemctl status regradar-api

# Confirm API is up locally
curl http://127.0.0.1:5001/api/health
# Expected: {"status": "ok", "service": "RegRadar API"}
```

- [ ] Service file created
- [ ] `systemctl start regradar-api` — status shows `active (running)`
- [ ] `curl http://127.0.0.1:5001/api/health` returns `{"status": "ok"}`
- [ ] `systemctl enable regradar-api` — service survives reboot

---

## 5. nginx

```bash
sudo nano /etc/nginx/sites-available/regradar
```

Contents (replace domain or use `_` for IP-only testing):

```nginx
server {
    listen 80;
    server_name your-domain.com;   # or _ for IP-only testing

    root /srv/regradar/web/dist;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 30s;
        proxy_connect_timeout 5s;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /data/ {
        deny all;
        return 404;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/regradar /etc/nginx/sites-enabled/regradar
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t          # must say "test is successful"
sudo systemctl reload nginx
```

```bash
# Firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

- [ ] nginx site config created
- [ ] `nginx -t` passes
- [ ] nginx reloaded
- [ ] Firewall allows SSH + HTTP/HTTPS

---

## 6. SSL — HTTPS (required before outreach)

**Do not share an HTTP URL with prospects.**

```bash
# DNS must be pointing to this VPS before running certbot
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

- [ ] Domain DNS A record → VPS IP (propagated)
- [ ] `certbot --nginx` succeeded — HTTPS certificate issued
- [ ] `https://your-domain.com/api/health` returns `{"status": "ok"}`
- [ ] Auto-renewal dry-run passed

> If domain is not ready: test with `curl http://YOUR_VPS_IP/api/health` over HTTP first.

---

## 7. Contact delivery verification

```bash
# 1. Test Telegram independently (does not use /api/contact)
sudo -u regradar /srv/regradar/.venv/bin/python run.py telegram-test
# A test message should arrive in your Telegram chat
```

- [ ] `telegram-test` sends successfully

```bash
# 2. Submit fake contact request (sends real Telegram)
curl -s -X POST https://your-domain.com/api/contact \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SMOKE TEST — ignore",
    "email": "smoke-test@example.com",
    "company": "RegRadar Internal",
    "message": "SMOKE TEST ONLY. System verification. Do not treat as a lead."
  }'
# Expected: {"ok": true, "queued": true, "delivered": true}
```

- [ ] Response: `ok: true, queued: true, delivered: true`
- [ ] Telegram message received in admin chat

```bash
# 3. Verify queue entry
sudo -u regradar /srv/regradar/.venv/bin/python run.py contact-queue --latest

# 4. Clean up test entry (IMPORTANT — do not leave fake leads in queue)
# Edit /srv/regradar/data/contact_requests.jsonl and delete the last line,
# or if it contains only the test entry: sudo -u regradar rm /srv/regradar/data/contact_requests.jsonl
```

- [ ] Queue entry visible via `contact-queue --latest`
- [ ] Smoke test entry cleaned up

---

## 8. Source health (post-deployment)

Coverage data is included in the deployed codebase (`source_audit_2026-05-27.json`). No health run is required on the server for the API to function.

```bash
# Optional: verify coverage report reads correctly on the server
sudo -u regradar /srv/regradar/.venv/bin/python run.py coverage --json
```

- [ ] Coverage report runs without error (optional — for confidence only)
- [ ] Do not run `health` or `source-audit` on server during initial deployment — these take 40+ minutes and are not required for the API

> SA and QA scores show `100 limited` — this is correct. Geo-blocked sources are excluded from the denominator. Disclose in demos.

---

## 9. Final go-live checklist

```bash
# Open in browser:
# https://your-domain.com
```

- [ ] Landing page loads in browser
- [ ] Coverage section shows correct market count
- [ ] Source proof links visible in Interactive Demo
- [ ] Watchlist Builder renders and allows market selection
- [ ] Contact form submits and shows success state
- [ ] `/api/contact` returns `ok: true` (check Network tab if needed)
- [ ] Queue is on persistent VPS disk (not ephemeral)
- [ ] `git ls-files .env` returns nothing — no secrets committed
- [ ] `git status` on server is clean
- [ ] `REGRADAR_CONTACT_DELIVERY_DISABLED` is not `1` in `.env`

---

## 10. Do not proceed if any of these are true

| Blocker | Check |
|---------|-------|
| `/api/contact` returns 404 | nginx routing missing; `proxy_pass` block wrong |
| systemd service not `active (running)` | Python import error; check `journalctl -u regradar-api -n 50` |
| nginx 502 Bad Gateway | Python API not running or crashed |
| Contact queue not writable | `chown -R regradar:regradar /srv/regradar/data` |
| `.env` missing | Telegram delivery will fail silently; queue still works |
| `data/` not persistent | All leads lost on restart/redeploy |
| HTTPS not configured | Do not send outreach with HTTP URL |

---

## Quick-reference commands (post-deployment)

```bash
# Service status
sudo systemctl status regradar-api nginx

# API health
curl http://127.0.0.1:5001/api/health

# View logs
sudo journalctl -u regradar-api -f

# View queued leads
sudo -u regradar /srv/regradar/.venv/bin/python run.py contact-queue

# Restart
sudo systemctl restart regradar-api
sudo systemctl reload nginx

# Update (after git push)
cd /srv/regradar && git pull origin main
cd web && npm ci && npm run build && cd ..
sudo systemctl restart regradar-api
```
