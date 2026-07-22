"""Per-alert review-workflow request handlers, extracted from ``app.api``.

This module holds one cohesive slice of the HTTP surface — the per-alert action
log (get/post), the per-alert review checklist (get/add/update), the sealed
redline read view, and the sealed decision log (get/post) — as a mixin that
``app.api._Handler`` inherits. The method bodies are byte-identical to their
former inline definitions; only their host class/file changed.

Names the moved bodies read as bare globals are imported here FROM ``app.api``
so they are the SAME objects the rest of the handler uses (and so tests that
monkeypatch ``app.api_alerts.<name>`` steer these methods exactly as they
previously steered ``app.api.<name>``). The function-local import inside a body
(``from app.sealed_redline import build_redline_for_match``) resolves at call
time against its source module. Shared per-request helpers (``_send_json``,
``_rate_limited``, ``_rbac_guard``, ``_read_json_strict``) stay on ``_Handler``
and are reached through ``self``.
"""
from __future__ import annotations

from app.api import (
    CHECKLIST_FRAMING,
    DECISION_FRAMING,
    DECISION_KINDS,
    DECISION_MAX_NAME_LEN,
    DECISION_MAX_REASON_LEN,
    DECISION_MAX_STATEMENT_LEN,
    _CHECKLIST_LIMITER,
    _DECISION_LIMITER,
    _REDLINE_LIMITER,
    _official_alert_blocked_by_plan,
    add_checklist_item,
    checklist_valid_alert_id,
    delete_checklist_item,
    find_routing_match_for_user,
    get_action_log,
    list_checklist_items,
    list_decisions,
    logger,
    parse_qs,
    rbac_runtime,
    read_decision_head,
    redact_decision_reviewed_for_plan,
    require_auth,
    save_action_log_entry,
    seal_decision,
    update_checklist_item,
    urlparse,
)


class _AlertsHandlerMixin:
    """Per-alert review-workflow request handlers for ``_Handler``."""

    def _handle_alert_action_log_get(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        alert_id = str((params.get("alert_id") or [""])[0]).strip()
        if not alert_id:
            self._send_json({"ok": False, "message": "alert_id required."}, 400)
            return
        entries = get_action_log(int(user["id"]), alert_id)
        self._send_json({"ok": True, "entries": entries})

    def _handle_alert_action_log_post(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        # RBAC Stage-2: recording an act/monitor/no_action review decision is a
        # review write. Owner passes; a read-only auditor seat is denied 403.
        if not self._rbac_guard(user, rbac_runtime.REVIEW_SUBMIT, resource_type="review"):
            return
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        alert_id = str(body.get("alert_id", "")).strip()
        decision = str(body.get("decision", "")).strip()
        notes = str(body.get("notes", "")).strip()[:2000]
        reviewer_name = str(body.get("reviewer_name", "")).strip()[:200]
        if not alert_id:
            self._send_json({"ok": False, "message": "alert_id required."}, 400)
            return
        if decision not in ("act", "monitor", "no_action"):
            self._send_json({"ok": False, "message": "decision must be act, monitor, or no_action."}, 400)
            return
        result = save_action_log_entry(int(user["id"]), alert_id, decision, notes, reviewer_name)
        if result is None:
            self._send_json({"ok": False, "message": "Could not save action log entry."}, 500)
            return
        self._send_json({"ok": True, "entry": result}, 201)

    # ── Per-alert review checklist (obligation-workflow v1) ─────────────────────
    # The user's OWN review to-do list for an alert. Owner-scoped end to end:
    # every handler passes int(user["id"]) as the owner, and the module filters
    # every query on owner_user_id so a user can never read or mutate another
    # user's items (a cross-user id resolves to 404, no oracle). The item text is
    # the USER'S words — StatuteProof never authors an action here; only the
    # returned FRAMING block is StatuteProof copy, and it is forbidden-claims
    # guarded (see tests/test_action_checklist.py).

    def _handle_alert_checklist_get(self) -> None:
        if self._rate_limited(_CHECKLIST_LIMITER, "alert_checklist_get"):
            return
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        alert_id = str((params.get("alert_id") or [""])[0]).strip()
        if not checklist_valid_alert_id(alert_id):
            self._send_json({"ok": False, "message": "Invalid alert_id."}, 400)
            return
        items = list_checklist_items(int(user["id"]), alert_id)
        self._send_json({"ok": True, "items": items, "framing": CHECKLIST_FRAMING})

    def _handle_alert_checklist_add(self) -> None:
        if self._rate_limited(_CHECKLIST_LIMITER, "alert_checklist_add"):
            return
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        # RBAC Stage-2: authoring a review action is a review write. Owner passes;
        # a read-only auditor seat is denied 403. No-op for accounts today.
        if not self._rbac_guard(user, rbac_runtime.REVIEW_SUBMIT, resource_type="checklist"):
            return
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        alert_id = str(body.get("alert_id", "")).strip()
        if not checklist_valid_alert_id(alert_id):
            self._send_json({"ok": False, "message": "Invalid alert_id."}, 400)
            return
        # `or ""` (not the get() default) so an explicit JSON null coerces to ""
        # rather than the string "None" — matching the str(x or "") guard used for
        # every other nullable body field in this file.
        text = str(body.get("text") or "").strip()
        if not text:
            self._send_json({"ok": False, "message": "A review action is required."}, 400)
            return
        assignee = str(body.get("assignee") or "")
        due_date = str(body.get("due_date") or "")
        item = add_checklist_item(int(user["id"]), alert_id, text, assignee, due_date)
        if item is None:
            self._send_json(
                {
                    "ok": False,
                    "message": "Could not add the review action. This alert's checklist may be full.",
                },
                400,
            )
            return
        self._send_json({"ok": True, "item": item}, 201)

    def _handle_alert_checklist_update(self) -> None:
        """Update / toggle / delete one of the caller's OWN checklist items.

        A single mutating endpoint: ``delete: true`` removes the item; otherwise
        the provided fields (``status`` to tick, ``text`` / ``assignee`` /
        ``due_date`` to edit) are updated. Owner-scoped in the module; a
        cross-user or absent id returns 404 with no existence oracle.
        """
        if self._rate_limited(_CHECKLIST_LIMITER, "alert_checklist_update"):
            return
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if not self._rbac_guard(user, rbac_runtime.REVIEW_SUBMIT, resource_type="checklist"):
            return
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        try:
            item_id = int(body.get("item_id"))
        except (TypeError, ValueError):
            self._send_json({"ok": False, "message": "Invalid item_id."}, 400)
            return

        if body.get("delete") is True:
            if delete_checklist_item(int(user["id"]), item_id):
                self._send_json({"ok": True, "deleted": item_id})
                return
            self._send_json({"ok": False, "message": "Checklist item not found."}, 404)
            return

        # Only pass through fields the caller actually supplied so an update
        # touches nothing else (immutable-by-omission).
        kwargs: dict = {}
        if "status" in body:
            kwargs["status"] = body.get("status")
        if "text" in body:
            kwargs["text"] = body.get("text")
        if "assignee" in body:
            kwargs["assignee"] = body.get("assignee")
        if "due_date" in body:
            kwargs["due_date"] = body.get("due_date")
        if not kwargs:
            self._send_json({"ok": False, "message": "Nothing to update."}, 400)
            return
        item = update_checklist_item(int(user["id"]), item_id, **kwargs)
        if item is None:
            # Ambiguous between "not yours / gone" and "invalid field" by design —
            # 404 gives no oracle for a cross-user probe. A bad status is the only
            # value-level rejection, but conflating it here keeps the surface tight.
            self._send_json({"ok": False, "message": "Checklist item not found."}, 404)
            return
        self._send_json({"ok": True, "item": item})

    # ── Sealed-evidence redline (read-only monitoring view) ─────────────────────
    #
    # Renders the added/removed text of ONE alert's SEALED diff artifact as
    # structured redline blocks. Tenancy rides the SAME owner-scoped loader the
    # alerts page's preview is built from: find_routing_match_for_user applies
    # the identical deny-list + approved-review gate but normalizes ONLY the
    # target candidate — a per-click fetch never re-scores the whole draft
    # corpus (security review 2026-07-12). An alert outside the caller's scope
    # simply isn't found — identical 404 for "not yours" and "gone", no oracle.
    # The redline module itself adds no scope (see app/sealed_redline.py); it
    # renders only what the match's proof block points to.

    def _handle_alert_redline_get(self) -> None:
        if self._rate_limited(_REDLINE_LIMITER, "alert_redline_get"):
            return
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        alert_id = str((params.get("alert_id") or [""])[0]).strip()
        if not checklist_valid_alert_id(alert_id):
            self._send_json({"ok": False, "message": "Invalid alert_id."}, 400)
            return
        try:
            days = int((params.get("days") or ["14"])[0])
        except (TypeError, ValueError):
            days = 14
        try:
            from app.sealed_redline import build_redline_for_match

            match = find_routing_match_for_user(int(user["id"]), alert_id, days=days)
            if match is None:
                self._send_json({"ok": False, "message": "Alert not found."}, 404)
                return
            # The redline IS the paid official-source deliverable (the sealed
            # added/removed text). Redacting the preview alone would be
            # worthless: the redacted preview still carries every alert_id, so
            # the diff would be one GET away. Same flag, same eligibility
            # helper as delivery — own custom sources stay visible.
            if _official_alert_blocked_by_plan(int(user["id"]), match.get("source_id")):
                self._send_json({
                    "ok": False,
                    "message": "Official-source alert content requires an active plan.",
                    "reason": "plan_required",
                }, 402)
                return
            redline = build_redline_for_match(match)
            self._send_json({"ok": True, "redline": redline})
        except Exception as exc:
            logger.error("Alert redline failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    # ── Sealed decision log (individual-accountability sign-off, Stage 2) ────────
    #
    # A reviewer's OWN decision for one alert, sealed IN THEIR OWN WORDS into the
    # org's append-only hash chain (app/decision_records.py). StatuteProof never
    # prescribes, suggests, scores, or assesses the decision — the only app-
    # authored copy is DECISION_FRAMING, forbidden-claims guarded at import.
    # Tenancy: the org comes from the caller's resolved principal (never the
    # request body); the alert binding rides the SAME owner-scoped loader as the
    # redline (find_routing_match_for_user), so an alert outside the caller's
    # scope is an identical 404 for "not yours" and "gone" — no oracle.
    # RBAC: sealing (POST) requires review.submit; listing (GET) deliberately
    # does NOT — an auditor seat is read-only but MUST be able to read the log.

    def _handle_alert_decisions_get(self) -> None:
        if self._rate_limited(_DECISION_LIMITER, "alert_decisions_get"):
            return
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        alert_id = str((params.get("alert_id") or [""])[0]).strip()
        if not checklist_valid_alert_id(alert_id):
            self._send_json({"ok": False, "message": "Invalid alert_id."}, 400)
            return
        try:
            principal = rbac_runtime.resolve_principal(user)
            if principal.org_id is None:
                # A user with no resolvable org has no decision chain yet — an
                # honest empty list, not an error (read path stays fail-soft).
                self._send_json({
                    "ok": True,
                    "decisions": [],
                    "framing": DECISION_FRAMING,
                    "kinds": list(DECISION_KINDS),
                    "chain": None,
                })
                return
            org_id = int(principal.org_id)
            self._send_json({
                "ok": True,
                "decisions": list_decisions(org_id, alert_id),
                "framing": DECISION_FRAMING,
                "kinds": list(DECISION_KINDS),
                "chain": read_decision_head(org_id),
            })
        except Exception as exc:
            logger.error("Alert decisions list failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_alert_decisions_post(self) -> None:
        """Seal ONE user-authored decision for an alert into the org chain.

        Order matters: auth → rate limit → RBAC (review.submit) → validate →
        owner-scoped alert resolution (404, no oracle) → evidence binding
        (409 when the alert carries no sealed proof block) → seal. The user's
        ``statement`` / ``amendment_reason`` are passed through VERBATIM — never
        guarded, rewritten, or truncated; oversize input is rejected with an
        honest message so nothing the user did not write is ever sealed.

        This is a thin orchestrator: field validation lives in
        ``_decision_validate_body``, the evidence-bound seal in ``_decision_seal``.
        """
        if self._rate_limited(_DECISION_LIMITER, "alert_decisions_seal"):
            return
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        # RBAC Stage-2: sealing a decision is a review write. Owner passes; a
        # read-only auditor seat is denied 403 (it may still GET the list).
        if not self._rbac_guard(user, rbac_runtime.REVIEW_SUBMIT, resource_type="decision"):
            return
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        params, param_error = self._decision_validate_body(body)
        if param_error is not None:
            message, status = param_error
            self._send_json({"ok": False, "message": message}, status)
            return
        try:
            self._decision_seal(user, body, params)
        except Exception as exc:
            logger.error("Alert decision seal failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _decision_validate_body(self, body):
        """Validate the decision request body.

        Returns ``(params, None)`` on success, or ``(None, (message, status))``
        with the exact rejection to surface — no response is sent here. The
        user's ``statement`` / ``amendment_reason`` are rejected (never
        truncated) when oversize so nothing they did not write is ever sealed.
        """
        alert_id = str(body.get("alert_id", "")).strip()
        if not checklist_valid_alert_id(alert_id):
            return None, ("Invalid alert_id.", 400)
        kind = str(body.get("kind") or "").strip()
        if kind not in DECISION_KINDS:
            return None, ("Invalid decision kind.", 400)
        statement = body.get("statement")
        if not isinstance(statement, str) or not statement.strip():
            return None, ("A decision statement is required.", 400)
        if len(statement) > DECISION_MAX_STATEMENT_LEN:
            # REJECT, never truncate — these are the user's sealed words.
            return None, (
                f"The statement is longer than the {DECISION_MAX_STATEMENT_LEN}-character "
                "limit. It is sealed exactly as written, so nothing was recorded — "
                "please shorten it and try again.",
                400,
            )
        supersedes = str(body.get("supersedes_decision_id") or "").strip()
        amendment_reason = body.get("amendment_reason")
        amendment = "" if amendment_reason is None else amendment_reason
        if not isinstance(amendment, str):
            return None, ("The correction reason must be text.", 400)
        if len(amendment) > DECISION_MAX_REASON_LEN:
            return None, (
                f"The correction reason is longer than the {DECISION_MAX_REASON_LEN}-character "
                "limit. It is sealed exactly as written, so nothing was recorded — "
                "please shorten it and try again.",
                400,
            )
        if bool(supersedes) != bool(amendment.strip()):
            return None, (
                "A correction needs both the earlier decision and your reason "
                "for correcting it.",
                400,
            )
        try:
            days = int(body.get("days") or 14)
        except (TypeError, ValueError):
            days = 14
        params = {
            "alert_id": alert_id,
            "kind": kind,
            "statement": statement,
            "supersedes": supersedes,
            "amendment": amendment,
            "days": days,
        }
        return params, None

    def _decision_resolve_reviewed(self, user, alert_id, days):
        """Resolve "what the user saw" for an owner-scoped alert.

        Returns ``(reviewed, None)`` — the alert's sealed proof block plus its
        identity fields, plan-redacted — or ``(None, (message, status))`` for a
        404 (no owner-scoped alert; no cross-org oracle) or 409 (the alert
        carries no sealed evidence to bind to). Exceptions propagate to the
        caller's handler so a storage failure still becomes a 500.
        """
        match = find_routing_match_for_user(int(user["id"]), alert_id, days=days)
        if match is None:
            return None, ("Alert not found.", 404)
        proof = match.get("proof")
        if not isinstance(proof, dict) or not proof:
            return None, (
                "This alert has no sealed evidence record to bind a decision to.",
                409,
            )
        # "What they saw": the alert's proof block verbatim, plus the alert /
        # source identity fields the design binds into content.reviewed.
        reviewed = dict(proof)
        reviewed["alert_id"] = alert_id
        reviewed["source_id"] = str(match.get("source_id") or "")
        reviewed["source_name"] = str(match.get("source_name") or "")
        reviewed["official_url"] = str(match.get("source_url") or "")
        # Entitlement: the sealed record is returned to the caller, so this
        # echoed field must obey the SAME boundary as every other reader of
        # official-source content — one choke point, not a local re-decision.
        # Empty is already a legitimate value here; the evidence_record_id +
        # record_hash still identify exactly what was reviewed.
        reviewed = redact_decision_reviewed_for_plan(
            int(user["id"]), reviewed, match.get("source_id")
        )
        return reviewed, None

    def _decision_seal(self, user, body, params) -> None:
        """Bind the validated decision to sealed evidence and seal it.

        Sends the terminal response for every outcome: 400 (workspace
        unresolved / fail-soft seal failure), 404/409 (from evidence binding),
        or 201 with the sealed record. Runs inside the caller's try/except so
        an unexpected failure still becomes a 500.
        """
        principal = rbac_runtime.resolve_principal(user)
        if principal.org_id is None:
            self._send_json(
                {"ok": False, "message": "Your workspace could not be resolved. Please retry."},
                400,
            )
            return
        reviewed, reviewed_error = self._decision_resolve_reviewed(
            user, params["alert_id"], params["days"]
        )
        if reviewed_error is not None:
            message, status = reviewed_error
            self._send_json({"ok": False, "message": message}, status)
            return

        # Account metadata (not the user's sealed words) — bounded here so an
        # over-long profile name can never block a legitimate seal.
        display_name = (
            str(user.get("full_name") or "").strip()
            or str(user.get("email") or "").strip()
        )[:DECISION_MAX_NAME_LEN]

        record = seal_decision(
            int(user["id"]),
            int(principal.org_id),
            display_name=display_name,
            reviewed=reviewed,
            kind=params["kind"],
            statement=params["statement"],
            checklist_ref=body.get("checklist_ref"),
            supersedes_decision_id=params["supersedes"],
            amendment_reason=params["amendment"],
        )
        if record is None:
            # Fail-soft: covers a malformed checklist_ref, an unknown or
            # foreign supersedes id (same message — no cross-org oracle), or
            # a storage failure. Nothing was sealed.
            self._send_json(
                {
                    "ok": False,
                    "message": "The decision could not be sealed. Nothing was recorded — "
                    "check the entry and try again.",
                },
                400,
            )
            return
        self._send_json({"ok": True, "decision": record}, 201)
