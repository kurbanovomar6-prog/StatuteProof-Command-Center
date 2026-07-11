"""
Feature 4 — "Does this affect me?" per-change impact tag (LIGHT, not an RTM).

The alert content layer emits an impact tag ONLY when the matched source's
topics intersect the customer profile's ``topics_in_scope``. Requirements
guarded here:

- Tag emitted when topics intersect; absent when they do not.
- The "what changed" evidence is pulled STRAIGHT from the real diff excerpt —
  never fabricated, never asserted without a diff.
- No profile / no topics / no overlap / no readable diff → no tag, and the
  alert body is byte-for-byte identical to the no-profile rendering
  (graceful degradation, additive only).
- Phrasing stays monitoring-info ("may be relevant", "review the excerpt and
  source") — never advice ("you must"), and the mandatory disclaimer footer
  and forbidden-claims guard are respected.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.alert_content import build_alert_content, render_markdown, render_telegram
from app.monthly_assurance_report import _FORBIDDEN_PHRASES


# A DFSA source: topics = financial_services, securities, funds, aml_cft,
# enforcement, consultations (see app/client_profiles.SOURCE_METADATA).
def _payload(**over):
    base = {
        "url": "https://example.gov.ae/rules",
        # Exact metadata name so source_metadata_for_alert resolves DFSA topics
        # (financial_services, securities, funds, aml_cft, enforcement,
        # consultations — see app/client_profiles.SOURCE_METADATA).
        "source_name": "Dubai Financial Services Authority (DFSA)",
        "jurisdiction": "AE",
        "risk_level": "HIGH",
        "risk_reason": "High risk: strong indicators matched: penalty, sanction.",
        "risk_details": {
            "risk_level": "HIGH",
            "rule": "HIGH_MULTIPLE_STRONG",
            "matched_keywords": ["penalty", "sanction"],
            "matched_context": [],
            "reason": "High risk: strong indicators matched: penalty, sanction.",
        },
        "added": ["A new administrative penalty of AED 50,000 applies to late "
                  "STR filing. Sanction screening cycles are now quarterly."],
        "removed": ["Old text about annual screening cycles."],
        "checked_at_utc": "2026-07-05T14:30:00+00:00",
    }
    base.update(over)
    return base


# Overlaps DFSA on {financial_services, securities, funds, aml_cft, consultations}.
_MATCHING_PROFILE = {
    "client_id": "difc_financial_demo",
    "company_name": "DIFC Financial Demo",
    "topics_in_scope": [
        "financial_services", "securities", "funds",
        "aml_cft", "data_protection", "consultations",
    ],
}

# A tax firm: no topic overlap with a DFSA financial-crime source.
_NON_MATCHING_PROFILE = {
    "client_id": "uae_tax_demo",
    "company_name": "UAE Tax Demo",
    "topics_in_scope": ["tax", "vat", "corporate_tax", "excise"],
}


# ── tag emission ─────────────────────────────────────────────────────────────

def test_impact_tag_emitted_when_topics_intersect():
    c = build_alert_content(_payload(), client_profile=_MATCHING_PROFILE)
    assert c.get("impact_tag"), "topics intersect → impact tag expected"
    assert c["impact_tag"].startswith("May affect:")
    # The reported topics are a real subset of both source and profile topics.
    assert set(c["impact_topics"]) <= {
        "financial_services", "securities", "funds", "aml_cft", "consultations",
    }
    assert c["impact_topics"], "matched topic slugs must be recorded"


def test_impact_tag_absent_when_topics_do_not_intersect():
    c = build_alert_content(_payload(), client_profile=_NON_MATCHING_PROFILE)
    assert "impact_tag" not in c
    assert "impact_line" not in c


def test_no_profile_leaves_alert_unchanged():
    """Default (no profile) call must be byte-for-byte identical to a
    non-matching profile call — additive, zero behavior change."""
    without = build_alert_content(_payload())
    non_match = build_alert_content(_payload(), client_profile=_NON_MATCHING_PROFILE)
    assert "impact_tag" not in without
    assert without == non_match
    # And the rendered channels are identical too.
    assert render_telegram(without) == render_telegram(non_match)
    assert render_markdown(without) == render_markdown(non_match)


def test_profile_without_topics_in_scope_emits_no_tag():
    profile = {"client_id": "empty", "topics_in_scope": []}
    c = build_alert_content(_payload(), client_profile=profile)
    assert "impact_tag" not in c


# ── evidence-grounding ───────────────────────────────────────────────────────

def test_what_changed_is_pulled_straight_from_the_real_diff():
    c = build_alert_content(_payload(), client_profile=_MATCHING_PROFILE)
    # The impact "what changed" evidence IS the real diff excerpt, verbatim.
    assert c["impact_what_changed"] == c["excerpt"]
    assert "AED 50,000" in c["impact_what_changed"], "must carry the real diff text"
    # Nothing fabricated: content the diff never contained must never appear.
    assert "AED 999,999" not in c["impact_what_changed"]
    assert "you will be fined" not in c["impact_what_changed"].lower()


def test_impact_suppressed_when_there_is_no_diff_even_if_topics_match():
    # Topics intersect, but there is no diff to ground a "what changed" line.
    c = build_alert_content(
        _payload(added=[], removed=[]), client_profile=_MATCHING_PROFILE
    )
    assert not c.get("excerpt")
    assert "impact_tag" not in c, "no diff → no impact claim (evidence-grounded)"


def test_impact_suppressed_when_diff_is_unreadable():
    # A binary / mis-decoded body yields only the unreadable-excerpt note —
    # not a real excerpt — so no impact claim may be asserted.
    c = build_alert_content(
        _payload(added=["�" * 40], removed=[]), client_profile=_MATCHING_PROFILE
    )
    assert "impact_tag" not in c


# ── legal safety: wording, disclaimer, forbidden claims ──────────────────────

def test_impact_wording_is_monitoring_info_not_advice():
    c = build_alert_content(_payload(), client_profile=_MATCHING_PROFILE)
    line = c["impact_line"]
    assert "may be relevant to your" in line
    assert line.endswith("review the excerpt and source.")
    low = line.lower()
    for advice in ("you must", "you should", "you are required", "ensure you"):
        assert advice not in low, f"impact line must not give advice: {advice!r}"


def test_impact_strings_contain_no_forbidden_phrase():
    c = build_alert_content(_payload(), client_profile=_MATCHING_PROFILE)
    for text in (c["impact_tag"], c["impact_line"]):
        low = text.lower()
        for phrase in _FORBIDDEN_PHRASES:
            assert phrase not in low, f"forbidden phrase {phrase!r} in impact text"


def test_rendered_channels_carry_tag_and_keep_disclaimer():
    c = build_alert_content(_payload(), client_profile=_MATCHING_PROFILE)
    tg = render_telegram(c)
    md = render_markdown(c)
    for msg in (tg, md):
        assert "May affect:" in msg
        assert "may be relevant to your" in msg
        # Mandatory disclaimer + proof URL survive alongside the new tag.
        assert "Monitoring information only. Not legal advice." in msg
        assert "https://example.gov.ae/rules" in msg
        # The impact block never introduces a forbidden claim (footer's
        # "legal advice" is excluded — it is the mandated disclaimer wording).
        scrubbed = msg.replace("Not legal advice.", "")
        for phrase in _FORBIDDEN_PHRASES:
            assert phrase not in scrubbed.lower(), f"forbidden phrase {phrase!r} rendered"


def test_topic_label_cap_keeps_tag_concise():
    # DFSA ∩ DIFC profile = 5 topics → capped at 4 shown + "(+1 more)".
    c = build_alert_content(_payload(), client_profile=_MATCHING_PROFILE)
    assert "(+1 more)" in c["impact_tag"]
    # All five matched slugs are still recorded even though the tag is trimmed.
    assert len(c["impact_topics"]) == 5
