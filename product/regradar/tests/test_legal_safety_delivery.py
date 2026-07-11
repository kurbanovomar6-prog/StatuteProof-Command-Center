"""GROUP A — legal-safety on the customer delivery paths (SF-1…SF-8).

Legal safety is StatuteProof's #1 promise. These tests lock the guards that
keep a forbidden claim, an unreviewed high-risk run, or an unlabelled SAMPLE
from reaching a customer on ANY delivery path. Each test targets a concrete
leak that shipped before this change and is now closed:

* SF-1 forbidden claim in the FINAL rendered bytes of an alert / brief email.
* SF-2 automated broadcast of a HIGH-risk / low-confidence / review-required run.
* SF-3 an AI obligation/deadline the diff does not back.
* SF-4 a human-reviewed preview whose final bytes still carry a banned claim.
* SF-5 a canonical banned phrase blocked in one path but missed in the brief scan.
* SF-6 a banned phrase in the source-derived "what changed" excerpt.
* SF-8 a SAMPLE brief attributing invented content to a real regulator, unlabelled.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


_CANONICAL = (
    "guarantee compliance",
    "prevent fines",
    "we handle compliance for you",
    "automated compliance decisions",
    "avoid all penalties",
    "never miss",
    "100% accurate",
    "legal advice",
)


# ══════════════════════════════════════════════════════════════════════════
# SF-5 — ONE shared ban list; a phrase blocked anywhere is blocked everywhere
# ══════════════════════════════════════════════════════════════════════════

def test_shared_list_is_single_source_of_truth():
    from app.legal_safety import FORBIDDEN_PHRASES
    from app.monthly_assurance_report import _FORBIDDEN_PHRASES

    # monthly_assurance_report re-exports the canonical list (no fork).
    assert _FORBIDDEN_PHRASES is FORBIDDEN_PHRASES
    for phrase in _CANONICAL:
        assert phrase in FORBIDDEN_PHRASES, f"canonical ban phrase missing: {phrase!r}"


def test_weekly_brief_now_blocks_phrases_it_used_to_miss():
    # Before: weekly_brief.FORBIDDEN_IN_BRIEF was a short hardcoded list that
    # missed these canonical phrases entirely.
    from app.weekly_brief import legal_scan_brief

    for phrase in (
        "never miss",
        "100% accurate",
        "automated compliance decisions",
        "we handle compliance for you",
        "avoid all penalties",
    ):
        brief = {"executive_summary": f"Our system will {phrase} for you."}
        flags = legal_scan_brief(brief)
        assert flags, f"weekly brief scan must flag {phrase!r}, got no flags"


def test_disclaimers_never_self_trip_but_affirmative_claims_are_caught():
    from app.evidence_assessment import LEGAL_DISCLAIMER
    from app.legal_safety import find_forbidden_claims
    from app.weekly_brief import _FULL_BRIEF_DISCLAIMER

    # The product's own denials must NOT self-trip the guard.
    for safe in (
        LEGAL_DISCLAIMER,
        _FULL_BRIEF_DISCLAIMER,
        "Monitoring information only. Not legal advice.",
        "For monitoring information only. Not legal advice and not a guarantee of compliance.",
    ):
        assert find_forbidden_claims(safe) == [], safe

    # An AFFIRMATIVE claim phrased with the same words as a denial must NOT hide
    # inside a neutralized fragment (anchored-denial neutralization).
    assert find_forbidden_claims("We guarantee compliance, prevent fines for you.") == [
        "guarantee compliance", "prevent fines",
    ]
    assert "legal advice" in find_forbidden_claims("Our reports constitute legal advice.")


def test_change_register_guard_shares_the_expanded_list():
    from app.change_register import ChangeRegisterError, assert_no_forbidden_claims

    # "never miss" was NOT in the old monthly list on some paths; now unified.
    with pytest.raises(ChangeRegisterError):
        assert_no_forbidden_claims("StatuteProof will never miss an update.")
    # the disclaimer's own denial must NOT self-trip the guard.
    assert_no_forbidden_claims("Monitoring intelligence only. Not legal advice.")


# ══════════════════════════════════════════════════════════════════════════
# SF-1 — forbidden AI fields dropped at the content layer
# ══════════════════════════════════════════════════════════════════════════

def test_forbidden_ai_summary_and_action_are_dropped_from_render():
    from app.alert_content import build_alert_content, render_telegram
    from app.legal_safety import contains_forbidden_claim

    payload = {
        "risk_level": "HIGH",
        "risk_details": {"rule": "HIGH_MULTIPLE_STRONG",
                         "matched_keywords": ["penalty"], "matched_context": []},
        "source_name": "Src", "url": "https://x.gov.ae", "jurisdiction": "AE",
        "added": ["A new penalty framework applies."],
        "removed": [],
        "checked_at_utc": "2026-07-11T10:00:00Z",
        "executive_summary": "This guarantees compliance and will prevent fines.",
        "business_action_required": "We handle compliance for you; automated compliance decisions apply.",
    }
    content = build_alert_content(payload)
    msg = render_telegram(content)
    assert not contains_forbidden_claim(msg), "final bytes must be free of banned claims"
    assert "prevent fines" not in msg.lower()
    assert "handle compliance for you" not in msg.lower()


# ══════════════════════════════════════════════════════════════════════════
# SF-1 / SF-6 — final-bytes guard on send_telegram_alert (excerpt-borne phrase)
# ══════════════════════════════════════════════════════════════════════════

def test_send_telegram_alert_holds_forbidden_excerpt_and_does_not_broadcast(monkeypatch, tmp_path):
    import app.telegram as tg
    import app.review_queue as rq
    from app.review_queue import list_held_alerts

    monkeypatch.setattr(rq, "_BASE_DIR", tmp_path)
    monkeypatch.delenv("ALERT_DRY_RUN", raising=False)

    def _broadcast_boom(_msg):
        raise AssertionError("customer broadcast must NOT run for a withheld alert")

    # MEDIUM + not review-required + high confidence ⇒ passes the human-review
    # gate, so the ONLY thing that can block delivery is the forbidden phrase
    # SITTING IN THE SOURCE-DERIVED EXCERPT (SF-6), proving the final-bytes guard.
    result = {
        "risk_level": "MEDIUM",
        "risk_details": {"rule": "MEDIUM_SINGLE_STRONG",
                         "matched_keywords": ["licence"], "matched_context": []},
        "source_name": "Adversarial Source", "url": "https://x.gov.ae", "jurisdiction": "AE",
        "added": ["The authority will guarantee compliance for every licensee."],
        "removed": [],
        "checked_at_utc": "2026-07-11T10:00:00Z",
        "review_required": False,
        "confidence": "high",
        "normalized_hash": "d" * 64,
    }
    with patch.object(tg, "_deliver_alert_to_subscribed_users", side_effect=_broadcast_boom), \
         patch.object(tg.requests, "post", side_effect=AssertionError("no network send allowed")):
        sent = tg.send_telegram_alert(result)

    assert sent is False, "a forbidden-claim alert must report not-sent"
    holds = list_held_alerts(base_dir=tmp_path)
    assert holds and holds[0]["reason"] == "forbidden_claim_in_final_bytes", holds


# ══════════════════════════════════════════════════════════════════════════
# SF-2 — human-review gate: HIGH / low-confidence / review_required never
#        auto-broadcasts; a clean, confident, non-HIGH run still does
# ══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("result", [
    {"risk_level": "HIGH", "review_required": True, "confidence": "low"},
    {"risk_level": "MEDIUM", "review_required": True, "confidence": "medium"},
    {"risk_level": "MEDIUM", "review_required": False, "confidence": 0.5},
    {"risk_level": "MEDIUM", "review_required": False, "confidence": "low"},
])
def test_human_review_gate_holds_and_never_broadcasts(monkeypatch, tmp_path, result):
    import app.telegram as tg
    import app.review_queue as rq
    from app.review_queue import list_held_alerts

    monkeypatch.setattr(rq, "_BASE_DIR", tmp_path)
    monkeypatch.delenv("ALERT_DRY_RUN", raising=False)

    payload = {
        **result,
        "risk_details": {"rule": "HIGH_MULTIPLE_STRONG",
                         "matched_keywords": ["penalty"], "matched_context": []},
        "source_name": "Src", "url": "https://x.gov.ae", "jurisdiction": "AE",
        "added": ["A new reporting requirement was introduced for licensees."],
        "removed": [],
        "checked_at_utc": "2026-07-11T10:00:00Z",
        "normalized_hash": "e" * 64,
    }

    def _broadcast_boom(_msg):
        raise AssertionError("must NOT auto-broadcast a run that needs human review")

    with patch.object(tg, "_deliver_alert_to_subscribed_users", side_effect=_broadcast_boom), \
         patch.object(tg.requests, "post", side_effect=AssertionError("no founder send either")):
        sent = tg.send_telegram_alert(payload)

    assert sent is False
    holds = list_held_alerts(base_dir=tmp_path)
    assert holds and holds[0]["reason"] == "requires_human_review", holds


def test_clean_confident_non_high_run_still_auto_broadcasts(monkeypatch, tmp_path):
    import app.telegram as tg
    import app.review_queue as rq

    monkeypatch.setattr(rq, "_BASE_DIR", tmp_path)
    monkeypatch.delenv("ALERT_DRY_RUN", raising=False)

    payload = {
        "risk_level": "MEDIUM",
        "review_required": False,
        "confidence": "high",
        "risk_details": {"rule": "MEDIUM_SINGLE_STRONG",
                         "matched_keywords": ["licence"], "matched_context": []},
        "source_name": "Src", "url": "https://x.gov.ae", "jurisdiction": "AE",
        "added": ["A new licence category was introduced for market operators."],
        "removed": [],
        "checked_at_utc": "2026-07-11T10:00:00Z",
        "normalized_hash": "f" * 64,
    }
    reached = []
    with patch.object(tg, "_deliver_alert_to_subscribed_users",
                      side_effect=lambda m: reached.append(m) or 1):
        sent = tg.send_telegram_alert(payload)

    assert sent is True, "a clean, confident, non-HIGH, non-review run must still deliver"
    assert reached, "customer broadcast should have been invoked"


# ══════════════════════════════════════════════════════════════════════════
# SF-1 — final-bytes guard on the brief email path
# ══════════════════════════════════════════════════════════════════════════

def test_brief_email_with_forbidden_claim_is_held_not_queued(tmp_path):
    from app.email_delivery import build_monitoring_brief_email, deliver_brief_email

    payload = build_monitoring_brief_email(
        brief_markdown="This monitoring brief will guarantee compliance for you.",
        source_name="Src", risk_level="HIGH", client_email="c@example.com",
    )
    result = deliver_brief_email(payload, source_id="s1", env={}, base_dir=tmp_path)
    assert result["status"] == "error"
    assert result.get("forbidden_claims"), result
    # Fail closed: nothing queued to the outbox.
    outbox = tmp_path / "data" / "outbox"
    assert not (outbox.exists() and any(outbox.iterdir())), "a withheld email must not be queued"


def test_clean_brief_email_still_queues(tmp_path):
    from app.email_delivery import build_monitoring_brief_email, deliver_brief_email

    payload = build_monitoring_brief_email(
        brief_markdown="A monitored source recorded a change. Review the evidence record.",
        source_name="Src", risk_level="MEDIUM", client_email="c@example.com",
    )
    result = deliver_brief_email(payload, source_id="s2", env={}, base_dir=tmp_path)
    assert result["status"] == "queued_local", result


# ══════════════════════════════════════════════════════════════════════════
# SF-4 — human-reviewed preview: final bytes still guarded (fail closed)
# ══════════════════════════════════════════════════════════════════════════

def test_reviewed_preview_raises_on_forbidden_final_bytes():
    from app.alert_routing import build_alert_telegram_message
    from app.legal_safety import ForbiddenClaimError

    profile = {"markets": ["UAE"], "topics": []}
    match = {
        "source_name": "Src", "market": "UAE", "change_type": "update",
        "risk_level": "HIGH", "reviewed_at": "2026-07-11",
        "executive_summary": "This reviewed change means we handle compliance for you.",
        "reasons": ["Matched"], "limitations": [], "source_url": "https://x.gov.ae",
    }
    with pytest.raises(ForbiddenClaimError):
        build_alert_telegram_message(profile, match)


def test_reviewed_preview_clean_returns_message():
    from app.alert_routing import build_alert_telegram_message

    profile = {"markets": ["UAE"], "topics": []}
    match = {
        "source_name": "Src", "market": "UAE", "change_type": "update",
        "risk_level": "MEDIUM", "reviewed_at": "2026-07-11",
        "executive_summary": "A monitored rulebook change was reviewed.",
        "reasons": ["Matched"], "limitations": [], "source_url": "https://x.gov.ae",
    }
    msg = build_alert_telegram_message(profile, match)
    assert "Reviewed alert preview" in msg


# ══════════════════════════════════════════════════════════════════════════
# SF-3 — AI obligation/deadline not backed by the diff is labelled unverified
# ══════════════════════════════════════════════════════════════════════════

def test_ungrounded_ai_obligation_is_labelled_unverified():
    from app.alert_content import build_alert_content

    payload = {
        "risk_level": "MEDIUM",
        "risk_details": {"rule": "MEDIUM_SINGLE_STRONG",
                         "matched_keywords": ["licence"], "matched_context": []},
        "source_name": "Src", "url": "https://x.gov.ae", "jurisdiction": "AE",
        "added": ["General narrative text with no structured obligation."],
        "removed": [],
        "checked_at_utc": "2026-07-11T10:00:00Z",
        # AI asserts a hard deadline the delta does NOT contain as a detected fact.
        "executive_summary": "Entities must file returns no later than 1 August 2026.",
    }
    content = build_alert_content(payload)  # no detected_facts supplied
    assert content.get("summary", "").startswith("AI-generated, unverified:")


def test_grounded_summary_is_not_labelled():
    from app.alert_content import build_alert_content
    from app.detected_facts import extract_detected_facts

    added = ["All returns are due no later than 1 August 2026."]
    payload = {
        "risk_level": "MEDIUM",
        "risk_details": {"rule": "MEDIUM_SINGLE_STRONG",
                         "matched_keywords": ["licence"], "matched_context": []},
        "source_name": "Src", "url": "https://x.gov.ae", "jurisdiction": "AE",
        "added": added, "removed": [],
        "checked_at_utc": "2026-07-11T10:00:00Z",
        "detected_facts": extract_detected_facts(added),
        "executive_summary": "A monitored rulebook change was reviewed.",
    }
    content = build_alert_content(payload)
    assert not content.get("summary", "").startswith("AI-generated, unverified:")


# ══════════════════════════════════════════════════════════════════════════
# SF-8 — SAMPLE brief attributing invented content to a real regulator is labelled
# ══════════════════════════════════════════════════════════════════════════

def test_sample_brief_carries_sample_fake_label():
    from app.user_delivery import build_sample_brief_message

    msg = build_sample_brief_message({"company_name": "Acme"})
    assert "SAMPLE / FAKE" in msg
    # the invented regulator attribution must sit AFTER the top label.
    assert msg.index("SAMPLE / FAKE") < msg.index("DFSA")
