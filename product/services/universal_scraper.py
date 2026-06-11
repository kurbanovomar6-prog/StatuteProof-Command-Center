"""
services/universal_scraper.py — Production-grade Universal AI-Driven Scraper.

Fetch pipeline:
  1. curl_cffi  — TLS-fingerprint spoofing, fast path, status-code-aware
  2. Playwright — stealth context (webdriver flag removed, realistic fingerprint),
                  networkidle wait + DOM scroll for SPAs, proxy injection

Error contract:
  - 403 / 404           → _FetchAborted raised immediately, no LLM tokens spent
  - 5xx / timeout       → exponential backoff, up to MAX_RETRIES attempts per layer
  - LLM validation fail → partial-recovery logging, empty PageAnalysis returned
  - Persist error       → per-item exception, remainder of batch continues

DB: RegulationRepository.upsert_raw()  (SQLite dev / PostgreSQL production)
"""
from __future__ import annotations

import logging
import random
import re
import time
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

# ── Stealth JS — injected before any page script executes ────────────────────
_STEALTH_JS = """(() => {
  Object.defineProperty(navigator, 'webdriver',          {get: () => undefined});
  Object.defineProperty(navigator, 'plugins',            {get: () => Array.from({length:5},(_,i)=>i)});
  Object.defineProperty(navigator, 'languages',          {get: () => ['ru-RU','ru','en-US','en']});
  Object.defineProperty(navigator, 'hardwareConcurrency',{get: () => 8});
  Object.defineProperty(navigator, 'platform',           {get: () => 'Win32'});
  if ('deviceMemory' in navigator)
    Object.defineProperty(navigator, 'deviceMemory',     {get: () => 8});
  if (!window.chrome) window.chrome = {runtime: {}};
  const _oq = navigator.permissions.query.bind(navigator.permissions);
  navigator.permissions.query = p =>
    p.name === 'notifications' ? Promise.resolve({state: Notification.permission}) : _oq(p);
})();"""

# ── Fingerprint rotation pools ────────────────────────────────────────────────
_USER_AGENTS = [
    # Chrome 124 Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Edge 124 Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    # Chrome 123 macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Safari 17 macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    # Firefox 125 Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    # Chrome 122 Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]
_VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1366, "height": 768},
]

# ── Lazy heavy imports ────────────────────────────────────────────────────────

def _instructor_client():
    import instructor
    from openai import OpenAI
    return instructor.from_openai(OpenAI())


def _html2text_converter():
    import html2text as _h2t
    h = _h2t.HTML2Text()
    h.ignore_links    = False
    h.ignore_images   = True
    h.body_width      = 0
    h.ignore_emphasis = True
    return h


# ── Pydantic output schemas ───────────────────────────────────────────────────

class DiscoveredItem(BaseModel):
    """One regulatory document or link found on a page."""
    title:            str = Field(...,   description="Document title or НПА name")
    publication_date: str = Field("",   description="ISO date YYYY-MM-DD or empty")
    document_url:     str = Field(...,   description="Absolute URL (http/https)")
    context_summary:  str = Field("",   description="1-2 sentence summary of what this document regulates")
    # URL validator intentionally absent — LLM often returns relative paths;
    # normalisation via urljoin() happens in _llm_discover() after model construction.


class PageAnalysis(BaseModel):
    """Structured result of one page analysis."""
    items:             list[DiscoveredItem] = Field(default_factory=list)
    has_pagination:    bool                 = Field(False)
    next_page_url:     str                  = Field("")
    page_type:         str                  = Field("unknown",
        description="'list' | 'document' | 'mixed' | 'unknown'")
    jurisdiction_hint: str                  = Field("",
        description="RU / KZ / AZ / BY / UZ inferred from page content")


# ── Error hierarchy ───────────────────────────────────────────────────────────

class _FetchAborted(Exception):
    """Non-retryable HTTP error (403/404). Raised to skip LLM processing."""
    def __init__(self, status: int):
        self.status = status
        super().__init__(f"HTTP {status} — aborting, will not retry")


# ── HTML cleaning utilities ───────────────────────────────────────────────────

_NOISE_TAGS = ["script", "style", "nav", "header", "footer",
               "aside", "form", "noscript", "iframe", "svg"]
_COOKIE_RE  = re.compile(
    r"cookie|куки|gdpr|privacy policy|политика конфиденциальности", re.I)
_DOC_EXT    = re.compile(r"\.(pdf|docx?|xlsx?|rtf|odt|zip)(\?|$)", re.I)
_DATE_RE    = re.compile(r"\b(20\d{2})[-./](0?[1-9]|1[0-2])[-./](0?[1-9]|[12]\d|3[01])\b")


def _clean_html(html: str, base_url: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(_NOISE_TAGS):
        tag.decompose()
    for tag in soup.find_all(True):
        text = (tag.get_text() or "").strip()
        if len(text) < 200 and _COOKIE_RE.search(text):
            tag.decompose()
    for a in soup.find_all("a", href=True):
        a["href"] = urljoin(base_url, a["href"])
    return str(soup)


def _to_markdown(html: str) -> str:
    return _html2text_converter().handle(html)


def _og_tags(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    og: dict = {}
    for meta in soup.find_all("meta"):
        prop    = meta.get("property", "") or meta.get("name", "")
        content = meta.get("content", "")
        if prop.startswith("og:") and content:
            og[prop[3:]] = content
    return og


def _cluster_doc_links(html: str, base_url: str) -> list[DiscoveredItem]:
    """Regex fallback: collect PDF/DOCX links with anchor-text dates."""
    soup  = BeautifulSoup(html, "lxml")
    items: list[DiscoveredItem] = []
    seen:  set[str]             = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        if href in seen or not _DOC_EXT.search(href):
            continue
        seen.add(href)
        anchor  = (a.get_text(separator=" ") or "").strip()[:300]
        dm      = _DATE_RE.search(anchor) or _DATE_RE.search(href)
        pub     = f"{dm.group(1)}-{int(dm.group(2)):02d}-{int(dm.group(3)):02d}" if dm else ""
        try:
            items.append(DiscoveredItem(
                title=anchor or urlparse(href).path.split("/")[-1],
                publication_date=pub,
                document_url=href,
            ))
        except Exception:
            pass
    return items


# ── Playwright helpers ────────────────────────────────────────────────────────

def _build_pw_context(pw, proxy: Optional[str] = None):
    """
    Return (browser, context) with full stealth fingerprint.
    proxy format: 'http://user:pass@host:port'  or  'http://host:port'
    """
    ua       = random.choice(_USER_AGENTS)
    viewport = random.choice(_VIEWPORTS)

    proxy_cfg: Optional[dict] = None
    if proxy:
        parsed    = urlparse(proxy)
        proxy_cfg = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
        if parsed.username:
            proxy_cfg["username"] = parsed.username
            proxy_cfg["password"] = parsed.password or ""

    browser = pw.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-extensions",
        ],
    )
    context = browser.new_context(
        user_agent=ua,
        viewport=viewport,
        locale="ru-RU",
        timezone_id="Europe/Moscow",
        proxy=proxy_cfg,
        java_script_enabled=True,
        accept_downloads=False,
        extra_http_headers={
            "Accept-Language":       "ru-RU,ru;q=0.9,en-US;q=0.5,en;q=0.3",
            "Accept":                "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "sec-ch-ua":             '"Chromium";v="124","Google Chrome";v="124","Not-A.Brand";v="99"',
            "sec-ch-ua-mobile":      "?0",
            "sec-ch-ua-platform":    '"Windows"',
        },
    )
    context.add_init_script(_STEALTH_JS)
    return browser, context


def _pw_load(page, url: str) -> str:
    """
    Navigate with networkidle; fall back to capturing the DOM on timeout.
    Scrolls to bottom to trigger lazy-loaded content.
    Raises _FetchAborted on 403/404.
    """
    from playwright.sync_api import TimeoutError as PWTimeout

    response = None
    try:
        response = page.goto(url, timeout=40_000, wait_until="networkidle")
    except PWTimeout:
        log.debug("pw: networkidle timeout — capturing current DOM for %s", url[:60])
        # Page may be fully rendered despite idle timeout (heavy analytics scripts)

    if response and response.status in (403, 404):
        raise _FetchAborted(response.status)

    # Ensure body is accessible
    try:
        page.wait_for_selector("body", timeout=5_000)
    except PWTimeout:
        pass

    # Scroll triggers lazy-loaded lists / infinite scroll sections
    try:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1_200)
    except Exception:
        pass

    return page.content()


# ── Main class ────────────────────────────────────────────────────────────────

class UniversalScraper:
    """
    Selector-free regulatory document scraper.
    LLM semantically discovers НПА on any page — no CSS, no XPath.

    Usage:
        scraper = UniversalScraper(proxy="http://user:pass@host:port")
        saved   = scraper.scrape_url("https://cbr.ru/press/pr/", "RU", max_pages=3)
    """

    LLM_MODEL    = "gpt-4o-mini"
    LLM_TOKENS   = 2_000
    LLM_TRUNCATE = 12_000   # markdown chars sent to LLM per page
    MAX_RETRIES  = 3        # for 5xx / transient errors in curl_cffi layer

    def __init__(self, proxy: Optional[str] = None) -> None:
        self.proxy = proxy

    # ── Public ───────────────────────────────────────────────────────────────

    def scrape_url(self, url: str, jurisdiction: str = "", max_pages: int = 5) -> int:
        """Scrape url and paginate up to max_pages. Returns count of new records saved."""
        saved_total = 0
        visited: set[str] = set()
        current  = url

        for page_num in range(1, max_pages + 1):
            if current in visited:
                break
            visited.add(current)

            log.info("universal_scraper: page %d/%d — %s", page_num, max_pages, current[:80])

            try:
                html = self._fetch_html(current)
            except _FetchAborted as e:
                log.warning("universal_scraper: %s for %s — stopping", e, current[:70])
                break

            if not html:
                log.warning("universal_scraper: empty response — %s", current[:70])
                break

            clean = _clean_html(html, current)
            md    = _to_markdown(clean)

            analysis = self._llm_discover(md, current, jurisdiction)

            if not analysis.items:
                log.info("universal_scraper: LLM found 0 items — running fallback for %s", current[:60])
                fallback = self._fallback_discover(html, current)
                if fallback:
                    analysis.items = fallback

            if analysis.items:
                saved         = self._persist(analysis.items, jurisdiction or analysis.jurisdiction_hint)
                saved_total  += saved
                log.info("universal_scraper: p%d found=%d saved=%d url=%s",
                         page_num, len(analysis.items), saved, current[:60])

            if analysis.has_pagination and analysis.next_page_url:
                nxt = analysis.next_page_url
                if nxt in visited:
                    break
                current = nxt
                time.sleep(1.5)
            else:
                break

        log.info("universal_scraper: done %s total_saved=%d", url[:60], saved_total)
        return saved_total

    # ── Fetch layer ───────────────────────────────────────────────────────────

    def _fetch_html(self, url: str) -> Optional[str]:
        """
        curl_cffi fast path → Playwright stealth fallback.
        - 403/404: raises _FetchAborted immediately (no LLM tokens wasted).
        - 5xx/timeout: retries with exponential back-off up to MAX_RETRIES.
        """
        try:
            from curl_cffi import requests as _cffi
            _has_cffi = True
        except ImportError:
            _has_cffi = False

        headers = {
            "User-Agent":      random.choice(_USER_AGENTS),
            "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
        }
        proxies = {"https": self.proxy, "http": self.proxy} if self.proxy else None

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                if _has_cffi:
                    r = _cffi.get(url, headers=headers, timeout=22,
                                  impersonate="chrome124", proxies=proxies)
                else:
                    import httpx
                    r = httpx.get(url, headers=headers, timeout=22,
                                  follow_redirects=True,
                                  proxies=self.proxy if self.proxy else None)

                if r.status_code in (403, 404):
                    raise _FetchAborted(r.status_code)

                if r.status_code == 429 or r.status_code >= 500:
                    wait = 2 ** attempt
                    log.warning("curl_cffi: HTTP %d for %s — backoff %ds (attempt %d/%d)",
                                r.status_code, url[:60], wait, attempt, self.MAX_RETRIES)
                    time.sleep(wait)
                    continue

                if r.status_code < 400 and r.text and len(r.text) > 500:
                    return r.text

                break   # unexpected small/empty body — fall through to Playwright

            except _FetchAborted:
                raise
            except Exception as exc:
                log.debug("curl_cffi attempt %d/%d failed for %s: %s",
                          attempt, self.MAX_RETRIES, url[:60], str(exc)[:80])
                if attempt < self.MAX_RETRIES:
                    time.sleep(2 ** attempt)

        # Playwright stealth fallback
        log.info("universal_scraper: curl_cffi exhausted — switching to Playwright for %s", url[:60])
        return self._playwright_fetch(url)

    def _playwright_fetch(self, url: str) -> Optional[str]:
        """Headless Chromium with stealth fingerprint. Raises _FetchAborted on 403/404."""
        try:
            from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
        except ImportError:
            log.warning("universal_scraper: playwright not installed")
            return None

        try:
            with sync_playwright() as pw:
                browser, context = _build_pw_context(pw, proxy=self.proxy)
                try:
                    page = context.new_page()
                    html = _pw_load(page, url)
                finally:
                    context.close()
                    browser.close()
            return html
        except _FetchAborted:
            raise
        except Exception as exc:
            log.warning("universal_scraper: Playwright error %s — %s", url[:60], str(exc)[:100])
            return None

    # ── LLM discovery ─────────────────────────────────────────────────────────

    def _llm_discover(self, markdown: str, base_url: str, jurisdiction: str = "") -> PageAnalysis:
        """
        instructor + gpt-4o-mini → structured PageAnalysis.
        On any failure: logs exc type + raw LLM message, returns empty PageAnalysis
        so the fallback chain runs rather than the task dying.
        """
        jur_hint = f"Jurisdiction: {jurisdiction}. " if jurisdiction else ""
        content  = markdown[: self.LLM_TRUNCATE]

        system = (
            "You are a regulatory intelligence specialist for CIS financial markets. "
            "Analyse the Markdown content of a regulator's web page "
            "(CBR, NBK, CBAR, NBRB, CBU, Minfinance, etc.) and extract structured data "
            "about НПА: orders, decrees, letters, regulations, standards, draft laws.\n"
            "IMPORTANT: document_url must be an absolute URL beginning with http/https. "
            "If you see a relative path, prepend the base URL provided."
        )
        user = f"{jur_hint}Base URL: {base_url}\n\nPage content (Markdown):\n\n{content}"

        try:
            client   = _instructor_client()
            analysis: PageAnalysis = client.chat.completions.create(
                model          = self.LLM_MODEL,
                response_model = PageAnalysis,
                max_tokens     = self.LLM_TOKENS,
                max_retries    = 1,
                messages       = [
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
            )
            # Normalise any relative URLs the model still returned
            for item in analysis.items:
                if item.document_url and not item.document_url.startswith("http"):
                    item.document_url = urljoin(base_url, item.document_url)
            if analysis.next_page_url and not analysis.next_page_url.startswith("http"):
                analysis.next_page_url = urljoin(base_url, analysis.next_page_url)
            return analysis

        except Exception as exc:
            # High-granularity logging for production debugging
            exc_name = type(exc).__name__
            raw_hint = ""
            if hasattr(exc, "last_completion"):            # instructor retry exhausted
                raw_hint = str(exc.last_completion)[:200]
            elif hasattr(exc, "errors") and callable(exc.errors):  # pydantic ValidationError
                raw_hint = "; ".join(
                    f"{'.'.join(str(l) for l in e['loc'])}={e['msg']}"
                    for e in exc.errors()[:4]
                )
            log.warning(
                "universal_scraper: LLM [%s] url=%s | %s%s",
                exc_name, base_url[:60], str(exc)[:120],
                f" | fields: {raw_hint}" if raw_hint else "",
            )
            return PageAnalysis()

    # ── Fallback discovery ────────────────────────────────────────────────────

    def _fallback_discover(self, html: str, base_url: str) -> list[DiscoveredItem]:
        """Link clustering → OG tags (two-level fallback, never raises)."""
        items = _cluster_doc_links(html, base_url)
        if items:
            return items
        og = _og_tags(html)
        if og.get("title") or og.get("description"):
            try:
                return [DiscoveredItem(
                    title           = og.get("title", urlparse(base_url).path),
                    document_url    = og.get("url", base_url),
                    context_summary = og.get("description", "")[:300],
                )]
            except Exception:
                pass
        return []

    # ── Persistence ───────────────────────────────────────────────────────────

    def _persist(self, items: list[DiscoveredItem], jurisdiction: str) -> int:
        """Write batch to RegulationRepository with versioning. Continues on per-item errors."""
        from app.infrastructure.db.repository import RegulationRepository
        repo  = RegulationRepository()
        saved = 0
        for item in items:
            if not item.document_url:
                continue
            try:
                raw = {
                    "source_url":       item.document_url,
                    "title":            (item.title or item.document_url)[:500],
                    "jurisdiction":     (jurisdiction or "").upper()[:2],
                    "publication_date": item.publication_date,
                    "effective_date":   item.publication_date,
                    "summary":          (item.context_summary or "")[:1000],
                    "industries":       "",
                    "critical_level":   "MEDIUM",
                    "confidence":       0.7,
                    "status":           "HUMAN_REVIEW",
                    "source_type":      "universal_scraper",
                }
                result = repo.upsert_raw_versioned(raw)
                if result.saved:
                    saved += 1
                if result.is_update and result.version_id:
                    from celery_app import analyze_delta_task
                    analyze_delta_task.delay(
                        version_id=result.version_id,
                        old_summary=result.old_summary or "",
                    )
            except Exception as exc:
                log.error("universal_scraper: persist error url=%s — %s",
                          item.document_url[:70], str(exc)[:120])
        return saved
