"""
RegRadar — 6-layer source capability discovery (deep mode).

discover_source_capabilities(url, deep=False) → dict

Layer 1  Static HTML extraction   (requests + multi-extractor)
Layer 2  JS-rendered extraction   (Playwright — if Layer 1 is low/failed)
Layer 3  Sitemap / RSS / Atom     (deep=True only)
Layer 4  Document links + sample  (deep=True only)
Layer 5  Adapter recommendation   (embedded in verdict logic)
Layer 6  Structured report        (printed by run.py --deep)

Constraints
-----------
· No AI, no DB writes, no Telegram
· Every outbound URL validated before fetching
· Sitemap/feed link counts capped at DISCOVERY_MAX_LINKS
· Document samples capped at DISCOVERY_MAX_SAMPLE_DOCS
· Document download size capped at DOCUMENT_MAX_DOWNLOAD_MB
· No CAPTCHA/auth bypass; no global SSL disable
· Deep mode is opt-in; fast test-source behavior unchanged
"""

from __future__ import annotations

import logging
import re
from urllib.parse import urljoin, urlparse

import requests as _req
from bs4 import BeautifulSoup

from app.config import (
    DISCOVERY_MAX_LINKS,
    DISCOVERY_MAX_SAMPLE_DOCS,
    DOCUMENT_MAX_DOWNLOAD_MB,
    HTTP_TIMEOUT_S,
    REQUESTS_UA,
)
from app.extractors import extract_best_text
from app.scraper import _fetch_via_playwright, is_low_content_html
from app.source_tester import validate_public_url

logger = logging.getLogger(__name__)

# ── constants ─────────────────────────────────────────────────────────────────

_PROBE_TIMEOUT = 10   # seconds per feed/sitemap probe request
_GOOD_CHARS    = 1_000
_LOW_CHARS     = 100

_FEED_PATHS = (
    "/rss", "/rss.xml", "/feed", "/feed.xml", "/atom.xml",
    "/news/rss", "/press/rss", "/publications/rss",
    "/en/rss", "/en/feed", "/ru/rss",
)
_SITEMAP_PATHS = ("/sitemap.xml", "/sitemap_index.xml")

_DOC_EXTS = (".pdf", ".docx", ".xlsx", ".xls")

_LEGAL_KW = frozenset({
    "закон", "постановление", "приказ", "нормативн", "регуляци",
    "regulation", "law", "act", "decree", "order", "legal", "directive",
    "circular", "guidance", "consultation", "publication",
})
_NEWS_KW = frozenset({
    "news", "press", "новости", "пресс", "публикац",
    "announcement", "release",
})

_ROBOTS_SM_RE = re.compile(r"^Sitemap:\s*(\S+)", re.MULTILINE | re.IGNORECASE)
_LOC_RE       = re.compile(r"<loc>\s*(https?://[^\s<]+)\s*</loc>", re.IGNORECASE)
_FEED_MARKERS = ("<rss", "<feed", "<channel>", "xmlns:atom")


# ── private helpers ───────────────────────────────────────────────────────────

def _origin(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def _probe(url: str) -> tuple[int | None, str, str | None]:
    """
    GET url with a short timeout.  Validates safety first.
    Returns (http_status, content_type, text) or (None, "", None) on failure.
    """
    safe, _ = validate_public_url(url)
    if not safe:
        return None, "", None
    try:
        resp = _req.get(
            url,
            headers={"User-Agent": REQUESTS_UA, "Accept-Language": "ru,en;q=0.8"},
            timeout=_PROBE_TIMEOUT,
            allow_redirects=True,
        )
        ct = resp.headers.get("content-type", "")
        return resp.status_code, ct, (resp.text if resp.ok else None)
    except _req.RequestException as exc:
        logger.debug("discovery._probe %s: %s", url, exc)
        return None, "", None


def _quality(chars: int) -> str:
    if chars >= _GOOD_CHARS:
        return "good"
    if chars >= _LOW_CHARS:
        return "low_content"
    return "failed"


# ── Layer 3 helpers ───────────────────────────────────────────────────────────

def _discover_feeds(base_url: str) -> list[dict]:
    """Probe candidate feed paths on the same origin. Return valid feed dicts."""
    origin = _origin(base_url)
    found: list[dict] = []
    for path in _FEED_PATHS:
        candidate = origin + path
        status, ct, text = _probe(candidate)
        if status != 200 or not text:
            continue
        ct_l = ct.lower()
        head = text[:3_000].lower()
        is_feed = (
            any(m in ct_l for m in ("xml", "rss", "atom"))
            or any(m in head for m in _FEED_MARKERS)
        )
        if not is_feed:
            continue
        items = len(re.findall(r"<item[\s>]|<entry[\s>]", text, re.IGNORECASE))
        found.append({"url": candidate, "status": "ok", "items_found": items})
        if len(found) >= 3:
            break
    return found


def _discover_sitemaps(base_url: str) -> list[dict]:
    """Probe /sitemap.xml, /sitemap_index.xml, and robots.txt Sitemap: lines."""
    origin = _origin(base_url)
    candidates: list[str] = [origin + p for p in _SITEMAP_PATHS]

    _, _, robots = _probe(origin + "/robots.txt")
    if robots:
        for m in _ROBOTS_SM_RE.finditer(robots):
            sm = m.group(1).strip()
            safe, _ = validate_public_url(sm)
            if safe and sm not in candidates:
                candidates.append(sm)

    found: list[dict] = []
    seen:  set[str]   = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        status, _, text = _probe(candidate)
        if status != 200 or not text:
            continue
        if "<urlset" not in text and "<sitemapindex" not in text:
            continue
        locs  = _LOC_RE.findall(text)
        count = min(len(locs), DISCOVERY_MAX_LINKS)
        found.append({"url": candidate, "status": "ok", "links_found": count})
    return found


# ── Layer 4 helpers ───────────────────────────────────────────────────────────

def _extract_links(html: str, base_url: str) -> dict:
    """Parse HTML and return categorized link lists (no network calls)."""
    soup = BeautifulSoup(html, "html.parser")
    doc_links:   list[str] = []
    legal_links: list[str] = []
    news_links:  list[str] = []
    pub_links:   list[str] = []
    seen: set[str] = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
            continue
        try:
            full = urljoin(base_url, href)
            p = urlparse(full)
            if p.scheme not in ("http", "https") or not p.netloc or full in seen:
                continue
            seen.add(full)
            hl    = full.lower()
            tl    = tag.get_text(" ", strip=True).lower()
            combo = hl + " " + tl

            if any(hl.endswith(ext) for ext in _DOC_EXTS):
                if len(doc_links) < DISCOVERY_MAX_LINKS:
                    doc_links.append(full)
            if any(kw in combo for kw in _LEGAL_KW) and len(legal_links) < DISCOVERY_MAX_LINKS:
                legal_links.append(full)
            if any(kw in combo for kw in _NEWS_KW) and len(news_links) < DISCOVERY_MAX_LINKS:
                news_links.append(full)
            if len(pub_links) < DISCOVERY_MAX_LINKS:
                pub_links.append(full)
        except Exception:
            continue

    return {
        "publication_links": pub_links,
        "document_links":    doc_links,
        "legal_links":       legal_links,
        "news_links":        news_links,
    }


def _sample_documents(doc_links: list[str]) -> tuple[list[dict], int]:
    """
    Download and extract text from up to DISCOVERY_MAX_SAMPLE_DOCS document URLs.

    Returns (sample_results_list, extractable_count).
    extractable_count is the number of documents that yielded >= 100 chars.
    """
    from app.document_extractors import (
        extract_docx_text,
        extract_pdf_text,
        extract_xlsx_text,
    )

    max_bytes = DOCUMENT_MAX_DOWNLOAD_MB * 1_024 * 1_024
    samples:    list[dict] = []
    extractable = 0

    for url in doc_links[:DISCOVERY_MAX_SAMPLE_DOCS]:
        safe, _ = validate_public_url(url)
        if not safe:
            continue
        try:
            resp = _req.get(
                url,
                headers={"User-Agent": REQUESTS_UA},
                timeout=_PROBE_TIMEOUT,
                allow_redirects=True,
                stream=True,
            )
            if not resp.ok:
                samples.append({"url": url, "status": "failed", "chars": 0})
                continue

            buf = b""
            for chunk in resp.iter_content(chunk_size=65_536):
                buf += chunk
                if len(buf) >= max_bytes:
                    break

            hl = url.lower()
            if hl.endswith(".pdf"):
                text = extract_pdf_text(buf)
            elif hl.endswith(".docx"):
                text = extract_docx_text(buf)
            elif hl.endswith((".xlsx", ".xls")):
                text = extract_xlsx_text(buf)
            else:
                text = ""

            chars = len(text)
            if chars >= _LOW_CHARS:
                extractable += 1
            samples.append({"url": url, "status": "ok", "chars": chars})

        except Exception as exc:
            logger.debug("discovery._sample_documents %s: %s", url, exc)
            samples.append({"url": url, "status": "failed", "chars": 0})

    return samples, extractable


# ── empty result skeleton ──────────────────────────────────────────────────────

# ── client-facing scoring and verdict ─────────────────────────────────────────

def _readiness_score(result: dict) -> int:
    """
    Compute a 0–100 readiness score for client communication.

    Scoring (additive):
      +10  URL passed safety validation
      +15  page was reachable (HTTP response received)
      +30  good static HTML extraction
      +25  good JS-rendered extraction (Playwright)
      +10  Playwright reached the page but extraction is weak
      +25  valid RSS/Atom feed found
      +20  useful sitemap found
      +20  extractable documents found
      +10  more than 20 links found on page
      -20  low-content extraction with no feed/sitemap/document alternative

    Caps:
      cannot_monitor / unavailable → max 25
      needs_adapter                → max 60
    Clamp: 0–100.
    """
    page  = result.get("page", {})
    caps  = result.get("capabilities", {})
    links = result.get("links", {})

    score = 0

    if result.get("safe_url"):
        score += 10
    if page.get("status") == "ok":
        score += 15

    html_ok = caps.get("html_monitoring") and not page.get("used_playwright")
    js_ok   = caps.get("js_html_monitoring")

    if html_ok:
        score += 30
    elif js_ok:
        score += 25
    elif page.get("used_playwright") and page.get("quality") != "failed":
        score += 10  # Playwright reached the page but extraction is weak

    if caps.get("feed_monitoring"):
        score += 25
    if caps.get("sitemap_monitoring"):
        score += 20
    if caps.get("document_monitoring"):
        score += 20

    pub_links = len(links.get("publication_links", []))
    if pub_links > 20:
        score += 10

    # Penalty: low-content with no structural alternative
    q = page.get("quality", "failed")
    has_alternative = (
        caps.get("feed_monitoring")
        or caps.get("sitemap_monitoring")
        or caps.get("document_monitoring")
    )
    if q == "low_content" and not has_alternative:
        score -= 20

    # Caps by verdict
    verdict = result.get("verdict", "cannot_monitor")
    mode    = result.get("recommended_mode", "unavailable")
    if verdict == "cannot_monitor" or mode == "unavailable":
        score = min(score, 25)
    elif verdict == "needs_adapter":
        score = min(score, 60)

    return max(0, min(100, score))


_CLIENT_TITLES = {
    "ready":          "Ready for monitoring",
    "limited":        "Limited monitoring available",
    "custom_adapter": "Custom adapter recommended",
    "unavailable":    "Source unavailable",
}

_CLIENT_SUMMARIES = {
    "ready": (
        "StatuteProof found a reliable way to monitor this source automatically."
    ),
    "limited": (
        "StatuteProof can extract some public information from this source, "
        "but coverage may be incomplete or require closer review."
    ),
    "custom_adapter": (
        "The source is publicly accessible, but its structure requires a "
        "dedicated adapter for reliable ongoing monitoring."
    ),
    "unavailable": (
        "StatuteProof could not access this source reliably. "
        "A corrected URL or an alternative official source may be required."
    ),
}

_CLIENT_NEXT_STEPS = {
    "ready":          "Activate this source for production monitoring.",
    "limited":        "Consider activating for pilot monitoring with periodic review.",
    "custom_adapter": "Request a custom adapter for this source structure.",
    "unavailable":    "Verify the official URL and retest, or provide an alternative source.",
}


def _client_fields(result: dict, score: int) -> dict:
    """Return the four client-facing fields derived from discovery result + score."""
    verdict = result.get("verdict", "cannot_monitor")
    if verdict == "cannot_monitor":
        cv = "unavailable"
    elif verdict == "needs_adapter":
        cv = "custom_adapter"
    elif score >= 75:
        cv = "ready"
    else:
        cv = "limited"

    return {
        "client_verdict":   cv,
        "client_title":     _CLIENT_TITLES[cv],
        "client_summary":   _CLIENT_SUMMARIES[cv],
        "client_next_step": _CLIENT_NEXT_STEPS[cv],
        "readiness_score":  score,
    }


def _empty_result(url: str, safe: bool, reason: str) -> dict:
    base = {
        "url":      url,
        "safe_url": safe,
        "page": {
            "status": "failed", "http_status": None,
            "html_chars": 0, "extracted_chars": 0,
            "quality": "failed", "best_extractor": "none",
            "used_playwright": False,
        },
        "sitemaps": [],
        "feeds":    [],
        "links": {
            "publication_links": [], "document_links": [],
            "legal_links": [], "news_links": [],
        },
        "documents": {
            "pdf_links_found": 0, "docx_links_found": 0, "xlsx_links_found": 0,
            "sample_documents_tested": [], "extractable_documents": 0,
        },
        "capabilities": {
            "html_monitoring": False, "js_html_monitoring": False,
            "feed_monitoring": False, "sitemap_monitoring": False,
            "document_monitoring": False, "needs_adapter": False,
        },
        "recommended_mode": "unavailable",
        "verdict":          "cannot_monitor",
        "reason":           reason,
    }
    score = _readiness_score(base)
    base.update(_client_fields(base, score))
    return base


# ── public API ────────────────────────────────────────────────────────────────

def discover_source_capabilities(url: str, deep: bool = False) -> dict:
    """
    Run 6-layer source capability discovery.

    deep=False  Layers 1–2 only (HTML extraction + JS rendering).
    deep=True   All 6 layers including feed, sitemap, and document discovery.

    No AI · No DB writes · No Telegram · Safe anytime.
    """
    # ── Safety check ──────────────────────────────────────────────────
    safe, msg = validate_public_url(url)
    if not safe:
        return _empty_result(url, safe=False, reason=f"URL failed safety validation: {msg}")

    # ── Layer 1: Static HTML extraction ───────────────────────────────
    http_status: int | None = None
    raw_html:    str | None = None
    html_chars:  int        = 0

    try:
        resp = _req.get(
            url,
            headers={"User-Agent": REQUESTS_UA, "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"},
            timeout=HTTP_TIMEOUT_S,
            allow_redirects=True,
        )
        http_status = resp.status_code
        if resp.ok:
            raw_html   = resp.text
            html_chars = len(raw_html)
    except _req.RequestException as exc:
        logger.debug("discovery: Layer 1 failed for %s: %s", url, exc)

    tier1_low = (raw_html is None) or is_low_content_html(raw_html)

    # ── Layer 2: JS rendering (Playwright fallback) ───────────────────
    used_playwright = False
    if tier1_low:
        try:
            pw_html = _fetch_via_playwright(url)
            if pw_html and len(pw_html) > (html_chars or 0):
                raw_html        = pw_html
                html_chars      = len(pw_html)
                used_playwright = True
        except Exception as exc:
            logger.debug("discovery: Layer 2 (Playwright) failed for %s: %s", url, exc)

    # Extract text from best available HTML
    extr: dict = {"extracted_chars": 0, "method": "none", "quality": "failed", "candidates": []}
    if raw_html:
        extr = extract_best_text(raw_html, url)

    extracted_chars    = extr.get("extracted_chars", 0)
    best_extractor     = extr.get("method", "none")
    extraction_quality = _quality(extracted_chars)

    page_info = {
        "status":          "ok" if raw_html else "failed",
        "http_status":     http_status,
        "html_chars":      html_chars,
        "extracted_chars": extracted_chars,
        "quality":         extraction_quality,
        "best_extractor":  best_extractor,
        "used_playwright": used_playwright,
    }

    # ── Layer 3: Feed / Sitemap (deep only) ───────────────────────────
    feeds:    list[dict] = []
    sitemaps: list[dict] = []
    if deep:
        try:
            feeds    = _discover_feeds(url)
        except Exception as exc:
            logger.debug("discovery: feed discovery error: %s", exc)
        try:
            sitemaps = _discover_sitemaps(url)
        except Exception as exc:
            logger.debug("discovery: sitemap discovery error: %s", exc)

    # ── Layer 4: Document links + sample extraction ───────────────────
    links_info: dict = {
        "publication_links": [], "document_links": [],
        "legal_links": [], "news_links": [],
    }
    doc_info: dict = {
        "pdf_links_found": 0, "docx_links_found": 0, "xlsx_links_found": 0,
        "sample_documents_tested": [], "extractable_documents": 0,
    }

    if raw_html:
        links_info = _extract_links(raw_html, url)
        dl = links_info["document_links"]
        doc_info["pdf_links_found"]  = sum(1 for u in dl if u.lower().endswith(".pdf"))
        doc_info["docx_links_found"] = sum(1 for u in dl if u.lower().endswith(".docx"))
        doc_info["xlsx_links_found"] = sum(1 for u in dl if u.lower().endswith((".xlsx", ".xls")))

        if deep and dl:
            samples, extractable = _sample_documents(dl)
            doc_info["sample_documents_tested"] = samples
            doc_info["extractable_documents"]   = extractable

    # ── Layers 5–6: Capability flags + recommended mode ───────────────
    html_ok    = (extraction_quality == "good") and (not used_playwright)
    js_ok      = (extraction_quality == "good") and used_playwright
    feed_ok    = bool(feeds)
    sitemap_ok = any(s.get("links_found", 0) > 0 for s in sitemaps)
    doc_ok     = doc_info["extractable_documents"] > 0

    capabilities = {
        "html_monitoring":     html_ok,
        "js_html_monitoring":  js_ok,
        "feed_monitoring":     feed_ok,
        "sitemap_monitoring":  sitemap_ok,
        "document_monitoring": doc_ok,
        "needs_adapter":       False,
    }

    # Priority: feed > html > js_html > sitemap > documents > adapter > unavailable
    if feed_ok:
        recommended_mode = "feed"
        verdict = "can_monitor"
        f0 = feeds[0]
        reason = (
            f"RSS/Atom feed found at {f0['url']} ({f0.get('items_found', 0)} items). "
            "Feed monitoring recommended."
        )
    elif html_ok:
        recommended_mode = "html"
        verdict = "can_monitor"
        reason = (
            f"Static HTML extraction succeeded ({extracted_chars:,} chars via {best_extractor}). "
            "Ready for generic HTML monitoring."
        )
    elif js_ok:
        recommended_mode = "js_html"
        verdict = "can_monitor"
        reason = (
            f"JS-rendered extraction succeeded ({extracted_chars:,} chars via "
            f"Playwright + {best_extractor}). Ready for JS-rendered monitoring."
        )
    elif sitemap_ok:
        recommended_mode = "sitemap"
        verdict = "can_monitor"
        best_sm = max(sitemaps, key=lambda s: s.get("links_found", 0))
        reason = (
            f"Sitemap found at {best_sm['url']} with {best_sm['links_found']} links. "
            "Sitemap-based monitoring possible."
        )
    elif doc_ok:
        recommended_mode = "documents"
        verdict = "can_monitor"
        reason = (
            f"{doc_info['extractable_documents']} extractable document(s) found. "
            "Document-mode monitoring possible."
        )
    elif raw_html is not None:
        recommended_mode = "adapter"
        verdict = "needs_adapter"
        capabilities["needs_adapter"] = True
        reason = (
            f"Site is reachable (HTTP {http_status}) but extraction yielded only "
            f"{extracted_chars:,} chars — below threshold. "
            "No usable feed, sitemap, or documents found. "
            "A custom source adapter is recommended."
        )
    else:
        recommended_mode = "unavailable"
        verdict = "cannot_monitor"
        reason = (
            "Page could not be fetched after static and JS-rendered attempts. "
            "Likely DNS failure, SSL certificate error, connection timeout, or complete block."
        )

    result = {
        "url":              url,
        "safe_url":         True,
        "page":             page_info,
        "sitemaps":         sitemaps,
        "feeds":            feeds,
        "links":            links_info,
        "documents":        doc_info,
        "capabilities":     capabilities,
        "recommended_mode": recommended_mode,
        "verdict":          verdict,
        "reason":           reason,
    }
    score = _readiness_score(result)
    result.update(_client_fields(result, score))
    return result
