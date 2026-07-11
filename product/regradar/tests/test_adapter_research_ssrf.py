"""
SSRF guard on the adapter-research fetch paths (group C-ssrf-residue).

`run.py adapter-research` investigates a single source to help plan a custom
adapter. Before this fix its two fetch sites —

    * `_probe_discovery_paths` (sitemap/robots probing), and
    * `run_adapter_research` Tier 1 (the initial page GET)

— called `requests.get(url, allow_redirects=True)` directly, with NO
`validate_public_url` and no per-hop IP pinning. `requests` auto-follows a 30x
redirect with no revalidation, so a malicious / compromised / MITM'd source
could answer the research fetch with a redirect (or a rebound DNS record)
pointing at an internal address — cloud metadata (169.254.169.254), loopback,
RFC1918, link-local — and the body would be fetched and surfaced in the report.

The fix routes both sites through the shared per-hop SSRF guard in
`app.adapters.base` (`fetch_text_bounded_status` → `_guarded_get`), which
follows redirects MANUALLY and re-resolves + IP-pins every hop BEFORE
connecting, rejecting any non-public target.

All transport and DNS are mocked; no real network calls.
"""

from __future__ import annotations

import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.adapter_research as ar
import app.adapters.base as base


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

    def iter_content(self, chunk_size):
        yield self._body

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _FakeSession:
    """Replaces requests.Session inside app.adapters.base. Serves scripted
    responses keyed by the pre-mount URL that _guarded_get passes to
    session.get(), and records every host actually contacted."""

    def __init__(self, script):
        self._script = script
        self.trust_env = True
        self.requested: list[str] = []

    def mount(self, prefix, adapter):
        pass

    def close(self):
        pass

    def get(self, url, **kwargs):
        # The old raw `requests.get(..., allow_redirects=True)` would bypass this
        # guarded session entirely; asserting allow_redirects is False proves the
        # call went through the per-hop guard.
        assert kwargs.get("allow_redirects") is False, "must follow redirects manually"
        self.requested.append(url)
        try:
            return self._script[url]
        except KeyError:  # pragma: no cover - wiring error
            raise AssertionError(f"unexpected fetch: {url}")


def _dns_public_metadata(host, port, *args, **kwargs):
    """Public host resolves public; the metadata literal resolves link-local."""
    ip = "169.254.169.254" if host == "169.254.169.254" else "93.184.216.34"
    family = socket.AF_INET6 if ":" in ip else socket.AF_INET
    return [(family, socket.SOCK_STREAM, 6, "", (ip, port))]


def _dns_all_public(host, port, *args, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]


# ── _probe_discovery_paths goes through the guard ──────────────────────────────

def test_probe_discovery_paths_blocks_redirect_to_metadata_ip(monkeypatch):
    """A source whose sitemap/robots paths 302-redirect to cloud metadata must
    be refused before connecting — nothing is returned and the metadata host is
    never contacted."""
    base_url = "https://gov.example"
    metadata = "http://169.254.169.254/latest/meta-data/iam/security-credentials/"
    secret = b"AKIA-SECRET-METADATA-CREDENTIALS"

    # Every discovery path answers with a 302 to the metadata endpoint.
    script = {
        base_url + p: _FakeResp(302, location=metadata, url=base_url + p)
        for p in ar._DISCOVERY_PATHS
    }
    script[metadata] = _FakeResp(200, body=secret, url=metadata)
    session = _FakeSession(script)

    monkeypatch.setattr(base.socket, "getaddrinfo", _dns_public_metadata)
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    found = ar._probe_discovery_paths(base_url)

    assert found == [], "redirect to a private IP must yield no discovery hits"
    # Only the public first hops were dialled; the metadata host was refused
    # BEFORE connecting, so it never appears in the request log or the output.
    assert metadata not in session.requested
    assert secret.decode() not in str(found)


def test_probe_discovery_paths_returns_public_sitemap(monkeypatch):
    """Sanity: a legitimate public 200 sitemap is returned, with content-type
    inferred from the path extension (the guarded transport hides headers)."""
    base_url = "https://gov.example"
    sitemap_url = base_url + "/sitemap.xml"
    body = b"<?xml version='1.0'?><urlset>" + b"<url><loc>x</loc></url>" * 20 + b"</urlset>"

    script = {base_url + p: _FakeResp(404, url=base_url + p) for p in ar._DISCOVERY_PATHS}
    script[sitemap_url] = _FakeResp(200, body=body, url=sitemap_url)
    session = _FakeSession(script)

    monkeypatch.setattr(base.socket, "getaddrinfo", _dns_all_public)
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    found = ar._probe_discovery_paths(base_url)

    assert len(found) == 1
    hit = found[0]
    assert hit["path"] == "/sitemap.xml"
    assert hit["url"] == sitemap_url
    assert hit["status"] == 200
    assert hit["content_type"] == "application/xml"
    assert hit["size"] == len(body.decode("utf-8"))


# ── run_adapter_research Tier 1 goes through the guard ─────────────────────────

def test_run_adapter_research_tier1_blocks_ssrf_redirect(monkeypatch):
    """The full `run.py adapter-research` entry point: the Tier 1 page fetch must
    refuse a redirect into the private network. The metadata body must never be
    fetched, and the result reports a fetch failure rather than internal data."""
    start = "https://attacker.example/start"
    metadata = "http://169.254.169.254/latest/meta-data/"
    secret = b"INTERNAL-METADATA-SECRET"

    # Isolate Tier 1: no browser fallback, no discovery probing.
    monkeypatch.setattr(
        ar, "find_sources",
        lambda q: [{"name": "Attacker Source", "url": start,
                    "jurisdiction": "XX", "category": "test"}],
    )
    monkeypatch.setattr(ar, "_probe_discovery_paths", lambda base_url: [])

    def _no_browser(url):
        raise RuntimeError("no playwright in test env")
    monkeypatch.setattr(ar, "_fetch_via_playwright", _no_browser)

    script = {
        start: _FakeResp(302, location=metadata, url=start),
        metadata: _FakeResp(200, body=secret, url=metadata),
    }
    session = _FakeSession(script)
    monkeypatch.setattr(base.socket, "getaddrinfo", _dns_public_metadata)
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    result = ar.run_adapter_research("attacker")

    assert result is not None
    assert result["http_status"] is None, "SSRF-blocked fetch must not report a status"
    assert result["fetch_ok"] is False
    assert result["fetch_error"] and (
        "SSRF" in result["fetch_error"] or "blocked" in result["fetch_error"].lower()
    )
    # The public first hop was attempted; the metadata host was refused before
    # connecting and its body never reached the report.
    assert start in session.requested
    assert metadata not in session.requested
    assert secret.decode() not in str(result)


# ── explicit routing proof: the guarded function is the one being called ───────

def test_probe_discovery_paths_calls_guarded_transport(monkeypatch):
    """Direct proof the call site was swapped: _probe_discovery_paths invokes
    app.adapters.base.fetch_text_bounded_status (imported into adapter_research)
    rather than a raw redirect-following requests.get."""
    calls: list[tuple[str, dict]] = []

    def _spy(url, **kwargs):
        calls.append((url, kwargs))
        return None, None  # request "failed / blocked" — never raises

    monkeypatch.setattr(ar, "fetch_text_bounded_status", _spy)

    out = ar._probe_discovery_paths("https://gov.example")

    assert out == []
    assert [u for u, _ in calls] == [
        "https://gov.example" + p for p in ar._DISCOVERY_PATHS
    ]
    # The guard is called with a bounded, non-auto-redirect contract.
    for _, kw in calls:
        assert "allow_redirects" not in kw  # the guard follows hops manually
        assert kw.get("label") == "adapter-research"
