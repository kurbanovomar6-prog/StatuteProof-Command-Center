"""Cross-tenant leak regression for the AUTOMATED Telegram alert broadcast.

Round-6 finding (the most severe of the class): the pipeline's automatic
delivery path `send_telegram_alert` -> `_deliver_alert_to_subscribed_users` sent
the rendered alert (source_name, private official_url, diff excerpt, executive
summary) to `get_all_linked_chat_ids()` — EVERY paired account — with no owner
scoping. A routine change on user 1's PRIVATE custom source was broadcast to
user 2 automatically, no attacker action beyond pairing.

Fix: a custom source's alert is delivered ONLY to its owner; a custom source
with no resolvable owner is delivered to NOBODY (fail closed); official/shared
sources (and legacy no-source_id calls) still broadcast.
"""
from __future__ import annotations

import sys
from pathlib import Path

PRODUCT_DIR = str(Path(__file__).resolve().parents[1])
if PRODUCT_DIR not in sys.path:
    sys.path.insert(0, PRODUCT_DIR)

import app.telegram as telegram

_OWNER_ID = 1
_SOURCES = [
    {"source_id": "custom-A", "custom": True, "owner_user_id": _OWNER_ID,
     "name": "ACME Internal Compliance Feed", "url": "https://acme-private.example/x"},
    {"source_id": "official-X", "name": "CBUAE — Public Notices",
     "url": "https://www.centralbank.ae/en/notices"},
]


def _wire(monkeypatch, sources=_SOURCES):
    sent: list[str] = []
    monkeypatch.setattr("app.source_intake.load_sources_json", lambda: list(sources))
    monkeypatch.setattr(telegram, "send_telegram_message", lambda chat, msg: sent.append(str(chat)) or True)
    monkeypatch.setattr("app.telegram_pairing.get_all_linked_chat_ids", lambda: ["chatOwner", "chatAttacker"])
    monkeypatch.setattr(
        "app.telegram_pairing.get_alert_chat_ids_for_user",
        lambda uid: ["chatOwner"] if int(uid) == _OWNER_ID else ["chatAttacker"],
    )
    return sent


def test_custom_source_alert_delivered_only_to_owner(monkeypatch):
    sent = _wire(monkeypatch)
    n = telegram._deliver_alert_to_subscribed_users("private diff", source_id="custom-A")
    assert n == 1
    assert sent == ["chatOwner"]  # attacker's chat never receives it


def test_official_source_alert_still_broadcasts(monkeypatch):
    sent = _wire(monkeypatch)
    n = telegram._deliver_alert_to_subscribed_users("public notice", source_id="official-X")
    assert set(sent) == {"chatOwner", "chatAttacker"}
    assert n == 2


def test_legacy_no_source_id_still_broadcasts(monkeypatch):
    sent = _wire(monkeypatch)
    n = telegram._deliver_alert_to_subscribed_users("legacy alert")
    assert set(sent) == {"chatOwner", "chatAttacker"}


def test_custom_source_no_owner_delivers_to_nobody(monkeypatch):
    # custom source with no owner recorded → unattributable → deliver to nobody.
    sent = _wire(monkeypatch, sources=[{"source_id": "custom-Z", "custom": True}])
    n = telegram._deliver_alert_to_subscribed_users("orphan private diff", source_id="custom-Z")
    assert n == 0
    assert sent == []


def test_custom_prefix_fails_closed_when_source_list_unreadable(monkeypatch):
    """Belt-and-suspenders: even if sources.json is unreadable, a ``custom-``
    prefixed id is never broadcast (is_custom_source uses the prefix)."""
    sent: list[str] = []

    def _boom():
        raise RuntimeError("unreadable sources.json")

    monkeypatch.setattr("app.source_intake.load_sources_json", _boom)
    monkeypatch.setattr(telegram, "send_telegram_message", lambda chat, msg: sent.append(str(chat)) or True)
    monkeypatch.setattr("app.telegram_pairing.get_all_linked_chat_ids", lambda: ["chatOwner", "chatAttacker"])
    monkeypatch.setattr("app.telegram_pairing.get_alert_chat_ids_for_user", lambda uid: [])
    n = telegram._deliver_alert_to_subscribed_users("private diff", source_id="custom-deadbeef")
    assert n == 0
    assert sent == []
