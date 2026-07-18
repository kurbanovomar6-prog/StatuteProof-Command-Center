import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.text_normalization import normalize_for_change_hash, stable_normalized_hash


class TextNormalizationTests(unittest.TestCase):
    def test_whitespace_differences_hash_the_same(self):
        a = "Financial institutions should maintain controls."
        b = "  Financial   institutions\n\nshould maintain\tcontrols.  "

        self.assertEqual(stable_normalized_hash(a), stable_normalized_hash(b))

    def test_repeated_footer_and_nav_do_not_change_hash(self):
        base = "Circular 12 of 2026\nPayment firms must retain AML records."
        noisy = "\n".join([
            "Menu",
            "Home",
            base,
            "Privacy Policy",
            "Privacy Policy",
            "Back to top",
            "Back to top",
        ])

        self.assertEqual(normalize_for_change_hash(noisy), base)
        self.assertEqual(stable_normalized_hash(noisy), stable_normalized_hash(base))

    def test_meaningful_obligation_change_changes_hash(self):
        should_text = "Payment firms should maintain controls."
        must_text = "Payment firms must maintain controls."

        self.assertNotEqual(stable_normalized_hash(should_text), stable_normalized_hash(must_text))

    def test_short_percent_change_is_detected_not_collapsed(self):
        # A short "5%" -> "8%" line must survive normalization so the change is
        # caught. The <=3-char boilerplate filter used to erase it, collapsing a
        # real regulatory change to the same hash (a missed change / false negative).
        a = "Capital ratio\n5%\nApplies to licensed banks."
        b = "Capital ratio\n8%\nApplies to licensed banks."
        self.assertNotEqual(stable_normalized_hash(a), stable_normalized_hash(b))
        self.assertIn("5%", normalize_for_change_hash(a))

    def test_render_stamp_stripped_but_publication_date_kept(self):
        # A render-run stamp ("Current date: ...") must be stripped so a daily
        # reload does not fabricate CHANGED; a real "Published <date>" line must be
        # KEPT so a genuine publication-date change IS detected.
        d1 = "Current date: 16 July 2026\nCircular 3\nBanks must file by year end."
        d2 = "Current date: 17 July 2026\nCircular 3\nBanks must file by year end."
        self.assertEqual(stable_normalized_hash(d1), stable_normalized_hash(d2))
        pub1 = "Published 1 March 2026\nBanks must file quarterly."
        pub2 = "Published 1 April 2026\nBanks must file quarterly."
        self.assertNotEqual(stable_normalized_hash(pub1), stable_normalized_hash(pub2))

    def test_duplicate_lines_do_not_change_hash(self):
        once = "Rulebook update\nLicensed firms must file reports."
        duplicated = "Rulebook update\nLicensed firms must file reports.\nLicensed firms must file reports."

        self.assertEqual(normalize_for_change_hash(duplicated), once)
        self.assertEqual(stable_normalized_hash(duplicated), stable_normalized_hash(once))

    def test_empty_and_thin_text_are_safe(self):
        self.assertEqual(normalize_for_change_hash(""), "")
        self.assertEqual(stable_normalized_hash(""), "")
        self.assertEqual(normalize_for_change_hash("Menu\nHome\nSearch"), "")

    def test_volatile_visitor_count_is_removed(self):
        a = "Regulatory notice\nعدد الزوار: 240711271\nOfficial text remains."
        b = "Regulatory notice\nعدد الزوار: 240712342\nOfficial text remains."

        self.assertEqual(stable_normalized_hash(a), stable_normalized_hash(b))

    def test_rotating_social_feed_is_removed(self):
        a = "Latest legislation\nحساب حكومة الإمارات 1 uaegov rotating text Powered by Curator.io"
        b = "Latest legislation\nحساب حكومة الإمارات 9 uaegov different rotating text Powered by Curator.io"

        self.assertEqual(normalize_for_change_hash(a), "Latest legislation")
        self.assertEqual(stable_normalized_hash(a), stable_normalized_hash(b))


if __name__ == "__main__":
    unittest.main()


class NavStripEdgeGatingTests(unittest.TestCase):
    """F1: the nav-label stripper must NOT eat interior short-line regulatory
    lists (predicate offences, sanctioned entities, defined terms) — that made a
    real add/remove invisible to the change hash (a missed change). It must still
    strip leading/trailing menu chrome."""

    def test_interior_offence_list_is_kept_and_change_is_detected(self):
        base = (
            "The following are predicate offences under the AML framework.\n"
            "Money Laundering\nTerrorist Financing\nProliferation Financing\n"
            "Sanctions Evasion\n"
            "These offences apply to all licensed persons in the DIFC."
        )
        added = base.replace(
            "Sanctions Evasion\n", "Sanctions Evasion\nHuman Trafficking\n")
        # The 5-item vs 6-item list must produce DIFFERENT hashes (change caught).
        self.assertNotEqual(stable_normalized_hash(base), stable_normalized_hash(added))
        self.assertIn("Money Laundering", normalize_for_change_hash(base))
        self.assertIn("Human Trafficking", normalize_for_change_hash(added))

    def test_leading_menu_run_is_still_stripped(self):
        page = (
            "Home\nAbout\nServices\nContact\nLogin\n"
            "Circular 5 of 2026 requires licensed firms to file quarterly reports."
        )
        norm = normalize_for_change_hash(page)
        self.assertIn("Circular 5 of 2026", norm)
        self.assertNotIn("Services", norm)

    def test_trailing_footer_menu_run_is_still_stripped(self):
        page = (
            "Payment firms must retain AML transaction records for five years.\n"
            "Careers\nInvestors\nNewsroom\nMediaCentre\nSitemap"
        )
        norm = normalize_for_change_hash(page)
        self.assertIn("Payment firms", norm)
        self.assertNotIn("Newsroom", norm)

    def test_pure_nav_page_normalizes_empty(self):
        from app.text_normalization import _strip_nav_label_runs
        nav = ["Home", "About", "Services", "Contact", "Login", "Careers"]
        self.assertEqual(_strip_nav_label_runs(nav), [])

    def test_short_leading_run_is_kept(self):
        from app.text_normalization import _strip_nav_label_runs
        # 2 short label-like lines (< _NAV_RUN_MIN) are not a menu — keep them.
        lines = ["Alpha", "Beta", "A full sentence of regulatory content here."]
        self.assertEqual(_strip_nav_label_runs(lines), lines)


class BotWallDetectionTests(unittest.TestCase):
    """A JS/anti-bot challenge page must never become a monitoring baseline.

    Source-health audit 2026-07-18: difc.com intermittently served a DDoS-Guard
    wall in RUSSIAN ('Мы проверяем ваш браузер') that the customer path
    (run_pipeline) did NOT catch — looks_like_error_page + is_mostly_unreadable
    both returned False, so 87 chars of wall text were hashable content. The
    existing error-page markers only knew 'cloudflare ray id', not the bare
    'checking your browser' / Russian variant / 'Website owner? click here to
    fix' DDoS-Guard phrasing.
    """

    def test_difc_russian_ddos_guard_wall_is_detected(self):
        from app.text_normalization import looks_like_bot_wall
        # The exact text extracted from difc.com on prod (2026-07-18).
        wall = "Мы проверяем ваш браузер\nWebsite owner? Click here to fix\nEnable JavaScript to continue"
        self.assertTrue(looks_like_bot_wall(wall))

    def test_english_cloudflare_wall_is_detected(self):
        from app.text_normalization import looks_like_bot_wall
        self.assertTrue(looks_like_bot_wall(
            "Checking your browser before accessing the site. This process is automatic."
        ))

    def test_just_a_moment_and_verify_human_walls_detected(self):
        from app.text_normalization import looks_like_bot_wall
        self.assertTrue(looks_like_bot_wall("Just a moment...\nEnable JavaScript and cookies to continue"))
        self.assertTrue(looks_like_bot_wall("Verify you are human by completing the action below."))

    def test_real_document_mentioning_javascript_is_not_a_wall(self):
        from app.text_normalization import looks_like_bot_wall
        # A long, genuine regulatory doc that merely mentions javascript must
        # NOT be misread as a wall — length cap protects real content.
        doc = ("This Regulation sets out obligations for authorised firms. " * 60
               + "Firms should enable JavaScript for the online portal. "
               + "Article 5 requires records to be kept for six years. " * 40)
        self.assertGreater(len(doc), 2000)
        self.assertFalse(looks_like_bot_wall(doc))

    def test_empty_and_normal_short_text_are_not_walls(self):
        from app.text_normalization import looks_like_bot_wall
        self.assertFalse(looks_like_bot_wall(""))
        self.assertFalse(looks_like_bot_wall("DFSA publishes new AML consultation paper CP-2026-3."))
