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
