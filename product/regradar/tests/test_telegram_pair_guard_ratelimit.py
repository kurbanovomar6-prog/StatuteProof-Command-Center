"""Regression coverage for the Telegram pairing status/unlink hardening.

Two defense-in-depth gaps were closed on the customer-facing Telegram pairing
handlers in ``app.api_telegram``:

  * ``_handle_telegram_pair_unlink`` severs alert-delivery configuration — a
    settings mutation, exactly like ``profile_update`` / ``plan_set`` — yet it
    ran ``unlink_telegram`` straight after ``require_auth`` with NO RBAC gate.
    It now calls ``self._rbac_guard(user, SETTINGS_EDIT, ...)`` so a read-only
    auditor seat is denied 403 and the binding is never cleared.
  * ``pair/status`` and ``pair/unlink`` had NO per-IP rate limiter, unlike every
    sibling endpoint (``pair/generate``, ``account/test``). Both now consult a
    dedicated ``_RateLimiter`` before doing any work.

These drive the REAL ``_Handler`` the same way ``tests/test_api_coverage_uplift``
does (``__new__`` + captured ``_send_json``), asserting real status codes.
"""
from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api as api
import app.api_telegram as api_telegram
from app.api import _Handler, _RateLimiter


def _make_handler(method: str, path: str, *, ip: str = "10.9.9.1") -> _Handler:
    """Build a real _Handler with a captured ``_send_json`` and a fixed client IP.

    A FIXED X-Real-IP (not the per-call unique IP the broad suite uses) lets the
    rate-limit tests drive repeated calls into the SAME limiter bucket.
    """
    header_map = {"Content-Length": "0", "X-Real-IP": ip}
    handler = _Handler.__new__(_Handler)
    handler.command = method
    handler.path = path
    handler.request = MagicMock()
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(b"")
    handler.wfile = BytesIO()
    handler.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": header_map.get(key, default)
    handler.headers = hdrs

    sent: list = []
    handler._send_json = (  # type: ignore[method-assign]
        lambda data, status=200, extra_headers=None: sent.append((data, status, extra_headers))
    )
    handler._sent = sent  # type: ignore[attr-defined]
    return handler


def _auth_as(monkeypatch, user: dict | None) -> None:
    # ``require_auth`` is read as a bare global inside the moved mixin module.
    monkeypatch.setattr(api, "require_auth", lambda handler: user)
    monkeypatch.setattr(api_telegram, "require_auth", lambda handler: user)


def _last(handler: _Handler):
    return handler._sent[-1]  # type: ignore[attr-defined]


# ── (A) unlink is RBAC-gated as a settings mutation ───────────────────────────

def test_unlink_denied_when_settings_edit_not_permitted(monkeypatch):
    """A seat that fails the SETTINGS_EDIT gate gets 403 and the binding stays."""
    _auth_as(monkeypatch, {"id": 42})
    called = {"unlink": False}
    monkeypatch.setattr(
        api_telegram, "unlink_telegram",
        lambda uid: called.__setitem__("unlink", True),
    )
    handler = _make_handler("POST", "/api/telegram/pair/unlink")
    # Auditor seat: the guard denies and emits its own 403 (mirrors profile_update).
    handler._rbac_guard = lambda user, action, **kw: (  # type: ignore[method-assign]
        handler._sent.append(({"ok": False}, 403, None)) or False
    )
    handler._handle_telegram_pair_unlink()

    _, status, _ = _last(handler)
    assert status == 403
    assert called["unlink"] is False  # alert-delivery config was NOT severed


def test_unlink_passes_settings_edit_action_to_guard(monkeypatch):
    """The unlink handler gates on SETTINGS_EDIT specifically, not some other action."""
    from app import rbac_runtime

    _auth_as(monkeypatch, {"id": 42})
    monkeypatch.setattr(api_telegram, "unlink_telegram", lambda uid: None)
    handler = _make_handler("POST", "/api/telegram/pair/unlink")
    seen = {}
    handler._rbac_guard = lambda user, action, **kw: (  # type: ignore[method-assign]
        seen.setdefault("action", action) is None or True
    )
    handler._handle_telegram_pair_unlink()

    assert seen["action"] == rbac_runtime.SETTINGS_EDIT
    _, status, _ = _last(handler)
    assert status == 200


def test_unlink_allowed_when_guard_permits(monkeypatch):
    """An owner seat (guard True) clears only the caller's binding and returns 200."""
    _auth_as(monkeypatch, {"id": 77})
    seen = {}
    monkeypatch.setattr(api_telegram, "unlink_telegram",
                        lambda uid: seen.__setitem__("uid", uid))
    handler = _make_handler("POST", "/api/telegram/pair/unlink")
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_telegram_pair_unlink()

    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True
    assert seen["uid"] == 77


# ── (B) status and unlink are rate-limited ────────────────────────────────────

def test_unlink_is_rate_limited(monkeypatch):
    """Once the unlink limiter is exhausted the handler returns 429 before any work."""
    _auth_as(monkeypatch, {"id": 5})
    called = {"unlink": 0}
    monkeypatch.setattr(
        api_telegram, "unlink_telegram",
        lambda uid: called.__setitem__("unlink", called["unlink"] + 1),
    )
    # Swap in a limit-1 limiter so the second call trips deterministically.
    monkeypatch.setattr(api_telegram, "_PAIR_UNLINK_LIMITER", _RateLimiter(1, 3600))

    first = _make_handler("POST", "/api/telegram/pair/unlink", ip="10.9.9.5")
    first._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    first._handle_telegram_pair_unlink()
    assert _last(first)[1] == 200

    second = _make_handler("POST", "/api/telegram/pair/unlink", ip="10.9.9.5")
    second._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    second._handle_telegram_pair_unlink()
    assert _last(second)[1] == 429
    assert called["unlink"] == 1  # the throttled call never reached unlink_telegram


def test_status_is_rate_limited(monkeypatch):
    """Once the status limiter is exhausted the handler returns 429 before any work."""
    _auth_as(monkeypatch, {"id": 5})
    called = {"status": 0}
    monkeypatch.setattr(
        api_telegram, "get_pairing_status",
        lambda uid: called.__setitem__("status", called["status"] + 1) or {"linked": False},
    )
    monkeypatch.setattr(api_telegram, "_PAIR_STATUS_LIMITER", _RateLimiter(1, 3600))

    first = _make_handler("GET", "/api/telegram/pair/status", ip="10.9.9.6")
    first._handle_telegram_pair_status()
    assert _last(first)[1] == 200

    second = _make_handler("GET", "/api/telegram/pair/status", ip="10.9.9.6")
    second._handle_telegram_pair_status()
    assert _last(second)[1] == 429
    assert called["status"] == 1  # the throttled call never reached get_pairing_status
