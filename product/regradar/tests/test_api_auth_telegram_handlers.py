"""Behavioral coverage for the auth + telegram HTTP handler mixins.

These tests drive the REAL ``_Handler`` (built like the surrounding suite:
``__new__`` + a ``BytesIO`` body + a ``_send_json`` capture) through the
error/edge branches of ``_AuthHandlerMixin`` (``app.api_auth``) and
``_TelegramHandlerMixin`` (``app.api_telegram``) that ``test_api_coverage_uplift``
does not already exercise: register (validation / duplicate / success / 500),
logout, email verify / resend, forgot / reset password, ``/auth/me``, Google
status, and the Telegram account-test + unlink RBAC / send-failure branches.

A moved handler reads ``require_auth`` and its feature globals from its OWN
module (``app.api_auth`` / ``app.api_telegram``), so every dependency is
monkeypatched THERE, never at ``app.api``. No network, Telegram, or mailer runs:
the email senders and ``send_telegram_message`` are patched to inert stubs.
"""
from __future__ import annotations

import json
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api as api  # noqa: E402
import app.api_auth as api_auth  # noqa: E402
import app.api_telegram as api_telegram  # noqa: E402
from app.api import _Handler  # noqa: E402
from app.auth import DuplicateEmailError  # noqa: E402


# ── handler harness ───────────────────────────────────────────────────────────

_IP_SEQ = [0]


def _make_handler(method: str, path: str, body: dict | None = None,
                  raw: bytes | None = None, cookie: str = "") -> _Handler:
    """Build a real _Handler with a throwaway request body.

    A UNIQUE X-Real-IP per handler keeps every call under the per-IP rate
    limiter so a limiter never fires spuriously across tests.
    """
    _IP_SEQ[0] += 1
    if raw is not None:
        payload = raw
    elif body is not None:
        payload = json.dumps(body).encode()
    else:
        payload = b""

    header_map = {
        "Content-Length": str(len(payload)),
        "X-Real-IP": f"10.9.{_IP_SEQ[0] // 240 % 240}.{_IP_SEQ[0] % 240 + 1}",
        "Cookie": cookie,
    }
    handler = _Handler.__new__(_Handler)
    handler.command = method
    handler.path = path
    handler.request = MagicMock()
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(payload)
    handler.wfile = BytesIO()
    handler.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": header_map.get(key, default)
    handler.headers = hdrs

    sent: list = []
    handler._send_json = (  # type: ignore[method-assign]
        lambda data, status=200, extra_headers=None: sent.append((data, status, extra_headers))
    )
    redirects: list = []
    handler._redirect = (  # type: ignore[method-assign]
        lambda location, *, status=302, extra_headers=None: redirects.append(
            (location, status, extra_headers)
        )
    )
    # Email links are built from this — pin it so a poisoned Host / missing
    # config never leaks into the assertions.
    handler._public_base_url = lambda: "https://app.example.test"  # type: ignore[method-assign]
    handler._session_cookie_header = lambda sid: f"sp_session={sid}; HttpOnly"  # type: ignore[method-assign]
    handler._clear_session_cookie_header = lambda: "sp_session=; Max-Age=0"  # type: ignore[method-assign]
    handler._sent = sent  # type: ignore[attr-defined]
    handler._redirects = redirects  # type: ignore[attr-defined]
    return handler


def _last(handler: _Handler):
    return handler._sent[-1]  # type: ignore[attr-defined]


def _auth_as(monkeypatch, user: dict | None) -> None:
    """Steer ``require_auth`` in each module a moved handler now lives in."""
    monkeypatch.setattr(api_auth, "require_auth", lambda handler: user)
    monkeypatch.setattr(api_telegram, "require_auth", lambda handler: user)


@pytest.fixture(autouse=True)
def _silence_outbound(monkeypatch):
    """No real mail / founder notification threads fire from these tests."""
    monkeypatch.setattr(api_auth, "_send_verification_email", lambda *a, **k: None)
    monkeypatch.setattr(api_auth, "_send_password_reset_email", lambda *a, **k: None)
    monkeypatch.setattr(api_auth, "_notify_founder_registration", lambda *a, **k: None)


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/auth/register — validation, duplicate, success, internal error
# ══════════════════════════════════════════════════════════════════════════════

def test_register_bad_json_is_400():
    handler = _make_handler("POST", "/api/auth/register", raw=b"{not json")
    handler._handle_auth_register()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["ok"] is False


def test_register_missing_body_is_400():
    # The defensive ``body is None`` branch: a strict read that yields no error
    # yet no object (None, None) must still be rejected, not passed downstream.
    handler = _make_handler("POST", "/api/auth/register")
    handler._read_json_strict = lambda: (None, None)  # type: ignore[method-assign]
    handler._handle_auth_register()
    data, status, _ = _last(handler)
    assert status == 400
    assert "body required" in data["message"].lower()


def test_register_invalid_email_is_400():
    handler = _make_handler(
        "POST", "/api/auth/register",
        {"email": "not-an-email", "password": "Sufficiently-Long-1"},
    )
    handler._handle_auth_register()
    data, status, _ = _last(handler)
    assert status == 400
    assert "valid email" in data["message"].lower()


def test_register_weak_password_is_400(monkeypatch):
    monkeypatch.setattr(api_auth, "validate_password",
                        lambda pw: (False, "Password is too weak."))
    handler = _make_handler(
        "POST", "/api/auth/register",
        {"email": "new@acme.io", "password": "short"},
    )
    handler._handle_auth_register()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "Password is too weak."


def test_register_duplicate_email_is_409(monkeypatch):
    def _dupe(**kwargs):
        raise DuplicateEmailError("exists")

    monkeypatch.setattr(api_auth, "validate_password", lambda pw: (True, ""))
    monkeypatch.setattr(api_auth, "create_user", _dupe)
    handler = _make_handler(
        "POST", "/api/auth/register",
        {"email": "dupe@acme.io", "password": "Sufficiently-Long-1"},
    )
    handler._handle_auth_register()
    data, status, _ = _last(handler)
    assert status == 409
    assert "already registered" in data["message"].lower()


def test_register_success_is_201_and_requires_verification(monkeypatch):
    seen = {}

    def _create(**kwargs):
        seen.update(kwargs)
        return {"id": 501, "email": kwargs["email"]}

    monkeypatch.setattr(api_auth, "validate_password", lambda pw: (True, ""))
    monkeypatch.setattr(api_auth, "create_user", _create)
    monkeypatch.setattr(api_auth, "generate_verification_token", lambda uid: "vtok")
    handler = _make_handler(
        "POST", "/api/auth/register",
        {"email": "New@Acme.io", "password": "Sufficiently-Long-1",
         "full_name": "New User", "company_name": "Acme"},
    )
    handler._handle_auth_register()
    data, status, _ = _last(handler)
    assert status == 201
    assert data["ok"] is True
    assert data["requires_verification"] is True
    # Email is normalized before the account is created.
    assert seen["email"] == "new@acme.io"
    assert data["email"] == "new@acme.io"


def test_register_create_user_raises_is_500(monkeypatch):
    def _boom(**kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(api_auth, "validate_password", lambda pw: (True, ""))
    monkeypatch.setattr(api_auth, "create_user", _boom)
    handler = _make_handler(
        "POST", "/api/auth/register",
        {"email": "new@acme.io", "password": "Sufficiently-Long-1"},
    )
    handler._handle_auth_register()
    data, status, _ = _last(handler)
    assert status == 500
    assert data["message"] == "Internal server error."


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/auth/logout — clears the session cookie either way
# ══════════════════════════════════════════════════════════════════════════════

def test_logout_with_cookie_deletes_session(monkeypatch):
    deleted = {}
    monkeypatch.setattr(api_auth, "parse_session_cookie", lambda raw: "sess-1")
    monkeypatch.setattr(api_auth, "delete_session",
                        lambda sid: deleted.setdefault("sid", sid))
    handler = _make_handler("POST", "/api/auth/logout", cookie="sp_session=sess-1")
    handler._handle_auth_logout()
    data, status, extra = _last(handler)
    assert status == 200
    assert deleted["sid"] == "sess-1"
    assert any(k == "Set-Cookie" for k, _ in (extra or []))


def test_logout_without_cookie_still_clears(monkeypatch):
    monkeypatch.setattr(api_auth, "parse_session_cookie", lambda raw: None)
    monkeypatch.setattr(api_auth, "delete_session",
                        lambda sid: pytest.fail("delete_session must not run without a session"))
    handler = _make_handler("POST", "/api/auth/logout")
    handler._handle_auth_logout()
    data, status, extra = _last(handler)
    assert status == 200
    assert data["ok"] is True
    assert any(k == "Set-Cookie" for k, _ in (extra or []))


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/auth/verify-email — consume, idempotent re-click, invalid token
# ══════════════════════════════════════════════════════════════════════════════

def test_verify_email_valid_token_marks_verified_no_session(monkeypatch):
    marked = {}
    monkeypatch.setattr(api_auth, "consume_verification_token", lambda tok: 88)
    monkeypatch.setattr(api_auth, "mark_email_verified",
                        lambda uid: marked.setdefault("uid", uid))
    handler = _make_handler("GET", "/api/auth/verify-email?token=abc")
    handler._handle_auth_verify_email()
    data, status, extra = _last(handler)
    assert status == 200
    assert data["verified"] is True
    assert marked["uid"] == 88
    # A GET email link must NEVER mint a login session.
    assert extra is None or all(k != "Set-Cookie" for k, _ in (extra or []))


def test_verify_email_already_verified_is_idempotent_200(monkeypatch):
    # The single-use token is already burned (mail scanner pre-fetch), but the
    # account is verified -> friendly success, not a scary error.
    monkeypatch.setattr(api_auth, "consume_verification_token", lambda tok: None)
    monkeypatch.setattr(api_auth, "verified_user_for_consumed_token",
                        lambda tok: {"id": 5, "email_verified": True})
    monkeypatch.setattr(api_auth, "mark_email_verified",
                        lambda uid: pytest.fail("must not re-mark on an already-verified token"))
    handler = _make_handler("GET", "/api/auth/verify-email?token=burned")
    handler._handle_auth_verify_email()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["verified"] is True
    assert "already verified" in data["message"].lower()


def test_verify_email_invalid_token_is_400(monkeypatch):
    monkeypatch.setattr(api_auth, "consume_verification_token", lambda tok: None)
    monkeypatch.setattr(api_auth, "verified_user_for_consumed_token", lambda tok: None)
    handler = _make_handler("GET", "/api/auth/verify-email?token=garbage")
    handler._handle_auth_verify_email()
    data, status, _ = _last(handler)
    assert status == 400
    assert "invalid or has expired" in data["message"].lower()


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/auth/resend-verification — enumeration-safe resend
# ══════════════════════════════════════════════════════════════════════════════

def test_resend_missing_body_is_400():
    handler = _make_handler("POST", "/api/auth/resend-verification", raw=b"null")
    handler._handle_auth_resend_verification()
    data, status, _ = _last(handler)
    assert status == 400
    assert "email required" in data["message"].lower()


def test_resend_invalid_email_is_400():
    handler = _make_handler(
        "POST", "/api/auth/resend-verification", {"email": "bad"})
    handler._handle_auth_resend_verification()
    data, status, _ = _last(handler)
    assert status == 400
    assert "valid email" in data["message"].lower()


def test_resend_unknown_email_is_generic_200(monkeypatch):
    # No user -> generic success, never revealing the address is unknown.
    monkeypatch.setattr(api_auth, "get_user_by_email", lambda email: None)
    monkeypatch.setattr(api_auth, "generate_verification_token",
                        lambda uid: pytest.fail("no token minted for an unknown email"))
    handler = _make_handler(
        "POST", "/api/auth/resend-verification", {"email": "ghost@acme.io"})
    handler._handle_auth_resend_verification()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True
    assert "if that email is registered" in data["message"].lower()


def test_resend_already_verified_is_200(monkeypatch):
    monkeypatch.setattr(api_auth, "get_user_by_email",
                        lambda email: {"id": 1, "email": email, "email_verified": True})
    monkeypatch.setattr(api_auth, "generate_verification_token",
                        lambda uid: pytest.fail("no token minted for a verified account"))
    handler = _make_handler(
        "POST", "/api/auth/resend-verification", {"email": "done@acme.io"})
    handler._handle_auth_resend_verification()
    data, status, _ = _last(handler)
    assert status == 200
    assert "already verified" in data["message"].lower()


def test_resend_unverified_user_sends_and_200(monkeypatch):
    monkeypatch.setattr(api_auth, "get_user_by_email",
                        lambda email: {"id": 7, "email": email, "email_verified": False})
    monkeypatch.setattr(api_auth, "generate_verification_token", lambda uid: "rtok")
    handler = _make_handler(
        "POST", "/api/auth/resend-verification", {"email": "pending@acme.io"})
    handler._handle_auth_resend_verification()
    data, status, _ = _last(handler)
    assert status == 200
    assert "verification email sent" in data["message"].lower()


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/auth/forgot-password — always generic (no enumeration)
# ══════════════════════════════════════════════════════════════════════════════

def test_forgot_missing_body_is_400():
    handler = _make_handler("POST", "/api/auth/forgot-password", raw=b"null")
    handler._handle_auth_forgot_password()
    data, status, _ = _last(handler)
    assert status == 400
    assert "email required" in data["message"].lower()


def test_forgot_invalid_email_is_generic_200(monkeypatch):
    monkeypatch.setattr(api_auth, "generate_password_reset_token",
                        lambda email: pytest.fail("no token for an invalid email"))
    handler = _make_handler(
        "POST", "/api/auth/forgot-password", {"email": "not-valid"})
    handler._handle_auth_forgot_password()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True
    assert "if that email is registered" in data["message"].lower()


def test_forgot_token_issue_raises_is_still_generic_200(monkeypatch):
    def _boom(email):
        raise RuntimeError("token store down")

    monkeypatch.setattr(api_auth, "generate_password_reset_token", _boom)
    handler = _make_handler(
        "POST", "/api/auth/forgot-password", {"email": "user@acme.io"})
    handler._handle_auth_forgot_password()
    data, status, _ = _last(handler)
    assert status == 200  # a failing token issue must never leak via status
    assert data["ok"] is True


def test_forgot_no_account_returns_generic_200(monkeypatch):
    # A valid-but-unknown email: generate returns None (no account) -> generic.
    monkeypatch.setattr(api_auth, "generate_password_reset_token", lambda email: None)
    handler = _make_handler(
        "POST", "/api/auth/forgot-password", {"email": "ghost@acme.io"})
    handler._handle_auth_forgot_password()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True


def test_forgot_issued_token_sends_and_generic_200(monkeypatch):
    monkeypatch.setattr(api_auth, "generate_password_reset_token",
                        lambda email: ("rtok", 42))
    handler = _make_handler(
        "POST", "/api/auth/forgot-password", {"email": "user@acme.io"})
    handler._handle_auth_forgot_password()
    data, status, _ = _last(handler)
    assert status == 200
    assert "if that email is registered" in data["message"].lower()


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/auth/reset-password — token consume + password set
# ══════════════════════════════════════════════════════════════════════════════

def test_reset_missing_body_is_400():
    handler = _make_handler("POST", "/api/auth/reset-password", raw=b"null")
    handler._handle_auth_reset_password()
    data, status, _ = _last(handler)
    assert status == 400
    assert "token and password required" in data["message"].lower()


def test_reset_missing_token_is_400():
    handler = _make_handler(
        "POST", "/api/auth/reset-password", {"password": "Sufficiently-Long-1"})
    handler._handle_auth_reset_password()
    data, status, _ = _last(handler)
    assert status == 400
    assert "reset token is required" in data["message"].lower()


def test_reset_weak_password_is_400(monkeypatch):
    monkeypatch.setattr(api_auth, "validate_password",
                        lambda pw: (False, "Password is too weak."))
    handler = _make_handler(
        "POST", "/api/auth/reset-password", {"token": "t", "password": "x"})
    handler._handle_auth_reset_password()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "Password is too weak."


def test_reset_invalid_token_is_400(monkeypatch):
    monkeypatch.setattr(api_auth, "validate_password", lambda pw: (True, ""))
    monkeypatch.setattr(api_auth, "consume_password_reset_token", lambda tok: None)
    monkeypatch.setattr(api_auth, "set_user_password",
                        lambda uid, pw: pytest.fail("must not set a password on an invalid token"))
    handler = _make_handler(
        "POST", "/api/auth/reset-password",
        {"token": "expired", "password": "Sufficiently-Long-1"})
    handler._handle_auth_reset_password()
    data, status, _ = _last(handler)
    assert status == 400
    assert "invalid or has expired" in data["message"].lower()


def test_reset_set_password_raises_is_500(monkeypatch):
    monkeypatch.setattr(api_auth, "validate_password", lambda pw: (True, ""))
    monkeypatch.setattr(api_auth, "consume_password_reset_token", lambda tok: 9)

    def _boom(uid, pw):
        raise RuntimeError("write failed")

    monkeypatch.setattr(api_auth, "set_user_password", _boom)
    handler = _make_handler(
        "POST", "/api/auth/reset-password",
        {"token": "ok", "password": "Sufficiently-Long-1"})
    handler._handle_auth_reset_password()
    data, status, _ = _last(handler)
    assert status == 500


def test_reset_success_sets_password_and_200(monkeypatch):
    seen = {}
    monkeypatch.setattr(api_auth, "validate_password", lambda pw: (True, ""))
    monkeypatch.setattr(api_auth, "consume_password_reset_token", lambda tok: 9)
    monkeypatch.setattr(api_auth, "set_user_password",
                        lambda uid, pw: seen.update({"uid": uid, "pw": pw}))
    handler = _make_handler(
        "POST", "/api/auth/reset-password",
        {"token": "ok", "password": "Sufficiently-Long-1"})
    handler._handle_auth_reset_password()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True
    assert seen["uid"] == 9
    assert seen["pw"] == "Sufficiently-Long-1"


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/auth/me — identity read
# ══════════════════════════════════════════════════════════════════════════════

def test_me_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/auth/me")
    handler._handle_auth_me()
    data, status, _ = _last(handler)
    assert status == 401
    assert data["ok"] is False


def test_me_authenticated_returns_public_user(monkeypatch):
    _auth_as(monkeypatch, {"id": 3, "email": "me@acme.io", "password_hash": "secret"})
    monkeypatch.setattr(api_auth, "make_public_user",
                        lambda u: {"id": u["id"], "email": u["email"]})
    handler = _make_handler("GET", "/api/auth/me")
    handler._handle_auth_me()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["user"]["id"] == 3
    assert "password_hash" not in data["user"]  # public projection only


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/auth/google/status — configured / not configured
# ══════════════════════════════════════════════════════════════════════════════

def test_google_status_available_true(monkeypatch):
    monkeypatch.setattr(api_auth, "google_oauth_available", lambda: True)
    handler = _make_handler("GET", "/api/auth/google/status")
    handler._handle_auth_google_status()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["available"] is True
    assert "configured" in data["message"].lower()


def test_google_status_available_false(monkeypatch):
    monkeypatch.setattr(api_auth, "google_oauth_available", lambda: False)
    handler = _make_handler("GET", "/api/auth/google/status")
    handler._handle_auth_google_status()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["available"] is False
    assert "not configured" in data["message"].lower()


# ══════════════════════════════════════════════════════════════════════════════
# Telegram — rate-limit short-circuit, pair-status 500, unlink RBAC/500
# ══════════════════════════════════════════════════════════════════════════════

def test_pair_generate_rate_limited_short_circuits(monkeypatch):
    # When the limiter fires, the handler returns BEFORE require_auth/pairing.
    monkeypatch.setattr(api_telegram, "require_auth",
                        lambda handler: pytest.fail("require_auth must not run when rate-limited"))
    handler = _make_handler("POST", "/api/telegram/pair/generate")
    handler._rate_limited = (  # type: ignore[method-assign]
        lambda limiter, label: handler._sent.append(({"ok": False}, 429, None)) or True
    )
    handler._handle_telegram_pair_generate()
    _, status, _ = _last(handler)
    assert status == 429


def test_pair_status_internal_error_is_500(monkeypatch):
    _auth_as(monkeypatch, {"id": 4})

    def _boom(uid):
        raise RuntimeError("status store down")

    monkeypatch.setattr(api_telegram, "get_pairing_status", _boom)
    handler = _make_handler("GET", "/api/telegram/pair/status")
    handler._handle_telegram_pair_status()
    data, status, _ = _last(handler)
    assert status == 500
    assert data["message"] == "Internal server error."


def test_pair_unlink_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("POST", "/api/telegram/pair/unlink")
    handler._handle_telegram_pair_unlink()
    _, status, _ = _last(handler)
    assert status == 401


def test_pair_unlink_rbac_denied_403(monkeypatch):
    # A read-only auditor seat is denied SETTINGS_EDIT: the RBAC guard emits its
    # own 403 and unlink_telegram is never reached.
    _auth_as(monkeypatch, {"id": 4})
    monkeypatch.setattr(api_telegram, "unlink_telegram",
                        lambda uid: pytest.fail("unlink must not run when RBAC denies"))
    handler = _make_handler("POST", "/api/telegram/pair/unlink")
    handler._rbac_guard = lambda user, action, **kw: (  # type: ignore[method-assign]
        handler._sent.append(({"ok": False}, 403, None)) or False
    )
    handler._handle_telegram_pair_unlink()
    _, status, _ = _last(handler)
    assert status == 403


def test_pair_unlink_internal_error_is_500(monkeypatch):
    _auth_as(monkeypatch, {"id": 4})
    monkeypatch.setattr(api_telegram, "unlink_telegram",
                        lambda uid: (_ for _ in ()).throw(RuntimeError("unlink store down")))
    handler = _make_handler("POST", "/api/telegram/pair/unlink")
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_telegram_pair_unlink()
    data, status, _ = _last(handler)
    assert status == 500
    assert data["message"] == "Internal server error."


# ══════════════════════════════════════════════════════════════════════════════
# Telegram account-test — the whole not-connected / send / fail / error surface
# ══════════════════════════════════════════════════════════════════════════════

def test_account_test_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("POST", "/api/telegram/account/test")
    handler._handle_telegram_account_test()
    _, status, _ = _last(handler)
    assert status == 401


def test_account_test_not_connected_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 4})
    monkeypatch.setattr(api_telegram, "get_telegram_link",
                        lambda uid: {"telegram_chat_id": None})
    monkeypatch.setattr(api_telegram, "send_telegram_message",
                        lambda cid, msg: pytest.fail("no send without a connected chat"))
    handler = _make_handler("POST", "/api/telegram/account/test")
    handler._handle_telegram_account_test()
    data, status, _ = _last(handler)
    assert status == 400
    assert "not connected" in data["message"].lower()


def test_account_test_send_success_touches_and_200(monkeypatch):
    _auth_as(monkeypatch, {"id": 4})
    touched = {}
    monkeypatch.setattr(api_telegram, "get_telegram_link",
                        lambda uid: {"telegram_chat_id": "999"})
    monkeypatch.setattr(api_telegram, "send_telegram_message", lambda cid, msg: True)
    monkeypatch.setattr(api_telegram, "touch_telegram_test_sent",
                        lambda uid: touched.setdefault("uid", uid))
    handler = _make_handler("POST", "/api/telegram/account/test")
    handler._handle_telegram_account_test()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True
    assert touched["uid"] == 4  # only marked sent on a successful delivery


def test_account_test_send_failure_is_502(monkeypatch):
    _auth_as(monkeypatch, {"id": 4})
    monkeypatch.setattr(api_telegram, "get_telegram_link",
                        lambda uid: {"telegram_chat_id": "999"})
    monkeypatch.setattr(api_telegram, "send_telegram_message", lambda cid, msg: False)
    monkeypatch.setattr(api_telegram, "touch_telegram_test_sent",
                        lambda uid: pytest.fail("must not mark sent on a delivery failure"))
    handler = _make_handler("POST", "/api/telegram/account/test")
    handler._handle_telegram_account_test()
    data, status, _ = _last(handler)
    assert status == 502
    assert "could not send" in data["message"].lower()


def test_account_test_internal_error_is_500(monkeypatch):
    _auth_as(monkeypatch, {"id": 4})

    def _boom(uid):
        raise RuntimeError("link lookup down")

    monkeypatch.setattr(api_telegram, "get_telegram_link", _boom)
    handler = _make_handler("POST", "/api/telegram/account/test")
    handler._handle_telegram_account_test()
    data, status, _ = _last(handler)
    assert status == 500
    assert data["message"] == "Internal server error."


def test_account_test_rate_limited_short_circuits(monkeypatch):
    monkeypatch.setattr(api_telegram, "require_auth",
                        lambda handler: pytest.fail("require_auth must not run when rate-limited"))
    handler = _make_handler("POST", "/api/telegram/account/test")
    handler._rate_limited = (  # type: ignore[method-assign]
        lambda limiter, label: handler._sent.append(({"ok": False}, 429, None)) or True
    )
    handler._handle_telegram_account_test()
    _, status, _ = _last(handler)
    assert status == 429
