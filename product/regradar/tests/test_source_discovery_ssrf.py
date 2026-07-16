"""
Regression tests for the source-discovery module (group G6-discovery-coverage).

Bug 3 — Authenticated SSRF via HTTP redirect. `discover_source` (and the other
        discovery fetch paths) called `requests.get(..., allow_redirects=True)`,
        which auto-follows a 30x redirect with NO per-hop revalidation.
        `validate_public_url` only vets the ORIGINAL host, so an attacker-owned
        public page could 302 the fetch to a private/link-local address (e.g.
        cloud metadata 169.254.169.254) and have the body returned in the
        report. The fix routes every discovery GET through the base per-hop
        SSRF guard (`_guarded_get`), which re-vets and IP-pins each hop.

Bug 4 — `capture_playwright_network_candidates` created the browser context /
        page OUTSIDE any try/except, so a disconnected/crashed shared browser
        made the exception propagate uncaught out of discovery instead of
        returning a structured rejection like every other branch.

All transport and DNS are mocked; no real network calls.
"""

from __future__ import annotations

import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.adapters.base as base
import app.source_discovery as sd
import app.source_tester as st


# ── HTTP / DNS transport doubles (mirrors tests/test_ssrf_guard.py) ────────────

class _FakeResp:
    """Minimal stand-in for a streamed requests.Response."""

    def __init__(self, status, *, location=None, body=b"", url="https://x/"):
        self.status_code = status
        self.url = url
        self.headers = {}
        if location is not None:
            self.headers["Location"] = location
        self._body = body
        self.encoding = "utf-8"
        self.apparent_encoding = "utf-8"

    @property
    def is_redirect(self):
        return self.status_code in (301, 302, 303, 307, 308) and "Location" in self.headers

    @property
    def ok(self):
        return 200 <= self.status_code < 400

    @property
    def text(self):
        return self._body.decode("utf-8", "replace")

    def iter_content(self, chunk_size):
        yield self._body

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _FakeSession:
    def __init__(self, script):
        self._script = script
        self.trust_env = True
        self.requested: list[str] = []

    def mount(self, prefix, adapter):
        pass

    def close(self):
        pass

    def get(self, url, **kwargs):
        assert kwargs.get("allow_redirects") is False, "must follow redirects manually"
        self.requested.append(url)
        try:
            return self._script[url]
        except KeyError:  # pragma: no cover - wiring error
            raise AssertionError(f"unexpected fetch: {url}")


def _dns(host, port, *args, **kwargs):
    """Public attacker host resolves public; metadata host resolves link-local."""
    ip = "169.254.169.254" if host == "169.254.169.254" else "93.184.216.34"
    family = socket.AF_INET6 if ":" in ip else socket.AF_INET
    return [(family, socket.SOCK_STREAM, 6, "", (ip, port))]


# ── Bug 3: SSRF via redirect to cloud-metadata is blocked ──────────────────────

def test_discover_source_blocks_redirect_to_metadata_ip(monkeypatch):
    secret = b"AKIA-SECRET-METADATA-CREDENTIALS"
    attacker = "https://attacker.example/redirect"
    metadata = "http://169.254.169.254/latest/meta-data/iam/security-credentials/"

    script = {
        attacker: _FakeResp(302, location=metadata, url=attacker),
        metadata: _FakeResp(200, body=secret, url=metadata),
    }
    session = _FakeSession(script)

    # DNS used by both the base guard and validate_public_url.
    monkeypatch.setattr(base.socket, "getaddrinfo", _dns)
    monkeypatch.setattr(st.socket, "getaddrinfo", _dns)
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    report = sd.discover_source(
        attacker,
        include_sitemap=False,
        include_feeds=False,
        include_documents=False,
    )

    blob = str(report)
    # The metadata credential body must NEVER surface in the discovery output.
    assert secret.decode() not in blob
    # The guard rejected the hop and surfaced a benign warning instead.
    assert any("SSRF" in w or "blocked" in w.lower() for w in report.get("warnings", []))
    # The safe original request was attempted; the private hop was refused
    # before connecting (its URL is never the *returned* body).
    assert attacker in session.requested


def test_probe_blocks_redirect_to_private_ip(monkeypatch):
    """`_probe` (feed/sitemap prober) must also refuse a redirect to a private IP."""
    start = "https://gov.example/feed"
    internal = "http://10.0.0.5/secret"
    secret = b"INTERNAL-ONLY-BODY"

    def _dns2(host, port, *a, **k):
        ip = "10.0.0.5" if host == "10.0.0.5" else "93.184.216.34"
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port))]

    script = {
        start: _FakeResp(302, location=internal, url=start),
        internal: _FakeResp(200, body=secret, url=internal),
    }
    session = _FakeSession(script)
    monkeypatch.setattr(base.socket, "getaddrinfo", _dns2)
    monkeypatch.setattr(st.socket, "getaddrinfo", _dns2)
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    status, ct, text = sd._probe(start)

    assert text is None
    assert status is None
    # Proves _probe went through the per-hop guarded path (not the old
    # allow_redirects=True requests.get, which would bypass this session
    # entirely and follow the 302 into the private network).
    assert session.requested == [start]
    assert internal not in session.requested


# ── Bug 4: browser-context failure returns a rejection, does not raise ─────────

def test_capture_network_candidates_returns_rejection_when_browser_unavailable(monkeypatch):
    """
    A disconnected/crashed shared browser makes new_context() raise. The
    function must return a structured 'rejected' candidate, not propagate.
    """
    # validate_public_url must pass so we reach the browser-creation code.
    monkeypatch.setattr(st.socket, "getaddrinfo", _dns)

    class _BrokenBrowser:
        def new_context(self, *a, **k):
            raise RuntimeError("Browser has been closed")

    monkeypatch.setattr(
        "app.scraper._get_shared_browser", lambda: _BrokenBrowser()
    )

    result = sd.capture_playwright_network_candidates("https://attacker.example/x")

    assert isinstance(result, list) and len(result) == 1
    assert result[0]["candidate_status"] == "rejected"
    assert "Browser context unavailable" in result[0]["failure_reason"]
    assert result[0]["next_action"] == "manual_review"


# ── SEC-1: the Playwright page-network capture path must ALSO be SSRF-guarded ──
# Bug 3 fixed the requests-tier redirect guard; capture_playwright_network_candidates
# still did page.goto() with no context.route() guard and echoed response bodies
# (up to 5000 chars) back to the caller — reachable via
# POST /api/custom-sources/discover {network:true} by any authenticated account.

class _PWResponse:
    def __init__(self, url, content_type, body="", status=200):
        self.url = url
        self.headers = {"content-type": content_type}
        self.status = status
        self._body = body

    def text(self):
        return self._body


class _PWPage:
    def __init__(self, responses, final_url):
        self._responses = responses
        self._cb = None
        self.url = final_url

    def on(self, event, cb):
        if event == "response":
            self._cb = cb

    def goto(self, url, **_k):
        for r in self._responses:
            if self._cb:
                self._cb(r)

    def wait_for_timeout(self, _ms):
        pass


class _PWContext:
    def __init__(self, page):
        self._page = page
        self.route_calls = []
        self.ws_route_calls = []

    def route(self, pattern, handler):
        self.route_calls.append((pattern, handler))

    def route_web_socket(self, pattern, handler):
        self.ws_route_calls.append((pattern, handler))

    def new_page(self):
        return self._page

    def close(self):
        pass


class _PWBrowser:
    def __init__(self, context):
        self._context = context

    def new_context(self, **_k):
        return self._context


def _wire_browser(monkeypatch, responses, final_url="https://vara.ae/rulebook"):
    ctx = _PWContext(_PWPage(responses, final_url))
    monkeypatch.setattr("app.scraper._get_shared_browser", lambda: _PWBrowser(ctx))
    monkeypatch.setattr(base.socket, "getaddrinfo", _dns)
    monkeypatch.setattr(st.socket, "getaddrinfo", _dns)
    return ctx


def test_capture_installs_guard_and_drops_private_response_bodies(monkeypatch):
    responses = [
        _PWResponse("http://169.254.169.254/latest/meta-data/", "application/json", body="SECRET-METADATA"),
        _PWResponse("https://vara.ae/api/rules.json", "application/json", body='{"ok":true}'),
    ]
    ctx = _wire_browser(monkeypatch, responses)
    out = sd.capture_playwright_network_candidates("https://vara.ae/rulebook")

    # (a) the SSRF guard is installed on the discovery context (both surfaces).
    assert ctx.route_calls, "SSRF route guard must be installed on the discovery context"
    assert ctx.ws_route_calls, "WebSocket SSRF guard must be installed too"

    blob = " ".join(str(c) for c in out)
    # (b) the metadata-IP response is never captured and its body never echoed.
    assert "169.254.169.254" not in blob, "metadata-IP response must never be captured"
    assert "SECRET-METADATA" not in blob, "private response body must never be echoed to the caller"
    # the genuine public JSON candidate is still captured.
    assert "vara.ae/api/rules.json" in blob


def test_capture_rejects_navigation_to_private_final_url(monkeypatch):
    ctx = _wire_browser(monkeypatch, responses=[], final_url="http://169.254.169.254/latest/")
    out = sd.capture_playwright_network_candidates("https://vara.ae/rulebook")
    assert len(out) == 1
    assert out[0]["candidate_status"] == "rejected"
    assert "non-public" in out[0]["failure_reason"].lower()
    assert ctx.route_calls  # guard still installed before the navigation was refused
