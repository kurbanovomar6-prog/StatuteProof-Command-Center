"""Behavioral coverage for the ``_AccountHandlerMixin`` handlers in
``app/api_account.py`` — the PUBLIC unauthenticated verify endpoint and its
spec, the Auditor Evidence Room view + share lifecycle (create/list/revoke),
profile get/update, the self-service account export, and the seven delivery
handlers (test-brief, logs, preview, send-preview-alert, and the three email
handlers).

Every test drives the REAL ``_Handler`` (built ``__new__``-style with a
``BytesIO`` request body, exactly like ``tests/test_api_coverage_uplift.py``)
and asserts REAL behavior — status codes, the unauth 401 guard, RBAC 403s,
plan/capability gating, tenancy delegation (the caller's own ``user`` is the
scope every module call receives), and the internal-error 500 branches.

Dependencies are monkeypatched where the moved handler READS them: bare
module-level names (``verify_submission``, ``update_profile``,
``build_account_export`` …) at ``app.api_account``; function-local imports
(``app.evidence_room.*``, ``app.email_delivery.*``, ``app.weekly_brief.*``)
at their SOURCE module. ``require_auth`` is read as a bare global inside the
mixin's own module, so it is patched at ``app.api_account``.
"""
from __future__ import annotations

import json
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api  # noqa: F401 — import the host module first to avoid a circular import
import app.api_account as api_account
import app.email_delivery as email_delivery
import app.evidence_room as evidence_room
import app.weekly_brief as weekly_brief
from app.api import _Handler


# ── handler harness ───────────────────────────────────────────────────────────

_IP_SEQ = [0]


def _make_handler(method: str, path: str, body: dict | None = None,
                  raw: bytes | None = None) -> _Handler:
    """Build a real _Handler with a throwaway request body.

    A UNIQUE X-Real-IP per handler keeps every call under the per-IP rate
    limiter, so a real limiter never fires spuriously across tests. Both
    ``_send_json`` AND ``_send_bytes`` are captured into ``handler._sent`` so
    binary responses (verify-spec, account-export) are asserted the same way as
    JSON ones, without exercising BaseHTTPRequestHandler's socket writer.
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
    handler._send_bytes = (  # type: ignore[method-assign]
        lambda body, content_type, status=200, extra_headers=None: sent.append(
            (body, content_type, status, extra_headers)
        )
    )
    handler._sent = sent  # type: ignore[attr-defined]
    return handler


def _last(handler: _Handler):
    return handler._sent[-1]  # type: ignore[attr-defined]


def _auth_as(monkeypatch, user: dict | None) -> None:
    # ``require_auth`` is read as a bare global inside the mixin's own module.
    monkeypatch.setattr(api_account, "require_auth", lambda handler: user)


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/verify — PUBLIC, no auth (verify_submission wiring)
# ══════════════════════════════════════════════════════════════════════════════

def test_public_verify_no_body_is_400():
    handler = _make_handler("POST", "/api/verify")
    handler._handle_public_verify()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["ok"] is False


def test_public_verify_missing_record_is_400():
    handler = _make_handler("POST", "/api/verify", {"raw": "x"})
    handler._handle_public_verify()
    data, status, _ = _last(handler)
    assert status == 400
    assert "'record' object is required" in data["error"]


def test_public_verify_non_string_raw_is_400():
    handler = _make_handler("POST", "/api/verify", {"record": {}, "raw": 123})
    handler._handle_public_verify()
    data, status, _ = _last(handler)
    assert status == 400
    assert "'raw' must be a string" in data["error"]


def test_public_verify_non_string_diff_is_400():
    handler = _make_handler("POST", "/api/verify", {"record": {}, "diff": 5})
    handler._handle_public_verify()
    data, status, _ = _last(handler)
    assert status == 400
    assert "'diff' must be a string" in data["error"]


def test_public_verify_non_string_timestamp_token_is_400():
    handler = _make_handler("POST", "/api/verify", {"record": {}, "timestamp_token": 1})
    handler._handle_public_verify()
    data, status, _ = _last(handler)
    assert status == 400
    assert "timestamp_token" in data["error"]


def test_public_verify_forged_record_is_200_but_not_verified():
    """A blob with no hashes is not a StatuteProof evidence record: the REAL
    verify_submission reports verified:false (never a 500) at 200."""
    handler = _make_handler("POST", "/api/verify", {"record": {"totally": "forged"}})
    handler._handle_public_verify()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True
    assert data["verified"] is False


def test_public_verify_wires_all_optional_fields_through(monkeypatch):
    captured = {}

    def _fake_verify(record, *, raw=None, normalized=None, diff=None,
                     timestamp_token=None, timestamp_digest=None):
        captured.update(
            record=record, raw=raw, normalized=normalized, diff=diff,
            timestamp_token=timestamp_token, timestamp_digest=timestamp_digest,
        )
        return {"ok": True, "verified": True}

    monkeypatch.setattr(api_account, "verify_submission", _fake_verify)
    handler = _make_handler(
        "POST", "/api/verify",
        {"record": {"a": 1}, "raw": "R", "normalized": "N", "diff": "D",
         "timestamp_token": "TOK", "timestamp_digest": "DIG"},
    )
    handler._handle_public_verify()
    data, status, _ = _last(handler)
    assert status == 200
    assert captured == {
        "record": {"a": 1}, "raw": "R", "normalized": "N", "diff": "D",
        "timestamp_token": "TOK", "timestamp_digest": "DIG",
    }


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/verify-spec — PUBLIC static doc
# ══════════════════════════════════════════════════════════════════════════════

def test_verify_spec_serves_markdown_bytes():
    handler = _make_handler("GET", "/api/verify-spec")
    handler._handle_verify_spec()
    body, content_type, status, _ = _last(handler)
    assert status == 200
    assert content_type.startswith("text/markdown")
    assert isinstance(body, (bytes, bytearray)) and len(body) > 0


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/room/<token> — PUBLIC read-only evidence-room view
# ══════════════════════════════════════════════════════════════════════════════

def test_room_view_unknown_token_is_404(monkeypatch):
    monkeypatch.setattr(evidence_room, "get_room_view", lambda token: None)
    handler = _make_handler("GET", "/api/room/deadbeef")
    handler._handle_room_view("deadbeef")
    data, status, _ = _last(handler)
    assert status == 404
    assert data["error"] == "not_found"


def test_room_view_valid_token_returns_frozen_scope(monkeypatch):
    monkeypatch.setattr(evidence_room, "get_room_view",
                        lambda token: {"org_display_name": "Acme", "sources": []})
    handler = _make_handler("GET", "/api/room/goodtoken")
    handler._handle_room_view("goodtoken")
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True
    assert data["room"]["org_display_name"] == "Acme"


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/evidence-room/shares — create a time-boxed external share
# ══════════════════════════════════════════════════════════════════════════════

def test_share_create_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("POST", "/api/evidence-room/shares", {"source_ids": ["s1"]})
    handler._handle_evidence_room_share_create()
    _, status, _ = _last(handler)
    assert status == 401


def test_share_create_rbac_denied_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/evidence-room/shares", {"source_ids": ["s1"]})
    handler._rbac_guard = lambda user, action, **kw: (  # type: ignore[method-assign]
        handler._sent.append(({"ok": False}, 403, None)) or False
    )
    # Make the RBAC gate the ONLY thing that can 403: let the capability gate pass
    # and give create_share a spy. If the RBAC gate were removed the handler would
    # fall through to a 201 and reach create_share — so this genuinely pins the gate
    # rather than masking behind the sibling capability 403.
    handler._require_capability = lambda user, cap: True  # type: ignore[method-assign]
    reached = {"create_share": False}
    monkeypatch.setattr(
        evidence_room, "create_share",
        lambda *a, **k: reached.__setitem__("create_share", True) or {"ok": True, "token": "t", "share_id": "x"},
    )
    handler._handle_evidence_room_share_create()
    _, status, _ = _last(handler)
    assert status == 403
    assert reached["create_share"] is False  # the RBAC gate fired BEFORE create_share


def test_share_create_plan_capability_denied_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/evidence-room/shares", {"source_ids": ["s1"]})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._require_capability = lambda user, cap: (  # type: ignore[method-assign]
        handler._sent.append(({"ok": False}, 403, None)) or False
    )
    handler._handle_evidence_room_share_create()
    _, status, _ = _last(handler)
    assert status == 403


def test_share_create_success_is_201(monkeypatch):
    _auth_as(monkeypatch, {"id": 5})
    monkeypatch.setattr(evidence_room, "create_share",
                        lambda user, *a, **k: {"ok": True, "token": "raw-token", "share_id": "sh1"})
    handler = _make_handler("POST", "/api/evidence-room/shares",
                            {"source_ids": ["s1"], "date_from": "2026-01-01", "date_to": "2026-02-01"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._require_capability = lambda user, cap: True  # type: ignore[method-assign]
    handler._handle_evidence_room_share_create()
    data, status, _ = _last(handler)
    assert status == 201
    assert data["token"] == "raw-token"


@pytest.mark.parametrize(
    "error,expected_status",
    [
        ("invalid", 400),
        ("invalid_expiry", 400),
        ("forbidden_claim", 400),
        ("no_entitled_sources", 403),
        ("forbidden", 403),
        ("too_large", 413),
        ("some_unknown_error", 500),
    ],
)
def test_share_create_error_status_mapping(monkeypatch, error, expected_status):
    _auth_as(monkeypatch, {"id": 5})
    monkeypatch.setattr(evidence_room, "create_share",
                        lambda user, *a, **k: {"ok": False, "error": error})
    handler = _make_handler("POST", "/api/evidence-room/shares", {"source_ids": ["s1"]})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._require_capability = lambda user, cap: True  # type: ignore[method-assign]
    handler._handle_evidence_room_share_create()
    _, status, _ = _last(handler)
    assert status == expected_status


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/evidence-room/shares — the caller's OWN shares (tenancy delegation)
# ══════════════════════════════════════════════════════════════════════════════

def test_shares_list_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/evidence-room/shares")
    handler._handle_evidence_room_shares_list()
    _, status, _ = _last(handler)
    assert status == 401


def test_shares_list_scopes_to_caller(monkeypatch):
    caller = {"id": 42}
    seen = {}

    def _list(user):
        seen["user"] = user
        return {"ok": True, "shares": []}

    _auth_as(monkeypatch, caller)
    monkeypatch.setattr(evidence_room, "list_shares", _list)
    handler = _make_handler("GET", "/api/evidence-room/shares")
    handler._handle_evidence_room_shares_list()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True
    # The caller's OWN principal is the only scope the module ever receives.
    assert seen["user"] is caller


def test_shares_list_module_failure_is_500(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(evidence_room, "list_shares", lambda user: {"ok": False})
    handler = _make_handler("GET", "/api/evidence-room/shares")
    handler._handle_evidence_room_shares_list()
    _, status, _ = _last(handler)
    assert status == 500


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/evidence-room/shares/revoke — kill a share (owner-scoped, no oracle)
# ══════════════════════════════════════════════════════════════════════════════

def test_share_revoke_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("POST", "/api/evidence-room/shares/revoke", {"share_id": "sh1"})
    handler._handle_evidence_room_share_revoke()
    _, status, _ = _last(handler)
    assert status == 401


def test_share_revoke_rbac_denied_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/evidence-room/shares/revoke", {"share_id": "sh1"})
    handler._rbac_guard = lambda user, action, **kw: (  # type: ignore[method-assign]
        handler._sent.append(({"ok": False}, 403, None)) or False
    )
    handler._handle_evidence_room_share_revoke()
    _, status, _ = _last(handler)
    assert status == 403


def test_share_revoke_other_tenants_share_is_404_not_oracle(monkeypatch):
    """A share the caller does not own resolves exactly like one that does not
    exist (404) — the module is owner-scoped and returns ``not_found``."""
    caller = {"id": 7}
    seen = {}

    def _revoke(user, share_id):
        seen["user"] = user
        seen["share_id"] = share_id
        return {"ok": False, "error": "not_found"}

    _auth_as(monkeypatch, caller)
    monkeypatch.setattr(evidence_room, "revoke_share", _revoke)
    handler = _make_handler("POST", "/api/evidence-room/shares/revoke",
                            {"share_id": "someone-elses-share"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_evidence_room_share_revoke()
    _, status, _ = _last(handler)
    assert status == 404
    assert seen["user"] is caller  # scope is the caller, never request input


def test_share_revoke_success_is_200(monkeypatch):
    _auth_as(monkeypatch, {"id": 7})
    monkeypatch.setattr(evidence_room, "revoke_share",
                        lambda user, share_id: {"ok": True})
    handler = _make_handler("POST", "/api/evidence-room/shares/revoke", {"share_id": "sh1"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_evidence_room_share_revoke()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True


def test_share_revoke_module_error_is_500(monkeypatch):
    _auth_as(monkeypatch, {"id": 7})
    monkeypatch.setattr(evidence_room, "revoke_share",
                        lambda user, share_id: {"ok": False, "error": "boom"})
    handler = _make_handler("POST", "/api/evidence-room/shares/revoke", {"share_id": "sh1"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_evidence_room_share_revoke()
    _, status, _ = _last(handler)
    assert status == 500


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/profile — profile read
# ══════════════════════════════════════════════════════════════════════════════

def test_profile_get_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/profile")
    handler._handle_profile_get()
    _, status, _ = _last(handler)
    assert status == 401


def test_profile_get_success_seeds_from_user(monkeypatch):
    seen = {}

    def _get_or_create(uid, seed=None):
        seen["uid"] = uid
        seen["seed"] = seed
        return {"company_name": "Acme", "industry": "Fintech"}

    _auth_as(monkeypatch, {"id": 9, "company_name": "Acme", "industry": "Fintech"})
    monkeypatch.setattr(api_account, "get_or_create_profile", _get_or_create)
    handler = _make_handler("GET", "/api/profile")
    handler._handle_profile_get()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["profile"]["company_name"] == "Acme"
    assert seen["uid"] == 9
    assert seen["seed"] == {"company_name": "Acme", "industry": "Fintech"}


def test_profile_get_internal_error_is_500(monkeypatch):
    _auth_as(monkeypatch, {"id": 9})

    def _boom(uid, seed=None):
        raise RuntimeError("profile store down")

    monkeypatch.setattr(api_account, "get_or_create_profile", _boom)
    handler = _make_handler("GET", "/api/profile")
    handler._handle_profile_get()
    _, status, _ = _last(handler)
    assert status == 500


# ══════════════════════════════════════════════════════════════════════════════
# PUT /api/profile — settings mutation (RBAC-gated)
# ══════════════════════════════════════════════════════════════════════════════

def test_profile_update_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("PUT", "/api/profile", {"company_name": "Acme"})
    handler._handle_profile_update()
    _, status, _ = _last(handler)
    assert status == 401


def test_profile_update_success_is_200(monkeypatch):
    _auth_as(monkeypatch, {"id": 3})
    monkeypatch.setattr(api_account, "update_profile",
                        lambda uid, body: {"company_name": body.get("company_name")})
    handler = _make_handler("PUT", "/api/profile", {"company_name": "Beta Ltd"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_profile_update()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["profile"]["company_name"] == "Beta Ltd"


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/account/export — self-service data export (no role gate, own data)
# ══════════════════════════════════════════════════════════════════════════════

def test_account_export_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/account/export")
    handler._handle_account_export()
    _, status, _ = _last(handler)
    assert status == 401


def test_account_export_attachment_download(monkeypatch):
    _auth_as(monkeypatch, {"id": 11})
    monkeypatch.setattr(api_account, "build_account_export",
                        lambda user, org_id: {"account": {"id": 11}, "org_id": org_id})
    monkeypatch.setattr(api_account.rbac_runtime, "resolve_principal",
                        lambda user: MagicMock(org_id="org-11"))
    monkeypatch.setattr(api_account.rbac_runtime, "log_sensitive_action",
                        lambda *a, **k: None)
    handler = _make_handler("GET", "/api/account/export")
    handler._handle_account_export()
    body, content_type, status, extra = _last(handler)
    assert status == 200
    assert content_type.startswith("application/json")
    disposition = dict(extra).get("Content-Disposition", "")
    assert disposition.startswith("attachment; filename=")
    parsed = json.loads(body.decode("utf-8"))
    assert parsed["account"]["id"] == 11
    assert parsed["org_id"] == "org-11"


def test_account_export_org_resolution_failure_still_exports(monkeypatch):
    """A caller with no resolvable org exports with an empty decisions section,
    not a 500 — org resolution failure is swallowed to ``org_id=None``."""
    _auth_as(monkeypatch, {"id": 12})
    seen = {}

    def _build(user, org_id):
        seen["org_id"] = org_id
        return {"account": {"id": 12}}

    def _boom(user):
        raise RuntimeError("no org")

    monkeypatch.setattr(api_account, "build_account_export", _build)
    monkeypatch.setattr(api_account.rbac_runtime, "resolve_principal", _boom)
    monkeypatch.setattr(api_account.rbac_runtime, "log_sensitive_action", lambda *a, **k: None)
    handler = _make_handler("GET", "/api/account/export")
    handler._handle_account_export()
    _, _, status, _extra = _last(handler)
    assert status == 200
    assert seen["org_id"] is None


def test_account_export_build_failure_is_500(monkeypatch):
    _auth_as(monkeypatch, {"id": 13})

    def _boom(user, org_id):
        raise RuntimeError("export gather failed")

    monkeypatch.setattr(api_account, "build_account_export", _boom)
    monkeypatch.setattr(api_account.rbac_runtime, "resolve_principal",
                        lambda user: MagicMock(org_id="org-13"))
    handler = _make_handler("GET", "/api/account/export")
    handler._handle_account_export()
    data, status, _ = _last(handler)
    assert status == 500
    assert data["message"] == "Internal server error."


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/delivery/test-brief
# ══════════════════════════════════════════════════════════════════════════════

def test_delivery_test_brief_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("POST", "/api/delivery/test-brief")
    handler._handle_delivery_test_brief()
    _, status, _ = _last(handler)
    assert status == 401


def test_delivery_test_brief_success_is_200(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(api_account, "send_sample_brief_to_user",
                        lambda uid: {"ok": True, "message": "sent", "log_id": 7})
    handler = _make_handler("POST", "/api/delivery/test-brief")
    handler._handle_delivery_test_brief()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["log_id"] == 7


@pytest.mark.parametrize(
    "reason,expected_status,expected_reason",
    [
        ("Sample brief already sent today.", 429, "already_sent_today"),
        ("Telegram not connected.", 400, "no_telegram"),
        ("Telegram alerts are disabled.", 400, "telegram_disabled"),
        ("Onboarding is not complete.", 400, "onboarding_incomplete"),
        ("Some other failure", 502, "delivery_failed"),
    ],
)
def test_delivery_test_brief_reason_mapping(monkeypatch, reason, expected_status, expected_reason):
    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(api_account, "send_sample_brief_to_user",
                        lambda uid: {"ok": False, "reason": reason})
    handler = _make_handler("POST", "/api/delivery/test-brief")
    handler._handle_delivery_test_brief()
    data, status, _ = _last(handler)
    assert status == expected_status
    assert data["reason"] == expected_reason


def test_delivery_test_brief_internal_error_is_500(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})

    def _boom(uid):
        raise RuntimeError("delivery blew up")

    monkeypatch.setattr(api_account, "send_sample_brief_to_user", _boom)
    handler = _make_handler("POST", "/api/delivery/test-brief")
    handler._handle_delivery_test_brief()
    _, status, _ = _last(handler)
    assert status == 500


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/delivery/logs
# ══════════════════════════════════════════════════════════════════════════════

def test_delivery_logs_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/delivery/logs")
    handler._handle_delivery_logs()
    _, status, _ = _last(handler)
    assert status == 401


def test_delivery_logs_clamps_limit_and_scopes_to_caller(monkeypatch):
    seen = {}

    def _logs(uid, limit=20):
        seen["uid"] = uid
        seen["limit"] = limit
        return [{"id": 1}]

    _auth_as(monkeypatch, {"id": 44})
    monkeypatch.setattr(api_account, "get_user_delivery_logs", _logs)
    handler = _make_handler("GET", "/api/delivery/logs?limit=999")
    handler._handle_delivery_logs()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["logs"] == [{"id": 1}]
    assert seen["uid"] == 44
    assert seen["limit"] == 50  # clamped to the 50 ceiling


def test_delivery_logs_bad_limit_falls_back_to_default(monkeypatch):
    seen = {}
    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(api_account, "get_user_delivery_logs",
                        lambda uid, limit=20: seen.setdefault("limit", limit) or [])
    handler = _make_handler("GET", "/api/delivery/logs?limit=abc")
    handler._handle_delivery_logs()
    _, status, _ = _last(handler)
    assert status == 200
    assert seen["limit"] == 20


def test_delivery_logs_internal_error_is_500(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})

    def _boom(uid, limit=20):
        raise RuntimeError("logs down")

    monkeypatch.setattr(api_account, "get_user_delivery_logs", _boom)
    handler = _make_handler("GET", "/api/delivery/logs")
    handler._handle_delivery_logs()
    _, status, _ = _last(handler)
    assert status == 500


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/delivery/preview — redacted for accounts the send gate would refuse
# ══════════════════════════════════════════════════════════════════════════════

def test_delivery_preview_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/delivery/preview")
    handler._handle_delivery_preview()
    _, status, _ = _last(handler)
    assert status == 401


def test_delivery_preview_success_applies_plan_redaction(monkeypatch):
    seen = {}

    def _build(uid, days=14):
        seen["days"] = days
        return {"raw": True}

    def _redact(uid, preview):
        seen["redacted_input"] = preview
        return {"redacted": True}

    _auth_as(monkeypatch, {"id": 2})
    monkeypatch.setattr(api_account, "build_routing_preview_for_user", _build)
    monkeypatch.setattr(api_account, "redact_preview_for_plan", _redact)
    handler = _make_handler("GET", "/api/delivery/preview?days=999")
    handler._handle_delivery_preview()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["preview"] == {"redacted": True}
    assert seen["days"] == 60  # clamped to the 60-day ceiling
    assert seen["redacted_input"] == {"raw": True}


def test_delivery_preview_internal_error_is_500(monkeypatch):
    _auth_as(monkeypatch, {"id": 2})

    def _boom(uid, days=14):
        raise RuntimeError("preview down")

    monkeypatch.setattr(api_account, "build_routing_preview_for_user", _boom)
    handler = _make_handler("GET", "/api/delivery/preview")
    handler._handle_delivery_preview()
    _, status, _ = _last(handler)
    assert status == 500


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/delivery/send-preview-alert — plan-gated privileged dispatch
# ══════════════════════════════════════════════════════════════════════════════

def test_send_preview_alert_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("POST", "/api/delivery/send-preview-alert", {"alert_id": "a1"})
    handler._handle_delivery_send_preview_alert()
    _, status, _ = _last(handler)
    assert status == 401


def test_send_preview_alert_rbac_denied_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/delivery/send-preview-alert", {"alert_id": "a1"})
    handler._rbac_guard = lambda user, action, **kw: (  # type: ignore[method-assign]
        handler._sent.append(({"ok": False}, 403, None)) or False
    )
    handler._handle_delivery_send_preview_alert()
    _, status, _ = _last(handler)
    assert status == 403


def test_send_preview_alert_invalid_alert_id_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/delivery/send-preview-alert",
                            {"alert_id": "bad id with spaces!"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_delivery_send_preview_alert()
    data, status, _ = _last(handler)
    assert status == 400
    assert "Invalid alert_id" in data["message"]


def test_send_preview_alert_plan_required_is_402(monkeypatch):
    """A free account asking for the paid official-source deliverable gets 402,
    not a server fault."""
    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(api_account, "send_preview_alert_to_user",
                        lambda uid, aid: {"ok": False, "code": "plan_required", "reason": "upgrade"})
    handler = _make_handler("POST", "/api/delivery/send-preview-alert", {"alert_id": "a1"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_delivery_send_preview_alert()
    data, status, _ = _last(handler)
    assert status == 402
    assert data["reason"] == "plan_required"


@pytest.mark.parametrize(
    "code,expected_status",
    [
        ("duplicate", 409),
        ("not_found", 404),
        ("not_ready", 400),
        ("telegram_failed", 502),
        ("something_else", 400),
    ],
)
def test_send_preview_alert_code_status_mapping(monkeypatch, code, expected_status):
    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(api_account, "send_preview_alert_to_user",
                        lambda uid, aid: {"ok": False, "code": code, "reason": "x"})
    handler = _make_handler("POST", "/api/delivery/send-preview-alert", {"alert_id": "a1"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_delivery_send_preview_alert()
    _, status, _ = _last(handler)
    assert status == expected_status


def test_send_preview_alert_success_is_200(monkeypatch):
    seen = {}

    def _send(uid, aid):
        seen["uid"] = uid
        seen["aid"] = aid
        return {"ok": True, "message": "sent", "log_id": 3}

    _auth_as(monkeypatch, {"id": 88})
    monkeypatch.setattr(api_account, "send_preview_alert_to_user", _send)
    handler = _make_handler("POST", "/api/delivery/send-preview-alert", {"alert_id": "alert-9"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_delivery_send_preview_alert()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["log_id"] == 3
    assert seen == {"uid": 88, "aid": "alert-9"}  # dispatch scoped to the caller


def test_send_preview_alert_internal_error_is_500(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})

    def _boom(uid, aid):
        raise RuntimeError("dispatch blew up")

    monkeypatch.setattr(api_account, "send_preview_alert_to_user", _boom)
    handler = _make_handler("POST", "/api/delivery/send-preview-alert", {"alert_id": "a1"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_delivery_send_preview_alert()
    _, status, _ = _last(handler)
    assert status == 500


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/delivery/email-test-mode
# ══════════════════════════════════════════════════════════════════════════════

def test_email_test_mode_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("POST", "/api/delivery/email-test-mode", {})
    handler._handle_delivery_email_test_mode()
    _, status, _ = _last(handler)
    assert status == 401


def test_email_test_mode_success_is_200(monkeypatch):
    _auth_as(monkeypatch, {"id": 1, "email": "u@e.com"})
    monkeypatch.setattr(weekly_brief, "build_weekly_brief", lambda **kw: {"brief": True})
    monkeypatch.setattr(email_delivery, "deliver_weekly_brief_test_mode",
                        lambda brief, recipient_email=None: {"ok": True, "outbox_path": "/tmp/x"})
    handler = _make_handler("POST", "/api/delivery/email-test-mode", {})
    handler._handle_delivery_email_test_mode()
    data, status, _ = _last(handler)
    assert status == 200
    assert "test-mode payload written" in data["message"]


def test_email_test_mode_delivery_failure_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1, "email": "u@e.com"})
    monkeypatch.setattr(weekly_brief, "build_weekly_brief", lambda **kw: {"brief": True})
    monkeypatch.setattr(email_delivery, "deliver_weekly_brief_test_mode",
                        lambda brief, recipient_email=None: {"ok": False, "error_message": "no recipient"})
    handler = _make_handler("POST", "/api/delivery/email-test-mode", {})
    handler._handle_delivery_email_test_mode()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "no recipient"


def test_email_test_mode_internal_error_is_500(monkeypatch):
    _auth_as(monkeypatch, {"id": 1, "email": "u@e.com"})

    def _boom(**kw):
        raise RuntimeError("brief build failed")

    monkeypatch.setattr(weekly_brief, "build_weekly_brief", _boom)
    handler = _make_handler("POST", "/api/delivery/email-test-mode", {})
    handler._handle_delivery_email_test_mode()
    _, status, _ = _last(handler)
    assert status == 500


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/delivery/email-status
# ══════════════════════════════════════════════════════════════════════════════

def test_email_status_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/delivery/email-status")
    handler._handle_delivery_email_status()
    _, status, _ = _last(handler)
    assert status == 401


def test_email_status_success_is_200(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(email_delivery, "build_email_status_response",
                        lambda: {"ok": True, "configured": False})
    handler = _make_handler("GET", "/api/delivery/email-status")
    handler._handle_delivery_email_status()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["configured"] is False


def test_email_status_internal_error_is_500(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})

    def _boom():
        raise RuntimeError("status down")

    monkeypatch.setattr(email_delivery, "build_email_status_response", _boom)
    handler = _make_handler("GET", "/api/delivery/email-status")
    handler._handle_delivery_email_status()
    _, status, _ = _last(handler)
    assert status == 500


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/delivery/email-config-check
# ══════════════════════════════════════════════════════════════════════════════

def test_email_config_check_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("POST", "/api/delivery/email-config-check")
    handler._handle_delivery_email_config_check()
    _, status, _ = _last(handler)
    assert status == 401


def test_email_config_check_configuration_required_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(email_delivery, "record_email_config_check",
                        lambda: {"status": "configuration_required"})
    handler = _make_handler("POST", "/api/delivery/email-config-check")
    handler._handle_delivery_email_config_check()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["status"] == "configuration_required"


def test_email_config_check_configured_is_200(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(email_delivery, "record_email_config_check",
                        lambda: {"status": "ok"})
    handler = _make_handler("POST", "/api/delivery/email-config-check")
    handler._handle_delivery_email_config_check()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["status"] == "ok"


def test_email_config_check_internal_error_is_500(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})

    def _boom():
        raise RuntimeError("config check down")

    monkeypatch.setattr(email_delivery, "record_email_config_check", _boom)
    handler = _make_handler("POST", "/api/delivery/email-config-check")
    handler._handle_delivery_email_config_check()
    _, status, _ = _last(handler)
    assert status == 500
