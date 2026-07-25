"""Guessing one account's password must get harder, not just slower from one IP.

`app/api.py:596` keys its limiter on client IP, so an attacker with a pool of
addresses presents a fresh key on every request and the account is unprotected.
Measured 2026-07-25 with tools/measure_security_axis.py: 25 consecutive failures
against a single account left the correct password still accepted.

The two limits are different in kind and both stay — the IP limiter protects the
service from volume, this protects an ACCOUNT from being ground down.

The enumeration property is as important as the lockout itself: a locked account
must answer exactly like a wrong password, and an address that does not exist must
be counted exactly like one that does. Otherwise the defence becomes an oracle for
"which of these emails are customers".
"""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.auth as auth  # noqa: E402
from app.auth import (  # noqa: E402
    LOGIN_MAX_FAILURES,
    clear_failed_logins,
    create_user,
    get_user_by_email,
    is_account_locked,
    record_failed_login,
    verify_password,
)
from app.db import ensure_auth_tables  # noqa: E402

EMAIL = "victim@example.test"
PASSWORD = "correct-horse-battery"


@pytest.fixture()
def account():
    """A real account in the per-test database the autouse fixture provides."""
    ensure_auth_tables()
    return create_user(EMAIL, PASSWORD)


def _sign_in(email: str, password: str) -> bool:
    """The sequence app/api_auth.py performs, minus the HTTP wrapper."""
    if is_account_locked(email):
        return False
    row = get_user_by_email(email)
    ok = bool(row and row.get("is_active") and verify_password(password, row.get("password_hash", "")))
    if ok:
        clear_failed_logins(email)
    else:
        record_failed_login(email)
    return ok


# ── the lockout ─────────────────────────────────────────────────────────────


def test_a_few_wrong_guesses_do_not_lock_the_account(account):
    for _ in range(LOGIN_MAX_FAILURES - 1):
        assert _sign_in(EMAIL, "wrong") is False

    assert _sign_in(EMAIL, PASSWORD) is True


def test_crossing_the_threshold_locks_the_account(account):
    for _ in range(LOGIN_MAX_FAILURES):
        _sign_in(EMAIL, "wrong")

    assert is_account_locked(EMAIL) is True
    # The point of the lock: the CORRECT password stops working too, so an
    # attacker who eventually guesses it still cannot get in.
    assert _sign_in(EMAIL, PASSWORD) is False


def test_a_successful_sign_in_clears_the_counter(account):
    for _ in range(LOGIN_MAX_FAILURES - 1):
        _sign_in(EMAIL, "wrong")
    assert _sign_in(EMAIL, PASSWORD) is True

    # Fresh budget — the near-miss run must not carry over.
    for _ in range(LOGIN_MAX_FAILURES - 1):
        assert _sign_in(EMAIL, "wrong") is False
    assert _sign_in(EMAIL, PASSWORD) is True


def test_failures_older_than_the_window_stop_counting(account, monkeypatch):
    """A slow trickle of typos over days is not an attack in progress."""
    for _ in range(LOGIN_MAX_FAILURES - 1):
        _sign_in(EMAIL, "wrong")

    real_now = auth._now()
    monkeypatch.setattr(auth, "_now", lambda: real_now + timedelta(seconds=auth.LOGIN_FAILURE_WINDOW_S + 60))

    _sign_in(EMAIL, "wrong")  # would be the Nth in-window failure
    assert is_account_locked(EMAIL) is False
    assert _sign_in(EMAIL, PASSWORD) is True


def test_the_lock_expires(account, monkeypatch):
    for _ in range(LOGIN_MAX_FAILURES):
        _sign_in(EMAIL, "wrong")
    assert is_account_locked(EMAIL) is True

    real_now = auth._now()
    monkeypatch.setattr(auth, "_now", lambda: real_now + timedelta(seconds=auth.LOGIN_LOCKOUT_S + 60))

    assert is_account_locked(EMAIL) is False
    assert _sign_in(EMAIL, PASSWORD) is True


# ── it must not become an account-existence oracle ──────────────────────────


def test_an_address_that_does_not_exist_is_counted_the_same_way(account):
    unknown = "nobody@example.test"
    for _ in range(LOGIN_MAX_FAILURES):
        _sign_in(unknown, "wrong")

    assert is_account_locked(unknown) is True, (
        "an unknown address must lock like a real one, or the difference reveals "
        "which addresses are customers"
    )


def test_a_locked_account_and_a_wrong_password_are_indistinguishable(account):
    """Both return the same falsey sign-in result; the handler sends the same 401."""
    assert _sign_in(EMAIL, "wrong") is False
    for _ in range(LOGIN_MAX_FAILURES):
        _sign_in(EMAIL, "wrong")
    assert _sign_in(EMAIL, PASSWORD) is False


# ── failure modes ───────────────────────────────────────────────────────────


def test_storage_trouble_does_not_lock_everyone_out(account, monkeypatch):
    """Failing closed here would turn a broken table into a full outage."""
    def _boom():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(auth, "_connect", _boom)
    assert is_account_locked(EMAIL) is False


def test_recording_a_failure_never_raises(account, monkeypatch):
    """A failed sign-in must not become a 500."""
    def _boom():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(auth, "_connect", _boom)
    record_failed_login(EMAIL)  # must not raise
    clear_failed_logins(EMAIL)  # must not raise


def test_a_blank_email_is_ignored_rather_than_counted(account):
    record_failed_login("")
    assert is_account_locked("") is False
