"""Stripe webhook — proration price selection + customer.subscription.updated.

Regression cover for two grant-mapping fixes in ``app.stripe_webhook``:

FIX A (``_extract_price_id``) — on a plan-change PRORATION ``invoice.paid`` the
``lines.data`` list carries BOTH an unused-time CREDIT for the OLD (lower) price and
the remaining-time CHARGE for the NEW (higher) price, and Stripe commonly lists the
credit FIRST. The old code returned the FIRST price, so an upgrade mapped to the OLD
lower plan and the rank guard treated it as a no-op. The fix collects EVERY price
(``lines`` / ``line_items`` / ``items``), maps each, and picks the HIGHEST tier.

FIX B (``customer.subscription.updated``) — the old handler had NO update branch, so a
mid-subscription DOWNGRADE never applied (the user kept the higher tier while paying
less). The fix adds ``_process_subscription_update`` which — exactly like revocation —
resolves users ONLY via the customer→grant ledger, touches ONLY that customer's own
grant, and re-derives the tier to the highest surviving grant. This inherits the
anti-takedown invariant: a foreign customer's update can never strip a victim below
the victim's OWN grant floor.

Uses an obvious PLACEHOLDER webhook secret — never a real ``whsec_`` value. Runs
against a REAL throwaway SQLite DB and the REAL HTTP handler.
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
from app.access_log import read_access_log
from app.db import ensure_auth_tables
from app.plan import get_plan_state

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

CUS_VICTIM = "cus_TEST_VICTIM"
CUS_ATTACKER = "cus_TEST_ATTACKER"


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "stripe_updates.db"))
    ensure_auth_tables()
    return tmp_path / "stripe_updates.db"


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
        "X-Real-IP": f"10.9.0.{_IP_SEQ[0] % 240 + 1}",
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


def _checkout_event(
    event_id: str, price_id: str, *, user_id: int, customer: str
) -> bytes:
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


def _proration_invoice_event(
    event_id: str,
    price_ids: list[str],
    *,
    user_id: int,
    customer: str,
) -> bytes:
    """An ``invoice.paid`` whose ``lines.data`` lists ``price_ids`` in order.

    A plan-change proration lists the OLD-price credit and the NEW-price charge; pass
    them in Stripe's common CREDIT-FIRST order to exercise the fix.
    """
    obj = {
        "lines": {"data": [{"price": {"id": pid}} for pid in price_ids]},
        "client_reference_id": str(user_id),
        "customer": customer,
    }
    return json.dumps(
        {"id": event_id, "type": "invoice.paid", "data": {"object": obj}}
    ).encode()


def _subscription_updated_event(event_id: str, customer: str, price_id: str) -> bytes:
    """A ``customer.subscription.updated`` carrying the subscription's current price."""
    obj = {"customer": customer, "items": {"data": [{"price": {"id": price_id}}]}}
    return json.dumps(
        {"id": event_id, "type": "customer.subscription.updated", "data": {"object": obj}}
    ).encode()


# ── FIX A — proration with a CREDIT-FIRST line maps to the NEW higher plan ─────────

def test_proration_credit_first_maps_to_new_higher_plan(isolated_db, configured):
    user = _new_user("upgrader@acme.io")
    # Start on starter.
    _pay("evt_start_starter", PRICE_STARTER, user["id"], CUS_VICTIM)
    assert get_plan_state(user["id"])["active_plan_name"] == "starter_pilot"

    # Upgrade proration: OLD (starter) credit listed FIRST, NEW (professional) charge
    # second. The first-price bug would map to starter and no-op; the fix maps to
    # professional and the rank guard lets the upgrade through.
    payload = _proration_invoice_event(
        "evt_proration_up",
        [PRICE_STARTER, PRICE_PRO],
        user_id=user["id"],
        customer=CUS_VICTIM,
    )
    data, status = _post(payload, _sign(payload))

    assert status == 200, data
    assert data["activated"] is True and data["plan"] == "professional"
    assert get_plan_state(user["id"])["active_plan_name"] == "professional"


def test_proration_selects_highest_regardless_of_order(isolated_db, configured):
    # Even three lines in an adversarial order still resolve to the top tier.
    user = _new_user("multiline@acme.io")
    payload = _proration_invoice_event(
        "evt_proration_multi",
        [PRICE_STARTER, PRICE_CONSULTANT, PRICE_PRO],
        user_id=user["id"],
        customer=CUS_VICTIM,
    )
    data, status = _post(payload, _sign(payload))
    assert status == 200, data
    assert get_plan_state(user["id"])["active_plan_name"] == "consultant"


def test_subscription_shape_items_price_is_read(isolated_db, configured):
    # The items.data[].price.id path (subscription shape) is now read by _extract_price_id.
    from app.stripe_webhook import _extract_price_id

    obj = {"items": {"data": [{"price": {"id": PRICE_STARTER}}, {"price": {"id": PRICE_PRO}}]}}
    assert _extract_price_id(obj) == PRICE_PRO  # highest-tier mapped


# ── FIX B — customer.subscription.updated applies a downgrade ──────────────────────

def test_subscription_updated_applies_downgrade(isolated_db, configured):
    user = _new_user("downgrader@acme.io")
    _pay("evt_pay_pro", PRICE_PRO, user["id"], CUS_VICTIM)
    assert get_plan_state(user["id"])["active_plan_name"] == "professional"

    # The customer self-downgrades their own subscription to starter.
    payload = _subscription_updated_event("evt_down", CUS_VICTIM, PRICE_STARTER)
    data, status = _post(payload, _sign(payload))

    assert status == 200, data
    assert data["updated"] is True and user["id"] in data["user_ids"]
    assert get_plan_state(user["id"])["active_plan_name"] == "starter_pilot"
    # …audited as a plan change tied to the Stripe event id.
    rows = read_access_log(limit=100)
    assert any(
        r["action"] == "stripe.update_plan"
        and r["result"] == "allow"
        and r["actor_user_id"] == user["id"]
        and "evt_down" in str(r["resource_id"])
        for r in rows
    ), rows


def test_subscription_updated_applies_upgrade(isolated_db, configured):
    user = _new_user("selfupgrader@acme.io")
    _pay("evt_pay_starter", PRICE_STARTER, user["id"], CUS_VICTIM)
    assert get_plan_state(user["id"])["active_plan_name"] == "starter_pilot"

    payload = _subscription_updated_event("evt_up", CUS_VICTIM, PRICE_PRO)
    data, status = _post(payload, _sign(payload))

    assert status == 200, data
    assert data["updated"] is True
    assert get_plan_state(user["id"])["active_plan_name"] == "professional"


def test_subscription_updated_from_non_grantor_is_noop(isolated_db, configured):
    user = _new_user("stillpaying@acme.io")
    _pay("evt_pay_np", PRICE_PRO, user["id"], CUS_VICTIM)

    # An update from a customer that granted nobody must not touch anyone.
    payload = _subscription_updated_event("evt_foreign_update", "cus_SOME_OTHER", PRICE_STARTER)
    data, status = _post(payload, _sign(payload))

    assert status == 200, data
    assert data["updated"] is False and data["reason"] == "no_grant"
    assert get_plan_state(user["id"])["active_plan_name"] == "professional"


# ── FIX B — anti-takedown: a foreign update cannot strip a victim's own floor ──────

def test_attacker_subscription_update_cannot_strip_victim_floor(isolated_db, configured):
    victim = _new_user("victim-floor@acme.io")

    # Victim genuinely pays professional via their OWN customer.
    _pay("evt_victim_pro", PRICE_PRO, victim["id"], CUS_VICTIM)
    assert get_plan_state(victim["id"])["active_plan_name"] == "professional"

    # Attacker gifts the victim a cheaper starter via the ATTACKER's customer (a real
    # payment aimed at the victim's client_reference_id). The rank guard refuses to
    # LOWER the active plan, but the attacker's own (starter) grant IS recorded.
    data, status = _pay("evt_attacker_gift", PRICE_STARTER, victim["id"], CUS_ATTACKER)
    assert status == 200 and data["reason"] == "protected_downgrade"
    assert get_plan_state(victim["id"])["active_plan_name"] == "professional"

    # Attacker now sends a subscription.updated on their OWN customer lowering the gift
    # even further. It updates ONLY the attacker's grant; re-derivation still takes the
    # MAX over surviving grants → professional (the victim's own). No strip.
    payload = _subscription_updated_event("evt_attacker_update", CUS_ATTACKER, PRICE_STARTER)
    data, status = _post(payload, _sign(payload))
    assert status == 200, data
    assert data["updated"] is False and data["reason"] == "no_change"
    assert get_plan_state(victim["id"])["active_plan_name"] == "professional"


def test_downgrade_of_own_grant_stops_at_higher_surviving_grant(isolated_db, configured):
    # A user holds TWO grants (own professional + a friend's consultant gift). Downgrading
    # their OWN subscription must re-derive to the surviving higher (consultant) grant.
    user = _new_user("two-grants@acme.io")
    _pay("evt_own_pro", PRICE_PRO, user["id"], CUS_VICTIM)
    _pay("evt_friend_consultant", PRICE_CONSULTANT, user["id"], "cus_FRIEND")
    assert get_plan_state(user["id"])["active_plan_name"] == "consultant"

    # The user downgrades their OWN customer to starter. Re-derivation keeps consultant
    # (the friend's surviving grant), so no downgrade lands.
    payload = _subscription_updated_event("evt_own_down", CUS_VICTIM, PRICE_STARTER)
    data, status = _post(payload, _sign(payload))
    assert status == 200, data
    assert data["updated"] is False and data["reason"] == "no_change"
    assert get_plan_state(user["id"])["active_plan_name"] == "consultant"


# ── FIX B — signature + idempotency preserved on the new path ──────────────────────

def test_forged_subscription_update_rejected(isolated_db, configured):
    user = _new_user("forgeupdate@acme.io")
    _pay("evt_pay_fu", PRICE_PRO, user["id"], CUS_VICTIM)

    payload = _subscription_updated_event("evt_forge_update", CUS_VICTIM, PRICE_STARTER)
    forged = _sign(payload, secret="whsec_wrong_secret")
    data, status = _post(payload, forged)

    assert status == 400, data
    # Downgrade never applied — still fully paid.
    assert get_plan_state(user["id"])["active_plan_name"] == "professional"


def test_replayed_subscription_update_is_idempotent(isolated_db, configured):
    user = _new_user("replayupdate@acme.io")
    _pay("evt_pay_ru", PRICE_PRO, user["id"], CUS_VICTIM)

    payload = _subscription_updated_event("evt_replay_update", CUS_VICTIM, PRICE_STARTER)
    sig = _sign(payload)
    first, s1 = _post(payload, sig)
    second, s2 = _post(payload, sig)

    assert s1 == 200 and first["updated"] is True
    assert s2 == 200 and second.get("duplicate") is True
    assert get_plan_state(user["id"])["active_plan_name"] == "starter_pilot"
    # Exactly one plan-change audit row for this event id.
    rows = read_access_log(limit=200)
    updates = [
        r for r in rows
        if r["action"] == "stripe.update_plan" and "evt_replay_update" in str(r["resource_id"])
    ]
    assert len(updates) == 1, updates


def test_unknown_price_subscription_update_is_noop(isolated_db, configured):
    user = _new_user("unknownupdate@acme.io")
    _pay("evt_pay_uu", PRICE_PRO, user["id"], CUS_VICTIM)

    # An update whose price maps to nothing must change nothing (fail-safe).
    payload = _subscription_updated_event("evt_unknown_update", CUS_VICTIM, "price_NOT_MAPPED")
    data, status = _post(payload, _sign(payload))

    assert status == 200, data
    assert data["updated"] is False and data["reason"] == "unknown_price"
    assert get_plan_state(user["id"])["active_plan_name"] == "professional"


# ── FIX (finding 3) — proration CREDIT lines are skipped so a DOWNGRADE proration
#    maps to the go-forward charged price and a late invoice.paid cannot revert a
#    completed self-service downgrade (event ordering no longer matters) ──────────

def _proration_invoice_with_amounts(event_id, lines, *, user_id, customer):
    """An ``invoice.paid`` whose lines carry realistic proration ``amount`` values.

    ``lines`` is a list of ``(price_id, amount)`` — a NEGATIVE amount models the
    unused-time CREDIT for the old price, a positive amount the go-forward CHARGE.
    """
    obj = {
        "lines": {"data": [{"price": {"id": pid}, "amount": amt} for pid, amt in lines]},
        "client_reference_id": str(user_id),
        "customer": customer,
    }
    return json.dumps(
        {"id": event_id, "type": "invoice.paid", "data": {"object": obj}}
    ).encode()


def test_extract_price_id_skips_proration_credit_lines(configured):
    from app.stripe_webhook import _extract_price_id

    # DOWNGRADE proration: the OLD (professional) line is a NEGATIVE credit, the NEW
    # (starter) line the positive go-forward charge. The old "highest-tier wins" logic
    # returned professional (reverting the downgrade); skipping credits returns starter.
    downgrade = {"lines": {"data": [
        {"price": {"id": PRICE_PRO}, "amount": -1500},
        {"price": {"id": PRICE_STARTER}, "amount": 400},
    ]}}
    assert _extract_price_id(downgrade) == PRICE_STARTER

    # UPGRADE proration still maps to the new higher charge (credit skipped either way).
    upgrade = {"lines": {"data": [
        {"price": {"id": PRICE_STARTER}, "amount": -200},
        {"price": {"id": PRICE_PRO}, "amount": 1800},
    ]}}
    assert _extract_price_id(upgrade) == PRICE_PRO


def test_late_downgrade_proration_invoice_does_not_revert(isolated_db, configured):
    """An out-of-order proration invoice.paid must not re-raise a completed downgrade."""
    user = _new_user("downgrader@acme.io")
    _pay("evt_dg_start_pro", PRICE_PRO, user["id"], CUS_VICTIM)
    assert get_plan_state(user["id"])["active_plan_name"] == "professional"

    # Self-service downgrade applied via customer.subscription.updated.
    upd = _subscription_updated_event("evt_dg_update", CUS_VICTIM, PRICE_STARTER)
    _post(upd, _sign(upd))
    assert get_plan_state(user["id"])["active_plan_name"] == "starter_pilot"

    # A LATE proration invoice.paid (Stripe does NOT guarantee event ordering) carrying
    # the OLD professional credit + NEW starter charge must NOT revert to professional.
    late = _proration_invoice_with_amounts(
        "evt_dg_late_proration",
        [(PRICE_PRO, -1500), (PRICE_STARTER, 400)],
        user_id=user["id"],
        customer=CUS_VICTIM,
    )
    data, status = _post(late, _sign(late))
    assert status == 200, data
    assert get_plan_state(user["id"])["active_plan_name"] == "starter_pilot"
