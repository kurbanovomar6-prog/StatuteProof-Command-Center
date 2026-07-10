"""
FTA (UAE Federal Tax Authority) adapter.

Handles public tax.gov.ae URLs across two content shapes:

1. Direct PDF links — the majority of monitored FTA sources are PDFs served at
   /Datafolder/Files/… and /DownloadOpenTextFile?fileUrl=… paths.  These are
   fetched and extracted via document_extractor.extract_pdf_text.

2. HTML pages — the FTA portal is a JavaScript SPA.  The adapter tries
   requests + BeautifulSoup first, then falls back to Playwright headless
   browsing when the page is JS-rendered (detected by low plain-text yield).
   Playwright is imported lazily with a graceful ImportError fallback.

can_handle() matches any URL whose host contains tax.gov.ae.
"""

from __future__ import annotations

import logging
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.adapters.base import SourceAdapter, is_quality_content
from app.config import HTTP_TIMEOUT_S, PAGE_TIMEOUT_MS, REQUESTS_UA
from app.document_extractor import extract_pdf_text
from app.parser import extract_text

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": REQUESTS_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    # No explicit Accept-Encoding: urllib3 advertises only codecs it can
    # actually decode — hardcoded "br" without the brotli package corrupts
    # the body (see adapters/vara.py, 2026-07-10 incident).
    "Referer": "https://tax.gov.ae/",
}

_PDF_HEADERS = {
    "User-Agent": REQUESTS_UA,
    "Accept": "application/pdf,*/*;q=0.8",
    "Referer": "https://tax.gov.ae/",
}

# Largest PDF we will download (bytes) — matches DOCUMENT_MAX_DOWNLOAD_MB
_PDF_MAX_BYTES = 15 * 1024 * 1024

# Characters of plain text below which we consider the page JS-rendered
_JS_PAGE_THRESHOLD = 300

def _clean(value: str | None, limit: int | None = None) -> str:
    """Collapse horizontal whitespace only; preserve newlines for paragraph detection."""
    text = re.sub(r"[ \t\xa0]+", " ", value or "")
    # Collapse runs of 3+ newlines to double-newline (paragraph boundary)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text



def _is_pdf_url(url: str) -> bool:
    """
    Detect PDF URLs including FTA's DownloadOpenTextFile redirect pattern
    and standard .pdf extension paths.
    """
    lower_url = url.lower()
    if lower_url.endswith(".pdf"):
        return True
    # FTA uses /DownloadOpenTextFile?fileUrl=... to serve PDFs
    if "downloadopentextfile" in lower_url and "fileurlf=en/" in lower_url.replace("fileurl=", "fileurlf="):
        return True
    if "downloadopentextfile" in lower_url:
        return True
    return False


def _strip_noise(soup: BeautifulSoup) -> None:
    """Remove boilerplate elements from FTA pages in-place.

    NOTE: Do NOT include 'form' here.  The FTA portal wraps its entire page
    content — including the <main id="maincontent"> element — inside a single
    top-level <form> tag (standard ASP.NET WebForms pattern).  Decomposing
    form elements would destroy all page content.
    """
    for tag in soup(["script", "style", "noscript", "nav", "footer", "header",
                     "iframe"]):
        tag.decompose()
    # FTA has a persistent cookie and chat widget
    for sel in (".cookie-bar", ".chat-widget", "#CybotCookiebotDialog",
                ".gdpr", "[aria-label='cookie']"):
        for el in soup.select(sel):
            el.decompose()


class FTAAdapter(SourceAdapter):
    """
    Production adapter for UAE Federal Tax Authority (tax.gov.ae) pages.

    Covers:
    - FTA PDF guides and legislation documents (most monitored sources)
    - FTA HTML portal pages with Playwright fallback for JS-rendered content
    """

    name = "uae_fta"

    # Track Playwright availability at class level to avoid repeated import attempts
    _playwright_available: bool | None = None

    def can_handle(self, url: str, source: dict | None = None) -> bool:
        try:
            return "tax.gov.ae" in urlparse(url).netloc.lower()
        except Exception:
            return False

    def fetch_content(self, url: str, source: dict | None = None) -> str | None:
        """
        Dispatch to the appropriate extraction strategy.

        Returns clean monitorable text, or None when extraction fails or
        content does not meet the quality gate.  Never raises.
        """
        try:
            if _is_pdf_url(url):
                return self._fetch_pdf(url)
            return self._fetch_html_page(url)
        except Exception as exc:
            logger.warning("FTAAdapter.fetch_content unexpected error for %s: %s: %s",
                           url, type(exc).__name__, exc)
            return None

    # ── private: PDF extraction ──────────────────────────────────────────────

    def _fetch_pdf(self, url: str) -> str | None:
        logger.debug("FTAAdapter: fetching PDF %s", url)
        try:
            response = requests.get(
                url,
                headers=_PDF_HEADERS,
                timeout=HTTP_TIMEOUT_S,
                allow_redirects=True,
                stream=True,
            )
        except Exception as exc:
            logger.warning("FTAAdapter: PDF request failed for %s: %s", url, exc)
            return None

        if response.status_code != 200:
            logger.warning("FTAAdapter: PDF HTTP %d for %s", response.status_code, url)
            return None

        content_length = int(response.headers.get("Content-Length", 0) or 0)
        if content_length > _PDF_MAX_BYTES:
            logger.warning("FTAAdapter: PDF too large (%d bytes) for %s", content_length, url)
            return None

        try:
            pdf_bytes = response.content
        except Exception as exc:
            logger.warning("FTAAdapter: PDF read failed for %s: %s", url, exc)
            return None

        if len(pdf_bytes) > _PDF_MAX_BYTES:
            logger.warning("FTAAdapter: PDF content exceeded size limit for %s", url)
            return None

        result = extract_pdf_text(pdf_bytes)
        text = result.get("text") or ""
        if not text or len(text) < 200:
            logger.warning("FTAAdapter: PDF extraction low quality for %s (method=%s, chars=%d)",
                           url, result.get("method"), result.get("chars", 0))
            return None

        header = (
            f"UAE Federal Tax Authority — regulatory document (PDF)\n\n"
            f"URL: {url}\n"
            f"Method: {result.get('method', 'unknown')}\n"
        )
        full_text = f"{header}\n{text}"
        if not is_quality_content(full_text):
            logger.debug("FTAAdapter: PDF text below quality gate for %s", url)
            return None
        return full_text

    # ── private: HTML page — requests tier ───────────────────────────────────

    def _fetch_html_page(self, url: str) -> str | None:
        logger.debug("FTAAdapter: fetching HTML page %s", url)
        text = self._fetch_via_requests(url)

        # If requests returned very little, the page is likely JS-rendered
        if not text or len(text) < _JS_PAGE_THRESHOLD:
            logger.debug("FTAAdapter: requests tier low yield (%d chars) for %s, trying Playwright",
                         len(text or ""), url)
            playwright_text = self._fetch_via_playwright(url)
            if playwright_text and len(playwright_text) > len(text or ""):
                text = playwright_text

        if not is_quality_content(text):
            logger.debug("FTAAdapter: content below quality gate for %s", url)
            return None

        return f"UAE Federal Tax Authority — official page\n\nURL: {url}\n\n{text}"

    def _fetch_via_requests(self, url: str) -> str | None:
        """Fast path: requests + BeautifulSoup."""
        try:
            response = requests.get(
                url, headers=_HEADERS, timeout=HTTP_TIMEOUT_S, allow_redirects=True
            )
        except Exception as exc:
            logger.debug("FTAAdapter: requests failed for %s: %s", url, exc)
            return None

        if response.status_code != 200:
            logger.debug("FTAAdapter: HTTP %d for %s", response.status_code, url)
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        _strip_noise(soup)

        # Trafilatura / readability via extract_text
        text = extract_text(response.text) or ""

        # Target known FTA content containers when trafilatura is insufficient.
        # #maincontent and the UpdatePanel ID are preferred because the FTA
        # portal nests <main id="maincontent"> inside a top-level <form> tag;
        # those selectors survive the noise-strip pass intact.
        # Use "\n\n" as the get_text separator so block-level elements produce
        # double newlines, which is what is_quality_content() splits on.
        if not is_quality_content(text):
            for selector in (
                "#maincontent",
                "#ctrlContentArea_ctlOpenData_ctrlUpdatePanel",
                "main",
                ".content-area",
                ".page-content",
                "article",
                "#content",
                "[role='main']",
                ".tax-content",
                ".inner-content",
            ):
                region = soup.select_one(selector)
                if region:
                    candidate = _clean(region.get_text("\n\n", strip=True))
                    if len(candidate) > len(text):
                        text = candidate
                        break

        # Final fallback: full body text
        if not is_quality_content(text):
            text = _clean(soup.get_text("\n\n", strip=True))

        return text or None

    def _fetch_via_playwright(self, url: str) -> str | None:
        """
        Playwright headless browser fallback for JS-rendered FTA pages.

        Imported lazily — if Playwright is not installed this path returns None
        without error.  Playwright must be installed with `playwright install chromium`.
        """
        if FTAAdapter._playwright_available is False:
            logger.debug("FTAAdapter: Playwright known unavailable, skipping")
            return None

        try:
            from playwright.sync_api import sync_playwright  # type: ignore[import-untyped]
            FTAAdapter._playwright_available = True
        except ImportError:
            FTAAdapter._playwright_available = False
            logger.debug("FTAAdapter: Playwright not installed, skipping JS fallback for %s", url)
            return None

        logger.debug("FTAAdapter: using Playwright for %s", url)
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                try:
                    context = browser.new_context(
                        user_agent=REQUESTS_UA,
                        locale="en-US",
                        extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
                    )
                    page = context.new_page()
                    page.set_default_timeout(PAGE_TIMEOUT_MS)
                    page.goto(url, wait_until="domcontentloaded")

                    # Wait for meaningful content — look for any heading or paragraph
                    try:
                        page.wait_for_selector("h1, h2, p, article, main", timeout=10000)
                    except Exception:
                        pass  # Proceed with whatever is rendered

                    html = page.content()
                finally:
                    browser.close()

            soup = BeautifulSoup(html, "html.parser")
            _strip_noise(soup)

            # Try trafilatura on rendered HTML
            text = extract_text(html) or ""
            if not is_quality_content(text):
                for selector in (
                    "#maincontent",
                    "#ctrlContentArea_ctlOpenData_ctrlUpdatePanel",
                    "main",
                    ".content-area",
                    ".page-content",
                    "article",
                    "#content",
                    "[role='main']",
                ):
                    region = soup.select_one(selector)
                    if region:
                        candidate = _clean(region.get_text("\n\n", strip=True))
                        if len(candidate) > len(text):
                            text = candidate
                            break

            if not is_quality_content(text):
                text = _clean(soup.get_text("\n\n", strip=True))

            return text or None

        except Exception as exc:
            logger.warning("FTAAdapter: Playwright extraction failed for %s: %s: %s",
                           url, type(exc).__name__, exc)
            return None

    def __repr__(self) -> str:
        return f"FTAAdapter(name={self.name!r})"
