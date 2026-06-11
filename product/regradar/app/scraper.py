"""
Two-tier page fetcher — v5 (content-aware fallback).

Tier 1 — requests (fast path):
  Plain HTTP GET with a realistic User-Agent.  Returns immediately for most
  static / server-rendered pages.  Timeout: HTTP_TIMEOUT_S (default 15 s).

  After a successful HTTP 200, the response is passed through
  is_low_content_html() which runs BeautifulSoup to measure actual visible
  text.  If the visible text is below MIN_EXTRACTED_TEXT_CHARS the response
  is treated as a JS-rendered shell and Playwright is triggered regardless
  of raw HTML size.

Tier 2 — Playwright (fallback):
  Headless Chromium browser.  Used when Tier 1 fails, the response looks
  like a bot wall, or Tier 1 returned too little visible text.

  Navigation strategy:
    1. Try wait_until="networkidle"  — best content; may time out on pages
       with persistent analytics / long-poll connections.
    2. On timeout: fall back to wait_until="domcontentloaded" — the DOM is
       ready but JS may still be executing.
    3. Always wait an extra 2 s after navigation for React/Vue hydration.

  If Playwright also fails but Tier 1 had some HTML, Tier 1 HTML is
  returned as a best-effort result rather than crashing the pipeline.

Block / low-content detection heuristics:
  - HTML shorter than 1 000 chars (raw)
  - Body contains known JS-gate phrases
  - Visible extracted text shorter than MIN_EXTRACTED_TEXT_CHARS (500)
"""

import atexit
import logging
import re
import sys
import threading

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import Browser as PWBrowser, TimeoutError as PWTimeout, sync_playwright

from app.config import HTTP_TIMEOUT_S, PAGE_TIMEOUT_MS, REQUESTS_UA

logger = logging.getLogger(__name__)

# ── constants ─────────────────────────────────────────────────────────────────

# These phrases only appear in actual bot-wall / JS-gate pages, not in
# legitimate page content.  Keep them specific to avoid false positives:
#   - "cloudflare" alone matches CDN asset URLs (cdnjs.cloudflare.com)
#   - "access denied" appears in legal/policy text
# Use sub-phrases that are unique to bot-wall templates.
_BLOCK_PHRASES = (
    "enable javascript to",        # "Please enable JavaScript to continue"
    "please enable javascript",    # Cloudflare / generic JS gate
    "checking your browser",       # Cloudflare interstitial
    "cf-browser-verification",     # Cloudflare internal marker
    "cloudflare ray id",           # Cloudflare error page footer
    "ddos protection by cloudflare",
)

_MIN_HTML_LEN          = 1_000   # raw HTML chars — fast pre-filter
_MIN_EXTRACTED_TEXT_CHARS = 500  # visible text chars — content-quality gate

# Tags stripped before content measurement (mirrors parser._NOISE_TAGS)
_NOISE_TAGS = [
    "script", "style", "noscript", "head",
    "nav", "footer", "header", "aside",
    "form", "button", "input", "select",
    "textarea", "iframe", "img", "svg",
    "meta", "link",
]

# Semantic content elements — mirrors parser._CONTENT_TAGS.
# is_low_content_html measures text only from these tags so its verdict
# matches what extract_text() will actually produce.
_CONTENT_TAGS = [
    "p", "li", "td", "th",
    "h1", "h2", "h3", "h4", "h5",
    "article", "section", "blockquote",
    "dd", "dt", "pre",
]

_WS_RE = re.compile(r"[\s\xa0]+")

# ── Playwright browser pool ───────────────────────────────────────────────────
# One shared browser instance per process; each call gets its own context/page.
# Threading lock guards initialisation only — contexts are isolated per call.

_PW_INSTANCE: object | None = None   # SyncPlaywright — keeps the subprocess alive
_PW_BROWSER: PWBrowser | None = None
_PW_BROWSER_LOCK = threading.Lock()


def _teardown_playwright() -> None:
    global _PW_INSTANCE, _PW_BROWSER
    if _PW_BROWSER is not None:
        try:
            _PW_BROWSER.close()
        except Exception:
            pass
        _PW_BROWSER = None
    if _PW_INSTANCE is not None:
        try:
            _PW_INSTANCE.stop()   # type: ignore[attr-defined]
        except Exception:
            pass
        _PW_INSTANCE = None


def _get_shared_browser() -> PWBrowser:
    global _PW_INSTANCE, _PW_BROWSER
    with _PW_BROWSER_LOCK:
        if _PW_BROWSER is None or not _PW_BROWSER.is_connected():
            _teardown_playwright()
            _PW_INSTANCE = sync_playwright().start()
            _PW_BROWSER = _PW_INSTANCE.chromium.launch(   # type: ignore[attr-defined]
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            atexit.register(_teardown_playwright)
    return _PW_BROWSER


# ── content quality check ─────────────────────────────────────────────────────

def is_low_content_html(html: str) -> bool:
    """
    Return True when `html` contains too little visible text to be useful.

    Checks (in order):
      1. Raw HTML too short — obvious JS shell or empty response.
      2. Known JS-gate / bot-wall phrases present.
      3. Visible text after stripping noise tags falls below threshold.

    Parameters
    ----------
    html : str
        Raw HTML string from an HTTP response.

    Returns
    -------
    bool
        True → reject Tier 1 result and escalate to Playwright.
        False → Tier 1 content is usable.
    """
    if not html or len(html) < _MIN_HTML_LEN:
        logger.debug("is_low_content: raw HTML too short (%d chars)", len(html) if html else 0)
        return True

    lower = html.lower()
    for phrase in _BLOCK_PHRASES:
        if phrase in lower:
            logger.debug("is_low_content: block phrase found: %r", phrase)
            return True

    soup = BeautifulSoup(html, "html.parser")

    # Remove structural noise first (same as parser step 1)
    for tag in soup(_NOISE_TAGS):
        tag.decompose()

    # Measure text only from semantic content elements — this mirrors
    # what extract_text() will actually produce, so the verdict here
    # accurately predicts whether the parser will find useful content.
    total_chars = 0
    seen: set[str] = set()
    for el in soup.find_all(_CONTENT_TAGS):
        if not el.attrs and el.parent is None:
            continue  # skip detached nodes from prior decompose
        text = _WS_RE.sub(" ", el.get_text(separator=" ", strip=True)).strip()
        if len(text) >= 30 and text not in seen:
            seen.add(text)
            total_chars += len(text)

    logger.debug(
        "is_low_content: semantic text = %d chars (threshold %d)",
        total_chars, _MIN_EXTRACTED_TEXT_CHARS,
    )
    return total_chars < _MIN_EXTRACTED_TEXT_CHARS


# ── Tier 1: requests ──────────────────────────────────────────────────────────

def _fetch_via_requests(url: str) -> str | None:
    """
    Attempt a plain HTTP GET.

    Returns the response text on success, or None when the request fails.
    Does NOT apply the content-quality check — that is done in fetch_page()
    so the caller can log the decision with full context.
    """
    try:
        resp = requests.get(
            url,
            headers={
                "User-Agent":      REQUESTS_UA,
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            },
            timeout=HTTP_TIMEOUT_S,
            allow_redirects=True,
        )
        resp.raise_for_status()
        logger.info("Tier 1 (requests) HTTP OK — %d chars from %s", len(resp.text), url)
        return resp.text

    except requests.RequestException as exc:
        logger.warning("Tier 1 (requests) failed: %s — escalating to Playwright", exc)
        print(f"  Tier 1 (requests) failed: {exc} — escalating to Playwright", file=sys.stderr, flush=True)
        return None


# ── Tier 2: Playwright ────────────────────────────────────────────────────────

_PW_JS_SETTLE_MS   = 5_000   # extra wait after navigation for JS-rendered content
_PW_IDLE_EXTRA_MS  = 3_000   # extra wait when networkidle timed out (page IS loaded)


def _fetch_via_playwright(url: str) -> str:
    """
    Launch headless Chromium and return the fully rendered HTML.

    Navigation strategy:
      1. Navigate with wait_until="networkidle".
         This is the best signal that SPA data-fetching is complete.
      2. If networkidle times out, the DOM is already loaded — the timeout
         only means some connections stayed open (analytics, long-poll, etc.).
         In that case, wait _PW_IDLE_EXTRA_MS more and capture content.
         Do NOT navigate again: a second goto loses the already-rendered state.
      3. If domcontentloaded itself fails (navigation error), raise TimeoutError.
      4. Always apply _PW_JS_SETTLE_MS after a clean networkidle to let
         any final JS rendering complete.

    Raises
    ------
    TimeoutError  — Navigation failed entirely (not just networkidle timeout).
    ValueError    — Playwright returned empty or tiny HTML.
    """
    print(f"  Playwright fallback triggered — {url}", file=sys.stderr, flush=True)
    logger.info("Tier 2 (Playwright) starting for %s", url)

    browser = _get_shared_browser()
    context = browser.new_context(
        user_agent=REQUESTS_UA,
        locale="ru-RU",
        viewport={"width": 1280, "height": 900},
    )
    page = context.new_page()

    try:
        networkidle_ok = False
        try:
            page.goto(url, timeout=PAGE_TIMEOUT_MS, wait_until="networkidle")
            networkidle_ok = True
            logger.debug("Playwright: networkidle achieved for %s", url)
        except PWTimeout:
            # Network never went fully idle (analytics, long-poll, etc.).
            # The DOM and XHR data-fetching are typically done by now.
            # Wait a bit more before capturing — do NOT navigate again.
            logger.info(
                "Playwright: networkidle timed out — "
                "waiting %d ms more for JS rendering at %s",
                _PW_IDLE_EXTRA_MS, url,
            )
            print(
                f"  Playwright: networkidle timeout — "
                f"waiting {_PW_IDLE_EXTRA_MS // 1000} s more for JS rendering",
                file=sys.stderr, flush=True,
            )
            page.wait_for_timeout(_PW_IDLE_EXTRA_MS)

        if networkidle_ok:
            # Give any post-idle JS rendering a moment to finish
            page.wait_for_timeout(_PW_JS_SETTLE_MS)

        html = page.content()

    except PWTimeout as exc:
        raise TimeoutError(
            f"Playwright: navigation failed within "
            f"{PAGE_TIMEOUT_MS // 1000} s — {url}"
        ) from exc

    finally:
        context.close()
        # context closed; browser reused — do not call browser.close() here

    if not html or len(html) < 200:
        raise ValueError(f"Playwright returned empty HTML for {url}")

    logger.info("Tier 2 (Playwright) OK — %d chars from %s", len(html), url)
    print(f"  Playwright succeeded — {len(html):,} chars fetched", file=sys.stderr, flush=True)
    return html


# ── public API ────────────────────────────────────────────────────────────────

def fetch_page(url: str) -> str:
    """
    Fetch `url` and return raw HTML.

    Decision flow:
      1. Try Tier 1 (requests).
         a. If request fails           → go to step 2.
         b. If request succeeds:
            - Run is_low_content_html().
            - If content is adequate   → return Tier 1 HTML.
            - If content is too thin   → go to step 2.
      2. Try Tier 2 (Playwright).
         a. If Playwright succeeds     → return Playwright HTML.
         b. If Playwright fails:
            - If Tier 1 had any HTML   → return it (best-effort).
            - Otherwise                → raise.

    Raises
    ------
    TimeoutError  — Playwright tier timed out and no Tier 1 fallback.
    ValueError    — Both tiers returned unusable content.
    """
    # ── Step 1: Tier 1 ────────────────────────────────────────────────
    requests_html = _fetch_via_requests(url)

    if requests_html is not None:
        if not is_low_content_html(requests_html):
            logger.info("Tier 1 accepted — adequate visible content")
            return requests_html

        # Tier 1 responded but content quality is too low
        logger.info(
            "Tier 1 rejected: visible text below %d chars — escalating to Playwright",
            _MIN_EXTRACTED_TEXT_CHARS,
        )
        print(
            f"  Tier 1 rejected (low visible content < {_MIN_EXTRACTED_TEXT_CHARS} chars) "
            f"— Playwright fallback triggered",
            file=sys.stderr, flush=True,
        )

    # ── Step 2: Tier 2 ────────────────────────────────────────────────
    try:
        return _fetch_via_playwright(url)

    except (TimeoutError, ValueError, Exception) as exc:
        if requests_html is not None:
            logger.warning(
                "Playwright failed (%s: %s) — using Tier 1 HTML as best-effort fallback",
                type(exc).__name__, exc,
            )
            print(
                f"  Playwright failed ({type(exc).__name__}) "
                f"— using Tier 1 HTML as best-effort fallback",
                file=sys.stderr, flush=True,
            )
            return requests_html
        raise
