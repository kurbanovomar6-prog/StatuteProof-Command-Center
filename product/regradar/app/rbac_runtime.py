"""RBAC Stage-2 — the LIVE runtime bridge between requests and the pure policy.

WHAT CHANGED FROM STAGE-1: Stage-1 landed an INERT foundation — the pure
default-deny :func:`app.rbac.can`, the immutable :mod:`app.access_log`, and the
``orgs`` / ``org_members`` tables with every existing user backfilled as the
``owner`` of their org-of-one. Nothing called any of it. This module is the thin,
ADDITIVE layer that finally wires that foundation into the running product,
WITHOUT changing behaviour for any existing user.

WHY A SEPARATE MODULE (not inline in ``app/api.py``): the HTTP layer stays free
of RBAC internals. ``app/api.py`` imports THIS module only and calls its helpers;
it never touches :mod:`app.rbac` or :mod:`app.access_log` directly. That keeps a
single, unit-testable choke point for principal resolution, audit logging, and
the role gate — and keeps the 3.6k-line API surface from growing an authorization
tangle.

TWO GUARANTEES, both proven by tests:

* **No regression for existing users.** Every existing account is the ``owner``
  of its org (Stage-1 backfill), and :func:`resolve_principal` fails SAFE to
  ``owner`` whenever membership cannot be read (brand-new user before the
  once-per-process backfill, or any lookup error). ``owner`` is granted every
  action, so :func:`is_permitted` returns ``True`` for them and NOTHING about the
  request changes. There is exactly one role in the live data today — ``owner`` —
  so the gate is a no-op in practice while the machinery is fully live.

* **Audit logging never breaks an action.** :func:`log_sensitive_action` is
  wrapped so a logging failure (disk full, locked DB, …) is swallowed and the
  endpoint proceeds exactly as before. It is ADDITIVE observation, never a gate.

The role GATE (:func:`is_permitted` / the ``_rbac_guard`` in ``app/api.py``) only
ever DENIES a non-``owner`` role that lacks the action — e.g. an ``auditor`` seat
attempting a mutation. Because no such seat exists in live data yet, activating
this changes nothing today; it makes the least-privilege machinery real for the
moment a teammate is added as an ``auditor``.
"""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone
from typing import Any

from app.access_log import (  # noqa: F401 (read_access_log re-exported for callers)
    RESULT_ALLOW,
    RESULT_DENY,
    RESULT_ERROR,
    append_access_log,
    read_access_log,
)
from app.db import _connect, ensure_rbac_tables
from app.rbac import (
    ASSIGNABLE_ROLES,
    GLOBAL_ORG_ID,
    Principal,
    Resource,
    ROLE_DENIED,
    ROLE_OWNER,
    SYSTEM,
    can,
)

# Re-export the action vocabulary and result constants so callers (``app/api.py``)
# reference them through THIS module and never import ``app.rbac`` /
# ``app.access_log`` directly. The HTTP layer thus depends on one RBAC module.
from app.rbac import (  # noqa: F401 (re-exported for callers)
    ALERT_SEND,
    EVIDENCE_EXPORT,
    EVIDENCE_SHARE,
    MEMBER_MANAGE,
    PLAN_ADMIN,
    REVIEW_APPROVE,
    REVIEW_SUBMIT,
    SETTINGS_EDIT,
    SOURCE_EDIT,
)

__all__ = [
    "resolve_principal",
    "evaluate",
    "is_permitted",
    "log_sensitive_action",
    "assign_org_role",
    "bootstrap_operator",
    "read_access_log",
    "ROLE_OWNER",
    # re-exports
    "RESULT_ALLOW",
    "RESULT_DENY",
    "ALERT_SEND",
    "EVIDENCE_EXPORT",
    "EVIDENCE_SHARE",
    "MEMBER_MANAGE",
    "PLAN_ADMIN",
    "REVIEW_APPROVE",
    "REVIEW_SUBMIT",
    "SETTINGS_EDIT",
    "SOURCE_EDIT",
]

logger = logging.getLogger(__name__)


# ── principal resolution ─────────────────────────────────────────────────────────

def _safe_user_id(user: Any) -> int | None:
    """Extract an int user id from the authed ``user`` dict, or ``None``.

    Never raises — a malformed ``user`` yields ``None`` and the caller fails safe.
    """
    if not isinstance(user, dict):
        return None
    try:
        return int(user["id"])
    except (KeyError, TypeError, ValueError):
        return None


def _resolve_from_db(user_id: int) -> tuple[int | None, str] | None:
    """Return ``(org_id, role)`` for ``user_id`` from ``org_members``, or ``None``.

    Prefers the org the user OWNS (their backfilled org-of-one) so a solo user
    resolves to ``owner`` of the org that actually holds their resources, even if
    they were later added as a lesser role in some other org. A single connection
    provisions the tables (idempotent) and runs the lookup.
    """
    conn = _connect()
    try:
        ensure_rbac_tables(conn)
        row = conn.execute(
            """
            SELECT m.org_id AS org_id, m.role AS role
            FROM org_members m
            JOIN orgs o ON o.id = m.org_id
            WHERE m.user_id = ?
            ORDER BY
                -- GLOBAL scope wins outright. An operator seat is granted only by
                -- the founder CLI (bootstrap_operator), and its entire purpose is
                -- to act across orgs — so if a user holds it, it IS their operative
                -- scope. Without this the seat is inert: the founder also OWNS an
                -- org-of-one, which the next clause prefers, so resolve_principal
                -- kept returning that org and _caller_is_operator stayed False.
                CASE WHEN m.org_id = ? THEN 0 ELSE 1 END,
                CASE WHEN o.owner_user_id = ? THEN 0 ELSE 1 END,
                m.id ASC
            LIMIT 1
            """,
            (user_id, GLOBAL_ORG_ID, user_id),
        ).fetchone()
        if row is not None:
            role = str(row["role"])
            # A corrupt/unknown stored role must FAIL CLOSED, not escalate: mapping
            # it to owner would hand full privileges to a member whose row was
            # damaged or tampered. ROLE_DENIED grants nothing (can() denies), so a
            # bad row locks the seat down until an owner reassigns a valid role.
            # Known assignable roles (incl. auditor) are preserved as-is.
            if role not in ASSIGNABLE_ROLES:
                role = ROLE_DENIED
            return (row["org_id"], role)
        # No membership row yet. Recover the org the user owns if one exists (the
        # backfill may not have run on this process's hot path yet), else None.
        owned = conn.execute(
            "SELECT id FROM orgs WHERE owner_user_id = ? LIMIT 1",
            (user_id,),
        ).fetchone()
        if owned is not None:
            return (owned["id"], ROLE_OWNER)
        return None
    finally:
        conn.close()


def resolve_principal(user: Any) -> Principal:
    """Resolve the authed ``user`` to a :class:`Principal`. NEVER raises.

    FAIL-CLOSED posture — a failure to establish the caller's real role denies
    rather than escalating (owner decision 2026-07-13):

    * A membership row → that ``(org_id, role)`` (assignable roles incl.
      ``auditor`` preserved as-is; a corrupt/unknown stored role → ``denied``).
    * No membership row, but the user owns an org → ``owner`` of that org.
    * No membership and owns no org yet → ``owner`` of their own (``org_id=None``)
      scope. This is a newly-registered solo user before the once-per-process
      backfill — ONBOARDING, not escalation: org-scoped reads isolate ``None`` to
      the empty bucket, so they see none of another tenant's data.
    * Malformed user id, or ANY DB error during lookup → ``denied`` (zero
      capabilities). A transient failure must not hand a lesser-role member owner
      privileges; the seat is locked until resolution succeeds again.
    """
    user_id = _safe_user_id(user)
    if user_id is None:
        # Post-auth this should not happen; deny rather than mint owner from a
        # malformed identity.
        return Principal(user_id=None, org_id=None, role=ROLE_DENIED)
    try:
        found = _resolve_from_db(user_id)
    except sqlite3.Error:
        logger.warning("rbac principal lookup failed for user %s; failing CLOSED (denied)", user_id)
        return Principal(user_id=user_id, org_id=None, role=ROLE_DENIED)
    except Exception:  # noqa: BLE001 — resolution must never break a live request
        logger.warning("rbac principal resolution error for user %s; failing CLOSED (denied)", user_id)
        return Principal(user_id=user_id, org_id=None, role=ROLE_DENIED)
    if found is not None:
        org_id, role = found
        return Principal(user_id=user_id, org_id=org_id, role=role)
    # No membership and owns no org yet — onboarding (see docstring). Owner of
    # their OWN None-scoped resources so a brand-new customer can use the product.
    return Principal(user_id=user_id, org_id=None, role=ROLE_OWNER)


# ── permission evaluation (Part B — role gate) ───────────────────────────────────

def evaluate(user: Any, action: str, resource: Resource | None = None) -> tuple[bool, Principal]:
    """Resolve the principal and evaluate ``action`` against the role matrix.

    Returns ``(allowed, principal)`` so the caller can log the decision with the
    SAME principal it evaluated (one resolution, one truth). Pure once the
    principal is resolved — delegates to :func:`app.rbac.can`.
    """
    principal = resolve_principal(user)
    allowed = bool(can(principal, action, resource))
    return allowed, principal


def is_permitted(user: Any, action: str, resource: Resource | None = None) -> bool:
    """True when ``user`` may perform ``action``. Convenience over :func:`evaluate`."""
    allowed, _ = evaluate(user, action, resource)
    return allowed


# ── immutable audit logging (Part A — additive, never a gate) ────────────────────

def log_sensitive_action(
    user: Any,
    action: str,
    *,
    result: str = RESULT_ALLOW,
    resource_type: str = "",
    resource_id: str = "",
    principal: Principal | None = None,
) -> None:
    """Append one immutable ``access_log`` row for a sensitive action. NEVER raises.

    This is ADDITIVE observation — the compliance "who did what, when, allowed or
    denied" trail. It is wrapped end-to-end so a logging failure (locked DB, disk
    error, …) is swallowed and the calling endpoint proceeds EXACTLY as before.
    It must therefore never appear in a code path that decides an outcome.

    Pass ``principal`` to reuse an already-resolved principal (avoids a second DB
    lookup); otherwise it is resolved here.
    """
    try:
        p = principal if isinstance(principal, Principal) else resolve_principal(user)
        append_access_log(
            actor_user_id=p.user_id,
            org_id=p.org_id,
            action=str(action),
            result=str(result),
            resource_type=str(resource_type or ""),
            resource_id=str(resource_id or ""),
        )
    except Exception:  # noqa: BLE001 — audit logging must NEVER break the action
        logger.warning("access-log write failed for action=%s (non-fatal)", action)


# ── membership management (owner-gated) ──────────────────────────────────────────

def assign_org_role(
    actor_user: Any,
    target_user_id: int,
    org_id: int,
    role: str,
) -> dict[str, Any]:
    """Assign ``role`` to ``target_user_id`` within ``org_id``. Owner-gated.

    Authorization: the acting principal must hold ``member.manage`` for that org —
    under the role matrix ONLY ``owner`` does (admin deliberately does not), and
    org-scoping in :func:`app.rbac.can` confines an owner to their own org. So an
    owner can seat a teammate as an ``auditor`` in THEIR org, and nobody else can.

    Returns ``{"ok": True, "org_id", "user_id", "role"}`` on success, or
    ``{"ok": False, "error": <code>}`` for ``invalid_role`` / ``invalid_target`` /
    ``forbidden``. The decision is written to the immutable access log either way.
    Upserts on the ``UNIQUE(org_id, user_id)`` membership so re-assigning a role is
    idempotent.
    """
    role = str(role or "").strip()
    if role not in ASSIGNABLE_ROLES:
        return {"ok": False, "error": "invalid_role"}
    try:
        target_user_id = int(target_user_id)
        org_id = int(org_id)
    except (TypeError, ValueError):
        return {"ok": False, "error": "invalid_target"}

    actor = resolve_principal(actor_user)
    resource = Resource(
        resource_type="member",
        resource_id=str(target_user_id),
        org_id=org_id,
    )
    if not can(actor, MEMBER_MANAGE, resource):
        log_sensitive_action(
            actor_user,
            MEMBER_MANAGE,
            result=RESULT_DENY,
            resource_type="member",
            resource_id=str(target_user_id),
            principal=actor,
        )
        return {"ok": False, "error": "forbidden"}

    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        ensure_rbac_tables(conn)
        conn.execute(
            """
            INSERT INTO org_members (org_id, user_id, role, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(org_id, user_id) DO UPDATE SET role = excluded.role
            """,
            (org_id, target_user_id, role, now),
        )
        conn.commit()
    finally:
        conn.close()

    log_sensitive_action(
        actor_user,
        MEMBER_MANAGE,
        result=RESULT_ALLOW,
        resource_type="member",
        resource_id=str(target_user_id),
        principal=actor,
    )
    return {"ok": True, "org_id": org_id, "user_id": target_user_id, "role": role}


def bootstrap_operator(target_user_id: int, role: str = ROLE_OWNER) -> dict[str, Any]:
    """Seed the FIRST operator — a principal scoped to the GLOBAL org.

    Why this has to exist. ``assign_org_role`` requires the actor to hold
    ``member.manage`` for the target org, and :func:`app.rbac.can` confines an
    owner to their own org. For ``GLOBAL_ORG_ID`` that means you must already BE
    an operator to create one, and nothing ever seeds the first — ``app/db.py``
    inserts the GLOBAL *org* row but never a membership in it. Measured
    2026-07-25 (tools/measure_security_axis.py, and against the working database):
    0 rows in ``org_members`` with ``org_id = 0``, so ``_caller_is_operator`` is
    False for every account that can exist and the shared-official-evidence review
    gate can never be satisfied by anyone.

    This breaks the cycle with the SYSTEM principal, which is cross-org by
    construction (``app/rbac.py``) — the same identity the pipeline acts under.

    NOT reachable over HTTP, and deliberately so: it is called from the founder
    CLI (``run.py bootstrap-operator``), which already requires shell access to
    the production host. Granting cross-tenant scope is the single most powerful
    action in this system, and it should cost an SSH session. The grant is written
    to the immutable access log like any other.
    """
    role = str(role or "").strip()
    if role not in ASSIGNABLE_ROLES:
        return {"ok": False, "error": "invalid_role"}
    try:
        target_user_id = int(target_user_id)
    except (TypeError, ValueError):
        return {"ok": False, "error": "invalid_target"}

    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        ensure_rbac_tables(conn)
        exists = conn.execute(
            "SELECT 1 FROM users WHERE id = ?", (target_user_id,)
        ).fetchone()
        if exists is None:
            return {"ok": False, "error": "invalid_target"}
        conn.execute(
            """
            INSERT INTO org_members (org_id, user_id, role, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(org_id, user_id) DO UPDATE SET role = excluded.role
            """,
            (GLOBAL_ORG_ID, target_user_id, role, now),
        )
        conn.commit()
    finally:
        conn.close()

    log_sensitive_action(
        None,
        MEMBER_MANAGE,
        result=RESULT_ALLOW,
        resource_type="member",
        resource_id=str(target_user_id),
        principal=SYSTEM,
    )
    return {"ok": True, "org_id": GLOBAL_ORG_ID, "user_id": target_user_id, "role": role}
