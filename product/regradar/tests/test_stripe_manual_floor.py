"""Manual/admin activation floors the Stripe grant ledger (anti-silent-downgrade).

Regression cover for the PRODUCT-HIGH bug: ``app.plan.activate_plan`` sets the
``activated_plan`` column but historically wrote NO row to ``stripe_customer_grants``.
So once Stripe billing was enabled, a Stripe lifecycle event (cancel / downgrade) that
re-derived a user's tier from the *surviving grants* was blind to the manual activation
and silently stripped a comped/manual consultant to the free tier.

The fix records a server-only SENTINEL grant (``customer_id='manual'``) on every
manual/admin activation, so re-derivation (a MAX over surviving grants) floors at the
manual tier. The Stripe webhook path opts OUT (``record_manual_grant=False``) so it
never writes a bogus sentinel over its genuine customer grants.

Invariants verified here:
* a manual activation writes exactly one ``'manual'`` sentinel grant;
* the Stripe activation path writes NO ``'manual'`` sentinel;
* a manual floor SURVIVES a Stripe cancel of a separate (lower) paid grant — the user
  is NOT stripped to free (the reported bug);
* a genuine Stripe-only customer STILL downgrades to free on cancel (fix did not break
  the existing revocation path);
* ANTI-TAKEDOWN: an attacker's forged/foreign cancel cannot strip a victim's manual
  floor (nor the victim's own paid grant).

Uses an obvious PLACEHOLDER webhook secret — never a real ``whsec_`` value. Runs against
a REAL throwaway SQLite DB and the REAL HTTP handler.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sys
import time
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.db as app_db
from app.api import _Handler
from app.auth import create_user
from app.db import ensure_auth_tables
from app.plan import activate_plan, get_plan_state

# Obvious placeholder — a TEST secret, never a real whsec_ value.
TEST_SECRET = "whsec_test_placeholder_do_not_use_in_prod"
PRICE_STARTER = "price_TEST_STARTER"
PRICE_PRO = "price_TEST_PRO"
PRICE_CONSULTANT = "price_TEST_CONSULTANT"
PRICE_TO_PLAN = (
    f"{PRICE_STARTER}:starter_pilot,"
    f"{PRICE_PRO}:professional,"
    f"{PRICE_CONSULTANT}:consultant"
)

CUS_PAID = "cus_TEST_PAID"
CUS_VICTIM = "cus_TEST_VICTIM"
CUS_ATTACKER = "cus_TEST_ATTACKER"


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "stripe_manual_floor.db"))
    ensure_auth_tables()
    return tmp_path / "stripe_manual_floor.db"


@pytest.fixture()
def configured(monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", TEST_SECRET)
    monkeypatch.setenv("STRIPE_PRICE_TO_PLAN", PRICE_TO_PLAN)


_IP_SEQ = [0]


def _sign(payload: bytes, secret: str = TEST_SECRET, timestamp: int | None = None) -> str:
    ts = int(time.time()) if timestamp is None else int(timestamp)
    signed = f"{ts}".encode() + b"." + payload
    v1 = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return f"t={ts},v1={v1}"


def _make_handler(payload: bytes, sig_header: str | None) -> _Handler:
    _IP_SEQ[0] += 1
    header_map = {
        "Content-Length": str(len(payload)),
        "X-Real-IP": f"10.11.0.{_IP_SEQ[0] % 240 + 1}",
    }
    if sig_header is not None:
        header_map["Stripe-Signature"] = sig_header

    handler = _Handler.__new__(_Handler)
    handler.command = "POST"
    handler.path = "/api/stripe/webhook"
    handler.request = MagicMock()
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(payload)
    handler.wfile = BytesIO()
    handler.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": header_map.get(key, default)
    handler.headers = hdrs

    sent: list[tuple[dict, int]] = []
    handler._send_json = lambda data, status=200, **kw: sent.append((data, status))  # type: ignore[method-assign]
    handler._sent = sent  # type: ignore[attr-defined]
    return handler


def _post(payload: bytes, sig_header: str | None) -> tuple[dict, int]:
    handler = _make_handler(payload, sig_header)
    handler.do_POST()
    return handler._sent[-1]  # type: ignore[attr-defined]


def _new_user(email: str) -> dict:
    user = create_user(email, "password-123")
    return {"id": int(user["id"]), "email": user["email"]}


def _checkout_event(event_id: str, price_id: str, *, user_id: int, customer: str) -> bytes:
    obj = {
        "line_items": {"data": [{"price": {"id": price_id}}]},
        "client_reference_id": str(user_id),
        "customer": customer,
    }
    return json.dumps(
        {"id": event_id, "type": "checkout.session.completed", "data": {"object": obj}}
    ).encode()


def _pay(event_id: str, price_id: str, user_id: int, customer: str) -> tuple[dict, int]:
    payload = _checkout_event(event_id, price_id, user_id=user_id, customer=customer)
    return _post(payload, _sign(payload))


def _subscription_deleted_event(event_id: str, customer: str) -> bytes:
    return json.dumps(
        {
            "id": event_id,
            "type": "customer.subscription.deleted",
            "data": {"object": {"customer": customer, "status": "canceled"}},
        }
    ).encode()


def _cancel(event_id: str, customer: str) -> tuple[dict, int]:
    payload = _subscription_deleted_event(event_id, customer)
    return _post(payload, _sign(payload))


def _grants(user_id: int) -> dict[str, str]:
    """Return the ``{granting_customer_id: plan}`` grant ledger for a user."""
    conn = app_db._connect()
    try:
        rows = conn.execute(
            "SELECT granting_customer_id, plan FROM stripe_customer_grants "
            "WHERE user_id = ?",
            (int(user_id),),
        ).fetchall()
        return {r["granting_customer_id"]: r["plan"] for r in rows}
    finally:
        conn.close()


# ── the sentinel is written by manual activations, and only by them ───────────────

def test_manual_activation_records_a_single_manual_sentinel_grant(isolated_db):
    user = _new_user("comped@acme.io")
    state = activate_plan(user["id"], "consultant")
    assert state["active_plan_name"] == "consultant"

    grants = _grants(user["id"])
    assert grants == {"manual": "consultant"}, grants


def test_manual_reactivation_upserts_the_sentinel_to_the_new_plan(isolated_db):
    user = _new_user("bumped@acme.io")
    activate_plan(user["id"], "starter_pilot")
    activate_plan(user["id"], "consultant")  # founder later bumps the tier
    # Upsert on (user, 'manual') → exactly one sentinel row, reflecting the latest.
    assert _grants(user["id"]) == {"manual": "consultant"}


def test_stripe_activation_writes_no_manual_sentinel(isolated_db, configured):
    user = _new_user("stripeonly@acme.io")
    data, status = _pay("evt_stripe_pay", PRICE_PRO, user["id"], CUS_PAID)
    assert status == 200 and data["activated"] is True

    grants = _grants(user["id"])
    assert grants == {CUS_PAID: "professional"}, grants
    assert "manual" not in grants


# ── scenario (a): the manual floor survives an unrelated Stripe cancel ────────────

def test_manual_floor_survives_unrelated_stripe_cancel(isolated_db, configured):
    user = _new_user("consultant-comped@acme.io")
    activate_plan(user["id"], "consultant")

    # A cancel for a customer that never granted this user resolves to nobody.
    data, status = _cancel("evt_unrelated_cancel", CUS_ATTACKER)
    assert status == 200
    assert get_plan_state(user["id"])["active_plan_name"] == "consultant"
    # The 'manual' sentinel is never the target of a cancel (real ids are cus_...).
    assert _grants(user["id"]) == {"manual": "consultant"}


# ── the reported bug: manual floor survives cancel of a SEPARATE paid grant ───────

def test_manual_floor_survives_cancel_of_own_paid_stripe_grant(isolated_db, configured):
    """Founder comps a paying customer up to consultant; the customer later cancels the
    now-redundant Stripe subscription → they must STAY consultant, not fall to free."""
    user = _new_user("paid-then-comped@acme.io")

    # 1. Genuine Stripe payment for professional.
    _pay("evt_pay_pro", PRICE_PRO, user["id"], CUS_PAID)
    assert get_plan_state(user["id"])["active_plan_name"] == "professional"

    # 2. Founder comps them up to consultant (manual activation → sentinel floor).
    activate_plan(user["id"], "consultant")
    assert get_plan_state(user["id"])["active_plan_name"] == "consultant"
    assert _grants(user["id"]) == {CUS_PAID: "professional", "manual": "consultant"}

    # 3. The Stripe professional subscription is cancelled. Re-derivation removes the
    #    cus_PAID grant; the surviving 'manual' floor keeps them at consultant.
    #    WITHOUT the sentinel this stripped them all the way to the free tier.
    data, status = _cancel("evt_cancel_pro", CUS_PAID)
    assert status == 200, data
    assert get_plan_state(user["id"])["active_plan_name"] == "consultant"
    assert _grants(user["id"]) == {"manual": "consultant"}


# ── scenario (b): a genuine Stripe-only customer STILL downgrades to free ──────────

def test_stripe_only_customer_still_downgrades_to_free_on_cancel(isolated_db, configured):
    user = _new_user("genuine-payer@acme.io")
    _pay("evt_pay_only", PRICE_PRO, user["id"], CUS_PAID)
    assert get_plan_state(user["id"])["active_plan_name"] == "professional"

    data, status = _cancel("evt_cancel_only", CUS_PAID)
    assert status == 200, data
    assert data["revoked"] is True and user["id"] in data["user_ids"]
    # No manual sentinel exists → the last surviving grant is gone → free.
    assert get_plan_state(user["id"])["active_plan_name"] == "evidence_preview"
    assert _grants(user["id"]) == {}


# ── scenario (c): anti-takedown — a forged/foreign cancel strips nothing ──────────

def test_forged_cancel_cannot_strip_victim_manual_floor(isolated_db, configured):
    victim = _new_user("victim@acme.io")

    # Victim genuinely pays professional, then is comped up to consultant.
    _pay("evt_victim_pay", PRICE_PRO, victim["id"], CUS_VICTIM)
    activate_plan(victim["id"], "consultant")
    assert get_plan_state(victim["id"])["active_plan_name"] == "consultant"
    assert _grants(victim["id"]) == {CUS_VICTIM: "professional", "manual": "consultant"}

    # Attacker (a DIFFERENT Stripe customer that never granted the victim) fires a
    # signed cancel. It resolves to nobody → the victim is untouched.
    data, status = _cancel("evt_attacker_cancel", CUS_ATTACKER)
    assert status == 200, data
    assert data["revoked"] is False

    assert get_plan_state(victim["id"])["active_plan_name"] == "consultant"
    assert _grants(victim["id"]) == {CUS_VICTIM: "professional", "manual": "consultant"}
