"""
Founder self-monitoring — deadman alerts.

The monitoring loop is the product: if it wedges or fails wholesale and nobody
notices, customers silently stop getting alerts while StatuteProof reports keep
promising coverage. `Restart=on-failure` catches a crash, but NOT a loop that
is alive yet doing nothing (network partition, every source returning 403, a
scraper hang). This module is the out-of-band signal for that case.

notify_founder() posts a best-effort Telegram message to the ADMIN bot
(TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID) — the same founder-only channel used by
the contact form and registration notifier in app/api.py. It mirrors those
notifiers exactly:

  • best-effort — NEVER raises; returns False on any failure
  • quiet no-op when the admin bot is not configured
  • respects a disable env (STATUTEPROOF_OPS_ALERTS_DISABLED) so smoke tests
    and dry-run environments do not emit real Telegram traffic
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

import requests as _req

from app.config import (
    BASE_DIR,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    WATCH_INTERVAL_MINUTES,
)

logger = logging.getLogger(__name__)

# Heartbeat file written by scheduler.write_heartbeat() at the end of each full
# cycle. Resolved via config.BASE_DIR (same as app/scheduler.py:_HEARTBEAT_FILE)
# so writer and watchdog reader always point at the same file.
_HEARTBEAT_FILE = Path(BASE_DIR) / "data" / "monitor_heartbeat"

# A wedged loop is one that has not completed a full cycle in 2× the configured
# interval. One missed cycle can be a slow run; two is a stall worth paging on.
_HEARTBEAT_STALE_MULTIPLIER = 2

# Matches api.py's _TELEGRAM_TIMEOUT_S — a wedged Telegram must not wedge us too.
_TELEGRAM_TIMEOUT_S = 10

# Disable switch for smoke tests / dry-run environments. Mirrors
# CONTACT_DELIVERY_DISABLED semantics (accepts the usual truthy spellings).
_DISABLED_TRUTHY = {"1", "true", "yes", "on"}


def _ops_alerts_disabled() -> bool:
    """True when ops deadman alerts are explicitly disabled via env.

    Read at call time (not import time) so tests and one-off runs can toggle
    the switch with monkeypatch/os.environ without re-importing the module.
    """
    return (
        os.getenv("STATUTEPROOF_OPS_ALERTS_DISABLED", "false").strip().lower()
        in _DISABLED_TRUTHY
    )


def notify_founder(text: str) -> bool:
    """Best-effort founder Telegram alert via the admin bot.

    Parameters
    ----------
    text : str
        Plain-text message body. Sent as-is (no HTML/Markdown parse mode) so a
        stray character in a source name or error string can never break
        delivery.

    Returns
    -------
    bool
        True only when Telegram accepted the message (API ``ok: true``).
        False on any other outcome: disabled, unconfigured, network error,
        timeout, or an API not-ok response. NEVER raises.
    """
    if _ops_alerts_disabled():
        logger.info("ops_alert: disabled via env — not sending (%.60s)", text)
        return False

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning(
            "ops_alert: admin bot not configured "
            "(TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID) — cannot send founder alert"
        )
        return False

    try:
        resp = _req.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "disable_web_page_preview": True,
            },
            timeout=_TELEGRAM_TIMEOUT_S,
        )
        if resp.json().get("ok"):
            logger.info("ops_alert: founder alert delivered")
            return True
        logger.warning("ops_alert: Telegram API returned not-ok")
        return False
    except Exception as exc:  # noqa: BLE001 — deliberately swallow everything
        logger.warning("ops_alert: founder alert failed: %s", type(exc).__name__)
        return False


def _heartbeat_stale_seconds() -> int:
    """Max heartbeat age (seconds) before the loop is considered wedged."""
    interval_min = max(1, int(WATCH_INTERVAL_MINUTES or 60))
    return interval_min * 60 * _HEARTBEAT_STALE_MULTIPLIER


def check_heartbeat(now: float | None = None) -> bool:
    """
    Watchdog: alert the founder if the monitor heartbeat is missing or stale.

    A healthy watch loop touches ``data/monitor_heartbeat`` at the end of every
    full cycle. If that file is absent, or older than 2× the configured
    interval, the loop is wedged (alive but not progressing) — a state
    ``Restart=on-failure`` cannot catch because the process never crashed.

    Parameters
    ----------
    now : float | None
        Override the reference wall-clock time (seconds since epoch) for tests.
        Defaults to ``time.time()``.

    Returns
    -------
    bool
        True when a stale/missing heartbeat was detected (an alert was
        attempted). False when the heartbeat is fresh. Never raises.
    """
    ref = time.time() if now is None else now
    stale_after = _heartbeat_stale_seconds()

    try:
        if not _HEARTBEAT_FILE.exists():
            logger.error("heartbeat: file missing at %s — monitor may be down", _HEARTBEAT_FILE)
            notify_founder(
                "🚨 StatuteProof monitor heartbeat MISSING\n"
                f"No heartbeat file at {_HEARTBEAT_FILE.name}. The watch loop "
                "has not completed a cycle since it (re)started, or never "
                "started. Check the scheduler service now."
            )
            return True

        age = ref - _HEARTBEAT_FILE.stat().st_mtime
        if age > stale_after:
            age_min = int(age // 60)
            stale_min = int(stale_after // 60)
            logger.error(
                "heartbeat: stale — %ds old (> %ds threshold); monitor wedged",
                int(age), stale_after,
            )
            notify_founder(
                "🚨 StatuteProof monitor heartbeat STALE\n"
                f"Last full cycle was ~{age_min} min ago "
                f"(threshold {stale_min} min). The watch loop appears wedged — "
                "alive but not progressing, so auto-restart will not fire. "
                "Check the scheduler service now."
            )
            return True

        logger.info("heartbeat: fresh (%ds old, threshold %ds)", int(age), stale_after)
        return False
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("heartbeat: check failed: %s", type(exc).__name__)
        return False
