"""Stripe webhook → plan entitlement automation.

This is the ONLY self-service path that reaches ``app.plan.activate_plan``. It
turns a *verified* Stripe payment event into the exact same founder-only
activation the admin panel and ``run.py activate-plan`` CLI perform — no forked
entitlement logic, no new capability model.

SECURITY POSTURE (this endpoint grants paid access, so it is treated as hostile
input end to end):

* NON-FORGEABILITY — the request is authenticated by the Stripe signature over
  the RAW request body, never by a session. The signing scheme is HMAC-SHA256 of
  ``"{timestamp}.{raw_body}"`` with ``STRIPE_WEBHOOK_SECRET`` (the documented
  Stripe scheme), compared in constant time. A missing / malformed / wrong
  signature is rejected with 400 and NOTHING is activated. The ``stripe`` SDK is
  not a dependency (see requirements.txt), so verification is implemented with
  the stdlib ``hmac`` / ``hashlib``.
* REPLAY — the signed timestamp must be within ``TOLERANCE_SECONDS`` of now, and
  every processed Stripe event id is persisted (``stripe_webhook_events``) under
  a UNIQUE constraint BEFORE activation, so a redelivered or captured-and-replayed
  event activates AT MOST ONCE.
* AMBIGUITY NEVER ACTIVATES — an unknown price id or an unresolvable user is
  acknowledged with 200 (so Stripe stops retrying) but activates NOTHING.

CONFIG (owner fills real values — this module invents none):
* ``STRIPE_WEBHOOK_SECRET``  — the ``whsec_...`` signing secret for THIS endpoint.
  Unset ⇒ the webhook is disabled and every call is rejected (fail-closed).
* ``STRIPE_PRICE_TO_PLAN``   — comma-separated ``price_id:plan_name`` pairs, e.g.
  ``price_abc:starter_pilot,price_def:professional``. ``plan_name`` must be a
  known plan (``app.plan.PLAN_NAMES``). Unknown/blank entries are ignored.

USER RESOLUTION (documented, deterministic):
1. ``client_reference_id`` on the checkout session — the StatuteProof user id the
   frontend MUST set when creating the Checkout Session. This is the primary,
   unambiguous binding.
2. Fallback: ``customer_email`` / ``customer_details.email`` matched to an
   existing account whose email is VERIFIED. An unverified or unknown email does
   NOT resolve (never activate a plan for an address nobody proved they own).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

from app.access_log import append_access_log
from app.db import _connect, ensure_stripe_events_table

logger = logging.getLogger(__name__)

# Stripe's default webhook tolerance. A signed timestamp older/newer than this is
# rejected, which — together with the idempotency ledger — bounds replay.
TOLERANCE_SECONDS = 300

# Events that represent a completed payment we entitle on. Both carry the line
# items / price we map to a plan.
_ACTIVATING_EVENT_TYPES = frozenset({"checkout.session.completed", "invoice.paid"})

# Audit action label recorded in the immutable access log.
STRIPE_ACTIVATE = "stripe.activate_plan"


# ── config ──────────────────────────────────────────────────────────────────────

def _webhook_secret() -> str:
    """The configured Stripe signing secret, or ``""`` when unset (disabled)."""
    return str(os.environ.get("STRIPE_WEBHOOK_SECRET", "") or "").strip()


def plan_for_price(price_id: str) -> str | None:
    """Map a Stripe price id to a known StatuteProof plan, or ``None``.

    Reads ``STRIPE_PRICE_TO_PLAN`` (``price:plan,price:plan``). Only pairs whose
    plan is in ``PLAN_NAMES`` are honoured; a typo or an unknown plan yields no
    mapping (and therefore no activation), never a crash.
    """
    pid = str(price_id or "").strip()
    if not pid:
        return None
    from app.plan import PLAN_NAMES

    raw = str(os.environ.get("STRIPE_PRICE_TO_PLAN", "") or "")
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair or ":" not in pair:
            continue
        key, _, value = pair.partition(":")
        if key.strip() == pid:
            plan = value.strip()
            return plan if plan in PLAN_NAMES else None
    return None


# ── signature verification (stdlib HMAC-SHA256, Stripe's documented scheme) ──────

def verify_signature(
    payload: bytes,
    sig_header: str,
    secret: str,
    *,
    tolerance: int = TOLERANCE_SECONDS,
    now: int | None = None,
) -> bool:
    """Return True only for a genuine, in-window Stripe signature over ``payload``.

    ``sig_header`` is the raw ``Stripe-Signature`` value:
    ``t=<unix>,v1=<hex>[,v1=<hex>...]``. The signed payload is
    ``"{t}.{raw_body}"`` and the expected signature is its HMAC-SHA256 (hex) keyed
    by ``secret``. Every ``v1`` candidate is compared in constant time
    (``hmac.compare_digest``). Fails closed on any missing piece: no secret, no
    header, no timestamp, no ``v1``, an out-of-tolerance timestamp, or a mismatch.
    Never raises.
    """
    if not secret or not payload or not sig_header:
        return False
    timestamp: str | None = None
    v1_signatures: list[str] = []
    for part in str(sig_header).split(","):
        key, _, value = part.strip().partition("=")
        key = key.strip()
        value = value.strip()
        if key == "t":
            timestamp = value
        elif key == "v1":
            v1_signatures.append(value)
    if not timestamp or not v1_signatures:
        return False

    # Replay window: reject a timestamp too far from now in EITHER direction.
    try:
        ts_int = int(timestamp)
    except (TypeError, ValueError):
        return False
    current = int(time.time()) if now is None else int(now)
    if abs(current - ts_int) > int(tolerance):
        return False

    signed_payload = timestamp.encode("utf-8") + b"." + payload
    expected = hmac.new(
        secret.encode("utf-8"), signed_payload, hashlib.sha256
    ).hexdigest()
    # Constant-time compare against each provided v1 (Stripe may send several
    # during a secret rotation). Any match authenticates.
    return any(hmac.compare_digest(expected, candidate) for candidate in v1_signatures)


# ── idempotency ledger ───────────────────────────────────────────────────────────

def _claim_event(event_id: str, event_type: str) -> bool:
    """Atomically claim ``event_id`` for processing. True = newly claimed.

    Inserts the id under the UNIQUE constraint. If the row already exists (Stripe
    redelivery or a replay), the insert fails and we return False so the caller
    no-ops. Claiming BEFORE activation is what makes double-activation impossible.
    """
    ensure_stripe_events_table()
    ts = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO stripe_webhook_events (event_id, event_type, processed_at) "
            "VALUES (?, ?, ?)",
            (str(event_id), str(event_type or ""), ts),
        )
        conn.commit()
        return True
    except Exception:  # noqa: BLE001 — a UNIQUE collision (or any insert failure) → not newly claimed
        return False
    finally:
        conn.close()


def _record_outcome(event_id: str, outcome: str) -> None:
    """Best-effort note of what happened to a claimed event (never raises)."""
    try:
        conn = _connect()
        try:
            conn.execute(
                "UPDATE stripe_webhook_events SET outcome = ? WHERE event_id = ?",
                (str(outcome), str(event_id)),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:  # noqa: BLE001 — audit metadata only; must not affect the ack
        logger.warning("stripe webhook: failed to record outcome for %s", event_id)


# ── user + price extraction ──────────────────────────────────────────────────────

def _extract_price_id(obj: dict) -> str | None:
    """Best-effort price id from a checkout.session / invoice event object.

    Checkout sessions do not embed line items by default, so we read the common
    locations Stripe populates: invoice lines (``lines.data[].price.id``) and, if
    the integration expands them, checkout ``line_items``. Returns the first price
    id found, else None (→ handled as an unknown price = no activation).
    """
    if not isinstance(obj, dict):
        return None
    # invoice.paid → lines.data[].price.id
    lines = obj.get("lines")
    if isinstance(lines, dict):
        for item in lines.get("data") or []:
            if isinstance(item, dict):
                price = item.get("price")
                if isinstance(price, dict) and price.get("id"):
                    return str(price["id"])
    # checkout.session.completed (when line_items are expanded) → line_items.data[].price.id
    line_items = obj.get("line_items")
    if isinstance(line_items, dict):
        for item in line_items.get("data") or []:
            if isinstance(item, dict):
                price = item.get("price")
                if isinstance(price, dict) and price.get("id"):
                    return str(price["id"])
    return None


def _resolve_user(obj: dict) -> dict | None:
    """Resolve the StatuteProof user this payment entitles, or None (ambiguous).

    Primary: ``client_reference_id`` = the StatuteProof user id set at checkout.
    Fallback: ``customer_email`` / ``customer_details.email`` matched to an
    account whose email is VERIFIED. Any other case (no reference, unknown email,
    unverified email) resolves to None so the caller acknowledges WITHOUT
    activating. Never raises.
    """
    if not isinstance(obj, dict):
        return None
    from app.auth import get_user_by_email, get_user_by_id

    ref = obj.get("client_reference_id")
    if ref is not None and str(ref).strip():
        try:
            user = get_user_by_id(int(str(ref).strip()))
            if user:
                return user
        except (TypeError, ValueError):
            pass  # non-numeric reference → fall through to email

    email = obj.get("customer_email")
    if not email:
        details = obj.get("customer_details")
        if isinstance(details, dict):
            email = details.get("email")
    if email and str(email).strip():
        try:
            user = get_user_by_email(str(email).strip())
        except Exception:  # noqa: BLE001 — a lookup failure must not activate
            user = None
        # Only a VERIFIED account resolves by email — never activate for an
        # address whose ownership was not proven.
        if user and bool(user.get("email_verified")):
            return user
    return None


# ── orchestration ────────────────────────────────────────────────────────────────

def handle_webhook(payload: bytes, sig_header: str) -> tuple[int, dict[str, Any]]:
    """Verify, parse, and act on a raw Stripe webhook. Returns (status, body).

    Contract:
    * bad/missing signature or disabled secret → (400, ...); NEVER activates.
    * verified but replayed event id            → (200, already-processed no-op).
    * verified activating event, mapped price + resolved user → activate_plan,
      audit, (200, activated).
    * verified but unknown price / unresolvable user / non-activating type →
      (200, ack) with NO activation (never make Stripe retry a benign event).
    """
    secret = _webhook_secret()
    if not secret:
        # Fail-closed: with no configured secret we cannot authenticate anything.
        logger.warning("stripe webhook called but STRIPE_WEBHOOK_SECRET is unset")
        return 400, {"ok": False, "error": "Webhook not configured."}

    if not verify_signature(payload, sig_header, secret):
        return 400, {"ok": False, "error": "Signature verification failed."}

    # Signature verified over the RAW bytes — only now is it safe to parse JSON.
    try:
        event = json.loads(payload.decode("utf-8"))
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
        return 400, {"ok": False, "error": "Invalid JSON."}
    if not isinstance(event, dict):
        return 400, {"ok": False, "error": "Event must be an object."}

    event_id = str(event.get("id") or "").strip()
    event_type = str(event.get("type") or "").strip()
    if not event_id:
        return 400, {"ok": False, "error": "Event id missing."}

    # Non-activating event types are acknowledged and ignored (no ledger entry —
    # we only spend an idempotency slot on events we would act on).
    if event_type not in _ACTIVATING_EVENT_TYPES:
        return 200, {"ok": True, "ignored": event_type or "unknown"}

    # Idempotency: claim the id BEFORE any activation. A redelivery/replay loses
    # the claim and no-ops.
    if not _claim_event(event_id, event_type):
        return 200, {"ok": True, "duplicate": True}

    obj = event.get("data", {})
    obj = obj.get("object") if isinstance(obj, dict) else None
    if not isinstance(obj, dict):
        _record_outcome(event_id, "no_object")
        return 200, {"ok": True, "activated": False, "reason": "no_object"}

    price_id = _extract_price_id(obj)
    plan = plan_for_price(price_id) if price_id else None
    if not plan:
        # Unknown/unmapped price → ack, do not activate, do not 500-loop Stripe.
        _record_outcome(event_id, "unknown_price")
        logger.info("stripe webhook %s: no plan mapping for price %r", event_id, price_id)
        return 200, {"ok": True, "activated": False, "reason": "unknown_price"}

    user = _resolve_user(obj)
    if not user:
        _record_outcome(event_id, "unresolved_user")
        logger.info("stripe webhook %s: could not resolve a user", event_id)
        return 200, {"ok": True, "activated": False, "reason": "unresolved_user"}

    user_id = int(user["id"])
    try:
        from app.plan import activate_plan

        activate_plan(user_id, plan)
    except Exception as exc:  # noqa: BLE001 — activation failed; record and ack
        _record_outcome(event_id, "activation_error")
        logger.error("stripe webhook %s: activate_plan failed: %s", event_id, type(exc).__name__)
        # The event id is already claimed; a redelivery will no-op rather than
        # retry. This is deliberate — a persistent activation error must be fixed
        # by the operator (and re-run via the admin panel / CLI), not hammered by
        # Stripe retries. Return 200 so Stripe does not loop.
        return 200, {"ok": True, "activated": False, "reason": "activation_error"}

    _record_outcome(event_id, "activated")
    # Immutable audit: WHO (the resolved customer) got WHAT plan from WHICH Stripe
    # event. actor_user_id is the customer being entitled; the Stripe event id is
    # the non-repudiable external reference.
    append_access_log(
        actor_user_id=user_id,
        org_id=None,
        action=STRIPE_ACTIVATE,
        result="allow",
        resource_type="plan",
        resource_id=f"user:{user_id}->{plan}@{event_id}",
    )
    logger.info("stripe webhook %s: activated %s for user %s", event_id, plan, user_id)
    return 200, {"ok": True, "activated": True, "plan": plan, "user_id": user_id}
