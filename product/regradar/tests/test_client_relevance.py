import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.client_profiles import (
    DELIVERY_REVIEW,
    DELIVERY_SUPPRESS,
    DELIVERY_URGENT,
    DELIVERY_WEEKLY,
    SOURCE_METADATA,
    load_client_profile,
    score_alert_relevance,
    source_metadata_for_alert,
)


def _alert(source_id, source_name, change_type, risk_level="MEDIUM", confidence="MEDIUM", text=""):
    return {
        "alert_id": f"draft-{source_id}",
        "review_status": "DRAFT",
        "send_decision": "HOLD_FOR_REVIEW",
        "market": "AE",
        "source_id": source_id,
        "source_name": source_name,
        "source_url": "https://example.gov.ae/",
        "checked_at_utc": "2026-05-30T10:00:00+00:00",
        "change_status": "CHANGED",
        "change_type": change_type,
        "risk_level": risk_level,
        "confidence": confidence,
        "what_changed": text,
        "added_chunks": [text] if text else [],
        "removed_chunks": [],
        "changed_chunks": [],
        "affected_entities": "",
        "recommended_action": "",
        "limitations": [],
        "proof_block": {"proof_quality": "GOOD"},
    }


def _score(alert, profile_id):
    profile = load_client_profile(profile_id)
    metadata = source_metadata_for_alert(alert)
    return score_alert_relevance(alert, profile, metadata)


class ClientRelevanceTests(unittest.TestCase):
    def test_vara_custody_alert_matches_vasp_not_payments(self):
        alert = _alert(
            SOURCE_METADATA["vara"]["source_id"],
            SOURCE_METADATA["vara"]["source_name"],
            "LICENSING",
            risk_level="HIGH",
            text="Licensed VASPs must maintain custody controls and authorization records.",
        )

        vasp = _score(alert, "uae_vasp_demo")
        payments = _score(alert, "uae_payments_demo")

        self.assertIn(vasp["delivery_decision"], {DELIVERY_URGENT, DELIVERY_WEEKLY})
        self.assertIn("custody", vasp["matched_topics"])
        self.assertIn(payments["delivery_decision"], {DELIVERY_SUPPRESS, DELIVERY_REVIEW})

    def test_cbuae_payment_alert_matches_payments_and_vasp_source_overlap(self):
        alert = _alert(
            SOURCE_METADATA["cbuae"]["source_id"],
            SOURCE_METADATA["cbuae"]["source_name"],
            "DEADLINE_OR_REPORTING",
            risk_level="MEDIUM",
            text="Payment service providers must submit stored value reporting by the effective date.",
        )

        payments = _score(alert, "uae_payments_demo")
        vasp = _score(alert, "uae_vasp_demo")

        self.assertIn(payments["delivery_decision"], {DELIVERY_URGENT, DELIVERY_WEEKLY})
        self.assertIn("payments", payments["matched_topics"])
        self.assertIn(vasp["delivery_decision"], {DELIVERY_WEEKLY, DELIVERY_SUPPRESS})

    def test_uae_fiu_aml_alert_matches_payments_vasp_and_difc(self):
        alert = _alert(
            SOURCE_METADATA["uae_fiu"]["source_id"],
            SOURCE_METADATA["uae_fiu"]["source_name"],
            "AML_CFT",
            risk_level="MEDIUM",
            text="AML/CFT suspicious transaction reporting guidance updated.",
        )

        for profile_id in ("uae_payments_demo", "uae_vasp_demo", "difc_financial_demo"):
            result = _score(alert, profile_id)
            self.assertIn(result["delivery_decision"], {DELIVERY_WEEKLY, DELIVERY_URGENT})
            self.assertIn("aml_cft", result["matched_topics"])

    def test_fta_tax_alert_matches_tax_profile_not_vasp(self):
        alert = _alert(
            SOURCE_METADATA["fta"]["source_id"],
            SOURCE_METADATA["fta"]["source_name"],
            "TAX",
            risk_level="MEDIUM",
            text="Corporate tax and VAT reporting deadline guidance updated.",
        )

        tax = _score(alert, "uae_tax_demo")
        vasp = _score(alert, "uae_vasp_demo")

        self.assertIn(tax["delivery_decision"], {DELIVERY_WEEKLY, DELIVERY_URGENT})
        self.assertIn("tax", tax["matched_topics"])
        self.assertEqual(vasp["delivery_decision"], DELIVERY_SUPPRESS)

    def test_dfsa_alert_matches_difc_not_mainland_payments(self):
        alert = _alert(
            SOURCE_METADATA["dfsa"]["source_id"],
            SOURCE_METADATA["dfsa"]["source_name"],
            "CONSULTATION",
            risk_level="MEDIUM",
            text="DFSA consultation on funds and securities framework.",
        )

        difc = _score(alert, "difc_financial_demo")
        payments = _score(alert, "uae_payments_demo")

        self.assertIn(difc["delivery_decision"], {DELIVERY_WEEKLY, DELIVERY_URGENT})
        self.assertEqual(payments["delivery_decision"], DELIVERY_SUPPRESS)

    def test_unknown_low_confidence_legislation_change_is_never_urgent(self):
        alert = _alert(
            SOURCE_METADATA["uae_legislation"]["source_id"],
            SOURCE_METADATA["uae_legislation"]["source_name"],
            "UNKNOWN",
            risk_level="REVIEW",
            confidence="LOW",
            text="Arabic homepage aggregate count changed.",
        )
        alert["limitations"] = ["UAE Legislation Portal diff appears to be a broad homepage aggregate-count change; adapter review required."]

        for profile_id in ("uae_payments_demo", "uae_vasp_demo", "difc_financial_demo", "adgm_financial_demo", "uae_tax_demo"):
            result = _score(alert, profile_id)
            self.assertIn(result["delivery_decision"], {DELIVERY_REVIEW, DELIVERY_SUPPRESS})
            self.assertNotEqual(result["delivery_decision"], DELIVERY_URGENT)


if __name__ == "__main__":
    unittest.main()
