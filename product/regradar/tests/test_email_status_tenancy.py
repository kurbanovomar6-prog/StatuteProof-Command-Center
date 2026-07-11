"""Cross-tenant leak regression for the email delivery-status read path.

Final sign-off finding: build_email_status_response surfaces the LAST row of a
single GLOBAL data/email_outbox/delivery_status.jsonl to any authenticated
caller. The row's allowlist exposed recipient_email (another tenant's PII) and
subject (which for a monitoring brief embeds a private custom source's name,
"[StatuteProof] Monitoring Brief — <source_name> (<risk>)"). It survived six
rounds because the READ side carries no source_id.

Fix: the cross-request status row exposes only channel/config health — never
per-send content (recipient_email / subject / outbox_path / error_message).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PRODUCT_DIR = str(Path(__file__).resolve().parents[1])
if PRODUCT_DIR not in sys.path:
    sys.path.insert(0, PRODUCT_DIR)

import app.email_delivery as email_delivery

# Fields that must never appear in a cross-request delivery-status read.
_SENSITIVE = {"recipient_email", "subject", "outbox_path", "error_message", "to", "body_text", "body_html"}


def _seed_status_row(tmp_path: Path, row: dict) -> None:
    outbox = tmp_path / "data" / "email_outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    (outbox / "delivery_status.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")


def test_latest_status_never_leaks_recipient_or_subject(tmp_path):
    _seed_status_row(tmp_path, {
        "ok": True, "channel": "email", "provider": "zoho", "status": "sent",
        "created_at": "2026-07-11T10:00:00Z", "external_send": True,
        "recipient_email": "victim@othertenant.example",
        "subject": "[StatuteProof] Monitoring Brief — ACME Internal Compliance Feed (HIGH)",
        "outbox_path": "data/email_outbox/msg-1.json",
        "error_message": "550 mailbox victim@othertenant.example unavailable",
    })
    row = email_delivery.latest_email_delivery_status(base_dir=tmp_path) or {}
    blob = json.dumps(row)
    assert "victim@othertenant.example" not in blob
    assert "ACME Internal Compliance Feed" not in blob
    assert not (_SENSITIVE & set(row.keys()))
    # Health signal is preserved.
    assert row.get("status") == "sent"
    assert row.get("provider") == "zoho"


def test_email_status_response_excludes_per_send_content(tmp_path, monkeypatch):
    _seed_status_row(tmp_path, {
        "ok": False, "channel": "email", "provider": "zoho", "status": "failed",
        "recipient_email": "victim@othertenant.example",
        "subject": "[StatuteProof] Monitoring Brief — ACME Internal Compliance Feed (HIGH)",
        "created_at": "2026-07-11T10:00:00Z",
    })
    resp = email_delivery.build_email_status_response(base_dir=tmp_path, env={})
    blob = json.dumps(resp)
    assert "victim@othertenant.example" not in blob
    assert "ACME Internal Compliance Feed" not in blob
    last = resp.get("last_delivery_status") or {}
    assert not (_SENSITIVE & set(last.keys()))
