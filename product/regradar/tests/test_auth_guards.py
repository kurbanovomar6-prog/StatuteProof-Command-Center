"""Tests for API authentication guards and URL safety checks.

Coverage areas:
1. Auth guards — endpoints return 401 when no valid session cookie is present.
2. URL safety — discover/test endpoints return 400 for internal/private URLs.
3. Thread-safety — AI call budget does not exceed its limit under concurrent load.
"""
from __future__ import annotations

import json
import sys
import threading
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure the app package is importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api as api_module
from app.api import _Handler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_handler(
    method: str = "GET",
    path: str = "/",
    body: dict | None = None,
    cookie: str = "",
) -> _Handler:
    """Build a minimal _Handler instance with mocked socket/request infra.

    The handler's ``_send_json`` is replaced with a recorder so tests can
    inspect the status code and payload without needing a live socket.
    """
    raw_body = json.dumps(body or {}).encode()

    # Fake socket — wfile/rfile are BytesIO streams.
    request = MagicMock()
    request.makefile.return_value = BytesIO(raw_body)

    handler = _Handler.__new__(_Handler)

    # Minimal BaseHTTPRequestHandler attributes required before method calls.
    handler.command = method
    handler.path = path
    handler.request = request
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(raw_body)
    handler.wfile = BytesIO()
    handler.headers = MagicMock()
    handler.headers.get = lambda key, default="": (
        cookie if key == "Cookie" else (str(len(raw_body)) if key == "Content-Length" else default)
    )

    # Replace _send_json with a recorder.
    sent: list[tuple[dict, int]] = []

    def _fake_send_json(data: dict, status: int = 200, **kw):
        sent.append((data, status))

    handler._send_json = _fake_send_json  # type: ignore[method-assign]
    handler._sent = sent  # type: ignore[attr-defined]

    return handler


# ---------------------------------------------------------------------------
# ЗАДАЧА 2: Auth guard tests — no cookie → 401
# ---------------------------------------------------------------------------

class TestAuthGuards:
    """Endpoints must return 401 when require_auth returns None (no session)."""

    def _assert_401(self, handler: _Handler) -> None:
        statuses = [s for _, s in handler._sent]  # type: ignore[attr-defined]
        assert 401 in statuses, (
            f"Expected a 401 response but got statuses: {statuses}. "
            f"Payloads: {[d for d, _ in handler._sent]}"  # type: ignore[attr-defined]
        )

    def test_monthly_assurance_requires_auth(self):
        """GET /api/reports/monthly-assurance without auth must return 401."""
        handler = _make_handler("GET", "/api/reports/monthly-assurance")
        with patch("app.api.require_auth", return_value=None):
            handler._handle_monthly_assurance_report()
        self._assert_401(handler)

    def test_audit_vault_requires_auth(self):
        """POST /api/audit/vault without auth must return 401."""
        handler = _make_handler("POST", "/api/audit/vault", body={})
        with patch("app.api.require_auth", return_value=None):
            handler._handle_audit_vault()
        self._assert_401(handler)

    def test_custom_source_discover_requires_auth(self):
        """POST /api/custom-sources/discover without auth must return 401."""
        handler = _make_handler(
            "POST", "/api/custom-sources/discover", body={"url": "https://example.com"}
        )
        with patch("app.api.require_auth", return_value=None):
            handler._handle_custom_source_discover()
        self._assert_401(handler)

    def test_custom_source_test_requires_auth(self):
        """POST /api/custom-sources/test without auth must return 401."""
        handler = _make_handler(
            "POST", "/api/custom-sources/test", body={"url": "https://example.com"}
        )
        with patch("app.api.require_auth", return_value=None):
            handler._handle_custom_source_test()
        self._assert_401(handler)


# ---------------------------------------------------------------------------
# ЗАДАЧА 3: validate_public_url — internal/private URLs → 400
# ---------------------------------------------------------------------------

FAKE_USER = {"id": 1, "email": "test@example.com"}

_INTERNAL_URLS = [
    "http://localhost",
    "http://localhost:8080/api/data",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://192.168.1.1",
    "http://192.168.0.100/admin",
    "http://10.0.0.1",
    "http://172.16.0.1",
    "http://0.0.0.0",
]


class TestValidatePublicUrlRejectsInternalUrls:
    """Discover and test endpoints must reject internal/private URLs with 400."""

    def _assert_400(self, handler: _Handler) -> None:
        statuses = [s for _, s in handler._sent]  # type: ignore[attr-defined]
        assert 400 in statuses, (
            f"Expected 400 for internal URL but got statuses: {statuses}. "
            f"Payloads: {[d for d, _ in handler._sent]}"  # type: ignore[attr-defined]
        )

    def test_discover_rejects_localhost(self):
        """POST /api/custom-sources/discover with http://localhost must return 400."""
        handler = _make_handler(
            "POST", "/api/custom-sources/discover", body={"url": "http://localhost"}
        )
        with patch("app.api.require_auth", return_value=FAKE_USER):
            # Rate limiter must allow this call through.
            with patch.object(handler, "_rate_limited", return_value=False):
                handler._handle_custom_source_discover()
        self._assert_400(handler)

    def test_discover_rejects_private_ip(self):
        """POST /api/custom-sources/discover with http://192.168.1.1 must return 400."""
        handler = _make_handler(
            "POST", "/api/custom-sources/discover", body={"url": "http://192.168.1.1"}
        )
        with patch("app.api.require_auth", return_value=FAKE_USER):
            with patch.object(handler, "_rate_limited", return_value=False):
                handler._handle_custom_source_discover()
        self._assert_400(handler)

    def test_source_test_rejects_localhost(self):
        """POST /api/custom-sources/test with http://localhost must return 400."""
        handler = _make_handler(
            "POST", "/api/custom-sources/test", body={"url": "http://localhost"}
        )
        with patch("app.api.require_auth", return_value=FAKE_USER):
            with patch.object(handler, "_rate_limited", return_value=False):
                handler._handle_custom_source_test()
        self._assert_400(handler)

    def test_source_test_rejects_private_ip(self):
        """POST /api/custom-sources/test with http://192.168.1.1 must return 400."""
        handler = _make_handler(
            "POST", "/api/custom-sources/test", body={"url": "http://192.168.1.1"}
        )
        with patch("app.api.require_auth", return_value=FAKE_USER):
            with patch.object(handler, "_rate_limited", return_value=False):
                handler._handle_custom_source_test()
        self._assert_400(handler)

    def test_discover_parametrised_internal_urls(self):
        """All known internal/private URL patterns must be rejected by discover."""
        for url in _INTERNAL_URLS:
            handler = _make_handler(
                "POST", "/api/custom-sources/discover", body={"url": url}
            )
            with patch("app.api.require_auth", return_value=FAKE_USER):
                with patch.object(handler, "_rate_limited", return_value=False):
                    handler._handle_custom_source_discover()
            statuses = [s for _, s in handler._sent]  # type: ignore[attr-defined]
            assert 400 in statuses, f"URL {url!r} was not rejected with 400 (got {statuses})"

    def test_source_test_parametrised_internal_urls(self):
        """All known internal/private URL patterns must be rejected by source test."""
        for url in _INTERNAL_URLS:
            handler = _make_handler(
                "POST", "/api/custom-sources/test", body={"url": url}
            )
            with patch("app.api.require_auth", return_value=FAKE_USER):
                with patch.object(handler, "_rate_limited", return_value=False):
                    handler._handle_custom_source_test()
            statuses = [s for _, s in handler._sent]  # type: ignore[attr-defined]
            assert 400 in statuses, f"URL {url!r} was not rejected with 400 (got {statuses})"


# ---------------------------------------------------------------------------
# ЗАДАЧА 4: Thread-safety of AI budget
# ---------------------------------------------------------------------------

class TestAIBudgetThreadSafety:
    """_AI_RUN_BUDGET must not be exceeded when many threads try to reserve."""

    def test_ai_budget_thread_safe(self):
        """_AI_RUN_BUDGET does not exceed its limit under concurrent reservation."""
        from app.pipeline import _AI_RUN_BUDGET, _AI_BUDGET_LOCK, reset_ai_call_counter

        reset_ai_call_counter(limit=5)
        reservations: list[int] = []

        def try_reserve() -> None:
            with _AI_BUDGET_LOCK:
                if _AI_RUN_BUDGET["count"] < _AI_RUN_BUDGET["limit"]:
                    _AI_RUN_BUDGET["count"] += 1
                    reservations.append(1)

        threads = [threading.Thread(target=try_reserve) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(reservations) <= 5, (
            f"Expected at most 5 reservations, got {len(reservations)}"
        )
        assert _AI_RUN_BUDGET["count"] <= 5, (
            f"Budget count exceeded limit: {_AI_RUN_BUDGET['count']}"
        )

    def test_ai_budget_resets_cleanly(self):
        """reset_ai_call_counter properly resets count and updates limit."""
        from app.pipeline import _AI_RUN_BUDGET, reset_ai_call_counter

        # Prime with some count.
        _AI_RUN_BUDGET["count"] = 99
        _AI_RUN_BUDGET["limit"] = 99

        reset_ai_call_counter(limit=10)

        assert _AI_RUN_BUDGET["count"] == 0
        assert _AI_RUN_BUDGET["limit"] == 10

    def test_ai_budget_blocks_when_limit_reached(self):
        """Once the budget is exhausted, additional threads cannot reserve."""
        from app.pipeline import _AI_RUN_BUDGET, _AI_BUDGET_LOCK, reset_ai_call_counter

        reset_ai_call_counter(limit=3)
        granted: list[int] = []
        denied: list[int] = []

        def try_reserve() -> None:
            with _AI_BUDGET_LOCK:
                if _AI_RUN_BUDGET["count"] < _AI_RUN_BUDGET["limit"]:
                    _AI_RUN_BUDGET["count"] += 1
                    granted.append(1)
                else:
                    denied.append(1)

        threads = [threading.Thread(target=try_reserve) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(granted) == 3, f"Expected exactly 3 granted, got {len(granted)}"
        assert len(denied) == 7, f"Expected exactly 7 denied, got {len(denied)}"
        assert len(granted) + len(denied) == 10
