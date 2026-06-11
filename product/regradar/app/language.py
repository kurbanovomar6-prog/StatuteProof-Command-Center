"""
RegRadar v9 — Lightweight heuristic language detector.

detect_language_hint(text) → "ru" | "az" | "kk" | "uz" | "en" | "unknown"

This is a hint only — used to inform AI prompt context.  It does not need
to be perfect; occasional misclassifications are acceptable because the AI
itself reads the text and produces the correct output regardless of the hint.

Detection strategy
------------------
1. Count Cyrillic vs Latin alphabetic characters.
2. If Cyrillic-dominant: check for Kazakh-specific characters → "kk",
   otherwise → "ru".
3. If Latin-dominant: check for Azerbaijani-specific characters → "az",
   then Uzbek Latin markers → "uz",
   then common English function words → "en",
   otherwise → "unknown".
4. Mixed or very short text → "unknown".

No external libraries — stdlib only.
"""

from __future__ import annotations

# ── character sets ────────────────────────────────────────────────────────────

# Kazakh Cyrillic letters absent from the Russian alphabet.
# Two or more occurrences in a Cyrillic text is a strong Kazakh signal.
_KK_CHARS: frozenset[str] = frozenset("әғқңөұүһі")

# Azerbaijani Latin letters.
# ə (schwa) and ğ (soft g) are essentially unique to Azerbaijani in CIS context.
# The remaining — ı (dotless i), ş (sh), ç (ch), ö, ü — are shared with Turkish
# but within a CIS regulatory context they still strongly suggest Azerbaijani.
_AZ_STRONG: frozenset[str] = frozenset("əğ")   # highly distinctive
_AZ_WEAK:   frozenset[str] = frozenset("ışçöü") # common with Turkish

# Uzbek Latin markers:  apostrophe-digraphs and distinctive Uzbek words.
# These appear in official Uzbek Latin orthography (post-1993 reform).
_UZ_MARKERS: tuple[str, ...] = (
    "o'",          # o' = Uzbek ō (common in every Uzbek word)
    "g'",          # g' = Uzbek ğ
    "o'zbek",      # "Uzbek"
    "qaror",       # "decision / resolution"
    "moliya",      # "finance"
    "markaziy",    # "central"
    "respublika",  # "republic" (Uzbek spelling)
    "qonun",       # "law"
)

# English function words checked against a space-padded lowercase string so
# word-boundary matching works at sentence start and end too.
_EN_WORDS: tuple[str, ...] = (
    " the ",
    " of ",
    " and ",
    " to ",
    " in ",
    " for ",
    " on ",
    " with ",
    " from ",
    " that ",
    " are ",
    " is ",
    " this ",
    " which ",
    " has ",
    " have ",
    " by ",
    " an ",
    " a ",
    " at ",
    " be ",
    " or ",
)

# Common English regulatory / compliance content words.
# Checked as space-padded substrings against punctuation-stripped text so
# end-of-sentence words like "regulation." still match " regulation ".
_EN_REGULATORY_WORDS: tuple[str, ...] = (
    " central ",
    " bank ",
    " banks ",
    " financial ",
    " compliance ",
    " regulation ",
    " regulations ",
    " payment ",
    " payments ",
    " legal ",
    " risk ",
    " authority ",
    " report ",
    " reports ",
    " policy ",
    " policies ",
    " institution ",
    " institutions ",
    " provider ",
    " providers ",
    " requirement ",
    " requirements ",
    " deadline ",
    " published ",
    " update ",
    " updated ",
)

# Minimum character counts for reliable classification
_MIN_CYRILLIC = 10
_MIN_LATIN    = 10
_MIN_EN_HITS  = 3   # function words needed for guaranteed "en" classification


# ── public API ────────────────────────────────────────────────────────────────

def detect_language_hint(text: str) -> str:
    """
    Return a two-letter language code or "unknown" for `text`.

    Parameters
    ----------
    text : str
        Clean plain text (not HTML).  Works best with 100+ characters.

    Returns
    -------
    "ru" | "az" | "kk" | "uz" | "en" | "unknown"
    """
    if not text or not text.strip():
        return "unknown"

    t_lower = text.lower()
    # Strip punctuation so end-of-sentence words ("regulation.") still match
    # space-padded patterns (" regulation ").  Uzbek o'/g' markers are checked
    # against t_lower below, so stripping here doesn't affect them.
    t_plain  = "".join(c if c.isalpha() or c.isspace() else " " for c in t_lower)
    t_padded = " " + t_plain + " "

    cyrillic_count = sum(1 for c in text if "Ѐ" <= c <= "ӿ")
    latin_count    = sum(1 for c in text if "a" <= c <= "z" or "A" <= c <= "Z")

    # ── Cyrillic-dominant ─────────────────────────────────────────────
    if cyrillic_count >= _MIN_CYRILLIC and cyrillic_count >= latin_count:
        kk_hits = sum(1 for c in t_lower if c in _KK_CHARS)
        if kk_hits >= 2:
            return "kk"
        return "ru"

    # ── Latin-dominant ────────────────────────────────────────────────
    if latin_count >= _MIN_LATIN and latin_count > cyrillic_count:
        # Azerbaijani: one strong char is sufficient; or three weak chars
        az_strong_hits = sum(1 for c in t_lower if c in _AZ_STRONG)
        az_weak_hits   = sum(1 for c in t_lower if c in _AZ_WEAK)
        if az_strong_hits >= 1 or az_weak_hits >= 3:
            return "az"

        # Uzbek Latin: any single distinctive marker
        uz_hits = sum(1 for m in _UZ_MARKERS if m in t_lower)
        if uz_hits >= 1:
            return "uz"

        # English: function words + regulatory content words, both against the
        # punctuation-stripped padded string.
        # "en" is returned when:
        #   • ≥3 function words alone (original threshold), OR
        #   • ≥1 function word AND ≥1 regulatory word (mixed evidence), OR
        #   • ≥2 regulatory words alone (e.g. "financial institutions report")
        en_hits     = sum(1 for w in _EN_WORDS             if w in t_padded)
        en_reg_hits = sum(1 for w in _EN_REGULATORY_WORDS  if w in t_padded)
        if (en_hits >= _MIN_EN_HITS
                or (en_hits >= 1 and en_reg_hits >= 1)
                or en_reg_hits >= 2):
            return "en"

        return "unknown"

    # ── Mixed or insufficient data ────────────────────────────────────
    return "unknown"
