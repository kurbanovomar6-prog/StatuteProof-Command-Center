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


# ── WARN-2: obligation-keyword check is WORD-BOUNDED, not raw substring ────────

def test_short_volatile_fragment_stays_non_material_ban_in_urban():
    """A short numeric fragment where "ban" only appears inside "urban" must
    stay NON_MATERIAL. Raw ``kw in combined_lower`` fired "ban" inside "urban"
    and falsely flagged the change material; _match_terms word-bounds it.
    """
    diff = _diff(added="urban district 4822", removed="urban district 4821")
    assert is_non_material(diff) is True
    result = analyze_risk(diff)
    assert result["risk_level"] == "NON_MATERIAL"
    assert result.get("non_material") is True


def test_standalone_ban_word_is_still_material():
    """A genuine standalone "ban" keyword must still block NON_MATERIAL."""
    diff = _diff(added="we ban this activity", removed="we allow this activity")
    assert is_non_material(diff) is False


# ── WARN-3: _edited_char_count short-circuits huge inputs without SequenceMatcher

def test_edited_char_count_short_circuits_large_input(monkeypatch):
    """A combined length far above the threshold returns 'material' without
    invoking SequenceMatcher (O(n·m) guard), while behaviour is unchanged.

    _edited_char_count does ``from difflib import SequenceMatcher`` at call
    time, so patching difflib.SequenceMatcher intercepts the expensive path.
    """
    import difflib

    import app.risk as risk_module

    called = {"seq": False}

    class _Tripwire(difflib.SequenceMatcher):  # type: ignore[misc]
        def __init__(self, *a, **k):
            called["seq"] = True
            super().__init__(*a, **k)

    monkeypatch.setattr(difflib, "SequenceMatcher", _Tripwire)

    # Combined length > 4 * NON_MATERIAL_MAX_CHARS (80) → 400 chars.
    count = risk_module._edited_char_count("", "x" * 400)
    assert count >= risk_module.NON_MATERIAL_MAX_CHARS
    assert called["seq"] is False  # matcher never constructed


def test_edited_char_count_small_input_uses_exact_diff(monkeypatch):
    """Small/borderline inputs still run the exact character-level diff."""
    import difflib

    import app.risk as risk_module

    called = {"seq": False}

    class _Spy(difflib.SequenceMatcher):  # type: ignore[misc]
        def __init__(self, *a, **k):
            called["seq"] = True
            super().__init__(*a, **k)

    monkeypatch.setattr(difflib, "SequenceMatcher", _Spy)
    # A same-length swap well under 4× threshold → exact diff must run.
    count = risk_module._edited_char_count("allowance", "restriction")
    assert count > 0
    assert called["seq"] is True


# ── WARN-4 (i): a static obligation-keyword sentence elsewhere in an otherwise
#               unrelated edit must NOT escalate to a false HIGH ───────────────

def test_untouched_obligation_sentence_does_not_cause_false_high():
    """An unrelated edit to a paragraph that ALSO contains a static, untouched
    obligation-keyword sentence must not FALSELY escalate to HIGH.

    Delta-only scoring (``_delta_scoring_text``) preserves a lone obligation
    keyword from an equal span (so a real "penalty ... AED 50000" change is not
    lost), which lands at MEDIUM — never HIGH — because HIGH requires two
    strong keywords or one strong keyword plus a *distinct* context term, and a
    static single-keyword sentence with an unrelated numeric edit supplies
    neither. This guards against the static sentence self-confirming into HIGH.
    """
    static = "The penalty for non-compliance is set out in section 12. "
    diff = _diff(
        added=static + "Office hours are now 9am to 6pm on weekdays.",
        removed=static + "Office hours are now 9am to 5pm on weekdays.",
    )
    result = analyze_risk(diff)
    assert result["risk_level"] != "HIGH", result


# ── WARN-4 (ii): a page whose only diff is a short volatile fragment stays
#                NON_MATERIAL through analyze_risk (not merely has_changes) ────

def test_short_volatile_only_diff_stays_non_material_end_to_end():
    """The full analyze_risk path (not just has_changes) must return
    NON_MATERIAL when the sole change is a short volatile numeric fragment.
    """
    diff = _diff(added="Reference no. 4822", removed="Reference no. 4821")
    result = analyze_risk(diff)
    assert result["risk_level"] == "NON_MATERIAL"
    assert result.get("non_material") is True
