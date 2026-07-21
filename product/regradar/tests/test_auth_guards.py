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
import time
from contextlib import ExitStack
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
    """The REAL per-run AI reserve in ``app.pipeline.run_pipeline`` must honour its budget.

    Scope note (honest): the production reserve/commit is an INLINE
    check-then-increment inside ``run_pipeline`` (``app/pipeline.py``), guarded by
    the module-level ``_AI_BUDGET_LOCK`` over ``_AI_RUN_BUDGET`` — it is NOT
    exposed as an importable function. The previous tests re-implemented that
    predicate locally and asserted against their OWN copy, so they passed even if
    production were broken (a tautology). These tests instead drive the reserve
    through the REAL ``run_pipeline`` code path with only the I/O boundary mocked,
    and assert the production budget invariant: the real ``analyze_change_with_ai``
    fires at most ``limit`` times regardless of concurrency, and once the budget
    is spent ``run_pipeline`` reports a "call limit ... reached" skip reason.
    """

    # Old vs new content that produces a genuine, non-shrinking CHANGED diff so
    # run_pipeline reaches the AI-reserve branch (not is_new, above risk floor).
    _OLD = (
        "Regulatory paragraph one about AML systems and controls.\n\n"
        "Paragraph two about ongoing monitoring."
    )
    _NEW = (
        "Regulatory paragraph one about AML systems and controls.\n\n"
        "Paragraph two about ongoing monitoring and a new filing duty within 30 days."
    )

    def _pipeline_patches(self, pipeline, fake_ai):
        """Mock only run_pipeline's I/O boundary; leave the real reserve intact."""
        old_hash = pipeline.stable_content_hash(
            pipeline.normalize_for_change_hash(self._OLD)
        )
        return [
            patch.object(pipeline, "get_adapter_for_url", return_value=None),
            patch.object(pipeline, "fetch_page", return_value="<html><body>x</body></html>"),
            patch.object(
                pipeline, "extract_best_text",
                return_value={"text": self._NEW, "method": "test"},
            ),
            patch.object(pipeline, "detect_language_hint", return_value="en"),
            patch.object(
                pipeline, "get_latest_document",
                return_value={"content": self._OLD, "content_hash": old_hash},
            ),
            patch.object(
                pipeline, "analyze_risk",
                return_value={"risk_level": "HIGH", "reason": "test"},
            ),
            patch.object(pipeline, "save_document", return_value=None),
            patch.object(pipeline, "ENABLE_AI_ANALYSIS", True),
            patch.object(pipeline, "ENABLE_TELEGRAM_ALERTS", False),
            # Patched on app.ai because run_pipeline imports it at call time.
            patch("app.ai.analyze_change_with_ai", fake_ai),
        ]

    def test_reserve_thread_safe_via_production_pipeline(self):
        """Under concurrency, the real reserve grants AT MOST ``limit`` AI calls."""
        import app.pipeline as pipeline

        LIMIT, N_THREADS = 5, 25
        calls: list[int] = []
        calls_lock = threading.Lock()

        def fake_ai(url, diff_result, rule_risk, source_language="unknown", output_language="en"):
            with calls_lock:
                calls.append(1)
            time.sleep(0.01)  # widen the race window so a broken reserve over-counts
            return None

        with ExitStack() as stack:
            for cm in self._pipeline_patches(pipeline, fake_ai):
                stack.enter_context(cm)
            pipeline.reset_ai_call_counter(limit=LIMIT)
            threads = [
                threading.Thread(
                    target=pipeline.run_pipeline, args=("https://example.test/reg",)
                )
                for _ in range(N_THREADS)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

        assert len(calls) == LIMIT, (
            f"real AI reservations must equal the budget {LIMIT} "
            f"({N_THREADS} threads contended), got {len(calls)}"
        )
        assert pipeline._AI_RUN_BUDGET["count"] <= LIMIT

    def test_reserve_denies_calls_once_exhausted_via_production_pipeline(self):
        """Once the budget is spent, further run_pipeline calls skip the AI call."""
        import app.pipeline as pipeline

        LIMIT = 2
        calls: list[int] = []

        def fake_ai(url, diff_result, rule_risk, source_language="unknown", output_language="en"):
            calls.append(1)
            return None

        with ExitStack() as stack:
            for cm in self._pipeline_patches(pipeline, fake_ai):
                stack.enter_context(cm)
            pipeline.reset_ai_call_counter(limit=LIMIT)
            results = [
                pipeline.run_pipeline("https://example.test/reg") for _ in range(4)
            ]

        assert len(calls) == LIMIT, (
            f"budget must cap real AI calls at {LIMIT}, got {len(calls)}"
        )
        exhausted = [
            r for r in results if "call limit" in str(r.get("ai_skipped_reason", ""))
        ]
        assert exhausted, (
            "once exhausted, run_pipeline must report a 'call limit ... reached' "
            "skip reason instead of calling the model again"
        )

    def test_ai_budget_resets_cleanly(self):
        """reset_ai_call_counter (real production reset) zeroes count and sets limit."""
        from app.pipeline import _AI_RUN_BUDGET, reset_ai_call_counter

        # Prime with some count.
        _AI_RUN_BUDGET["count"] = 99
        _AI_RUN_BUDGET["limit"] = 99

        reset_ai_call_counter(limit=10)

        assert _AI_RUN_BUDGET["count"] == 0
        assert _AI_RUN_BUDGET["limit"] == 10


# ---------------------------------------------------------------------------
# GET /api/evidence and GET /api/briefs must be rate limited (resource-bounds)
# ---------------------------------------------------------------------------

class TestHeavyReadRateLimits:
    """Heavy authenticated reads must be throttled, not loopable to pin the box."""

    def test_evidence_list_is_rate_limited(self):
        """GET /api/evidence returns 429 once its per-IP budget is exhausted."""
        handler = _make_handler("GET", "/api/evidence")
        user = {"id": 1, "email": "a@example.com"}
        with patch("app.api.require_auth", return_value=user), \
             patch("app.api_evidence.require_auth", return_value=user), \
             patch.object(api_module._EVIDENCE_LIST_LIMITER, "is_allowed", return_value=False):
            handler._handle_evidence_list()
        statuses = [s for _, s in handler._sent]  # type: ignore[attr-defined]
        assert 429 in statuses, f"expected 429 (rate limited) but got {statuses}"

    def test_briefs_list_is_rate_limited(self):
        """GET /api/briefs returns 429 once its per-IP budget is exhausted."""
        handler = _make_handler("GET", "/api/briefs")
        user = {"id": 1, "email": "a@example.com"}
        with patch("app.api.require_auth", return_value=user), \
             patch.object(api_module._BRIEFS_LIST_LIMITER, "is_allowed", return_value=False):
            handler._handle_briefs_list()
        statuses = [s for _, s in handler._sent]  # type: ignore[attr-defined]
        assert 429 in statuses, f"expected 429 (rate limited) but got {statuses}"

    def test_evidence_and_briefs_have_independent_buckets(self):
        """The two limiters are distinct objects — one bucket cannot starve the other."""
        assert api_module._EVIDENCE_LIST_LIMITER is not api_module._BRIEFS_LIST_LIMITER


# ---------------------------------------------------------------------------
# Custom-source add must not expose a cross-tenant URL-existence oracle
# ---------------------------------------------------------------------------

class TestCustomSourceAddNoCrossTenantOracle:
    """A URL added by another tenant must not be revealed by the add-source 409."""

    def test_add_does_not_reveal_another_tenants_url(self, tmp_path, monkeypatch):
        import app.source_tester as source_tester

        other_url = "https://private-portal.example.gov/reg"
        sources_path = tmp_path / "sources.json"
        sources_path.write_text(
            json.dumps([
                {"source_id": "custom-deadbeef", "url": other_url,
                 "custom": True, "owner_user_id": 202},
            ]),
            encoding="utf-8",
        )
        monkeypatch.setattr(source_tester, "_SOURCES_PATH", sources_path)

        handler = _make_handler(
            "POST", "/api/custom-sources",
            body={"url": other_url, "name": "X", "legal_confirmed": True},
        )
        user_a = {"id": 101, "email": "a@example.com"}
        with patch("app.api.require_auth", return_value=user_a), \
             patch.object(handler, "_rbac_guard", return_value=True), \
             patch("app.source_tester.validate_public_url", return_value=(True, "")), \
             patch("app.source_intake.run_source_intake",
                   return_value={"status": "READINESS_FAILED",
                                 "failure_reason": "n/a", "remediation_hint": ""}):
            handler._handle_custom_sources_add()

        statuses = [s for _, s in handler._sent]  # type: ignore[attr-defined]
        payloads = [d for d, _ in handler._sent]  # type: ignore[attr-defined]
        # The oracle 409 ("already in ... source list") must NOT fire for a URL
        # that only another tenant owns. The request proceeds to readiness.
        assert 409 not in statuses, f"leaked cross-tenant existence: {payloads}"
        joined = " ".join(str(p.get("message", "")) for p in payloads).lower()
        assert "already in" not in joined

    def test_add_still_rejects_the_owners_own_duplicate(self, tmp_path, monkeypatch):
        import app.source_tester as source_tester

        own_url = "https://my-portal.example.gov/reg"
        sources_path = tmp_path / "sources.json"
        sources_path.write_text(
            json.dumps([
                {"source_id": "custom-cafebabe", "url": own_url,
                 "custom": True, "owner_user_id": 101},
            ]),
            encoding="utf-8",
        )
        monkeypatch.setattr(source_tester, "_SOURCES_PATH", sources_path)

        handler = _make_handler(
            "POST", "/api/custom-sources",
            body={"url": own_url, "name": "X", "legal_confirmed": True},
        )
        user_a = {"id": 101, "email": "a@example.com"}
        with patch("app.api.require_auth", return_value=user_a), \
             patch.object(handler, "_rbac_guard", return_value=True), \
             patch.object(handler, "_require_capability", return_value=True), \
             patch("app.source_tester.validate_public_url", return_value=(True, "")):
            handler._handle_custom_sources_add()

        statuses = [s for _, s in handler._sent]  # type: ignore[attr-defined]
        payloads = [d for d, _ in handler._sent]  # type: ignore[attr-defined]
        assert 409 in statuses, f"owner's own duplicate should 409, got {statuses}"
        joined = " ".join(str(p.get("message", "")) for p in payloads).lower()
        assert "already in your source list" in joined
