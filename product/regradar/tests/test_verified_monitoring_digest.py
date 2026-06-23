import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.verified_monitoring_digest import build_verified_monitoring_digest, render_verified_monitoring_digest_markdown


def _write_sources(base: Path) -> None:
    (base / "sources.json").write_text(
        json.dumps(
            [
                {
                    "source_id": "AE-vara-rulebook",
                    "name": "VARA Rulebook",
                    "url": "https://www.vara.ae/",
                    "jurisdiction": "AE",
                    "category": "virtual_assets",
                    "enabled": True,
                    "status": "active",
                    "monitoring_mode": "fresh_alert",
                },
                {
                    "source_id": "AE-source-failing",
                    "name": "Failing Official Source",
                    "url": "https://regulator.example/failing",
                    "jurisdiction": "AE",
                    "category": "financial_regulator",
                    "enabled": True,
                    "status": "active",
                    "monitoring_mode": "fresh_alert",
                },
            ],
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _write_run(
    base: Path,
    *,
    source_id: str = "AE-vara-rulebook",
    run_id: str = "run-1",
    change_status: str = "CHANGED",
    normalized_hash: str = "a" * 64,
) -> dict:
    runs_path = base / "data" / "source_runs" / "source_runs.jsonl"
    runs_path.parent.mkdir(parents=True, exist_ok=True)
    run = {
        "run_id": run_id,
        "source_id": source_id,
        "source_name": source_id,
        "official_url": f"https://regulator.example/{source_id}",
        "timestamp_utc": "2026-06-20T10:00:00Z",
        "change_status": change_status,
        "extraction_quality": "FAILED" if change_status == "FAILED" else "GOOD",
        "normalized_hash": normalized_hash,
    }
    with runs_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(run, sort_keys=True) + "\n")
    return run


def _write_alert(
    base: Path,
    *,
    source_id: str = "AE-vara-rulebook",
    run_id: str = "run-1",
    evidence_record_id: str = "",
    diff: dict | None = None,
    delivery_approved: bool = False,
) -> None:
    diff = diff or {
        "meaningful_change_detected": True,
        "diff_quality": "GOOD",
        "diff_summary": "1 added, 0 removed, 0 changed chunks; 9 unchanged.",
        "added_count": 1,
        "removed_count": 0,
        "changed_count": 0,
        "unchanged_count": 9,
        "added_chunks": ["New AML/CFT circular"],
        "removed_chunks": [],
        "changed_chunks": [],
    }
    snapshot_dir = base / "data" / "source_snapshots" / "2026-06-20" / "AE" / source_id / run_id
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    diff_path = snapshot_dir / "diff.json"
    diff_path.write_text(json.dumps(diff, sort_keys=True), encoding="utf-8")
    queue_dir = base / "data" / "alert_queue"
    queue_dir.mkdir(parents=True, exist_ok=True)
    alert = {
        "source_id": source_id,
        "run_id": run_id,
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
    (queue_dir / f"{source_id}-{run_id}.json").write_text(json.dumps(alert, sort_keys=True), encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_canonical_record(base: Path, *, source_id: str = "AE-vara-rulebook", review_status: str = "approved") -> str:
    record_dir = base / "evidence" / "vara" / source_id / "run-1"
    record_dir.mkdir(parents=True, exist_ok=True)
    current = record_dir / "current.normalized.txt"
    previous = record_dir / "previous.normalized.txt"
    raw = record_dir / "raw.txt"
    snapshot = record_dir / "snapshot.txt"
    metadata = record_dir / "metadata.json"
    diff = record_dir / "diff.txt"
    current.write_text("Current official VARA AML/CFT rulebook text", encoding="utf-8")
    previous.write_text("Previous official VARA AML/CFT rulebook text", encoding="utf-8")
    raw.write_text("<main>Current official VARA AML/CFT rulebook text</main>", encoding="utf-8")
    snapshot.write_text("<html><main>Current official VARA AML/CFT rulebook text</main></html>", encoding="utf-8")
    metadata.write_text(json.dumps({"provider": "fixture"}, sort_keys=True), encoding="utf-8")
    diff.write_text("- Previous official VARA AML/CFT rulebook text\n+ Current official VARA AML/CFT rulebook text\n", encoding="utf-8")
    record = {
        "schema_version": "2.0",
        "record_id": "evr_vara_rulebook_run_1",
        "record_status": "complete",
        "source": {
            "source_id": source_id,
            "regulator": "VARA",
            "official_url": "https://www.vara.ae/",
            "source_name": "VARA Rulebook",
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
            "summary": "Fixture canonical record.",
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


class VerifiedMonitoringDigestTests(unittest.TestCase):
    def test_unlinked_pending_alert_is_held_and_not_deliverable(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)
            _write_run(base)
            _write_alert(base)

            digest = build_verified_monitoring_digest(base_dir=base)
            item = digest["items"][0]

            self.assertEqual(item["triage_status"], "HOLD")
            self.assertIn("missing_canonical_evidence_record_id", item["blockers"])
            self.assertFalse(item["customer_delivery_allowed"])
            self.assertFalse(digest["customer_delivery"])

    def test_limited_non_meaningful_diff_is_likely_noise_when_evidence_is_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)
            _write_run(base)
            record_id = _write_canonical_record(base)
            _write_alert(
                base,
                evidence_record_id=record_id,
                diff={
                    "meaningful_change_detected": False,
                    "diff_quality": "LIMITED",
                    "diff_summary": "1 added, 0 removed, 0 changed chunks; 25 unchanged.",
                    "added_count": 1,
                    "removed_count": 0,
                    "changed_count": 0,
                    "unchanged_count": 25,
                    "added_chunks": ["Row hash: abc123 locale=en"],
                    "removed_chunks": [],
                    "changed_chunks": [],
                },
            )

            digest = build_verified_monitoring_digest(base_dir=base)
            item = digest["items"][0]

            self.assertEqual(item["triage_status"], "LIKELY_NOISE")
            self.assertTrue(item["brief_input_eligible"])
            self.assertIn("meaningful_change_detected_false", item["noise_indicators"])
            self.assertFalse(item["customer_delivery_allowed"])

    def test_approved_canonical_evidence_can_be_review_ready_without_customer_delivery(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)
            _write_run(base)
            record_id = _write_canonical_record(base)
            _write_alert(base, evidence_record_id=record_id)

            digest = build_verified_monitoring_digest(base_dir=base)
            item = digest["items"][0]

            self.assertEqual(item["triage_status"], "REVIEW_READY")
            self.assertTrue(item["brief_input_eligible"])
            self.assertEqual(digest["summary"]["customer_delivery_allowed"], 0)
            self.assertFalse(item["customer_delivery_allowed"])

    def test_source_health_blocker_is_included_in_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)
            _write_run(base, source_id="AE-source-failing", run_id="run-1", change_status="FAILED")
            _write_run(base, source_id="AE-source-failing", run_id="run-2", change_status="FAILED")
            _write_run(base, source_id="AE-source-failing", run_id="run-3", change_status="FAILED")
            _write_alert(base, source_id="AE-source-failing", run_id="run-3")

            digest = build_verified_monitoring_digest(base_dir=base)
            item = digest["items"][0]

            self.assertEqual(digest["summary"]["source_health_blocked"], 1)
            self.assertIn("source_health_operator_review_required", item["blockers"])

    def test_disabled_source_health_failures_are_historical_not_active_blockers(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)
            sources = json.loads((base / "sources.json").read_text(encoding="utf-8"))
            sources.append(
                {
                    "source_id": "AE-disabled-source",
                    "name": "Disabled Historical Source",
                    "url": "https://regulator.example/disabled",
                    "jurisdiction": "AE",
                    "enabled": False,
                    "status": "disabled_external_access",
                    "monitoring_mode": "remediation",
                }
            )
            (base / "sources.json").write_text(json.dumps(sources), encoding="utf-8")
            _write_run(base, source_id="AE-disabled-source", run_id="run-1", change_status="FAILED")
            _write_run(base, source_id="AE-disabled-source", run_id="run-2", change_status="FAILED")
            _write_run(base, source_id="AE-disabled-source", run_id="run-3", change_status="FAILED")
            _write_alert(base, source_id="AE-vara-rulebook", run_id="run-ok")

            digest = build_verified_monitoring_digest(base_dir=base)
            markdown = render_verified_monitoring_digest_markdown(digest)

            self.assertEqual(digest["summary"]["source_health_blocked"], 0)
            self.assertEqual(digest["summary"]["historical_source_health_blocked"], 1)
            self.assertEqual(digest["source_health"]["sources_requiring_operator_review"], 0)
            self.assertEqual(digest["source_health"]["historical_sources_requiring_operator_review"], 1)
            self.assertIn("Historical / Disabled Source Failures", markdown)
            self.assertIn("AE-disabled-source", markdown)

    def test_markdown_report_preserves_operator_only_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)
            _write_run(base)
            _write_alert(base)

            digest = build_verified_monitoring_digest(base_dir=base)
            markdown = render_verified_monitoring_digest_markdown(digest)

            self.assertIn("operator-only", markdown.lower())
            self.assertIn("not a customer brief", markdown.lower())
            self.assertIn("Customer delivery allowed: 0", markdown)


if __name__ == "__main__":
    unittest.main()
