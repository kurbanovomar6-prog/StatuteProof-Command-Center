import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.alert_drafts import build_evidence_backed_brief_draft
from app.evidence_records import build_risk_brief_inputs
from app.review_queue import record_canonical_review_action


def _write(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _pending_canonical_record(base: Path, record_id: str = "evr_review_flow_001") -> dict:
    record_dir = base / "evidence" / "dfsa" / "AE-dfsa-review-flow" / "run-1"
    current_hash = _write(record_dir / "current.normalized.txt", "Current official DFSA review-flow text")
    previous_hash = _write(record_dir / "previous.normalized.txt", "Previous official DFSA review-flow text")
    _write(record_dir / "raw.html", "<main>Current official DFSA review-flow text</main>")
    _write(record_dir / "snapshot.html", "<html><main>Current official DFSA review-flow text</main></html>")
    _write(record_dir / "metadata.json", json.dumps({"provider": "fixture"}, sort_keys=True))
    _write(record_dir / "diff.txt", "- Previous official DFSA review-flow text\n+ Current official DFSA review-flow text\n")
    record = {
        "schema_version": "2.0",
        "record_id": record_id,
        "record_status": "complete",
        "source": {
            "source_id": "AE-dfsa-review-flow",
            "regulator": "DFSA",
            "official_url": "https://www.dfsa.ae/example",
            "source_name": "DFSA Review Flow",
        },
        "run": {"run_id": "run-1", "timestamp": "2026-06-21T00:00:00Z", "status": "CHANGED"},
        "content": {
            "previous_hash": f"sha256:{previous_hash}",
            "current_hash": f"sha256:{current_hash}",
            "raw_content_path": "evidence/dfsa/AE-dfsa-review-flow/run-1/raw.html",
            "normalized_current_path": "evidence/dfsa/AE-dfsa-review-flow/run-1/current.normalized.txt",
            "normalized_previous_path": "evidence/dfsa/AE-dfsa-review-flow/run-1/previous.normalized.txt",
        },
        "change": {
            "diff_path": "evidence/dfsa/AE-dfsa-review-flow/run-1/diff.txt",
            "summary": "Fixture diff for canonical review workflow.",
            "lines_added": 1,
            "lines_removed": 1,
        },
        "files": {
            "snapshot_path": "evidence/dfsa/AE-dfsa-review-flow/run-1/snapshot.html",
            "raw_path": "evidence/dfsa/AE-dfsa-review-flow/run-1/raw.html",
            "normalized_path": "evidence/dfsa/AE-dfsa-review-flow/run-1/current.normalized.txt",
            "previous_path": "evidence/dfsa/AE-dfsa-review-flow/run-1/previous.normalized.txt",
            "metadata_path": "evidence/dfsa/AE-dfsa-review-flow/run-1/metadata.json",
            "diff_path": "evidence/dfsa/AE-dfsa-review-flow/run-1/diff.txt",
        },
        "integrity": {
            "hash_verified": True,
            "integrity_status": "VERIFIED",
            "verified_at": "2026-06-21T00:01:00Z",
        },
        "review": {
            "human_review_required": True,
            "review_status": "pending",
            "review_reason": "Customer-facing brief requires human review.",
        },
    }
    (record_dir / "evidence-record.json").write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return record


def test_canonical_review_action_approval_unlocks_non_delivery_brief_draft(tmp_path):
    record = _pending_canonical_record(tmp_path)

    result = record_canonical_review_action(
        record["record_id"],
        decision="approved",
        reviewer="Evidence Trail",
        note="Verified paths, hashes, and diff before draft-only use.",
        base_dir=tmp_path,
    )
    gate = build_risk_brief_inputs(record["record_id"], base_dir=tmp_path)
    draft = build_evidence_backed_brief_draft(
        record["record_id"],
        base_dir=tmp_path,
        brief_fields={
            "executive_summary": "Official DFSA source changed and requires human review.",
            "business_action_required": "Review the official source and update internal tracker if relevant.",
            "specific_obligation": "Confirm whether the update affects the monitored DFSA control inventory.",
            "risk_level": "MEDIUM",
            "confidence": "medium",
        },
    )

    assert result["status"] == "ok"
    assert result["decision"] == "approved"
    assert result["brief_eligible"] is True
    assert result["customer_delivery_approved"] is False
    assert gate["eligible"] is True
    assert draft["customer_delivery"] is False
    assert draft["delivery_approved"] is False
    assert draft["evidence_record_id"] == record["record_id"]


def test_canonical_review_action_rejection_keeps_record_blocked(tmp_path):
    record = _pending_canonical_record(tmp_path)

    result = record_canonical_review_action(
        record["record_id"],
        decision="rejected",
        reviewer="Evidence Trail",
        note="Diff requires manual investigation before draft use.",
        base_dir=tmp_path,
    )
    gate = build_risk_brief_inputs(record["record_id"], base_dir=tmp_path)

    assert result["status"] == "ok"
    assert result["decision"] == "rejected"
    assert result["brief_eligible"] is False
    assert result["customer_delivery_approved"] is False
    assert gate["eligible"] is False
    assert "rejected" in gate["blocked_reason"]
