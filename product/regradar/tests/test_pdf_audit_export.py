import json
import tempfile
import unittest
from pathlib import Path
import sys

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.audit_export import build_audit_pack_export_response, write_audit_pack, write_audit_pack_pdf
from app.evidence_assessment import LEGAL_DISCLAIMER, create_assessment
from test_mvp_trust_workflow import _write_evidence_run


class PdfAuditExportTests(unittest.TestCase):
    def test_pdf_export_creates_real_pdf_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            run = _write_evidence_run(base)
            assessment = create_assessment(
                evidence_record_id=run["run_id"],
                impact_level="policy_review",
                internal_note="Review policy impact for the MLRO file.",
                reviewer_user_id="user-1",
                reviewer_name="Omar",
                next_action="Attach to compliance review file.",
                base_dir=base,
            )

            out = write_audit_pack_pdf(run, assessment=assessment, base_dir=base)

            pdf_path = base / out["pdf_path"]
            metadata_path = base / out["metadata_path"]
            self.assertTrue(pdf_path.exists())
            self.assertGreater(pdf_path.stat().st_size, 1000)
            self.assertEqual(pdf_path.read_bytes()[:4], b"%PDF")

            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertIn("pdf", metadata["formats"])
            self.assertEqual(metadata["pdf_path"], out["pdf_path"])
            self.assertEqual(metadata["source_name"], "Official Test Source")
            self.assertEqual(metadata["official_url"], "https://regulator.example/source")
            self.assertEqual(metadata["proof_path"], run["proof_block_path"])
            self.assertEqual(metadata["normalized_hash"], run["normalized_hash"])
            self.assertEqual(metadata["assessment_id"], assessment["assessment_id"])
            self.assertEqual(metadata["legal_disclaimer"], LEGAL_DISCLAIMER)

            text = "\n".join(page.extract_text() or "" for page in PdfReader(str(pdf_path)).pages)
            self.assertIn("Official Test Source", text)
            self.assertIn("https://regulator.example/source", text)
            self.assertIn("Review policy impact for the MLRO file.", text)
            self.assertIn(LEGAL_DISCLAIMER, text)
            self.assertNotIn("SAMPLE / DEMO", text)

    def test_demo_pdf_export_is_labeled_sample_demo(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            run = _write_evidence_run(base, run_id="demo-run")

            out = write_audit_pack_pdf(run, base_dir=base, demo=True)

            pdf_path = base / out["pdf_path"]
            text = "\n".join(page.extract_text() or "" for page in PdfReader(str(pdf_path)).pages)
            self.assertIn("SAMPLE / DEMO", text)
            self.assertIn(LEGAL_DISCLAIMER, text)

    def test_markdown_html_export_still_omits_pdf_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            run = _write_evidence_run(base)

            out = write_audit_pack(run, base_dir=base)

            self.assertTrue((base / out["md_path"]).exists())
            self.assertTrue((base / out["html_path"]).exists())
            self.assertNotIn("pdf_path", out)
            metadata = json.loads((base / out["metadata_path"]).read_text(encoding="utf-8"))
            self.assertEqual(metadata["formats"], ["md", "html"])

    def test_pdf_export_response_reports_pdf_status_and_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            run = _write_evidence_run(base)
            assessment = create_assessment(
                evidence_record_id=run["run_id"],
                impact_level="monitor",
                internal_note="Monitor this update in the next MLRO review.",
                reviewer_user_id="user-1",
                reviewer_name="Omar",
                base_dir=base,
            )

            response = build_audit_pack_export_response(
                run,
                assessment=assessment,
                export_format="pdf",
                base_dir=base,
            )

            self.assertTrue(response["ok"])
            self.assertEqual(response["format"], "pdf")
            self.assertTrue(response["pdf_available"])
            self.assertEqual(response["evidence_record_id"], run["run_id"])
            self.assertEqual(response["assessment_id"], assessment["assessment_id"])
            self.assertIn("pdf_path", response["export"])
            self.assertTrue((base / response["export"]["pdf_path"]).exists())
            self.assertEqual(response["disclaimer"], LEGAL_DISCLAIMER)

    def test_markdown_html_response_remains_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            run = _write_evidence_run(base)

            response = build_audit_pack_export_response(run, export_format="md_html", base_dir=base)

            self.assertTrue(response["ok"])
            self.assertEqual(response["format"], "md_html")
            self.assertFalse(response["pdf_available"])
            self.assertIn("md_path", response["export"])
            self.assertIn("html_path", response["export"])
            self.assertNotIn("pdf_path", response["export"])


if __name__ == "__main__":
    unittest.main()
