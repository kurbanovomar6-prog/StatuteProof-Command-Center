import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.chunk_diff import build_chunk_diff, build_incomplete_diff
from app.proof import build_source_proof, DISCLAIMER


class ChunkDiffAndProofTests(unittest.TestCase):
    def test_identical_normalized_text_has_no_meaningful_change(self):
        text = "Circular update\n\nPayment firms must maintain controls."

        diff = build_chunk_diff(text, text)

        self.assertFalse(diff["meaningful_change_detected"])
        self.assertEqual(diff["diff_quality"], "GOOD")
        self.assertEqual(diff["added_count"], 0)
        self.assertEqual(diff["removed_count"], 0)

    def test_added_paragraph_is_meaningful_change(self):
        before = "Circular update\n\nPayment firms must maintain controls."
        after = before + "\n\nLicensed firms must submit quarterly attestations."

        diff = build_chunk_diff(before, after)

        self.assertTrue(diff["meaningful_change_detected"])
        self.assertEqual(diff["added_count"], 1)
        self.assertIn("quarterly attestations", diff["added_chunks"][0])

    def test_removed_paragraph_is_meaningful_change(self):
        before = "Circular update\n\nPayment firms must maintain controls."
        after = "Circular update"

        diff = build_chunk_diff(before, after)

        self.assertTrue(diff["meaningful_change_detected"])
        self.assertEqual(diff["removed_count"], 1)

    def test_previous_snapshot_missing_is_incomplete(self):
        diff = build_incomplete_diff(
            previous_run_id=None,
            current_run_id="run-2",
            previous_snapshot_normalized_path=None,
            current_snapshot_normalized_path="data/source_snapshots/today/AE/src/run-2/normalized.txt",
            limitation="Previous normalized snapshot unavailable; diff cannot be generated.",
        )

        self.assertFalse(diff["meaningful_change_detected"])
        self.assertEqual(diff["diff_quality"], "INCOMPLETE")
        self.assertIn("Previous normalized snapshot unavailable", diff["limitations"][0])

    def test_proof_block_includes_core_source_evidence(self):
        record = {
            "source_name": "Central Bank of the UAE (CBUAE)",
            "market": "AE",
            "source_id": "AE-cbuae",
            "official_url": "https://www.centralbank.ae/",
            "final_url": "https://www.centralbank.ae/en/",
            "timestamp_utc": "2026-05-30T10:00:00+00:00",
            "fetch_method": "requests",
            "extraction_quality": "GOOD",
            "raw_chars": 2500,
            "normalized_chars": 2100,
            "raw_hash": "raw123",
            "normalized_hash": "norm123",
            "pdf_text_hash": "pdf123",
            "pdf_links_count": 2,
            "pdf_extracted_chars": 900,
            "change_status": "CHANGED",
            "snapshot_raw_path": "data/source_snapshots/2026-05-30/AE/AE-cbuae/run/raw.txt",
            "snapshot_normalized_path": "data/source_snapshots/2026-05-30/AE/AE-cbuae/run/normalized.txt",
            "snapshot_pdf_text_path": "data/source_snapshots/2026-05-30/AE/AE-cbuae/run/pdf_text.txt",
            "diff_json_path": "data/source_snapshots/2026-05-30/AE/AE-cbuae/run/diff.json",
            "diff_md_path": "data/source_snapshots/2026-05-30/AE/AE-cbuae/run/diff.md",
        }

        proof = build_source_proof(record, {"meaningful_change_detected": True, "diff_quality": "GOOD"})

        self.assertEqual(proof["official_url"], record["official_url"])
        self.assertEqual(proof["normalized_hash"], "norm123")
        self.assertEqual(proof["snapshot_normalized_path"], record["snapshot_normalized_path"])
        self.assertEqual(proof["disclaimer"], DISCLAIMER)
        self.assertEqual(proof["proof_quality"], "GOOD")


if __name__ == "__main__":
    unittest.main()
