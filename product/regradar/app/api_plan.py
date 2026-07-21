"""Plan-intent, founder billing-admin, and Stripe-webhook request handlers,
extracted from ``app.api``.

This module holds one cohesive slice of the HTTP surface — the plan read/intent
endpoints, the founder-only account roster + plan-activation endpoints, and the
unauthenticated Stripe webhook — as a mixin that ``app.api._Handler`` inherits.
The method bodies are byte-identical to their former inline definitions; only
their host class/file changed.

Names the moved bodies read as bare globals are imported here FROM ``app.api``
so they are the SAME objects the rest of the handler uses (and so tests that
monkeypatch ``app.api_plan.<name>`` steer these methods exactly as they
previously steered ``app.api.<name>``). The function-local imports inside the
methods (``from app.plan import …``, ``from app.stripe_webhook import …``)
resolve at CALL time against their source modules, so tests patching
``app.plan.*`` / ``app.stripe_webhook`` keep working unchanged. Shared
per-request helpers (``_send_json``, ``_rate_limited``, ``_rbac_guard``,
``_read_json_strict``, ``_read_raw_body``, ``_admin_guard``,
``_caller_is_admin``) stay on ``_Handler`` and are reached through ``self``.
"""
from __future__ import annotations

from app.api import (
    _ADMIN_LIMITER,
    _PLAN_INTENT_LIMITER,
    _STRIPE_WEBHOOK_LIMITER,
    _notify_founder_plan_intent,
    get_user_by_email,
    get_user_by_id,
    logger,
    parse_qs,
    rbac_runtime,
    require_auth,
    urlparse,
)


class _PlanHandlerMixin:
    """Plan-intent, founder billing-admin, and Stripe-webhook handlers for ``_Handler``."""

    def _handle_plan_get(self) -> None:
        """GET /api/plan — returns current plan + trial state for the logged-in user."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            from app.plan import get_plan_state
            state = get_plan_state(int(user["id"]))
            # Founder-only UI hint carried INSIDE the plan state (the frontend
            # stores `data.plan` as planState, so a top-level sibling would be
            # dropped). It only toggles whether the admin nav is shown — it is NOT
            # an authorization boundary: every admin endpoint independently
            # re-checks _admin_guard server-side.
            state["is_admin"] = self._caller_is_admin(user)
            self._send_json({"ok": True, "plan": state, "is_admin": state["is_admin"]})
        except Exception as exc:
            logger.error("plan_get failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_plan_set(self) -> None:
        """POST /api/plan — record plan intent (no payment processed)."""
        if self._rate_limited(_PLAN_INTENT_LIMITER, "plan_set"):
            return

        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        # RBAC Stage-2: changing plan intent is a settings mutation. Owner passes;
        # a read-only auditor seat is denied 403. No-op for accounts today.
        if not self._rbac_guard(user, rbac_runtime.SETTINGS_EDIT, resource_type="settings"):
            return
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        plan_name = str(body.get("plan_name", "")).strip()
        try:
            from app.plan import set_plan_intent, PLAN_NAMES
            if plan_name not in PLAN_NAMES:
                self._send_json({"ok": False, "message": f"Unknown plan: {plan_name}"}, 400)
                return
            state = set_plan_intent(int(user["id"]), plan_name)
            # ``intent_changed`` is dedupe metadata from set_plan_intent, not
            # customer-facing plan state — strip it before building the payload.
            # Missing key (e.g. a patched/legacy return) defaults to True so a
            # genuine intent is never silently dropped.
            intent_changed = bool(state.pop("intent_changed", True))
            # Founder heads-up via the admin bot — best-effort, never blocks or
            # fails the plan request (see _notify_founder_plan_intent). Without
            # this the customer was promised "Our team will contact you" while
            # nobody was told. Only fired when the recorded intent actually
            # CHANGED (2026-07-20 review: re-posting the same plan must not
            # re-page the founder channel), and the endpoint itself is throttled
            # by _PLAN_INTENT_LIMITER above.
            if intent_changed:
                import threading as _threading
                _threading.Thread(
                    target=_notify_founder_plan_intent,
                    args=(str(user.get("email") or ""), plan_name),
                    daemon=True,
                ).start()
            self._send_json({
                "ok": True,
                "plan": state,
                "message": "Plan intent recorded. Our team will contact you to activate your pilot.",
                "disclaimer": "No payment has been processed. Billing is manually activated for founding pilots.",
            })
        except ValueError as exc:
            self._send_json({"ok": False, "message": str(exc)}, 400)
        except Exception as exc:
            logger.error("plan_set failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_admin_accounts(self) -> None:
        """GET /api/admin/accounts — founder-only account roster (no secrets).

        Bounded, read-only. Every field is operational (email, verification,
        plan intent vs. activated tier, telegram-linked bool, created_at); no
        password hash, session id, or raw token is ever returned.
        """
        if self._rate_limited(_ADMIN_LIMITER, "admin_accounts"):
            return
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if not self._admin_guard(user):
            return
        try:
            from app.plan import list_accounts_admin

            params = parse_qs(urlparse(self.path).query)
            try:
                limit = int((params.get("limit") or ["100"])[0])
            except (TypeError, ValueError):
                limit = 100
            try:
                offset = int((params.get("offset") or ["0"])[0])
            except (TypeError, ValueError):
                offset = 0
            accounts = list_accounts_admin(limit=limit, offset=offset)
            self._send_json({"ok": True, "accounts": accounts, "count": len(accounts)})
        except Exception as exc:
            logger.error("admin_accounts failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_admin_activate_plan(self) -> None:
        """POST /api/admin/activate-plan — founder activates/changes a customer plan.

        Body: ``{user_id | email, plan_name}``. Grants a BILLING TIER only — it
        calls ``app.plan.activate_plan`` (which sets the ``activated_plan`` column)
        and NEVER touches org membership / RBAC roles, so it cannot escalate a
        caller (or anyone) to owner/operator. Founder-gated (``_admin_guard``);
        the activation is written to the immutable access log with the target and
        the tier. Returns the new plan state (no secrets).
        """
        if self._rate_limited(_ADMIN_LIMITER, "admin_activate_plan"):
            return
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        # Identity + role gate BEFORE reading the body or touching any target, so a
        # non-founder never learns whether a target exists.
        if not self._admin_guard(user):
            return
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return

        from app.plan import PLAN_NAMES, activate_plan

        plan_name = str(body.get("plan_name", "")).strip()
        if plan_name not in PLAN_NAMES:
            self._send_json({"ok": False, "message": f"Unknown plan: {plan_name}"}, 400)
            return

        # Resolve the target by explicit id, else by email. Only ONE tenant is
        # ever touched, chosen by the founder — no IDOR: a non-founder never
        # reaches this point (blocked by _admin_guard above).
        target = None
        raw_uid = body.get("user_id")
        raw_email = body.get("email")
        if raw_uid is not None and str(raw_uid).strip() != "":
            try:
                target = get_user_by_id(int(raw_uid))
            except (TypeError, ValueError):
                target = None
        elif raw_email:
            target = get_user_by_email(str(raw_email))

        if not target:
            self._send_json({"ok": False, "message": "No such account."}, 400)
            return

        target_id = int(target["id"])
        try:
            state = activate_plan(target_id, plan_name)
        except ValueError as exc:
            self._send_json({"ok": False, "message": str(exc)}, 400)
            return
        except Exception as exc:
            logger.error("admin_activate_plan failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)
            return

        # Record WHO activated WHOM to WHAT, WHEN — a specific, immutable audit row
        # beyond the generic plan.admin allow logged by _admin_guard.
        rbac_runtime.log_sensitive_action(
            user,
            rbac_runtime.PLAN_ADMIN,
            result=rbac_runtime.RESULT_ALLOW,
            resource_type="plan",
            resource_id=f"user:{target_id}->{plan_name}",
        )
        self._send_json({
            "ok": True,
            "account": {
                "id": target_id,
                "email": target.get("email"),
                "activated_plan": state.get("active_plan_name"),
            },
            "plan": state,
            "message": f"Activated {state.get('active_plan_display', plan_name)} for {target.get('email')}.",
        })

    def _handle_stripe_webhook(self) -> None:
        """POST /api/stripe/webhook — payment → plan entitlement automation.

        UNAUTHENTICATED at the HTTP layer BY DESIGN (Stripe, not a logged-in user,
        calls it), but SECURED by Stripe signature verification over the RAW body
        — never by session auth. This is the ONLY self-service path to
        ``app.plan.activate_plan``; it reuses that founder-only activation rather
        than forking entitlement logic.

        The raw bytes are read BEFORE any JSON parse (the signature is computed
        over them). All verification, idempotency, price→plan mapping, user
        resolution, activation, and audit live in ``app.stripe_webhook`` — this
        handler only marshals the HTTP request/response. A missing/invalid
        signature yields 400 and activates nothing; a verified event is
        acknowledged with 200 whether or not it resulted in an activation, so
        Stripe never enters a retry loop on a benign (unknown-price / unresolved-
        user) event.
        """
        if self._rate_limited(_STRIPE_WEBHOOK_LIMITER, "stripe_webhook"):
            return
        payload = self._read_raw_body()
        if payload is None:  # 413 already emitted by _read_raw_body
            return
        sig_header = self.headers.get("Stripe-Signature", "")
        try:
            from app.stripe_webhook import handle_webhook

            status, body = handle_webhook(payload, sig_header)
        except Exception as exc:  # noqa: BLE001 — never leak internals to Stripe
            logger.error("stripe webhook handler failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "error": "Internal server error."}, 500)
            return
        self._send_json(body, status)
