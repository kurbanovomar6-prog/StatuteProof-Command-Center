"""Per-alert review checklist — obligation-workflow v1.

WHAT THIS IS: a lightweight, user-authored to-do list hung off a single alert.
A user adds a few review action items (their own words), optionally names an
assignee and a due date, ticks them done, and deletes them. Every mutation is
appended to the immutable access log so the review -> action chain becomes part
of the evidence trail (who ticked what, when).

LEGAL FRAMING (CLAUDE.md, load-bearing): the checklist is the USER'S OWN review
workflow. ``text`` and ``assignee`` are the user's words. StatuteProof NEVER
generates, prescribes, or suggests a compliance action here — there is no
AI-authored item, no "you must file X". The app's OWN framing strings
(``FRAMING`` below) are the only StatuteProof-authored copy, and they are held to
the forbidden-claims guard (see tests). This module is a workflow aid over
monitoring evidence, not compliance advice.

TENANCY: ``owner_user_id`` is the ONE scoping key. Every query filters on
``owner_user_id = ?`` so a user can only ever read or mutate their own items.
Update/delete match ``WHERE id = ? AND owner_user_id = ?``; a cross-user (or
absent) id matches zero rows and returns ``None`` / ``False`` — the caller maps
that to a 404 with no existence oracle (the same response for "not yours" and
"does not exist").

RESILIENCE: every function is fail-soft — bad input returns a benign value and
no function raises across the boundary. The access-log append is best-effort and
never blocks or fails a mutation.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

from app.db import _connect, ensure_checklist_table

logger = logging.getLogger(__name__)

# ── bounds (KISS caps so the surface stays small and abuse-resistant) ────────────
MAX_ITEMS_PER_ALERT = 25          # a checklist is a handful of actions, not a backlog
# Aggregate per-user cap: without it the per-alert cap is a false bound — alert_id
# is an opaque string, so distinct alert_ids (and thus total rows) would be capped
# only by the rate limiter. 100 alerts' worth of items is far beyond real use and
# keeps a single account's worst-case footprint at ~1.6MB in the shared DB.
MAX_ITEMS_PER_USER = 2500         # = 100 alerts × 25 items
MAX_TEXT_LEN = 500                # a single action item, not a document
MAX_ASSIGNEE_LEN = 120            # a name / role / email, bounded
MAX_DUE_DATE_LEN = 32             # an ISO date (YYYY-MM-DD) with slack
MAX_ALERT_ID_LEN = 200

STATUS_OPEN = "open"
STATUS_DONE = "done"
VALID_STATUSES = (STATUS_OPEN, STATUS_DONE)

# alert_id shape mirrors the send-preview handler's validation — opaque, bounded.
# \Z (not $): in Python re, $ also matches just before a trailing newline, which
# would let "abc\n" through and store a newline-bearing grouping key.
_ALERT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,%d}\Z" % MAX_ALERT_ID_LEN)

# access-log action vocabulary (free-text ``action`` column; namespaced).
ACTION_CREATE = "checklist.create"
ACTION_UPDATE = "checklist.update"
ACTION_DELETE = "checklist.delete"

# ── app-authored framing — the ONLY StatuteProof words in this feature ───────────
# Held to the forbidden-claims guard (tests/test_action_checklist.py). Deliberately
# describes the user's OWN workflow ("actions you choose to track") and never
# prescribes a compliance action. Returned in the GET payload so the UI renders
# guard-clean, server-authored copy.
FRAMING: dict[str, str] = {
    "title": "Your review checklist",
    "subtitle": "Review actions you choose to track for this alert.",
    "add_label": "Add a review action",
    "add_placeholder": "Describe a review step you want to track",
    "empty": "No review actions yet. Add the steps you choose to track for this alert.",
    "disclaimer": (
        "You author these items. For monitoring information only. "
        "Not legal advice and not a guarantee of compliance."
    ),
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def valid_alert_id(alert_id: Any) -> bool:
    """True when ``alert_id`` is a well-formed, bounded alert identifier."""
    return bool(_ALERT_ID_RE.match(str(alert_id or "")))


def _clean_text(value: Any, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _coerce_status(value: Any) -> str | None:
    text = str(value or "").strip().lower()
    return text if text in VALID_STATUSES else None


def _row_to_item(row: Any) -> dict[str, Any]:
    """Project a DB row to the client shape (owner_user_id is never exposed)."""
    return {
        "id": row["id"],
        "alert_id": row["alert_id"],
        "text": row["text"],
        "assignee": row["assignee"],
        "due_date": row["due_date"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _record_access_log(user_id: int, action: str, item_id: int | None, result: str = "allow") -> None:
    """Append one immutable access-log row for a checklist mutation. NEVER raises.

    Best-effort observation so the review -> action chain lands in the audit
    trail. Wrapped end-to-end: a logging failure (locked DB, import error, …) is
    swallowed here so it can never block or fail the mutation that already
    committed. Delegates to the shared ``rbac_runtime.log_sensitive_action`` so
    the org principal is resolved and the row is written the SAME way as every
    other sensitive action.
    """
    try:
        from app import rbac_runtime

        rbac_runtime.log_sensitive_action(
            {"id": int(user_id)},
            action,
            result=result,
            resource_type="checklist",
            resource_id=str(item_id if item_id is not None else ""),
        )
    except Exception:  # noqa: BLE001 — audit logging must NEVER break the action
        logger.warning("checklist access-log write failed for action=%s (non-fatal)", action)


def list_checklist_items(user_id: int, alert_id: str) -> list[dict[str, Any]]:
    """Return the caller's OWN checklist items for ``alert_id`` (may be empty).

    Owner-scoped by ``owner_user_id = ?``. Fail-soft: any error (or a malformed
    id) yields an empty list, never a raise.
    """
    if not valid_alert_id(alert_id):
        return []
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        return []
    try:
        ensure_checklist_table()
        conn = _connect()
        try:
            rows = conn.execute(
                """
                SELECT id, alert_id, text, assignee, due_date, status, created_at, updated_at
                FROM alert_checklist_items
                WHERE owner_user_id = ? AND alert_id = ?
                ORDER BY
                    CASE status WHEN 'open' THEN 0 ELSE 1 END,
                    created_at ASC, id ASC
                """,
                (uid, str(alert_id)),
            ).fetchall()
            return [_row_to_item(r) for r in rows]
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001 — read must never raise across the boundary
        logger.warning("list_checklist_items failed: %s", type(exc).__name__)
        return []


def add_checklist_item(
    user_id: int,
    alert_id: str,
    text: str,
    assignee: str = "",
    due_date: str = "",
) -> dict[str, Any] | None:
    """Add one user-authored action item to the caller's checklist for ``alert_id``.

    Returns the saved item dict, or ``None`` on invalid input / cap reached /
    failure. Bounded: rejects when the alert already holds
    ``MAX_ITEMS_PER_ALERT`` of the caller's items; text/assignee/due_date are
    length-capped. Appends an access-log row on success. Never raises.
    """
    if not valid_alert_id(alert_id):
        return None
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        return None

    clean_text = _clean_text(text, MAX_TEXT_LEN)
    if not clean_text:
        return None  # an empty action item is meaningless
    clean_assignee = _clean_text(assignee, MAX_ASSIGNEE_LEN)
    clean_due = _clean_text(due_date, MAX_DUE_DATE_LEN)

    try:
        now = _now_utc()
        ensure_checklist_table()
        conn = _connect()
        try:
            # BOTH caps are enforced ATOMICALLY inside the INSERT: the row is
            # written only when (a) the caller's item count for THIS alert is
            # under the per-alert bound AND (b) the caller's TOTAL item count is
            # under the per-user bound. One statement (not SELECT COUNT then
            # INSERT) removes the check-then-act race — concurrent adds can never
            # slip past either cap — and there is no separate count that could
            # fail open. Owner-scoped by ``owner_user_id`` in both subqueries.
            # The per-user bound matters because alert_id is an opaque string:
            # without it, distinct alert_ids would make total rows unbounded.
            cur = conn.execute(
                """
                INSERT INTO alert_checklist_items
                    (alert_id, owner_user_id, text, assignee, due_date, status, created_at, updated_at)
                SELECT ?, ?, ?, ?, ?, ?, ?, ?
                WHERE (
                    SELECT COUNT(*) FROM alert_checklist_items
                    WHERE owner_user_id = ? AND alert_id = ?
                ) < ?
                AND (
                    SELECT COUNT(*) FROM alert_checklist_items
                    WHERE owner_user_id = ?
                ) < ?
                """,
                (
                    str(alert_id), uid, clean_text, clean_assignee, clean_due, STATUS_OPEN, now, now,
                    uid, str(alert_id), MAX_ITEMS_PER_ALERT,
                    uid, MAX_ITEMS_PER_USER,
                ),
            )
            conn.commit()
            if cur.rowcount == 0:
                return None  # cap reached — the conditional INSERT wrote nothing
            item_id = cur.lastrowid
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001 — write must never raise across the boundary
        logger.warning("add_checklist_item failed: %s", type(exc).__name__)
        return None

    _record_access_log(uid, ACTION_CREATE, item_id)
    return {
        "id": item_id,
        "alert_id": str(alert_id),
        "text": clean_text,
        "assignee": clean_assignee,
        "due_date": clean_due,
        "status": STATUS_OPEN,
        "created_at": now,
        "updated_at": now,
    }


def update_checklist_item(
    user_id: int,
    item_id: int,
    *,
    status: str | None = None,
    text: str | None = None,
    assignee: str | None = None,
    due_date: str | None = None,
) -> dict[str, Any] | None:
    """Update the caller's OWN item (toggle status and/or edit fields).

    Owner-scoped: the UPDATE matches ``WHERE id = ? AND owner_user_id = ?`` so a
    cross-user (or absent) id changes nothing and returns ``None`` — no oracle.
    Only the provided fields change; ``status`` must be a valid value or the whole
    update is rejected. Appends an access-log row when a row actually changes.
    Never raises.
    """
    try:
        uid = int(user_id)
        iid = int(item_id)
    except (TypeError, ValueError):
        return None

    sets: list[str] = []
    params: list[Any] = []
    if status is not None:
        coerced = _coerce_status(status)
        if coerced is None:
            return None  # reject an unknown status rather than silently ignoring it
        sets.append("status = ?")
        params.append(coerced)
    if text is not None:
        clean_text = _clean_text(text, MAX_TEXT_LEN)
        if not clean_text:
            return None  # never blank out an item's text
        sets.append("text = ?")
        params.append(clean_text)
    if assignee is not None:
        sets.append("assignee = ?")
        params.append(_clean_text(assignee, MAX_ASSIGNEE_LEN))
    if due_date is not None:
        sets.append("due_date = ?")
        params.append(_clean_text(due_date, MAX_DUE_DATE_LEN))

    if not sets:
        return None  # nothing to update

    now = _now_utc()
    sets.append("updated_at = ?")
    params.append(now)

    try:
        ensure_checklist_table()
        conn = _connect()
        try:
            cur = conn.execute(
                f"""
                UPDATE alert_checklist_items
                SET {", ".join(sets)}
                WHERE id = ? AND owner_user_id = ?
                """,
                (*params, iid, uid),
            )
            conn.commit()
            if cur.rowcount == 0:
                return None  # not the caller's item (or gone) → 404, no oracle
            # Re-read the committed row for the response. If the caller concurrently
            # deleted this same item between the UPDATE and here, the SELECT returns
            # None and we surface None — the update did commit, but there is no row
            # left to return (a narrow, self-inflicted race, acceptable).
            row = conn.execute(
                """
                SELECT id, alert_id, text, assignee, due_date, status, created_at, updated_at
                FROM alert_checklist_items
                WHERE id = ? AND owner_user_id = ?
                """,
                (iid, uid),
            ).fetchone()
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        logger.warning("update_checklist_item failed: %s", type(exc).__name__)
        return None

    if row is None:
        return None
    _record_access_log(uid, ACTION_UPDATE, iid)
    return _row_to_item(row)


def delete_checklist_item(user_id: int, item_id: int) -> bool:
    """Delete the caller's OWN item. Returns True only when a row was removed.

    Owner-scoped: ``WHERE id = ? AND owner_user_id = ?`` so a cross-user id
    deletes nothing and returns ``False`` (→ 404, no oracle). Appends an
    access-log row on a real delete. Never raises.
    """
    try:
        uid = int(user_id)
        iid = int(item_id)
    except (TypeError, ValueError):
        return False
    try:
        ensure_checklist_table()
        conn = _connect()
        try:
            cur = conn.execute(
                "DELETE FROM alert_checklist_items WHERE id = ? AND owner_user_id = ?",
                (iid, uid),
            )
            conn.commit()
            removed = cur.rowcount > 0
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        logger.warning("delete_checklist_item failed: %s", type(exc).__name__)
        return False

    if removed:
        _record_access_log(uid, ACTION_DELETE, iid)
    return removed
