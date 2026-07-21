"""Self-service account data export — GET /api/account/export (exit portability).

Proves the API contract AND the two load-bearing invariants:

1. Auth — an unauthenticated caller is 401 (before any gather work).
2. Happy path — every promised section is present: schema envelope, explicit
   account projection, workspace profile, notification preferences, the user's
   checklist items across alerts, the org's sealed decision records VERBATIM
   plus the chain head, and the Telegram link (chat id included — it is the
   user's own data). Delivered as an application/json ATTACHMENT.
3. Secrets — the password hash (key AND value) and session ids are ABSENT from
   the serialized export, asserted explicitly against the real stored values.
4. Tenancy — two seeded users: user B's export contains NONE of user A's data
   (email, checklist text, sealed statement), and vice-versa sections stay
   intact for the caller.
5. Rate limit — the 11th export from one IP inside the window is 429.
6. Legal — every app-authored framing string passes the forbidden-claims guard.

Harness mirrors tests/test_decision_api.py: a bare ``_Handler`` instance with
``_send_json`` / ``_send_bytes`` captured and a real throwaway SQLite DB.
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
import app.api_account as api_account
import app.db as app_db
import app.decision_records as decision_records
from app import account_export
from app.action_checklist import add_checklist_item
from app.api import _Handler
from app.auth import create_session, create_user
from app.decision_records import seal_decision
from app.legal_safety import assert_no_forbidden_claims
from app.materiality import SHORT_DISCLAIMER
from app.telegram_pairing import consume_pairing_code, create_pairing_code


# ── fixtures & harness ───────────────────────────────────────────────────────────

@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    """Point the DB layer AND the decision head-file base dir at a temp dir."""
    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "account_export.db"))
    monkeypatch.setattr(decision_records, "_BASE_DIR", tmp_path)
    return tmp_path


ALERT = "draft-cbuae001"

PROOF = {
    "evidence_record_id": "evr_cbuae_rulebook_run9",
    "record_hash": "sha256:" + "a" * 64,
    "run_id": "run9",
    "diff_available": True,
    "normalized_hash": "sha256:" + "b" * 64,
}


def _make_handler(path: str = "/api/account/export", ip: str = "10.0.0.9") -> _Handler:
    header_map = {"Content-Length": "0", "X-Real-IP": ip}
    handler = _Handler.__new__(_Handler)
    handler.command = "GET"
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
    sent: list[tuple[dict, int]] = []
    sent_bytes: list[tuple[bytes, str, int, list]] = []
    handler._send_json = lambda data, status=200, **kw: sent.append((data, status))  # type: ignore[method-assign]
    handler._send_bytes = (  # type: ignore[method-assign]
        lambda body, content_type, status=200, extra_headers=None: sent_bytes.append(
            (body, content_type, status, list(extra_headers or []))
        )
    )
    handler._sent = sent  # type: ignore[attr-defined]
    handler._sent_bytes = sent_bytes  # type: ignore[attr-defined]
    return handler


def _auth_as(monkeypatch, user: dict) -> None:
    monkeypatch.setattr(api, "require_auth", lambda handler: dict(user))
    monkeypatch.setattr(api_account, "require_auth", lambda handler: dict(user))


def _new_owner(email: str, full_name: str | None = None) -> dict:
    user = create_user(email, "password-123", full_name=full_name)
    app_db.backfill_org_memberships()
    return user


def _owned_org_id(user_id: int) -> int:
    conn = app_db._connect()
    try:
        return int(
            conn.execute(
                "SELECT id FROM orgs WHERE owner_user_id = ? LIMIT 1", (user_id,)
            ).fetchone()["id"]
        )
    finally:
        conn.close()


def _export_body(handler: _Handler) -> dict:
    body, content_type, status, headers = handler._sent_bytes[-1]  # type: ignore[attr-defined]
    assert status == 200
    assert "application/json" in content_type
    disposition = dict(headers).get("Content-Disposition", "")
    assert disposition.startswith('attachment; filename="statuteproof-account-export-')
    assert disposition.endswith('.json"')
    return json.loads(body.decode("utf-8"))


def _run_export(monkeypatch, user: dict, ip: str = "10.0.0.9") -> _Handler:
    _auth_as(monkeypatch, user)
    handler = _make_handler(ip=ip)
    handler._handle_account_export()
    return handler


# ── 1. auth ──────────────────────────────────────────────────────────────────────

def test_export_requires_auth(isolated_db, monkeypatch):
    monkeypatch.setattr(api, "require_auth", lambda handler: None)
    handler = _make_handler(ip="10.1.0.1")
    handler._handle_account_export()
    _, status = handler._sent[-1]  # type: ignore[attr-defined]
    assert status == 401
    assert handler._sent_bytes == []  # type: ignore[attr-defined]


# ── 2. happy path: every section, attachment download ────────────────────────────

def test_happy_path_every_section_present(isolated_db, monkeypatch):
    owner = _new_owner("exporter@example.com", full_name="A. Rahman")
    org_id = _owned_org_id(owner["id"])

    item1 = add_checklist_item(owner["id"], ALERT, "Review section 4 scope")
    item2 = add_checklist_item(owner["id"], "draft-vara002", "Confirm licence impact")
    assert item1 is not None and item2 is not None

    sealed = seal_decision(
        owner["id"], org_id,
        display_name="A. Rahman",
        reviewed=dict(PROOF, alert_id=ALERT),
        kind="reviewed",
        statement="I reviewed the diff against our licence scope.",
    )
    assert sealed is not None

    code = create_pairing_code(owner["id"])["code"]
    assert consume_pairing_code(code, "987654321", {"username": "arahman"}) != "invalid"

    handler = _run_export(monkeypatch, owner, ip="10.1.0.2")
    export = _export_body(handler)

    assert export["schema"] == "statuteproof-account-export-v1"
    assert export["disclaimer"] == SHORT_DISCLAIMER
    assert export["generated_at"]
    assert export["framing"]["title"]

    account = export["account"]
    assert account["email"] == "exporter@example.com"
    assert account["full_name"] == "A. Rahman"
    assert account["email_verified"] is False

    # Workspace profile + notification prefs (explicit projections).
    assert "industries" in export["workspace_profile"]
    prefs = export["notification_preferences"]
    for key in (
        "alert_threshold", "urgent_threshold", "weekly_threshold",
        "digest_cadence", "brief_language", "weekly_brief_enabled",
        "telegram_alerts_enabled", "email_alerts_enabled",
    ):
        assert key in prefs

    # Checklist items across ALL alerts, the user's own words verbatim.
    texts = {item["text"] for item in export["checklist_items"]}
    assert texts == {"Review section 4 scope", "Confirm licence impact"}
    alert_ids = {item["alert_id"] for item in export["checklist_items"]}
    assert alert_ids == {ALERT, "draft-vara002"}

    # Sealed decisions travel VERBATIM (the self-verifiable envelope) + head.
    decisions = export["sealed_decisions"]
    assert decisions["records"] == [sealed]
    assert decisions["chain_head"]["decision_id"] == sealed["decision_id"]
    assert decisions["verification"]

    # Telegram link — the chat id is the user's own data and travels with them.
    telegram = export["telegram"]
    assert telegram["connected"] is True
    assert telegram["chat_id"] == "987654321"
    assert telegram["username"] == "arahman"


def test_org_less_user_gets_honest_empty_decisions(isolated_db, monkeypatch):
    # No backfill_org_memberships: the principal resolves with org_id=None.
    user = create_user("solo@example.com", "password-123")
    handler = _run_export(monkeypatch, user, ip="10.1.0.3")
    export = _export_body(handler)
    assert export["sealed_decisions"]["records"] == []
    assert export["sealed_decisions"]["chain_head"] is None
    assert export["account"]["email"] == "solo@example.com"


# ── 3. secrets: password hash and session ids are structurally absent ────────────

def test_password_hash_and_session_ids_absent(isolated_db, monkeypatch):
    owner = _new_owner("secrets@example.com")
    session_id = create_session(owner["id"])

    conn = app_db._connect()
    try:
        stored_hash = conn.execute(
            "SELECT password_hash FROM users WHERE id = ?", (owner["id"],)
        ).fetchone()["password_hash"]
    finally:
        conn.close()
    assert stored_hash  # the secret exists in the DB…

    handler = _run_export(monkeypatch, owner, ip="10.1.0.4")
    raw = handler._sent_bytes[-1][0].decode("utf-8")  # type: ignore[attr-defined]

    # …and is ABSENT from the export: no key, no value, no session token.
    assert "password_hash" not in raw
    assert stored_hash not in raw
    assert session_id not in raw
    # The explicit column list can never silently widen to SELECT *.
    assert "password_hash" not in account_export._ACCOUNT_COLUMNS


# ── 4. tenancy: two users, zero cross-contamination ──────────────────────────────

def test_cross_user_isolation(isolated_db, monkeypatch):
    owner_a = _new_owner("tenant-a@example.com", full_name="Tenant A")
    owner_b = _new_owner("tenant-b@example.com", full_name="Tenant B")
    org_a = _owned_org_id(owner_a["id"])
    org_b = _owned_org_id(owner_b["id"])

    assert add_checklist_item(owner_a["id"], ALERT, "Tenant A private action") is not None
    assert add_checklist_item(owner_b["id"], ALERT, "Tenant B private action") is not None
    sealed_a = seal_decision(
        owner_a["id"], org_a,
        display_name="Tenant A",
        reviewed=dict(PROOF, alert_id=ALERT),
        kind="reviewed",
        statement="Tenant A confidential sealed statement.",
    )
    sealed_b = seal_decision(
        owner_b["id"], org_b,
        display_name="Tenant B",
        reviewed=dict(PROOF, alert_id=ALERT),
        kind="reviewed",
        statement="Tenant B confidential sealed statement.",
    )
    assert sealed_a is not None and sealed_b is not None

    handler_b = _run_export(monkeypatch, owner_b, ip="10.1.0.5")
    raw_b = handler_b._sent_bytes[-1][0].decode("utf-8")  # type: ignore[attr-defined]
    export_b = json.loads(raw_b)

    # B sees B's own data…
    assert export_b["account"]["email"] == "tenant-b@example.com"
    assert [item["text"] for item in export_b["checklist_items"]] == ["Tenant B private action"]
    assert export_b["sealed_decisions"]["records"] == [sealed_b]
    # …and NOTHING of A's, anywhere in the serialized body.
    assert "tenant-a@example.com" not in raw_b
    assert "Tenant A private action" not in raw_b
    assert "Tenant A confidential sealed statement" not in raw_b
    assert sealed_a["decision_id"] not in raw_b

    handler_a = _run_export(monkeypatch, owner_a, ip="10.1.0.6")
    raw_a = handler_a._sent_bytes[-1][0].decode("utf-8")  # type: ignore[attr-defined]
    assert "Tenant B private action" not in raw_a
    assert sealed_b["decision_id"] not in raw_a


# ── 5. rate limit: the 11th export in the window is refused ──────────────────────

def test_rate_limited_after_ten_exports(isolated_db, monkeypatch):
    owner = _new_owner("limited@example.com")
    _auth_as(monkeypatch, owner)
    ip = "10.9.9.9"  # unique IP so other tests never share this budget
    for _ in range(10):
        handler = _make_handler(ip=ip)
        handler._handle_account_export()
        assert handler._sent_bytes, "export within the budget must succeed"  # type: ignore[attr-defined]
    eleventh = _make_handler(ip=ip)
    eleventh._handle_account_export()
    body, status = eleventh._sent[-1]  # type: ignore[attr-defined]
    assert status == 429
    assert eleventh._sent_bytes == []  # type: ignore[attr-defined]
    assert "Too many requests" in body["message"]


# ── 6. legal: every app-authored string is guard-clean ───────────────────────────

def test_export_framing_passes_forbidden_claims_guard():
    for key, value in account_export.FRAMING.items():
        assert_no_forbidden_claims(value, label=f"account export framing[{key}]")
