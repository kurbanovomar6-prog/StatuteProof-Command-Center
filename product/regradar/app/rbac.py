"""RBAC Stage-1 — the pure, DEFAULT-DENY permission primitive.

WHY THIS EXISTS (and why it is INERT):

StatuteProof's authorization is FLAT today: a single per-user owner-scope rule
(``app/tenancy.py``) decides whether a caller may see a given custom source, and
paid capabilities gate exports (``app/plan.py``). There is no notion of an
organisation, of teammates, or of least-privilege roles. This module lands the
*model* for that — an explicit role→permission matrix behind one pure function,
:func:`can` — WITHOUT touching any live request path.

SAFETY POSTURE — this mirrors the dormant/additive discipline used for the RFC
3161 anchor (see ``app/rfc3161_anchor.py``). Every default is chosen so that
adding this module changes nothing about how the running product behaves:

* **PURE + SIDE-EFFECT-FREE.** :func:`can` is a deterministic function of
  ``(principal.role, action)`` plus an optional resource-ownership check. It
  imports no database, performs no I/O, and never raises for bad input — an
  unusable principal or an unknown action simply DENIES. This makes it trivial
  to unit-test in isolation, exactly as required for a Stage-1 foundation.
* **NOT WIRED IN.** Nothing in ``app/api.py`` (or any other request path) calls
  :func:`can` in this stage. A later Stage-2 will resolve a real
  :class:`Principal` from the ``org_members`` table and gate endpoints on it.
* **DEFAULT-DENY.** The matrix grants ONLY what is explicitly listed. Any action
  string not present in a role's set — including typos and future actions not yet
  added — is denied. There is no wildcard and no "allow the rest" fallthrough.

BACKWARD COMPATIBILITY WITH TODAY'S FLAT MODEL: every existing user is
backfilled (``app/db.backfill_org_memberships``) as the ``owner`` of their own
org-of-one. Under this matrix ``owner`` is granted every action, and an owner
acting on a resource inside their own org passes the ownership check — so once
Stage-2 activates :func:`can`, a solo user retains exactly the full access they
have under the flat model.
"""
from __future__ import annotations

from dataclasses import dataclass

# ── org identity ────────────────────────────────────────────────────────────────

# The GLOBAL org (see ``app/db._CREATE_RBAC_TABLES``). A principal scoped to the
# GLOBAL org is treated as cross-org (an operator/founder view), never confined
# to a single tenant. Kept in sync with the seeded ``orgs.id`` = 0 row.
GLOBAL_ORG_ID = 0


# ── roles ───────────────────────────────────────────────────────────────────────

ROLE_OWNER = "owner"
ROLE_ADMIN = "admin"
ROLE_REVIEWER = "reviewer"
ROLE_APPROVER = "approver"
ROLE_AUDITOR = "auditor"
# SYSTEM is a machine principal (pipeline, scheduler), not an assignable seat.
ROLE_SYSTEM = "system"

# Roles a human can be assigned to in ``org_members.role``. ``system`` is
# deliberately excluded — it is not a membership seat, only the identity carried
# by :data:`SYSTEM`.
ASSIGNABLE_ROLES = frozenset(
    {ROLE_OWNER, ROLE_ADMIN, ROLE_REVIEWER, ROLE_APPROVER, ROLE_AUDITOR}
)


# ── actions (resource.verb) ──────────────────────────────────────────────────────

EVIDENCE_VIEW = "evidence.view"
EVIDENCE_EXPORT = "evidence.export"
EVIDENCE_CAPTURE = "evidence.capture"  # machine-written evidence record

REVIEW_VIEW = "review.view"
REVIEW_SUBMIT = "review.submit"    # annotate / submit a review for approval
REVIEW_APPROVE = "review.approve"  # the canonical human review gate

ALERT_VIEW = "alert.view"
ALERT_SEND = "alert.send"          # dispatch an alert to a customer

SOURCE_VIEW = "source.view"
SOURCE_EDIT = "source.edit"        # add / enable / disable / mutate a source

SETTINGS_VIEW = "settings.view"
SETTINGS_EDIT = "settings.edit"

MEMBER_VIEW = "member.view"
MEMBER_MANAGE = "member.manage"    # invite/remove members, change roles

# The full vocabulary. ``can`` denies any action string not in this set.
ALL_ACTIONS = frozenset(
    {
        EVIDENCE_VIEW,
        EVIDENCE_EXPORT,
        EVIDENCE_CAPTURE,
        REVIEW_VIEW,
        REVIEW_SUBMIT,
        REVIEW_APPROVE,
        ALERT_VIEW,
        ALERT_SEND,
        SOURCE_VIEW,
        SOURCE_EDIT,
        SETTINGS_VIEW,
        SETTINGS_EDIT,
        MEMBER_VIEW,
        MEMBER_MANAGE,
    }
)

# Every ``.view`` action, plus evidence export — the read/observe surface. Used to
# compose the auditor and other read-mostly roles so the "read-only" intent is
# expressed once, not duplicated per role.
_READ_ACTIONS = frozenset(
    {
        EVIDENCE_VIEW,
        REVIEW_VIEW,
        ALERT_VIEW,
        SOURCE_VIEW,
        SETTINGS_VIEW,
        MEMBER_VIEW,
    }
)


# ── principal / resource ─────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class Principal:
    """Who is acting. Immutable so it can be shared and hashed safely.

    ``user_id`` is ``None`` for the :data:`SYSTEM` principal. ``org_id`` is the
    org the principal is acting within (``GLOBAL_ORG_ID`` = cross-org). ``role``
    must be one of the role constants; an unknown role DENIES every action.
    """

    user_id: int | None
    org_id: int | None
    role: str


@dataclass(frozen=True, slots=True)
class Resource:
    """What is being acted upon (optional).

    When ``org_id`` is set, :func:`can` enforces that the principal is scoped to
    that same org (or is cross-org / SYSTEM). ``owner_user_id`` is carried for
    Stage-2 record-level checks; Stage-1 :func:`can` does not branch on it, but
    it keeps the shape stable so callers wired up later need not change.
    """

    resource_type: str = ""
    resource_id: str = ""
    org_id: int | None = None
    owner_user_id: int | None = None


# The SYSTEM principal — the identity for automated, non-human actions (the
# scrape→diff→evidence→alert pipeline, the scheduler). Cross-org by construction.
SYSTEM = Principal(user_id=None, org_id=GLOBAL_ORG_ID, role=ROLE_SYSTEM)


# ── role → permission matrix ─────────────────────────────────────────────────────
#
# DEFAULT-DENY: a role grants ONLY the actions explicitly listed here. There is
# no wildcard. Editing this table is the single place authorization policy lives.
#
#   owner     — full control of the org, including membership.
#   admin     — broad operational control, but NOT membership management
#               (inviting/removing members and changing roles is the owner's
#               governance lever).
#   approver  — the review actions PLUS approval authority and alert dispatch.
#   reviewer  — the review actions (view/submit) but cannot approve or send.
#   auditor   — READ + EXPORT evidence only. Cannot approve, send, or mutate
#               anything. This is the compliance-observer seat.
#   system    — the machine actions the pipeline needs (capture evidence, read,
#               dispatch alerts). It deliberately CANNOT approve a review — the
#               human review gate is never self-approved by the machine — nor
#               mutate sources/settings/members.

_MATRIX: dict[str, frozenset[str]] = {
    ROLE_OWNER: ALL_ACTIONS,
    ROLE_ADMIN: ALL_ACTIONS - frozenset({MEMBER_MANAGE}),
    ROLE_APPROVER: _READ_ACTIONS
    | frozenset({EVIDENCE_EXPORT, REVIEW_SUBMIT, REVIEW_APPROVE, ALERT_SEND}),
    ROLE_REVIEWER: _READ_ACTIONS | frozenset({EVIDENCE_EXPORT, REVIEW_SUBMIT}),
    ROLE_AUDITOR: _READ_ACTIONS | frozenset({EVIDENCE_EXPORT}),
    ROLE_SYSTEM: frozenset(
        {
            EVIDENCE_CAPTURE,
            EVIDENCE_VIEW,
            REVIEW_VIEW,
            ALERT_VIEW,
            ALERT_SEND,
            SOURCE_VIEW,
        }
    ),
}


def permissions_for(role: str) -> frozenset[str]:
    """Return the (immutable) set of actions granted to ``role``.

    An unknown role returns the empty set — default-deny, never a crash.
    """
    return _MATRIX.get(role, frozenset())


def _org_scope_ok(principal: Principal, resource: Resource) -> bool:
    """True when ``principal`` may act on a resource owned by ``resource.org_id``.

    SYSTEM and any GLOBAL-org principal act across orgs; everyone else is
    confined to their own org. A principal with no ``org_id`` is confined
    (fail-closed): it can only match a resource with the same ``None`` org, which
    a real tenant resource never has.
    """
    if principal.role == ROLE_SYSTEM:
        return True
    if principal.org_id == GLOBAL_ORG_ID:
        return True
    return principal.org_id == resource.org_id


def can(principal: Principal, action: str, resource: Resource | None = None) -> bool:
    """Return True only when ``principal`` is explicitly permitted ``action``.

    Pure and default-deny. Denies (returns ``False``, never raises) when:

    * ``principal`` is not a :class:`Principal`;
    * ``principal.role`` / ``action`` is not a string (defensive: keeps the
      "never raises" contract even if a caller passes an unhashable value);
    * ``principal.role`` is unknown (not in the matrix);
    * ``action`` is not explicitly granted to that role (covers typos and any
      not-yet-modelled action);
    * a :class:`Resource` with an ``org_id`` is supplied and the principal is not
      scoped to that org (and is neither cross-org nor SYSTEM).

    The parameters are typed as :class:`Principal` / :class:`Resource` so callers
    are type-checked, while the ``isinstance`` guards below make the runtime
    behaviour fail-closed for anything that slips past static typing. This is NOT
    wired into any live endpoint in Stage-1; it exists to be unit tested and
    activated later.
    """
    if not isinstance(principal, Principal):
        return False
    if not isinstance(principal.role, str) or not isinstance(action, str):
        return False

    granted = _MATRIX.get(principal.role)
    if granted is None:
        return False  # unknown role → deny everything
    if action not in granted:
        return False  # default-deny: only explicitly granted actions pass

    if isinstance(resource, Resource) and resource.org_id is not None:
        if not _org_scope_ok(principal, resource):
            return False

    return True
