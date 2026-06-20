"""
CBUAE Rulebook adapter — registered in app.adapters.registry as CBUAERulebookAdapter.

Handles all public rulebook.centralbank.ae URLs:
- Revision-updates listing page: structured item extraction (title, date, row_hash)
- Individual rulebook pages: full text extraction via extract_text + BeautifulSoup fallback

can_handle() matches any URL whose host ends with rulebook.centralbank.ae.
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

DEFAULT_CBUAE_RULEBOOK_UPDATES_URL = (
    "https://rulebook.centralbank.ae/en/view-revision-updates?f_days=on&changed=-365%20day"
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

_NOISE = {
    "rulebook",
    "cbuae rulebook",
    "view updates",
    "advanced search",
    "home",
    "search",
    "login",
    "contact",
    "privacy policy",
    "terms and conditions",
}


def _clean(value: str | None, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _date(text: str) -> str | None:
    match = _DATE_RE.search(text or "")
    return match.group(1) if match else None


def _is_cbuae_rulebook_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    return parsed.netloc.lower().endswith("rulebook.centralbank.ae")


def _row_hash(row: dict) -> str:
    payload = "|".join([row.get("title") or "", row.get("date") or "", row.get("url") or ""])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _container_for(anchor) -> object:
    container = anchor
    for _ in range(4):
        if getattr(container, "parent", None) is None:
            break
        container = container.parent
        if getattr(container, "name", None) in {"tr", "li", "article", "section", "div"}:
            break
    return container


def _candidate_from_anchor(anchor, source_page_url: str) -> dict | None:
    title = _clean(anchor.get_text(" ", strip=True), 240)
    if not title or title.lower() in _NOISE or len(title) < 8:
        return None
    href = (anchor.get("href") or "").strip()
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    url = urljoin(source_page_url, href)
    if not _is_cbuae_rulebook_url(url):
        return None

    container = _container_for(anchor)
    context = _clean(container.get_text(" ", strip=True), 700)
    context_l = context.lower()
    url_l = url.lower()
    title_l = title.lower()
    has_update_signal = any(
        token in context_l or token in url_l or token in title_l
        for token in ("revision", "update", "amend", "rulebook", "regulation", "standard")
    )
    if not has_update_signal and not _date(context):
        return None

    row = {
        "title": title,
        "date": _date(context),
        "url": url,
        "document_url": None,
        "pdf_url": None,
        "source_page_url": source_page_url,
        "raw_text_snippet": context,
        "extraction_status": "row_candidate",
        "limitation_notes": [
            "Prototype extraction from CBUAE Rulebook revision/update HTML; repeated proof/diff required before activation."
        ],
    }
    row["row_hash"] = _row_hash(row)
    return row


def extract_cbuae_rulebook_update_items(
    source_page_url: str = DEFAULT_CBUAE_RULEBOOK_UPDATES_URL,
    timeout: int = HTTP_TIMEOUT_S,
) -> dict:
    """
    Fetch CBUAE Rulebook revision updates and return structured item candidates.

    Never raises to callers. Failed requests return extraction_status="failed".
    """
    try:
        response = requests.get(
            source_page_url,
            headers=_HEADERS,
            timeout=timeout,
            allow_redirects=True,
        )
    except Exception as exc:
        return {
            "source_page_url": source_page_url,
            "http_status": None,
            "item_count": 0,
            "items": [],
            "extraction_status": "failed",
            "limitation_notes": [f"Request failed: {type(exc).__name__}"],
        }

    if response.status_code != 200:
        return {
            "source_page_url": source_page_url,
            "http_status": response.status_code,
            "item_count": 0,
            "items": [],
            "extraction_status": "failed",
            "limitation_notes": [f"HTTP {response.status_code}; source not extractable in this run."],
        }

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    rows: list[dict] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        row = _candidate_from_anchor(anchor, source_page_url)
        if not row:
            continue
        key = f"{row['title'].lower()}|{row['url'].lower()}"
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)

    rows.sort(key=lambda row: ((row.get("date") or ""), row.get("title") or "", row.get("url") or ""))
    limitations = [
        "Scheduled comparison is required — same-run content is not a change-diff.",
    ]
    if not rows:
        limitations.append("No CBUAE revision/update rows were isolated from the current HTML response.")

    return {
        "source_page_url": source_page_url,
        "http_status": response.status_code,
        "item_count": len(rows),
        "items": rows,
        "extraction_status": "ok" if rows else "empty",
        "limitation_notes": limitations,
    }


class CBUAERulebookAdapter(SourceAdapter):
    """Production adapter for public CBUAE Rulebook pages and revision listings."""

    name = "uae_cbuae_rulebook"

    def can_handle(self, url: str, source: dict | None = None) -> bool:
        return _is_cbuae_rulebook_url(url)

    def fetch_content(self, url: str, source: dict | None = None) -> str | None:
        """Return stable monitorable text for CBUAE Rulebook URLs."""
        if "view-revision-updates" in url:
            return self._fetch_revision_listing(url)
        return self._fetch_rulebook_page(url)

    def _fetch_revision_listing(self, url: str) -> str | None:
        result = extract_cbuae_rulebook_update_items(url)
        rows = result.get("items") or []
        if not rows:
            return None
        blocks = [
            "CBUAE Rulebook revision updates",
            f"Source page: {result.get('source_page_url') or url}",
        ]
        for row in rows:
            blocks.append(
                "\n".join(
                    [
                        f"Title: {row.get('title') or 'Untitled update'}",
                        f"Date: {row.get('date') or 'not stated'}",
                        f"URL: {row.get('url') or ''}",
                        f"Hash: {row.get('row_hash') or ''}",
                        f"Context: {row.get('raw_text_snippet') or ''}",
                    ]
                )
            )
        return "\n\n".join(blocks)

    def _fetch_rulebook_page(self, url: str) -> str | None:
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
            text = _clean(soup.get_text("\n", strip=True))
        if len(text) < 500:
            return None
        return f"CBUAE Rulebook source\n\nURL: {url}\n\n{text}"
