"""F2 — detected facts in alerts.

Fixtures are real sentences from the historical delta corpus
(docs/signal/replay_severity.jsonl):
  - CBUAE retail-payment rulebook delta: "Effective from 1/8/2022 Status: In-Force"
  - SCA aml-cft delta: "Federal Decree-Law No. (20) of 2018"
  - EOCN delta: "Cabinet Decision No. (141) of 2024 On Rewards for Reporting…"
  - CBUAE exchange-business delta: paid-up capital / license category / Articles 8 and 9

A fact may be stated in an alert ONLY when truly detected in the change;
absence renders nothing.
"""

import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.detected_facts import extract_detected_facts
from app.alert_content import build_alert_content, render_markdown, render_telegram


class ExtractionTests(unittest.TestCase):
    def test_effective_date_and_in_force_from_real_cbuae_delta(self):
        text = (
            "3.1.2. Retail Payment Services and Card Schemes Regulation "
            "Effective from 1/8/2022 Status: In-Force Download In July 2021 "
            "the CBUAE issued the Retail Payment Services Regulation."
        )
        facts = extract_detected_facts([text])
        kinds = {f["kind"] for f in facts}
        self.assertIn("effective_date", kinds)
        eff = next(f for f in facts if f["kind"] == "effective_date")
        self.assertIn("1/8/2022", eff["value"])
        self.assertIn("in_force_status", kinds)

    def test_law_references_from_real_deltas(self):
        text = (
            "Federal Decree-Law No. (20) of 2018 on Anti-Money Laundering. "
            "Cabinet Decision No. (141) of 2024 On Rewards for Reporting "
            "Illicit Trade. Circular No. 5 of 2026 concerning AML controls."
        )
        facts = extract_detected_facts([text])
        refs = [f["value"] for f in facts if f["kind"] == "law_reference"]
        self.assertTrue(any("Decree-Law No. (20) of 2018" in r for r in refs))
        self.assertTrue(any("Cabinet Decision No. (141) of 2024" in r for r in refs))
        self.assertTrue(any("Circular No. 5 of 2026" in r for r in refs))

    def test_deadline_phrases(self):
        text = (
            "Licensed firms must file the annual AML return no later than "
            "30 September 2026. Remediation must be completed within 60 days."
        )
        facts = extract_detected_facts([text])
        deadlines = [f for f in facts if f["kind"] == "deadline"]
        self.assertEqual(len(deadlines), 2)
        values = " | ".join(d["value"] for d in deadlines)
        self.assertIn("30 September 2026", values)
        self.assertIn("within 60 days", values)

    def test_amounts(self):
        text = "The administrative penalty is AED 500,000 and a fee of 2,000 dirhams applies."
        facts = extract_detected_facts([text])
        amounts = [f["value"] for f in facts if f["kind"] == "amount"]
        self.assertTrue(any("AED 500,000" in a for a in amounts))
        self.assertTrue(any("2,000 dirhams" in a for a in amounts))

    def test_licence_and_article_references_from_real_cbuae_delta(self):
        text = (
            "5.1.3 demonstrate that it will satisfy the respective initial "
            "Paid-up Capital and bank guarantee requirements for the license "
            "category applied for, specified in Articles 8 and 9 of this Regulation."
        )
        facts = extract_detected_facts([text])
        kinds = {f["kind"] for f in facts}
        self.assertIn("licence_reference", kinds)
        self.assertIn("article_reference", kinds)

    def test_arabic_law_reference(self):
        text = "صدر قانون اتحادي رقم (20) لسنة 2018 في شأن مواجهة غسل الأموال"
        facts = extract_detected_facts([text])
        refs = [f for f in facts if f["kind"] == "law_reference"]
        self.assertTrue(refs, "Arabic federal-law reference must be detected")

    def test_nav_noise_produces_no_facts(self):
        nav = "About us\nGo Back\nWho we are\nBoard of Directors\nRead More"
        self.assertEqual(extract_detected_facts([nav]), [])

    def test_subsumed_spans_deduplicated(self):
        # "Articles 8 and 9" must not also yield "Articles 8" (real CBUAE
        # exchange-business delta produced both before dedup).
        facts = extract_detected_facts(["specified in Articles 8 and 9 of this Regulation"])
        articles = [f["value"] for f in facts if f["kind"] == "article_reference"]
        self.assertEqual(articles, ["Articles 8 and 9"])

    def test_every_fact_carries_its_matched_span(self):
        text = "Effective from 1/8/2022 the penalty is AED 500,000."
        for fact in extract_detected_facts([text]):
            self.assertTrue(fact.get("span"), f"fact without span: {fact}")
            self.assertIn(fact["span"], text)


class RenderingTests(unittest.TestCase):
    _BASE = {
        "risk_level": "HIGH",
        "risk_details": {
            "rule": "HIGH_MULTIPLE_STRONG",
            "matched_keywords": ["penalty", "licence"],
        },
        "source_name": "CBUAE Rulebook",
        "jurisdiction": "AE",
        "url": "https://rulebook.centralbank.ae/x",
        "checked_at_utc": "2026-07-06T10:00:00+00:00",
        "added": ["Effective from 1/8/2022 the penalty is AED 500,000."],
        "removed": [],
    }

    def test_detected_facts_render_in_both_channels(self):
        payload = dict(self._BASE)
        payload["detected_facts"] = extract_detected_facts(payload["added"])
        content = build_alert_content(payload)
        tg = render_telegram(content)
        md = render_markdown(content)
        for rendered in (tg, md):
            self.assertIn("Detected in this change", rendered)
            self.assertIn("1/8/2022", rendered)
            self.assertIn("AED 500,000", rendered)

    def test_absence_renders_nothing(self):
        payload = dict(self._BASE)
        payload["added"] = ["Board meeting photographs published."]
        payload["detected_facts"] = extract_detected_facts(payload["added"])
        content = build_alert_content(payload)
        tg = render_telegram(content)
        md = render_markdown(content)
        for rendered in (tg, md):
            self.assertNotIn("Detected in this change", rendered)
            self.assertNotIn("Not specified", rendered)

    def test_deadline_line_only_from_detection_not_from_ai_field(self):
        # An AI-supplied deadline with no detected deadline fact must NOT
        # render — a stated deadline requires a real detection (F2 contract).
        payload = dict(self._BASE)
        payload["added"] = ["Board meeting photographs published."]
        payload["deadline"] = "2026-09-30"  # unbacked claim
        payload["detected_facts"] = extract_detected_facts(payload["added"])
        content = build_alert_content(payload)
        self.assertNotIn("deadline", content)
        payload2 = dict(self._BASE)
        payload2["added"] = ["Returns are due no later than 30 September 2026."]
        payload2["detected_facts"] = extract_detected_facts(payload2["added"])
        content2 = build_alert_content(payload2)
        self.assertIn("30 September 2026", content2.get("deadline", ""))


class PipelineWiringTests(unittest.TestCase):
    def test_pipeline_passes_detected_facts_to_alert_payload(self):
        from unittest import mock
        from app.pipeline import init_pipeline, run_pipeline

        old = "\n\n".join(f"Standing obligation paragraph {i}." for i in range(30))
        new = (
            "Firms must complete remediation no later than 30 September 2026. "
            "The penalty is AED 500,000 under Federal Decree-Law No. (20) of 2018.\n\n"
            + old
        )
        sends: list[dict] = []
        init_pipeline(0)
        from app.text_normalization import normalize_for_change_hash, stable_content_hash
        old_hash = stable_content_hash(normalize_for_change_hash(old))
        with mock.patch("app.pipeline.fetch_page", return_value="<html>x</html>"), \
             mock.patch("app.pipeline.extract_best_text", return_value={"text": new, "method": "t"}), \
             mock.patch("app.pipeline.get_latest_document", return_value={"content": old, "content_hash": old_hash}), \
             mock.patch("app.pipeline.save_document", return_value=None), \
             mock.patch("app.pipeline.ENABLE_TELEGRAM_ALERTS", True), \
             mock.patch("app.telegram.send_telegram_alert", side_effect=lambda p: sends.append(p) or True), \
             mock.patch("app.pipeline.get_adapter_for_url", return_value=None):
            result = run_pipeline("https://example.gov.ae/facts")

        self.assertTrue(result["changed"])
        kinds = {f["kind"] for f in result.get("detected_facts", [])}
        self.assertLessEqual({"deadline", "amount", "law_reference"}, kinds)
        self.assertEqual(len(sends), 1)
        payload_kinds = {f["kind"] for f in sends[0].get("detected_facts", [])}
        self.assertIn("deadline", payload_kinds)


if __name__ == "__main__":
    unittest.main()
