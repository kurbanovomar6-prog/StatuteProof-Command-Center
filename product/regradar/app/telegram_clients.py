"""Pre-auth legacy helper.

Auth C uses user_profiles + telegram_pairing_codes for account pairing.
Do not add new product features here unless migrating legacy admin tooling.

StatuteProof Telegram client storage — MVP.

Stores per-client Telegram configuration in data/telegram_clients.json
(gitignored).  Falls back to .env TELEGRAM_CHAT_ID for admin/testing.

Security contract
-----------------
- Never stores the bot token in this file.
- Bot token is always read from telegram_settings.get_token() / .env.
- Client data file is gitignored and must not be committed.
- Never raises in any public function.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

_DATA_DIR    = Path(__file__).parent.parent / "data"
_CLIENTS_FILE = _DATA_DIR / "telegram_clients.json"
_TIMEOUT_S   = 10


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_telegram_clients() -> dict:
    """Return the full clients store dict.  Never raises."""
    try:
        return json.loads(_CLIENTS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"clients": []}
    except Exception as exc:
        logger.warning("Could not read telegram_clients.json: %s", exc)
        return {"clients": []}


def save_telegram_clients(data: dict) -> None:
    """Persist the clients store dict.  Never raises."""
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        _CLIENTS_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.warning("Could not write telegram_clients.json: %s", exc)


def upsert_telegram_client(
    client_id: str,
    chat_id:   str,
    name:      str = "",
    enabled:   bool = True,
    language:  str = "en",
) -> dict:
    """
    Add or update a client record.  Returns the upserted record.

    Parameters
    ----------
    client_id : str   Short slug, e.g. "acme" or "demo"
    chat_id   : str   Telegram chat / channel ID
    name      : str   Human-readable workspace name
    enabled   : bool  Whether alerts are active for this client
    language  : str   Alert language code (default "en")
    """
    data    = load_telegram_clients()
    clients = data.get("clients", [])

    existing = next((c for c in clients if c.get("client_id") == client_id), None)

    if existing:
        existing["telegram_chat_id"] = str(chat_id).strip()
        existing["telegram_enabled"] = enabled
        existing["alert_language"]   = language
        existing["updated_at"]       = _now()
        if name:
            existing["name"] = name
        record = existing
    else:
        record = {
            "client_id":         client_id,
            "name":              name or client_id,
            "telegram_chat_id":  str(chat_id).strip(),
            "telegram_enabled":  enabled,
            "alert_language":    language,
            "created_at":        _now(),
            "updated_at":        _now(),
        }
        clients.append(record)

    data["clients"] = clients
    save_telegram_clients(data)
    return record


def get_telegram_client(client_id: str) -> dict | None:
    """Return one client record by client_id, or None."""
    data = load_telegram_clients()
    return next(
        (c for c in data.get("clients", []) if c.get("client_id") == client_id),
        None,
    )


def list_telegram_clients() -> list[dict]:
    """Return all client records."""
    return load_telegram_clients().get("clients", [])


def disable_telegram_client(client_id: str) -> bool:
    """Disable alerts for client_id. Returns True if found."""
    data    = load_telegram_clients()
    clients = data.get("clients", [])
    record  = next((c for c in clients if c.get("client_id") == client_id), None)
    if not record:
        return False
    record["telegram_enabled"] = False
    record["updated_at"]       = _now()
    data["clients"] = clients
    save_telegram_clients(data)
    return True


def send_client_test_alert(client_id: str) -> bool:
    """
    Send a clearly-labelled test alert to client_id's chat.

    Uses the shared bot token from telegram_settings / .env.
    Returns True if delivered, False on any failure.
    """
    from app.telegram_settings import get_token

    client = get_telegram_client(client_id)
    if not client:
        logger.warning("send_client_test_alert: client_id=%r not found", client_id)
        return False

    if not client.get("telegram_enabled", True):
        logger.info("send_client_test_alert: client_id=%r is disabled", client_id)
        return False

    chat_id   = client.get("telegram_chat_id", "")
    workspace = client.get("name", client_id)
    token     = get_token()

    if not token or not chat_id:
        logger.warning(
            "send_client_test_alert: missing token or chat_id for client_id=%r",
            client_id,
        )
        return False

    text = (
        "✅ StatuteProof connected.\n\n"
        f"*Workspace:* {workspace}\n"
        "This Telegram chat is now ready to receive StatuteProof alerts.\n\n"
        "Need help?\n"
        "Contact us via the website contact form."
    )

    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id":    chat_id,
                "text":       text,
                "parse_mode": "Markdown",
            },
            timeout=_TIMEOUT_S,
        )
        data = resp.json()
        if data.get("ok"):
            logger.info("Client test alert sent — client_id=%s chat_id=%s", client_id, chat_id)
            return True
        logger.warning(
            "Client test alert failed — client_id=%s: %s",
            client_id, data.get("description"),
        )
        return False
    except Exception as exc:
        logger.warning(
            "Client test alert error — client_id=%s: %s: %s",
            client_id, type(exc).__name__, exc,
        )
        return False
