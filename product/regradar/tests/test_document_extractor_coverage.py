"""
Behavioral coverage for app.document_extractor beyond the SSRF-guard path
(see test_document_extractor_ssrf.py, which already covers the fetch_document
redirect/guard branches).

This file exercises the pure logic that is otherwise untested:

  * find_document_links   — link discovery, categorisation, dedup, scheme
                            filtering, extensionless-anchor detection, and
                            regulatory-priority sorting.
  * extract_pdf_text      — empty input, pypdf success (good / low_content),
                            pypdf failure → pdfplumber fallback, whitespace
                            normalisation.  PDF libraries are injected as fakes
                            via sys.modules so no real parsing runs.
  * extract_documents_from_page — page-level aggregation with fetch_document
                            and extract_pdf_text mocked (no network).
  * fetch_document        — the two branches the SSRF file does not reach:
                            a non-integer Content-Length (ValueError swallowed)
                            and an exception raised mid-stream.
  * helper functions      — _quality, _doc_ext, _normalise_text, _priority_score.

All network / subprocess / PDF-parsing I/O is mocked. Nothing hits a live host.
"""

from __future__ import annotations

import socket
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import app.adapters.base as base
import app.document_extractor as de
from app.document_extractor import (
    _doc_ext,
    _normalise_text,
    _priority_score,
    _quality,
    extract_documents_from_page,
    extract_pdf_text,
    fetch_document,
    find_document_links,
)


# ── helper-function behavior ──────────────────────────────────────────────────

def test_quality_thresholds():
    assert _quality(0) == "failed"
    assert _quality(99) == "failed"
    assert _quality(100) == "low_content"
    assert _quality(999) == "low_content"
    assert _quality(1000) == "good"
    assert _quality(50_000) == "good"


def test_doc_ext_matches_known_extensions_case_insensitively():
    assert _doc_ext("https://x.ae/Circular.PDF") == ".pdf"
    assert _doc_ext("https://x.ae/form.doc") == ".doc"
    assert _doc_ext("https://x.ae/rule.docx") == ".docx"
    assert _doc_ext("https://x.ae/table.xlsx") == ".xlsx"
    assert _doc_ext("https://x.ae/legacy.xls") == ".xls"
    assert _doc_ext("https://x.ae/page.html") == ""
    assert _doc_ext("https://x.ae/no-extension") == ""


def test_normalise_text_collapses_newlines_and_crlf():
    raw = "line one  \r\n\r\n\r\n\r\nline two   \r\n"
    out = _normalise_text(raw)
    assert out == "line one\n\nline two"
    assert "\r" not in out
    assert "\n\n\n" not in out


def test_normalise_text_empty_input():
    assert _normalise_text("") == ""
    assert _normalise_text(None) == ""


def test_priority_score_rewards_regulatory_signal_and_penalises_noise():
    dated_reg = {"anchor_text": "Circular 2024 on capital"}
    generic = {"anchor_text": "Download here"}
    # date (+2) + regulatory keyword (+1) = 3
    assert _priority_score(dated_reg) == 3
    # "download" + "here" both noise but scored once each path: -1
    assert _priority_score(generic) == -1
    assert _priority_score(dated_reg) > _priority_score(generic)


# ── find_document_links ───────────────────────────────────────────────────────

def test_find_document_links_empty_html_returns_empty_shape():
    out = find_document_links("", "https://vara.ae/")
    assert out == {
        "pdf_links": [], "doc_links": [], "docx_links": [],
        "xlsx_links": [], "all_document_links": [],
    }


def test_find_document_links_categorises_and_absolutises():
    html = """
      <a href="/docs/circular.pdf">Circular</a>
      <a href="form.doc">Form</a>
      <a href="https://cdn.vara.ae/rule.docx">Rule</a>
      <a href="data/report.xlsx">Report</a>
      <a href="/page.html">Not a doc</a>
    """
    out = find_document_links(html, "https://vara.ae/regs/")
    assert out["pdf_links"] == ["https://vara.ae/docs/circular.pdf"]
    assert out["doc_links"] == ["https://vara.ae/regs/form.doc"]
    assert out["docx_links"] == ["https://cdn.vara.ae/rule.docx"]
    assert out["xlsx_links"] == ["https://vara.ae/regs/data/report.xlsx"]
    # union contains all four, .html excluded
    assert len(out["all_document_links"]) == 4
    assert all(u.startswith("https://") for u in out["all_document_links"])


def test_find_document_links_skips_non_navigational_hrefs():
    html = """
      <a href="#top">anchor</a>
      <a href="javascript:void(0)">js</a>
      <a href="mailto:a@b.ae">mail</a>
      <a href="tel:+9711234">tel</a>
      <a href="data:application/pdf;base64,AAA">data</a>
      <a href="ftp://host/file.pdf">ftp pdf</a>
    """
    out = find_document_links(html, "https://vara.ae/")
    assert out["all_document_links"] == []


def test_find_document_links_deduplicates_repeated_urls():
    html = (
        '<a href="/a.pdf">one</a>'
        '<a href="/a.pdf">dupe</a>'
        '<a href="https://vara.ae/a.pdf">absolute dupe</a>'
    )
    out = find_document_links(html, "https://vara.ae/")
    assert out["pdf_links"] == ["https://vara.ae/a.pdf"]


def test_find_document_links_picks_up_extensionless_pdf_anchor():
    html = '<a href="/download/1234">Download Circular Notice</a>'
    out = find_document_links(html, "https://vara.ae/")
    assert out["pdf_links"] == ["https://vara.ae/download/1234"]


def test_find_document_links_ignores_extensionless_non_document_anchor():
    html = '<a href="/about-us">About the authority</a>'
    out = find_document_links(html, "https://vara.ae/")
    assert out["pdf_links"] == []


def test_find_document_links_sorts_pdfs_by_regulatory_priority():
    html = (
        '<a href="/noise.pdf">click here download</a>'
        '<a href="/reg.pdf">Circular 2024 Decision</a>'
    )
    out = find_document_links(html, "https://vara.ae/")
    # higher regulatory signal must come first
    assert out["pdf_links"][0] == "https://vara.ae/reg.pdf"
    assert out["pdf_links"][1] == "https://vara.ae/noise.pdf"


def test_find_document_links_caps_pdf_list_at_twenty():
    links = "".join(f'<a href="/doc{i}.pdf">Regulation {i}</a>' for i in range(30))
    out = find_document_links(links, "https://vara.ae/")
    assert len(out["pdf_links"]) == 20
    assert len(out["all_document_links"]) == 30  # union cap is 60


# ── extract_pdf_text (PDF libs injected as fakes) ─────────────────────────────

def _install_fake_pypdf(monkeypatch, pages_text=None, raises=None):
    mod = types.ModuleType("pypdf")

    class _Page:
        def __init__(self, t):
            self._t = t

        def extract_text(self):
            return self._t

    class _Reader:
        def __init__(self, stream):
            if raises is not None:
                raise raises
            self.pages = [_Page(t) for t in (pages_text or [])]

    mod.PdfReader = _Reader
    monkeypatch.setitem(sys.modules, "pypdf", mod)


def _install_fake_pdfplumber(monkeypatch, pages_text):
    mod = types.ModuleType("pdfplumber")

    class _Page:
        def __init__(self, t):
            self._t = t

        def extract_text(self):
            return self._t

    class _PDF:
        def __init__(self, pages):
            self.pages = [_Page(t) for t in pages]

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    mod.open = lambda stream: _PDF(pages_text)
    monkeypatch.setitem(sys.modules, "pdfplumber", mod)


def test_extract_pdf_text_empty_input():
    out = extract_pdf_text(b"")
    assert out["error"] == "empty input"
    assert out["quality"] == "failed"
    assert out["method"] == "none"
    assert out["chars"] == 0


def test_extract_pdf_text_pypdf_good_quality(monkeypatch):
    long_page = "Regulatory text. " * 100  # > 1000 chars
    _install_fake_pypdf(monkeypatch, pages_text=[long_page])
    out = extract_pdf_text(b"%PDF-fake")
    assert out["method"] == "pypdf"
    assert out["quality"] == "good"
    assert out["chars"] >= 1000
    assert out["error"] == ""
    assert "Regulatory text." in out["text"]


def test_extract_pdf_text_pypdf_low_content(monkeypatch):
    short = "Short circular notice about capital requirements. " * 6  # ~300 chars
    assert 100 <= len(short) < 1000
    _install_fake_pypdf(monkeypatch, pages_text=[short])
    out = extract_pdf_text(b"%PDF-fake")
    assert out["method"] == "pypdf"
    assert out["quality"] == "low_content"
    assert out["chars"] == len(_normalise_text(short))


def test_extract_pdf_text_falls_back_to_pdfplumber_when_pypdf_raises(monkeypatch):
    _install_fake_pypdf(monkeypatch, raises=ValueError("corrupt xref"))
    good = "Fallback extracted body. " * 80  # > 1000 chars
    _install_fake_pdfplumber(monkeypatch, pages_text=[good])
    out = extract_pdf_text(b"%PDF-fake")
    assert out["method"] == "pdfplumber"
    assert out["quality"] == "good"
    # pdfplumber success clears the earlier pypdf error
    assert out["error"] == ""
    assert "Fallback extracted body." in out["text"]


def test_extract_pdf_text_normalises_multi_page_whitespace(monkeypatch):
    _install_fake_pypdf(
        monkeypatch,
        pages_text=["Page one line.  \r\n\r\n\r\n", "Page two body. " * 80],
    )
    out = extract_pdf_text(b"%PDF-fake")
    assert "\r" not in out["text"]
    assert "\n\n\n" not in out["text"]
    assert out["method"] == "pypdf"


# ── extract_documents_from_page (fetch + extract mocked) ──────────────────────

def test_extract_documents_from_page_aggregates_successful_pdf(monkeypatch):
    html = '<a href="/reg.pdf">Circular 2024</a><a href="/form.doc">Form</a>'

    def _fake_fetch(url, *a, **k):
        return {"status": "ok", "data": b"%PDF-bytes", "error": ""}

    def _fake_extract(data):
        return {
            "text": "Extracted regulatory body text.",
            "chars": 31,
            "quality": "low_content",
            "method": "pypdf",
            "error": "",
        }

    monkeypatch.setattr(de, "fetch_document", _fake_fetch)
    monkeypatch.setattr(de, "extract_pdf_text", _fake_extract)

    out = extract_documents_from_page(html, "https://vara.ae/")
    assert out["documents_found"] == 2       # 1 pdf + 1 doc discovered
    assert out["pdf_links_count"] == 1
    assert out["pdf_processed"] == 1
    assert out["doc_links"] == 1
    assert out["docx_links"] == 0
    assert "[Document 1]" in out["combined_text"]
    assert "Extracted regulatory body text." in out["combined_text"]
    assert out["combined_chars"] == len(out["combined_text"])
    item = out["items"][0]
    assert item["type"] == "pdf"
    assert item["method"] == "pypdf"
    assert item["error"] == ""


def test_extract_documents_from_page_records_fetch_failure(monkeypatch):
    html = '<a href="/reg.pdf">Circular 2024</a>'

    def _fake_fetch(url, *a, **k):
        return {"status": "failed", "data": b"", "error": "HTTP 503"}

    # extract must never be called when fetch fails
    def _boom(data):  # pragma: no cover - guarded against
        raise AssertionError("extract_pdf_text must not run on failed fetch")

    monkeypatch.setattr(de, "fetch_document", _fake_fetch)
    monkeypatch.setattr(de, "extract_pdf_text", _boom)

    out = extract_documents_from_page(html, "https://vara.ae/")
    assert out["pdf_processed"] == 1
    assert out["combined_text"] == ""
    assert out["combined_chars"] == 0
    assert out["quality"] == "failed"
    assert out["items"][0]["error"] == "HTTP 503"
    assert out["items"][0]["chars"] == 0


def test_extract_documents_from_page_respects_max_docs(monkeypatch):
    html = "".join(f'<a href="/d{i}.pdf">Regulation {i}</a>' for i in range(5))

    calls = []

    def _fake_fetch(url, *a, **k):
        calls.append(url)
        return {"status": "ok", "data": b"%PDF", "error": ""}

    def _fake_extract(data):
        return {"text": "", "chars": 0, "quality": "failed", "method": "none", "error": ""}

    monkeypatch.setattr(de, "fetch_document", _fake_fetch)
    monkeypatch.setattr(de, "extract_pdf_text", _fake_extract)

    out = extract_documents_from_page(html, "https://vara.ae/", max_docs=2)
    assert len(calls) == 2
    assert out["pdf_processed"] == 2
    assert out["pdf_links_count"] == 5  # all discovered, only 2 processed


def test_extract_documents_from_page_empty_page():
    out = extract_documents_from_page("", "https://vara.ae/")
    assert out["documents_found"] == 0
    assert out["pdf_processed"] == 0
    assert out["items"] == []
    assert out["combined_text"] == ""


# ── fetch_document branches not reached by the SSRF suite ─────────────────────

def _fake_getaddrinfo(*addresses):
    def _inner(host, port, *args, **kwargs):
        infos = []
        for ip in addresses:
            family = socket.AF_INET6 if ":" in ip else socket.AF_INET
            infos.append((family, socket.SOCK_STREAM, 6, "", (ip, port)))
        return infos
    return _inner


class _FakeResp:
    def __init__(self, status, *, body=b"", headers=None, url="https://x/", iter_raises=None):
        self.status_code = status
        self.url = url
        self.headers = dict(headers or {})
        self._body = body
        self._iter_raises = iter_raises
        self.closed = False

    @property
    def ok(self):
        return self.status_code < 400

    @property
    def is_redirect(self):
        return self.status_code in (301, 302, 303, 307, 308) and "Location" in self.headers

    def iter_content(self, chunk_size):
        if self._iter_raises is not None:
            raise self._iter_raises
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
        self.requested.append(url)
        return self._script[url]


def test_fetch_document_ignores_non_integer_content_length(monkeypatch):
    """A malformed Content-Length header must be swallowed (ValueError), and the
    download proceeds via the streaming cap instead of crashing."""
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    resp = _FakeResp(
        200,
        body=b"%PDF real body",
        headers={"content-type": "application/pdf", "content-length": "not-a-number"},
        url="https://vara.ae/ok.pdf",
    )
    session = _FakeSession({"https://vara.ae/ok.pdf": resp})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    out = fetch_document("https://vara.ae/ok.pdf")
    assert out["status"] == "ok"
    assert out["data"] == b"%PDF real body"
    assert out["bytes"] == len(b"%PDF real body")


def test_fetch_document_handles_stream_exception(monkeypatch):
    """An exception raised while iterating the body is caught and reported as a
    failure rather than propagating."""
    monkeypatch.setattr(base.socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))
    resp = _FakeResp(
        200,
        headers={"content-type": "application/pdf"},
        url="https://vara.ae/broken.pdf",
        iter_raises=ConnectionResetError("peer reset mid-stream"),
    )
    session = _FakeSession({"https://vara.ae/broken.pdf": resp})
    monkeypatch.setattr(base.requests, "Session", lambda: session)

    out = fetch_document("https://vara.ae/broken.pdf")
    assert out["status"] == "failed"
    assert out["data"] == b""
    assert "ConnectionResetError" in out["error"]
    assert "peer reset mid-stream" in out["error"]
