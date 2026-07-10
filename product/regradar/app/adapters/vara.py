"""
VARA (Virtual Assets Regulatory Authority) adapter.

Handles all public VARA URLs across two hosts:
- www.vara.ae         — regulatory framework, notices, enforcement, news pages
- rulebooks.vara.ae   — rulebook listing pages, revision-update listings

PDF links (e.g. rulebooks.vara.ae/sites/default/files/…/VARA_EN_*.pdf) are
fetched and extracted via the shared document_extractor.extract_pdf_text helper.

can_handle() matches any URL whose host contains vara.ae.
Stable monitorable text for listing pages is sorted by URL so publication-date
reordering does not trigger false-positive change signals.
"""

from __future__ import annotations

import hashlib
import logging
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.adapters.base import (
    SourceAdapter,
    fetch_text_bounded,
    is_quality_content,
    read_bytes_bounded,
)
from app.config import HTTP_TIMEOUT_S, REQUESTS_UA
from app.document_extractor import extract_pdf_text
from app.parser import extract_text

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": REQUESTS_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    # No explicit Accept-Encoding: urllib3 advertises only codecs it can
    # actually decode (br/zstd only when the libs are installed). Hardcoding
    # "br" without the brotli package shipped compressed bytes into the
    # pipeline as mojibake (VARA public-register incident, 2026-07-10).
}

_PDF_HEADERS = {
    "User-Agent": REQUESTS_UA,
    "Accept": "application/pdf,*/*;q=0.8",
}

# Largest PDF we will download (bytes) — 15 MB matches DOCUMENT_MAX_DOWNLOAD_MB
_PDF_MAX_BYTES = 15 * 1024 * 1024

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
    r"cookie|accessibility|download|sitemap|careers|media|press releases|"
    r"news|arabic|english|back|next|previous)$",
    re.IGNORECASE,
)

# CSS selectors tried in order for listing pages — first that yields >= 3 items wins
_LISTING_SELECTORS = [
    ".view-content .views-row",
    ".view-content li",
    "article",
    ".rulebook-item",
    ".listing-item",
    "table tr",
    "li",
]

_ITEM_TYPE_MAP = {
    "compulsory-rulebook": "compulsory_rulebook",
    "compliance-and-risk": "compliance_rulebook",
    "va-activity": "activity_rulebook",
    "marketing-regulation": "marketing_rulebook",
    "rulebook": "rulebook",
    "regulatory-notice": "notice",
    "regulatory-framework": "framework",
    "enforcement": "enforcement",
    "circular": "circular",
    "guidance": "guidance",
    "view-revision-updates": "revision_update",
}


def _clean(value: str | None, limit: int | None = None) -> str:
    text = re.sub(r"[\s\xa0]+", " ", value or "").strip()
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


def _row_hash(title: str, url: str) -> str:
    payload = f"{title}|{url}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _is_vara_url(url: str) -> bool:
    try:
        return "vara.ae" in urlparse(url).netloc.lower()
    except Exception:
        return False


def _is_pdf_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return path.endswith(".pdf")


def _extract_listing_items(soup: BeautifulSoup, source_page_url: str) -> list[dict]:
    """
    Walk the page HTML and extract structured item records for each VARA
    publication link found.  Returns items sorted by URL for diff stability.
    """
    items: list[dict] = []
    seen: set[str] = set()

    # Try structured CSS selectors first
    anchor_pool: list = []
    for selector in _LISTING_SELECTORS:
        containers = soup.select(selector)
        if len(containers) >= 3:
            for container in containers:
                anchor_pool.extend(container.find_all("a", href=True))
            break

    # Fallback to full anchor walk
    if not anchor_pool:
        anchor_pool = soup.find_all("a", href=True)

    for anchor in anchor_pool:
        title = _clean(anchor.get_text(" ", strip=True), 240)
        if not title or _NOISE_RE.match(title) or len(title) < 6:
            continue
        href = (anchor.get("href") or "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        url = urljoin(source_page_url, href)
        if not _is_vara_url(url):
            continue

        key = url.lower()
        if key in seen:
            continue
        seen.add(key)

        # Walk up the DOM to collect container context
        container = anchor
        for _ in range(4):
            if getattr(container, "parent", None) is None:
                break
            container = container.parent
            if getattr(container, "name", None) in {"li", "article", "tr", "div", "section"}:
                break
        context = _clean(container.get_text(" ", strip=True), 600)

        row: dict = {
            "title": title,
            "url": url,
            "date": _extract_date(context),
            "item_type": _item_type_from_url(url),
            "is_pdf": _is_pdf_url(url),
            "source_page_url": source_page_url,
            "raw_text_snippet": context,
        }
        row["hash"] = _row_hash(title, url)
        items.append(row)

    items.sort(key=lambda r: r.get("url") or "")
    return items


def _format_listing(source_page_url: str, items: list[dict]) -> str:
    blocks = ["VARA regulatory listing", f"Source page: {source_page_url}"]
    for item in items:
        blocks.append(
            "\n".join([
                f"Title: {item.get('title') or 'Untitled VARA item'}",
                f"Date: {item.get('date') or 'not stated'}",
                f"URL: {item.get('url') or ''}",
                f"Type: {item.get('item_type') or ''}",
                f"PDF: {item.get('is_pdf', False)}",
                f"Hash: {item.get('hash') or ''}",
            ])
        )
    return "\n\n".join(blocks)


class VARAAdapter(SourceAdapter):
    """
    Production adapter for VARA (Virtual Assets Regulatory Authority) pages.

    Covers:
    - www.vara.ae regulatory pages (framework, notices, enforcement, news)
    - rulebooks.vara.ae listing pages and individual rulebook pages
    - VARA PDF documents (rulebooks, regulations, circulars)
    """

    name = "uae_vara"

    def can_handle(self, url: str, source: dict | None = None) -> bool:  # noqa: ARG002
        try:
            return "vara.ae" in urlparse(url).netloc.lower()
        except Exception:
            return False

    def fetch_content(self, url: str, source: dict | None = None) -> str | None:  # noqa: ARG002
        """
        Dispatch to the appropriate extraction strategy based on URL shape.

        Returns clean monitorable text, or None when extraction fails or
        content does not meet the quality gate.  Never raises.
        """
        try:
            if _is_pdf_url(url):
                return self._fetch_pdf(url)
            if "view-revision-updates" in url:
                return self._fetch_revision_listing(url)
            return self._fetch_html_page(url)
        except Exception as exc:
            logger.warning("VARAAdapter.fetch_content unexpected error for %s: %s: %s",
                           url, type(exc).__name__, exc)
            return None

    # ── private: PDF extraction ──────────────────────────────────────────────

    def _fetch_pdf(self, url: str) -> str | None:
        logger.debug("VARAAdapter: fetching PDF %s", url)
        try:
            response = requests.get(
                url,
                headers=_PDF_HEADERS,
                timeout=HTTP_TIMEOUT_S,
                allow_redirects=True,
                stream=True,
            )
        except Exception as exc:
            logger.warning("VARAAdapter: PDF request failed for %s: %s", url, exc)
            return None

        if response.status_code != 200:
            logger.warning("VARAAdapter: PDF HTTP %d for %s", response.status_code, url)
            return None

        # Guard against oversized documents
        content_length = int(response.headers.get("Content-Length", 0) or 0)
        if content_length > _PDF_MAX_BYTES:
            logger.warning("VARAAdapter: PDF too large (%d bytes) for %s", content_length, url)
            return None

        # Chunked read bounds peak memory even when Content-Length lies
        pdf_bytes = read_bytes_bounded(response, _PDF_MAX_BYTES, label="VARAAdapter")
        if pdf_bytes is None:
            return None

        result = extract_pdf_text(pdf_bytes)
        text = result.get("text") or ""
        if not text or len(text) < 200:
            logger.warning("VARAAdapter: PDF extraction low quality for %s (method=%s, chars=%d)",
                           url, result.get("method"), result.get("chars", 0))
            return None

        header = f"VARA regulatory document (PDF)\n\nURL: {url}\nMethod: {result.get('method', 'unknown')}\n"
        full_text = f"{header}\n{text}"
        if not is_quality_content(full_text):
            logger.debug("VARAAdapter: PDF text below quality gate for %s", url)
            return None
        return full_text

    # ── private: revision/update listing (rulebooks.vara.ae) ─────────────────

    def _fetch_revision_listing(self, url: str) -> str | None:
        logger.debug("VARAAdapter: fetching revision listing %s", url)
        html = fetch_text_bounded(
            url, headers=_HEADERS, timeout=HTTP_TIMEOUT_S, label="VARAAdapter"
        )
        if html is None:
            return None

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
            tag.decompose()

        items = _extract_listing_items(soup, url)
        if not items:
            logger.debug("VARAAdapter: no items found in revision listing %s", url)
            # Fall through to generic HTML extraction
            text = extract_text(html) or _clean(soup.get_text("\n", strip=True))
            if not is_quality_content(text):
                return None
            return f"VARA revision listing\n\nURL: {url}\n\n{text}"

        result = _format_listing(url, items)
        if not is_quality_content(result):
            logger.debug("VARAAdapter: revision listing below quality gate for %s", url)
            return None
        return result

    # ── private: generic HTML page ───────────────────────────────────────────

    def _fetch_html_page(self, url: str) -> str | None:
        logger.debug("VARAAdapter: fetching HTML page %s", url)
        html = fetch_text_bounded(
            url, headers=_HEADERS, timeout=HTTP_TIMEOUT_S, label="VARAAdapter"
        )
        if html is None:
            return None

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
            tag.decompose()

        # For listing pages, try structured item extraction first
        items = _extract_listing_items(soup, url)
        if items:
            result = _format_listing(url, items)
            if is_quality_content(result):
                return result

        # Trafilatura / readability via extract_text
        text = extract_text(html) or ""

        # BeautifulSoup fallback — target known VARA content regions
        if not is_quality_content(text):
            for selector in ("main", "article", ".content", ".regulatory-content",
                             ".field-body", ".field--type-text-with-summary", "[role='main']"):
                region = soup.select_one(selector)
                if region:
                    candidate = _clean(region.get_text("\n", strip=True))
                    if len(candidate) > len(text):
                        text = candidate
                        break

        # Final fallback: full body text
        if not is_quality_content(text):
            text = _clean(soup.get_text("\n", strip=True))

        if not is_quality_content(text):
            logger.debug("VARAAdapter: content below quality gate for %s", url)
            return None

        host_label = "VARA Rulebook" if "rulebooks.vara.ae" in url else "VARA"
        return f"{host_label} official page\n\nURL: {url}\n\n{text}"

    def __repr__(self) -> str:
        return f"VARAAdapter(name={self.name!r})"
