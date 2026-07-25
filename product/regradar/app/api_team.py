"""Team seating over HTTP — the door that only a shell could open before.

Seating a colleague existed solely as a founder CLI (``run.py seat-member``), so
every customer who wanted a second pair of eyes on their evidence had to email
us and wait for someone to SSH into production. For a product whose buyer is an
MLRO who must *evidence* review, "your colleague cannot log in until we run a
command" is not a missing nicety; it is the workflow.

Scope is deliberately small: list the roster, seat someone who already has an
account, revoke a seat, and switch between orgs you already belong to. There is
no email-invite flow here — that needs deliverability the account-verification
path only got last week, and half an invite system is worse than none.

Authorization is not re-implemented. Every mutation goes through
``app.rbac_runtime``, where ``member.manage`` is owner-only under the role
matrix and ``app.rbac.can`` confines an owner to their own org; the roster query
is bounded to ``principal.org_id`` and never to a caller-supplied one, so there
is no shape of request that reads another tenant's members.
"""
from __future__ import annotations

from app.api import (
    _ADMIN_LIMITER,
    logger,
    rbac_runtime,
    require_auth,
)


class _TeamHandlerMixin:
    def _team_user(self) -> dict | None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return None
        return user

    def _handle_team_members_list(self) -> None:
        """GET /api/team/members — the caller's own org roster. Owner-gated."""
        user = self._team_user()
        if not user:
            return

        result = rbac_runtime.list_org_members(user)
        if not result.get("ok"):
            # Deliberately the same 403 shape as any other refused action: an
            # owner-only endpoint that explained *why* would tell a seated
            # auditor exactly which privilege to go phishing for.
            self._send_json({"ok": False, "message": "Not permitted."}, 403)
            return

        self._send_json({
            "ok": True,
            "org_id": result["org_id"],
            "members": result["members"],
        })

    def _handle_team_member_add(self) -> None:
        """POST /api/team/members {email, role} — seat an existing account."""
        user = self._team_user()
        if not user:
            return
        if self._rate_limited(_ADMIN_LIMITER, "team_member_add"):
            return

        body, err = self._read_json_strict()
        if err or body is None:
            self._send_json({"ok": False, "message": err or "Invalid JSON."}, 400)
            return

        email = str(body.get("email", "")).strip()
        role = str(body.get("role", "auditor")).strip() or "auditor"
        if not email:
            self._send_json({"ok": False, "message": "Email is required."}, 400)
            return

        from app.auth import get_user_by_email

        target = get_user_by_email(email)
        if not target:
            # Not an enumeration oracle worth worrying about — the caller is an
            # authenticated owner acting on their own org — but it IS the one
            # case where silence would be cruel: they typed a colleague's
            # address and need to know the colleague must register first.
            self._send_json({
                "ok": False,
                "message": "No StatuteProof account uses that email yet. "
                           "Ask them to register first, then add them here.",
                "error": "no_such_account",
            }, 404)
            return

        principal = rbac_runtime.resolve_principal(user)
        result = rbac_runtime.assign_org_role(
            user, int(target["id"]), int(principal.org_id or 0), role
        )
        if not result.get("ok"):
            code = str(result.get("error") or "")
            if code == "invalid_role":
                self._send_json({"ok": False, "message": "Unknown role."}, 400)
            else:
                self._send_json({"ok": False, "message": "Not permitted."}, 403)
            return

        logger.info(
            "team: user %s seated in org %s as %s",
            target["id"], result["org_id"], result["role"],
        )
        self._send_json({
            "ok": True,
            "org_id": result["org_id"],
            "user_id": result["user_id"],
            "role": result["role"],
        })

    def _handle_team_member_revoke(self) -> None:
        """POST /api/team/members/revoke {email} — remove a seat."""
        user = self._team_user()
        if not user:
            return
        if self._rate_limited(_ADMIN_LIMITER, "team_member_revoke"):
            return

        body, err = self._read_json_strict()
        if err or body is None:
            self._send_json({"ok": False, "message": err or "Invalid JSON."}, 400)
            return

        email = str(body.get("email", "")).strip()
        if not email:
            self._send_json({"ok": False, "message": "Email is required."}, 400)
            return

        from app.auth import get_user_by_email

        target = get_user_by_email(email)
        if not target:
            self._send_json({"ok": False, "message": "No such member."}, 404)
            return

        result = rbac_runtime.revoke_org_member(user, int(target["id"]))
        if not result.get("ok"):
            if result.get("error") == "cannot_revoke_owner":
                self._send_json({
                    "ok": False,
                    "message": "The org owner cannot be removed.",
                }, 400)
                return
            self._send_json({"ok": False, "message": "Not permitted."}, 403)
            return

        self._send_json({"ok": True, "removed": bool(result.get("removed"))})

    def _handle_team_active_org(self) -> None:
        """POST /api/team/active-org {org_id} — switch between your own orgs.

        Not owner-gated: it only selects among orgs the caller has already been
        seated in. Requiring a privilege here would mean an owner had to approve
        a colleague viewing the very org that owner just added them to.
        """
        user = self._team_user()
        if not user:
            return

        body, err = self._read_json_strict()
        if err or body is None:
            self._send_json({"ok": False, "message": err or "Invalid JSON."}, 400)
            return

        result = rbac_runtime.set_active_org(user, body.get("org_id"))
        if not result.get("ok"):
            self._send_json({
                "ok": False,
                "message": "You are not a member of that workspace.",
            }, 403)
            return

        self._send_json({"ok": True, "org_id": result["org_id"]})
