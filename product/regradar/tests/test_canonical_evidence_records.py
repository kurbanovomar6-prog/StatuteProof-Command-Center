import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.evidence_records import (
    EvidenceRecordError,
    build_risk_brief_inputs,
    create_canonical_evidence_record,
    validate_evidence_record,
)
from app.alert_drafts import build_evidence_backed_brief_draft


REPO_ROOT = Path(__file__).resolve().parents[3]


def _write(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_record(
    base: Path,
    *,
    status: str = "CHANGED",
    with_diff: bool = True,
    review_status: str = "approved",
) -> dict:
    record_dir = base / "evidence" / "dfsa" / "AE-dfsa-test" / "run_AE-dfsa-test_20260620T000000Z"
    current_hash = _write(record_dir / "current.normalized.txt", "Current official DFSA regulatory text")
    previous_hash = _write(record_dir / "previous.normalized.txt", "Previous official DFSA regulatory text")
    _write(record_dir / "raw.html", "<main>Current official DFSA regulatory text</main>")
    _write(record_dir / "snapshot.html", "<html><body><main>Current official DFSA regulatory text</main></body></html>")
    _write(record_dir / "metadata.json", json.dumps({"provider": "fixture"}, sort_keys=True))
    if with_diff:
        _write(record_dir / "diff.txt", "- Previous official DFSA regulatory text\n+ Current official DFSA regulatory text\n")

    record = {
        "schema_version": "2.0",
        "record_id": "evr_dfsa_test_20260620T000000Z",
        "record_status": "complete",
        "source": {
            "source_id": "AE-dfsa-test",
            "regulator": "DFSA",
            "official_url": "https://www.dfsa.ae/example",
            "source_name": "DFSA Test Source",
        },
        "run": {
            "run_id": "run_AE-dfsa-test_20260620T000000Z",
            "timestamp": "2026-06-20T00:00:00Z",
            "status": status,
        },
        "content": {
            "previous_hash": f"sha256:{previous_hash}",
            "current_hash": f"sha256:{current_hash}",
            "raw_content_path": str((record_dir / "raw.html").relative_to(base)),
            "normalized_current_path": str((record_dir / "current.normalized.txt").relative_to(base)),
            "normalized_previous_path": str((record_dir / "previous.normalized.txt").relative_to(base)),
        },
        "change": {
            "diff_path": str((record_dir / "diff.txt").relative_to(base)) if with_diff else "",
            "summary": "Evidence-only DFSA fixture summary.",
            "lines_added": 1,
            "lines_removed": 1,
        },
        "files": {
            "snapshot_path": str((record_dir / "snapshot.html").relative_to(base)),
            "raw_path": str((record_dir / "raw.html").relative_to(base)),
            "normalized_path": str((record_dir / "current.normalized.txt").relative_to(base)),
            "previous_path": str((record_dir / "previous.normalized.txt").relative_to(base)),
            "metadata_path": str((record_dir / "metadata.json").relative_to(base)),
            "diff_path": str((record_dir / "diff.txt").relative_to(base)) if with_diff else "",
        },
        "integrity": {
            "hash_verified": True,
            "integrity_status": "VERIFIED",
            "verified_at": "2026-06-20T00:01:00Z",
        },
        "review": {
            "human_review_required": True,
            "review_status": review_status,
            "review_reason": "Customer-facing brief requires human review.",
        },
    }
    (record_dir / "evidence-record.json").write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return record


def test_snapshot_proof_json_is_not_brief_eligible(tmp_path):
    proof_path = tmp_path / "data" / "source_snapshots" / "2026-06-20" / "AE" / "AE-dfsa-test" / "proof.json"
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text(json.dumps({"proof_quality": "GOOD", "source_id": "AE-dfsa-test"}), encoding="utf-8")

    result = build_risk_brief_inputs(str(proof_path.relative_to(tmp_path)), base_dir=tmp_path)

    assert result["eligible"] is False
    assert "not a canonical evidence record" in result["blocked_reason"]


def test_complete_canonical_evidence_record_is_brief_input_eligible(tmp_path):
    record = _canonical_record(tmp_path)

    validation = validate_evidence_record(record, base_dir=tmp_path)
    result = build_risk_brief_inputs(record["record_id"], base_dir=tmp_path)

    assert validation["valid"] is True
    assert result["eligible"] is True
    assert result["evidence_record_id"] == record["record_id"]
    assert result["official_url"] == "https://www.dfsa.ae/example"
    assert result["diff_path"].endswith("diff.txt")
    assert result["current_hash"].startswith("sha256:")


def _snapshot_run_record(base: Path, *, status: str = "FIRST_SEEN", bad_hash: bool = False) -> dict:
    run_dir = base / "data" / "source_snapshots" / "2026-06-20" / "AE" / "AE-dfsa-writer-test" / "run-writer-001"
    current_hash = _write(run_dir / "normalized.txt", "Current official DFSA writer text")
    _write(run_dir / "raw.txt", "<main>Current official DFSA writer text</main>")
    _write(run_dir / "metadata.json", json.dumps({"provider": "fixture"}, sort_keys=True))
    _write(run_dir / "proof.json", json.dumps({"proof_quality": "LIMITED"}, sort_keys=True))
    return {
        "run_id": "run-writer-001",
        "timestamp_utc": "2026-06-20T00:00:00Z",
        "market": "AE",
        "source_id": "AE-dfsa-writer-test",
        "source_name": "DFSA Writer Test Source",
        "category": "regulatory",
        "official_url": "https://www.dfsa.ae/example",
        "access_status": "accessible",
        "fetch_method": "fixture",
        "extraction_quality": "GOOD",
        "change_status": status,
        "normalized_hash": ("0" * 64 if bad_hash else current_hash),
        "snapshot_raw_path": str((run_dir / "raw.txt").relative_to(base)),
        "snapshot_normalized_path": str((run_dir / "normalized.txt").relative_to(base)),
        "snapshot_metadata_path": str((run_dir / "metadata.json").relative_to(base)),
        "proof_block_path": str((run_dir / "proof.json").relative_to(base)),
    }


def test_create_canonical_evidence_record_copies_saved_run_into_canonical_tree(tmp_path):
    run = _snapshot_run_record(tmp_path)

    record = create_canonical_evidence_record(run, base_dir=tmp_path)
    validation = validate_evidence_record(record, base_dir=tmp_path)
    gate = build_risk_brief_inputs(record["record_id"], base_dir=tmp_path)

    assert validation["valid"] is True
    assert gate["eligible"] is False
    assert "review_status" in gate["blocked_reason"]
    assert record["record_status"] == "complete"
    assert record["review"]["review_status"] == "pending"
    assert record["content"]["current_hash"].startswith("sha256:")
    assert "source_snapshots" not in record["files"]["normalized_path"]
    assert (tmp_path / "evidence" / "dfsa" / "AE-dfsa-writer-test" / "run-writer-001" / "evidence-record.json").exists()


def test_create_canonical_evidence_record_rejects_hash_mismatch(tmp_path):
    run = _snapshot_run_record(tmp_path, bad_hash=True)

    with pytest.raises(EvidenceRecordError) as exc:
        create_canonical_evidence_record(run, base_dir=tmp_path)

    assert "normalized_hash does not match" in str(exc.value)


@pytest.mark.parametrize("bad_status", ["FAILED", "QUALITY_DROP"])
def test_create_canonical_evidence_record_rejects_blocked_run_status(tmp_path, bad_status):
    run = _snapshot_run_record(tmp_path, status=bad_status)

    with pytest.raises(EvidenceRecordError) as exc:
        create_canonical_evidence_record(run, base_dir=tmp_path)

    assert bad_status in str(exc.value)


def test_create_canonical_evidence_record_rejects_run_without_snapshot_proof(tmp_path):
    run = _snapshot_run_record(tmp_path)
    (tmp_path / run["proof_block_path"]).unlink()

    with pytest.raises(EvidenceRecordError) as exc:
        create_canonical_evidence_record(run, base_dir=tmp_path)

    assert "proof" in str(exc.value).lower()


def test_evidence_backed_brief_draft_requires_approved_canonical_record(tmp_path):
    run = _snapshot_run_record(tmp_path)
    record = create_canonical_evidence_record(run, base_dir=tmp_path)

    with pytest.raises(ValueError) as exc:
        build_evidence_backed_brief_draft(
            record["record_id"],
            brief_fields={
                "executive_summary": "Official-source monitoring detected a relevant update.",
                "business_action_required": "Review the official source and evidence record.",
                "specific_obligation": "No specific obligation is asserted by this draft.",
                "risk_level": "MEDIUM",
                "confidence": "medium",
            },
            base_dir=tmp_path,
        )

    assert "review_status" in str(exc.value)


def test_evidence_backed_brief_draft_is_not_customer_delivery(tmp_path):
    run = _snapshot_run_record(tmp_path)
    record = create_canonical_evidence_record(run, base_dir=tmp_path, review_status="approved")

    draft = build_evidence_backed_brief_draft(
        record["record_id"],
        brief_fields={
            "executive_summary": "Official-source monitoring detected a relevant update.",
            "business_action_required": "Review the official source and evidence record.",
            "specific_obligation": "No specific obligation is asserted by this draft.",
            "risk_level": "MEDIUM",
            "confidence": "medium",
        },
        base_dir=tmp_path,
    )

    assert draft["evidence_record_id"] == record["record_id"]
    assert draft["customer_delivery"] is False
    assert draft["delivery_approved"] is False
    assert "explicit delivery approval required" in draft["delivery_blocked_reason"].lower()
    assert "not legal advice" in draft["not_legal_advice_disclaimer"].lower()


def test_evidence_backed_brief_draft_blocks_forbidden_claims(tmp_path):
    run = _snapshot_run_record(tmp_path)
    record = create_canonical_evidence_record(run, base_dir=tmp_path, review_status="approved")

    with pytest.raises(ValueError) as exc:
        build_evidence_backed_brief_draft(
            record["record_id"],
            brief_fields={
                "executive_summary": "This update will guarantee compliance.",
                "business_action_required": "Review the official source and evidence record.",
                "specific_obligation": "No specific obligation is asserted by this draft.",
                "risk_level": "MEDIUM",
                "confidence": "medium",
            },
            base_dir=tmp_path,
        )

    assert "FORBIDDEN phrase" in str(exc.value)


def test_pending_review_canonical_record_is_not_customer_brief_eligible(tmp_path):
    record = _canonical_record(tmp_path, review_status="pending")

    validation = validate_evidence_record(record, base_dir=tmp_path)
    result = build_risk_brief_inputs(record["record_id"], base_dir=tmp_path)

    assert validation["valid"] is True
    assert result["eligible"] is False
    assert "review_status" in result["blocked_reason"]


def test_changed_canonical_record_without_diff_is_blocked(tmp_path):
    record = _canonical_record(tmp_path, status="CHANGED", with_diff=False)

    validation = validate_evidence_record(record, base_dir=tmp_path)
    result = build_risk_brief_inputs(record["record_id"], base_dir=tmp_path)

    assert validation["valid"] is False
    assert any("diff" in error.lower() for error in validation["errors"])
    assert result["eligible"] is False
    assert "diff" in result["blocked_reason"].lower()


def test_direct_evidence_record_path_must_live_under_canonical_evidence_tree(tmp_path):
    record = _canonical_record(tmp_path)
    noncanonical_dir = tmp_path / "other" / "AE-dfsa-test" / record["run"]["run_id"]
    noncanonical_dir.mkdir(parents=True)
    noncanonical_path = noncanonical_dir / "evidence-record.json"
    noncanonical_path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")

    result = build_risk_brief_inputs(str(noncanonical_path.relative_to(tmp_path)), base_dir=tmp_path)

    assert result["eligible"] is False
    assert "canonical evidence tree" in result["blocked_reason"]


def test_nested_evidence_named_folder_is_not_canonical_tree(tmp_path):
    record = _canonical_record(tmp_path)
    noncanonical_dir = tmp_path / "other" / "evidence" / "AE-dfsa-test" / record["run"]["run_id"]
    noncanonical_dir.mkdir(parents=True)
    noncanonical_path = noncanonical_dir / "evidence-record.json"
    noncanonical_path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")

    result = build_risk_brief_inputs(str(noncanonical_path.relative_to(tmp_path)), base_dir=tmp_path)

    assert result["eligible"] is False
    assert "canonical evidence tree" in result["blocked_reason"]


def test_unknown_run_status_is_blocked(tmp_path):
    record = _canonical_record(tmp_path, status="MADE_UP_STATUS")

    validation = validate_evidence_record(record, base_dir=tmp_path)
    result = build_risk_brief_inputs(record["record_id"], base_dir=tmp_path)

    assert validation["valid"] is False
    assert any("run.status" in error for error in validation["errors"])
    assert result["eligible"] is False
    assert "MADE_UP_STATUS" in result["blocked_reason"]


@pytest.mark.parametrize("bad_status", ["FAILED", "QUALITY_DROP"])
def test_failed_or_quality_drop_records_are_blocked(tmp_path, bad_status):
    record = _canonical_record(tmp_path, status=bad_status)

    validation = validate_evidence_record(record, base_dir=tmp_path)
    result = build_risk_brief_inputs(record["record_id"], base_dir=tmp_path)

    assert validation["valid"] is False
    assert result["eligible"] is False
    assert bad_status in result["blocked_reason"]


def test_evidence_record_schema_exists_and_requires_brief_gate_fields():
    schema_path = REPO_ROOT / "schemas" / "evidence-record.schema.json"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert schema["$id"] == "https://statuteproof.local/schemas/evidence-record.schema.json"
    assert "record_status" in schema["required"]
    assert "source" in schema["required"]
    assert "run" in schema["required"]
    assert "content" in schema["required"]
    assert "integrity" in schema["required"]
    assert "review" in schema["required"]
    assert schema["properties"]["record_status"]["enum"] == [
        "pending",
        "complete",
        "integrity_error",
        "blocked",
    ]
    assert "FAILED" in schema["properties"]["run"]["properties"]["status"]["enum"]
    assert "QUALITY_DROP" in schema["properties"]["run"]["properties"]["status"]["enum"]
