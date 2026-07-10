"""
Shared text-readability primitives (undecodable-content incident, 2026-07-10).

ONE place defines what counts as an "unreadable" character so the adapter
quality gate (app/adapters/base.py) and the customer-facing excerpt builder
(app/alert_content.py) can never drift apart — a divergence between those two
layers silently reopens one side of the mojibake guard.

A body that failed decoding (e.g. compressed bytes read as UTF-8) is
saturated with U+FFFD replacement characters and control bytes. Correctly
decoded page text — including Arabic, Cyrillic, CJK, emoji — contains
essentially none of them.

Detected as unreadable:
- U+FFFD replacement character (the UTF-8 errors="replace" signature)
- C0 controls except \\n \\r \\t
- DEL (U+007F) and the full C1 range (U+0080–U+009F) — the signature of
  Latin-1/CP1252-flavored mis-decodes. Legitimate page text never uses
  these; the caller-side floor/ratio thresholds absorb stray occurrences.
"""

from __future__ import annotations

_ALLOWED_CONTROL = "\n\r\t"


def is_unreadable_char(ch: str) -> bool:
    """True when the character indicates binary or mis-decoded content."""
    if ch == "�":
        return True
    code = ord(ch)
    if code < 0x20 or 0x7F <= code <= 0x9F:
        return ch not in _ALLOWED_CONTROL
    return False


def unreadable_char_count(text: str) -> int:
    """Count unreadable characters in text."""
    return sum(1 for ch in text if is_unreadable_char(ch))


def unreadable_ratio(text: str) -> float:
    """Fraction of unreadable characters in text (0.0 for empty input)."""
    if not text:
        return 0.0
    return unreadable_char_count(text) / len(text)


def strip_unreadable_chars(text: str) -> str:
    """Remove unreadable characters, keeping all legitimate content."""
    return "".join(ch for ch in text if not is_unreadable_char(ch))
