"""
RegRadar Telegram settings store (MVP).

Stores non-secret configuration in telegram_settings.json (enabled flag, chat_id).
The bot token is NEVER written to the JSON file — it must be set via the
TELEGRAM_ALERTS_BOT_TOKEN environment variable, with TELEGRAM_BOT_TOKEN kept as
legacy single-bot fallback.

Security contract
-----------------
- get_token() reads TELEGRAM_ALERTS_BOT_TOKEN first, then TELEGRAM_BOT_TOKEN.
- load() returns a public-safe dict that never contains the token.
- The token is never written to logs or disk by this module.
"""

import json
import logging
import os
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
        TELEGRAM_CHAT_ID,
    )
    return {
        "enabled": ENABLE_TELEGRAM_ALERTS,
        "chat_id": TELEGRAM_CHAT_ID,
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

    bot_token = get_token()
    chat_id   = (raw.get("chat_id") or "").strip() or env["chat_id"]
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
    Return the customer-facing alerts bot token for server-side use only.

    Prefers TELEGRAM_ALERTS_BOT_TOKEN (customer/public bot).
    Falls back to TELEGRAM_BOT_TOKEN (legacy / single-bot mode).
    Never pass this value to an API response.
    """
    return (
        os.environ.get("TELEGRAM_ALERTS_BOT_TOKEN", "").strip()
        or os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    )


def save(*, enabled: bool, chat_id: str, bot_token: str | None = None) -> None:
    """
    Persist non-secret settings to telegram_settings.json (enabled flag and chat_id only).

    The bot_token parameter is accepted for API compatibility but is intentionally
    ignored — the token must be set via TELEGRAM_ALERTS_BOT_TOKEN or legacy
    TELEGRAM_BOT_TOKEN environment variables and is never written to disk.
    """
    raw = _load_raw()
    raw["enabled"] = bool(enabled)
    raw["chat_id"] = str(chat_id).strip()
    # Explicitly remove any previously stored token from disk (migration safety).
    raw.pop("bot_token", None)
    _SETTINGS_FILE.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Telegram settings saved (enabled=%s, chat_id_set=%s)", enabled, bool(chat_id))
