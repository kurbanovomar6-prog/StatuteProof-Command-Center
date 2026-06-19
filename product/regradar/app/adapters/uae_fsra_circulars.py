"""
ADGM FSRA circulars row-extraction prototype.

This adapter is intentionally not registered in app.adapters.registry. It is
used by scripts/validate_uae_sources.py for manual source-readiness validation
only and must not activate production monitoring by itself.
"""

from __future__ import annotations

import hashlib
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.adapters.base import SourceAdapter
from app.config import HTTP_TIMEOUT_S, REQUESTS_UA
from app.parser import extract_text

DEFAULT_FSRA_CIRCULARS_URL = (
    "https://www.adgm.com/operating-in-adgm/additional-obligations-of-"
    "financial-services-entities/supervision/circulars"
)

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
    r"cookie|accessibility|download|business areas|business|setting up|"
    r"operating in|public registers|legal framework|overview|publications|"
    r"accessadgm|accessrp|adgm ecourts platform|electronic prudential reporting)$",
    re.IGNORECASE,
)


def _clean_text(value: str | None, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _is_internal_adgm_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    host = parsed.netloc.lower()
    return host.endswith("adgm.com")


def _looks_like_circular_item(title: str, url: str, context: str) -> bool:
    title_l = title.lower()
    url_l = url.lower()
    context_l = context.lower()

    if not title or len(title) < 8 or _NOISE_RE.match(title):
        return False
    if not _is_internal_adgm_url(url):
        return False
    if url_l.endswith((".pdf", ".doc", ".docx")):
        return True
    has_date = bool(_extract_date(context))
    is_document = url_l.split("?", 1)[0].endswith((".pdf", ".doc", ".docx"))
    strong_markers = (
        "circular",
        "consultation",
        "guidance",
        "framework",
        "amendment",
        "notice",
        "publication",
    )
    weak_markers = ("fsra", "supervision", "financial services")
    has_strong_marker = any(marker in title_l or marker in url_l for marker in strong_markers)
    has_weak_marker = any(
        marker in title_l or marker in url_l or marker in context_l
        for marker in weak_markers
    )

    # Avoid counting generic ADGM service/navigation links as circular rows.
    return is_document or has_date or has_strong_marker or (has_weak_marker and has_date)


def _extract_date(text: str) -> str | None:
    match = _DATE_RE.search(text or "")
    return match.group(1) if match else None


def _row_hash(row: dict) -> str:
    payload = "|".join(
        [
            row.get("title") or "",
            row.get("date") or "",
            row.get("url") or "",
            row.get("document_url") or "",
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def extract_fsra_circular_items(
    source_page_url: str = DEFAULT_FSRA_CIRCULARS_URL,
    timeout: int = HTTP_TIMEOUT_S,
) -> dict:
    """
    Fetch the ADGM FSRA circulars page and return structured item candidates.

    The function never raises to callers. A failed fetch returns a result with
    extraction_status="failed" and an empty items list.
    """
    try:
        response = requests.get(
            source_page_url,
            headers=_HEADERS,
            timeout=timeout,
            allow_redirects=True,
        )
        http_status = response.status_code
    except Exception as exc:
        return {
            "source_page_url": source_page_url,
            "http_status": None,
            "item_count": 0,
            "items": [],
            "extraction_status": "failed",
            "limitation_notes": [f"Request failed: {type(exc).__name__}"],
        }

    if http_status != 200:
        return {
            "source_page_url": source_page_url,
            "http_status": http_status,
            "item_count": 0,
            "items": [],
            "extraction_status": "failed",
            "limitation_notes": [f"HTTP {http_status}; source not extractable in this run."],
        }

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    items: list[dict] = []
    seen: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        title = _clean_text(anchor.get_text(" ", strip=True), 220)
        href = (anchor.get("href") or "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue

        url = urljoin(source_page_url, href)
        container = anchor
        for _ in range(3):
            if container.parent is None:
                break
            container = container.parent
            if container.name in {"article", "li", "tr", "div", "section"}:
                break
        context = _clean_text(container.get_text(" ", strip=True), 600)

        if not _looks_like_circular_item(title, url, context):
            continue

        key = f"{title.lower()}|{url.lower()}"
        if key in seen:
            continue
        seen.add(key)

        is_document = url.lower().split("?", 1)[0].endswith((".pdf", ".doc", ".docx"))
        row = {
            "title": title or _clean_text(context, 160) or "Untitled FSRA item",
            "date": _extract_date(context),
            "url": url,
            "document_url": url if is_document else None,
            "pdf_url": url if url.lower().split("?", 1)[0].endswith(".pdf") else None,
            "source_page_url": source_page_url,
            "raw_text_snippet": context,
            "extraction_status": "row_candidate",
            "limitation_notes": [
                "Prototype row extraction; item-level suitability requires repeated validation before activation."
            ],
        }
        row["row_hash"] = _row_hash(row)
        items.append(row)

    items.sort(key=lambda item: ((item.get("date") or ""), item.get("title") or "", item.get("url") or ""))

    limitations = [
        "This adapter is not wired into production monitoring.",
        "Same-run stability is not a true change-diff; scheduled comparison is still required.",
    ]
    if not items:
        limitations.append("No circular rows were isolated from the current HTML response.")

    return {
        "source_page_url": source_page_url,
        "http_status": http_status,
        "item_count": len(items),
        "items": items,
        "extraction_status": "ok" if items else "empty",
        "limitation_notes": limitations,
    }


class FSRACircularsAdapter(SourceAdapter):
    """Production adapter for public ADGM/FSRA circular and listing pages."""

    name = "uae_fsra_circulars"

    def can_handle(self, url: str, source: dict | None = None) -> bool:
        try:
            parsed = urlparse(url)
        except Exception:
            return False
        host = parsed.netloc.lower()
        path = parsed.path.lower()
        if not host.endswith("adgm.com"):
            return False
        source_id = str((source or {}).get("source_id") or "").lower()
        adapter_name = str((source or {}).get("adapter_name") or "").lower()
        return (
            "supervision/circulars" in path
            or "regulatory-alerts" in path
            or "public-consultations" in path
            or "guidance" in path
            or "ra-circular" in source_id
            or adapter_name == "adgm_fsra_listing"
        )

    def fetch_content(self, url: str, source: dict | None = None) -> str | None:
        if "supervision/circulars" in url.lower():
            listing = self._fetch_circular_listing(url)
            if listing:
                return listing
        return self._fetch_generic_adgm_listing(url)

    def _fetch_circular_listing(self, url: str) -> str | None:
        result = extract_fsra_circular_items(url)
        items = result.get("items") or []
        if not items:
            return None
        blocks = [
            "ADGM FSRA circular listing",
            f"Source page: {result.get('source_page_url') or url}",
        ]
        for item in items:
            blocks.append(
                "\n".join(
                    [
                        f"Title: {item.get('title') or 'Untitled FSRA item'}",
                        f"Date: {item.get('date') or 'not stated'}",
                        f"URL: {item.get('url') or ''}",
                        f"Document URL: {item.get('document_url') or ''}",
                        f"Hash: {item.get('row_hash') or ''}",
                        f"Context: {item.get('raw_text_snippet') or ''}",
                    ]
                )
            )
        return "\n\n".join(blocks)

    def _fetch_generic_adgm_listing(self, url: str) -> str | None:
        try:
            response = requests.get(
                url,
                headers=_HEADERS,
                timeout=HTTP_TIMEOUT_S,
                allow_redirects=True,
            )
        except Exception:
            return None
        if response.status_code != 200:
            return None
        text = extract_text(response.text) or ""
        if len(text) < 500:
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "noscript", "nav", "footer", "header"]):
                tag.decompose()
            text = _clean_text(soup.get_text("\n", strip=True))
        if len(text) < 500:
            return None
        return f"ADGM FSRA official listing\n\nURL: {url}\n\n{text}"
