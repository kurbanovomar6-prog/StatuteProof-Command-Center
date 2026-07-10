"""
SSRF guard on the document-download path (DEFECT A-ssrf, finding 1).

document_extractor.fetch_document() downloads PDF/DOC links that were parsed
out of the HTML of a monitored regulator page (find_document_links). That page
is untrusted: a malicious / compromised / MITM'd source controls its content,
including the href of an embedded document link and any redirect that link's
server returns.

Before this fix fetch_document() called requests.get(url, allow_redirects=True)
with ZERO host/IP validation, so a document link that 30x-redirected to
http://169.254.169.254/latest/meta-data/... (cloud metadata) was transparently
followed and the credential body was handed to extract_pdf_text(). This path is
exercised during source onboarding (source_tester include_documents=True) and
adapter research (adapter_research PDF extraction).

These tests prove fetch_document() now routes through the same SSRF guard
(_guarded_get) used by the bounded page-text fetches: every hop is resolved and
vetted BEFORE connecting, and the vetted IP is pinned. No real network is used —
DNS and the HTTP session are mocked at app.adapters.base level (the module
_guarded_get lives in, which document_extractor imports).
"""

from __future__ import annotations

import socket
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import app.adapters.base as base
from app.document_extractor import fetch_document


# ── transport doubles (a .ok-aware variant of the test_ssrf_guard fakes) ──────

def _fake_getaddrinfo(*addresses):
    def _inner(host, port, *args, **kwargs):
        infos = []
        for ip in addresses:
            family = socket.AF_INET6 if ":" in ip else socket.AF_INET
            infos.append((family, socket.SOCK_STREAM, 6, "", (ip, port)))
        return infos
    return _inner


class _FakeResp:
    """Stand-in for a streamed requests.Response, including .ok for fetch_document."""

    def __init__(self, status, *, location=None, body=b"", headers=None, url="https://x/"):
        self.status_code = status
        self.url = url
        self.headers = dict(headers or {})
        if location is not None:
            self.headers["Location"] = location
        self._body = body
        self.closed = False

    @property
    def ok(self):
        return self.status_code < 400

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
        assert kwargs.get("allow_redirects") is False, "must not auto-follow redirects"
        assert kwargs.get("stream") is True
        self.requested.append(url)
        try:
            return self._script[url]
        except KeyError:  # pragma: no cover - test wiring error
            raise AssertionError(f"unexpected fetch: {url}")


# ── the attack the finding describes ──────────────────────────────────────────

def test_fetch_document_blocks_redirect_to_cloud_metadata(monkeypatch):
    """
    A PDF link on a regulator page points at a server that 302-redirects to the
    cloud-metadata endpoint. The guard must resolve the redirect target, see a
    link-local (169.254.0.0/16) address, and refuse to connect — the metadata
    host is never fetched and no data is returned to extract_pdf_text().
    """
    def _dns(host, port, *a, **k):
        if host == "attacker.example":
            return _fake_getaddrinfo("93.184.216.34")(host, port)
        return _fake_getaddrinfo("169.254.169.254")(host, port)
    monkeypatch.setattr(base.socket, "getaddrinfo", _dns)

    redirect = _FakeResp(
        302,
        location="http://169.254.169.254/latest/meta-data/iam/security-credentials/",
        url="https://attacker.example/report.pdf",
    )
    session = _FakeSession({"https://attacker.example/report.pdf": redirect})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    out = fetch_document("https://attacker.example/report.pdf")

    assert out["status"] == "failed"
    assert out["data"] == b""
    assert out["bytes"] == 0
    # The metadata host must never have been contacted.
    assert session.requested == ["https://attacker.example/report.pdf"]
    assert redirect.closed


def test_fetch_document_blocks_first_hop_private(monkeypatch):
    """A document link whose host resolves directly to loopback is rejected
    before any GET is issued."""
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("127.0.0.1"))
    session = _FakeSession({})  # any fetch would raise
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    out = fetch_document("http://localhost/secret.pdf")

    assert out["status"] == "failed"
    assert out["data"] == b""
    assert session.requested == [], "must not fire a request to an internal host"


def test_fetch_document_blocks_rfc1918_host(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("10.1.2.3"))
    session = _FakeSession({})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    out = fetch_document("https://intranet.corp/leak.pdf")
    assert out["status"] == "failed"
    assert session.requested == []


# ── the guard must not break legitimate public downloads ──────────────────────

def test_fetch_document_downloads_public_pdf(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    resp = _FakeResp(
        200,
        body=b"%PDF-1.7 real regulatory pdf bytes",
        headers={"content-type": "application/pdf; charset=binary"},
        url="https://vara.ae/circular.pdf",
    )
    session = _FakeSession({"https://vara.ae/circular.pdf": resp})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    out = fetch_document("https://vara.ae/circular.pdf")

    assert out["status"] == "ok"
    assert out["http_status"] == 200
    assert out["content_type"] == "application/pdf"
    assert out["data"] == b"%PDF-1.7 real regulatory pdf bytes"
    assert out["bytes"] == len(out["data"])
    assert out["error"] == ""


def test_fetch_document_follows_public_redirect(monkeypatch):
    """A public->public redirect (e.g. http->https CDN) is followed and the
    final body is returned — the guard does not break benign redirects."""
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    redirect = _FakeResp(301, location="https://cdn.vara.ae/final.pdf", url="https://vara.ae/doc.pdf")
    final = _FakeResp(
        200,
        body=b"%PDF final",
        headers={"content-type": "application/pdf"},
        url="https://cdn.vara.ae/final.pdf",
    )
    session = _FakeSession(
        {"https://vara.ae/doc.pdf": redirect, "https://cdn.vara.ae/final.pdf": final}
    )
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    out = fetch_document("https://vara.ae/doc.pdf")
    assert out["status"] == "ok"
    assert out["data"] == b"%PDF final"
    assert session.requested == [
        "https://vara.ae/doc.pdf",
        "https://cdn.vara.ae/final.pdf",
    ]


# ── existing semantics preserved through the rewrite ──────────────────────────

def test_fetch_document_skips_unsupported_scheme(monkeypatch):
    """file:// must be skipped before DNS is ever consulted."""
    monkeypatch.setattr(
        base.socket, "getaddrinfo",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("DNS must not run")),
    )
    out = fetch_document("file:///etc/passwd")
    assert out["status"] == "skipped"
    assert "Unsupported scheme" in out["error"]


def test_fetch_document_reports_http_error_status(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    resp = _FakeResp(404, url="https://vara.ae/missing.pdf")
    session = _FakeSession({"https://vara.ae/missing.pdf": resp})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    out = fetch_document("https://vara.ae/missing.pdf")
    assert out["status"] == "failed"
    assert out["http_status"] == 404
    assert out["error"] == "HTTP 404"


def test_fetch_document_skips_oversized_content_length(monkeypatch):
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    resp = _FakeResp(
        200,
        body=b"x",
        headers={"content-type": "application/pdf", "content-length": "99999999"},
        url="https://vara.ae/big.pdf",
    )
    session = _FakeSession({"https://vara.ae/big.pdf": resp})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    out = fetch_document("https://vara.ae/big.pdf", max_bytes=1000)
    assert out["status"] == "skipped"
    assert "too large" in out["error"].lower()


def test_fetch_document_skips_when_streamed_body_exceeds_cap(monkeypatch):
    """No Content-Length header, but the streamed body blows past max_bytes."""
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    resp = _FakeResp(
        200,
        body=b"y" * 5000,
        headers={"content-type": "application/pdf"},
        url="https://vara.ae/stream.pdf",
    )
    session = _FakeSession({"https://vara.ae/stream.pdf": resp})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    out = fetch_document("https://vara.ae/stream.pdf", max_bytes=1000)
    assert out["status"] == "skipped"
    assert "too large" in out["error"].lower()
