"""
RegRadar Telegram onboarding module.

Handles bot commands from clients who want to connect their Telegram
chat, group, or channel to RegRadar alerts.

Supported commands
------------------
/start    — full pairing instructions
/start CODE — consume a dashboard pairing code
/id       — show chat_id (quick copy)
/connect  — pairing help
/connect CODE — consume a dashboard pairing code

Also handles unknown messages with a help reply.

Security contract
-----------------
- Never prints or logs the bot token.
- Only sends replies to the chat that sent the command.
- Writes only account pairing data when a valid pairing code is provided.
- Never triggers monitoring pipeline.
"""

from __future__ import annotations

import logging
import os
import time

import requests

from app.telegram_pairing import consume_pairing_code, ensure_telegram_pairing_tables

logger = logging.getLogger(__name__)

_ADMIN_CHAT_IDS: frozenset[str] = frozenset(
    filter(None, os.environ.get("TELEGRAM_ADMIN_CHAT_IDS", "").split(","))
)

_TIMEOUT_S = 10
_POLL_TIMEOUT_S = 30   # long-poll window for getUpdates


def _build_start(chat_id: int | str) -> str:
    return (
        "Welcome to StatuteProof Alerts.\n\n"
        "This bot connects Telegram to your StatuteProof account.\n\n"
        f"Your Telegram Chat ID:\n`{chat_id}`\n\n"
        "To connect this chat:\n"
        "1. Open StatuteProof → Integrations.\n"
        "2. Generate a pairing code.\n"
        "3. Send `/start CODE` here.\n\n"
        "Need help?\n"
        "Contact us via the website contact form.\n\n"
        "For channels:\n"
        "1. Add this bot as an admin.\n"
        "2. Allow posting messages.\n"
        "3. Send the pairing command from the channel or connected chat."
    )


def _build_id(chat_id: int | str) -> str:
    return (
        f"Your Telegram Chat ID:\n`{chat_id}`\n\n"
        "Manual Chat ID entry is no longer required for account pairing.\n"
        "Generate a code in StatuteProof → Integrations and send `/start CODE` here.\n\n"
        "Need help? Contact us via the website contact form."
    )


def _build_connect(chat_id: int | str) -> str:
    return (
        f"Your Telegram Chat ID:\n`{chat_id}`\n\n"
        "Generate a pairing code in StatuteProof → Integrations and send `/start CODE` here.\n\n"
        "Need help? Contact us via the website contact form."
    )


def _build_unknown() -> str:
    return (
        "StatuteProof Alerts bot is ready.\n\n"
        "Commands:\n"
        "/start — pairing instructions and your Chat ID\n"
        "/start CODE — connect this chat to your account\n"
        "/id — show your Chat ID\n"
        "/connect — connection steps\n"
        "/connect CODE — connect this chat to your account\n\n"
        "Need help? Contact us via the website contact form."
    )


def _build_pairing_result(result: str) -> str:
    if result == "ok":
        return (
            "✅ Telegram connected to your StatuteProof account.\n\n"
            "You can return to StatuteProof → Integrations and click Refresh.\n"
            "This chat can now receive test messages."
        )
    if result == "expired":
        return "⏱ This pairing code has expired. Generate a new code in StatuteProof → Integrations."
    return "⚠️ Invalid pairing code. Generate a new code in StatuteProof → Integrations."


def _parse_command(text: str) -> tuple[str, str]:
    parts = text.strip().split(maxsplit=1)
    command = parts[0].split("@")[0].lower() if parts else ""
    argument = parts[1].strip() if len(parts) > 1 else ""
    return command, argument


def send_reply(chat_id: int | str, text: str, bot_token: str) -> bool:
    """Send a Markdown reply to chat_id. Returns True on success."""
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id":    str(chat_id),
                "text":       text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=_TIMEOUT_S,
        )
        data = resp.json()
        if data.get("ok"):
            logger.info("Onboarding reply sent to chat_id=%s", chat_id)
            return True
        logger.warning("Telegram API error sending reply: %s", data.get("description"))
        return False
    except Exception as exc:
        logger.warning("Failed to send reply to %s: %s", chat_id, exc)
        return False


def handle_update(update: dict, bot_token: str) -> None:
    """
    Process one Telegram update dict.  Replies to /start, /id, /connect.
    Unknown text gets a help reply.  Non-text updates are silently ignored.
    """
    message = update.get("message") or update.get("channel_post")
    if not message:
        return

    chat    = message.get("chat", {})
    chat_id = chat.get("id")
    text    = (message.get("text") or "").strip()
    if not chat_id or not text:
        return

    cmd, argument = _parse_command(text)

    if cmd in {"/start", "/connect"} and argument:
        ensure_telegram_pairing_tables()
        sender = message.get("from") or {}
        from_user = {
            "username": sender.get("username") or chat.get("username") or chat.get("title") or "",
            "first_name": sender.get("first_name") or chat.get("first_name") or "",
        }
        reply = _build_pairing_result(
            consume_pairing_code(argument, str(chat_id), from_user),
        )
    elif cmd == "/start":
        reply = _build_start(chat_id)
    elif cmd == "/id":
        if _ADMIN_CHAT_IDS and str(chat_id) not in _ADMIN_CHAT_IDS:
            send_reply(chat_id, "Unauthorized.", bot_token)
            return
        reply = _build_id(chat_id)
    elif cmd == "/connect":
        reply = _build_connect(chat_id)
    else:
        reply = _build_unknown()

    send_reply(chat_id, reply, bot_token)

    chat_type = chat.get("type", "unknown")
    username  = chat.get("username") or chat.get("title") or ""
    logger.info(
        "Handled %s from chat_id=%s type=%s user=%s",
        cmd, chat_id, chat_type, username,
    )


def fetch_updates(bot_token: str, offset: int = 0, timeout: int = 0) -> list[dict]:
    """
    Call getUpdates once.  Returns list of update dicts.  Never raises.
    """
    try:
        params: dict = {"timeout": timeout}
        if offset:
            params["offset"] = offset
        resp = requests.get(
            f"https://api.telegram.org/bot{bot_token}/getUpdates",
            params=params,
            timeout=timeout + _TIMEOUT_S,
        )
        data = resp.json()
        if data.get("ok"):
            return data.get("result", [])
        logger.warning("getUpdates error: %s", data.get("description"))
        return []
    except Exception as exc:
        logger.warning("fetch_updates failed: %s", exc)
        return []


def run_listen_loop(bot_token: str, bot_username: str = "") -> None:
    """
    Long-poll Telegram for bot commands.  Runs until Ctrl-C.
    Replies to /start, /id, /connect and consumes pairing codes. Never sends monitoring alerts.
    """
    ensure_telegram_pairing_tables()
    label = f"@{bot_username}" if bot_username else "bot"
    print(f"\nStatuteProof Telegram listener started.")
    print(f"Bot: {label}")
    print("Waiting for /start, /id, /connect … (Ctrl-C to stop)\n")

    offset = 0
    try:
        while True:
            updates = fetch_updates(bot_token, offset=offset, timeout=_POLL_TIMEOUT_S)
            for upd in updates:
                upd_id = upd.get("update_id", 0)
                if upd_id >= offset:
                    offset = upd_id + 1

                message = upd.get("message") or upd.get("channel_post")
                if message:
                    chat    = message.get("chat", {})
                    chat_id = chat.get("id", "?")
                    chat_type = chat.get("type", "?")
                    text    = (message.get("text") or "").strip()
                    uname   = chat.get("username") or chat.get("title") or ""
                    uname_str = f" (@{uname})" if uname else ""
                    print(f"  Received {text!r} from chat {chat_id} {chat_type}{uname_str}")
                    handle_update(upd, bot_token)
                    print(f"  → Replied.")

    except KeyboardInterrupt:
        print("\nListener stopped.")
