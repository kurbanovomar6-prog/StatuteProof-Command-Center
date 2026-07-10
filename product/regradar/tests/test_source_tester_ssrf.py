"""
SSRF guard on the user-supplied source-test path (FINDING 1).

``test_source_url()`` is reachable from the authenticated ``/api`` source-test
endpoint with a USER-SUPPLIED url — a higher-value SSRF target than the static
source list. Before the fix, Tier 1 did a plain ``requests.get(..., allow_
redirects=True)`` after only a one-shot ``validate_public_url()`` check, so a
live DNS-rebind or a 30x redirect toward a private/loopback/metadata address
would still be followed.

The fix routes the Tier 1 HTML fetch through
``app.adapters.base.fetch_text_bounded_status``, which re-validates and IP-pins
every hop before connecting. These tests mock the DNS resolver seam and the
HTTP transport — no real network — and assert that a redirect toward an
internal address never reaches that host.
"""

from __future__ import annotations

import socket
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import app.adapters.base as base
import app.source_tester as source_tester


def _fake_getaddrinfo(mapping):
    """getaddrinfo replacement resolving each host to a scripted IP string."""
    def _inner(host, port, *args, **kwargs):
        ip = mapping[host]
        family = socket.AF_INET6 if ":" in ip else socket.AF_INET
        return [(family, socket.SOCK_STREAM, 6, "", (ip, port))]
    return _inner


class _FakeResp:
    """Minimal streamed requests.Response stand-in (mirrors test_ssrf_guard)."""

    def __init__(self, status, *, location=None, body=b"", headers=None, url="https://x/"):
        self.status_code = status
        self.url = url
        self.headers = dict(headers or {})
        if location is not None:
            self.headers["Location"] = location
        self._body = body
        self.encoding = "utf-8"
        self.apparent_encoding = "utf-8"
        self.closed = False

    @property
    def is_redirect(self):
        return self.status_code in (301, 302, 303, 307, 308) and "Location" in self.headers

    def iter_content(self, chunk_size):
        yield self._body

    def close(self):
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
        return False


class _FakeSession:
    """Replaces requests.Session; serves scripted responses keyed by URL."""

    def __init__(self, script):
        self._script = script
        self.trust_env = True
        self.requested = []
        self.closed = False

    def mount(self, prefix, adapter):
        pass

    def close(self):
        self.closed = True

    def get(self, url, **kwargs):
        assert kwargs.get("allow_redirects") is False
        assert kwargs.get("stream") is True
        self.requested.append(url)
        try:
            return self._script[url]
        except KeyError:  # pragma: no cover - test wiring error
            raise AssertionError(f"unexpected fetch: {url}")


def _block_playwright(monkeypatch):
    """Make the Tier 2 fallback observable and offline (no real browser)."""
    calls: list[str] = []

    def _fake_playwright(url):
        calls.append(url)
        return None  # Playwright also fails to reach anything

    monkeypatch.setattr(source_tester, "_fetch_via_playwright", _fake_playwright)
    return calls


def test_test_source_url_blocks_redirect_to_metadata_ip(monkeypatch):
    """
    A user-supplied URL whose first hop is public but 302-redirects toward the
    cloud-metadata IP must have that redirect refused: the metadata host is
    never fetched, and Tier 1 yields no HTML (fetch_ok=False → cannot_monitor).
    """
    # First hop resolves public; the redirect target is cloud metadata.
    def _dns(host, port, *a, **k):
        table = {"evil.example": "93.184.216.34", "169.254.169.254": "169.254.169.254"}
        return _fake_getaddrinfo(table)(host, port)

    monkeypatch.setattr(base.socket, "getaddrinfo", _dns)

    redirect = _FakeResp(
        302,
        location="http://169.254.169.254/latest/meta-data/",
        url="https://evil.example/start",
    )
    session = _FakeSession({"https://evil.example/start": redirect})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    pw_calls = _block_playwright(monkeypatch)

    result = source_tester.test_source_url("https://evil.example/start")

    # The metadata host was never contacted — only the first public hop fired.
    assert session.requested == ["https://evil.example/start"]
    # Tier 1 produced no usable HTML, so the fetch path fell through to
    # Playwright (also offline here) and ultimately reports it cannot monitor.
    assert pw_calls == ["https://evil.example/start"]
    assert result["status"] == "failed"
    assert result["verdict"] == "cannot_monitor"
    assert result["safe_url"] is True  # validate_public_url passed the entry URL


def test_test_source_url_blocks_redirect_to_loopback(monkeypatch):
    """A redirect toward loopback (127.0.0.1) is refused on the same path."""
    def _dns(host, port, *a, **k):
        table = {"reg.example": "93.184.216.34", "127.0.0.1": "127.0.0.1"}
        return _fake_getaddrinfo(table)(host, port)

    monkeypatch.setattr(base.socket, "getaddrinfo", _dns)

    redirect = _FakeResp(
        301, location="http://127.0.0.1/admin", url="https://reg.example/x"
    )
    session = _FakeSession({"https://reg.example/x": redirect})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    pw_calls = _block_playwright(monkeypatch)

    result = source_tester.test_source_url("https://reg.example/x")

    assert session.requested == ["https://reg.example/x"]
    assert "127.0.0.1" not in session.requested
    assert pw_calls == ["https://reg.example/x"]
    assert result["verdict"] == "cannot_monitor"


def test_test_source_url_public_fetch_captures_status_and_html(monkeypatch):
    """
    Contract preserved: a normal public 200 flows through the guarded helper,
    captures http_status, and yields extracted HTML for the verdict.
    """
    monkeypatch.setattr(
        base.socket, "getaddrinfo", _fake_getaddrinfo({"vara.ae": "93.184.216.34"})
    )
    html = (
        b"<html><body><main>"
        b"<h1>VARA Rulebook Update</h1>"
        b"<p>" + b"The Virtual Assets Regulatory Authority has amended its rulebook. " * 8 + b"</p>"
        b"<p>" + b"Licensed VASPs must review their compliance controls before the effective date. " * 6 + b"</p>"
        b"<p>" + b"Further guidance is available on the official VARA portal for registered firms. " * 6 + b"</p>"
        b"</main></body></html>"
    )
    resp = _FakeResp(200, body=html, url="https://vara.ae/rulebook")
    session = _FakeSession({"https://vara.ae/rulebook": resp})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    # Playwright must NOT be needed for a good Tier 1 fetch.
    def _no_playwright(url):  # pragma: no cover - must not be called
        raise AssertionError("Playwright must not run when Tier 1 succeeds")

    monkeypatch.setattr(source_tester, "_fetch_via_playwright", _no_playwright)

    result = source_tester.test_source_url("https://vara.ae/rulebook")

    assert session.requested == ["https://vara.ae/rulebook"]
    assert result["http_status"] == 200
    assert result["fetch_method"] == "generic"
    assert result["status"] == "ok"
    assert result["extracted_chars"] > 0
