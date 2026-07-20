# RegRadar — VPS Deployment Runbook

> **SUPERSEDED (2026-07-20).** This document describes the old nginx-based
> stack and is kept for history only. Current production is a DigitalOcean
> droplet running **Caddy + systemd units** with the app at `/srv/regradar`.
> Use [`DEPLOY.md`](../DEPLOY.md) for fresh deploys and
> [`UPDATE.md`](../UPDATE.md) for updates and rollback.

## Overview

RegRadar requires two processes running together:

| Process | Purpose |
|---------|---------|
| Python API (`run.py api`) | Handles `/api/contact`, `/api/health`, settings |
| nginx | Serves the built React frontend, proxies `/api/*` to Python |

**Static-only hosting (Vercel, Netlify, GitHub Pages) is not sufficient.**  
The contact form calls `/api/contact` via a relative URL. Without a backend at that path, every pilot request is silently lost. See `docs/deployment_architecture.md` for the full explanation.

This runbook assumes:
- Ubuntu 22.04 LTS VPS (or 24.04)
- Repo path: `/srv/regradar`
- App user: `regradar`
- Backend port: `5001` on `127.0.0.1` (not exposed directly)
- nginx handles all public traffic

---

## 1. Server prerequisites

```bash
# Update package index
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y \
  git \
  nginx \
  python3 \
  python3-venv \
  python3-pip \
  curl \
  ufw

# Install Node.js 20.x (for frontend build only — not needed at runtime)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify versions
python3 --version    # 3.10+ required; 3.12 preferred
node --version       # 20.x
npm --version        # 10.x
nginx -v
```

### Create app user and directory

```bash
# Create a system user without a login shell
sudo useradd --system --shell /usr/sbin/nologin --home /srv/regradar regradar

# Create the app directory
sudo mkdir -p /srv/regradar
sudo chown regradar:regradar /srv/regradar

# Allow your deploy user (e.g. ubuntu) to write to the directory
sudo usermod -aG regradar ubuntu   # adjust 'ubuntu' to your SSH user if needed
```

---

## 2. Clone repository

```bash
# Clone as your SSH user; ownership will be fixed below
cd /srv
sudo git clone https://github.com/kurbanovomar6-prog/regradar.git regradar
# or if deploying from a branch:
# sudo git clone --branch main https://github.com/kurbanovomar6-prog/regradar.git regradar

cd /srv/regradar
git checkout main
git pull

# Fix ownership so app user can read and write data/
sudo chown -R regradar:regradar /srv/regradar
# Allow your deploy user to pull/rebuild without sudo
sudo chmod -R g+w /srv/regradar
```

---

## 3. Python environment setup

```bash
cd /srv/regradar

# Create virtual environment
python3 -m venv .venv

# Upgrade pip
.venv/bin/pip install --upgrade pip

# Install all dependencies from requirements.txt
.venv/bin/pip install -r requirements.txt
```

Do not use a partial Python install for production. Even when systemd only runs
`run.py api`, `run.py` imports the monitoring pipeline before dispatching the
API command, so parser/scraper packages must be importable at process startup.

---

## 4. Playwright setup (browser-based source scraping)

The Playwright Python package is installed by `requirements.txt` because it is
imported at startup. The Chromium browser download below is only needed for
source monitoring commands (`run.py all`, `run.py health`, `run.py watch`) and
is **not required** for `run.py api` alone.

Install only if you plan to run monitoring from this server:

```bash
# Install system dependencies for Chromium
sudo apt install -y \
  libglib2.0-0 libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
  libcups2 libdrm2 libdbus-1-3 libexpat1 libxcb1 libxkbcommon0 \
  libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 \
  libgbm1 libpango-1.0-0 libcairo2 libasound2

# Install Playwright's Chromium browser
.venv/bin/python -m playwright install chromium
```

Skip this section if the server will only serve the website and API — not run scheduled monitoring.

---

## 5. Frontend build

```bash
cd /srv/regradar/web

# Install Node dependencies from lockfile
npm ci

# Build the React app
npm run build

# Confirm output exists
ls -la /srv/regradar/web/dist/
# Should show: index.html, assets/
```

`web/dist/` is the built frontend. It is served statically by nginx.

---

## 6. Environment variables

Create the production `.env` file:

```bash
sudo -u regradar nano /srv/regradar/.env
```

Contents (replace placeholders with real values):

```bash
# RegRadar production environment

# ── Required for contact form delivery ───────────────────────────────────────
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
TELEGRAM_CHAT_ID=YOUR_CHAT_ID_HERE

# ── Leave unset or set to 0 in production ────────────────────────────────────
# Setting this to 1 disables Telegram delivery — use only for local smoke tests.
# REGRADAR_CONTACT_DELIVERY_DISABLED=0

# ── Optional ─────────────────────────────────────────────────────────────────
# LOG_LEVEL=WARNING
# REGRADAR_DB_PATH=/srv/regradar/regradar.db
# ENABLE_AI_ANALYSIS=false
# ANTHROPIC_API_KEY=
# ENABLE_TELEGRAM_ALERTS=false
```

Restrict permissions so only the app user can read it:

```bash
sudo chown regradar:regradar /srv/regradar/.env
sudo chmod 600 /srv/regradar/.env
```

**Never commit `.env` to git.** It is already in `.gitignore`.

---

## 7. Persistent data directory

```bash
# Create data directory
sudo mkdir -p /srv/regradar/data

# Fix ownership
sudo chown -R regradar:regradar /srv/regradar/data
sudo chmod 750 /srv/regradar/data
```

`data/contact_requests.jsonl` is written here when a prospect submits the contact form. On a VPS, this directory persists across reboots and deployments as long as the disk is not wiped.

**Back up `data/` regularly.** It contains all queued pilot requests and cannot be recovered from git.

```bash
# Example: daily backup to another location
# crontab -e → add:
# 0 3 * * * cp -r /srv/regradar/data /srv/backups/regradar-data-$(date +%Y%m%d)
```

---

## 8. systemd service

Create the service unit file:

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

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable regradar-api
sudo systemctl start regradar-api

# Verify it's running
sudo systemctl status regradar-api

# Test API is reachable locally (before nginx)
curl http://127.0.0.1:5001/api/health
# Expected: {"status": "ok", "service": "RegRadar API"}
```

Follow logs in real time:

```bash
sudo journalctl -u regradar-api -f
```

View last 100 lines:

```bash
sudo journalctl -u regradar-api -n 100
```

---

## 9. nginx config

Create the site config:

```bash
sudo nano /etc/nginx/sites-available/regradar
```

Contents (replace `regradar.example.com` with your domain):

```nginx
server {
    listen 80;
    server_name regradar.example.com;

    root /srv/regradar/web/dist;
    index index.html;

    # Proxy all /api/* requests to the Python backend
    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 30s;
        proxy_connect_timeout 5s;
    }

    # SPA fallback — all other routes return index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Deny direct access to data directory (extra safety)
    location /data/ {
        deny all;
        return 404;
    }
}
```

Enable and reload:

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/regradar /etc/nginx/sites-enabled/regradar

# Remove the default placeholder if present
sudo rm -f /etc/nginx/sites-enabled/default

# Test config syntax
sudo nginx -t
# Expected: nginx: configuration file /etc/nginx/nginx.conf test is successful

# Reload nginx
sudo systemctl reload nginx
```

### Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

---

## 10. SSL (HTTPS)

**Do not send outreach from an HTTP site.** Get a TLS certificate before sharing the URL with prospects.

Requires a domain name pointing to this VPS. Update your domain's DNS A record to the VPS IP, wait for propagation, then:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d regradar.example.com

# Test automatic renewal
sudo certbot renew --dry-run
```

certbot modifies the nginx config automatically to redirect HTTP → HTTPS and add the certificate.

If the domain is not ready yet, test over HTTP with the VPS IP first:

```bash
# Temporarily test with IP (replace with your server's public IP)
curl http://YOUR_VPS_IP/api/health
```

---

## 11. Production smoke test (with Telegram delivery)

Run this after initial deployment and after each major update:

```bash
# 1. Confirm API health
curl https://regradar.example.com/api/health
# {"status": "ok", "service": "RegRadar API"}

# 2. Confirm Telegram independently
cd /srv/regradar
sudo -u regradar .venv/bin/python run.py telegram-test

# 3. Open the site in a browser
#    Navigate to the contact section or Watchlist Builder
#    Fill in OBVIOUS fake data: name "SMOKE TEST", email "smoke-test@example.com"
#    In the message field: "SMOKE TEST ONLY — do not treat as real lead"
#    Submit the form

# 4. Verify Telegram delivery
#    Check the admin Telegram chat for the submission

# 5. Verify the queue was written
sudo -u regradar .venv/bin/python run.py contact-queue --latest

# 6. Check API logs for any errors
sudo journalctl -u regradar-api -n 50

# 7. Clean up the smoke test entry
#    Edit /srv/regradar/data/contact_requests.jsonl
#    Remove the last line (the smoke test entry)
#    Or delete the file if it contains only the test entry:
#    sudo -u regradar rm /srv/regradar/data/contact_requests.jsonl
```

---

## 12. Safe dry-run smoke test (no Telegram delivery)

Use this to verify queue behavior without sending a real Telegram message:

```bash
# 1. Temporarily disable Telegram delivery in .env
sudo nano /srv/regradar/.env
# Add or set:
# REGRADAR_CONTACT_DELIVERY_DISABLED=1

# 2. Restart the API
sudo systemctl restart regradar-api
sudo systemctl status regradar-api

# 3. Submit fake contact request
curl -s -X POST https://regradar.example.com/api/contact \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Smoke Test",
    "email": "smoke-test@example.com",
    "company": "RegRadar Test",
    "message": "Smoke test only. Do not treat as real lead."
  }'
# Expected: {"ok": true, "queued": true, "delivered": false}

# 4. Verify queue entry
sudo -u regradar .venv/bin/python run.py contact-queue --latest

# 5. Restore production setting in .env
sudo nano /srv/regradar/.env
# Remove or comment out:
# REGRADAR_CONTACT_DELIVERY_DISABLED=1
# or set to:
# REGRADAR_CONTACT_DELIVERY_DISABLED=0

# 6. Restart API to apply
sudo systemctl restart regradar-api

# 7. Clean up the test queue entry
#    Edit /srv/regradar/data/contact_requests.jsonl and remove only the
#    smoke-test line. Delete the file only if it contains no real prospects.
#    sudo -u regradar rm /srv/regradar/data/contact_requests.jsonl
```

---

## 13. Deployment update procedure

After pushing new code to the repo:

```bash
cd /srv/regradar

# 1. Pull latest code
sudo -u regradar git pull origin main

# 2. Rebuild frontend if frontend files changed
cd web && npm ci && npm run build && cd ..

# 3. Restart backend
sudo systemctl restart regradar-api

# 4. Reload nginx if nginx config changed
# (only if you edited /etc/nginx/sites-available/regradar)
sudo nginx -t && sudo systemctl reload nginx

# 5. Verify health
curl https://regradar.example.com/api/health

# 6. Run smoke test (dry-run or full depending on risk)
```

---

## 14. Rollback procedure

```bash
# 1. Find the previous stable commit
cd /srv/regradar
git log --oneline -10

# 2. Checkout previous commit
sudo -u regradar git checkout <PREVIOUS_COMMIT_HASH>

# 3. Rebuild frontend
cd web && npm ci && npm run build && cd ..

# 4. Restart API
sudo systemctl restart regradar-api

# 5. Verify
curl https://regradar.example.com/api/health

# 6. If stable, create a fix branch; don't leave HEAD detached in production
sudo -u regradar git checkout main
sudo -u regradar git revert HEAD    # preferred over checkout to old hash
```

`data/contact_requests.jsonl` is NOT managed by git and is unaffected by rollbacks.

---

## 15. Troubleshooting

### `/api/contact` returns 404

```bash
# Check nginx routing
curl http://127.0.0.1:5001/api/health   # should return ok
sudo nginx -t                            # check config syntax
cat /etc/nginx/sites-enabled/regradar    # check location /api/ block
sudo journalctl -u nginx -n 20
```

nginx `proxy_pass` target must end without a trailing slash when the `location` block has a trailing slash:  
`location /api/ { proxy_pass http://127.0.0.1:5001; }` — this is correct.

### Frontend loads but contact form fails silently

- Check browser DevTools → Network → look for 4xx/5xx on `/api/contact`
- Check that nginx `location /api/` block is present and pointing to port 5001
- Check that `regradar-api` service is running

### Telegram not delivered

```bash
# Test Telegram independently
sudo -u regradar .venv/bin/python run.py telegram-test

# Check env vars are set without printing secret values
sudo -u regradar bash -c 'set -a; source /srv/regradar/.env; set +a; test -n "$TELEGRAM_BOT_TOKEN" && echo "token present" || echo "token missing"; test -n "$TELEGRAM_CHAT_ID" && echo "chat id present" || echo "chat id missing"'

# Note: REGRADAR_CONTACT_DELIVERY_DISABLED must be 0 or unset in production
```

### Queue file missing after submission

```bash
# Check data directory exists and is writable
ls -la /srv/regradar/data/
sudo -u regradar touch /srv/regradar/data/test-write && rm /srv/regradar/data/test-write
```

If permission denied: `sudo chown -R regradar:regradar /srv/regradar/data`

### Permission denied writing `data/contact_requests.jsonl`

```bash
sudo chown -R regradar:regradar /srv/regradar/data
sudo chmod 750 /srv/regradar/data
```

### systemd service fails to start

```bash
sudo journalctl -u regradar-api -n 50
# Common causes:
# - Python not found at .venv/bin/python → check venv was created correctly
# - Import error → pip install -r requirements.txt was not run
# - Port already in use → check what's on port 5001: ss -tlnp | grep 5001
# - .env not found → check EnvironmentFile path in service unit
```

### nginx 502 Bad Gateway

```bash
# Python API is not running or crashed
sudo systemctl status regradar-api
sudo journalctl -u regradar-api -n 30
sudo systemctl restart regradar-api
```

### CORS error in browser (only if split-origin deployed)

If you deploy the frontend on a different domain from the API, the CORS headers in `app/api.py` must be updated. The current hardcoded value (`http://localhost:5173`) blocks all cross-origin requests. Request a separate code change task for split-origin deployment — it is not needed for VPS + nginx same-origin deployment.

### `npm run build` fails

```bash
cd /srv/regradar/web
node --version     # must be 20.x
npm ci             # use ci not install to respect lockfile
npm run build
# Check for missing packages or wrong Node version
```

### Python import error at startup

```bash
sudo -u regradar /srv/regradar/.venv/bin/python -m compileall app run.py -q
# If errors: re-run pip install -r requirements.txt
sudo -u regradar /srv/regradar/.venv/bin/pip install -r /srv/regradar/requirements.txt
```

---

## 16. Security notes

- **Never commit `.env`** — it is already in `.gitignore`. Verify: `git ls-files .env` should return nothing.
- **Restrict `.env` permissions**: `chmod 600 /srv/regradar/.env` — readable only by `regradar` user.
- **Keep `data/` private**: The nginx config blocks direct access to `/data/`. Do not accidentally expose it.
- **`data/contact_requests.jsonl` contains prospect details** — treat it as sensitive. Back it up securely.
- **Use HTTPS before outreach** — do not share an HTTP URL with prospects.
- **Keep the server updated**: `sudo apt update && sudo apt upgrade -y` regularly.
- **Use SSH keys**, not passwords, for server access.
- **Disable password auth** in `/etc/ssh/sshd_config`: `PasswordAuthentication no`

---

## 17. Future improvements

| Improvement | When to add |
|-------------|-------------|
| ✅ `requirements.txt` | Done — added in this task |
| Automated `data/` backup | Before receiving more than ~10 leads |
| Let's Encrypt HTTPS renewal check | After first certificate issued |
| Email / CRM secondary delivery | If Telegram-only feels risky for volume |
| CI/CD deploy pipeline | When team size or deploy frequency warrants it |
| Dockerfile | When portability or reproducibility becomes a need |
| Replace Python stdlib HTTP server | Only if concurrency or response-time becomes a bottleneck |

---

## Quick-reference commands

```bash
# Status
sudo systemctl status regradar-api nginx

# Logs
sudo journalctl -u regradar-api -f
sudo journalctl -u nginx -f

# API health
curl http://127.0.0.1:5001/api/health

# View queued leads
sudo -u regradar /srv/regradar/.venv/bin/python run.py contact-queue
sudo -u regradar /srv/regradar/.venv/bin/python run.py contact-queue --latest
sudo -u regradar /srv/regradar/.venv/bin/python run.py contact-queue --json

# Restart
sudo systemctl restart regradar-api
sudo systemctl reload nginx

# Update
cd /srv/regradar && git pull origin main && cd web && npm ci && npm run build && cd .. && sudo systemctl restart regradar-api
```
