"""F4 — scoring depth.

Every case below reproduces a defect proven in the Phase-0 replay
(docs/signal/SIGNAL_QUALITY.md §A):
  - substring matching: 'ban' in 'bank' drove both CBUAE recorded false
    HIGHs on 2026-06-12
  - topic terms ('vasp', 'virtual asset', 'circular') matched VARA
    letterhead / page titles, never an obligation
  - adapter listing-format shifts (22/63 historical CHANGED runs) scored
    HIGH from structural tokens (URL: / Row hash: / Context:)
"""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.risk import analyze_risk


def _diff(added, removed=None):
    return {
        "has_changes": True,
        "added": added,
        "removed": removed or [],
        "modified_count": 0,
    }


class WordBoundaryTests(unittest.TestCase):
    def test_ban_does_not_match_inside_bank(self):
        # Real CBUAE false-HIGH driver: rating-counter delta on a page full
        # of "bank"/"licensed banks".
        # Wholly-new block => scored in full; 'bank'/'banking' everywhere.
        d = _diff(
            ["The Central Bank of the UAE published photographs from the "
             "banking sector forum. Banks and banking institutions attended."]
        )
        r = analyze_risk(d)
        self.assertNotIn("ban", r.get("matched_keywords", []))
        self.assertNotEqual(r["risk_level"], "HIGH", r)

    def test_real_ban_still_matches(self):
        r = analyze_risk(_diff(["The authority announced a ban on unlicensed "
                                "deposit-taking with immediate enforcement."]))
        self.assertIn("ban", r.get("matched_keywords", []))
        self.assertEqual(r["risk_level"], "HIGH")

    def test_licensing_variants_still_match(self):
        r = analyze_risk(_diff(["New licensing requirements: a licence "
                                "condition and license fees apply. Compliance is mandatory."]))
        self.assertEqual(r["risk_level"], "HIGH")

    def test_cease_does_not_match_inside_unrelated_words(self):
        r = analyze_risk(_diff(["Deceased estates guidance photographs published."]))
        self.assertNotIn("cease", r.get("matched_keywords", []))


class TopicTermTests(unittest.TestCase):
    def test_vara_letterhead_terms_not_high(self):
        # VARA marketing/letterhead (2026-05-30 false HIGH matched
        # vasp + virtual asset).
        d = _diff(
            ["As the world's first independent regulator for virtual assets, "
             "VARA serves as a transparent and trusted guiding authority for "
             "the emerging world of virtual assets and VASPs."]
        )
        r = analyze_risk(d)
        self.assertNotEqual(r["risk_level"], "HIGH", r)

    def test_circulars_page_title_not_high(self):
        r = analyze_risk(_diff(["Registration Authority Circulars", "Overview"]))
        self.assertNotEqual(r["risk_level"], "HIGH", r)


class FormatShiftGuardTests(unittest.TestCase):
    def test_structural_listing_delta_capped(self):
        # Real DFSA adapter-format shift shape (2026-06-19): structural
        # tokens dominate the delta.
        added = [
            "DFSA notice/enforcement listing items\n"
            "- Title: AML, CTF & Sanctions Compliance\n"
            "Category: listing_item\n"
            "URL: https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/summary\n"
            "Context: Summary Regulatory Framework Supervisory Methodology\n"
            "Row hash: 6ee69a590c7f5100\n"
            "- Title: About Enforcement\n"
            "URL: https://www.dfsa.ae/what-we-do/enforcement/about-enforcement-119\n"
            "Row hash: 454322d2b5acc1ca"
        ]
        removed = [
            "About us Go Back Who we are The DFSA Governance How we regulate "
            "What we do AML, CTF & Sanctions Compliance Summary"
        ]
        r = analyze_risk(_diff(added, removed))
        self.assertNotEqual(r["risk_level"], "HIGH", r)
        self.assertEqual(r.get("rule"), "FORMAT_SHIFT_REVIEW")
        self.assertIn("format", r["reason"].lower())

    def test_genuine_new_listing_item_not_capped(self):
        # A genuinely new obligation sentence inside a small delta must not
        # be swallowed by the guard.
        added = [
            "- Title: Circular No. 9 of 2026 — sanctions screening remediation\n"
            "Licensed exchange houses must complete sanctions screening "
            "remediation within 60 days or face a penalty of AED 500,000. "
            "This enforcement action takes effect immediately for all licence holders."
        ]
        r = analyze_risk(_diff(added))
        self.assertEqual(r["risk_level"], "HIGH", r)


class RuleNamingTests(unittest.TestCase):
    def test_every_verdict_carries_rule_and_matches(self):
        cases = [
            _diff(["A ban and a penalty apply. Enforcement is mandatory."]),
            _diff(["Guidance updated for reporting entities."]),
            _diff(["Board photographs published."]),
            _diff(["صدر تعميم جديد ويجب الالتزام به"]),
        ]
        for d in cases:
            r = analyze_risk(d)
            self.assertTrue(r.get("rule"), f"missing rule id: {r}")
            self.assertIn("matched_keywords", r, f"missing matches: {r}")


if __name__ == "__main__":
    unittest.main()
