"""Safe email brief delivery test mode.

No SMTP or external delivery happens here. The MVP writes a complete email
payload to a local outbox and records delivery status so the reviewed brief
pipeline can be tested end-to-end without contacting customers.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from app.evidence_assessment import LEGAL_DISCLAIMER
from app.weekly_brief import render_weekly_brief_html, render_weekly_brief_markdown


_BASE_DIR = Path(__file__).parent.parent

SUPPORTED_EMAIL_PROVIDERS = {"local_outbox", "smtp", "postmark", "sendgrid"}
SECRET_ENV_NAMES = {"SMTP_PASSWORD", "POSTMARK_SERVER_TOKEN", "SENDGRID_API_KEY"}


def validate_email_provider_config(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = env if env is not None else os.environ
    provider = str(source.get("STATUTEPROOF_EMAIL_PROVIDER") or "local_outbox").strip().lower() or "local_outbox"
    if provider not in SUPPORTED_EMAIL_PROVIDERS:
        return {
            "provider": provider,
            "mode": "configuration",
            "provider_configured": False,
            "send_enabled": False,
            "missing_config": ["STATUTEPROOF_EMAIL_PROVIDER"],
            "from_email": _safe_email(source.get("STATUTEPROOF_EMAIL_FROM")),
            "reply_to_email": _safe_email(source.get("STATUTEPROOF_EMAIL_REPLY_TO")),
            "sender_name": _safe_sender_name(source.get("STATUTEPROOF_EMAIL_SENDER_NAME")),
            "test_recipient_email": "",
            "status": "configuration_required",
            "customer_safe_status": "Unsupported email provider. Review configuration before delivery.",
            "internal_debug_status": "unsupported_provider",
        }

    from_email = _safe_email(source.get("STATUTEPROOF_EMAIL_FROM"))
    reply_to_email = _safe_email(source.get("STATUTEPROOF_EMAIL_REPLY_TO"))
    sender_name = _safe_sender_name(source.get("STATUTEPROOF_EMAIL_SENDER_NAME"))
    send_enabled = _truthy(source.get("STATUTEPROOF_EMAIL_SEND_ENABLED"))

    if provider == "local_outbox":
        return {
            "provider": "local_outbox",
            "mode": "test_mode",
            "provider_configured": True,
            "send_enabled": False,
            "missing_config": [],
            "from_email": from_email,
            "reply_to_email": reply_to_email,
            "sender_name": sender_name,
            "test_recipient_email": "",
            "status": "test_mode",
            "customer_safe_status": "Email delivery is in local outbox/test-mode. No external customer email is sent.",
            "internal_debug_status": "local_outbox_default",
        }

    required_by_provider = {
        "smtp": ["STATUTEPROOF_EMAIL_FROM", "SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD"],
        "postmark": ["STATUTEPROOF_EMAIL_FROM", "POSTMARK_SERVER_TOKEN"],
        "sendgrid": ["STATUTEPROOF_EMAIL_FROM", "SENDGRID_API_KEY"],
    }
    missing = [
        key for key in required_by_provider[provider]
        if not str(source.get(key) or "").strip()
    ]
    provider_configured = not missing
    status = (
        "configuration_required"
        if missing
        else "production_enabled"
        if send_enabled
        else "ready_but_disabled"
    )
    customer_safe_status = {
        "configuration_required": "Email provider configuration is incomplete. Missing fields must be added before production delivery.",
        "ready_but_disabled": "Email provider configuration is present, but external sending is disabled.",
        "production_enabled": "Email provider configuration is present and external sending is explicitly enabled.",
    }[status]
    return {
        "provider": provider,
        "mode": "provider",
        "provider_configured": provider_configured,
        "send_enabled": bool(send_enabled and provider_configured),
        "missing_config": missing,
        "from_email": from_email,
        "reply_to_email": reply_to_email,
        "sender_name": sender_name,
        "test_recipient_email": "",
        "status": status,
        "customer_safe_status": customer_safe_status,
        "internal_debug_status": f"{provider}:{status}:missing={len(missing)}",
    }


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def deliver_weekly_brief_test_mode(
    brief: dict[str, Any],
    *,
    recipient_email: str,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    root = base_dir or _BASE_DIR
    recipient = str(recipient_email or "").strip()
    status_path = root / "data" / "email_outbox" / "delivery_status.jsonl"
    if not _valid_email(recipient):
        record = {
            "ok": False,
            "channel": "email",
            "status": "failed",
            "recipient_email": recipient,
            "error_message": "Invalid recipient email.",
            "created_at": now_utc(),
        }
        _append_status(record, status_path)
        return {"ok": False, "channel": "email", "status": "failed", "status_path": _rel(status_path, root), "error_message": record["error_message"]}

    subject = _subject_for_brief(brief)
    body_text = render_weekly_brief_markdown(brief)
    if LEGAL_DISCLAIMER not in body_text:
        body_text = body_text.rstrip() + "\n\n" + LEGAL_DISCLAIMER + "\n"
    body_html = render_weekly_brief_html(brief)
    if LEGAL_DISCLAIMER not in body_html:
        body_html = body_html.replace("</body>", f"<p>{LEGAL_DISCLAIMER}</p></body>")

    created_at = now_utc()
    email_id = _email_id(recipient, subject, created_at)
    outbox_dir = root / "data" / "email_outbox"
    outbox_dir.mkdir(parents=True, exist_ok=True)
    outbox_path = outbox_dir / f"{email_id}.json"
    payload = {
        "email_id": email_id,
        "mode": "test",
        "external_send": False,
        "to": recipient,
        "subject": subject,
        "body_text": body_text,
        "body_html": body_html,
        "created_at": created_at,
        "legal_disclaimer": LEGAL_DISCLAIMER,
        "brief_id": _brief_id(brief),
    }
    outbox_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    record = {
        "ok": True,
        "channel": "email",
        "status": "written",
        "recipient_email": recipient,
        "subject": subject,
        "outbox_path": _rel(outbox_path, root),
        "created_at": created_at,
        "external_send": False,
    }
    _append_status(record, status_path)
    return {
        "ok": True,
        "channel": "email",
        "status": "written",
        "outbox_path": _rel(outbox_path, root),
        "status_path": _rel(status_path, root),
        "subject": subject,
        "external_send": False,
    }


def deliver_weekly_brief_provider_ready(
    brief: dict[str, Any],
    *,
    recipient_email: str,
    env: Mapping[str, str] | None = None,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    root = base_dir or _BASE_DIR
    config = validate_email_provider_config(env=env)
    if config["provider"] == "local_outbox":
        return deliver_weekly_brief_test_mode(brief, recipient_email=recipient_email, base_dir=root)

    recipient = str(recipient_email or "").strip()
    status_path = root / "data" / "email_outbox" / "delivery_status.jsonl"
    subject = _subject_for_brief(brief)
    body_text = render_weekly_brief_markdown(brief)
    if LEGAL_DISCLAIMER not in body_text:
        body_text = body_text.rstrip() + "\n\n" + LEGAL_DISCLAIMER + "\n"
    body_html = render_weekly_brief_html(brief)
    if LEGAL_DISCLAIMER not in body_html:
        body_html = body_html.replace("</body>", f"<p>{LEGAL_DISCLAIMER}</p></body>")

    status = config["status"]
    if status == "production_enabled":
        status = "ready_but_disabled"
    record = {
        "ok": False,
        "channel": "email",
        "provider": config["provider"],
        "status": status,
        "recipient_email": recipient,
        "subject": subject,
        "created_at": now_utc(),
        "external_send": False,
        "missing_config": config["missing_config"],
        "legal_disclaimer": LEGAL_DISCLAIMER,
    }
    _append_status(record, status_path)
    return {
        "ok": False,
        "channel": "email",
        "provider": config["provider"],
        "status": status,
        "recipient_email": recipient,
        "subject": subject,
        "body_text": body_text,
        "body_html": body_html,
        "status_path": _rel(status_path, root),
        "external_send": False,
        "missing_config": config["missing_config"],
        "message": config["customer_safe_status"],
        "disclaimer": LEGAL_DISCLAIMER,
    }


def build_email_status_response(
    *,
    base_dir: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    config = validate_email_provider_config(env=env)
    return {
        "ok": True,
        "provider": config["provider"],
        "mode": config["mode"],
        "provider_configured": config["provider_configured"],
        "send_enabled": config["send_enabled"],
        "status": config["status"],
        "missing_config": config["missing_config"],
        "from_email": config["from_email"],
        "reply_to_email": config["reply_to_email"],
        "sender_name": config["sender_name"],
        "test_recipient_email": config["test_recipient_email"],
        "customer_safe_status": config["customer_safe_status"],
        "internal_debug_status": config["internal_debug_status"],
        "last_delivery_status": latest_email_delivery_status(base_dir=base_dir),
        "disclaimer": LEGAL_DISCLAIMER,
    }


def record_email_config_check(
    *,
    base_dir: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    root = base_dir or _BASE_DIR
    config = validate_email_provider_config(env=env)
    status_path = root / "data" / "email_outbox" / "delivery_status.jsonl"
    record = {
        "ok": config["provider_configured"],
        "channel": "email",
        "provider": config["provider"],
        "status": config["status"],
        "missing_config": config["missing_config"],
        "created_at": now_utc(),
        "external_send": False,
        "legal_disclaimer": LEGAL_DISCLAIMER,
    }
    _append_status(record, status_path)
    response = build_email_status_response(base_dir=root, env=env)
    response["status_path"] = _rel(status_path, root)
    return response


def latest_email_delivery_status(base_dir: Path | None = None) -> dict[str, Any] | None:
    root = base_dir or _BASE_DIR
    status_path = root / "data" / "email_outbox" / "delivery_status.jsonl"
    if not status_path.exists():
        return None
    last: dict[str, Any] | None = None
    for line in status_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        last = _safe_status_row(row)
    return last


def _subject_for_brief(brief: dict[str, Any]) -> str:
    market = brief.get("market") or "AE"
    period_end = brief.get("period_end") or datetime.now(timezone.utc).date().isoformat()
    return f"StatuteProof Weekly Regulatory Brief - {market} - {period_end}"


def _brief_id(brief: dict[str, Any]) -> str:
    seed = "|".join(str(brief.get(k) or "") for k in ("client_id", "market", "period_start", "period_end"))
    return "brief-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]


def _email_id(recipient: str, subject: str, created_at: str) -> str:
    seed = f"{recipient}|{subject}|{created_at}"
    return "email-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def _valid_email(value: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value))


def _safe_email(value: str | None) -> str:
    text = str(value or "").strip()
    return text if _valid_email(text) else ""


def _safe_sender_name(value: str | None) -> str:
    text = str(value or "").strip()
    return text[:80] if text else "StatuteProof"


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _safe_status_row(row: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "ok",
        "channel",
        "provider",
        "status",
        "recipient_email",
        "subject",
        "outbox_path",
        "created_at",
        "external_send",
        "missing_config",
        "error_message",
    }
    safe = {key: value for key, value in row.items() if key in allowed}
    for key in SECRET_ENV_NAMES:
        safe.pop(key, None)
    return safe


def _append_status(record: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _rel(path: Path, base_dir: Path) -> str:
    try:
        return str(path.resolve().relative_to(base_dir.resolve()))
    except ValueError:
        return str(path)
