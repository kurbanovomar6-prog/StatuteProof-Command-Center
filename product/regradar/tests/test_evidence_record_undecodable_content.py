"""Evidence records must not certify undecodable content as VERIFIED.

Regression guard for the VARA mojibake incident (2026-07-10): a normalized
body saturated with U+FFFD replacement / control characters hashes perfectly
and used to be stamped ``integrity_status=VERIFIED``. Integrity is not just
"the hash matches the bytes" — undecodable content must be quarantined, never
certified, and never brief-eligible. Clean regulatory text must still certify
normally.
"""

import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.evidence_records import (
    build_risk_brief_inputs,
    create_canonical_evidence_record,
    validate_evidence_record,
)


# A mis-decoded / binary body: saturated with replacement characters, the
# UTF-8 errors="replace" signature. Well above the shared saturation floor.
MOJIBAKE = "���\x00\x01���\x02�" * 40
CLEAN_TEXT = (
    "The DFSA has amended its conduct-of-business rulebook. Authorised firms "
    "must review client-classification records and update onboarding controls."
)


def _write(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _snapshot_run_record(base: Path, *, normalized_text: str) -> dict:
    run_dir = base / "data" / "source_snapshots" / "2026-06-20" / "AE" / "AE-vara-test" / "run-vara-001"
    current_hash = _write(run_dir / "normalized.txt", normalized_text)
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
        "change_status": "FIRST_SEEN",
        "normalized_hash": current_hash,
        "snapshot_raw_path": str((run_dir / "raw.txt").relative_to(base)),
        "snapshot_normalized_path": str((run_dir / "normalized.txt").relative_to(base)),
        "snapshot_metadata_path": str((run_dir / "metadata.json").relative_to(base)),
        "proof_block_path": str((run_dir / "proof.json").relative_to(base)),
    }


def test_create_record_over_mojibake_is_not_certified_verified(tmp_path):
    run = _snapshot_run_record(tmp_path, normalized_text=MOJIBAKE)

    record = create_canonical_evidence_record(run, base_dir=tmp_path)

    assert record["integrity"]["integrity_status"] == "FAILED"
    assert record["integrity"]["integrity_status"] != "VERIFIED"
    assert record["integrity"]["hash_verified"] is False
    assert record["record_status"] == "integrity_error"
    assert "undecodable" in record["integrity"]["reason"].lower()
    # The hash is still recorded (bytes are what they are) but never certified.
    assert record["content"]["current_hash"].startswith("sha256:")


def test_mojibake_record_is_not_brief_eligible(tmp_path):
    run = _snapshot_run_record(tmp_path, normalized_text=MOJIBAKE)

    record = create_canonical_evidence_record(run, base_dir=tmp_path)
    validation = validate_evidence_record(record, base_dir=tmp_path)
    gate = build_risk_brief_inputs(record["record_id"], base_dir=tmp_path)

    assert validation["valid"] is False
    assert any("undecodable" in err.lower() for err in validation["errors"])
    assert gate["eligible"] is False


def test_validate_reports_integrity_problem_when_verified_claimed_over_mojibake(tmp_path):
    # A hand-crafted record that (wrongly) claims VERIFIED over mojibake must
    # be rejected by validation, closing the loop even if a record is forged.
    run = _snapshot_run_record(tmp_path, normalized_text=MOJIBAKE)
    record = create_canonical_evidence_record(run, base_dir=tmp_path)

    forged = json.loads(json.dumps(record))
    forged["record_status"] = "complete"
    forged["integrity"] = {
        "hash_verified": True,
        "integrity_status": "VERIFIED",
        "verified_at": "2026-06-20T00:01:00Z",
    }
    forged["review"] = {
        "human_review_required": True,
        "review_status": "approved",
        "review_reason": "Forged.",
    }

    validation = validate_evidence_record(forged, base_dir=tmp_path)

    assert validation["valid"] is False
    assert any("undecodable" in err.lower() for err in validation["errors"])


def test_clean_regulatory_text_still_certifies_verified(tmp_path):
    run = _snapshot_run_record(tmp_path, normalized_text=CLEAN_TEXT)

    record = create_canonical_evidence_record(run, base_dir=tmp_path)
    validation = validate_evidence_record(record, base_dir=tmp_path)

    assert record["integrity"]["integrity_status"] == "VERIFIED"
    assert record["integrity"]["hash_verified"] is True
    assert record["record_status"] == "complete"
    assert validation["valid"] is True
    # Clean content still requires human review before brief use — but is not
    # blocked for an integrity reason.
    gate = build_risk_brief_inputs(record["record_id"], base_dir=tmp_path)
    assert "undecodable" not in gate["blocked_reason"].lower()
