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

def _alerts_require_plan() -> bool:
    """Plan gate on the official-source broadcast — default ON (audit 07-20).

    Thin alias over ``telegram_pairing.alerts_require_plan``, which is the one
    switch every delivery path reads (broadcast here, scheduled digests in
    app/digest_cadence.py, deadline reminders in app/deadline_radar.py). Kept
    under this name for existing callers. Lazy import: app.telegram is imported
    from many modules and must not pull the pairing DB layer at import time.
    """
    from app.telegram_pairing import alerts_require_plan

    return alerts_require_plan()


def _deliver_alert_to_subscribed_users(message: str, *, source_id: object = None) -> int:
    """
    Send a formatted alert message to subscribed customers via the ALERTS bot
    (token = TELEGRAM_ALERTS_BOT_TOKEN).

    TENANCY (critical): a change on a customer's PRIVATE custom source must be
    delivered ONLY to that source's owner — never broadcast to every paired
    account. When ``source_id`` is a custom source, delivery is restricted to
    the owner's alerts-enabled chat(s); a custom source with no resolvable owner
    delivers to NOBODY (fail closed) rather than broadcasting. Official / shared
    sources (and calls with no source_id, e.g. legacy) broadcast to all paired
    accounts as before.

    Returns the number of users successfully reached. Falls back to 0 without
    raising if anything goes wrong.
    """
    try:
        from app.telegram_pairing import (
            filter_plan_eligible_chat_ids,
            get_alert_chat_ids_for_user,
            get_all_linked_chat_ids,
        )
        from app.tenancy import custom_source_owner, is_custom_source

        if source_id is not None and is_custom_source(source_id):
            owner_id = custom_source_owner(source_id)
            if owner_id is None:
                # Custom source we cannot attribute → never broadcast a private
                # source's content. Deliver to nobody.
                logger.warning(
                    "telegram: custom source %s has no resolvable owner — alert not broadcast",
                    str(source_id),
                )
                return 0
            chat_ids = get_alert_chat_ids_for_user(owner_id)
        else:
            # Server-side plan gate on the paid core deliverable (audit 07-20):
            # the official-source broadcast reaches only founder-ACTIVATED paid
            # plans + operator emails in STATUTEPROOF_ALERT_PLAN_EXEMPT_EMAILS.
            # The custom-source owner branch above is deliberately NOT gated —
            # it delivers only the owner's own private-source content, and
            # custom sources are themselves plan-gated at creation. Chat ids
            # that do not resolve to a user_profiles row pass through the
            # filter (see filter_plan_eligible_chat_ids docstring).
            chat_ids = get_all_linked_chat_ids()
            if _alerts_require_plan():
                chat_ids = filter_plan_eligible_chat_ids(chat_ids)
    except Exception as exc:
        logger.debug("_deliver_alert_to_subscribed_users: could not resolve recipients: %s", exc)
        return 0

    if not chat_ids:
        return 0

    sent = 0
    for chat_id in chat_ids:
        try:
            # Render Markdown so customers see formatted alerts (bold severity,
            # etc.) — the same formatting the founder-fallback path already uses.
            if send_telegram_message(str(chat_id), message, parse_mode="Markdown"):
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


def send_telegram_message(chat_id: str, text: str, parse_mode: str | None = None) -> bool:
    """Send an account-scoped Telegram message to the provided chat_id.

    ``parse_mode`` (e.g. "Markdown") is applied when set so customers see the
    same formatted alert the founder-fallback path already renders — without it,
    the ``*bold*`` / ``_italic_`` markers show up as literal characters. If
    Telegram rejects the formatted message (HTTP 400 "can't parse entities"), the
    message is retried once as plain text so a formatting quirk never drops a
    customer alert (the auto path does not rebuild a lost alert).
    """
    token = _ts.get_token()
    if not token or not str(chat_id).strip():
        logger.warning("Telegram message skipped — bot token or target chat_id missing")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    base_payload = {
        "chat_id": str(chat_id).strip(),
        "text": str(text),
        "disable_web_page_preview": True,
    }
    # First attempt uses parse_mode (if any); on a markdown parse error fall back
    # to a plain-text attempt so the customer still receives the alert.
    modes = [parse_mode, None] if parse_mode else [None]
    last_desc: str | None = None
    for attempt, mode in enumerate(modes):
        payload = dict(base_payload)
        if mode:
            payload["parse_mode"] = mode
        try:
            resp = requests.post(url, json=payload, timeout=_TELEGRAM_TIMEOUT_S)
            data = resp.json() if resp.content else {}
            if resp.status_code == 200 and data.get("ok"):
                return True
            last_desc = data.get("description") if isinstance(data, dict) else None
            if mode and resp.status_code == 400 and attempt + 1 < len(modes):
                logger.warning(
                    "Telegram %s parse failed (%s) — retrying as plain text", mode, last_desc
                )
                continue
            logger.warning("Telegram message API error: %s", last_desc)
            return False
        except requests.Timeout:
            logger.warning("Telegram message timed out after %ds", _TELEGRAM_TIMEOUT_S)
            return False
        except Exception as exc:
            logger.warning("Telegram message failed (%s: %s)", type(exc).__name__, exc)
            return False
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


# CLAUDE.md customer-delivery rule: "No customer delivery without human review
# when risk >= 70 or confidence < 0.70." 70/100 maps to risk_level HIGH.
_HUMAN_REVIEW_CONFIDENCE_FLOOR = 0.70


def _requires_human_review(result: dict) -> str:
    """Return a non-empty reason when an AUTOMATED customer broadcast must be
    held for human review, or "" when it may auto-send.

    Gate (any one holds): HIGH risk, an explicit review_required flag, or a
    confidence below the floor — numeric < 0.70 or the string "low".
    """
    risk = str(result.get("risk_level") or "").strip().upper()
    if risk == "HIGH":
        return "risk_level HIGH (>= review threshold)"
    if result.get("review_required"):
        return "review_required flag set"

    conf = result.get("confidence")
    if isinstance(conf, bool):  # guard: bool is a subclass of int
        conf = None
    if isinstance(conf, (int, float)):
        if float(conf) < _HUMAN_REVIEW_CONFIDENCE_FLOOR:
            return f"confidence {conf} < {_HUMAN_REVIEW_CONFIDENCE_FLOOR}"
    else:
        conf_str = str(conf or "").strip().lower()
        if conf_str == "low":
            return "confidence 'low'"
        try:
            if conf_str and float(conf_str) < _HUMAN_REVIEW_CONFIDENCE_FLOOR:
                return f"confidence {conf_str} < {_HUMAN_REVIEW_CONFIDENCE_FLOOR}"
        except ValueError:
            pass
    return ""


def _hold_alert_for_review(result: dict, message: str, *, reason: str, detail: str = "") -> None:
    """Record a withheld automated alert so it is HELD (not dropped) for review.

    Never raises — a recording failure must not turn a safety hold into an
    unhandled exception on the monitoring path.
    """
    try:
        from app.review_queue import record_held_alert

        record_held_alert(
            reason,
            message=message,
            context={
                "source_id": result.get("source_id") or result.get("source_name") or "",
                "source_name": result.get("source_name") or "",
                "url": result.get("url") or "",
                "risk_level": result.get("risk_level") or "",
                "confidence": result.get("confidence"),
                "review_required": bool(result.get("review_required")),
                "normalized_hash": result.get("normalized_hash") or "",
                "detail": detail,
            },
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(
            "Failed to record held alert (reason=%s, detail=%s): %s", reason, detail, exc
        )


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

    # ── SF-1 legal-safety: final-bytes forbidden-claims guard (fail closed) ──
    # The authoritative check runs on the EXACT string a customer would receive.
    # build_alert_content already drops offending AI fields, so a hit here means
    # a banned phrase survived elsewhere (e.g. a source-derived excerpt, SF-6).
    # Never ship it: hold the alert for human review and report not-sent.
    from app.legal_safety import find_forbidden_claims

    _forbidden_hits = find_forbidden_claims(message)
    if _forbidden_hits:
        logger.error(
            "LEGAL-SAFETY BLOCK: Telegram alert WITHHELD — forbidden claim(s) %s "
            "in final rendered bytes for source=%s url=%s; routed to review, NOT sent",
            _forbidden_hits, source_name or "", url,
        )
        _hold_alert_for_review(
            result, message,
            reason="forbidden_claim_in_final_bytes",
            detail=", ".join(_forbidden_hits),
        )
        return False

    # Cycle 3: verification/e2e runs must never send real alerts. With
    # ALERT_DRY_RUN set, log the fully rendered message and report not-sent
    # so dedup state (alert_sent) is not poisoned by test traffic.
    if str(os.getenv("ALERT_DRY_RUN") or "").strip().lower() in {"1", "true", "yes"}:
        logger.info("ALERT_DRY_RUN — alert not sent. Rendered message:\n%s", message)
        return False

    # ── SF-2 human-review gate (CLAUDE.md): no automated customer delivery ───
    # when the run needs human review — risk >= HIGH, confidence < 0.70 / "low",
    # or review_required. Hold for the human-approved preview path
    # (alert_routing.send_preview_alert_to_user) instead of auto-broadcasting.
    # Do NOT silently drop: record the hold so an operator can act on it.
    _hold_reason = _requires_human_review(result)
    if _hold_reason:
        logger.warning(
            "LEGAL-SAFETY HOLD: automated Telegram alert WITHHELD for human review "
            "(%s) source=%s url=%s — routed to review, NOT auto-broadcast",
            _hold_reason, source_name or "", url,
        )
        _hold_alert_for_review(
            result, message,
            reason="requires_human_review",
            detail=_hold_reason,
        )
        return False

    # ── Step 1: deliver to subscribed customers via ALERTS bot ──────────────
    # Falls back to founder chat during pilot phase;
    # production routes through user_delivery / _deliver_alert_to_subscribed_users.
    # Pass source_id so a PRIVATE custom source's alert is delivered only to its
    # owner, never broadcast to every paired account (tenancy).
    users_reached = _deliver_alert_to_subscribed_users(
        message, source_id=result.get("source_id"),
    )
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
