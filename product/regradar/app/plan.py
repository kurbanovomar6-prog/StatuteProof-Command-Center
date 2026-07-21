"""Plan and trial state management.

Payment *processing* lives in ``app.stripe_webhook``; this module only decides
capabilities from the founder-activated plan. One cross-cutting exception: a
MANUAL/admin activation ALSO records a server-side SENTINEL grant in the Stripe
grant ledger (``customer_id='manual'``) so that a comped/manual tier acts as a
FLOOR the Stripe revocation/downgrade re-derivation can never strip (see
``activate_plan`` and ``app.stripe_webhook``).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.db import _connect

logger = logging.getLogger(__name__)

TRIAL_DAYS = 7

PLAN_NAMES = {
    "evidence_preview",
    "starter_pilot",
    "professional",
    "consultant",
}

PLAN_DISPLAY = {
    "evidence_preview": "Source Readiness Review",
    "starter_pilot": "Founding Pilot",
    "professional": "UAE Monitor",
    "consultant": "Compliance Consultant",
}

PLAN_PRICE_MONTHLY = {
    "evidence_preview": 0,
    "starter_pilot": 199,
    "professional": 399,
    "consultant": 0,  # custom / Talk to us
}

PLAN_CAPABILITIES = {
    "evidence_preview": {
        "live_monitoring": False,
        "manual_activation_required": False,
        "source_limit": 0,
        "custom_sources": 0,
        "official_alerts": False,   # official-source Telegram broadcast is a paid deliverable
        "weekly_briefs": False,
        "audit_export": False,
        "pdf_export": False,
        "users": 1,
        "retention_days": 0,
        "multiple_workspaces": False,
        "white_label": False,
    },
    "starter_pilot": {
        "live_monitoring": False,
        "manual_activation_required": True,
        "source_limit": 3,          # 3 official UAE sources, manually curated
        "custom_sources": 0,
        "official_alerts": True,    # receives the official-source Telegram broadcast
        "weekly_briefs": "status_only",  # source status summary only
        "audit_export": False,
        "pdf_export": False,
        "users": 1,
        "retention_days": 30,
        "multiple_workspaces": False,
        "white_label": False,
        "high_risk_queue": False,
    },
    "professional": {
        "live_monitoring": False,
        "manual_activation_required": True,
        "source_limit": 172,        # selected fresh-alert eligible UAE sources after readiness gates
        "custom_sources": 2,        # requires activation
        "official_alerts": True,    # receives the official-source Telegram broadcast
        "weekly_briefs": True,      # Telegram; email requires activation
        "audit_export": True,
        "pdf_export": True,         # PDF audit pack for internal compliance files
        "users": 2,
        "retention_days": 180,
        "multiple_workspaces": False,
        "white_label": False,
        "high_risk_queue": True,
    },
    "consultant": {
        "live_monitoring": False,
        "manual_activation_required": True,
        "source_limit": 999,
        "custom_sources": 999,
        "official_alerts": True,    # receives the official-source Telegram broadcast
        "weekly_briefs": True,
        "audit_export": True,
        "pdf_export": True,         # PDF audit pack for internal compliance files
        "users": 999,
        "retention_days": 999,
        "multiple_workspaces": False,  # pilot roadmap
        "white_label": False,          # pilot roadmap
        "high_risk_queue": True,
    },
}


def capabilities_for(user_id: int) -> dict[str, Any]:
    """Return the capability dict for the user's ACTIVATED plan.

    This is the single source of truth for authorization decisions on paid
    export paths. It deliberately reads ``active_capabilities`` (the capabilities
    of the plan a founder has actually *activated*), NOT ``capabilities`` (the
    plan the user merely self-selected). A user who POSTs ``plan_name=consultant``
    without a founder activation therefore keeps ``evidence_preview`` (free-tier)
    capabilities — self-selecting a paid plan grants nothing on its own.

    A default (free ``evidence_preview``) account has every paid capability set
    to ``False`` and ``source_limit`` 0, so it cannot pull paid exports for any
    source. Never raises — falls back to the free-tier caps.
    """
    try:
        caps = get_plan_state(int(user_id)).get("active_capabilities")
    except Exception:  # noqa: BLE001 — an auth gate must never crash the request
        caps = None
    return caps if isinstance(caps, dict) else PLAN_CAPABILITIES["evidence_preview"]


def has_capability(user_id: int, capability: str) -> bool:
    """True when the user's selected plan grants ``capability`` (truthy value)."""
    return bool(capabilities_for(user_id).get(capability))


def source_limit_for(user_id: int) -> int:
    """Max number of sources the user's plan entitles per export (0 = none)."""
    try:
        return int(capabilities_for(user_id).get("source_limit") or 0)
    except (TypeError, ValueError):
        return 0


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        return None


def get_plan_state(user_id: int) -> dict[str, Any]:
    """Return plan state dict for the given user."""
    conn = _connect()
    try:
        activated_plan = None
        # ``activated_plan`` is added by a DB migration (app.db.ensure_auth_tables).
        # Tolerate a pre-migration schema so a plan lookup never crashes an
        # auth gate: absent column → no activation → free-tier capabilities.
        cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
        select_cols = "plan_name, trial_started_at, plan_intent_at"
        if "activated_plan" in cols:
            select_cols += ", activated_plan"
        row = conn.execute(
            f"SELECT {select_cols} FROM users WHERE id = ? LIMIT 1",
            (user_id,),
        ).fetchone()
        if row is None:
            return _build_state("evidence_preview", None, None)
        if "activated_plan" in cols:
            activated_plan = row["activated_plan"]
        return _build_state(
            row["plan_name"],
            row["trial_started_at"],
            row["plan_intent_at"],
            activated_plan,
        )
    finally:
        conn.close()


def _build_state(
    plan_name: str,
    trial_started_at_raw,
    plan_intent_at_raw,
    activated_plan_raw=None,
) -> dict[str, Any]:
    plan = plan_name if plan_name in PLAN_NAMES else "evidence_preview"
    now = _now()

    trial_started = _parse_iso(trial_started_at_raw)
    days_remaining: int | None = None
    trial_active = False
    trial_expired = False

    if plan == "evidence_preview" and trial_started:
        expires_at = trial_started + timedelta(days=TRIAL_DAYS)
        remaining = (expires_at - now).days
        days_remaining = max(0, remaining)
        trial_active = remaining > 0
        trial_expired = remaining <= 0

    caps = PLAN_CAPABILITIES.get(plan, PLAN_CAPABILITIES["evidence_preview"])

    # The ACTIVE plan (which capabilities actually apply) is decided solely by a
    # founder-set activation, never by the user's self-selected ``plan_name``.
    # An un-activated account stays on ``evidence_preview`` capabilities even
    # after POSTing a paid ``plan_name`` — this is what closes the "self-select
    # consultant → free audit export" bypass.
    activated_plan = str(activated_plan_raw or "").strip()
    active_plan = activated_plan if activated_plan in PLAN_NAMES else "evidence_preview"
    active_caps = PLAN_CAPABILITIES.get(active_plan, PLAN_CAPABILITIES["evidence_preview"])

    # "Pending manual activation" = the user asked for a plan that requires a
    # founder to switch it on, and it has not yet been activated to that plan.
    pending_manual_activation = bool(caps.get("manual_activation_required")) and active_plan != plan

    return {
        "plan_name": plan,
        "plan_display": PLAN_DISPLAY.get(plan, plan),
        "active_plan_name": active_plan,
        "active_plan_display": PLAN_DISPLAY.get(active_plan, active_plan),
        "requested_plan": plan if pending_manual_activation else None,
        "requested_plan_display": PLAN_DISPLAY.get(plan, plan) if pending_manual_activation else None,
        "trial_active": trial_active,
        "trial_expired": trial_expired,
        "days_remaining": days_remaining,
        "trial_started_at": trial_started_at_raw,
        "status": _resolve_status(
            plan, trial_active, trial_expired, pending_manual_activation, active_plan
        ),
        "manual_activation_required": bool(caps.get("manual_activation_required")),
        "active_capabilities": active_caps,
        "requested_capabilities": caps if pending_manual_activation else None,
        "capabilities": caps,
    }


def _resolve_status(
    plan: str,
    trial_active: bool,
    trial_expired: bool,
    pending_manual_activation: bool = False,
    active_plan: str = "evidence_preview",
) -> str:
    if plan == "evidence_preview":
        if trial_expired:
            return "trial_expired"
        if trial_active:
            return "trial_active"
        return "evidence_preview"
    if pending_manual_activation:
        return "pending_manual_activation"
    # A paid plan that a founder has activated (active_plan == requested plan).
    return "active"


def set_plan_intent(user_id: int, plan_name: str) -> dict[str, Any]:
    """Record the user's plan selection intent (no payment processed).

    This only records what the user *wants* — it never grants capabilities.
    Entitlements follow the ACTIVATED plan (see ``activate_plan`` /
    ``capabilities_for``), which only a founder can set.

    The returned state carries one extra key, ``intent_changed`` (bool): True
    when ``plan_name`` differs from the previously stored intent. Callers that
    page a human on plan intent (POST /api/plan) use it to dedupe — re-posting
    the SAME plan must not re-notify (2026-07-20 review). It is metadata, not
    plan state: the API handler pops it before responding.
    """
    if plan_name not in PLAN_NAMES:
        raise ValueError(f"Unknown plan: {plan_name}")
    now_str = _iso(_now())
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT plan_name FROM users WHERE id = ? LIMIT 1", (user_id,)
        ).fetchone()
        previous_plan = str(row["plan_name"] or "") if row is not None else ""
        conn.execute(
            "UPDATE users SET plan_name = ?, plan_intent_at = ? WHERE id = ?",
            (plan_name, now_str, user_id),
        )
        conn.commit()
    finally:
        conn.close()
    state = get_plan_state(user_id)
    state["intent_changed"] = plan_name != previous_plan
    return state


def _record_manual_floor_grant(user_id: int, plan_name: str) -> None:
    """Record a server-only SENTINEL grant so a manual activation acts as a FLOOR.

    A manual/admin activation sets the ``activated_plan`` column but, historically,
    wrote NO row to the Stripe grant ledger. When a Stripe lifecycle event later
    re-derived a user's tier from the *surviving grants* (revocation / downgrade),
    the manual activation was invisible to that ledger and the user silently fell
    to the free tier — stripping a comped/manual consultant on a normal Stripe
    cancel or downgrade of an unrelated (or lower) grant.

    Recording a sentinel grant keyed to ``customer_id='manual'`` fixes this: the
    re-derivation takes the MAX over surviving grants, so the manual tier floors
    the result. The sentinel is UNFORGEABLE and UN-STRIPPABLE by any Stripe event:
    it is written only here (a founder-only, server-side path — never a buyer HTTP
    request), and every genuine Stripe revocation/downgrade carries a real
    ``cus_...`` customer id and removes/updates ONLY that customer's own grant,
    never the literal ``'manual'`` sentinel. Best-effort — a ledger write failure
    is logged but never turns a successful activation into an error.
    """
    try:
        from app.stripe_webhook import MANUAL_GRANT_CUSTOMER_ID, _record_grant

        _record_grant(int(user_id), MANUAL_GRANT_CUSTOMER_ID, plan_name)
    except Exception:  # noqa: BLE001 — the floor is a safeguard, never a hard dep
        logger.warning(
            "activate_plan: failed to record manual floor grant for user %s", user_id
        )


def activate_plan(
    user_id: int, plan_name: str, *, record_manual_grant: bool = True
) -> dict[str, Any]:
    """Activate ``plan_name`` for a user — the ONLY path that grants paid caps.

    This is deliberately founder-only: it is invoked from the ``activate-plan``
    CLI subcommand (which requires shell/SSH access to the production host) and the
    admin panel, and there is no self-service HTTP endpoint that reaches it. Setting
    the ``activated_plan`` column is what makes ``capabilities_for`` return the paid
    plan's capabilities; until then a user who self-selected a paid plan keeps
    ``evidence_preview`` (free-tier) capabilities.

    ``record_manual_grant`` (default True) records a server-side SENTINEL grant so a
    manual/admin activation acts as a FLOOR in the Stripe grant ledger that a later
    Stripe revocation/downgrade of a DIFFERENT customer can never strip (see
    :func:`_record_manual_floor_grant`). The Stripe webhook — which already records
    the *real* paying customer's grant and re-derives tiers from that ledger — is
    the ONE caller that passes ``record_manual_grant=False`` so it never double-
    records a bogus ``'manual'`` sentinel over its genuine customer grants.

    Passing ``evidence_preview`` (or a to-be-added future value) effectively
    de-activates paid access. Raises ``ValueError`` on an unknown plan or a
    non-existent user id so a founder gets a clear failure instead of a silent
    no-op.
    """
    if plan_name not in PLAN_NAMES:
        raise ValueError(f"Unknown plan: {plan_name}")
    now_str = _iso(_now())
    conn = _connect()
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
        if "activated_plan" not in cols:
            raise ValueError(
                "users.activated_plan column is missing — run the DB migration "
                "(app.db.ensure_auth_tables) before activating a plan."
            )
        set_activated_at = ", plan_activated_at = ?" if "plan_activated_at" in cols else ""
        params: tuple[Any, ...] = (
            (plan_name, now_str, user_id) if set_activated_at else (plan_name, user_id)
        )
        cur = conn.execute(
            f"UPDATE users SET activated_plan = ?{set_activated_at} WHERE id = ?",
            params,
        )
        if cur.rowcount == 0:
            raise ValueError(f"No user with id {user_id}.")
        conn.commit()
    finally:
        conn.close()
    # Only after the activation is durably committed (and the user proven to exist)
    # do we floor the grant ledger, so a manual tier survives Stripe re-derivation.
    if record_manual_grant:
        _record_manual_floor_grant(user_id, plan_name)
    return get_plan_state(user_id)


def list_accounts_admin(limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    """Read-only account roster for the founder admin panel. NO secrets, ever.

    Returns bounded, non-sensitive fields only — id, email, email_verified,
    plan_name (self-selected intent), activated_plan (the founder-activated tier,
    the entitlement source of truth), plan_intent_at, telegram_linked (a BOOLEAN,
    never the chat id itself), and created_at. It deliberately never selects
    ``password_hash``, session ids, or any token / raw chat-id value: an admin
    listing must never widen the blast radius of a read.

    Tolerant of a pre-migration schema (absent ``activated_plan`` / ``user_profiles``).
    Bounded by ``limit`` (1..500) and ``offset``; sorted newest-first by id. This
    is a pure read — it never activates, mutates, or changes activation semantics.
    """
    try:
        capped = max(1, min(int(limit), 500))
    except (TypeError, ValueError):
        capped = 100
    try:
        off = max(0, int(offset))
    except (TypeError, ValueError):
        off = 0

    conn = _connect()
    try:
        ucols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
        has_activated = "activated_plan" in ucols
        has_intent_at = "plan_intent_at" in ucols
        has_verified = "email_verified" in ucols
        has_created = "created_at" in ucols
        # The Telegram link lives on user_profiles.telegram_chat_id; expose only a
        # boolean, and only when that table/column exist on this schema.
        up_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='user_profiles'"
        ).fetchone() is not None
        has_tg = up_exists and "telegram_chat_id" in {
            r[1] for r in conn.execute("PRAGMA table_info(user_profiles)")
        }

        cols = ["u.id AS id", "u.email AS email", "u.plan_name AS plan_name"]
        cols.append("u.activated_plan AS activated_plan" if has_activated else "'' AS activated_plan")
        cols.append("u.plan_intent_at AS plan_intent_at" if has_intent_at else "NULL AS plan_intent_at")
        cols.append("u.email_verified AS email_verified" if has_verified else "0 AS email_verified")
        cols.append("u.created_at AS created_at" if has_created else "NULL AS created_at")
        if has_tg:
            cols.append(
                "(SELECT CASE WHEN p.telegram_chat_id IS NOT NULL AND p.telegram_chat_id != '' "
                "THEN 1 ELSE 0 END FROM user_profiles p WHERE p.user_id = u.id LIMIT 1) AS tg_linked"
            )
        else:
            cols.append("0 AS tg_linked")

        rows = conn.execute(
            f"SELECT {', '.join(cols)} FROM users u ORDER BY u.id DESC LIMIT ? OFFSET ?",
            (capped, off),
        ).fetchall()
    finally:
        conn.close()

    out: list[dict[str, Any]] = []
    for row in rows:
        intent = row["plan_name"] if row["plan_name"] in PLAN_NAMES else "evidence_preview"
        activated_raw = str((row["activated_plan"] or "")).strip()
        active_plan = activated_raw if activated_raw in PLAN_NAMES else "evidence_preview"
        intent_is_paid = bool(PLAN_CAPABILITIES.get(intent, {}).get("manual_activation_required"))
        out.append({
            "id": int(row["id"]),
            "email": row["email"],
            "email_verified": bool(row["email_verified"]),
            "plan_name": intent,
            "plan_display": PLAN_DISPLAY.get(intent, intent),
            "activated_plan": active_plan,
            "active_plan_display": PLAN_DISPLAY.get(active_plan, active_plan),
            "plan_intent_at": row["plan_intent_at"],
            "telegram_linked": bool(row["tg_linked"]),
            "created_at": row["created_at"],
            "needs_activation": intent_is_paid and active_plan != intent,
        })
    return out


def list_user_plans() -> list[dict[str, Any]]:
    """Return every user's plan intent vs. activated plan, for the operator CLI.

    This exists so ``run.py activate-plan --list`` can show, after a deploy, who
    self-selected a paid plan (``plan_name`` = intent) but is NOT yet activated
    (``activated_plan`` unset), and therefore silently dropped to free-tier caps
    by the activation gate. ``needs_activation`` is True when the user asked for a
    paid plan that a founder has not yet switched on — those are the accounts the
    operator must re-run ``activate-plan --user <id> --plan <name>`` for.

    Read-only; tolerant of a pre-migration schema (absent ``activated_plan``).
    Sorted by user id. Never raises for a missing column.
    """
    conn = _connect()
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
        has_activated = "activated_plan" in cols
        select_cols = "id, email, plan_name"
        if has_activated:
            select_cols += ", activated_plan"
        rows = conn.execute(
            f"SELECT {select_cols} FROM users ORDER BY id ASC"
        ).fetchall()
    finally:
        conn.close()

    out: list[dict[str, Any]] = []
    for row in rows:
        intent = row["plan_name"] if row["plan_name"] in PLAN_NAMES else "evidence_preview"
        activated_raw = str((row["activated_plan"] if has_activated else "") or "").strip()
        active_plan = activated_raw if activated_raw in PLAN_NAMES else "evidence_preview"
        intent_is_paid = bool(PLAN_CAPABILITIES.get(intent, {}).get("manual_activation_required"))
        needs_activation = intent_is_paid and active_plan != intent
        out.append({
            "id": int(row["id"]),
            "email": row["email"],
            "plan_name": intent,
            "plan_display": PLAN_DISPLAY.get(intent, intent),
            "activated_plan": active_plan,
            "active_plan_name": active_plan,
            "needs_activation": needs_activation,
        })
    return out
