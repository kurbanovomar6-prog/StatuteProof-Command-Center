# RegRadar — Telegram Alerts Setup

RegRadar delivers regulatory monitoring alerts via Telegram.
A single shared bot (`@regradar_alerts_bot`) serves all workspaces.
Clients only need a **Chat ID** — never the bot token.

---

## 1. Admin Setup (server operator)

The bot token is a one-time server-side configuration.

```bash
# 1. Create a bot with BotFather in Telegram
#    Send /newbot, follow prompts, copy the token.

# 2. Add to .env
TELEGRAM_BOT_TOKEN=<your_token>
TELEGRAM_CHAT_ID=<your_admin_chat_id>   # admin fallback
ENABLE_TELEGRAM_ALERTS=true

# 3. Verify
.venv/bin/python run.py env-check
.venv/bin/python run.py telegram-test
```

The token is stored in `.env` (gitignored). It is never sent to clients or logged.

---

## 2. Client — Private Chat Setup

The client opens the bot directly in Telegram.

1. Open Telegram and search for `@regradar_alerts_bot`.
2. Send `/start`. The bot replies with your Chat ID.
3. Send `/id` to see just the Chat ID.
4. Copy the Chat ID (e.g. `8208518608`).
5. Save in RegRadar:
   ```bash
   .venv/bin/python run.py telegram-client-set acme 8208518608 "Acme Corp"
   ```
6. Send a test alert:
   ```bash
   .venv/bin/python run.py telegram-client-test acme
   ```

---

## 3. Client — Group Setup

1. Add `@regradar_alerts_bot` to the group (search bot username).
2. In the group, send `/start` or `/id`. The bot replies with the group Chat ID.
3. The group Chat ID is a negative number, e.g. `-1001234567890`.
4. Save and test:
   ```bash
   .venv/bin/python run.py telegram-client-set acme-team -1001234567890 "Acme Team Group"
   .venv/bin/python run.py telegram-client-test acme-team
   ```

---

## 4. Client — Channel Setup

1. Open channel settings → Administrators → Add administrator.
2. Add `@regradar_alerts_bot` as admin.
3. Enable permission: **Post messages**.
4. For a **public channel**: use `@your_channel_username` as the Chat ID.
5. For a **private channel**: use the numeric `-100...` ID.
   - To find it: forward a message from the channel to `@getidsbot`.
6. Save and test:
   ```bash
   # public channel
   .venv/bin/python run.py telegram-client-set acme-ch @acmechannel "Acme Channel"

   # private channel
   .venv/bin/python run.py telegram-client-set acme-ch -1001987654321 "Acme Private Channel"
   .venv/bin/python run.py telegram-client-test acme-ch
   ```

---

## 5. Discovering Chat IDs (CLI)

If a client has already sent `/start` to the bot, fetch pending updates:

```bash
.venv/bin/python run.py telegram-updates
```

Output includes chat IDs, types, and usernames from recent bot interactions.

To respond to commands interactively (local testing):

```bash
.venv/bin/python run.py telegram-listen
# Ctrl-C to stop
```

---

## 6. Managing Clients

```bash
# List all clients
.venv/bin/python run.py telegram-clients

# Add / update
.venv/bin/python run.py telegram-client-set <id> <chat_id> [name]

# Send test alert
.venv/bin/python run.py telegram-client-test <id>

# Disable alerts
.venv/bin/python run.py telegram-client-disable <id>
```

Client data is stored in `data/telegram_clients.json` (gitignored).

---

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Bot token not configured` | `.env` not loaded or wrong Python | Use `.venv/bin/python run.py` |
| `getMe ❌` | Invalid bot token | Re-create bot with BotFather |
| Test message not received | Wrong Chat ID | Send `/id` to bot and re-copy |
| Test message not received | Bot not started | Open bot in Telegram, send `/start` |
| Channel: `Forbidden` | Bot not admin | Add bot as admin with post permission |
| Channel: message not posted | Missing post permission | Re-add bot with "Post messages" enabled |
| Old token in shell | Stale env variable | Check with `env-check`; use `.venv/bin/python` |
| System Python used | Wrong interpreter | Always use `.venv/bin/python run.py` |

---

## 8. Security Model

| Who | What they have access to |
|---|---|
| Server operator | Bot token (in `.env`, never logged or sent to clients) |
| Client / workspace | Chat ID only |
| Frontend UI | Chat ID only (bot token field is admin-only, marked clearly) |

- Bot token is stored in `.env` (gitignored).
- `data/telegram_clients.json` is gitignored and must not be committed.
- Clients never need the bot token.
- One bot can serve unlimited workspaces via per-client Chat IDs.

---

## 9. Alert Format

```
🚨 RegRadar Alert — 🔴 HIGH

Market: 🇦🇿 AZ
Source: Central Bank of Azerbaijan
Analysis: ✅ AI

Affected: Banks, payment providers, VASPs
Urgency: Immediate ⚠️
Deadline: 2026-09-01
Materiality: Critical 🔴

Summary:
New mandatory reserve requirement effective 1 September 2026...

Action required:
Update treasury models and notify the CFO before the deadline.

⚠️ Legal review required: Multiple concurrent obligations detected.

🔗 https://cbar.az/...
```
