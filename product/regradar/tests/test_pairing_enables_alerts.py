"""Pairing IS the opt-in to alerts (live CRITICAL, 2026-07-18).

The product's core deliverable is regulatory alerts. telegram_alerts_enabled
defaults to 0 and was NEVER set to 1 by any automatic path — only a manual
SettingsPage toggle flipped it. Delivery filters `AND telegram_alerts_enabled
= 1` (telegram_pairing.get_all_linked_chat_ids). So every customer who paired
Telegram via /start CODE — and whom the bot told "This chat can now receive
regulatory change alerts" — received NOTHING unless they later dug into
Settings. Pairing is the explicit consent; consume_pairing_code must enable
alerts in the same transaction.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "pair.db"))
    yield tmp_path / "pair.db"


def _new_user(email: str) -> int:
    from app.auth import create_user

    return int(create_user(email, "password-123")["id"])


def test_pairing_enables_telegram_alerts(isolated_db):
    from app.telegram_pairing import create_pairing_code, consume_pairing_code
    from app.profile import get_or_create_profile as get_profile

    user_id = _new_user("mlro@firm.ae")
    # Before pairing: the default is off.
    assert bool(get_profile(user_id).get("telegram_alerts_enabled")) is False

    code = create_pairing_code(user_id)["code"]
    assert consume_pairing_code(code, "555001", {"username": "mlro"}) == "ok"

    # After pairing: alerts are ON — pairing is the explicit opt-in, and the
    # bot's success message promises exactly this.
    profile = get_profile(user_id)
    assert bool(profile.get("telegram_alerts_enabled")) is True, (
        "pairing must enable telegram alerts — otherwise the paired customer "
        "silently receives nothing while the bot says they will"
    )
    # (chat_id landing is asserted end-to-end by the delivery-list test below.)


def test_paired_user_reaches_the_delivery_list(isolated_db):
    from app.telegram_pairing import (
        create_pairing_code,
        consume_pairing_code,
        get_all_linked_chat_ids,
    )

    user_id = _new_user("cco@vasp.ae")
    code = create_pairing_code(user_id)["code"]
    assert consume_pairing_code(code, "555002", {"username": "cco"}) == "ok"

    # The delivery query filters telegram_alerts_enabled = 1 — a freshly paired
    # user must be included, or alerts never reach them.
    chat_ids = get_all_linked_chat_ids()
    assert "555002" in chat_ids, (
        "a freshly paired user must appear in the alert delivery list"
    )
