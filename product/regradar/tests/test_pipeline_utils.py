"""
Tests for pure utility functions in pipeline.py and text_normalization.py.

Covers:
- _extraction_quality()  — internal pipeline utility
- reset_ai_call_counter() — stateful budget reset
- normalize_for_change_hash() — full coverage of normalization paths
- stable_content_hash() — hash determinism and edge cases
- stable_normalized_hash() — combined normalize + hash

No network, no DB, no file system writes (tmp_path used where needed).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

# Pipeline internals
from app.pipeline import _extraction_quality, reset_ai_call_counter, _AI_RUN_BUDGET

# Text normalization
from app.text_normalization import (
    normalize_for_change_hash,
    stable_content_hash,
    stable_normalized_hash,
)


# ── _extraction_quality ───────────────────────────────────────────────────────

def test_extraction_quality_returns_good_for_500_or_more_chars():
    assert _extraction_quality(500) == "good"
    assert _extraction_quality(1000) == "good"
    assert _extraction_quality(100_000) == "good"


def test_extraction_quality_returns_low_content_for_1_to_499_chars():
    assert _extraction_quality(1) == "low_content"
    assert _extraction_quality(100) == "low_content"
    assert _extraction_quality(499) == "low_content"


def test_extraction_quality_returns_failed_for_zero_chars():
    assert _extraction_quality(0) == "failed"


# ── reset_ai_call_counter ─────────────────────────────────────────────────────

def test_reset_ai_call_counter_sets_count_to_zero():
    _AI_RUN_BUDGET["count"] = 99
    reset_ai_call_counter(limit=10)
    assert _AI_RUN_BUDGET["count"] == 0


def test_reset_ai_call_counter_sets_custom_limit():
    reset_ai_call_counter(limit=5)
    assert _AI_RUN_BUDGET["limit"] == 5


def test_reset_ai_call_counter_uses_configured_default_when_limit_is_none():
    from app.config import AI_MAX_CALLS_PER_RUN
    reset_ai_call_counter(limit=None)
    assert _AI_RUN_BUDGET["limit"] == AI_MAX_CALLS_PER_RUN
    assert _AI_RUN_BUDGET["count"] == 0


# ── normalize_for_change_hash ─────────────────────────────────────────────────

def test_normalize_returns_empty_string_for_empty_input():
    assert normalize_for_change_hash("") == ""


def test_normalize_removes_boilerplate_navigation_words():
    text = "Home\nSearch\nPrivacy Policy\nActual regulatory text about AML compliance requirements."
    result = normalize_for_change_hash(text)
    assert "Home" not in result
    assert "AML compliance" in result


def test_normalize_removes_accept_cookies_line():
    text = "Accept\nAccept All\nThe regulatory update requires all firms to register."
    result = normalize_for_change_hash(text)
    assert "Accept" not in result
    assert "regulatory update" in result


def test_normalize_removes_volatile_generated_at_timestamps():
    text = "Page generated at 2026-06-23 10:00:00\nCircular 5 of 2026 has been published."
    result = normalize_for_change_hash(text)
    assert "generated at" not in result.lower()
    assert "Circular 5" in result


def test_normalize_removes_duplicate_repeated_lines():
    text = "Subscribe to our newsletter\nOfficial circular text.\nSubscribe to our newsletter"
    result = normalize_for_change_hash(text)
    assert result.count("Official circular") == 1


def test_normalize_handles_html_entities():
    text = "Financial institutions &amp; payment providers must comply."
    result = normalize_for_change_hash(text)
    assert "&amp;" not in result
    assert "Financial institutions & payment providers" in result


def test_normalize_collapses_extra_blank_lines():
    text = "Line one.\n\n\n\n\nLine two."
    result = normalize_for_change_hash(text)
    assert "\n\n\n" not in result


def test_normalize_preserves_regulatory_obligation_text():
    obligation = "Licensed firms shall maintain a capital buffer of no less than AED 10 million."
    result = normalize_for_change_hash(obligation)
    assert "capital buffer" in result
    assert "AED 10 million" in result


def test_normalize_removes_arabic_visitor_count_fragment():
    text = "عدد الزوار : 12,345\nالتشريعات المالية الرئيسية تتطلب الامتثال."
    result = normalize_for_change_hash(text)
    assert "عدد الزوار" not in result


def test_normalize_preserves_arabic_regulatory_text():
    text = "يلتزم المرخص لهم بالإفصاح عن أي تغييرات جوهرية في هيكل الملكية."
    result = normalize_for_change_hash(text)
    assert "يلتزم" in result


def test_normalize_is_idempotent():
    text = "Licensed firms must submit annual compliance reports by 31 March each year."
    first = normalize_for_change_hash(text)
    second = normalize_for_change_hash(first)
    assert first == second


def test_normalize_removes_time_only_lines():
    text = "10:30 AM\nThe rulebook update is effective immediately."
    result = normalize_for_change_hash(text)
    # time-only line should be dropped
    assert "10:30" not in result
    assert "rulebook update" in result


def test_normalize_keeps_date_lines_with_publication_keywords():
    text = "Published: 15 June 2026\nCircular on AML reporting obligations."
    result = normalize_for_change_hash(text)
    # "Published:" triggers _DATE_WORD_RE — line should survive
    assert "2026" in result


# ── stable_content_hash ───────────────────────────────────────────────────────

def test_stable_content_hash_returns_64_char_hex_string():
    h = stable_content_hash("Some regulatory text.")
    assert h is not None
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_stable_content_hash_is_deterministic():
    text = "Financial institutions must comply with AML/CFT obligations."
    assert stable_content_hash(text) == stable_content_hash(text)


def test_stable_content_hash_differs_for_different_text():
    h1 = stable_content_hash("AML obligations updated.")
    h2 = stable_content_hash("AML obligations unchanged.")
    assert h1 != h2


def test_stable_content_hash_returns_none_for_empty_string():
    assert stable_content_hash("") is None


def test_stable_content_hash_returns_none_for_whitespace_only():
    assert stable_content_hash("   \n\t  ") is None


def test_stable_content_hash_is_insensitive_to_whitespace_differences():
    h1 = stable_content_hash("AML  obligations\nupdated.")
    h2 = stable_content_hash("AML obligations updated.")
    assert h1 == h2


def test_stable_content_hash_handles_very_long_text():
    long_text = "Regulatory obligation. " * 10_000
    h = stable_content_hash(long_text)
    assert h is not None
    assert len(h) == 64


# ── stable_normalized_hash ────────────────────────────────────────────────────

def test_stable_normalized_hash_returns_hex_string_for_real_text():
    h = stable_normalized_hash("AML reporting obligations for licensed firms.")
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_stable_normalized_hash_returns_empty_string_for_empty_input():
    assert stable_normalized_hash("") == ""


def test_stable_normalized_hash_returns_empty_string_for_boilerplate_only():
    # After normalization all boilerplate is stripped, leaving nothing
    text = "Home\nSearch\nAccept\nBack to top"
    result = stable_normalized_hash(text)
    assert result == ""


def test_stable_normalized_hash_is_stable_for_same_content_different_whitespace():
    text1 = "Financial  firms  shall maintain capital buffers."
    text2 = "Financial firms shall maintain capital buffers."
    # Both normalize to same result so hashes match
    assert stable_normalized_hash(text1) == stable_normalized_hash(text2)
