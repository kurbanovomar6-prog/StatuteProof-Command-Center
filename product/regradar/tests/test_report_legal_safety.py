"""Legal-safety regression tests for app.report (the CLI compliance report).

Covers the two confirmed findings:
  1. _derive_review inverted the HIGH-risk review rule (returned "no review"
     for AI-analysed HIGH records).
  2. generate_report rendered stored AI free text with no forbidden-claims scan.

app.report was previously untested.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import report  # noqa: E402


# ── 1. HIGH always requires human review ──────────────────────────────────────

def test_high_risk_with_ai_summary_still_requires_review():
    rec = {"risk_level": "HIGH", "ai_summary": "A plain-language summary of the change."}
    review_required, reason = report._derive_review(rec)
    assert review_required is True
    assert reason  # a non-empty reason is rendered


def test_high_risk_without_ai_summary_requires_review():
    rec = {"risk_level": "HIGH", "ai_summary": ""}
    review_required, _ = report._derive_review(rec)
    assert review_required is True


def test_high_risk_renders_review_required_yes_in_markdown():
    rec = {
        "url": "https://example.gov/aml",
        "risk_level": "HIGH",
        "ai_summary": "The section on customer due diligence was amended.",
        "created_at": "2026-07-13T09:00:00",
        "content_length": 4200,
    }
    lines = "\n".join(report._md_record(rec))
    assert "**Review required:** Yes" in lines
    assert "**Review required:** No" not in lines


def test_medium_without_ai_still_flags_review():
    rec = {"risk_level": "MEDIUM", "ai_summary": ""}
    review_required, _ = report._derive_review(rec)
    assert review_required is True


# ── 2. forbidden AI free text is scrubbed before rendering ────────────────────

def test_scrub_removes_forbidden_ai_summary():
    rec = {
        "risk_level": "HIGH",
        "ai_summary": "This update means we guarantee compliance for your firm.",
        "business_action": "No action — you will avoid all penalties.",
    }
    clean, scrubbed = report._scrub_record_claims(rec)
    assert scrubbed is True
    assert "guarantee compliance" not in clean["ai_summary"].lower()
    assert "avoid all penalties" not in (clean["business_action"] or "").lower()


def test_scrub_keeps_clean_ai_summary_intact():
    rec = {
        "risk_level": "MEDIUM",
        "ai_summary": "The reporting threshold was lowered; review whether it is relevant.",
    }
    clean, scrubbed = report._scrub_record_claims(rec)
    assert scrubbed is False
    assert clean["ai_summary"] == rec["ai_summary"]


def test_forbidden_risk_reason_does_not_break_the_report(monkeypatch, tmp_path):
    """A forbidden phrase in risk_reason (AI-derived) must be scrubbed, not raise
    a ValueError that produces NO report for ANY record."""
    from app import legal_safety

    poisoned = [
        {
            "url": "https://example.gov/a",
            "risk_level": "HIGH",
            "risk_reason": "This change means we guarantee compliance.",
            "created_at": "2026-07-13T09:00:00",
            "content_length": 3000,
        },
        {
            "url": "https://example.gov/b",
            "risk_level": "LOW",
            "risk_reason": "Minor wording change.",
            "created_at": "2026-07-13T09:00:00",
            "content_length": 1000,
        },
    ]
    monkeypatch.setattr(report, "_fetch_records", lambda days: poisoned)
    monkeypatch.setattr(report, "_REPORTS_DIR", tmp_path)

    result = report.generate_report(days=7)  # must NOT raise
    assert result["forbidden_claims_scrubbed"] >= 1
    md = Path(result["markdown_path"]).read_text(encoding="utf-8")
    assert legal_safety.find_forbidden_claims(md) == []
    # Both records still appear (the clean one is not lost).
    assert "example.gov/b" in md


def test_generate_report_scrubs_and_stays_clean(monkeypatch, tmp_path):
    from app import legal_safety

    poisoned = [
        {
            "url": "https://example.gov/aml",
            "risk_level": "HIGH",
            "ai_summary": "We guarantee compliance and prevent fines for you.",
            "business_action": "Relax — stay compliant automatically.",
            "created_at": "2026-07-13T09:00:00",
            "content_length": 5000,
        }
    ]
    monkeypatch.setattr(report, "_fetch_records", lambda days: poisoned)
    monkeypatch.setattr(report, "_REPORTS_DIR", tmp_path)

    result = report.generate_report(days=7)

    assert result["forbidden_claims_scrubbed"] == 1
    md = Path(result["markdown_path"]).read_text(encoding="utf-8")
    html = Path(result["html_path"]).read_text(encoding="utf-8")
    # The final rendered bytes must carry no forbidden claim...
    assert legal_safety.find_forbidden_claims(md) == []
    assert legal_safety.find_forbidden_claims(html) == []
    # ...and the HIGH record must still show review required.
    assert "**Review required:** Yes" in md
