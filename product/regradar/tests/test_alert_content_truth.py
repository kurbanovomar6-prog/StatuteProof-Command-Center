"""
A2/A3/A4/A5 (alert-quality sprint): the alert content layer must be truthful.

- Every sentence backed by an actual detection: matched rule + keywords are
  named; a capped (≤400 chars) excerpt of the REAL diff is included.
- No detected deadline → no deadline language anywhere (A2).
- Absent fields are omitted entirely — never "Market: —" / "Not specified" (A3).
- HIGH states its indicator; without recorded matches the alert claims only
  what it knows (A4).
- Mandatory in every rendering: "Monitoring information only. Not legal
  advice." footer, proof URL, timestamp (regression-guarded).
- Cosmetics: no double periods (A5).

Telegram and the alert-draft markdown share ONE content layer.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.risk import analyze_risk


# ── risk result enrichment (A2/A4 foundation) ────────────────────────────────

def test_high_two_keywords_names_the_matches():
    r = analyze_risk({
        "has_changes": True,
        "added": ["New penalty framework and licence revocation applies " * 4],
        "removed": [],
    })
    assert r["risk_level"] == "HIGH"
    assert r.get("rule") == "HIGH_MULTIPLE_STRONG"
    assert "penalty" in r.get("matched_keywords", [])
    # reason must name the actual matches, not generic boilerplate
    assert "penalty" in r["reason"].lower()


def test_high_one_keyword_plus_context_names_both():
    r = analyze_risk({
        "has_changes": True,
        "added": ["sanction screening obligations for reporting entities " * 4],
        "removed": [],
    })
    assert r["risk_level"] == "HIGH"
    assert r.get("rule") == "HIGH_STRONG_PLUS_CONTEXT"
    assert r.get("matched_keywords") and r.get("matched_context")
    low = r["reason"].lower()
    for kw in r["matched_keywords"]:
        assert kw in low
    # A2: must not claim deadline/penalty context it did not match
    for claim in ("deadline", "penalty"):
        if claim not in r.get("matched_context", []) and claim not in r.get("matched_keywords", []):
            assert claim not in low, f"reason claims undetected context {claim!r}"


def test_medium_single_keyword_claims_nothing_extra():
    r = analyze_risk({
        "has_changes": True,
        "added": ["a new license category was introduced for market operators " * 3],
        "removed": [],
    })
    assert r["risk_level"] in {"MEDIUM", "HIGH"}
    assert "matched_keywords" in r and "rule" in r


def test_no_reason_ends_with_double_period():
    samples = [
        {"has_changes": True, "added": ["penalty and sanction text " * 6], "removed": []},
        {"has_changes": True, "added": ["update to guidance " * 10], "removed": []},
        {"has_changes": True, "added": ["plain narrative text with nothing risky " * 6], "removed": []},
        {"has_changes": False},
    ]
    for s in samples:
        r = analyze_risk(s)
        assert ".." not in r["reason"], f"double period in: {r['reason']!r}"


# ── shared content layer ─────────────────────────────────────────────────────

def _payload(**over):
    base = {
        "url": "https://example.gov.ae/rules",
        "source_name": "DFSA Financial Crime Prevention Notices and MLRO Letters",
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
        "ai_used": False,
        "executive_summary": "",
        "business_action_required": "",
        "normalized_hash": "c" * 64,
        "checked_at_utc": "2026-07-05T14:30:00+00:00",
        "deadline": None,
        "affected_entities": [],
        "urgency": "",
    }
    base.update(over)
    return base


def test_content_includes_rule_keywords_and_capped_excerpt():
    from app.alert_content import build_alert_content
    c = build_alert_content(_payload())
    assert "penalty" in c["matched_keywords"] and "sanction" in c["matched_keywords"]
    assert c["excerpt"], "real diff excerpt required"
    assert len(c["excerpt"]) <= 400
    assert "AED 50,000" in c["excerpt"], "excerpt must come from the actual diff"


def test_telegram_render_omits_absent_fields_entirely():
    from app.alert_content import build_alert_content, render_telegram
    msg = render_telegram(build_alert_content(_payload()))
    assert "Not specified" not in msg
    assert ": —" not in msg and "*—*" not in msg
    assert "Deadline" not in msg, "no detected deadline → no deadline language"
    assert "Materiality" not in msg
    assert "Affected" not in msg


def test_telegram_render_mandatory_elements():
    from app.alert_content import build_alert_content, render_telegram
    msg = render_telegram(build_alert_content(_payload()))
    assert "Monitoring information only. Not legal advice." in msg
    assert "https://example.gov.ae/rules" in msg
    assert "2026-07-05" in msg, "timestamp mandatory"
    assert ".." not in msg.replace("...", ""), "no double periods"


def test_telegram_render_high_names_indicator():
    from app.alert_content import build_alert_content, render_telegram
    msg = render_telegram(build_alert_content(_payload()))
    assert "HIGH" in msg
    assert "penalty" in msg and "sanction" in msg, "HIGH must state its indicators"


def test_high_without_recorded_matches_claims_only_what_it_knows():
    from app.alert_content import build_alert_content, render_telegram
    p = _payload(risk_details={}, risk_reason="")
    msg = render_telegram(build_alert_content(p))
    assert "HIGH" in msg
    low = msg.lower()
    for phrase in ("strong regulatory risk indicator", "deadline", "penalty, or mandatory"):
        assert phrase not in low, f"unbacked claim {phrase!r} in HIGH alert"


def test_detected_deadline_is_rendered_when_present():
    # F2 (signal-max): a deadline renders ONLY when rule-detected in the
    # actual delta with a matched span — a bare payload field is an
    # unbacked claim and must not render.
    from app.alert_content import build_alert_content, render_telegram
    from app.detected_facts import extract_detected_facts

    added = ["All returns are due no later than 1 August 2026."]
    payload = _payload(added=added, detected_facts=extract_detected_facts(added))
    msg = render_telegram(build_alert_content(payload))
    assert "1 August 2026" in msg

    unbacked = render_telegram(build_alert_content(_payload(deadline="2026-08-01")))
    assert "2026-08-01" not in unbacked, "unbacked deadline field must not render"


def test_markdown_render_shares_the_same_content():
    from app.alert_content import build_alert_content, render_markdown
    c = build_alert_content(_payload())
    md = render_markdown(c)
    assert "AED 50,000" in md, "email/md channel must carry the same excerpt"
    assert "penalty" in md and "sanction" in md
    assert "Monitoring information only. Not legal advice." in md
    assert "https://example.gov.ae/rules" in md
    assert "Not specified" not in md and ": —" not in md


def test_excerpt_capped_at_400_even_for_huge_diffs():
    from app.alert_content import build_alert_content
    huge = _payload(added=["penalty " * 500], removed=["sanction " * 500])
    c = build_alert_content(huge)
    assert len(c["excerpt"]) <= 400


# ── headline shape: front-loaded, factual, bounded, guarded (info-presentation) ──

def test_headline_is_front_loaded_factual_and_dated():
    from app.alert_content import build_alert_content

    c = build_alert_content(_payload())
    title = c["title"]
    # Front-loaded on the source/regulator, NOT the brand or a severity label.
    assert title.startswith("DFSA Financial Crime Prevention Notices")
    assert not title.startswith("StatuteProof alert")
    # A severity/priority word is never the headline — the band carries that.
    assert "HIGH" not in title
    # States the FACT and carries the recorded date.
    assert "monitored change detected" in title
    assert "2026-07-05" in title


def test_headline_prefixes_regulator_when_source_name_lacks_it():
    from app.alert_content import build_alert_content

    c = build_alert_content(_payload(source_name="Virtual Assets Rulebook", url="https://www.vara.ae/"))
    assert c["title"].startswith("VARA — Virtual Assets Rulebook")


def test_headline_is_length_bounded():
    from app.alert_content import build_alert_content

    huge = _payload(source_name="Extremely Long Official Regulatory Source Name " * 6)
    c = build_alert_content(huge)
    assert len(c["title"]) <= 120


def test_headline_falls_back_when_no_source_name():
    from app.alert_content import build_alert_content

    c = build_alert_content(_payload(source_name=""))
    assert c["title"] == "StatuteProof alert — monitored change detected"


def test_headline_guards_forbidden_claim_in_source_name():
    # The source name is source-controlled free text. A headline that would embed
    # a forbidden claim must never ship; it falls back to the fixed safe title.
    from app.alert_content import build_alert_content

    c = build_alert_content(_payload(source_name="We guarantee compliance Ltd"))
    assert c["title"] == "StatuteProof alert — monitored change detected"


def test_headline_strips_markdown_metachars_from_source_name():
    # Telegram renders the title inside *...*; page-derived metachars must not
    # break formatting or inject markup.
    from app.alert_content import build_alert_content

    c = build_alert_content(_payload(source_name="DFSA *Notice* [inject]"))
    for ch in "*_`[]":
        assert ch not in c["title"]


# ── fact / assessment split: facts flat, "why it may matter" calibrated ──────

def test_what_changed_block_carries_flat_diff_facts_not_hedged():
    from app.alert_content import build_alert_content, render_markdown

    md = render_markdown(build_alert_content(_payload()))
    # The "what changed" block is the real diff — flat declarative facts
    # (amounts/dates), carried verbatim, with no StatuteProof hedging wrapper.
    assert "**What changed (excerpt):**" in md
    assert "AED 50,000" in md


def test_why_it_may_matter_uses_calibrated_verb_never_imperative():
    from app.alert_content import build_alert_content

    # Exact SOURCE_METADATA name (DFSA) + a profile that overlaps its topics
    # reliably triggers the "why it may matter" assessment line — the same setup
    # test_alert_impact_tag.py proves resolves. The fact block stays flat; the
    # assessment must use a calibrated verb and never an obligation imperative.
    profile = {"topics_in_scope": ["financial_services", "aml_cft", "securities"]}
    payload = _payload(source_name="Dubai Financial Services Authority (DFSA)")
    content = build_alert_content(payload, client_profile=profile)
    line = content["impact_line"].lower()
    assert "may be relevant" in line, "assessment must use a calibrated verb"
    for imperative in ("you must", "required action", "ensure compliance", "you are required"):
        assert imperative not in line
    # The assessment's "what changed" evidence is the flat diff excerpt verbatim —
    # facts are never re-summarised or hedged into the assessment.
    assert content["impact_what_changed"] == content["excerpt"]


def test_alert_draft_markdown_embeds_shared_content_block():
    """The draft/email channel renders the SAME content layer (A2 shared-layer
    requirement): when the pipeline attaches alert_content_markdown, the
    rendered alert_draft.md must carry it verbatim."""
    from app.alert_content import build_alert_content, render_markdown
    from app.alert_drafts import render_alert_markdown

    shared = render_markdown(build_alert_content(_payload()))
    alert = {
        "alert_id": "draft-test", "source_name": "X", "risk_level": "HIGH",
        "alert_content_markdown": shared,
    }
    md = render_alert_markdown(alert)
    assert "AED 50,000" in md, "shared excerpt must reach the draft channel"
    assert "Monitoring information only. Not legal advice." in md
