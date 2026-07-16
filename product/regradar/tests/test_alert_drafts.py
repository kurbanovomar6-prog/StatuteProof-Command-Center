import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.alert_drafts import build_alert_draft, render_alert_markdown, HUMAN_REVIEW_BANNER
from app.proof import DISCLAIMER


def _proof(**overrides):
    base = {
        "official_url": "https://example.gov.ae/",
        "final_url": "https://example.gov.ae/",
        "normalized_hash": "abc123",
        "proof_quality": "GOOD",
        "diff_json_path": "data/source_snapshots/diff.json",
        "snapshot_normalized_path": "data/source_snapshots/normalized.txt",
        "limitations_notes": "",
    }
    base.update(overrides)
    return base


def _run(source_name, source_id="AE-source"):
    return {
        "run_id": "run-1",
        "market": "AE",
        "source_id": source_id,
        "source_name": source_name,
        "official_url": "https://example.gov.ae/",
        "timestamp_utc": "2026-05-30T10:00:00+00:00",
        "change_status": "CHANGED",
    }


class AlertDraftTests(unittest.TestCase):
    def test_vara_custody_licensing_change_stays_draft_hold(self):
        diff = {
            "diff_quality": "GOOD",
            "meaningful_change_detected": True,
            "added_chunks": ["Licensed VASPs must maintain custody controls and authorization records."],
            "removed_chunks": [],
            "changed_chunks": [],
            "diff_summary": "1 added, 0 removed, 0 changed chunks; 2 unchanged.",
        }

        alert = build_alert_draft(_run("Dubai Virtual Assets Regulatory Authority (VARA)", "AE-vara"), diff, _proof())

        self.assertEqual(alert["review_status"], "DRAFT")
        self.assertEqual(alert["send_decision"], "HOLD_FOR_REVIEW")
        self.assertIn(alert["risk_level"], {"MEDIUM", "HIGH"})
        self.assertIn(alert["change_type"], {"LICENSING", "RULEBOOK_UPDATE"})

    def test_cbuae_payment_obligation_change_is_meaningful(self):
        diff = {
            "diff_quality": "GOOD",
            "meaningful_change_detected": True,
            "added_chunks": ["Payment service providers must submit reporting by the effective date."],
            "removed_chunks": [],
            "changed_chunks": [],
            "diff_summary": "1 added, 0 removed, 0 changed chunks; 4 unchanged.",
        }

        alert = build_alert_draft(_run("Central Bank of the UAE", "AE-cbuae"), diff, _proof())

        self.assertEqual(alert["send_decision"], "HOLD_FOR_REVIEW")
        self.assertIn("Payment service providers", alert["affected_entities"])
        self.assertIn(alert["risk_level"], {"MEDIUM", "HIGH"})

    def test_generic_homepage_count_change_is_review_low_confidence(self):
        diff = {
            "diff_quality": "GOOD",
            "meaningful_change_detected": True,
            "added_chunks": [],
            "removed_chunks": [],
            "changed_chunks": [{"before": ["تشريع القطاع المالي 107 تشريع"], "after": ["تشريع القطاع المالي 108 تشريع"]}],
            "added_count": 0,
            "removed_count": 0,
            "changed_count": 1,
            "diff_summary": "0 added, 0 removed, 1 changed chunks; 2 unchanged.",
        }

        alert = build_alert_draft(_run("UAE Legislation Portal", "AE-uae-legislation-portal"), diff, _proof())

        self.assertEqual(alert["risk_level"], "REVIEW")
        self.assertEqual(alert["confidence"], "LOW")
        self.assertEqual(alert["send_decision"], "HOLD_FOR_REVIEW")
        self.assertIn("adapter review", alert["recommended_action"].lower())

    def test_missing_proof_or_diff_forces_review(self):
        diff = {
            "diff_quality": "INCOMPLETE",
            "meaningful_change_detected": False,
            "diff_summary": "Diff artifact unavailable; human review required.",
            "limitations": ["Diff artifact unavailable; human review required."],
        }

        alert = build_alert_draft(_run("Unknown Source"), diff, _proof(proof_quality="INCOMPLETE"))

        self.assertEqual(alert["risk_level"], "REVIEW")
        self.assertEqual(alert["send_decision"], "HOLD_FOR_REVIEW")

    def test_markdown_contains_draft_banner_and_disclaimer(self):
        diff = {
            "diff_quality": "GOOD",
            "meaningful_change_detected": True,
            "added_chunks": ["Guidance update for regulated firms."],
            "removed_chunks": [],
            "changed_chunks": [],
            "diff_summary": "1 added, 0 removed, 0 changed chunks; 1 unchanged.",
        }
        alert = build_alert_draft(_run("DFSA"), diff, _proof())

        markdown = render_alert_markdown(alert)

        self.assertIn(HUMAN_REVIEW_BANNER, markdown)
        self.assertIn(DISCLAIMER, markdown)
        self.assertIn("not legal advice", markdown.lower())


if __name__ == "__main__":
    unittest.main()
