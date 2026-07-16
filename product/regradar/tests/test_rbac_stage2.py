"""RBAC Stage-2 — the LIVE wiring: principal resolution, immutable audit logging,
owner no-regression, and auditor read-only enforcement.

Stage-1 (``tests/test_rbac.py``) proved the INERT foundation. This suite proves
Stage-2 makes it live WITHOUT changing anything for existing users:

1. Principal resolution — an existing (backfilled) user resolves to ``owner`` of
   their org-of-one; a user with no membership fails SAFE to ``owner``.
2. Audit logging — the sensitive actions (evidence export, review approve, alert
   send, source edit) each append an immutable ``access_log`` row; a logging
   FAILURE does NOT break the action.
3. No regression — an ``owner`` (the only role in live data today) passes every
   mutating endpoint gate, exactly as before Stage-2.
4. Auditor enforcement — an ``auditor`` principal is DENIED a mutation (403) but
   ALLOWED evidence view/export.
5. Membership management — assigning the ``auditor`` role is owner-gated via
   ``can(member.manage)`` (and org-scoped).

Everything runs against a REAL throwaway SQLite DB and the REAL HTTP handler
(``app.api._Handler``), reusing the handler-harness pattern from
``tests/test_export_authz_limits.py``.
"""
from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api as api
import app.db as app_db
import app.rbac_runtime as rbac_runtime
from app import rbac
from app.access_log import read_access_log
from app.api import _Handler
from app.auth import create_user
from app.rbac import (
    EVIDENCE_EXPORT,
    EVIDENCE_VIEW,
    Principal,
    ROLE_AUDITOR,
    ROLE_DENIED,
    ROLE_OWNER,
    SOURCE_EDIT,
    can,
)


# ── fixtures & harness ───────────────────────────────────────────────────────────

@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    """Point the whole DB layer (auth, rbac_runtime, access_log) at a temp file.

    Every module resolves its connection through ``app.db._connect`` → ``db.DB_PATH``,
    so this single monkeypatch isolates users, org_members, and access_log.
    """
    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "rbac_stage2.db"))
    return tmp_path / "rbac_stage2.db"


def _make_handler(method: str = "POST", path: str = "/", *, real_ip: str = "10.0.0.5") -> _Handler:
    header_map = {"Content-Length": "0", "X-Real-IP": real_ip}
    handler = _Handler.__new__(_Handler)
    handler.command = method
    handler.path = path
    handler.request = MagicMock()
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(b"")
    handler.wfile = BytesIO()
    handler.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": header_map.get(key, default)
    handler.headers = hdrs

    sent: list[tuple[dict, int]] = []
    handler._send_json = lambda data, status=200, **kw: sent.append((data, status))  # type: ignore[method-assign]
    handler._sent = sent  # type: ignore[attr-defined]
    return handler


def _statuses(handler: _Handler) -> list[int]:
    return [s for _, s in handler._sent]  # type: ignore[attr-defined]


def _auth_as(monkeypatch, user: dict) -> None:
    monkeypatch.setattr(api, "require_auth", lambda handler: dict(user))


def _new_owner(email: str) -> dict:
    """Create a user and backfill them as owner of their org-of-one (as init_db does)."""
    user = create_user(email, "password-123")
    app_db.backfill_org_memberships()
    return user


def _owned_org_id(user_id: int) -> int:
    conn = app_db._connect()
    try:
        return int(
            conn.execute(
                "SELECT id FROM orgs WHERE owner_user_id = ? LIMIT 1", (user_id,)
            ).fetchone()["id"]
        )
    finally:
        conn.close()


def _actions_logged() -> list[str]:
    return [row["action"] for row in read_access_log(limit=1000)]


# ── 1. principal resolution ──────────────────────────────────────────────────────

def test_existing_backfilled_user_resolves_to_owner_of_their_org(isolated_db):
    user = _new_owner("owner@example.com")
    org_id = _owned_org_id(user["id"])

    principal = rbac_runtime.resolve_principal({"id": user["id"], "email": user["email"]})

    assert principal.role == ROLE_OWNER
    assert principal.user_id == user["id"]
    assert principal.org_id == org_id
    # And the owner is granted every mutating action (nothing changes for them).
    for action in (
        rbac_runtime.SOURCE_EDIT,
        rbac_runtime.SETTINGS_EDIT,
        rbac_runtime.ALERT_SEND,
        rbac_runtime.REVIEW_APPROVE,
        rbac_runtime.REVIEW_SUBMIT,
        rbac_runtime.EVIDENCE_EXPORT,
    ):
        assert rbac_runtime.is_permitted({"id": user["id"]}, action) is True


def test_user_without_membership_fails_safe_to_owner(isolated_db):
    # A user created but NOT backfilled has no org_members row and owns no org.
    user = create_user("nomember@example.com", "password-123")
    principal = rbac_runtime.resolve_principal({"id": user["id"]})
    assert principal.role == ROLE_OWNER  # fail-safe → keeps full self-access
    assert principal.user_id == user["id"]


def test_malformed_user_fails_closed_to_denied(isolated_db):
    # FAIL-CLOSED (owner decision 2026-07-13): a caller with a broken shape must
    # not mint an owner. Resolution never raises, but yields the zero-capability
    # ``denied`` role.
    for bad in (None, {"no_id": 1}):
        principal = rbac_runtime.resolve_principal(bad)
        assert principal.role == ROLE_DENIED
        assert not can(principal, EVIDENCE_VIEW)
        assert not can(principal, SOURCE_EDIT)


def test_resolution_db_error_fails_closed_to_denied(isolated_db, monkeypatch):
    # A transient DB error must DENY, never escalate: we cannot read the caller's
    # real role, so we must not assume owner (that would hand a lesser-role member
    # full privileges on any sqlite blip).
    def _boom(_uid):
        raise RuntimeError("db down")

    monkeypatch.setattr(rbac_runtime, "_resolve_from_db", _boom)
    principal = rbac_runtime.resolve_principal({"id": 42})
    assert principal.role == ROLE_DENIED
    assert principal.user_id == 42
    assert not can(principal, SOURCE_EDIT)  # no owner action on error


def test_corrupt_stored_role_fails_closed_to_denied(isolated_db, monkeypatch):
    # A membership row whose stored role is unknown/corrupt must NOT map to owner.
    user = _new_owner("corruptrole@example.com")
    import app.db as _db
    conn = _db._connect()
    try:
        conn.execute(
            "UPDATE org_members SET role = ? WHERE user_id = ?",
            ("superuser-💀", user["id"]),
        )
        conn.commit()
    finally:
        conn.close()
    principal = rbac_runtime.resolve_principal({"id": user["id"]})
    assert principal.role == ROLE_DENIED
    assert not can(principal, SOURCE_EDIT)


# ── 2. audit logging on the sensitive actions ────────────────────────────────────

def test_source_edit_writes_access_log(isolated_db, monkeypatch):
    user = _new_owner("adder@example.com")
    _auth_as(monkeypatch, {"id": user["id"], "email": user["email"]})
    saved: dict = {}
    monkeypatch.setattr("app.source_tester.validate_public_url", lambda url: (True, ""))
    monkeypatch.setattr("app.source_tester.source_url_exists", lambda url: False)
    monkeypatch.setattr("app.source_intake.load_sources_json", lambda: [])
    monkeypatch.setattr("app.source_intake.run_source_intake", lambda *a, **k: {"status": "CONFIRMED_ACCESSIBLE"})
    monkeypatch.setattr("app.source_tester.append_source_to_json", lambda src, **kw: saved.update(src) or True)

    handler = _make_handler("POST", "/api/custom-sources")
    # SEC-3 gate is not under test here — grant the custom_sources capability.
    monkeypatch.setattr(handler, "_require_capability", lambda u, cap: True)
    monkeypatch.setattr(
        handler, "_read_json",
        lambda: {"url": "https://regulator.example.ae/rules", "name": "R", "legal_confirmed": True},
    )
    handler._handle_custom_sources_add()

    # Action completed (owner) AND was recorded to the immutable log.
    assert saved.get("owner_user_id") == user["id"]
    rows = read_access_log(limit=10)
    assert any(r["action"] == rbac.SOURCE_EDIT and r["result"] == "allow" for r in rows)
    assert rows[0]["actor_user_id"] == user["id"]


def test_evidence_export_writes_access_log(isolated_db, monkeypatch):
    user = _new_owner("exporter@example.com")
    _auth_as(monkeypatch, {"id": user["id"], "email": user["email"]})
    handler = _make_handler("GET", "/api/evidence/export?run_id=run_official_1")
    # Bypass tenancy and the plan paywall (neither under test) and the writer.
    monkeypatch.setattr(handler, "_evidence_source_out_of_scope", lambda u, e: False)
    monkeypatch.setattr(handler, "_require_capability", lambda u, cap: True)
    called: dict = {}
    monkeypatch.setattr(handler, "_write_evidence_export", lambda evidence_id, **k: called.update(evidence_id=evidence_id))

    handler._handle_evidence_export_get()

    assert called.get("evidence_id") == "run_official_1"
    assert rbac.EVIDENCE_EXPORT in _actions_logged()


def test_alert_send_writes_access_log(isolated_db, monkeypatch):
    user = _new_owner("sender@example.com")
    _auth_as(monkeypatch, {"id": user["id"], "email": user["email"]})
    monkeypatch.setattr(api, "send_preview_alert_to_user", lambda uid, alert_id: {"ok": True, "message": "sent"})

    handler = _make_handler("POST", "/api/delivery/send-preview-alert")
    monkeypatch.setattr(handler, "_read_json_strict", lambda: ({"alert_id": "abc123"}, None))
    handler._handle_delivery_send_preview_alert()

    assert 403 not in _statuses(handler)
    assert rbac.ALERT_SEND in _actions_logged()


def test_review_approve_writes_access_log(isolated_db, monkeypatch):
    user = _new_owner("reviewer@example.com")
    _auth_as(monkeypatch, {"id": user["id"], "email": user["email"]})
    handler = _make_handler("POST", "/api/canonical-evidence/review")
    monkeypatch.setattr(handler, "_canonical_record_out_of_scope", lambda u, r: False)
    # SEC-2: a shared-official review requires an operator/global principal.
    monkeypatch.setattr(handler, "_caller_is_operator", lambda u: True)
    monkeypatch.setattr(handler, "_read_json_strict", lambda: ({"record_id": "r1", "decision": "approve", "note": "ok"}, None))
    monkeypatch.setattr("app.review_queue.record_canonical_review_action", lambda *a, **k: {"status": "ok"})

    handler._handle_canonical_evidence_review_action()

    assert 403 not in _statuses(handler)
    assert rbac.REVIEW_APPROVE in _actions_logged()


def test_review_shared_official_by_non_operator_is_forbidden(isolated_db, monkeypatch):
    """SEC-2: a self-registered ROLE_OWNER (non-operator) must NOT be able to
    approve/block a SHARED official evidence record — that decision changes
    brief-eligibility for every tenant relying on the record."""
    user = _new_owner("attacker@example.com")
    _auth_as(monkeypatch, {"id": user["id"], "email": user["email"]})
    handler = _make_handler("POST", "/api/canonical-evidence/review")
    # Not another tenant's custom record, but a shared OFFICIAL record...
    monkeypatch.setattr(handler, "_canonical_record_out_of_scope", lambda u, r: False)
    monkeypatch.setattr(handler, "_caller_is_operator", lambda u: False)
    monkeypatch.setattr(handler, "_canonical_record_is_own_custom", lambda u, r: False)
    called = {"write": False}
    monkeypatch.setattr(
        "app.review_queue.record_canonical_review_action",
        lambda *a, **k: called.__setitem__("write", True) or {"status": "ok"},
    )
    monkeypatch.setattr(handler, "_read_json_strict", lambda: ({"record_id": "shared-official-1", "decision": "blocked", "note": "sabotage"}, None))

    handler._handle_canonical_evidence_review_action()

    assert 403 in _statuses(handler), "non-operator review of shared official evidence must be 403"
    assert called["write"] is False, "the review decision must never be written"


def test_review_own_custom_record_by_owner_is_allowed(isolated_db, monkeypatch):
    """SEC-2: the operator gate must NOT block a customer reviewing their OWN
    custom-source record (private to their tenant)."""
    user = _new_owner("owner@example.com")
    _auth_as(monkeypatch, {"id": user["id"], "email": user["email"]})
    handler = _make_handler("POST", "/api/canonical-evidence/review")
    monkeypatch.setattr(handler, "_canonical_record_out_of_scope", lambda u, r: False)
    monkeypatch.setattr(handler, "_caller_is_operator", lambda u: False)
    monkeypatch.setattr(handler, "_canonical_record_is_own_custom", lambda u, r: True)
    monkeypatch.setattr("app.review_queue.record_canonical_review_action", lambda *a, **k: {"status": "ok"})
    monkeypatch.setattr(handler, "_read_json_strict", lambda: ({"record_id": "custom-abcd1234", "decision": "approve", "note": "mine"}, None))

    handler._handle_canonical_evidence_review_action()

    assert 403 not in _statuses(handler)


def test_review_shared_official_by_real_non_operator_is_forbidden_e2e(isolated_db, tmp_path, monkeypatch):
    """SEC-2 end-to-end WITHOUT mocking the gate functions: a genuine self-registered
    owner (real resolve_principal → org_id != GLOBAL_ORG_ID) hitting a genuine
    on-disk OFFICIAL evidence record must be 403'd by the REAL _caller_is_operator
    and _canonical_record_is_own_custom, and nothing may be written. This is the
    test the security review asked for — it would catch a regression in the
    `== GLOBAL_ORG_ID` compare or in is_custom_source ownership resolution that the
    boolean-mocking tests above cannot."""
    import json as _json
    import app.evidence_records as er

    user = _new_owner("realattacker@example.com")
    _auth_as(monkeypatch, {"id": user["id"], "email": user["email"]})

    # Real evidence-record.json on disk for a SHARED OFFICIAL source (not custom-).
    monkeypatch.setattr(er, "_BASE_DIR", tmp_path)
    rec_dir = tmp_path / "evidence" / "dfsa" / "AE-dfsa-official-e2e" / "run1"
    rec_dir.mkdir(parents=True)
    (rec_dir / "evidence-record.json").write_text(_json.dumps({
        "record_id": "evr-e2e-1",
        "source": {"source_id": "AE-dfsa-official-e2e", "regulator": "DFSA"},
        "run": {"run_id": "run1", "status": "CHANGED"},
    }), encoding="utf-8")

    wrote = {"v": False}
    monkeypatch.setattr(
        "app.review_queue.record_canonical_review_action",
        lambda *a, **k: wrote.__setitem__("v", True) or {"status": "ok"},
    )
    handler = _make_handler("POST", "/api/canonical-evidence/review")
    monkeypatch.setattr(
        handler, "_read_json_strict",
        lambda: ({"record_id": "evr-e2e-1", "decision": "blocked", "note": "sabotage"}, None),
    )

    handler._handle_canonical_evidence_review_action()

    assert 403 in _statuses(handler), "a REAL non-operator must be 403 on shared official evidence"
    assert wrote["v"] is False, "the review decision must never be written"


# ── 3. a logging failure must NOT break the action (isolation) ────────────────────

def test_logging_failure_does_not_break_the_action(isolated_db, monkeypatch):
    user = _new_owner("resilient@example.com")
    _auth_as(monkeypatch, {"id": user["id"], "email": user["email"]})

    # Make the audit write blow up — the endpoint must still succeed.
    def _boom(*a, **k):
        raise RuntimeError("access_log disk full")

    monkeypatch.setattr(rbac_runtime, "append_access_log", _boom)

    saved: dict = {}
    monkeypatch.setattr("app.source_tester.validate_public_url", lambda url: (True, ""))
    monkeypatch.setattr("app.source_tester.source_url_exists", lambda url: False)
    monkeypatch.setattr("app.source_intake.load_sources_json", lambda: [])
    monkeypatch.setattr("app.source_intake.run_source_intake", lambda *a, **k: {"status": "CONFIRMED_ACCESSIBLE"})
    monkeypatch.setattr("app.source_tester.append_source_to_json", lambda src, **kw: saved.update(src) or True)

    handler = _make_handler("POST", "/api/custom-sources")
    # SEC-3 gate is not under test here — grant the custom_sources capability.
    monkeypatch.setattr(handler, "_require_capability", lambda u, cap: True)
    monkeypatch.setattr(
        handler, "_read_json",
        lambda: {"url": "https://regulator.example.ae/rules", "name": "R", "legal_confirmed": True},
    )
    # Must not raise, and the mutation must complete.
    handler._handle_custom_sources_add()
    assert saved.get("owner_user_id") == user["id"]
    assert 403 not in _statuses(handler)
    assert 500 not in _statuses(handler)


def test_log_sensitive_action_swallows_errors(isolated_db, monkeypatch):
    def _boom(*a, **k):
        raise RuntimeError("nope")

    monkeypatch.setattr(rbac_runtime, "append_access_log", _boom)
    # Never raises, returns None.
    assert rbac_runtime.log_sensitive_action({"id": 1}, rbac.SOURCE_EDIT) is None


# ── 4. owner no-regression at the gate ───────────────────────────────────────────

def test_owner_passes_every_mutating_gate(isolated_db, monkeypatch):
    user = _new_owner("boss@example.com")
    handler = _make_handler()
    for action in (
        rbac_runtime.SETTINGS_EDIT,
        rbac_runtime.ALERT_SEND,
        rbac_runtime.REVIEW_SUBMIT,
        rbac_runtime.REVIEW_APPROVE,
        rbac_runtime.SOURCE_EDIT,
    ):
        allowed = handler._rbac_guard({"id": user["id"], "email": user["email"]}, action)
        assert allowed is True, f"owner must pass {action}"
    # An owner is NEVER handed a 403 by the gate.
    assert 403 not in _statuses(handler)


def test_gate_fails_open_when_rbac_errors(isolated_db, monkeypatch):
    # If the RBAC evaluation itself throws, the gate must ALLOW (never break an
    # already-authenticated request).
    def _boom(*a, **k):
        raise RuntimeError("rbac exploded")

    monkeypatch.setattr(rbac_runtime, "evaluate", _boom)
    handler = _make_handler()
    assert handler._rbac_guard({"id": 1}, rbac_runtime.SOURCE_EDIT) is True
    assert 403 not in _statuses(handler)


# ── 5. auditor read-only enforcement ─────────────────────────────────────────────

@pytest.fixture()
def org_with_auditor(isolated_db):
    """An owner org plus an ``auditor`` seat (a user who owns no org of their own).

    Returns ``(owner_user, auditor_user, org_id)``. The auditor is added to the
    owner's org via the owner-gated ``assign_org_role`` — the real assignment path.
    """
    owner = _new_owner("org-owner@example.com")
    org_id = _owned_org_id(owner["id"])
    # Create the auditor AFTER backfill so they own no org → they resolve purely to
    # the auditor seat we grant next.
    auditor = create_user("auditor@example.com", "password-123")
    result = rbac_runtime.assign_org_role(
        {"id": owner["id"]}, auditor["id"], org_id, ROLE_AUDITOR
    )
    assert result["ok"] is True and result["role"] == ROLE_AUDITOR
    return owner, auditor, org_id


def test_auditor_principal_resolves_to_auditor(org_with_auditor):
    _owner, auditor, org_id = org_with_auditor
    principal = rbac_runtime.resolve_principal({"id": auditor["id"]})
    assert principal.role == ROLE_AUDITOR
    assert principal.org_id == org_id


def test_auditor_is_denied_a_mutation_403(org_with_auditor, monkeypatch):
    _owner, auditor, _org = org_with_auditor
    handler = _make_handler()
    allowed = handler._rbac_guard({"id": auditor["id"]}, rbac_runtime.SOURCE_EDIT)
    assert allowed is False
    assert 403 in _statuses(handler)
    # …and the denial is recorded to the immutable log.
    rows = read_access_log(limit=10)
    assert any(r["action"] == rbac.SOURCE_EDIT and r["result"] == "deny" for r in rows)


def test_auditor_is_allowed_evidence_view_and_export(org_with_auditor):
    _owner, auditor, _org = org_with_auditor
    user = {"id": auditor["id"]}
    assert rbac_runtime.is_permitted(user, EVIDENCE_VIEW) is True
    assert rbac_runtime.is_permitted(user, EVIDENCE_EXPORT) is True
    # But every mutation is denied.
    assert rbac_runtime.is_permitted(user, rbac_runtime.SOURCE_EDIT) is False
    assert rbac_runtime.is_permitted(user, rbac_runtime.REVIEW_APPROVE) is False
    assert rbac_runtime.is_permitted(user, rbac_runtime.ALERT_SEND) is False


def test_auditor_blocked_from_source_add_handler(org_with_auditor, monkeypatch):
    """End-to-end: an auditor calling the source-add endpoint gets 403 and the
    mutation never reaches the writer."""
    _owner, auditor, _org = org_with_auditor
    _auth_as(monkeypatch, {"id": auditor["id"], "email": auditor["email"]})
    monkeypatch.setattr(
        "app.source_tester.append_source_to_json",
        lambda src: pytest.fail("auditor mutation reached the writer"),
    )
    handler = _make_handler("POST", "/api/custom-sources")
    monkeypatch.setattr(
        handler, "_read_json",
        lambda: {"url": "https://regulator.example.ae/rules", "name": "R", "legal_confirmed": True},
    )
    handler._handle_custom_sources_add()
    assert 403 in _statuses(handler)


def test_auditor_allowed_through_export_handler(org_with_auditor, monkeypatch):
    """Exports are NOT gated by role (auditor may export). The export handler must
    proceed for an auditor and record the evidence.export event."""
    _owner, auditor, _org = org_with_auditor
    _auth_as(monkeypatch, {"id": auditor["id"], "email": auditor["email"]})
    handler = _make_handler("GET", "/api/evidence/export?run_id=run_official_9")
    monkeypatch.setattr(handler, "_evidence_source_out_of_scope", lambda u, e: False)
    monkeypatch.setattr(handler, "_require_capability", lambda u, cap: True)  # paywall not under test
    called: dict = {}
    monkeypatch.setattr(handler, "_write_evidence_export", lambda evidence_id, **k: called.update(evidence_id=evidence_id))
    handler._handle_evidence_export_get()
    assert 403 not in _statuses(handler)
    assert called.get("evidence_id") == "run_official_9"
    assert rbac.EVIDENCE_EXPORT in _actions_logged()


# ── 6. assign-auditor path is owner-gated & org-scoped ───────────────────────────

def test_assign_role_requires_owner_member_manage(org_with_auditor):
    # The auditor (no member.manage) cannot grant a role — forbidden.
    _owner, auditor, org_id = org_with_auditor
    other = create_user("victim@example.com", "password-123")
    result = rbac_runtime.assign_org_role({"id": auditor["id"]}, other["id"], org_id, ROLE_AUDITOR)
    assert result == {"ok": False, "error": "forbidden"}


def test_assign_role_is_org_scoped(isolated_db):
    # Owner of org A cannot assign into org B (org-scoping in can()).
    owner_a = _new_owner("a-owner@example.com")
    owner_b = _new_owner("b-owner@example.com")
    org_b = _owned_org_id(owner_b["id"])
    victim = create_user("v@example.com", "password-123")
    result = rbac_runtime.assign_org_role({"id": owner_a["id"]}, victim["id"], org_b, ROLE_AUDITOR)
    assert result == {"ok": False, "error": "forbidden"}


def test_assign_role_rejects_unknown_role(isolated_db):
    owner = _new_owner("role-owner@example.com")
    org_id = _owned_org_id(owner["id"])
    target = create_user("t@example.com", "password-123")
    result = rbac_runtime.assign_org_role({"id": owner["id"]}, target["id"], org_id, "superuser")
    assert result == {"ok": False, "error": "invalid_role"}


def test_assign_role_rejects_system_role(isolated_db):
    # "system" is the machine identity, never an assignable human seat.
    owner = _new_owner("sys-owner@example.com")
    org_id = _owned_org_id(owner["id"])
    target = create_user("sys-target@example.com", "password-123")
    result = rbac_runtime.assign_org_role({"id": owner["id"]}, target["id"], org_id, "system")
    assert result == {"ok": False, "error": "invalid_role"}


def test_assign_role_cannot_seat_into_global_org(isolated_db):
    # No owner may seat a user into the GLOBAL org (id 0) — that is operator scope.
    # An ordinary owner's org_id is never 0, so the org-scope check forbids it.
    owner = _new_owner("global-owner@example.com")
    _owned_org_id(owner["id"])  # give the owner a real org-of-one
    target = create_user("global-target@example.com", "password-123")
    result = rbac_runtime.assign_org_role({"id": owner["id"]}, target["id"], 0, ROLE_AUDITOR)
    assert result == {"ok": False, "error": "forbidden"}


def test_assign_role_is_idempotent_upsert(isolated_db):
    owner = _new_owner("up-owner@example.com")
    org_id = _owned_org_id(owner["id"])
    target = create_user("up-target@example.com", "password-123")

    first = rbac_runtime.assign_org_role({"id": owner["id"]}, target["id"], org_id, ROLE_AUDITOR)
    assert first["ok"] is True
    # Re-assigning (e.g. promoting) must update in place, not duplicate the row.
    second = rbac_runtime.assign_org_role({"id": owner["id"]}, target["id"], org_id, "reviewer")
    assert second["ok"] is True and second["role"] == "reviewer"

    conn = app_db._connect()
    try:
        rows = conn.execute(
            "SELECT role FROM org_members WHERE org_id = ? AND user_id = ?",
            (org_id, target["id"]),
        ).fetchall()
    finally:
        conn.close()
    assert [r["role"] for r in rows] == ["reviewer"]  # exactly one row, updated
