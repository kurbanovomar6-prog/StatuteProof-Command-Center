"""
RegRadar Telegram settings store (MVP).

Stores configuration in telegram_settings.json (gitignored).
Falls back to .env values so the CLI keeps working with the
existing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID variables.

Security contract
-----------------
- get_token() is for **internal server-side use only**.
- load() returns a public-safe dict that never contains the token.
- The token is never written to logs by this module.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_SETTINGS_FILE = Path(__file__).parent.parent / "telegram_settings.json"


def _load_raw() -> dict:
    try:
        return json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except Exception as exc:
        logger.warning("Could not read telegram_settings.json: %s", exc)
        return {}


def _env_defaults() -> dict:
    """Read .env fallbacks without importing config at module level."""
    from app.config import (
        ENABLE_TELEGRAM_ALERTS,
        TELEGRAM_BOT_TOKEN,
        TELEGRAM_CHAT_ID,
    )
    return {
        "enabled":   ENABLE_TELEGRAM_ALERTS,
        "chat_id":   TELEGRAM_CHAT_ID,
        "bot_token": TELEGRAM_BOT_TOKEN,
    }


def load() -> dict:
    """
    Return a public-safe settings dict (no bot_token).

    Shape:
      {
        "telegram_enabled":  bool,
        "chat_id":           str,
        "bot_token_present": bool,
        "status":            "configured" | "missing_credentials"
      }
    """
    raw = _load_raw()
    env = _env_defaults()

    bot_token = (raw.get("bot_token") or "").strip() or env["bot_token"]
    chat_id   = (raw.get("chat_id")   or "").strip() or env["chat_id"]
    # enabled: prefer JSON file value if it exists; fall back to .env
    if "enabled" in raw:
        enabled = bool(raw["enabled"])
    else:
        enabled = env["enabled"]

    status = "configured" if (bot_token and chat_id) else "missing_credentials"

    return {
        "telegram_enabled":  enabled,
        "chat_id":           chat_id,
        "bot_token_present": bool(bot_token),
        "status":            status,
    }


def get_token() -> str:
    """
    Return the bot token for **server-side use only**.
    Never pass this value to an API response.
    """
    raw = _load_raw()
    token = (raw.get("bot_token") or "").strip()
    if not token:
        from app.config import TELEGRAM_BOT_TOKEN
        token = TELEGRAM_BOT_TOKEN
    return token


def save(*, enabled: bool, chat_id: str, bot_token: str | None) -> None:
    """
    Persist settings to telegram_settings.json.

    If bot_token is None or empty the existing stored token is kept,
    allowing the frontend to save enabled/chat_id without re-submitting
    the token every time.
    """
    raw = _load_raw()
    raw["enabled"]  = bool(enabled)
    raw["chat_id"]  = str(chat_id).strip()
    if bot_token and str(bot_token).strip():
        raw["bot_token"] = str(bot_token).strip()
    _SETTINGS_FILE.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Telegram settings saved (bot_token_changed=%s)", bool(bot_token))
