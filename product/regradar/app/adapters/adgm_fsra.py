"""
ADGM FSRA (Abu Dhabi Global Market — Financial Services Regulatory Authority) adapter.

NOTE: adgm.com circulars are already handled by uae_fsra_circulars.py for the
specific supervision/circulars path. This adapter extends coverage to the
broader ADGM FSRA regulatory framework pages:

- Regulations:    https://www.adgm.com/fsra/regulatory-framework/rules-and-regulations
- Notices:        https://www.adgm.com/fsra/regulatory-requirements/notices
- Consultations:  https://www.adgm.com/fsra/regulatory-requirements/consultations

can_handle() matches adgm.com hosts with fsra/regulatory-framework or
fsra/regulatory-requirements path prefixes (does NOT overlap with the
supervision/circulars path owned by FSRACircularsAdapter).

Stable monitorable text is sorted by URL so publication-date reordering
does not trigger false-positive change signals.
"""

from __future__ import annotations

import hashlib
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup  # type: ignore

from app.adapters.base import fetch_text_bounded, proxy_for_url, SourceAdapter
from app.config import HTTP_TIMEOUT_S, REQUESTS_UA
from app.parser import extract_text  # type: ignore

_HEADERS = {
    "User-Agent": REQUESTS_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

_DATE_RE = re.compile(
    r"\b("
    r"\d{1,2}\s+(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|"
    r"Jul|July|Aug|August|Sep|Sept|September|Oct|October|Nov|November|"
    r"Dec|December)\s+\d{4}|"
    r"\d{4}-\d{2}-\d{2}|"
    r"\d{1,2}/\d{1,2}/\d{4}"
    r")\b",
    re.IGNORECASE,
)

_NOISE_RE = re.compile(
    r"^(home|about|contact|privacy|terms|search|login|subscribe|read more|"
    r"cookie|accessibility|download|business areas|setting up|operating in|"
    r"public registers|legal framework|overview|publications|accessadgm)$",
    re.IGNORECASE,
)

_ITEM_TYPE_MAP = {
    "rules-and-regulations": "regulation",
    "notices": "notice",
    "consultations": "consultation",
}

# Paths this adapter owns — does not include supervision/circulars (owned by FSRACircularsAdapter)
_OWNED_PATH_PREFIXES = (
    "/fsra/regulatory-framework/",
    "/fsra/regulatory-requirements/",
)


def _clean(value: str | None, limit: int | None = None) -> str:
    # Collapse horizontal whitespace only (spaces, tabs, non-breaking spaces).
    # Newlines are preserved so that paragraph delimiters (\n\n) survive when
    # _clean() is called on multi-paragraph fallback body text — is_quality_content()
    # relies on \n\n to detect real prose paragraphs.
    text = re.sub(r"[ \t\xa0]+", " ", value or "")
    # Normalise runs of 3+ newlines down to a paragraph break, then strip.
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
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


def _is_adgm_url(url: str) -> bool:
    try:
        return urlparse(url).netloc.lower().endswith("adgm.com")
    except Exception:
        return False


def _extract_items(soup: BeautifulSoup, source_page_url: str) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        title = _clean(anchor.get_text(" ", strip=True), 240)
        if not title or _NOISE_RE.match(title) or len(title) < 8:
            continue
        href = (anchor.get("href") or "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        url = urljoin(source_page_url, href)
        if not _is_adgm_url(url):
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


class ADGMFSRAAdapter(SourceAdapter):
    """Adapter for ADGM FSRA regulatory framework and requirements listing pages."""

    name = "uae_adgm_fsra"

    def can_handle(self, url: str, source: dict | None = None) -> bool:
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        if not parsed.netloc.lower().endswith("adgm.com"):
            return False
        path = parsed.path.lower()
        # Do not claim paths owned by FSRACircularsAdapter
        if "supervision/circulars" in path:
            return False
        return any(path.startswith(prefix) for prefix in _OWNED_PATH_PREFIXES)

    def fetch_content(self, url: str, source: dict | None = None) -> str | None:
        html = fetch_text_bounded(
            url, headers=_HEADERS, timeout=HTTP_TIMEOUT_S, label="ADGMFSRAAdapter",
            proxy=proxy_for_url(url),
        )
        if html is None:
            return None

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
            tag.decompose()

        items = _extract_items(soup, url)
        if items:
            return self._format_listing(url, items)

        text = extract_text(html) or _clean(soup.get_text("\n\n", strip=True))
        if len(text) < 500:
            return None
        return f"ADGM FSRA official listing\n\nURL: {url}\n\n{text}"

    def _format_listing(self, url: str, items: list[dict]) -> str:
        blocks = ["ADGM FSRA regulatory listing", f"Source page: {url}"]
        for item in items:
            blocks.append(
                "\n".join([
                    f"Title: {item.get('title') or 'Untitled ADGM FSRA item'}",
                    f"Date: {item.get('date') or 'not stated'}",
                    f"URL: {item.get('url') or ''}",
                    f"Type: {item.get('item_type') or ''}",
                    f"Hash: {item.get('hash') or ''}",
                ])
            )
        return "\n\n".join(blocks)
