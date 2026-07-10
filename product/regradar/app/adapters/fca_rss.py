"""
FCA (Financial Conduct Authority) RSS adapter.

Strategy
--------
fca.org.uk publishes a public RSS 2.0 feed at /news/rss.xml that lists
the most recent regulatory news, statements, and policy documents.

1. Fetch https://www.fca.org.uk/news/rss.xml.
2. Parse the RSS XML (<channel><item> structure, standard RSS 2.0,
   no custom namespace required for core fields).
3. Extract: title, link, pubDate, description per item.
4. CRITICAL — sort items by link URL (not by pubDate) before formatting.
   The FCA feed reorders items by date each run; sorting by the stable
   link identifier prevents spurious change detections on re-ordering.
5. Return one line per item: "{title} | {link}".
   This format is compact, diff-friendly, and machine-readable.

No fallback to generic scraping — if the RSS endpoint is unavailable,
return None so the pipeline falls through to its own generic scraper.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET


from app.adapters.base import fetch_bytes_bounded, SourceAdapter
from app.config import HTTP_TIMEOUT_S, REQUESTS_UA

logger = logging.getLogger(__name__)

_RSS_URL   = "https://www.fca.org.uk/news/rss.xml"
_MAX_ITEMS = 50   # cap to keep snapshot size bounded


class FCARSSAdapter(SourceAdapter):
    """Source adapter for fca.org.uk — RSS-driven, link-sorted extraction."""

    name = "fca_rss"

    def can_handle(self, url: str, source: dict | None = None) -> bool:  # noqa: ARG002
        return "fca.org.uk" in url

    def fetch_content(self, url: str, source: dict | None = None) -> str | None:  # noqa: ARG002
        """
        Fetch the FCA RSS feed and return sorted, stable one-line-per-item text.

        Returns None when the feed cannot be reached or yields no items.
        Never raises.
        """
        data = fetch_bytes_bounded(
            _RSS_URL,
            headers={"User-Agent": REQUESTS_UA},
            timeout=HTTP_TIMEOUT_S,
            label="FCARSSAdapter",
        )
        if data is None:
            logger.warning("FCA RSS fetch failed")
            return None

        try:
            root = ET.fromstring(data)
        except ET.ParseError as exc:
            logger.warning("FCA RSS XML parse error: %s", exc)
            return None

        channel = root.find("channel")
        if channel is None:
            logger.warning("FCA RSS: no <channel> element in feed")
            return None

        items: list[tuple[str, str]] = []  # (link, title)
        for item in channel.findall("item")[:_MAX_ITEMS]:
            title = (item.findtext("title") or "").strip()
            link  = (item.findtext("link")  or "").strip()
            if not link:
                continue
            items.append((link, title))

        if not items:
            logger.info("FCA RSS: feed parsed but no items with links extracted")
            return None

        # Sort by link URL — this is the stability guarantee.
        # pubDate ordering varies each run; link slugs are immutable once
        # an article is published.
        items.sort(key=lambda pair: pair[0])

        lines = [
            f"{title} | {link}" if title else link
            for link, title in items
        ]
        combined = "\n".join(lines)

        logger.info(
            "FCA RSS adapter: %d chars from %d items",
            len(combined), len(items),
        )
        return combined
