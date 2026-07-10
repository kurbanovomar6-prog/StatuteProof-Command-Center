"""G2-risk regression tests.

Covers three defects in the risk/diff scoring path:

  1. Delta-only scoring dropped a strong obligation keyword when it sat in the
     UNCHANGED part of a modified sentence, so a material penalty/fine change
     scored LOW with no alert (app/risk.py:_delta_scoring_text).

  2. is_non_material downgraded genuinely material changes because
     (a) net-change measured pure length delta, masking same-length swaps, and
     (b) restriction/licence were absent from _OBLIGATION_KEYWORDS
     (app/risk.py:is_non_material / _OBLIGATION_KEYWORDS).

  3. Sub-20-char paragraph changes were erased by the _MIN_FRAGMENT filter, so a
     real change reported has_changes=False and scored LOW with no alert
     (app/diff.py:get_diff / _parse_hunks).

Each test fails before the fix and passes after.
"""

from __future__ import annotations

from app.diff import get_diff
from app.risk import (
    _delta_scoring_text,
    _edited_char_count,
    analyze_risk,
    is_non_material,
)


def _diff(added, removed, has_changes: bool = True, changed: bool = True) -> dict:
    """Build a diff_result dict from added/removed lists (or strings)."""
    if isinstance(added, str):
        added = [added] if added else []
    if isinstance(removed, str):
        removed = [removed] if removed else []
    return {
        "has_changes": has_changes,
        "changed": changed,
        "added": list(added),
        "removed": list(removed),
    }


# ── Bug 1: delta scoring must not drop obligation keywords ────────────────────

def test_delta_scoring_preserves_obligation_keyword_in_unchanged_span():
    """A strong keyword common to both sides of a modified sentence survives."""
    added = ["The penalty for late filing is now AED 50000 effective immediately"]
    removed = ["The penalty for late filing is AED 10000"]
    delta = _delta_scoring_text(added, removed)
    assert "penalty" in delta.lower()


def test_material_penalty_increase_scores_above_low():
    """A 5x penalty increase made effective immediately must produce a signal."""
    diff = _diff(
        added=["The penalty for late filing is now AED 50000 effective immediately"],
        removed=["The penalty for late filing is AED 10000"],
    )
    result = analyze_risk(diff)
    assert result["risk_level"] in {"MEDIUM", "HIGH"}
    assert "penalty" in [k.lower() for k in result.get("matched_keywords", [])]


def test_delta_scoring_still_suppresses_unchanged_chrome():
    """Non-obligation words common to both sides stay dropped (chrome guard)."""
    added = ["Dubai Financial Services Authority home about news"]
    removed = ["Dubai Financial Services Authority home about contact"]
    delta = _delta_scoring_text(added, removed).lower()
    # Only the differing tail tokens survive; the shared title is suppressed.
    assert "authority" not in delta
    assert "news" in delta and "contact" in delta


# ── Bug 2: is_non_material must not downgrade material changes ─────────────────

def test_small_licence_restriction_is_material():
    """A short 'licence restriction' change must NOT be NON_MATERIAL."""
    diff = _diff(added=["New licence restriction applies now."], removed=[])
    assert is_non_material(diff) is False
    assert analyze_risk(diff)["risk_level"] in {"MEDIUM", "HIGH"}


def test_same_length_content_swap_is_material():
    """A same-length swap (allowance -> restriction) must NOT be NON_MATERIAL."""
    added = ["A" * 60 + " restriction " + "B" * 60]
    removed = ["A" * 60 + " allowance " + "B" * 60]
    diff = _diff(added=added, removed=removed)
    # Pure length delta is only ~2 chars; the fix must look at edited content.
    assert is_non_material(diff) is False
    assert analyze_risk(diff)["risk_level"] in {"MEDIUM", "HIGH"}


def test_large_same_length_swap_without_keywords_is_material():
    """A large same-length content swap (no keyword) is caught by edit size."""
    added = ["X" * 90]
    removed = ["Y" * 90]
    assert _edited_char_count("Y" * 90, "X" * 90) >= 80
    assert is_non_material(_diff(added=added, removed=removed)) is False


def test_whitespace_edit_remains_non_material():
    """The materiality fix must still treat pure whitespace edits as immaterial."""
    diff = _diff(added=["   "], removed=[" "])
    assert is_non_material(diff) is True


def test_restriction_and_licence_in_obligation_keywords():
    """restriction/licence are obligation keywords (materiality guard)."""
    from app.risk import _OBLIGATION_KEYWORDS

    assert "restriction" in _OBLIGATION_KEYWORDS
    assert "licence" in _OBLIGATION_KEYWORDS
    assert "license" in _OBLIGATION_KEYWORDS


# ── Bug 3: sub-20-char changes must stay visible ──────────────────────────────

def test_short_value_change_is_visible():
    """A short value change (Fee: 100 -> Fee: 999) must report has_changes=True."""
    result = get_diff("Fee: 100", "Fee: 999")
    assert result["has_changes"] is True
    assert result["added"] == ["Fee: 999"]
    assert result["removed"] == ["Fee: 100"]


def test_short_change_not_reported_as_no_change_by_risk():
    """analyze_risk on a short value change must not say 'No changes detected'."""
    result = analyze_risk(get_diff("Fee: 100", "Fee: 999"))
    assert result.get("reason") != "No changes detected"


def test_identical_text_still_reports_no_change():
    """The short-change fallback must not invent changes for identical text."""
    assert get_diff("same text here", "same text here")["has_changes"] is False


def test_whitespace_only_paragraphs_report_no_change():
    """Whitespace-only paragraph differences must not resurface as a change."""
    assert get_diff("  \n\n  ", "   \n\n   ")["has_changes"] is False


def test_substantial_fragment_path_unaffected():
    """When a substantial fragment survives, short lines stay filtered out."""
    old = "x\n\nThis is a substantial paragraph of regulatory text that is long."
    new = "y\n\nThis is a substantial paragraph of regulatory text that changed now."
    result = get_diff(old, new)
    joined = " ".join(result["added"] + result["removed"])
    # Short 'x'/'y' fragments filtered; only the long paragraph pair remains.
    assert "substantial paragraph" in joined
    assert result["added"] == [
        "This is a substantial paragraph of regulatory text that changed now."
    ]
    assert result["removed"] == [
        "This is a substantial paragraph of regulatory text that is long."
    ]
