"""User-triggered sample brief delivery and per-user delivery logs."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from app.db import _connect, ensure_auth_tables, ensure_delivery_log_table
from app.profile import get_or_create_profile
from app.telegram import send_telegram_message
from app.telegram_pairing import get_telegram_link


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _json_dumps(data) -> str:
    return json.dumps(data or {}, ensure_ascii=False, sort_keys=True)


def _safe_preview(text: str, limit: int = 300) -> str:
    value = str(text or "").strip()
    if len(value) > limit:
        return value[:limit] + "..."
    return value


def is_user_delivery_eligible(user_id: int) -> tuple[bool, str, dict]:
    ensure_auth_tables()
    profile = get_or_create_profile(int(user_id))
    link = get_telegram_link(int(user_id))
    context = {"profile": profile, "link": link}

    if not link.get("telegram_chat_id"):
        return False, "Telegram not connected.", context
    if not profile.get("onboarding_completed"):
        return False, "Onboarding is not complete.", context
    if not profile.get("telegram_alerts_enabled"):
        return False, "Telegram alerts are disabled.", context
    return True, "ok", context


def build_sample_brief_message(profile: dict, link: dict) -> str:
    company = profile.get("company_name") or "Your workspace"
    today = _today_iso()
    return "\n".join([
        "StatuteProof - Sample Delivery Confirmation",
        "",
        f"Workspace: {company}",
        f"Date: {today}",
        "",
        "This sample brief confirms your Telegram is connected and can receive StatuteProof notifications.",
        "",
        "------------------------------",
        "Sample: Regulatory Update",
        "",
        "Source: DFSA - Dubai Financial Services Authority",
        "Type: Consultation paper",
        "Topic: Fund manager licensing",
        "",
        "Why it matters:",
        "Relevant to financial services and securities operations in DIFC.",
        "",
        "Source proof:",
        "https://www.dfsa.ae/consultations",
        "",
        "Limitations:",
        "This is a delivery test with illustrative content. Real briefs include only human-reviewed changes.",
        "",
        "Not legal advice.",
        "Manage alerts: StatuteProof -> Integrations",
    ])


def create_delivery_log(
    user_id: int,
    delivery_type: str,
    channel: str = "telegram",
    status: str = "pending",
    title: str | None = None,
    message_preview: str | None = None,
    source_id: str | None = None,
    alert_id: str | None = None,
    brief_id: str | None = None,
    error_message: str | None = None,
    idempotency_key: str | None = None,
    metadata: dict | None = None,
) -> dict:
    ensure_delivery_log_table()
    conn = _connect()
    try:
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO user_delivery_log (
                user_id, delivery_type, channel, status, title, message_preview,
                source_id, alert_id, brief_id, error_message, idempotency_key,
                created_at, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                str(delivery_type),
                str(channel or "telegram"),
                str(status or "pending"),
                title,
                _safe_preview(message_preview or "", 300) if message_preview else None,
                source_id,
                alert_id,
                brief_id,
                _safe_preview(error_message or "", 500) if error_message else None,
                idempotency_key,
                _now_iso(),
                _json_dumps(metadata),
            ),
        )
        conn.commit()
        if cur.rowcount:
            return {"created": True, "id": cur.lastrowid}
        return {"created": False, "reason": "duplicate"}
    finally:
        conn.close()


def update_delivery_log_sent(log_id: int) -> None:
    ensure_delivery_log_table()
    now = _now_iso()
    conn = _connect()
    try:
        conn.execute(
            "UPDATE user_delivery_log SET status = ?, sent_at = ? WHERE id = ?",
            ("sent", now, int(log_id)),
        )
        conn.commit()
    finally:
        conn.close()


def update_delivery_log_failed(log_id: int, error_message: str) -> None:
    ensure_delivery_log_table()
    conn = _connect()
    try:
        conn.execute(
            """
            UPDATE user_delivery_log
            SET status = ?, error_message = ?
            WHERE id = ?
            """,
            ("failed", _safe_preview(error_message, 500), int(log_id)),
        )
        conn.commit()
    finally:
        conn.close()


def send_sample_brief_to_user(user_id: int) -> dict:
    eligible, reason, context = is_user_delivery_eligible(int(user_id))
    if not eligible:
        return {"ok": False, "reason": reason}

    profile = context["profile"]
    link = context["link"]
    idempotency_key = f"{int(user_id)}:sample_brief:{_today_iso()}"
    message = build_sample_brief_message(profile, link)
    log = create_delivery_log(
        int(user_id),
        delivery_type="sample_brief",
        channel="telegram",
        status="pending",
        title="Sample Regulatory Brief",
        message_preview=_safe_preview(message, 300),
        idempotency_key=idempotency_key,
        metadata={
            "sample": True,
            "source": "DFSA",
            "source_url": "https://www.dfsa.ae/consultations",
        },
    )
    if not log.get("created"):
        return {"ok": False, "reason": "Sample brief already sent today."}

    log_id = int(log["id"])
    if send_telegram_message(str(link["telegram_chat_id"]), message):
        update_delivery_log_sent(log_id)
        return {
            "ok": True,
            "message": "Sample brief sent to your Telegram.",
            "log_id": log_id,
        }

    update_delivery_log_failed(log_id, "Telegram send failed.")
    return {"ok": False, "reason": "Telegram send failed.", "log_id": log_id}


def get_user_delivery_logs(user_id: int, limit: int = 20) -> list[dict]:
    ensure_delivery_log_table()
    safe_limit = max(1, min(int(limit or 20), 50))
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT id, delivery_type, channel, status, title, created_at,
                   sent_at, error_message
            FROM user_delivery_log
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (int(user_id), safe_limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
