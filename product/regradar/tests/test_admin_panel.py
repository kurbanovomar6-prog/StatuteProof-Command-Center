"""Founder admin panel — activate a customer plan without SSH, safely.

Onboarding a paying customer previously required the founder to SSH into the
droplet and run ``run.py activate-plan``. This suite covers the authenticated,
RBAC-gated HTTP surface that replaces that CLI step WITHOUT widening who may act:

* the founder (identity via the ``STATUTEPROOF_ADMIN_EMAILS`` allowlist, layered
  on the fail-closed ``plan.admin`` RBAC action) can list accounts and activate a
  plan, and the activation both takes effect and is written to the immutable
  access log;
* a non-founder authenticated account is 403'd on BOTH endpoints with no data or
  existence leak;
* an unauthenticated call is 401;
* an unknown ``plan_name`` is 400;
* NO password hash / session id / raw token ever appears in an admin response;
* activating a PLAN never mutates anyone's RBAC ROLE (entitlements ≠ roles).

Runs against a REAL throwaway SQLite DB and the REAL HTTP handler.
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
import app.db as app_db
import app.rbac_runtime as rbac_runtime
from app import rbac
from app.access_log import read_access_log
from app.api import _Handler
from app.auth import create_user
from app.db import ensure_auth_tables


FOUNDER_EMAIL = "founder@statuteproof.com"


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "admin_panel.db"))
    ensure_auth_tables()
    return tmp_path / "admin_panel.db"


@pytest.fixture()
def as_founder(monkeypatch):
    monkeypatch.setenv("STATUTEPROOF_ADMIN_EMAILS", FOUNDER_EMAIL)


_IP_SEQ = [0]


def _make_handler(method: str, path: str, body: dict | None = None) -> _Handler:
    _IP_SEQ[0] += 1
    raw = json.dumps(body).encode() if body is not None else b""
    header_map = {
        "Content-Length": str(len(raw)),
        "X-Real-IP": f"10.9.0.{_IP_SEQ[0] % 240 + 1}",
    }
    handler = _Handler.__new__(_Handler)
    handler.command = method
    handler.path = path
    handler.request = MagicMock()
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(raw)
    handler.wfile = BytesIO()
    handler.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": header_map.get(key, default)
    handler.headers = hdrs

    sent: list[tuple[dict, int]] = []
    handler._send_json = lambda data, status=200, **kw: sent.append((data, status))  # type: ignore[method-assign]
    handler._sent = sent  # type: ignore[attr-defined]
    return handler


def _auth_as(monkeypatch, user: dict | None) -> None:
    monkeypatch.setattr(api, "require_auth", lambda handler: user)


def _last(handler: _Handler) -> tuple[dict, int]:
    return handler._sent[-1]  # type: ignore[attr-defined]


def _new_user(email: str) -> dict:
    user = create_user(email, "password-123")
    app_db.backfill_org_memberships()
    return {"id": int(user["id"]), "email": user["email"]}


def _role_of(user_id: int) -> str:
    conn = app_db._connect()
    try:
        row = conn.execute(
            "SELECT role FROM org_members WHERE user_id = ? ORDER BY id ASC LIMIT 1",
            (user_id,),
        ).fetchone()
        return str(row["role"]) if row is not None else ""
    finally:
        conn.close()


# ── happy path: founder activates a plan, it takes effect + is audited ────────────

def test_founder_activates_plan_takes_effect_and_audited(isolated_db, as_founder, monkeypatch):
    founder = _new_user(FOUNDER_EMAIL)
    customer = _new_user("customer@acme.io")

    _auth_as(monkeypatch, founder)
    handler = _make_handler(
        "POST", "/api/admin/activate-plan",
        {"user_id": customer["id"], "plan_name": "professional"},
    )
    handler.do_POST()

    data, status = _last(handler)
    assert status == 200, data
    assert data["ok"] is True

    # The entitlement actually changed (active plan follows the founder activation).
    from app.plan import get_plan_state
    state = get_plan_state(customer["id"])
    assert state["active_plan_name"] == "professional"

    # …and the action is in the immutable access log, attributed to the founder.
    rows = read_access_log(limit=50)
    assert any(
        r["action"] == rbac.PLAN_ADMIN
        and r["result"] == "allow"
        and r["actor_user_id"] == founder["id"]
        for r in rows
    ), rows


def test_founder_can_activate_by_email(isolated_db, as_founder, monkeypatch):
    founder = _new_user(FOUNDER_EMAIL)
    customer = _new_user("by-email@acme.io")

    _auth_as(monkeypatch, founder)
    handler = _make_handler(
        "POST", "/api/admin/activate-plan",
        {"email": "by-email@acme.io", "plan_name": "starter_pilot"},
    )
    handler.do_POST()

    data, status = _last(handler)
    assert status == 200, data
    from app.plan import get_plan_state
    assert get_plan_state(customer["id"])["active_plan_name"] == "starter_pilot"


# ── activation grants a PLAN, never an RBAC ROLE ──────────────────────────────────

def test_activation_does_not_change_rbac_role(isolated_db, as_founder, monkeypatch):
    founder = _new_user(FOUNDER_EMAIL)
    customer = _new_user("role-stable@acme.io")
    assert _role_of(customer["id"]) == "owner"

    _auth_as(monkeypatch, founder)
    handler = _make_handler(
        "POST", "/api/admin/activate-plan",
        {"user_id": customer["id"], "plan_name": "consultant"},
    )
    handler.do_POST()
    assert _last(handler)[1] == 200

    # The billing tier changed; the RBAC seat did NOT — and no member.manage row.
    assert _role_of(customer["id"]) == "owner"
    rows = read_access_log(limit=50)
    assert not any(r["action"] == rbac.MEMBER_MANAGE for r in rows), rows


# ── accounts list: founder sees a roster, with no secrets ─────────────────────────

def test_founder_lists_accounts_without_secrets(isolated_db, as_founder, monkeypatch):
    founder = _new_user(FOUNDER_EMAIL)
    _new_user("listed@acme.io")

    _auth_as(monkeypatch, founder)
    handler = _make_handler("GET", "/api/admin/accounts")
    handler.do_GET()

    data, status = _last(handler)
    assert status == 200, data
    assert data["ok"] is True
    emails = {a["email"] for a in data["accounts"]}
    assert "listed@acme.io" in emails
    # Every row exposes the operational fields the founder needs…
    row = next(a for a in data["accounts"] if a["email"] == "listed@acme.io")
    for key in ("id", "email", "email_verified", "plan_name", "activated_plan",
                "telegram_linked", "created_at"):
        assert key in row
    # …and NONE of the sensitive ones.
    blob = json.dumps(data)
    assert "password_hash" not in blob
    assert "password" not in blob
    for a in data["accounts"]:
        assert "password_hash" not in a
        assert "session" not in a
        assert isinstance(a["telegram_linked"], bool)


# ── authz: non-founder authenticated → 403 on both endpoints, no leak ─────────────

def test_non_founder_forbidden_on_accounts(isolated_db, as_founder, monkeypatch):
    _new_user(FOUNDER_EMAIL)
    intruder = _new_user("intruder@acme.io")

    _auth_as(monkeypatch, intruder)
    handler = _make_handler("GET", "/api/admin/accounts")
    handler.do_GET()

    data, status = _last(handler)
    assert status == 403
    assert "accounts" not in data  # no data leak


def test_non_founder_forbidden_on_activate(isolated_db, as_founder, monkeypatch):
    _new_user(FOUNDER_EMAIL)
    victim = _new_user("victim@acme.io")
    intruder = _new_user("intruder2@acme.io")

    _auth_as(monkeypatch, intruder)
    handler = _make_handler(
        "POST", "/api/admin/activate-plan",
        {"user_id": victim["id"], "plan_name": "professional"},
    )
    handler.do_POST()

    data, status = _last(handler)
    assert status == 403
    # IDOR / no-op: the victim's entitlement is untouched by a non-founder call.
    from app.plan import get_plan_state
    assert get_plan_state(victim["id"])["active_plan_name"] == "evidence_preview"
    # The denial is audited (never silent).
    rows = read_access_log(limit=50)
    assert any(r["action"] == rbac.PLAN_ADMIN and r["result"] == "deny" for r in rows), rows


# ── authz: unauthenticated → 401 ──────────────────────────────────────────────────

def test_unauthenticated_accounts_is_401(isolated_db, as_founder, monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/admin/accounts")
    handler.do_GET()
    assert _last(handler)[1] == 401


def test_unauthenticated_activate_is_401(isolated_db, as_founder, monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler(
        "POST", "/api/admin/activate-plan",
        {"user_id": 1, "plan_name": "professional"},
    )
    handler.do_POST()
    assert _last(handler)[1] == 401


# ── validation: unknown plan_name → 400 ───────────────────────────────────────────

def test_unknown_plan_name_is_400(isolated_db, as_founder, monkeypatch):
    founder = _new_user(FOUNDER_EMAIL)
    customer = _new_user("unknownplan@acme.io")

    _auth_as(monkeypatch, founder)
    handler = _make_handler(
        "POST", "/api/admin/activate-plan",
        {"user_id": customer["id"], "plan_name": "enterprise_ultra"},
    )
    handler.do_POST()

    data, status = _last(handler)
    assert status == 400, data
    from app.plan import get_plan_state
    assert get_plan_state(customer["id"])["active_plan_name"] == "evidence_preview"
