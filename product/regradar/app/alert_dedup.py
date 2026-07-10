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
_DEFAULT_FLAPPING_MAX_CONSECUTIVE = 3


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


def _flapping_max_consecutive() -> int:
    raw = os.getenv("FLAPPING_MAX_CONSECUTIVE")
    if not raw:
        return _DEFAULT_FLAPPING_MAX_CONSECUTIVE
    try:
        value = int(raw)
    except ValueError:
        logger.warning("FLAPPING_MAX_CONSECUTIVE=%r is not an integer — using default %s",
                       raw, _DEFAULT_FLAPPING_MAX_CONSECUTIVE)
        return _DEFAULT_FLAPPING_MAX_CONSECUTIVE
    # A threshold < 2 would quarantine every single genuine change (a lone new
    # hash always "differs from the previous"), which defeats the product.
    # Clamp to the default so a misconfiguration never silences real alerts.
    if value < 2:
        logger.warning("FLAPPING_MAX_CONSECUTIVE=%s is < 2 — using default %s",
                       value, _DEFAULT_FLAPPING_MAX_CONSECUTIVE)
        return _DEFAULT_FLAPPING_MAX_CONSECUTIVE
    return value


def _is_flapping(source_id: str, new_hash: str, k: int) -> bool:
    """
    Detect a flapping source (defect C, 2026-07-11).

    A source is "flapping" when it produces CHANGED with a DISTINCT new
    normalized_hash on K consecutive recent runs — dynamic page chrome that
    re-hashes every sweep, not real regulatory change. The existing
    hash-dedup gate does not help because each flip carries a brand-new hash.

    Counts the streak of consecutive most-recent CHANGED runs whose
    normalized_hash differs from the run immediately before it, INCLUDING the
    current (new_hash) run as the tip of the streak. If that streak reaches
    ``k`` the source is quarantined.

    A genuine single change has a streak of 1 (or the prior run had the same
    hash, breaking the streak) and is never suppressed. A source that flapped
    then stabilised (same hash twice) breaks the streak, so a later real
    change alerts again.
    """
    if not new_hash or k < 2:
        return False

    # Chronological history for this source (append order == time order),
    # then reversed so index 0 is the most recent prior run.
    history = [r for r in _read_runs() if r.get("source_id") == source_id]
    history.reverse()

    # The current run is the tip: a distinct new hash vs the previous run.
    # Walk backwards accumulating consecutive CHANGED runs whose hash differs
    # from the one before them.
    streak = 1  # the current new_hash run itself
    newer_hash = new_hash
    for record in history:
        if record.get("change_status") != "CHANGED":
            break
        this_hash = record.get("normalized_hash")
        if not this_hash or this_hash == newer_hash:
            # A repeated hash means the source stabilised — streak is broken.
            break
        streak += 1
        newer_hash = this_hash
        if streak >= k:
            return True

    return streak >= k


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
    flapping_max_consecutive: int | None = None,
    now: datetime | None = None,
) -> tuple[bool, str]:
    """
    Decide whether an alert for (source_id, new_hash) may be sent.

    Returns (True, "") when allowed, or (False, reason) with reason one of:
    "hash_already_alerted" | "cooldown_active" | "flapping_quarantine".
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

    # C: flapping quarantine — a source that re-hashes on every sweep (dynamic
    # page chrome, not real regulatory change) is suppressed so the founder
    # chat is not spammed with a fresh alert per cycle. Checked after the
    # exact-hash gate so a stabilised/oscillating hash is still deduped by it.
    k = flapping_max_consecutive if flapping_max_consecutive is not None else _flapping_max_consecutive()
    if _is_flapping(source_id, new_hash, k):
        return False, "flapping_quarantine"

    if last_alert_ts is not None and cooldown > timedelta(0) and (now - last_alert_ts) < cooldown:
        return False, "cooldown_active"
    return True, ""
