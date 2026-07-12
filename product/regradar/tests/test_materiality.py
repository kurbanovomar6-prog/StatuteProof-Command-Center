"""Tests for the review-priority (materiality) monitoring heuristic.

Covers: each signal contributes as documented; a deadline/penalty change ranks
higher than a whitespace-only change; whitespace-only / boilerplate → the
``noise`` band; a big substantive diff → ``high``; determinism; evidence is
NEVER dropped by noise-banding (the input dict is not mutated and carries no
"discard" flag); and every customer-facing string passes the shared
forbidden-claims guard.

Fixtures mirror the REAL diff shape (``added_chunks`` / ``removed_chunks`` /
``changed_chunks``) produced by app.chunk_diff.build_chunk_diff.
"""

from __future__ import annotations

import copy

import pytest

from app.chunk_diff import build_chunk_diff
from app.legal_safety import assert_no_forbidden_claims, contains_forbidden_claim
from app.materiality import (
    BAND_HIGH,
    BAND_LOW,
    BAND_MEDIUM,
    BAND_NOISE,
    SHORT_DISCLAIMER,
    _NOISE_SCORE_CAP,
    score_change,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _added(*chunks: str) -> dict:
    return {"added_chunks": list(chunks), "change_status": "CHANGED"}


def _changed(before: str, after: str) -> dict:
    return {"changed_chunks": [{"before": [before], "after": [after]}], "change_status": "CHANGED"}


# ── Return shape ────────────────────────────────────────────────────────────────

def test_return_shape_has_required_keys():
    result = score_change(_added("Firms must file a return by 1 September 2026."))
    assert set(result) >= {"score", "band", "signals", "rationale"}
    assert isinstance(result["score"], int)
    assert 0 <= result["score"] <= 100
    assert result["band"] in {BAND_HIGH, BAND_MEDIUM, BAND_LOW, BAND_NOISE}
    for signal in result["signals"]:
        assert set(signal) == {"name", "detail", "weight"}
        assert isinstance(signal["weight"], int)


def test_non_dict_input_is_tolerated():
    result = score_change(None)  # type: ignore[arg-type]
    assert result["band"] == BAND_NOISE
    assert result["score"] <= _NOISE_SCORE_CAP


# ── Each signal contributes as documented ──────────────────────────────────────

def _signal_names(result: dict) -> set[str]:
    return {s["name"] for s in result["signals"]}


def test_obligation_signal_contributes():
    base = score_change(_added("The exchange rate table was updated for the quarter with new averages listed."))
    withob = score_change(_added("Licensed entities must comply with the new averages listed for the quarter."))
    assert "binding_obligation" in _signal_names(withob)
    assert withob["score"] > base["score"]


def test_deadline_signal_contributes():
    result = score_change(_added("The reporting form must be submitted no later than 1 September 2026."))
    assert "deadline_or_date" in _signal_names(result)


def test_penalty_signal_contributes():
    result = score_change(_added("A penalty of will apply to firms that breach the new averages requirement here."))
    assert "penalty_or_enforcement" in _signal_names(result)


def test_monetary_signal_contributes():
    result = score_change(_added("The minimum capital requirement rises to AED 50,000 for all registered members."))
    assert "monetary_threshold" in _signal_names(result)


def test_licensing_signal_contributes():
    result = score_change(_added("A new licence category is introduced for market operators under this framework."))
    assert "licensing_registration" in _signal_names(result)


def test_reporting_signal_contributes():
    result = score_change(_added("Members shall submit an annual disclosure report to the authority each year."))
    assert "reporting_obligation" in _signal_names(result)


def test_first_seen_signal_contributes():
    result = score_change({
        "added_chunks": ["A brand new guidance page has been published for consultation and comment."],
        "change_status": "FIRST_SEEN",
    })
    assert "new_source_baseline" in _signal_names(result)


def test_source_tier_signal_contributes_when_provided():
    without = score_change(_added("The circular text was amended with new procedural averages listed here."))
    withtier = score_change({**_added("The circular text was amended with new procedural averages listed here."), "source_tier": 1})
    assert "source_importance" in _signal_names(withtier)
    assert withtier["score"] > without["score"]


def test_source_tier_absent_adds_no_signal():
    result = score_change(_added("The circular text was amended with new procedural averages listed here."))
    assert "source_importance" not in _signal_names(result)


def test_magnitude_signal_always_present():
    result = score_change(_added("Some regulated firms will notice a longer document with more detail now."))
    assert "change_magnitude" in _signal_names(result)


# ── Ranking: deadline/penalty > whitespace-only ────────────────────────────────

def test_deadline_penalty_scores_higher_than_whitespace_only():
    deadline_penalty = score_change(_added(
        "Firms must pay a penalty and file the return no later than 1 September 2026."
    ))
    whitespace = score_change(_changed(
        "The rule applies to all licensed firms.",
        "The   rule  applies to   all licensed firms.",
    ))
    assert deadline_penalty["score"] > whitespace["score"]
    assert deadline_penalty["band"] in {BAND_MEDIUM, BAND_HIGH}
    assert whitespace["band"] == BAND_NOISE


# ── Noise banding ──────────────────────────────────────────────────────────────

def test_whitespace_only_change_is_noise():
    result = score_change(_changed(
        "Regulated firms shall maintain adequate records at all times.",
        "Regulated  firms  shall   maintain adequate records at all times.",
    ))
    assert result["band"] == BAND_NOISE
    assert result["score"] <= _NOISE_SCORE_CAP


def test_boilerplate_last_updated_churn_is_noise():
    result = score_change(_changed("Last updated: 5 July 2026", "Last updated: 6 July 2026"))
    assert result["band"] == BAND_NOISE


def test_visitor_counter_churn_is_noise():
    result = score_change(_changed("Total visitors: 12,344", "Total visitors: 12,401"))
    assert result["band"] == BAND_NOISE


def test_below_tiny_magnitude_no_keyword_is_noise():
    result = score_change(_changed("Section A note.", "Section B note."))
    assert result["band"] == BAND_NOISE


def test_explicit_below_threshold_flag_is_noise():
    result = score_change({
        "added_chunks": ["Licensed firms must file a penalty report by the deadline of 2026."],
        "meaningful_change_detected": False,
        "change_status": "CHANGED",
    })
    # Even with high-signal wording, an explicit below-threshold verdict from the
    # diff layer sinks it to noise (prioritization only).
    assert result["band"] == BAND_NOISE


def test_noise_rationale_notes_evidence_is_kept():
    result = score_change(_changed("Last updated: 5 July 2026", "Last updated: 6 July 2026"))
    assert "evidence record" in result["rationale"].lower()
    assert "not discarded" in result["rationale"].lower()


# ── Big substantive diff → high ────────────────────────────────────────────────

def test_big_substantive_diff_is_high():
    previous = "Introduction paragraph that stays the same across both versions of the page."
    additions = "\n\n".join(
        f"Article {i}: Regulated entities shall maintain minimum capital of AED 500,000 "
        f"and must file quarterly returns; failure incurs an administrative fine and "
        f"possible suspension of the licence, effective from 1 September 2026."
        for i in range(8)
    )
    current = previous + "\n\n" + additions
    diff = build_chunk_diff(previous, current)
    result = score_change({**diff, "change_status": "CHANGED"})
    assert result["band"] == BAND_HIGH
    assert result["score"] >= 65


def test_medium_band_for_single_moderate_signal():
    # A modest, real content change with one moderate signal lands in low/medium,
    # never high and never noise.
    result = score_change(_added(
        "The authority published an updated guidance note describing the revised "
        "administrative process for members over the coming period of operations."
    ))
    assert result["band"] in {BAND_LOW, BAND_MEDIUM}
    assert result["band"] not in {BAND_HIGH, BAND_NOISE}


# ── Determinism ────────────────────────────────────────────────────────────────

def test_determinism_same_input_same_output():
    change = _added("Firms must file a return and pay a fine of AED 10,000 by 1 September 2026.")
    first = score_change(copy.deepcopy(change))
    second = score_change(copy.deepcopy(change))
    assert first == second


def test_determinism_across_many_runs():
    change = _added("Licence holders shall submit a disclosure report no later than 30 June 2026.")
    scores = {score_change(copy.deepcopy(change))["score"] for _ in range(15)}
    assert len(scores) == 1


# ── Evidence is NEVER dropped by noise-banding ─────────────────────────────────

def test_scoring_does_not_mutate_input_change():
    change = _changed("Last updated: 5 July 2026", "Last updated: 6 July 2026")
    snapshot = copy.deepcopy(change)
    score_change(change)
    assert change == snapshot  # input untouched — the evidence record is not altered


def test_noise_result_carries_no_discard_directive():
    result = score_change(_changed("Last updated: 5 July 2026", "Last updated: 6 July 2026"))
    # The scorer only ranks; it must never emit a directive to drop/delete/purge
    # the underlying evidence.
    for key in ("drop", "discard", "delete", "purge", "suppress_evidence"):
        assert key not in result


# ── Legal-safety: every customer-facing string passes the guard ────────────────

@pytest.mark.parametrize("change", [
    _added("Firms must pay a penalty and file a return no later than 1 September 2026."),
    _added("A new licence category with a minimum capital requirement of AED 50,000."),
    _changed("The rule applies.", "The  rule   applies."),
    _changed("Last updated: 5 July 2026", "Last updated: 6 July 2026"),
    {"added_chunks": ["New page."], "change_status": "FIRST_SEEN"},
    {},
])
def test_rationale_passes_forbidden_claims_guard(change):
    result = score_change(change)
    # Raises if any forbidden claim is present.
    assert_no_forbidden_claims(result["rationale"], label="materiality rationale")
    assert not contains_forbidden_claim(result["rationale"])


def test_all_framing_strings_are_legal_safe():
    result = score_change(_added("Firms must file a report by the deadline of 1 September 2026."))
    for field in ("rationale", "label", "framing", "disclaimer"):
        assert_no_forbidden_claims(str(result[field]), label=field)


def test_short_disclaimer_present_in_every_rationale():
    for change in (
        _added("Firms must file a return by 1 September 2026 or face a penalty."),
        _changed("Last updated: 5 July 2026", "Last updated: 6 July 2026"),
        {"added_chunks": ["New page."], "change_status": "FIRST_SEEN"},
    ):
        assert SHORT_DISCLAIMER in score_change(change)["rationale"]


def test_rationale_names_its_signals_transparently():
    result = score_change(_added(
        "Licensed firms must file a return and pay a penalty of AED 50,000 by 1 September 2026."
    ))
    low = result["rationale"].lower()
    assert "binding-obligation" in low
    assert "deadline" in low
    assert "penalty" in low


# ── Robustness: excerpt fallback, large inputs, malformed shapes ───────────────

def test_diff_excerpt_fallback_is_scored_without_zero_block_artifact():
    result = score_change({
        "diff_excerpt": "Firms must file a return no later than 1 September 2026.",
        "change_status": "CHANGED",
    })
    assert result["band"] in {BAND_LOW, BAND_MEDIUM, BAND_HIGH}
    assert "0 block(s)" not in result["rationale"]


def test_very_large_input_is_bounded_and_deterministic():
    huge = ["Regulated entities shall maintain minimum capital of AED 500,000." * 400]
    change = {"added_chunks": huge, "change_status": "CHANGED"}
    first = score_change(change)
    second = score_change(change)
    assert first == second
    assert 0 <= first["score"] <= 100


def test_malformed_changed_chunks_do_not_crash():
    # A stray non-list / non-dict shape must be tolerated, not iterated per char.
    assert score_change({"changed_chunks": "oops"})["band"] == BAND_NOISE
    assert score_change({"changed_chunks": [None, "x", 5]})["band"] == BAND_NOISE


# ── Preview wiring: materiality block is additive + optional ranking ────────────

def test_preview_attaches_materiality_block(monkeypatch):
    from app import alert_routing

    candidates = [
        {
            "alert_id": "draft-hi",
            "source_id": "AE-x",
            "source_name": "Test source",
            "risk_level": "HIGH",
            "change_type": "LICENSING",
            "review_status": "APPROVED_FOR_WEEKLY",
            "reviewed_at": "2026-07-10T00:00:00+00:00",
            "added_chunks": [
                "Licensed firms must pay an administrative penalty of AED 50,000 and "
                "file the quarterly return no later than 1 September 2026; failure may "
                "result in suspension of the licence for the registered member.",
            ],
            "removed_chunks": [],
            "changed_chunks": [],
            "change_status": "CHANGED",
        },
        {
            "alert_id": "draft-noise",
            "source_id": "AE-y",
            "source_name": "Test source 2",
            "risk_level": "LOW",
            "change_type": "GENERAL_UPDATE",
            "review_status": "APPROVED_FOR_WEEKLY",
            "reviewed_at": "2026-07-11T00:00:00+00:00",
            "added_chunks": [],
            "removed_chunks": [],
            "changed_chunks": [{"before": ["Last updated: 5 July 2026"], "after": ["Last updated: 6 July 2026"]}],
            "change_status": "CHANGED",
        },
    ]

    profile = {
        "markets": ["UAE"], "industries": [], "topics": [], "regulators": [],
        "custom_sources": [], "alert_threshold": "LOW",
        "onboarding_completed": True, "telegram_alerts_enabled": True,
    }
    monkeypatch.setattr(alert_routing, "user_profile_to_routing_profile", lambda uid: profile)
    monkeypatch.setattr(alert_routing, "load_approved_alert_candidates", lambda days, user_id=None: candidates)
    monkeypatch.setattr(alert_routing, "get_telegram_link", lambda uid: {"telegram_chat_id": "123"})
    monkeypatch.setattr(alert_routing, "get_sent_alert_ids_for_user", lambda uid: set())

    preview = alert_routing.build_routing_preview_for_user(1, days=30)
    assert preview["ranked_by"] == "profile_fit"
    for match in preview["matches"]:
        assert isinstance(match["materiality"], dict)
        assert "score" in match["materiality"]
        assert "band" in match["materiality"]

    by_id = {m["alert_id"]: m for m in preview["matches"]}
    assert by_id["draft-hi"]["materiality"]["band"] == BAND_HIGH
    assert by_id["draft-noise"]["materiality"]["band"] == BAND_NOISE

    # Opt-in ranking surfaces the high-significance change first. Emitted as
    # "review_priority", never the bare legal-sense word "materiality" — this value
    # is customer-reachable via the API payload (legal review 2026-07-12).
    ranked = alert_routing.build_routing_preview_for_user(1, days=30, rank_by_materiality=True)
    assert ranked["ranked_by"] == "review_priority"
    assert ranked["matches"][0]["alert_id"] == "draft-hi"
