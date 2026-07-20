"""Homoglyph folding is part of the forbidden-claims guard, not a nicety.

The ban list in CLAUDE.md is absolute, so a banned phrase must stay blocked when
an adversarial source spells one of its letters with a Cyrillic or Greek
lookalike ("we guarantεe compliance"). These tests are DATA-DRIVEN off
``_CONFUSABLE_FOLD``: every confusable in the table is substituted into every
banned phrase, one letter at a time. Adding a row to the table therefore
extends the coverage automatically, and a row that does not actually fold (the
Greek-epsilon bypass found on 2026-07-21) fails here.
"""

from __future__ import annotations

import pytest

from app.legal_safety import (
    BRIEF_EXTRA_PHRASES,
    FORBIDDEN_PHRASES,
    ForbiddenClaimError,
    _CONFUSABLE_FOLD,
    assert_no_forbidden_claims,
    contains_forbidden_claim,
)

# ASCII letter -> every confusable codepoint that must fold to it.
_BY_LATIN: dict[str, list[str]] = {}
for _cp, _latin in _CONFUSABLE_FOLD.items():
    _BY_LATIN.setdefault(str(_latin), []).append(chr(_cp))


def _substitutions(phrase: str) -> list[tuple[str, str, str]]:
    """(confusable, latin, mutated phrase) for every foldable letter position."""
    out: list[tuple[str, str, str]] = []
    for idx, ch in enumerate(phrase):
        for confusable in _BY_LATIN.get(ch, ()):
            out.append((confusable, ch, phrase[:idx] + confusable + phrase[idx + 1 :]))
    return out


_CANONICAL_CASES = [
    pytest.param(phrase, confusable, mutated, id=f"{phrase}-{ord(confusable):04X}-{idx}")
    for phrase in FORBIDDEN_PHRASES
    for idx, (confusable, _latin, mutated) in enumerate(_substitutions(phrase))
]

_BRIEF_CASES = [
    pytest.param(phrase, confusable, mutated, id=f"{phrase}-{ord(confusable):04X}-{idx}")
    for phrase in BRIEF_EXTRA_PHRASES
    for idx, (confusable, _latin, mutated) in enumerate(_substitutions(phrase))
]


def test_fold_table_is_non_trivial():
    """Guard against the table being emptied or the reverse index breaking."""
    assert len(_CONFUSABLE_FOLD) >= 20
    assert _CANONICAL_CASES, "no confusable covers any letter of the ban list"


def test_every_banned_letter_has_a_confusable_row():
    """Every ASCII letter used by the ban list should be foldable-to.

    Not every letter has a plausible Cyrillic/Greek lookalike, so this only
    asserts the letters we have deliberately covered stay covered — it records
    the audited set so a future edit cannot silently drop one.
    """
    covered = set(_BY_LATIN)
    assert {"a", "c", "e", "i", "l", "m", "o", "p", "r", "s", "t", "u", "v"} <= covered


@pytest.mark.parametrize("phrase,confusable,mutated", _CANONICAL_CASES)
def test_canonical_phrase_blocked_with_confusable(phrase, confusable, mutated):
    assert mutated != phrase
    with pytest.raises(ForbiddenClaimError):
        assert_no_forbidden_claims(f"StatuteProof will {mutated} for your firm.")


@pytest.mark.parametrize("phrase,confusable,mutated", _BRIEF_CASES)
def test_brief_extra_phrase_blocked_with_confusable(phrase, confusable, mutated):
    assert contains_forbidden_claim(
        f"This week: {mutated}.", phrases=BRIEF_EXTRA_PHRASES
    )


@pytest.mark.parametrize(
    "text",
    [
        "we guarantεe compliance",  # Greek small epsilon U+03B5
        "we guarantϵe compliance",  # Greek lunate epsilon symbol U+03F5
        "we guarantеe compliance",  # Cyrillic small ie U+0435
        "we guarantee сompliance",  # Cyrillic es U+0441
    ],
)
def test_known_homoglyph_bypasses_stay_blocked(text):
    with pytest.raises(ForbiddenClaimError):
        assert_no_forbidden_claims(text)


def test_uppercase_homoglyph_is_folded():
    """Case folding must not run before the confusable fold and lose coverage."""
    with pytest.raises(ForbiddenClaimError):
        assert_no_forbidden_claims("We GUARANTEE COMPLIANCE".replace("E", "Ε", 1))


def test_safe_text_still_passes():
    """The wider fold table must not start tripping on legitimate output."""
    assert_no_forbidden_claims(
        "StatuteProof monitors selected official sources and seals evidence "
        "records. Not legal advice and not a guarantee of compliance."
    )
