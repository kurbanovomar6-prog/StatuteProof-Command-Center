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
) -> bytes:
    obj: dict = {"line_items": {"data": [{"price": {"id": price_id}}]}}
    if client_reference_id is not None:
        obj["client_reference_id"] = str(client_reference_id)
    if customer_email is not None:
        obj["customer_email"] = customer_email
    return json.dumps(
        {"id": event_id, "type": "checkout.session.completed", "data": {"object": obj}}
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
