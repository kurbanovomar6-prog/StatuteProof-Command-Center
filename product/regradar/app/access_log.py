"""Immutable, append-only access log for RBAC Stage-1 — INERT in this stage.

WHAT THIS IS: a write-once audit trail of authorization decisions and privileged
actions. Each call to :func:`append_access_log` inserts exactly one row into the
``access_log`` table (created by ``app/db.ensure_rbac_tables``). It records WHO
(``actor_user_id`` / ``org_id``), WHAT (``action`` on ``resource_type`` /
``resource_id``), and the OUTCOME (``result`` — typically "allow" / "deny").

APPEND-ONLY BY CONSTRUCTION — enforced at two layers:
* Application: this module exposes INSERT and read helpers ONLY; there is
  deliberately no update or delete function anywhere in the RBAC layer.
* Database: ``app/db._CREATE_RBAC_TABLES`` installs ``BEFORE UPDATE`` /
  ``BEFORE DELETE`` triggers that ``RAISE(ABORT, …)``, so even a stray writer
  opening its own connection cannot alter or remove a recorded row.
That immutability is the whole point of an access log used for audit.

INERT IN STAGE-1: no endpoint, pipeline, or scheduler calls
:func:`append_access_log` yet. It exists so Stage-2 — when :func:`app.rbac.can`
is wired into request paths — can record every decision without introducing a new
storage primitive at that time. Adding this module changes nothing about how the
running product behaves.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.db import _connect, ensure_rbac_tables

logger = logging.getLogger(__name__)

# Canonical result values. ``result`` is stored as free text so Stage-2 can add
# outcomes without a migration, but these two cover the allow/deny decision.
RESULT_ALLOW = "allow"
RESULT_DENY = "deny"
# RBAC evaluation itself failed and the gate fell open; recorded so the anomaly is
# never silent in the audit trail (see app/api.py::_rbac_guard fail-open branch).
RESULT_ERROR = "error"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_access_log(
    *,
    actor_user_id: int | None,
    org_id: int | None,
    action: str,
    result: str,
    resource_type: str = "",
    resource_id: str = "",
) -> int:
    """Append one immutable row to ``access_log`` and return its row id.

    Keyword-only so a caller can never transpose ``actor_user_id`` and ``org_id``
    or ``action`` and ``result`` positionally. ``actor_user_id`` / ``org_id`` may
    be ``None`` (e.g. the SYSTEM principal has no user id). ``action`` and
    ``result`` are coerced to ``str`` so a caller passing an action constant or a
    boolean-ish result cannot inject a non-text value.

    There is no companion update/delete function — rows are permanent once
    written. INERT in Stage-1: nothing calls this on a live path yet.
    """
    ensure_rbac_tables()
    ts = _now_iso()
    conn = _connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO access_log
                (ts, actor_user_id, org_id, action, resource_type, resource_id, result)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts,
                actor_user_id,
                org_id,
                str(action),
                str(resource_type or ""),
                str(resource_id or ""),
                str(result),
            ),
        )
        conn.commit()
        row_id = cur.lastrowid
        return int(row_id) if row_id is not None else -1
    finally:
        conn.close()


def read_access_log(limit: int = 100) -> list[dict[str, Any]]:
    """Return the most recent access-log rows, newest first (read-only).

    A convenience reader for tests and future audit views. It performs no writes
    and there is intentionally no update/delete counterpart, preserving the
    append-only guarantee.
    """
    ensure_rbac_tables()
    try:
        capped = max(1, min(int(limit), 10_000))
    except (TypeError, ValueError):
        capped = 100
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT id, ts, actor_user_id, org_id, action,
                   resource_type, resource_id, result
            FROM access_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (capped,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
