"""Registration must not answer "check your inbox" when nothing was sent.

The verification mail was fired into a daemon thread whose result was discarded,
so a customer whose mail silently failed — misconfigured provider, sending
disabled, a bounce — saw a success screen and then could not sign in, because
login refuses an unverified account. There was no signal anywhere: not in the
response, not in the logs.

The send is still off the request thread (every provider path in
app/email_delivery.py allows timeout=15, far too long to hold a signup on), but
the result is waited for briefly and reported. Three outcomes stay distinct:
sent, failed, and still-in-flight — the last is NOT reported as either.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api  # noqa: E402,F401  (resolves the api <-> mixin import chain first)
import app.api_auth as api_auth  # noqa: E402

from test_api_coverage_uplift import _last, _make_handler  # noqa: E402

REGISTRATION = {
    "email": "newcustomer@example.test",
    "password": "a-long-enough-password",
    "full_name": "New Customer",
}


@pytest.fixture(autouse=True)
def _quiet_founder_notification(monkeypatch):
    """The admin-bot ping is best-effort and irrelevant here."""
    monkeypatch.setattr(api_auth, "_notify_founder_registration", lambda *a, **k: None)


def _register(monkeypatch, sender) -> dict:
    monkeypatch.setattr(api_auth, "_send_verification_email", sender)
    handler = _make_handler("POST", "/api/auth/register", body=REGISTRATION)
    handler._public_base_url = lambda: "https://statuteproof.com"  # type: ignore[method-assign]
    handler._handle_auth_register()
    data, status, _ = _last(handler)
    assert status == 201, data
    return data


def test_a_successful_send_is_reported_as_sent(monkeypatch):
    data = _register(monkeypatch, lambda *a, **k: {"ok": True, "status": "sent"})

    assert data["verification_email_sent"] is True
    assert "check your inbox" in data["message"].lower()


def test_a_failed_send_is_not_dressed_up_as_success(monkeypatch):
    """The account exists either way — the customer has to be told which."""
    data = _register(monkeypatch, lambda *a, **k: {"ok": False, "status": "failed"})

    assert data["ok"] is True                      # the account WAS created
    assert data["verification_email_sent"] is False
    assert "could not send" in data["message"].lower()
    assert "resend" in data["message"].lower()


def test_a_raising_sender_is_reported_as_failed_not_as_a_500(monkeypatch):
    def _boom(*_args, **_kwargs):
        raise RuntimeError("smtp unreachable")

    data = _register(monkeypatch, _boom)

    assert data["ok"] is True
    assert data["verification_email_sent"] is False


def test_a_slow_send_is_reported_as_unknown_rather_than_invented(monkeypatch):
    """Past the wait we genuinely do not know. Saying "sent" would be a guess,
    and saying "failed" would be a different guess."""
    monkeypatch.setattr(api_auth, "_VERIFICATION_SEND_WAIT_S", 0.05)

    def _slow(*_args, **_kwargs):
        time.sleep(0.5)
        return {"ok": True}

    data = _register(monkeypatch, _slow)

    assert data["verification_email_sent"] is None
    assert "still sending" in data["message"].lower()


def test_registration_does_not_block_for_the_full_provider_timeout(monkeypatch):
    """Provider paths allow 15s; a signup must not hold the request that long."""
    monkeypatch.setattr(api_auth, "_VERIFICATION_SEND_WAIT_S", 0.2)

    def _slow(*_args, **_kwargs):
        time.sleep(3)
        return {"ok": True}

    started = time.monotonic()
    _register(monkeypatch, _slow)
    elapsed = time.monotonic() - started

    assert elapsed < 2, f"registration waited {elapsed:.1f}s on a hanging provider"


def test_the_verification_link_points_at_the_page_not_the_api(monkeypatch):
    """The link the customer clicks must land on a page; /api/... renders JSON."""
    seen: dict = {}

    def _capture(recipient, url, *a, **k):
        seen["url"] = url
        return {"ok": True}

    _register(monkeypatch, _capture)

    assert seen["url"].startswith("https://statuteproof.com/verify-email?token=")
    assert "/api/auth/verify-email" not in seen["url"]
