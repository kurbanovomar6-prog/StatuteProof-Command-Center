"""Regression tests for G4-api security/robustness bugs.

Covered:
- _client_ip must not trust the client-controlled leftmost X-Forwarded-For token
  (rate-limit bypass / brute-force protection).
- _RateLimiter must not leak dict keys once a key's window has fully expired.
- _send_json is one-shot: an oversized body must not yield a double HTTP response.
- verify-email GET must NOT mint a login session (token-in-URL as credential).
"""

from __future__ import annotations

import json
import sys
import time
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api as api_module
from app.api import _Handler, _RateLimiter


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_handler(
    method: str = "POST",
    path: str = "/",
    body: dict | None = None,
    headers: dict | None = None,
    real_send: bool = False,
    content_length: int | None = None,
) -> _Handler:
    """Build a minimal _Handler with mocked socket infra.

    headers: a dict of header name -> value (case-sensitive keys as sent).
    real_send: keep the real _send_json (writes to wfile) for double-response
    tests; otherwise record (data, status) tuples.
    content_length: override the Content-Length header value.
    """
    raw_body = json.dumps(body or {}).encode()
    header_map = dict(headers or {})
    if content_length is None:
        header_map.setdefault("Content-Length", str(len(raw_body)))
    else:
        header_map["Content-Length"] = str(content_length)

    request = MagicMock()
    request.makefile.return_value = BytesIO(raw_body)

    handler = _Handler.__new__(_Handler)
    handler.command = method
    handler.path = path
    handler.request = request
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(raw_body)
    handler.wfile = BytesIO()
    handler.close_connection = False
    # Attributes BaseHTTPRequestHandler.send_response()/log_request expect.
    handler.requestline = f"{method} {path} HTTP/1.1"
    handler.request_version = "HTTP/1.1"
    handler.protocol_version = "HTTP/1.1"
    handler.log_request = lambda *a, **k: None  # type: ignore[method-assign]
    handler.log_message = lambda *a, **k: None  # type: ignore[method-assign]

    hdrs = MagicMock()
    hdrs.get = lambda key, default="": header_map.get(key, default)
    handler.headers = hdrs

    if not real_send:
        sent: list[tuple[dict, int]] = []

        def _fake_send_json(data: dict, status: int = 200, **kw):
            sent.append((data, status))

        handler._send_json = _fake_send_json  # type: ignore[method-assign]
        handler._sent = sent  # type: ignore[attr-defined]

    return handler


# ── Bug: X-Forwarded-For spoofing defeats rate limiting ──────────────────────

def test_client_ip_ignores_client_controlled_leftmost_xff():
    """Behind a proxy that appends the real IP, the trusted hop is the rightmost.

    A client that spoofs a fresh leftmost XFF token each request must still map
    to a stable IP (the proxy-appended rightmost value / X-Real-IP), so the
    limiter key does not change per request.
    """
    # Attacker spoofs leftmost; nginx appended the real peer as rightmost.
    h1 = _make_handler(headers={"X-Forwarded-For": "1.1.1.1, 203.0.113.9"})
    h2 = _make_handler(headers={"X-Forwarded-For": "2.2.2.2, 203.0.113.9"})
    assert h1._client_ip() == "203.0.113.9"
    assert h2._client_ip() == h1._client_ip()


def test_client_ip_prefers_x_real_ip():
    """X-Real-IP (nginx overwrites client value) takes precedence."""
    h = _make_handler(
        headers={"X-Real-IP": "198.51.100.7", "X-Forwarded-For": "1.1.1.1, 198.51.100.7"}
    )
    assert h._client_ip() == "198.51.100.7"


def test_rate_limiter_not_bypassed_by_spoofed_leftmost_xff():
    """Repeated logins with distinct leftmost XFF must still be rate limited."""
    limiter = _RateLimiter(3, 3600)
    keys = set()
    for i in range(10):
        h = _make_handler(headers={"X-Forwarded-For": f"9.9.9.{i}, 203.0.113.9"})
        keys.add(f"{h._client_ip()}:login")
    # All requests share one trusted IP → one limiter key, not 10.
    assert keys == {"203.0.113.9:login"}
    # And that single key is actually throttled after `limit` allows.
    allowed = [limiter.is_allowed("203.0.113.9:login") for _ in range(10)]
    assert allowed.count(True) == 3
    assert allowed.count(False) == 7


# ── Bug: rate-limiter dict grows unbounded ───────────────────────────────────

def test_rate_limiter_prunes_expired_keys():
    """Keys whose window fully expired must be removed, not retained forever."""
    limiter = _RateLimiter(5, 60)
    base = 1_000_000.0
    limiter._last_sweep = base  # deterministic sweep clock
    with patch("app.api.time.monotonic", return_value=base):
        for i in range(50):
            limiter.is_allowed(f"ip-{i}:label")
    assert len(limiter._hits) == 50  # all fresh

    # Advance past the window + sweep interval, then touch a single new key.
    with patch("app.api.time.monotonic", return_value=base + 200):
        limiter.is_allowed("survivor:label")

    # The 50 expired keys must have been swept; only the survivor remains.
    assert "survivor:label" in limiter._hits
    for i in range(50):
        assert f"ip-{i}:label" not in limiter._hits, (
            f"expired key ip-{i}:label was never garbage collected"
        )


def test_rate_limiter_denied_request_still_prunes_over_time():
    """Even a saturated key does not prevent eventual sweeping of stale keys."""
    limiter = _RateLimiter(2, 30)
    base = 500.0
    limiter._last_sweep = base  # deterministic sweep clock
    with patch("app.api.time.monotonic", return_value=base):
        for i in range(5):
            limiter.is_allowed(f"stale-{i}:x")
    with patch("app.api.time.monotonic", return_value=base + 100):
        limiter.is_allowed("fresh:x")
    assert len(limiter._hits) == 1


# ── Bug: double HTTP response on oversized body ──────────────────────────────

def test_send_json_is_one_shot():
    """A second _send_json on the same connection must be a no-op (no double body)."""
    h = _make_handler(real_send=True)
    h._send_json({"ok": False, "message": "too large"}, 413)
    first = h.wfile.getvalue()
    h._send_json({"ok": False, "message": "second"}, 400)
    second = h.wfile.getvalue()
    assert first == second, "a second response was written to the socket"
    # Exactly one HTTP status line.
    assert second.count(b"HTTP/1.0 ") + second.count(b"HTTP/1.1 ") == 1


def test_read_json_oversized_body_single_response_and_closes():
    """Oversized body: _read_json returns {} and only one 413 is ever sent."""
    h = _make_handler(real_send=True, content_length=api_module._Handler._MAX_BODY_BYTES + 1)
    result = h._read_json()
    assert result == {}
    assert h.close_connection is True
    wire = h.wfile.getvalue()
    assert b"413" in wire
    # Simulate the caller emitting its own error on the empty body.
    h._send_json({"ok": False, "message": "Name and email are required."}, 400)
    wire2 = h.wfile.getvalue()
    assert wire2 == wire, "handler emitted a second response after the 413"


# ── Bug: verify-email GET auto-creates a login session ───────────────────────

def test_verify_email_does_not_set_session_cookie():
    """A successful email verification GET must not return a Set-Cookie/session."""
    captured: list[tuple] = []

    def _fake_send_json(data, status=200, extra_headers=None, **kw):
        captured.append((data, status, extra_headers))

    h = _make_handler("GET", "/api/auth/verify-email?token=T")
    h._send_json = _fake_send_json  # type: ignore[method-assign]

    with patch("app.api.consume_verification_token", return_value=42) as consume, \
         patch("app.api.mark_email_verified") as mark, \
         patch("app.api.create_session") as create_sess:
        h._handle_auth_verify_email()

    consume.assert_called_once_with("T")
    mark.assert_called_once_with(42)
    # No session should be created and no Set-Cookie returned.
    create_sess.assert_not_called()
    assert captured, "no response emitted"
    data, status, extra_headers = captured[-1]
    assert status == 200 and data.get("verified") is True
    header_names = [k for (k, _v) in (extra_headers or [])]
    assert "Set-Cookie" not in header_names, (
        "verify-email must not mint a login session cookie"
    )
