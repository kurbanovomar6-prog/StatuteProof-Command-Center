# Production Contact Smoke Test

## Purpose

Verify that the contact form pipeline works end-to-end before sending real traffic:
- Form submission reaches `/api/contact`
- Request is written to `data/contact_requests.jsonl`
- Telegram delivery is attempted with the configured credentials
- Operator can inspect and recover queued requests

---

## Preconditions

| Item | Required | Notes |
|------|----------|-------|
| Python `.venv` activated | Yes | `source .venv/bin/activate` |
| `run.py api` reachable | Yes | Port 5001 by default |
| `data/` directory writable | Yes | Created automatically if absent |
| `TELEGRAM_BOT_TOKEN` | For delivery | Without it, requests queue only |
| `TELEGRAM_CHAT_ID` | For delivery | Without it, requests queue only |
| `REGRADAR_CONTACT_DELIVERY_DISABLED=1` | For safe local tests | Queues `/api/contact` requests without Telegram delivery |

---

## Critical: `.env` always overrides shell env vars

`app/config.py` calls `load_dotenv(..., override=True)`.

This means: setting `TELEGRAM_BOT_TOKEN=""` in your shell **does not prevent Telegram delivery** if `.env` contains the real token.

**Preferred safe local test without Telegram:**

Use the contact-only delivery-disable flag when starting the API:
```bash
REGRADAR_CONTACT_DELIVERY_DISABLED=1 .venv/bin/python run.py api --port 5012
```

This flag affects only `/api/contact`: the request is still written to `data/contact_requests.jsonl`, but Telegram delivery is skipped and the response should include:
```json
{"ok": true, "queued": true, "delivered": false, "message": "Request received and queued."}
```

Other Telegram commands, including `telegram-test`, are not disabled by this flag.

**Older fallback if the flag is unavailable:**

Option A — temporarily rename or blank out Telegram lines in `.env`:
```bash
# Before test: comment out creds in .env
# TELEGRAM_BOT_TOKEN=...
# TELEGRAM_CHAT_ID=...

# After test: restore them
```

Option B — test in an environment where `.env` does not exist (e.g., CI, Docker, staging server with env vars set via platform).

If Telegram creds are configured, `.env` is present, and `REGRADAR_CONTACT_DELIVERY_DISABLED` is not set, every POST to `/api/contact` sends a real Telegram message.

---

## Local safe test (queue-only, no Telegram)

**Step 1** — Start API on a test port with contact delivery disabled:
```bash
REGRADAR_CONTACT_DELIVERY_DISABLED=1 .venv/bin/python run.py api --port 5012
```

**Step 2** — Submit a fake request (in a separate terminal):
```bash
curl -s -X POST http://127.0.0.1:5012/api/contact \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Smoke Test",
    "email": "smoke-test@example.com",
    "company": "RegRadar Test",
    "industry": "Compliance",
    "markets": "UAE, Turkey",
    "message": "Smoke test only. Do not treat as real lead.",
    "watchlistContext": {
      "companyType": "Crypto / VASP firm",
      "markets": ["UAE", "Turkey"],
      "topics": ["AML/CFT", "Crypto/VASP"],
      "delivery": ["Telegram", "Weekly digest"]
    }
  }'
```

**Expected response (Telegram skipped by flag):**
```json
{"ok": true, "queued": true, "delivered": false, "message": "Request received and queued."}
```

**Step 3** — Verify queue:
```bash
.venv/bin/python run.py contact-queue --latest
.venv/bin/python run.py contact-queue --json
```

**Step 4** — Clean up:
```bash
rm data/contact_requests.jsonl
```

**Step 5** — Stop API (`Ctrl-C`).

---

## Local test with Telegram (sends real message)

If `.env` has real credentials and you accept that a real message will be sent:

```bash
# Use an obvious marker so the message is visibly a test
curl -s -X POST http://127.0.0.1:5001/api/contact \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SMOKE TEST — ignore",
    "email": "smoke-test@example.com",
    "company": "RegRadar Internal Test",
    "message": "SMOKE TEST ONLY. This is a system verification message."
  }'
```

Expected response (Telegram configured):
```json
{"ok": true, "queued": true, "delivered": true}
```

After verifying, delete the test entry from the queue file:
```bash
# View and manually edit data/contact_requests.jsonl to remove the test line,
# or delete the file entirely if it only contains test entries.
```

---

## Actual API response shape

The actual response fields returned by `/api/contact`:

| Field | Type | Meaning |
|-------|------|---------|
| `ok` | bool | `true` if at least one of queue/delivery succeeded |
| `queued` | bool | `true` if written to `data/contact_requests.jsonl` |
| `delivered` | bool | `true` if Telegram delivery confirmed |
| `message` | string | Optional human-readable status, used for queue-only smoke tests and errors |

The frontend (`Contact.jsx`) only inspects `ok`. It shows the success state when `ok: true` and the fallback error link (`@regradar_founder`) when `ok: false`.

Note: `delivered: false` with `ok: true` means the request is safely queued but Telegram failed. The user sees a success message. Operator recovery: `run.py contact-queue`.

---

## Production smoke test

No production deployment configuration exists in the repository yet. When deployed:

### Preconditions for production
- [ ] Frontend (`web/dist/`) and Python API must be served from **the same origin** (same domain/port).  
  The frontend uses a relative URL `/api/contact` with no base URL prefix.  
  The Vite dev-proxy (`vite.config.js` → `'/api'` → `http://127.0.0.1:5001`) is **dev-only** and does not apply to built assets.
- [ ] API must bind to `0.0.0.0` (not `127.0.0.1`) or be behind a reverse proxy serving the same domain.
- [ ] `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` set in production environment variables (not just `.env`).
- [ ] `data/` directory on a **persistent volume** — not an ephemeral container filesystem.

### Production checklist
1. [ ] Deploy backend: `python run.py api` (or process manager equivalent).
2. [ ] Confirm `/api/health` returns `{"status": "ok"}` from the public URL.
3. [ ] Confirm frontend loads and the contact form renders.
4. [ ] Submit one fake request from the live form with visibly fake data.
5. [ ] Confirm Telegram message arrives in admin chat.
6. [ ] SSH to server and run `python run.py contact-queue --latest` to confirm queue entry.
7. [ ] Confirm `ok: true` shown to user in browser (success state, not error).
8. [ ] Delete the smoke test entry from `data/contact_requests.jsonl`.

---

## How to verify Telegram delivery

Check admin Telegram chat for a message containing:
```
New RegRadar demo request
Name: <value>
Email: <value>
```

If the message arrives: `delivered: true` confirmed.  
If no message: check `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in the production environment. Then inspect the queue: `python run.py contact-queue --latest`.

---

## How to recover queued requests after Telegram outage

```bash
# Inspect what was queued
python run.py contact-queue
python run.py contact-queue --json | jq '.[] | {ts: .received_at, name: .body.name, email: .body.email}'
```

Contact each lead manually using the printed details, or import the JSON into your CRM/email workflow.

Do **not** re-POST queue entries to `/api/contact` for recovery — this creates duplicate queue entries and re-sends Telegram messages for entries that were already delivered.

---

## Persistent storage warning

`data/contact_requests.jsonl` is written to the local filesystem of the process.

**Ephemeral deployment platforms** (Heroku free dynos, Vercel serverless, Railway ephemeral volumes) will **lose this file on redeploy or restart.**

Before sending real traffic, confirm one of:
- Persistent volume mounted at the `data/` path, OR
- A durable delivery channel (database, external webhook, email) is added before the queue.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `{"error": "not found", ...}` | Frontend hitting wrong path or API not running | Start API; confirm same-origin serving |
| `ok: false` in response | Both queue write and Telegram failed | Check `data/` write permissions; check Telegram creds |
| `queued: true, delivered: false` | Contact delivery disabled, or Telegram credentials missing/wrong | If using `REGRADAR_CONTACT_DELIVERY_DISABLED=1`, this is expected. Otherwise set `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`; verify with `python run.py telegram-test` |
| `ok: true` but no Telegram message | `.env` credentials configured but wrong chat/token | Run `python run.py telegram-test` to debug independently |
| Queue file keeps disappearing | Ephemeral filesystem | Move to persistent volume |
| User sees error despite `ok: true` | CORS issue (browser blocked) | Confirm same-origin; or configure CORS for production domain in `app/api.py` |
