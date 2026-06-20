import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.evidence_assessment import create_assessment
from app.review_queue import build_review_queue
from app.source_summary import build_sources_summary


def _write_sources(base: Path) -> None:
    (base / "sources.json").write_text(
        json.dumps(
            [
                {
                    "source_id": "AE-active-one",
                    "name": "Active One",
                    "url": "https://regulator.example/one",
                    "jurisdiction": "AE",
                    "enabled": True,
                    "status": "active",
                    "monitoring_mode": "fresh_alert",
                    "alert_eligible": True,
                },
                {
                    "source_id": "AE-remediation-one",
                    "name": "Remediation One",
                    "url": "https://regulator.example/remediation",
                    "jurisdiction": "AE",
                    "enabled": True,
                    "status": "remediation",
                    "monitoring_mode": "remediation",
                    "alert_eligible": False,
                },
                {
                    "source_id": "AE-disabled-one",
                    "name": "Disabled One",
                    "url": "https://regulator.example/disabled",
                    "jurisdiction": "AE",
                    "enabled": False,
                    "status": "active",
                    "monitoring_mode": "fresh_alert",
                    "alert_eligible": True,
                },
            ]
        ),
        encoding="utf-8",
    )


def _write_run(base: Path, *, run_id: str = "run-queue-1", source_id: str = "AE-active-one", change_status: str = "CHANGED") -> dict:
    snapshot_dir = base / "data" / "source_snapshots" / "2026-06-16" / "AE" / source_id / run_id
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    proof_path = snapshot_dir / "proof.json"
    normalized_path = snapshot_dir / "normalized.txt"
    proof_path.write_text(json.dumps({"proof_quality": "GOOD"}), encoding="utf-8")
    normalized_path.write_text("official regulatory text", encoding="utf-8")
    record = {
        "run_id": run_id,
        "timestamp_utc": "2026-06-16T09:00:00+00:00",
        "market": "AE",
        "jurisdiction": "AE",
        "source_id": source_id,
        "source_name": "Active One",
        "official_url": "https://regulator.example/one",
        "final_url": "https://regulator.example/one",
        "access_status": "accessible",
        "extraction_quality": "GOOD",
        "change_status": change_status,
        "normalized_hash": "a" * 64,
        "content_hash": "a" * 64,
        "raw_hash": "b" * 64,
        "snapshot_normalized_path": str(normalized_path.relative_to(base)),
        "proof_block_path": str(proof_path.relative_to(base)),
        "diff_json_path": str((snapshot_dir / "diff.json").relative_to(base)) if change_status == "CHANGED" else None,
    }
    if change_status == "CHANGED":
        (snapshot_dir / "diff.json").write_text(json.dumps({"meaningful_change_detected": True}), encoding="utf-8")
    runs_path = base / "data" / "source_runs" / "source_runs.jsonl"
    runs_path.parent.mkdir(parents=True, exist_ok=True)
    with runs_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
    return record


class IdealProductWorkflowTests(unittest.TestCase):
    def test_source_summary_reads_current_registry_truth(self):
        summary = build_sources_summary("AE")

        self.assertTrue(summary["ok"])
        self.assertEqual(summary["enabled_count"], 239)
        self.assertEqual(summary["readiness_supported_count"], 170)
        self.assertEqual(summary["fresh_alert_count"], 170)
        self.assertEqual(summary["evidence_library_count"], 61)
        self.assertEqual(summary["candidate_count"], 5)
        self.assertEqual(summary["remediation_count"], 3)
        self.assertIn("170 fresh-alert eligible", summary["source_truth"])
        self.assertIn("Not legal advice", summary["disclaimer"])

    def test_source_summary_uses_registry_and_run_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)
            _write_run(base)

            summary = build_sources_summary("AE", base_dir=base)

            self.assertEqual(summary["enabled_count"], 2)
            self.assertEqual(summary["readiness_supported_count"], 1)
            self.assertEqual(summary["fresh_alert_count"], 1)
            self.assertEqual(summary["evidence_library_count"], 0)
            self.assertEqual(summary["candidate_count"], 0)
            self.assertEqual(summary["remediation_count"], 1)
            self.assertEqual(summary["monitored_count"], 1)
            self.assertEqual(summary["last_run_at"], "2026-06-16T09:00:00+00:00")

    def test_review_queue_returns_pending_evidence_without_assessment(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)
            run = _write_run(base)

            queue = build_review_queue(base_dir=base, status="pending")

            self.assertEqual(queue["total"], 1)
            self.assertEqual(queue["queue"][0]["evidence_record_id"], run["run_id"])
            self.assertTrue(queue["queue"][0]["pending_review"])
            self.assertEqual(queue["queue"][0]["source_health_status"], "HASH_DRIFT")
            self.assertNotIn("SAMPLE", json.dumps(queue))

    def test_review_queue_returns_assessed_record_when_assessment_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)
            run = _write_run(base)
            assessment = create_assessment(
                evidence_record_id=run["run_id"],
                impact_level="policy_review",
                internal_note="Review AML policy impact.",
                reviewer_user_id="user-1",
                reviewer_name="Omar",
                base_dir=base,
            )

            pending = build_review_queue(base_dir=base, status="pending")
            assessed = build_review_queue(base_dir=base, status="assessed")

            self.assertEqual(pending["total"], 0)
            self.assertEqual(assessed["total"], 1)
            self.assertFalse(assessed["queue"][0]["pending_review"])
            self.assertEqual(assessed["queue"][0]["latest_assessment_id"], assessment["assessment_id"])
            self.assertEqual(assessed["queue"][0]["impact_level"], "policy_review")

    def test_review_queue_empty_state_has_no_fake_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_sources(base)

            queue = build_review_queue(base_dir=base, status="all")

            self.assertEqual(queue["queue"], [])
            self.assertEqual(queue["total"], 0)
            self.assertIn("saved evidence", queue["message"].lower())


if __name__ == "__main__":
    unittest.main()
