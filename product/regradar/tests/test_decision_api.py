"""Sealed decision log — Stage 2 HTTP endpoints (auth, RBAC, binding, no-oracle).

Proves the API contract over the Stage-1 module (tests/test_decision_records.py
covers the seal/chain/tamper mechanics; this file covers the WIRING):

1. Auth — both endpoints reject an unauthenticated caller with 401.
2. Validation — a malformed ``alert_id`` is 400 on GET and POST.
3. RBAC asymmetry — POST (sealing) requires ``review.submit`` so an ``auditor``
   seat is denied 403 and nothing is sealed; GET (reading) deliberately does
   NOT require it, so the same auditor can read the org's decision log.
4. Tenancy — GET returns only the CALLER's org chain; another org's owner sees
   an empty list for the same alert id.
5. No-oracle — an unknown alert and another tenant's alert are the identical
   404 ("Alert not found.") on POST.
6. Evidence binding — an alert without a sealed proof block is refused with an
   honest 409; a sealed one binds ``content.reviewed`` = proof block verbatim
   + alert/source identity fields.
7. Bounds — an oversize statement is REJECTED (400) and nothing is written;
   the user's words are never truncated.
8. Legal — every NEW API-authored message string passes the forbidden-claims
   guard.

Harness mirrors tests/test_sealed_redline.py §6 / tests/test_rbac_stage2.py:
a bare ``_Handler`` instance with ``_send_json`` captured, a real throwaway
SQLite DB, and the owner-scoped alert loader monkeypatched at the api seam.
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
import app.decision_records as decision_records
import app.rbac_runtime as rbac_runtime
from app.api import _Handler
from app.auth import create_user
from app.decision_records import (
    MAX_STATEMENT_LEN,
    list_decisions,
    seal_decision,
    verify_decision_chain,
)
from app.legal_safety import assert_no_forbidden_claims
from app.rbac import ROLE_AUDITOR


# ── fixtures & harness ───────────────────────────────────────────────────────────

@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    """Point the DB layer AND the decision head-file base dir at a temp dir."""
    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "decision_api.db"))
    monkeypatch.setattr(decision_records, "_BASE_DIR", tmp_path)
    return tmp_path


ALERT = "draft-cbuae001"

# The shape find_routing_match_for_user returns for a proof-carrying alert
# (see app.alert_routing.normalize_alert_for_routing + app.alert_proof).
PROOF = {
    "evidence_record_id": "evr_cbuae_rulebook_run9",
    "record_hash": "sha256:" + "a" * 64,
    "run_id": "run9",
    "diff_available": True,
    "normalized_hash": "sha256:" + "b" * 64,
}


def _match(proof=PROOF):
    return {
        "alert_id": ALERT,
        "source_id": "cbuae_rulebook",
        "source_name": "CBUAE Rulebook",
        "source_url": "https://rulebook.centralbank.ae/en",
        "proof": dict(proof) if isinstance(proof, dict) else proof,
    }


def _make_handler(method: str = "GET", path: str = "/", body: dict | None = None) -> _Handler:
    header_map = {"Content-Length": "0", "X-Real-IP": "10.0.0.9"}
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
    if body is not None:
        handler._read_json_strict = lambda: (dict(body), None)  # type: ignore[method-assign]
    return handler


def _last(handler: _Handler) -> tuple[dict, int]:
    return handler._sent[-1]  # type: ignore[attr-defined]


def _auth_as(monkeypatch, user: dict) -> None:
    monkeypatch.setattr(api, "require_auth", lambda handler: dict(user))
    monkeypatch.setattr(api_alerts, "require_auth", lambda handler: dict(user))


def _new_owner(email: str, full_name: str | None = None) -> dict:
    user = create_user(email, "password-123", full_name=full_name)
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


def _seal_body(**overrides) -> dict:
    body = {
        "alert_id": ALERT,
        "kind": "reviewed",
        "statement": "I reviewed the diff against our licence scope.",
    }
    body.update(overrides)
    return body


@pytest.fixture()
def org_with_auditor(isolated_db):
    """An owner org plus an ``auditor`` seat (mirrors tests/test_rbac_stage2.py)."""
    owner = _new_owner("decision-owner@example.com", full_name="A. Rahman")
    org_id = _owned_org_id(owner["id"])
    auditor = create_user("decision-auditor@example.com", "password-123")
    result = rbac_runtime.assign_org_role(
        {"id": owner["id"]}, auditor["id"], org_id, ROLE_AUDITOR
    )
    assert result["ok"] is True and result["role"] == ROLE_AUDITOR
    return owner, auditor, org_id


# ── 1. auth ──────────────────────────────────────────────────────────────────────

def test_get_requires_auth(isolated_db, monkeypatch):
    monkeypatch.setattr(api, "require_auth", lambda handler: None)
    monkeypatch.setattr(api_alerts, "require_auth", lambda handler: None)
    handler = _make_handler("GET", f"/api/alerts/decisions?alert_id={ALERT}")
    handler._handle_alert_decisions_get()
    _, status = _last(handler)
    assert status == 401


def test_post_requires_auth(isolated_db, monkeypatch):
    monkeypatch.setattr(api, "require_auth", lambda handler: None)
    monkeypatch.setattr(api_alerts, "require_auth", lambda handler: None)
    handler = _make_handler("POST", "/api/alerts/decisions", body=_seal_body())
    handler._handle_alert_decisions_post()
    _, status = _last(handler)
    assert status == 401


# ── 2. validation ────────────────────────────────────────────────────────────────

def test_get_rejects_malformed_alert_id(isolated_db, monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/alerts/decisions?alert_id=..%2F..%2Fetc")
    handler._handle_alert_decisions_get()
    _, status = _last(handler)
    assert status == 400


def test_post_rejects_malformed_alert_id(isolated_db, monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler(
        "POST", "/api/alerts/decisions", body=_seal_body(alert_id="../../etc")
    )
    handler._handle_alert_decisions_post()
    _, status = _last(handler)
    assert status == 400


def test_post_rejects_invalid_kind_and_missing_statement(isolated_db, monkeypatch):
    owner = _new_owner("kinds@example.com")
    _auth_as(monkeypatch, {"id": owner["id"], "email": owner["email"]})

    handler = _make_handler("POST", "/api/alerts/decisions", body=_seal_body(kind="approved"))
    handler._handle_alert_decisions_post()
    body, status = _last(handler)
    assert status == 400 and body["message"] == "Invalid decision kind."

    handler2 = _make_handler("POST", "/api/alerts/decisions", body=_seal_body(statement="   "))
    handler2._handle_alert_decisions_post()
    body2, status2 = _last(handler2)
    assert status2 == 400 and body2["message"] == "A decision statement is required."


def test_post_rejects_correction_without_its_reason(isolated_db, monkeypatch):
    owner = _new_owner("pairing@example.com")
    _auth_as(monkeypatch, {"id": owner["id"], "email": owner["email"]})

    handler = _make_handler(
        "POST", "/api/alerts/decisions",
        body=_seal_body(supersedes_decision_id="dec_1_1_deadbeefdeadbeefdead"),
    )
    handler._handle_alert_decisions_post()
    body, status = _last(handler)
    assert status == 400
    assert "correction" in body["message"].lower()
    assert list_decisions(_owned_org_id(owner["id"])) == []


def test_post_oversize_statement_is_rejected_never_truncated(isolated_db, monkeypatch):
    owner = _new_owner("bounds@example.com")
    org_id = _owned_org_id(owner["id"])
    _auth_as(monkeypatch, {"id": owner["id"], "email": owner["email"]})
    monkeypatch.setattr(api_alerts, "find_routing_match_for_user", lambda *a, **k: _match())

    handler = _make_handler(
        "POST", "/api/alerts/decisions",
        body=_seal_body(statement="x" * (MAX_STATEMENT_LEN + 1)),
    )
    handler._handle_alert_decisions_post()
    body, status = _last(handler)
    assert status == 400
    assert "nothing was recorded" in body["message"].lower()
    assert list_decisions(org_id) == []  # rejected, not silently truncated


# ── 3. RBAC asymmetry (auditor: read yes, seal no) ───────────────────────────────

def test_auditor_post_is_denied_403_and_nothing_is_sealed(org_with_auditor, monkeypatch):
    _owner, auditor, org_id = org_with_auditor
    _auth_as(monkeypatch, {"id": auditor["id"], "email": auditor["email"]})
    monkeypatch.setattr(
        api_alerts, "find_routing_match_for_user",
        lambda *a, **k: pytest.fail("auditor seal reached the alert loader"),
    )
    handler = _make_handler("POST", "/api/alerts/decisions", body=_seal_body())
    handler._handle_alert_decisions_post()
    _, status = _last(handler)
    assert status == 403
    assert list_decisions(org_id) == []


def test_auditor_get_list_works_without_review_submit(org_with_auditor, monkeypatch):
    owner, auditor, org_id = org_with_auditor
    sealed = seal_decision(
        owner["id"], org_id,
        display_name="A. Rahman",
        reviewed=dict(PROOF, alert_id=ALERT),
        kind="reviewed",
        statement="Owner's sealed review note.",
    )
    assert sealed is not None

    _auth_as(monkeypatch, {"id": auditor["id"], "email": auditor["email"]})
    handler = _make_handler("GET", f"/api/alerts/decisions?alert_id={ALERT}")
    handler._handle_alert_decisions_get()
    body, status = _last(handler)
    assert status == 200 and body["ok"] is True
    assert [d["decision_id"] for d in body["decisions"]] == [sealed["decision_id"]]
    assert body["framing"] == decision_records.FRAMING
    assert body["kinds"] == list(decision_records.KINDS)
    assert body["chain"]["decision_id"] == sealed["decision_id"]


# ── 4. tenancy ───────────────────────────────────────────────────────────────────

def test_get_is_org_scoped(isolated_db, monkeypatch):
    owner_a = _new_owner("tenant-a@example.com")
    owner_b = _new_owner("tenant-b@example.com")
    org_a = _owned_org_id(owner_a["id"])
    sealed = seal_decision(
        owner_a["id"], org_a,
        display_name="Tenant A",
        reviewed=dict(PROOF, alert_id=ALERT),
        kind="reviewed",
        statement="Org A's decision.",
    )
    assert sealed is not None

    _auth_as(monkeypatch, {"id": owner_b["id"], "email": owner_b["email"]})
    handler = _make_handler("GET", f"/api/alerts/decisions?alert_id={ALERT}")
    handler._handle_alert_decisions_get()
    body, status = _last(handler)
    assert status == 200
    assert body["decisions"] == []  # another org's chain is invisible
    assert body["chain"] is None


# ── 5. no-oracle 404 + evidence binding ──────────────────────────────────────────

def test_post_unknown_alert_is_404_no_oracle(isolated_db, monkeypatch):
    owner = _new_owner("noalert@example.com")
    _auth_as(monkeypatch, {"id": owner["id"], "email": owner["email"]})
    seen: list[tuple[int, str]] = []

    def fake_find(user_id, alert_id, days=14):
        seen.append((user_id, alert_id))
        return None  # unknown OR another tenant's — indistinguishable

    monkeypatch.setattr(api_alerts, "find_routing_match_for_user", fake_find)
    handler = _make_handler("POST", "/api/alerts/decisions", body=_seal_body())
    handler._handle_alert_decisions_post()
    body, status = _last(handler)
    assert status == 404
    assert body["message"] == "Alert not found."
    assert seen[0] == (owner["id"], ALERT)  # scope key from the session, not the body
    assert list_decisions(_owned_org_id(owner["id"])) == []


def test_post_alert_without_proof_is_refused_409(isolated_db, monkeypatch):
    owner = _new_owner("noproof@example.com")
    _auth_as(monkeypatch, {"id": owner["id"], "email": owner["email"]})
    monkeypatch.setattr(api_alerts, "find_routing_match_for_user", lambda *a, **k: _match(proof=None))

    handler = _make_handler("POST", "/api/alerts/decisions", body=_seal_body())
    handler._handle_alert_decisions_post()
    body, status = _last(handler)
    assert status == 409
    assert body["message"] == "This alert has no sealed evidence record to bind a decision to."
    assert list_decisions(_owned_org_id(owner["id"])) == []


# ── 6. happy path: seal + reviewed binding + amend ───────────────────────────────

def test_happy_path_seals_and_binds_reviewed_from_the_match(isolated_db, monkeypatch):
    from app.plan import activate_plan

    owner = _new_owner("sealer@example.com", full_name="A. Rahman")
    # The sealed ``reviewed`` block carries the official URL only for a
    # plan-eligible account — the same entitlement boundary as every other
    # reader of official-source content (see
    # tests/test_alert_plan_gating.py::test_free_account_decision_does_not_echo_official_url).
    activate_plan(owner["id"], "professional")
    org_id = _owned_org_id(owner["id"])
    _auth_as(
        monkeypatch,
        {"id": owner["id"], "email": owner["email"], "full_name": "A. Rahman"},
    )
    monkeypatch.setattr(api_alerts, "find_routing_match_for_user", lambda *a, **k: _match())

    handler = _make_handler("POST", "/api/alerts/decisions", body=_seal_body())
    handler._handle_alert_decisions_post()
    body, status = _last(handler)
    assert status == 201 and body["ok"] is True

    record = body["decision"]
    content = record["content"]
    # The binding: proof block VERBATIM + the alert/source identity fields.
    assert content["reviewed"] == {
        **PROOF,
        "alert_id": ALERT,
        "source_id": "cbuae_rulebook",
        "source_name": "CBUAE Rulebook",
        "official_url": "https://rulebook.centralbank.ae/en",
    }
    # The user's words, verbatim; identity from the session.
    assert content["decision"]["statement"] == "I reviewed the diff against our licence scope."
    assert content["decided_by"] == {"user_id": owner["id"], "display_name": "A. Rahman"}
    assert content["org_id"] == org_id
    assert verify_decision_chain(org_id)["ok"] is True

    # And the GET path lists it for the same org.
    get_handler = _make_handler("GET", f"/api/alerts/decisions?alert_id={ALERT}")
    get_handler._handle_alert_decisions_get()
    get_body, get_status = _last(get_handler)
    assert get_status == 200
    assert [d["decision_id"] for d in get_body["decisions"]] == [record["decision_id"]]


def test_display_name_falls_back_to_email(isolated_db, monkeypatch):
    owner = _new_owner("noname@example.com")  # no full_name on the account
    _auth_as(monkeypatch, {"id": owner["id"], "email": owner["email"], "full_name": None})
    monkeypatch.setattr(api_alerts, "find_routing_match_for_user", lambda *a, **k: _match())

    handler = _make_handler("POST", "/api/alerts/decisions", body=_seal_body())
    handler._handle_alert_decisions_post()
    body, status = _last(handler)
    assert status == 201
    assert body["decision"]["content"]["decided_by"]["display_name"] == "noname@example.com"


def test_amend_flow_seals_a_linked_correction(isolated_db, monkeypatch):
    owner = _new_owner("amender@example.com", full_name="A. Rahman")
    org_id = _owned_org_id(owner["id"])
    _auth_as(
        monkeypatch,
        {"id": owner["id"], "email": owner["email"], "full_name": "A. Rahman"},
    )
    monkeypatch.setattr(api_alerts, "find_routing_match_for_user", lambda *a, **k: _match())

    first = _make_handler("POST", "/api/alerts/decisions", body=_seal_body())
    first._handle_alert_decisions_post()
    original = _last(first)[0]["decision"]

    second = _make_handler(
        "POST", "/api/alerts/decisions",
        body=_seal_body(
            statement="On re-reading, section 4 does affect our reporting form.",
            supersedes_decision_id=original["decision_id"],
            amendment_reason="I misread the scope of section 4 in my earlier entry.",
        ),
    )
    second._handle_alert_decisions_post()
    body, status = _last(second)
    assert status == 201
    content = body["decision"]["content"]
    assert content["supersedes_decision_id"] == original["decision_id"]
    assert content["amendment_reason"].startswith("I misread")
    assert verify_decision_chain(org_id)["ok"] is True
    assert len(list_decisions(org_id)) == 2  # the original stays


# ── 7. legal: every NEW API-authored string is guard-clean ───────────────────────

def test_new_api_messages_pass_forbidden_claims_guard():
    messages = [
        "Invalid decision kind.",
        "A decision statement is required.",
        "The correction reason must be text.",
        "A correction needs both the earlier decision and your reason for correcting it.",
        "Your workspace could not be resolved. Please retry.",
        "This alert has no sealed evidence record to bind a decision to.",
        "The decision could not be sealed. Nothing was recorded — check the entry and try again.",
        (
            f"The statement is longer than the {MAX_STATEMENT_LEN}-character limit. "
            "It is sealed exactly as written, so nothing was recorded — please "
            "shorten it and try again."
        ),
    ]
    for message in messages:
        assert_no_forbidden_claims(message, label="decision api message")
