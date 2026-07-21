"""Lifecycle + fail-closed coverage for app/telegram_pairing.py.

These tests exercise the pairing lifecycle branches (status, consume rejections,
rollback-on-exception, unlink, test-touch, tenancy-scoped delivery lookup) and —
most importantly — the PLAN fail-CLOSED gates that decide who receives the paid
official-source deliverable. The gate tests deliberately drive
``app.plan.has_capability`` into a RAISING state to prove the fail direction:
when eligibility cannot be resolved, the recipient is EXCLUDED (returns []), not
included. A future regression that silently swaps a fail-open default for the
fail-closed one must make one of these tests go red.

Pure-additive: no production code is touched.
"""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    """Point every _connect() at a throwaway SQLite file and clear ambient env."""
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "pairing.db"))
    monkeypatch.delenv("STATUTEPROOF_ALERTS_REQUIRE_PLAN", raising=False)
    monkeypatch.delenv("STATUTEPROOF_ALERT_PLAN_EXEMPT_EMAILS", raising=False)
    yield tmp_path / "pairing.db"


def _make_user(email: str) -> int:
    from app.auth import create_user

    user = create_user(email, "password-123")
    return int(user["id"])


def _pair(user_id: int, chat_id: str, *, username: str = "tester") -> str:
    from app.telegram_pairing import consume_pairing_code, create_pairing_code

    code = create_pairing_code(user_id)["code"]
    return consume_pairing_code(code, chat_id, {"username": username})


# --------------------------------------------------------------------------- #
# get_pairing_status (190-216)
# --------------------------------------------------------------------------- #

def test_status_disconnected_shows_active_code_and_not_connected(isolated_db):
    from app.telegram_pairing import create_pairing_code, get_pairing_status

    uid = _make_user("nostatus@co.com")
    created = create_pairing_code(uid)

    status = get_pairing_status(uid)

    assert status["connected"] is False
    assert status["telegram_chat_id_masked"] is None
    assert status["telegram_username"] is None
    assert status["active_code"] is not None
    assert status["active_code"]["code"] == created["code"]


def test_status_connected_masks_chat_id_after_pairing(isolated_db):
    from app.telegram_pairing import get_pairing_status

    uid = _make_user("connected@co.com")
    assert _pair(uid, "123456789", username="omar") == "ok"

    status = get_pairing_status(uid)

    assert status["connected"] is True
    assert status["telegram_username"] == "omar"
    masked = status["telegram_chat_id_masked"]
    assert masked is not None
    assert masked.endswith("6789")
    assert masked.startswith("*")
    assert "123456789" not in masked
    # A freshly consumed code is no longer active.
    assert status["active_code"] is None


# --------------------------------------------------------------------------- #
# consume_pairing_code rejection branches (223 / 241 / 244 / 246)
# --------------------------------------------------------------------------- #

def test_consume_rejects_malformed_code(isolated_db):
    """Fails the _CODE_RE shape check before any DB lookup (line 223)."""
    from app.telegram_pairing import consume_pairing_code

    assert consume_pairing_code("not-a-real-code", "555") == "invalid"


def test_consume_rejects_wellformed_but_unknown_code(isolated_db):
    """Passes the regex but matches no row -> 'invalid' (line 241)."""
    from app.telegram_pairing import consume_pairing_code

    # ensure the table exists but contains no such code
    _make_user("norow@co.com")
    assert consume_pairing_code("SP-ABCDEF", "555") == "invalid"


def test_consume_rejects_already_used_code(isolated_db):
    """Second /start on a consumed code is rejected (line 244, used_at set)."""
    from app.telegram_pairing import (
        consume_pairing_code,
        create_pairing_code,
    )

    uid = _make_user("reuse@co.com")
    code = create_pairing_code(uid)["code"]
    assert consume_pairing_code(code, "700001") == "ok"
    # Same code, different chat: must NOT re-bind.
    assert consume_pairing_code(code, "700002") == "invalid"


def test_consume_rejects_invalidated_code(isolated_db):
    """A code superseded by a newer create is invalidated (line 244)."""
    from app.telegram_pairing import consume_pairing_code, create_pairing_code

    uid = _make_user("superseded@co.com")
    first = create_pairing_code(uid)["code"]
    second = create_pairing_code(uid)["code"]
    assert first != second
    # Creating the second invalidated the first.
    assert consume_pairing_code(first, "710001") == "invalid"
    # The current code still works.
    assert consume_pairing_code(second, "710002") == "ok"


def test_consume_rejects_expired_code(isolated_db):
    """A code whose expires_at is in the past -> 'expired' (line 246)."""
    from app.telegram_pairing import (
        _iso,
        _now,
        consume_pairing_code,
        create_pairing_code,
    )

    uid = _make_user("expired@co.com")
    code = create_pairing_code(uid)["code"]

    # Age the code out of its TTL directly in storage.
    past = _iso(_now() - timedelta(minutes=1))
    conn = db._connect()
    try:
        conn.execute(
            "UPDATE telegram_pairing_codes SET expires_at = ? WHERE code = ?",
            (past, code),
        )
        conn.commit()
    finally:
        conn.close()

    assert consume_pairing_code(code, "720001") == "expired"


# --------------------------------------------------------------------------- #
# rollback-on-exception inside the transaction (281-284)
# --------------------------------------------------------------------------- #

class _StrOnceThenBoom:
    """Stringifies once (letting the first UPDATE run), then raises.

    The first ``str(chat_id)`` at the used_at UPDATE succeeds; the second one at
    the profile UPDATE raises, forcing the ``except`` branch to roll back the
    open transaction and return 'invalid'.
    """

    def __init__(self, value: str) -> None:
        self.value = value
        self.calls = 0

    def __str__(self) -> str:
        self.calls += 1
        if self.calls >= 2:
            raise RuntimeError("boom stringifying chat_id")
        return self.value


def test_consume_rolls_back_and_returns_invalid_on_exception(isolated_db):
    from app.telegram_pairing import (
        consume_pairing_code,
        create_pairing_code,
        get_pairing_status,
    )

    uid = _make_user("rollback@co.com")
    code = create_pairing_code(uid)["code"]

    boom = _StrOnceThenBoom("730001")
    assert consume_pairing_code(code, boom) == "invalid"
    assert boom.calls >= 2  # proves we reached the second UPDATE and raised

    # Transaction rolled back: profile is NOT connected and the code is still
    # active (its used_at was reverted).
    status = get_pairing_status(uid)
    assert status["connected"] is False
    assert status["active_code"] is not None
    assert status["active_code"]["code"] == code


# --------------------------------------------------------------------------- #
# unlink_telegram (290-321)
# --------------------------------------------------------------------------- #

def test_unlink_clears_profile_and_invalidates_codes(isolated_db):
    from app.telegram_pairing import (
        create_pairing_code,
        get_pairing_status,
        unlink_telegram,
    )

    uid = _make_user("unlink@co.com")
    assert _pair(uid, "800001") == "ok"
    assert get_pairing_status(uid)["connected"] is True

    # A pending (unused) code should be invalidated by unlink.
    pending = create_pairing_code(uid)["code"]

    result = unlink_telegram(uid)

    # unlink returns the fresh (disconnected) status.
    assert result["connected"] is False
    assert result["telegram_chat_id_masked"] is None
    assert result["active_code"] is None

    status = get_pairing_status(uid)
    assert status["connected"] is False

    # The pending code is now dead (invalidated) — cannot be consumed.
    from app.telegram_pairing import consume_pairing_code

    assert consume_pairing_code(pending, "800002") == "invalid"


# --------------------------------------------------------------------------- #
# touch_telegram_test_sent (348-363)
# --------------------------------------------------------------------------- #

def test_touch_records_last_test_timestamp(isolated_db):
    from app.telegram_pairing import (
        get_pairing_status,
        touch_telegram_test_sent,
    )

    uid = _make_user("touch@co.com")
    assert _pair(uid, "810001") == "ok"
    assert get_pairing_status(uid)["last_test_at"] is None

    touch_telegram_test_sent(uid)

    assert get_pairing_status(uid)["last_test_at"] is not None


# --------------------------------------------------------------------------- #
# get_alert_chat_ids_for_user (375-402) — tenancy-scoped delivery route
# --------------------------------------------------------------------------- #

def test_alert_chat_ids_are_scoped_to_the_owning_user(isolated_db):
    from app.telegram_pairing import get_alert_chat_ids_for_user

    owner = _make_user("owner@co.com")
    other = _make_user("other@co.com")
    assert _pair(owner, "820001") == "ok"
    assert _pair(other, "820002") == "ok"

    # Only the owner's chat is returned — never the other tenant's.
    assert get_alert_chat_ids_for_user(owner) == ["820001"]
    assert get_alert_chat_ids_for_user(other) == ["820002"]


def test_alert_chat_ids_empty_when_alerts_disabled(isolated_db):
    from app.profile import update_profile
    from app.telegram_pairing import get_alert_chat_ids_for_user

    uid = _make_user("optout@co.com")
    assert _pair(uid, "830001") == "ok"
    update_profile(uid, {"telegram_alerts_enabled": 0})

    assert get_alert_chat_ids_for_user(uid) == []


def test_alert_chat_ids_returns_empty_on_non_integer_user_id(isolated_db):
    """Bad user_id fails int() and returns [] without raising (375-378)."""
    from app.telegram_pairing import get_alert_chat_ids_for_user

    assert get_alert_chat_ids_for_user("not-an-int") == []
    assert get_alert_chat_ids_for_user(None) == []


# --------------------------------------------------------------------------- #
# filter_plan_eligible_chat_ids — empty input (547) + fail-CLOSED (585-587)
# --------------------------------------------------------------------------- #

def test_filter_chat_ids_empty_input_short_circuits(isolated_db):
    from app.telegram_pairing import filter_plan_eligible_chat_ids

    assert filter_plan_eligible_chat_ids([]) == []


def test_filter_chat_ids_fails_CLOSED_when_capability_lookup_raises(
    isolated_db, monkeypatch
):
    """A resolvable free chat is EXCLUDED (not included) when has_capability
    raises — proving the fail-CLOSED direction (585-587)."""
    import app.plan as plan
    from app.telegram_pairing import filter_plan_eligible_chat_ids

    uid = _make_user("failclosed@co.com")
    assert _pair(uid, "900001") == "ok"

    def _boom(user_id, capability):  # pragma: no cover - body never returns
        raise RuntimeError("capability backend down")

    monkeypatch.setattr(plan, "has_capability", _boom)

    # The chat resolves to a real user_profiles row, so the code path reaches
    # has_capability, which raises -> the whole filter returns [] (fail closed).
    assert filter_plan_eligible_chat_ids(["900001"]) == []


def test_filter_chat_ids_keeps_capable_user(isolated_db, monkeypatch):
    """Sanity twin: with a granting capability the chat IS kept — so the
    fail-closed test above is not vacuously empty."""
    import app.plan as plan
    from app.telegram_pairing import filter_plan_eligible_chat_ids

    uid = _make_user("capable@co.com")
    assert _pair(uid, "900002") == "ok"

    monkeypatch.setattr(plan, "has_capability", lambda user_id, capability: True)

    assert filter_plan_eligible_chat_ids(["900002"]) == ["900002"]


# --------------------------------------------------------------------------- #
# plan_eligible_user_ids — bad-id skip (621-622) + fail-CLOSED (626-628)
# --------------------------------------------------------------------------- #

def test_plan_eligible_user_ids_empty_input(isolated_db):
    from app.telegram_pairing import plan_eligible_user_ids

    assert plan_eligible_user_ids([]) == []


def test_plan_eligible_user_ids_skips_non_integer_ids(isolated_db, monkeypatch):
    """Un-parseable ids are silently skipped; valid capable ids survive
    (621-622)."""
    import app.plan as plan
    from app.telegram_pairing import plan_eligible_user_ids

    monkeypatch.setattr(plan, "has_capability", lambda user_id, capability: True)

    result = plan_eligible_user_ids([42, "not-an-int", None])

    assert result == [42]


def test_plan_eligible_user_ids_fails_CLOSED_when_lookup_raises(
    isolated_db, monkeypatch
):
    """has_capability raising drops everyone -> [] (fail CLOSED, 626-628)."""
    import app.plan as plan
    from app.telegram_pairing import plan_eligible_user_ids

    def _boom(user_id, capability):  # pragma: no cover - body never returns
        raise RuntimeError("capability backend down")

    monkeypatch.setattr(plan, "has_capability", _boom)

    assert plan_eligible_user_ids([42]) == []


# --------------------------------------------------------------------------- #
# _alert_plan_exempt_user_ids — exception path (512-514)
# --------------------------------------------------------------------------- #

def test_exempt_user_ids_empty_env_returns_empty_set(isolated_db):
    from app.telegram_pairing import _alert_plan_exempt_user_ids

    assert _alert_plan_exempt_user_ids() == set()


def test_exempt_user_ids_fails_safe_on_db_error(isolated_db, monkeypatch):
    """A DB failure during the exemption lookup must never crash delivery — it
    returns an empty set (512-514)."""
    import app.telegram_pairing as tp

    monkeypatch.setenv("STATUTEPROOF_ALERT_PLAN_EXEMPT_EMAILS", "op@statuteproof.com")

    def _boom(*args, **kwargs):
        raise RuntimeError("connection refused")

    monkeypatch.setattr(tp, "_connect", _boom)

    assert tp._alert_plan_exempt_user_ids() == set()
