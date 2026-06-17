"""StatuteProof email delivery — monitoring brief dispatch with multi-provider support.

Supports local_outbox (safe default), smtp, sendgrid, and postmark providers.
Production sending is gated by STATUTEPROOF_EMAIL_SEND_ENABLED=true.

Required ENV for production email delivery:
  STATUTEPROOF_EMAIL_PROVIDER     = sendgrid | postmark | smtp | local_outbox (default: local_outbox)
  STATUTEPROOF_EMAIL_SEND_ENABLED = true   (must be explicitly "true" to send externally)
  STATUTEPROOF_EMAIL_FROM         = noreply@statuteproof.com
  STATUTEPROOF_EMAIL_REPLY_TO     = support@statuteproof.com
  STATUTEPROOF_EMAIL_SENDER_NAME  = StatuteProof Monitoring
  SENDGRID_API_KEY                = (required for sendgrid provider)
  POSTMARK_SERVER_TOKEN           = (required for postmark provider)
  SMTP_HOST / SMTP_PORT / SMTP_USERNAME / SMTP_PASSWORD  = (required for smtp provider)
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


def build_monitoring_brief_email(
    brief_markdown: str,
    source_name: str,
    risk_level: str,
    client_name: str = "",
    client_email: str = "",
) -> dict[str, Any]:
    """Build a monitoring brief email payload dict ready for delivery.

    Both body_text and body_html include the mandatory LEGAL_DISCLAIMER.
    If brief_markdown already contains the disclaimer, it is not duplicated.

    Parameters
    ----------
    brief_markdown:
        The monitoring brief content in Markdown format.
    source_name:
        Name of the monitored source (used in the subject line).
    risk_level:
        Risk level string, e.g. "HIGH", "MEDIUM", "LOW", "NON_MATERIAL".
    client_name:
        Optional client name for personalisation.
    client_email:
        Recipient email address.

    Returns
    -------
    dict
        Email payload with keys: to, subject, body_text, body_html, disclaimer_included.
    """
    source_name_safe = str(source_name or "Source").strip()
    risk_level_safe = str(risk_level or "").strip().upper()

    subject = f"[StatuteProof] Monitoring Brief — {source_name_safe} ({risk_level_safe})"

    # Build plain-text body
    body_text = str(brief_markdown or "").strip()
    if LEGAL_DISCLAIMER not in body_text:
        body_text = body_text + "\n\n" + LEGAL_DISCLAIMER + "\n"

    # Build HTML body
    greeting = f"<p>Dear {_esc_html(client_name)},</p>\n" if client_name else ""
    md_html = _brief_markdown_to_html(brief_markdown)
    disclaimer_html = f"<hr><p style='font-size:.85em;color:#555;'>{_esc_html(LEGAL_DISCLAIMER)}</p>"
    if LEGAL_DISCLAIMER in (brief_markdown or ""):
        body_html = (
            "<!doctype html><html><head><meta charset='utf-8'></head><body>"
            + greeting + md_html
            + "</body></html>"
        )
    else:
        body_html = (
            "<!doctype html><html><head><meta charset='utf-8'></head><body>"
            + greeting + md_html + disclaimer_html
            + "</body></html>"
        )

    return {
        "to": str(client_email or "").strip(),
        "subject": subject,
        "body_text": body_text,
        "body_html": body_html,
        "disclaimer_included": True,
    }


def deliver_brief_email(
    payload: dict[str, Any],
    *,
    source_id: str = "",
    env: Mapping[str, str] | None = None,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Dispatch a monitoring brief email using the configured provider.

    Routes to local outbox, sendgrid, postmark, or smtp based on ENV config.
    Writes to outbox when send is not enabled. Never raises.

    Parameters
    ----------
    payload:
        Output of ``build_monitoring_brief_email()``.
    source_id:
        Source identifier for outbox filename.
    env:
        Optional ENV override (used in tests).
    base_dir:
        Optional base dir override (used in tests).

    Returns
    -------
    dict
        Delivery result with ``status`` key.
    """
    try:
        root = base_dir or _BASE_DIR
        config = validate_email_provider_config(env=env)
        provider = config["provider"]
        send_enabled = config.get("send_enabled", False)
        from_email = config.get("from_email") or "noreply@statuteproof.com"
        sender_name = config.get("sender_name") or "StatuteProof Monitoring"

        outbox_dir = root / "data" / "outbox"
        outbox_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        safe_sid = re.sub(r"[^a-zA-Z0-9_-]", "-", str(source_id or "unknown"))[:60]
        outbox_filename = f"brief_{safe_sid}_{timestamp}.json"
        outbox_path = outbox_dir / outbox_filename

        def _write_outbox(reason: str = "") -> dict[str, Any]:
            outbox_dir.mkdir(parents=True, exist_ok=True)
            entry = {**payload, "source_id": source_id, "queued_at": timestamp, "provider": provider}
            outbox_path.write_text(
                json.dumps(entry, ensure_ascii=False, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            result: dict[str, Any] = {"status": "queued_local", "outbox_path": str(outbox_path)}
            if reason:
                result["reason"] = reason
            return result

        if provider == "local_outbox":
            return _write_outbox()

        if not send_enabled:
            return _write_outbox(reason="send_not_enabled")

        # ── SendGrid ──────────────────────────────────────────────────────────
        if provider == "sendgrid":
            source_env = env if env is not None else os.environ
            api_key = str(source_env.get("SENDGRID_API_KEY") or "").strip()
            import urllib.request as _urllib_req
            import urllib.error as _urllib_err
            sg_body = json.dumps({
                "personalizations": [{"to": [{"email": payload["to"]}]}],
                "from": {"email": from_email, "name": sender_name},
                "subject": payload["subject"],
                "content": [
                    {"type": "text/plain", "value": payload["body_text"]},
                    {"type": "text/html", "value": payload["body_html"]},
                ],
            }).encode("utf-8")
            req = _urllib_req.Request(
                "https://api.sendgrid.com/v3/mail/send",
                data=sg_body,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with _urllib_req.urlopen(req, timeout=15) as resp:
                    message_id = resp.headers.get("X-Message-Id", "")
                return {"status": "sent", "provider": "sendgrid", "message_id": message_id}
            except _urllib_err.HTTPError as exc:
                return {"status": "error", "message": f"SendGrid HTTP {exc.code}: {exc.reason}"}

        # ── Postmark ──────────────────────────────────────────────────────────
        if provider == "postmark":
            source_env = env if env is not None else os.environ
            token = str(source_env.get("POSTMARK_SERVER_TOKEN") or "").strip()
            import urllib.request as _urllib_req
            import urllib.error as _urllib_err
            pm_body = json.dumps({
                "From": f"{sender_name} <{from_email}>",
                "To": payload["to"],
                "Subject": payload["subject"],
                "TextBody": payload["body_text"],
                "HtmlBody": payload["body_html"],
            }).encode("utf-8")
            req = _urllib_req.Request(
                "https://api.postmarkapp.com/email",
                data=pm_body,
                headers={
                    "X-Postmark-Server-Token": token,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                method="POST",
            )
            try:
                import json as _json
                with _urllib_req.urlopen(req, timeout=15) as resp:
                    resp_data = _json.loads(resp.read().decode("utf-8"))
                message_id = str(resp_data.get("MessageID") or "")
                return {"status": "sent", "provider": "postmark", "message_id": message_id}
            except _urllib_err.HTTPError as exc:
                return {"status": "error", "message": f"Postmark HTTP {exc.code}: {exc.reason}"}

        # ── SMTP ──────────────────────────────────────────────────────────────
        if provider == "smtp":
            import smtplib
            import email.mime.multipart as _mime_mp
            import email.mime.text as _mime_text
            source_env = env if env is not None else os.environ
            smtp_host = str(source_env.get("SMTP_HOST") or "").strip()
            smtp_port = int(source_env.get("SMTP_PORT") or 465)
            smtp_user = str(source_env.get("SMTP_USERNAME") or "").strip()
            smtp_pass = str(source_env.get("SMTP_PASSWORD") or "").strip()
            msg = _mime_mp.MIMEMultipart("alternative")
            msg["Subject"] = payload["subject"]
            msg["From"] = f"{sender_name} <{from_email}>"
            msg["To"] = payload["to"]
            msg.attach(_mime_text.MIMEText(payload["body_text"], "plain", "utf-8"))
            msg.attach(_mime_text.MIMEText(payload["body_html"], "html", "utf-8"))
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(from_email, [payload["to"]], msg.as_string())
            return {"status": "sent", "provider": "smtp"}

        # Unknown provider fallback
        return _write_outbox(reason="send_not_enabled")

    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def _brief_markdown_to_html(markdown: str) -> str:
    """Convert brief markdown to simple HTML paragraphs (no external deps)."""
    import html as _html_mod
    lines = str(markdown or "").splitlines()
    parts: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            parts.append(f"<h1>{_html_mod.escape(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            parts.append(f"<h2>{_html_mod.escape(stripped[3:])}</h2>")
        elif stripped.startswith("- "):
            parts.append(f"<li>{_html_mod.escape(stripped[2:])}</li>")
        else:
            import re as _re
            escaped = _html_mod.escape(stripped)
            escaped = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
            parts.append(f"<p>{escaped}</p>")
    return "\n".join(parts)


def _esc_html(text: str) -> str:
    """HTML-escape a string."""
    import html as _html_mod
    return _html_mod.escape(str(text or ""))


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
