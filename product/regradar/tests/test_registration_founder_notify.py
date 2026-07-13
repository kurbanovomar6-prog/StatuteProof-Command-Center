"""Founder Telegram notification on new user registration.

Requirements (owner, 2026-07-10):
1. Every successful registration sends a best-effort Telegram message to the
   founder via the admin bot (TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID).
2. The notification must NEVER affect the registration outcome — Telegram
   down, misconfigured, or erroring still yields 201 for the user.
3. When the admin bot is not configured, the helper is a quiet no-op.
"""
from __future__ import annotations

import json
import sys
import threading
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api as api_module
from app.api import _Handler, _notify_founder_registration


# ---------------------------------------------------------------------------
# Helpers (mirrors tests/test_auth_guards.py conventions)
# ---------------------------------------------------------------------------

def _make_handler(body: dict) -> _Handler:
    raw_body = json.dumps(body).encode()

    request = MagicMock()
    request.makefile.return_value = BytesIO(raw_body)

    handler = _Handler.__new__(_Handler)
    handler.command = "POST"
    handler.path = "/api/auth/register"
    handler.request = request
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(raw_body)
    handler.wfile = BytesIO()
    handler.headers = MagicMock()
    handler.headers.get = lambda key, default="": (
        str(len(raw_body)) if key == "Content-Length" else default
    )

    sent: list[tuple[dict, int]] = []

    def _fake_send_json(data: dict, status: int = 200, **kw):
        sent.append((data, status))

    handler._send_json = _fake_send_json  # type: ignore[method-assign]
    handler._sent = sent  # type: ignore[attr-defined]
    handler._base_url = lambda: "https://statuteproof.com"  # type: ignore[method-assign]
    return handler


_REGISTER_BODY = {
    "email": "new.customer@example.com",
    "password": "Str0ng!Passw0rd",
    "full_name": "Test Customer",
    "company_name": "Test DMCC",
}


class TestFounderNotifyOnRegistration:
    def test_successful_registration_notifies_founder(self):
        """Successful create_user → founder notification fired with the email."""
        handler = _make_handler(_REGISTER_BODY)
        fired = threading.Event()
        captured: dict = {}

        def _fake_notify(email, full_name="", company_name=""):
            captured["email"] = email
            captured["company"] = company_name
            fired.set()

        with patch.object(api_module, "create_user") as mock_create, \
             patch.object(api_module, "generate_verification_token", return_value="tok"), \
             patch.object(api_module, "_send_verification_email"), \
             patch.object(api_module, "_notify_founder_registration", side_effect=_fake_notify), \
             patch.object(handler, "_rate_limited", return_value=False, create=True):
            mock_create.return_value = {"id": 7, "email": _REGISTER_BODY["email"]}
            handler._handle_auth_register()

        assert handler._sent, "handler sent no response"
        payload, status = handler._sent[-1]
        assert status == 201 and payload.get("ok") is True
        assert fired.wait(timeout=3.0), "founder notification was not fired"
        assert captured["email"] == _REGISTER_BODY["email"]
        assert captured["company"] == _REGISTER_BODY["company_name"]

    def test_notification_failure_does_not_break_registration(self):
        """Notify helper raising inside its daemon thread must not affect the 201.

        The notify runs in a fire-and-forget daemon thread. We capture that
        thread's exception via ``threading.excepthook`` so it (a) is asserted to
        have actually fired and (b) does not leak into interpreter teardown as a
        stray ``PytestUnhandledThreadExceptionWarning`` mis-attributed to a later
        test. In production ``_notify_founder_registration`` swallows its own
        errors (see ``test_helper_swallows_request_errors``); this test patches
        the whole helper to force the raise and prove the 201 is unaffected.
        """
        handler = _make_handler(_REGISTER_BODY)

        raised = threading.Event()
        captured_exc: list[BaseException] = []

        def _boom(*a, **kw):
            raise RuntimeError("telegram down")

        original_hook = threading.excepthook

        def _capture_hook(args):
            exc = args.exc_value
            if isinstance(exc, RuntimeError) and str(exc) == "telegram down":
                captured_exc.append(exc)
                raised.set()
            else:  # pragma: no cover - unexpected thread errors still surface
                original_hook(args)

        threading.excepthook = _capture_hook
        try:
            with patch.object(api_module, "create_user") as mock_create, \
                 patch.object(api_module, "generate_verification_token", return_value="tok"), \
                 patch.object(api_module, "_send_verification_email"), \
                 patch.object(api_module, "_notify_founder_registration", side_effect=_boom), \
                 patch.object(handler, "_rate_limited", return_value=False, create=True):
                mock_create.return_value = {"id": 8, "email": _REGISTER_BODY["email"]}
                handler._handle_auth_register()

            payload, status = handler._sent[-1]
            assert status == 201 and payload.get("ok") is True
            # The daemon notify thread must have run and raised — captured here,
            # not leaked to teardown.
            assert raised.wait(timeout=3.0), "notify thread did not run"
            assert captured_exc and isinstance(captured_exc[0], RuntimeError)
        finally:
            threading.excepthook = original_hook

    def test_helper_swallows_request_errors(self):
        """Direct call: requests.post raising must not propagate."""
        with patch.object(api_module, "TELEGRAM_BOT_TOKEN", "x"), \
             patch.object(api_module, "TELEGRAM_CHAT_ID", "1"), \
             patch.object(api_module._req, "post", side_effect=Exception("boom")):
            _notify_founder_registration("a@b.com", "Name", "Co")  # must not raise

    def test_helper_noop_when_unconfigured(self):
        """No token/chat_id → no HTTP call at all."""
        with patch.object(api_module, "TELEGRAM_BOT_TOKEN", ""), \
             patch.object(api_module, "TELEGRAM_CHAT_ID", ""), \
             patch.object(api_module._req, "post") as mock_post:
            _notify_founder_registration("a@b.com")
        mock_post.assert_not_called()

    def test_helper_sends_email_in_message(self):
        """Configured helper posts to the admin bot with the email in the text."""
        with patch.object(api_module, "TELEGRAM_BOT_TOKEN", "tkn"), \
             patch.object(api_module, "TELEGRAM_CHAT_ID", "42"), \
             patch.object(api_module._req, "post") as mock_post:
            mock_post.return_value.json.return_value = {"ok": True}
            _notify_founder_registration("a@b.com", "Name", "Co DMCC")
        assert mock_post.called
        url = mock_post.call_args[0][0]
        body = mock_post.call_args[1]["json"]
        assert "tkn" in url and str(body["chat_id"]) == "42"
        assert "a@b.com" in body["text"] and "Co DMCC" in body["text"]
