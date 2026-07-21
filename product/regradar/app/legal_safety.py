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

import re
from functools import lru_cache
from typing import Iterable

from app.evidence_assessment import LEGAL_DISCLAIMER

# ── Canonical ban list (single source of truth) ────────────────────────────────
# Case-insensitive, matched INFLECTION-AWARE (see ``_phrase_pattern``): each
# entry is a CLAIM, not a spelling, so "guarantee compliance" also blocks
# "guarantees / guaranteed / guaranteeing compliance". Mirrors the CLAUDE.md
# "Forbidden Claims" table. Other modules re-export this rather than
# maintaining divergent copies.
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
    # The inflection engine is FORWARD-only (it adds suffixes, never strips
    # them), so a phrase stored in plural/participle form covers nothing to its
    # left. The base forms below are therefore listed explicitly — each expands
    # to its own plural / 3rd-person / past / -ing forms, which is why they are
    # supersets of the participle entries kept above for message stability.
    "certify compliance",
    "replace lawyer",
    "automated compliance decision",
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
    # change_register / audit_export footer: a LIST of denials under one "does
    # not", so the later items sit too far from the negation for the tight
    # denial anchor to see it. Fixed product wording, denial-anchored.
    "does not determine legal obligations, certify compliance",
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


# Markup that a renderer inserts BETWEEN the words of a phrase. The delivery
# gates scan the FINAL rendered artefacts (email body_text + body_html, Telegram
# markdown), and `**guarantee** compliance` / `<strong>guarantee</strong>
# compliance` read to the customer as the plain claim, so both representations
# must fold to the same plain words.
# ``[^<>]`` (not ``[^>]``) is load-bearing for AVAILABILITY, not for matching:
# with ``[^>]*`` the engine can cross other "<" characters, so text carrying
# "<letter" with no later ">" (comparison notation in a diff excerpt, mojibake,
# truncated HTML) restarts a scan-to-end-of-document at every "<" — O(n^2).
# Measured on this module: 198KB of "if x<y then …" cost 1.7s (400KB ~ 86s)
# inside the fail-closed guard that sits on the synchronous path of every audit
# pack and register export. Excluding "<" makes it linear (~2ms) and folds
# well-formed tags identically; where it differs (a "<" inside an attribute
# value) it strips LESS, i.e. leaves more text for the scanner — the safe
# direction. Pinned by test_canonical_guard_stays_linear_on_markup_heavy_documents.
_HTML_TAG = re.compile(r"</?[a-z][^<>]*>", re.IGNORECASE)
# Emphasis markers HUG the text they emphasise ("**guarantee**"). A marker that
# touches no word character is a LIST BULLET ("* guarantee"), and dropping it
# would weld two list items into a phrase the customer never read.
_MARKDOWN_EMPHASIS = re.compile(r"(?<=[0-9a-z])[*_`~]+|[*_`~]+(?=[0-9a-z])")

# Separator artefacts that split a word or join two: zero-width characters, the
# soft hyphen, and the hyphen/dash class. They are ambiguous — "AI-lawyer" needs
# the hyphen to become a SPACE, while a PDF line-wrap "com-\npliance" needs it
# REMOVED — so ``find_forbidden_claims`` scans both foldings (see ``_haystacks``).
_ARTEFACT_CLASS = "[\u200b-\u200d\ufeff\u00ad\u2010-\u2015\u2212\u002d]"
_SEPARATOR_ARTEFACT = re.compile(_ARTEFACT_CLASS)
# Folding is INTRA-WORD only: the artefact must be attached to the preceding
# word character, and at most a single line break may follow it (a PDF or
# plaintext line-wrap, "guarantee com-\npliance", rejoins into one word). A dash
# with whitespace on BOTH sides is punctuation, not an artefact — it is the
# markdown bullet marker every alert/digest message uses (``- {reason}`` lines
# in alert_routing / digest_cadence) and the spaced em dash of ordinary prose.
# Folding those joined unrelated list items into claims the text never made
# ("- guarantee\n- compliance" -> "guarantee compliance"; "…is a guarantee —
# compliance remains your obligation"), and the guard is fail-closed, so the
# whole human-approved delivery was withheld.
_INTRAWORD_ARTEFACT = re.compile(
    r"(?<=[0-9a-z])" + _ARTEFACT_CLASS + r"+[^\S\n]*\n?[^\S\n]*(?=[0-9a-z])"
)

# "A.I. lawyer" → "ai lawyer". Only fires on 2+ single-letter-plus-dot runs, so
# an ordinary full stop still separates two words.
_ACRONYM_DOTS = re.compile(r"\b(?:[a-z]\.){2,}")

# "100 % accurate" / "100%accurate" → "100% accurate".
_PERCENT_SPACING = re.compile(r"\s*%\s*")


def _fold(text: str, *, artefact_sub: str = " ") -> str:
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

    Markup is removed BEFORE the collapse: the fail-closed gates scan the FINAL
    rendered artefacts, and a renderer legitimately puts `<strong>`/`**` between
    the words of a phrase the customer reads as one plain sentence. HTML tags
    become a space (never merging two words); markdown emphasis runs are dropped
    (they can sit INSIDE a word). Every step here is strictly stricter — it can
    only make more text match, never less.
    """
    import unicodedata
    raw = str(text or "").translate(_CONFUSABLE_FOLD)
    folded = unicodedata.normalize("NFKC", raw).lower().translate(_CONFUSABLE_FOLD)
    folded = _HTML_TAG.sub(" ", folded)
    folded = _MARKDOWN_EMPHASIS.sub("", folded)
    folded = _INTRAWORD_ARTEFACT.sub(artefact_sub, folded)
    folded = _ACRONYM_DOTS.sub(lambda m: m.group(0).replace(".", ""), folded)
    folded = _PERCENT_SPACING.sub("% ", folded)
    return " ".join(folded.split())


def _neutralize_disclaimers(text: str, *, artefact_sub: str = " ") -> str:
    """Fold ``text`` and strip the product's fixed safe disclaimer fragments.

    Fragments are folded the SAME way (incl. whitespace collapse) so a
    line-wrapped disclaimer in the rendered output is still recognised and
    neutralised — otherwise a wrapped disclaimer's own denial could be missed.
    """
    low = _fold(text, artefact_sub=artefact_sub)
    for fragment in _SAFE_DISCLAIMER_FRAGMENTS:
        folded_fragment = _fold(fragment, artefact_sub=artefact_sub)
        if folded_fragment:
            # Leave a negation cue behind rather than a bare space. Several safe
            # fragments carry the clause's "does not"/"no" (e.g. "does not
            # guarantee compliance, prevent fines"); deleting the fragment
            # outright removed that cue, so a FURTHER banned phrase in a trailing
            # conjunct of the SAME honest denial ("...or replace lawyers") lost
            # its negation context and was wrongly blocked. " not " keeps
            # _is_denied() true for those trailing conjuncts; it is itself not a
            # banned phrase, so it introduces no new match.
            low = low.replace(folded_fragment, " not ")
    return low


def _haystacks(text: str, *, neutralize: bool) -> tuple[str, ...]:
    """Every folding of ``text`` the guard must scan.

    Separator artefacts (hyphen/dash class, zero-width, soft hyphen) are
    ambiguous: "AI-lawyer" and "never-miss" need them read as a SPACE, while a
    PDF line-wrap ("guarantee com-\npliance") or a zero-width injected mid-word
    needs them REMOVED. Rather than guess, both foldings are scanned. The second
    is only built when such a character is actually present, so ordinary text
    pays nothing and the guard stays linear.
    """
    prep = _neutralize_disclaimers if neutralize else _fold
    spaced = prep(text)
    if not _SEPARATOR_ARTEFACT.search(str(text or "")):
        return (spaced,)
    joined = prep(text, artefact_sub="")
    return (spaced,) if joined == spaced else (spaced, joined)



# ── inflection-aware matching ──────────────────────────────────────────────────
# The ban list names CLAIMS, not spellings. A flat literal-substring scan blocks
# "we guarantee compliance" but passed "StatuteProof guarantees compliance" —
# the way a marketer actually writes it, needing no adversarial crafting. So
# every banned phrase is compiled to a regex whose words carry their regular
# English inflections. The table below is the ONLY place the morphology lives;
# adding a phrase to the ban list picks it up automatically.

# Endings that take "-es" for the third person / plural ("miss" → "misses").
_SIBILANT_ENDINGS = ("s", "x", "z", "ch", "sh")
_VOWELS = "aeiou"


def _is_consonant_y(word: str) -> bool:
    """True for "certify"-shaped words (consonant + y → -ies / -ied)."""
    return len(word) > 1 and word.endswith("y") and word[-2] not in _VOWELS


def _word_inflections(word: str) -> tuple[str, ...]:
    """``word`` plus its regular inflections (plural / 3rd person / past / -ing).

    Deliberately additive and regular-only: it never removes the literal form,
    so every match the old substring scan made is still made. Irregular verbs
    are not guessed — the ban list is short, literal and reviewed, and inventing
    forms would risk false positives on honest text.
    """
    if not word.isalpha():
        return (word,)
    forms = {word}
    if _is_consonant_y(word):
        stem = word[:-1]
        forms.update({stem + "ies", stem + "ied", word + "ing"})
    else:
        forms.add(word + "es" if word.endswith(_SIBILANT_ENDINGS) else word + "s")
        if word.endswith("ee"):
            # "guarantee" → "guaranteed" / "guaranteeing" (the -e is kept).
            forms.update({word + "d", word + "ing"})
        elif word.endswith("e"):
            forms.update({word + "d", word[:-1] + "ing"})
        else:
            forms.update({word + "ed", word + "ing"})
    # Longest-first so the alternation prefers the fuller form on a first pass.
    return tuple(sorted(forms, key=lambda f: (-len(f), f)))


# Closed-class fillers a marketer naturally slips between the words of a claim:
# "guarantees FULL compliance", "guarantee YOUR compliance", "guarantee OF
# compliance", "guarantee 100% compliance". Requiring the words to be adjacent
# let every one of those through. The gap is capped at two of these listed words
# — an open-ended gap would start matching across unrelated clauses, and only
# closed-class fillers can appear, so an honest sentence cannot be joined into a
# claim. The denial anchor is measured from the FIRST word of the match, so
# widening the gap does not weaken the "does not guarantee …" neutralization.
_PHRASE_GAP_WORDS = (
    "a", "an", "the", "this", "that", "these", "those",
    "my", "our", "your", "their", "its", "his", "her",
    "all", "any", "every", "full", "total", "complete", "entire",
    "ongoing", "continuous", "permanent", "future", "real", "ultimate",
    "regulatory", "legal", "of", "100%",
)
_PHRASE_SEPARATOR = (
    r"\s+(?:(?:" + "|".join(re.escape(w) for w in _PHRASE_GAP_WORDS) + r")\s+){0,2}"
)


@lru_cache(maxsize=512)
def _phrase_pattern(phrase: str) -> re.Pattern[str]:
    """Compile one banned phrase into an inflection-aware pattern.

    Applied to text that ``_fold`` already lowercased, homoglyph-folded and
    whitespace-collapsed, so words are joined by a single space plus an optional
    closed-class filler gap (``_PHRASE_SEPARATOR``). No word-boundary anchors
    are imposed: the literal form stays one of the alternatives, so the pattern
    is a strict SUPERSET of the previous substring scan and no previously-blocked
    string can start passing.
    """
    words = _fold(phrase).split()
    parts = [
        "(?:" + "|".join(re.escape(form) for form in _word_inflections(word)) + ")"
        for word in words
    ]
    return re.compile(_PHRASE_SEPARATOR.join(parts))


# ── Is this a claim WE make, or text we QUOTE or DENY? ────────────────────────
# The guard exists to stop StatuteProof asserting something it cannot back. It
# must NOT censor the regulator. A blocked delivery is a WITHHELD delivery, and
# the sentence the customer pays for is precisely the rulebook line — so holding
# "An Authorised Firm must certify compliance with GEN 5.3.7" is a worse and
# more silent failure than the first-party marketing bypasses this engine
# closes. Two exemptions therefore apply, both scoped to the CLAUSE around the
# match and both cancelled by any first-party subject:
#
#   1. DENIAL   — a negation cue anywhere earlier in the clause ("there is no
#                 guarantee of compliance", "nothing here guarantees compliance",
#                 "does not determine legal obligations, certify compliance, or
#                 …" — the 2nd and 3rd conjuncts of a coordinated denial sit far
#                 from the "not", which the previous adjacency anchor missed).
#   2. QUOTED OBLIGATION — a modal obligation ("must", "shall", "is required
#                 to", "requires X to") governing the phrase, with a regulated
#                 third-party subject in the clause and NO first-party subject.
#
# Both are deliberately clause-scoped rather than sentence- or document-scoped:
# a clause is the smallest unit that carries a single subject+polarity, so a
# distant negation in an earlier sentence still cannot launder a claim.
# Sentence punctuation, plus the dash/hyphen class: after the intra-word folding
# above, any dash still present has whitespace around it, i.e. it is a spaced em
# dash or a list bullet — both of which start a new clause with its own subject
# and polarity ("No action — you will avoid all penalties" is a CLAIM, not a
# denial, and bullet 1's "no" must not cover bullet 2).
_CLAUSE_BOUNDARY = re.compile(r"[.!?;:‐-―−-]")

# Only the nearest text can participate, and every scan below runs per match, so
# the window is capped to keep the guard linear on large deliveries (the same
# reason the previous denial anchor used a fixed look-back).
_CLAUSE_WINDOW = 240

_NEGATION_CUE = re.compile(
    r"(?:^|[^a-z])(?:not|cannot|never|nor|without|neither|no|none|nothing|nobody)"
    r"(?![a-z])"
)
# Cues that CANCEL an earlier negation, so a contrast clause cannot smuggle a
# claim in behind one ("we do not merely monitor, but we guarantee compliance").
_NEGATION_CANCEL = re.compile(
    r"(?:^|[^a-z])(?:but|however|yet|instead|rather|although|though|doubt)(?![a-z])"
)

# First-party subjects. Their presence anywhere in the clause cancels BOTH
# exemptions: if StatuteProof is the subject, the sentence is our claim no
# matter how it is dressed ("StatuteProof must guarantee compliance for your
# firm" stays blocked).
_FIRST_PARTY = re.compile(
    r"(?:^|[^a-z])(?:statuteproof|we|our|ours|us|the platform|this platform|"
    r"this service|the service|this product|the product|this report|this brief)"
    r"(?![a-z])"
)

# Regulated third-party subjects — who a rulebook sentence puts the obligation
# on. Deliberately a closed list of entity nouns: an open-ended "some noun"
# rule would exempt marketing copy that merely mentions a firm.
_THIRD_PARTY_SUBJECT = re.compile(
    r"(?:^|[^a-z])(?:firm|firms|entity|entities|licensee|licensees|licence holder|"
    r"license holder|authorised person|authorised persons|authorized person|"
    r"authorized persons|senior management|management|officer|officers|"
    r"applicant|applicants|institution|institutions|bank|banks|company|companies|"
    r"registrant|registrants|issuer|issuers|vasp|vasps|broker|brokers|"
    r"auditor|auditors|director|directors|member|members|person|persons|"
    r"party|parties|holder|holders|subject person|reporting entity|"
    r"relevant person|panel|board|committee|counsel|lawyer|lawyers)(?![a-z])"
)

# A modal obligation that GOVERNS the phrase: it must sit within a few words of
# the match, so "must" three clauses back cannot exempt an unrelated claim.
_OBLIGATION_GOVERNOR = re.compile(
    r"(?:^|[^a-z])(?:must|shall|should|may|ought to|required to|obliged to|"
    r"expected to|has to|have to|had to|needs to|need to|"
    r"requires?[a-z0-9 ']{0,40}?\sto|required[a-z0-9 ']{0,40}?\sto)"
    r"(?:\s+[a-z0-9%']+){0,3}\s+$"
)

# Phrases that are only a CLAIM when StatuteProof is the subject. "certify
# compliance" is standard DFSA/CBUAE/VARA rulebook wording ("an Authorised Firm
# must certify compliance with …"), not marketing language, and the final-bytes
# gate scans diff excerpts passed through VERBATIM from the source — so a
# product-wide ban on it withholds genuine rule changes. CLAUDE.md bans
# compliance certification BY StatuteProof, which is exactly what this tier
# keeps blocked ("StatuteProof certifies your compliance"). The authored-prose
# lists (BRIEF_EXTRA_PHRASES and the report/assurance extras) never carry raw
# source excerpts, so their own "certified" entries stay unconditional.
_FIRST_PARTY_ONLY_PHRASES: frozenset[str] = frozenset({"certify compliance"})


def _clause_around(haystack: str, start: int, end: int) -> tuple[str, str]:
    """The clause text before and after a match, capped to ``_CLAUSE_WINDOW``."""
    prefix = haystack[max(0, start - _CLAUSE_WINDOW):start]
    last_boundary = None
    for last_boundary in _CLAUSE_BOUNDARY.finditer(prefix):
        pass
    before = prefix[last_boundary.end():] if last_boundary else prefix
    suffix = haystack[end:end + _CLAUSE_WINDOW]
    next_boundary = _CLAUSE_BOUNDARY.search(suffix)
    after = suffix[:next_boundary.start()] if next_boundary else suffix
    return before, after


def _is_denied(before: str) -> bool:
    """True when a negation earlier in the clause makes the match a denial."""
    last_cue = None
    for last_cue in _NEGATION_CUE.finditer(before):
        pass
    if last_cue is None:
        return False
    return not _NEGATION_CANCEL.search(before[last_cue.end():])


def _is_quoted_obligation(before: str, after: str) -> bool:
    """True when the match is a third-party regulatory obligation, not our claim."""
    return bool(
        _OBLIGATION_GOVERNOR.search(before)
        and _THIRD_PARTY_SUBJECT.search(before + " " + after)
    )


def _is_attributed(haystack: str, start: int, end: int, *, phrase: str) -> bool:
    """True when the match is text we QUOTE or DENY rather than a claim we make.

    ``phrase``-specific: entries in ``_FIRST_PARTY_ONLY_PHRASES`` are a claim
    only with a first-party subject, so everything else is attributed.
    """
    before, after = _clause_around(haystack, start, end)
    # A denial stands whoever the subject is — "we cannot prevent fines" is the
    # product's own honest wording, so the first-party check must not veto it.
    if _is_denied(before):
        return True
    if _FIRST_PARTY.search(before + " " + after):
        return False
    if phrase in _FIRST_PARTY_ONLY_PHRASES:
        return True
    return _is_quoted_obligation(before, after)


def find_forbidden_claims(
    text: str,
    *,
    phrases: Iterable[str] | None = None,
    neutralize_disclaimers: bool = True,
) -> list[str]:
    """Return every banned phrase present in ``text`` (deduped, sorted).

    ``phrases`` overrides the canonical list (e.g. the brief scan passes its
    superset). By default the product's fixed disclaimers are neutralized first
    and ATTRIBUTED occurrences — denials, and third-party regulatory obligations
    we are quoting — are not treated as claims, so neither honest wording
    ("StatuteProof does not guarantee compliance") nor the regulator's own
    sentence ("an Authorised Firm must certify compliance with …") is withheld.
    """
    haystacks = _haystacks(text, neutralize=neutralize_disclaimers)
    candidates = tuple(phrases) if phrases is not None else FORBIDDEN_PHRASES
    hits = set()
    for phrase in candidates:
        if not phrase:
            continue
        for haystack in haystacks:
            if any(
                not (
                    neutralize_disclaimers
                    and _is_attributed(
                        haystack, match.start(), match.end(), phrase=phrase
                    )
                )
                for match in _phrase_pattern(phrase).finditer(haystack)
            ):
                hits.add(phrase)
                break
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
