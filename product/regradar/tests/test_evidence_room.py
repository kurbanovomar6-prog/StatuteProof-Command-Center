"""Auditor Evidence Room — the external, time-boxed, read-only share surface.

This is a NEW EXTERNAL AUTHORIZATION SURFACE, so the suite is adversarial:

* creation is owner/admin-gated (``evidence.share`` in the RBAC matrix),
  entitlement-clipped (another tenant's custom source can never enter the
  scope) and bounded (an oversized scope is rejected at creation);
* the URL token is stored ONLY as a SHA-256 hash — the raw token must not
  appear anywhere in the database file;
* expired, revoked, and garbage tokens all resolve to the SAME 404 envelope
  (no existence oracle);
* the room view NEVER contains a record outside the frozen scope;
* every room access appends an immutable ``room.view`` access-log row;
* there is NO mutation route under /api/room/ (read-only by construction);
* the examiner-facing view carries the FULL standard disclaimer and its
  authored prose passes the shared forbidden-claims guard.

Reuses the proven harnesses: the real canonical-record writer from
``tests/test_evidence_pack.py``, the throwaway-DB + handler pattern from
``tests/test_rbac_stage2.py``, and the mocked sources.json tenancy pattern
from ``tests/test_evidence_endpoint_tenancy.py``.
"""

from __future__ import annotations

import hashlib
import json
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.api as api
import app.db as app_db
import app.evidence_room as evidence_room
from app.access_log import read_access_log
from app.api import _Handler, _RateLimiter
from app.auth import create_user
from app.evidence_pack import assert_no_forbidden_claims
from app.evidence_records import create_canonical_evidence_record
from app.evidence_room import (
    DEFAULT_EXPIRY_DAYS,
    MAX_EXPIRY_DAYS,
    ROOM_HEADER_NOTE,
    ROOM_VIEW_ACTION,
    VERIFICATION_NOTE,
    create_share,
    get_room_view,
    list_shares,
    revoke_share,
)
from app.rbac_runtime import assign_org_role


# ── fixtures ────────────────────────────────────────────────────────────────────

_OWNER_ID = 1
_ATTACKER_ID = 2

# Tenancy world: one official (shared) source, one custom source owned by the
# ATTACKER (must never enter user 1's share), one custom source owned by user 1.
_SOURCES = [
    {"source_id": "official-cbuae", "name": "CBUAE Rulebook", "url": "https://example.gov/cbuae", "enabled": True},
    {"source_id": "custom-1111aaaa", "name": "Victim private source", "custom": True, "owner_user_id": _ATTACKER_ID, "url": "https://victim.example/x"},
    {"source_id": "custom-2222bbbb", "name": "My private source", "custom": True, "owner_user_id": _OWNER_ID, "url": "https://mine.example/y"},
]


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    """Point the whole DB layer (users, shares, access_log) at a temp file."""
    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "evidence_room.db"))
    return tmp_path / "evidence_room.db"


@pytest.fixture()
def entitled(monkeypatch):
    """Grant a generous plan source limit and mock the sources.json world."""
    monkeypatch.setattr("app.plan.source_limit_for", lambda uid: 100)
    monkeypatch.setattr("app.source_intake.load_sources_json", lambda: list(_SOURCES))


def _write(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _make_record(
    base: Path,
    *,
    source_id: str,
    run_id: str,
    timestamp: str,
    market: str = "AE",
    text: str = "Current official regulatory text captured for evidence.",
) -> dict:
    """Real complete/VERIFIED canonical record via the product writer (mirrors
    tests/test_evidence_pack.py so the room is exercised on genuine objects)."""
    run_dir = base / "data" / "source_snapshots" / timestamp[:10] / market / source_id / run_id
    normalized_hash = _write(run_dir / "normalized.txt", text)
    _write(run_dir / "raw.txt", f"<main>{text}</main>")
    _write(run_dir / "metadata.json", json.dumps({"provider": "fixture"}, sort_keys=True))
    _write(run_dir / "proof.json", json.dumps({"proof_quality": "GOOD"}, sort_keys=True))
    run = {
        "run_id": run_id,
        "timestamp_utc": timestamp,
        "market": market,
        "source_id": source_id,
        "source_name": f"{source_id} Source",
        "category": "regulatory",
        "official_url": f"https://example.gov/{source_id}",
        "access_status": "accessible",
        "fetch_method": "fixture",
        "extraction_quality": "GOOD",
        "change_status": "FIRST_SEEN",
        "normalized_hash": normalized_hash,
        "snapshot_raw_path": str((run_dir / "raw.txt").relative_to(base)),
        "snapshot_normalized_path": str((run_dir / "normalized.txt").relative_to(base)),
        "snapshot_metadata_path": str((run_dir / "metadata.json").relative_to(base)),
        "proof_block_path": str((run_dir / "proof.json").relative_to(base)),
    }
    return create_canonical_evidence_record(run, base_dir=base)


def _create_ok(tmp_path, user_id=_OWNER_ID, sources=("official-cbuae",), **kw) -> dict:
    result = create_share(
        {"id": user_id},
        list(sources),
        "2026-03-01",
        "2026-03-31",
        base_dir=tmp_path,
        **kw,
    )
    assert result["ok"] is True, result
    return result


def _room_view_rows(share_id: int) -> list[dict]:
    return [
        row
        for row in read_access_log(limit=1000)
        if row["action"] == ROOM_VIEW_ACTION and row["resource_id"] == str(share_id)
    ]


# ── handler harness (mirrors tests/test_rbac_stage2.py) ─────────────────────────

def _make_handler(method: str = "POST", path: str = "/", body: dict | None = None) -> _Handler:
    raw_body = json.dumps(body or {}).encode()
    header_map = {"Content-Length": str(len(raw_body)), "X-Real-IP": "203.0.113.7"}
    handler = _Handler.__new__(_Handler)
    handler.command = method
    handler.path = path
    handler.request = MagicMock()
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(raw_body)
    handler.wfile = BytesIO()
    handler.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": header_map.get(key, default)
    handler.headers = hdrs

    sent: list[tuple[dict, int]] = []
    handler._send_json = lambda data, status=200, **kw: sent.append((data, status))  # type: ignore[method-assign]
    handler._sent = sent  # type: ignore[attr-defined]
    return handler


def _auth_as(monkeypatch, user: dict | None) -> None:
    monkeypatch.setattr(api, "require_auth", lambda handler: dict(user) if user else None)


def _fresh_limiters(monkeypatch) -> None:
    """Isolate the shared module-level limiters from other tests' hits."""
    monkeypatch.setattr(api, "_EXPORT_LIMITER", _RateLimiter(1000, 3600))
    monkeypatch.setattr(api, "_ROOM_LIMITER", _RateLimiter(1000, 3600))


# ── token lifecycle: creation → hash-only storage ────────────────────────────────

def test_create_share_returns_token_once_and_stores_only_its_hash(isolated_db, entitled, tmp_path):
    _make_record(tmp_path, source_id="official-cbuae", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = _create_ok(tmp_path)

    token = result["token"]
    assert len(token) >= 40  # token_urlsafe(32) → 43 chars

    conn = app_db._connect()
    try:
        row = conn.execute("SELECT * FROM evidence_shares WHERE id = ?", (result["share_id"],)).fetchone()
    finally:
        conn.close()
    assert row["token_hash"] == hashlib.sha256(token.encode()).hexdigest()

    # The raw token must not exist ANYWHERE in the database file — a DB read
    # (backup leak, stray SELECT) can never yield a usable link.
    db_bytes = Path(isolated_db).read_bytes()
    assert token.encode() not in db_bytes
    assert row["token_hash"].encode() in db_bytes  # sanity: we read the right file


def test_create_share_expiry_defaults_and_bounds(isolated_db, entitled, tmp_path):
    _make_record(tmp_path, source_id="official-cbuae", run_id="run-001", timestamp="2026-03-15T10:00:00Z")

    default = _create_ok(tmp_path)
    created = evidence_room._parse_ts(default["created_at"])
    expires = evidence_room._parse_ts(default["expires_at"])
    assert (expires - created).days == DEFAULT_EXPIRY_DAYS

    for bad in (0, -5, MAX_EXPIRY_DAYS + 1, "soon", 10.5):
        result = create_share(
            {"id": _OWNER_ID}, ["official-cbuae"], "2026-03-01", "2026-03-31",
            base_dir=tmp_path, expires_days=bad,
        )
        assert result["ok"] is False, f"expires_days={bad!r} must be rejected"
        assert result["error"] == "invalid_expiry"

    ok_max = _create_ok(tmp_path, expires_days=MAX_EXPIRY_DAYS)
    assert ok_max["ok"] is True


def test_create_share_validates_scope_inputs(isolated_db, entitled, tmp_path):
    bad_ids = create_share({"id": _OWNER_ID}, [], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    assert bad_ids["ok"] is False and bad_ids["error"] == "invalid"

    bad_dates = create_share({"id": _OWNER_ID}, ["official-cbuae"], "2026-06-30", "2026-01-01", base_dir=tmp_path)
    assert bad_dates["ok"] is False and bad_dates["error"] == "invalid"

    no_user = create_share({}, ["official-cbuae"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    assert no_user["ok"] is False and no_user["error"] == "forbidden"


# ── entitlement at creation: cross-tenant clipping ───────────────────────────────

def test_create_share_clips_out_another_tenants_custom_source(isolated_db, entitled, tmp_path):
    """Naming the victim's custom source must silently drop it from the frozen
    scope — entitlement is applied at CREATION, the moment the scope is sealed."""
    _make_record(tmp_path, source_id="official-cbuae", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = _create_ok(tmp_path, sources=("official-cbuae", "custom-1111aaaa"))
    assert result["source_ids"] == ["official-cbuae"]
    assert "custom-1111aaaa" not in result["source_ids"]


def test_create_share_only_foreign_custom_source_is_refused(isolated_db, entitled, tmp_path):
    result = create_share(
        {"id": _OWNER_ID}, ["custom-1111aaaa"], "2026-03-01", "2026-03-31", base_dir=tmp_path
    )
    assert result["ok"] is False
    assert result["error"] == "no_entitled_sources"


def test_create_share_own_custom_source_is_allowed(isolated_db, entitled, tmp_path):
    result = _create_ok(tmp_path, sources=("custom-2222bbbb",))
    assert result["source_ids"] == ["custom-2222bbbb"]


def test_create_share_respects_plan_source_limit(isolated_db, monkeypatch, tmp_path):
    monkeypatch.setattr("app.source_intake.load_sources_json", lambda: list(_SOURCES))
    monkeypatch.setattr("app.plan.source_limit_for", lambda uid: 1)
    result = _create_ok(tmp_path, sources=("official-cbuae", "custom-2222bbbb"))
    assert result["source_ids"] == ["official-cbuae"]  # truncated to the plan limit


# ── bounded at creation ──────────────────────────────────────────────────────────

def test_create_share_rejects_oversized_scope(isolated_db, entitled, tmp_path):
    for i in range(3):
        _make_record(
            tmp_path, source_id="official-cbuae", run_id=f"run-{i:03d}",
            timestamp=f"2026-03-1{i}T10:00:00Z",
        )
    result = create_share(
        {"id": _OWNER_ID}, ["official-cbuae"], "2026-03-01", "2026-03-31",
        base_dir=tmp_path, max_records=2,
    )
    assert result["ok"] is False
    assert result["error"] == "too_large"
    assert result["max_records"] == 2


# ── legal safety at creation ─────────────────────────────────────────────────────

def test_create_share_rejects_forbidden_claim_in_display_name(isolated_db, entitled, tmp_path):
    _make_record(tmp_path, source_id="official-cbuae", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = create_share(
        {"id": _OWNER_ID}, ["official-cbuae"], "2026-03-01", "2026-03-31",
        base_dir=tmp_path, org_display_name="Acme — we guarantee compliance",
    )
    assert result["ok"] is False
    assert result["error"] == "forbidden_claim"


def test_room_authored_prose_passes_forbidden_claims_guard():
    # The examiner-facing authored strings must never trip the shared guard.
    assert_no_forbidden_claims(ROOM_HEADER_NOTE)
    assert_no_forbidden_claims(VERIFICATION_NOTE)


# ── the room view: frozen scope, honest content ──────────────────────────────────

def test_room_view_shows_only_the_frozen_scope(isolated_db, entitled, tmp_path):
    """Adversarial: evidence exists for the victim's custom source and for an
    out-of-scope official source — NEITHER may appear in the room."""
    _make_record(tmp_path, source_id="official-cbuae", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    _make_record(tmp_path, source_id="custom-1111aaaa", run_id="run-vic", timestamp="2026-03-16T10:00:00Z")
    _make_record(tmp_path, source_id="official-other", run_id="run-oth", timestamp="2026-03-17T10:00:00Z")
    # In range for the source but the share is created for March only:
    _make_record(tmp_path, source_id="official-cbuae", run_id="run-apr", timestamp="2026-04-02T10:00:00Z")

    result = _create_ok(tmp_path)
    view = get_room_view(result["token"], base_dir=tmp_path)
    assert view is not None

    source_ids = {r["source_id"] for r in view["records"]}
    assert source_ids == {"official-cbuae"}
    assert view["record_count"] == 1
    record = view["records"][0]
    assert record["record_hash"].startswith("sha256:")
    # The per-record normalized-content hash — the value /verify checks — is
    # always exposed so the examiner has a verifiable value per record.
    assert record["normalized_hash"].startswith("sha256:")
    assert record["timestamp"] == "2026-03-15T10:00:00Z"
    assert record["record_id"]
    # No snapshot bytes ever leave the server through the room.
    assert "raw_bytes" not in record and "normalized_bytes" not in record

    # Coverage summary is scope-honest.
    assert view["coverage"]["sources_in_scope"] == 1
    assert view["coverage"]["total_records"] == 1

    # Examiner-facing legal framing: BOTH disclaimers, plus verify pointers.
    assert view["disclaimer"] == "Monitoring intelligence only. Not legal advice."
    assert "does not guarantee compliance" in view["legal_notice"]
    assert view["verification"]["verify_url"] == "/verify"
    assert view["verification"]["spec_url"] == "/api/verify-spec"


def test_room_view_never_leaks_owner_identity_or_token(isolated_db, entitled, tmp_path):
    _make_record(tmp_path, source_id="official-cbuae", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = _create_ok(tmp_path)  # no org_display_name supplied
    view = get_room_view(result["token"], base_dir=tmp_path)
    assert view["shared_by"] is None  # nothing beyond what the owner chose
    flat = json.dumps(view)
    assert result["token"] not in flat
    assert "token" not in view
    assert "owner_user_id" not in flat


def test_room_view_optional_display_name_is_shown_when_chosen(isolated_db, entitled, tmp_path):
    _make_record(tmp_path, source_id="official-cbuae", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = _create_ok(tmp_path, org_display_name="Acme Exchange FZE")
    view = get_room_view(result["token"], base_dir=tmp_path)
    assert view["shared_by"] == "Acme Exchange FZE"


# ── token resolution: no existence oracle ────────────────────────────────────────

def test_expired_revoked_and_garbage_tokens_all_resolve_to_none(isolated_db, entitled, tmp_path):
    _make_record(tmp_path, source_id="official-cbuae", run_id="run-001", timestamp="2026-03-15T10:00:00Z")

    # Expired: force expiry into the past directly in the DB.
    expired = _create_ok(tmp_path)
    conn = app_db._connect()
    try:
        conn.execute(
            "UPDATE evidence_shares SET expires_at = '2020-01-01T00:00:00+00:00' WHERE id = ?",
            (expired["share_id"],),
        )
        conn.commit()
    finally:
        conn.close()
    assert get_room_view(expired["token"], base_dir=tmp_path) is None

    # Revoked.
    revoked = _create_ok(tmp_path)
    assert revoke_share({"id": _OWNER_ID}, revoked["share_id"])["ok"] is True
    assert get_room_view(revoked["token"], base_dir=tmp_path) is None

    # Garbage / malformed / traversal-shaped tokens.
    for garbage in ("A" * 43, "short", "", None, "../../../etc/passwd", "abc/def" + "x" * 40, "x" * 500):
        assert get_room_view(garbage, base_dir=tmp_path) is None


def test_unparsable_expiry_fails_closed(isolated_db, entitled, tmp_path):
    _make_record(tmp_path, source_id="official-cbuae", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = _create_ok(tmp_path)
    conn = app_db._connect()
    try:
        conn.execute(
            "UPDATE evidence_shares SET expires_at = 'not-a-timestamp' WHERE id = ?",
            (result["share_id"],),
        )
        conn.commit()
    finally:
        conn.close()
    assert get_room_view(result["token"], base_dir=tmp_path) is None


# ── immutable audit trail of the audit ───────────────────────────────────────────

def test_room_view_appends_immutable_access_log_rows(isolated_db, entitled, tmp_path):
    _make_record(tmp_path, source_id="official-cbuae", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = _create_ok(tmp_path)

    assert get_room_view(result["token"], base_dir=tmp_path) is not None
    allow_rows = _room_view_rows(result["share_id"])
    assert len(allow_rows) == 1
    assert allow_rows[0]["result"] == "allow"
    assert allow_rows[0]["actor_user_id"] is None  # external viewer, no account
    assert allow_rows[0]["resource_type"] == "evidence_share"

    # A revoked share's access is denied AND recorded against the share id.
    revoke_share({"id": _OWNER_ID}, result["share_id"])
    assert get_room_view(result["token"], base_dir=tmp_path) is None
    rows = _room_view_rows(result["share_id"])
    assert [r["result"] for r in rows][:1] == ["deny"]  # newest first

    # A well-formed but unknown token is recorded as a deny with no share id.
    assert get_room_view("B" * 43, base_dir=tmp_path) is None
    anon_denies = [
        r for r in read_access_log(limit=1000)
        if r["action"] == ROOM_VIEW_ACTION and r["result"] == "deny" and r["resource_id"] == ""
    ]
    assert len(anon_denies) == 1


# ── owner-scoped management ──────────────────────────────────────────────────────

def test_revoke_is_owner_scoped_with_no_existence_oracle(isolated_db, entitled, tmp_path):
    _make_record(tmp_path, source_id="official-cbuae", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = _create_ok(tmp_path)

    # Another user revoking → indistinguishable from a nonexistent share.
    stranger = revoke_share({"id": _ATTACKER_ID}, result["share_id"])
    assert stranger == revoke_share({"id": _ATTACKER_ID}, 999_999)
    assert stranger["ok"] is False and stranger["error"] == "not_found"
    # ... and the share still works.
    assert get_room_view(result["token"], base_dir=tmp_path) is not None

    # The owner's revoke lands, and is idempotent.
    first = revoke_share({"id": _OWNER_ID}, result["share_id"])
    assert first["ok"] is True and first["already_revoked"] is False
    second = revoke_share({"id": _OWNER_ID}, result["share_id"])
    assert second["ok"] is True and second["already_revoked"] is True
    assert get_room_view(result["token"], base_dir=tmp_path) is None


def test_list_shares_is_own_only_and_never_leaks_tokens(isolated_db, entitled, tmp_path):
    _make_record(tmp_path, source_id="official-cbuae", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    mine = _create_ok(tmp_path)
    _create_ok(tmp_path, user_id=_ATTACKER_ID)  # someone else's share

    listing = list_shares({"id": _OWNER_ID})
    assert listing["ok"] is True
    assert [s["share_id"] for s in listing["shares"]] == [mine["share_id"]]
    flat = json.dumps(listing)
    assert mine["token"] not in flat
    assert "token" not in flat  # neither raw token nor token_hash is listed
    assert listing["shares"][0]["status"] == "active"

    revoke_share({"id": _OWNER_ID}, mine["share_id"])
    assert list_shares({"id": _OWNER_ID})["shares"][0]["status"] == "revoked"


# ── HTTP layer: RBAC governance gate + uniform 404 + read-only ───────────────────

def _seed_owner_and_auditor():
    """Real users + memberships: user 1 owns an org; user 2 is its auditor.

    The auditor is created AFTER the backfill so they own no org-of-one and
    resolve purely to the auditor seat (mirrors tests/test_rbac_stage2.py).
    """
    owner = create_user("owner@example.com", "password-123")
    app_db.backfill_org_memberships()
    conn = app_db._connect()
    try:
        org_id = int(
            conn.execute(
                "SELECT id FROM orgs WHERE owner_user_id = ?", (int(owner["id"]),)
            ).fetchone()["id"]
        )
    finally:
        conn.close()
    seat = create_user("auditor@example.com", "password-123")
    assigned = assign_org_role(owner, int(seat["id"]), org_id, "auditor")
    assert assigned["ok"] is True
    return owner, seat


def test_share_create_endpoint_requires_auth(isolated_db, monkeypatch):
    _fresh_limiters(monkeypatch)
    _auth_as(monkeypatch, None)
    handler = _make_handler(body={"source_ids": ["official-cbuae"]})
    handler._handle_evidence_room_share_create()
    assert handler._sent[-1][1] == 401


def test_share_create_endpoint_denies_auditor_role(isolated_db, entitled, monkeypatch, tmp_path):
    """The governance gate: an auditor seat may READ evidence but must never be
    able to mint an external share. Denied 403 + immutable access-log row."""
    owner, seat = _seed_owner_and_auditor()
    _fresh_limiters(monkeypatch)
    monkeypatch.setattr("app.plan.has_capability", lambda uid, cap: True)
    monkeypatch.setattr(evidence_room, "_BASE_DIR", tmp_path)

    _auth_as(monkeypatch, seat)
    handler = _make_handler(body={
        "source_ids": ["official-cbuae"], "date_from": "2026-03-01", "date_to": "2026-03-31",
    })
    handler._handle_evidence_room_share_create()
    assert handler._sent[-1][1] == 403

    denies = [
        r for r in read_access_log(limit=100)
        if r["action"] == "evidence.share" and r["result"] == "deny"
    ]
    assert len(denies) == 1 and denies[0]["actor_user_id"] == int(seat["id"])


def test_share_create_endpoint_owner_succeeds(isolated_db, entitled, monkeypatch, tmp_path):
    owner, _seat = _seed_owner_and_auditor()
    _make_record(tmp_path, source_id="official-cbuae", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    _fresh_limiters(monkeypatch)
    monkeypatch.setattr("app.plan.has_capability", lambda uid, cap: True)
    monkeypatch.setattr("app.plan.source_limit_for", lambda uid: 100)
    monkeypatch.setattr(evidence_room, "_BASE_DIR", tmp_path)

    _auth_as(monkeypatch, owner)
    handler = _make_handler(body={
        "source_ids": ["official-cbuae"], "date_from": "2026-03-01", "date_to": "2026-03-31",
    })
    handler._handle_evidence_room_share_create()
    payload, status = handler._sent[-1]
    assert status == 201, payload
    assert payload["ok"] is True and payload["token"]

    # The freshly minted token opens the public room through the real GET route.
    viewer = _make_handler(method="GET", path=f"/api/room/{payload['token']}")
    viewer.do_GET()
    view_payload, view_status = viewer._sent[-1]
    assert view_status == 200
    assert view_payload["room"]["records"][0]["source_id"] == "official-cbuae"


def test_share_create_gate_fails_closed_on_rbac_error(isolated_db, entitled, monkeypatch, tmp_path):
    """Governance action: if RBAC evaluation itself ERRORS, minting an external
    evidence-room credential must be DENIED (403), never allowed — unlike the
    default fail-open mutation gate. (Security review 2026-07-12.)"""
    owner, _seat = _seed_owner_and_auditor()
    _fresh_limiters(monkeypatch)
    monkeypatch.setattr("app.plan.has_capability", lambda uid, cap: True)
    monkeypatch.setattr(evidence_room, "_BASE_DIR", tmp_path)
    # Force the RBAC evaluate to blow up on the share-create gate.
    import app.rbac_runtime as rr
    monkeypatch.setattr(rr, "evaluate", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))

    _auth_as(monkeypatch, owner)
    handler = _make_handler(body={
        "source_ids": ["official-cbuae"], "date_from": "2026-03-01", "date_to": "2026-03-31",
    })
    handler._handle_evidence_room_share_create()
    # fail_closed → 403, and no share was minted.
    assert handler._sent[-1][1] == 403
    assert evidence_room.list_shares(owner)["shares"] == []


def test_share_create_endpoint_requires_plan_capability(isolated_db, entitled, monkeypatch, tmp_path):
    owner, _seat = _seed_owner_and_auditor()
    _fresh_limiters(monkeypatch)
    monkeypatch.setattr("app.plan.has_capability", lambda uid, cap: False)
    _auth_as(monkeypatch, owner)
    handler = _make_handler(body={
        "source_ids": ["official-cbuae"], "date_from": "2026-03-01", "date_to": "2026-03-31",
    })
    handler._handle_evidence_room_share_create()
    assert handler._sent[-1][1] == 403


def test_room_endpoint_404_shape_is_identical_for_all_failure_modes(isolated_db, entitled, monkeypatch, tmp_path):
    """Wrong, expired, and revoked tokens must be byte-identical to the caller —
    the endpoint must never reveal that a share once existed."""
    _make_record(tmp_path, source_id="official-cbuae", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    _fresh_limiters(monkeypatch)
    monkeypatch.setattr(evidence_room, "_BASE_DIR", tmp_path)

    expired = _create_ok(tmp_path)
    conn = app_db._connect()
    try:
        conn.execute(
            "UPDATE evidence_shares SET expires_at = '2020-01-01T00:00:00+00:00' WHERE id = ?",
            (expired["share_id"],),
        )
        conn.commit()
    finally:
        conn.close()
    revoked = _create_ok(tmp_path)
    revoke_share({"id": _OWNER_ID}, revoked["share_id"])

    payloads = []
    for token in ("C" * 43, expired["token"], revoked["token"]):
        handler = _make_handler(method="GET", path=f"/api/room/{token}")
        handler.do_GET()
        payloads.append(handler._sent[-1])
    assert payloads[0] == payloads[1] == payloads[2]
    assert payloads[0][1] == 404


def test_no_mutation_route_exists_under_api_room(isolated_db, entitled, monkeypatch, tmp_path):
    """READ-ONLY by construction: every POST under /api/room/ must fall through
    to the router's 404 — there is no handler to reach."""
    _make_record(tmp_path, source_id="official-cbuae", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    _fresh_limiters(monkeypatch)
    monkeypatch.setattr(evidence_room, "_BASE_DIR", tmp_path)
    result = _create_ok(tmp_path)

    for path in (f"/api/room/{result['token']}", f"/api/room/{result['token']}/revoke", "/api/room/"):
        handler = _make_handler(method="POST", path=path, body={})
        handler.do_POST()
        payload, status = handler._sent[-1]
        assert status == 404, f"POST {path} must not be routable"
        assert payload == {"error": "not found"}
    # ... and the share is untouched by the attempts.
    assert get_room_view(result["token"], base_dir=tmp_path) is not None


def test_room_endpoint_is_rate_limited_per_ip(isolated_db, monkeypatch):
    monkeypatch.setattr(api, "_ROOM_LIMITER", _RateLimiter(1, 3600))
    first = _make_handler(method="GET", path="/api/room/" + "D" * 43)
    first.do_GET()
    assert first._sent[-1][1] == 404  # consumed the single slot
    second = _make_handler(method="GET", path="/api/room/" + "D" * 43)
    second.do_GET()
    assert second._sent[-1][1] == 429


def test_shares_list_endpoint_requires_auth_and_lists_own(isolated_db, entitled, monkeypatch, tmp_path):
    _auth_as(monkeypatch, None)
    handler = _make_handler(method="GET", path="/api/evidence-room/shares")
    handler._handle_evidence_room_shares_list()
    assert handler._sent[-1][1] == 401

    _make_record(tmp_path, source_id="official-cbuae", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    mine = _create_ok(tmp_path)
    _auth_as(monkeypatch, {"id": _OWNER_ID})
    handler = _make_handler(method="GET", path="/api/evidence-room/shares")
    handler._handle_evidence_room_shares_list()
    payload, status = handler._sent[-1]
    assert status == 200
    assert [s["share_id"] for s in payload["shares"]] == [mine["share_id"]]


def test_share_revoke_endpoint_owner_flow(isolated_db, entitled, monkeypatch, tmp_path):
    owner, _seat = _seed_owner_and_auditor()
    _make_record(tmp_path, source_id="official-cbuae", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    _fresh_limiters(monkeypatch)
    monkeypatch.setattr(evidence_room, "_BASE_DIR", tmp_path)
    result = _create_ok(tmp_path, user_id=int(owner["id"]))

    _auth_as(monkeypatch, owner)
    handler = _make_handler(body={"share_id": result["share_id"]})
    handler._handle_evidence_room_share_revoke()
    payload, status = handler._sent[-1]
    assert status == 200 and payload["ok"] is True
    assert get_room_view(result["token"], base_dir=tmp_path) is None

    # Unknown / foreign share id → 404, same envelope as nonexistent.
    handler = _make_handler(body={"share_id": 424242})
    handler._handle_evidence_room_share_revoke()
    assert handler._sent[-1][1] == 404


def test_safe_source_segment_re_rejects_traversal():
    """A source_id segment interpolated into the per-source glob must reject all-dot
    traversal ids ('..'/'.') so it can never re-collapse to a whole-tree walk
    (verify-swarm 2026-07-12)."""
    from app.evidence_room import _SAFE_SOURCE_SEGMENT_RE as R
    assert R.match("AE-vara-rulebook") and R.match("custom-1a2b3c4d")
    for bad in ("..", ".", "...", "....", "./.."):
        assert not R.match(bad), bad
