"""
Deferred delivery of cooldown-suppressed alerts (defect G1, 2026-07-16).

The per-source cooldown (``alert_dedup.should_send_alert``) intentionally
rate-limits to one alert per source per ``ALERT_COOLDOWN_HOURS``. But a GENUINELY
NEW change that landed inside that window used to be written as CHANGED and then
NEVER delivered: the next sweep sees unchanged content and short-circuits, so the
alert path is never re-entered and ``alert_suppressed_reason="cooldown_active"``
is only ever written, never acted on. That turned a rate-limit into a permanent
LOST alert — the worst customer-facing failure for a monitoring product.

Fix: when (and only when) the cooldown suppresses an otherwise-vetted alert, its
full payload is STASHED durably here. On any later sweep, ``flush_due()`` re-checks
the gate; once the cooldown has elapsed AND the stashed hash is still the source's
current state (not superseded by a newer change, not already delivered), the alert
is sent — a delay, not a drop. A superseded or already-delivered stash is
discarded unsent. State is one small JSON file per source; the evidence trail
remains the source of truth for ``alert_sent``.
"""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _pending_dir() -> Path:
    # Resolve through the configured base dir (STATUTEPROOF_BASE_DIR or the repo
    # default) exactly like the evidence trail, so the stash lives beside the
    # data it defers — never a hardcoded path relative to this file.
    from app import source_runs as _sr

    return Path(_sr._BASE_DIR) / "data" / "pending_alerts"


def _pending_path(source_id: str) -> Path:
    safe = _SAFE_ID_RE.sub("-", str(source_id or "unknown")).strip("-") or "unknown"
    return _pending_dir() / f"{safe}.json"


def load(source_id: str) -> dict | None:
    """Return the stashed pending-alert payload for a source, or None."""
    path = _pending_path(source_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as err:
        logger.warning("pending_alerts.load: unreadable stash for %s: %s", source_id, err)
        return None


def stash(payload: dict) -> Path | None:
    """Persist a cooldown-suppressed alert payload for later delivery.

    Overwrites any existing stash for the source — only the LATEST suppressed
    change matters (an older one it supersedes would be discarded anyway). No-op
    (returns None) when the payload lacks the fields flush_due needs.
    """
    source_id = str(payload.get("source_id") or "").strip()
    if not source_id or not payload.get("normalized_hash") or not payload.get("run_id"):
        logger.warning(
            "pending_alerts.stash: refusing incomplete payload (source_id/hash/run_id required)"
        )
        return None
    record = dict(payload)
    record["stashed_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    path = _pending_path(source_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic write: tmp in the same dir + os.replace, so a crash never leaves a
    # half-written stash that flush_due would choke on.
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".pending-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(record, fh, ensure_ascii=False)
        os.replace(tmp, path)
    except OSError as err:
        logger.warning("pending_alerts.stash: could not persist for %s: %s", source_id, err)
        try:
            os.unlink(tmp)
        except OSError:
            pass
        return None
    return path


def discard(source_id: str) -> None:
    """Remove a source's pending stash (superseded / delivered / stale)."""
    try:
        _pending_path(source_id).unlink(missing_ok=True)
    except OSError as err:
        logger.warning("pending_alerts.discard: could not remove stash for %s: %s", source_id, err)


def _latest_changed_hash(source_id: str, runs: list[dict]) -> str | None:
    """The normalized_hash of the source's most recent CHANGED run, or None."""
    for record in reversed(runs):
        if record.get("source_id") != source_id:
            continue
        if str(record.get("change_status") or "").upper() == "CHANGED":
            return record.get("normalized_hash")
    return None


def flush_due(
    source: dict,
    *,
    send_fn: Callable[[dict], object],
    now: datetime | None = None,
) -> bool:
    """Deliver a source's stashed alert if it is now due; return True if sent.

    Due means: the cooldown has elapsed (``should_send_alert`` allows it again),
    AND the stashed hash is still the source's current state (not superseded by a
    newer change), AND it was not already delivered by another path. Otherwise the
    stash is either kept (still cooling down / flapping) or discarded unsent
    (superseded / already alerted). A failed send keeps the stash for next sweep.
    """
    from app.alert_dedup import should_send_alert
    from app.source_runs import _read_runs, make_source_id, mark_alert_sent

    source_id = make_source_id(source)
    payload = load(source_id)
    if not payload:
        return False

    new_hash = payload.get("normalized_hash")
    run_id = payload.get("run_id")
    if not new_hash:
        discard(source_id)
        return False

    # Superseded? A newer CHANGED run carries its own alert/stash, so an older
    # stash is stale — drop it unsent rather than deliver an out-of-date change.
    latest_hash = _latest_changed_hash(source_id, _read_runs())
    if latest_hash is not None and latest_hash != new_hash:
        logger.info(
            "pending_alerts: discarding superseded stash for %s (stashed=%s current=%s)",
            source_id, str(new_hash)[:12], str(latest_hash)[:12],
        )
        discard(source_id)
        return False

    ok, reason = should_send_alert(source_id, new_hash, now=now)
    if not ok:
        if reason == "hash_already_alerted":
            # Delivered by some other path already — drop the duplicate stash.
            discard(source_id)
        # "cooldown_active" / "flapping_quarantine": keep waiting for a later sweep.
        return False

    try:
        sent = bool(send_fn(payload))
    except Exception as err:  # noqa: BLE001 - send is best-effort; keep the stash
        logger.warning("pending_alerts.flush_due: send failed for %s: %s", source_id, err)
        return False

    if not sent:
        # Delivery not confirmed — keep the stash so the next sweep retries.
        return False

    if run_id:
        try:
            mark_alert_sent(source_id, run_id, alert_sent=True)
        except Exception as err:  # noqa: BLE001
            logger.warning("pending_alerts.flush_due: mark_alert_sent failed for %s: %s", source_id, err)
    discard(source_id)
    logger.info(
        "pending_alerts: delivered deferred cooldown alert for %s (hash=%s)",
        source_id, str(new_hash)[:12],
    )
    return True
