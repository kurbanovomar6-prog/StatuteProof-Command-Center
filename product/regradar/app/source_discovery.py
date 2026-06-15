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
import xml.etree.ElementTree as ET
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

_PRIVATE_URL_RE = re.compile(
    r"(/|^)(login|log-in|signin|sign-in|account|auth|token|admin|private|captcha|paywall|checkout|cart)(/|$|[?#])",
    re.IGNORECASE,
)
_REGULATORY_SIGNAL_WORDS = frozenset({
    "aml",
    "cft",
    "sanction",
    "regulation",
    "regulations",
    "rulebook",
    "rule",
    "rules",
    "circular",
    "notice",
    "guidance",
    "consultation",
    "decision",
    "law",
    "enforcement",
    "publication",
    "register",
    "licensed",
    "payment",
    "financial",
    "virtual asset",
    "market",
})
_MARKETING_SIGNAL_WORDS = frozenset({
    "about",
    "careers",
    "contact",
    "services",
    "media",
    "gallery",
    "event",
    "events",
    "brand",
})
_JSON_MARKERS = ("application/json", "text/json", "+json")
_XML_MARKERS = ("application/xml", "text/xml", "+xml", "rss", "atom")
_PDF_MARKERS = ("application/pdf",)
_DOC_EXT_RE = re.compile(r"\.(pdf|docx?|xlsx?|csv)($|[?#])", re.IGNORECASE)
_SCA_ALLOWED_OPEN_DATA_SLUGS = (
    "/open-data/companies",
    "/open-data/licensed-companies",
    "/open-data/mutual-funds",
    "/open-data/warnings",
    "/open-data/violations-and-violators",
    "/open-data/finfluencers",
)
_SCA_GENERIC_PATH_FRAGMENTS = (
    "/about-us",
    "/services",
    "/media-center",
    "/contact",
    "/careers",
    "/open-data/open-data-policy",
    "/open-data/prosposerequest-data",
    "/open-data/numbers-and-statistics",
    "/open-data/sca-budget",
)


# ── private helpers ───────────────────────────────────────────────────────────

def _origin(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def _same_domain(url: str, base_url: str) -> bool:
    return _domain(url) == _domain(base_url)


def _strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child_text(node: ET.Element, name: str) -> str:
    for child in list(node):
        if _strip_ns(child.tag) == name:
            return (child.text or "").strip()
    return ""


def _clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _normalize_candidate_url(url: str) -> str:
    """Normalize known official-site path artifacts without changing authority."""
    parsed = urlparse(url)
    if parsed.netloc.lower() != "www.sca.gov.ae":
        return url
    path = parsed.path or ""
    while "/en/regulations/en/regulations/" in path:
        path = path.replace("/en/regulations/en/regulations/", "/en/regulations/")
    while "/en/regulations/en/" in path:
        path = path.replace("/en/regulations/en/", "/en/")
    rebuilt = parsed._replace(path=path).geturl()
    return rebuilt


def _is_sca_low_value_candidate(url: str, title: str = "", source_type: str = "") -> bool:
    """Reject official-but-low-value SCA chrome pages from default activation paths."""
    parsed = urlparse(url)
    if parsed.netloc.lower() != "www.sca.gov.ae":
        return False
    path = (parsed.path or "").lower()
    title_l = (title or "").lower()
    if any(fragment in path for fragment in _SCA_ALLOWED_OPEN_DATA_SLUGS):
        return False
    if any(fragment in path for fragment in _SCA_GENERIC_PATH_FRAGMENTS):
        return True
    generic_titles = {"about us", "services", "cma logo", "awards and achievements", "board of directors"}
    if title_l.strip() in generic_titles:
        return True
    if "/open-data/" in path and source_type not in {"register", "table"}:
        return True
    return False


def _private_url_reason(url: str) -> str:
    parsed = urlparse(url)
    pathish = f"{parsed.path}?{parsed.query}".lower()
    if parsed.username or parsed.password:
        return "credentials-in-url"
    if _PRIVATE_URL_RE.search(pathish):
        return "private/login/paywall-looking URL"
    return ""


def _regulatory_score_for_text(text: str) -> int:
    lowered = text.lower()
    return sum(1 for token in _REGULATORY_SIGNAL_WORDS if token in lowered)


def _infer_source_type(url: str, title: str = "", content_type: str = "", signals: list[str] | None = None) -> str:
    lowered = " ".join([url, title, content_type, " ".join(signals or [])]).lower()
    if ".pdf" in lowered or "application/pdf" in lowered:
        return "pdf_document"
    if any(marker in lowered for marker in _JSON_MARKERS):
        return "public_json_api"
    if any(marker in lowered for marker in ("rss", "atom", "feed")) and "json" not in lowered:
        return "feed"
    if "sitemap" in lowered:
        return "sitemap"
    if "register" in lowered or "licensed" in lowered or (
        "sca.gov.ae" in lowered and any(token in lowered for token in ("companies", "mutual-funds", "warnings", "violations-and-violators", "finfluencers"))
    ):
        return "register"
    if "rulebook" in lowered or "rulebook_module" in lowered:
        return "rulebook"
    if "table" in lowered:
        return "table"
    if any(token in lowered for token in ("regulation", "circular", "decision", "notice", "consultation", "publication", "listing")):
        return "listing"
    return "html_page"


def _adapter_for_source_type(source_type: str, url: str = "", title: str = "") -> tuple[str, str]:
    joined = f"{url} {title}".lower()
    if source_type == "public_json_api":
        return "public_json_api", "public_json_api"
    if source_type == "pdf_document":
        return "pdf_document", "pdf_document"
    if source_type == "feed" or source_type == "sitemap":
        return "sitemap_feed", "sitemap_feed"
    if source_type == "register":
        return "register", "register"
    if source_type == "table":
        return "table", "table"
    if source_type == "rulebook":
        return "dfsa_rulebook", "dfsa_rulebook" if "dfsa" in joined or "rulebook" in joined else "listing"
    if "sca.gov.ae" in joined:
        return "sca_listing", "sca_listing"
    if "centralbank" in joined or "cbuae" in joined:
        return "cbuae_document_listing", "cbuae_document_listing"
    if "adgm" in joined:
        return "adgm_fsra_listing", "adgm_fsra_listing"
    if "dfsa" in joined:
        return "dfsa_notice_listing", "dfsa_notice_listing"
    if "vara" in joined:
        return "vara_pdf_listing", "vara_pdf_listing"
    if "fiu" in joined or "eocn" in joined:
        return "fiu_eocn_document_listing", "fiu_eocn_document_listing"
    if source_type == "listing":
        return "listing", "listing"
    return "static_html", "static_html"


def parse_robots_sitemaps(robots_text: str) -> dict:
    """Extract Sitemap lines from robots.txt text without interpreting access as approval."""
    urls: list[str] = []
    for line in (robots_text or "").splitlines():
        stripped = line.strip()
        if not stripped.lower().startswith("sitemap:"):
            continue
        url = stripped.split(":", 1)[1].strip()
        if url and url not in urls:
            urls.append(url)
    return {
        "status": "parsed" if robots_text else "empty",
        "sitemap_urls": urls,
        "notes": "Robots data is used for discovery only; it is not used to bypass restrictions.",
    }


def parse_sitemap_xml(xml_text: str, sitemap_url: str = "") -> dict:
    """Parse sitemap index or urlset XML into normalized entries."""
    try:
        root = ET.fromstring(xml_text or "")
    except ET.ParseError as exc:
        return {"url": sitemap_url, "type": "invalid", "entries": [], "failure_reason": str(exc)}

    root_type = _strip_ns(root.tag)
    entries: list[dict] = []
    if root_type == "sitemapindex":
        for node in list(root):
            if _strip_ns(node.tag) != "sitemap":
                continue
            loc = _child_text(node, "loc")
            if loc:
                entries.append({"loc": loc, "lastmod": _child_text(node, "lastmod"), "entry_type": "sitemap"})
        parsed_type = "sitemapindex"
    elif root_type == "urlset":
        for node in list(root):
            if _strip_ns(node.tag) != "url":
                continue
            loc = _child_text(node, "loc")
            if loc:
                entries.append({
                    "loc": loc,
                    "lastmod": _child_text(node, "lastmod"),
                    "changefreq": _child_text(node, "changefreq"),
                    "entry_type": "url",
                })
        parsed_type = "urlset"
    else:
        parsed_type = "unknown"
    return {"url": sitemap_url, "type": parsed_type, "entries": entries}


def discover_feed_links_from_html(html: str, base_url: str) -> list[dict]:
    """Find RSS/Atom alternate links in HTML."""
    soup = BeautifulSoup(html or "", "html.parser")
    feeds: list[dict] = []
    seen: set[str] = set()
    for node in soup.select("link[href], a[href]"):
        href = str(node.get("href") or "").strip()
        if not href:
            continue
        rel = " ".join(node.get("rel") or []).lower() if node.name == "link" else ""
        type_ = str(node.get("type") or "").lower()
        text = _clean_text(node.get("title") or node.get_text(" ", strip=True)).lower()
        href_l = href.lower()
        is_feed = (
            "alternate" in rel and any(marker in type_ for marker in ("rss", "atom", "xml"))
        ) or any(marker in href_l for marker in ("/rss", "/feed", "atom.xml", "rss.xml")) or "rss" in text or "atom" in text
        if not is_feed:
            continue
        full = urljoin(base_url, href)
        if full in seen:
            continue
        seen.add(full)
        feeds.append({
            "url": full,
            "title": _clean_text(node.get("title") or node.get_text(" ", strip=True)) or "Feed",
            "source_type": "feed",
            "discovery_method": "html_feed_link",
        })
    return feeds[:20]


def parse_feed_xml(feed_text: str, feed_url: str = "") -> dict:
    """Parse RSS/Atom title/link/date candidates."""
    soup = BeautifulSoup(feed_text or "", "xml")
    items: list[dict] = []
    for node in soup.find_all(["item", "entry"]):
        title = _clean_text(node.find("title").get_text(" ", strip=True) if node.find("title") else "")
        link_node = node.find("link")
        link = ""
        if link_node:
            link = str(link_node.get("href") or link_node.get_text(" ", strip=True) or "").strip()
        date_node = node.find(["pubDate", "updated", "published"])
        date = _clean_text(date_node.get_text(" ", strip=True) if date_node else "")
        if title or link:
            items.append({"title": title, "url": urljoin(feed_url, link) if link else "", "date": date})
    return {"url": feed_url, "source_type": "feed", "items": items[:50], "item_count": len(items)}


def extract_document_links_from_html(html: str, base_url: str) -> list[dict]:
    """Extract public-looking document links from HTML."""
    soup = BeautifulSoup(html or "", "html.parser")
    docs: list[dict] = []
    seen: set[str] = set()
    for anchor in soup.select("a[href]"):
        href = str(anchor.get("href") or "").strip()
        if not href:
            continue
        full = urljoin(base_url, href)
        if full in seen or _private_url_reason(full):
            continue
        match = _DOC_EXT_RE.search(full.lower())
        if not match:
            continue
        ext = match.group(1).lower()
        seen.add(full)
        docs.append({
            "url": full,
            "title": _clean_text(anchor.get_text(" ", strip=True)) or full.rsplit("/", 1)[-1],
            "source_type": "pdf_document" if ext == "pdf" else "document",
            "adapter_family": "pdf_document" if ext == "pdf" else "document_listing",
            "discovery_method": "document_link",
            "content_type": f"application/{ext}",
            "linked_from_url": base_url,
        })
    return docs[:100]


def discover_same_domain_links(html: str, base_url: str, *, max_links: int = 50) -> dict:
    """Collect same-domain public candidate links and rejection reasons."""
    soup = BeautifulSoup(html or "", "html.parser")
    accepted: list[dict] = []
    rejected: list[dict] = []
    seen: set[str] = set()
    for anchor in soup.select("a[href]"):
        href = str(anchor.get("href") or "").strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
            continue
        full = _normalize_candidate_url(urljoin(base_url, href))
        if full in seen:
            continue
        seen.add(full)
        if not _same_domain(full, base_url):
            rejected.append({"url": full, "reason": "off-domain link"})
            continue
        private_reason = _private_url_reason(full)
        if private_reason:
            rejected.append({"url": full, "reason": private_reason})
            continue
        title = _clean_text(anchor.get_text(" ", strip=True))
        inferred_type = _infer_source_type(full, title, signals=["listing"])
        if _is_sca_low_value_candidate(full, title, inferred_type):
            rejected.append({"url": full, "reason": "low-value SCA chrome/generic page"})
            continue
        score = _regulatory_score_for_text(f"{full} {title}")
        if score == 0 and len(accepted) >= max_links:
            continue
        accepted.append({
            "url": full,
            "title": title,
            "source_type": inferred_type,
            "regulatory_score": score,
            "discovery_method": "same_domain_link",
        })
        if len(accepted) >= max_links:
            break
    accepted.sort(key=lambda row: (-int(row.get("regulatory_score") or 0), row.get("url") or ""))
    return {"accepted": accepted[:max_links], "rejected": rejected[:max_links]}


def classify_network_response(
    url: str,
    *,
    status_code: int,
    content_type: str,
    body_preview: str,
    page_url: str,
) -> dict:
    """Classify a captured browser/network response as a possible public endpoint."""
    full = urljoin(page_url, url)
    private_reason = _private_url_reason(full)
    same_domain = _same_domain(full, page_url)
    content_type_l = (content_type or "").lower()
    preview = (body_preview or "").strip()
    rejected = bool(private_reason or not same_domain or status_code >= 400)
    source_type = "unknown"
    adapter_family = ""
    if any(marker in content_type_l for marker in _JSON_MARKERS) or preview.startswith(("{", "[")):
        source_type = "public_json_api"
        adapter_family = "public_json_api"
    elif any(marker in content_type_l for marker in _PDF_MARKERS) or ".pdf" in full.lower():
        source_type = "pdf_document"
        adapter_family = "pdf_document"
    elif any(marker in content_type_l for marker in _XML_MARKERS) or preview.startswith("<"):
        source_type = "feed_or_xml"
        adapter_family = "sitemap_feed"

    if source_type == "unknown":
        rejected = True

    reason = ""
    if private_reason:
        reason = private_reason
    elif not same_domain:
        reason = "off-domain network endpoint"
    elif status_code >= 400:
        reason = f"HTTP {status_code}"
    elif source_type == "unknown":
        reason = "unsupported network content type"

    return {
        "candidate_url": full,
        "source_type": source_type,
        "discovery_method": "playwright_network",
        "official_status": "official_domain" if same_domain else "off_domain",
        "access_status": "public_fetch_candidate" if not rejected else "rejected",
        "adapter_family": adapter_family,
        "adapter_name": adapter_family,
        "content_type": content_type,
        "status_code": status_code,
        "confidence": 75 if not rejected else 0,
        "noise_risk": "medium" if source_type == "public_json_api" else "low",
        "source_health_risk": "medium",
        "failure_reason": reason,
        "remediation_hint": "" if not rejected else "Use only same-domain public unauthenticated endpoints.",
        "candidate_status": "candidate" if not rejected else "rejected",
        "next_action": "run_no_save_test" if not rejected else "reject",
    }


def capture_playwright_network_candidates(
    url: str,
    *,
    max_responses: int = 50,
    timeout_ms: int = 20_000,
) -> list[dict]:
    """Capture same-domain public JSON/XML/PDF candidates from a scoped Playwright page load."""
    safe, reason = validate_public_url(url)
    if not safe:
        return [{
            "candidate_url": url,
            "source_type": "unknown",
            "discovery_method": "playwright_network",
            "candidate_status": "rejected",
            "failure_reason": reason,
            "next_action": "reject",
        }]

    try:
        from app.scraper import _get_shared_browser
    except Exception as exc:
        return [{
            "candidate_url": url,
            "source_type": "unknown",
            "discovery_method": "playwright_network",
            "candidate_status": "rejected",
            "failure_reason": f"Playwright unavailable: {type(exc).__name__}",
            "next_action": "manual_review",
        }]

    candidates: list[dict] = []
    seen: set[str] = set()
    browser = _get_shared_browser()
    context = browser.new_context(user_agent=REQUESTS_UA)
    page = context.new_page()

    def _on_response(response) -> None:
        if len(candidates) >= max_responses:
            return
        response_url = response.url
        if response_url in seen:
            return
        seen.add(response_url)
        headers = response.headers or {}
        content_type = headers.get("content-type", "")
        if not any(marker in content_type.lower() for marker in (*_JSON_MARKERS, *_XML_MARKERS, *_PDF_MARKERS)) and not _DOC_EXT_RE.search(response_url.lower()):
            return
        body_preview = ""
        if any(marker in content_type.lower() for marker in (*_JSON_MARKERS, *_XML_MARKERS)):
            try:
                body_preview = response.text()[:5_000]
            except Exception:
                body_preview = ""
        candidates.append(classify_network_response(
            response_url,
            status_code=response.status,
            content_type=content_type,
            body_preview=body_preview,
            page_url=url,
        ))

    try:
        page.on("response", _on_response)
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        try:
            page.wait_for_timeout(1_500)
        except Exception:
            pass
    except Exception as exc:
        candidates.append({
            "candidate_url": url,
            "source_type": "unknown",
            "discovery_method": "playwright_network",
            "candidate_status": "rejected",
            "failure_reason": f"Network capture failed: {type(exc).__name__}: {exc}",
            "next_action": "manual_review",
        })
    finally:
        try:
            context.close()
        except Exception:
            pass

    return candidates[:max_responses]


def score_endpoint_candidate(candidate: dict, *, official_domain: str) -> dict:
    """Score and enrich an endpoint candidate without marking it active."""
    url = _normalize_candidate_url(str(candidate.get("candidate_url") or candidate.get("url") or ""))
    title = str(candidate.get("title") or "")
    content_type = str(candidate.get("content_type") or "")
    signals = list(candidate.get("signals") or [])
    same_domain = _domain(url) == official_domain.lower()
    linked_from_url = str(candidate.get("linked_from_url") or "")
    linked_from_official_page = bool(linked_from_url and _domain(linked_from_url) == official_domain.lower())
    private_reason = _private_url_reason(url)
    source_type = str(candidate.get("source_type") or _infer_source_type(url, title, content_type, signals))
    adapter_family, adapter_name = _adapter_for_source_type(source_type, url, title)
    signal_score = _regulatory_score_for_text(" ".join([url, title, " ".join(signals)]))
    officially_linked_document = (
        not same_domain
        and linked_from_official_page
        and str(candidate.get("discovery_method") or "") == "document_link"
        and source_type in {"pdf", "pdf_document", "document"}
    )
    confidence = 20 + (25 if same_domain else 15 if officially_linked_document else 0) + min(35, signal_score * 8)
    if source_type in {"public_json_api", "pdf_document", "feed", "sitemap", "listing", "table", "rulebook", "register"}:
        confidence += 15
    if private_reason:
        confidence = 0

    candidate_status = "candidate"
    failure_reason = ""
    remediation_hint = ""
    if private_reason:
        candidate_status = "rejected"
        failure_reason = private_reason
        remediation_hint = "Do not use private/login/auth/paywall-looking endpoints."
    elif _is_sca_low_value_candidate(url, title, source_type):
        candidate_status = "rejected"
        failure_reason = "Official SCA page is generic/chrome-heavy and not a default monitoring source."
        remediation_hint = "Use a specific regulations, circulars, AML/CFT, market rules, register, or warnings endpoint."
    elif officially_linked_document:
        candidate_status = "candidate"
        failure_reason = "Document is hosted off-domain but linked from an official source page; review provenance before evidence save."
        remediation_hint = "Treat as officially linked candidate only after Source Monitor and Legal Language review."
    elif not same_domain:
        candidate_status = "rejected"
        failure_reason = "Candidate is not on the official source domain."
        remediation_hint = "Use official or officially linked endpoints only."
    elif confidence < 45:
        candidate_status = "remediation"
        failure_reason = "Low regulatory/source relevance confidence."
        remediation_hint = "Review manually before no-save testing."

    noise = "medium" if source_type in {"listing", "register", "public_json_api"} else "low"
    health = "medium" if source_type in {"public_json_api", "listing", "register"} else "low"
    enriched = dict(candidate)
    enriched.update({
        "candidate_url": url,
        "source_type": source_type,
        "official_status": "official_domain" if same_domain else "officially_linked" if officially_linked_document else "off_domain",
        "access_status": "manual_review_required" if officially_linked_document else "public_candidate" if candidate_status != "rejected" else "rejected",
        "adapter_family": adapter_family,
        "adapter_name": adapter_name,
        "selector_hint": candidate.get("selector_hint", ""),
        "wait_selector_hint": candidate.get("wait_selector_hint", ""),
        "confidence": max(0, min(100, confidence)),
        "buyer_relevance": "MLRO/CCO regulatory monitoring" if signal_score else "manual relevance review required",
        "noise_risk": candidate.get("noise_risk") or noise,
        "source_health_risk": candidate.get("source_health_risk") or health,
        "failure_reason": candidate.get("failure_reason") or failure_reason,
        "remediation_hint": candidate.get("remediation_hint") or remediation_hint,
        "candidate_status": candidate.get("candidate_status") or candidate_status,
        "next_action": "manual_review" if officially_linked_document else "run_no_save_test" if candidate_status == "candidate" else "manual_review",
    })
    return enriched


def generate_source_candidate(candidate: dict, *, regulator: str = "", jurisdiction: str = "") -> dict:
    """Generate an inactive source work-queue candidate with agent gate placeholders."""
    url = str(candidate.get("candidate_url") or candidate.get("url") or "")
    slug = re.sub(r"[^a-z0-9]+", "-", urlparse(url).path.strip("/").lower()).strip("-") or "source"
    domain_slug = re.sub(r"[^a-z0-9]+", "-", urlparse(url).netloc.lower()).strip("-") or "official-source"
    proposed_id = candidate.get("proposed_source_id") or f"candidate-{domain_slug}-{slug}"[:96]
    now_reason = "Generated candidate only; no no-save, proof, baseline, or activation gate has passed."
    hold_gate = {"status": "hold", "reason": now_reason, "reviewed_at": "", "blocking_issues": ["no_save_not_run", "proof_missing", "baseline_missing"]}
    return {
        "proposed_source_id": proposed_id,
        "regulator": regulator,
        "jurisdiction": jurisdiction,
        "title": candidate.get("title") or candidate.get("candidate_url") or url,
        "official_url": url,
        "source_type": candidate.get("source_type", ""),
        "discovery_method": candidate.get("discovery_method", ""),
        "adapter_family": candidate.get("adapter_family", ""),
        "adapter_name": candidate.get("adapter_name", ""),
        "adapter_config": {},
        "expected_min_length": 500,
        "selector_hints": {
            "selector_hint": candidate.get("selector_hint", ""),
            "wait_selector_hint": candidate.get("wait_selector_hint", ""),
        },
        "buyer_relevance": candidate.get("buyer_relevance", "manual relevance review required"),
        "noise_risk": candidate.get("noise_risk", "unknown"),
        "source_health_risk": candidate.get("source_health_risk", "unknown"),
        "current_state": "candidate",
        "next_action": candidate.get("next_action", "run_no_save_test"),
        "source_monitor_gate": {"status": "hold", "reason": "Officialness and endpoint quality require review.", "reviewed_at": "", "blocking_issues": ["source_monitor_review_required"]},
        "evidence_trail_gate": hold_gate,
        "qa_critic_gate": {"status": "hold", "reason": "No no-save or evidence validation has run.", "reviewed_at": "", "blocking_issues": ["qa_review_required"]},
        "legal_language_gate": {"status": "hold", "reason": "Candidate must not be customer-facing as ready.", "reviewed_at": "", "blocking_issues": ["ready_claim_forbidden"]},
        "product_manager_gate": {"status": "hold", "reason": "Buyer relevance requires review.", "reviewed_at": "", "blocking_issues": ["buyer_relevance_review_required"]},
        "code_architect_gate": {"status": "hold", "reason": "Adapter config has not been tested.", "reviewed_at": "", "blocking_issues": ["adapter_test_required"]},
        "final_activation_gate": {"status": "candidate", "reason": now_reason},
    }


def _metadata_from_html(html: str, base_url: str) -> dict:
    soup = BeautifulSoup(html or "", "html.parser")
    title = _clean_text(soup.select_one("title").get_text(" ", strip=True) if soup.select_one("title") else "")
    canonical_node = soup.select_one("link[rel='canonical'][href]")
    canonical = urljoin(base_url, canonical_node.get("href")) if canonical_node else base_url
    desc_node = soup.select_one("meta[name='description'], meta[property='og:description']")
    description = _clean_text(desc_node.get("content") if desc_node else "")
    return {"page_title": title, "canonical_url": canonical, "meta_description": description}


def build_discovery_report_from_html(
    input_url: str,
    html: str,
    *,
    robots_text: str = "",
    sitemap_entries: list[dict] | None = None,
    network_candidates: list[dict] | None = None,
    max_links: int = 50,
) -> dict:
    """Build the structured no-save discovery contract from already-fetched HTML."""
    meta = _metadata_from_html(html, input_url)
    official_domain = _domain(input_url)
    robots = parse_robots_sitemaps(robots_text)
    feeds = discover_feed_links_from_html(html, input_url)
    documents = extract_document_links_from_html(html, input_url)
    links = discover_same_domain_links(html, input_url, max_links=max_links)
    soup = BeautifulSoup(html or "", "html.parser")

    table_candidates: list[dict] = []
    for idx, table in enumerate(soup.select("table")[:10], 1):
        table_candidates.append(score_endpoint_candidate({
            "candidate_url": input_url,
            "title": f"{meta['page_title']} table {idx}".strip(),
            "source_type": "table",
            "discovery_method": "dom_table",
            "selector_hint": "table",
            "signals": ["table", "register"] if "register" in input_url.lower() else ["table"],
        }, official_domain=official_domain))

    listing_candidates: list[dict] = []
    for node in soup.select("[data-icms-list], .listing, .list, main")[:5]:
        item_count = len(node.select("article, li, tr, .card, .item, a[href]"))
        if item_count >= 3:
            selector = "[data-icms-list]" if node.has_attr("data-icms-list") else (f".{node.get('class')[0]}" if node.get("class") else node.name)
            listing_candidates.append(score_endpoint_candidate({
                "candidate_url": input_url,
                "title": meta["page_title"] or "Listing candidate",
                "source_type": "listing",
                "discovery_method": "dom_listing",
                "selector_hint": selector,
                "wait_selector_hint": selector,
                "signals": ["listing", "regulation"],
            }, official_domain=official_domain))

    rulebook_candidates: list[dict] = []
    register_candidates: list[dict] = []
    for link in links["accepted"]:
        text = f"{link.get('url')} {link.get('title')}".lower()
        scored = score_endpoint_candidate({
            "candidate_url": link["url"],
            "title": link.get("title", ""),
            "source_type": link.get("source_type", ""),
            "discovery_method": link.get("discovery_method", "same_domain_link"),
            "signals": ["rulebook"] if "rulebook" in text else ["register"] if "register" in text else ["regulation"],
        }, official_domain=official_domain)
        if scored["source_type"] == "rulebook":
            rulebook_candidates.append(scored)
        elif scored["source_type"] == "register":
            register_candidates.append(scored)

    public_json_candidates = [
        cand for cand in (network_candidates or []) if cand.get("source_type") == "public_json_api" and cand.get("candidate_status") != "rejected"
    ]
    xhr_candidates = list(network_candidates or [])

    scored_documents = [
        score_endpoint_candidate({
            "candidate_url": doc["url"],
            "title": doc.get("title", ""),
            "source_type": doc.get("source_type", "document"),
            "discovery_method": "document_link",
            "content_type": doc.get("content_type", ""),
            "linked_from_url": doc.get("linked_from_url", input_url),
            "signals": ["publication", "guidance"],
        }, official_domain=official_domain)
        for doc in documents
    ]
    scored_feeds = [
        score_endpoint_candidate({
            "candidate_url": feed["url"],
            "title": feed.get("title", ""),
            "source_type": "feed",
            "discovery_method": feed.get("discovery_method", "html_feed_link"),
            "signals": ["feed", "publication"],
        }, official_domain=official_domain)
        for feed in feeds
    ]
    scored_links = [
        score_endpoint_candidate({
            "candidate_url": link["url"],
            "title": link.get("title", ""),
            "source_type": link.get("source_type", ""),
            "discovery_method": link.get("discovery_method", "same_domain_link"),
            "signals": ["regulation"] if link.get("regulatory_score") else [],
        }, official_domain=official_domain)
        for link in links["accepted"]
    ]
    sitemap_urls = robots["sitemap_urls"] + [entry.get("loc") for entry in (sitemap_entries or []) if entry.get("loc")]
    scored_sitemaps = [
        score_endpoint_candidate({
            "candidate_url": url,
            "title": "Sitemap URL",
            "source_type": "sitemap",
            "discovery_method": "sitemap",
            "signals": ["sitemap"],
        }, official_domain=official_domain)
        for url in sitemap_urls
    ]

    try:
        from app.dom_investigator import investigate_html
        dom_investigation = investigate_html(html, url=input_url)
    except Exception as exc:
        dom_investigation = {"failure_reason": f"DOM investigation failed: {type(exc).__name__}"}

    recommended = [
        *public_json_candidates,
        *listing_candidates,
        *table_candidates,
        *rulebook_candidates,
        *register_candidates,
        *scored_documents,
        *scored_feeds,
        *scored_sitemaps,
        *scored_links,
    ]
    recommended = [item for item in recommended if item.get("candidate_status") != "rejected"]
    recommended.sort(key=lambda item: (-int(item.get("confidence") or 0), item.get("candidate_url") or ""))

    return {
        "input_url": input_url,
        "final_url": meta["canonical_url"],
        "official_domain": official_domain,
        "page_title": meta["page_title"],
        "meta_description": meta["meta_description"],
        "robots_status": robots["status"],
        "sitemap_urls": sitemap_urls[:100],
        "feed_urls": scored_feeds[:50],
        "document_links": scored_documents[:100],
        "pdf_links": [doc for doc in scored_documents if doc.get("source_type") == "pdf_document"][:100],
        "public_json_candidates": public_json_candidates[:50],
        "xhr_candidates": xhr_candidates[:100],
        "listing_candidates": listing_candidates[:20],
        "table_candidates": table_candidates[:20],
        "rulebook_candidates": rulebook_candidates[:20],
        "register_candidates": register_candidates[:20],
        "same_domain_candidate_urls": scored_links[:max_links],
        "rejected_urls": links["rejected"][:max_links],
        "dom_investigation": dom_investigation,
        "warnings": [],
        "recommended_activation_paths": recommended[:50],
    }


def discover_source(
    url: str,
    *,
    use_js: bool = False,
    include_network: bool = False,
    include_sitemap: bool = True,
    include_feeds: bool = True,
    include_documents: bool = True,
    max_links: int = 50,
    max_depth: int = 1,
) -> dict:
    """Fetch one public URL and return structured no-save discovery output."""
    safe, reason = validate_public_url(url)
    if not safe:
        return {
            "input_url": url,
            "final_url": url,
            "official_domain": _domain(url),
            "robots_status": "blocked",
            "sitemap_urls": [],
            "feed_urls": [],
            "document_links": [],
            "pdf_links": [],
            "public_json_candidates": [],
            "xhr_candidates": [],
            "listing_candidates": [],
            "table_candidates": [],
            "rulebook_candidates": [],
            "register_candidates": [],
            "same_domain_candidate_urls": [],
            "rejected_urls": [],
            "warnings": [reason],
            "recommended_activation_paths": [],
        }

    html = ""
    final_url = url
    warnings: list[str] = []
    network_candidates: list[dict] = []
    http_status: int | None = None
    try:
        if use_js:
            html = _fetch_via_playwright(url)
        else:
            resp = _req.get(url, headers={"User-Agent": REQUESTS_UA, "Accept-Language": "en,ru;q=0.8"}, timeout=HTTP_TIMEOUT_S, allow_redirects=True)
            final_url = resp.url or url
            http_status = resp.status_code
            html = resp.text if resp.ok else ""
            if not resp.ok:
                warnings.append(f"HTTP {resp.status_code}")
    except Exception as exc:
        warnings.append(f"Fetch failed: {type(exc).__name__}: {exc}")

    robots_text = ""
    if include_sitemap:
        try:
            robots_resp = _req.get(_origin(final_url) + "/robots.txt", headers={"User-Agent": REQUESTS_UA}, timeout=_PROBE_TIMEOUT, allow_redirects=True)
            robots_text = robots_resp.text if robots_resp.ok else ""
        except Exception as exc:
            warnings.append(f"robots.txt fetch failed: {type(exc).__name__}")

    if include_network:
        network_candidates = capture_playwright_network_candidates(final_url, max_responses=max_links)

    report = build_discovery_report_from_html(
        final_url,
        html,
        robots_text=robots_text,
        network_candidates=network_candidates,
        max_links=max_links,
    )
    report["input_url"] = url
    report["final_url"] = report.get("final_url") or final_url
    report["warnings"].extend(warnings)
    if http_status and http_status >= 400:
        report["access_status"] = "blocked" if http_status in {401, 403} else "stale_or_unavailable"
        report["failure_code"] = "LIKELY_WAF_403" if http_status == 403 else "URL_STALE" if http_status == 404 else "ACCESS_BLOCKED"
        report["failure_reason"] = f"HTTP {http_status}"
        report["remediation_hint"] = (
            "Try safe official alternate discovery only: robots/sitemap, official same-domain pages, or public document links. "
            "Do not bypass access controls."
        )
        report["source_health_risk"] = "high"
        report["recommended_activation_paths"] = []
    else:
        report.setdefault("access_status", "public_candidate" if html else "unknown")
        report.setdefault("failure_code", "")
        report.setdefault("failure_reason", "")
        report.setdefault("remediation_hint", "")
        report.setdefault("source_health_risk", (report.get("dom_investigation") or {}).get("source_health_risk", "unknown"))
    report["discovery_options"] = {
        "use_js": use_js,
        "include_network": include_network,
        "include_sitemap": include_sitemap,
        "include_feeds": include_feeds,
        "include_documents": include_documents,
        "max_links": max_links,
        "max_depth": max_depth,
    }
    if not include_feeds:
        report["feed_urls"] = []
    if not include_documents:
        report["document_links"] = []
        report["pdf_links"] = []
    return report


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
