"""F3 — Arabic lane.

Term choices are grounded in measured trail frequencies
(docs/signal/SIGNAL_QUALITY.md §B): ترخيص 35, عقوبة/جزاء 85, تعميم 58,
الأصول الافتراضية 339, غسل الأموال 54, درهم 233, التزام/يجب 369,
قانون اتحادي 242, مرسوم بقانون 149, قرار 257, لائحة 81.
Arabic deadline vocabulary measured ~absent (0 delta hits) → NO Arabic
deadline detector is claimed; unmatched Arabic routes to the explicit
human-review path (MEDIUM_ARABIC) instead of fake confidence.
"""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.arabic_text import normalize_arabic, normalize_arabic_digits
from app.risk import analyze_risk
from app.detected_facts import extract_detected_facts


def _diff(added: list[str]) -> dict:
    return {"has_changes": True, "added": added, "removed": [], "modified_count": 0}


class NormalizationTests(unittest.TestCase):
    def test_diacritics_stripped(self):
        self.assertEqual(normalize_arabic("قُيِّمَتْ"), normalize_arabic("قيمت"))

    def test_arabic_indic_digits_unified(self):
        self.assertEqual(normalize_arabic_digits("٥٠٠٬٠٠٠ درهم"), "500,000 درهم")
        self.assertEqual(normalize_arabic_digits("۱۲۳"), "123")  # Eastern (Persian) forms

    def test_kashida_and_directional_marks_removed(self):
        decorated = "التـــرخيص‏‎"
        self.assertEqual(normalize_arabic(decorated), normalize_arabic("الترخيص"))


class ArabicScoringTests(unittest.TestCase):
    def test_parity_licence_penalty_sentence(self):
        en = _diff(["A penalty of AED 500,000 applies for operating without a licence. Compliance is mandatory."])
        ar = _diff(["تفرض عقوبة قدرها ٥٠٠٬٠٠٠ درهم على ممارسة النشاط دون ترخيص. الالتزام إلزامي ويجب على المنشآت التقيد."])
        r_en, r_ar = analyze_risk(en), analyze_risk(ar)
        self.assertEqual(r_en["risk_level"], "HIGH")
        self.assertEqual(
            r_ar["risk_level"], "HIGH",
            f"AR equivalent must score like EN, got {r_ar}",
        )
        self.assertTrue(r_ar.get("matched_keywords"), "AR matches must be named")

    def test_arabic_single_strong_is_medium(self):
        ar = _diff(["صدر تعميم جديد بشأن إجراءات التسجيل"])  # circular, no obligation context
        r = analyze_risk(ar)
        self.assertEqual(r["risk_level"], "MEDIUM")
        self.assertTrue(r.get("rule"), "rule id must be present on Arabic path")
        self.assertTrue(r.get("matched_keywords"))

    def test_unmatched_arabic_routes_to_human_review(self):
        ar = _diff(["الصفحة الرئيسية البحث في الموقع الكلمات الأكثر بحثاً"])
        r = analyze_risk(ar)
        self.assertEqual(r["risk_level"], "MEDIUM")
        self.assertEqual(r.get("rule"), "MEDIUM_ARABIC")
        self.assertEqual(r.get("matched_keywords"), [])
        self.assertIn("human review", r["reason"].lower())

    def test_mixed_language_keeps_english_matches(self):
        mixed = _diff(["تحديث الصفحة — New enforcement action and penalty for licensed firms announced."])
        r = analyze_risk(mixed)
        self.assertEqual(r["risk_level"], "HIGH")
        self.assertTrue(any(k in ("penalty", "enforcement action") for k in r.get("matched_keywords", [])))


class ArabicNoiseGuardTests(unittest.TestCase):
    def test_vara_letterhead_is_not_high(self):
        # "سلطة تنظيم الأصول الافتراضية" is VARA's own name — it appears in
        # page chrome on every VARA page (339 delta hits, mostly noise).
        # The regulator's letterhead must never drive HIGH by itself.
        letterhead = _diff([
            "سُلطة تنظيم الأصول الافتراضية - صندوق بريد 9292 دبي، الإمارات العربية المتحدة"
        ])
        r = analyze_risk(letterhead)
        self.assertNotEqual(r["risk_level"], "HIGH", r)

    def test_uaefiu_mission_tagline_is_not_high(self):
        tagline = _diff([
            "نساعد على حماية الاقتصاد الإماراتي والعالمي من غسل الأموال وتمويل الإرهاب ومختلف الجرائم المالية."
        ])
        r = analyze_risk(tagline)
        self.assertNotEqual(r["risk_level"], "HIGH", r)


class ArabicFactsTests(unittest.TestCase):
    def test_arabic_indic_amount_detected(self):
        facts = extract_detected_facts(["غرامة قدرها ٥٠٠٬٠٠٠ درهم"])
        amounts = [f["value"] for f in facts if f["kind"] == "amount"]
        self.assertTrue(any("500,000 درهم" in a for a in amounts), amounts)

    def test_arabic_law_ref_with_arabic_indic_digits(self):
        facts = extract_detected_facts(["مرسوم بقانون اتحادي رقم (٢٠) لسنة ٢٠١٨"])
        refs = [f for f in facts if f["kind"] == "law_reference"]
        self.assertTrue(refs)


if __name__ == "__main__":
    unittest.main()
