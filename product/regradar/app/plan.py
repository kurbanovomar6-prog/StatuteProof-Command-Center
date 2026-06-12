"""Plan and trial state management — no Stripe, no payment processing."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.db import _connect

TRIAL_DAYS = 7

PLAN_NAMES = {
    "evidence_preview",
    "starter_pilot",
    "professional",
    "consultant",
}

PLAN_DISPLAY = {
    "evidence_preview": "Evidence Preview",
    "starter_pilot": "Starter Pilot",
    "professional": "Professional",
    "consultant": "Compliance Consultant",
}

PLAN_CAPABILITIES = {
    "evidence_preview": {
        "live_monitoring": False,
        "source_limit": 0,
        "custom_sources": 0,
        "weekly_briefs": False,
        "audit_export": False,
        "pdf_export": False,
        "users": 1,
        "retention_days": 0,
        "multiple_workspaces": False,
        "white_label": False,
    },
    "starter_pilot": {
        "live_monitoring": True,
        "source_limit": 3,
        "custom_sources": 0,
        "weekly_briefs": "limited",
        "audit_export": False,
        "pdf_export": False,
        "users": 1,
        "retention_days": 30,
        "multiple_workspaces": False,
        "white_label": False,
    },
    "professional": {
        "live_monitoring": True,
        "source_limit": 16,
        "custom_sources": 3,
        "weekly_briefs": True,
        "audit_export": True,
        "pdf_export": True,
        "users": 3,
        "retention_days": 365,
        "multiple_workspaces": False,
        "white_label": False,
    },
    "consultant": {
        "live_monitoring": True,
        "source_limit": 999,
        "custom_sources": 999,
        "weekly_briefs": True,
        "audit_export": True,
        "pdf_export": True,
        "users": 999,
        "retention_days": 999,
        "multiple_workspaces": True,
        "white_label": True,
    },
}


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
        row = conn.execute(
            "SELECT plan_name, trial_started_at, plan_intent_at FROM users WHERE id = ? LIMIT 1",
            (user_id,),
        ).fetchone()
        if row is None:
            return _build_state("evidence_preview", None, None)
        return _build_state(row["plan_name"], row["trial_started_at"], row["plan_intent_at"])
    finally:
        conn.close()


def _build_state(plan_name: str, trial_started_at_raw, plan_intent_at_raw) -> dict[str, Any]:
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

    return {
        "plan_name": plan,
        "plan_display": PLAN_DISPLAY.get(plan, plan),
        "trial_active": trial_active,
        "trial_expired": trial_expired,
        "days_remaining": days_remaining,
        "trial_started_at": trial_started_at_raw,
        "status": _resolve_status(plan, trial_active, trial_expired),
        "capabilities": caps,
    }


def _resolve_status(plan: str, trial_active: bool, trial_expired: bool) -> str:
    if plan == "evidence_preview":
        if trial_expired:
            return "trial_expired"
        if trial_active:
            return "trial_active"
        return "evidence_preview"
    return "active"


def set_plan_intent(user_id: int, plan_name: str) -> dict[str, Any]:
    """Record the user's plan selection intent (no payment processed)."""
    if plan_name not in PLAN_NAMES:
        raise ValueError(f"Unknown plan: {plan_name}")
    now_str = _iso(_now())
    conn = _connect()
    try:
        conn.execute(
            "UPDATE users SET plan_name = ?, plan_intent_at = ? WHERE id = ?",
            (plan_name, now_str, user_id),
        )
        conn.commit()
    finally:
        conn.close()
    return get_plan_state(user_id)
