"""Tests for the additive canonical evidence-record self-seal (content-sha256-v1).

The canonical ``evidence-record.json`` that a customer holds is now fully
self-verifiable by the public verifier: the writer seals it with a top-level
``record_hash`` over its ``content`` block (which includes ``content.raw_hash``),
computed through the ONE shared function ``app.record_hashing.canonical_record_hash``
that the verifier also uses. These tests build records via the REAL writer (no
hand-faked digests) and prove:

* the writer stamps ``record_hash`` + ``record_hash_method`` + ``content.raw_hash``;
* ``validate_evidence_record`` accepts the sealed record;
* ``verify_submission`` returns ``verified: true`` with the self-seal, raw-bytes,
  and normalized-bytes checks all PASS;
* tampering ANY field inside ``content`` flips ``record_hash_self_consistent`` to
  FAIL (and ``validate_evidence_record`` reports the mismatch);
* a LEGACY record predating the seal (no ``record_hash`` / ``record_hash_method``)
  still validates and the verifier SKIPS the self-seal check — never FAIL.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.evidence_records import create_canonical_evidence_record, validate_evidence_record
from app.public_verify import STATUS_FAIL, STATUS_PASS, STATUS_SKIPPED, verify_submission
from app.record_hashing import RECORD_HASH_METHOD, canonical_record_hash
from app.text_normalization import normalize_for_change_hash


def _status_of(result: dict, check_name: str) -> str:
    for check in result["checks"]:
        if check["name"] == check_name:
            return check["status"]
    raise AssertionError(f"check {check_name!r} not present in {result['checks']}")


def _build_sealed_record(
    tmp_path: Path, *, source_id: str = "cbuae-seal", run_id: str = "run-seal-1"
) -> tuple[dict, str, str]:
    """Build a genuine canonical evidence record via the real writer.

    Returns ``(record, raw_text, normalized_text)`` — the bytes the customer would
    hold as ``raw.txt`` / ``normalized.txt``.
    """
    text = "Official regulatory text sealed for canonical record-hash verification.\n"
    run_dir = tmp_path / "data" / "source_snapshots" / "2026-07-12" / "AE" / source_id / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    normalized = normalize_for_change_hash(text)
    (run_dir / "raw.txt").write_text(text, encoding="utf-8")
    (run_dir / "normalized.txt").write_text(normalized, encoding="utf-8")
    (run_dir / "metadata.json").write_text(json.dumps({"provider": "fixture"}), encoding="utf-8")
    (run_dir / "proof.json").write_text(json.dumps({"proof_quality": "GOOD"}), encoding="utf-8")
    run = {
        "run_id": run_id,
        "timestamp_utc": "2026-07-12T10:00:00Z",
        "market": "AE",
        "source_id": source_id,
        "source_name": "CBUAE Seal Test Source",
        "category": "regulatory",
        "official_url": "https://example.gov/cbuae-seal",
        "access_status": "accessible",
        "fetch_method": "fixture",
        "extraction_quality": "GOOD",
        "change_status": "FIRST_SEEN",
        "normalized_hash": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "snapshot_raw_path": str((run_dir / "raw.txt").relative_to(tmp_path)),
        "snapshot_normalized_path": str((run_dir / "normalized.txt").relative_to(tmp_path)),
        "snapshot_metadata_path": str((run_dir / "metadata.json").relative_to(tmp_path)),
        "proof_block_path": str((run_dir / "proof.json").relative_to(tmp_path)),
    }
    record = create_canonical_evidence_record(run, base_dir=tmp_path)
    return record, text, normalized


# ── shared-function contract ─────────────────────────────────────────────────────

def test_canonical_record_hash_is_sorted_key_compact_bare_hex():
    """The digest is stable, key-order-independent, compact, and bare lowercase hex."""
    a = canonical_record_hash({"b": "2", "a": "1"})
    b = canonical_record_hash({"a": "1", "b": "2"})

    assert a == b
    assert re.fullmatch(r"[0-9a-f]{64}", a)
    # Exact serialization contract: compact separators + sorted keys.
    assert a == hashlib.sha256(b'{"a":"1","b":"2"}').hexdigest()


# ── writer seals the record ──────────────────────────────────────────────────────

def test_writer_seals_canonical_record_with_content_sha256_v1(tmp_path):
    record, _text, _normalized = _build_sealed_record(tmp_path)

    assert record["record_hash_method"] == RECORD_HASH_METHOD
    assert record["record_hash"].startswith("sha256:")
    assert record["content"]["raw_hash"].startswith("sha256:")
    # record_hash is exactly sha256:<canonical_record_hash(content)>.
    assert record["record_hash"] == "sha256:" + canonical_record_hash(record["content"])


def test_validate_accepts_sealed_record(tmp_path):
    record, _text, _normalized = _build_sealed_record(tmp_path)

    validation = validate_evidence_record(record, base_dir=tmp_path)

    assert validation["valid"] is True, validation["errors"]


# ── full public-verifier pass ────────────────────────────────────────────────────

def test_verifier_full_pass_with_raw_and_normalized(tmp_path):
    record, raw, normalized = _build_sealed_record(tmp_path)

    result = verify_submission(record, raw=raw, normalized=normalized)

    assert result["verified"] is True
    assert _status_of(result, "record_hash_self_consistent") == STATUS_PASS
    assert _status_of(result, "raw_bytes_match") == STATUS_PASS
    assert _status_of(result, "normalized_bytes_match") == STATUS_PASS
    # Bonus: raw fully re-derives normalized too.
    assert _status_of(result, "normalization_reproducible") == STATUS_PASS


# ── tamper detection: ANY field inside content ───────────────────────────────────

@pytest.mark.parametrize(
    "field,value",
    [
        ("raw_content_path", "evidence/tampered/raw.txt"),
        ("normalized_current_path", "evidence/tampered/current.normalized.txt"),
        ("current_hash", "sha256:" + "a" * 64),
        ("raw_hash", "sha256:" + "b" * 64),
    ],
)
def test_tampering_any_content_field_fails_self_consistency(tmp_path, field, value):
    record, _raw, _normalized = _build_sealed_record(tmp_path)
    # Edit a field INSIDE content without re-sealing record_hash — the exact
    # in-place tamper the self-seal is designed to catch.
    record["content"][field] = value

    # Verifier: submit no bytes so record_hash_self_consistent is the isolated signal.
    result = verify_submission(record)
    assert result["verified"] is False
    assert _status_of(result, "record_hash_self_consistent") == STATUS_FAIL

    # Validator (write-side lockstep) reports the same divergence.
    validation = validate_evidence_record(record, base_dir=tmp_path)
    assert validation["valid"] is False
    assert "record_hash does not match content" in validation["errors"]


# ── legacy records stay valid; verifier SKIPS the self-seal ───────────────────────

def test_legacy_record_without_seal_validates_and_verifier_skips(tmp_path):
    record, _raw, normalized = _build_sealed_record(
        tmp_path, source_id="cbuae-legacy", run_id="run-legacy-1"
    )
    # Simulate a canonical record written BEFORE the self-seal existed.
    legacy = copy.deepcopy(record)
    legacy.pop("record_hash", None)
    legacy.pop("record_hash_method", None)
    legacy["content"].pop("raw_hash", None)

    validation = validate_evidence_record(legacy, base_dir=tmp_path)
    result = verify_submission(legacy, normalized=normalized)

    # Legacy records lack the seal fields and MUST remain valid.
    assert validation["valid"] is True, validation["errors"]
    # The verifier honestly SKIPS (never FAILS) the self-seal for a legacy record,
    # while still genuinely verifying the normalized bytes.
    assert result["verified"] is True
    assert _status_of(result, "record_hash_self_consistent") == STATUS_SKIPPED
    assert _status_of(result, "normalized_bytes_match") == STATUS_PASS
