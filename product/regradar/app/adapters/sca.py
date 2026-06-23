"""
SCA (UAE Securities and Commodities Authority) adapter.

Handles public sca.gov.ae URLs for:
- Circulars:          https://www.sca.gov.ae/en/services/circulars.aspx
- Decisions:          https://www.sca.gov.ae/en/services/decisions.aspx
- Laws/Regulations:   https://www.sca.gov.ae/en/legislation/legislation.aspx

SCA publishes in Arabic and English. The adapter prefers English text where
present but does not strip Arabic — Arabic content is included in the stable
text so Arabic-only changes are not silently dropped.

Stable monitorable text is sorted by URL so publication-date reordering
does not trigger false-positive change signals.
"""

from __future__ import annotations

import hashlib
import re
from urllib.parse import urljoin, urlparse

import requests  # type: ignore
from bs4 import BeautifulSoup  # type: ignore

from app.adapters.base import SourceAdapter
from app.config import HTTP_TIMEOUT_S, REQUESTS_UA
from app.parser import extract_text  # type: ignore

_HEADERS = {
    "User-Agent": REQUESTS_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
}

_DATE_RE = re.compile(
    r"\b("
    r"\d{1,2}\s+(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|"
    r"Jul|July|Aug|August|Sep|Sept|September|Oct|October|Nov|November|"
    r"Dec|December)\s+\d{4}|"
    r"\d{4}-\d{2}-\d{2}|"
    r"\d{1,2}/\d{1,2}/\d{4}|"
    r"\d{4}/\d{1,2}/\d{1,2}"  # Arabic-style date order also seen on sca.gov.ae
    r")\b",
    re.IGNORECASE,
)

_NOISE_RE = re.compile(
    r"^(home|about|contact|privacy|terms|search|login|subscribe|read more|"
    r"cookie|accessibility|download|sitemap|careers|media|press|news|"
    r"arabic|english)$",
    re.IGNORECASE,
)

_ITEM_TYPE_MAP = {
    "circulars": "circular",
    "decisions": "decision",
    "legislation": "legislation",
    "laws": "legislation",
}


def _clean(value: str | None, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _extract_date(text: str | None) -> str | None:
    match = _DATE_RE.search(text or "")
    return match.group(1) if match else None


def _item_type_from_url(url: str) -> str:
    lower = url.lower()
    for key, label in _ITEM_TYPE_MAP.items():
        if key in lower:
            return label
    return "publication"


def _row_hash(row: dict) -> str:
    payload = "|".join([row.get("title") or "", row.get("url") or ""])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _is_sca_url(url: str) -> bool:
    try:
        return "sca.gov.ae" in urlparse(url).netloc.lower()
    except Exception:
        return False


def _extract_items(soup: BeautifulSoup, source_page_url: str) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        title = _clean(anchor.get_text(" ", strip=True), 240)
        if not title or _NOISE_RE.match(title) or len(title) < 6:
            continue
        href = (anchor.get("href") or "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        url = urljoin(source_page_url, href)
        if not _is_sca_url(url):
            continue

        container = anchor
        for _ in range(4):
            if getattr(container, "parent", None) is None:
                break
            container = container.parent
            if getattr(container, "name", None) in {"li", "article", "tr", "div", "section"}:
                break
        context = _clean(container.get_text(" ", strip=True), 600)

        key = url.lower()
        if key in seen:
            continue
        seen.add(key)

        row: dict = {
            "title": title,
            "url": url,
            "date": _extract_date(context),
            "item_type": _item_type_from_url(url),
            "source_page_url": source_page_url,
            "raw_text_snippet": context,
        }
        row["hash"] = _row_hash(row)
        items.append(row)

    # Sort by URL for stable hashing — not by date
    items.sort(key=lambda r: r.get("url") or "")
    return items


class SCAAdapter(SourceAdapter):
    """Adapter for UAE SCA circulars, decisions, and legislation listing pages."""

    name = "uae_sca"

    def can_handle(self, url: str, source: dict | None = None) -> bool:
        try:
            return "sca.gov.ae" in urlparse(url).netloc.lower()
        except Exception:
            return False

    def fetch_content(self, url: str, source: dict | None = None) -> str | None:
        try:
            response = requests.get(
                url, headers=_HEADERS, timeout=HTTP_TIMEOUT_S, allow_redirects=True
            )
        except Exception:
            return None
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
            tag.decompose()

        items = _extract_items(soup, url)
        if items:
            return self._format_listing(url, items)

        text = extract_text(response.text) or _clean(soup.get_text("\n", strip=True))
        if len(text) < 500:
            return None
        return f"UAE SCA official listing\n\nURL: {url}\n\n{text}"

    def _format_listing(self, url: str, items: list[dict]) -> str:
        blocks = ["UAE SCA regulatory listing", f"Source page: {url}"]
        for item in items:
            blocks.append(
                "\n".join([
                    f"Title: {item.get('title') or 'Untitled SCA item'}",
                    f"Date: {item.get('date') or 'not stated'}",
                    f"URL: {item.get('url') or ''}",
                    f"Type: {item.get('item_type') or ''}",
                    f"Hash: {item.get('hash') or ''}",
                ])
            )
        return "\n\n".join(blocks)
