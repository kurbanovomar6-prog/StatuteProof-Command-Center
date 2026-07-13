"""`run.py assign-role` — the founder-only door to seat a teammate/auditor.

Regression for the enterprise finding that rbac_runtime.assign_org_role had zero
production callers: the multi-user model was machinery with no door, so teams
could only be created by hand-editing SQLite. This CLI is that door.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.db as app_db  # noqa: E402
from app.auth import create_user  # noqa: E402
import run  # noqa: E402


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "assign.db"))
    return tmp_path


def _owned_org_id(user_id: int) -> int | None:
    from app.db import _connect
    from app.rbac_runtime import ensure_rbac_tables

    conn = _connect()
    try:
        ensure_rbac_tables(conn)
        row = conn.execute("SELECT id FROM orgs WHERE owner_user_id = ?", (user_id,)).fetchone()
        return row["id"] if row else None
    finally:
        conn.close()


def _role_in_org(org_id: int, user_id: int) -> str | None:
    from app.db import _connect

    conn = _connect()
    try:
        row = conn.execute(
            "SELECT role FROM org_members WHERE org_id = ? AND user_id = ?",
            (org_id, user_id),
        ).fetchone()
        return row["role"] if row else None
    finally:
        conn.close()


def test_assign_role_seats_auditor_in_owner_org(isolated_db):
    owner = create_user("owner@x.io", "password-123")
    target = create_user("teammate@x.io", "password-123")
    app_db.backfill_org_memberships()

    with pytest.raises(SystemExit) as ex:
        run._cmd_assign_role(
            ["--owner", str(owner["id"]), "--user", str(target["id"]), "--role", "auditor"]
        )
    assert ex.value.code == 0

    org_id = _owned_org_id(owner["id"])
    assert _role_in_org(org_id, target["id"]) == "auditor"


def test_assign_role_rejects_unknown_role(isolated_db):
    owner = create_user("owner2@x.io", "password-123")
    target = create_user("teammate2@x.io", "password-123")
    app_db.backfill_org_memberships()
    with pytest.raises(SystemExit) as ex:
        run._cmd_assign_role(
            ["--owner", str(owner["id"]), "--user", str(target["id"]), "--role", "superuser"]
        )
    assert ex.value.code == 2


def test_assign_role_requires_all_args(isolated_db):
    with pytest.raises(SystemExit) as ex:
        run._cmd_assign_role(["--owner", "1"])
    assert ex.value.code == 2


def test_assign_role_list_runs(isolated_db, capsys):
    owner = create_user("owner3@x.io", "password-123")
    app_db.backfill_org_memberships()
    with pytest.raises(SystemExit) as ex:
        run._cmd_assign_role(["--list"])
    assert ex.value.code == 0
    out = capsys.readouterr().out
    assert "ROLE" in out or "membership" in out.lower()
