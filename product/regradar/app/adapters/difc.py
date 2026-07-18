"""
DIFC (Dubai International Financial Centre) adapter.

Handles all public www.difc.com URLs.  DIFC's website is built with the
Astro framework and uses client-side hydration.  Regular HTTP requests
receive HTTP 429 for virtually all paths.  Playwright (headless Chromium)
with wait_until="networkidle" is the only reliable way to obtain rendered
content.

This adapter therefore skips the requests tier entirely and goes straight
to Playwright.  It is registered at the TOP of the UAE adapter block in
registry.py so it is tried before any generic fallback.

can_handle() matches any URL whose host is www.difc.com.
"""

from __future__ import annotations

import logging
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.adapters.base import SourceAdapter, is_quality_content
from app.config import PAGE_TIMEOUT_MS, REQUESTS_UA

logger = logging.getLogger(__name__)

# ── constants ─────────────────────────────────────────────────────────────────

_DIFC_HOST = "www.difc.com"

# Playwright timeout for the content-selector wait (ms) — shorter than the
# overall page timeout so we don't block too long on missing containers.
_SELECTOR_TIMEOUT_MS = 15_000

# Characters of extracted listing items below which we fall back to full body
_LISTING_FALLBACK_THRESHOLD = 300

# Selectors to strip from the page before text extraction
_NOISE_TAGS = ["script", "style", "noscript", "nav", "footer", "header",
               "iframe", "form", "aside"]

# CSS selectors that identify DIFC listing containers (tried in order)
_LISTING_SELECTORS = [
    ".law-list",
    ".law-item",
    ".listing-item",
    ".card",
    ".article-card",
    "article",
    ".news-item",
    ".content-item",
    ".regulatory-item",
    ".item",
]

# CSS selectors for a primary content region (fallback for non-listing pages)
_CONTENT_SELECTORS = [
    "main",
    "[role='main']",
    ".content",
    ".page-content",
    ".main-content",
    "#content",
    ".container",
]

# Wait-for selector — any of these means the SPA has hydrated enough
_WAIT_SELECTOR = "main, article, .law-list, ul li a, h1, h2"

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

# Playwright availability cache
_playwright_available: bool | None = None


# ── helpers ───────────────────────────────────────────────────────────────────


def _clean(value: str | None, limit: int | None = None) -> str:
    """Collapse whitespace and optionally truncate."""
    text = re.sub(r"[\s\xa0]+", " ", value or "").strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def _strip_noise(soup: BeautifulSoup) -> None:
    """Remove boilerplate elements in-place."""
    for tag in soup(_NOISE_TAGS):
        tag.decompose()
    # DIFC cookie banner and chat widgets
    for sel in (".cookie-banner", ".cookie-bar", ".chat-widget", "#cookieBanner",
                "[aria-label='cookie']", ".gdpr", ".overlay", ".modal"):
        for el in soup.select(sel):
            el.decompose()


def _extract_date(element: BeautifulSoup) -> str:
    """Pull the first date-like string visible inside an element."""
    text = element.get_text(" ", strip=True)
    m = _DATE_RE.search(text)
    return m.group(0) if m else ""


def _extract_listing_items(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """
    Extract structured listing items from DIFC page types.

    Returns a list of dicts with keys: title, url, date.
    The list is sorted by URL for stable diffs.
    """
    items: list[dict] = []

    # Strategy 1: try known listing container selectors
    for sel in _LISTING_SELECTORS:
        containers = soup.select(sel)
        if not containers:
            continue
        for container in containers:
            anchor = container.find("a", href=True)
            if not anchor:
                continue
            title = _clean(anchor.get_text(" ", strip=True), limit=200)
            if not title or len(title) < 3:
                continue
            href = anchor.get("href", "")
            if href and not href.startswith("http"):
                href = urljoin(base_url, href)
            date = _extract_date(container)
            items.append({"title": title, "url": href, "date": date})
        if len(items) >= 3:
            break  # Found enough items in this selector pass

    # Strategy 2: search li elements with anchor children across the whole page
    if len(items) < 3:
        main = soup.select_one("main, [role='main'], .content, body")
        if main:
            for li in main.select("li"):
                anchor = li.find("a", href=True)
                if not anchor:
                    continue
                title = _clean(anchor.get_text(" ", strip=True), limit=200)
                if not title or len(title) < 5:
                    continue
                href = anchor.get("href", "")
                if href and not href.startswith("http"):
                    href = urljoin(base_url, href)
                date = _extract_date(li)
                # Avoid duplicates
                if not any(i["url"] == href for i in items):
                    items.append({"title": title, "url": href, "date": date})

    # Sort for stable diffs — ordering may change between renders
    items.sort(key=lambda d: d["url"])
    return items


def _items_to_text(items: list[dict]) -> str:
    """Render listing items as stable monitorable paragraph text."""
    parts: list[str] = []
    for item in items:
        line = f"Title: {item['title']}"
        if item.get("url"):
            line += f"\nURL: {item['url']}"
        if item.get("date"):
            line += f"\nDate: {item['date']}"
        parts.append(line)
    return "\n\n".join(parts)


# ── adapter ───────────────────────────────────────────────────────────────────


class DIFCAdapter(SourceAdapter):
    """
    Production adapter for DIFC (www.difc.com) Astro SPA pages.

    All requests go directly to Playwright — the site 429s all regular HTTP.
    Extracts structured listing items (title + URL + date) where possible,
    falls back to full body text when fewer than 3 items are found.
    """

    name = "uae_difc"

    def can_handle(self, url: str, source: dict | None = None) -> bool:
        try:
            host = urlparse(url).netloc.lower()
            return host == _DIFC_HOST or host.endswith("." + _DIFC_HOST)
        except Exception:
            return False

    def fetch_content(self, url: str, source: dict | None = None) -> str | None:
        """
        Fetch DIFC page content via Playwright and return clean paragraph text.

        Returns None when extraction fails or content is below quality gate.
        Never raises.
        """
        try:
            return self._fetch_via_playwright(url)
        except Exception as exc:
            logger.warning(
                "DIFCAdapter.fetch_content unexpected error for %s: %s: %s",
                url, type(exc).__name__, exc,
            )
            return None

    def _fetch_via_playwright(self, url: str) -> str | None:
        """Dispatch the sync-Playwright path safely from ANY context.

        playwright.sync_api refuses to run inside a live asyncio event loop
        ("Sync API inside the asyncio loop" — 981 occurrences in the prod
        journal). When that happened the adapter silently fell back to the
        generic scraper, which extracted the SAME text but with a degraded
        quality signal — the cause of the intermittent QUALITY_DROP flapping
        on DIFC fresh-alert sources (constant chars, flapping status). Run
        the sync API on a dedicated thread when a loop is running.
        """
        try:
            import asyncio
            asyncio.get_running_loop()
            in_loop = True
        except RuntimeError:
            in_loop = False
        if in_loop:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=1, thread_name_prefix="difc-playwright"
            ) as ex:
                return ex.submit(self._fetch_via_playwright_impl, url).result()
        return self._fetch_via_playwright_impl(url)

    def _fetch_via_playwright_impl(self, url: str) -> str | None:
        """
        Core Playwright extraction path.

        Launches headless Chromium, navigates to the URL with
        wait_until='networkidle' so the Astro SPA fully hydrates, then
        extracts structured listing items or falls back to body text.
        """
        global _playwright_available

        if _playwright_available is False:
            logger.debug("DIFCAdapter: Playwright known unavailable, skipping %s", url)
            return None

        try:
            from playwright.sync_api import sync_playwright  # type: ignore[import-untyped]
            _playwright_available = True
        except ImportError:
            _playwright_available = False
            logger.debug("DIFCAdapter: Playwright not installed")
            return None

        logger.debug("DIFCAdapter: launching Playwright for %s", url)
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                try:
                    context = browser.new_context(
                        user_agent=REQUESTS_UA,
                        locale="en-US",
                        extra_http_headers={
                            "Accept-Language": "en-US,en;q=0.9",
                            "Accept": (
                                "text/html,application/xhtml+xml,"
                                "application/xml;q=0.9,*/*;q=0.8"
                            ),
                        },
                    )
                    page = context.new_page()
                    page.set_default_timeout(PAGE_TIMEOUT_MS)

                    # First attempt: domcontentloaded + selector wait.
                    # This works for most DIFC pages.
                    page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)

                    # Wait for the Astro SPA to hydrate and render content.
                    selector_found = False
                    try:
                        page.wait_for_selector(_WAIT_SELECTOR, timeout=_SELECTOR_TIMEOUT_MS)
                        selector_found = True
                    except Exception:
                        logger.debug("DIFCAdapter: wait_for_selector timed out for %s", url)

                    if not selector_found:
                        # Selector never appeared — page may need a load event.
                        # Try waiting for load state with a relaxed timeout.
                        try:
                            page.wait_for_load_state("load", timeout=20000)
                        except Exception:
                            pass

                    # Additional settle for async content injection (e.g. news listings)
                    try:
                        page.wait_for_timeout(3000)
                    except Exception:
                        pass

                    html = page.content()
                finally:
                    browser.close()

        except Exception as exc:
            logger.warning(
                "DIFCAdapter: Playwright browser error for %s: %s: %s",
                url, type(exc).__name__, exc,
            )
            return None

        return self._parse_html(html, url)

    def _parse_html(self, html: str, url: str) -> str | None:
        """
        Parse rendered HTML and return monitorable text, or None.

        Priority:
        1. Structured listing items (articles, list items with anchors, cards)
        2. Primary content region text (main, .content, etc.)
        3. Full body text (last resort)
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            _strip_noise(soup)
        except Exception as exc:
            logger.warning("DIFCAdapter: HTML parse error for %s: %s", url, exc)
            return None

        # --- Step 1: structured listing items ---
        items = _extract_listing_items(soup, base_url=url)
        if len(items) >= 3:
            listing_text = _items_to_text(items)
            if len(listing_text) >= _LISTING_FALLBACK_THRESHOLD:
                text = listing_text
                logger.debug(
                    "DIFCAdapter: extracted %d listing items (%d chars) for %s",
                    len(items), len(text), url,
                )
                full_text = f"DIFC official page\n\nURL: {url}\n\n{text}"
                if is_quality_content(full_text):
                    return full_text

        # --- Step 2: primary content region ---
        text = ""
        for sel in _CONTENT_SELECTORS:
            region = soup.select_one(sel)
            if region:
                candidate = _clean(region.get_text("\n", strip=True))
                if len(candidate) > len(text):
                    text = candidate

        # --- Step 3: full body fallback ---
        if not is_quality_content(text):
            body = soup.find("body")
            if body:
                text = _clean(body.get_text("\n", strip=True))

        if not text:
            logger.warning("DIFCAdapter: no usable text extracted for %s", url)
            return None

        full_text = f"DIFC official page\n\nURL: {url}\n\n{text}"
        if not is_quality_content(full_text):
            logger.debug(
                "DIFCAdapter: content below quality gate for %s (%d chars)",
                url, len(full_text),
            )
            return None

        logger.debug(
            "DIFCAdapter: extracted %d chars for %s", len(full_text), url
        )
        return full_text

    def __repr__(self) -> str:
        return f"DIFCAdapter(name={self.name!r})"
