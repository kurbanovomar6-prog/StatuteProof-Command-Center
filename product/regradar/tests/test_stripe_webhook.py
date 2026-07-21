"""Stripe webhook → plan entitlement automation.

This suite covers the ONLY self-service path to ``app.plan.activate_plan``: an
unauthenticated (Stripe-called) endpoint secured by signature verification over
the RAW body, not a session. The security-critical invariants:

* a VALID signed ``checkout.session.completed`` activates the mapped plan for the
  resolved user AND writes an immutable access-log row;
* a FORGED or ABSENT signature → 400 and NOTHING is activated;
* a REPLAYED event id is an idempotent no-op (activated exactly once);
* an unknown price id → 200 ack, no activation;
* an unresolvable user → 200 ack, no activation;
* a STALE timestamp (outside tolerance) is rejected even with a valid HMAC.

The webhook secret used here is an obvious placeholder — NEVER a real value.
Runs against a REAL throwaway SQLite DB and the REAL HTTP handler.
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

import app.api as api
import app.db as app_db
from app.api import _Handler
from app.auth import create_user, mark_email_verified
from app.access_log import read_access_log
from app.db import ensure_auth_tables
from app.plan import get_plan_state

# Obvious placeholder — a TEST secret, never a real whsec_ value.
TEST_SECRET = "whsec_test_placeholder_do_not_use_in_prod"
PRICE_STARTER = "price_TEST_STARTER"
PRICE_PRO = "price_TEST_PRO"
PRICE_TO_PLAN = f"{PRICE_STARTER}:starter_pilot,{PRICE_PRO}:professional"


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "stripe_webhook.db"))
    ensure_auth_tables()
    return tmp_path / "stripe_webhook.db"


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
        "X-Real-IP": f"10.7.0.{_IP_SEQ[0] % 240 + 1}",
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


def _checkout_event(
    event_id: str,
    price_id: str,
    *,
    client_reference_id: str | int | None = None,
    customer_email: str | None = None,
    customer: str | None = None,
) -> bytes:
    obj: dict = {"line_items": {"data": [{"price": {"id": price_id}}]}}
    if client_reference_id is not None:
        obj["client_reference_id"] = str(client_reference_id)
    if customer_email is not None:
        obj["customer_email"] = customer_email
    if customer is not None:
        obj["customer"] = customer
    return json.dumps(
        {"id": event_id, "type": "checkout.session.completed", "data": {"object": obj}}
    ).encode()


def _subscription_deleted_event(event_id: str, customer: str) -> bytes:
    """A ``customer.subscription.deleted`` (cancellation) event for ``customer``."""
    return json.dumps(
        {
            "id": event_id,
            "type": "customer.subscription.deleted",
            "data": {"object": {"customer": customer, "status": "canceled"}},
        }
    ).encode()


def _charge_refunded_event(
    event_id: str,
    customer: str,
    *,
    amount: int = 39900,
    amount_refunded: int | None = None,
    refunded: bool = True,
) -> bytes:
    """A ``charge.refunded`` event. Full refund by default; pass a smaller
    ``amount_refunded`` with ``refunded=False`` for a partial refund."""
    if amount_refunded is None:
        amount_refunded = amount
    return json.dumps(
        {
            "id": event_id,
            "type": "charge.refunded",
            "data": {
                "object": {
                    "customer": customer,
                    "amount": amount,
                    "amount_refunded": amount_refunded,
                    "refunded": refunded,
                }
            },
        }
    ).encode()


def _invoice_failed_event(
    event_id: str, customer: str, *, next_payment_attempt: int | None
) -> bytes:
    """An ``invoice.payment_failed`` event. ``next_payment_attempt=None`` marks the
    FINAL (no-more-retries) failure; an integer marks an interim retry pending."""
    return json.dumps(
        {
            "id": event_id,
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "customer": customer,
                    "next_payment_attempt": next_payment_attempt,
                }
            },
        }
    ).encode()


def _dispute_created_event(event_id: str, customer: str) -> bytes:
    """A ``charge.dispute.created`` (chargeback) event for ``customer``."""
    return json.dumps(
        {
            "id": event_id,
            "type": "charge.dispute.created",
            "data": {"object": {"customer": customer, "status": "warning_needs_response"}},
        }
    ).encode()


def _new_user(email: str) -> dict:
    user = create_user(email, "password-123")
    return {"id": int(user["id"]), "email": user["email"]}


# ── happy path: valid signed checkout activates the mapped plan + audits ──────────

def test_valid_signed_checkout_activates_and_audits(isolated_db, configured):
    customer = _new_user("buyer@acme.io")
    payload = _checkout_event("evt_ok_1", PRICE_PRO, client_reference_id=customer["id"])

    data, status = _post(payload, _sign(payload))

    assert status == 200, data
    assert data["ok"] is True and data["activated"] is True
    # The entitlement actually changed to the mapped plan.
    assert get_plan_state(customer["id"])["active_plan_name"] == "professional"
    # …and it is in the immutable access log, tied to the Stripe event id.
    rows = read_access_log(limit=50)
    assert any(
        r["action"] == "stripe.activate_plan"
        and r["result"] == "allow"
        and r["actor_user_id"] == customer["id"]
        and "evt_ok_1" in str(r["resource_id"])
        for r in rows
    ), rows


def test_starter_plan_mapping(isolated_db, configured):
    customer = _new_user("starter@acme.io")
    payload = _checkout_event("evt_ok_2", PRICE_STARTER, client_reference_id=customer["id"])
    data, status = _post(payload, _sign(payload))
    assert status == 200, data
    assert get_plan_state(customer["id"])["active_plan_name"] == "starter_pilot"


# ── forged / absent signature → 400 and NO activation ─────────────────────────────

def test_forged_signature_rejected_no_activation(isolated_db, configured):
    customer = _new_user("victim@acme.io")
    payload = _checkout_event("evt_forge", PRICE_PRO, client_reference_id=customer["id"])
    # Sign with the WRONG secret — a forgery.
    forged = _sign(payload, secret="whsec_wrong_secret")

    data, status = _post(payload, forged)

    assert status == 400, data
    assert data["ok"] is False
    assert get_plan_state(customer["id"])["active_plan_name"] == "evidence_preview"


def test_tampered_body_rejected(isolated_db, configured):
    customer = _new_user("tamper@acme.io")
    payload = _checkout_event("evt_tamper", PRICE_PRO, client_reference_id=customer["id"])
    sig = _sign(payload)  # signature over the ORIGINAL body
    tampered = payload.replace(b"evt_tamper", b"evt_tamperX")

    data, status = _post(tampered, sig)

    assert status == 400, data
    assert get_plan_state(customer["id"])["active_plan_name"] == "evidence_preview"


def test_absent_signature_rejected_no_activation(isolated_db, configured):
    customer = _new_user("nosig@acme.io")
    payload = _checkout_event("evt_nosig", PRICE_PRO, client_reference_id=customer["id"])

    data, status = _post(payload, None)

    assert status == 400, data
    assert get_plan_state(customer["id"])["active_plan_name"] == "evidence_preview"


# ── replay → idempotent no-op (activated exactly once) ────────────────────────────

def test_replayed_event_is_idempotent(isolated_db, configured):
    customer = _new_user("replay@acme.io")
    payload = _checkout_event("evt_replay", PRICE_PRO, client_reference_id=customer["id"])
    sig = _sign(payload)

    first, s1 = _post(payload, sig)
    second, s2 = _post(payload, sig)

    assert s1 == 200 and first["activated"] is True
    assert s2 == 200 and second.get("duplicate") is True
    # Exactly one activation audit row for this event id.
    rows = read_access_log(limit=100)
    activations = [
        r for r in rows
        if r["action"] == "stripe.activate_plan" and "evt_replay" in str(r["resource_id"])
    ]
    assert len(activations) == 1, activations


# ── unknown price → 200 ack, no activation ────────────────────────────────────────

def test_unknown_price_acks_without_activating(isolated_db, configured):
    customer = _new_user("unknownprice@acme.io")
    payload = _checkout_event(
        "evt_unknown_price", "price_NOT_MAPPED", client_reference_id=customer["id"]
    )

    data, status = _post(payload, _sign(payload))

    assert status == 200, data
    assert data["activated"] is False and data["reason"] == "unknown_price"
    assert get_plan_state(customer["id"])["active_plan_name"] == "evidence_preview"


# ── unresolvable user → 200 ack, no activation ────────────────────────────────────

def test_unresolvable_user_acks_without_activating(isolated_db, configured):
    # No client_reference_id, and an email that matches no account.
    payload = _checkout_event(
        "evt_no_user", PRICE_PRO, customer_email="ghost@nowhere.example"
    )

    data, status = _post(payload, _sign(payload))

    assert status == 200, data
    assert data["activated"] is False and data["reason"] == "unresolved_user"


def test_unverified_email_does_not_resolve(isolated_db, configured):
    # An existing but UNVERIFIED account must not be entitled by email match.
    customer = _new_user("unverified@acme.io")
    payload = _checkout_event(
        "evt_unverified", PRICE_PRO, customer_email="unverified@acme.io"
    )

    data, status = _post(payload, _sign(payload))

    assert status == 200, data
    assert data["activated"] is False
    assert get_plan_state(customer["id"])["active_plan_name"] == "evidence_preview"


def test_verified_email_fallback_resolves(isolated_db, configured):
    customer = _new_user("verified@acme.io")
    mark_email_verified(customer["id"])
    payload = _checkout_event(
        "evt_verified", PRICE_PRO, customer_email="verified@acme.io"
    )

    data, status = _post(payload, _sign(payload))

    assert status == 200, data
    assert data["activated"] is True
    assert get_plan_state(customer["id"])["active_plan_name"] == "professional"


# ── stale timestamp rejected even with a valid HMAC ───────────────────────────────

def test_stale_timestamp_rejected(isolated_db, configured):
    customer = _new_user("stale@acme.io")
    payload = _checkout_event("evt_stale", PRICE_PRO, client_reference_id=customer["id"])
    # Correct HMAC, but the signed timestamp is far outside the tolerance window.
    stale_sig = _sign(payload, timestamp=int(time.time()) - 10_000)

    data, status = _post(payload, stale_sig)

    assert status == 400, data
    assert get_plan_state(customer["id"])["active_plan_name"] == "evidence_preview"


# ── fail-closed when no secret is configured ──────────────────────────────────────

def test_no_secret_configured_rejects(isolated_db, monkeypatch):
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    monkeypatch.setenv("STRIPE_PRICE_TO_PLAN", PRICE_TO_PLAN)
    customer = _new_user("nosecret@acme.io")
    payload = _checkout_event("evt_nosecret", PRICE_PRO, client_reference_id=customer["id"])

    # Even a "valid" signature can't help — the server has no secret to verify with.
    data, status = _post(payload, _sign(payload))

    assert status == 400, data
    assert get_plan_state(customer["id"])["active_plan_name"] == "evidence_preview"


# ── REVOCATION — the actual fix, and the anti-takedown design that makes it safe ──
#
# Cycle-12 added revocation and was reverted because it introduced a customer
# TAKEDOWN: with client-side Payment Links the buyer controls both the typed email
# and the client_reference_id, so an attacker could weaponise a refund/cancel to
# strip a paying victim. These tests pin the SAFE design: grants are a SET of
# (user, customer) pairs, revocation resolves the user ONLY through that ledger
# and removes ONLY the revoked customer's grant, downgrading solely when the user
# has ZERO remaining grants — so an attacker's cancel can only ever drop the
# attacker's OWN grant, never a victim's separate grant (in EITHER order), and an
# activation can never LOWER a paying victim's tier (the rank guard).

CUS_VICTIM = "cus_TEST_VICTIM"
CUS_ATTACKER = "cus_TEST_ATTACKER"


def _pay(event_id: str, price_id: str, user_id: int, customer: str) -> tuple[dict, int]:
    """Drive a signed, grantor-recording checkout activation for ``user_id``."""
    payload = _checkout_event(
        event_id, price_id, client_reference_id=user_id, customer=customer
    )
    return _post(payload, _sign(payload))


# (a) a valid cancel BY THE GRANTING CUSTOMER downgrades the user to free + audits
def test_valid_cancel_by_grantor_downgrades_and_audits(isolated_db, configured):
    customer = _new_user("cancelme@acme.io")
    _pay("evt_pay_a", PRICE_PRO, customer["id"], CUS_VICTIM)
    assert get_plan_state(customer["id"])["active_plan_name"] == "professional"

    payload = _subscription_deleted_event("evt_cancel_a", CUS_VICTIM)
    data, status = _post(payload, _sign(payload))

    assert status == 200, data
    assert data["revoked"] is True and customer["id"] in data["user_ids"]
    assert get_plan_state(customer["id"])["active_plan_name"] == "evidence_preview"
    rows = read_access_log(limit=100)
    assert any(
        r["action"] == "stripe.revoke_plan"
        and r["result"] == "allow"
        and r["actor_user_id"] == customer["id"]
        and "evt_cancel_a" in str(r["resource_id"])
        for r in rows
    ), rows


# (b) THE TAKEDOWN — the exact Cycle-12 attack (victim pays FIRST), which MUST FAIL
def test_cycle12_takedown_is_defeated(isolated_db, configured):
    victim = _new_user("victim-paid@acme.io")
    attacker_target = victim  # attacker aims the strip at the paying victim

    # 1) Victim genuinely pays via their own customer.
    _pay("evt_victim_pay", PRICE_PRO, victim["id"], CUS_VICTIM)
    assert get_plan_state(victim["id"])["active_plan_name"] == "professional"

    # 2) Attacker "activates" the victim via the ATTACKER's customer — controlling
    #    the client_reference_id (buyer-typed on a client-side Payment Link). Under
    #    the SET model this merely APPENDS a separate (victim, cus_ATTACKER) grant;
    #    the victim's own grant is untouched and the plan is unchanged.
    data, status = _pay("evt_attacker_pay", PRICE_PRO, attacker_target["id"], CUS_ATTACKER)
    assert status == 200, data
    assert get_plan_state(victim["id"])["active_plan_name"] == "professional"

    # 3) Attacker cancels / refunds their OWN customer to try to strip the victim.
    #    Only the attacker's grant is removed; the victim's cus_VICTIM grant
    #    survives, so there is NO downgrade.
    cancel = _subscription_deleted_event("evt_attacker_cancel", CUS_ATTACKER)
    data, status = _post(cancel, _sign(cancel))
    assert status == 200, data
    assert data["revoked"] is False  # the surviving victim grant blocks any downgrade

    refund = _charge_refunded_event("evt_attacker_refund", CUS_ATTACKER)
    data, status = _post(refund, _sign(refund))
    assert status == 200, data
    assert data["revoked"] is False

    # The victim is STILL fully paid throughout — the takedown is defeated.
    assert get_plan_state(victim["id"])["active_plan_name"] == "professional"


# (b2) GIFT-FIRST ORDERING — the attacker records a grant BEFORE the victim pays.
# This is the ordering that broke the single-grantor design (the round-1 blocker):
# the victim's later genuine payment must still survive the attacker's cancel.
def test_gift_first_then_victim_pays_cannot_be_stripped(isolated_db, configured):
    victim = _new_user("victim-latepay@acme.io")

    # 1) Attacker gifts the (still-FREE) victim a plan via the ATTACKER's customer,
    #    aiming the client_reference_id at the victim.
    data, status = _pay("evt_gift_first", PRICE_PRO, victim["id"], CUS_ATTACKER)
    assert status == 200 and data["activated"] is True
    assert get_plan_state(victim["id"])["active_plan_name"] == "professional"

    # 2) The victim then GENUINELY subscribes and pays via their OWN customer. Even
    #    though they are already 'paid' (via the gift), this MUST record a second,
    #    independent (victim, cus_VICTIM) grant — not be blocked.
    data, status = _pay("evt_victim_latepay", PRICE_PRO, victim["id"], CUS_VICTIM)
    assert status == 200, data
    assert get_plan_state(victim["id"])["active_plan_name"] == "professional"

    # 3) The attacker cancels AND refunds their own customer to strip the victim.
    cancel = _subscription_deleted_event("evt_gift_cancel", CUS_ATTACKER)
    data, status = _post(cancel, _sign(cancel))
    assert status == 200, data
    assert data["revoked"] is False  # victim's own grant survives → no downgrade

    refund = _charge_refunded_event("evt_gift_refund", CUS_ATTACKER)
    data, status = _post(refund, _sign(refund))
    assert status == 200, data
    assert data["revoked"] is False

    # The victim keeps the plan they are genuinely paying for — no strip.
    assert get_plan_state(victim["id"])["active_plan_name"] == "professional"


# (b3) DOWNGRADE-GIFT GUARD — a gift of a CHEAPER plan can never lower a paying
# victim's active tier. The attacker's grant IS recorded (so it cannot pin a
# phantom below the victim's own), but the victim's higher grant always survives
# the attacker's cancel, so the victim is never stripped.
def test_cheaper_gift_cannot_downgrade_a_paying_user(isolated_db, configured):
    victim = _new_user("victim-pro@acme.io")
    _pay("evt_pro_pay", PRICE_PRO, victim["id"], CUS_VICTIM)
    assert get_plan_state(victim["id"])["active_plan_name"] == "professional"

    # Attacker "gifts" a cheaper starter plan via their own customer, aimed at the
    # professional victim. The rank guard refuses to LOWER the active plan; the
    # attacker's own (starter) grant is recorded but it is ranked below the
    # victim's professional grant, so it can never raise or defend anything.
    data, status = _pay("evt_cheap_gift", PRICE_STARTER, victim["id"], CUS_ATTACKER)
    assert status == 200, data
    assert data["activated"] is False and data["reason"] == "protected_downgrade"
    assert get_plan_state(victim["id"])["active_plan_name"] == "professional"

    # The attacker cancel removes only the attacker's starter grant; the victim's
    # professional grant survives and still justifies professional → no downgrade.
    cancel = _subscription_deleted_event("evt_cheap_cancel", CUS_ATTACKER)
    data, status = _post(cancel, _sign(cancel))
    assert status == 200, data
    assert data["revoked"] is False and data["reason"] == "still_granted"
    assert get_plan_state(victim["id"])["active_plan_name"] == "professional"


# (b4) GIFT-HIGHER-FIRST, VICTIM-PAYS-LOWER — the round-2 blocker. The attacker
# gifts a HIGHER plan while the victim is FREE, the victim then genuinely pays a
# LOWER tier (blocked by the rank guard from raising the active plan), and the
# attacker cancels. The victim MUST land on exactly the tier they pay for — never
# stripped to free — because their own lower grant was recorded and survives.
def test_gift_higher_then_victim_pays_lower_is_not_stripped(isolated_db, configured):
    victim = _new_user("victim-lowerpay@acme.io")
    assert get_plan_state(victim["id"])["active_plan_name"] == "evidence_preview"

    # 1) Attacker gifts the (FREE) victim a HIGHER plan via the attacker's customer.
    data, status = _pay("evt_hi_gift", PRICE_PRO, victim["id"], CUS_ATTACKER)
    assert status == 200 and data["activated"] is True
    assert get_plan_state(victim["id"])["active_plan_name"] == "professional"

    # 2) Victim genuinely subscribes to a LOWER tier via their OWN customer. The
    #    rank guard leaves the active plan at professional (never lowers), but the
    #    victim's (starter) grant MUST be recorded so it survives an attacker cancel.
    data, status = _pay("evt_lo_pay", PRICE_STARTER, victim["id"], CUS_VICTIM)
    assert status == 200, data
    assert data["activated"] is False and data["reason"] == "protected_downgrade"
    assert get_plan_state(victim["id"])["active_plan_name"] == "professional"

    # 3) Attacker cancels their own customer. The professional grant is removed; the
    #    victim's surviving starter grant re-derives the tier to STARTER — exactly
    #    what the victim pays for. NOT stripped to free.
    cancel = _subscription_deleted_event("evt_hi_cancel", CUS_ATTACKER)
    data, status = _post(cancel, _sign(cancel))
    assert status == 200, data
    assert data["revoked"] is True and victim["id"] in data["user_ids"]
    assert get_plan_state(victim["id"])["active_plan_name"] == "starter_pilot"

    # 4) A refund replay of the attacker's (now grant-less) customer is a pure no-op;
    #    the victim keeps the tier they pay for.
    refund = _charge_refunded_event("evt_hi_refund", CUS_ATTACKER)
    data, status = _post(refund, _sign(refund))
    assert status == 200, data
    assert data["revoked"] is False and data["reason"] == "no_grant"
    assert get_plan_state(victim["id"])["active_plan_name"] == "starter_pilot"


# (c) a cancel from a customer that is NOT the current grantor → no-op
def test_cancel_from_non_grantor_customer_is_noop(isolated_db, configured):
    customer = _new_user("stillpaying@acme.io")
    _pay("evt_pay_c", PRICE_PRO, customer["id"], CUS_VICTIM)

    payload = _subscription_deleted_event("evt_cancel_c", "cus_SOME_OTHER")
    data, status = _post(payload, _sign(payload))

    assert status == 200, data
    assert data["revoked"] is False and data["reason"] == "no_grant"
    assert get_plan_state(customer["id"])["active_plan_name"] == "professional"


# (d) forged / absent / stale signature on a cancel → 400, no downgrade
def test_forged_cancel_signature_does_not_downgrade(isolated_db, configured):
    customer = _new_user("forgecancel@acme.io")
    _pay("evt_pay_d", PRICE_PRO, customer["id"], CUS_VICTIM)

    cancel = _subscription_deleted_event("evt_cancel_d", CUS_VICTIM)
    forged = _sign(cancel, secret="whsec_wrong_secret")
    data, status = _post(cancel, forged)
    assert status == 400, data
    assert get_plan_state(customer["id"])["active_plan_name"] == "professional"

    # Absent signature — also rejected, still paid.
    data, status = _post(cancel, None)
    assert status == 400, data
    assert get_plan_state(customer["id"])["active_plan_name"] == "professional"

    # Stale but correctly-keyed HMAC — rejected, still paid.
    stale = _sign(cancel, timestamp=int(time.time()) - 10_000)
    data, status = _post(cancel, stale)
    assert status == 400, data
    assert get_plan_state(customer["id"])["active_plan_name"] == "professional"


# (e) a replayed cancel is idempotent (downgrades once, one audit row)
def test_replayed_cancel_is_idempotent(isolated_db, configured):
    customer = _new_user("replaycancel@acme.io")
    _pay("evt_pay_e", PRICE_PRO, customer["id"], CUS_VICTIM)

    cancel = _subscription_deleted_event("evt_cancel_e", CUS_VICTIM)
    sig = _sign(cancel)
    first, s1 = _post(cancel, sig)
    second, s2 = _post(cancel, sig)

    assert s1 == 200 and first["revoked"] is True
    assert s2 == 200 and second.get("duplicate") is True
    assert get_plan_state(customer["id"])["active_plan_name"] == "evidence_preview"
    rows = read_access_log(limit=200)
    revocations = [
        r for r in rows
        if r["action"] == "stripe.revoke_plan" and "evt_cancel_e" in str(r["resource_id"])
    ]
    assert len(revocations) == 1, revocations


# (f) gift-then-strip of a currently-FREE user → back to free (net-zero, allowed)
def test_gift_then_strip_of_free_user_is_net_zero(isolated_db, configured):
    free_user = _new_user("gifted@acme.io")
    assert get_plan_state(free_user["id"])["active_plan_name"] == "evidence_preview"

    # A customer gifts the free user a paid plan (allowed — user was FREE).
    data, status = _pay("evt_gift", PRICE_PRO, free_user["id"], CUS_ATTACKER)
    assert status == 200 and data["activated"] is True
    assert get_plan_state(free_user["id"])["active_plan_name"] == "professional"

    # …then strips it. The user returns to free — net-zero, the sole harmless residual.
    cancel = _subscription_deleted_event("evt_gift_strip", CUS_ATTACKER)
    data, status = _post(cancel, _sign(cancel))
    assert status == 200 and data["revoked"] is True
    assert get_plan_state(free_user["id"])["active_plan_name"] == "evidence_preview"


# (g) final invoice.payment_failed by the grantor → downgrade; non-final → no-op
def test_invoice_failure_only_downgrades_when_final(isolated_db, configured):
    customer = _new_user("dunning@acme.io")
    _pay("evt_pay_g", PRICE_PRO, customer["id"], CUS_VICTIM)

    # A non-final failure (a retry is still scheduled) is a no-op — stays paid.
    interim = _invoice_failed_event(
        "evt_fail_interim", CUS_VICTIM, next_payment_attempt=int(time.time()) + 86_400
    )
    data, status = _post(interim, _sign(interim))
    assert status == 200, data
    assert data["revoked"] is False and data["reason"] == "not_final"
    assert get_plan_state(customer["id"])["active_plan_name"] == "professional"

    # The FINAL failure (no more retries) downgrades to free.
    final = _invoice_failed_event("evt_fail_final", CUS_VICTIM, next_payment_attempt=None)
    data, status = _post(final, _sign(final))
    assert status == 200, data
    assert data["revoked"] is True
    assert get_plan_state(customer["id"])["active_plan_name"] == "evidence_preview"


# a full refund downgrades; a partial refund does not
def test_partial_refund_does_not_downgrade_full_refund_does(isolated_db, configured):
    customer = _new_user("refundme@acme.io")
    _pay("evt_pay_ref", PRICE_PRO, customer["id"], CUS_VICTIM)

    partial = _charge_refunded_event(
        "evt_partial", CUS_VICTIM, amount=39900, amount_refunded=10000, refunded=False
    )
    data, status = _post(partial, _sign(partial))
    assert status == 200, data
    assert data["revoked"] is False and data["reason"] == "not_final"
    assert get_plan_state(customer["id"])["active_plan_name"] == "professional"

    full = _charge_refunded_event("evt_full_refund", CUS_VICTIM)
    data, status = _post(full, _sign(full))
    assert status == 200, data
    assert data["revoked"] is True
    assert get_plan_state(customer["id"])["active_plan_name"] == "evidence_preview"


# a chargeback (dispute created) by the grantor downgrades
def test_dispute_created_by_grantor_downgrades(isolated_db, configured):
    customer = _new_user("chargeback@acme.io")
    _pay("evt_pay_disp", PRICE_PRO, customer["id"], CUS_VICTIM)

    payload = _dispute_created_event("evt_dispute", CUS_VICTIM)
    data, status = _post(payload, _sign(payload))

    assert status == 200, data
    assert data["revoked"] is True
    assert get_plan_state(customer["id"])["active_plan_name"] == "evidence_preview"
