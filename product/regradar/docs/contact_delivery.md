# Contact Delivery — Operations Guide

## How it works

Every contact form submission is processed in two steps:

1. **Queue first** — written to `data/contact_requests.jsonl` before any network call.
2. **Telegram delivery** — forwarded to the admin chat via `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`.

For local smoke tests, start the API with `REGRADAR_CONTACT_DELIVERY_DISABLED=1`.
That flag affects only `/api/contact`: requests are queued, Telegram delivery is skipped, and other Telegram commands are unchanged.

API response shape:

| Scenario | `ok` | `queued` | `delivered` |
|----------|------|----------|-------------|
| Queued + delivered | `true` | `true` | `true` |
| Queued, Telegram failed | `true` | `true` | `false` |
| Queued, contact delivery disabled | `true` | `true` | `false` |
| Queue failed, Telegram delivered | `true` | `false` | `true` |
| Both failed | `false` | `false` | — |

The frontend shows success as long as `ok: true`. Operators should inspect the queue if Telegram delivery is suspected to be down.

---

## Inspecting the queue

```bash
# List last 20 requests (default)
.venv/bin/python run.py contact-queue

# List last N requests
.venv/bin/python run.py contact-queue --limit 5

# Show the most recent request in full
.venv/bin/python run.py contact-queue --latest

# Dump all entries as a JSON array (pipe to jq, import to CRM, etc.)
.venv/bin/python run.py contact-queue --json
.venv/bin/python run.py contact-queue --json | jq '.[].body.email'
```

---

## Recovery after Telegram outage

If Telegram was down and submissions were queued but not delivered, recover them from the queue:

```bash
# Review what was queued
.venv/bin/python run.py contact-queue --json | jq '.[] | {ts: .received_at, name: .body.name, email: .body.email}'
```

Forward each lead manually using the printed details, or import the JSON into your CRM/email workflow.
Do **not** re-post queue entries to `/api/contact` for recovery: that creates duplicate queue entries and may send Telegram messages again.

---

## Production checklist

- [ ] `data/` directory has write access for the API process.
- [ ] `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set in the production environment.
- [ ] `data/contact_requests.jsonl` is on a persistent volume (not in-memory / ephemeral).
- [ ] Backup or log-shipping covers `data/contact_requests.jsonl` in case the instance is replaced.
- [ ] Decide the durable delivery target beyond the local queue: email, database, CRM, or webhook.
- [ ] `.gitignore` already excludes `data/contact_requests.jsonl` — confirm it is not tracked:
  ```bash
  git ls-files data/contact_requests.jsonl  # should return nothing
  ```

---

## File location

`data/contact_requests.jsonl` — one JSON object per line, each with:

```json
{"received_at": "2026-05-26T10:00:00+00:00", "body": {<form fields>}}
```

The file is appended atomically per request. It is never truncated by the API.
To archive completed leads, copy the file out and delete it; the API will create a fresh one on the next submission.
