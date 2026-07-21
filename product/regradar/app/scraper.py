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

SSRF guard (both tiers):
  Tier 1 (requests) is guarded per-hop by app.adapters.base._guarded_get:
  every redirect hop's host is resolved and validated, and a DIRECT hop is
  IP-pinned before connecting, defeating DNS-rebind. EXCEPTION — a hop routed
  through the owner-configured egress proxy (only the fixed allowlist of
  WAF/geo-blocked regulator hosts, e.g. CBUAE) is NOT IP-pinned: a forward
  proxy does its own DNS+connect, so pinning is impossible on that path. The
  host is still validated and the proxy is re-gated per hop (dropped the moment
  a redirect leaves the allowlist), but the DNS-rebind window is not closed for
  those 3 allowlisted regulator hosts — closing it would require compromising
  the regulator's own DNS. See PROXY_RESIDUAL_RISK below. Tier 2
  (Playwright/Chromium) cannot be IP-pinned the same way
  from the Python side, so it is guarded instead by intercepting every
  request the browser makes — navigation, each redirect hop, every
  subresource, AND WebSocket connections opened by the page's own JS — via
  context.route() / context.route_web_socket() and re-using the EXACT SAME
  host/IP-range validation (app.adapters.base._validate_fetch_target) — see
  SSRF_RESIDUAL_RISK below for what this does and does not close.
"""

import atexit
import logging
import re
import sys
import threading
from urllib.parse import urlsplit, urlunsplit

from bs4 import BeautifulSoup
from playwright.sync_api import Browser as PWBrowser, TimeoutError as PWTimeout, sync_playwright

from app.adapters.base import _validate_fetch_target, fetch_text_bounded_status, proxy_for_url
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


def _html_is_bot_wall(html: str) -> bool:
    """True when the HTML is a bot-wall / JS-gate page (a known block phrase).

    Distinct from merely-thin content: is_low_content_html() rejects BOTH a
    bot-wall AND an honestly-thin page, but only a bot-wall must never be sealed
    as best-effort content. A bot-wall commonly returns HTTP 200, so it cannot be
    told apart by status code — the phrase match is the signal. Honest thin
    content is monitored as-is (and surfaces as QUALITY_DROP/low_content
    downstream); a bot-wall is refused so it can be reported as an access block
    instead of poisoning the baseline with a challenge page."""
    if not html:
        return False
    lower = html.lower()
    return any(phrase in lower for phrase in _BLOCK_PHRASES)


# ── Tier 1: requests ──────────────────────────────────────────────────────────

_MAX_RESPONSE_BYTES = 10 * 1024 * 1024  # 10 MB hard limit


def _fetch_via_requests(
    url: str, status_out: dict | None = None, *, allow_proxy: bool = False
) -> str | None:
    """
    Attempt a plain HTTP GET with a bounded, streamed read.

    Returns the response text on success, or None when the request fails.
    Does NOT apply the content-quality check — that is done in fetch_page()
    so the caller can log the decision with full context.

    Size guard: the body is read in chunks and the read ABORTS once the
    DECOMPRESSED size exceeds 10 MB, bounding peak memory even against
    decompression bombs (Content-Length reflects wire size, not inflated
    size, so a post-hoc check would be too late).

    ``status_out``, when provided, is a caller-owned dict that receives the
    real HTTP status code under ``"http_status"`` (None when the request
    failed entirely, including an SSRF-guard block) — this is how callers
    (e.g. source_intake.run_source_intake) surface the status that
    map_source_health_status's http_status>=400 gate checks.
    """
    status, body = fetch_text_bounded_status(
        url,
        headers={
            "User-Agent":      REQUESTS_UA,
            # Prefer English (the UAE regulator portals this generic tier fetches
            # are English) but keep a wildcard so a non-English source reached via
            # the generic FALLBACK (e.g. a .ru site whose own ru-RU adapter failed)
            # still gets a body. Adding an explicit Accept header + dropping the
            # ru-RU default fixed worse content negotiation on some UAE portals.
            "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,*;q=0.5",
        },
        timeout=HTTP_TIMEOUT_S,
        max_bytes=_MAX_RESPONSE_BYTES,
        label="Tier 1 (requests)",
        # Route allowlisted WAF/geo-blocked regulator hosts (e.g. CBUAE) through
        # the owner-configured egress proxy — but ONLY on trusted monitoring
        # paths (allow_proxy=True). The user-supplied "test a custom source"
        # path leaves allow_proxy=False, so an authenticated user can never aim
        # the owner's proxy with an arbitrary (even allowlisted-host) URL.
        proxy=proxy_for_url(url) if allow_proxy else None,
    )
    if status_out is not None:
        status_out["http_status"] = status

    if body is None:
        print("  Tier 1 (requests) failed — escalating to Playwright", file=sys.stderr, flush=True)
        return None

    logger.info("Tier 1 (requests) HTTP OK — %d chars from %s", len(body), url)
    return body


# ── Tier 2 SSRF guard ────────────────────────────────────────────────────────
#
# app.adapters.base._guarded_get is the requests-tier SSRF defence: every
# redirect hop is resolved and vetted BEFORE connecting, and the vetted IP is
# pinned so a request cannot be re-resolved (DNS-rebound) to an internal
# address between the check and the connect. Chromium — driven via Playwright
# — does its own DNS resolution and follows redirects internally; there is no
# Playwright API that lets Python force the browser's socket to dial a
# specific, pre-vetted IP the way requests.Session + a custom HTTPAdapter can.
# IP pinning is therefore NOT achievable for this tier.
#
# What IS achievable: context.route() lets us intercept EVERY request
# Chromium is about to fire — the initial navigation, each individual
# redirect hop (Chromium emits a fresh request event per hop), and every
# subresource — before it connects. Each intercepted request's host is
# vetted with the SAME validator the requests tier uses
# (app.adapters.base._validate_fetch_target: scheme allowlist, hostname
# resolution, and rejection of loopback/private/link-local/multicast/
# metadata addresses), and the request is aborted if the check fails.
#
# SSRF_RESIDUAL_RISK documents precisely what this does not close: a fast
# DNS-rebinding attack, where the attacker's resolver answers with a public
# IP for our synchronous check and then rebinds the SAME hostname to a
# private IP a few milliseconds later (before Chromium performs its own,
# separate DNS resolution at connect time), is not fully defeated — because
# we cannot pin the IP Chromium actually dials. A literal-IP attack (the nav
# target or a redirect Location IS a reserved/metadata IP) and a
# stable-DNS attack (a hostname that already resolves privately at the time
# of the request) are both blocked, matching the finding's fallback
# requirement.
SSRF_RESIDUAL_RISK = (
    "Playwright (Tier 2) SSRF guard: every navigation, redirect hop, "
    "subresource request, and WebSocket connection is validated against the "
    "same private/loopback/link-local/multicast/reserved/metadata blocklist "
    "the requests tier uses (app.adapters.base._validate_fetch_target), and "
    "the final landed URL is re-validated after navigation completes. This "
    "blocks (a) direct navigation or redirect to a literal reserved-range/"
    "metadata IP, (b) a hostname that currently resolves to a non-public "
    "address for any of those request types, and (c) a page's own "
    "JavaScript opening a raw WebSocket to an internal host (verified: "
    "page.route() does NOT intercept WebSocket upgrades — a separate "
    "context.route_web_socket() handler is required and is installed here). "
    "It does NOT pin the vetted IP: Chromium performs its own DNS resolution "
    "at connect time, milliseconds after our check runs in a separate "
    "process, so a fast DNS-rebinding attack (public answer at check-time, "
    "private answer at connect-time, e.g. TTL=0) is not fully defeated for "
    "this tier — unlike Tier 1 (requests), which pins the vetted IP and is "
    "fully rebind-proof. This is a known, intentional gap: full per-hop IP "
    "pinning is not achievable through Playwright's public "
    "route-interception API. The sibling Playwright-driven fetch path in "
    "app/source_discovery.py (capture_playwright_network_candidates, which "
    "creates its own browser context) now installs the SAME guard via "
    "_install_ssrf_guard(context) and additionally re-validates each response "
    "URL with _validate_fetch_target before echoing any body (SEC-1); it "
    "carries the same Tier-2 DNS-rebind residual described above."
)

# Non-network / browser-internal schemes that must never be run through the
# fetch-target validator (which only understands http/https): blocking these
# would break normal page rendering (inline data: images, blob: object URLs,
# about:blank, Chromium's own error/interstitial pages) without adding any
# SSRF protection, since none of them cause an outbound connection to an
# attacker-influenced host.
_SSRF_SAFE_SCHEMES = frozenset({"data", "blob", "about", "chrome-error", "chrome-extension", "chrome"})


def _ssrf_guard_route(route, request) -> None:
    """
    context.route() handler — validate every request Chromium is about to
    fire (navigation, each redirect hop, every subresource) before letting it
    proceed. Mirrors app.adapters.base._validate_fetch_target exactly (same
    scheme allowlist, same resolve-and-vet-every-IP check) so there is a
    single source of truth for what counts as a safe fetch target. Never
    raises internally — any unexpected error aborts the request rather than
    risking a silent bypass.
    """
    url = request.url
    try:
        scheme = (urlsplit(url).scheme or "").lower()
    except Exception:
        scheme = ""

    if scheme in _SSRF_SAFE_SCHEMES:
        try:
            route.continue_()
        except Exception:
            pass
        return

    try:
        vetted = _validate_fetch_target(url)
    except Exception:
        vetted = None

    if vetted is None:
        logger.warning("Playwright SSRF guard: blocked request to %s", url)
        try:
            route.abort()
        except Exception:
            pass
        return

    try:
        route.continue_()
    except Exception:
        pass


def _ssrf_guard_websocket(ws) -> None:
    """
    context.route_web_socket() handler — WebSocket connections opened by a
    page's own JavaScript (``new WebSocket(...)``) are a SEPARATE
    interception surface from context.route(): Playwright does not run HTTP
    request routes for the WebSocket upgrade handshake at all (verified
    empirically against a real headless Chromium — a route("**/*") handler
    never sees the request, and the target host receives a real TCP
    connection with a genuine WS handshake). Without this handler, a
    malicious or compromised source's page JS could pivot to an internal
    host over a raw WebSocket, bypassing the HTTP-only guard above entirely.

    _validate_fetch_target only understands http/https, so ws/wss are
    translated to their http/https equivalent before vetting — the
    underlying host/IP validation is identical, only the wire protocol
    differs. A blocked target is left UNCONNECTED (connect_to_server() is
    simply never called) rather than actively closed: closing from inside
    this handler was observed, empirically, to hang browser/context
    teardown on the installed Playwright version, whereas never connecting
    at all completes cleanly and the target server receives no TCP
    connection at all (also verified empirically).
    """
    url = ws.url
    try:
        parsed = urlsplit(url)
        http_scheme = {"ws": "http", "wss": "https"}.get((parsed.scheme or "").lower())
        if http_scheme is None:
            return  # unrecognised scheme — leave unconnected
        translated = urlunsplit((http_scheme, parsed.netloc, parsed.path, parsed.query, parsed.fragment))
    except Exception:
        return  # malformed URL — leave unconnected rather than risk a bypass

    try:
        vetted = _validate_fetch_target(translated)
    except Exception:
        vetted = None

    if vetted is None:
        logger.warning("Playwright SSRF guard: blocked WebSocket connection to %s", url)
        return  # never connect — see docstring for why this doesn't call close()

    try:
        ws.connect_to_server()
    except Exception:
        pass


def _install_ssrf_guard(context) -> None:
    """
    Wire the per-request SSRF guard onto every request the context makes —
    both HTTP(S) requests (context.route) and WebSocket connections
    (context.route_web_socket, a separate Playwright interception surface;
    see _ssrf_guard_websocket).
    """
    context.route("**/*", _ssrf_guard_route)
    context.route_web_socket("**/*", _ssrf_guard_websocket)


def _final_url_is_safe(page) -> bool:
    """
    Defense-in-depth: re-validate the FINAL landed URL's host after
    navigation completes.

    The route guard above already vets every request before it fires, so in
    the normal case this is redundant by construction. It exists as an
    explicit backstop per the SSRF fix requirement, and as a cheap safety net
    against any navigation path that does not surface as a routed request.
    It does NOT close the DNS-rebind gap described in SSRF_RESIDUAL_RISK —
    if Chromium already connected to a rebound private IP under a
    still-public-looking hostname, page.url reflects the hostname, not the
    IP actually dialled, and this check cannot detect that.
    """
    try:
        final_url = page.url
    except Exception:
        return True  # cannot determine — do not block on an internal error

    if not final_url or final_url == "about:blank":
        return True

    try:
        scheme = (urlsplit(final_url).scheme or "").lower()
    except Exception:
        return True

    if scheme in _SSRF_SAFE_SCHEMES or scheme not in ("http", "https"):
        return True

    return _validate_fetch_target(final_url) is not None


# ── Tier 2: Playwright ────────────────────────────────────────────────────────

_PW_JS_SETTLE_MS   = 5_000   # extra wait after navigation for JS-rendered content
_PW_IDLE_EXTRA_MS  = 3_000   # extra wait when networkidle timed out (page IS loaded)
_PW_CONTENT_RETRY_MS = 1_000  # retry capture when SPA content is mid-navigation


def _capture_page_content(page) -> str:
    """Capture rendered HTML, retrying once if a SPA is still navigating."""
    try:
        return page.content()
    except Exception as exc:
        message = str(exc).lower()
        if "page.content" not in message or "navigat" not in message:
            raise
        logger.info(
            "Playwright content capture raced with navigation — waiting %d ms and retrying",
            _PW_CONTENT_RETRY_MS,
        )
        try:
            page.wait_for_timeout(_PW_CONTENT_RETRY_MS)
        except Exception:
            pass
        return page.content()


def _fetch_via_playwright(url: str, status_out: dict | None = None) -> str:
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

    SSRF guard: the context has the per-request guard installed (see
    _install_ssrf_guard / SSRF_RESIDUAL_RISK above) before any navigation is
    attempted, and the final landed URL is re-validated after capture.

    ``status_out``, when provided, receives the navigation response's HTTP
    status under ``"http_status"`` (left untouched when Chromium does not
    return a Response object for the main-frame navigation, e.g. a blocked
    or same-document navigation).

    Raises
    ------
    TimeoutError  — Navigation failed entirely (not just networkidle timeout).
    ValueError    — Playwright returned empty or tiny HTML, or the
                     navigation resolved to a non-public address.
    """
    print(f"  Playwright fallback triggered — {url}", file=sys.stderr, flush=True)
    logger.info("Tier 2 (Playwright) starting for %s", url)

    browser = _get_shared_browser()
    context = browser.new_context(
        user_agent=REQUESTS_UA,
        locale="en-US",
        viewport={"width": 1280, "height": 900},
    )
    _install_ssrf_guard(context)
    page = context.new_page()

    try:
        networkidle_ok = False
        response = None
        try:
            response = page.goto(url, timeout=PAGE_TIMEOUT_MS, wait_until="networkidle")
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

        html = _capture_page_content(page)

        if not _final_url_is_safe(page):
            logger.warning(
                "Tier 2 (Playwright): navigation resolved to a non-public "
                "address for %s (final URL %s) — rejecting",
                url, getattr(page, "url", "?"),
            )
            raise ValueError(
                f"Playwright navigation resolved to a non-public address for {url}"
            )

        # Only record the status once the content that produced it is the
        # content we are actually about to return (i.e. past the safety
        # gate above) — a status set before an early raise would misattribute
        # a rejected navigation's status to whatever fallback content the
        # caller ends up using instead.
        if status_out is not None and response is not None:
            try:
                status_out["http_status"] = response.status
            except Exception:
                pass

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

    # Same ceiling as Tier 1: a rendered page this large is not a monitorable
    # regulatory document. Reject rather than truncate — partial HTML would
    # produce a bogus content diff.
    if len(html) > _MAX_RESPONSE_BYTES:
        raise ValueError(
            f"Playwright HTML ({len(html):,} chars) exceeds "
            f"{_MAX_RESPONSE_BYTES // (1024 * 1024)} MB limit for {url}"
        )

    logger.info("Tier 2 (Playwright) OK — %d chars from %s", len(html), url)
    print(f"  Playwright succeeded — {len(html):,} chars fetched", file=sys.stderr, flush=True)
    return html


# ── public API ────────────────────────────────────────────────────────────────

def fetch_page(url: str, *, status_out: dict | None = None, allow_proxy: bool = False) -> str:
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

    ``status_out``, when provided, is a caller-owned dict that receives the
    real HTTP status of whichever tier's content is actually returned, under
    ``"http_status"``.

    Raises
    ------
    TimeoutError  — Playwright tier timed out and no Tier 1 fallback.
    ValueError    — Both tiers returned unusable content.
    """
    # ── Step 1: Tier 1 ────────────────────────────────────────────────
    # Always capture Tier 1's HTTP status locally (mirrored to the caller's
    # status_out when provided) so Step 2's failure handling can tell an
    # access BLOCK (WAF/geo 401/403/451) apart from a generic extraction error.
    _status: dict = status_out if status_out is not None else {}
    requests_html = _fetch_via_requests(url, status_out=_status, allow_proxy=allow_proxy)
    tier1_status = _status.get("http_status")

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
    # Give Tier 2 its own status slot so we can tell a genuine Tier-2 HTTP
    # status apart from a leftover Tier-1 status. A same-IP Tier 2 cannot
    # legitimately bypass an IP block, but it CAN silently RENDER a WAF/geo
    # block page (a >200-char "403 Forbidden" body raises no exception) — that
    # rendered page is not the regulator document and must never be sealed.
    _t2_status: dict = {}
    try:
        tier2_html = _fetch_via_playwright(url, status_out=_t2_status)

    except (TimeoutError, ValueError, Exception) as exc:
        # A hard access block (WAF/geo) must be surfaced as such — never
        # classified as a generic error, and never fed downstream as content.
        # The block page (e.g. a 520-byte "403 Forbidden") is NOT the regulator
        # document; using it as best-effort content would seal a bogus baseline.
        if tier1_status in (401, 403, 451):
            raise PermissionError(
                f"HTTP {tier1_status} — access blocked (WAF/geo) for {url}"
            ) from exc

        # A bot-wall / JS-gate Tier-1 page (Cloudflare "checking your browser",
        # "enable javascript", etc.) commonly returns HTTP 200, so the status
        # check above misses it. It is precisely why Tier 1 was rejected and Tier 2
        # was tried; if Tier 2 then fails, the ONLY thing left is the challenge
        # page — which is NOT the regulator document. Sealing it would poison the
        # baseline (and mask a chronically-blocked source as "healthy/unchanged"
        # forever). Report it as an access block instead of returning it.
        if requests_html is not None and _html_is_bot_wall(requests_html):
            raise PermissionError(
                f"access blocked (bot-wall/JS-gate) — Tier 1 challenge page and "
                f"Tier 2 {type(exc).__name__} for {url}"
            ) from exc

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
            # _fetch_via_playwright only writes status_out on a path that
            # does not raise (see its docstring), so a failed Tier 2 attempt
            # never overwrites it — status_out still holds Tier 1's status
            # from the call above, which matches the Tier 1 content we are
            # about to return here. Nothing to restore.
            return requests_html
        raise

    # Tier 2 succeeded. Its status reflects the content we are about to return,
    # so mirror it into the caller's status_out. Then refuse a rendered block
    # page: if Tier 2's OWN status is a hard block, the body is the block page,
    # not the document. (Using Tier 2's own status — not Tier 1's — means a
    # legitimate browser bypass of a requests-tier 403, i.e. Tier 2 got 200,
    # still returns real content.)
    if "http_status" in _t2_status:
        _status["http_status"] = _t2_status["http_status"]
    if _t2_status.get("http_status") in (401, 403, 451):
        raise PermissionError(
            f"HTTP {_t2_status['http_status']} — access blocked (WAF/geo) for {url}"
        )
    return tier2_html


def fetch_page_with_config(
    url: str,
    *,
    wait_for_selector: str | None = None,
    content_selector: str | None = None,
    force_playwright: bool = False,
    prefer_requests_on_low_content: bool = False,
    status_out: dict | None = None,
) -> str:
    """
    Fetch `url` with optional per-source Playwright config.

    When wait_for_selector or content_selector are provided, Playwright is
    used regardless of Tier 1 content quality (force_playwright=True implicit).
    These fields come from sources.json per-source config:
      "wait_for_selector": "main"    — wait for this CSS selector before capture
      "content_selector": "main"     — extract HTML from this element only

    Falls back to fetch_page() when no per-source config is set.

    SSRF guard: the explicit per-source Playwright run below installs the
    same per-request guard as the generic Tier 2 path (see
    _install_ssrf_guard / SSRF_RESIDUAL_RISK) — this is the path exercised by
    the authenticated "test a custom source" endpoint with
    fetch_method="playwright", so it must never navigate anywhere the
    requests-tier guard would refuse.

    ``status_out``, when provided, is a caller-owned dict that receives the
    real HTTP status of whichever path's content is returned, under
    ``"http_status"``.
    """
    needs_playwright = force_playwright or bool(wait_for_selector) or bool(content_selector)

    if not needs_playwright and prefer_requests_on_low_content:
        requests_html = _fetch_via_requests(url, status_out=status_out)
        if requests_html:
            return requests_html

    if not needs_playwright:
        return fetch_page(url, status_out=status_out)

    # Per-source Playwright run
    print(f"  Per-source Playwright config — {url}", file=sys.stderr, flush=True)
    if wait_for_selector:
        print(f"    wait_for_selector: {wait_for_selector}", file=sys.stderr, flush=True)
    if content_selector:
        print(f"    content_selector: {content_selector}", file=sys.stderr, flush=True)

    browser = _get_shared_browser()
    context = browser.new_context(
        user_agent=REQUESTS_UA,
        locale="en-US",
        viewport={"width": 1280, "height": 900},
    )
    _install_ssrf_guard(context)
    page = context.new_page()

    response = None
    try:
        response = page.goto(url, timeout=PAGE_TIMEOUT_MS, wait_until="networkidle")
    except Exception:
        try:
            page.wait_for_timeout(_PW_IDLE_EXTRA_MS)
        except Exception:
            pass

    try:
        if wait_for_selector:
            try:
                page.wait_for_selector(wait_for_selector, timeout=10_000)
            except Exception as exc:
                logger.warning("wait_for_selector '%s' not found within 10s at %s", wait_for_selector, url)
                raise TimeoutError(
                    f"wait_for_selector {wait_for_selector!r} not found at {url}"
                ) from exc
        else:
            page.wait_for_timeout(_PW_JS_SETTLE_MS)

        if content_selector:
            element = page.query_selector(content_selector)
            if element:
                html = element.inner_html()
                logger.info("content_selector '%s' extracted %d chars from %s", content_selector, len(html), url)
            else:
                logger.warning("content_selector '%s' matched nothing at %s", content_selector, url)
                raise ValueError(
                    f"content_selector {content_selector!r} matched nothing at {url}"
                )
        else:
            html = _capture_page_content(page)

        if not _final_url_is_safe(page):
            logger.warning(
                "fetch_page_with_config: navigation resolved to a non-public "
                "address for %s (final URL %s) — rejecting",
                url, getattr(page, "url", "?"),
            )
            raise ValueError(
                f"fetch_page_with_config: navigation resolved to a non-public address for {url}"
            )

        if status_out is not None and response is not None:
            try:
                status_out["http_status"] = response.status
            except Exception:
                pass
    finally:
        context.close()

    if not html or len(html) < 200:
        raise ValueError(f"fetch_page_with_config: empty result from {url}")

    return html
