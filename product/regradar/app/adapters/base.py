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

import requests

from app.text_quality import unreadable_char_count

logger = logging.getLogger(__name__)

# Content must exceed both thresholds to be accepted
_MIN_CONTENT_CHARS = 500
_MIN_CONTENT_PARAS = 3

# Undecodable-content guard: real page text decoded correctly contains
# essentially zero unreadable characters (see app/text_quality.py for the
# shared definition). A body that failed decoding (e.g. compressed bytes
# read as UTF-8) is saturated with them. Tolerate a small absolute number
# (sloppy server encodings emit a stray one or two) but reject saturation.
_UNREADABLE_CHAR_FLOOR = 8
_UNREADABLE_CHAR_RATIO = 0.02

# Hard ceiling on DECOMPRESSED response size for adapter fetches. With
# brotli installed, urllib3 transparently inflates br bodies whose
# compression ratio an attacker controls — a bounded chunked read is the
# only guard that limits peak memory (Content-Length reflects wire size,
# not decompressed size). Matches scraper.py's _MAX_RESPONSE_BYTES.
MAX_FETCH_BYTES = 10 * 1024 * 1024
_FETCH_CHUNK_BYTES = 64 * 1024


def read_bytes_bounded(response, max_bytes: int, label: str = "adapter") -> bytes | None:
    """
    Read a streamed requests response in chunks, aborting once the
    DECOMPRESSED size exceeds max_bytes. Returns None on overflow or
    read failure — never raises.
    """
    chunks: list[bytes] = []
    total = 0
    try:
        for chunk in response.iter_content(chunk_size=_FETCH_CHUNK_BYTES):
            total += len(chunk)
            if total > max_bytes:
                logger.warning(
                    "%s: response exceeded %d MB decompressed for %s — aborting read",
                    label, max_bytes // (1024 * 1024), response.url,
                )
                response.close()
                return None
            chunks.append(chunk)
    except Exception as exc:
        logger.warning("%s: bounded read failed for %s: %s", label, response.url, exc)
        return None
    return b"".join(chunks)


def fetch_text_bounded(
    url: str,
    *,
    headers: dict,
    timeout: float,
    max_bytes: int = MAX_FETCH_BYTES,
    label: str = "adapter",
) -> str | None:
    """
    HTTP GET with a hard cap on decompressed body size.

    Returns decoded text on success, None on any failure (request error,
    non-200 status, oversized body). Never raises.
    """
    try:
        response = requests.get(
            url, headers=headers, timeout=timeout, allow_redirects=True, stream=True
        )
    except Exception as exc:
        logger.warning("%s: request failed for %s: %s", label, url, exc)
        return None

    with response:
        if response.status_code != 200:
            logger.warning("%s: HTTP %d for %s", label, response.status_code, url)
            return None

        declared_len = response.headers.get("Content-Length")
        if declared_len is not None:
            try:
                if int(declared_len) > max_bytes:
                    logger.warning(
                        "%s: Content-Length %s exceeds %d MB limit for %s",
                        label, declared_len, max_bytes // (1024 * 1024), url,
                    )
                    return None
            except ValueError:
                pass  # malformed header; the bounded read below still protects us

        data = read_bytes_bounded(response, max_bytes, label=label)
        if data is None:
            return None

        encoding = response.encoding or response.apparent_encoding or "utf-8"
        try:
            return data.decode(encoding, errors="replace")
        except LookupError:
            return data.decode("utf-8", errors="replace")


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
    unreadable = unreadable_char_count(text)
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
