import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.alert_review import (
    DECISION_DO_NOT_SEND,
    DECISION_HOLD,
    DECISION_URGENT,
    DECISION_WEEKLY,
    STATUS_APPROVED_WEEKLY,
    STATUS_NEEDS_SOURCE_ADAPTER,
    STATUS_REJECTED,
    list_alert_drafts,
    load_review_records,
    review_alert,
)


def _write_alert(base_dir: Path, *, low_confidence: bool = False) -> dict:
    folder = base_dir / "data" / "source_snapshots" / "2026-05-30" / "AE" / "AE-vara" / "run-1"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "diff.json").write_text(json.dumps({"diff_quality": "GOOD"}), encoding="utf-8")
    (folder / "proof.json").write_text(json.dumps({"proof_quality": "GOOD"}), encoding="utf-8")
    alert = {
        "alert_id": "draft-test-1",
        "review_status": "DRAFT",
        "send_decision": "HOLD_FOR_REVIEW",
        "market": "AE",
        "source_id": "AE-vara",
        "source_name": "Dubai Virtual Assets Regulatory Authority (VARA)",
        "checked_at_utc": "2026-05-30T10:00:00+00:00",
        "change_type": "LICENSING",
        "risk_level": "MEDIUM",
        "confidence": "LOW" if low_confidence else "MEDIUM",
        "limitations": [],
        "proof_block": {
            "proof_quality": "GOOD",
            "meaningful_change_detected": True,
            "diff_json_path": "data/source_snapshots/2026-05-30/AE/AE-vara/run-1/diff.json",
            "snapshot_normalized_path": "data/source_snapshots/2026-05-30/AE/AE-vara/run-1/normalized.txt",
        },
    }
    (folder / "alert_draft.json").write_text(json.dumps(alert, indent=2), encoding="utf-8")
    return alert


class AlertReviewTests(unittest.TestCase):
    def test_draft_alert_can_be_approved_for_weekly(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_alert(base)
            review_file = base / "data" / "alert_reviews" / "reviews.jsonl"

            record = review_alert(
                alert_id="draft-test-1",
                action="approve_weekly",
                reviewer="Omar",
                note="Weekly review approved.",
                base_dir=base,
                review_file=review_file,
            )

            self.assertEqual(record["new_status"], STATUS_APPROVED_WEEKLY)
            self.assertEqual(record["new_send_decision"], DECISION_WEEKLY)

    def test_draft_alert_can_be_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_alert(base)
            review_file = base / "data" / "alert_reviews" / "reviews.jsonl"

            record = review_alert(
                alert_id="draft-test-1",
                action="reject",
                reviewer="Omar",
                note="Not relevant.",
                base_dir=base,
                review_file=review_file,
            )

            self.assertEqual(record["new_status"], STATUS_REJECTED)
            self.assertEqual(record["new_send_decision"], DECISION_DO_NOT_SEND)

    def test_low_confidence_alert_cannot_be_approved_urgent_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_alert(base, low_confidence=True)

            with self.assertRaises(ValueError):
                review_alert(
                    alert_id="draft-test-1",
                    action="approve_urgent",
                    reviewer="Omar",
                    note="",
                    base_dir=base,
                    review_file=base / "data" / "alert_reviews" / "reviews.jsonl",
                )

    def test_needs_source_adapter_blocks_urgent_delivery(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_alert(base)
            review_file = base / "data" / "alert_reviews" / "reviews.jsonl"
            record = review_alert(
                alert_id="draft-test-1",
                action="needs_adapter",
                reviewer="Omar",
                note="Adapter required.",
                base_dir=base,
                review_file=review_file,
            )
            self.assertEqual(record["new_status"], STATUS_NEEDS_SOURCE_ADAPTER)
            self.assertEqual(record["new_send_decision"], DECISION_HOLD)

            with self.assertRaises(ValueError):
                review_alert(
                    alert_id="draft-test-1",
                    action="approve_urgent",
                    reviewer="Omar",
                    note="Urgent anyway.",
                    base_dir=base,
                    review_file=review_file,
                )

    def test_review_record_is_appended_to_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_alert(base)
            review_file = base / "data" / "alert_reviews" / "reviews.jsonl"
            review_alert(
                alert_id="draft-test-1",
                action="approve_weekly",
                reviewer="Omar",
                note="Append record.",
                base_dir=base,
                review_file=review_file,
            )

            records = load_review_records(review_file)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["alert_id"], "draft-test-1")

    def test_alert_draft_json_is_updated_safely(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_alert(base)
            draft_path = base / "data" / "source_snapshots" / "2026-05-30" / "AE" / "AE-vara" / "run-1" / "alert_draft.json"
            review_alert(
                alert_id="draft-test-1",
                action="approve_weekly",
                reviewer="Omar",
                note="Update draft.",
                base_dir=base,
                review_file=base / "data" / "alert_reviews" / "reviews.jsonl",
            )

            updated = json.loads(draft_path.read_text(encoding="utf-8"))
            self.assertEqual(updated["review_status"], STATUS_APPROVED_WEEKLY)
            self.assertEqual(updated["send_decision"], DECISION_WEEKLY)
            self.assertEqual(updated["reviewer"], "Omar")
            self.assertIn("review_history", updated)


if __name__ == "__main__":
    unittest.main()
