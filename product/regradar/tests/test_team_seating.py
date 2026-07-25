"""An owner can seat a colleague over HTTP, and only an owner can.

Before this, seating existed solely as a founder CLI, so a customer who wanted a
second reviewer on their evidence had to email us and wait for an SSH session.
Measured with tools/measure_team_axis.py: every candidate route returned 404.

The subtler half is that seating used to be a NO-OP even from the CLI. Every user
owns a backfilled org-of-one and resolve_principal prefers the org you OWN, so an
auditor seat in the customer's org lost to the colleague's own empty workspace —
`assign_org_role` returned ok, a row landed, and the colleague signed in to
nothing. `users.active_org_id` is what makes the seat reachable, and the tests
below pin both halves: the door, and the seat actually meaning something.
"""

from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api as api  # noqa: E402
import app.api_team as api_team  # noqa: E402
import app.db as app_db  # noqa: E402
import app.rbac_runtime as rbac_runtime  # noqa: E402
from app.api import _Handler  # noqa: E402
from app.auth import create_user  # noqa: E402


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "team.db"))
    return tmp_path


def _handler(method: str, path: str, body: dict | None = None) -> _Handler:
    import json as _json

    raw = _json.dumps(body or {}).encode("utf-8")
    header_map = {"Content-Length": str(len(raw)), "X-Real-IP": "10.0.0.9"}

    h = _Handler.__new__(_Handler)
    h.command = method
    h.path = path
    h.request = MagicMock()
    h.client_address = ("127.0.0.1", 9999)
    h.server = MagicMock()
    h.rfile = BytesIO(raw)
    h.wfile = BytesIO()
    h.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": header_map.get(key, default)
    h.headers = hdrs
    sent: list[tuple[dict, int]] = []
    h._send_json = lambda data, status=200, **kw: sent.append((data, status))  # type: ignore[method-assign]
    h._sent = sent  # type: ignore[attr-defined]
    return h


def _auth_as(monkeypatch, user: dict) -> None:
    monkeypatch.setattr(api, "require_auth", lambda handler: dict(user))
    monkeypatch.setattr(api_team, "require_auth", lambda handler: dict(user))


def _last(h: _Handler) -> tuple[dict, int]:
    return h._sent[-1]  # type: ignore[attr-defined]


def _org_of(user: dict) -> int:
    return int(rbac_runtime.resolve_principal(user).org_id or -1)


@pytest.fixture()
def firm(isolated_db):
    """One owner, one colleague, and an unrelated person in another org."""
    owner = create_user("owner@firm.example", "password-123")
    mate = create_user("mate@firm.example", "password-123")
    stranger = create_user("stranger@other.example", "password-123")
    app_db.backfill_org_memberships()
    return {"owner": owner, "mate": mate, "stranger": stranger}


# ── the door ────────────────────────────────────────────────────────────────


def test_owner_seats_a_colleague_over_http(firm, monkeypatch):
    _auth_as(monkeypatch, firm["owner"])
    owner_org = _org_of(firm["owner"])

    h = _handler("POST", "/api/team/members",
                 {"email": "mate@firm.example", "role": "auditor"})
    h.do_POST()
    body, status = _last(h)

    assert status == 200, body
    assert _org_of(firm["mate"]) == owner_org, (
        "the seat did not change where the colleague lands — they still sign in "
        "to their own empty workspace"
    )
    assert rbac_runtime.resolve_principal(firm["mate"]).role == "auditor"


def test_the_roster_lists_the_seated_colleague(firm, monkeypatch):
    _auth_as(monkeypatch, firm["owner"])
    add = _handler("POST", "/api/team/members", {"email": "mate@firm.example"})
    add.do_POST()

    h = _handler("GET", "/api/team/members")
    h.do_GET()
    body, status = _last(h)

    assert status == 200
    assert {m["email"] for m in body["members"]} == {
        "owner@firm.example", "mate@firm.example"
    }


def test_revoking_removes_the_seat(firm, monkeypatch):
    _auth_as(monkeypatch, firm["owner"])
    owner_org = _org_of(firm["owner"])
    _handler("POST", "/api/team/members", {"email": "mate@firm.example"}).do_POST()

    h = _handler("POST", "/api/team/members/revoke", {"email": "mate@firm.example"})
    h.do_POST()
    body, status = _last(h)

    assert status == 200 and body["removed"] is True
    assert _org_of(firm["mate"]) != owner_org


def test_unauthenticated_requests_are_refused(firm, monkeypatch):
    monkeypatch.setattr(api, "require_auth", lambda handler: None)
    monkeypatch.setattr(api_team, "require_auth", lambda handler: None)

    for method, path in (
        ("GET", "/api/team/members"),
        ("POST", "/api/team/members"),
        ("POST", "/api/team/members/revoke"),
        ("POST", "/api/team/active-org"),
    ):
        h = _handler(method, path, {"email": "x@example.com", "org_id": 1})
        h.do_POST() if method == "POST" else h.do_GET()
        assert _last(h)[1] == 401, f"{method} {path} was not refused"


def test_seating_an_address_with_no_account_says_so(firm, monkeypatch):
    """Silence here would look like success and leave the owner waiting."""
    _auth_as(monkeypatch, firm["owner"])

    h = _handler("POST", "/api/team/members", {"email": "nobody@firm.example"})
    h.do_POST()
    body, status = _last(h)

    assert status == 404
    assert body["error"] == "no_such_account"


# ── the privilege boundary ──────────────────────────────────────────────────


def test_a_seated_auditor_cannot_seat_anyone(firm, monkeypatch):
    """Otherwise "add one colleague" quietly becomes "add anyone"."""
    _auth_as(monkeypatch, firm["owner"])
    _handler("POST", "/api/team/members", {"email": "mate@firm.example"}).do_POST()
    owner_org = _org_of(firm["owner"])
    assert _org_of(firm["mate"]) == owner_org, "setup failed — mate was never seated"

    _auth_as(monkeypatch, firm["mate"])
    h = _handler("POST", "/api/team/members", {"email": "stranger@other.example"})
    h.do_POST()

    assert _last(h)[1] == 403
    assert _org_of(firm["stranger"]) != owner_org


def test_a_seated_auditor_cannot_read_the_roster(firm, monkeypatch):
    _auth_as(monkeypatch, firm["owner"])
    _handler("POST", "/api/team/members", {"email": "mate@firm.example"}).do_POST()

    _auth_as(monkeypatch, firm["mate"])
    h = _handler("GET", "/api/team/members")
    h.do_GET()

    assert _last(h)[1] == 403


def test_an_owner_sees_only_their_own_roster(firm, monkeypatch):
    """The roster is bounded to the caller's principal, never a supplied org."""
    _auth_as(monkeypatch, firm["stranger"])
    h = _handler("GET", "/api/team/members")
    h.do_GET()
    body, status = _last(h)

    assert status == 200
    assert {m["email"] for m in body["members"]} == {"stranger@other.example"}


def test_the_org_owner_cannot_be_revoked(firm, monkeypatch):
    """An org with no owner can never seat anyone again — recovery is a shell."""
    _auth_as(monkeypatch, firm["owner"])

    h = _handler("POST", "/api/team/members/revoke", {"email": "owner@firm.example"})
    h.do_POST()

    assert _last(h)[1] == 400
    assert _org_of(firm["owner"]) == _org_of(firm["owner"])


# ── active_org_id: the half that makes a seat mean something ────────────────


def test_a_hostile_active_org_grants_nothing(firm):
    """A stale or tampered active_org_id must not become an access grant.

    resolve_principal ranks orgs, but only ones the membership WHERE already
    matched — so pointing the column at a stranger's org selects no row and
    falls through to the user's own.
    """
    victim_org = _org_of(firm["stranger"])
    conn = app_db._connect()
    try:
        conn.execute(
            "UPDATE users SET active_org_id = ? WHERE id = ?",
            (victim_org, firm["mate"]["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    assert _org_of(firm["mate"]) != victim_org


def test_a_solo_user_is_unaffected(firm):
    """active_org_id is NULL for every existing row; behaviour must be identical."""
    principal = rbac_runtime.resolve_principal(firm["owner"])
    assert principal.role == "owner"
    assert principal.org_id == _org_of(firm["owner"])


def test_switching_requires_membership(firm):
    result = rbac_runtime.set_active_org(firm["mate"], _org_of(firm["stranger"]))
    assert result == {"ok": False, "error": "not_a_member"}
    assert _org_of(firm["mate"]) != _org_of(firm["stranger"])


def test_an_explicit_choice_is_not_overridden_by_a_later_seat(firm, monkeypatch):
    """Otherwise any owner could yank someone out of the org they are working in."""
    _auth_as(monkeypatch, firm["owner"])
    _handler("POST", "/api/team/members", {"email": "mate@firm.example"}).do_POST()
    owner_org = _org_of(firm["owner"])

    # The colleague deliberately switches back to their own workspace.
    own_org = int(
        app_db._connect()
        .execute("SELECT id FROM orgs WHERE owner_user_id = ?", (firm["mate"]["id"],))
        .fetchone()["id"]
    )
    assert rbac_runtime.set_active_org(firm["mate"], own_org)["ok"] is True
    assert _org_of(firm["mate"]) == own_org

    # A second org seats them too. Their current choice must survive.
    _auth_as(monkeypatch, firm["stranger"])
    _handler("POST", "/api/team/members", {"email": "mate@firm.example"}).do_POST()

    assert _org_of(firm["mate"]) == own_org, "a later seat hijacked an explicit choice"
    assert own_org not in (owner_org, _org_of(firm["stranger"]))
