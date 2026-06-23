import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.evidence_records import record_canonical_evidence_review
from app.internal_brief_cycle import (
    InternalBriefCycleError,
    build_internal_non_customer_brief_cycle,
    validate_internal_non_customer_brief_cycle,
    write_internal_non_customer_brief_cycle,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_sources(base: Path) -> None:
    (base / "sources.json").write_text(
        json.dumps(
            [
                {
                    "source_id": "AE-sca-aml-cft",
                    "name": "SCA AML/CFT",
                    "url": "https://www.sca.gov.ae/en/regulations/anti-money-laundering-and-terrorist-financing",
                    "jurisdiction": "AE",
                    "category": "aml_cft",
                    "enabled": True,
                    "status": "active",
                    "monitoring_mode": "fresh_alert",
                }
            ],
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _write_run(base: Path, *, run_id: str = "run-1") -> None:
    runs_path = base / "data" / "source_runs" / "source_runs.jsonl"
    runs_path.parent.mkdir(parents=True, exist_ok=True)
    run = {
        "run_id": run_id,
        "source_id": "AE-sca-aml-cft",
        "source_name": "SCA AML/CFT",
        "official_url": "https://www.sca.gov.ae/en/regulations/anti-money-laundering-and-terrorist-financing",
        "timestamp_utc": "2026-06-20T10:00:00Z",
        "change_status": "CHANGED",
        "access_status": "accessible",
        "extraction_quality": "GOOD",
        "normalized_hash": "a" * 64,
    }
    with runs_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(run, sort_keys=True) + "\n")


def _write_canonical_record(base: Path, *, review_status: str = "pending") -> str:
    record_dir = base / "evidence" / "sca" / "AE-sca-aml-cft" / "run-1"
    record_dir.mkdir(parents=True, exist_ok=True)
    current = record_dir / "current.normalized.txt"
    previous = record_dir / "previous.normalized.txt"
    raw = record_dir / "raw.txt"
    snapshot = record_dir / "snapshot.txt"
    metadata = record_dir / "metadata.json"
    diff = record_dir / "diff.txt"
    current.write_text("Current SCA AML/CFT official text", encoding="utf-8")
    previous.write_text("Previous SCA AML/CFT official text", encoding="utf-8")
    raw.write_text("<main>Current SCA AML/CFT official text</main>", encoding="utf-8")
    snapshot.write_text("<html><main>Current SCA AML/CFT official text</main></html>", encoding="utf-8")
    metadata.write_text(json.dumps({"provider": "fixture"}, sort_keys=True), encoding="utf-8")
    diff.write_text("- Previous SCA AML/CFT official text\n+ Current SCA AML/CFT official text\n", encoding="utf-8")
    record = {
        "schema_version": "2.0",
        "record_id": "evr_sca_aml_cft_run_1",
        "record_status": "complete",
        "source": {
            "source_id": "AE-sca-aml-cft",
            "regulator": "SCA",
            "official_url": "https://www.sca.gov.ae/en/regulations/anti-money-laundering-and-terrorist-financing",
            "source_name": "SCA AML/CFT",
        },
        "run": {"run_id": "run-1", "timestamp": "2026-06-20T10:00:00Z", "status": "CHANGED"},
        "content": {
            "current_hash": f"sha256:{_sha(current)}",
            "previous_hash": f"sha256:{_sha(previous)}",
            "raw_content_path": str(raw.relative_to(base)),
            "normalized_current_path": str(current.relative_to(base)),
            "normalized_previous_path": str(previous.relative_to(base)),
        },
        "change": {
            "summary": "Fixture SCA AML/CFT change.",
            "lines_added": 1,
            "lines_removed": 1,
            "diff_path": str(diff.relative_to(base)),
        },
        "files": {
            "snapshot_path": str(snapshot.relative_to(base)),
            "raw_path": str(raw.relative_to(base)),
            "normalized_path": str(current.relative_to(base)),
            "previous_path": str(previous.relative_to(base)),
            "metadata_path": str(metadata.relative_to(base)),
            "diff_path": str(diff.relative_to(base)),
        },
        "integrity": {"hash_verified": True, "integrity_status": "VERIFIED", "verified_at": "2026-06-20T10:01:00Z"},
        "review": {
            "human_review_required": True,
            "review_status": review_status,
            "review_reason": "Fixture review.",
        },
    }
    (record_dir / "evidence-record.json").write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
    return record["record_id"]


def _write_alert(base: Path, *, evidence_record_id: str = "", delivery_approved: bool = False) -> None:
    snapshot_dir = base / "data" / "source_snapshots" / "2026-06-20" / "AE" / "AE-sca-aml-cft" / "run-1"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    diff_path = snapshot_dir / "diff.json"
    diff_path.write_text(
        json.dumps(
            {
                "meaningful_change_detected": True,
                "diff_quality": "GOOD",
                "diff_summary": "0 added, 0 removed, 3 changed chunks; 8 unchanged.",
                "added_count": 0,
                "removed_count": 0,
                "changed_count": 3,
                "unchanged_count": 8,
                "added_chunks": [],
                "removed_chunks": [],
                "changed_chunks": [{"before": ["Previous"], "after": ["Current"]}],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    queue_dir = base / "data" / "alert_queue"
    queue_dir.mkdir(parents=True, exist_ok=True)
    alert = {
        "source_id": "AE-sca-aml-cft",
        "run_id": "run-1",
        "run_at": "2026-06-20T10:00:00Z",
        "queued_at": "2026-06-20T10:01:00Z",
        "status": "PENDING_REVIEW",
        "change_status": "CHANGED",
        "diff_json_path": str(diff_path.relative_to(base)),
        "proof_block_path": str((snapshot_dir / "proof.json").relative_to(base)),
        "evidence_record_id": evidence_record_id,
        "human_reviewed": False,
        "delivery_approved": delivery_approved,
        "normalized_hash": "a" * 64,
    }
    (queue_dir / "sca-alert.json").write_text(json.dumps(alert, sort_keys=True), encoding="utf-8")


class InternalBriefCycleTests(unittest.TestCase):
    def test_missing_evidence_link_blocks_cycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)
            _write_run(base)
            _write_alert(base)

            with self.assertRaises(InternalBriefCycleError):
                build_internal_non_customer_brief_cycle(base_dir=base)

    def test_pending_evidence_blocks_cycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)
            _write_run(base)
            record_id = _write_canonical_record(base, review_status="pending")
            _write_alert(base, evidence_record_id=record_id)

            with self.assertRaises(InternalBriefCycleError):
                build_internal_non_customer_brief_cycle(base_dir=base)

    def test_external_approval_builds_internal_sample_without_customer_delivery(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)
            _write_run(base)
            record_id = _write_canonical_record(base, review_status="pending")
            _write_alert(base, evidence_record_id=record_id)
            review = record_canonical_evidence_review(
                record_id,
                decision="approved",
                reviewer="Evidence Trail",
                note="Fixture operator review for internal sample.",
                base_dir=base,
            )

            report = build_internal_non_customer_brief_cycle(base_dir=base)
            validation = validate_internal_non_customer_brief_cycle(report, base_dir=base)
            paths = write_internal_non_customer_brief_cycle(report, base_dir=base)

            self.assertTrue(validation["valid"])
            self.assertEqual(report["review"]["review_id"], review["review_id"])
            self.assertFalse(report["customer_delivery"])
            self.assertFalse(report["delivery_approved"])
            self.assertTrue((base / paths["json_path"]).exists())
            self.assertTrue((base / paths["markdown_path"]).exists())

    def test_latest_rejection_blocks_cycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)
            _write_run(base)
            record_id = _write_canonical_record(base, review_status="pending")
            _write_alert(base, evidence_record_id=record_id)
            record_canonical_evidence_review(
                record_id,
                decision="approved",
                reviewer="Evidence Trail",
                note="Fixture operator review.",
                base_dir=base,
            )
            record_canonical_evidence_review(
                record_id,
                decision="rejected",
                reviewer="Evidence Trail",
                note="Fixture rejection supersedes approval.",
                base_dir=base,
            )

            with self.assertRaises(InternalBriefCycleError):
                build_internal_non_customer_brief_cycle(base_dir=base)

    def test_forbidden_phrase_blocks_internal_brief_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)
            _write_run(base)
            record_id = _write_canonical_record(base, review_status="pending")
            _write_alert(base, evidence_record_id=record_id)
            record_canonical_evidence_review(
                record_id,
                decision="approved",
                reviewer="Evidence Trail",
                note="Fixture operator review.",
                base_dir=base,
            )

            with self.assertRaises(InternalBriefCycleError):
                build_internal_non_customer_brief_cycle(
                    base_dir=base,
                    brief_fields={
                        "executive_summary": "This will guarantee compliance.",
                        "business_action_required": "No action.",
                        "specific_obligation": "Unsafe.",
                        "risk_level": "LOW",
                        "confidence": "LOW",
                    },
                )


if __name__ == "__main__":
    unittest.main()
