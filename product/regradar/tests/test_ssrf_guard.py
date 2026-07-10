"""
SSRF guard on the bounded fetch paths (DEFECT A-ssrf).

The pipeline fetches ~116 external regulator URLs. Before this guard a source
could answer with a 30x redirect (or a rebound DNS record) pointing at an
internal address — cloud metadata (169.254.169.254), loopback, RFC1918,
link-local — and the fetch would happily connect: a classic SSRF.

The guard (app/adapters/base.py) follows redirects MANUALLY and, BEFORE firing
each hop, resolves the target host via socket.getaddrinfo and rejects when ANY
resolved IP is non-public. It pins the vetted IP so requests cannot re-resolve
to a different (internal) address between check and connect.

These tests use mocked DNS and mocked HTTP transport — no real network.
"""

from __future__ import annotations

import io
import ipaddress
import socket
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

import app.adapters.base as base
from app.adapters.base import (
    _guarded_get,
    _ip_is_blocked,
    _ip_to_netloc_host,
    _PinnedHTTPAdapter,
    _resolve_public_addr,
    _validate_fetch_target,
    fetch_bytes_bounded,
    fetch_text_bounded,
    fetch_text_bounded_status,
)


# ── IP classification ─────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "ip",
    [
        "127.0.0.1",        # loopback
        "127.0.0.53",       # loopback (systemd-resolved)
        "10.0.0.1",         # RFC1918 10/8
        "172.16.5.4",       # RFC1918 172.16/12
        "172.31.255.255",   # RFC1918 172.16/12 upper edge
        "192.168.1.1",      # RFC1918 192.168/16
        "169.254.169.254",  # link-local — cloud metadata endpoint
        "169.254.1.1",      # link-local 169.254/16
        "0.0.0.0",          # unspecified
        "::1",              # IPv6 loopback
        "::",               # IPv6 unspecified
        "fe80::1",          # IPv6 link-local fe80::/10
        "fc00::1",          # IPv6 unique-local fc00::/7
        "fd12:3456::1",     # IPv6 unique-local
        "::ffff:127.0.0.1", # IPv4-mapped loopback (smuggling attempt)
        "::ffff:10.0.0.1",  # IPv4-mapped RFC1918
        "::ffff:169.254.169.254",  # IPv4-mapped metadata
        "224.0.0.1",        # IPv4 multicast (all-hosts) — ipaddress marks is_global
        "239.255.255.250",  # IPv4 multicast — SSDP; ipaddress marks is_global
        "ff02::1",          # IPv6 multicast (all-nodes link-local) — is_global True
    ],
)
def test_ip_is_blocked_rejects_non_public(ip):
    assert _ip_is_blocked(ipaddress.ip_address(ip)), ip


@pytest.mark.parametrize(
    "ip",
    [
        "8.8.8.8",
        "1.1.1.1",
        "93.184.216.34",         # example.com
        "185.199.108.153",       # public
        "2606:4700:4700::1111",  # public IPv6
    ],
)
def test_ip_is_blocked_allows_public(ip):
    assert not _ip_is_blocked(ipaddress.ip_address(ip)), ip


# ── DNS resolution vetting ────────────────────────────────────────────────────

def _fake_getaddrinfo(*addresses):
    """Build a getaddrinfo replacement that yields the given IP strings."""
    def _inner(host, port, *args, **kwargs):
        infos = []
        for ip in addresses:
            family = socket.AF_INET6 if ":" in ip else socket.AF_INET
            infos.append((family, socket.SOCK_STREAM, 6, "", (ip, port)))
        return infos
    return _inner


def test_resolve_public_addr_accepts_public(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    vetted = _resolve_public_addr("vara.ae", 443)
    assert vetted is not None
    assert vetted[2] == "93.184.216.34"


def test_resolve_public_addr_rejects_private(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("169.254.169.254"))
    assert _resolve_public_addr("metadata.evil", 80) is None


def test_resolve_public_addr_rejects_when_any_record_private(monkeypatch):
    # Host publishes a public AND an internal A record — must reject, not
    # cherry-pick the public one.
    monkeypatch.setattr(
        base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34", "10.0.0.5")
    )
    assert _resolve_public_addr("dual.evil", 443) is None


def test_resolve_public_addr_handles_dns_failure(monkeypatch):
    def _boom(*a, **k):
        raise socket.gaierror("no such host")
    monkeypatch.setattr(base.socket, "getaddrinfo", _boom)
    assert _resolve_public_addr("nxdomain.invalid", 443) is None


def test_resolve_public_addr_handles_empty_result(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", lambda *a, **k: [])
    assert _resolve_public_addr("void.invalid", 443) is None


# ── URL / scheme validation ───────────────────────────────────────────────────

@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://internal/secret",
        "gopher://127.0.0.1:6379/",
        "not-a-url",
        "https:///no-host",
        "",
    ],
)
def test_validate_fetch_target_rejects_bad_schemes_and_urls(monkeypatch, url):
    # DNS should never even be consulted for these; make it explode if it is.
    monkeypatch.setattr(
        base.socket, "getaddrinfo",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("DNS must not run")),
    )
    assert _validate_fetch_target(url) is None


def test_validate_fetch_target_accepts_public_https(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    assert _validate_fetch_target("https://dfsa.ae/rulebook") is not None


def test_validate_fetch_target_blocks_private_host(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("192.168.0.10"))
    assert _validate_fetch_target("http://intranet.local/") is None


# ── HTTP transport doubles for _guarded_get ───────────────────────────────────

class _FakeResp:
    """Minimal stand-in for a streamed requests.Response."""

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
    """
    Replaces requests.Session. Serves scripted responses keyed by the URL
    _guarded_get asks for, recording which hosts were requested. Because the
    real _PinnedHTTPAdapter rewrites the URL host to the pinned IP inside
    send(), we bypass mounting entirely and match on the pre-mount URL that
    _guarded_get passes to session.get().
    """

    def __init__(self, script):
        self._script = script          # dict: url -> _FakeResp
        self.trust_env = True
        self.requested = []            # ordered list of URLs actually fetched
        self.mounted = []
        self.closed = False

    def mount(self, prefix, adapter):
        self.mounted.append((prefix, adapter))

    def close(self):
        self.closed = True

    def get(self, url, **kwargs):
        assert kwargs.get("allow_redirects") is False, "must not auto-follow redirects"
        assert kwargs.get("stream") is True
        self.requested.append(url)
        try:
            return self._script[url]
        except KeyError:  # pragma: no cover - test wiring error
            raise AssertionError(f"unexpected fetch: {url}")


# ── _guarded_get behaviour ────────────────────────────────────────────────────

def test_guarded_get_normal_public_fetch(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    resp = _FakeResp(200, body=b"hello", url="https://vara.ae/page")
    session = _FakeSession({"https://vara.ae/page": resp})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    out = _guarded_get(
        "https://vara.ae/page", headers={}, timeout=5, verify=True, label="test"
    )
    assert out is resp
    assert session.requested == ["https://vara.ae/page"]


def test_guarded_get_follows_public_redirect(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    redirect = _FakeResp(301, location="https://vara.ae/final", url="https://vara.ae/start")
    final = _FakeResp(200, body=b"ok", url="https://vara.ae/final")
    session = _FakeSession(
        {"https://vara.ae/start": redirect, "https://vara.ae/final": final}
    )
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    out = _guarded_get(
        "https://vara.ae/start", headers={}, timeout=5, verify=True, label="test"
    )
    assert out is final
    assert redirect.closed, "intermediate redirect response must be closed"
    assert session.requested == ["https://vara.ae/start", "https://vara.ae/final"]


def test_guarded_get_blocks_redirect_to_private_ip(monkeypatch):
    # First hop resolves public; the redirect target resolves to cloud metadata.
    def _dns(host, port, *a, **k):
        if host == "vara.ae":
            return _fake_getaddrinfo("93.184.216.34")(host, port)
        return _fake_getaddrinfo("169.254.169.254")(host, port)
    monkeypatch.setattr(base.socket, "getaddrinfo", _dns)

    redirect = _FakeResp(
        302, location="http://169.254.169.254/latest/meta-data/", url="https://vara.ae/start"
    )
    session = _FakeSession({"https://vara.ae/start": redirect})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    out = _guarded_get(
        "https://vara.ae/start", headers={}, timeout=5, verify=True, label="test"
    )
    assert out is None, "redirect to a private IP must be blocked"
    assert redirect.closed
    # The metadata host must never have been fetched.
    assert session.requested == ["https://vara.ae/start"]


def test_guarded_get_blocks_redirect_to_private_hostname(monkeypatch):
    # Redirect Location is a *hostname* that resolves internally (DNS rebind
    # style) — the guard resolves it before connecting and rejects.
    def _dns(host, port, *a, **k):
        if host == "dfsa.ae":
            return _fake_getaddrinfo("93.184.216.34")(host, port)
        return _fake_getaddrinfo("10.1.2.3")(host, port)
    monkeypatch.setattr(base.socket, "getaddrinfo", _dns)

    redirect = _FakeResp(
        307, location="https://internal.corp/admin", url="https://dfsa.ae/x"
    )
    session = _FakeSession({"https://dfsa.ae/x": redirect})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    out = _guarded_get("https://dfsa.ae/x", headers={}, timeout=5, verify=True, label="t")
    assert out is None
    assert session.requested == ["https://dfsa.ae/x"]


def test_guarded_get_first_hop_private_never_connects(monkeypatch):
    # The very first URL resolves internally — guard rejects before any GET.
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("127.0.0.1"))
    session = _FakeSession({})  # any fetch would raise
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    out = _guarded_get("http://localhost/admin", headers={}, timeout=5, verify=True, label="t")
    assert out is None
    assert session.requested == [], "must not fire a request to an internal host"
    assert session.closed, "session must be released on the blocked path"


def test_guarded_get_caps_redirect_chain(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    # A public host that redirects to itself forever.
    loop = _FakeResp(302, location="https://loop.ae/next", url="https://loop.ae/next")
    session = _FakeSession({"https://loop.ae/next": loop})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    out = _guarded_get("https://loop.ae/next", headers={}, timeout=5, verify=True, label="t")
    assert out is None, "redirect loop must terminate as failure, not hang"
    # 1 initial + _MAX_REDIRECTS follows, then give up.
    assert len(session.requested) == base._MAX_REDIRECTS + 1


def test_guarded_get_disables_trust_env(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    resp = _FakeResp(200, body=b"x", url="https://tax.gov.ae/")
    session = _FakeSession({"https://tax.gov.ae/": resp})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    _guarded_get("https://tax.gov.ae/", headers={}, timeout=5, verify=True, label="t")
    assert session.trust_env is False, "env proxies must not reroute the fetch"


def test_guarded_get_never_raises_on_transport_error(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))

    class _Boom(_FakeSession):
        def get(self, url, **kwargs):
            raise ConnectionError("connection reset")

    monkeypatch.setattr(base.requests, "Session", lambda: _Boom({}))
    out = _guarded_get("https://cbr.ru/", headers={}, timeout=5, verify=True, label="t")
    assert out is None


# ── public entry points thread the guard ──────────────────────────────────────

def test_fetch_text_bounded_status_returns_body_for_public(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    resp = _FakeResp(200, body=b"regulatory text", url="https://cbr.ru/x")
    session = _FakeSession({"https://cbr.ru/x": resp})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    status, text = fetch_text_bounded_status(
        "https://cbr.ru/x", headers={}, timeout=5
    )
    assert status == 200
    assert text == "regulatory text"


def test_fetch_text_bounded_status_blocks_ssrf_redirect(monkeypatch):
    def _dns(host, port, *a, **k):
        if host == "cbr.ru":
            return _fake_getaddrinfo("93.184.216.34")(host, port)
        return _fake_getaddrinfo("169.254.169.254")(host, port)
    monkeypatch.setattr(base.socket, "getaddrinfo", _dns)
    redirect = _FakeResp(
        302, location="http://169.254.169.254/", url="https://cbr.ru/x"
    )
    session = _FakeSession({"https://cbr.ru/x": redirect})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    status, text = fetch_text_bounded_status("https://cbr.ru/x", headers={}, timeout=5)
    assert status is None
    assert text is None


def test_fetch_text_bounded_wraps_status_variant(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    resp = _FakeResp(200, body=b"body text", url="https://dfsa.ae/")
    session = _FakeSession({"https://dfsa.ae/": resp})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    assert fetch_text_bounded("https://dfsa.ae/", headers={}, timeout=5) == "body text"


def test_fetch_text_bounded_returns_none_on_ssrf(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("127.0.0.1"))
    session = _FakeSession({})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    assert fetch_text_bounded("http://localhost/", headers={}, timeout=5) is None


def test_fetch_bytes_bounded_returns_body_for_public(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    resp = _FakeResp(200, body=b"<rss>feed</rss>", url="https://tax.gov.ae/rss")
    session = _FakeSession({"https://tax.gov.ae/rss": resp})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    out = fetch_bytes_bounded("https://tax.gov.ae/rss", headers={}, timeout=5)
    assert out == b"<rss>feed</rss>"


def test_fetch_bytes_bounded_blocks_ssrf(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("10.0.0.1"))
    session = _FakeSession({})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    assert fetch_bytes_bounded("http://internal/rss", headers={}, timeout=5) is None


def test_fetch_bytes_bounded_respects_content_length_cap(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    resp = _FakeResp(
        200,
        body=b"x",
        headers={"Content-Length": str(base.MAX_FETCH_BYTES + 1)},
        url="https://tax.gov.ae/big",
    )
    session = _FakeSession({"https://tax.gov.ae/big": resp})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    assert fetch_bytes_bounded("https://tax.gov.ae/big", headers={}, timeout=5) is None


# ── scraper.py Tier 1 inherits the guard ──────────────────────────────────────

def test_scraper_tier1_blocks_ssrf_redirect(monkeypatch):
    """
    scraper.py Tier 1 (_fetch_via_requests) routes through fetch_text_bounded,
    so a redirect to an internal address must be blocked there too — the
    metadata host is never contacted and Tier 1 escalates (returns None).
    """
    import app.scraper as scraper

    def _dns(host, port, *a, **k):
        if host == "cbr.ru":
            return _fake_getaddrinfo("93.184.216.34")(host, port)
        return _fake_getaddrinfo("169.254.169.254")(host, port)
    monkeypatch.setattr(base.socket, "getaddrinfo", _dns)

    redirect = _FakeResp(
        302, location="http://169.254.169.254/latest/meta-data/", url="https://cbr.ru/x"
    )
    session = _FakeSession({"https://cbr.ru/x": redirect})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    assert scraper._fetch_via_requests("https://cbr.ru/x") is None
    assert session.requested == ["https://cbr.ru/x"]


def test_scraper_tier1_normal_public_fetch(monkeypatch):
    import app.scraper as scraper

    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    resp = _FakeResp(200, body=b"<html>regulator page</html>", url="https://vara.ae/reg")
    session = _FakeSession({"https://vara.ae/reg": resp})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    assert scraper._fetch_via_requests("https://vara.ae/reg") == "<html>regulator page</html>"


# ── _ip_to_netloc_host: IPv6 literals must be bracketed ───────────────────────

@pytest.mark.parametrize(
    "ip, expected",
    [
        ("93.184.216.34", "93.184.216.34"),          # IPv4 — unchanged
        ("8.8.8.8", "8.8.8.8"),
        ("2606:4700:4700::1111", "[2606:4700:4700::1111]"),  # IPv6 — bracketed
        ("2001:db8::1", "[2001:db8::1]"),
        ("::1", "[::1]"),
        ("[2606:4700:4700::1111]", "[2606:4700:4700::1111]"),  # already bracketed
    ],
)
def test_ip_to_netloc_host_brackets_ipv6(ip, expected):
    assert _ip_to_netloc_host(ip) == expected


# ── _PinnedHTTPAdapter.send: the vetted IP is what actually gets dialled ───────
#
# The _FakeSession-based tests above replace requests.Session wholesale and
# never call _PinnedHTTPAdapter.send(), so the DNS-rebind/TOCTOU pinning — the
# crux of the SSRF fix — had ZERO coverage. These tests drive the real adapter
# and assert on the URL it hands to the underlying transport, which is exactly
# where the IPv6-bracketing regression lives.

class _CapturingHTTPAdapter(_PinnedHTTPAdapter):
    """
    Real _PinnedHTTPAdapter with the network hop stubbed. send() runs the true
    URL-rewrite logic, then we capture the rewritten request instead of opening
    a socket. The capture also re-parses the rewritten URL through requests'
    own PreparedRequest.prepare_url — the same call that raises InvalidURL on a
    bare (unbracketed) IPv6 netloc — so a malformed rewrite fails the test.
    """

    captured: dict = {}

    def send(self, request, **kwargs):
        # super() here is _PinnedHTTPAdapter, whose send() does the rewrite and
        # then calls HTTPAdapter.send(). We stub HTTPAdapter.send for the
        # duration so no real connection is attempted.
        real_transport_send = requests.adapters.HTTPAdapter.send

        def _capture(inner_self, req, **kw):
            type(self).captured = {
                "url": req.url,
                "host": req.headers.get("Host"),
            }
            # Prove requests accepts the rewritten URL (bare IPv6 would raise).
            reparsed = requests.PreparedRequest()
            reparsed.prepare_url(req.url, None)
            type(self).captured["reparsed_url"] = reparsed.url

            class _Resp:
                status_code = 200
                is_redirect = False
                headers: dict = {}
                url = req.url

                def close(self):
                    pass

            return _Resp()

        requests.adapters.HTTPAdapter.send = _capture
        try:
            return super().send(request, **kwargs)
        finally:
            requests.adapters.HTTPAdapter.send = real_transport_send


def _prepared_get(url: str) -> requests.PreparedRequest:
    """Build a PreparedRequest the way requests.Session.get would."""
    return requests.Request("GET", url, headers={"Host": urlsplit_host(url)}).prepare()


def urlsplit_host(url: str) -> str:
    from urllib.parse import urlsplit
    return urlsplit(url).hostname or ""


def test_pinned_adapter_dials_ipv4_and_preserves_host():
    adapter = _CapturingHTTPAdapter(pinned_ip="93.184.216.34", server_hostname="cbr.ru")
    adapter.send(_prepared_get("https://cbr.ru/page"))
    cap = _CapturingHTTPAdapter.captured
    assert cap["url"] == "https://93.184.216.34/page", "must dial the pinned IP, not re-resolve DNS"
    assert cap["host"] == "cbr.ru", "original Host header must be preserved for vhosting/SNI"


def test_pinned_adapter_brackets_ipv6_literal():
    """
    Regression guard for the IPv6 SSRF-fetch bug: a pinned IPv6 literal must be
    rewritten to a bracketed, RFC-3986-valid authority. On the pre-fix code the
    bare netloc `https://2606:4700:4700::1111/page` makes requests raise
    InvalidURL, _guarded_get swallows it, and every dual-stack regulator host
    silently fails to fetch. This test drives the real adapter and would fail
    on that bug.
    """
    adapter = _CapturingHTTPAdapter(
        pinned_ip="2606:4700:4700::1111", server_hostname="cbr.ru"
    )
    adapter.send(_prepared_get("https://cbr.ru/page"))
    cap = _CapturingHTTPAdapter.captured
    assert cap["url"] == "https://[2606:4700:4700::1111]/page", "IPv6 literal must be bracketed"
    assert cap["reparsed_url"] == "https://[2606:4700:4700::1111]/page", "requests must accept it"
    assert cap["host"] == "cbr.ru", "original Host header must be preserved"


def test_pinned_adapter_preserves_explicit_port_for_ipv6():
    adapter = _CapturingHTTPAdapter(
        pinned_ip="2606:4700:4700::1111", server_hostname="cbr.ru"
    )
    adapter.send(_prepared_get("https://cbr.ru:8443/x"))
    cap = _CapturingHTTPAdapter.captured
    assert cap["url"] == "https://[2606:4700:4700::1111]:8443/x"
    assert cap["reparsed_url"] == "https://[2606:4700:4700::1111]:8443/x"


def test_pinned_adapter_preserves_explicit_port_for_ipv4():
    adapter = _CapturingHTTPAdapter(pinned_ip="93.184.216.34", server_hostname="cbr.ru")
    adapter.send(_prepared_get("https://cbr.ru:8443/x"))
    cap = _CapturingHTTPAdapter.captured
    assert cap["url"] == "https://93.184.216.34:8443/x"


def _make_transport_capture(seen: dict, status: int = 200, body: bytes = b"ok"):
    """
    Build a replacement for requests.adapters.HTTPAdapter.send that records the
    request it receives (AFTER _PinnedHTTPAdapter.send has rewritten it) and
    returns a genuine requests.Response so requests' Session.send post-processing
    (cookies, redirect resolution) runs unbroken. Only the socket layer is
    stubbed — the real _PinnedHTTPAdapter still runs and rewrites the URL/Host.
    """
    from urllib3.response import HTTPResponse

    def _capture(inner_self, req, **kw):
        seen["url"] = req.url
        seen["host"] = req.headers.get("Host")
        raw = HTTPResponse(
            body=io.BytesIO(body), headers={}, status=status, preload_content=False
        )
        resp = requests.Response()
        resp.status_code = status
        resp.raw = raw
        resp.url = req.url
        resp.request = req
        resp.headers = requests.structures.CaseInsensitiveDict()
        return resp

    return _capture


def test_guarded_get_end_to_end_pins_ipv6_host(monkeypatch):
    """
    Full _guarded_get path with a REAL session and REAL _PinnedHTTPAdapter (only
    the socket-level transport is stubbed). The host resolves to a public IPv6
    address; the guard must vet it, pin it, and dial the bracketed literal —
    never re-resolving DNS at connect. On the pre-fix code the bare-IPv6 rewrite
    raises inside send(), _guarded_get's blanket except returns None, and the
    fetch silently fails for a 100%-legitimate host.
    """
    monkeypatch.setattr(
        base.socket, "getaddrinfo", _fake_getaddrinfo("2606:4700:4700::1111")
    )
    seen: dict = {}
    monkeypatch.setattr(
        requests.adapters.HTTPAdapter, "send", _make_transport_capture(seen)
    )

    out = _guarded_get(
        "https://cbr.ru/reg", headers={}, timeout=5, verify=True, label="t"
    )

    assert out is not None, "a legitimate public IPv6 host must NOT be silently dropped"
    assert out.status_code == 200
    assert seen["url"] == "https://[2606:4700:4700::1111]/reg", "must dial bracketed pinned IPv6"
    assert seen["host"] == "cbr.ru", "Host header must carry the original hostname"


def test_guarded_get_end_to_end_pins_ipv4_host(monkeypatch):
    """Same end-to-end path, IPv4 — the vetted IP is the one actually dialled."""
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    seen: dict = {}
    monkeypatch.setattr(
        requests.adapters.HTTPAdapter, "send", _make_transport_capture(seen)
    )

    out = _guarded_get(
        "https://vara.ae/reg", headers={}, timeout=5, verify=True, label="t"
    )

    assert out is not None
    assert seen["url"] == "https://93.184.216.34/reg", "must dial the vetted IPv4, not re-resolve"
    assert seen["host"] == "vara.ae"


# ── plain-HTTP pool must NOT crash on the TLS-only pinning kwargs ──────────────
#
# _PinnedHTTPAdapter injects server_hostname / assert_hostname so urllib3
# validates the cert against the real hostname while we dial the pinned IP.
# urllib3 strips server_hostname (an SSL_KEYWORD) for http pools, but NOT
# assert_hostname — so before the fix a plain-HTTP hop reached
# HTTPConnection.__init__(assert_hostname=...) and raised
#   TypeError: HTTPConnection.__init__() got an unexpected keyword argument 'assert_hostname'
# which _guarded_get's blanket except swallowed, silently dropping any
# https->http redirect and any future http:// source. Every prior success-path
# test used https with the transport stubbed, so init_poolmanager's kwargs were
# never exercised against a real http pool — this is that missing coverage.


def test_pinned_adapter_builds_http_pool_without_crash():
    """
    Regression guard for the assert_hostname TypeError. Ask the real pinned
    adapter's poolmanager for an *http* connection pool and force a real
    HTTPConnection to be constructed. On the pre-fix code this raises
    TypeError; the fix drops the TLS-only kwargs for http pools.
    """
    adapter = _PinnedHTTPAdapter(pinned_ip="93.184.216.34", server_hostname="neverssl.com")
    pool = adapter.poolmanager.connection_from_url("http://neverssl.com/")
    conn = pool._get_conn()  # constructs HTTPConnection — the crash site
    assert type(conn).__name__ == "HTTPConnection"
    # assert_hostname is TLS-only and must not have leaked onto the http conn.
    assert getattr(conn, "assert_hostname", None) is None


def test_pinned_adapter_https_pool_keeps_hostname_pinning():
    """
    The https pool MUST still carry server_hostname / assert_hostname so cert
    validation runs against the real hostname even though the socket dials the
    pinned IP — the fix must not weaken TLS verification.
    """
    adapter = _PinnedHTTPAdapter(pinned_ip="93.184.216.34", server_hostname="cbr.ru")
    pool = adapter.poolmanager.connection_from_url("https://cbr.ru/")
    conn = pool._get_conn()
    assert type(conn).__name__ == "HTTPSConnection"
    assert conn.assert_hostname == "cbr.ru"
    assert conn.server_hostname == "cbr.ru"


def test_guarded_get_end_to_end_plain_http_succeeds(monkeypatch):
    """
    Full _guarded_get path for a legitimate plain-HTTP fetch, with a REAL
    session and REAL _PinnedHTTPAdapter (only the socket-level transport is
    stubbed). Before the fix the http pool TypeErrors inside send(),
    _guarded_get returns None, and the fetch silently fails.
    """
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    seen: dict = {}
    monkeypatch.setattr(
        requests.adapters.HTTPAdapter, "send", _make_transport_capture(seen, body=b"plain http body")
    )

    out = _guarded_get(
        "http://neverssl.com/", headers={"User-Agent": "t"}, timeout=5, verify=True, label="t"
    )

    assert out is not None, "a legitimate plain-HTTP fetch must NOT be silently dropped"
    assert out.status_code == 200
    assert seen["url"] == "http://93.184.216.34/", "must dial the vetted IP over http"
    assert seen["host"] == "neverssl.com"


def test_guarded_get_follows_https_to_http_redirect(monkeypatch):
    """
    An https regulator source that 301-redirects to an http:// URL must be
    followed to completion. The final http hop exercises the http pool (the
    crash site) end-to-end through the real adapter.
    """
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    seen: dict = {}

    from urllib3.response import HTTPResponse

    def _capture(inner_self, req, **kw):
        seen.setdefault("urls", []).append(req.url)
        # First (https) hop: return a 301 to an http URL. Second (http) hop: 200.
        if req.url.endswith("/start"):
            raw = HTTPResponse(body=io.BytesIO(b""), headers={"Location": "http://reg.example/final"},
                               status=301, preload_content=False)
            resp = requests.Response()
            resp.status_code = 301
            resp.raw = raw
            resp.url = req.url
            resp.request = req
            resp.headers = requests.structures.CaseInsensitiveDict({"Location": "http://reg.example/final"})
            return resp
        raw = HTTPResponse(body=io.BytesIO(b"final over http"), headers={}, status=200, preload_content=False)
        resp = requests.Response()
        resp.status_code = 200
        resp.raw = raw
        resp.url = req.url
        resp.request = req
        resp.headers = requests.structures.CaseInsensitiveDict()
        return resp

    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", _capture)

    out = _guarded_get(
        "https://reg.example/start", headers={}, timeout=5, verify=True, label="t"
    )

    assert out is not None, "https->http redirect must complete, not TypeError to None"
    assert out.status_code == 200
    # https hop dialled over https, http hop dialled over http — both to the vetted IP.
    assert seen["urls"] == [
        "https://93.184.216.34/start",
        "http://93.184.216.34/final",
    ]
