"""Cross-tenant leak regression for the automated deadline-reminder broadcast.

Round-6 convergence finding: deadline_radar.send_due_reminders resolved
recipients ONCE globally via get_all_linked_chat_ids() and sent every due
reminder — which embeds source_name, private official_url, and a verbatim diff
excerpt — to all of them. A custom source owned by user 1 leaked its private
reminder to every paired customer on the daily `watch` pass (and the
`run.py deadlines --send` CLI, which shares the function).

Fix: recipients are resolved PER ENTRY — a custom source reminder goes only to
its owner (get_alert_chat_ids_for_user), a custom source with no resolvable
owner goes to nobody, and official/legacy entries use the broadcast pool.
"""
from __future__ import annotations

import sys
from pathlib import Path

PRODUCT_DIR = str(Path(__file__).resolve().parents[1])
if PRODUCT_DIR not in sys.path:
    sys.path.insert(0, PRODUCT_DIR)

import app.deadline_radar as deadline_radar

_OWNER_ID = 1
_SOURCES = [
    {"source_id": "custom-A", "custom": True, "owner_user_id": _OWNER_ID,
     "name": "ACME Internal Compliance Feed", "url": "https://acme-private.example/x"},
    {"source_id": "official-X", "name": "CBUAE — Public Notices",
     "url": "https://www.centralbank.ae/en/notices"},
]

_CUSTOM_ENTRY = {"deadline_id": "d-custom", "source_id": "custom-A",
                 "source_name": "ACME Internal Compliance Feed",
                 "official_url": "https://acme-private.example/x",
                 "evidence_record_id": "r-A", "lead_stage": 7, "days_until": 7,
                 "deadline_date": "2026-08-01"}
_OFFICIAL_ENTRY = {"deadline_id": "d-official", "source_id": "official-X",
                   "source_name": "CBUAE — Public Notices",
                   "official_url": "https://www.centralbank.ae/en/notices",
                   "evidence_record_id": "r-X", "lead_stage": 7, "days_until": 7,
                   "deadline_date": "2026-08-01"}


def _wire(monkeypatch, entries):
    monkeypatch.setattr("app.source_intake.load_sources_json", lambda: list(_SOURCES))
    monkeypatch.setattr(deadline_radar, "due_reminders", lambda **k: [dict(e) for e in entries])
    monkeypatch.setattr(deadline_radar, "render_reminder_message", lambda e: f"reminder for {e['source_id']}")
    monkeypatch.setattr("app.telegram_pairing.get_all_linked_chat_ids", lambda: ["chatOwner", "chatAttacker"])
    monkeypatch.setattr(
        "app.telegram_pairing.get_alert_chat_ids_for_user",
        lambda uid: ["chatOwner"] if int(uid) == _OWNER_ID else ["chatAttacker"],
    )
    sent: list[tuple[str, str]] = []

    def _send(chat_id, message):
        sent.append((str(chat_id), str(message)))
        return True

    return sent, _send


def test_custom_source_reminder_only_to_owner(monkeypatch, tmp_path):
    sent, send = _wire(monkeypatch, [_CUSTOM_ENTRY])
    deadline_radar.send_due_reminders(base_dir=tmp_path, send_fn=send)
    recipients = {c for c, _ in sent}
    assert recipients == {"chatOwner"}  # attacker never receives the private reminder
    assert all("custom-A" in m for _, m in sent)


def test_official_source_reminder_broadcasts(monkeypatch, tmp_path):
    sent, send = _wire(monkeypatch, [_OFFICIAL_ENTRY])
    deadline_radar.send_due_reminders(base_dir=tmp_path, send_fn=send)
    assert {c for c, _ in sent} == {"chatOwner", "chatAttacker"}


def test_mixed_batch_scopes_each_entry(monkeypatch, tmp_path):
    sent, send = _wire(monkeypatch, [_CUSTOM_ENTRY, _OFFICIAL_ENTRY])
    deadline_radar.send_due_reminders(base_dir=tmp_path, send_fn=send)
    by_source = {}
    for chat, msg in sent:
        src = "custom-A" if "custom-A" in msg else "official-X"
        by_source.setdefault(src, set()).add(chat)
    assert by_source["custom-A"] == {"chatOwner"}
    assert by_source["official-X"] == {"chatOwner", "chatAttacker"}


def test_custom_source_no_owner_reaches_nobody(monkeypatch, tmp_path):
    orphan = dict(_CUSTOM_ENTRY, source_id="custom-Z")
    monkeypatch.setattr("app.source_intake.load_sources_json", lambda: [{"source_id": "custom-Z", "custom": True}])
    monkeypatch.setattr(deadline_radar, "due_reminders", lambda **k: [dict(orphan)])
    monkeypatch.setattr(deadline_radar, "render_reminder_message", lambda e: "orphan reminder")
    monkeypatch.setattr("app.telegram_pairing.get_all_linked_chat_ids", lambda: ["chatOwner", "chatAttacker"])
    monkeypatch.setattr("app.telegram_pairing.get_alert_chat_ids_for_user", lambda uid: [])
    sent: list = []
    result = deadline_radar.send_due_reminders(
        base_dir=tmp_path, send_fn=lambda c, m: sent.append(c) or True
    )
    assert sent == []
    assert result["skipped_no_recipients"] >= 1
