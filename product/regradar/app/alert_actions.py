"""
Alert Action Log — v1.

Records the compliance team's decision for each alert:
  decision: "act" | "monitor" | "no_action"
  notes: free text (optional)
  reviewer_name: free text (optional)
  action_hash: SHA-256 of (alert_id + decision + notes + created_at) for immutability evidence

Never raises. Returns None on failure.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

from app.db import _connect

logger = logging.getLogger(__name__)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compute_hash(alert_id: str, decision: str, notes: str, created_at: str) -> str:
    payload = f"{alert_id}|{decision}|{notes}|{created_at}"
    return hashlib.sha256(payload.encode()).hexdigest()


def save_action_log_entry(
    user_id: int,
    alert_id: str,
    decision: str,
    notes: str = "",
    reviewer_name: str = "",
) -> dict | None:
    """Insert a new action log entry. Returns the saved row as dict, or None on failure."""
    valid_decisions = {"act", "monitor", "no_action"}
    if decision not in valid_decisions:
        logger.warning("save_action_log_entry: invalid decision %r", decision)
        return None
    try:
        created_at = _now_utc()
        action_hash = _compute_hash(alert_id, decision, notes, created_at)
        conn = _connect()
        try:
            cursor = conn.execute(
                """INSERT INTO alert_action_log
                   (user_id, alert_id, decision, notes, reviewer_name, created_at, action_hash)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, alert_id, decision, notes or "", reviewer_name or "", created_at, action_hash),
            )
            conn.commit()
            row_id = cursor.lastrowid
            return {
                "id": row_id,
                "user_id": user_id,
                "alert_id": alert_id,
                "decision": decision,
                "notes": notes or "",
                "reviewer_name": reviewer_name or "",
                "created_at": created_at,
                "action_hash": action_hash,
            }
        finally:
            conn.close()
    except Exception as exc:
        logger.warning("save_action_log_entry failed: %s", exc)
        return None


def get_action_log(user_id: int, alert_id: str) -> list[dict]:
    """Fetch action log entries for a given alert and user. Returns list (may be empty)."""
    try:
        conn = _connect()
        try:
            rows = conn.execute(
                """SELECT id, user_id, alert_id, decision, notes, reviewer_name, created_at, action_hash
                   FROM alert_action_log
                   WHERE user_id = ? AND alert_id = ?
                   ORDER BY created_at DESC""",
                (user_id, alert_id),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    except Exception as exc:
        logger.warning("get_action_log failed: %s", exc)
        return []
