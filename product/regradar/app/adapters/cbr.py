"""
CBR (Central Bank of Russia) source adapter — v5.0.

Strategy
--------
cbr.ru's press-release list page (/press/pr/) and all section news pages
(/dkp/news/, /finstab/news/, etc.) are React SPAs — they return <100 chars
of extractable text because content loads via XHR at runtime.

However, CBR publishes a set of server-side-rendered (SSR) regulatory pages
that contain full text and are publicly accessible without authentication:

  /press/keypr/   — always shows the most recent key rate decision (4,800+ c)
  /dkp/w_infl/   — inflation dynamics and DKP commentary (4,200+ c)

These two pages alone exceed the 1,000-char threshold.  The adapter also
fetches CBR's HTML sitemap (/sitemap/) and probes additional pages from it
to supplement coverage when anchor pages fail or produce low content.

Extraction method reported: adapter:cbr:sitemap
"""

from __future__ import annotations

import logging
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.adapters.base import fetch_text_bounded, SourceAdapter
from app.config import HTTP_TIMEOUT_S, REQUESTS_UA
from app.parser import extract_text

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

# Pages confirmed SSR and content-rich.  Fetched first; if total ≥ 1000 chars,
# the sitemap walk is skipped entirely.
_ANCHOR_URLS: list[str] = [
    "https://cbr.ru/press/keypr/",   # latest key-rate press release
    "https://cbr.ru/dkp/w_infl/",   # inflation / monetary-policy commentary
]

_SITEMAP_URL = "https://cbr.ru/sitemap/"

# URL suffixes that reliably indicate React SPAs — skip them from sitemap.
_SPA_SKIP_SUFFIXES: tuple[str, ...] = ("/news/", "/subscribe/", "/search/")

# Minimum per-page extracted chars to keep a page's contribution.
_MIN_PAGE_CHARS = 100

# Max links collected from sitemap for probing.
_MAX_SITEMAP_CANDIDATES = 50

# Total page cap across anchors + sitemap (never exceeds this many HTTP GETs).
_MAX_PAGES_TOTAL = 10

# Chars threshold to stop the sitemap walk early.
_EARLY_STOP_CHARS = 1_000

_CBR_BASE = "https://cbr.ru"

_HEADERS = {
    "User-Agent":      REQUESTS_UA,
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fetch_page_text(url: str) -> str | None:
    """GET one page and return extracted paragraph text, or None on any error."""
    html = fetch_text_bounded(
        url, headers=_HEADERS, timeout=HTTP_TIMEOUT_S, label="CBRAdapter"
    )
    if html is None:
        return None
    return extract_text(html) or None


def _sitemap_candidates() -> list[str]:
    """
    Fetch CBR's HTML sitemap and return up to _MAX_SITEMAP_CANDIDATES
    internal links that are plausible SSR pages (not known SPA patterns).
    """
    html = fetch_text_bounded(
        _SITEMAP_URL, headers=_HEADERS, timeout=HTTP_TIMEOUT_S, label="CBRAdapter"
    )
    if html is None:
        logger.warning("CBR sitemap fetch failed")
        return []

    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    candidates: list[str] = []

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()

        # Only internal absolute paths
        if not href.startswith("/"):
            continue
        # Skip known SPA patterns
        if any(href.endswith(sfx) for sfx in _SPA_SKIP_SUFFIXES):
            continue
        # Skip anchor-only links
        if href == "/" or "#" in href:
            continue

        url = _CBR_BASE + href
        if url in seen:
            continue
        seen.add(url)

        # Skip the anchor pages — already handled
        if url in _ANCHOR_URLS:
            continue

        candidates.append(url)
        if len(candidates) >= _MAX_SITEMAP_CANDIDATES:
            break

    logger.debug("CBR adapter: %d sitemap candidates", len(candidates))
    return candidates


# ── Adapter ───────────────────────────────────────────────────────────────────

class CBRAdapter(SourceAdapter):
    """Source adapter for cbr.ru — sitemap-walker targeting SSR pages."""

    name = "cbr"

    def can_handle(self, url: str, source: dict | None = None) -> bool:
        return "cbr.ru" in url

    def fetch_content(self, url: str, source: dict | None = None) -> str | None:
        """
        Fetch SSR-rendered CBR pages and combine their text.

        Phase 1 — Anchor pages (always fetched first).
        Phase 2 — Sitemap walk (only if Phase 1 total < _EARLY_STOP_CHARS).

        Returns combined clean text, or None when everything fails.
        """
        blocks: list[str] = []
        pages_fetched = 0

        # ── Phase 1: anchor pages ─────────────────────────────────────────────
        for anchor in _ANCHOR_URLS:
            if pages_fetched >= _MAX_PAGES_TOTAL:
                break
            text = _fetch_page_text(anchor)
            pages_fetched += 1
            if text and len(text) >= _MIN_PAGE_CHARS:
                blocks.append(f"[{anchor}]\n{text}")
                logger.debug("CBR anchor %s: %d chars", anchor, len(text))

        total = sum(len(b) for b in blocks)

        if total >= _EARLY_STOP_CHARS:
            logger.info(
                "CBR adapter: %d chars from %d anchor page(s) — sitemap walk skipped",
                total, len(blocks),
            )
            return "\n\n".join(blocks)

        # ── Phase 2: sitemap walk ─────────────────────────────────────────────
        logger.info(
            "CBR adapter: anchor pages gave %d chars — trying sitemap walk", total
        )
        candidates = _sitemap_candidates()

        for candidate_url in candidates:
            if pages_fetched >= _MAX_PAGES_TOTAL:
                break
            text = _fetch_page_text(candidate_url)
            pages_fetched += 1
            if not text or len(text) < _MIN_PAGE_CHARS:
                continue
            blocks.append(f"[{candidate_url}]\n{text}")
            total += len(text)
            logger.debug("CBR sitemap page %s: %d chars", candidate_url, len(text))
            if total >= _EARLY_STOP_CHARS:
                break

        if not blocks:
            logger.info("CBR adapter: no extractable content found")
            return None

        combined = "\n\n".join(blocks)
        logger.info(
            "CBR adapter: %d chars from %d page(s) (adapter:cbr:sitemap)",
            len(combined), len(blocks),
        )
        return combined
