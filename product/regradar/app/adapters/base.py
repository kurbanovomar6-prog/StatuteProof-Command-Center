"""
Source adapter base class — v4.2.

Adapters provide source-specific content extraction for regulator websites
that defeat the generic two-tier scraper (requests → Playwright).

Contract
--------
• fetch_content() returns clean paragraph text, NOT raw HTML.
• Returns None when the adapter cannot extract meaningful content.
• Never raises — all exceptions must be caught internally.
• Logs failures at WARNING level.

Quality gate
------------
is_quality_content() is the shared helper used by the pipeline to decide
whether adapter output is good enough to use.  If the adapter's text does
not pass this check, the pipeline falls back to the generic scraper.
"""

import logging

logger = logging.getLogger(__name__)

# Content must exceed both thresholds to be accepted
_MIN_CONTENT_CHARS = 500
_MIN_CONTENT_PARAS = 3

# Undecodable-content guard: real page text decoded correctly contains
# essentially zero U+FFFD replacement characters or C0 control bytes.
# A body that failed decoding (e.g. compressed bytes read as UTF-8)
# is saturated with them. Tolerate a small absolute number (sloppy
# server encodings emit a stray one or two) but reject saturation.
_UNREADABLE_CHAR_FLOOR = 8
_UNREADABLE_CHAR_RATIO = 0.02


def _unreadable_char_count(text: str) -> int:
    """Count replacement characters and non-whitespace C0 control bytes."""
    return sum(
        1
        for ch in text
        if ch == "�" or (ord(ch) < 32 and ch not in "\n\r\t")
    )


def is_quality_content(text: str | None) -> bool:
    """
    Return True when adapter text is substantial enough to use.

    Checks:
      - text is not None or empty
      - at least _MIN_CONTENT_CHARS total characters
      - at least _MIN_CONTENT_PARAS non-empty double-newline paragraphs
      - not saturated with undecodable characters (binary or mis-decoded
        body must fall back to the generic scraper, never enter the diff)
    """
    if not text or len(text) < _MIN_CONTENT_CHARS:
        return False
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paras) < _MIN_CONTENT_PARAS:
        return False
    unreadable = _unreadable_char_count(text)
    if unreadable > _UNREADABLE_CHAR_FLOOR and unreadable / len(text) > _UNREADABLE_CHAR_RATIO:
        logger.warning(
            "is_quality_content: rejecting undecodable content — %d/%d (%.1f%%) "
            "replacement/control chars",
            unreadable, len(text), 100.0 * unreadable / len(text),
        )
        return False
    return True


class SourceAdapter:
    """
    Abstract base for source-specific content adapters.

    Subclasses must set ``name`` and implement ``can_handle`` and
    ``fetch_content``.
    """

    name: str = "base"

    def can_handle(self, url: str, source: dict | None = None) -> bool:
        """Return True when this adapter can service the given URL."""
        return False

    def fetch_content(self, url: str, source: dict | None = None) -> str | None:
        """
        Fetch and return clean paragraph text for the URL.

        Returns None when extraction is not possible or content quality
        is insufficient.  Must never raise.
        """
        return None
