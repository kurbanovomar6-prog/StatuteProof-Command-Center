"""Authentication + account request handlers, extracted from ``app.api``.

This module holds one cohesive slice of the HTTP surface — register, login,
logout, email verification/resend, password forgot/reset, the ``/auth/me``
identity read, and the Google OAuth status/start/callback flow — as a mixin
that ``app.api._Handler`` inherits. The method bodies are byte-identical to
their former inline definitions; only their host class/file changed.

Names the moved bodies read as bare globals are imported here FROM ``app.api``
so they are the SAME objects the rest of the handler uses (and so tests that
monkeypatch ``app.api_auth.<name>`` steer these methods exactly as they
previously steered ``app.api.<name>``). The only function-local import inside a
body (``import threading as _threading``) stays in the body and resolves at call
time. Shared per-request helpers (``_send_json``, ``_rate_limited``,
``_read_json_strict``, ``_public_base_url``, ``_session_cookie_header``,
``_clear_session_cookie_header``, ``_redirect``, ``_caller_is_admin``) stay on
``_Handler`` and are reached through ``self``.
"""
from __future__ import annotations

from app.api import (
    DuplicateEmailError,
    OAuthAccountError,
    _LOGIN_LIMITER,
    _REGISTER_LIMITER,
    _notify_founder_registration,
    _send_password_reset_email,
    _send_verification_email,
    consume_google_oauth_state,
    consume_password_reset_token,
    consume_verification_token,
    create_google_oauth_state,
    create_session,
    create_user,
    delete_session,
    exchange_google_oauth_code,
    generate_password_reset_token,
    generate_verification_token,
    clear_failed_logins,
    get_user_by_email,
    is_account_locked,
    google_oauth_authorization_url,
    google_oauth_available,
    hashlib,
    link_or_create_google_user,
    logger,
    make_public_user,
    mark_email_verified,
    normalize_email,
    record_failed_login,
    parse_qs,
    parse_session_cookie,
    require_auth,
    set_user_password,
    urlparse,
    validate_email,
    validate_password,
    verified_user_for_consumed_token,
    verify_password,
)


# How long registration waits for the verification mail before answering. Every
# provider path in app/email_delivery.py allows timeout=15, which is far too long
# to hold a signup request on; this bounds the wait while still capturing the
# result in the ordinary case, where a send succeeds or fails in well under a
# second. Past this the answer is an honest "still sending", never a fabricated
# success.
_VERIFICATION_SEND_WAIT_S = 6.0


class _AuthHandlerMixin:
    """Authentication + account request handlers for ``_Handler``."""

    def _handle_auth_register(self) -> None:
        if self._rate_limited(_REGISTER_LIMITER, "auth_register"):
            return

        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return

        email = normalize_email(body.get("email", ""))
        password = str(body.get("password", ""))
        full_name = body.get("full_name") or body.get("fullName") or body.get("name")
        company_name = str(body.get("company_name", "")).strip()
        industry = str(body.get("industry", "")).strip()
        job_title = str(body.get("job_title", "")).strip()
        company_type = str(body.get("company_type", "")).strip()
        jurisdiction = str(body.get("jurisdiction", "")).strip()

        if not validate_email(email):
            self._send_json({"ok": False, "message": "Enter a valid email address."}, 400)
            return

        password_ok, password_msg = validate_password(password)
        if not password_ok:
            self._send_json({"ok": False, "message": password_msg}, 400)
            return

        try:
            user = create_user(
                email=email,
                password=password,
                full_name=full_name,
                company_name=company_name,
                industry=industry,
                job_title=job_title,
                company_type=company_type,
                jurisdiction=jurisdiction,
            )
            token = generate_verification_token(int(user["id"]))
            verification_url = f"{self._public_base_url()}/verify-email?token={token}"
            import threading as _threading

            # The verification mail used to be fired into a daemon thread whose
            # result was thrown away, so registration answered "check your inbox"
            # whether or not anything was sent. A customer whose mail silently
            # failed — misconfigured provider, sending disabled, a bounce — was
            # left staring at a success screen and could not sign in, because
            # login refuses an unverified account.
            #
            # It is still off the request thread (every provider path allows
            # timeout=15, too long to hold a signup on), but the result is WAITED
            # for, briefly, and reported. Three honest outcomes, never conflated:
            #   True  — the provider accepted it
            #   False — it failed, and the customer is told to use Resend
            #   None  — still in flight past the wait; we do not know, and say so
            email_outcome: bool | None = None
            send_result: dict = {}

            def _send_and_capture() -> None:
                nonlocal send_result
                try:
                    send_result = _send_verification_email(user["email"], verification_url) or {}
                except Exception as exc:  # noqa: BLE001 — a send failure is not a 500
                    logger.warning("verification email failed: %s", type(exc).__name__)
                    send_result = {"status": "error"}

            sender = _threading.Thread(target=_send_and_capture, daemon=True)
            sender.start()
            sender.join(timeout=_VERIFICATION_SEND_WAIT_S)
            if not sender.is_alive():
                # app.email_delivery returns {"status": "sent"|"error"|"dry_run"}.
                # There is no "ok" key and there never was, so reading one made
                # email_outcome False on EVERY successful registration — the
                # customer was told the email had failed while it was being
                # delivered. The pinning test hid it by monkeypatching a fake
                # that returned {"ok": True}, a shape production never produces.
                #
                # dry_run is deliberately NOT success: it means the local outbox
                # took the message and no customer received anything.
                email_outcome = str(send_result.get("status") or "") == "sent"
                if not email_outcome:
                    logger.warning(
                        "verification email not delivered for a new registration "
                        "(status=%s); the account exists and can use Resend",
                        send_result.get("status") or "unknown",
                    )

            # Founder heads-up via the admin bot — best-effort, never blocks
            # or fails the registration (see _notify_founder_registration).
            _threading.Thread(
                target=_notify_founder_registration,
                args=(user["email"], str(full_name or ""), company_name),
                daemon=True,
            ).start()

            if email_outcome is False:
                message = (
                    "Your account was created, but we could not send the "
                    "verification email. Use Resend below, or contact support if it "
                    "keeps failing."
                )
            elif email_outcome is None:
                message = (
                    "Your account was created. The verification email is still "
                    "sending — if it has not arrived shortly, use Resend below."
                )
            else:
                message = "Account created. Check your inbox for the verification link."

            self._send_json(
                {
                    "ok": True,
                    "requires_verification": True,
                    "email": user["email"],
                    "verification_email_sent": email_outcome,
                    "message": message,
                },
                201,
            )
        except DuplicateEmailError:
            self._send_json({"ok": False, "message": "Email is already registered."}, 409)
        except Exception as exc:
            logger.error("Auth register failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_auth_login(self) -> None:
        if self._rate_limited(_LOGIN_LIMITER, "auth_login"):
            return

        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return

        email = normalize_email(body.get("email", ""))
        password = str(body.get("password", ""))

        # Per-ACCOUNT lockout. The limiter above caps one IP; this caps attempts
        # against one account, which is what an attacker with a pool of addresses
        # actually attacks. The response is the SAME 401 as a wrong password on
        # purpose: a distinct "account locked" reply would confirm the address
        # exists, turning the defence into an enumeration oracle.
        if is_account_locked(email):
            self._send_json({"ok": False, "message": "Invalid email or password."}, 401)
            return

        user = get_user_by_email(email) if validate_email(email) else None
        if not user or not user.get("is_active") or not verify_password(password, user.get("password_hash", "")):
            # Counted for unknown addresses too, so the counter's behaviour does
            # not differ between a real and an invented account.
            record_failed_login(email)
            self._send_json({"ok": False, "message": "Invalid email or password."}, 401)
            return

        clear_failed_logins(email)

        if not user.get("email_verified"):
            self._send_json(
                {
                    "ok": False,
                    "message": "Please verify your email before signing in. Check your inbox for a verification link.",
                    "requires_verification": True,
                    "email": user.get("email"),
                },
                403,
            )
            return

        try:
            session_id = create_session(int(user["id"]))
            self._send_json(
                {"ok": True, "user": make_public_user(user)},
                200,
                [("Set-Cookie", self._session_cookie_header(session_id))],
            )
        except Exception:
            logger.error("Auth login failed for email_hash=%s", hashlib.sha256(email.encode()).hexdigest()[:12])
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_auth_logout(self) -> None:
        session_id = parse_session_cookie(self.headers.get("Cookie", ""))
        if session_id:
            delete_session(session_id)
        self._send_json(
            {"ok": True},
            200,
            [("Set-Cookie", self._clear_session_cookie_header())],
        )

    def _handle_auth_verify_email(self) -> None:
        qs = parse_qs(urlparse(self.path).query)
        token = (qs.get("token") or [""])[0]
        user_id = consume_verification_token(token)
        if user_id is None:
            # Idempotent re-click: a corporate mail scanner (Safe Links / URL
            # Defense) commonly pre-fetches the link and burns the single-use
            # token before the human clicks — the pre-fetch already verified the
            # email. Show success for an already-verified user rather than a
            # scary "invalid link" error (our ICP runs exactly these scanners).
            already = verified_user_for_consumed_token(token)
            if already is not None:
                self._send_json(
                    {"ok": True, "verified": True, "message": "Email already verified. Please sign in to continue."},
                    200,
                )
                return
            self._send_json(
                {"ok": False, "message": "Verification link is invalid or has expired. Please request a new one."},
                400,
            )
            return
        mark_email_verified(user_id)
        # Security: do NOT mint a login session here. This is a GET link
        # delivered by email; a mailbox security scanner or shared-inbox viewer
        # can fetch it before the real user clicks. Auto-issuing a Set-Cookie
        # would hand that party a valid 7-day session for the victim account
        # (token-in-URL becoming a login credential). Verifying the email is
        # sufficient; the user then signs in normally with their password.
        self._send_json(
            {
                "ok": True,
                "verified": True,
                "message": "Email verified. Please sign in to continue.",
            },
            200,
        )

    def _handle_auth_resend_verification(self) -> None:
        if self._rate_limited(_REGISTER_LIMITER, "auth_resend"):
            return
        body, error = self._read_json_strict()
        if error or body is None:
            self._send_json({"ok": False, "message": "Request body with email required."}, 400)
            return
        email = normalize_email(body.get("email", ""))
        if not validate_email(email):
            self._send_json({"ok": False, "message": "Enter a valid email address."}, 400)
            return
        user = get_user_by_email(email)
        if not user:
            # Don't reveal whether email exists
            self._send_json({"ok": True, "message": "If that email is registered, a verification link has been sent."}, 200)
            return
        if user.get("email_verified"):
            self._send_json({"ok": True, "message": "Email is already verified. Please sign in."}, 200)
            return
        token = generate_verification_token(int(user["id"]))
        # SEC-5: build the emailed link from the CONFIGURED public base, never the
        # attacker-controllable Host header (parity with register/reset, 3789ab4).
        verification_url = f"{self._public_base_url()}/verify-email?token={token}"
        import threading as _threading
        _threading.Thread(
            target=_send_verification_email,
            args=(user["email"], verification_url),
            daemon=True,
        ).start()
        self._send_json({"ok": True, "message": "Verification email sent. Check your inbox."}, 200)

    def _handle_auth_forgot_password(self) -> None:
        """POST /api/auth/forgot-password {email} — always returns a generic
        success (no user enumeration). If the account exists, emails a 2-hour
        single-use reset link."""
        if self._rate_limited(_REGISTER_LIMITER, "auth_forgot"):
            return
        body, error = self._read_json_strict()
        if error or body is None:
            self._send_json({"ok": False, "message": "Request body with email required."}, 400)
            return
        email = normalize_email(body.get("email", ""))
        generic = {"ok": True, "message": "If that email is registered, a password reset link has been sent."}
        if not validate_email(email):
            # Same generic response — never reveal validity/existence.
            self._send_json(generic, 200)
            return
        try:
            issued = generate_password_reset_token(email)
        except Exception as exc:
            logger.error("forgot-password token issue failed: %s", type(exc).__name__)
            self._send_json(generic, 200)
            return
        if issued:
            token, _uid = issued
            reset_url = f"{self._public_base_url()}/reset-password?token={token}"
            import threading as _threading
            _threading.Thread(
                target=_send_password_reset_email,
                args=(email, reset_url),
                daemon=True,
            ).start()
        self._send_json(generic, 200)

    def _handle_auth_reset_password(self) -> None:
        """POST /api/auth/reset-password {token, password} — consume the reset
        token, set the new password, and log the user out everywhere."""
        if self._rate_limited(_REGISTER_LIMITER, "auth_reset"):
            return
        body, error = self._read_json_strict()
        if error or body is None:
            self._send_json({"ok": False, "message": "Request body with token and password required."}, 400)
            return
        token = str(body.get("token") or "").strip()
        new_password = str(body.get("password") or "")
        if not token:
            self._send_json({"ok": False, "message": "Reset token is required."}, 400)
            return
        ok, msg = validate_password(new_password)
        if not ok:
            self._send_json({"ok": False, "message": msg}, 400)
            return
        try:
            user_id = consume_password_reset_token(token)
            if user_id is None:
                self._send_json({"ok": False, "message": "This reset link is invalid or has expired."}, 400)
                return
            set_user_password(user_id, new_password)
        except Exception as exc:
            logger.error("reset-password failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)
            return
        self._send_json({"ok": True, "message": "Your password has been reset. Please sign in with your new password."}, 200)

    def _handle_auth_me(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        self._send_json({"ok": True, "user": make_public_user(user)})

    def _handle_auth_google_status(self) -> None:
        available = google_oauth_available()
        self._send_json(
            {
                "ok": True,
                "available": available,
                "message": (
                    "Google sign-in is configured."
                    if available
                    else "Google sign-in is not configured for this environment."
                ),
            }
        )

    def _handle_auth_google_start(self) -> None:
        if self._rate_limited(_LOGIN_LIMITER, "auth_google_start"):
            return
        if not google_oauth_available():
            self._send_json(
                {
                    "ok": False,
                    "available": False,
                    "message": "Google sign-in is not configured for this environment.",
                },
                503,
            )
            return
        params = parse_qs(urlparse(self.path).query)
        next_path = str((params.get("next") or ["/app"])[0] or "/app")
        try:
            state = create_google_oauth_state(next_path=next_path)
            self._redirect(google_oauth_authorization_url(state))
        except OAuthAccountError as exc:
            self._send_json({"ok": False, "message": "Google sign-in is not available for this account type."}, 503)
        except Exception as exc:
            logger.error("Google OAuth start failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Google sign-in could not be started."}, 500)

    def _handle_auth_google_callback(self) -> None:
        params = parse_qs(urlparse(self.path).query)
        if params.get("error"):
            self._redirect("/login?google=cancelled")
            return
        state = str((params.get("state") or [""])[0] or "").strip()
        code = str((params.get("code") or [""])[0] or "").strip()
        state_record = consume_google_oauth_state(state)
        if not state_record or not code:
            self._redirect("/login?google=failed")
            return
        try:
            claims = exchange_google_oauth_code(code)
            user = link_or_create_google_user(claims)
            if not user.get("is_active"):
                raise OAuthAccountError("Account is not active.")
            session_id = create_session(int(user["id"]))
            self._redirect(
                str(state_record.get("next_path") or "/app"),
                extra_headers=[("Set-Cookie", self._session_cookie_header(session_id))],
            )
        except OAuthAccountError:
            self._redirect("/login?google=failed")
        except Exception as exc:
            logger.error("Google OAuth callback failed: %s", type(exc).__name__)
            self._redirect("/login?google=failed")
