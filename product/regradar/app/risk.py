"""
Lightweight rule-based risk scoring engine.

No AI, no external APIs.  Runs entirely offline via keyword matching.

Scoring rules (evaluated in order — first match wins):

  NON_MATERIAL  Fires before all other tiers.
                Change exists but net diff < 80 chars AND no obligation
                keywords detected.  Pure formatting / whitespace edits.

  HIGH    requires one of:
            • ≥ 2 strong-risk keywords matched, OR
            • 1 strong-risk keyword + ≥ 1 context-amplifier word
          strong-risk keywords:   ban, restriction, license/licence, penalty,
                                   sanction, fine, revoke, suspend, cease …
          context-amplifier words: deadline, compliance, reporting, obligation,
                                   mandatory, enforcement
          Context amplifiers are DISTINCT from strong keywords — a single
          strong word cannot self-pair into HIGH (fix-self-pairing).

  MEDIUM  • 1 strong-risk keyword without context support, OR
          • Moderate-change keyword: update, change, amendment

  LOW     Everything else (no keywords matched)

Severity rubric — rule identifiers returned in analyze_risk()["rule"]:
  HIGH_MULTIPLE_STRONG      ≥2 strong keywords matched in changed text
  HIGH_STRONG_PLUS_CONTEXT  1 strong keyword + ≥1 context amplifier
  MEDIUM_SINGLE_STRONG      1 strong keyword, no context support
  MEDIUM_MODERATE_KEYWORD   moderate-change keyword only
  MEDIUM_ARABIC             Arabic content — English-only matcher, human review
  LOW_NO_KEYWORDS           nothing matched
  NON_MATERIAL              below materiality threshold
An alert may only claim what its rule actually matched; matched keywords are
carried alongside so the alert layer can name them (defect A2/A4).
"""

from __future__ import annotations

import re

_ARABIC_RE = re.compile(r"[؀-ۿ]")

# ── Improvement 4: urgency derivation from diff text ─────────────────────────
# Canonical implementation lives in app.ai; the patterns are duplicated here
# so risk.py can be used standalone (offline, no AI dependency) in tests and
# rule-based-only pipelines.

_URGENCY_PATTERNS: list[tuple[re.Pattern, str]] = [
    (
        re.compile(
            r"effective\s+(from|as\s+of|on)\s+"
            r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}-\d{2}-\d{2})",
            re.I,
        ),
        "IMMEDIATE",
    ),
    (
        re.compile(
            r"by\s+(end\s+of\s+)?"
            r"(january|february|march|april|may|june|july|august|"
            r"september|october|november|december)\s+\d{4}",
            re.I,
        ),
        "WITHIN_30_DAYS",
    ),
    (re.compile(r"within\s+(\d+)\s+days", re.I), "WITHIN_30_DAYS"),
    (re.compile(r"no\s+later\s+than", re.I),     "WITHIN_30_DAYS"),
]


def derive_urgency_from_text(diff_text: str) -> str:
    """
    Scan diff text for deadline/effectivity patterns and return urgency tier.

    Returns one of: IMMEDIATE | WITHIN_30_DAYS | MONITOR (fallback).
    Used as a fallback when the AI does not return urgency or returns an
    unrecognised value.  Mirrors the identical function in app.ai so that
    rule-based pipelines can use urgency derivation without importing the AI layer.

    Never raises.
    """
    if not diff_text:
        return "MONITOR"
    for pattern, urgency in _URGENCY_PATTERNS:
        if pattern.search(diff_text):
            return urgency
    return "MONITOR"

# F4: matching is WORD-BOUNDED (see _match_terms) — Phase-0 replay proved
# substring matching fired 'ban' inside 'bank' on both CBUAE recorded false
# HIGHs (docs/signal/SIGNAL_QUALITY.md §A defect 1). Topic terms measured as
# letterhead/page-title noise ('vasp', 'virtual asset', 'circular') moved to
# the moderate tier — presence of the topic is not a change of obligation.
_HIGH_KEYWORDS: tuple[str, ...] = (
    "ban",
    "banned",
    "prohibition",
    "restriction",
    "license",
    "licence",   # UK spelling — DFSA/DIFC write UK English
    "licensing",
    "penalty",
    "penalties",
    "fine",
    "fines",
    "sanction",
    "sanctions",
    "revoke",
    "revoked",
    "revocation",
    "cease",
    "suspend",
    "suspended",
    "suspension",
    "enforcement action",
)

# Words that amplify a single HIGH keyword into a confirmed HIGH signal.
# They indicate a concrete regulatory obligation rather than incidental usage
# (e.g. "exchange rate update" vs "penalty for non-compliance by deadline").
#
# fix-self-pairing: context amplifiers MUST be terms DISTINCT from
# _HIGH_KEYWORDS. Previously `license`, `sanction`, `penalty`, and `fine`
# appeared in BOTH lists, so a single occurrence of one such token matched
# _HIGH_KEYWORDS and _HIGH_CONTEXT_WORDS independently — self-pairing one
# strong word into a false HIGH via HIGH path 2 ("A penalty applies." -> HIGH).
# Removing the overlap keeps those terms strong (still in _HIGH_KEYWORDS)
# while requiring a genuinely different obligation term to confirm HIGH.
#
# `enforcement` STAYS here: standing alone it is a genuine obligation
# amplifier ("a ban ... with immediate enforcement" -> real HIGH). It is,
# however, a word-bounded SUBSTRING of the strong keyword "enforcement
# action", which would let that phrase self-pair. That case — and any future
# exact/substring overlap between the two lists — is neutralised structurally
# by _drop_self_pairs() in analyze_risk, which removes a context term only
# when it is contained in an actually-matched strong keyword. This keeps the
# legitimate amplifier while blocking the self-pair.
_HIGH_CONTEXT_WORDS: tuple[str, ...] = (
    "deadline",
    "compliance",
    "reporting",
    "obligation",
    "mandatory",
    "enforcement",
    # Obligation / deadline markers — genuine, DISTINCT amplifiers (none of
    # these appear in _HIGH_KEYWORDS, so they cannot self-pair a strong term).
    # They confirm a concrete obligation attached to a single strong keyword,
    # e.g. "A penalty applies ... must file ... no later than <date>" (a real
    # HIGH) versus "It was a fine morning" (no obligation marker -> not HIGH).
    "must",
    "shall",
    "required",
    "no later than",
)

_MEDIUM_KEYWORDS: tuple[str, ...] = (
    "update",
    "change",
    "amendment",
    "guidance",
    "guideline",
    "notice",
    "consultation",
    "aml",
    "cft",
    "fit and proper",
    "prudential",
    # F4 demotions — topic/letterhead terms (Phase-0: matched VARA
    # marketing and page titles, never an obligation):
    "circular",
    "vasp",
    "vasps",
    "virtual asset",
    "virtual assets",
    # F4 additions measured in the delta corpus (SIGNAL_QUALITY.md §B):
    "decree-law",
    "cabinet decision",
    "cabinet resolution",
    "federal law",
)

# ── F3: Arabic detection lane ─────────────────────────────────────────────────
# Terms and tiers are grounded in measured trail frequencies
# (docs/signal/SIGNAL_QUALITY.md §B). Matching runs on
# arabic_text.normalize_arabic()-folded delta text. Arabic deadline
# vocabulary is effectively absent from the trail — no AR deadline term is
# claimed; unmatched Arabic routes to MEDIUM_ARABIC (human review).

_AR_STRONG_KEYWORDS: tuple[str, ...] = (
    "ترخيص",             # licence (35 delta hits)
    "رخصة",              # licence (variant)
    "عقوبة",             # penalty (85 delta hits with جزاء)
    "عقوبات",
    "جزاء",
    "جزاءات",
    "غرامة",             # fine (11 doc hits; 0 delta — kept, obligation-bearing)
    "تعميم",             # circular (58 delta hits)
)

# Topic/entity-name terms measured as weak discriminators: الأصول الافتراضية
# is VARA's own letterhead (339 delta hits, overwhelmingly chrome);
# غسل الأموال / تمويل الإرهاب sit in the UAEFIU mission tagline. High delta
# frequency here signals PRESENCE OF THE REGULATOR, not a change of
# obligation — moderate tier only (noise-guard tests in test_arabic_lane.py).

_AR_CONTEXT_WORDS: tuple[str, ...] = (
    "التزام",   # obligation (369 delta hits with يجب/يتعين)
    "يجب",      # must
    "يتعين",    # shall/required to
    "ملزم",     # binding
    "الزامي",   # mandatory (alef-folded)
    "نافذ",     # in force (13 delta hits)
)

_AR_MEDIUM_KEYWORDS: tuple[str, ...] = (
    "قانون اتحادي",       # federal law (242 delta hits)
    "مرسوم بقانون",       # decree-law (149 delta hits)
    "قرار",               # decision/resolution (257 delta hits)
    "لائحة",              # regulation (81 delta hits)
    "الاصول الافتراضية",   # virtual assets — demoted, letterhead noise
    "غسل الاموال",         # AML — demoted, mission-tagline noise
    "تمويل الارهاب",       # CFT — demoted, mission-tagline noise
)

# ── NON_MATERIAL tier constants ───────────────────────────────────────────────

NON_MATERIAL_MAX_CHARS = 80  # net diff length threshold

_OBLIGATION_KEYWORDS: tuple[str, ...] = (
    "deadline",
    "obligation",
    "mandatory",
    "must",
    "shall",
    "required",
    "compliance date",
    "effective date",
    "enforcement",
    "penalty",
    "fine",
    "sanction",
    "revoke",
    "suspend",
    "cease",
    "ban",
    # Absent-strong-keyword fix: restriction/licence are strong obligation
    # signals in _HIGH_KEYWORDS but were missing here, so a small diff that
    # introduced or altered a licence restriction slipped through the
    # materiality gate as NON_MATERIAL. Keep them (and common variants)
    # aligned with the strong keyword list.
    "restriction",
    "restrictions",
    "prohibition",
    "licence",
    "license",
    "licensing",
    "revocation",
    "suspension",
    "revoked",
    "suspended",
)


def _edited_char_count(removed_str: str, added_str: str) -> int:
    """Number of characters that actually differ between two texts.

    Uses a character-level diff and sums the inserted and deleted characters.
    A pure whitespace/formatting tweak yields a small count; a same-length
    content swap (e.g. "allowance" -> "restriction") yields a count equal to
    the combined length of the differing spans — the true edit magnitude,
    unlike a bare ``|len(added) - len(removed)|`` length delta.
    """
    from difflib import SequenceMatcher

    matcher = SequenceMatcher(a=removed_str, b=added_str, autojunk=False)
    changed = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "delete":
            changed += i2 - i1
        elif tag == "insert":
            changed += j2 - j1
        elif tag == "replace":
            changed += (i2 - i1) + (j2 - j1)
    return changed


def is_non_material(diff_result: dict) -> bool:
    """Return True when a change is below the materiality threshold.

    A change is NON_MATERIAL when ALL of the following are true:

    a. ``diff_result["changed"]`` is True (there is a change).
    b. Edited-content size (characters that actually differ between the
       removed and added text) < NON_MATERIAL_MAX_CHARS.
    c. None of the _OBLIGATION_KEYWORDS appear in the combined added+removed text.
    d. ``diff_result["risk_level"]`` is not already "HIGH".

    Returns False (conservative fallback) if the diff has no added/removed text fields.

    Note on (b): the magnitude is measured as the number of characters that
    actually changed between the two sides (via a character-level diff), NOT a
    pure length delta ``|added_len - removed_len|``. A same-length swap such as
    replacing "allowance" with "restriction" inside an otherwise-identical
    paragraph has a length delta of only a couple of characters but is a real,
    material edit — the edited-content metric captures it while pure
    formatting/whitespace edits still fall below the threshold.
    """
    if not diff_result.get("changed"):
        return False

    added_text = diff_result.get("added")
    removed_text = diff_result.get("removed")

    # Conservative fallback: no text to analyse → do not downgrade
    if added_text is None and removed_text is None:
        return False

    # Normalise: added/removed may be list[str] or str
    if isinstance(added_text, list):
        added_str = " ".join(added_text)
    else:
        added_str = str(added_text or "")

    if isinstance(removed_text, list):
        removed_str = " ".join(removed_text)
    else:
        removed_str = str(removed_text or "")

    # (b) Edited-content size — count characters that actually differ between
    # the two sides, so a same-length material swap (allowance -> restriction)
    # is not masked by a near-zero length delta.
    net_change = _edited_char_count(removed_str, added_str)
    if net_change >= NON_MATERIAL_MAX_CHARS:
        return False

    # (c) Obligation keywords
    combined_lower = (added_str + " " + removed_str).lower()
    for kw in _OBLIGATION_KEYWORDS:
        if kw in combined_lower:
            return False

    # (d) Do not downgrade already-HIGH
    if str(diff_result.get("risk_level") or "").upper() == "HIGH":
        return False

    return True


def _match_terms(terms: tuple[str, ...], text: str) -> list[str]:
    """Word-bounded term matching (F4).

    Substring matching fired 'ban' inside 'bank' on both CBUAE recorded
    false HIGHs (2026-06-12). Multi-word terms are matched as phrases.
    """
    matched: list[str] = []
    for term in terms:
        if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text):
            matched.append(term)
    return matched


def _drop_self_pairs(
    matched_context: list[str], matched_high: list[str]
) -> list[str]:
    """Structural self-pairing guard (fix-self-pairing, rework).

    HIGH path 2 (one strong keyword + a context amplifier) must be confirmed
    by a GENUINELY DISTINCT context signal. A context term that is equal to,
    or a substring of, a matched strong keyword is the SAME token acting as
    its own amplifier — e.g. context "enforcement" inside strong keyword
    "enforcement action", or a future exact duplicate across the two lists.

    Drop any such context term so a lone strong keyword can never self-amplify
    into HIGH. Order-preserving; distinct context terms are untouched.
    """
    return [
        ctx
        for ctx in matched_context
        if not any(ctx in strong for strong in matched_high)
    ]


_ADAPTER_BANNER = "listing items"


def _is_format_shift(diff_result: dict) -> bool:
    """True when the adapter output format flipped between runs (F4).

    22 of 63 historical CHANGED runs were adapter-format shifts: the page
    did not change, our extraction did (nav-scrape ↔ structured
    '... listing items'). Detector: the adapter banner appears on exactly
    one side of a two-sided diff.
    """
    added_txt = " ".join(str(a) for a in (diff_result.get("added") or [])).lower()
    removed_txt = " ".join(str(x) for x in (diff_result.get("removed") or [])).lower()
    if not added_txt.strip() or not removed_txt.strip():
        return False
    return (_ADAPTER_BANNER in added_txt) != (_ADAPTER_BANNER in removed_txt)


# Single-word obligation-bearing terms that must survive delta extraction even
# when they sit in the UNCHANGED portion of a MODIFIED block. Chrome/navigation
# words are deliberately excluded so the delta filter keeps suppressing them;
# only genuine obligation/severity signal is preserved. Built from the strong
# keyword and obligation lists, restricted to single tokens (multi-word phrases
# are matched later against the full delta text, not token-by-token here).
_DELTA_PRESERVE_TERMS: frozenset[str] = frozenset(
    term
    for term in (*_HIGH_KEYWORDS, *_OBLIGATION_KEYWORDS)
    if " " not in term
)


def _delta_scoring_text(added: list, removed: list) -> str:
    """
    Cycle 3 (delta-only severity scoring): when a block appears in both
    removed and added form, only the tokens that actually differ are scored.
    Keywords that merely sit inside a changed block (site navigation, page
    chrome) must not drive severity — that is what turned a DFSA title
    tagline flip into a false HIGH on 2026-07-05.

    Exception (obligation-signal preservation): a strong obligation keyword
    (penalty, fine, restriction, ban, …) that sits in the UNCHANGED part of a
    MODIFIED block is still scored. Otherwise a sentence like
    "The penalty ... is now AED 50000" vs "The penalty ... is AED 10000" would
    strip the word "penalty" (it is common to both sides) and a 5x penalty
    increase would score LOW with no alert. Only obligation-bearing tokens are
    preserved from equal spans; page-chrome words remain suppressed.

    Wholly new or wholly removed content is scored in full.
    """
    from difflib import SequenceMatcher

    added_tokens = " ".join(str(a) for a in (added or [])).split()
    removed_tokens = " ".join(str(r) for r in (removed or [])).split()
    if not added_tokens or not removed_tokens:
        return " ".join(added_tokens + removed_tokens)

    matcher = SequenceMatcher(a=removed_tokens, b=added_tokens, autojunk=False)
    delta: list[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "delete"):
            delta.extend(removed_tokens[i1:i2])
        if tag in ("replace", "insert"):
            delta.extend(added_tokens[j1:j2])
        if tag == "equal":
            # Preserve obligation-bearing keywords that happen to be common to
            # both sides of a modified block; drop everything else (chrome).
            delta.extend(
                tok
                for tok in added_tokens[j1:j2]
                if _strip_token(tok) in _DELTA_PRESERVE_TERMS
            )
    return " ".join(delta)


def _strip_token(token: str) -> str:
    """Lowercase a token and strip surrounding punctuation for keyword lookup.

    Keeps internal characters (e.g. hyphenated forms) intact; only trims
    leading/trailing non-word characters so "penalty," or "(penalty)" match.
    """
    return token.strip(".,;:!?()[]{}\"'").lower()


def analyze_risk(diff_result: dict) -> dict:
    """
    Score a structured diff result and return a risk assessment.

    Parameters
    ----------
    diff_result : dict
        Output of ``diff.get_diff()``.
        Expected keys: ``added`` (list[str]), ``removed`` (list[str]),
        optionally ``changed`` (bool) and ``has_changes`` (bool).

    Returns
    -------
    dict
        {
            "risk_level": "NON_MATERIAL" | "HIGH" | "MEDIUM" | "LOW",
            "reason":     str,
        }
    """
    if not diff_result.get("has_changes"):
        return {"risk_level": "LOW", "reason": "No changes detected"}

    # NON_MATERIAL check fires before all other tiers
    if is_non_material(diff_result):
        return {
            "risk_level": "NON_MATERIAL",
            "reason": (
                "Change is below materiality threshold: net diff < 80 chars "
                "and no obligation keywords detected."
            ),
            "matched_keywords": [],
            "non_material": True,
        }

    # F4: extraction-format shifts are OUR change, not the regulator's —
    # cap severity and say so instead of scoring adapter banners as risk.
    if _is_format_shift(diff_result):
        return {
            "risk_level": "MEDIUM",
            "rule": "FORMAT_SHIFT_REVIEW",
            "matched_keywords": [],
            "matched_context": [],
            "reason": (
                "Extraction format shift detected: the adapter output format "
                "changed between runs (structured listing on one side only). "
                "This is an extraction-layer change, not a confirmed "
                "regulatory change — adapter review recommended before "
                "relying on this diff."
            ),
        }

    combined_text = _delta_scoring_text(
        diff_result.get("added", []),
        diff_result.get("removed", []),
    )

    all_text = combined_text.lower()
    has_arabic = bool(_ARABIC_RE.search(combined_text))

    matched_high    = _match_terms(_HIGH_KEYWORDS, all_text)
    matched_context = _match_terms(_HIGH_CONTEXT_WORDS, all_text)
    matched_medium_ar: list[str] = []

    # F3: Arabic lane — match measured AR terms on folded text; merge into
    # the same severity ladder so EN and AR sentences rank alike.
    if has_arabic:
        from app.arabic_text import normalize_arabic

        ar_text = normalize_arabic(combined_text)
        matched_high    += [kw for kw in _AR_STRONG_KEYWORDS if kw in ar_text]
        matched_context += [cw for cw in _AR_CONTEXT_WORDS if cw in ar_text]
        matched_medium_ar = [kw for kw in _AR_MEDIUM_KEYWORDS if kw in ar_text]

        if not matched_high and not matched_medium_ar:
            # No measured term matched — no fake confidence: human review.
            return {
                "risk_level": "MEDIUM",
                "rule": "MEDIUM_ARABIC",
                "matched_keywords": [],
                "matched_context": [],
                "reason": (
                    "Arabic regulatory content detected with no matched "
                    "detection terms — human review required to assess risk."
                ),
            }

    # fix-self-pairing (structural guard): a context amplifier that is equal
    # to — or a word-bounded substring of — a matched strong keyword is the
    # SAME token self-pairing (e.g. "enforcement" inside "enforcement action").
    # Drop it so HIGH path 2 always requires a genuinely DISTINCT context
    # signal. Runs after the EN + AR context lists are fully assembled.
    matched_context = _drop_self_pairs(matched_context, matched_high)

    # A2 (alert-quality sprint): every reason names the ACTUAL matches.
    # Rule ids form the documented severity rubric (see module docstring).

    # HIGH path 1: two or more strong keywords
    if len(matched_high) >= 2:
        return {
            "risk_level": "HIGH",
            "rule": "HIGH_MULTIPLE_STRONG",
            "matched_keywords": matched_high,
            "matched_context": matched_context,
            "reason": (
                "High risk: multiple strong regulatory indicators matched in "
                f"the changed text: {', '.join(matched_high)}. "
                "Compliance review is required."
            ),
        }

    # HIGH path 2: one strong keyword confirmed by a context amplifier
    if len(matched_high) == 1 and matched_context:
        return {
            "risk_level": "HIGH",
            "rule": "HIGH_STRONG_PLUS_CONTEXT",
            "matched_keywords": matched_high,
            "matched_context": matched_context,
            "reason": (
                f"High risk: strong indicator '{matched_high[0]}' matched "
                f"together with context term(s): {', '.join(matched_context)}. "
                "Compliance review is required."
            ),
        }

    # MEDIUM: one strong keyword present but no context support
    if len(matched_high) == 1:
        return {
            "risk_level": "MEDIUM",
            "rule": "MEDIUM_SINGLE_STRONG",
            "matched_keywords": matched_high,
            "matched_context": [],
            "reason": (
                f"Medium risk: strong regulatory keyword '{matched_high[0]}' "
                "matched without supporting context. Compliance review is "
                "recommended."
            ),
        }

    # MEDIUM: moderate-change language
    matched_medium = _match_terms(_MEDIUM_KEYWORDS, all_text)
    if matched_medium:
        keyword = matched_medium[0]
        return {
            "risk_level": "MEDIUM",
            "rule": "MEDIUM_MODERATE_KEYWORD",
            "matched_keywords": [keyword],
            "matched_context": [],
            "reason": (
                f"Medium risk: moderate-change keyword '{keyword}' matched. "
                "No strong regulatory indicators matched. Compliance review "
                "is recommended."
            ),
        }

    # F3: Arabic moderate-change terms (law/decree/decision/regulation refs)
    if matched_medium_ar:
        return {
            "risk_level": "MEDIUM",
            "rule": "MEDIUM_MODERATE_KEYWORD",
            "matched_keywords": matched_medium_ar[:4],
            "matched_context": [],
            "reason": (
                "Medium risk: Arabic legislative reference term(s) matched: "
                f"{', '.join(matched_medium_ar[:4])}. Compliance review is "
                "recommended."
            ),
        }

    return {
        "risk_level": "LOW",
        "rule": "LOW_NO_KEYWORDS",
        "matched_keywords": [],
        "matched_context": [],
        "reason": (
            "Low risk: no strong regulatory keywords matched in the changed "
            "text. Continue routine monitoring."
        ),
    }
