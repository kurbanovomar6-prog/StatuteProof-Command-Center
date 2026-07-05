"""
Alert deduplication (defect A1, alert-quality sprint 2026-07-05).

Policy (owner decision):
- One alert per unique normalized_hash transition per source. A hash that has
  already been alerted for a source never re-alerts — this covers oscillating
  sources (the DFSA title A→B→A case that produced two HIGH alerts in 34 min).
- A configurable cooldown (ALERT_COOLDOWN_HOURS, default 24) applies between
  alerts for the same source even when the new hash was never alerted.

State lives in the evidence trail itself: run records carry
``alert_sent: true`` when a Telegram alert was actually delivered for that
run. No side-channel state files.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

from app.source_runs import _read_runs

logger = logging.getLogger(__name__)

_DEFAULT_COOLDOWN_HOURS = 24.0


def _cooldown_hours() -> float:
    raw = os.getenv("ALERT_COOLDOWN_HOURS")
    if not raw:
        return _DEFAULT_COOLDOWN_HOURS
    try:
        value = float(raw)
    except ValueError:
        logger.warning("ALERT_COOLDOWN_HOURS=%r is not a number — using default %s",
                       raw, _DEFAULT_COOLDOWN_HOURS)
        return _DEFAULT_COOLDOWN_HOURS
    return value if value >= 0 else _DEFAULT_COOLDOWN_HOURS


def _parse_ts(value) -> datetime | None:
    if not value:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def should_send_alert(
    source_id: str,
    new_hash: str,
    *,
    cooldown_hours: float | None = None,
    now: datetime | None = None,
) -> tuple[bool, str]:
    """
    Decide whether an alert for (source_id, new_hash) may be sent.

    Returns (True, "") when allowed, or (False, reason) with reason one of:
    "hash_already_alerted" | "cooldown_active".
    """
    now = now or datetime.now(timezone.utc)
    cooldown = timedelta(hours=cooldown_hours if cooldown_hours is not None else _cooldown_hours())

    last_alert_ts: datetime | None = None
    for record in _read_runs():
        if record.get("source_id") != source_id:
            continue
        if not record.get("alert_sent"):
            continue
        if new_hash and record.get("normalized_hash") == new_hash:
            return False, "hash_already_alerted"
        ts = _parse_ts(record.get("timestamp_utc"))
        if ts and (last_alert_ts is None or ts > last_alert_ts):
            last_alert_ts = ts

    if last_alert_ts is not None and cooldown > timedelta(0) and (now - last_alert_ts) < cooldown:
        return False, "cooldown_active"
    return True, ""
