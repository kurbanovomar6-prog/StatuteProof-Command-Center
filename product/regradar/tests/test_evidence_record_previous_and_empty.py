"""Evidence integrity gate must cover the PREVIOUS side and EMPTY content.

Two adversarial findings closed here:

FINDING 3 (previous side): the undecodable-content gate used to run only
against the current/normalized-current path. A CHANGED record with a clean
current but a mojibake ``previous.normalized.txt`` still certified
``integrity_status=VERIFIED``, passed ``validate_evidence_record`` with zero
errors, and baked garbled previous-side lines into the customer diff. Both
sides must now fail integrity, naming which side broke.

FINDING 4 (empty content): ``is_mostly_unreadable("")`` returns False, so a
zero-length ``normalized.txt`` used to certify VERIFIED with nothing to review.
Empty / whitespace-only normalized content referenced by an evidence record is
now an integrity failure.
"""

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.evidence_records import (
    build_risk_brief_inputs,
    create_canonical_evidence_record,
    validate_evidence_record,
)


MOJIBAKE = "���\x00\x01���\x02�" * 40
CLEAN_CURRENT = (
    "The VARA rulebook has been amended. Virtual asset service providers must "
    "review client-onboarding controls and update their compliance attestations."
)
CLEAN_PREVIOUS = (
    "The VARA rulebook previously required quarterly attestations. Virtual asset "
    "service providers submitted onboarding controls under the prior framework."
)


def _write(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _previous_run(base: Path, *, normalized_text: str) -> dict:
    prev_dir = base / "data" / "source_snapshots" / "2026-06-19" / "AE" / "AE-vara-test" / "run-vara-000"
    prev_hash = _write(prev_dir / "normalized.txt", normalized_text)
    return {
        "run_id": "run-vara-000",
        "source_id": "AE-vara-test",
        "change_status": "FIRST_SEEN",
        "normalized_hash": prev_hash,
        "snapshot_normalized_path": str((prev_dir / "normalized.txt").relative_to(base)),
    }


def _changed_run_record(base: Path, *, current_text: str) -> dict:
    run_dir = base / "data" / "source_snapshots" / "2026-06-20" / "AE" / "AE-vara-test" / "run-vara-001"
    current_hash = _write(run_dir / "normalized.txt", current_text)
    _write(run_dir / "raw.txt", "<main>raw body</main>")
    _write(run_dir / "metadata.json", json.dumps({"provider": "fixture"}, sort_keys=True))
    _write(run_dir / "proof.json", json.dumps({"proof_quality": "LIMITED"}, sort_keys=True))
    return {
        "run_id": "run-vara-001",
        "timestamp_utc": "2026-06-20T00:00:00Z",
        "market": "AE",
        "source_id": "AE-vara-test",
        "source_name": "VARA Test Source",
        "category": "regulatory",
        "official_url": "https://www.vara.ae/example",
        "access_status": "accessible",
        "fetch_method": "fixture",
        "extraction_quality": "GOOD",
        "change_status": "CHANGED",
        "normalized_hash": current_hash,
        "snapshot_raw_path": str((run_dir / "raw.txt").relative_to(base)),
        "snapshot_normalized_path": str((run_dir / "normalized.txt").relative_to(base)),
        "snapshot_metadata_path": str((run_dir / "metadata.json").relative_to(base)),
        "proof_block_path": str((run_dir / "proof.json").relative_to(base)),
    }


# ── FINDING 3: mojibake on the PREVIOUS side must not certify VERIFIED ──────────


def test_changed_record_with_mojibake_previous_is_not_certified(tmp_path):
    run = _changed_run_record(tmp_path, current_text=CLEAN_CURRENT)
    previous = _previous_run(tmp_path, normalized_text=MOJIBAKE)

    record = create_canonical_evidence_record(run, previous, base_dir=tmp_path)

    # Clean current alone must NOT be enough — the mojibake previous quarantines.
    assert record["integrity"]["integrity_status"] == "FAILED"
    assert record["integrity"]["integrity_status"] != "VERIFIED"
    assert record["integrity"]["hash_verified"] is False
    assert record["record_status"] == "integrity_error"
    # The reason must name the PREVIOUS side so a reviewer knows which broke.
    assert "previous" in record["integrity"]["reason"].lower()
    assert "undecodable" in record["integrity"]["reason"].lower()


def test_validate_flags_changed_record_with_mojibake_previous(tmp_path):
    # Build a well-formed CHANGED record with clean BOTH sides, then swap the
    # previous file to mojibake so validate_evidence_record must catch it even
    # if a record already claims VERIFIED (forged / drifted on disk).
    run = _changed_run_record(tmp_path, current_text=CLEAN_CURRENT)
    previous = _previous_run(tmp_path, normalized_text=CLEAN_PREVIOUS)
    record = create_canonical_evidence_record(run, previous, base_dir=tmp_path)
    assert record["integrity"]["integrity_status"] == "VERIFIED"  # sanity: clean certifies

    # Corrupt the copied previous normalized artifact in the canonical tree.
    prev_rel = record["content"]["normalized_previous_path"]
    (tmp_path / prev_rel).write_text(MOJIBAKE, encoding="utf-8")

    validation = validate_evidence_record(record, base_dir=tmp_path)

    assert validation["valid"] is False
    assert any(
        "undecodable" in err.lower() and "previous" in err.lower()
        for err in validation["errors"]
    ), validation["errors"]
    gate = build_risk_brief_inputs(record["record_id"], base_dir=tmp_path)
    assert gate["eligible"] is False


def test_changed_record_with_clean_both_sides_still_certifies(tmp_path):
    run = _changed_run_record(tmp_path, current_text=CLEAN_CURRENT)
    previous = _previous_run(tmp_path, normalized_text=CLEAN_PREVIOUS)

    record = create_canonical_evidence_record(run, previous, base_dir=tmp_path)
    validation = validate_evidence_record(record, base_dir=tmp_path)

    assert record["integrity"]["integrity_status"] == "VERIFIED"
    assert record["record_status"] == "complete"
    assert validation["valid"] is True


# ── FINDING 4: empty / whitespace-only normalized content fails integrity ──────


def test_empty_current_normalized_is_not_certified(tmp_path):
    run = _changed_run_record(tmp_path, current_text="")
    previous = _previous_run(tmp_path, normalized_text=CLEAN_PREVIOUS)

    record = create_canonical_evidence_record(run, previous, base_dir=tmp_path)

    assert record["integrity"]["integrity_status"] == "FAILED"
    assert record["record_status"] == "integrity_error"
    assert "empty" in record["integrity"]["reason"].lower()
    assert "current" in record["integrity"]["reason"].lower()


def test_whitespace_only_previous_is_not_certified(tmp_path):
    run = _changed_run_record(tmp_path, current_text=CLEAN_CURRENT)
    previous = _previous_run(tmp_path, normalized_text="   \n\t  \n")

    record = create_canonical_evidence_record(run, previous, base_dir=tmp_path)

    assert record["integrity"]["integrity_status"] == "FAILED"
    assert record["record_status"] == "integrity_error"
    assert "empty" in record["integrity"]["reason"].lower()
    assert "previous" in record["integrity"]["reason"].lower()


def test_validate_flags_empty_current_normalized(tmp_path):
    # Build a clean record, then blank the current normalized artifact so
    # validate_evidence_record must reject the zero-length body.
    run = _changed_run_record(tmp_path, current_text=CLEAN_CURRENT)
    previous = _previous_run(tmp_path, normalized_text=CLEAN_PREVIOUS)
    record = create_canonical_evidence_record(run, previous, base_dir=tmp_path)

    current_rel = record["content"]["normalized_current_path"]
    (tmp_path / current_rel).write_text("", encoding="utf-8")

    validation = validate_evidence_record(record, base_dir=tmp_path)

    assert validation["valid"] is False
    assert any(
        "empty" in err.lower() and "current" in err.lower()
        for err in validation["errors"]
    ), validation["errors"]
