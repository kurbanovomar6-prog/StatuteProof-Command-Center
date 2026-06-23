#!/bin/bash
# StatuteProof — Telegram bot listener
#
# This process handles customer pairing (/start CODE) and sends
# "account connected" confirmations. It does NOT send monitoring alerts
# (that goes through the main alert pipeline).
#
# Usage:
#   ./run_telegram_bot.sh           # foreground (Ctrl-C to stop)
#   ./run_telegram_bot.sh &         # background (note PID)
#
# The listener responds to:
#   /start          → pairing instructions + Chat ID
#   /start SP-XXXX  → link this chat to a StatuteProof account
#   /connect CODE   → same as /start CODE
#   /id             → show Chat ID
#
# TELEGRAM_BOT_TOKEN is loaded from .env by config.py (override=True).

set -e
cd "$(dirname "$0")"

echo "Starting @StatuteProof_bot listener..."
python3 run.py telegram-listen
