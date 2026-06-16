"""Safe email brief delivery test mode.

No SMTP or external delivery happens here. The MVP writes a complete email
payload to a local outbox and records delivery status so the reviewed brief
pipeline can be tested end-to-end without contacting customers.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.evidence_assessment import LEGAL_DISCLAIMER
from app.weekly_brief import render_weekly_brief_html, render_weekly_brief_markdown


_BASE_DIR = Path(__file__).parent.parent


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

