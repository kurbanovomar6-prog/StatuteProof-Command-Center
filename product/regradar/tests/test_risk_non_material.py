"""Tests for risk.py NON_MATERIAL tier — Feature 3."""

from __future__ import annotations

from app.risk import analyze_risk, is_non_material


def _diff(added: str = "", removed: str = "", has_changes: bool = True, changed: bool = True) -> dict:
    """Helper to build a diff_result dict."""
    return {
        "has_changes": has_changes,
        "changed": changed,
        "added": [added] if added else [],
        "removed": [removed] if removed else [],
    }


# ── Test 1: tiny whitespace diff → NON_MATERIAL ───────────────────────────────

def test_tiny_whitespace_diff_is_non_material():
    """A small whitespace-only change (< 80 chars, no keywords) must be NON_MATERIAL."""
    diff = _diff(added="   ", removed=" ")
    assert is_non_material(diff) is True


# ── Test 2: small diff with "deadline" keyword → NOT NON_MATERIAL ─────────────

def test_diff_with_deadline_keyword_not_non_material():
    """A small diff containing 'deadline' must NOT be classified NON_MATERIAL."""
    diff = _diff(added="new deadline applies", removed="old deadline")
    assert is_non_material(diff) is False


# ── Test 3: small diff with "mandatory" keyword → NOT NON_MATERIAL ────────────

def test_diff_with_mandatory_keyword_not_non_material():
    """A small diff containing 'mandatory' must NOT be classified NON_MATERIAL."""
    diff = _diff(added="mandatory requirement", removed="requirement")
    assert is_non_material(diff) is False


# ── Test 4: diff >= 80 chars, no keywords → NOT NON_MATERIAL ──────────────────

def test_large_diff_without_keywords_not_non_material():
    """A diff >= 80 net chars (no keywords) must NOT be NON_MATERIAL — should score LOW."""
    long_added = "a" * 100
    long_removed = "b" * 5
    diff = _diff(added=long_added, removed=long_removed)
    assert is_non_material(diff) is False
    result = analyze_risk(diff)
    assert result["risk_level"] in {"LOW", "MEDIUM", "HIGH"}


# ── Test 5: analyze_risk returns NON_MATERIAL for pure whitespace ──────────────

def test_analyze_risk_returns_non_material_for_whitespace():
    """analyze_risk must return risk_level='NON_MATERIAL' for a tiny whitespace change."""
    diff = _diff(added="  \n  ", removed=" ")
    result = analyze_risk(diff)
    assert result["risk_level"] == "NON_MATERIAL"
    assert result.get("non_material") is True


# ── Test 6: is_non_material returns False when no added/removed fields ─────────

def test_is_non_material_false_when_no_text_fields():
    """is_non_material must return False (conservative) when added/removed are absent."""
    diff = {"has_changes": True, "changed": True}  # no added/removed keys
    assert is_non_material(diff) is False
