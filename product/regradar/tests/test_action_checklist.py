"""Per-alert review checklist (obligation-workflow v1) — behavior + safety.

Proves the four things the feature must guarantee:

1. CRUD — a user can add, list, tick (toggle status), edit, and delete their own
   review action items.
2. Owner-scoping (adversarial) — user A can NEVER see, update, or delete user B's
   items; a cross-user id resolves to nothing (404-shaped) with no oracle.
3. Bounded — the per-alert item cap is enforced and text/assignee are length-capped.
4. Legal-safety — every mutation lands in the immutable access log (and a logging
   failure never breaks the mutation); the app's OWN framing strings pass the
   product-wide forbidden-claims guard; bad input fails soft, never raises.

Runs against a REAL throwaway SQLite DB and, for the endpoint wiring, the REAL
HTTP handler (``app.api._Handler``), reusing the harness from test_rbac_stage2.py.
"""
from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api as api
import app.api_alerts as api_alerts
import app.db as app_db
import app.action_checklist as checklist
from app.access_log import read_access_log
from app.action_checklist import (
    FRAMING,
    MAX_ITEMS_PER_ALERT,
    MAX_TEXT_LEN,
    add_checklist_item,
    delete_checklist_item,
    list_checklist_items,
    update_checklist_item,
)
from app.api import _Handler
from app.auth import create_user
from app.legal_safety import assert_no_forbidden_claims


# ── fixtures & harness ───────────────────────────────────────────────────────────

@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    """Point the whole DB layer at a temp file (users, checklist, access_log)."""
    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "checklist.db"))
    return tmp_path / "checklist.db"


def _user(email: str) -> dict:
    user = create_user(email, "password-123")
    app_db.backfill_org_memberships()
    return user


def _make_handler(method: str, path: str, *, real_ip: str = "10.0.0.9") -> _Handler:
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


def _auth_as(monkeypatch, user: dict) -> None:
    monkeypatch.setattr(api, "require_auth", lambda handler: dict(user))
    monkeypatch.setattr(api_alerts, "require_auth", lambda handler: dict(user))


def _last(handler: _Handler) -> tuple[dict, int]:
    return handler._sent[-1]  # type: ignore[attr-defined]


ALERT = "draft-cbuae001"


# ── 1. CRUD ──────────────────────────────────────────────────────────────────────

def test_add_then_list_returns_the_item(isolated_db):
    user = _user("crud@example.com")
    item = add_checklist_item(user["id"], ALERT, "Review the reporting form change", assignee="MLRO", due_date="2026-09-01")
    assert item is not None
    assert item["text"] == "Review the reporting form change"
    assert item["assignee"] == "MLRO"
    assert item["due_date"] == "2026-09-01"
    assert item["status"] == "open"

    items = list_checklist_items(user["id"], ALERT)
    assert len(items) == 1
    assert items[0]["id"] == item["id"]
    # owner_user_id is an internal scoping column — never surfaced to the client.
    assert "owner_user_id" not in items[0]


def test_tick_toggles_status_open_and_done(isolated_db):
    user = _user("tick@example.com")
    item = add_checklist_item(user["id"], ALERT, "Confirm effective date")
    ticked = update_checklist_item(user["id"], item["id"], status="done")
    assert ticked is not None and ticked["status"] == "done"
    assert ticked["updated_at"] >= item["created_at"]

    reopened = update_checklist_item(user["id"], item["id"], status="open")
    assert reopened["status"] == "open"


def test_edit_fields_and_delete(isolated_db):
    user = _user("edit@example.com")
    item = add_checklist_item(user["id"], ALERT, "Original text")
    edited = update_checklist_item(user["id"], item["id"], text="Revised text", assignee="Compliance")
    assert edited["text"] == "Revised text"
    assert edited["assignee"] == "Compliance"

    assert delete_checklist_item(user["id"], item["id"]) is True
    assert list_checklist_items(user["id"], ALERT) == []
    # Deleting again returns False (already gone) — idempotent, no raise.
    assert delete_checklist_item(user["id"], item["id"]) is False


def test_list_orders_open_before_done(isolated_db):
    user = _user("order@example.com")
    first = add_checklist_item(user["id"], ALERT, "First")
    add_checklist_item(user["id"], ALERT, "Second")
    update_checklist_item(user["id"], first["id"], status="done")  # tick the first
    items = list_checklist_items(user["id"], ALERT)
    # Done items sort after open ones regardless of creation order.
    assert items[-1]["text"] == "First"
    assert items[-1]["status"] == "done"


# ── 2. owner-scoping (adversarial) ───────────────────────────────────────────────

def test_user_cannot_see_another_users_items(isolated_db):
    alice = _user("alice@example.com")
    bob = _user("bob@example.com")
    a_item = add_checklist_item(alice["id"], ALERT, "Alice private action")
    add_checklist_item(bob["id"], ALERT, "Bob private action")

    # Same alert_id, but each user only ever sees their own items.
    alice_items = list_checklist_items(alice["id"], ALERT)
    bob_items = list_checklist_items(bob["id"], ALERT)
    assert [i["text"] for i in alice_items] == ["Alice private action"]
    assert [i["text"] for i in bob_items] == ["Bob private action"]
    assert a_item["id"] not in {i["id"] for i in bob_items}


def test_user_cannot_update_another_users_item(isolated_db):
    alice = _user("alice2@example.com")
    bob = _user("bob2@example.com")
    a_item = add_checklist_item(alice["id"], ALERT, "Alice action")

    # Bob targets Alice's item id directly → zero rows matched → None (404, no oracle).
    assert update_checklist_item(bob["id"], a_item["id"], status="done") is None
    # Alice's item is untouched.
    assert list_checklist_items(alice["id"], ALERT)[0]["status"] == "open"


def test_user_cannot_delete_another_users_item(isolated_db):
    alice = _user("alice3@example.com")
    bob = _user("bob3@example.com")
    a_item = add_checklist_item(alice["id"], ALERT, "Alice action")

    assert delete_checklist_item(bob["id"], a_item["id"]) is False
    # Still there for Alice.
    assert len(list_checklist_items(alice["id"], ALERT)) == 1


def test_endpoint_cross_user_update_is_404_no_oracle(isolated_db, monkeypatch):
    alice = _user("alice-http@example.com")
    bob = _user("bob-http@example.com")
    a_item = add_checklist_item(alice["id"], ALERT, "Alice action")

    # Bob hits the real update endpoint aimed at Alice's item id.
    _auth_as(monkeypatch, bob)
    handler = _make_handler("POST", "/api/alerts/checklist/update")
    monkeypatch.setattr(handler, "_read_json_strict", lambda: ({"item_id": a_item["id"], "status": "done"}, None))
    handler._handle_alert_checklist_update()
    body, status = _last(handler)
    assert status == 404
    # The same 404 a genuinely missing item returns — no existence oracle.
    handler2 = _make_handler("POST", "/api/alerts/checklist/update")
    monkeypatch.setattr(handler2, "_read_json_strict", lambda: ({"item_id": 999999, "status": "done"}, None))
    handler2._handle_alert_checklist_update()
    body2, status2 = _last(handler2)
    assert status2 == 404
    assert body["message"] == body2["message"]


def test_endpoint_add_rejects_json_null_text(isolated_db, monkeypatch):
    # Regression: an explicit JSON null for `text` must be treated as empty (400),
    # never coerced to the string "None" and stored as a bogus action item.
    user = _user("nulltext@example.com")
    _auth_as(monkeypatch, user)
    add = _make_handler("POST", "/api/alerts/checklist")
    monkeypatch.setattr(add, "_read_json_strict", lambda: ({"alert_id": ALERT, "text": None, "assignee": None}, None))
    add._handle_alert_checklist_add()
    _body, status = _last(add)
    assert status == 400
    assert list_checklist_items(user["id"], ALERT) == []


def test_endpoint_get_and_add_roundtrip(isolated_db, monkeypatch):
    user = _user("http-crud@example.com")
    _auth_as(monkeypatch, user)

    add = _make_handler("POST", "/api/alerts/checklist")
    monkeypatch.setattr(add, "_read_json_strict", lambda: ({"alert_id": ALERT, "text": "Do the review"}, None))
    add._handle_alert_checklist_add()
    body, status = _last(add)
    assert status == 201 and body["ok"] and body["item"]["text"] == "Do the review"

    get = _make_handler("GET", f"/api/alerts/checklist?alert_id={ALERT}")
    get._handle_alert_checklist_get()
    gbody, gstatus = _last(get)
    assert gstatus == 200 and gbody["ok"]
    assert len(gbody["items"]) == 1
    # The GET carries the server-authored, guard-clean framing block.
    assert gbody["framing"] == FRAMING


# ── 3. bounded ───────────────────────────────────────────────────────────────────

def test_cap_enforced_per_alert(isolated_db):
    user = _user("cap@example.com")
    for i in range(MAX_ITEMS_PER_ALERT):
        assert add_checklist_item(user["id"], ALERT, f"Action {i}") is not None
    # The (cap+1)th is rejected.
    assert add_checklist_item(user["id"], ALERT, "One too many") is None
    assert len(list_checklist_items(user["id"], ALERT)) == MAX_ITEMS_PER_ALERT
    # A DIFFERENT alert has its own budget (cap is per-alert, not per-user).
    assert add_checklist_item(user["id"], "draft-other002", "Fresh budget") is not None


def test_text_is_length_capped(isolated_db):
    user = _user("caplen@example.com")
    item = add_checklist_item(user["id"], ALERT, "x" * (MAX_TEXT_LEN + 500))
    assert item is not None
    assert len(item["text"]) == MAX_TEXT_LEN


def test_alert_id_with_trailing_newline_is_rejected(isolated_db):
    # \Z hardening: Python's $ also matches before a trailing newline, which
    # would have let "…\n" through validation and stored a newline-bearing key.
    user = _user("newline@example.com")
    assert add_checklist_item(user["id"], ALERT + "\n", "Review the diff") is None
    assert list_checklist_items(user["id"], ALERT + "\n") == []


def test_aggregate_per_user_cap_enforced_across_alert_ids(isolated_db, monkeypatch):
    # Without the aggregate cap, the per-alert cap is a false bound: alert_id is
    # an opaque string, so fresh alert_ids would grow total rows without limit.
    # Shrink the constant (the SQL reads the module global at call time).
    monkeypatch.setattr(checklist, "MAX_ITEMS_PER_USER", 3)
    user = _user("aggcap@example.com")
    assert add_checklist_item(user["id"], "draft-agg001", "one") is not None
    assert add_checklist_item(user["id"], "draft-agg002", "two") is not None
    assert add_checklist_item(user["id"], "draft-agg003", "three") is not None
    # 4th item on a FRESH alert_id still hits the per-user aggregate bound.
    assert add_checklist_item(user["id"], "draft-agg004", "four") is None
    # The cap is owner-scoped: another user is unaffected.
    other = _user("aggcap-other@example.com")
    assert add_checklist_item(other["id"], "draft-agg001", "their own") is not None


# ── 4. legal-safety: audit log, framing guard, fail-soft ─────────────────────────

def test_each_mutation_writes_access_log(isolated_db):
    user = _user("audit@example.com")
    item = add_checklist_item(user["id"], ALERT, "Audited action")
    update_checklist_item(user["id"], item["id"], status="done")
    delete_checklist_item(user["id"], item["id"])

    actions = [(r["action"], r["actor_user_id"], r["result"]) for r in read_access_log(limit=100)]
    assert ("checklist.create", user["id"], "allow") in actions
    assert ("checklist.update", user["id"], "allow") in actions
    assert ("checklist.delete", user["id"], "allow") in actions


def test_logging_failure_does_not_break_the_mutation(isolated_db, monkeypatch):
    user = _user("resilient@example.com")

    import app.rbac_runtime as rbac_runtime

    def _boom(*a, **k):
        raise RuntimeError("access log unavailable")

    monkeypatch.setattr(rbac_runtime, "log_sensitive_action", _boom)
    # The mutation still commits and returns even though the audit write raises.
    item = add_checklist_item(user["id"], ALERT, "Still saved")
    assert item is not None
    assert list_checklist_items(user["id"], ALERT)[0]["text"] == "Still saved"


def test_app_framing_strings_pass_forbidden_claims_guard(isolated_db):
    # StatuteProof's OWN copy must never contain a banned claim. The item text is
    # the user's words and is deliberately NOT guarded here; only app framing is.
    for key, value in FRAMING.items():
        assert_no_forbidden_claims(value, label=f"checklist framing[{key}]")


def test_fail_soft_on_bad_input(isolated_db):
    user = _user("failsoft@example.com")
    # Invalid alert_id shapes → no write, benign return.
    assert add_checklist_item(user["id"], "", "text") is None
    assert add_checklist_item(user["id"], "has spaces!", "text") is None
    assert list_checklist_items(user["id"], "bad id") == []
    # Empty / whitespace text → rejected.
    assert add_checklist_item(user["id"], ALERT, "   ") is None
    # Unknown status on update → rejected (no silent no-op mutation).
    good = add_checklist_item(user["id"], ALERT, "Valid")
    assert update_checklist_item(user["id"], good["id"], status="archived") is None
    # Non-int identifiers never raise.
    assert list_checklist_items("not-an-int", ALERT) == []
    assert add_checklist_item("nope", ALERT, "text") is None
    assert update_checklist_item("nope", good["id"], status="done") is None
    assert delete_checklist_item(user["id"], "nope") is False
