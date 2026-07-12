"""Self-service account data export — exit portability (vendor-DD FAQ Q25).

WHAT THIS IS: one bounded, owner-scoped gather of everything a signed-in user
OWNS, assembled into a single JSON document the dashboard streams as a file
download (``GET /api/account/export``). It closes the honest gap the vendor-DD
FAQ used to admit: account records (profile, checklists) previously had no
dedicated export endpoint.

TENANCY (the ONE invariant): every read is keyed by the caller's ``user_id``
(account row, workspace profile, checklist items, Telegram link) or by the
caller's RESOLVED org id (sealed decision records) — never by request input.
No cross-tenant field is read anywhere; another user's data is structurally
unreachable from this module.

SECRETS: the account section is an EXPLICIT column list (``_ACCOUNT_COLUMNS``)
— ``password_hash``, session ids, pairing codes, and verification tokens are
structurally absent because no query here selects them (asserted by
tests/test_account_export.py). ``telegram_chat_id`` IS included deliberately:
the linked chat id is the user's own data and belongs in their export.

PORTABILITY: sealed decision records travel VERBATIM — each is a self-contained
``{content, record_hash, record_hash_method}`` envelope sealed with standard
SHA-256 over compact sorted-key JSON, so it stays independently verifiable
(public verifier or plain scripting) without a StatuteProof account, forever.
The org chain head travels too, so the export carries the chain tip it was cut
at.

RESILIENCE: every section is fail-soft — a broken sub-read logs a warning and
yields that section's empty shape instead of failing the whole export. The
assembled envelope is always returned.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.action_checklist import list_all_checklist_items
from app.db import _connect
from app.decision_records import read_decision_head, read_org_decision_chain
from app.legal_safety import assert_no_forbidden_claims
from app.materiality import SHORT_DISCLAIMER
from app.profile import get_or_create_profile
from app.telegram_pairing import get_telegram_link

logger = logging.getLogger(__name__)

SCHEMA = "statuteproof-account-export-v1"

# Explicit, enumerated account columns. NEVER widen this to SELECT * — the
# users table also holds password_hash, and sessions/verification tokens hang
# off it. Adding a column here is a deliberate, reviewed act.
_ACCOUNT_COLUMNS = (
    "email",
    "full_name",
    "company_name",
    "industry",
    "job_title",
    "company_type",
    "jurisdiction",
    "auth_provider",
    "email_verified",
    "plan_name",
    "activated_plan",
    "created_at",
    "updated_at",
)

# ── app-authored framing — the ONLY StatuteProof words in this feature ───────────
# Guarded AT IMPORT (below) so a wording drift into a forbidden claim breaks the
# build, not a customer. The disclaimer reuses SHORT_DISCLAIMER verbatim.
FRAMING: dict[str, str] = {
    "title": "Your StatuteProof account data export",
    "contents": (
        "This file contains the data your account owns: account profile, "
        "workspace monitoring profile, notification preferences, your review "
        "checklist items, your organisation's sealed decision records, and "
        "your Telegram delivery link."
    ),
    "portability": (
        "Sealed decision records in this file are self-contained envelopes: "
        "each carries its own SHA-256 record hash and hash method, so it can "
        "be checked with the public verifier or standard tools, without a "
        "StatuteProof account."
    ),
    "disclaimer": SHORT_DISCLAIMER,
}


def _guard_framing_at_import() -> None:
    """Fail the IMPORT if any app-authored string drifts into a forbidden claim."""
    for key, value in FRAMING.items():
        assert_no_forbidden_claims(value, label=f"account export framing[{key}]")


_guard_framing_at_import()


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── sections (each fail-soft; each keyed ONLY by the caller's own identity) ──────

def _account_section(user_id: int, session_user: dict[str, Any]) -> dict[str, Any]:
    """The caller's own account row, projected through the explicit column list.

    Falls back to the (equally explicit) session projection when the DB read
    fails, so the export never silently drops the account section.
    """
    try:
        conn = _connect()
        try:
            row = conn.execute(
                f"SELECT {', '.join(_ACCOUNT_COLUMNS)} FROM users WHERE id = ? LIMIT 1",
                (int(user_id),),
            ).fetchone()
        finally:
            conn.close()
        if row is not None:
            data = {col: row[col] for col in _ACCOUNT_COLUMNS}
            data["email_verified"] = bool(data.get("email_verified"))
            return data
    except Exception as exc:  # noqa: BLE001 — fall back, never fail the export
        logger.warning("account export: account read failed: %s", type(exc).__name__)
    return {
        "email": session_user.get("email"),
        "full_name": session_user.get("full_name"),
        "company_name": session_user.get("company_name"),
        "industry": session_user.get("industry"),
        "auth_provider": session_user.get("auth_provider"),
        "email_verified": bool(session_user.get("email_verified")),
        "created_at": session_user.get("created_at"),
        "updated_at": session_user.get("updated_at"),
    }


def _profile_sections(user_id: int) -> tuple[dict[str, Any], dict[str, Any]]:
    """``(workspace_profile, notification_preferences)`` — explicit projections
    over the already-sanitized ``get_or_create_profile`` dict (no raw row leaks).
    """
    try:
        profile = get_or_create_profile(int(user_id))
    except Exception as exc:  # noqa: BLE001
        logger.warning("account export: profile read failed: %s", type(exc).__name__)
        return {}, {}
    workspace = {
        "company_name": profile.get("company_name"),
        "industries": profile.get("industries", []),
        "markets": profile.get("markets", []),
        "topics": profile.get("topics", []),
        "licence_type": profile.get("licence_type"),
        "custom_sources": profile.get("custom_sources", []),
        "regulators": profile.get("regulators", []),
        "onboarding_completed": bool(profile.get("onboarding_completed")),
        "created_at": profile.get("created_at"),
        "updated_at": profile.get("updated_at"),
    }
    notifications = {
        "alert_threshold": profile.get("alert_threshold"),
        "urgent_threshold": profile.get("urgent_threshold"),
        "weekly_threshold": profile.get("weekly_threshold"),
        "digest_cadence": profile.get("digest_cadence"),
        "brief_language": profile.get("brief_language"),
        "weekly_brief_enabled": bool(profile.get("weekly_brief_enabled")),
        "ai_enabled": bool(profile.get("ai_enabled")),
        "telegram_alerts_enabled": bool(profile.get("telegram_alerts_enabled")),
        "email_alerts_enabled": bool(profile.get("email_alerts_enabled")),
    }
    return workspace, notifications


def _decisions_section(org_id: int | None) -> dict[str, Any]:
    """The caller's ORG chain, verbatim envelopes + the chain head it was cut at.

    ``org_id`` comes from the caller's resolved principal (never request
    input); ``None`` (no resolvable org) is an honest empty section.
    """
    if org_id is None:
        return {"verification": FRAMING["portability"], "chain_head": None, "records": []}
    try:
        return {
            "verification": FRAMING["portability"],
            "chain_head": read_decision_head(int(org_id)),
            "records": read_org_decision_chain(int(org_id)),
        }
    except Exception as exc:  # noqa: BLE001 — both reads are fail-soft already
        logger.warning("account export: decisions read failed: %s", type(exc).__name__)
        return {"verification": FRAMING["portability"], "chain_head": None, "records": []}


def _telegram_section(user_id: int) -> dict[str, Any]:
    """The caller's OWN Telegram link. The chat id is the user's data: included.

    Explicit projection — the bot token and pairing codes live elsewhere and
    are never read here.
    """
    try:
        link = get_telegram_link(int(user_id))
    except Exception as exc:  # noqa: BLE001
        logger.warning("account export: telegram read failed: %s", type(exc).__name__)
        return {"connected": False}
    chat_id = link.get("telegram_chat_id")
    return {
        "connected": bool(chat_id),
        "chat_id": str(chat_id) if chat_id else None,
        "username": link.get("telegram_username"),
        "first_name": link.get("telegram_first_name"),
        "paired_at": link.get("telegram_paired_at"),
        "last_test_at": link.get("telegram_last_test_at"),
    }


# ── the assembled export ──────────────────────────────────────────────────────────

def build_account_export(user: dict[str, Any], org_id: int | None) -> dict[str, Any]:
    """Assemble the caller's complete account export envelope. Never raises.

    ``user`` is the authenticated SESSION dict (already an explicit, secret-free
    projection — see ``app.auth.validate_session``); ``org_id`` is the caller's
    resolved org (or ``None``). Every section is owner/org-scoped by these two
    values only.
    """
    user_id = int(user["id"])
    workspace, notifications = _profile_sections(user_id)
    return {
        "schema": SCHEMA,
        "generated_at": _now_utc(),
        "disclaimer": SHORT_DISCLAIMER,
        "framing": dict(FRAMING),
        "account": _account_section(user_id, user),
        "workspace_profile": workspace,
        "notification_preferences": notifications,
        "checklist_items": list_all_checklist_items(user_id),
        "sealed_decisions": _decisions_section(org_id),
        "telegram": _telegram_section(user_id),
    }
