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
    latest_canonical_evidence_review,
    list_canonical_evidence_records,
    record_canonical_evidence_review,
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


def test_append_only_canonical_review_approval_unlocks_brief_inputs_without_rewriting_record(tmp_path):
    record = _canonical_record(tmp_path, review_status="pending")
    record_path = tmp_path / "evidence" / "dfsa" / "AE-dfsa-test" / "run_AE-dfsa-test_20260620T000000Z" / "evidence-record.json"
    before = record_path.read_text(encoding="utf-8")

    review = record_canonical_evidence_review(
        record["record_id"],
        decision="approved",
        reviewer="Evidence Trail",
        note="Hashes recomputed and source/diff paths verified.",
        base_dir=tmp_path,
    )
    result = build_risk_brief_inputs(record["record_id"], base_dir=tmp_path)

    assert review["decision"] == "approved"
    assert result["eligible"] is True
    assert result["review_status"] == "approved"
    assert result["review_reason"] == "Hashes recomputed and source/diff paths verified."
    assert record_path.read_text(encoding="utf-8") == before


def test_append_only_canonical_review_blocks_if_record_changed_after_approval(tmp_path):
    record = _canonical_record(tmp_path, review_status="pending")
    record_path = tmp_path / "evidence" / "dfsa" / "AE-dfsa-test" / "run_AE-dfsa-test_20260620T000000Z" / "evidence-record.json"
    record_canonical_evidence_review(
        record["record_id"],
        decision="approved",
        reviewer="Evidence Trail",
        note="Hashes recomputed and source/diff paths verified.",
        base_dir=tmp_path,
    )

    tampered = json.loads(record_path.read_text(encoding="utf-8"))
    tampered["review"]["review_reason"] = "Tampered after review."
    record_path.write_text(json.dumps(tampered, indent=2, sort_keys=True), encoding="utf-8")
    result = build_risk_brief_inputs(record["record_id"], base_dir=tmp_path)

    assert result["eligible"] is False
    assert "external review hash" in result["blocked_reason"]


def test_append_only_canonical_review_rejection_keeps_brief_inputs_blocked(tmp_path):
    record = _canonical_record(tmp_path, review_status="pending")

    review = record_canonical_evidence_review(
        record["record_id"],
        decision="rejected",
        reviewer="Evidence Trail",
        note="Diff path needs review before customer use.",
        base_dir=tmp_path,
    )
    result = build_risk_brief_inputs(record["record_id"], base_dir=tmp_path)

    assert review["decision"] == "rejected"
    assert result["eligible"] is False
    assert "rejected" in result["blocked_reason"]


def test_canonical_review_requires_reviewer_and_note(tmp_path):
    record = _canonical_record(tmp_path, review_status="pending")

    with pytest.raises(EvidenceRecordError, match="reviewer"):
        record_canonical_evidence_review(
            record["record_id"],
            decision="approved",
            reviewer="",
            note="Verified.",
            base_dir=tmp_path,
        )
    with pytest.raises(EvidenceRecordError, match="note"):
        record_canonical_evidence_review(
            record["record_id"],
            decision="approved",
            reviewer="Evidence Trail",
            note="",
            base_dir=tmp_path,
        )


def test_list_canonical_evidence_records_includes_latest_review(tmp_path):
    record = _canonical_record(tmp_path, review_status="pending")
    record_canonical_evidence_review(
        record["record_id"],
        decision="approved",
        reviewer="Evidence Trail",
        note="Ready for draft-only brief inputs.",
        base_dir=tmp_path,
    )

    rows = list_canonical_evidence_records(base_dir=tmp_path)
    latest = latest_canonical_evidence_review(record["record_id"], base_dir=tmp_path)

    assert rows[0]["record_id"] == record["record_id"]
    assert rows[0]["record_review_status"] == "pending"
    assert rows[0]["latest_review_decision"] == "approved"
    assert latest["note"] == "Ready for draft-only brief inputs."


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


def test_ev1_validate_catches_tampered_diff_and_raw(tmp_path):
    """EV-1: content.diff_hash and content.raw_hash are sealed under record_hash;
    validate must RE-HASH the stored files so an in-place edit to the customer-
    facing redline (or the raw evidence) is caught — not just a missing file."""
    import hashlib

    record = _canonical_record(tmp_path, status="CHANGED", with_diff=True)
    record_dir = tmp_path / "evidence" / "dfsa" / "AE-dfsa-test" / "run_AE-dfsa-test_20260620T000000Z"
    diff_file = record_dir / "diff.txt"
    raw_file = record_dir / "raw.html"
    original_diff = diff_file.read_text(encoding="utf-8")

    # Seal the two hashes exactly as create_canonical_evidence_record does.
    record["content"]["diff_hash"] = "sha256:" + hashlib.sha256(diff_file.read_bytes()).hexdigest()
    record["content"]["raw_hash"] = "sha256:" + hashlib.sha256(raw_file.read_bytes()).hexdigest()
    assert validate_evidence_record(record, base_dir=tmp_path)["valid"] is True

    # Tamper the redline in place -> diff_hash mismatch -> invalid.
    diff_file.write_text("- Previous text\n+ ATTACKER-INSERTED obligation\n", encoding="utf-8")
    v = validate_evidence_record(record, base_dir=tmp_path)
    assert v["valid"] is False
    assert any("diff_hash" in e for e in v["errors"]), v["errors"]

    # Restore the diff, tamper the raw evidence -> raw_hash mismatch -> invalid.
    diff_file.write_text(original_diff, encoding="utf-8")
    raw_file.write_text("<main>ATTACKER swapped raw bytes</main>", encoding="utf-8")
    v2 = validate_evidence_record(record, base_dir=tmp_path)
    assert v2["valid"] is False
    assert any("raw_hash" in e for e in v2["errors"]), v2["errors"]


def test_ev1_legacy_record_without_sealed_hashes_still_validates(tmp_path):
    """EV-1 is additive: a legacy record with no diff_hash/raw_hash is unaffected."""
    record = _canonical_record(tmp_path, status="CHANGED", with_diff=True)
    assert "diff_hash" not in record["content"]
    assert "raw_hash" not in record["content"]
    assert validate_evidence_record(record, base_dir=tmp_path)["valid"] is True


def test_ev3_flavor_b_live_run_certifies(tmp_path):
    """EV-3: a live-pipeline run whose normalized_hash is the flavor-B
    stable_content_hash(normalize(...)) must now certify (previously rejected as
    'normalized_hash does not match snapshot_normalized_path'), so live runs get a
    sealed evidence record. The sealed content.current_hash stays flavor-A (sha256
    of the file) — the sealed format and verifier contract are unchanged."""
    import hashlib
    from app.text_normalization import stable_content_hash

    run = _snapshot_run_record(tmp_path)  # FIRST_SEEN
    # Overwrite the normalized snapshot with MULTI-LINE content so the two flavors
    # genuinely differ (flavor-B collapses the newlines, flavor-A keeps them).
    norm_path = tmp_path / run["snapshot_normalized_path"]
    norm_text = "Circular 3 of 2026\nThe amended AML threshold applies.\nLicensed firms are in scope."
    norm_path.write_text(norm_text, encoding="utf-8")
    flavor_a = hashlib.sha256(norm_text.encode("utf-8")).hexdigest()
    run["normalized_hash"] = stable_content_hash(norm_text)  # flavor-B (live pipeline)
    assert run["normalized_hash"] != flavor_a, "flavors must differ or the test is vacuous"

    record = create_canonical_evidence_record(run, base_dir=tmp_path)
    # The record certifies AND validates (validate re-hashes the sealed normalized
    # snapshot against content.current_hash), so the sealed record is internally
    # consistent — the whole EV-3 point: a flavor-B run gets a sealed record.
    assert validate_evidence_record(record, base_dir=tmp_path)["valid"] is True
    assert record["content"]["current_hash"].startswith("sha256:")


def test_ev3_still_rejects_a_hash_that_matches_neither_flavor(tmp_path):
    """EV-3 must not weaken integrity: a normalized_hash that is neither flavor-A
    nor flavor-B of the snapshot is still rejected."""
    run = _snapshot_run_record(tmp_path)
    run["normalized_hash"] = "0" * 64  # matches neither flavor
    import pytest as _pytest
    with _pytest.raises(EvidenceRecordError):
        create_canonical_evidence_record(run, base_dir=tmp_path)


def test_ev3_flavor_b_changed_run_with_flavor_b_previous_certifies(tmp_path):
    """EV-3 (symmetry — the case the security review found unaddressed): a live
    CHANGED run whose OWN and whose PREVIOUS run's normalized_hash are BOTH the
    pipeline flavor-B must certify. This is the alert-firing case the fix exists
    for, and it always resolves a previous run (the second hash check)."""
    import hashlib
    from app.text_normalization import stable_content_hash

    base = tmp_path
    prev_dir = base / "data" / "source_snapshots" / "2026-06-19" / "AE" / "AE-dfsa-writer-test" / "run-prev"
    prev_text = "Circular 3 of 2026\nOriginal AML threshold applies.\nLicensed firms are in scope."
    _write(prev_dir / "normalized.txt", prev_text)
    _write(prev_dir / "raw.txt", "<main>" + prev_text + "</main>")
    _write(prev_dir / "metadata.json", "{}")
    _write(prev_dir / "proof.json", '{"proof_quality":"LIMITED"}')
    previous_run = {
        "run_id": "run-prev", "source_id": "AE-dfsa-writer-test",
        "source_name": "DFSA Writer Test Source", "official_url": "https://www.dfsa.ae/example",
        "change_status": "FIRST_SEEN", "extraction_quality": "GOOD",
        "normalized_hash": stable_content_hash(prev_text),  # flavor-B, like the live pipeline
        "snapshot_normalized_path": str((prev_dir / "normalized.txt").relative_to(base)),
        "snapshot_raw_path": str((prev_dir / "raw.txt").relative_to(base)),
        "snapshot_metadata_path": str((prev_dir / "metadata.json").relative_to(base)),
        "proof_block_path": str((prev_dir / "proof.json").relative_to(base)),
        "timestamp_utc": "2026-06-19T00:00:00Z",
    }

    cur = _snapshot_run_record(base, status="CHANGED")
    cur_text = "Circular 3 of 2026\nThe AMENDED AML threshold applies.\nLicensed firms are in scope."
    (base / cur["snapshot_normalized_path"]).write_text(cur_text, encoding="utf-8")
    cur["normalized_hash"] = stable_content_hash(cur_text)  # flavor-B
    assert cur["normalized_hash"] != hashlib.sha256(cur_text.encode("utf-8")).hexdigest()

    record = create_canonical_evidence_record(cur, previous_run, base_dir=base)
    assert validate_evidence_record(record, base_dir=base)["valid"] is True
