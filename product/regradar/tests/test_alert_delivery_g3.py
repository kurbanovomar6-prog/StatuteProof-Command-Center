"""G3 alerts-group bugs (delivery + routing).

Covers three confirmed live defects:

1. Customer alert delivery dead: telegram.py imported a non-existent
   get_all_linked_chat_ids from telegram_pairing, so
   _deliver_alert_to_subscribed_users always returned 0.

2. REVIEW-grade drafts silently relabeled MEDIUM by _normalize_risk_level and
   then scored as deliverable.

3. Failed preview alert could never be retried: create_delivery_log
   INSERT OR IGNORE found the existing idempotency row (left at 'failed') and
   returned "already sent", while the readiness check reported it ready.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "g3.db"))
    yield tmp_path / "g3.db"


def _make_paired_user(email: str, chat_id: str, *, alerts_enabled: bool = True) -> int:
    """Create a user, pair a Telegram chat, and set the alerts flag."""
    from app.auth import create_user
    from app.telegram_pairing import create_pairing_code, consume_pairing_code
    from app.profile import update_profile

    user = create_user(email, "password-123")
    user_id = int(user["id"])
    code = create_pairing_code(user_id)["code"]
    result = consume_pairing_code(code, chat_id, {"username": "tester"})
    assert result == "ok"
    update_profile(user_id, {"telegram_alerts_enabled": 1 if alerts_enabled else 0})
    return user_id


# ---------------------------------------------------------------------------
# Bug 2: get_all_linked_chat_ids exists and drives customer delivery
# ---------------------------------------------------------------------------

def test_get_all_linked_chat_ids_returns_paired_enabled_users(isolated_db):
    from app.telegram_pairing import get_all_linked_chat_ids

    _make_paired_user("a@co.com", "111111", alerts_enabled=True)
    _make_paired_user("b@co.com", "222222", alerts_enabled=True)
    # opted out of telegram alerts -> excluded
    _make_paired_user("c@co.com", "333333", alerts_enabled=False)

    chat_ids = get_all_linked_chat_ids()
    assert set(chat_ids) == {"111111", "222222"}


def test_deliver_alert_reaches_subscribed_users(isolated_db, monkeypatch):
    # Pre-fix: the import of get_all_linked_chat_ids raised ImportError, the
    # broad except swallowed it, and this returned 0 (no user ever reached).
    import app.telegram as tg

    _make_paired_user("d@co.com", "444444", alerts_enabled=True)
    _make_paired_user("e@co.com", "555555", alerts_enabled=True)

    sent_to: list[str] = []

    def _fake_send(chat_id: str, text: str) -> bool:
        sent_to.append(str(chat_id))
        return True

    monkeypatch.setattr(tg, "send_telegram_message", _fake_send)

    reached = tg._deliver_alert_to_subscribed_users("hello")
    assert reached == 2
    assert set(sent_to) == {"444444", "555555"}


# ---------------------------------------------------------------------------
# Bug 4: REVIEW must not be relabeled MEDIUM and must not be deliverable
# ---------------------------------------------------------------------------

def test_normalize_risk_level_preserves_review():
    from app.alert_routing import _normalize_risk_level

    assert _normalize_risk_level("REVIEW") == "REVIEW"
    # canonical levels unchanged; genuine garbage still defaults to MEDIUM
    assert _normalize_risk_level("low") == "LOW"
    assert _normalize_risk_level("HIGH") == "HIGH"
    assert _normalize_risk_level("weird") == "MEDIUM"


def test_review_draft_is_not_scored_deliverable():
    from app.alert_routing import normalize_alert_for_routing, score_alert_for_user

    review_alert = {
        "risk_level": "REVIEW",
        "source_name": "DFSA",
        "market": "AE",
        "jurisdiction": "AE",
        "topics": ["aml"],
        "url": "https://example.ae/x",
        "source_url": "https://example.ae/x",
        "alert_id": "draft-review-1",
    }
    normalized = normalize_alert_for_routing(review_alert)
    assert normalized["risk_level"] == "REVIEW"

    profile = {
        "markets": ["UAE"],
        "industries": [],
        "topics": ["aml"],
        "custom_sources": [],
        "alert_threshold": "MEDIUM",
        "regulators": [],
    }
    result = score_alert_for_user(profile, normalized)
    assert result["matched"] is False
    assert result["score"] == 0

    # Sanity: the same draft at MEDIUM is deliverable (proves the exclusion
    # is REVIEW-specific, not a blanket break of the scorer).
    medium = dict(normalized, risk_level="MEDIUM")
    med_result = score_alert_for_user(profile, medium)
    assert med_result["matched"] is True


# ---------------------------------------------------------------------------
# Bug 3: a failed preview alert can be retried
# ---------------------------------------------------------------------------

def test_reclaim_failed_delivery_log_only_recovers_failed_rows(isolated_db):
    from app.user_delivery import (
        create_delivery_log,
        reclaim_failed_delivery_log,
        update_delivery_log_failed,
        update_delivery_log_sent,
    )
    from app.auth import create_user

    user_id = int(create_user("f@co.com", "password-123")["id"])
    key = f"{user_id}:reviewed_alert_preview:alert-A"

    log = create_delivery_log(
        user_id,
        delivery_type="reviewed_alert_preview",
        idempotency_key=key,
    )
    assert log["created"] is True
    log_id = int(log["id"])

    # A duplicate INSERT is ignored (idempotency), and while the row is
    # pending/sent it is NOT reclaimable.
    dup = create_delivery_log(user_id, delivery_type="reviewed_alert_preview", idempotency_key=key)
    assert dup["created"] is False
    assert reclaim_failed_delivery_log(key) is None

    update_delivery_log_sent(log_id)
    assert reclaim_failed_delivery_log(key) is None  # sent stays sent

    # Now mark it failed -> it becomes reclaimable exactly once.
    update_delivery_log_failed(log_id, "transient network error")
    reclaimed = reclaim_failed_delivery_log(key)
    assert reclaimed == log_id
    # After reclaim it is pending again -> no longer reclaimable.
    assert reclaim_failed_delivery_log(key) is None


def test_send_preview_alert_retries_after_failed_send(isolated_db, monkeypatch):
    import app.alert_routing as ar
    from app.user_delivery import get_user_delivery_logs

    user_id = _make_paired_user("g@co.com", "666666", alerts_enabled=True)
    # onboarding must be complete for delivery readiness
    from app.profile import update_profile
    update_profile(user_id, {"onboarding_completed": 1})

    alert_id = "reviewed-alert-1"
    match = {
        "alert_id": alert_id,
        "source_id": "AE-1",
        "source_name": "DFSA",
        "source_url": "https://example.ae/x",
        "url": "https://example.ae/x",
        "title": "Reviewed alert",
        "risk_level": "MEDIUM",
        "change_type": "REGULATORY_UPDATE",
        "market": "AE",
        "jurisdiction": "AE",
        "topics": ["aml"],
        "executive_summary": "Something changed.",
        "business_action": "",
        "affected_entities": [],
        "review_status": "APPROVED_FOR_URGENT",
        "limitations": [],
        "score": 85,
        "matched": True,
        "delivery_ready": True,
        "reviewed_at": "2026-07-10T00:00:00+00:00",
    }

    # Force the routing preview to yield our ready match, and keep the
    # still-approved gate green.
    monkeypatch.setattr(
        ar,
        "build_routing_preview_for_user",
        lambda uid, days=14: {"matches": [dict(match)]},
    )
    monkeypatch.setattr(ar, "_is_still_approved", lambda aid: True)

    # First attempt: Telegram send fails.
    monkeypatch.setattr(ar, "send_telegram_message", lambda chat_id, text: False)
    first = ar.send_preview_alert_to_user(user_id, alert_id)
    assert first["ok"] is False
    assert first["code"] == "telegram_failed"

    # Second attempt: Telegram now succeeds. Pre-fix this returned the
    # "already sent" duplicate error and never delivered.
    sent: list[str] = []

    def _ok(chat_id, text):
        sent.append(str(chat_id))
        return True

    monkeypatch.setattr(ar, "send_telegram_message", _ok)
    second = ar.send_preview_alert_to_user(user_id, alert_id)
    assert second["ok"] is True
    assert sent == ["666666"]

    # Exactly one delivery-log row for this alert, now marked sent.
    logs = [row for row in get_user_delivery_logs(user_id, limit=50)
            if row["delivery_type"] == "reviewed_alert_preview"]
    assert len(logs) == 1
    assert logs[0]["status"] == "sent"


# ── WARN-7: a raising send must mark the row failed (reclaimable), not stuck ──

def test_send_preview_alert_marks_failed_when_send_raises(isolated_db, monkeypatch):
    """If send_telegram_message RAISES, the freshly-'pending' row must be flipped
    to 'failed' (reclaimable) and the exception re-raised — never left stuck at
    'pending', which reclaim_failed_delivery_log cannot recover.
    """
    import app.alert_routing as ar
    from app.user_delivery import get_user_delivery_logs

    user_id = _make_paired_user("raise@co.com", "777777", alerts_enabled=True)
    from app.profile import update_profile
    update_profile(user_id, {"onboarding_completed": 1})

    alert_id = "reviewed-alert-raise"
    match = {
        "alert_id": alert_id,
        "source_id": "AE-1",
        "source_name": "DFSA",
        "source_url": "https://example.ae/x",
        "url": "https://example.ae/x",
        "title": "Raising alert",
        "risk_level": "MEDIUM",
        "change_type": "REGULATORY_UPDATE",
        "market": "AE",
        "jurisdiction": "AE",
        "topics": ["aml"],
        "executive_summary": "Something changed.",
        "business_action": "",
        "affected_entities": [],
        "review_status": "APPROVED_FOR_URGENT",
        "limitations": [],
        "score": 85,
        "matched": True,
        "delivery_ready": True,
        "reviewed_at": "2026-07-10T00:00:00+00:00",
    }
    monkeypatch.setattr(
        ar,
        "build_routing_preview_for_user",
        lambda uid, days=14: {"matches": [dict(match)]},
    )
    monkeypatch.setattr(ar, "_is_still_approved", lambda aid: True)

    # The send raises an unexpected exception.
    def _boom(chat_id, text):
        raise RuntimeError("telegram client blew up")

    monkeypatch.setattr(ar, "send_telegram_message", _boom)
    with pytest.raises(RuntimeError):
        ar.send_preview_alert_to_user(user_id, alert_id)

    # The row must be 'failed' (reclaimable), NOT stuck at 'pending'.
    logs = [row for row in get_user_delivery_logs(user_id, limit=50)
            if row["delivery_type"] == "reviewed_alert_preview"]
    assert len(logs) == 1
    assert logs[0]["status"] == "failed"

    # And because it is failed, a genuine retry with a working send re-delivers.
    sent: list[str] = []

    def _ok(chat_id, text):
        sent.append(str(chat_id))
        return True

    monkeypatch.setattr(ar, "send_telegram_message", _ok)
    retry = ar.send_preview_alert_to_user(user_id, alert_id)
    assert retry["ok"] is True
    assert sent == ["777777"]
    logs2 = [row for row in get_user_delivery_logs(user_id, limit=50)
             if row["delivery_type"] == "reviewed_alert_preview"]
    assert len(logs2) == 1
    assert logs2[0]["status"] == "sent"
