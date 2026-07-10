"""Regression test for the get_or_create_profile INSERT race (G4-api).

Two concurrent first requests for a new user both SELECT (no row), both
INSERT the same user_id PRIMARY KEY; the loser's INSERT raises IntegrityError.
Pre-fix that propagated as an unhandled 500. Post-fix it must return the row
the winner committed.
"""

from __future__ import annotations

import sqlite3
import threading

import app.db as db_module
import app.profile as profile_module
from app.profile import get_or_create_profile


def _fresh_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "race.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    return db_path


def test_get_or_create_profile_survives_concurrent_insert(tmp_path, monkeypatch):
    """A simulated lost INSERT race must return the existing row, not raise."""
    _fresh_db(tmp_path, monkeypatch)
    profile_module.ensure_profile_table()

    # Simulate the winning thread: insert the row first.
    other = get_or_create_profile(42)
    assert other["user_id"] == 42

    # Now force the race window: the SELECT inside get_or_create_profile returns
    # None (as if run before the winner committed), driving the code into the
    # INSERT path where sqlite raises IntegrityError for the duplicate PK.
    real_get = profile_module._get_profile_row
    state = {"first": True}

    def _racy_get(conn, user_id):
        if state["first"]:
            state["first"] = False
            return None  # pretend the winner has not committed yet
        return real_get(conn, user_id)

    monkeypatch.setattr(profile_module, "_get_profile_row", _racy_get)

    # Must not raise IntegrityError; must return the committed row.
    result = get_or_create_profile(42)
    assert result["user_id"] == 42


def test_get_or_create_profile_true_concurrency(tmp_path, monkeypatch):
    """Two real threads racing on the same new user_id: neither may 500."""
    _fresh_db(tmp_path, monkeypatch)
    profile_module.ensure_profile_table()

    barrier = threading.Barrier(2)
    results: list = []
    errors: list = []

    def worker():
        try:
            barrier.wait()
            results.append(get_or_create_profile(77))
        except Exception as exc:  # noqa: BLE001 — we assert none occur
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"concurrent get_or_create_profile raised: {errors}"
    assert len(results) == 2
    assert all(r["user_id"] == 77 for r in results)
