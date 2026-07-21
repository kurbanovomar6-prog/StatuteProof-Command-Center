"""Fail-closed coverage for app/user_delivery.py.

These tests pin the plan-eligibility delivery gate
(``is_user_delivery_eligible``) and the user-triggered sample-brief send
(``send_sample_brief_to_user``) so a future regression fails loudly:

* the gate must refuse delivery unless Telegram is connected AND onboarding
  is complete AND Telegram alerts are enabled (each refusal has its own
  human-readable reason);
* a second same-day sample brief must be idempotent — the row is keyed
  ``{uid}:sample_brief:{today}`` and INSERT OR IGNORE makes the second
  attempt a no-op, so Telegram is never messaged twice; and
* when the Telegram send fails, the delivery-log row must be flipped to
  ``failed`` (not left ``pending``) and the caller told it failed.

The DB is isolated per test by monkeypatching ``app.db.DB_PATH`` (the same
binding ``app.db._connect`` reads). Eligibility state is built through the
real pairing + profile code paths — not by stubbing the gate — so the tests
exercise the branches they assert on.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db
from app import user_delivery


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "user_delivery.db"))
    yield tmp_path / "user_delivery.db"


def _new_user(email: str) -> int:
    from app.auth import create_user

    return int(create_user(email, "password-123")["id"])


def _pair(user_id: int, chat_id: str) -> None:
    """Drive the real pairing path so a genuine telegram_chat_id lands and
    telegram_alerts_enabled is flipped on (pairing is the opt-in)."""
    from app.telegram_pairing import create_pairing_code, consume_pairing_code

    code = create_pairing_code(user_id)["code"]
    assert consume_pairing_code(code, chat_id, {"username": "u"}) == "ok"


def _complete_onboarding(user_id: int) -> None:
    from app.profile import update_profile

    update_profile(user_id, {"onboarding_completed": 1})


class _RecordingSender:
    """Stand-in for send_telegram_message that records every call and returns
    a configurable outcome (True/False), or raises if told to."""

    def __init__(self, result=True, raise_exc=None):
        self.result = result
        self.raise_exc = raise_exc
        self.calls: list[tuple[str, str]] = []

    def __call__(self, chat_id, text, parse_mode=None):
        self.calls.append((str(chat_id), str(text)))
        if self.raise_exc is not None:
            raise self.raise_exc
        return self.result


# --------------------------------------------------------------------------
# is_user_delivery_eligible — the plan-eligibility delivery gate (34-45)
# --------------------------------------------------------------------------


def test_eligible_when_paired_onboarded_and_alerts_enabled(isolated_db):
    user_id = _new_user("ready@firm.ae")
    _pair(user_id, "700001")
    _complete_onboarding(user_id)

    eligible, reason, context = user_delivery.is_user_delivery_eligible(user_id)

    assert eligible is True
    assert reason == "ok"
    # The context must carry the real link + profile the gate inspected.
    assert context["link"].get("telegram_chat_id") == "700001"
    assert context["profile"].get("onboarding_completed") is True


def test_not_eligible_when_telegram_not_connected(isolated_db):
    # No pairing at all -> the link has no chat_id -> first gate fails closed.
    user_id = _new_user("nolink@firm.ae")

    eligible, reason, _ = user_delivery.is_user_delivery_eligible(user_id)

    assert eligible is False
    assert reason == "Telegram not connected."


def test_not_eligible_when_onboarding_incomplete(isolated_db):
    # Paired (chat_id + alerts on) but onboarding never completed.
    user_id = _new_user("halfway@firm.ae")
    _pair(user_id, "700002")

    eligible, reason, _ = user_delivery.is_user_delivery_eligible(user_id)

    assert eligible is False
    assert reason == "Onboarding is not complete."


def test_not_eligible_when_alerts_disabled(isolated_db):
    from app.profile import update_profile

    user_id = _new_user("optedout@firm.ae")
    _pair(user_id, "700003")
    _complete_onboarding(user_id)
    # Explicitly disable alerts after pairing turned them on.
    update_profile(user_id, {"telegram_alerts_enabled": 0})

    eligible, reason, _ = user_delivery.is_user_delivery_eligible(user_id)

    assert eligible is False
    assert reason == "Telegram alerts are disabled."


# --------------------------------------------------------------------------
# send_sample_brief_to_user — gate refusal, success, idempotency, failure
# --------------------------------------------------------------------------


def test_send_sample_brief_refused_when_not_eligible(isolated_db, monkeypatch):
    # An ineligible user must never reach the sender.
    sender = _RecordingSender(result=True)
    monkeypatch.setattr(user_delivery, "send_telegram_message", sender)

    user_id = _new_user("blocked@firm.ae")  # never paired

    out = user_delivery.send_sample_brief_to_user(user_id)

    assert out["ok"] is False
    assert out["reason"] == "Telegram not connected."
    assert sender.calls == [], "sender must not be called for an ineligible user"


def test_send_sample_brief_success_marks_log_sent(isolated_db, monkeypatch):
    sender = _RecordingSender(result=True)
    monkeypatch.setattr(user_delivery, "send_telegram_message", sender)

    user_id = _new_user("go@firm.ae")
    _pair(user_id, "700010")
    _complete_onboarding(user_id)

    out = user_delivery.send_sample_brief_to_user(user_id)

    assert out["ok"] is True
    assert "log_id" in out
    # The real chat_id from pairing was used, and the SAMPLE/FAKE label is
    # present so an invented-content brief can never pass as a real change.
    assert len(sender.calls) == 1
    sent_chat_id, sent_text = sender.calls[0]
    assert sent_chat_id == "700010"
    assert "SAMPLE / FAKE" in sent_text

    logs = user_delivery.get_user_delivery_logs(user_id)
    assert len(logs) == 1
    assert logs[0]["status"] == "sent"
    assert logs[0]["delivery_type"] == "sample_brief"


def test_second_same_day_sample_brief_is_idempotent(isolated_db, monkeypatch):
    sender = _RecordingSender(result=True)
    monkeypatch.setattr(user_delivery, "send_telegram_message", sender)

    user_id = _new_user("twice@firm.ae")
    _pair(user_id, "700011")
    _complete_onboarding(user_id)

    first = user_delivery.send_sample_brief_to_user(user_id)
    second = user_delivery.send_sample_brief_to_user(user_id)

    assert first["ok"] is True
    # The idempotency key {uid}:sample_brief:{today} makes the second insert a
    # no-op (created=False) -> the caller is told it was already sent and the
    # sender is NOT invoked a second time.
    assert second["ok"] is False
    assert second["reason"] == "Sample brief already sent today."
    assert len(sender.calls) == 1, "same-day resend must not message Telegram again"

    # Exactly one log row exists (the duplicate was ignored).
    logs = user_delivery.get_user_delivery_logs(user_id)
    assert len(logs) == 1
    assert logs[0]["status"] == "sent"


def test_send_failure_marks_log_failed(isolated_db, monkeypatch):
    # send returns falsy -> failure branch (241-242) must flip the row to
    # 'failed' rather than leaving a 'pending' row that looks delivered.
    sender = _RecordingSender(result=False)
    monkeypatch.setattr(user_delivery, "send_telegram_message", sender)

    user_id = _new_user("fail@firm.ae")
    _pair(user_id, "700012")
    _complete_onboarding(user_id)

    out = user_delivery.send_sample_brief_to_user(user_id)

    assert out["ok"] is False
    assert out["reason"] == "Telegram send failed."
    assert "log_id" in out
    assert len(sender.calls) == 1

    logs = user_delivery.get_user_delivery_logs(user_id)
    assert len(logs) == 1
    assert logs[0]["status"] == "failed", (
        "a failed Telegram send must leave the log at 'failed', not 'pending'"
    )
    assert logs[0]["error_message"] == "Telegram send failed."


def test_raising_sender_propagates_and_leaves_row_pending(isolated_db, monkeypatch):
    # send_sample_brief_to_user does NOT wrap the send in try/except, so an
    # exception from the transport propagates and the row is left 'pending'
    # (the False-return path is the only one that marks it 'failed'). This pins
    # that observable behavior; see residual_risk.
    sender = _RecordingSender(raise_exc=RuntimeError("boom"))
    monkeypatch.setattr(user_delivery, "send_telegram_message", sender)

    user_id = _new_user("raise@firm.ae")
    _pair(user_id, "700013")
    _complete_onboarding(user_id)

    with pytest.raises(RuntimeError):
        user_delivery.send_sample_brief_to_user(user_id)

    logs = user_delivery.get_user_delivery_logs(user_id)
    assert len(logs) == 1
    assert logs[0]["status"] == "pending"
