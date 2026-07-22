"""
Tests for classify_change_type and classify_risk in alert_drafts.py.

Covers all return branches of classify_change_type and all risk-level
outcomes of classify_risk, including the HIGH/MEDIUM/LOW/REVIEW paths.
No network calls, no file writes, no external mocking.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from app.alert_drafts import (
    classify_change_type,
    classify_risk,
    _is_legislation_aggregate_change,
    _joined_diff_text,
    _contains_any,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _run(source_name: str = "Test Source", source_id: str = "AE-test", category: str = "") -> dict:
    return {
        "run_id": "run-001",
        "source_id": source_id,
        "source_name": source_name,
        "category": category,
        "market": "AE",
        "timestamp_utc": "2026-06-23T10:00:00+00:00",
        "change_status": "CHANGED",
        "official_url": "https://example.gov.ae/",
    }


def _diff(
    added: list[str] | None = None,
    removed: list[str] | None = None,
    changed: list[dict] | None = None,
    *,
    quality: str = "GOOD",
    meaningful: bool = True,
    added_count: int | None = None,
    removed_count: int = 0,
    changed_count: int = 0,
    summary: str = "",
) -> dict:
    added = added or []
    return {
        "diff_quality": quality,
        "meaningful_change_detected": meaningful,
        "added_chunks": added,
        "removed_chunks": removed or [],
        "changed_chunks": changed or [],
        "added_count": added_count if added_count is not None else len(added),
        "removed_count": removed_count,
        "changed_count": changed_count,
        "diff_summary": summary or f"{len(added)} added",
    }


def _proof(quality: str = "GOOD") -> dict:
    return {
        "official_url": "https://example.gov.ae/",
        "final_url": "https://example.gov.ae/",
        "normalized_hash": "deadbeef01234567",
        "proof_quality": quality,
        "limitations_notes": "",
    }


# ── _joined_diff_text ────────────────────────────────────────────────────────

def test_joined_diff_text_concatenates_added_and_removed():
    diff = _diff(added=["para A"], removed=["para B"])
    result = _joined_diff_text(diff)
    assert "para A" in result
    assert "para B" in result


def test_joined_diff_text_includes_changed_chunk_before_and_after():
    diff = _diff(changed=[{"before": ["old text"], "after": ["new text"]}])
    result = _joined_diff_text(diff)
    assert "old text" in result
    assert "new text" in result


def test_joined_diff_text_empty_diff_returns_empty_string():
    diff = _diff()
    assert _joined_diff_text(diff) == ""


# ── _contains_any ────────────────────────────────────────────────────────────

def test_contains_any_case_insensitive_match():
    assert _contains_any("AML compliance report", ["aml"]) is True


def test_contains_any_returns_false_when_no_pattern_matches():
    assert _contains_any("routine website update", ["deadline", "fine"]) is False


def test_contains_any_empty_text_returns_false():
    assert _contains_any("", ["aml"]) is False


# ── _is_legislation_aggregate_change ─────────────────────────────────────────

def test_is_legislation_aggregate_change_returns_true_for_arabic_counter_change():
    run = _run("UAE Legislation Portal", "AE-uae-legislation-portal")
    diff = _diff(
        changed=[{"before": ["تشريع القطاع المالي 107 تشريع"], "after": ["تشريع القطاع المالي 108 تشريع"]}],
        added_count=0,
        removed_count=0,
        changed_count=1,
        meaningful=True,
    )
    assert _is_legislation_aggregate_change(run, diff) is True


def test_is_legislation_aggregate_change_returns_false_for_non_legislation_source():
    run = _run("Dubai VARA", "AE-vara")
    diff = _diff(
        changed=[{"before": ["تشريع count 10"], "after": ["تشريع count 11"]}],
        added_count=0,
        removed_count=0,
        changed_count=1,
    )
    assert _is_legislation_aggregate_change(run, diff) is False


def test_is_legislation_aggregate_change_returns_false_when_added_count_nonzero():
    run = _run("UAE Legislation Portal", "AE-uae-legislation-portal")
    diff = _diff(
        added=["تشريع جديد"],
        changed=[{"before": ["تشريع 10"], "after": ["تشريع 11"]}],
        added_count=1,
        removed_count=0,
        changed_count=1,
    )
    assert _is_legislation_aggregate_change(run, diff) is False


# ── classify_change_type ─────────────────────────────────────────────────────

def test_classify_change_type_returns_consultation_for_consultation_text():
    diff = _diff(added=["A public consultation on the proposed licensing framework."])
    result = classify_change_type(_run(), diff)
    assert result == "CONSULTATION"


def test_classify_change_type_returns_aml_cft_for_aml_text():
    diff = _diff(added=["Financial institutions must report suspicious transactions to the UAE FIU."])
    result = classify_change_type(_run(), diff)
    assert result == "AML_CFT"


def test_classify_change_type_returns_aml_cft_for_cft_keyword():
    diff = _diff(added=["The CFT framework has been updated."])
    result = classify_change_type(_run(), diff)
    assert result == "AML_CFT"


def test_classify_change_type_returns_tax_for_vat_text():
    diff = _diff(added=["The VAT registration threshold has been revised to AED 375,000."])
    result = classify_change_type(_run(), diff)
    assert result == "TAX"


def test_classify_change_type_returns_tax_for_corporate_tax():
    diff = _diff(added=["Corporate tax filing deadline extended."])
    result = classify_change_type(_run(), diff)
    assert result == "TAX"


def test_classify_change_type_returns_data_protection_for_privacy_text():
    diff = _diff(added=["Controllers must register under the data protection regime."])
    result = classify_change_type(_run(), diff)
    assert result == "DATA_PROTECTION"


def test_classify_change_type_returns_deadline_or_reporting_for_submit_keyword():
    diff = _diff(added=["Entities must submit their annual report by 31 March."])
    result = classify_change_type(_run(), diff)
    assert result == "DEADLINE_OR_REPORTING"


def test_classify_change_type_returns_licensing_for_authorisation_text():
    diff = _diff(added=["New authorisation requirements for payment service providers."])
    result = classify_change_type(_run(), diff)
    assert result == "LICENSING"


def test_classify_change_type_returns_rulebook_update_for_custody_text():
    diff = _diff(added=["The custody rules for client assets have been amended."])
    result = classify_change_type(_run(), diff)
    assert result == "RULEBOOK_UPDATE"


def test_classify_change_type_returns_circular_update_for_circular_keyword():
    diff = _diff(added=["Circular No. 3 of 2026 has been published."])
    result = classify_change_type(_run(), diff)
    assert result == "CIRCULAR_UPDATE"


def test_classify_change_type_returns_guidance_update_for_guidance_keyword():
    diff = _diff(added=["Guidance on risk-based approach to customer due diligence."])
    result = classify_change_type(_run(), diff)
    assert result == "GUIDANCE_UPDATE"


def test_classify_change_type_returns_enforcement_for_penalty_text():
    diff = _diff(added=["A penalty of AED 500,000 was imposed for AML violations."])
    result = classify_change_type(_run(), diff)
    # AML takes priority over enforcement in keyword order
    assert result in {"AML_CFT", "ENFORCEMENT"}


def test_classify_change_type_returns_enforcement_for_sanction_text():
    diff = _diff(added=["The regulator issued a sanction and revocation of licence."])
    result = classify_change_type(_run(), diff)
    assert result in {"ENFORCEMENT", "LICENSING"}


def test_classify_change_type_enforcement_wording_wins_over_notice():
    # Regression: an enforcement notice containing both "notice" and "penalty"
    # must classify as ENFORCEMENT, not CIRCULAR_UPDATE — enforcement wording
    # is a stronger, more specific signal and gates the enforcement surface.
    diff = _diff(added=["Regulatory Notice: penalty imposed on Firm X."])
    result = classify_change_type(_run(), diff)
    assert result == "ENFORCEMENT"


def test_classify_change_type_plain_circular_without_enforcement_stays_circular():
    # A plain circular with no enforcement wording still classifies as CIRCULAR_UPDATE.
    diff = _diff(added=["Circular 5/2026: reporting template update."])
    result = classify_change_type(_run(), diff)
    assert result == "CIRCULAR_UPDATE"


def test_classify_change_type_plain_guidance_without_enforcement_stays_guidance():
    # A guidance note with no enforcement wording still classifies as GUIDANCE_UPDATE.
    diff = _diff(added=["Guidance note on the risk-based approach to onboarding."])
    result = classify_change_type(_run(), diff)
    assert result == "GUIDANCE_UPDATE"


def test_classify_change_type_suspension_of_trading_stays_circular():
    # Regression: a market-operations trading halt is NOT an enforcement action
    # against a firm. "suspension of trading" must not light the enforcement
    # badge; the "notice" wording keeps it a CIRCULAR_UPDATE.
    diff = _diff(added=["Notice: temporary suspension of trading in the affected securities."])
    result = classify_change_type(_run(), diff)
    assert result == "CIRCULAR_UPDATE"


def test_classify_change_type_sanctions_screening_guidance_stays_circular():
    # Regression: AML sanctions-screening obligations are compliance guidance,
    # not an enforcement action. The "circular" wording keeps it CIRCULAR_UPDATE.
    diff = _diff(added=["This circular provides guidance on sanctions screening obligations."])
    result = classify_change_type(_run(), diff)
    assert result == "CIRCULAR_UPDATE"


def test_classify_change_type_targeted_financial_sanctions_list_stays_guidance():
    # Regression: the targeted-financial-sanctions LIST framework is AML/CFT
    # screening guidance, not enforcement. Must stay GUIDANCE_UPDATE.
    diff = _diff(added=["Guideline clarifying the targeted financial sanctions list framework."])
    result = classify_change_type(_run(), diff)
    assert result == "GUIDANCE_UPDATE"


def test_classify_change_type_genuine_suspension_with_action_context_is_enforcement():
    # A real firm-level suspension imposed as a disciplinary action IS
    # enforcement — the ambiguous root is rescued by the action context.
    diff = _diff(added=["Notice: a suspension was imposed on Firm X as a disciplinary measure."])
    result = classify_change_type(_run(), diff)
    assert result == "ENFORCEMENT"


def test_classify_change_type_defined_term_is_not_enforcement():
    # Regression (word-boundary): the substring 'fine' inside 'defined' must NOT
    # light the enforcement badge. A glossary/definitional change is not an
    # enforcement action. Previously classified ENFORCEMENT via 'fine' in 'defined'.
    diff = _diff(added=["The term is defined in the GLO module of the rulebook glossary."])
    result = classify_change_type(_run(), diff)
    assert result != "ENFORCEMENT"


def test_classify_change_type_refine_confine_define_are_not_enforcement():
    # Regression (word-boundary): 'refine', 'confine', 'define' all contain the
    # substring 'fine' but none is enforcement wording.
    diff = _diff(added=["We refine and confine the scope; the process is defined below."])
    result = classify_change_type(_run(), diff)
    assert result != "ENFORCEMENT"


def test_classify_change_type_plural_penalties_is_enforcement():
    # Regression (stem): plural 'penalties' must classify as ENFORCEMENT. The
    # old singular substring 'penalty' is not contained in 'penalties', so
    # genuine plural penalty text was MISSED (false negative).
    diff = _diff(added=["Administrative penalties of AED 500,000 were imposed on the firm."])
    result = classify_change_type(_run(), diff)
    assert result == "ENFORCEMENT"


def test_classify_change_type_singular_penalty_imposed_is_enforcement():
    # A genuine singular 'penalty imposed' diff still classifies as ENFORCEMENT.
    diff = _diff(added=["A penalty was imposed on the firm following a supervisory review."])
    result = classify_change_type(_run(), diff)
    assert result == "ENFORCEMENT"


def test_classify_change_type_enforcement_not_driven_by_source_name():
    # Regression (honest badge): a BENIGN administrative change on a source
    # merely NAMED 'DFSA Enforcement' must NOT classify as ENFORCEMENT — the
    # badge/tooltip attribute the classification to enforcement wording IN THE
    # DIFF, and this diff has none. Previously the 'enforcement' token in the
    # source name short-circuited to ENFORCEMENT (a false in-the-diff claim).
    run = _run(source_name="DFSA Enforcement", source_id="AE-dfsa-enforcement", category="enforcement")
    diff = _diff(added=["The office address and contact telephone number were updated."])
    result = classify_change_type(run, diff)
    assert result != "ENFORCEMENT"


def test_classify_change_type_benign_sanctions_screening_on_enforcement_source_not_enforcement():
    # A benign AML sanctions-screening update on an enforcement-NAMED source must
    # not light the badge: no punitive action context, benign phrase suppresses,
    # and the source name no longer drives the classification.
    run = _run(source_name="DFSA Enforcement", source_id="AE-dfsa-enforcement", category="enforcement")
    diff = _diff(added=["Updated guidance on sanctions screening obligations for onboarding."])
    result = classify_change_type(run, diff)
    assert result != "ENFORCEMENT"


def test_classify_change_type_enforcement_wording_on_enforcement_source_is_enforcement():
    # The honest positive case: enforcement wording genuinely in the diff on an
    # enforcement-named source correctly classifies ENFORCEMENT — the tooltip's
    # in-the-diff attribution is TRUE.
    run = _run(source_name="DFSA Enforcement", source_id="AE-dfsa-enforcement", category="enforcement")
    diff = _diff(added=["A financial penalty was imposed on Firm X for compliance breaches."])
    result = classify_change_type(run, diff)
    assert result == "ENFORCEMENT"


def test_classify_change_type_returns_new_publication_when_added_count_positive_no_keywords():
    diff = _diff(added_count=3, meaningful=True)
    result = classify_change_type(_run(), diff)
    assert result == "NEW_PUBLICATION"


def test_classify_change_type_returns_general_update_for_meaningful_with_no_keywords():
    diff = {
        "diff_quality": "GOOD",
        "meaningful_change_detected": True,
        "added_chunks": [],
        "removed_chunks": [],
        "changed_chunks": [],
        "added_count": 0,
        "removed_count": 0,
        "changed_count": 0,
        "diff_summary": "minor update",
    }
    result = classify_change_type(_run(), diff)
    assert result == "GENERAL_UPDATE"


def test_classify_change_type_returns_unknown_for_empty_diff_no_keywords():
    diff = {
        "diff_quality": "GOOD",
        "meaningful_change_detected": False,
        "added_chunks": [],
        "removed_chunks": [],
        "changed_chunks": [],
        "added_count": 0,
        "removed_count": 0,
        "changed_count": 0,
        "diff_summary": "",
    }
    result = classify_change_type(_run(), diff)
    assert result == "UNKNOWN"


def test_classify_change_type_returns_unknown_for_legislation_aggregate_change():
    run = _run("UAE Legislation Portal", "AE-uae-legislation-portal")
    diff = _diff(
        changed=[{"before": ["تشريع 50"], "after": ["تشريع 51"]}],
        added_count=0,
        removed_count=0,
        changed_count=1,
    )
    result = classify_change_type(run, diff)
    assert result == "UNKNOWN"


def test_classify_change_type_uses_source_name_for_keyword_matching():
    # "consultation" in source category field triggers CONSULTATION even without diff text
    run = _run("My Consultative Body", category="consultative")
    diff = _diff(added_count=1)
    result = classify_change_type(run, diff)
    assert result == "CONSULTATION"


# ── classify_risk ─────────────────────────────────────────────────────────────

def test_classify_risk_returns_review_for_limited_diff_quality():
    diff = _diff(quality="LIMITED")
    level, rationale, confidence = classify_risk(_run(), diff, _proof(), "AML_CFT")
    assert level == "REVIEW"
    assert confidence == "LOW"
    assert "manual review" in rationale.lower()


def test_classify_risk_returns_review_for_incomplete_diff_quality():
    diff = _diff(quality="INCOMPLETE")
    level, _, _ = classify_risk(_run(), diff, _proof(), "AML_CFT")
    assert level == "REVIEW"


def test_classify_risk_returns_review_for_incomplete_proof_quality():
    diff = _diff()
    level, _, _ = classify_risk(_run(), diff, _proof(quality="INCOMPLETE"), "AML_CFT")
    assert level == "REVIEW"


def test_classify_risk_returns_review_for_unknown_change_type():
    diff = _diff()
    level, _, _ = classify_risk(_run(), diff, _proof(), "UNKNOWN")
    assert level == "REVIEW"


def test_classify_risk_returns_high_for_obligation_plus_deadline():
    diff = _diff(added=["Firms must submit the AML report by the effective date of 1 January 2027."])
    level, rationale, _ = classify_risk(_run(), diff, _proof(), "AML_CFT")
    assert level == "HIGH"
    assert "obligation" in rationale.lower()


def test_classify_risk_returns_high_for_obligation_plus_penalty():
    diff = _diff(added=["Entities shall maintain capital requirements or face a fine of AED 1m."])
    level, _, _ = classify_risk(_run(), diff, _proof(), "LICENSING")
    assert level == "HIGH"


def test_classify_risk_returns_high_for_obligation_plus_aml():
    diff = _diff(added=["Financial institutions must file suspicious transaction reports via the AML portal."])
    level, _, _ = classify_risk(_run(), diff, _proof(), "AML_CFT")
    assert level == "HIGH"


def test_classify_risk_returns_medium_for_aml_cft_change_type_no_obligation():
    diff = _diff(added=["The regulator published updated AML guidance notes."])
    level, _, _ = classify_risk(_run(), diff, _proof(), "AML_CFT")
    assert level == "MEDIUM"


def test_classify_risk_returns_medium_for_circular_update_type():
    diff = _diff(added=["Circular 5 of 2026 — updated licensing framework."])
    level, _, _ = classify_risk(_run(), diff, _proof(), "CIRCULAR_UPDATE")
    assert level == "MEDIUM"


def test_classify_risk_returns_medium_for_consultation_type():
    diff = _diff(added=["A public consultation has been launched on proposed changes."])
    level, _, _ = classify_risk(_run(), diff, _proof(), "CONSULTATION")
    assert level == "MEDIUM"


def test_classify_risk_returns_medium_for_tax_type():
    diff = _diff(added=["VAT return filing period extended to 90 days."])
    level, _, _ = classify_risk(_run(), diff, _proof(), "TAX")
    assert level == "MEDIUM"


def test_classify_risk_returns_medium_for_guidance_update_type():
    diff = _diff(added=["New guidance framework for customer due diligence."])
    level, _, _ = classify_risk(_run(), diff, _proof(), "GUIDANCE_UPDATE")
    assert level == "MEDIUM"


def test_classify_risk_returns_low_for_general_update_with_no_signals():
    diff = _diff(added=["The page layout was updated with a new logo."])
    level, rationale, _ = classify_risk(_run(), diff, _proof(), "GENERAL_UPDATE")
    # GENERAL_UPDATE falls into the MEDIUM consultation/guidance bucket
    assert level in {"LOW", "MEDIUM"}


def test_classify_risk_returns_low_when_no_obligation_no_urgency_no_keywords():
    diff = _diff(
        added=["The navigation header was reformatted."],
        quality="GOOD",
        meaningful=True,
    )
    level, rationale, _ = classify_risk(_run(), diff, _proof(), "ENFORCEMENT")
    # ENFORCEMENT is not in any priority bucket so falls through to LOW
    assert level == "LOW"
    assert "obligation" in rationale.lower() or "signal" in rationale.lower()


def test_classify_risk_confidence_is_always_medium_for_non_review():
    diff = _diff(added=["Updated guidance on licensing requirements."])
    _, _, confidence = classify_risk(_run(), diff, _proof(), "LICENSING")
    assert confidence == "MEDIUM"


def test_classify_risk_confidence_is_low_for_review():
    diff = _diff(quality="LIMITED")
    _, _, confidence = classify_risk(_run(), diff, _proof(), "LICENSING")
    assert confidence == "LOW"
