import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.audit_export import build_customer_audit_pack_export_response


def _write(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_record(base: Path, *, review_status: str = "approved") -> dict:
    record_dir = base / "evidence" / "dfsa" / "AE-dfsa-export-test" / "run_AE-dfsa-export-test_20260620T000000Z"
    current_hash = _write(record_dir / "current.normalized.txt", "Current official DFSA export text")
    previous_hash = _write(record_dir / "previous.normalized.txt", "Previous official DFSA export text")
    _write(record_dir / "raw.html", "<main>Current official DFSA export text</main>")
    _write(record_dir / "snapshot.html", "<html><main>Current official DFSA export text</main></html>")
    _write(record_dir / "metadata.json", json.dumps({"provider": "fixture"}, sort_keys=True))
    _write(record_dir / "diff.txt", "- Previous official DFSA export text\n+ Current official DFSA export text\n")
    record = {
        "schema_version": "2.0",
        "record_id": "evr_dfsa_export_test_20260620T000000Z",
        "record_status": "complete",
        "source": {
            "source_id": "AE-dfsa-export-test",
            "regulator": "DFSA",
            "official_url": "https://www.dfsa.ae/example",
            "source_name": "DFSA Export Test Source",
        },
        "run": {
            "run_id": "run_AE-dfsa-export-test_20260620T000000Z",
            "timestamp": "2026-06-20T00:00:00Z",
            "status": "CHANGED",
        },
        "content": {
            "previous_hash": f"sha256:{previous_hash}",
            "current_hash": f"sha256:{current_hash}",
            "raw_content_path": str((record_dir / "raw.html").relative_to(base)),
            "normalized_current_path": str((record_dir / "current.normalized.txt").relative_to(base)),
            "normalized_previous_path": str((record_dir / "previous.normalized.txt").relative_to(base)),
        },
        "change": {
            "diff_path": str((record_dir / "diff.txt").relative_to(base)),
            "summary": "Evidence-only DFSA export fixture summary.",
            "lines_added": 1,
            "lines_removed": 1,
        },
        "files": {
            "snapshot_path": str((record_dir / "snapshot.html").relative_to(base)),
            "raw_path": str((record_dir / "raw.html").relative_to(base)),
            "normalized_path": str((record_dir / "current.normalized.txt").relative_to(base)),
            "previous_path": str((record_dir / "previous.normalized.txt").relative_to(base)),
            "metadata_path": str((record_dir / "metadata.json").relative_to(base)),
            "diff_path": str((record_dir / "diff.txt").relative_to(base)),
        },
        "integrity": {
            "hash_verified": True,
            "integrity_status": "VERIFIED",
            "verified_at": "2026-06-20T00:01:00Z",
        },
        "review": {
            "human_review_required": True,
            "review_status": review_status,
            "review_reason": "Customer-facing export requires human review.",
        },
    }
    (record_dir / "evidence-record.json").write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return record


def test_customer_export_blocks_source_snapshot_proof(tmp_path):
    proof_path = tmp_path / "data" / "source_snapshots" / "2026-06-20" / "AE" / "AE-dfsa-test" / "proof.json"
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text(json.dumps({"proof_quality": "GOOD"}), encoding="utf-8")

    with pytest.raises(ValueError) as exc:
        build_customer_audit_pack_export_response(str(proof_path.relative_to(tmp_path)), base_dir=tmp_path)

    assert "not a canonical evidence record" in str(exc.value)


def test_customer_export_blocks_pending_canonical_evidence(tmp_path):
    record = _canonical_record(tmp_path, review_status="pending")

    with pytest.raises(ValueError) as exc:
        build_customer_audit_pack_export_response(record["record_id"], base_dir=tmp_path)

    assert "review_status" in str(exc.value)


def test_customer_export_accepts_approved_canonical_evidence(tmp_path):
    record = _canonical_record(tmp_path, review_status="approved")

    response = build_customer_audit_pack_export_response(record["record_id"], base_dir=tmp_path)

    assert response["ok"] is True
    assert response["customer_delivery"] is True
    assert response["canonical_evidence_record_id"] == record["record_id"]
    assert response["evidence_record_id"] == record["record_id"]
    assert (tmp_path / response["export"]["md_path"]).exists()
    assert (tmp_path / response["export"]["html_path"]).exists()
