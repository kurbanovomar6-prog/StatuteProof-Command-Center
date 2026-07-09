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


class SelfPairingGuardTests(unittest.TestCase):
    """A single strong keyword must not self-amplify to HIGH by acting as
    its own context amplifier.

    Defect (fix-self-pairing): `license`, `licence`, `sanction(s)`,
    `fine(s)`, `penalty(ies)` appeared in BOTH _HIGH_KEYWORDS and
    _HIGH_CONTEXT_WORDS. A single occurrence of one such token matched both
    lists independently, so HIGH path 2 (1 strong + context) fired from ONE
    word pairing with itself. Verified live on main:
      "A penalty applies."                 -> HIGH (matched=['penalty'], context=['penalty'])
      "It was a fine morning ... picnic."  -> HIGH (matched=['fine'],    context=['fine'])
    A genuine context amplifier must be a DISTINCT term (deadline,
    compliance, reporting, obligation, mandatory, enforcement).
    """

    def test_single_penalty_alone_is_medium_not_high(self):
        r = analyze_risk(_diff(["A penalty applies."]))
        self.assertEqual(r["risk_level"], "MEDIUM", r)
        self.assertEqual(r.get("rule"), "MEDIUM_SINGLE_STRONG", r)
        self.assertEqual(r.get("matched_keywords"), ["penalty"], r)
        self.assertEqual(r.get("matched_context"), [], r)

    def test_single_fine_non_regulatory_not_high(self):
        r = analyze_risk(
            _diff(["It was a fine morning for the staff picnic."])
        )
        self.assertNotEqual(r["risk_level"], "HIGH", r)

    def test_single_license_alone_not_high(self):
        r = analyze_risk(_diff(["A single license issued."]))
        self.assertNotEqual(r["risk_level"], "HIGH", r)

    def test_single_sanction_alone_not_high(self):
        r = analyze_risk(_diff(["One sanction referenced in the notice."]))
        self.assertNotEqual(r["risk_level"], "HIGH", r)

    def test_enforcement_action_alone_not_high(self):
        # Residual SUBSTRING self-pair: "enforcement" (context) is a
        # word-bounded substring of the strong keyword "enforcement action".
        # A single "enforcement action" phrase, standing alone, must NOT
        # self-pair to HIGH — it is one strong keyword with no distinct
        # context signal.
        r = analyze_risk(_diff(["enforcement action"]))
        self.assertEqual(r["risk_level"], "MEDIUM", r)
        self.assertEqual(r.get("rule"), "MEDIUM_SINGLE_STRONG", r)
        self.assertEqual(r.get("matched_keywords"), ["enforcement action"], r)
        self.assertEqual(r.get("matched_context"), [], r)

    def test_enforcement_action_plus_distinct_context_still_high(self):
        # "enforcement action" (strong) + a genuinely distinct context word
        # (deadline) must still confirm HIGH.
        r = analyze_risk(
            _diff(["An enforcement action follows. The reporting deadline is fixed."])
        )
        self.assertEqual(r["risk_level"], "HIGH", r)
        self.assertEqual(r.get("rule"), "HIGH_STRONG_PLUS_CONTEXT", r)
        self.assertIn("deadline", r.get("matched_context", []), r)
        # The substring self-pair token must NOT survive in context.
        self.assertNotIn("enforcement", r.get("matched_context", []), r)

    def test_genuine_multi_strong_still_high(self):
        # Three distinct strong keywords — path 1 (>=2 strong) still fires.
        r = analyze_risk(
            _diff(["A ban and a penalty apply, with revocation of the licence."])
        )
        self.assertEqual(r["risk_level"], "HIGH", r)

    def test_strong_plus_distinct_context_still_high(self):
        # One strong keyword + a genuine DISTINCT context word (deadline).
        r = analyze_risk(
            _diff(["A penalty applies. The reporting deadline is fixed."])
        )
        self.assertEqual(r["risk_level"], "HIGH", r)
        self.assertEqual(r.get("rule"), "HIGH_STRONG_PLUS_CONTEXT", r)
        self.assertIn("deadline", r.get("matched_context", []), r)
        # The self-pairing token must NOT appear in the context list.
        self.assertNotIn("penalty", r.get("matched_context", []), r)


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
