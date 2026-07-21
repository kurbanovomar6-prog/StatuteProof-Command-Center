"""RBAC fail-CLOSED — the last security fail-open in the tree, closed.

Before this change, ``_rbac_guard`` in ``app/api.py`` FAILED OPEN: when
``rbac_runtime.evaluate()`` raised, any non-``fail_closed`` mutating action was
ALLOWED (only the anomaly was logged). Today every seat is backfilled as
``owner`` so there was no live exposure, but the code's own comment flagged that
this MUST flip to fail-closed before any real non-owner (auditor/reviewer) seat
is assignable — otherwise a transient RBAC error would silently hand a
least-privilege seat a privileged mutation.

This suite proves the flip WITHOUT locking the legitimate owner out:

* a real non-owner ``auditor`` seat is DENIED a sensitive mutation (403) when
  ``evaluate()`` errors — the behaviour that was previously ALLOWED;
* an ``owner`` (positively resolved) is still ALLOWED the same mutation on the
  same error — no-regression for the only role in live data today;
* the highest-stakes governance path (``fail_closed=True``) keeps denying even
  the owner on error (unchanged);
* the read/export observation path (``_rbac_log_export``) is not gated by the
  flip and stays permissive — the flip is on MUTATIONS only.

Runs against a REAL throwaway SQLite DB and the REAL HTTP handler, reusing the
Stage-2 handler harness.
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
from app.rbac import ROLE_AUDITOR


# ── fixtures & harness (mirrors tests/test_rbac_stage2.py) ────────────────────────

@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "rbac_fail_closed.db"))
    return tmp_path / "rbac_fail_closed.db"


def _make_handler(method: str = "POST", path: str = "/") -> _Handler:
    header_map = {"Content-Length": "0", "X-Real-IP": "10.0.0.5"}
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


def _new_owner(email: str) -> dict:
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


@pytest.fixture()
def org_with_auditor(isolated_db):
    """An owner org plus a REAL ``auditor`` seat, assigned via the owner-gated path.

    The auditor is created AFTER the backfill so they own no org of their own and
    resolve purely to the ``auditor`` seat — not the onboarding owner fail-safe.
    """
    owner = _new_owner("fc-owner@example.com")
    org_id = _owned_org_id(owner["id"])
    auditor = create_user("fc-auditor@example.com", "password-123")
    result = rbac_runtime.assign_org_role({"id": owner["id"]}, auditor["id"], org_id, ROLE_AUDITOR)
    assert result["ok"] is True and result["role"] == ROLE_AUDITOR
    return owner, auditor, org_id


def _make_evaluate_raise(monkeypatch) -> None:
    def _boom(*a, **k):
        raise RuntimeError("rbac evaluate exploded")

    monkeypatch.setattr(rbac_runtime, "evaluate", _boom)


# ── the flip: non-owner sensitive mutation fails CLOSED on evaluate() error ───────

def test_evaluate_error_denies_non_owner_auditor_mutation(org_with_auditor, monkeypatch):
    # Regression for the fail-open finding: with evaluate() raising, a REAL auditor
    # seat attempting a sensitive mutation must be DENIED (403), not allowed.
    _owner, auditor, _org = org_with_auditor
    _make_evaluate_raise(monkeypatch)

    handler = _make_handler()
    allowed = handler._rbac_guard({"id": auditor["id"], "email": auditor["email"]}, rbac_runtime.SOURCE_EDIT)

    assert allowed is False, "non-owner mutation must FAIL CLOSED on an RBAC evaluation error"
    assert 403 in _statuses(handler)
    # …and the fail-closed decision is recorded to the immutable log (never silent).
    rows = read_access_log(limit=20)
    assert any(r["action"] == rbac.SOURCE_EDIT and r["result"] == "error" for r in rows)


def test_evaluate_error_still_allows_owner_mutation(org_with_auditor, monkeypatch):
    # No-regression: the legitimate OWNER must never be locked out by an RBAC
    # plumbing glitch. resolve_principal still positively resolves them as owner.
    owner, _auditor, _org = org_with_auditor
    _make_evaluate_raise(monkeypatch)

    handler = _make_handler()
    allowed = handler._rbac_guard({"id": owner["id"], "email": owner["email"]}, rbac_runtime.SOURCE_EDIT)

    assert allowed is True, "a positively-resolved owner must still be allowed on an evaluate() error"
    assert 403 not in _statuses(handler)


def test_evaluate_error_fail_closed_true_denies_even_owner(org_with_auditor, monkeypatch):
    # Preserved behaviour: the highest-stakes governance actions (fail_closed=True,
    # e.g. minting an external evidence-room credential) DENY even the owner on an
    # evaluation error — never mint a durable external credential on a glitch.
    owner, _auditor, _org = org_with_auditor
    _make_evaluate_raise(monkeypatch)

    handler = _make_handler()
    allowed = handler._rbac_guard(
        {"id": owner["id"], "email": owner["email"]},
        rbac_runtime.EVIDENCE_SHARE,
        fail_closed=True,
    )

    assert allowed is False
    assert 403 in _statuses(handler)


def test_read_only_export_path_stays_permissive_under_error(org_with_auditor, monkeypatch):
    # Documented policy: read/export observation uses _rbac_log_export, which never
    # denies. The fail-closed flip is on MUTATIONS only, so an evaluate() error does
    # not turn a permitted export into a 403.
    _owner, auditor, _org = org_with_auditor
    _make_evaluate_raise(monkeypatch)

    handler = _make_handler()
    handler._rbac_log_export({"id": auditor["id"]}, resource_id="ev-fc-1")

    assert 403 not in _statuses(handler)
    rows = read_access_log(limit=20)
    assert any(r["action"] == rbac.EVIDENCE_EXPORT and r["result"] == "allow" for r in rows)
