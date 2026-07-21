"""Founder Telegram notification on paid-plan intent (POST /api/plan).

Audit 2026-07-20 product_readiness HIGH: `_handle_plan_set` recorded the plan
intent and told the customer "Our team will contact you to activate your
pilot." — but notified NOBODY. The commercial funnel dead-ended in a DB column.

Requirements under test (mirrors tests/test_registration_founder_notify.py):
1. Every successful plan-intent POST fires exactly one best-effort Telegram
   message to the founder via the admin bot (TELEGRAM_BOT_TOKEN +
   TELEGRAM_CHAT_ID) with the plan name and the account email.
2. The notification must NEVER affect the API outcome — Telegram down still
   yields ok=True for the customer.
3. When the admin bot is not configured, the helper is a quiet no-op.
4. An unknown plan → 400 and no notification.
5. Abuse hardening (repair round 2026-07-20): POST /api/plan is throttled per
   IP (_PLAN_INTENT_LIMITER) and re-posting the SAME plan does not re-page the
   founder (set_plan_intent returns ``intent_changed``; the handler pops it
   from the customer payload and only notifies on a real change).
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
import app.api_plan as api_plan_module
import app.db as app_db
from app.api import _Handler, _RateLimiter


# ---------------------------------------------------------------------------
# Helpers (mirrors tests/test_registration_founder_notify.py conventions)
# ---------------------------------------------------------------------------

def _make_handler(body: dict) -> _Handler:
    raw_body = json.dumps(body).encode()

    request = MagicMock()
    request.makefile.return_value = BytesIO(raw_body)

    handler = _Handler.__new__(_Handler)
    handler.command = "POST"
    handler.path = "/api/plan"
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
    handler._rbac_guard = lambda *a, **kw: True  # type: ignore[method-assign]
    return handler


_USER = {"id": 7, "email": "buyer@firm.ae"}

_PLAN_STATE = {
    "plan": "professional",
    "status": "pending_manual_activation",
    "active_capabilities": {},
}


class TestFounderNotifyOnPlanIntent:
    def test_plan_set_fires_exactly_one_founder_notification(self):
        """Successful plan intent → founder paged once with email + plan name."""
        handler = _make_handler({"plan_name": "professional"})
        fired = threading.Event()
        captured: list[tuple[str, str]] = []

        def _fake_notify(email, plan_name):
            captured.append((email, plan_name))
            fired.set()

        with patch.object(api_plan_module, "require_auth", return_value=dict(_USER)), \
             patch("app.plan.set_plan_intent", return_value=dict(_PLAN_STATE)), \
             patch.object(
                 api_plan_module, "_notify_founder_plan_intent", side_effect=_fake_notify
             ):
            handler._handle_plan_set()

        assert handler._sent, "handler sent no response"
        payload, status = handler._sent[-1]
        assert status == 200 and payload.get("ok") is True
        assert "Our team will contact you" in payload.get("message", "")
        assert fired.wait(timeout=3.0), "founder notification was not fired"
        assert captured == [("buyer@firm.ae", "professional")]

    def test_notify_failure_does_not_break_plan_set(self):
        """Notify helper raising inside its daemon thread must not affect ok=True.

        The notify runs fire-and-forget; the daemon thread's exception is
        captured via ``threading.excepthook`` so it is asserted to have fired
        and does not leak into interpreter teardown.
        """
        handler = _make_handler({"plan_name": "professional"})

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
            with patch.object(api_plan_module, "require_auth", return_value=dict(_USER)), \
                 patch("app.plan.set_plan_intent", return_value=dict(_PLAN_STATE)), \
                 patch.object(
                     api_plan_module, "_notify_founder_plan_intent", side_effect=_boom
                 ):
                handler._handle_plan_set()

            payload, status = handler._sent[-1]
            assert status == 200 and payload.get("ok") is True
            assert raised.wait(timeout=3.0), "notify thread did not run"
            assert captured_exc and isinstance(captured_exc[0], RuntimeError)
        finally:
            threading.excepthook = original_hook

    def test_helper_is_noop_without_admin_bot_config(self):
        """No token/chat_id → no HTTP call at all."""
        with patch.object(api_module, "TELEGRAM_BOT_TOKEN", ""), \
             patch.object(api_module, "TELEGRAM_CHAT_ID", ""), \
             patch.object(api_module._req, "post") as mock_post:
            api_module._notify_founder_plan_intent("a@b.c", "professional")
        mock_post.assert_not_called()

    def test_helper_swallows_request_errors(self):
        """Direct call: requests.post raising must not propagate."""
        with patch.object(api_module, "TELEGRAM_BOT_TOKEN", "tkn"), \
             patch.object(api_module, "TELEGRAM_CHAT_ID", "42"), \
             patch.object(api_module._req, "post", side_effect=Exception("boom")):
            api_module._notify_founder_plan_intent("a@b.c", "professional")  # must not raise

    def test_no_notification_on_unknown_plan(self):
        """Unknown plan → 400 and the notify helper is never invoked."""
        handler = _make_handler({"plan_name": "not_a_plan"})

        with patch.object(api_plan_module, "require_auth", return_value=dict(_USER)), \
             patch.object(api_plan_module, "_notify_founder_plan_intent") as mock_notify:
            handler._handle_plan_set()

        payload, status = handler._sent[-1]
        assert status == 400 and payload.get("ok") is False
        mock_notify.assert_not_called()


class TestPlanIntentAbuseHardening:
    """Repair round 2026-07-20: unthrottled founder-page per POST was a HIGH.

    An authenticated free account could loop POST /api/plan to flood the
    founder's admin channel (the same channel as heartbeat/backup/watchdog
    pages) and spawn one notify thread per request. Two independent brakes:
    a per-IP rate limit on the endpoint, and change-detection so re-posting
    the SAME plan never re-pages.
    """

    def test_plan_set_is_rate_limited_per_ip(self):
        """Beyond the limiter budget → 429, no intent write, no founder page."""
        with patch.object(api_plan_module, "_PLAN_INTENT_LIMITER", _RateLimiter(2, 3600)), \
             patch.object(api_plan_module, "require_auth", return_value=dict(_USER)), \
             patch("app.plan.set_plan_intent", return_value=dict(_PLAN_STATE)) as mock_set, \
             patch.object(api_plan_module, "_notify_founder_plan_intent") as mock_notify:
            statuses = []
            for _ in range(3):
                handler = _make_handler({"plan_name": "professional"})
                handler._handle_plan_set()
                statuses.append(handler._sent[-1][1])

        assert statuses[:2] == [200, 200]
        assert statuses[2] == 429, "third request from the same IP must be throttled"
        assert mock_set.call_count == 2, "throttled request must not write plan intent"
        assert mock_notify.call_count == 2, "throttled request must not page the founder"

    def test_same_plan_resubmission_does_not_repage_founder(self):
        """set_plan_intent says intent_changed=False → ok=True but NO notify,
        and the dedupe flag never leaks into the customer payload."""
        state = dict(_PLAN_STATE)
        state["intent_changed"] = False
        handler = _make_handler({"plan_name": "professional"})

        with patch.object(api_plan_module, "require_auth", return_value=dict(_USER)), \
             patch("app.plan.set_plan_intent", return_value=state), \
             patch.object(api_plan_module, "_notify_founder_plan_intent") as mock_notify:
            handler._handle_plan_set()

        payload, status = handler._sent[-1]
        assert status == 200 and payload.get("ok") is True
        assert "intent_changed" not in payload.get("plan", {})
        mock_notify.assert_not_called()

    def test_set_plan_intent_reports_real_changes_only(self, tmp_path, monkeypatch):
        """plan.set_plan_intent flags a change on first pick and on a switch,
        but NOT on re-posting the same plan (isolated SQLite DB)."""
        monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "intent.db"))
        from app.auth import create_user
        from app.plan import set_plan_intent

        uid = int(create_user("dedupe@x.io", "password-123")["id"])

        first = set_plan_intent(uid, "professional")
        assert first["intent_changed"] is True  # evidence_preview → professional

        repeat = set_plan_intent(uid, "professional")
        assert repeat["intent_changed"] is False  # same plan re-posted

        switch = set_plan_intent(uid, "consultant")
        assert switch["intent_changed"] is True  # professional → consultant
