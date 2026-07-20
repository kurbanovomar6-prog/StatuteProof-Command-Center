"""Shared legal-safety guard — the ONE forbidden-claims list + the ONE guard.

Legal safety is StatuteProof's #1 promise: no customer-facing byte may assert a
claim the product forbids (see CLAUDE.md "Forbidden Claims"). Historically the
ban list was duplicated across modules (``monthly_assurance_report``,
``weekly_brief``, ``coverage_certificate`` …) which let a phrase slip through a
gap in one path while another blocked it. This module is the single source of
truth:

* ``FORBIDDEN_PHRASES`` — the canonical, product-wide ban list.
* ``assert_no_forbidden_claims`` / ``find_forbidden_claims`` /
  ``contains_forbidden_claim`` — the ONE guard, applied to the FINAL rendered
  customer-facing string on every delivery path.

The guard neutralizes the product's own fixed *disclaimers* before scanning:
those legitimately DENY the forbidden claims ("Not legal advice",
"does not guarantee compliance, prevent fines"), so scanning them verbatim
would trip the guard on safe text. Any AFFIRMATIVE occurrence of a banned
phrase still raises.
"""

from __future__ import annotations

from typing import Iterable

from app.evidence_assessment import LEGAL_DISCLAIMER

# ── Canonical ban list (single source of truth) ────────────────────────────────
# Substring, case-insensitive. Mirrors the CLAUDE.md "Forbidden Claims" table.
# Other modules re-export this rather than maintaining divergent copies.
FORBIDDEN_PHRASES: tuple[str, ...] = (
    "ai lawyer",
    "guarantee compliance",
    "guaranteed compliance",
    "prevent fines",
    "replace lawyers",
    # "legal advice" is banned ONLY in AFFIRMATIVE forms (StatuteProof claiming
    # to give it). The bare noun is intentionally NOT listed: official regulator
    # sources routinely say "seek independent legal advice", and holding those
    # legitimate excerpts would degrade the core alert function. Denials ("not
    # legal advice") are handled by _SAFE_DISCLAIMER_FRAGMENTS.
    "automatic legal advice",
    "automated legal advice",
    "provides legal advice",
    "provide legal advice",
    "providing legal advice",
    "gives legal advice",
    "give legal advice",
    "offer legal advice",
    "offering legal advice",
    "is legal advice",
    "constitutes legal advice",
    "constitute legal advice",
    "official partner",
    "certified by",
    "regulator certified",
    "100% accurate",
    "never miss",
    "stay compliant automatically",
    "we handle compliance for you",
    "automated compliance decisions",
    "avoid all penalties",
)

# Brief-specific advisory over-promises (weekly-brief prose only). Additive to
# the canonical list so the brief scan stays a SUPERSET of the product ban list,
# never a fork.
BRIEF_EXTRA_PHRASES: tuple[str, ...] = (
    "ensure you are compliant",
    "you will be compliant",
    "automatically compliant",
    "no action needed",
    "fully covered",
    "certified",
)

# Fixed disclaimer / denial fragments that legitimately embed a banned substring
# ("legal advice"; or "guarantee compliance"/"prevent fines" in DENIAL form).
# Removed before scanning so a disclaimer never trips its own guard, while any
# affirmative banned claim still raises. Same neutralization pattern historically
# used by change_register / evidence_pack / coverage_certificate.
# Anchored to the DENIAL form ("not …", "does not …") so an AFFIRMATIVE claim
# phrased with the same words (e.g. "we guarantee compliance, prevent fines")
# can never hide inside a neutralized fragment.
_SAFE_DISCLAIMER_FRAGMENTS: tuple[str, ...] = (
    str(LEGAL_DISCLAIMER or "").lower(),
    "monitoring information only. not legal advice.",
    "not legal advice and not a guarantee of compliance",
    "not legal advice",
    "not constitute legal advice",
    "does not guarantee compliance, prevent fines",
    "not a guarantee of compliance",
)


class ForbiddenClaimError(ValueError):
    """Raised when customer-facing output contains a forbidden claim."""


# Common Cyrillic/Greek homoglyphs of ASCII letters that appear in the ban
# phrases. Folded to their Latin lookalike so an adversarial source cannot
# smuggle "guarantee сompliance" (Cyrillic с) past the substring scan. AI models
# emit ASCII, so this only matters for deliberately-crafted source content.
# Audited 2026-07-21 against every ASCII letter used by FORBIDDEN_PHRASES and
# BRIEF_EXTRA_PHRASES: the Greek epsilons were missing, so "guarantεe
# compliance" passed the gate while the Cyrillic spelling was blocked. Only
# genuine lookalikes are listed — no mapping is invented for letters that have
# no plausible Cyrillic/Greek confusable (f, g, n, …). Covered by
# tests/test_legal_safety_homoglyphs.py, which is data-driven off this table.
_CONFUSABLE_FOLD = str.maketrans({
    # Cyrillic
    "а": "a", "с": "c", "е": "e", "о": "o", "р": "p", "х": "x", "у": "y",
    "і": "i", "ѕ": "s", "ј": "j", "ԁ": "d", "һ": "h", "ӏ": "l", "т": "t",
    "г": "r", "м": "m", "ѵ": "v",
    # Greek
    "α": "a", "β": "b", "γ": "y", "ε": "e", "ϵ": "e", "ι": "i", "κ": "k",
    "μ": "m", "ν": "v", "ο": "o", "ρ": "p", "ς": "c", "ϲ": "c", "τ": "t",
    "υ": "u", "χ": "x", "ω": "w",
    # NFKC rewrites the lunate sigma ϲ (a c-lookalike) to the final sigma ς, so
    # ς must fold to "c" as well or the ϲ row never fires after normalization.
})


def _fold(text: str) -> str:
    """NFKC-normalize + fold homoglyphs + lowercase + collapse whitespace runs.

    Whitespace collapse matters: rendered output (markdown→plaintext email,
    PDF text extraction, line-wrapped Telegram) reflows text across newlines,
    tabs and double spaces, so a banned two-word phrase like "guarantee
    compliance" routinely appears as "guarantee\ncompliance". Collapsing every
    whitespace run to a single space before the substring scan closes that
    bypass (found by the test-coverage audit 2026-07-13). Punctuation is left
    intact, so it never merges two words that were separated by a full stop.

    The homoglyph table is applied BEFORE and AFTER normalization, and the
    lowercase pass runs between them: NFKC rewrites some confusables into other
    non-Latin letters (ϲ→ς) and some symbol forms into their letter (ϵ→ε), while
    an upper-case Cyrillic "Е" only becomes a table key once lowercased. One
    pass in isolation misses a class each way; two passes cover all of them.
    """
    import unicodedata
    raw = str(text or "").translate(_CONFUSABLE_FOLD)
    folded = unicodedata.normalize("NFKC", raw).lower().translate(_CONFUSABLE_FOLD)
    return " ".join(folded.split())


def _neutralize_disclaimers(text: str) -> str:
    """Fold ``text`` and strip the product's fixed safe disclaimer fragments.

    Fragments are folded the SAME way (incl. whitespace collapse) so a
    line-wrapped disclaimer in the rendered output is still recognised and
    neutralised — otherwise a wrapped disclaimer's own denial could be missed.
    """
    low = _fold(text)
    for fragment in _SAFE_DISCLAIMER_FRAGMENTS:
        folded_fragment = _fold(fragment)
        if folded_fragment:
            low = low.replace(folded_fragment, " ")
    return low


def find_forbidden_claims(
    text: str,
    *,
    phrases: Iterable[str] | None = None,
    neutralize_disclaimers: bool = True,
) -> list[str]:
    """Return every banned phrase present in ``text`` (deduped, sorted).

    ``phrases`` overrides the canonical list (e.g. the brief scan passes its
    superset). By default the product's fixed disclaimers are neutralized first
    so their denials do not self-trip.
    """
    haystack = _neutralize_disclaimers(text) if neutralize_disclaimers else _fold(text)
    candidates = tuple(phrases) if phrases is not None else FORBIDDEN_PHRASES
    hits = {p for p in candidates if p and p.lower() in haystack}
    return sorted(hits)


def contains_forbidden_claim(
    text: str,
    *,
    phrases: Iterable[str] | None = None,
    neutralize_disclaimers: bool = True,
) -> bool:
    """True if ``text`` contains any banned phrase (disclaimers neutralized)."""
    return bool(
        find_forbidden_claims(
            text, phrases=phrases, neutralize_disclaimers=neutralize_disclaimers
        )
    )


def assert_no_forbidden_claims(
    text: str,
    *,
    phrases: Iterable[str] | None = None,
    exc: type[Exception] = ForbiddenClaimError,
    label: str = "Customer-facing output",
) -> None:
    """Raise ``exc`` if ``text`` contains any forbidden claim.

    This is the authoritative fail-closed guard for the FINAL rendered bytes of
    any customer-facing delivery path.
    """
    hits = find_forbidden_claims(text, phrases=phrases)
    if hits:
        raise exc(f"{label} contains forbidden claim(s): " + ", ".join(hits))
