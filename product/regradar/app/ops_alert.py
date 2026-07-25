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
from datetime import datetime
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

# External uptime probe timeout — the ping must never block the oneshot.
_PING_TIMEOUT_S = 10

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


def ping_external_heartbeat() -> bool:
    """Best-effort GET to an owner-created external uptime probe.

    The internal deadman watchdog lives on the very droplet it watches, so a
    dead droplet can never page anyone. The fix is an external heartbeat
    service (healthchecks.io / UptimeRobot heartbeat — the OWNER creates the
    account and URL; we only send the ping): it alerts when pings STOP
    arriving. That is why this is called only after a SUCCESSFUL internal
    heartbeat check and deliberately NOT on the stale/missing paths — silence
    at the external service is the alarm signal.

    Returns
    -------
    bool
        True only when the probe URL is configured and answered 2xx.
        False on any other outcome: disabled, unset URL, non-2xx status,
        network error, or timeout. NEVER raises.
    """
    # Same kill switch as notify_founder: STATUTEPROOF_OPS_ALERTS_DISABLED
    # silences ALL outbound ops traffic. Without this a staging box or restore
    # drill carrying a production .env would keep the external deadman green
    # through a real production outage.
    if _ops_alerts_disabled():
        logger.info("heartbeat: external ping suppressed via env")
        return False

    # Read at call time (not import time) so the systemd oneshot picks up a
    # newly set .env value without a code change, and tests can toggle it
    # with monkeypatch — same rationale as _ops_alerts_disabled.
    url = os.getenv("STATUTEPROOF_HEARTBEAT_PING_URL", "").strip()
    if not url:
        logger.debug("heartbeat: no external ping URL configured — skipping")
        return False

    try:
        resp = _req.get(url, timeout=_PING_TIMEOUT_S)
        if 200 <= resp.status_code < 300:
            logger.info("heartbeat: external ping delivered")
            return True
        # Log the outcome only — healthchecks-style ping URLs embed a secret
        # UUID, so the URL itself stays out of warning-level logs.
        logger.warning(
            "heartbeat: external ping rejected (HTTP %s)", resp.status_code
        )
        return False
    except Exception as exc:  # noqa: BLE001 — deliberately swallow everything
        logger.warning("heartbeat: external ping failed: %s", type(exc).__name__)
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
        # Fresh = healthy: tell the external probe we're alive. Stale/missing
        # paths deliberately do NOT ping — silence upstream is the page.
        ping_external_heartbeat()
        return False
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("heartbeat: check failed: %s", type(exc).__name__)
        return False


# ── sweep progress and a side-effect-free heartbeat read ─────────────────────
#
# check_heartbeat() answers "is it wedged?" by ALERTING — it notifies the founder
# and pings the external probe as a side effect. A watchdog that wants to look at
# the state on every tick, or a human running a status command, needs the same
# facts without paging anyone. These are those facts.
#
# The heartbeat alone cannot tell "working slowly" from "stopped": a sweep over
# 140 sources can legitimately outlive the stale threshold. The progress marker
# (written by app.scheduler.record_progress) is what distinguishes them — if the
# heartbeat is stale but progress moved a minute ago, the sweep is running.

_PROGRESS_FILE = Path(BASE_DIR) / "data" / "scheduler_progress.json"


def read_progress() -> dict | None:
    """The sweep's last progress marker, or None. Never raises."""
    try:
        if not _PROGRESS_FILE.exists():
            return None
        import json as _json

        loaded = _json.loads(_PROGRESS_FILE.read_text(encoding="utf-8"))
        return loaded if isinstance(loaded, dict) else None
    except Exception:  # noqa: BLE001 — an unreadable marker is "no marker"
        return None


def describe_progress() -> str:
    """One line a human or a shell script can read. Never raises."""
    progress = read_progress()
    if not progress:
        return "no progress marker"
    index = progress.get("index")
    total = progress.get("total")
    label = str(progress.get("label") or "?")
    at = str(progress.get("at") or "?")
    # The wrapper that records progress does not know the sweep length, and
    # printing "2/0" would be a wrong denominator rather than a missing one.
    position = f"{index}/{total}" if isinstance(total, int) and total > 0 else f"{index}"
    return f"source {position} ({label}) at {at}"


def heartbeat_state(now: float | None = None) -> dict:
    """The heartbeat and progress facts, with NO side effects.

    Deliberately does not notify and does not ping: it is safe to call on a timer,
    from a watchdog, or from a status command. check_heartbeat() remains the
    alerting path — mixing the two is how a status check starts paging someone.

    ``state`` is one of:
      fresh    — the last full cycle finished inside the stale window
      missing  — no heartbeat file: the loop has never completed a cycle
      stale    — older than the window AND progress has not moved recently
      working  — older than the window BUT the sweep is still advancing
    """
    ref = time.time() if now is None else now
    stale_after = _heartbeat_stale_seconds()
    progress = read_progress()

    try:
        exists = _HEARTBEAT_FILE.exists()
    except Exception:  # noqa: BLE001
        exists = False

    if not exists:
        return {
            "state": "missing", "ok": False, "age_seconds": None,
            "stale_after_seconds": stale_after, "progress": progress,
            "detail": f"no heartbeat file at {_HEARTBEAT_FILE.name}",
        }

    try:
        age = ref - _HEARTBEAT_FILE.stat().st_mtime
    except Exception:  # noqa: BLE001
        return {
            "state": "missing", "ok": False, "age_seconds": None,
            "stale_after_seconds": stale_after, "progress": progress,
            "detail": "heartbeat file could not be read",
        }

    if age <= stale_after:
        return {
            "state": "fresh", "ok": True, "age_seconds": int(age),
            "stale_after_seconds": stale_after, "progress": progress,
            "detail": f"last cycle {int(age)}s ago (threshold {stale_after}s)",
        }

    # Stale heartbeat, but a moving progress marker means a long sweep is still
    # advancing — restarting it there would abort real work for no reason.
    progress_age = None
    if progress:
        try:
            stamp = datetime.fromisoformat(str(progress.get("at")).replace("Z", "+00:00"))
            progress_age = ref - stamp.timestamp()
        except Exception:  # noqa: BLE001
            progress_age = None
    if progress_age is not None and progress_age <= stale_after:
        return {
            "state": "working", "ok": True, "age_seconds": int(age),
            "progress_age_seconds": int(progress_age),
            "stale_after_seconds": stale_after, "progress": progress,
            "detail": (
                f"heartbeat {int(age)}s old but the sweep advanced "
                f"{int(progress_age)}s ago — a long cycle, not a wedge"
            ),
        }

    return {
        "state": "stale", "ok": False, "age_seconds": int(age),
        "progress_age_seconds": None if progress_age is None else int(progress_age),
        "stale_after_seconds": stale_after, "progress": progress,
        "detail": (
            f"heartbeat {int(age)}s old (threshold {stale_after}s) and no recent "
            f"progress — {describe_progress()}"
        ),
    }


def check_heartbeat_detailed(now: float | None = None) -> dict:
    """check_heartbeat's verdict plus the facts behind it.

    Returns heartbeat_state() with ``paged`` recording whether an alert was
    actually attempted, so a caller can report "we noticed AND told someone" or
    "we noticed and could not tell anyone" rather than conflating them.
    """
    state = heartbeat_state(now=now)
    state["paged"] = bool(check_heartbeat(now=now)) if not state["ok"] else False
    return state
