"""Public-verify, evidence-room share, profile, account-export, and delivery
request handlers, extracted from ``app.api``.

One cohesive slice of the HTTP surface — the PUBLIC unauthenticated verify
endpoint and its machine-readable spec, the public Auditor Evidence Room view,
the evidence-room share lifecycle (create / list / revoke), the profile
get/update, the account data export, and the delivery handlers (test brief,
logs, preview, send-preview-alert, email test-mode/status/config-check) — as a
mixin that ``app.api._Handler`` inherits. The method bodies are byte-identical
to their former inline definitions; only their host class/file changed.

Bare module globals the moved bodies read are imported here FROM ``app.api`` so
they are the SAME objects the rest of the handler uses (and so tests that
monkeypatch ``app.api_account.<name>`` steer these methods exactly as they
previously steered ``app.api.<name>``). Shared per-request helpers (``_send_json``,
``_rate_limited``, ``_client_ip``, ``_public_base_url``, ``_rbac_guard`` …) stay on
``_Handler`` and are reached through ``self``. Function-local imports inside
bodies resolve at call time against their source modules.
"""
from __future__ import annotations

from app.api import (
    _ACCOUNT_EXPORT_LIMITER,
    _DELIVERY_SEND_PREVIEW_LIMITER,
    _DELIVERY_TEST_BRIEF_LIMITER,
    _EXPORT_LIMITER,
    _ROOM_LIMITER,
    _VERIFY_LIMITER,
    build_account_export,
    build_routing_preview_for_user,
    datetime,
    get_or_create_profile,
    get_user_delivery_logs,
    json,
    logger,
    parse_qs,
    rbac_runtime,
    re,
    redact_preview_for_plan,
    require_auth,
    send_preview_alert_to_user,
    send_sample_brief_to_user,
    timezone,
    update_profile,
    urlparse,
    verify_submission,
)


class _AccountHandlerMixin:
    def _handle_public_verify(self) -> None:
        """POST /api/verify — PUBLIC, no auth.

        Stateless integrity check of a caller-submitted evidence record. This is
        the no-login moat: it verifies the bytes the CALLER holds and never reads
        the server's evidence/ tree, so it requires trusting neither a login nor
        StatuteProof. Body:
        ``{"record": {...}, "raw"?: str, "normalized"?: str, "diff"?: str}``.
        A submitted ``diff`` is checked against the record's sealed ``diff_hash``
        (skipped for legacy records that predate it).
        Fail-closed: malformed input returns a clear 400, never a 500 stacktrace.
        """
        # Cheap but unauthenticated — cap per client IP.
        if self._rate_limited(_VERIFY_LIMITER, "public_verify"):
            return

        # _read_json_strict enforces the shared Content-Length body cap (413) and
        # rejects non-object / invalid JSON bodies.
        body, error = self._read_json_strict()
        if error is not None:
            self._send_json({"ok": False, "error": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "error": "Request body required."}, 400)
            return

        if "record" not in body or body.get("record") is None:
            self._send_json({"ok": False, "error": "A 'record' object is required."}, 400)
            return
        raw = body.get("raw")
        normalized = body.get("normalized")
        diff = body.get("diff")
        if raw is not None and not isinstance(raw, str):
            self._send_json({"ok": False, "error": "'raw' must be a string if provided."}, 400)
            return
        if normalized is not None and not isinstance(normalized, str):
            self._send_json({"ok": False, "error": "'normalized' must be a string if provided."}, 400)
            return
        if diff is not None and not isinstance(diff, str):
            self._send_json({"ok": False, "error": "'diff' must be a string if provided."}, 400)
            return
        timestamp_token = body.get("timestamp_token")
        timestamp_digest = body.get("timestamp_digest")
        if timestamp_token is not None and not isinstance(timestamp_token, str):
            self._send_json({"ok": False, "error": "'timestamp_token' must be a base64 string if provided."}, 400)
            return
        if timestamp_digest is not None and not isinstance(timestamp_digest, str):
            self._send_json({"ok": False, "error": "'timestamp_digest' must be a string if provided."}, 400)
            return

        # verify_submission never raises; a malformed record surfaces as failed
        # checks (verified: false), not a server error.
        result = verify_submission(
            body.get("record"),
            raw=raw,
            normalized=normalized,
            diff=diff,
            timestamp_token=timestamp_token,
            timestamp_digest=timestamp_digest,
        )
        self._send_json(result, 200)

    def _handle_verify_spec(self) -> None:
        """GET /api/verify-spec — PUBLIC, no auth.

        Serve the open verification specification (docs/EVIDENCE-VERIFICATION-SPEC.md)
        so anyone can read the exact method the verifier implements without a login
        or a StatuteProof code checkout. Static internal doc; no user data.
        """
        from pathlib import Path as _Path

        spec_path = _Path(__file__).resolve().parent.parent / "docs" / "EVIDENCE-VERIFICATION-SPEC.md"
        try:
            body = spec_path.read_bytes()
        except OSError:
            self._send_json({"ok": False, "error": "Specification is not available."}, 404)
            return
        self._send_bytes(body, "text/markdown; charset=utf-8")

    # ── Auditor Evidence Room ──────────────────────────────────────────────────

    def _handle_room_view(self, token: str) -> None:
        """GET /api/room/<token> — PUBLIC, no auth, READ-ONLY.

        The external examiner's view of a share an owner created. There is no
        session (the auditor has no account); the token IS the credential and is
        resolved fail-closed in ``app.evidence_room.get_room_view``: only the
        SHA-256 of the token is stored, the compare is constant-time, and the
        response contains ONLY the scope frozen at creation. Unknown, revoked,
        expired, and malformed tokens all produce the SAME 404 envelope — no
        existence oracle. Rate-limited per client IP (mirrors /api/verify).
        Every resolution is appended to the immutable access log as
        ``room.view`` inside the module. No mutation happens on this path.
        """
        if self._rate_limited(_ROOM_LIMITER, "room_view"):
            return
        from app.evidence_room import get_room_view

        view = get_room_view(token)
        if view is None:
            self._send_json(
                {
                    "ok": False,
                    "error": "not_found",
                    "message": (
                        "This evidence room link is not available. "
                        "It may have expired or been revoked."
                    ),
                },
                404,
            )
            return
        self._send_json({"ok": True, "room": view}, 200)

    def _handle_evidence_room_share_create(self) -> None:
        """POST /api/evidence-room/shares — create a time-boxed external share.

        Mirrors the export-handler discipline: require_auth → rate limit → strict
        body → RBAC governance gate (``evidence.share`` — owner/admin only; a
        reviewer/approver/auditor seat is denied 403 and the decision is written
        to the immutable access log) → plan capability (``audit_export``) →
        module call. ``create_share`` validates, entitlement-clips (tenancy +
        plan), bounds, and freezes the scope; the raw token in the 201 response
        is the ONLY time it ever exists server-side outside a hash.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_EXPORT_LIMITER, "evidence_room_share_create"):
            return
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        # fail_closed: minting an external evidence-room credential is a governance
        # action — if RBAC evaluation errors we DENY, never mint on a plumbing glitch.
        if not self._rbac_guard(
            user, rbac_runtime.EVIDENCE_SHARE, resource_type="evidence_share", fail_closed=True
        ):
            return
        if not self._require_capability(user, "audit_export"):
            return
        from app.evidence_room import create_share

        result = create_share(
            user,
            body.get("source_ids"),
            str(body.get("date_from") or "").strip(),
            str(body.get("date_to") or "").strip(),
            expires_days=body.get("expires_days"),
            org_display_name=str(body.get("org_display_name") or ""),
        )
        if result.get("ok"):
            self._send_json(result, 201)
            return
        status = {
            "invalid": 400,
            "invalid_expiry": 400,
            "forbidden_claim": 400,
            "no_entitled_sources": 403,
            "forbidden": 403,
            "too_large": 413,
        }.get(str(result.get("error")), 500)
        # The module's failure messages are authored-safe (no internal detail),
        # so the envelope is forwarded as-is.
        self._send_json(result, status)

    def _handle_evidence_room_shares_list(self) -> None:
        """GET /api/evidence-room/shares — the caller's OWN shares, metadata only.

        Never includes a token or token hash — a listed share cannot be turned
        back into a usable link. Auth-scoped to the owner inside the module.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_EXPORT_LIMITER, "evidence_room_shares_list"):
            return
        from app.evidence_room import list_shares

        result = list_shares(user)
        self._send_json(result, 200 if result.get("ok") else 500)

    def _handle_evidence_room_share_revoke(self) -> None:
        """POST /api/evidence-room/shares/revoke — kill a share immediately.

        Owner-scoped inside the module: a share the caller does not own resolves
        exactly like one that does not exist (404 — no existence oracle). Gated
        on the same ``evidence.share`` governance action as creation, so the
        RBAC decision lands in the immutable access log with the share id.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_EXPORT_LIMITER, "evidence_room_share_revoke"):
            return
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        share_id = body.get("share_id")
        if not self._rbac_guard(
            user,
            rbac_runtime.EVIDENCE_SHARE,
            resource_type="evidence_share",
            resource_id=str(share_id or "")[:64],
            fail_closed=True,
        ):
            return
        from app.evidence_room import revoke_share

        result = revoke_share(user, share_id)
        if result.get("ok"):
            self._send_json(result, 200)
            return
        status = 404 if result.get("error") == "not_found" else 500
        self._send_json(result, status)

    def _handle_profile_get(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            profile = get_or_create_profile(
                int(user["id"]),
                seed={
                    "company_name": user.get("company_name"),
                    "industry": user.get("industry"),
                },
            )
            self._send_json({"ok": True, "profile": profile})
        except Exception as exc:
            logger.error("Profile load failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_profile_update(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        # RBAC Stage-2: a settings mutation. Owner (every existing user) passes;
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

        try:
            profile = update_profile(int(user["id"]), body)
            self._send_json({"ok": True, "profile": profile})
        except ValueError as exc:
            self._send_json({"ok": False, "message": str(exc)}, 400)
        except Exception as exc:
            logger.error("Profile update failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    # ── Self-service account data export (exit portability, vendor-DD Q25) ───────

    def _handle_account_export(self) -> None:
        """Everything the CALLER owns, in one JSON attachment download.

        Order: auth → rate limit → gather → attachment. Owner/org scoping on
        EVERY read: account / profile / checklist / telegram rows are keyed by
        the session user id; sealed decision records come from the caller's
        RESOLVED org principal — never from request input (see
        app.account_export). RBAC: deliberately NO role gate — this is a read
        of the caller's own data, so a read-only auditor seat may export its
        own org view; the authorized export is still recorded in the immutable
        access log. The export NEVER contains the password hash, session ids,
        pairing codes, or verification tokens: every section is an explicit
        field list (asserted by tests/test_account_export.py).
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_ACCOUNT_EXPORT_LIMITER, "account_export"):
            return
        try:
            try:
                principal = rbac_runtime.resolve_principal(user)
                org_id = principal.org_id
            except Exception:  # noqa: BLE001 — no resolvable org is an empty decisions section, not a failure
                org_id = None
            export = build_account_export(user, org_id)
            body = json.dumps(export, ensure_ascii=False, indent=2).encode("utf-8")
            stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
            filename = f"statuteproof-account-export-{stamp}.json"
            # Immutable audit row with the TRUTHFUL action name (not the
            # evidence.export label _rbac_log_export would write). Additive
            # observation only — log_sensitive_action swallows its own errors.
            rbac_runtime.log_sensitive_action(
                user,
                "account.export",
                result=rbac_runtime.RESULT_ALLOW,
                resource_type="account",
                resource_id="",
            )
            self._send_bytes(
                body,
                "application/json; charset=utf-8",
                extra_headers=[
                    ("Content-Disposition", f'attachment; filename="{filename}"'),
                ],
            )
        except Exception as exc:
            logger.error("Account export failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_delivery_test_brief(self) -> None:
        if self._rate_limited(_DELIVERY_TEST_BRIEF_LIMITER, "delivery_test_brief"):
            return

        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            result = send_sample_brief_to_user(int(user["id"]))
            if result.get("ok"):
                self._send_json({
                    "ok": True,
                    "message": result.get("message", "Sample brief sent to your Telegram."),
                    "log_id": result.get("log_id"),
                })
                return

            reason = result.get("reason", "Delivery failed.")
            if reason == "Sample brief already sent today.":
                self._send_json(
                    {"ok": False, "message": reason, "reason": "already_sent_today"},
                    429,
                )
            elif reason == "Telegram not connected.":
                self._send_json(
                    {
                        "ok": False,
                        "message": "Telegram not connected. Pair your account first.",
                        "reason": "no_telegram",
                    },
                    400,
                )
            elif reason == "Telegram alerts are disabled.":
                self._send_json(
                    {
                        "ok": False,
                        "message": "Telegram alerts are disabled. Enable Telegram alerts in Settings.",
                        "reason": "telegram_disabled",
                    },
                    400,
                )
            elif reason == "Onboarding is not complete.":
                self._send_json(
                    {
                        "ok": False,
                        "message": "Complete onboarding before sending a sample brief.",
                        "reason": "onboarding_incomplete",
                    },
                    400,
                )
            else:
                self._send_json(
                    {
                        "ok": False,
                        "message": reason,
                        "reason": "delivery_failed",
                    },
                    502,
                )
        except Exception as exc:
            logger.error("Sample brief delivery failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_delivery_logs(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            params = parse_qs(urlparse(self.path).query)
            try:
                limit = int((params.get("limit") or ["20"])[0])
            except (TypeError, ValueError):
                limit = 20
            logs = get_user_delivery_logs(int(user["id"]), limit=max(1, min(limit, 50)))
            self._send_json({"ok": True, "logs": logs})
        except Exception as exc:
            logger.error("Delivery logs load failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_delivery_preview(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            params = parse_qs(urlparse(self.path).query)
            try:
                days = int((params.get("days") or ["14"])[0])
            except (TypeError, ValueError):
                days = 14
            preview = build_routing_preview_for_user(int(user["id"]), days=max(1, min(days, 60)))
            # The preview is a READ of the same official-source payload that
            # POST /api/delivery/send-preview-alert refuses with 402. Serve a
            # redacted view (counts, source names, risk levels kept; summary,
            # business action, official URL, diff excerpt withheld) to accounts
            # the delivery gate would refuse — same flag, same eligibility
            # helper. Own custom sources stay fully visible.
            preview = redact_preview_for_plan(int(user["id"]), preview)
            self._send_json({"ok": True, "preview": preview})
        except Exception as exc:
            logger.error("Delivery preview failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_delivery_send_preview_alert(self) -> None:
        if self._rate_limited(_DELIVERY_SEND_PREVIEW_LIMITER, "delivery_send_preview_alert"):
            return

        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        # RBAC Stage-2: dispatching an alert is a privileged action. Owner passes;
        # a read-only auditor seat is denied 403. No-op for accounts today.
        if not self._rbac_guard(user, rbac_runtime.ALERT_SEND, resource_type="alert"):
            return

        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return

        alert_id = str(body.get("alert_id", "")).strip()
        if not re.match(r"^[a-zA-Z0-9_-]{1,200}$", alert_id):
            self._send_json({"ok": False, "message": "Invalid alert_id."}, 400)
            return

        try:
            result = send_preview_alert_to_user(int(user["id"]), alert_id)
            if result.get("ok"):
                self._send_json({
                    "ok": True,
                    "message": result.get("message", "Preview alert sent to your Telegram."),
                    "log_id": result.get("log_id"),
                })
                return

            code = result.get("code")
            payload = {
                "ok": False,
                "message": result.get("reason", "Delivery failed."),
                "reason": code or "delivery_failed",
            }
            if result.get("details"):
                payload["details"] = result["details"]
            if code == "duplicate":
                self._send_json(payload, 409)
            elif code == "not_found":
                self._send_json(payload, 404)
            elif code == "not_ready":
                self._send_json(payload, 400)
            elif code == "plan_required":
                # Audit 07-20 FIX 6: free account asked for the paid
                # official-source deliverable. 402 — not a server fault, and the
                # message says nothing about plan internals or other tenants.
                self._send_json(payload, 402)
            elif code == "telegram_failed":
                self._send_json(payload, 502)
            else:
                self._send_json(payload, 400)
        except Exception as exc:
            logger.error("Preview alert delivery failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_delivery_email_test_mode(self) -> None:
        if self._rate_limited(_DELIVERY_TEST_BRIEF_LIMITER, "delivery_email_test_mode"):
            return

        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        recipient = str(body.get("recipient_email") or user.get("email") or "").strip()
        try:
            from datetime import timedelta

            from app.email_delivery import deliver_weekly_brief_test_mode
            from app.weekly_brief import build_weekly_brief

            end = datetime.now(timezone.utc)
            start = end - timedelta(days=7)
            brief = build_weekly_brief(
                client_profile={
                    "client_id": f"user_{int(user['id'])}",
                    "company_name": user.get("company_name") or user.get("email") or "Pilot workspace",
                },
                market="AE",
                start=start,
                end=end,
                alerts=[],
                demo_fixture=False,
            )
            result = deliver_weekly_brief_test_mode(brief, recipient_email=recipient)
            if result.get("ok"):
                self._send_json({
                    "ok": True,
                    "message": "Email test-mode payload written to local outbox. No external email was sent.",
                    **result,
                })
                return
            self._send_json({
                "ok": False,
                "message": result.get("error_message") or "Email test-mode delivery failed.",
                **result,
            }, 400)
        except Exception as exc:
            logger.error("Email test-mode delivery failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_delivery_email_status(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            from app.email_delivery import build_email_status_response

            self._send_json(build_email_status_response())
        except Exception as exc:
            logger.error("Email status failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_delivery_email_config_check(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            from app.email_delivery import record_email_config_check

            result = record_email_config_check()
            status_code = 200 if result.get("status") != "configuration_required" else 400
            self._send_json(result, status_code)
        except Exception as exc:
            logger.error("Email config check failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)
