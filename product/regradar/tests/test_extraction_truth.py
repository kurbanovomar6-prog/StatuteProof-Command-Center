"""F1 — extraction truth.

Every fixture string below is taken verbatim from the real evidence trail
(docs/signal/judgment_table.md classes; snapshots under data/source_snapshots).
The tests prove:
  1. chrome/nav/counter-only changes produce NO hash change and NO diff
  2. genuine regulatory content changes still produce a diff
  3. error pages (404 / 502 / challenge) are detected and never hashed
     as baselines
"""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.diff import get_diff
from app.text_normalization import (
    NORMALIZATION_VERSION,
    looks_like_error_page,
    normalize_for_change_hash,
    stable_normalized_hash,
)

# Real DFSA nav labels (2026-07-05 snapshots, run 17d38737 / 4bc2127d).
_DFSA_NAV = "\n".join(
    [
        "About us",
        "Go Back",
        "Who we are",
        "The DFSA",
        "Governance",
        "How we regulate",
        "International Assessment",
        "Corporate Social Responsibility",
        "Our structure",
        "Board of Directors",
        "Executive Team",
        "Financial Markets Tribunal",
        "DFSA Journey",
        "What we do",
    ]
)

_REGULATORY_BODY = (
    "Circular No. 5 of 2026 concerning anti-money laundering controls.\n"
    "Licensed firms must file the annual AML return no later than 30 September 2026.\n"
    "Federal Decree-Law No. (20) of 2018 applies to all designated businesses.\n"
    "Effective from 19 May 2025 the penalty is AED 500,000."
)


class ChromeStrippingTests(unittest.TestCase):
    def test_dfsa_title_tagline_flip_same_hash(self):
        # The exact 2026-07-05 false-HIGH pair: <title> suffix toggles.
        a = (
            "Financial Crime Prevention Notices and MLRO Letters | DFSA\n"
            + _DFSA_NAV + "\n" + _REGULATORY_BODY
        )
        b = (
            "Financial Crime Prevention Notices and MLRO Letters | DFSA | "
            "THE INDEPENDENT REGULATOR OF FINANCIAL SERVICES\n"
            + _DFSA_NAV + "\n" + _REGULATORY_BODY
        )
        self.assertEqual(stable_normalized_hash(a), stable_normalized_hash(b))
        self.assertFalse(
            get_diff(normalize_for_change_hash(a), normalize_for_change_hash(b))["has_changes"]
        )

    def test_nav_menu_run_is_stripped_and_content_survives(self):
        text = _DFSA_NAV + "\n" + _REGULATORY_BODY
        normalized = normalize_for_change_hash(text)
        self.assertNotIn("Go Back", normalized)
        self.assertNotIn("Board of Directors", normalized)
        self.assertIn("Circular No. 5 of 2026", normalized)
        self.assertIn("no later than 30 September 2026", normalized)
        self.assertIn("AED 500,000", normalized)

    def test_nav_reorder_only_no_diff(self):
        reordered_nav = "\n".join(reversed(_DFSA_NAV.split("\n")))
        a = _DFSA_NAV + "\n" + _REGULATORY_BODY
        b = reordered_nav + "\n" + _REGULATORY_BODY
        self.assertEqual(stable_normalized_hash(a), stable_normalized_hash(b))

    def test_rating_counter_lines_removed_en(self):
        # CBUAE 2026-06-12 false-HIGH pair: only the rating counter moved.
        a = "Rate this page Rated by 1008 People Thanks for rating\n" + _REGULATORY_BODY
        b = "Rate this page Rated by 1009 People Thanks for rating\n" + _REGULATORY_BODY
        self.assertEqual(stable_normalized_hash(a), stable_normalized_hash(b))

    def test_rating_counter_lines_removed_ar(self):
        a = "قيّم هذه الصفحة قُيّمت الصفحة من قبلِ 114175 مستخدماً شكراً على التقيّم\n" + _REGULATORY_BODY
        b = "قيّم هذه الصفحة قُيّمت الصفحة من قبلِ 114178 مستخدماً شكراً على التقيّم\n" + _REGULATORY_BODY
        self.assertEqual(stable_normalized_hash(a), stable_normalized_hash(b))

    def test_theme_widget_lines_removed(self):
        widgets = (
            "Theme color #DAAA00 #00C7B1 #F87C56\n"
            "Color blind mode Default switch checkbox input\n"
            "Night reading mode Default switch checkbox input\n"
        )
        with_widgets = widgets + _REGULATORY_BODY
        self.assertEqual(
            normalize_for_change_hash(with_widgets),
            normalize_for_change_hash(_REGULATORY_BODY),
        )

    def test_carousel_position_removed(self):
        a = "1/6\n" + _REGULATORY_BODY
        b = "2/6\n" + _REGULATORY_BODY
        self.assertEqual(stable_normalized_hash(a), stable_normalized_hash(b))

    def test_genuine_content_change_still_detected(self):
        old = _DFSA_NAV + "\n" + _REGULATORY_BODY
        new_paragraph = (
            "Circular No. 9 of 2026: licensed exchange houses must complete "
            "sanctions screening remediation within 60 days."
        )
        new = _DFSA_NAV + "\n" + _REGULATORY_BODY + "\n\n" + new_paragraph
        self.assertNotEqual(stable_normalized_hash(old), stable_normalized_hash(new))
        d = get_diff(normalize_for_change_hash(old), normalize_for_change_hash(new))
        self.assertTrue(d["has_changes"])
        self.assertTrue(any("Circular No. 9 of 2026" in p for p in d["added"]))

    def test_publication_facts_preserved(self):
        normalized = normalize_for_change_hash(_REGULATORY_BODY)
        for fact in (
            "Circular No. 5 of 2026",
            "30 September 2026",
            "Federal Decree-Law No. (20) of 2018",
            "19 May 2025",
            "AED 500,000",
        ):
            self.assertIn(fact, normalized)

    def test_arabic_site_update_timestamp_removed(self):
        # CBUAE AR homepage (2026-06-12): render-time "last site update"
        # stamps flip daily and must not change the hash.
        a = (
            "الإحصاءات المالية والنقدية أسعار إيبور آخر تحديث للموقع: "
            "الخميس 11 يونيو 2026 12:15:20 م الكل أسعار الصرف\n" + _REGULATORY_BODY
        )
        b = (
            "الإحصاءات المالية والنقدية أسعار إيبور آخر تحديث للموقع: "
            "الجمعة 12 يونيو 2026 12:15:20 م الكل أسعار الصرف\n" + _REGULATORY_BODY
        )
        self.assertEqual(stable_normalized_hash(a), stable_normalized_hash(b))

    def test_normalization_version_exported(self):
        self.assertGreaterEqual(int(NORMALIZATION_VERSION), 2)


class ErrorPageTests(unittest.TestCase):
    def test_cloudflare_502_detected(self):
        # Verbatim from AE-uae-legislation-portal 2026-06-11 snapshot.
        text = (
            "The web server reported a bad gateway error.\n"
            "Please try again in a few minutes.\n"
            "Cloudflare Ray ID: a0a412d2c97f610e • Your IP: 94.20.214.55 • "
            "Performance & security by Cloudflare"
        )
        self.assertTrue(looks_like_error_page(text))

    def test_vara_404_detected(self):
        # Verbatim from AE-dubai-virtual-assets-regulatory-authority-vara 2026-06-11.
        self.assertTrue(
            looks_like_error_page("Sorry 😔, we couldn’t find what you were looking for. Go home .")
        )

    def test_short_page_not_found_detected(self):
        self.assertTrue(looks_like_error_page("404\nPage not found"))

    def test_regulatory_page_not_flagged(self):
        self.assertFalse(looks_like_error_page(_REGULATORY_BODY * 3))

    def test_long_page_mentioning_404_not_flagged(self):
        text = _REGULATORY_BODY * 20 + "\nGuidance on handling HTTP 404 responses in e-services."
        self.assertFalse(looks_like_error_page(text))

    def test_pipeline_returns_error_page_status(self):
        from app.pipeline import run_pipeline
        from unittest import mock

        error_html = "<html><title>502</title><body>The web server reported a bad gateway error. Please try again in a few minutes. Cloudflare Ray ID: abc • Performance & security by Cloudflare</body></html>"
        with mock.patch("app.pipeline.fetch_page", return_value=error_html):
            result = run_pipeline("https://example.gov.ae/laws")
        self.assertEqual(result.get("status"), "error_page")
        self.assertFalse(result.get("changed"))
        self.assertEqual(result.get("extraction_quality"), "failed")
        self.assertIsNone(result.get("normalized_hash"))


if __name__ == "__main__":
    unittest.main()
