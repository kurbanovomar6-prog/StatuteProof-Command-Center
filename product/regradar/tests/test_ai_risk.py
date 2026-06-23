"""
Tests for pure utility functions in app/ai.py:
  - derive_urgency_from_text(text)
  - parse_action_steps(text)

No AI API calls, no network, no mocking — all functions are pure local logic.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from app.ai import derive_urgency_from_text, parse_action_steps


# ── derive_urgency_from_text ──────────────────────────────────────────────────

def test_derive_urgency_returns_monitor_for_empty_string():
    assert derive_urgency_from_text("") == "MONITOR"


def test_derive_urgency_returns_monitor_for_none_like_empty():
    # Function accepts str; empty string is the falsy case
    assert derive_urgency_from_text("") == "MONITOR"


def test_derive_urgency_returns_monitor_for_text_with_no_deadline_signals():
    text = "The regulator published updated guidance on customer due diligence."
    assert derive_urgency_from_text(text) == "MONITOR"


def test_derive_urgency_returns_immediate_for_effective_from_with_date():
    text = "The new requirements are effective from 01/07/2026."
    assert derive_urgency_from_text(text) == "IMMEDIATE"


def test_derive_urgency_returns_immediate_for_effective_as_of_iso_date():
    text = "The rule change is effective as of 2026-07-01."
    assert derive_urgency_from_text(text) == "IMMEDIATE"


def test_derive_urgency_returns_immediate_for_effective_on_date():
    text = "This circular is effective on 15/06/2026 for all licensed entities."
    assert derive_urgency_from_text(text) == "IMMEDIATE"


def test_derive_urgency_returns_within_30_days_for_within_n_days():
    text = "Firms must submit the return within 30 days of receipt."
    assert derive_urgency_from_text(text) == "WITHIN_30_DAYS"


def test_derive_urgency_returns_within_30_days_for_no_later_than():
    text = "The filing must be completed no later than the end of the quarter."
    assert derive_urgency_from_text(text) == "WITHIN_30_DAYS"


def test_derive_urgency_returns_within_30_days_for_by_month_year():
    text = "Entities must register by September 2026 with the relevant authority."
    assert derive_urgency_from_text(text) == "WITHIN_30_DAYS"


def test_derive_urgency_case_insensitive_for_effective_from():
    text = "EFFECTIVE FROM 2026-12-31 — all firms must comply."
    assert derive_urgency_from_text(text) == "IMMEDIATE"


def test_derive_urgency_returns_monitor_for_aml_text_without_deadline():
    text = "AML procedures should be reviewed regularly by compliance teams."
    assert derive_urgency_from_text(text) == "MONITOR"


def test_derive_urgency_prefers_immediate_when_effective_from_appears_first():
    # effective from pattern appears before a "by month year" pattern
    text = "Effective from 01/01/2027. Also note the filing by March 2027."
    result = derive_urgency_from_text(text)
    # The first pattern match wins
    assert result == "IMMEDIATE"


# ── parse_action_steps ────────────────────────────────────────────────────────

def test_parse_action_steps_returns_empty_list_for_empty_string():
    assert parse_action_steps("") == []


def test_parse_action_steps_returns_empty_list_for_whitespace_only():
    assert parse_action_steps("   \n  \t  ") == []


def test_parse_action_steps_splits_numbered_list():
    text = "1. Review Article 7(2)\n2. Update your AML policy\n3. Notify the MLRO"
    steps = parse_action_steps(text)
    assert len(steps) == 3
    assert any("Article 7" in s for s in steps)
    assert any("AML policy" in s for s in steps)
    assert any("MLRO" in s for s in steps)


def test_parse_action_steps_splits_bullet_list_with_dash():
    text = "- Review Article 7\n- Update policy\n- Notify counsel"
    steps = parse_action_steps(text)
    assert len(steps) >= 2
    assert all(isinstance(s, str) and s.strip() for s in steps)


def test_parse_action_steps_splits_bullet_list_with_bullet_character():
    text = "• First action\n• Second action\n• Third action"
    steps = parse_action_steps(text)
    assert len(steps) >= 2


def test_parse_action_steps_handles_plain_sentence_as_single_item():
    text = "Review the circular against internal AML policy before your next compliance review."
    steps = parse_action_steps(text)
    assert len(steps) == 1
    assert "AML policy" in steps[0]


def test_parse_action_steps_returns_list_of_strings():
    text = "1. Do something\n2. Do another thing"
    steps = parse_action_steps(text)
    assert all(isinstance(s, str) for s in steps)


def test_parse_action_steps_strips_whitespace_from_items():
    text = "1.   Padded step one   \n2.   Padded step two   "
    steps = parse_action_steps(text)
    for step in steps:
        assert step == step.strip()


def test_parse_action_steps_handles_newline_separated_items_without_bullets():
    text = "Step one\nStep two\nStep three"
    steps = parse_action_steps(text)
    assert len(steps) >= 2


def test_parse_action_steps_does_not_include_empty_items():
    text = "1. Real step\n\n\n2. Another real step"
    steps = parse_action_steps(text)
    for step in steps:
        assert step.strip() != ""


def test_parse_action_steps_handles_period_numbered_list():
    text = "1. First\n2. Second\n3. Third"
    steps = parse_action_steps(text)
    assert len(steps) == 3


def test_parse_action_steps_handles_paren_numbered_list():
    text = "1) Review the rules\n2) Update compliance manual\n3) Report to MLRO"
    steps = parse_action_steps(text)
    assert len(steps) == 3


def test_parse_action_steps_never_raises_on_arbitrary_text():
    """parse_action_steps must not raise regardless of input content."""
    inputs = [
        "random text",
        "1. one item only",
        "- dash\n- another\n- third",
        "\n".join(["line"] * 100),
    ]
    for text in inputs:
        result = parse_action_steps(text)
        assert isinstance(result, list)
