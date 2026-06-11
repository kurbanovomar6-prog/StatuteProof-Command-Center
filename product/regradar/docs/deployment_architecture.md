# RegRadar Deployment Architecture

## 1. Current production requirements

RegRadar has two parts that must run together:

| Part | What it is | Build/Start |
|------|-----------|-------------|
| Frontend | React 19 + Vite SPA | `cd web && npm run build` → `web/dist/` |
| Backend API | Python stdlib HTTP server | `python run.py api` |

The frontend calls `/api/contact` (and other `/api/*` routes) using a **relative URL**.  
This means the frontend and backend must share the same HTTP origin in production.

---

## 2. Why static-only hosting is not enough

> **Do not deploy the frontend as static-only unless `/api/contact` is routed to a live backend. Otherwise pilot requests will fail or be lost.**

The Vite dev proxy (`vite.config.js` → `'/api'` → `http://127.0.0.1:5001`) is **dev-only**.  
It is not compiled into `web/dist/` and does not apply to built static assets.

Deploying only `web/dist/` to Vercel, Netlify, or GitHub Pages means:

- Every `/api/contact` POST returns `404` or `Cannot POST /api/contact`
- The contact form shows an error to the prospect
- No queue entry is written
- Lead is permanently lost

---

## 3. Recommended MVP deployment — VPS + nginx

### Why

- Persistent filesystem (no ephemeral FS risk for `data/contact_requests.jsonl`)
- nginx proxies `/api/` → Python, serves `web/dist/` for everything else
- Python API stays on `127.0.0.1:5001` (not exposed directly to internet)
- Full control over env vars, process restart, logs
- Cheapest long-term option (~$6/month on Hetzner CX11 or DigitalOcean Basic)

### Architecture

```
Internet
   │
   ▼
nginx (port 80/443)
   ├── /api/*  → proxy_pass http://127.0.0.1:5001
   └── /*      → root web/dist/ (static files)
                          │
                          ▼
               Python API (127.0.0.1:5001)
                  writes data/contact_requests.jsonl
                  sends Telegram alerts
```

### Build steps (run once on the server or in CI)

```bash
# 1. Clone / pull repo
git clone <repo-url> /srv/regradar
cd /srv/regradar

# 2. Install Python dependencies
python3 -m venv .venv

# run.py imports the monitoring pipeline before dispatching the api command,
# so the API process still needs the scraper/parser packages installed.
.venv/bin/pip install -r requirements.txt

# Required before running health checks or any source fetch that uses Playwright.
# The API-only service does not need the Chromium browser download.
.venv/bin/python -m playwright install chromium

# 3. Build frontend
cd web && npm install && npm run build && cd ..
# output: web/dist/
```

### nginx config snippet

```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /srv/regradar/web/dist;
    index index.html;

    # Route API requests to Python backend
    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_read_timeout 30s;
    }

    # SPA fallback — send all non-asset requests to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

For HTTPS, add a Let's Encrypt certificate with certbot.

### Start command

```bash
# Start the Python API (runs on 127.0.0.1:5001 by default)
.venv/bin/python run.py api
```

For persistence, use a process manager:

```bash
# systemd example — /etc/systemd/system/regradar-api.service
[Unit]
Description=RegRadar API
After=network.target

[Service]
User=regradar
WorkingDirectory=/srv/regradar
ExecStart=/srv/regradar/.venv/bin/python run.py api
EnvironmentFile=/srv/regradar/.env
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable regradar-api
sudo systemctl start regradar-api
sudo systemctl status regradar-api
```

### Success check

```bash
curl https://your-domain.com/api/health
# {"status": "ok", "service": "RegRadar API"}

# From browser: visit https://your-domain.com — landing page loads
# From browser: submit a test contact form — Telegram message arrives
```

---

## 4. Alternative deployment options

### Option B — Render / Railway / Fly.io (single service)

These platforms can run a Python HTTP server as a web service.

**Setup:**
- Build command: `cd web && npm install && npm run build`
- Start command: `python run.py api --host 0.0.0.0 --port $PORT`
- The Python API does NOT currently serve `web/dist/` static files.

**Bridging the gap:**  
You need either:
1. Add a reverse proxy (nginx sidecar) to serve static files and proxy `/api/` — not trivial on single-process platforms
2. Make the Python API serve `web/dist/` files for non-API routes — requires a small code change

If using this option, request that change explicitly as a separate task.

**Persistent volume:**  
On Render/Railway, attach a persistent disk mounted at `/data` and set:
```
REGRADAR_DB_PATH=/data/regradar.db
```
The `data/contact_requests.jsonl` path is currently hardcoded to `BASE_DIR/data/` — it is not affected by `REGRADAR_DB_PATH`. Ensure the platform's filesystem is not ephemeral, or mount the entire `/srv/regradar/data/` directory.

### Option C — Split frontend + backend (not recommended for MVP)

- Frontend: Vercel/Netlify/CDN serving `web/dist/`
- Backend: Render/Railway/VPS running Python API

**Blockers before this works:**
1. Frontend uses relative `/api/contact` — must be changed to an absolute URL (e.g. `VITE_API_URL=https://api.your-domain.com`).
2. `app/api.py` CORS is hardcoded to `http://localhost:5173` — must be updated to the production frontend domain.
3. More moving parts and harder to debug.

**Not recommended** unless there is a specific need to CDN-host the frontend. For MVP, same-origin is simpler and already supported.

---

## 5. Required environment variables

Set in `/srv/regradar/.env` (VPS) or as platform environment variables:

| Variable | Required | Purpose |
|----------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | For contact delivery | Bot token for pilot request alerts |
| `TELEGRAM_CHAT_ID` | For contact delivery | Admin chat to receive alerts |
| `ENABLE_TELEGRAM_ALERTS` | Optional | Enable alert push for monitoring runs (separate from contact delivery) |
| `REGRADAR_DB_PATH` | Optional | Custom SQLite path (default: `regradar.db` next to `run.py`) |
| `REGRADAR_CONTACT_DELIVERY_DISABLED` | **Local smoke test only** | Set to `1` to skip Telegram on `/api/contact`. Remove in production. |
| `LOG_LEVEL` | Optional | `DEBUG` for verbose logs, `WARNING` (default) for quiet |

`TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are the only variables required for the contact form to deliver pilot requests.

---

## 6. Persistent storage requirements

| Path | Contents | Risk if lost |
|------|----------|-------------|
| `data/contact_requests.jsonl` | All queued pilot requests | Lead data lost permanently |
| `regradar.db` (configurable) | Monitoring history, alerts | Monitoring data lost (re-runs recover) |
| `data/telegram_clients.json` | Per-client Telegram targets | Settings lost |

**On a VPS**: these are on disk and survive reboots. Back up `data/` regularly.  
**On Render/Railway/Fly**: attach a persistent volume. Do not rely on the default container filesystem — it is wiped on each deploy.

Verify the queue file is not tracked by git:
```bash
git ls-files data/contact_requests.jsonl   # should return nothing
```

---

## 7. Frontend/backend routing

### Same-origin (recommended)

```
GET/POST /api/*   → nginx proxy → Python API on 127.0.0.1:5001
GET /*            → nginx root  → web/dist/ static files
```

The CORS headers in `app/api.py` are present but irrelevant for same-origin requests. They are set to `http://localhost:5173` (Vite dev origin) and do not interfere.

### Split-origin (requires code changes, not covered here)

Two changes needed in source before this works:
1. `app/api.py` line 39: `_ALLOWED_ORIGIN = "https://your-frontend-domain.com"`
2. `web/src/components/Contact.jsx` line 203: change `fetch('/api/contact', ...)` to use an absolute URL env var

---

## 8. Contact delivery smoke test

After deployment, run before announcing to pilots:

```bash
# 1. Verify API is reachable
curl https://your-domain.com/api/health

# 2. Verify Telegram delivery independently
python run.py telegram-test

# 3. Submit a fake contact request (sends real Telegram — use obvious fake data)
curl -s -X POST https://your-domain.com/api/contact \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SMOKE TEST — ignore",
    "email": "smoke-test@example.com",
    "company": "RegRadar Internal Test",
    "message": "SMOKE TEST ONLY. System verification."
  }'
# Expected: {"ok": true, "queued": true, "delivered": true}

# 4. Verify queue on server
python run.py contact-queue --latest

# 5. Clean up test entry
# Manually remove the last line from data/contact_requests.jsonl,
# or delete the file if it contains only the test entry.
```

See `docs/production_contact_smoke_test.md` for the full smoke test procedure and safe local test using `REGRADAR_CONTACT_DELIVERY_DISABLED=1`.

---

## 9. Operational checklist

Before taking live traffic:

- [ ] Backend API is running and returns `{"status": "ok"}` at `/api/health`
- [ ] Frontend loads at root URL and contact form renders
- [ ] nginx (or equivalent) routes `/api/*` to Python API
- [ ] Python dependencies are installed in `.venv`; `python run.py api` starts without import errors
- [ ] `TELEGRAM_BOT_TOKEN` is set and `python run.py telegram-test` sends successfully
- [ ] `TELEGRAM_CHAT_ID` is set and messages arrive in the correct chat
- [ ] `data/` directory is on a persistent volume or disk
- [ ] `data/contact_requests.jsonl` is NOT git-tracked (`git ls-files data/contact_requests.jsonl` returns nothing)
- [ ] Smoke test contact submission received in Telegram
- [ ] Smoke test entry visible via `python run.py contact-queue --latest`
- [ ] Fake smoke test entry cleaned up from queue

---

## 10. Rollback checklist

If deployment breaks:

```bash
# 1. Check API status
sudo systemctl status regradar-api
journalctl -u regradar-api -n 50

# 2. Check nginx
sudo nginx -t
sudo systemctl status nginx

# 3. Roll back code
git log --oneline -5
git checkout <previous-commit-hash>
cd web && npm run build && cd ..
sudo systemctl restart regradar-api

# 4. Verify API health
curl http://127.0.0.1:5001/api/health
```

Contact queue is preserved during rollbacks — it is not managed by git.

---

## 11. Future upgrade path

After MVP validation:

| Upgrade | When to do it |
|---------|--------------|
| HTTPS via Let's Encrypt | Before first external prospect |
| Database backup cron | After first real contact submission |
| CRM/email secondary delivery | When Telegram-only feels risky for lead volume |
| Docker/compose setup | When team grows or CI/CD needed |
| Split frontend CDN | Only if backend becomes a bottleneck |
| Replace Python stdlib HTTP server | If response time or concurrency becomes an issue |

Do not upgrade prematurely. The MVP backend handles low traffic well.
