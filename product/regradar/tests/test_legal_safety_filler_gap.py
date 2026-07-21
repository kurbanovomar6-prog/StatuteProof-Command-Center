"""The closed-class filler gap between claim words is UNBOUNDED, not capped.

The forbidden-claims guard tolerates a run of closed-class fillers between the
words of a banned phrase so a marketer cannot smuggle "guarantee compliance" past
it as "guarantees FULL ONGOING REGULATORY compliance". Any FINITE cap is itself a
bypass: one determiner in front of a three-filler stack — "guarantees YOUR full
ongoing regulatory compliance", a plain marketing sentence — already overflowed a
three-filler cap, and stacking N+1 fillers escapes any bound N. Because only
closed-class fillers can appear in the gap (a single content word breaks the
chain), the gap is unbounded. These tests pin the natural determiner-prefixed and
deep-stack catches and guard against over-widening back into honest prose.
"""

from __future__ import annotations

import pytest

from app.legal_safety import find_forbidden_claims


# ── The bypass that regressed: stacked closed-class fillers ───────────────────
@pytest.mark.parametrize(
    "text",
    [
        # The natural determiner-prefixed escape that overflowed a three-filler
        # cap: your / full / ongoing / regulatory (4 fillers) — a plain marketing
        # sentence, one determiner plus three adjectives.
        "StatuteProof guarantees your full ongoing regulatory compliance.",
        # An even deeper stack must not escape either — no finite bound is safe.
        "We guarantee our every total complete ongoing continuous compliance.",
        # The three-filler stacks that a previous cap sized exactly to.
        "StatuteProof guarantees full ongoing regulatory compliance for your firm.",
        "We guarantee your total ongoing compliance.",
        "This guarantees complete continuous regulatory compliance.",
    ],
)
def test_stacked_filler_gap_is_caught(text: str) -> None:
    assert "guarantee compliance" in find_forbidden_claims(text)


def test_two_filler_gap_still_caught() -> None:
    # The previously-blocked form must stay blocked (no regression the other way).
    assert "guarantee compliance" in find_forbidden_claims(
        "StatuteProof guarantees full ongoing compliance for your firm."
    )


# ── Honest prose with three-word gaps must still pass (no over-widening) ──────
@pytest.mark.parametrize(
    "text",
    [
        # "guarantee" and "compliance" both appear but belong to different clauses,
        # separated by content words that are NOT closed-class fillers.
        "We reviewed the guarantee on your recent regulatory filing before compliance sign-off.",
        "The full report notes that our ongoing legal review of the compliance program continues.",
        # Neutral operational sentence that happens to use several gap words.
        "StatuteProof monitors your ongoing regulatory obligations and supports your compliance review.",
    ],
)
def test_legitimate_three_word_gap_not_flagged(text: str) -> None:
    assert find_forbidden_claims(text) == []


def test_denial_with_stacked_fillers_still_exempt() -> None:
    # The denial anchor is measured from the first matched word, so an unbounded
    # gap must not break the "does not guarantee …" neutralization — even with a
    # determiner-prefixed four-filler stack.
    assert find_forbidden_claims(
        "StatuteProof does not guarantee your full ongoing regulatory compliance."
    ) == []
