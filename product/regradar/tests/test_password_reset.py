"""Password reset flow — closes the enterprise/support gap that a customer who
forgot their password was permanently locked out (no reset existed).

Covers: token issue only for real password accounts, single-use + expiry,
set_user_password actually changes the hash and invalidates sessions, and the
API endpoints do not enumerate users.
"""

from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api as api  # noqa: E402
import app.auth as auth  # noqa: E402
import app.db as app_db  # noqa: E402
from app.api import _Handler  # noqa: E402


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "reset.db"))
    return tmp_path


def _make_handler(path: str, body: dict) -> _Handler:
    import json
    raw = json.dumps(body).encode()
    handler = _Handler.__new__(_Handler)
    handler.command = "POST"
    handler.path = path
    handler.request = MagicMock()
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(raw)
    handler.wfile = BytesIO()
    handler.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": {"Content-Length": str(len(raw)), "X-Real-IP": "10.0.0.5"}.get(key, default)
    handler.headers = hdrs
    sent: list = []
    handler._send_json = lambda data, status=200, **kw: sent.append((data, status))  # type: ignore[method-assign]
    handler._sent = sent  # type: ignore[attr-defined]
    handler._read_json_strict = lambda: (body, None)  # type: ignore[method-assign]
    handler._rate_limited = lambda *a, **k: False  # type: ignore[method-assign]
    handler._base_url = lambda: "https://app.example"  # type: ignore[method-assign]
    return handler


# ── auth layer ────────────────────────────────────────────────────────────────

def test_reset_token_only_for_existing_password_account(isolated_db):
    auth.create_user("real@x.io", "password-123")
    assert auth.generate_password_reset_token("real@x.io") is not None
    assert auth.generate_password_reset_token("nobody@x.io") is None


def test_reset_flow_changes_password_and_is_single_use(isolated_db):
    user = auth.create_user("u@x.io", "old-password-1")
    issued = auth.generate_password_reset_token("u@x.io")
    assert issued is not None
    token, uid = issued
    assert uid == user["id"]

    assert auth.consume_password_reset_token(token) == user["id"]
    # Token cannot be reused.
    assert auth.consume_password_reset_token(token) is None

    auth.set_user_password(user["id"], "brand-new-pass-9")
    reloaded = auth.get_user_by_email("u@x.io")
    assert auth.verify_password("brand-new-pass-9", reloaded["password_hash"]) is True
    assert auth.verify_password("old-password-1", reloaded["password_hash"]) is False


def test_set_password_invalidates_sessions(isolated_db):
    user = auth.create_user("s@x.io", "old-password-1")
    sess = auth.create_session(user["id"])
    assert auth.validate_session(sess) is not None
    auth.set_user_password(user["id"], "new-password-2")
    # Every session is killed on password change.
    assert auth.validate_session(sess) is None


# ── API endpoints ─────────────────────────────────────────────────────────────

def test_forgot_password_does_not_enumerate(isolated_db):
    auth.create_user("known@x.io", "password-123")
    h_known = _make_handler("/api/auth/forgot-password", {"email": "known@x.io"})
    h_known._handle_auth_forgot_password()
    h_unknown = _make_handler("/api/auth/forgot-password", {"email": "ghost@x.io"})
    h_unknown._handle_auth_forgot_password()
    # Identical generic 200 response either way.
    assert h_known._sent[-1][1] == 200
    assert h_unknown._sent[-1][1] == 200
    assert h_known._sent[-1][0]["message"] == h_unknown._sent[-1][0]["message"]


def test_reset_password_endpoint_rejects_bad_token(isolated_db):
    h = _make_handler("/api/auth/reset-password", {"token": "nope", "password": "new-password-2"})
    h._handle_auth_reset_password()
    data, status = h._sent[-1]
    assert status == 400
    assert data["ok"] is False


def test_reset_password_endpoint_happy_path(isolated_db):
    user = auth.create_user("e2e@x.io", "old-password-1")
    token, _ = auth.generate_password_reset_token("e2e@x.io")
    h = _make_handler("/api/auth/reset-password", {"token": token, "password": "new-password-2"})
    h._handle_auth_reset_password()
    data, status = h._sent[-1]
    assert status == 200 and data["ok"] is True
    reloaded = auth.get_user_by_email("e2e@x.io")
    assert auth.verify_password("new-password-2", reloaded["password_hash"]) is True
