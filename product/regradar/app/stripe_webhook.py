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
* NO TAKEDOWN — with client-side Payment Links the buyer controls both the typed
  email and the ``client_reference_id``, but NOT which Stripe ``customer`` a
  signed event carries (Stripe sets that from the actual payer). Grants are
  therefore modelled as a SET of ``(user, customer, plan)`` triples: an activation
  only ever RAISES a user's active plan (never lowers it — the rank guard, rule 2)
  and always APPENDS the payer's grant, and a revocation resolves the user ONLY
  through the customer→user ledger (never a buyer-typed email), removes ONLY the
  revoked customer's own grant, and re-derives the tier to the highest-rank
  SURVIVING grant (rule 3). An attacker's cancel/refund can thus only ever remove
  the attacker's OWN grant, so a victim also paying via a DIFFERENT customer keeps
  that surviving grant and is never stripped below what they pay for — in EVERY
  ordering, including a higher attacker gift recorded before the victim pays a
  lower tier.

ENTITLEMENT LIFECYCLE (the grant SET — app.db.stripe_customer_grants):
1. GRANT RECORDING — when an activation entitles a user, the paying Stripe
   customer id (with the plan it paid for) is APPENDED to the user's grant set (a
   user may hold grants from several customers at once). Re-recording the same
   customer refreshes its row. The grant is recorded for EVERY resolved, mapped,
   signed payment — including one blocked by the rank guard (see 2) — so a genuine
   payment always leaves a surviving grant of its own.
2. PLAN (RANK) GUARD — an activation applies the mapped plan ONLY when it does not
   LOWER the user's current active plan (rank of new ≥ rank of current). A gift of
   a cheaper plan therefore cannot downgrade a genuinely-paying victim; the active
   plan is a 200 no-op — BUT the payer's own grant is still recorded, so if that
   payment is genuine it survives to defend the payer on a later revocation.
3. REVOCATION — a genuine revocation event (subscription deleted, full refund,
   dispute, final invoice failure) resolves the affected user(s) from the ledger
   alone, removes ONLY the revoked customer's grant, and RE-DERIVES the user's tier
   to the highest-rank plan among their SURVIVING grants (the FREE tier only when
   none remain). Revocation only ever lowers a plan to what the survivors justify —
   never below a genuinely-paying victim's own grant, in any ordering.

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
from app.db import (
    _connect,
    ensure_stripe_customer_grants_table,
    ensure_stripe_events_table,
)

logger = logging.getLogger(__name__)

# Stripe's default webhook tolerance. A signed timestamp older/newer than this is
# rejected, which — together with the idempotency ledger — bounds replay.
TOLERANCE_SECONDS = 300

# Events that represent a completed payment we entitle on. Both carry the line
# items / price we map to a plan.
_ACTIVATING_EVENT_TYPES = frozenset({"checkout.session.completed", "invoice.paid"})

# Events that represent a lost/withdrawn payment → downgrade to the free tier.
# ``charge.refunded`` only counts on a FULL refund; ``invoice.payment_failed``
# only on the FINAL (no-more-retries) attempt — both gated below.
_REVOKING_EVENT_TYPES = frozenset({
    "customer.subscription.deleted",
    "charge.refunded",
    "charge.dispute.created",
    "invoice.payment_failed",
})

# The free tier a revocation downgrades to (must be a known ``app.plan`` plan).
FREE_PLAN = "evidence_preview"

# Audit action labels recorded in the immutable access log.
STRIPE_ACTIVATE = "stripe.activate_plan"
STRIPE_REVOKE = "stripe.revoke_plan"
# An activation blocked because it would LOWER a user's current active plan (the
# rank guard, rule 2) — recorded so a would-be downgrade attempt is never silent.
STRIPE_ACTIVATE_BLOCKED = "stripe.activate_blocked"

# Plan tiers in ascending order of access. Used ONLY to guard the activation
# plan-change: an activation may raise or keep a user's active plan, but never
# lower it — so an attacker can never "gift" a cheaper plan to strip a paying
# victim down a tier. Unknown names sort as the free floor (0).
_PLAN_RANK = {
    "evidence_preview": 0,
    "starter_pilot": 1,
    "professional": 2,
    "consultant": 3,
}


def _plan_rank(plan: str) -> int:
    """Ascending access rank of ``plan`` (unknown → 0, the free floor)."""
    return _PLAN_RANK.get(str(plan or "").strip(), 0)


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


# ── grant SET ledger (customer → user mapping; the anti-takedown keystone) ────────

def _record_grant(user_id: int, customer_id: str, plan: str) -> None:
    """APPEND ``customer_id`` to ``user_id``'s grant SET (refresh if already there).

    Upserts on the composite ``(user_id, granting_customer_id)`` primary key so a
    user may hold grants from SEVERAL customers at once, and a renewal by the SAME
    customer refreshes its row rather than duplicating it. Recording every distinct
    paying customer separately is what lets a genuinely-paying victim's grant
    survive an attacker's separate grant being revoked. Best-effort — a ledger
    write failure is logged but never turns a successful activation into an error.
    """
    ensure_stripe_customer_grants_table()
    now = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO stripe_customer_grants "
            "(user_id, granting_customer_id, plan, granted_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(user_id, granting_customer_id) DO UPDATE SET "
            "plan = excluded.plan, updated_at = excluded.updated_at",
            (int(user_id), str(customer_id), str(plan), now, now),
        )
        conn.commit()
    except Exception:  # noqa: BLE001 — ledger write is best-effort, never blocks the ack
        logger.warning("stripe webhook: failed to record grant for user %s", user_id)
    finally:
        conn.close()


def _remove_grant(user_id: int, customer_id: str) -> None:
    """Delete the ONE ``(user_id, customer_id)`` grant row (on that customer's revoke).

    Removes only the revoked customer's grant, leaving any other customer's grant
    for the same user intact — so a foreign customer's cancel can never clear a
    victim's genuine grant. Best-effort; a failure is logged, never blocks the ack.
    """
    ensure_stripe_customer_grants_table()
    conn = _connect()
    try:
        conn.execute(
            "DELETE FROM stripe_customer_grants "
            "WHERE user_id = ? AND granting_customer_id = ?",
            (int(user_id), str(customer_id)),
        )
        conn.commit()
    except Exception:  # noqa: BLE001 — best-effort cleanup, never blocks the ack
        logger.warning("stripe webhook: failed to remove grant for user %s", user_id)
    finally:
        conn.close()


def _entitled_plan_from_grants(user_id: int) -> str | None:
    """The plan a user is still entitled to = highest-rank plan among SURVIVING grants.

    Returns ``FREE_PLAN`` when the user has NO remaining grant (a genuine full loss),
    or the highest-ranked plan across every customer that still grants them. A
    revocation re-derives the user's tier from this rather than from a bare count,
    so removing one customer's grant lowers the plan only to what the SURVIVING
    grants still justify — never below a genuinely-paying victim's own tier.

    Returns ``None`` on an unreadable ledger so the caller fails SAFE (never strips
    on a read error) rather than defaulting to the free floor.
    """
    ensure_stripe_customer_grants_table()
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT plan FROM stripe_customer_grants WHERE user_id = ?",
            (int(user_id),),
        ).fetchall()
    except Exception:  # noqa: BLE001 — fail SAFE: never strip on an unreadable ledger
        return None
    finally:
        conn.close()
    if not rows:
        return FREE_PLAN
    best = FREE_PLAN
    for row in rows:
        plan = str(row["plan"] or "")
        if _plan_rank(plan) > _plan_rank(best):
            best = plan
    return best


def _users_for_customer(customer_id: str) -> list[int]:
    """User ids who hold a grant FROM ``customer_id`` (revocation resolution).

    This is the ONLY way a revocation resolves a user — never a buyer-typed email —
    so an attacker's customer resolves to exactly the users that customer actually
    granted (normally zero for a victim paid by a different customer). Never raises.
    """
    cid = str(customer_id or "").strip()
    if not cid:
        return []
    ensure_stripe_customer_grants_table()
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT user_id FROM stripe_customer_grants WHERE granting_customer_id = ?",
            (cid,),
        ).fetchall()
        return [int(r["user_id"]) for r in rows]
    except Exception:  # noqa: BLE001 — a ledger read must never break the ack
        return []
    finally:
        conn.close()


def _current_active_plan(user_id: int) -> str:
    """The user's ACTIVATED plan name (``evidence_preview`` when free). Never raises."""
    try:
        from app.plan import get_plan_state

        return str(get_plan_state(int(user_id)).get("active_plan_name") or FREE_PLAN)
    except Exception:  # noqa: BLE001 — a state read must never break the ack
        return FREE_PLAN


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


def _extract_customer_id(obj: dict) -> str | None:
    """The Stripe customer id (``cus_...``) on an event object, or None.

    Reads the ``customer`` field, tolerating both the bare-id form and an expanded
    ``{"id": ...}`` object. Returns None when absent — a customer-less event can
    neither become a grantor nor resolve a revocation (both fail safe to no-op).
    """
    if not isinstance(obj, dict):
        return None
    cust = obj.get("customer")
    if isinstance(cust, dict):
        cust = cust.get("id")
    cust = str(cust or "").strip()
    return cust or None


def _is_full_refund(obj: dict) -> bool:
    """True only for a FULL charge refund — a partial refund does not revoke.

    A Stripe charge sets ``refunded`` True on a full refund; we additionally accept
    ``amount_refunded >= amount`` (with a positive amount) so an integration that
    fully refunds without flipping the flag is still honoured. A partial refund
    (``amount_refunded < amount``) returns False and never downgrades.
    """
    if not isinstance(obj, dict):
        return False
    try:
        amount = int(obj.get("amount") or 0)
        refunded_amount = int(obj.get("amount_refunded") or 0)
    except (TypeError, ValueError):
        amount = refunded_amount = 0
    if bool(obj.get("refunded")):
        return True
    return amount > 0 and refunded_amount >= amount


def _is_final_invoice_failure(obj: dict) -> bool:
    """True only when an ``invoice.payment_failed`` has NO further retry scheduled.

    Stripe sets ``next_payment_attempt`` to the unix time of the next automatic
    retry, or null once it will retry no more (the terminal dunning failure). We
    downgrade only on that terminal failure; an interim failure (a retry is still
    pending) is a no-op so a customer mid-dunning is never prematurely stripped.
    """
    if not isinstance(obj, dict):
        return False
    return obj.get("next_payment_attempt") is None


def _should_revoke(event_type: str, obj: dict) -> bool:
    """Whether a revocation-class event actually represents a terminal loss."""
    if event_type == "charge.refunded":
        return _is_full_refund(obj)
    if event_type == "invoice.payment_failed":
        return _is_final_invoice_failure(obj)
    # subscription deleted / dispute opened are terminal on arrival.
    return True


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
    * verified activating event, mapped price + resolved user, ACTIVATION GUARD
      satisfied → activate_plan, record grantor, audit, (200, activated).
    * verified revocation event, resolved via the grantor ledger, event customer ==
      current grantor → downgrade to the free tier, audit, (200, revoked).
    * verified but unknown price / unresolvable user / protected grant / non-final /
      non-mapped type → (200, ack) with NO change (never make Stripe retry a benign
      event, and never let a foreign customer strip a paying user).
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

    data = event.get("data", {})
    obj = data.get("object") if isinstance(data, dict) else None

    if event_type in _ACTIVATING_EVENT_TYPES:
        # Idempotency: claim the id BEFORE any activation. A redelivery/replay loses
        # the claim and no-ops.
        if not _claim_event(event_id, event_type):
            return 200, {"ok": True, "duplicate": True}
        if not isinstance(obj, dict):
            _record_outcome(event_id, "no_object")
            return 200, {"ok": True, "activated": False, "reason": "no_object"}
        return _process_activation(event_id, obj)

    if event_type in _REVOKING_EVENT_TYPES:
        if not isinstance(obj, dict):
            return 200, {"ok": True, "revoked": False, "reason": "no_object"}
        return _process_revocation(event_id, event_type, obj)

    # Any other event type is acknowledged and ignored (no ledger entry — we only
    # spend an idempotency slot on events we would act on).
    return 200, {"ok": True, "ignored": event_type or "unknown"}


def _process_activation(event_id: str, obj: dict) -> tuple[int, dict[str, Any]]:
    """Entitle the resolved user for a mapped price — subject to the RANK GUARD.

    The event id is already claimed by the caller. Returns a 200 body describing the
    outcome; NEVER raises. The RANK GUARD (rule 2) is the anti-strip core: an
    activation may RAISE or keep the user's active plan and APPEND a grant, but it
    can never LOWER the plan — so an attacker can never "gift" a cheaper plan to
    strip a genuinely-paying victim down a tier. A would-be downgrade is a logged
    no-op that changes neither the plan nor the grant set.
    """
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
    event_customer = _extract_customer_id(obj)

    # ── RANK GUARD (rule 2) ──────────────────────────────────────────────────────
    # An activation may apply its plan ONLY when doing so does not LOWER the user's
    # current active plan (rank of new ≥ rank of current). A gift of a CHEAPER plan
    # to a higher-paid user therefore never LOWERS the plan. But it STILL records the
    # paying customer's own grant (rule 1) — this is the anti-strip keystone: if the
    # payment is genuine (e.g. the victim subscribing to a lower tier while a prior
    # gift put them on a higher one), that grant MUST survive so a later revocation
    # of the higher grant re-derives the victim's tier DOWN only to what their own
    # surviving grant justifies — never below it. Skipping the grant here is exactly
    # what let an attacker strip a paying lower-tier victim (round-1 blocker), so the
    # grant is recorded even though the active plan is left unchanged.
    current_plan = _current_active_plan(user_id)
    if _plan_rank(plan) < _plan_rank(current_plan):
        if event_customer:
            _record_grant(user_id, event_customer, plan)
        _record_outcome(event_id, "protected_downgrade")
        append_access_log(
            actor_user_id=user_id,
            org_id=None,
            action=STRIPE_ACTIVATE_BLOCKED,
            result="deny",
            resource_type="plan",
            resource_id=f"user:{user_id}<-{event_customer or '?'}@{event_id}",
        )
        logger.warning(
            "stripe webhook %s: activation blocked — %s would lower user %s from "
            "%s; active plan unchanged (grant recorded so a genuine payment survives)",
            event_id, plan, user_id, current_plan,
        )
        return 200, {"ok": True, "activated": False, "reason": "protected_downgrade"}

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

    # Append this customer to the user's grant SET (rule 1) so a later revocation
    # can resolve THIS user only via THIS customer, and removing THIS customer's
    # grant leaves any OTHER customer's grant for the same user intact. A
    # customer-less activation still entitles the user but records no grant (it can
    # therefore never be auto-revoked — fail-safe).
    if event_customer:
        _record_grant(user_id, event_customer, plan)

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


def _process_revocation(
    event_id: str, event_type: str, obj: dict
) -> tuple[int, dict[str, Any]]:
    """Downgrade to the free tier on a genuine loss — resolved via the grantor ledger.

    Rule 3: resolve the affected user(s) ONLY from the customer→user ledger (never
    a buyer-typed email), remove ONLY the revoked customer's grant, and downgrade
    to free solely when the user has ZERO remaining granting customers. An
    attacker's cancel/refund therefore removes only the attacker's OWN grant — a
    victim also paying via a DIFFERENT customer keeps that surviving grant and is
    never stripped, even if the attacker's grant was recorded first. NEVER raises.
    """
    if not _should_revoke(event_type, obj):
        # Partial refund / non-final invoice failure → not a terminal loss.
        return 200, {"ok": True, "revoked": False, "reason": "not_final"}

    customer_id = _extract_customer_id(obj)
    if not customer_id:
        return 200, {"ok": True, "revoked": False, "reason": "no_customer"}

    # Idempotency: claim the id BEFORE any downgrade so a redelivery/replay no-ops.
    if not _claim_event(event_id, event_type):
        return 200, {"ok": True, "duplicate": True}

    user_ids = _users_for_customer(customer_id)
    if not user_ids:
        # This customer granted nobody a current plan → nothing to revoke. An
        # attacker's customer that never recorded a grant lands here (no-op).
        _record_outcome(event_id, "no_grant")
        logger.info(
            "stripe webhook %s: %s for customer with no current grant — no-op",
            event_id, event_type,
        )
        return 200, {"ok": True, "revoked": False, "reason": "no_grant"}

    revoked: list[int] = []
    survivors: list[int] = []
    for user_id in user_ids:
        # Remove ONLY this customer's grant, then RE-DERIVE the user's tier from the
        # SURVIVING grants (highest rank among them, or the free tier when none
        # remain). This is the branch that defeats the takedown in EVERY ordering:
        # an attacker's cancel drops the attacker's grant, but the victim's own
        # separate grant survives, so the re-derived plan can never fall below what
        # the victim genuinely pays for — even if the attacker's (higher) gift was
        # recorded first and the victim later paid a LOWER tier.
        _remove_grant(user_id, customer_id)
        target_plan = _entitled_plan_from_grants(user_id)
        if target_plan is None:
            # Unreadable ledger → fail SAFE: never strip on a read error.
            survivors.append(user_id)
            logger.warning(
                "stripe webhook %s: grant ledger unreadable for user %s — no "
                "downgrade (fail-safe)",
                event_id, user_id,
            )
            continue
        current_plan = _current_active_plan(user_id)
        if _plan_rank(target_plan) >= _plan_rank(current_plan):
            # A surviving grant still justifies at least the current tier (or the
            # removed grant was never the one setting it) → no downgrade. Revocation
            # only ever LOWERS a plan; it must never raise one.
            survivors.append(user_id)
            logger.info(
                "stripe webhook %s: removed %s's grant for user %s but surviving "
                "grants still justify %s — no downgrade",
                event_id, customer_id, user_id, current_plan,
            )
            continue
        try:
            from app.plan import activate_plan

            activate_plan(user_id, target_plan)
        except Exception as exc:  # noqa: BLE001 — downgrade failed for this user; ack
            logger.error(
                "stripe webhook %s: downgrade of user %s failed: %s",
                event_id, user_id, type(exc).__name__,
            )
            continue
        append_access_log(
            actor_user_id=user_id,
            org_id=None,
            action=STRIPE_REVOKE,
            result="allow",
            resource_type="plan",
            resource_id=f"user:{user_id}->{target_plan}@{event_id}",
        )
        revoked.append(user_id)
        logger.info(
            "stripe webhook %s: revoked user %s from %s to %s (%s)",
            event_id, user_id, current_plan, target_plan, event_type,
        )

    if revoked:
        outcome = "revoked"
    elif survivors:
        # Grant(s) removed, but every affected user still has a surviving grantor.
        outcome = "still_granted"
    else:
        outcome = "revoke_error"
    _record_outcome(event_id, outcome)
    return 200, {
        "ok": True,
        "revoked": bool(revoked),
        "user_ids": revoked,
        "reason": None if revoked else outcome,
    }
