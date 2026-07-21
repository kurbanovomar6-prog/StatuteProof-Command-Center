"""The attribution/change/status fields a human auditor READS are sealed.

``record_hash`` (content-sha256-v1) binds only ``content`` — the hashes and paths.
The display fields an auditor actually reads (``source.regulator``,
``source.source_name``, ``change.summary``, ``change.lines_added/removed``,
``run.status``, ``review.review_status``) sat OUTSIDE that seal, so a holder of a
genuine ``evidence-record.json`` could forge them ("400 new AML obligations", flip
CBUAE→VARA, FIRST_SEEN→CHANGED, pending→approved) with content and capture metadata
untouched, and the public verifier returned an UNQUALIFIED ``verified: true``.

New records now carry an additive full-record seal (``attribution_hash`` /
``attribution_hash_method: attribution-sha256-v1``). The public verifier FAILS on any
forged attribution field for sealed records, and reports an honest limited
``verified_scope`` for legacy records that cannot bind those fields. All additive:
the content-only ``record_hash`` is untouched and legacy records still verify.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.evidence_records import (  # noqa: E402
    ATTRIBUTION_HASH_METHOD,
    attribution_seal_payload,
    create_canonical_evidence_record,
    validate_evidence_record,
)
from app.public_verify import (  # noqa: E402
    SCOPE_FULL,
    SCOPE_LIMITED,
    verify_submission,
)
from app.record_hashing import canonical_record_hash  # noqa: E402

_CURRENT = "Current official CBUAE regulatory text — amended AML section 7."
_PREVIOUS = "Previous official CBUAE regulatory text — AML section 7 original."


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _changed_run(base: Path) -> tuple[dict, dict]:
    """A CHANGED run + its previous run, so the record carries change/status fields."""
    import hashlib

    def _h(t: str) -> str:
        return hashlib.sha256(t.encode("utf-8")).hexdigest()

    cur = base / "data" / "source_snapshots" / "2026-06-20" / "AE" / "AE-cbuae-attr" / "run-cur"
    prev = base / "data" / "source_snapshots" / "2026-06-19" / "AE" / "AE-cbuae-attr" / "run-prev"
    _write(cur / "normalized.txt", _CURRENT)
    _write(cur / "raw.txt", f"<main>{_CURRENT}</main>")
    _write(cur / "metadata.json", json.dumps({"provider": "fixture"}, sort_keys=True))
    _write(cur / "proof.json", json.dumps({"proof_quality": "LIMITED"}, sort_keys=True))
    _write(prev / "normalized.txt", _PREVIOUS)

    run = {
        "run_id": "run-cur",
        "timestamp_utc": "2026-06-20T00:00:00Z",
        "market": "AE",
        "source_id": "AE-cbuae-attr",
        "source_name": "CBUAE AML Source",
        "regulator": "CBUAE",
        "category": "regulatory",
        "official_url": "https://www.centralbank.ae/example",
        "access_status": "accessible",
        "fetch_method": "fixture",
        "extraction_quality": "GOOD",
        "change_status": "CHANGED",
        "normalized_hash": _h(_CURRENT),
        "snapshot_raw_path": str((cur / "raw.txt").relative_to(base)),
        "snapshot_normalized_path": str((cur / "normalized.txt").relative_to(base)),
        "snapshot_metadata_path": str((cur / "metadata.json").relative_to(base)),
        "proof_block_path": str((cur / "proof.json").relative_to(base)),
    }
    previous_run = {
        "run_id": "run-prev",
        "normalized_hash": _h(_PREVIOUS),
        "snapshot_normalized_path": str((prev / "normalized.txt").relative_to(base)),
    }
    return run, previous_run


def _status(res: dict, name: str) -> str:
    return next(c for c in res["checks"] if c["name"] == name)["status"]


# ── writer seals the attribution fields ──────────────────────────────────────────

def test_writer_stamps_attribution_seal(tmp_path):
    run, previous_run = _changed_run(tmp_path)
    record = create_canonical_evidence_record(run, previous_run, base_dir=tmp_path)

    assert record["attribution_hash_method"] == ATTRIBUTION_HASH_METHOD
    # attribution_hash recomputes from the shared payload builder.
    expected = f"sha256:{canonical_record_hash(attribution_seal_payload(record))}"
    assert record["attribution_hash"] == expected
    # content-only record_hash is untouched (the additive seal did not disturb it).
    assert record["record_hash"] == f"sha256:{canonical_record_hash(record['content'])}"
    # A genuine record validates.
    assert validate_evidence_record(record, base_dir=tmp_path)["valid"] is True


# ── public verify: untampered v2 record passes with FULL scope ───────────────────

def test_untampered_v2_record_verifies_full_scope(tmp_path):
    run, previous_run = _changed_run(tmp_path)
    record = create_canonical_evidence_record(run, previous_run, base_dir=tmp_path)
    normalized = (tmp_path / record["content"]["normalized_current_path"]).read_text(encoding="utf-8")

    res = verify_submission(record, normalized=normalized)

    assert res["verified"] is True
    assert res["verified_scope"] == SCOPE_FULL
    assert _status(res, "attribution_seal_consistent") == "pass"


# ── public verify: forged attribution fields FAIL ────────────────────────────────

def _forge(tmp_path, mutate) -> dict:
    run, previous_run = _changed_run(tmp_path)
    record = create_canonical_evidence_record(run, previous_run, base_dir=tmp_path)
    tampered = json.loads(json.dumps(record))
    mutate(tampered)
    return verify_submission(tampered)


def test_forged_change_summary_fails(tmp_path):
    def mutate(r):
        r["change"]["summary"] = "400 new AML obligations effective immediately"

    res = _forge(tmp_path, mutate)
    assert res["verified"] is False
    assert _status(res, "attribution_seal_consistent") == "fail"
    # content-only record_hash is NOT broken by a change.summary edit — the
    # attribution seal is what catches it.
    assert _status(res, "record_hash_self_consistent") == "pass"


def test_forged_regulator_fails(tmp_path):
    def mutate(r):
        r["source"]["regulator"] = "VARA"

    res = _forge(tmp_path, mutate)
    assert res["verified"] is False
    assert _status(res, "attribution_seal_consistent") == "fail"


def test_forged_run_status_fails(tmp_path):
    def mutate(r):
        r["run"]["status"] = "UNCHANGED"

    res = _forge(tmp_path, mutate)
    assert res["verified"] is False
    assert _status(res, "attribution_seal_consistent") == "fail"


def test_forged_review_status_pending_to_approved_fails(tmp_path):
    def mutate(r):
        r["review"]["review_status"] = "approved"

    res = _forge(tmp_path, mutate)
    assert res["verified"] is False
    assert _status(res, "attribution_seal_consistent") == "fail"


def test_forged_line_counts_fail(tmp_path):
    def mutate(r):
        r["change"]["lines_added"] = 999

    res = _forge(tmp_path, mutate)
    assert res["verified"] is False
    assert _status(res, "attribution_seal_consistent") == "fail"


def test_forged_source_name_fails(tmp_path):
    def mutate(r):
        r["source"]["source_name"] = "Fabricated Regulator Source"

    res = _forge(tmp_path, mutate)
    assert res["verified"] is False
    assert _status(res, "attribution_seal_consistent") == "fail"


def test_validate_evidence_record_catches_attribution_tamper(tmp_path):
    run, previous_run = _changed_run(tmp_path)
    record = create_canonical_evidence_record(run, previous_run, base_dir=tmp_path)
    tampered = json.loads(json.dumps(record))
    tampered["review"]["review_status"] = "approved"

    result = validate_evidence_record(tampered, base_dir=tmp_path)
    assert result["valid"] is False
    assert any("attribution_hash does not match" in e for e in result["errors"])


# ── public verify: legacy v1 record reports honest LIMITED scope ─────────────────

def test_legacy_v1_record_verifies_with_limited_scope(tmp_path):
    """A record predating the attribution seal (content_hash only). It still
    verifies — but the pass is honestly qualified as limited scope, NOT an
    unqualified verified:true over its unsealed regulator/summary/status fields."""
    run, previous_run = _changed_run(tmp_path)
    record = create_canonical_evidence_record(run, previous_run, base_dir=tmp_path)
    legacy = json.loads(json.dumps(record))
    # Simulate a pre-attribution-seal record: drop the attribution seal, keep the
    # content-only record_hash intact.
    legacy.pop("attribution_hash", None)
    legacy.pop("attribution_hash_method", None)
    normalized = (tmp_path / legacy["content"]["normalized_current_path"]).read_text(encoding="utf-8")

    res = verify_submission(legacy, normalized=normalized)

    assert res["verified"] is True  # content + capture metadata still pass
    assert res["verified_scope"] == SCOPE_LIMITED
    assert _status(res, "attribution_seal_consistent") == "skipped"
    # ...and the skip detail names why the attribution fields are not covered.
    detail = next(c for c in res["checks"] if c["name"] == "attribution_seal_consistent")["detail"]
    assert "not covered" in detail.lower() or "not covered by this record's seal" in detail.lower()


def test_legacy_v1_forged_summary_is_not_falsely_verified_full(tmp_path):
    """Even a legacy v1 record whose display summary is forged must not report a
    FULL scope pass — the scope stays limited, flagging the fields are unsealed."""
    run, previous_run = _changed_run(tmp_path)
    record = create_canonical_evidence_record(run, previous_run, base_dir=tmp_path)
    legacy = json.loads(json.dumps(record))
    legacy.pop("attribution_hash", None)
    legacy.pop("attribution_hash_method", None)
    legacy["change"]["summary"] = "400 new AML obligations effective immediately"
    normalized = (tmp_path / legacy["content"]["normalized_current_path"]).read_text(encoding="utf-8")

    res = verify_submission(legacy, normalized=normalized)

    # The seal cannot bind a legacy record's summary, so the honest outcome is a
    # LIMITED scope — never a FULL scope that would imply the summary was sealed.
    assert res["verified_scope"] == SCOPE_LIMITED
