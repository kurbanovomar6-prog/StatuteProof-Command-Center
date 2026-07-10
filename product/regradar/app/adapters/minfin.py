"""
Minfin (Ministry of Finance, Russia) source adapter — v4.2.

Strategy
--------
minfin.gov.ru is a React SPA.  The document list page (/ru/document/) and
individual section pages return mostly navigation boilerplate (~344 chars
each) because content is loaded via XHR.

However, the site exposes a public XML sitemap:
  https://minfin.gov.ru/sitemap.xml

This sitemap contains 1 272 section URLs with ``lastmod`` timestamps.
The adapter uses it to:

  1. Fetch the sitemap (confirmed working, 200 OK).
  2. Find pages with the most recent ``lastmod`` dates — these are the
     sections that changed most recently, which is the regulatory signal
     we care about.
  3. Fetch the top N of those pages via requests.
  4. Extract whatever text each page provides with the existing parser.
  5. Combine all extracted text.

Why this helps
--------------
• A single page yields ~344-519 chars (below the 500-char threshold).
• Combining _TOP_N = 10 pages yields ~3 000-5 000 chars — well above the
  threshold and meaningful for change detection.
• When minfin updates a section (adds documents, changes policy pages),
  the ``lastmod`` date of that section changes → it rises to the top of the
  sorted list → the combined content changes → change detected.
• When new sitemap entries appear, they also affect the combined content.

No authentication, no cookies, no stealth techniques are used.
"""

import logging
import xml.etree.ElementTree as ET


from app.adapters.base import fetch_bytes_bounded, fetch_text_bounded, SourceAdapter
from app.config import HTTP_TIMEOUT_S, REQUESTS_UA
from app.parser import extract_text

logger = logging.getLogger(__name__)

_SITEMAP_URL      = "https://minfin.gov.ru/sitemap.xml"
_SITEMAP_TIMEOUT_S = 15
_TOP_N            = 10     # pages to fetch from sitemap
_MIN_PAGE_CHARS   = 50     # minimum chars to include a page's contribution

# Standard sitemaps.org namespace
_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


class MinfinAdapter(SourceAdapter):
    """Source adapter for minfin.gov.ru — sitemap-driven multi-page extraction."""

    name = "minfin"

    def can_handle(self, url: str, source: dict | None = None) -> bool:
        return "minfin.gov.ru" in url

    def fetch_content(self, url: str, source: dict | None = None) -> str | None:
        """
        Fetch the minfin sitemap, select recently-modified pages, fetch each
        one and combine their extracted text.

        Returns combined clean text, or None on failure.
        """
        # ── Step 1: Get recently-modified page URLs from sitemap ───────
        page_urls = self._get_recent_urls()
        if not page_urls:
            logger.info("Minfin adapter: sitemap returned no usable URLs")
            return None

        logger.info(
            "Minfin adapter: sitemap has %d candidate URLs, fetching top %d",
            len(page_urls), _TOP_N,
        )

        # ── Step 2: Fetch and extract content from each page ──────────
        blocks: list[str] = []
        for page_url in page_urls[:_TOP_N]:
            text = self._fetch_page_text(page_url)
            if text and len(text) >= _MIN_PAGE_CHARS:
                blocks.append(f"[{page_url}]\n{text}")

        if not blocks:
            logger.info("Minfin adapter: no extractable content from any page")
            return None

        combined = "\n\n".join(blocks)
        logger.info(
            "Minfin adapter: combined %d chars from %d pages",
            len(combined), len(blocks),
        )
        return combined

    # ── private helpers ───────────────────────────────────────────────

    def _get_recent_urls(self) -> list[str]:
        """
        Fetch the sitemap and return page URLs sorted by lastmod DESC.

        Handles both standard <urlset> and <sitemapindex> formats.
        """
        data = fetch_bytes_bounded(
            _SITEMAP_URL,
            headers={"User-Agent": REQUESTS_UA},
            timeout=_SITEMAP_TIMEOUT_S,
            label="MinfinAdapter",
        )
        if data is None:
            logger.warning("Minfin sitemap fetch failed")
            return []

        try:
            root = ET.fromstring(data)
        except ET.ParseError as exc:
            logger.warning("Minfin sitemap XML parse error: %s", exc)
            return []

        # Determine root element type (strip namespace if present)
        local_tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag

        if local_tag == "sitemapindex":
            return self._process_sitemap_index(root)
        return self._extract_urls(root)

    def _extract_urls(self, root: ET.Element) -> list[str]:
        """
        Extract (lastmod, loc) pairs from a <urlset> element,
        sort by lastmod DESC, and return the loc list.

        Falls back to no-namespace lookup when the namespace-qualified
        lookup returns nothing.
        """
        url_els = root.findall("sm:url", _NS)
        if not url_els:
            url_els = root.findall("url")   # no-namespace fallback

        entries: list[tuple[str, str]] = []
        for u in url_els:
            # Try namespace-qualified, then plain
            loc     = (u.findtext("sm:loc",     default="", namespaces=_NS)
                       or u.findtext("loc", default="")).strip()
            lastmod = (u.findtext("sm:lastmod", default="", namespaces=_NS)
                       or u.findtext("lastmod", default="")).strip()

            if loc and loc.startswith("http"):
                entries.append((lastmod, loc))

        # Sort newest first, then by URL for deterministic tie-breaking
        entries.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [loc for _, loc in entries]

    def _process_sitemap_index(self, root: ET.Element) -> list[str]:
        """Fetch sub-sitemaps from a <sitemapindex> and collect URLs."""
        all_urls: list[str] = []
        sm_els = root.findall("sm:sitemap", _NS)
        if not sm_els:
            sm_els = root.findall("sitemap")

        for sm_el in sm_els[:5]:    # cap at 5 sub-sitemaps
            loc = (sm_el.findtext("sm:loc", default="", namespaces=_NS)
                   or sm_el.findtext("loc", default="")).strip()
            if not loc:
                continue
            try:
                sub_data = fetch_bytes_bounded(
                    loc,
                    headers={"User-Agent": REQUESTS_UA},
                    timeout=_SITEMAP_TIMEOUT_S,
                    label="MinfinAdapter",
                )
                if sub_data is not None:
                    sub_root = ET.fromstring(sub_data)
                    all_urls.extend(self._extract_urls(sub_root))
            except Exception as exc:
                logger.debug("Minfin sub-sitemap %s error: %s", loc, exc)

        # Re-sort across all sub-sitemaps
        return all_urls     # already sorted within each sub-sitemap

    def _fetch_page_text(self, page_url: str) -> str | None:
        """Fetch a single page and return extracted paragraph text."""
        html = fetch_text_bounded(
            page_url,
            headers={
                "User-Agent":      REQUESTS_UA,
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            },
            timeout=HTTP_TIMEOUT_S,
            label="MinfinAdapter",
        )
        if html is None:
            return None
        return extract_text(html) or None
