from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import app.adapters.base as base
from app.scraper import (
    SSRF_RESIDUAL_RISK,
    _final_url_is_safe,
    _fetch_via_playwright,
    _install_ssrf_guard,
    _ssrf_guard_route,
    _ssrf_guard_websocket,
    fetch_page,
    fetch_page_with_config,
)

_REGULATORY_HTML = "<main>" + ("Regulatory circular content. " * 40) + "</main>"


def _fake_getaddrinfo(*addresses):
    """Build a getaddrinfo replacement that yields the given IP strings."""
    import socket as _socket

    def _inner(host, port, *args, **kwargs):
        infos = []
        for ip in addresses:
            family = _socket.AF_INET6 if ":" in ip else _socket.AF_INET
            infos.append((family, _socket.SOCK_STREAM, 6, "", (ip, port)))
        return infos
    return _inner


def _per_host_dns(public_hosts, default_private: str = "10.0.0.9"):
    """
    Per-host getaddrinfo fake for tests that mix a legitimate public hostname
    with a malicious/private target in the SAME monkeypatch scope.

    A blanket ``_fake_getaddrinfo("93.184.216.34")`` ignores the ``host`` it
    is asked to resolve, so in a redirect-chain test it would incorrectly
    make even a 169.254.169.254 / 127.0.0.1 hop "resolve publicly" too —
    silently defeating the very check under test. This resolver instead:
      - returns a public IP for hostnames in ``public_hosts``;
      - echoes a literal IP host back to itself (matching real getaddrinfo
        semantics for IP literals, so a metadata/loopback/RFC1918 literal is
        correctly identified as itself, not remapped to something else);
      - resolves anything else to a private IP (fail-closed default).
    """
    import ipaddress as _ipaddress

    def _resolver(host, port, *a, **k):
        if host in public_hosts:
            return _fake_getaddrinfo("93.184.216.34")(host, port)
        try:
            _ipaddress.ip_address(host)
            return _fake_getaddrinfo(host)(host, port)
        except ValueError:
            pass
        return _fake_getaddrinfo(default_private)(host, port)

    return _resolver


# ── existing Playwright content-capture fakes (SPA race retry) ────────────────


class _FakeElement:
    def inner_html(self) -> str:
        return "<main>" + ("Regulatory circular content. " * 40) + "</main>"


class _FakePage:
    def __init__(self) -> None:
        self.content_calls = 0
        self.wait_calls = 0
        self.url = "https://www.sca.gov.ae/en/regulations/regulations-listing"

    def goto(self, *args, **kwargs) -> None:
        return None

    def wait_for_timeout(self, *_args, **_kwargs) -> None:
        self.wait_calls += 1

    def wait_for_selector(self, *_args, **_kwargs) -> None:
        return None

    def query_selector(self, selector: str):
        return _FakeElement() if selector == "main" else None

    def content(self) -> str:
        self.content_calls += 1
        if self.content_calls == 1:
            raise RuntimeError("Page.content: Unable to retrieve content because the page is navigating and changing the content.")
        return "<html><body><main>" + ("Regulatory circular content. " * 40) + "</main></body></html>"


class _FakeContext:
    def __init__(self, page: _FakePage) -> None:
        self.page = page

    def new_page(self) -> _FakePage:
        return self.page

    def close(self) -> None:
        return None

    def route(self, *_args, **_kwargs) -> None:
        # Not exercised by this fake — the SSRF-guard wiring itself is
        # covered separately below with _RoutingFakeContext. This stub only
        # keeps this pre-existing SPA-race-retry test working now that
        # fetch_page_with_config unconditionally installs the guard.
        return None

    def route_web_socket(self, *_args, **_kwargs) -> None:
        # See route() above — not exercised by this fake.
        return None


class _FakeBrowser:
    def __init__(self, page: _FakePage) -> None:
        self.page = page

    def new_context(self, **_kwargs) -> _FakeContext:
        return _FakeContext(self.page)


def test_fetch_page_with_config_retries_page_content_when_dom_is_still_navigating():
    page = _FakePage()

    with patch("app.scraper._get_shared_browser", return_value=_FakeBrowser(page)):
        html = fetch_page_with_config(
            "https://www.sca.gov.ae/en/regulations/regulations-listing",
            force_playwright=True,
        )

    assert "Regulatory circular content" in html
    assert page.content_calls == 2
    assert page.wait_calls >= 1


# ── SSRF-guard fakes: a real context.route() handler wired and invoked ────────
#
# Unlike _FakeContext above (a no-op stub), these fakes actually store the
# handler passed to context.route() and invoke it — with the REAL
# _ssrf_guard_route function — for every hop of a simulated navigation. This
# exercises the true guard logic (which calls the real
# app.adapters.base._validate_fetch_target), not just a hand-rolled
# assumption about how it should behave. A route.abort() during any hop
# raises from goto(), mirroring Chromium's actual net::ERR_FAILED behaviour
# (verified empirically against a real headless Chromium instance — see
# test_real_browser_* below).


class _FakeRoute:
    def __init__(self) -> None:
        self.aborted = False
        self.continued = False

    def abort(self, *_a, **_kw) -> None:
        self.aborted = True

    def continue_(self, *_a, **_kw) -> None:
        self.continued = True


class _FakeRequest:
    def __init__(self, url: str) -> None:
        self.url = url


class _FakeResponse:
    def __init__(self, status: int) -> None:
        self.status = status


class _RoutingFakePage:
    """
    Simulates enough of Playwright's Page to exercise the real route
    handler: goto() replays every URL in ``hops`` (representing the initial
    navigation request plus each redirect hop Chromium would emit as a
    separate routed request) through the handler registered via
    context.route(). If any hop is aborted, goto() raises — exactly as real
    Chromium does for an aborted navigation request.
    """

    def __init__(
        self,
        context: "_RoutingFakeContext",
        hops: list[str] | None = None,
        response_status: int | None = 200,
        html: str = _REGULATORY_HTML,
        final_url: str | None = None,
    ) -> None:
        self._context = context
        self._response_status = response_status
        self._html = html
        self._final_url = final_url
        self.url = "about:blank"
        self._goto_url: str | None = None
        self._hops = hops
        self._navigation_blocked = False

    def goto(self, url: str, **_kwargs):
        self._goto_url = url
        hops = self._hops if self._hops is not None else [url]
        handler = self._context.route_handler
        for hop_url in hops:
            route = _FakeRoute()
            request = _FakeRequest(hop_url)
            assert handler is not None, "context.route() was never wired"
            handler(route, request)
            if route.aborted:
                self.url = "chrome-error://chromewebdata/"
                self._navigation_blocked = True
                raise RuntimeError(f"net::ERR_FAILED at {hop_url}")
            assert route.continued, "route handler must abort() or continue_()"
        self.url = self._final_url or hops[-1]
        if self._response_status is None:
            return None
        return _FakeResponse(self._response_status)

    def wait_for_timeout(self, *_a, **_kw) -> None:
        return None

    def wait_for_selector(self, *_a, **_kw) -> None:
        return None

    def query_selector(self, _selector: str):
        return None

    def content(self) -> str:
        # Matches real Chromium's behaviour after an aborted navigation
        # (verified manually against a real headless browser): the page
        # lands on chrome-error://chromewebdata/ with an empty document —
        # the blocked target's body is never rendered, let alone captured.
        if self._navigation_blocked:
            return "<html><head></head><body></body></html>"
        return self._html


class _RoutingFakeContext:
    def __init__(self, page_factory) -> None:
        self.route_handler = None
        self.websocket_handler = None
        self._page_factory = page_factory
        self.closed = False

    def route(self, pattern: str, handler) -> None:
        assert pattern == "**/*"
        self.route_handler = handler

    def route_web_socket(self, pattern: str, handler) -> None:
        assert pattern == "**/*"
        self.websocket_handler = handler

    def new_page(self) -> _RoutingFakePage:
        page = self._page_factory(self)
        return page

    def close(self) -> None:
        self.closed = True


class _RoutingFakeBrowser:
    def __init__(self, page_factory) -> None:
        self._page_factory = page_factory
        self.contexts: list[_RoutingFakeContext] = []

    def new_context(self, **_kwargs) -> _RoutingFakeContext:
        context = _RoutingFakeContext(self._page_factory)
        self.contexts.append(context)
        return context


def _browser_for(hops=None, response_status=200, html=_REGULATORY_HTML, final_url=None):
    def factory(context):
        return _RoutingFakePage(
            context, hops=hops, response_status=response_status, html=html, final_url=final_url
        )
    return _RoutingFakeBrowser(factory)


# ── _ssrf_guard_route / _install_ssrf_guard: direct unit coverage ─────────────


def test_ssrf_guard_route_aborts_metadata_ip(monkeypatch):
    route = _FakeRoute()
    request = _FakeRequest("http://169.254.169.254/latest/meta-data/")
    _ssrf_guard_route(route, request)
    assert route.aborted is True
    assert route.continued is False


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/admin",
        "http://10.0.0.5/internal",
        "http://192.168.1.1/router",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/admin",
    ],
)
def test_ssrf_guard_route_aborts_reserved_targets(url):
    route = _FakeRoute()
    _ssrf_guard_route(route, _FakeRequest(url))
    assert route.aborted is True, url


def test_ssrf_guard_route_continues_public_target(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    route = _FakeRoute()
    _ssrf_guard_route(route, _FakeRequest("https://vara.ae/circular"))
    assert route.continued is True
    assert route.aborted is False


@pytest.mark.parametrize(
    "url",
    [
        "data:image/png;base64,aGVsbG8=",
        "blob:https://vara.ae/uuid-goes-here",
        "about:blank",
        "chrome-error://chromewebdata/",
    ],
)
def test_ssrf_guard_route_allows_non_network_schemes_without_dns(monkeypatch, url):
    # DNS must never be consulted for these — make it explode if it is.
    monkeypatch.setattr(
        base.socket, "getaddrinfo",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("DNS must not run for safe schemes")),
    )
    route = _FakeRoute()
    _ssrf_guard_route(route, _FakeRequest(url))
    assert route.continued is True
    assert route.aborted is False


def test_install_ssrf_guard_wires_the_real_handler():
    context = _RoutingFakeContext(lambda ctx: None)
    _install_ssrf_guard(context)
    assert context.route_handler is _ssrf_guard_route
    assert context.websocket_handler is _ssrf_guard_websocket


# ── _ssrf_guard_websocket: separate interception surface from route() ─────────
#
# Discovered during self-review (not in the original finding text): Playwright
# does NOT run context.route() handlers for WebSocket upgrade handshakes — a
# page's own `new WebSocket("ws://169.254.169.254/...")` bypasses the route
# guard above entirely and opens a real TCP connection to the target,
# confirmed empirically against a real headless Chromium (a raw TCP listener
# received a genuine WS handshake with zero route() callbacks firing). A
# separate context.route_web_socket() handler is required and is wired by
# _install_ssrf_guard. These tests cover it directly.


class _FakeWebSocketRoute:
    def __init__(self, url: str) -> None:
        self.url = url
        self.connected = False
        self.closed = False

    def connect_to_server(self):
        self.connected = True
        return self

    def close(self, *_a, **_kw) -> None:
        self.closed = True


def test_ssrf_guard_websocket_blocks_metadata_ip_without_connecting():
    ws = _FakeWebSocketRoute("ws://169.254.169.254/latest/meta-data/")
    _ssrf_guard_websocket(ws)
    assert ws.connected is False


@pytest.mark.parametrize(
    "ws_url",
    [
        "ws://127.0.0.1/admin",
        "ws://10.0.0.5/internal",
        "wss://169.254.169.254/",
    ],
)
def test_ssrf_guard_websocket_blocks_reserved_targets(ws_url):
    ws = _FakeWebSocketRoute(ws_url)
    _ssrf_guard_websocket(ws)
    assert ws.connected is False, ws_url


def test_ssrf_guard_websocket_allows_public_target(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    ws = _FakeWebSocketRoute("wss://vara.ae/live")
    _ssrf_guard_websocket(ws)
    assert ws.connected is True


def test_ssrf_guard_websocket_rejects_non_ws_scheme_without_connecting():
    ws = _FakeWebSocketRoute("file:///etc/passwd")
    _ssrf_guard_websocket(ws)
    assert ws.connected is False


def test_ssrf_guard_websocket_never_calls_close():
    """
    Regression guard for the hang observed during manual testing: calling
    ws.close() from inside this handler hung browser/context teardown on
    the installed Playwright version. Leaving a blocked target unconnected
    (never calling connect_to_server()) was verified to both block the
    connection AND complete cleanly. This test locks in "never close()".
    """
    ws = _FakeWebSocketRoute("ws://169.254.169.254/")
    _ssrf_guard_websocket(ws)
    assert ws.closed is False
    assert ws.connected is False


# ── _final_url_is_safe: backstop unit coverage ─────────────────────────────────


class _UrlOnlyPage:
    def __init__(self, url: str) -> None:
        self.url = url


def test_final_url_is_safe_rejects_private_landed_host(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("10.0.0.9"))
    assert _final_url_is_safe(_UrlOnlyPage("http://internal.evil/x")) is False


def test_final_url_is_safe_accepts_public_landed_host(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    assert _final_url_is_safe(_UrlOnlyPage("https://vara.ae/circular")) is True


def test_final_url_is_safe_accepts_about_blank_and_chrome_error():
    assert _final_url_is_safe(_UrlOnlyPage("about:blank")) is True
    assert _final_url_is_safe(_UrlOnlyPage("chrome-error://chromewebdata/")) is True


def test_final_url_is_safe_rejects_metadata_literal():
    assert _final_url_is_safe(_UrlOnlyPage("http://169.254.169.254/latest/meta-data/")) is False


# ── fetch_page_with_config(force_playwright=True): the exploited endpoint ─────
#
# This is the exact path from Finding 1: authenticated "test a custom
# source" → run_source_intake(force_playwright via fetch_method="playwright")
# → fetch_page_with_config(force_playwright=True) → (pre-fix) page.goto(url)
# with zero SSRF checking, Chromium follows the target/redirect unguarded.


@pytest.mark.parametrize(
    "url",
    [
        "http://169.254.169.254/latest/meta-data/",
        "http://127.0.0.1/admin",
        "http://10.1.2.3/internal",
    ],
)
def test_fetch_page_with_config_playwright_blocks_direct_nav_to_reserved_ip(url):
    """
    REPRODUCTION for Finding 1 (direct navigation).

    Before the fix: fetch_page_with_config(force_playwright=True) called
    page.goto(url) with no SSRF check at all — this would have returned
    Chromium's response body from the internal target. After the fix: the
    per-request route guard aborts the navigation before Chromium connects,
    and the harness's fallback capture yields too little content
    ("empty result") — no internal content is returned.
    """
    browser = _browser_for(response_status=None)
    with patch("app.scraper._get_shared_browser", return_value=browser):
        with pytest.raises(ValueError, match="empty result"):
            fetch_page_with_config(url, force_playwright=True)


def test_fetch_page_with_config_playwright_blocks_redirect_to_metadata_ip(monkeypatch):
    """
    REPRODUCTION for Finding 1 (redirect hop).

    A source that starts on a legitimate public host but 302-redirects to
    the cloud metadata endpoint. Every hop Chromium fires goes through the
    route guard, so the second hop is aborted even though the first hop
    (the public host) was allowed through.
    """
    monkeypatch.setattr(base.socket, "getaddrinfo", _per_host_dns(public_hosts={"cbr.ru"}))
    hops = ["https://cbr.ru/start", "http://169.254.169.254/latest/meta-data/"]
    browser = _browser_for(hops=hops, response_status=None)
    with patch("app.scraper._get_shared_browser", return_value=browser):
        with pytest.raises(ValueError, match="empty result"):
            fetch_page_with_config("https://cbr.ru/start", force_playwright=True)


def test_fetch_page_with_config_playwright_final_url_backstop_catches_bypass(monkeypatch):
    """
    Defense-in-depth: even if every routed request were somehow allowed
    through (e.g. a navigation path that does not surface as a fresh routed
    request — the residual gap documented in SSRF_RESIDUAL_RISK), the final
    landed URL is re-checked after capture and rejected if it is private.
    """
    monkeypatch.setattr(base.socket, "getaddrinfo", _per_host_dns(public_hosts={"cbr.ru"}))
    # hops=[] means no request is routed through the guard at all — the
    # only thing standing between this and a leak is the final-URL backstop.
    browser = _browser_for(hops=[], response_status=200, html=_REGULATORY_HTML,
                            final_url="http://169.254.169.254/latest/meta-data/")
    with patch("app.scraper._get_shared_browser", return_value=browser):
        with pytest.raises(ValueError, match="non-public address"):
            fetch_page_with_config("https://cbr.ru/start", force_playwright=True)


def test_fetch_page_with_config_playwright_allows_normal_public_fetch(monkeypatch):
    """
    The fix must not break legitimate fetches: a normal public host passes
    the route guard and returns real content, unchanged from pre-fix
    behaviour.
    """
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    browser = _browser_for(response_status=200, html=_REGULATORY_HTML)
    with patch("app.scraper._get_shared_browser", return_value=browser):
        html = fetch_page_with_config("https://vara.ae/circular", force_playwright=True)
    assert "Regulatory circular content" in html


def test_fetch_page_with_config_playwright_surfaces_http_status(monkeypatch):
    """Finding 2 support: the Playwright tier must thread the real response
    status back out through status_out (see test_source_intake.py for the
    full run_source_intake-level proof)."""
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    browser = _browser_for(response_status=503, html=_REGULATORY_HTML)
    status_out: dict = {}
    with patch("app.scraper._get_shared_browser", return_value=browser):
        fetch_page_with_config("https://vara.ae/circular", force_playwright=True, status_out=status_out)
    assert status_out.get("http_status") == 503


# ── _fetch_via_playwright: the generic two-tier fallback path ─────────────────
#
# fetch_page() escalates here automatically when Tier 1 (requests) fails or
# returns too little content; app/health.py, app/pipeline.py, and
# app/source_runs.py all reach this indirectly through fetch_page(). The
# same guard applies here so the fix protects every caller, not just the
# explicit per-source config path.


def test_fetch_via_playwright_blocks_direct_nav_to_metadata_ip():
    browser = _browser_for(response_status=None)
    with patch("app.scraper._get_shared_browser", return_value=browser):
        with pytest.raises(Exception):
            _fetch_via_playwright("http://169.254.169.254/latest/meta-data/")


def test_fetch_via_playwright_allows_normal_public_fetch(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    browser = _browser_for(response_status=200, html=_REGULATORY_HTML)
    with patch("app.scraper._get_shared_browser", return_value=browser):
        html = _fetch_via_playwright("https://vara.ae/circular")
    assert "Regulatory circular content" in html


def test_fetch_page_falls_back_to_tier1_when_tier2_ssrf_blocked(monkeypatch):
    """
    fetch_page() Tier1->Tier2 escalation: when Tier 1 (requests) returns
    thin/low-quality content and Tier 2 (Playwright) is then blocked by the
    SSRF guard for landing on a private redirect target, fetch_page() must
    fall back to the (already SSRF-guarded) Tier 1 content rather than
    raising or leaking anything from the blocked Tier 2 attempt.
    """
    monkeypatch.setattr(base.socket, "getaddrinfo", _per_host_dns(public_hosts={"cbr.ru"}))

    thin_html = "<html><body><p>too short</p></body></html>"
    with patch("app.scraper._fetch_via_requests", return_value=thin_html) as mocked_tier1:
        def _tier1_side_effect(url, status_out=None, **kw):
            if status_out is not None:
                status_out["http_status"] = 200
            return thin_html
        mocked_tier1.side_effect = _tier1_side_effect

        browser = _browser_for(hops=["https://cbr.ru/x", "http://127.0.0.1/internal"], response_status=None)
        with patch("app.scraper._get_shared_browser", return_value=browser):
            status_out: dict = {}
            html = fetch_page("https://cbr.ru/x", status_out=status_out)

    assert html == thin_html
    # Tier 1's status must be preserved — not overwritten by the blocked
    # Tier 2 attempt (which never reaches the "record status" line because
    # it raises before getting there).
    assert status_out.get("http_status") == 200


# ── access-block honesty: a WAF/geo 403 must not masquerade as a generic error ──


def test_fetch_page_surfaces_waf_403_as_access_block(monkeypatch):
    """A hard WAF/geo block (Tier-1 HTTP 403, Tier-2 Playwright empty) must be
    raised as an access block — classified as 'blocked', never a generic error,
    and the block page must never be used as best-effort content. This is the
    live CBUAE-from-datacenter case: rulebook.centralbank.ae 403s the droplet IP."""
    from app.monitor import _classify_access_status

    def _tier1_403(url, status_out=None, **kw):
        if status_out is not None:
            status_out["http_status"] = 403
        return None  # fetch_text_bounded_status returns a None body on non-2xx

    def _tier2_empty(url, status_out=None):
        raise ValueError(f"Playwright returned empty HTML for {url}")

    monkeypatch.setattr("app.scraper._fetch_via_requests", _tier1_403)
    monkeypatch.setattr("app.scraper._fetch_via_playwright", _tier2_empty)

    with pytest.raises(PermissionError) as ei:
        fetch_page("https://rulebook.centralbank.ae/en/rulebook/stored-value-facilities")
    msg = str(ei.value).lower()
    assert "403" in msg and "blocked" in msg
    # The monitor classifier must now read this as a block, not a generic error.
    assert _classify_access_status(ei.value) == "blocked"


def test_fetch_page_block_page_body_never_used_as_content(monkeypatch):
    """Even when Tier-1 returns a short block-page BODY (not None), a 401/403/451
    status must prevent that body from being sealed as best-effort content — a
    bogus '403 Forbidden' baseline is worse than an honest access-block failure."""
    block_body = "<html><head><title>403 Forbidden</title></head><body>403</body></html>"

    def _tier1_403_body(url, status_out=None, **kw):
        if status_out is not None:
            status_out["http_status"] = 403
        return block_body

    def _tier2_empty(url, status_out=None):
        raise ValueError("Playwright returned empty HTML")

    monkeypatch.setattr("app.scraper._fetch_via_requests", _tier1_403_body)
    monkeypatch.setattr("app.scraper._fetch_via_playwright", _tier2_empty)

    with pytest.raises(PermissionError):
        fetch_page("https://rulebook.centralbank.ae/en/rulebook/x")


def test_fetch_page_rejects_tier2_rendered_block_page(monkeypatch):
    """Tier 2 (Playwright) can RENDER a WAF block page with no exception (>200
    chars). If Tier 2's OWN HTTP status is a block (403), that body must be
    refused — not sealed as content. (The block guard must cover Tier-2's
    success path, not only its exception path.)"""
    def _tier1_lowcontent(url, status_out=None, **kw):
        if status_out is not None:
            status_out["http_status"] = 200
        return "<html><body><p>thin</p></body></html>"  # low → escalate to Tier 2

    def _tier2_block_page(url, status_out=None):
        if status_out is not None:
            status_out["http_status"] = 403
        return "<html><head><title>403 Forbidden</title></head><body>" + "x" * 400 + "</body></html>"

    monkeypatch.setattr("app.scraper._fetch_via_requests", _tier1_lowcontent)
    monkeypatch.setattr("app.scraper._fetch_via_playwright", _tier2_block_page)

    with pytest.raises(PermissionError) as ei:
        fetch_page("https://rulebook.centralbank.ae/en/rulebook/x")
    assert "403" in str(ei.value).lower()


def test_fetch_page_refuses_tier1_botwall_when_tier2_fails(monkeypatch):
    """A Tier-1 bot-wall / JS-gate page (HTTP 200, e.g. Cloudflare 'checking your
    browser') must NOT be sealed as best-effort content when Tier 2 then fails.
    A bot-wall returns 200, so the 401/403/451 status check misses it — the phrase
    check refuses it, reporting an access block instead of poisoning the baseline
    (which would otherwise mask a chronically-blocked source as healthy forever)."""
    from app.monitor import _classify_access_status

    botwall = (
        "<html><body><h1>Checking your browser before accessing</h1>"
        "<p>Please enable JavaScript to continue. Cloudflare Ray ID: abc123</p>"
        + "<p>.</p>" * 60 + "</body></html>"
    )

    def _tier1_botwall(url, status_out=None, **kw):
        if status_out is not None:
            status_out["http_status"] = 200
        return botwall

    def _tier2_timeout(url, status_out=None):
        raise TimeoutError(f"Playwright navigation timed out for {url}")

    monkeypatch.setattr("app.scraper._fetch_via_requests", _tier1_botwall)
    monkeypatch.setattr("app.scraper._fetch_via_playwright", _tier2_timeout)

    with pytest.raises(PermissionError) as ei:
        fetch_page("https://rulebook.centralbank.ae/en/rulebook/x")
    assert "blocked" in str(ei.value).lower()
    assert _classify_access_status(ei.value) == "blocked"


def test_fetch_page_thin_tier1_still_best_effort_when_tier2_fails(monkeypatch):
    """An honestly-THIN Tier-1 page (no bot-wall phrase) must STILL be returned as
    best-effort when Tier 2 fails — the bot-wall refusal must not over-reach and
    turn every thin page into a hard failure. Thin content is monitored as-is and
    surfaces as QUALITY_DROP/low_content downstream, not a lost run."""
    thin = "<html><body><p>Short but real regulatory note.</p></body></html>"

    def _tier1_thin(url, status_out=None, **kw):
        if status_out is not None:
            status_out["http_status"] = 200
        return thin

    def _tier2_timeout(url, status_out=None):
        raise TimeoutError("Playwright timed out")

    monkeypatch.setattr("app.scraper._fetch_via_requests", _tier1_thin)
    monkeypatch.setattr("app.scraper._fetch_via_playwright", _tier2_timeout)

    assert fetch_page("https://vara.ae/some-thin-page") == thin


def test_fetch_page_tier2_browser_bypass_of_requests_403_returns_content(monkeypatch):
    """A site that 403s the requests tier but serves 200 to a real browser must
    STILL yield content — the block check uses Tier 2's own status (200), never
    Tier 1's stale 403 — so we don't over-reject a legitimate browser bypass."""
    def _tier1_403(url, status_out=None, **kw):
        if status_out is not None:
            status_out["http_status"] = 403
        return None

    good_html = "<html><body><main>" + "Real regulatory content. " * 40 + "</main></body></html>"

    def _tier2_ok(url, status_out=None):
        if status_out is not None:
            status_out["http_status"] = 200
        return good_html

    monkeypatch.setattr("app.scraper._fetch_via_requests", _tier1_403)
    monkeypatch.setattr("app.scraper._fetch_via_playwright", _tier2_ok)

    out = fetch_page("https://someregulator.example/x")
    assert out == good_html


def test_fetch_via_requests_proxy_gated_by_allow_proxy(monkeypatch):
    """The proxy is engaged ONLY when allow_proxy=True (trusted monitoring). The
    default (user-URL test path) never proxies, even for an allowlisted host —
    closing the 'user aims the owner proxy' hole."""
    monkeypatch.setenv("STATUTEPROOF_FETCH_PROXY", "http://proxy.example:8080")
    monkeypatch.delenv("STATUTEPROOF_PROXY_HOSTS", raising=False)
    captured: dict = {}

    def _capture(url, *, headers, timeout, max_bytes, label, proxy=None):
        captured["proxy"] = proxy
        return 200, "<html>ok</html>"

    monkeypatch.setattr("app.scraper.fetch_text_bounded_status", _capture)
    from app.scraper import _fetch_via_requests

    # Allowlisted host but DEFAULT (user path) → no proxy.
    _fetch_via_requests("https://rulebook.centralbank.ae/x")
    assert captured["proxy"] is None
    # Trusted path + allowlisted host → proxy engaged.
    _fetch_via_requests("https://rulebook.centralbank.ae/x", allow_proxy=True)
    assert captured["proxy"] == "http://proxy.example:8080"
    # Trusted path but NON-allowlisted host → still no proxy.
    _fetch_via_requests("https://vara.ae/x", allow_proxy=True)
    assert captured["proxy"] is None


# ── SSRF_RESIDUAL_RISK: honesty check ──────────────────────────────────────────


def test_ssrf_residual_risk_is_documented_and_non_empty():
    """The fix must not overclaim: a residual-risk statement must exist and
    explicitly name the DNS-rebind gap that IP pinning (used by the requests
    tier) closes but per-request route interception cannot."""
    assert isinstance(SSRF_RESIDUAL_RISK, str)
    assert "dns" in SSRF_RESIDUAL_RISK.lower()
    assert "rebind" in SSRF_RESIDUAL_RISK.lower()
    assert "pin" in SSRF_RESIDUAL_RISK.lower()


# ── real headless Chromium, no mocking (skips cleanly if unavailable) ─────────
#
# Everything above mocks Playwright the way the rest of this test suite does.
# These two tests additionally drive a REAL headless Chromium against a REAL
# local HTTP server, through the REAL fetch_page_with_config/_fetch_via_playwright
# code paths (nothing patched except the well-known secret payload), to prove
# the abort actually happens at the browser level and not just in a Python
# mock's assumptions about Playwright's API. Verified manually against
# Playwright 1.58.0 headless Chromium before writing these assertions.


def _make_local_server(payload: bytes):
    import http.server
    import threading

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - stdlib method name
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *_a, **_kw) -> None:
            return None

    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, server.server_address[1]


def _real_chromium_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            browser.close()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _real_chromium_available(), reason="Chromium browser binaries not installed in this environment")
def test_real_browser_blocks_loopback_target_no_leak():
    payload = b"INTERNAL-SECRET-METADATA-PAYLOAD-6f19"
    server, port = _make_local_server(payload)
    try:
        url = f"http://127.0.0.1:{port}/secret"
        with pytest.raises(Exception) as excinfo:
            fetch_page_with_config(url, force_playwright=True)
        # Whatever failed, the raw secret payload must never surface in the
        # exception text (which would indicate it leaked into captured HTML
        # and only failed the downstream length/quality check).
        assert payload.decode() not in str(excinfo.value)
    finally:
        server.shutdown()


@pytest.mark.skipif(not _real_chromium_available(), reason="Chromium browser binaries not installed in this environment")
def test_real_browser_allows_legitimate_fetch_when_dns_says_public(monkeypatch):
    """
    Same real-Chromium harness, but with app.adapters.base's DNS resolution
    patched so the guard treats the (otherwise loopback) test server's host
    as public — isolating "does the guard break legitimate fetches" from
    "is loopback actually blocked" (covered by the test above) without
    depending on real internet access in CI.
    """
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    payload = ("<html><body><main>" + "Legit regulator content. " * 40 + "</main></body></html>").encode()
    server, port = _make_local_server(payload)
    try:
        url = f"http://127.0.0.1:{port}/legit"
        html = fetch_page_with_config(url, force_playwright=True)
        assert "Legit regulator content" in html
    finally:
        server.shutdown()


@pytest.mark.skipif(not _real_chromium_available(), reason="Chromium browser binaries not installed in this environment")
def test_real_browser_blocks_client_side_websocket_pivot(monkeypatch):
    """
    Real-Chromium proof for the WebSocket gap found during self-review: a
    page's own JS opens `new WebSocket("ws://127.0.0.1:<port>/")` targeting
    a real local TCP listener standing in for an internal service. Without
    context.route_web_socket() wired, the target receives a genuine TCP
    connection (verified manually — this exact scenario, unguarded, was how
    the gap was found). With the guard installed, the listener must receive
    no connection at all.

    The top-level navigation target is DNS-spoofed to "public" (by port, not
    by host — both servers bind 127.0.0.1) purely so the malicious page's JS
    actually runs; real getaddrinfo is used for every other port (including
    the WS target), so the WS target's loopback-ness — and therefore whether
    the guard blocks it — is genuine, not spoofed away.
    """
    import socket
    import threading as _threading
    import http.server

    raw_srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    raw_srv.bind(("127.0.0.1", 0))
    raw_srv.listen(5)
    raw_port = raw_srv.getsockname()[1]
    connections_received: list[bool] = []

    def _accept_loop() -> None:
        while True:
            try:
                conn, _addr = raw_srv.accept()
                connections_received.append(True)
                conn.close()
            except Exception:
                return

    _threading.Thread(target=_accept_loop, daemon=True).start()

    malicious_html = (
        '<html><body><div id="out">pending</div><script>'
        f'var ws = new WebSocket("ws://127.0.0.1:{raw_port}/");'
        'ws.onerror = function(){document.getElementById("out").innerText="ws-error";};'
        "</script></body></html>"
    ).encode()

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(malicious_html)

        def log_message(self, *_a, **_kw) -> None:
            return None

    page_server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    page_port = page_server.server_address[1]
    _threading.Thread(target=page_server.serve_forever, daemon=True).start()

    original_getaddrinfo = socket.getaddrinfo

    def _spoof_only_page_port(host, port, *a, **k):
        if port == page_port:
            return _fake_getaddrinfo("93.184.216.34")(host, port)
        return original_getaddrinfo(host, port, *a, **k)

    monkeypatch.setattr(base.socket, "getaddrinfo", _spoof_only_page_port)

    try:
        url = f"http://127.0.0.1:{page_port}/"
        html = fetch_page_with_config(url, force_playwright=True)
        assert "pending" in html or "ws-error" in html, (
            "sanity check: the top-level nav must have actually reached the "
            "malicious page for this test to mean anything"
        )
    finally:
        page_server.shutdown()
        raw_srv.close()

    assert connections_received == [], (
        "a page's client-side new WebSocket(...) to a loopback target must "
        "never reach the target — context.route_web_socket() must block it "
        "the same way context.route() blocks navigation/redirects/fetch"
    )
