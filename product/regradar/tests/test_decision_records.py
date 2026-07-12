"""Sealed decision log (Stage 1) — behavior + safety.

Proves the spec's full Stage-1 test plan:

1. Tenancy — org A can never read org B's decisions; a cross-org get returns the
   same ``None`` as a nonexistent id (no existence oracle).
2. Immutability — direct UPDATE/DELETE on ``decision_records`` is blocked by the
   database triggers; the module exposes no mutator.
3. Chain — seals link correctly (first prev = ""), verify_decision_chain passes,
   and CONCURRENT seals (threads) never fork the chain.
4. Tamper — flipping a byte in stored ``record_json`` or re-pointing a prev hash
   is detected by ``verify_decision_chain``.
5. Public-verify round-trip — a sealed record verifies through the UNCHANGED
   ``app.public_verify.verify_submission``.
6. Amend — a correction is a NEW sealed record referencing the original, which
   stays intact; superseding a nonexistent/foreign decision is rejected.
7. Legal — the app-authored FRAMING and kind labels pass the forbidden-claims
   guard (also enforced at import).
8. Access log — a seal appends a ``decision.seal`` row; a raising logger never
   blocks the seal (mirrors test_action_checklist).
9. Bounds — oversize statement/amendment/display_name are REJECTED, never
   truncated (they are the user's sealed words).
10. Head file — ``data/decision_chain/<org>/decision_chain_head.json`` matches
    the head row after each seal.

Runs against a REAL throwaway SQLite DB (isolated_env fixture), same harness
pattern as tests/test_action_checklist.py.
"""
from __future__ import annotations

import json
import sqlite3
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.db as app_db
import app.decision_records as decision_records
from app.access_log import read_access_log
from app.auth import create_user
from app.decision_records import (
    FRAMING,
    KINDS,
    MAX_AMENDMENT_REASON_LEN,
    MAX_DISPLAY_NAME_LEN,
    MAX_STATEMENT_LEN,
    get_decision,
    list_decisions,
    read_decision_head,
    seal_decision,
    verify_decision_chain,
)
from app.legal_safety import assert_no_forbidden_claims
from app.materiality import SHORT_DISCLAIMER
from app.record_hashing import RECORD_HASH_METHOD, canonical_record_hash


# ── fixtures & helpers ────────────────────────────────────────────────────────────

@pytest.fixture()
def isolated_env(tmp_path, monkeypatch):
    """Point the DB layer AND the decision head-file base dir at a temp dir."""
    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "decisions.db"))
    monkeypatch.setattr(decision_records, "_BASE_DIR", tmp_path)
    return tmp_path


ORG_A = 1
ORG_B = 2
USER_A = 101
USER_B = 202

# Verbatim proof-block shape (app.alert_proof.build_proof_for_candidate + alert
# identity fields), as the spec's ``content.reviewed`` binding describes.
REVIEWED = {
    "evidence_record_id": "rec_cbuae_rulebook_20260712",
    "record_hash": "sha256:" + "a" * 64,
    "run_id": "run_20260712T090000Z",
    "normalized_hash": "sha256:" + "b" * 64,
    "source_id": "cbuae_rulebook",
    "source_name": "CBUAE Rulebook",
    "official_url": "https://rulebook.centralbank.ae/en",
    "alert_id": "draft-cbuae001",
}


def _seal(org: int = ORG_A, user: int = USER_A, **overrides):
    kwargs = {
        "display_name": "A. Rahman",
        "reviewed": REVIEWED,
        "kind": "reviewed",
        "statement": "I reviewed the diff and the effective date against our licence scope.",
    }
    kwargs.update(overrides)
    return seal_decision(user, org, **kwargs)


def _raw_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(app_db.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── 1. tenancy ───────────────────────────────────────────────────────────────────

def test_org_a_cannot_read_org_b(isolated_env):
    sealed_a = _seal(org=ORG_A)
    sealed_b = _seal(org=ORG_B, user=USER_B, statement="Org B's own review note.")
    assert sealed_a is not None and sealed_b is not None

    a_list = list_decisions(ORG_A)
    b_list = list_decisions(ORG_B)
    assert [r["decision_id"] for r in a_list] == [sealed_a["decision_id"]]
    assert [r["decision_id"] for r in b_list] == [sealed_b["decision_id"]]

    # Cross-org get resolves to None — and each chain is independent (both seq 1).
    assert get_decision(ORG_B, sealed_a["decision_id"]) is None
    assert sealed_a["content"]["chain_seq"] == 1
    assert sealed_b["content"]["chain_seq"] == 1


def test_cross_org_get_is_indistinguishable_from_missing(isolated_env):
    sealed = _seal(org=ORG_A)
    # Same None for "another org's decision" and "no such decision" — no oracle.
    assert get_decision(ORG_B, sealed["decision_id"]) is None
    assert get_decision(ORG_B, "dec_2_1_0000000000000000dead") is None
    assert get_decision(ORG_A, sealed["decision_id"]) is not None


# ── 2. immutability ──────────────────────────────────────────────────────────────

def test_direct_update_is_blocked_by_trigger(isolated_env):
    _seal()
    conn = _raw_conn()
    try:
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            conn.execute("UPDATE decision_records SET record_json = '{}' WHERE org_id = 1")
    finally:
        conn.close()
    # The row is intact after the blocked attempt.
    assert verify_decision_chain(ORG_A)["ok"] is True


def test_direct_delete_is_blocked_by_trigger(isolated_env):
    _seal()
    conn = _raw_conn()
    try:
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            conn.execute("DELETE FROM decision_records WHERE org_id = 1")
    finally:
        conn.close()
    assert len(list_decisions(ORG_A)) == 1


def test_module_exposes_no_mutators():
    mutators = [
        name
        for name in dir(decision_records)
        if name.startswith(("update_", "delete_", "edit_", "remove_", "set_"))
    ]
    assert mutators == []


# ── 3. chain ─────────────────────────────────────────────────────────────────────

def test_chain_of_three_links_correctly(isolated_env):
    first = _seal(statement="First review decision.")
    second = _seal(statement="Second review decision.")
    third = _seal(statement="Third review decision.")

    assert first["content"]["prev_decision_hash"] == ""
    assert second["content"]["prev_decision_hash"] == first["record_hash"]
    assert third["content"]["prev_decision_hash"] == second["record_hash"]
    assert [r["content"]["chain_seq"] for r in (first, second, third)] == [1, 2, 3]

    report = verify_decision_chain(ORG_A)
    assert report == {"ok": True, "checked": 3, "broken_at": None, "reason": None}


def test_verify_empty_chain_is_ok(isolated_env):
    assert verify_decision_chain(ORG_A) == {
        "ok": True,
        "checked": 0,
        "broken_at": None,
        "reason": None,
    }


def test_concurrent_seals_never_fork_the_chain(isolated_env):
    n = 8
    results: list[dict | None] = [None] * n
    barrier = threading.Barrier(n)

    def _worker(i: int) -> None:
        barrier.wait()
        results[i] = _seal(statement=f"Concurrent review note {i}.")

    threads = [threading.Thread(target=_worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert all(r is not None for r in results), "every concurrent seal must succeed"
    seqs = sorted(r["content"]["chain_seq"] for r in results)
    assert seqs == list(range(1, n + 1)), "sequences must be distinct and gap-free"
    report = verify_decision_chain(ORG_A)
    assert report["ok"] is True and report["checked"] == n


# ── 4. tamper ────────────────────────────────────────────────────────────────────

def test_tampered_statement_breaks_the_seal(isolated_env):
    _seal(statement="First review decision.")
    _seal(statement="Second review decision.")
    _seal(statement="Third review decision.")

    # An attacker with FULL DB access can drop the trigger; the seal still catches it.
    conn = _raw_conn()
    try:
        conn.execute("DROP TRIGGER trg_decision_records_no_update")
        row = conn.execute(
            "SELECT id, record_json FROM decision_records WHERE org_id = 1 AND chain_seq = 2"
        ).fetchone()
        tampered = row["record_json"].replace(
            "Second review decision.", "Second review decision (edited)."
        )
        assert tampered != row["record_json"]
        conn.execute(
            "UPDATE decision_records SET record_json = ? WHERE id = ?",
            (tampered, row["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    report = verify_decision_chain(ORG_A)
    assert report["ok"] is False
    assert report["broken_at"] == 2
    assert report["reason"] == "seal_mismatch"
    assert report["checked"] == 1  # record 1 verified before the break


def test_repointed_prev_hash_breaks_the_chain(isolated_env):
    _seal(statement="First review decision.")
    _seal(statement="Second review decision.")
    _seal(statement="Third review decision.")

    # A smarter attacker RE-SEALS record 2 after re-pointing its prev hash, so
    # the self-seal recomputes — the prev-linkage walk must still catch it.
    conn = _raw_conn()
    try:
        conn.execute("DROP TRIGGER trg_decision_records_no_update")
        row = conn.execute(
            "SELECT id, record_json FROM decision_records WHERE org_id = 1 AND chain_seq = 2"
        ).fetchone()
        forged = json.loads(row["record_json"])
        forged["content"]["prev_decision_hash"] = "sha256:" + "f" * 64
        forged["record_hash"] = "sha256:" + canonical_record_hash(forged["content"])
        conn.execute(
            "UPDATE decision_records SET record_json = ?, decision_hash = ? WHERE id = ?",
            (json.dumps(forged, ensure_ascii=False, sort_keys=True), forged["record_hash"], row["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    report = verify_decision_chain(ORG_A)
    assert report["ok"] is False
    assert report["broken_at"] == 2
    assert report["reason"] == "prev_link_mismatch"


# ── 5. public-verify round-trip (ZERO changes to app.public_verify) ──────────────

def test_public_verify_roundtrip(isolated_env):
    from app.public_verify import verify_submission

    sealed = _seal()

    # Exactly what a customer would hold: the stored record_json, parsed.
    conn = _raw_conn()
    try:
        stored = conn.execute(
            "SELECT record_json FROM decision_records WHERE decision_id = ?",
            (sealed["decision_id"],),
        ).fetchone()["record_json"]
    finally:
        conn.close()

    report = verify_submission(json.loads(stored))
    assert report["verified"] is True
    by_name = {c["name"]: c["status"] for c in report["checks"]}
    assert by_name["record_hash_self_consistent"] == "pass"

    # The module's own read path round-trips identically.
    fetched = get_decision(ORG_A, sealed["decision_id"])
    assert verify_submission(fetched)["verified"] is True
    assert fetched["record_hash_method"] == RECORD_HASH_METHOD


def test_unicode_statement_seals_verbatim_and_verifies(isolated_env):
    # The canonicalization is ensure_ascii=False UTF-8; a non-ASCII statement
    # (Arabic is a live lane for this product) must seal byte-stable, round-trip
    # verbatim through storage, and still verify — no mojibake, no drift.
    from app.public_verify import verify_submission

    statement = "راجعتُ التعديل — القسم ٤: لا أثر على نطاق الترخيص لدينا."
    sealed = _seal(statement=statement)
    assert sealed is not None

    fetched = get_decision(ORG_A, sealed["decision_id"])
    assert fetched["content"]["decision"]["statement"] == statement
    assert verify_submission(fetched)["verified"] is True
    assert verify_decision_chain(ORG_A)["ok"] is True


# ── 6. amend (corrections are NEW records; the original stays) ───────────────────

def test_amend_links_and_original_stays_intact(isolated_env):
    original = _seal(statement="Reviewed; no licence impact identified.")
    before = get_decision(ORG_A, original["decision_id"])

    amendment = _seal(
        statement="On re-reading, section 4 does affect our reporting form.",
        supersedes_decision_id=original["decision_id"],
        amendment_reason="I misread the scope of section 4 in my earlier entry.",
    )
    assert amendment is not None
    assert amendment["content"]["supersedes_decision_id"] == original["decision_id"]
    assert amendment["content"]["amendment_reason"].startswith("I misread")
    assert amendment["content"]["chain_seq"] == 2

    # The original is byte-identical and the chain still verifies end-to-end.
    assert get_decision(ORG_A, original["decision_id"]) == before
    report = verify_decision_chain(ORG_A)
    assert report["ok"] is True and report["checked"] == 2


def test_supersede_nonexistent_decision_is_rejected(isolated_env):
    assert (
        _seal(
            supersedes_decision_id="dec_1_1_0000000000000000dead",
            amendment_reason="Correcting an entry that does not exist.",
        )
        is None
    )
    assert list_decisions(ORG_A) == []


def test_supersede_foreign_org_decision_is_rejected(isolated_env):
    foreign = _seal(org=ORG_B, user=USER_B, statement="Org B decision.")
    assert (
        _seal(
            org=ORG_A,
            supersedes_decision_id=foreign["decision_id"],
            amendment_reason="Trying to amend another org's record.",
        )
        is None
    )
    # Same None as a nonexistent id — no cross-org existence oracle.
    assert list_decisions(ORG_A) == []


def test_supersedes_and_amendment_reason_travel_together(isolated_env):
    original = _seal()
    # A correction without its reason is rejected…
    assert (
        _seal(supersedes_decision_id=original["decision_id"], amendment_reason="") is None
    )
    # …and a reason without a target is rejected too.
    assert _seal(amendment_reason="Reason with nothing to correct.") is None


# ── 7. legal: framing guard ──────────────────────────────────────────────────────

def test_framing_and_kind_labels_pass_forbidden_claims_guard():
    # Belt: the module already runs this AT IMPORT (a drift fails collection);
    # this test keeps the guarantee visible and pinned.
    for key, value in FRAMING.items():
        assert_no_forbidden_claims(value, label=f"decision framing[{key}]")
    for kind in KINDS:
        assert_no_forbidden_claims(kind.replace("_", " "), label=f"decision kind[{kind}]")
    # The disclaimer reuses the vetted constant verbatim — never retyped.
    assert FRAMING["disclaimer"].endswith(SHORT_DISCLAIMER)


# ── 8. access log ────────────────────────────────────────────────────────────────

def test_seal_writes_decision_seal_access_log_row(isolated_env):
    user = create_user("sealer@example.com", "password-123")
    app_db.backfill_org_memberships()
    sealed = _seal(user=user["id"])
    assert sealed is not None

    rows = [r for r in read_access_log(limit=100) if r["action"] == "decision.seal"]
    assert rows, "seal must append a decision.seal access-log row"
    assert rows[0]["actor_user_id"] == user["id"]
    assert rows[0]["result"] == "allow"
    assert rows[0]["resource_type"] == "decision"
    assert rows[0]["resource_id"] == sealed["decision_id"]


def test_raising_logger_never_blocks_the_seal(isolated_env, monkeypatch):
    import app.rbac_runtime as rbac_runtime

    def _boom(*a, **k):
        raise RuntimeError("access log unavailable")

    monkeypatch.setattr(rbac_runtime, "log_sensitive_action", _boom)
    sealed = _seal()
    assert sealed is not None
    assert get_decision(ORG_A, sealed["decision_id"]) is not None
    assert verify_decision_chain(ORG_A)["ok"] is True


# ── 9. bounds: REJECT, never truncate ────────────────────────────────────────────

def test_oversize_statement_is_rejected_not_truncated(isolated_env):
    assert _seal(statement="x" * (MAX_STATEMENT_LEN + 1)) is None
    assert list_decisions(ORG_A) == []  # nothing was silently written

    # Exactly at the bound the user's words are sealed VERBATIM.
    exact = "y" * MAX_STATEMENT_LEN
    sealed = _seal(statement=exact)
    assert sealed is not None
    assert sealed["content"]["decision"]["statement"] == exact


def test_oversize_amendment_reason_and_display_name_are_rejected(isolated_env):
    original = _seal()
    assert (
        _seal(
            supersedes_decision_id=original["decision_id"],
            amendment_reason="r" * (MAX_AMENDMENT_REASON_LEN + 1),
        )
        is None
    )
    assert _seal(display_name="n" * (MAX_DISPLAY_NAME_LEN + 1)) is None
    assert len(list_decisions(ORG_A)) == 1  # only the original exists


def test_invalid_inputs_fail_soft(isolated_env):
    # Identity coercion failures never raise.
    assert seal_decision("nope", ORG_A, display_name="A", reviewed=REVIEWED,
                         kind="reviewed", statement="Valid words.") is None
    assert seal_decision(USER_A, "org", display_name="A", reviewed=REVIEWED,
                         kind="reviewed", statement="Valid words.") is None
    # kind must be one of the five neutral labels.
    assert _seal(kind="approved") is None
    assert _seal(kind="") is None
    # statement required, non-empty, str.
    assert _seal(statement="   ") is None
    assert _seal(statement=None) is None
    # reviewed must be a validated flat proof-block copy.
    assert _seal(reviewed="not-a-dict") is None
    assert _seal(reviewed={}) is None
    assert _seal(reviewed={"alert_id": {"nested": True}}) is None
    assert _seal(reviewed={"": "empty key"}) is None
    # checklist_ref shape is validated.
    assert _seal(checklist_ref={"unexpected": 1}) is None
    assert _seal(checklist_ref={"item_ids": ["twelve"]}) is None
    # Reads fail soft on malformed identifiers.
    assert list_decisions("nope") == []
    assert get_decision(ORG_A, "") is None
    assert get_decision("nope", "dec_1_1_x") is None
    assert read_decision_head("nope") is None
    assert list_decisions(ORG_A) == []  # none of the above wrote anything


def test_valid_checklist_ref_is_sealed_normalized(isolated_env):
    sealed = _seal(
        kind="action_recorded",
        checklist_ref={"alert_id": "draft-cbuae001", "item_ids": [12, 13]},
    )
    assert sealed is not None
    assert sealed["content"]["decision"]["checklist_ref"] == {
        "alert_id": "draft-cbuae001",
        "item_ids": [12, 13],
    }
    assert sealed["content"]["decision"]["kind"] == "action_recorded"


def test_list_filters_by_alert_id(isolated_env):
    _seal()
    other_reviewed = dict(REVIEWED, alert_id="draft-other002")
    _seal(reviewed=other_reviewed, statement="Decision for the other alert.")

    assert len(list_decisions(ORG_A)) == 2
    filtered = list_decisions(ORG_A, alert_id="draft-other002")
    assert len(filtered) == 1
    assert filtered[0]["content"]["reviewed"]["alert_id"] == "draft-other002"


# ── 10. head file ────────────────────────────────────────────────────────────────

def test_head_file_matches_the_head_row(isolated_env):
    _seal(statement="First review decision.")
    second = _seal(statement="Second review decision.")

    head = read_decision_head(ORG_A)
    assert head is not None
    assert head["org_id"] == ORG_A
    assert head["decision_id"] == second["decision_id"]
    assert head["chain_seq"] == second["content"]["chain_seq"] == 2
    assert head["head_decision_hash"] == second["record_hash"]
    assert head["last_update_kind"] == "append"

    path = isolated_env / "data" / "decision_chain" / str(ORG_A) / "decision_chain_head.json"
    assert path.exists()

    # Per-org isolation of the head file too.
    assert read_decision_head(ORG_B) is None


def test_head_write_failure_never_blocks_the_seal(isolated_env, monkeypatch):
    def _boom(org_id):
        raise OSError("disk full")

    monkeypatch.setattr(decision_records, "_head_file", _boom)
    sealed = _seal()
    assert sealed is not None
    assert get_decision(ORG_A, sealed["decision_id"]) is not None
