import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.audit_export import render_audit_pack_markdown, write_audit_pack
from app.email_delivery import deliver_weekly_brief_test_mode
from app.evidence_assessment import create_assessment, latest_assessment_for
from app.weekly_brief import build_weekly_brief


DISCLAIMER = "Monitoring intelligence only. Not legal advice."


def _write_evidence_run(base: Path, *, run_id: str = "run-1", with_proof: bool = True) -> dict:
    snapshot_dir = base / "data" / "source_snapshots" / "2026-06-16" / "AE" / "AE-test-source" / run_id
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    proof_path = snapshot_dir / "proof.json"
    normalized_path = snapshot_dir / "normalized.txt"
    normalized_path.write_text("official regulatory text", encoding="utf-8")
    if with_proof:
        proof_path.write_text(json.dumps({"proof_quality": "GOOD"}), encoding="utf-8")

    record = {
        "run_id": run_id,
        "timestamp_utc": "2026-06-16T09:00:00+00:00",
        "market": "AE",
        "source_id": "AE-test-source",
        "source_name": "Official Test Source",
        "category": "AML/CFT",
        "official_url": "https://regulator.example/source",
        "final_url": "https://regulator.example/source",
        "access_status": "accessible",
        "fetch_method": "fixture",
        "extraction_quality": "GOOD",
        "change_status": "CHANGED",
        "normalized_hash": "a" * 64,
        "content_hash": "a" * 64,
        "raw_hash": "b" * 64,
        "snapshot_normalized_path": str(normalized_path.relative_to(base)),
        "proof_block_path": str(proof_path.relative_to(base)) if with_proof else None,
        "diff_json_path": None,
    }
    runs_path = base / "data" / "source_runs" / "source_runs.jsonl"
    runs_path.parent.mkdir(parents=True, exist_ok=True)
    runs_path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    return record


class MvpTrustWorkflowTests(unittest.TestCase):
    def test_assessment_requires_saved_evidence_with_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_evidence_run(base, with_proof=False)

            with self.assertRaises(ValueError) as ctx:
                create_assessment(
                    evidence_record_id="run-1",
                    impact_level="monitor",
                    internal_note="Reviewed but proof is missing.",
                    reviewer_user_id="user-1",
                    reviewer_name="Omar",
                    base_dir=base,
                )

            self.assertIn("proof", str(ctx.exception).lower())

    def test_create_assessment_links_note_to_saved_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            run = _write_evidence_run(base)

            assessment = create_assessment(
                evidence_record_id=run["run_id"],
                impact_level="policy_review",
                internal_note="Review internal AML policy impact.",
                reviewer_user_id="user-1",
                reviewer_name="Omar",
                next_action="Assign policy owner.",
                base_dir=base,
            )

            self.assertEqual(assessment["evidence_record_id"], run["run_id"])
            self.assertEqual(assessment["source_id"], run["source_id"])
            self.assertEqual(assessment["impact_level"], "policy_review")
            self.assertEqual(assessment["normalized_hash"], run["normalized_hash"])
            self.assertIn("Review internal AML policy impact.", assessment["internal_note"])
            self.assertEqual(assessment["legal_disclaimer"], DISCLAIMER)
            self.assertEqual(latest_assessment_for(run["run_id"], base_dir=base)["assessment_id"], assessment["assessment_id"])

    def test_audit_pack_export_includes_proof_hash_assessment_and_disclaimer(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            run = _write_evidence_run(base)
            assessment = create_assessment(
                evidence_record_id=run["run_id"],
                impact_level="external_counsel_review",
                internal_note="Ask counsel to review impact.",
                reviewer_user_id="user-1",
                reviewer_name="Omar",
                base_dir=base,
            )

            markdown = render_audit_pack_markdown(run, assessment=assessment)

            self.assertIn("Official Test Source", markdown)
            self.assertIn("https://regulator.example/source", markdown)
            self.assertIn("proof.json", markdown)
            self.assertIn("a" * 64, markdown)
            self.assertIn("external_counsel_review", markdown)
            self.assertIn("Ask counsel to review impact.", markdown)
            self.assertIn(DISCLAIMER, markdown)
            self.assertNotIn("SAMPLE / DEMO", markdown)

            out = write_audit_pack(run, assessment=assessment, base_dir=base)
            self.assertTrue((base / out["md_path"]).exists())
            self.assertTrue((base / out["html_path"]).exists())

    def test_demo_audit_pack_is_labeled_sample_demo(self):
        run = {
            "run_id": "demo-run",
            "source_name": "Demo Source",
            "official_url": "https://example.com",
            "normalized_hash": "demo",
            "proof_block_path": "demo-fixture",
            "timestamp_utc": "2026-06-16T09:00:00+00:00",
            "change_status": "CHANGED",
            "extraction_quality": "GOOD",
        }

        markdown = render_audit_pack_markdown(run, demo=True)

        self.assertIn("SAMPLE / DEMO - NOT CUSTOMER DATA", markdown)
        self.assertIn(DISCLAIMER, markdown)

    def test_weekly_brief_email_test_mode_writes_local_outbox_and_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            brief = build_weekly_brief(
                client_profile={"client_id": "pilot", "company_name": "Pilot Client"},
                market="AE",
                start=__import__("datetime").datetime(2026, 6, 9, tzinfo=__import__("datetime").timezone.utc),
                end=__import__("datetime").datetime(2026, 6, 16, tzinfo=__import__("datetime").timezone.utc),
                alerts=[],
            )

            result = deliver_weekly_brief_test_mode(
                brief,
                recipient_email="mlro@example.com",
                base_dir=base,
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["channel"], "email")
            self.assertEqual(result["status"], "written")
            payload = json.loads((base / result["outbox_path"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["to"], "mlro@example.com")
            self.assertIn("StatuteProof Weekly Regulatory Brief", payload["subject"])
            self.assertIn(DISCLAIMER, payload["body_text"])
            self.assertFalse(payload["external_send"])
            status_rows = (base / result["status_path"]).read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(status_rows), 1)
            self.assertIn('"status": "written"', status_rows[0])

    def test_weekly_brief_email_test_mode_records_validation_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            brief = build_weekly_brief(
                client_profile={"client_id": "pilot", "company_name": "Pilot Client"},
                market="AE",
                start=__import__("datetime").datetime(2026, 6, 9, tzinfo=__import__("datetime").timezone.utc),
                end=__import__("datetime").datetime(2026, 6, 16, tzinfo=__import__("datetime").timezone.utc),
                alerts=[],
            )

            result = deliver_weekly_brief_test_mode(
                brief,
                recipient_email="not-an-email",
                base_dir=base,
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["status"], "failed")
            status_rows = (base / result["status_path"]).read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(status_rows), 1)
            self.assertIn("Invalid recipient email", status_rows[0])


if __name__ == "__main__":
    unittest.main()
