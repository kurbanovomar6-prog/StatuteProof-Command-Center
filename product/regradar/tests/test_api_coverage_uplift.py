"""Behavioral coverage uplift for app/api.py — the auth / routing / tenancy /
entitlement surface.

Every test here drives the REAL ``_Handler`` (constructed the same way as
``tests/test_admin_panel.py``: ``__new__`` + a ``BytesIO`` request body + a
``_send_json`` capture) and asserts REAL behavior — status codes, the
authentication Set-Cookie header, fail-closed entitlement clipping, RBAC 403s,
the SSRF denial, and internal-error 500s. Dependencies are monkeypatched at the
``app.api`` boundary (module-level imports) or at ``app.plan`` / ``app.source_tester``
(function-local imports) exactly as the surrounding suite does, so no network,
no Telegram, and no real plan DB is required for the mocked paths.

Focus areas (in priority order):
  * POST /api/auth/login              — the core authentication decision
  * POST /api/source-test             — SSRF denial at the HTTP boundary
  * _entitle_source_ids / _require_capability — fail-closed entitlement core
  * PUT  /api/profile                 — RBAC-gated settings mutation
  * GET/POST /api/plan                — plan read/intent gating
  * POST /api/canonical-evidence/review — validation/error pre-checks
  * telegram pairing generate/status/unlink — unauth guard + tenancy
  * Google OAuth start/callback       — external-identity session boundary
  * admin accounts/activate residual param-parse branches
"""
from __future__ import annotations

import json
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api as api
import app.api_plan as api_plan
import app.api_telegram as api_telegram
import app.db as app_db
from app.api import _Handler
from app.auth import OAuthAccountError, create_user
from app.db import ensure_auth_tables


# ── handler harness ───────────────────────────────────────────────────────────

_IP_SEQ = [0]


def _make_handler(method: str, path: str, body: dict | None = None,
                  raw: bytes | None = None) -> _Handler:
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
        "X-Real-IP": f"10.7.{_IP_SEQ[0] // 240 % 240}.{_IP_SEQ[0] % 240 + 1}",
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
    handler._sent = sent  # type: ignore[attr-defined]
    handler._redirects = redirects  # type: ignore[attr-defined]
    return handler


def _last(handler: _Handler):
    return handler._sent[-1]  # type: ignore[attr-defined]


def _auth_as(monkeypatch, user: dict | None) -> None:
    # ``require_auth`` is read as a bare global inside each handler's own module.
    # Handlers that moved into mixin modules (app.api_telegram, app.api_plan) read
    # it from THEIR namespace, so patch it everywhere a moved handler lives.
    monkeypatch.setattr(api, "require_auth", lambda handler: user)
    monkeypatch.setattr(api_telegram, "require_auth", lambda handler: user)
    monkeypatch.setattr(api_plan, "require_auth", lambda handler: user)


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/auth/login — the core authentication decision (was entirely untested)
# ══════════════════════════════════════════════════════════════════════════════

def test_login_empty_body_is_401():
    # An empty body parses to {} (not the None "body required" branch), so login
    # falls through to the credential check with a blank email -> 401, never 200.
    handler = _make_handler("POST", "/api/auth/login")
    handler._handle_auth_login()
    _, status, _ = _last(handler)
    assert status == 401


def test_login_bad_json_is_400():
    handler = _make_handler("POST", "/api/auth/login", raw=b"{not json")
    handler._handle_auth_login()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["ok"] is False


def test_login_unknown_email_is_401(monkeypatch):
    monkeypatch.setattr(api, "get_user_by_email", lambda email: None)
    handler = _make_handler(
        "POST", "/api/auth/login",
        {"email": "nobody@example.com", "password": "whatever"},
    )
    handler._handle_auth_login()
    data, status, _ = _last(handler)
    assert status == 401
    assert data["message"] == "Invalid email or password."


def test_login_wrong_password_is_401(monkeypatch):
    monkeypatch.setattr(
        api, "get_user_by_email",
        lambda email: {"id": 1, "is_active": True, "email_verified": True,
                       "password_hash": "hash", "email": email},
    )
    monkeypatch.setattr(api, "verify_password", lambda pw, h: False)
    handler = _make_handler(
        "POST", "/api/auth/login",
        {"email": "user@example.com", "password": "wrong"},
    )
    handler._handle_auth_login()
    data, status, _ = _last(handler)
    assert status == 401
    assert data["message"] == "Invalid email or password."


def test_login_inactive_account_is_401(monkeypatch):
    monkeypatch.setattr(
        api, "get_user_by_email",
        lambda email: {"id": 1, "is_active": False, "email_verified": True,
                       "password_hash": "hash", "email": email},
    )
    monkeypatch.setattr(api, "verify_password", lambda pw, h: True)
    handler = _make_handler(
        "POST", "/api/auth/login",
        {"email": "user@example.com", "password": "correct"},
    )
    handler._handle_auth_login()
    data, status, _ = _last(handler)
    assert status == 401  # inactive is indistinguishable from bad creds
    assert data["message"] == "Invalid email or password."


def test_login_unverified_email_is_403_and_not_bypassable(monkeypatch):
    monkeypatch.setattr(
        api, "get_user_by_email",
        lambda email: {"id": 1, "is_active": True, "email_verified": False,
                       "password_hash": "hash", "email": email},
    )
    monkeypatch.setattr(api, "verify_password", lambda pw, h: True)
    # No session is minted for an unverified account.
    monkeypatch.setattr(api, "create_session",
                        lambda uid: pytest.fail("create_session must NOT run for unverified email"))
    handler = _make_handler(
        "POST", "/api/auth/login",
        {"email": "user@example.com", "password": "correct"},
    )
    handler._handle_auth_login()
    data, status, extra = _last(handler)
    assert status == 403
    assert data["requires_verification"] is True
    # The verification-gate response never carries a session cookie.
    assert extra is None or all(k != "Set-Cookie" for k, _ in (extra or []))


def test_login_success_sets_session_cookie_and_200(monkeypatch):
    monkeypatch.setattr(
        api, "get_user_by_email",
        lambda email: {"id": 42, "is_active": True, "email_verified": True,
                       "password_hash": "hash", "email": email},
    )
    monkeypatch.setattr(api, "verify_password", lambda pw, h: True)
    monkeypatch.setattr(api, "create_session", lambda uid: "sess-token-xyz")
    monkeypatch.setattr(api, "make_public_user", lambda u: {"id": u["id"], "email": u["email"]})
    handler = _make_handler(
        "POST", "/api/auth/login",
        {"email": "user@example.com", "password": "correct"},
    )
    handler._handle_auth_login()
    data, status, extra = _last(handler)
    assert status == 200
    assert data["ok"] is True
    assert data["user"]["id"] == 42
    header_names = [k for k, _ in (extra or [])]
    assert "Set-Cookie" in header_names
    cookie_val = next(v for k, v in extra if k == "Set-Cookie")
    assert "sess-token-xyz" in cookie_val


def test_login_create_session_raises_is_500(monkeypatch):
    monkeypatch.setattr(
        api, "get_user_by_email",
        lambda email: {"id": 1, "is_active": True, "email_verified": True,
                       "password_hash": "hash", "email": email},
    )
    monkeypatch.setattr(api, "verify_password", lambda pw, h: True)

    def _boom(uid):
        raise RuntimeError("session store down")

    monkeypatch.setattr(api, "create_session", _boom)
    handler = _make_handler(
        "POST", "/api/auth/login",
        {"email": "user@example.com", "password": "correct"},
    )
    handler._handle_auth_login()
    data, status, _ = _last(handler)
    assert status == 500
    assert data["message"] == "Internal server error."


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/source-test — SSRF denial at the HTTP boundary
# ══════════════════════════════════════════════════════════════════════════════

def test_source_test_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("POST", "/api/source-test", {"url": "https://ok.example"})
    handler._handle_source_test()
    data, status, _ = _last(handler)
    assert status == 401


def test_source_test_empty_url_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/source-test", {"url": "   "})
    handler._handle_source_test()
    data, status, _ = _last(handler)
    assert status == 400
    assert "URL is required" in data["message"]


def test_source_test_ssrf_denied_before_network(monkeypatch):
    """An internal/metadata URL is rejected 400 and test_source_url is NEVER reached."""
    import app.source_tester as st

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(st, "validate_public_url",
                        lambda url: (False, "resolves to private range"))
    monkeypatch.setattr(st, "test_source_url",
                        lambda url: pytest.fail("network path must NOT run for an unsafe URL"))
    handler = _make_handler("POST", "/api/source-test",
                            {"url": "http://169.254.169.254/latest/meta-data/"})
    handler._handle_source_test()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["status"] == "FAILED"
    assert "URL failed safety check" in data["message"]


def test_source_test_internal_error_is_500(monkeypatch):
    import app.source_tester as st

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(st, "validate_public_url", lambda url: (True, "ok"))

    def _boom(url):
        raise RuntimeError("fetch exploded")

    monkeypatch.setattr(st, "test_source_url", _boom)
    handler = _make_handler("POST", "/api/source-test", {"url": "https://ok.example"})
    handler._handle_source_test()
    data, status, _ = _last(handler)
    assert status == 500


@pytest.mark.parametrize(
    "verdict,method,expected_status,expected_extraction",
    [
        ("can_monitor", "playwright", "PASS", ["HTML", "JS"]),
        ("can_monitor", "http", "PASS", ["HTML"]),
        ("needs_adapter", "http", "NEEDS_ADAPTER", ["Limited"]),
        ("cannot_monitor", "http", "FAILED", []),
    ],
)
def test_source_test_verdict_mapping(monkeypatch, verdict, method,
                                     expected_status, expected_extraction):
    import app.source_tester as st

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(st, "validate_public_url", lambda url: (True, "ok"))
    monkeypatch.setattr(
        st, "test_source_url",
        lambda url: {"verdict": verdict, "extracted_chars": 123,
                     "recommended_method": method, "reason": "because"},
    )
    handler = _make_handler("POST", "/api/source-test", {"url": "https://ok.example"})
    handler._handle_source_test()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["status"] == expected_status
    assert data["extraction"] == expected_extraction
    assert data["chars"] == 123


# ══════════════════════════════════════════════════════════════════════════════
# _require_capability / _entitle_source_ids — fail-closed entitlement core
# ══════════════════════════════════════════════════════════════════════════════

def test_require_capability_grants_when_plan_allows(monkeypatch):
    import app.plan as plan

    monkeypatch.setattr(plan, "has_capability", lambda uid, cap: True)
    handler = _make_handler("POST", "/api/dummy")
    assert handler._require_capability({"id": 5}, "regulator_binder") is True
    assert handler._sent == []  # no 403 emitted on grant


def test_require_capability_denies_when_plan_lacks(monkeypatch):
    import app.plan as plan

    monkeypatch.setattr(plan, "has_capability", lambda uid, cap: False)
    handler = _make_handler("POST", "/api/dummy")
    assert handler._require_capability({"id": 5}, "regulator_binder") is False
    data, status, _ = _last(handler)
    assert status == 403


def test_require_capability_fails_closed_when_lookup_raises(monkeypatch):
    """A broken plan lookup must DENY (403), not fall through to a grant."""
    import app.plan as plan

    def _boom(uid, cap):
        raise RuntimeError("plan store down")

    monkeypatch.setattr(plan, "has_capability", _boom)
    handler = _make_handler("POST", "/api/dummy")
    assert handler._require_capability({"id": 5}, "regulator_binder") is False
    _, status, _ = _last(handler)
    assert status == 403


def test_entitle_source_ids_bad_user_id_returns_empty(monkeypatch):
    handler = _make_handler("POST", "/api/dummy")
    # A user dict with no usable id must yield [] — never the raw requested list.
    assert handler._entitle_source_ids({}, ["s1", "s2"]) == []
    assert handler._entitle_source_ids({"id": "not-an-int"}, ["s1"]) == []


def test_entitle_source_ids_blank_request_returns_empty():
    handler = _make_handler("POST", "/api/dummy")
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    assert handler._entitle_source_ids({"id": 1}, []) == []
    assert handler._entitle_source_ids({"id": 1}, ["", "   "]) == []


def test_entitle_source_ids_clips_to_plan_limit(monkeypatch):
    import app.plan as plan

    monkeypatch.setattr(plan, "source_limit_for", lambda uid: 2)
    handler = _make_handler("POST", "/api/dummy")
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    result = handler._entitle_source_ids({"id": 1}, ["a", "b", "c", "d"])
    assert result == ["a", "b"]  # truncated to the plan's source_limit


def test_entitle_source_ids_drops_denied_custom_sources(monkeypatch):
    import app.plan as plan

    monkeypatch.setattr(plan, "source_limit_for", lambda uid: 100)
    handler = _make_handler("POST", "/api/dummy")
    # 'other-tenant' is a custom source owned by someone else -> denied.
    handler._denied_custom_source_ids = lambda user: {"other-tenant"}  # type: ignore[method-assign]
    result = handler._entitle_source_ids({"id": 1}, ["mine", "other-tenant", "shared"])
    assert result == ["mine", "shared"]


def test_entitle_source_ids_fails_closed_when_limit_lookup_raises(monkeypatch):
    """A broken source_limit_for must NOT widen scope — limit falls to 0."""
    import app.plan as plan

    def _boom(uid):
        raise RuntimeError("plan store down")

    monkeypatch.setattr(plan, "source_limit_for", _boom)
    handler = _make_handler("POST", "/api/dummy")
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    # limit=0 => scope is fully clipped, never the raw input.
    assert handler._entitle_source_ids({"id": 1}, ["a", "b", "c"]) == []


# ══════════════════════════════════════════════════════════════════════════════
# PUT /api/profile — RBAC-gated settings mutation (was entirely untested)
# ══════════════════════════════════════════════════════════════════════════════

def test_profile_update_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("PUT", "/api/profile", {"company_name": "Acme"})
    handler._handle_profile_update()
    _, status, _ = _last(handler)
    assert status == 401


def test_profile_update_auditor_seat_denied_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("PUT", "/api/profile", {"company_name": "Acme"})
    # RBAC guard denies (read-only auditor seat) and emits its own 403.
    handler._rbac_guard = lambda user, action, **kw: (  # type: ignore[method-assign]
        handler._sent.append(({"ok": False}, 403, None)) or False
    )
    handler._handle_profile_update()
    _, status, _ = _last(handler)
    assert status == 403


def test_profile_update_empty_body_is_accepted_as_empty_update(monkeypatch):
    # An empty body parses to {} (not the None branch), so it is passed through
    # to update_profile as an empty update and succeeds — no 400 is raised.
    _auth_as(monkeypatch, {"id": 1})
    seen = {}
    monkeypatch.setattr(api, "update_profile",
                        lambda uid, body: seen.setdefault("body", body) or {"ok": True})
    handler = _make_handler("PUT", "/api/profile")
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_profile_update()
    _, status, _ = _last(handler)
    assert status == 200
    assert seen["body"] == {}


def test_profile_update_bad_json_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("PUT", "/api/profile", raw=b"{broken")
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_profile_update()
    _, status, _ = _last(handler)
    assert status == 400


def test_profile_update_value_error_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(api, "update_profile",
                        lambda uid, body: (_ for _ in ()).throw(ValueError("industry too long")))
    handler = _make_handler("PUT", "/api/profile", {"industry": "x" * 9999})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_profile_update()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "industry too long"


def test_profile_update_generic_error_is_500(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})

    def _boom(uid, body):
        raise RuntimeError("db down")

    monkeypatch.setattr(api, "update_profile", _boom)
    handler = _make_handler("PUT", "/api/profile", {"company_name": "Acme"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_profile_update()
    _, status, _ = _last(handler)
    assert status == 500


def test_profile_update_success_is_200(monkeypatch):
    _auth_as(monkeypatch, {"id": 7})
    monkeypatch.setattr(api, "update_profile",
                        lambda uid, body: {"company_name": body.get("company_name")})
    handler = _make_handler("PUT", "/api/profile", {"company_name": "Acme Ltd"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_profile_update()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["profile"]["company_name"] == "Acme Ltd"


# ══════════════════════════════════════════════════════════════════════════════
# GET/POST /api/plan — plan read + intent gating
# ══════════════════════════════════════════════════════════════════════════════

def test_plan_get_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/plan")
    handler._handle_plan_get()
    _, status, _ = _last(handler)
    assert status == 401


def test_plan_get_success_reflects_caller_is_admin(monkeypatch):
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 3})
    monkeypatch.setattr(plan, "get_plan_state", lambda uid: {"active_plan_name": "starter_pilot"})
    handler = _make_handler("GET", "/api/plan")
    handler._caller_is_admin = lambda user: True  # type: ignore[method-assign]
    handler._handle_plan_get()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["is_admin"] is True
    assert data["plan"]["is_admin"] is True


def test_plan_get_non_admin_hint_is_false(monkeypatch):
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 3})
    monkeypatch.setattr(plan, "get_plan_state", lambda uid: {"active_plan_name": "free"})
    handler = _make_handler("GET", "/api/plan")
    handler._caller_is_admin = lambda user: False  # type: ignore[method-assign]
    handler._handle_plan_get()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["is_admin"] is False


def test_plan_get_internal_error_is_500(monkeypatch):
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 3})

    def _boom(uid):
        raise RuntimeError("plan store down")

    monkeypatch.setattr(plan, "get_plan_state", _boom)
    handler = _make_handler("GET", "/api/plan")
    handler._caller_is_admin = lambda user: False  # type: ignore[method-assign]
    handler._handle_plan_get()
    _, status, _ = _last(handler)
    assert status == 500


def test_plan_set_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("POST", "/api/plan", {"plan_name": "starter_pilot"})
    handler._handle_plan_set()
    _, status, _ = _last(handler)
    assert status == 401


def test_plan_set_auditor_seat_denied_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/plan", {"plan_name": "starter_pilot"})
    handler._rbac_guard = lambda user, action, **kw: (  # type: ignore[method-assign]
        handler._sent.append(({"ok": False}, 403, None)) or False
    )
    handler._handle_plan_set()
    _, status, _ = _last(handler)
    assert status == 403


def test_plan_set_unknown_plan_is_400(monkeypatch):
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 1, "email": "u@e.com"})
    monkeypatch.setattr(plan, "PLAN_NAMES", {"starter_pilot", "professional"})
    handler = _make_handler("POST", "/api/plan", {"plan_name": "made_up_plan"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_plan_set()
    data, status, _ = _last(handler)
    assert status == 400
    assert "Unknown plan" in data["message"]


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/canonical-evidence/review — validation & error pre-checks
# ══════════════════════════════════════════════════════════════════════════════

def _pass_review_gates(handler: _Handler) -> None:
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._canonical_record_out_of_scope = lambda user, rid: False  # type: ignore[method-assign]
    handler._caller_is_operator = lambda user: True  # type: ignore[method-assign]
    handler._canonical_record_is_own_custom = lambda user, rid: True  # type: ignore[method-assign]


def test_canonical_review_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("POST", "/api/canonical-evidence/review",
                            {"record_id": "r1", "decision": "approve", "note": "ok"})
    handler._handle_canonical_evidence_review_action()
    _, status, _ = _last(handler)
    assert status == 401


def test_canonical_review_rbac_denied_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/canonical-evidence/review",
                            {"record_id": "r1", "decision": "approve", "note": "ok"})
    handler._rbac_guard = lambda user, action, **kw: (  # type: ignore[method-assign]
        handler._sent.append(({"ok": False}, 403, None)) or False
    )
    handler._handle_canonical_evidence_review_action()
    _, status, _ = _last(handler)
    assert status == 403


def test_canonical_review_bad_json_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/canonical-evidence/review", raw=b"{broken")
    _pass_review_gates(handler)
    handler._handle_canonical_evidence_review_action()
    _, status, _ = _last(handler)
    assert status == 400


def test_canonical_review_missing_fields_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    # record_id present, but decision + note missing -> 400.
    handler = _make_handler("POST", "/api/canonical-evidence/review",
                            {"record_id": "r1"})
    _pass_review_gates(handler)
    handler._handle_canonical_evidence_review_action()
    data, status, _ = _last(handler)
    assert status == 400
    assert "record_id, decision, and note are required" in data["message"]


def test_canonical_review_recorder_raises_is_500(monkeypatch):
    import app.review_queue as rq

    _auth_as(monkeypatch, {"id": 1, "email": "u@e.com"})

    def _boom(*a, **k):
        raise RuntimeError("queue down")

    monkeypatch.setattr(rq, "record_canonical_review_action", _boom)
    handler = _make_handler("POST", "/api/canonical-evidence/review",
                            {"record_id": "r1", "decision": "approve", "note": "looks good"})
    _pass_review_gates(handler)
    handler._handle_canonical_evidence_review_action()
    _, status, _ = _last(handler)
    assert status == 500


def test_canonical_review_success_is_200(monkeypatch):
    import app.review_queue as rq

    _auth_as(monkeypatch, {"id": 1, "email": "u@e.com"})
    monkeypatch.setattr(rq, "record_canonical_review_action",
                        lambda rid, **k: {"status": "ok", "record_id": rid})
    handler = _make_handler("POST", "/api/canonical-evidence/review",
                            {"record_id": "r1", "decision": "approve", "note": "looks good"})
    _pass_review_gates(handler)
    handler._handle_canonical_evidence_review_action()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True


# ══════════════════════════════════════════════════════════════════════════════
# Telegram pairing — unauth guard + tenancy (all three were untested)
# ══════════════════════════════════════════════════════════════════════════════

def test_telegram_pair_generate_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("POST", "/api/telegram/pair/generate")
    handler._handle_telegram_pair_generate()
    _, status, _ = _last(handler)
    assert status == 401


def test_telegram_pair_generate_scopes_to_caller_id(monkeypatch):
    seen = {}

    def _create(uid):
        seen["uid"] = uid
        return {"code": "SP-ABC123", "expires_at": "2026-01-01T00:00:00Z"}

    _auth_as(monkeypatch, {"id": 55})
    monkeypatch.setattr(api_telegram, "create_pairing_code", _create)
    handler = _make_handler("POST", "/api/telegram/pair/generate")
    handler._handle_telegram_pair_generate()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["code"] == "SP-ABC123"
    assert seen["uid"] == 55  # pairing code minted for the caller only


def test_telegram_pair_generate_error_is_500(monkeypatch):
    _auth_as(monkeypatch, {"id": 55})

    def _boom(uid):
        raise RuntimeError("pairing store down")

    monkeypatch.setattr(api_telegram, "create_pairing_code", _boom)
    handler = _make_handler("POST", "/api/telegram/pair/generate")
    handler._handle_telegram_pair_generate()
    _, status, _ = _last(handler)
    assert status == 500


def test_telegram_pair_status_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/telegram/pair/status")
    handler._handle_telegram_pair_status()
    _, status, _ = _last(handler)
    assert status == 401


def test_telegram_pair_status_scopes_to_caller(monkeypatch):
    seen = {}

    def _status(uid):
        seen["uid"] = uid
        return {"linked": True}

    _auth_as(monkeypatch, {"id": 99})
    monkeypatch.setattr(api_telegram, "get_pairing_status", _status)
    handler = _make_handler("GET", "/api/telegram/pair/status")
    handler._handle_telegram_pair_status()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["linked"] is True
    assert seen["uid"] == 99


def test_telegram_pair_unlink_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("POST", "/api/telegram/pair/unlink")
    handler._handle_telegram_pair_unlink()
    _, status, _ = _last(handler)
    assert status == 401


def test_telegram_pair_unlink_operates_on_caller_only(monkeypatch):
    seen = {}

    def _unlink(uid):
        seen["uid"] = uid

    _auth_as(monkeypatch, {"id": 77})
    monkeypatch.setattr(api_telegram, "unlink_telegram", _unlink)
    handler = _make_handler("POST", "/api/telegram/pair/unlink")
    handler._handle_telegram_pair_unlink()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True
    assert seen["uid"] == 77  # only the caller's binding is cleared


# ══════════════════════════════════════════════════════════════════════════════
# Google OAuth — external-identity session boundary
# ══════════════════════════════════════════════════════════════════════════════

def test_google_start_not_configured_is_503(monkeypatch):
    monkeypatch.setattr(api, "google_oauth_available", lambda: False)
    handler = _make_handler("GET", "/api/auth/google/start")
    handler._handle_auth_google_start()
    data, status, _ = _last(handler)
    assert status == 503
    assert data["available"] is False


def test_google_start_success_redirects_to_authorization_url(monkeypatch):
    monkeypatch.setattr(api, "google_oauth_available", lambda: True)
    monkeypatch.setattr(api, "create_google_oauth_state", lambda next_path: "state-token")
    monkeypatch.setattr(api, "google_oauth_authorization_url",
                        lambda state: f"https://accounts.google.com/o/oauth2?state={state}")
    handler = _make_handler("GET", "/api/auth/google/start?next=/app/settings")
    handler._handle_auth_google_start()
    assert handler._sent == []  # a redirect, not a JSON body
    location, status, _ = handler._redirects[-1]  # type: ignore[attr-defined]
    assert "accounts.google.com" in location
    assert "state-token" in location


def test_google_start_oauth_account_error_is_503(monkeypatch):
    monkeypatch.setattr(api, "google_oauth_available", lambda: True)

    def _boom(next_path):
        raise OAuthAccountError("password account cannot use Google")

    monkeypatch.setattr(api, "create_google_oauth_state", _boom)
    handler = _make_handler("GET", "/api/auth/google/start")
    handler._handle_auth_google_start()
    _, status, _ = _last(handler)
    assert status == 503


def test_google_start_generic_error_is_500(monkeypatch):
    monkeypatch.setattr(api, "google_oauth_available", lambda: True)

    def _boom(next_path):
        raise RuntimeError("state store down")

    monkeypatch.setattr(api, "create_google_oauth_state", _boom)
    handler = _make_handler("GET", "/api/auth/google/start")
    handler._handle_auth_google_start()
    _, status, _ = _last(handler)
    assert status == 500


def test_google_callback_user_cancelled_redirects_to_cancelled(monkeypatch):
    handler = _make_handler("GET", "/api/auth/google/callback?error=access_denied")
    handler._handle_auth_google_callback()
    location, _, _ = handler._redirects[-1]  # type: ignore[attr-defined]
    assert location == "/login?google=cancelled"


def test_google_callback_missing_state_redirects_to_failed(monkeypatch):
    monkeypatch.setattr(api, "consume_google_oauth_state", lambda state: None)
    handler = _make_handler("GET", "/api/auth/google/callback?code=abc&state=bad")
    handler._handle_auth_google_callback()
    location, _, _ = handler._redirects[-1]  # type: ignore[attr-defined]
    assert location == "/login?google=failed"


def test_google_callback_success_sets_cookie_and_redirects_next(monkeypatch):
    monkeypatch.setattr(api, "consume_google_oauth_state",
                        lambda state: {"next_path": "/app/dashboard"})
    monkeypatch.setattr(api, "exchange_google_oauth_code", lambda code: {"email": "g@e.com"})
    monkeypatch.setattr(api, "link_or_create_google_user",
                        lambda claims: {"id": 8, "is_active": True})
    monkeypatch.setattr(api, "create_session", lambda uid: "goog-sess")
    handler = _make_handler("GET", "/api/auth/google/callback?code=abc&state=good")
    handler._handle_auth_google_callback()
    location, status, extra = handler._redirects[-1]  # type: ignore[attr-defined]
    assert location == "/app/dashboard"
    header_names = [k for k, _ in (extra or [])]
    assert "Set-Cookie" in header_names
    assert "goog-sess" in next(v for k, v in extra if k == "Set-Cookie")


def test_google_callback_inactive_account_redirects_to_failed(monkeypatch):
    monkeypatch.setattr(api, "consume_google_oauth_state",
                        lambda state: {"next_path": "/app"})
    monkeypatch.setattr(api, "exchange_google_oauth_code", lambda code: {"email": "g@e.com"})
    monkeypatch.setattr(api, "link_or_create_google_user",
                        lambda claims: {"id": 8, "is_active": False})
    monkeypatch.setattr(api, "create_session",
                        lambda uid: pytest.fail("no session for an inactive account"))
    handler = _make_handler("GET", "/api/auth/google/callback?code=abc&state=good")
    handler._handle_auth_google_callback()
    location, _, _ = handler._redirects[-1]  # type: ignore[attr-defined]
    assert location == "/login?google=failed"


def test_google_callback_exchange_raises_redirects_to_failed(monkeypatch):
    monkeypatch.setattr(api, "consume_google_oauth_state",
                        lambda state: {"next_path": "/app"})

    def _boom(code):
        raise RuntimeError("token exchange failed")

    monkeypatch.setattr(api, "exchange_google_oauth_code", _boom)
    handler = _make_handler("GET", "/api/auth/google/callback?code=abc&state=good")
    handler._handle_auth_google_callback()
    location, _, _ = handler._redirects[-1]  # type: ignore[attr-defined]
    assert location == "/login?google=failed"


# ══════════════════════════════════════════════════════════════════════════════
# admin residual param-parse / no-such-account branches (real DB)
# ══════════════════════════════════════════════════════════════════════════════

FOUNDER_EMAIL = "founder@statuteproof.com"


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "api_uplift.db"))
    ensure_auth_tables()
    return tmp_path / "api_uplift.db"


@pytest.fixture()
def as_founder(monkeypatch):
    monkeypatch.setenv("STATUTEPROOF_ADMIN_EMAILS", FOUNDER_EMAIL)


def _new_user(email: str) -> dict:
    user = create_user(email, "password-123")
    app_db.backfill_org_memberships()
    return {"id": int(user["id"]), "email": user["email"]}


def test_admin_accounts_non_int_pagination_defaults(isolated_db, as_founder, monkeypatch):
    """Non-integer limit/offset query params fall back to defaults, not a 500."""
    founder = _new_user(FOUNDER_EMAIL)
    _new_user("listed@acme.io")
    _auth_as(monkeypatch, founder)
    handler = _make_handler("GET", "/api/admin/accounts?limit=abc&offset=xyz")
    handler._handle_admin_accounts()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True
    assert any(a["email"] == "listed@acme.io" for a in data["accounts"])


def test_admin_activate_plan_non_numeric_user_id_is_no_such_account(isolated_db, as_founder, monkeypatch):
    """A non-numeric user_id parses to None target -> 400 'No such account'."""
    founder = _new_user(FOUNDER_EMAIL)
    _auth_as(monkeypatch, founder)
    handler = _make_handler(
        "POST", "/api/admin/activate-plan",
        {"user_id": "not-a-number", "plan_name": "starter_pilot"},
    )
    handler._handle_admin_activate_plan()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "No such account."


def test_pairing_instructions_point_at_the_alerts_bot(monkeypatch):
    """Pairing instructions must name the ALERTS bot (@statuteproofalerts_bot),
    not the founder-only admin bot.

    Regression: _telegram_instructions used TELEGRAM_BOT_USERNAME (the admin
    @StatuteProof_bot), but the /start CODE listener runs on the alerts token
    (telegram_settings.get_token prefers TELEGRAM_ALERTS_BOT_TOKEN). A customer
    following the old text sent the code to the wrong bot and pairing silently
    failed. In two-bot production the instruction must carry the alerts username.
    """
    monkeypatch.setattr(api_telegram, "TELEGRAM_ALERTS_BOT_USERNAME", "statuteproofalerts_bot")
    monkeypatch.setattr(api, "TELEGRAM_BOT_USERNAME", "StatuteProof_bot")
    handler = _make_handler("POST", "/api/telegram/pair/generate")
    text = handler._telegram_instructions("SP-ABC123")
    assert "@statuteproofalerts_bot" in text
    assert "StatuteProof_bot" not in text  # never the admin bot

    # Single-bot dev: TELEGRAM_ALERTS_BOT_USERNAME is populated from the legacy
    # var by config, so the instruction still resolves to the configured bot.
    monkeypatch.setattr(api_telegram, "TELEGRAM_ALERTS_BOT_USERNAME", "solo_bot")
    assert "@solo_bot" in handler._telegram_instructions("SP-XYZ")

    # No username configured at all -> generic, no broken @-handle.
    monkeypatch.setattr(api_telegram, "TELEGRAM_ALERTS_BOT_USERNAME", "")
    assert handler._telegram_instructions("SP-1") == "Send /start SP-1 to our Telegram bot."
