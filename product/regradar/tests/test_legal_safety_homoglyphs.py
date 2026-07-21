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
    find_forbidden_claims,
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


# ══════════════════════════════════════════════════════════════════════════
# Inflection coverage — the ban list is a CLAIM list, not a spelling list
# ══════════════════════════════════════════════════════════════════════════
# A flat literal-substring list blocks "we guarantee compliance" but lets
# "StatuteProof guarantees compliance" through — the way a marketer actually
# writes it. No adversarial crafting required, so this is the wider hole.

_INFLECTED_CLAIMS = [
    "StatuteProof guarantees compliance for your firm.",
    "StatuteProof is guaranteeing compliance for your firm.",
    "StatuteProof guaranteed compliance last quarter.",
    "StatuteProof prevents fines.",
    "StatuteProof is preventing fines.",
    "StatuteProof prevented fines for this client.",
    "StatuteProof replaces lawyers.",
    "StatuteProof is replacing lawyers.",
    "StatuteProof provided legal advice on this change.",
    "StatuteProof never misses an update.",
    "StatuteProof is never missing an update.",
    "We are official partners of the regulator.",
    "StatuteProof avoids all penalties.",
    "Ask our AI lawyers about it.",
]


@pytest.mark.parametrize("text", _INFLECTED_CLAIMS)
def test_inflected_forbidden_claim_is_blocked(text):
    with pytest.raises(ForbiddenClaimError):
        assert_no_forbidden_claims(text)


_INFLECTED_BRIEF_CLAIMS = [
    "This week: this ensures you are compliant.",
    "This week: you will be compliant.",
    "This week: no actions needed.",
]


@pytest.mark.parametrize("text", _INFLECTED_BRIEF_CLAIMS)
def test_inflected_brief_extra_claim_is_blocked(text):
    assert contains_forbidden_claim(text, phrases=BRIEF_EXTRA_PHRASES)


# The denial-anchored disclaimer neutralization is load-bearing: honest denials
# must stay allowed for EVERY inflection the guard now understands.
_HONEST_DENIALS = [
    "StatuteProof does not guarantee compliance.",
    "StatuteProof does not guarantee compliance, prevent fines, or certify "
    "that all regulatory updates have been captured.",
    "We cannot prevent fines and we do not replace lawyers.",
    "Not legal advice and not a guarantee of compliance.",
    "StatuteProof is not a guarantee of compliance.",
    "Firms should seek independent legal advice.",
    "StatuteProof does not replace lawyers or compliance professionals.",
]


@pytest.mark.parametrize("text", _HONEST_DENIALS)
def test_honest_denial_is_not_blocked(text):
    assert_no_forbidden_claims(text)
    assert find_forbidden_claims(text) == []


# ══════════════════════════════════════════════════════════════════════════
# Guard parity — every delivery path must block the SAME corpus
# ══════════════════════════════════════════════════════════════════════════
# app.change_register.assert_no_forbidden_claims used to be an independent
# lower()+substring scan, so the deadline-reminder and digest delivery paths
# (which import it) were not protected by the whitespace-collapse or homoglyph
# folding at all. There must be exactly ONE implementation.

_PARITY_CORPUS = [
    pytest.param("We guarantee compliance.", id="plain"),
    pytest.param("StatuteProof guarantees compliance.", id="inflected"),
    pytest.param("We guarantee\ncompliance.", id="line-wrapped"),
    pytest.param("We guarantεe compliance.", id="homoglyph"),
    pytest.param("WE GUARANTEE COMPLIANCE.", id="upper"),
    pytest.param("AI\nlawyer", id="wrapped-ai-lawyer"),
    pytest.param("StatuteProof GUARANTEES\ncomplianсe.", id="mixed"),
]


@pytest.mark.parametrize("text", _PARITY_CORPUS)
def test_legal_safety_guard_blocks_corpus(text):
    with pytest.raises(ForbiddenClaimError):
        assert_no_forbidden_claims(text)


@pytest.mark.parametrize("text", _PARITY_CORPUS)
def test_change_register_guard_blocks_corpus(text):
    from app.change_register import ChangeRegisterError
    from app.change_register import assert_no_forbidden_claims as cr_guard

    with pytest.raises(ChangeRegisterError):
        cr_guard(text)


@pytest.mark.parametrize("text", _PARITY_CORPUS)
def test_deadline_reminder_path_blocks_corpus(text):
    from app.change_register import ChangeRegisterError
    from app.deadline_radar import render_reminder_message

    entry = {
        "lead_stage": 30,
        "days_until": 30,
        "deadline_kind": "deadline",
        "deadline_date": "2026-09-01",
        "source_name": f"Test source — {text}",
        "regulator": "VARA",
        "evidence_record_id": "rec-1",
    }
    with pytest.raises(ChangeRegisterError):
        render_reminder_message(entry)


@pytest.mark.parametrize("text", _PARITY_CORPUS)
def test_digest_path_blocks_corpus(text):
    from app.change_register import ChangeRegisterError
    from app.digest_cadence import render_digest_message

    bundle = [
        {
            "risk_level": "HIGH",
            "source_name": "Official source",
            "market": "AE",
            "change_type": "Regulatory update",
            "reviewed_at": "2026-07-21T00:00:00Z",
            "executive_summary": text,
            "source_url": "https://example.gov.ae",
        }
    ]
    with pytest.raises(ChangeRegisterError):
        render_digest_message({}, bundle, cadence="daily", period_label="2026-07-21")
