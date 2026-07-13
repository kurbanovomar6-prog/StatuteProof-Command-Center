"""GET /api/audit-log — owner-scoped, read-only view of the append-only log.

Regression for the enterprise finding that the access_log had no reader, so the
"who did what, when" record could not be shown to a customer, an auditor, or the
founder without raw SQLite. The endpoint must be owner-gated and never disclose
another tenant's rows.
"""

from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api as api  # noqa: E402
import app.db as app_db  # noqa: E402
from app.access_log import append_access_log  # noqa: E402
from app.api import _Handler  # noqa: E402
from app.auth import create_user  # noqa: E402


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "auditlog.db"))
    return tmp_path


def _make_handler(path: str) -> _Handler:
    handler = _Handler.__new__(_Handler)
    handler.command = "GET"
    handler.path = path
    handler.request = MagicMock()
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(b"")
    handler.wfile = BytesIO()
    handler.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": {"Content-Length": "0", "X-Real-IP": "10.0.0.5"}.get(key, default)
    handler.headers = hdrs
    sent: list = []
    handler._send_json = lambda data, status=200, **kw: sent.append((data, status))  # type: ignore[method-assign]
    handler._sent = sent  # type: ignore[attr-defined]
    return handler


def _org_id(user_id: int) -> int:
    from app.db import _connect
    from app.rbac_runtime import ensure_rbac_tables

    conn = _connect()
    try:
        ensure_rbac_tables(conn)
        return conn.execute("SELECT id FROM orgs WHERE owner_user_id = ?", (user_id,)).fetchone()["id"]
    finally:
        conn.close()


def test_owner_reads_only_their_org_rows(isolated_db, monkeypatch):
    owner = create_user("owner@x.io", "password-123")
    other = create_user("other@x.io", "password-123")
    app_db.backfill_org_memberships()
    my_org = _org_id(owner["id"])
    other_org = _org_id(other["id"])

    append_access_log(actor_user_id=owner["id"], org_id=my_org, action="evidence.export", result="allow", resource_id="r1")
    append_access_log(actor_user_id=other["id"], org_id=other_org, action="evidence.export", result="allow", resource_id="secret")

    monkeypatch.setattr(api, "require_auth", lambda h: {"id": owner["id"], "email": owner["email"]})
    handler = _make_handler("/api/audit-log")
    handler._handle_audit_log_get()

    data, status = handler._sent[-1]
    assert status == 200
    assert data["ok"] is True
    ids = {e["resource_id"] for e in data["entries"]}
    assert "r1" in ids
    # Another tenant's row must never appear.
    assert "secret" not in ids
    assert all(e["org_id"] == my_org for e in data["entries"])


def test_unresolved_org_fails_closed_not_all_rows(isolated_db, monkeypatch):
    """CRITICAL regression: a caller whose org resolves to None must be refused,
    NEVER handed every tenant's rows. resolve_principal fail-safes to
    (org_id=None, role=owner) for a user with no org; the endpoint must fail
    closed rather than pass org_id=None (which read_access_log treats as 'all')."""
    owner = create_user("tenantA@x.io", "password-123")
    app_db.backfill_org_memberships()
    my_org = _org_id(owner["id"])
    append_access_log(
        actor_user_id=owner["id"], org_id=my_org, action="evidence.export",
        result="allow", resource_id="tenantA-secret",
    )
    # User B is created but NOT backfilled -> owns no org, no membership ->
    # resolve_principal(B) = (org_id=None, role=owner).
    other = create_user("noorg@x.io", "password-123")
    from app.rbac_runtime import resolve_principal
    assert resolve_principal({"id": other["id"]}).org_id is None

    monkeypatch.setattr(api, "require_auth", lambda h: {"id": other["id"], "email": other["email"]})
    handler = _make_handler("/api/audit-log")
    handler._handle_audit_log_get()
    data, status = handler._sent[-1]
    assert status == 403
    # The other tenant's row must never appear.
    assert "tenantA-secret" not in str(data)


def test_unauthenticated_is_401(isolated_db, monkeypatch):
    monkeypatch.setattr(api, "require_auth", lambda h: None)
    handler = _make_handler("/api/audit-log")
    handler._handle_audit_log_get()
    _data, status = handler._sent[-1]
    assert status == 401


def test_non_owner_is_403(isolated_db, monkeypatch):
    owner = create_user("owner2@x.io", "password-123")
    app_db.backfill_org_memberships()  # owner becomes owner of their org-of-one
    org_id = _org_id(owner["id"])
    # Create the auditor AFTER backfill so they own NO org and are only a
    # member (auditor) of the owner's org — a genuine non-owner principal.
    auditor = create_user("auditor@x.io", "password-123")
    from app.rbac_runtime import assign_org_role
    assert assign_org_role({"id": owner["id"]}, auditor["id"], org_id, "auditor")["ok"]

    monkeypatch.setattr(api, "require_auth", lambda h: {"id": auditor["id"], "email": auditor["email"]})
    handler = _make_handler("/api/audit-log")
    handler._handle_audit_log_get()
    _data, status = handler._sent[-1]
    assert status == 403
