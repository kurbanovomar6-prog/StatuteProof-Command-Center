"""
DFSA (Dubai Financial Services Authority) adapter.

Handles public dfsa.ae URLs for:
- Rulebook:               https://www.dfsa.ae/rules-and-legislation/rulebook
- Policy/Regulatory dev:  https://www.dfsa.ae/news-and-publications/regulatory-developments
- Consultations:          https://www.dfsa.ae/news-and-publications/consultations

can_handle() matches only URLs whose host ends with dfsa.ae AND whose path
starts with one of the known monitorable path prefixes above.  Generic dfsa.ae
pages (e.g. /rules-and-standards, /about, /) are intentionally excluded so the
generic scraper handles them instead.
Stable monitorable text is sorted by URL so page re-ordering does not
produce false-positive change signals.
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
    r"cookie|accessibility|download|sitemap|careers|media centre|press releases)$",
    re.IGNORECASE,
)

_ITEM_SELECTORS = [
    ".regulatory-listing li",
    ".publication-list li",
    "article",
    ".card",
    "li",
]

_LABEL_MAP = {
    "rulebook": "rulebook",
    "rules-and-legislation": "rulebook",
    "regulatory-developments": "notice",
    "consultations": "consultation",
    "notice": "notice",
    "consultation": "consultation",
}


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
    for key, label in _LABEL_MAP.items():
        if key in lower:
            return label
    return "publication"


def _row_hash(row: dict) -> str:
    payload = "|".join([row.get("title") or "", row.get("url") or ""])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _is_dfsa_url(url: str) -> bool:
    try:
        return "dfsa.ae" in urlparse(url).netloc.lower()
    except Exception:
        return False


def _extract_items(soup: BeautifulSoup, source_page_url: str) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()

    # ── Primary: try structured CSS selectors first (faster, more precise) ──
    # _ITEM_SELECTORS are tried in order; first selector that yields >= 3 items wins.
    anchor_pool: list = []
    for selector in _ITEM_SELECTORS:
        containers = soup.select(selector)
        if len(containers) >= 3:
            # Extract all <a> tags from the matching containers
            for container in containers:
                anchor_pool.extend(container.find_all("a", href=True))
            break

    # ── Fallback: full anchor walk when no structured selector matched ──
    if not anchor_pool:
        anchor_pool = soup.find_all("a", href=True)

    for anchor in anchor_pool:
        title = _clean(anchor.get_text(" ", strip=True), 240)
        if not title or _NOISE_RE.match(title) or len(title) < 8:
            continue
        href = (anchor.get("href") or "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        url = urljoin(source_page_url, href)
        if not _is_dfsa_url(url):
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


class DFSAAdapter(SourceAdapter):
    """Production adapter for public DFSA regulatory publication pages."""

    name = "uae_dfsa"

    # Known monitorable path prefixes on dfsa.ae.
    _KNOWN_PATHS = (
        "/rules-and-legislation/",
        "/news-and-publications/regulatory-developments",
        "/news-and-publications/consultations",
    )

    def can_handle(self, url: str, source: dict | None = None) -> bool:
        try:
            parsed = urlparse(url)
            if not parsed.netloc.lower().endswith("dfsa.ae"):
                return False
            path = parsed.path.lower()
            return any(path.startswith(prefix) for prefix in self._KNOWN_PATHS)
        except Exception:
            return False

    def fetch_content(self, url: str, source: dict | None = None) -> str | None:
        html = fetch_text_bounded(
            url, headers=_HEADERS, timeout=HTTP_TIMEOUT_S, label="DFSAAdapter",
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
        return f"DFSA official publication\n\nURL: {url}\n\n{text}"

    def _format_listing(self, url: str, items: list[dict]) -> str:
        blocks = ["DFSA regulatory listing", f"Source page: {url}"]
        for item in items:
            blocks.append(
                "\n".join([
                    f"Title: {item.get('title') or 'Untitled DFSA item'}",
                    f"Date: {item.get('date') or 'not stated'}",
                    f"URL: {item.get('url') or ''}",
                    f"Type: {item.get('item_type') or ''}",
                    f"Hash: {item.get('hash') or ''}",
                ])
            )
        return "\n\n".join(blocks)
