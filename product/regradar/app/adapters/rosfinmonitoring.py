"""
Rosfinmonitoring (Федеральная служба по финансовому мониторингу) adapter.

Strategy
--------
fedsfm.ru exposes a public RSS feed at /rss that contains the 20 most
recent information messages with HTML descriptions.

SSL certificate verification is disabled because fedsfm.ru has a cert
chain mis-configuration that makes Tier-1 requests fail; Playwright
works around it, but we don't need Playwright here.

1. Fetch https://www.fedsfm.ru/rss (verify=False).
2. Parse the RSS XML (<channel><item> structure, no namespace).
3. Strip HTML markup from each <description> with the stdlib HTMLParser.
4. Build one block per item: title + clean description text.
5. Join the top _MAX_ITEMS blocks and return the combined text.

Fallback chain: if RSS fails for any reason, try /press then /documents
as plain HTML pages through the generic text extractor.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urlparse

import requests
import urllib3

from app.adapters.base import SourceAdapter
from app.config import HTTP_TIMEOUT_S, REQUESTS_UA

# fedsfm.ru has a cert chain issue — suppress the resulting urllib3 noise.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

_RSS_PATH  = "/rss"
_MAX_ITEMS = 10          # top N items from the feed (feed has 20 total)
_FALLBACKS = ["/press", "/documents"]


# ── HTML stripper ─────────────────────────────────────────────────────────────

class _HTMLStripper(HTMLParser):
    """Minimal HTML-to-text converter using the stdlib — zero extra deps."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(" ".join(self._parts).split())


def _strip_html(raw: str) -> str:
    s = _HTMLStripper()
    s.feed(raw)
    return s.get_text()


# ── Adapter ───────────────────────────────────────────────────────────────────

class RosfinmonitoringAdapter(SourceAdapter):
    """Source adapter for www.fedsfm.ru — RSS-driven extraction."""

    name = "rosfinmonitoring"

    def can_handle(self, url: str, source: dict | None = None) -> bool:
        return "fedsfm.ru" in url

    def fetch_content(self, url: str, source: dict | None = None) -> str | None:
        parsed = urlparse(url)
        base   = f"{parsed.scheme}://{parsed.netloc}"

        text = self._fetch_rss(base)
        if text:
            return text

        for path in _FALLBACKS:
            text = self._fetch_html_page(base, path)
            if text:
                return text

        return None

    # ── private helpers ───────────────────────────────────────────────────────

    def _fetch_rss(self, base: str) -> str | None:
        rss_url = base.rstrip("/") + _RSS_PATH
        try:
            resp = requests.get(
                rss_url,
                headers={"User-Agent": REQUESTS_UA},
                timeout=HTTP_TIMEOUT_S,
                verify=False,
                allow_redirects=True,
            )
        except Exception as exc:
            logger.warning("Rosfinmonitoring RSS fetch error: %s", exc)
            return None

        if resp.status_code != 200:
            logger.warning("Rosfinmonitoring RSS: HTTP %d", resp.status_code)
            return None

        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError as exc:
            logger.warning("Rosfinmonitoring RSS XML parse error: %s", exc)
            return None

        channel = root.find("channel")
        if channel is None:
            logger.warning("Rosfinmonitoring RSS: no <channel> element")
            return None

        blocks: list[str] = []
        for item in channel.findall("item")[:_MAX_ITEMS]:
            title = (item.findtext("title") or "").strip()
            desc  = _strip_html(item.findtext("description") or "")
            link  = (item.findtext("link")  or "").strip()
            parts = []
            if title:
                parts.append(title)
            if desc:
                parts.append(desc)
            if link:
                parts.append(link)
            if parts:
                blocks.append("\n".join(parts))

        if not blocks:
            logger.info("Rosfinmonitoring RSS: feed parsed but no items extracted")
            return None

        combined = "\n\n".join(blocks)
        logger.info(
            "Rosfinmonitoring adapter: %d chars from %d RSS items (rss)",
            len(combined), len(blocks),
        )
        return combined

    def _fetch_html_page(self, base: str, path: str) -> str | None:
        from app.parser import extract_text
        page_url = base.rstrip("/") + path
        try:
            resp = requests.get(
                page_url,
                headers={
                    "User-Agent":      REQUESTS_UA,
                    "Accept-Language": "ru-RU,ru;q=0.9",
                },
                timeout=HTTP_TIMEOUT_S,
                verify=False,
                allow_redirects=True,
            )
            if resp.status_code != 200:
                return None
            text = extract_text(resp.text) or None
            if text:
                logger.info(
                    "Rosfinmonitoring adapter: %d chars from fallback %s",
                    len(text), path,
                )
            return text
        except Exception as exc:
            logger.debug("Rosfinmonitoring fallback %s: %s", path, exc)
            return None
