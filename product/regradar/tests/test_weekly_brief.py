import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.alert_review import (
    DECISION_DO_NOT_SEND,
    DECISION_HOLD,
    DECISION_URGENT,
    DECISION_WEEKLY,
    STATUS_APPROVED_URGENT,
    STATUS_APPROVED_WEEKLY,
    STATUS_DRAFT,
    STATUS_REJECTED,
)
from app.weekly_brief import (
    build_weekly_brief,
    collect_approved_alerts,
    generate_weekly_brief,
    render_weekly_brief_html,
    render_weekly_brief_markdown,
)


def _profile():
    return {
        "client_id": "uae_vasp_demo",
        "company_name": "UAE VASP Demo",
        "jurisdictions": ["UAE / Dubai", "UAE / federal"],
        "topics_in_scope": ["crypto_vasp", "custody", "licensing", "aml_cft"],
        "sources_in_scope": ["VARA", "UAE FIU", "UAE Legislation Portal"],
        "sources_excluded": ["DFSA"],
        "alert_threshold": "MEDIUM",
    }


def _write_profile(base: Path):
    data = base / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "client_profiles.example.json").write_text(json.dumps({"uae_vasp_demo": _profile()}), encoding="utf-8")


def _write_alert(base: Path, idx: str, status: str, decision: str, source: str = "VARA"):
    folder = base / "data" / "source_snapshots" / "2026-05-30" / "AE" / f"AE-{idx}" / "run-1"
    folder.mkdir(parents=True, exist_ok=True)
    alert = {
        "alert_id": f"draft-{idx}",
        "review_status": status,
        "send_decision": decision,
        "market": "AE",
        "source_id": "AE-dubai-virtual-assets-regulatory-authority-vara",
        "source_name": source,
        "source_url": "https://www.vara.ae/",
        "checked_at_utc": "2026-05-30T10:00:00+00:00",
        "change_type": "LICENSING",
        "risk_level": "MEDIUM",
        "confidence": "MEDIUM",
        "why_it_matters": "The change may affect licensing controls.",
        "recommended_action": "Review licensing controls.",
        "limitations": ["Reviewed source limitation."],
        "proof_block": {
            "official_url": "https://www.vara.ae/",
            "final_url": "https://www.vara.ae/",
            "normalized_hash": "a" * 64,
            "extraction_quality": "GOOD",
            "proof_block_path": f"data/source_snapshots/2026-05-30/AE/AE-{idx}/run-1/proof.json",
            "diff_json_path": f"data/source_snapshots/2026-05-30/AE/AE-{idx}/run-1/diff.json",
        },
        "relevance": {"client_id": "uae_vasp_demo", "delivery_decision": decision, "relevance_score": 80},
    }
    (folder / "alert_draft.json").write_text(json.dumps(alert, indent=2), encoding="utf-8")
    return alert


class WeeklyBriefTests(unittest.TestCase):
    def test_approved_weekly_alert_appears_in_brief(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            alert = _write_alert(base, "weekly", STATUS_APPROVED_WEEKLY, DECISION_WEEKLY)
            rows = collect_approved_alerts(
                client_profile=_profile(),
                market="AE",
                start=datetime(2026, 5, 29, tzinfo=timezone.utc),
                end=datetime(2026, 5, 31, tzinfo=timezone.utc),
                base_dir=base,
            )
            self.assertEqual([item["alert_id"] for item in rows], [alert["alert_id"]])

    def test_approved_urgent_alert_appears_in_brief(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            alert = _write_alert(base, "urgent", STATUS_APPROVED_URGENT, DECISION_URGENT)
            rows = collect_approved_alerts(
                client_profile=_profile(),
                market="AE",
                start=datetime(2026, 5, 29, tzinfo=timezone.utc),
                end=datetime(2026, 5, 31, tzinfo=timezone.utc),
                base_dir=base,
            )
            self.assertEqual(rows[0]["alert_id"], alert["alert_id"])

    def test_rejected_alert_does_not_appear(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_alert(base, "reject", STATUS_REJECTED, DECISION_DO_NOT_SEND)
            rows = collect_approved_alerts(
                client_profile=_profile(),
                market="AE",
                start=datetime(2026, 5, 29, tzinfo=timezone.utc),
                end=datetime(2026, 5, 31, tzinfo=timezone.utc),
                base_dir=base,
            )
            self.assertEqual(rows, [])

    def test_unreviewed_draft_alert_does_not_appear(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_alert(base, "draft", STATUS_DRAFT, DECISION_HOLD)
            rows = collect_approved_alerts(
                client_profile=_profile(),
                market="AE",
                start=datetime(2026, 5, 29, tzinfo=timezone.utc),
                end=datetime(2026, 5, 31, tzinfo=timezone.utc),
                base_dir=base,
            )
            self.assertEqual(rows, [])

    def test_empty_period_generates_no_approved_updates_brief(self):
        brief = build_weekly_brief(
            client_profile=_profile(),
            market="AE",
            start=datetime(2026, 5, 29, tzinfo=timezone.utc),
            end=datetime(2026, 5, 31, tzinfo=timezone.utc),
            alerts=[],
        )
        markdown = render_weekly_brief_markdown(brief)
        self.assertIn("No reviewed updates were approved for this brief period.", markdown)
        self.assertNotIn("no changes occurred", markdown.lower())

    def test_disclaimer_and_client_proof_summary_appear(self):
        alert = _write_alert(Path(tempfile.mkdtemp()), "proof", STATUS_APPROVED_WEEKLY, DECISION_WEEKLY)
        brief = build_weekly_brief(
            client_profile=_profile(),
            market="AE",
            start=datetime(2026, 5, 29, tzinfo=timezone.utc),
            end=datetime(2026, 5, 31, tzinfo=timezone.utc),
            alerts=[alert],
        )
        markdown = render_weekly_brief_markdown(brief)
        self.assertIn("provided for information and compliance review support only", markdown)
        self.assertIn("do not constitute legal advice", markdown)
        self.assertIn("does not guarantee compliance", markdown)
        self.assertIn("Official source: https://www.vara.ae/", markdown)
        self.assertIn("Content fingerprint: aaaaaaaaaaaaaaaa...", markdown)
        self.assertIn("Snapshot/diff: Archived internally and available on request.", markdown)
        self.assertNotIn("a" * 64, markdown)
        self.assertNotIn("/tmp/", markdown)

    def test_generate_demo_fixture_brief(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_profile(base)
            result = generate_weekly_brief(
                client_id="uae_vasp_demo",
                market="AE",
                days=7,
                demo_fixture=True,
                base_dir=base,
            )
            self.assertTrue(result["demo_fixture"])
            md_path = base / result["paths"]["md"]
            self.assertIn("SAMPLE / DEMO - NOT CUSTOMER DATA", md_path.read_text(encoding="utf-8"))

    def test_internal_statuses_do_not_appear_in_rendered_markdown(self):
        alert = _write_alert(Path(tempfile.mkdtemp()), "internal", STATUS_APPROVED_WEEKLY, DECISION_WEEKLY)
        alert["risk_level"] = "REVIEW"
        alert["change_type"] = "UNKNOWN"
        brief = build_weekly_brief(
            client_profile=_profile(),
            market="AE",
            start=datetime(2026, 5, 29, tzinfo=timezone.utc),
            end=datetime(2026, 5, 31, tzinfo=timezone.utc),
            alerts=[alert],
        )
        markdown = render_weekly_brief_markdown(brief)

        self.assertNotIn("Change type: UNKNOWN", markdown)
        self.assertNotIn("Risk level: REVIEW", markdown)
        self.assertNotIn("APPROVED_FOR_WEEKLY", markdown)
        self.assertNotIn("WEEKLY_BRIEF_ONLY", markdown)
        self.assertIn("Included for transparency", markdown)

    def test_internal_why_and_action_copy_are_guarded(self):
        alert = _write_alert(Path(tempfile.mkdtemp()), "guard", STATUS_APPROVED_WEEKLY, DECISION_WEEKLY)
        alert["why_it_matters"] = "The diff is not reliable enough for customer dispatch."
        alert["recommended_action"] = "Source-specific adapter review required before customer dispatch."
        brief = build_weekly_brief(
            client_profile=_profile(),
            market="AE",
            start=datetime(2026, 5, 29, tzinfo=timezone.utc),
            end=datetime(2026, 5, 31, tzinfo=timezone.utc),
            alerts=[alert],
        )
        markdown = render_weekly_brief_markdown(brief)

        self.assertIn("The nature of this change could not be determined", markdown)
        self.assertIn("Monitor the official source for related publications", markdown)
        self.assertNotIn("customer dispatch", markdown)
        self.assertNotIn("source-specific adapter", markdown.lower())
        self.assertNotIn("adapter review required", markdown.lower())

    def test_html_does_not_leak_bold_markers(self):
        alert = _write_alert(Path(tempfile.mkdtemp()), "html", STATUS_APPROVED_WEEKLY, DECISION_WEEKLY)
        brief = build_weekly_brief(
            client_profile=_profile(),
            market="AE",
            start=datetime(2026, 5, 29, tzinfo=timezone.utc),
            end=datetime(2026, 5, 31, tzinfo=timezone.utc),
            alerts=[alert],
        )

        html = render_weekly_brief_html(brief)

        self.assertNotIn("**Why it matters**", html)
        self.assertNotIn("**", html)
        self.assertIn("<h4>Why it matters</h4>", html)

    def test_no_action_suppressed_note_removed(self):
        alert = _write_alert(Path(tempfile.mkdtemp()), "notes", STATUS_APPROVED_WEEKLY, DECISION_WEEKLY)
        brief = build_weekly_brief(
            client_profile=_profile(),
            market="AE",
            start=datetime(2026, 5, 29, tzinfo=timezone.utc),
            end=datetime(2026, 5, 31, tzinfo=timezone.utc),
            alerts=[alert],
        )
        markdown = render_weekly_brief_markdown(brief)

        self.assertNotIn("No-Action / Suppressed Note", markdown)
        self.assertIn("Monitoring Notes", markdown)
        self.assertIn("only human-reviewed items approved for this client profile", markdown)

    def test_executive_summary_boilerplate_removed_and_profile_framing_present(self):
        alert = _write_alert(Path(tempfile.mkdtemp()), "summary", STATUS_APPROVED_WEEKLY, DECISION_WEEKLY)
        brief = build_weekly_brief(
            client_profile=_profile(),
            market="AE",
            start=datetime(2026, 5, 29, tzinfo=timezone.utc),
            end=datetime(2026, 5, 31, tzinfo=timezone.utc),
            alerts=[alert],
        )
        markdown = render_weekly_brief_markdown(brief)

        self.assertNotIn("This brief covers reviewed regulatory monitoring for the selected client profile.", markdown)
        self.assertIn("This brief is configured for UAE VASP Demo", markdown)
        self.assertIn("1 reviewed update approved for this period is included.", markdown)

    def test_sources_monitored_no_change_line_uses_available_count_or_generic(self):
        alert = _write_alert(Path(tempfile.mkdtemp()), "sources", STATUS_APPROVED_WEEKLY, DECISION_WEEKLY)
        brief = build_weekly_brief(
            client_profile=_profile(),
            market="AE",
            start=datetime(2026, 5, 29, tzinfo=timezone.utc),
            end=datetime(2026, 5, 31, tzinfo=timezone.utc),
            alerts=[alert],
        )
        markdown = render_weekly_brief_markdown(brief)
        self.assertIn("- 67 additional monitored sources showed no detected change based on monitoring this period.", markdown)

        brief["summary"]["sources_checked"] = 4
        counted = render_weekly_brief_markdown(brief)
        self.assertIn("- 3 additional monitored sources showed no detected change based on monitoring this period.", counted)

    def test_duplicate_extraction_quality_is_not_repeated_in_limitations(self):
        alert = _write_alert(Path(tempfile.mkdtemp()), "quality", STATUS_APPROVED_WEEKLY, DECISION_WEEKLY)
        alert["limitations"] = ["Extracted 10,000 chars — sufficient for reliable generic monitoring."]
        brief = build_weekly_brief(
            client_profile=_profile(),
            market="AE",
            start=datetime(2026, 5, 29, tzinfo=timezone.utc),
            end=datetime(2026, 5, 31, tzinfo=timezone.utc),
            alerts=[alert],
        )
        markdown = render_weekly_brief_markdown(brief)

        self.assertEqual(markdown.count("Extraction quality: Good based on extracted content volume."), 1)

    def test_html_contains_inline_style_and_separated_disclaimer(self):
        alert = _write_alert(Path(tempfile.mkdtemp()), "style", STATUS_APPROVED_WEEKLY, DECISION_WEEKLY)
        brief = build_weekly_brief(
            client_profile=_profile(),
            market="AE",
            start=datetime(2026, 5, 29, tzinfo=timezone.utc),
            end=datetime(2026, 5, 31, tzinfo=timezone.utc),
            alerts=[alert],
        )
        html = render_weekly_brief_html(brief)

        self.assertIn("<style>", html)
        self.assertIn("max-width: 680px", html)
        self.assertIn("#16D9F5", html)
        self.assertIn('class="disclaimer"', html)

    def test_html_links_urls_in_list_items(self):
        alert = _write_alert(Path(tempfile.mkdtemp()), "links", STATUS_APPROVED_WEEKLY, DECISION_WEEKLY)
        brief = build_weekly_brief(
            client_profile=_profile(),
            market="AE",
            start=datetime(2026, 5, 29, tzinfo=timezone.utc),
            end=datetime(2026, 5, 31, tzinfo=timezone.utc),
            alerts=[alert],
        )
        html = render_weekly_brief_html(brief)

        self.assertIn(
            '<li>Official source: <a href="https://www.vara.ae/">https://www.vara.ae/</a></li>',
            html,
        )


if __name__ == "__main__":
    unittest.main()
