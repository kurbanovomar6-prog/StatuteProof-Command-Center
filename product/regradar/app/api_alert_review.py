"""Founder-only alert release over HTTP — the gate that was SSH-only.

An alert draft stays unsent until ``app.alert_review.review_alert`` records an
``approve_weekly`` / ``approve_urgent`` decision. Until now the only way to
record one was ``run.py alert-review approve`` on the production box, so every
release required a shell.

This is deliberately NOT a customer feature. It is the editorial gate deciding
whether a drafted alert reaches customers at all, so it is founder-scoped
through the existing ``_admin_guard`` — the same gate the admin panel uses,
which fails closed, audits both outcomes, and runs before any target lookup so
it can never act as an existence oracle.

WHAT "APPROVE" MEANS HERE. Both approving actions make an alert eligible for
customer delivery, and the scheduler dispatches on its own
(``scheduler.run_digest_dispatch_pass`` runs every full cycle). "Weekly" is a
cadence, not a smaller blast radius: ``digest_cadence._is_instant`` routes on
``risk_level``/``score``, never on ``send_decision``, so approving a HIGH-risk
draft "for weekly" sends it INSTANTLY to every matched customer's Telegram.
Nothing in this module may describe approve_weekly as brief-only, and the queue
tells the operator which drafts will go out instantly.

Messages are recallable from nobody. Once dispatch logs a send, a later reject
cannot undo it — which is why the safety gate now covers both approving actions
(see ``alert_review.APPROVING_ACTIONS``) rather than urgent alone.
"""
from __future__ import annotations

import threading

from app.api import (
    _ADMIN_LIMITER,
    logger,
    parse_qs,
    rbac_runtime,
    require_auth,
    urlparse,
)

# review_alert reads a draft, rewrites it, then appends to the review jsonl with
# no lock of its own, and the API runs on a threading server — two clicks on the
# same alert genuinely interleave. This serializes them in-process. It does NOT
# cover the CLI or the scheduler's qa_gate running in another process; that
# race predates this endpoint and is called out in the axis report rather than
# papered over here.
_REVIEW_LOCK = threading.Lock()

_MAX_NOTE_CHARS = 2000
_MAX_ALERT_ID_CHARS = 200

# Supplying any of these would let the caller rewrite history or redirect the
# audit trail: `reviewer` is the whole point of the record, and base_dir /
# review_file are review_alert kwargs that choose which files get written.
_FORBIDDEN_BODY_FIELDS = ("reviewer", "base_dir", "review_file")


def _legal_actions() -> tuple[str, ...]:
    return (
        "approve_weekly",
        "approve_urgent",
        "reject",
        "needs_adapter",
        "needs_legal",
        "manual_review",
    )


class _AlertReviewHandlerMixin:
    def _alert_review_actor(self) -> dict | None:
        """Authenticate and confirm the founder gate. None means a reply was sent."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return None
        # Runs BEFORE the body is read and before any draft is looked up, so a
        # non-founder never learns whether an alert_id exists. _admin_guard
        # sends its own 403 and audits the denial; do not send a second reply.
        if not self._admin_guard(user):
            return None
        return user

    def _reviewer_name(self, user: dict) -> str:
        """The reviewer recorded in the immutable review record.

        Derived from the authenticated session, NEVER from the request body. The
        CLI takes --reviewer because a human types their own name at their own
        terminal; accepting it over HTTP would let anyone who reaches this
        endpoint write someone else's name into a permanent compliance record.
        """
        email = str((user or {}).get("email") or "").strip()
        return email or f"user:{(user or {}).get('id', '?')}"

    def _handle_admin_alert_review(self) -> None:
        """POST /api/admin/alert-review — record a release decision. Founder only.

        Body: ``{alert_id, action, note?, force?}``.
        """
        if self._rate_limited(_ADMIN_LIMITER, "admin_alert_review"):
            return
        user = self._alert_review_actor()
        if not user:
            return

        body, error = self._read_json_strict()
        if error or body is None:
            self._send_json({"ok": False, "message": error or "Invalid JSON."}, 400)
            return

        present = [f for f in _FORBIDDEN_BODY_FIELDS if f in body]
        if present:
            self._send_json({
                "ok": False,
                "code": "forbidden_field",
                "message": (
                    "reviewer is taken from your login and cannot be supplied; "
                    "base_dir and review_file are not accepted."
                ),
            }, 400)
            return

        alert_id = body.get("alert_id")
        if not isinstance(alert_id, str) or not alert_id.strip():
            self._send_json({"ok": False, "message": "alert_id is required."}, 400)
            return
        alert_id = alert_id.strip()
        if len(alert_id) > _MAX_ALERT_ID_CHARS:
            self._send_json({"ok": False, "message": "alert_id is too long."}, 400)
            return

        action = body.get("action")
        if action not in _legal_actions():
            # Rejected before review_alert is called, because every call rglobs
            # and parses the whole snapshot tree — a typo should not pay for that.
            self._send_json({
                "ok": False,
                "code": "unknown_action",
                "message": "Unknown review action.",
                "legal_actions": list(_legal_actions()),
            }, 400)
            return

        note = body.get("note", "")
        if note is None:
            note = ""
        if not isinstance(note, str):
            self._send_json({"ok": False, "message": "note must be text."}, 400)
            return
        if len(note) > _MAX_NOTE_CHARS:
            self._send_json({"ok": False, "message": "note is too long."}, 400)
            return

        force = body.get("force", False)
        # Strictly a JSON boolean: Python truthiness would read the string
        # "false" as True, turning a safety override into a typo.
        if not isinstance(force, bool):
            self._send_json({"ok": False, "message": "force must be true or false."}, 400)
            return

        from app.alert_review import ApprovalBlocked, review_alert

        reviewer = self._reviewer_name(user)
        try:
            with _REVIEW_LOCK:
                record = review_alert(
                    alert_id=alert_id,
                    action=action,
                    reviewer=reviewer,
                    note=note,
                    force=force,
                )
        except FileNotFoundError:
            self._send_json({
                "ok": False,
                "code": "not_found",
                "message": "Alert draft not found.",
            }, 404)
            return
        except ApprovalBlocked as blocked:
            # A state conflict, not a malformed request. The issues are returned
            # structured so the operator can decide with them in front of them
            # rather than re-deriving them from a message string.
            self._send_json({
                "ok": False,
                "code": "safety_blocked",
                "message": "Approval blocked by safety checks.",
                "safety_issues": blocked.safety_issues,
                "override_requires": "force=true with a review note explaining why",
            }, 409)
            return
        except ValueError as exc:
            self._send_json({
                "ok": False,
                "code": "note_required" if "note" in str(exc) else "invalid_request",
                "message": str(exc),
            }, 400)
            return
        except Exception as exc:  # noqa: BLE001 — never leak a traceback or a path
            logger.error("admin_alert_review failed: %s", type(exc).__name__)
            self._send_json({
                "ok": False,
                "message": (
                    "Internal error. The decision may or may not have been "
                    "recorded — reload the review queue before retrying."
                ),
            }, 500)
            return

        rbac_runtime.log_sensitive_action(
            user,
            rbac_runtime.REVIEW_APPROVE,
            result=rbac_runtime.RESULT_ALLOW,
            resource_type="alert",
            resource_id=f"{alert_id}->{action}" + ("|force" if force else ""),
        )
        logger.info(
            "alert review: %s -> %s by %s%s",
            alert_id, action, reviewer, " (forced)" if force else "",
        )

        self._send_json({
            "ok": True,
            # "recorded", never "sent": delivery is separately gated downstream
            # (_is_still_approved re-check, forbidden-claim veto, plan gating),
            # so a 200 here is a decision, not proof anything went out.
            "message": "Review decision recorded.",
            "record": _public_record(record),
        })

    def _handle_admin_alert_review_queue(self) -> None:
        """GET /api/admin/alert-review-queue — drafts awaiting a decision."""
        user = self._alert_review_actor()
        if not user:
            return

        params = parse_qs(urlparse(self.path).query)
        show_all = str((params.get("all") or ["0"])[0]).strip() in ("1", "true", "yes")

        from app.alert_review import (
            approval_safety_issues,
            latest_review_for,
            list_alert_drafts,
        )

        try:
            drafts = list_alert_drafts()
        except Exception as exc:  # noqa: BLE001 — an unreadable tree is not a crash
            logger.error("alert review queue failed: %s", type(exc).__name__)
            self._send_json(
                {"ok": False, "message": "Could not read the review queue."}, 500
            )
            return

        rows = []
        for draft in drafts:
            alert_id = str(draft.get("alert_id") or "")
            if not alert_id:
                continue
            # jsonl-first, exactly like the delivery code resolves status — if the
            # queue and the release logic disagreed, the operator would be acting
            # on a status that is not the one gating delivery.
            latest = latest_review_for(alert_id) or {}
            status = str(latest.get("new_status") or draft.get("review_status") or "DRAFT")
            if not show_all and status.startswith("APPROVED"):
                continue
            try:
                issues = approval_safety_issues(draft)
            except Exception:  # noqa: BLE001 — one bad draft must not blank the queue
                issues = ["safety checks could not be evaluated"]
            rows.append({
                "alert_id": alert_id,
                "source_id": draft.get("source_id"),
                "source_name": draft.get("source_name"),
                "checked_at_utc": draft.get("checked_at_utc"),
                "risk_level": draft.get("risk_level"),
                "confidence": draft.get("confidence"),
                "status": status,
                "safety_issues": issues,
                # The blast radius, computed the way digest_cadence computes it,
                # so the operator sees it BEFORE clicking rather than after.
                "delivery_if_approved": _delivery_consequence(draft),
                "last_review": {
                    "reviewer": latest.get("reviewer"),
                    "action": latest.get("new_status"),
                    "reviewed_at_utc": latest.get("reviewed_at_utc"),
                    "force": latest.get("force"),
                } if latest else None,
            })

        self._send_json({"ok": True, "alerts": rows, "count": len(rows)})


def _delivery_consequence(draft: dict) -> str:
    """What approving this draft actually does, in the operator's words.

    Mirrors digest_cadence._is_instant, which keys on risk_level — NOT on the
    weekly/urgent choice. Saying "weekly brief only" here would be false for
    exactly the drafts where being wrong costs the most.
    """
    risk = str(draft.get("risk_level") or "").strip().upper()
    if risk == "HIGH":
        return "instant Telegram to every matched customer on the next cycle"
    return "bundled into matched customers' daily/weekly digests"


def _public_record(record: dict) -> dict:
    """The review record minus server filesystem paths."""
    hidden = {"alert_draft_path", "proof_path", "diff_path"}
    return {k: v for k, v in (record or {}).items() if k not in hidden}
