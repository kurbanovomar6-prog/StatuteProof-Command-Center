"""
Telegram alert dispatcher — v5.

Sends a formatted alert to a Telegram chat/channel when a MEDIUM or HIGH
risk regulatory change is detected.

Fallback contract:
  - Returns False on any failure (missing credentials, network error, API error).
  - Never raises.  Never blocks or crashes the pipeline.
  - Baseline (first-run) alerts are suppressed by the caller — this module
    does not enforce that rule; it just sends what it receives.

Message limits:
  - Telegram enforces a 4 096-character limit per message.
  - Summaries and actions are truncated before assembly to stay safe.
"""

import logging
import os

import requests

from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from app import telegram_settings as _ts

# ---------------------------------------------------------------------------
# Customer delivery helper
# ---------------------------------------------------------------------------

def _deliver_alert_to_subscribed_users(message: str) -> int:
    """
    Send a formatted alert message to every subscribed customer via the
    ALERTS bot (token = TELEGRAM_ALERTS_BOT_TOKEN).

    Returns the number of users successfully reached.
    Falls back to 0 without raising if anything goes wrong.
    """
    try:
        from app.telegram_pairing import get_all_linked_chat_ids
        chat_ids = get_all_linked_chat_ids()
    except Exception as exc:
        logger.debug("_deliver_alert_to_subscribed_users: could not fetch linked chat_ids: %s", exc)
        return 0

    if not chat_ids:
        return 0

    sent = 0
    for chat_id in chat_ids:
        try:
            if send_telegram_message(str(chat_id), message):
                sent += 1
        except Exception as exc:
            logger.warning("_deliver_alert_to_subscribed_users: failed for chat_id=%s: %s", chat_id, exc)
    return sent

logger = logging.getLogger(__name__)

_ALERT_THRESHOLD = {"MEDIUM", "HIGH"}
_TELEGRAM_TIMEOUT_S = 10
_MAX_SUMMARY_LEN    = 600
_MAX_ACTION_LEN     = 400
_MAX_REASON_LEN     = 200

_RISK_ICON = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}

_JURISDICTION_FLAG = {
    "RU": "🇷🇺",
    "KZ": "🇰🇿",
    "AZ": "🇦🇿",
    "BY": "🇧🇾",
    "UZ": "🇺🇿",
    "TR": "🇹🇷",
    "AE": "🇦🇪",
    "SA": "🇸🇦",
    "GE": "🇬🇪",
    "AM": "🇦🇲",
}

_URGENCY_LABEL = {
    "routine":   "Routine",
    "soon":      "Soon",
    "immediate": "Immediate ⚠️",
}

_MATERIALITY_LABEL = {
    "informational": "Informational",
    "important":     "Important",
    "critical":      "Critical 🔴",
}


def send_telegram_message(chat_id: str, text: str) -> bool:
    """Send a plain account-scoped Telegram message to the provided chat_id."""
    token = _ts.get_token()
    if not token or not str(chat_id).strip():
        logger.warning("Telegram message skipped — bot token or target chat_id missing")
        return False
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": str(chat_id).strip(),
                "text": str(text),
                "disable_web_page_preview": True,
            },
            timeout=_TELEGRAM_TIMEOUT_S,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("ok"):
            logger.info("Account Telegram test message sent")
            return True
        logger.warning("Telegram message API error: %s", data.get("description"))
        return False
    except requests.Timeout:
        logger.warning("Telegram message timed out after %ds", _TELEGRAM_TIMEOUT_S)
        return False
    except requests.HTTPError as exc:
        logger.warning("Telegram message HTTP error: %s", exc)
        return False
    except Exception as exc:
        logger.warning("Telegram message failed (%s: %s)", type(exc).__name__, exc)
        return False


def _safe(text: str, max_len: int) -> str:
    """
    Truncate text to `max_len` characters and strip characters that break
    Telegram Markdown v1 parsing (*bold*, _italic_, `code`).

    We strip formatting markers from dynamic content so the fixed structural
    markers in the message template always render correctly.
    """
    cleaned = (
        str(text)
        .replace("*", "")
        .replace("_", "")
        .replace("`", "")
        .replace("[", "")
        .replace("]", "")
    )
    if len(cleaned) > max_len:
        return cleaned[:max_len] + "…"
    return cleaned


def send_telegram_alert(result: dict) -> bool:
    """
    Send a Markdown-formatted alert for MEDIUM or HIGH risk results.

    Parameters
    ----------
    result : dict
        The structured result dict from ``pipeline.run_pipeline()``.

    Returns
    -------
    bool
        True if the message was delivered, False otherwise.
    """
    risk = result.get("risk_level", "LOW")

    if risk not in _ALERT_THRESHOLD:
        logger.debug("Telegram alert skipped — risk=%s below threshold", risk)
        return False

    from app.alert_content import build_alert_content, render_telegram

    url = result.get("url", "unknown")
    source_name = str(result.get("source_name") or "")
    message = render_telegram(build_alert_content(result))

    # Cycle 3: verification/e2e runs must never send real alerts. With
    # ALERT_DRY_RUN set, log the fully rendered message and report not-sent
    # so dedup state (alert_sent) is not poisoned by test traffic.
    if str(os.getenv("ALERT_DRY_RUN") or "").strip().lower() in {"1", "true", "yes"}:
        logger.info("ALERT_DRY_RUN — alert not sent. Rendered message:\n%s", message)
        return False


    # ── Step 1: deliver to subscribed customers via ALERTS bot ──────────────
    # Falls back to founder chat during pilot phase;
    # production routes through user_delivery / _deliver_alert_to_subscribed_users.
    users_reached = _deliver_alert_to_subscribed_users(message)
    if users_reached > 0:
        logger.info(
            "Telegram alert sent to %d subscribed user(s) via alerts bot — risk=%s url=%s",
            users_reached, risk, url,
        )
        return True

    # ── Step 2: no subscribed users yet — fall back to founder chat (admin bot) ──
    # This is acceptable during the pilot phase while no customers are linked.
    # Uses TELEGRAM_BOT_TOKEN (admin bot) + TELEGRAM_CHAT_ID (founder chat).
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning(
            "Telegram alert skipped — no subscribed users and "
            "TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID not set (pilot fallback unavailable)"
        )
        return False

    logger.debug(
        "No subscribed users found — sending alert to founder chat via admin bot (pilot fallback)"
    )

    tg_err: Exception | None = None
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id":                  TELEGRAM_CHAT_ID,
                "text":                     message,
                "parse_mode":               "Markdown",
                "disable_web_page_preview": True,
            },
            timeout=_TELEGRAM_TIMEOUT_S,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            tg_err = RuntimeError(f"Telegram returned not-ok: {data.get('description', data)}")
        else:
            logger.info(
                "Telegram alert sent to founder chat (pilot fallback) — risk=%s url=%s",
                risk, url,
            )
            return True
    except requests.Timeout as exc:
        logger.warning("Telegram alert timed out after %ds", _TELEGRAM_TIMEOUT_S)
        tg_err = exc
    except requests.HTTPError as exc:
        logger.warning("Telegram API error: %s", exc)
        tg_err = exc
    except Exception as exc:
        logger.warning("Telegram alert failed (%s: %s)", type(exc).__name__, exc)
        tg_err = exc

    if tg_err is not None:
        logger.warning(
            "Telegram alert failed for %s (risk=%s): %s — attempting email fallback",
            source_name or url, risk, tg_err,
        )
        if risk in _ALERT_THRESHOLD:
            try:
                from app.email_delivery import build_monitoring_brief_email, deliver_brief_email
                brief_text = result.get("executive_summary") or result.get("reason") or message
                email_payload = build_monitoring_brief_email(
                    brief_markdown=brief_text,
                    source_name=source_name or url,
                    risk_level=risk,
                )
                email_result = deliver_brief_email(
                    email_payload,
                    source_id=str(result.get("source_id") or result.get("source_name") or ""),
                )
                logger.info(
                    "Email fallback for %s (risk=%s): status=%s",
                    source_name or url, risk, email_result.get("status"),
                )
            except Exception as email_err:
                logger.error(
                    "Email fallback also failed for %s (risk=%s): %s",
                    source_name or url, risk, email_err,
                )

    return False
