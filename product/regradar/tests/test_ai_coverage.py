"""
Behavioural coverage for app/ai.py — the semantic risk-scoring / classification
layer that assigns risk_level + confidence to regulatory alerts.

Focus is the DETERMINISTIC logic that a wrong output would push to a customer:

  * _truncate_paras           — prompt-assembly input shaping (cap + count)
  * _parse_response           — risk normalisation, confidence float parse/clamp,
                                review-gating (conf<0.75 OR HIGH), urgency enum
                                normalisation, semantic_findings coercion, and
                                the v13 safe-default fields
  * analyze_change_with_ai    — key/import gating, the fake-LLM success path,
                                error handling (auth + generic), and the regex
                                urgency fallback

All network / LLM I/O is faked via a stub `anthropic` module installed into
sys.modules — no live endpoint or real model is ever contacted.
"""
from __future__ import annotations

import sys
import types as _pytypes
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from app import ai
from app.ai import _parse_response, _truncate_paras, analyze_change_with_ai


# ---------------------------------------------------------------------------
# Fake anthropic client — installed into sys.modules so the function-local
# `import anthropic` inside analyze_change_with_ai picks it up. Mirrors the
# pattern already used in tests/test_ai_brief.py.
# ---------------------------------------------------------------------------
class _TextBlock:
    def __init__(self, text: str) -> None:
        self.text = text


class _NonTextBlock:
    """A content block that is NOT a TextBlock (e.g. a tool_use block)."""


class _AuthenticationError(Exception):
    pass


def _make_fake_anthropic(spec):
    """
    spec is one of:
      - str                -> messages.create returns one TextBlock(text)
      - Exception instance -> messages.create raises it
      - [block, ...]       -> messages.create returns those content blocks verbatim
    """

    class _Msg:
        def __init__(self, blocks) -> None:
            self.content = blocks

    class _Messages:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        def create(self, **kwargs):
            self.calls.append(kwargs)
            if isinstance(spec, Exception):
                raise spec
            if isinstance(spec, list):
                return _Msg(spec)
            return _Msg([_TextBlock(spec)])

    messages = _Messages()

    class _Anthropic:
        def __init__(self, api_key=None) -> None:
            self.messages = messages

    fake = _pytypes.ModuleType("anthropic")
    fake.Anthropic = _Anthropic
    fake.AuthenticationError = _AuthenticationError
    fake.types = _pytypes.SimpleNamespace(TextBlock=_TextBlock)
    fake._messages = messages
    return fake


@pytest.fixture
def ai_enabled(monkeypatch):
    """Provide a dummy key + install a fake anthropic response. Returns installer."""
    monkeypatch.setattr("app.ai.ANTHROPIC_API_KEY", "sk-test-dummy", raising=False)

    def install(spec):
        fake = _make_fake_anthropic(spec)
        monkeypatch.setitem(sys.modules, "anthropic", fake)
        return fake

    return install


def _valid_json(**overrides) -> str:
    import json

    payload = {
        "risk_level": "MEDIUM",
        "executive_summary": "The rulebook article on reporting was clarified.",
        "confidence": 0.82,
        "urgency": "WITHIN_90_DAYS",
        "materiality": "MATERIAL",
        "legal_area": "AML/CFT",
        "jurisdiction": "UAE",
        "semantic_findings": {
            "new_obligation": True,
            "deadline_detected": False,
            "reporting_required": True,
            "licensing_impact": False,
            "enforcement_exposure": False,
            "operational_impact": "medium",
            "materiality": "material",
        },
        "affected_entities": ["DFSA authorised firm"],
        "recommendations": [
            "Consider reviewing the change before your next compliance review.",
            "Your compliance team may wish to assess impact with your MLRO.",
            "It would be prudent to preserve the diff before your next review.",
        ],
        "affected_licence_types": ["VASP"],
        "what_to_do": "1. Review Article 7 before your next compliance review.",
        "review_required": False,
        "review_reason": "",
    }
    payload.update(overrides)
    return json.dumps(payload)


# ===========================================================================
# _truncate_paras
# ===========================================================================
class TestTruncateParas:
    def test_empty_list_returns_none_marker(self):
        assert _truncate_paras([]) == "(none)"

    def test_numbers_each_paragraph(self):
        out = _truncate_paras(["alpha", "beta"])
        assert out == "1. alpha\n2. beta"

    def test_long_paragraph_capped_with_ellipsis(self):
        long_para = "x" * 500
        out = _truncate_paras([long_para])
        # capped to _MAX_PARA_LEN chars + "..."
        assert out == "1. " + "x" * ai._MAX_PARA_LEN + "..."
        assert len(out) == len("1. ") + ai._MAX_PARA_LEN + 3

    def test_short_paragraph_not_ellipsised(self):
        out = _truncate_paras(["short"])
        assert "..." not in out

    def test_caps_paragraph_count_at_max(self):
        paras = [f"p{i}" for i in range(ai._MAX_PARAS + 10)]
        out = _truncate_paras(paras)
        lines = out.splitlines()
        assert len(lines) == ai._MAX_PARAS
        # last kept line is the _MAX_PARAS-th paragraph (1-indexed)
        assert lines[-1].startswith(f"{ai._MAX_PARAS}. ")


# ===========================================================================
# _parse_response — risk / confidence / gating / normalisation
# ===========================================================================
class TestParseResponseCore:
    def test_valid_json_roundtrips(self):
        parsed = _parse_response(_valid_json())
        assert parsed is not None
        assert parsed["risk_level"] == "MEDIUM"
        assert parsed["confidence"] == pytest.approx(0.82)

    def test_invalid_json_returns_none(self):
        assert _parse_response("not json at all") is None

    def test_empty_string_returns_none(self):
        assert _parse_response("") is None

    def test_strips_json_fence(self):
        parsed = _parse_response("```json\n" + _valid_json(risk_level="HIGH") + "\n```")
        assert parsed is not None
        assert parsed["risk_level"] == "HIGH"

    def test_strips_bare_fence(self):
        parsed = _parse_response("```\n" + _valid_json(risk_level="LOW") + "\n```")
        assert parsed["risk_level"] == "LOW"

    def test_unknown_risk_coerced_to_low(self):
        assert _parse_response(_valid_json(risk_level="CRITICAL"))["risk_level"] == "LOW"

    def test_lowercase_risk_uppercased(self):
        assert _parse_response(_valid_json(risk_level="high"))["risk_level"] == "HIGH"

    def test_missing_risk_defaults_low(self):
        import json

        assert _parse_response(json.dumps({}))["risk_level"] == "LOW"


class TestParseResponseConfidence:
    def test_float_preserved(self):
        assert _parse_response(_valid_json(confidence=0.42))["confidence"] == pytest.approx(0.42)

    def test_float_string_parsed(self):
        assert _parse_response(_valid_json(confidence="0.31"))["confidence"] == pytest.approx(0.31)

    def test_above_one_clamped_to_one(self):
        assert _parse_response(_valid_json(confidence=5.0))["confidence"] == 1.0

    def test_below_zero_clamped_to_zero(self):
        assert _parse_response(_valid_json(confidence=-2.0))["confidence"] == 0.0

    def test_legacy_high_string_maps(self):
        assert _parse_response(_valid_json(confidence="high"))["confidence"] == 0.85

    def test_legacy_medium_string_maps(self):
        assert _parse_response(_valid_json(confidence="medium"))["confidence"] == 0.60

    def test_legacy_low_string_maps(self):
        assert _parse_response(_valid_json(confidence="low"))["confidence"] == 0.35

    def test_garbage_string_defaults_to_midpoint(self):
        assert _parse_response(_valid_json(confidence="banana"))["confidence"] == 0.5

    def test_none_confidence_defaults_to_midpoint(self):
        assert _parse_response(_valid_json(confidence=None))["confidence"] == 0.5


class TestParseResponseReviewGating:
    def test_low_confidence_forces_review(self):
        parsed = _parse_response(_valid_json(risk_level="LOW", confidence=0.5, review_required=False))
        assert parsed["review_required"] is True
        assert "below 0.75 threshold" in parsed["review_reason"]

    def test_high_risk_forces_review_even_at_high_confidence(self):
        parsed = _parse_response(_valid_json(risk_level="HIGH", confidence=0.99, review_required=False))
        assert parsed["review_required"] is True
        assert "HIGH risk classification" in parsed["review_reason"]

    def test_low_risk_high_confidence_no_forced_review(self):
        parsed = _parse_response(_valid_json(risk_level="LOW", confidence=0.9, review_required=False))
        assert parsed["review_required"] is False
        assert parsed["review_reason"] == ""

    def test_ai_requested_review_respected(self):
        parsed = _parse_response(
            _valid_json(risk_level="LOW", confidence=0.9, review_required=True, review_reason="analyst flag")
        )
        assert parsed["review_required"] is True
        assert "analyst flag" in parsed["review_reason"]

    def test_review_reason_combines_confidence_and_high_risk(self):
        parsed = _parse_response(_valid_json(risk_level="HIGH", confidence=0.5))
        assert "below 0.75 threshold" in parsed["review_reason"]
        assert "HIGH risk classification" in parsed["review_reason"]


class TestParseResponseSemanticFindings:
    def test_non_dict_replaced_with_defaults(self):
        sf = _parse_response(_valid_json(semantic_findings="broken"))["semantic_findings"]
        assert sf["new_obligation"] is False
        assert sf["operational_impact"] == "none"
        assert sf["materiality"] == "informational"

    def test_bool_coercion_of_truthy_values(self):
        sf = _parse_response(
            _valid_json(
                semantic_findings={
                    "new_obligation": 1,
                    "deadline_detected": 0,
                    "reporting_required": "yes",
                }
            )
        )["semantic_findings"]
        assert sf["new_obligation"] is True
        assert sf["deadline_detected"] is False
        assert sf["reporting_required"] is True

    def test_invalid_operational_impact_falls_back(self):
        sf = _parse_response(
            _valid_json(semantic_findings={"operational_impact": "SEVERE"})
        )["semantic_findings"]
        assert sf["operational_impact"] == "none"

    def test_invalid_findings_materiality_falls_back(self):
        sf = _parse_response(
            _valid_json(semantic_findings={"materiality": "nonsense"})
        )["semantic_findings"]
        assert sf["materiality"] == "informational"

    def test_valid_enum_values_preserved(self):
        sf = _parse_response(
            _valid_json(semantic_findings={"operational_impact": "high", "materiality": "critical"})
        )["semantic_findings"]
        assert sf["operational_impact"] == "high"
        assert sf["materiality"] == "critical"


class TestParseResponseUrgency:
    def test_valid_enum_preserved(self):
        assert _parse_response(_valid_json(urgency="IMMEDIATE"))["urgency"] == "IMMEDIATE"

    def test_legacy_high_maps_to_immediate(self):
        assert _parse_response(_valid_json(urgency="HIGH"))["urgency"] == "IMMEDIATE"

    def test_legacy_medium_maps_to_within_90(self):
        assert _parse_response(_valid_json(urgency="MEDIUM"))["urgency"] == "WITHIN_90_DAYS"

    def test_legacy_low_maps_to_monitor(self):
        assert _parse_response(_valid_json(urgency="LOW"))["urgency"] == "MONITOR"

    def test_unknown_urgency_defaults_to_monitor(self):
        assert _parse_response(_valid_json(urgency="SOMEDAY"))["urgency"] == "MONITOR"


class TestParseResponseV13Defaults:
    def test_missing_v13_text_fields_get_defaults(self):
        import json

        parsed = _parse_response(json.dumps({"risk_level": "LOW"}))
        assert parsed["what_changed"] == "No change description provided."
        assert parsed["why_it_matters"].startswith("Impact on regulated firms")
        assert parsed["risk_explanation"].startswith("Risk tier assigned")
        assert parsed["deadline_risk"] == "No explicit deadline in this diff."

    def test_top_level_materiality_valid_preserved(self):
        assert _parse_response(_valid_json(materiality="NON_MATERIAL"))["materiality"] == "NON_MATERIAL"

    def test_top_level_materiality_invalid_defaults_unclear(self):
        assert _parse_response(_valid_json(materiality="kinda"))["materiality"] == "UNCLEAR"

    def test_legal_area_and_jurisdiction_defaults(self):
        import json

        parsed = _parse_response(json.dumps({"risk_level": "LOW"}))
        assert parsed["legal_area"] == "Unknown"
        assert parsed["jurisdiction"] == "Unknown"

    def test_blank_legal_area_becomes_unknown(self):
        assert _parse_response(_valid_json(legal_area="   "))["legal_area"] == "Unknown"

    def test_blank_jurisdiction_becomes_unknown(self):
        assert _parse_response(_valid_json(jurisdiction=""))["jurisdiction"] == "Unknown"


class TestParseResponseActionSteps:
    def test_string_what_to_do_parsed_into_action_steps(self):
        parsed = _parse_response(
            _valid_json(what_to_do="1. Review Article 7\n2. Notify the MLRO")
        )
        assert parsed["action_steps"] == ["Review Article 7", "Notify the MLRO"]
        # original string form preserved
        assert "Review Article 7" in parsed["what_to_do"]

    def test_list_what_to_do_normalised(self):
        parsed = _parse_response(
            _valid_json(what_to_do=["  Step one  ", "", "Step two"])
        )
        assert parsed["action_steps"] == ["Step one", "Step two"]
        # list input is joined into the string form
        assert "Step one" in parsed["what_to_do"]

    def test_empty_what_to_do_gets_three_fallback_steps(self):
        parsed = _parse_response(_valid_json(what_to_do=""))
        assert len(parsed["action_steps"]) == 3
        assert all("compliance" in s.lower() or "diff" in s.lower() for s in parsed["action_steps"])


class TestParseResponseRecommendations:
    def test_non_list_padded_to_three(self):
        parsed = _parse_response(_valid_json(recommendations="not a list"))
        assert len(parsed["recommendations"]) == 3

    def test_short_list_padded_to_three(self):
        parsed = _parse_response(_valid_json(recommendations=["Only one rec."]))
        assert len(parsed["recommendations"]) == 3
        assert parsed["recommendations"][0] == "Only one rec."

    def test_long_list_trimmed_to_three(self):
        parsed = _parse_response(_valid_json(recommendations=["a", "b", "c", "d", "e"]))
        assert parsed["recommendations"] == ["a", "b", "c"]

    def test_empty_items_filtered_before_padding(self):
        parsed = _parse_response(_valid_json(recommendations=["real one", "", "   "]))
        assert len(parsed["recommendations"]) == 3
        assert parsed["recommendations"][0] == "real one"


class TestParseResponseLicenceTypes:
    def test_non_list_coerced_empty(self):
        assert _parse_response(_valid_json(affected_licence_types="VASP"))["affected_licence_types"] == []

    def test_empty_and_blank_items_filtered(self):
        parsed = _parse_response(_valid_json(affected_licence_types=["VASP", "", "  ", "CBUAE PI"]))
        assert parsed["affected_licence_types"] == ["VASP", "CBUAE PI"]


# ===========================================================================
# analyze_change_with_ai — gating, success, error handling, fallback
# ===========================================================================
DIFF = {"added": ["Some new obligation text."], "removed": []}
RULE = {"risk_level": "MEDIUM", "reason": "keyword scan"}


class TestAnalyzeGating:
    def test_no_api_key_returns_none(self, monkeypatch):
        monkeypatch.setattr("app.ai.ANTHROPIC_API_KEY", "", raising=False)
        assert analyze_change_with_ai("https://x", DIFF, RULE) is None

    def test_anthropic_not_installed_returns_none(self, monkeypatch):
        monkeypatch.setattr("app.ai.ANTHROPIC_API_KEY", "sk-x", raising=False)
        monkeypatch.setitem(sys.modules, "anthropic", None)  # import -> ImportError
        assert analyze_change_with_ai("https://x", DIFF, RULE) is None


class TestAnalyzeSuccessPath:
    def test_success_returns_normalised_dict(self, ai_enabled):
        ai_enabled(_valid_json())
        result = analyze_change_with_ai("https://x", DIFF, RULE)
        assert result is not None
        assert result["risk_level"] == "MEDIUM"
        assert result["confidence"] == pytest.approx(0.82)
        assert result["monitoring_disclaimer"] == ai._MONITORING_DISCLAIMER

    def test_success_fills_inherited_defaults(self, ai_enabled):
        import json

        ai_enabled(json.dumps({"risk_level": "LOW"}))
        result = analyze_change_with_ai("https://x", DIFF, RULE, source_language="ar", output_language="en")
        assert result["source_language"] == "ar"
        assert result["output_language"] == "en"
        assert result["affected_entities"] == []
        assert result["deadline"] is None

    def test_prompt_carries_diff_and_rule_context(self, ai_enabled):
        fake = ai_enabled(_valid_json())
        analyze_change_with_ai("https://reg.example/page", DIFF, RULE)
        sent = fake._messages.calls[0]["messages"][0]["content"]
        assert "https://reg.example/page" in sent
        assert "Some new obligation text." in sent
        assert "keyword scan" in sent

    def test_affected_entities_non_list_coerced(self, ai_enabled):
        ai_enabled(_valid_json(affected_entities="everyone"))
        result = analyze_change_with_ai("https://x", DIFF, RULE)
        assert result["affected_entities"] == []

    def test_deadline_null_string_normalised_to_none(self, ai_enabled):
        ai_enabled(_valid_json(deadline="null"))
        result = analyze_change_with_ai("https://x", DIFF, RULE)
        assert result["deadline"] is None

    def test_deadline_real_value_preserved(self, ai_enabled):
        ai_enabled(_valid_json(deadline="2026-07-01"))
        result = analyze_change_with_ai("https://x", DIFF, RULE)
        assert result["deadline"] == "2026-07-01"

    def test_non_text_first_block_yields_none(self, ai_enabled):
        # A non-TextBlock content block leaves raw="" -> _parse_response("") -> None
        ai_enabled([_NonTextBlock()])
        assert analyze_change_with_ai("https://x", DIFF, RULE) is None

    def test_unparseable_model_output_returns_none(self, ai_enabled):
        ai_enabled("this is not json")
        assert analyze_change_with_ai("https://x", DIFF, RULE) is None


class TestAnalyzeUrgencyFallback:
    def test_monitor_upgraded_via_regex_when_diff_has_deadline(self, ai_enabled):
        # AI says MONITOR, but the diff text itself contains "within 30 days".
        ai_enabled(_valid_json(urgency="MONITOR"))
        diff = {"added": ["Firms must file the return within 30 days of receipt."], "removed": []}
        result = analyze_change_with_ai("https://x", diff, RULE)
        assert result["urgency"] == "WITHIN_30_DAYS"

    def test_monitor_stays_monitor_when_no_deadline_signal(self, ai_enabled):
        ai_enabled(_valid_json(urgency="MONITOR"))
        diff = {"added": ["The regulator updated its website navigation menu."], "removed": []}
        result = analyze_change_with_ai("https://x", diff, RULE)
        assert result["urgency"] == "MONITOR"

    def test_immediate_not_downgraded_by_fallback(self, ai_enabled):
        ai_enabled(_valid_json(urgency="IMMEDIATE"))
        result = analyze_change_with_ai("https://x", DIFF, RULE)
        assert result["urgency"] == "IMMEDIATE"


class TestAnalyzeErrorHandling:
    def test_authentication_error_returns_none(self, ai_enabled):
        ai_enabled(_AuthenticationError("bad key"))
        assert analyze_change_with_ai("https://x", DIFF, RULE) is None

    def test_generic_exception_returns_none(self, ai_enabled):
        ai_enabled(RuntimeError("network exploded"))
        assert analyze_change_with_ai("https://x", DIFF, RULE) is None

    def test_never_raises_on_arbitrary_failure(self, ai_enabled):
        ai_enabled(ValueError("boom"))
        # must swallow and return None, never propagate
        assert analyze_change_with_ai("https://x", DIFF, RULE) is None
