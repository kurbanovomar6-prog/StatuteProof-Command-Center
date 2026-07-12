"""RBAC Stage-1 — tests for the INERT, additive org/role model.

Covers the four Stage-1 building blocks:

1. Schema migration — ``ensure_rbac_tables`` creates ``orgs`` / ``org_members`` /
   ``access_log`` and seeds the GLOBAL org (id 0). Idempotent.
2. Backfill — every existing user becomes the ``owner`` of their org-of-one, and
   re-running inserts nothing (idempotent, safe to re-run).
3. ``app.rbac.can`` — pure, default-deny matrix per role, the SYSTEM principal,
   resource org-scoping, and rejection of unknown roles/actions/inputs.
4. Access log — append works and there is NO update/delete path anywhere in the
   RBAC layer (append-only by construction).
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import access_log as access_log_module
from app import db
from app import rbac
from app.access_log import RESULT_ALLOW, RESULT_DENY, append_access_log, read_access_log
from app.auth import create_user
from app.rbac import (
    ALL_ACTIONS,
    GLOBAL_ORG_ID,
    Principal,
    Resource,
    ROLE_ADMIN,
    ROLE_APPROVER,
    ROLE_AUDITOR,
    ROLE_OWNER,
    ROLE_REVIEWER,
    ROLE_SYSTEM,
    SYSTEM,
    can,
    permissions_for,
)


# ── fixtures ─────────────────────────────────────────────────────────────────────

@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    """Point the whole DB layer at a throwaway SQLite file (see conftest)."""
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "rbac.db"))
    yield tmp_path / "rbac.db"


def _table_names(conn: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }


# ── 1. schema migration ──────────────────────────────────────────────────────────

def test_ensure_rbac_tables_creates_tables_and_global_org(isolated_db):
    db.ensure_rbac_tables()

    conn = db._connect()
    try:
        tables = _table_names(conn)
        assert {"orgs", "org_members", "access_log"} <= tables

        global_org = conn.execute(
            "SELECT id, name, owner_user_id FROM orgs WHERE id = ?",
            (GLOBAL_ORG_ID,),
        ).fetchone()
    finally:
        conn.close()

    assert global_org is not None
    assert global_org["id"] == 0
    assert global_org["name"] == "GLOBAL"
    assert global_org["owner_user_id"] is None


def test_ensure_rbac_tables_is_idempotent(isolated_db):
    db.ensure_rbac_tables()
    db.ensure_rbac_tables()
    db.ensure_rbac_tables()

    conn = db._connect()
    try:
        global_org_count = conn.execute(
            "SELECT COUNT(*) FROM orgs WHERE id = ?", (GLOBAL_ORG_ID,)
        ).fetchone()[0]
    finally:
        conn.close()

    # Re-running must never duplicate the seeded GLOBAL org.
    assert global_org_count == 1


def test_global_org_id_constant_matches_db_module(isolated_db):
    # rbac.py and db.py must agree on the GLOBAL org id or Stage-2 wiring drifts.
    assert rbac.GLOBAL_ORG_ID == db.GLOBAL_ORG_ID == 0


def test_init_db_runs_rbac_migration_and_backfill(isolated_db):
    # init_db() is the once-per-process migration entrypoint (pipeline startup);
    # it must provision the RBAC tables AND backfill existing users as owners.
    user_a = create_user("a@example.com", "password-123")
    user_b = create_user("b@example.com", "password-123")

    db.init_db()

    conn = db._connect()
    try:
        assert {"orgs", "org_members", "access_log"} <= _table_names(conn)
        assert conn.execute(
            "SELECT COUNT(*) FROM orgs WHERE id = 0"
        ).fetchone()[0] == 1
        for user in (user_a, user_b):
            row = conn.execute(
                """
                SELECT m.role
                FROM org_members m
                JOIN orgs o ON o.id = m.org_id
                WHERE m.user_id = ? AND o.owner_user_id = ?
                """,
                (user["id"], user["id"]),
            ).fetchone()
            assert row is not None
            assert row["role"] == ROLE_OWNER
    finally:
        conn.close()


# ── 2. backfill of existing users → org-of-one owner ─────────────────────────────

def test_backfill_makes_existing_user_org_of_one_owner(isolated_db):
    user = create_user("owner@example.com", "password-123")
    # create_user provisions the RBAC tables (via ensure_auth_tables) but does
    # NOT backfill on the request hot path. The backfill is the migration step —
    # run it explicitly here exactly as init_db() does once per process.
    db.backfill_org_memberships()

    conn = db._connect()
    try:
        personal_org = conn.execute(
            "SELECT id, name, owner_user_id FROM orgs WHERE owner_user_id = ?",
            (user["id"],),
        ).fetchone()
        assert personal_org is not None
        assert personal_org["owner_user_id"] == user["id"]

        membership = conn.execute(
            "SELECT org_id, user_id, role FROM org_members WHERE user_id = ?",
            (user["id"],),
        ).fetchall()
    finally:
        conn.close()

    assert len(membership) == 1
    assert membership[0]["org_id"] == personal_org["id"]
    assert membership[0]["role"] == ROLE_OWNER


def test_backfill_covers_all_users_and_is_idempotent(isolated_db):
    ids = [
        create_user(f"user{i}@example.com", "password-123")["id"] for i in range(3)
    ]
    db.backfill_org_memberships()

    def snapshot() -> tuple[int, int, int]:
        conn = db._connect()
        try:
            personal_orgs = conn.execute(
                "SELECT COUNT(*) FROM orgs WHERE owner_user_id IS NOT NULL"
            ).fetchone()[0]
            owner_members = conn.execute(
                "SELECT COUNT(*) FROM org_members WHERE role = 'owner'"
            ).fetchone()[0]
            total_members = conn.execute(
                "SELECT COUNT(*) FROM org_members"
            ).fetchone()[0]
            return personal_orgs, owner_members, total_members
        finally:
            conn.close()

    first = snapshot()
    assert first == (3, 3, 3)  # one personal org + one owner membership per user

    # Re-running the backfill several times must not create duplicates.
    db.backfill_org_memberships()
    db.ensure_rbac_tables()
    db.backfill_org_memberships()
    assert snapshot() == first

    # Every user id ended up with exactly one owner membership.
    conn = db._connect()
    try:
        for uid in ids:
            rows = conn.execute(
                "SELECT role FROM org_members WHERE user_id = ?", (uid,)
            ).fetchall()
            assert [r["role"] for r in rows] == [ROLE_OWNER]
    finally:
        conn.close()


def test_org_member_unique_constraint(isolated_db):
    user = create_user("dupe@example.com", "password-123")
    db.backfill_org_memberships()

    conn = db._connect()
    try:
        org_id = conn.execute(
            "SELECT id FROM orgs WHERE owner_user_id = ?", (user["id"],)
        ).fetchone()["id"]
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO org_members (org_id, user_id, role, created_at) "
                "VALUES (?, ?, 'admin', '2026-01-01T00:00:00+00:00')",
                (org_id, user["id"]),
            )
    finally:
        conn.close()


# ── 3. can() — pure, default-deny matrix ─────────────────────────────────────────

def _principal(role: str, org_id: int | None = 5) -> Principal:
    return Principal(user_id=1, org_id=org_id, role=role)


def test_can_denies_unknown_action_for_every_role():
    for role in (ROLE_OWNER, ROLE_ADMIN, ROLE_REVIEWER, ROLE_APPROVER, ROLE_AUDITOR):
        assert can(_principal(role), "evidence.nuke") is False
        assert can(_principal(role), "not.an.action") is False
        assert can(_principal(role), "") is False


def test_can_denies_unknown_role():
    ghost = Principal(user_id=1, org_id=5, role="superuser")
    assert can(ghost, "evidence.view") is False
    assert can(ghost, "evidence.export") is False
    assert permissions_for("superuser") == frozenset()


def test_can_denies_non_principal_input():
    assert can(None, "evidence.view") is False
    assert can({"role": "owner"}, "evidence.view") is False
    assert can("owner", "evidence.view") is False


def test_can_never_raises_on_unhashable_inputs():
    # A caller that mis-types role/action (e.g. a list) must DENY, not raise —
    # the "never raises for bad input" contract, defensive for Stage-2 callers.
    bad_role = Principal(user_id=1, org_id=5, role=["admin"])  # type: ignore[arg-type]
    assert can(bad_role, "evidence.view") is False
    assert can(_principal(ROLE_OWNER), ["evidence.view"]) is False  # type: ignore[arg-type]


def test_assignable_roles_excludes_system():
    # ``system`` is a machine identity, never a human-assignable membership seat.
    assert rbac.ASSIGNABLE_ROLES == frozenset(
        {ROLE_OWNER, ROLE_ADMIN, ROLE_REVIEWER, ROLE_APPROVER, ROLE_AUDITOR}
    )
    assert ROLE_SYSTEM not in rbac.ASSIGNABLE_ROLES


def test_owner_has_full_matrix():
    owner = _principal(ROLE_OWNER)
    for action in ALL_ACTIONS:
        assert can(owner, action) is True, f"owner should be granted {action}"


def test_admin_is_broad_but_not_member_manage():
    admin = _principal(ROLE_ADMIN)
    assert can(admin, "member.manage") is False
    for action in ALL_ACTIONS - {"member.manage"}:
        assert can(admin, action) is True, f"admin should be granted {action}"


def test_reviewer_can_review_but_not_approve_or_send():
    reviewer = _principal(ROLE_REVIEWER)
    assert can(reviewer, "evidence.view") is True
    assert can(reviewer, "evidence.export") is True
    assert can(reviewer, "review.view") is True
    assert can(reviewer, "review.submit") is True
    assert can(reviewer, "member.view") is True  # baseline read surface
    # Denied: approval, dispatch, and any mutation.
    assert can(reviewer, "review.approve") is False
    assert can(reviewer, "alert.send") is False
    assert can(reviewer, "source.edit") is False
    assert can(reviewer, "settings.edit") is False
    assert can(reviewer, "member.manage") is False


def test_approver_can_approve_and_send():
    approver = _principal(ROLE_APPROVER)
    assert can(approver, "review.approve") is True
    assert can(approver, "review.submit") is True
    assert can(approver, "alert.send") is True
    assert can(approver, "evidence.export") is True
    assert can(approver, "member.view") is True  # baseline read surface
    # Still not a config mutator.
    assert can(approver, "source.edit") is False
    assert can(approver, "settings.edit") is False
    assert can(approver, "member.manage") is False


def test_auditor_is_read_and_export_only():
    auditor = _principal(ROLE_AUDITOR)
    # Allowed: view everything + export evidence.
    assert can(auditor, "evidence.view") is True
    assert can(auditor, "evidence.export") is True
    assert can(auditor, "review.view") is True
    assert can(auditor, "alert.view") is True
    assert can(auditor, "source.view") is True
    assert can(auditor, "settings.view") is True
    assert can(auditor, "member.view") is True
    # Denied: every mutating / decisioning action.
    assert can(auditor, "review.approve") is False
    assert can(auditor, "review.submit") is False
    assert can(auditor, "alert.send") is False
    assert can(auditor, "source.edit") is False
    assert can(auditor, "settings.edit") is False
    assert can(auditor, "member.manage") is False
    assert can(auditor, "evidence.capture") is False


def test_system_principal_grants():
    # The SYSTEM constant is the machine identity used by the pipeline.
    assert SYSTEM.role == ROLE_SYSTEM
    assert SYSTEM.user_id is None
    assert SYSTEM.org_id == GLOBAL_ORG_ID

    # It can do the automated pipeline work…
    assert can(SYSTEM, "evidence.capture") is True
    assert can(SYSTEM, "evidence.view") is True
    assert can(SYSTEM, "alert.send") is True
    assert can(SYSTEM, "source.view") is True
    # …but must NEVER self-approve the human review gate or mutate config.
    assert can(SYSTEM, "review.approve") is False
    assert can(SYSTEM, "source.edit") is False
    assert can(SYSTEM, "settings.edit") is False
    assert can(SYSTEM, "member.manage") is False


def test_resource_org_scoping():
    owner_in_5 = Principal(user_id=1, org_id=5, role=ROLE_OWNER)

    same_org = Resource(resource_type="evidence", resource_id="e1", org_id=5)
    other_org = Resource(resource_type="evidence", resource_id="e2", org_id=6)
    no_org = Resource(resource_type="evidence", resource_id="e3")

    # Same org → allowed; other org → denied even for an owner.
    assert can(owner_in_5, "evidence.view", same_org) is True
    assert can(owner_in_5, "evidence.view", other_org) is False
    # No org on the resource → no scoping constraint applies.
    assert can(owner_in_5, "evidence.view", no_org) is True


def test_global_org_and_system_are_cross_org():
    other_org = Resource(resource_type="evidence", resource_id="e", org_id=99)

    operator = Principal(user_id=1, org_id=GLOBAL_ORG_ID, role=ROLE_OWNER)
    assert can(operator, "evidence.view", other_org) is True

    # SYSTEM acts across every org.
    assert can(SYSTEM, "evidence.view", other_org) is True


def test_scoping_never_upgrades_a_denied_action():
    # Ownership scope only ever ADDS a denial; it cannot grant an ungranted action.
    auditor_global = Principal(user_id=1, org_id=GLOBAL_ORG_ID, role=ROLE_AUDITOR)
    resource = Resource(resource_type="review", resource_id="r", org_id=GLOBAL_ORG_ID)
    assert can(auditor_global, "review.approve", resource) is False


# ── 4. access log — append-only by construction ──────────────────────────────────

def test_append_access_log_writes_row(isolated_db):
    row_id = append_access_log(
        actor_user_id=7,
        org_id=3,
        action="evidence.export",
        result=RESULT_ALLOW,
        resource_type="evidence",
        resource_id="rec-1",
    )
    assert row_id > 0

    rows = read_access_log()
    assert len(rows) == 1
    row = rows[0]
    assert row["actor_user_id"] == 7
    assert row["org_id"] == 3
    assert row["action"] == "evidence.export"
    assert row["result"] == RESULT_ALLOW
    assert row["resource_type"] == "evidence"
    assert row["resource_id"] == "rec-1"
    assert row["ts"]


def test_append_access_log_allows_system_actor(isolated_db):
    # SYSTEM has no user id — the log must accept a NULL actor.
    row_id = append_access_log(
        actor_user_id=None,
        org_id=None,
        action="alert.send",
        result=RESULT_DENY,
    )
    assert row_id > 0
    row = read_access_log()[0]
    assert row["actor_user_id"] is None
    assert row["org_id"] is None
    assert row["resource_type"] == ""
    assert row["resource_id"] == ""


def test_access_log_is_append_only_accumulates(isolated_db):
    for i in range(5):
        append_access_log(
            actor_user_id=i, org_id=1, action="evidence.view", result=RESULT_ALLOW
        )
    assert len(read_access_log()) == 5

    conn = db._connect()
    try:
        total = conn.execute("SELECT COUNT(*) FROM access_log").fetchone()[0]
    finally:
        conn.close()
    assert total == 5


def test_access_log_update_and_delete_are_blocked_by_trigger(isolated_db):
    """Immutability is enforced at the DB layer, not just by omitting helpers.

    Even a direct writer on its own connection cannot mutate or erase a row —
    the BEFORE UPDATE / BEFORE DELETE triggers RAISE(ABORT).
    """
    append_access_log(
        actor_user_id=1, org_id=1, action="evidence.view", result=RESULT_ALLOW
    )

    conn = db._connect()
    try:
        with pytest.raises(sqlite3.Error):
            conn.execute("UPDATE access_log SET result = 'deny' WHERE id = 1")
        conn.rollback()
        with pytest.raises(sqlite3.Error):
            conn.execute("DELETE FROM access_log WHERE id = 1")
        conn.rollback()
        # The row survived both attempts, unchanged.
        row = conn.execute("SELECT result FROM access_log WHERE id = 1").fetchone()
        assert row is not None
        assert row["result"] == RESULT_ALLOW
    finally:
        conn.close()


def test_no_update_or_delete_path_in_rbac_layer():
    """There must be NO code path that mutates or deletes an access-log row.

    Append-only is a structural guarantee (DB triggers +
    ``test_access_log_update_and_delete_are_blocked_by_trigger``). This adds a
    source-level tripwire: the writer modules expose no mutation helper and carry
    no UPDATE/DELETE statement against access_log. Whitespace is normalised so a
    reformatted multi-line statement cannot slip past the substring check.
    """
    # (a) No mutation function is exported from the access-log module.
    suspicious = [
        name
        for name in dir(access_log_module)
        if any(word in name.lower() for word in ("update", "delete", "clear", "purge", "drop"))
    ]
    assert suspicious == [], f"unexpected mutation helpers: {suspicious}"

    # (b) No UPDATE/DELETE statement targets access_log in the writer modules.
    #     (db.py legitimately references it in the *protective* triggers, so it is
    #     intentionally out of scope here.)
    for module_path in ("app/access_log.py", "app/rbac.py", "app/rbac_runtime.py", "app/api.py"):
        raw = (Path(__file__).resolve().parent.parent / module_path).read_text().lower()
        source = " ".join(raw.split())
        assert "update access_log" not in source
        assert "delete from access_log" not in source


def test_api_routes_rbac_only_through_the_runtime_bridge():
    """Architectural guardrail — UPDATED for Stage-2 (was Stage-1 inertness check).

    Stage-1 asserted RBAC was wired into NO live request path. Stage-2 makes RBAC
    LIVE, so that premise no longer holds. The invariant that remains — and that
    this test now enforces — is that ``app/api.py`` reaches RBAC ONLY through the
    single ``app.rbac_runtime`` bridge, never into ``app.rbac`` or
    ``app.access_log`` directly. That keeps one testable choke point for principal
    resolution, the role gate, and audit logging.

    (See ``tests/test_rbac_stage2.py`` for the behavioural Stage-2 coverage:
    access-log writes on sensitive actions, owner no-regression, and auditor
    denial.)
    """
    api_source = (Path(__file__).resolve().parent.parent / "app/api.py").read_text()
    # api.py must NOT touch the RBAC internals directly — everything goes through
    # the rbac_runtime bridge.
    assert "append_access_log" not in api_source
    assert "app.access_log" not in api_source
    assert "from app.rbac import" not in api_source
    assert "rbac.can(" not in api_source
    # …and it MUST use the bridge (proof Stage-2 is actually wired in).
    assert "import rbac_runtime" in api_source
    assert "rbac_runtime.EVIDENCE_EXPORT" in api_source
    assert "_rbac_guard" in api_source
