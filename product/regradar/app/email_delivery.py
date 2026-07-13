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
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from app.evidence_assessment import LEGAL_DISCLAIMER
from app.weekly_brief import render_weekly_brief_html, render_weekly_brief_markdown


_BASE_DIR = Path(os.environ.get("STATUTEPROOF_BASE_DIR") or Path(__file__).parent.parent).resolve()

logger = logging.getLogger(__name__)

SUPPORTED_EMAIL_PROVIDERS = {"local_outbox", "smtp", "postmark", "sendgrid"}
SECRET_ENV_NAMES = {"SMTP_PASSWORD", "POSTMARK_SERVER_TOKEN", "SENDGRID_API_KEY"}


def send_verification_email(
    recipient_email: str,
    verification_url: str,
    *,
    env: Mapping[str, str] | None = None,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Send an email verification link. Uses same provider config as brief delivery."""
    source = env if env is not None else os.environ
    from_email = _safe_email(source.get("STATUTEPROOF_EMAIL_FROM")) or "noreply@statuteproof.com"
    sender_name = _safe_sender_name(source.get("STATUTEPROOF_EMAIL_SENDER_NAME")) or "StatuteProof"
    subject = "Verify your StatuteProof email address"
    body_text = (
        f"Please verify your email address to activate your StatuteProof account.\n\n"
        f"Click the link below (valid for 24 hours):\n{verification_url}\n\n"
        f"If you did not create a StatuteProof account, ignore this email.\n\n"
        f"StatuteProof — Monitoring intelligence only. Not legal advice."
    )
    body_html = (
        f"<p>Please verify your email address to activate your StatuteProof account.</p>"
        f'<p><a href="{verification_url}">Verify my email address</a></p>'
        f"<p style='color:#888;font-size:12px'>Link valid for 24 hours. "
        f"If you did not create a StatuteProof account, ignore this email.</p>"
        f"<p style='color:#888;font-size:12px'>StatuteProof — Monitoring intelligence only. Not legal advice.</p>"
    )
    payload = {
        "to": recipient_email,
        "recipient_email": recipient_email,
        "subject": subject,
        "body_text": body_text,
        "body_html": body_html,
        "from_email": from_email,
        "sender_name": sender_name,
    }
    root = base_dir if base_dir is not None else _BASE_DIR
    return deliver_brief_email(payload, env=env, base_dir=root)


def send_password_reset_email(
    recipient_email: str,
    reset_url: str,
    *,
    env: Mapping[str, str] | None = None,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Send a password-reset link. Same provider config as brief delivery."""
    source = env if env is not None else os.environ
    from_email = _safe_email(source.get("STATUTEPROOF_EMAIL_FROM")) or "noreply@statuteproof.com"
    sender_name = _safe_sender_name(source.get("STATUTEPROOF_EMAIL_SENDER_NAME")) or "StatuteProof"
    subject = "Reset your StatuteProof password"
    body_text = (
        f"We received a request to reset your StatuteProof password.\n\n"
        f"Click the link below to set a new password (valid for 2 hours):\n{reset_url}\n\n"
        f"If you did not request this, ignore this email — your password is unchanged.\n\n"
        f"StatuteProof — Monitoring intelligence only. Not legal advice."
    )
    body_html = (
        f"<p>We received a request to reset your StatuteProof password.</p>"
        f'<p><a href="{reset_url}">Set a new password</a></p>'
        f"<p style='color:#888;font-size:12px'>Link valid for 2 hours. "
        f"If you did not request this, ignore this email — your password is unchanged.</p>"
        f"<p style='color:#888;font-size:12px'>StatuteProof — Monitoring intelligence only. Not legal advice.</p>"
    )
    payload = {
        "to": recipient_email,
        "recipient_email": recipient_email,
        "subject": subject,
        "body_text": body_text,
        "body_html": body_html,
        "from_email": from_email,
        "sender_name": sender_name,
    }
    root = base_dir if base_dir is not None else _BASE_DIR
    return deliver_brief_email(payload, env=env, base_dir=root)


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

    # When provider IS configured AND send is explicitly enabled, delegate to
    # deliver_brief_email() which handles the actual SMTP/SendGrid/Postmark call.
    # deliver_brief_email() branches on (provider, send_enabled) internally,
    # so this is the correct send path for production delivery.
    if status == "production_enabled" and config.get("send_enabled"):
        payload = build_monitoring_brief_email(
            brief_markdown=body_text,
            source_name="",
            risk_level="",
            client_email=recipient,
        )
        # Overwrite the auto-generated fields with the rendered weekly brief content
        payload["subject"]    = subject
        payload["body_text"]  = body_text
        payload["body_html"]  = body_html
        send_result = deliver_brief_email(payload, env=env, base_dir=root)
        send_result.setdefault("channel", "email")
        send_result.setdefault("provider", config["provider"])
        send_result.setdefault("recipient_email", recipient)
        send_result.setdefault("subject", subject)
        send_result.setdefault("body_text", body_text)
        send_result.setdefault("body_html", body_html)
        send_result.setdefault("disclaimer", LEGAL_DISCLAIMER)
        record = {
            "ok": send_result.get("status") == "sent",
            "channel": "email",
            "provider": config["provider"],
            "status": send_result.get("status", "unknown"),
            "recipient_email": recipient,
            "subject": subject,
            "created_at": now_utc(),
            "external_send": True,
            "missing_config": [],
            "legal_disclaimer": LEGAL_DISCLAIMER,
        }
        _append_status(record, status_path)
        return send_result

    # Provider not fully configured OR send_enabled is False — record and return
    # without sending.  status is "ready_but_disabled" or "configuration_required".
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


def _record_delivery_attempt(
    root: Path,
    *,
    provider: str,
    status: str,
    source_id: str,
    payload: dict[str, Any],
    detail: str = "",
) -> None:
    """Append one delivery-attempt row. Every deliver_brief_email outcome
    (queued, sent, dry_run, error, failed_configuration) is recorded so the
    delivery trail is auditable. Never raises."""
    try:
        status_path = root / "data" / "email_outbox" / "delivery_status.jsonl"
        _append_status({
            "channel": "email",
            "kind": "delivery_attempt",
            "provider": provider,
            "status": status,
            "source_id": source_id,
            "to": _safe_email(payload.get("to")),
            "subject": str(payload.get("subject") or "")[:200],
            "detail": detail,
            "external_send": status == "sent",
            "created_at": now_utc(),
        }, status_path)
    except Exception as exc:  # recording must never break delivery
        logger.warning("delivery attempt record failed: %s", exc)


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

        # ── SF-1 legal-safety: final-bytes forbidden-claims guard (fail closed) ──
        # Scan the EXACT bytes a recipient would receive (subject + both bodies)
        # before ANY provider send or outbox write. On a hit: do not send, do not
        # queue — hold for review and log loudly. The shared guard neutralizes
        # the mandatory disclaimer so a brief's own "Not legal advice" denial
        # never self-trips, while any affirmative banned claim is blocked.
        from app.legal_safety import find_forbidden_claims

        _final_bytes = "\n".join(
            str(payload.get(k) or "")
            for k in ("subject", "body_text", "body_html")
        )
        _forbidden_hits = find_forbidden_claims(_final_bytes)
        if _forbidden_hits:
            logger.error(
                "LEGAL-SAFETY BLOCK: brief email WITHHELD — forbidden claim(s) %s "
                "in final bytes (to=%s, source_id=%s); held for review, NOT sent",
                _forbidden_hits, _safe_email(payload.get("to")), source_id,
            )
            try:
                from app.review_queue import record_held_alert

                record_held_alert(
                    "forbidden_claim_in_email_final_bytes",
                    message=str(payload.get("body_text") or ""),
                    context={
                        "channel": "email",
                        "to": _safe_email(payload.get("to")),
                        "subject": str(payload.get("subject") or "")[:200],
                        "source_id": str(source_id or ""),
                        "detail": ", ".join(_forbidden_hits),
                    },
                    base_dir=root,
                )
            except Exception as hold_err:  # pragma: no cover - defensive
                logger.error("could not record held email: %s", hold_err)
            _record_delivery_attempt(
                root, provider="unknown", status="blocked_forbidden_claim",
                source_id=source_id, payload=payload,
                detail=", ".join(_forbidden_hits),
            )
            return {
                "status": "error",
                "message": "Email withheld: output contains a forbidden claim. Held for review.",
                "forbidden_claims": _forbidden_hits,
            }

        config = validate_email_provider_config(env=env)
        provider = config["provider"]
        send_enabled = config.get("send_enabled", False)
        from_email = config.get("from_email") or "noreply@statuteproof.com"
        sender_name = config.get("sender_name") or "StatuteProof Monitoring"
        source_env_top = env if env is not None else os.environ
        dry_run = _truthy(source_env_top.get("STATUTEPROOF_EMAIL_DRY_RUN"))

        # A selected-but-misconfigured provider must fail loudly — never a
        # silent outbox fallback (owner decision, cycle 2).
        if provider != "local_outbox" and config.get("missing_config"):
            missing = list(config["missing_config"])
            logger.error(
                "EMAIL DELIVERY MISCONFIGURED: provider=%s missing=%s — "
                "delivery refused, nothing queued to outbox",
                provider, ",".join(missing),
            )
            _record_delivery_attempt(
                root, provider=provider, status="failed_configuration",
                source_id=source_id, payload=payload,
                detail=f"missing: {', '.join(missing)}",
            )
            return {
                "status": "error",
                "message": f"Email provider {provider} is misconfigured. Missing: {', '.join(missing)}",
                "missing_config": missing,
            }

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
            _record_delivery_attempt(
                root, provider=provider, status="queued_local",
                source_id=source_id, payload=payload, detail=reason,
            )
            return result

        if provider == "local_outbox":
            return _write_outbox()

        if not send_enabled:
            return _write_outbox(reason="send_not_enabled")

        if dry_run:
            # Prod smoke test: exercise the full provider path with zero
            # network I/O; the attempt is recorded like any other outcome.
            logger.info(
                "EMAIL DRY_RUN: provider=%s to=%s subject=%r — no send performed",
                provider, _safe_email(payload.get("to")), str(payload.get("subject"))[:80],
            )
            _record_delivery_attempt(
                root, provider=provider, status="dry_run",
                source_id=source_id, payload=payload,
            )
            return {"status": "dry_run", "provider": provider, "to": payload.get("to"), "subject": payload.get("subject")}

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
                _record_delivery_attempt(root, provider="sendgrid", status="sent",
                                         source_id=source_id, payload=payload, detail=message_id)
                return {"status": "sent", "provider": "sendgrid", "message_id": message_id}
            except _urllib_err.HTTPError as exc:
                logger.error("EMAIL DELIVERY FAILED: SendGrid HTTP %s: %s", exc.code, exc.reason)
                _record_delivery_attempt(root, provider="sendgrid", status="error",
                                         source_id=source_id, payload=payload,
                                         detail=f"HTTP {exc.code}: {exc.reason}")
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
                _record_delivery_attempt(root, provider="postmark", status="sent",
                                         source_id=source_id, payload=payload, detail=message_id)
                return {"status": "sent", "provider": "postmark", "message_id": message_id}
            except _urllib_err.HTTPError as exc:
                logger.error("EMAIL DELIVERY FAILED: Postmark HTTP %s: %s", exc.code, exc.reason)
                _record_delivery_attempt(root, provider="postmark", status="error",
                                         source_id=source_id, payload=payload,
                                         detail=f"HTTP {exc.code}: {exc.reason}")
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
            _record_delivery_attempt(root, provider="smtp", status="sent",
                                     source_id=source_id, payload=payload)
            return {"status": "sent", "provider": "smtp"}

        # Unknown provider fallback
        return _write_outbox(reason="send_not_enabled")

    except Exception as exc:
        logger.error("EMAIL DELIVERY FAILED: %s: %s", type(exc).__name__, exc)
        try:
            _record_delivery_attempt(
                (base_dir or _BASE_DIR), provider="unknown", status="error",
                source_id=source_id, payload=payload, detail=str(exc)[:300],
            )
        except Exception:
            pass
        return {"status": "error", "message": str(exc)}


def _brief_markdown_to_html(markdown: str) -> str:
    """Convert brief markdown to simple HTML paragraphs (no external deps).

    Ordering contract:
    1. html.escape() the raw text first — this escapes &, <, >, " but NOT *.
    2. Apply bold/italic regex replacements on the escaped text — safe because
       html.escape() never touches asterisks, so **..** patterns survive intact.
       Inner content rendered inside <strong>...</strong> is already HTML-safe.
    This order is correct for all line types (headings, list items, paragraphs).
    """
    import html as _html_mod
    import re as _re

    def _apply_inline(text: str) -> str:
        """Escape HTML, then render **bold** and *italic* markers."""
        escaped = _html_mod.escape(text)
        # Bold — ** is not touched by html.escape, so this matches correctly.
        escaped = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
        # Italic — single * not adjacent to another *.
        escaped = _re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", escaped)
        return escaped

    lines = str(markdown or "").splitlines()
    parts: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            parts.append(f"<h1>{_apply_inline(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            parts.append(f"<h2>{_apply_inline(stripped[3:])}</h2>")
        elif stripped.startswith("- "):
            parts.append(f"<li>{_apply_inline(stripped[2:])}</li>")
        else:
            parts.append(f"<p>{_apply_inline(stripped)}</p>")
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
    # CROSS-TENANT SAFETY: build_email_status_response surfaces the LAST row of a
    # single GLOBAL delivery_status.jsonl to any authenticated caller, so this
    # allowlist must expose ONLY channel/config health — never per-send content.
    # ``recipient_email`` (another tenant's PII), ``subject`` (embeds a private
    # custom source's name, e.g. "Monitoring Brief — <source_name>"),
    # ``outbox_path`` and ``error_message`` (an SMTP bounce can echo a recipient)
    # are deliberately excluded. A user's own send details live in the per-user
    # scoped get_user_delivery_logs(user_id), not here.
    allowed = {
        "ok",
        "channel",
        "provider",
        "status",
        "created_at",
        "external_send",
        "missing_config",
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
