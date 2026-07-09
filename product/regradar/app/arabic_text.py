"""F3 — Arabic text normalization for matching layers.

Used by risk scoring and fact detection so Arabic keyword matching is not
defeated by diacritics, kashida stretching, digit forms, or invisible
directional marks. This is a MATCHING normalization — the change-hash
normalization (text_normalization.py) stays conservative so stored evidence
text remains faithful to the source.

Scope is deliberately small and measured; no stemming, no taa-marbuta or
alef unification beyond hamza-carrier folding — those change meaning more
aggressively than the trail evidence justifies.
"""

from __future__ import annotations

import re

# Tashkeel (harakat), Quranic annotation subset, tatweel handled separately.
_DIACRITICS_RE = re.compile("[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]")

# Kashida / tatweel stretching character.
_TATWEEL = "ـ"

# Invisible directional / formatting marks that break substring matching.
_DIRECTIONAL_RE = re.compile("[\u200B-\u200F\u202A-\u202E\u2066-\u2069\uFEFF]")

# Arabic-Indic (٠-٩) and Eastern Arabic-Indic (۰-۹) digits, plus the
# Arabic thousands separator (٬) and decimal separator (٫).
_DIGIT_MAP = {ord(c): str(i) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩")}
_DIGIT_MAP.update({ord(c): str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")})
_DIGIT_MAP[ord("٬")] = ","
_DIGIT_MAP[ord("٫")] = "."

# Hamza-carrier alef variants fold to bare alef for matching only.
_ALEF_RE = re.compile(r"[أإآٱ]")


def normalize_arabic_digits(text: str) -> str:
    """Map Arabic-Indic and Eastern Arabic-Indic digits to ASCII digits."""
    if not text:
        return ""
    return str(text).translate(_DIGIT_MAP)


def normalize_arabic(text: str) -> str:
    """Fold Arabic text for keyword/fact matching.

    Removes diacritics, tatweel, and directional marks; unifies digit forms
    and hamza-carrier alefs; collapses whitespace.
    """
    if not text:
        return ""
    out = normalize_arabic_digits(str(text))
    out = _DIACRITICS_RE.sub("", out)
    out = out.replace(_TATWEEL, "")
    out = _DIRECTIONAL_RE.sub("", out)
    out = _ALEF_RE.sub("ا", out)
    return re.sub(r"\s+", " ", out).strip()


def arabic_share(text: str) -> float:
    """Fraction of non-space characters that are Arabic-script."""
    if not text:
        return 0.0
    chars = [c for c in text if not c.isspace()]
    if not chars:
        return 0.0
    arabic = sum(1 for c in chars if "؀" <= c <= "ۿ")
    return arabic / len(chars)
