"""
Regression coverage for the pdfplumber early-return gate in
app.document_extractor.extract_pdf_text.

Bug: the pdfplumber fallback returned on ANY non-empty text (``if text:``),
so a scanned/image PDF that carries a tiny embedded text layer (a page-number
or header stamp below _LOW_CHARS) returned quality='low_content' and never
reached the eng+ara OCR fallback. The pypdf path already gated its early
return on ``len(text) >= _LOW_CHARS``; the pdfplumber path now mirrors it.

These tests inject pypdf / pdfplumber / OCR dependencies as fakes via
sys.modules, so no real parsing, imaging, or tesseract subprocess runs.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import app.document_extractor as de
from app.document_extractor import _LOW_CHARS, extract_pdf_text


# ── fakes ─────────────────────────────────────────────────────────────────────

def _install_pypdf_raises(monkeypatch, exc: Exception):
    """Force the pypdf branch to fail so control falls to pdfplumber."""
    mod = types.ModuleType("pypdf")

    class _Reader:
        def __init__(self, stream):
            raise exc

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


def _install_fake_ocr(monkeypatch, *, ocr_text: str, on_call=None):
    """Inject fake pytesseract / PIL.Image / fitz modules.

    ``on_call`` (if given) runs whenever the OCR entrypoint
    (pytesseract.image_to_string) is invoked — used to record that OCR was
    reached, or to fail a test that must never reach OCR.
    """
    # pytesseract
    pt = types.ModuleType("pytesseract")

    def _image_to_string(img, lang=None):
        if on_call is not None:
            on_call(lang)
        return ocr_text

    pt.image_to_string = _image_to_string
    monkeypatch.setitem(sys.modules, "pytesseract", pt)

    # PIL + PIL.Image
    pil = types.ModuleType("PIL")
    pil_image = types.ModuleType("PIL.Image")
    pil_image.frombytes = lambda mode, size, data: object()
    pil.Image = pil_image
    monkeypatch.setitem(sys.modules, "PIL", pil)
    monkeypatch.setitem(sys.modules, "PIL.Image", pil_image)

    # fitz (PyMuPDF)
    fitz = types.ModuleType("fitz")

    class _Pix:
        width = 8
        height = 8
        samples = b"\x00" * (8 * 8 * 3)

    class _Page:
        def get_pixmap(self, dpi=None):
            return _Pix()

    class _Doc:
        page_count = 1

        def __getitem__(self, i):
            return _Page()

        def close(self):
            pass

    fitz.open = lambda stream=None, filetype=None: _Doc()
    monkeypatch.setitem(sys.modules, "fitz", fitz)


# ── regression: pdfplumber tiny text now falls through to OCR ─────────────────

def test_pdfplumber_below_low_chars_falls_through_to_ocr(monkeypatch):
    stamp = "Page 1"  # scanned-PDF header stamp, well below _LOW_CHARS
    assert len(stamp) < _LOW_CHARS

    _install_pypdf_raises(monkeypatch, ValueError("no text layer"))
    _install_fake_pdfplumber(monkeypatch, pages_text=[stamp])

    reached: list[str] = []
    ocr_body = "Recovered scanned regulatory body text via OCR. " * 30  # > _LOW_CHARS
    _install_fake_ocr(monkeypatch, ocr_text=ocr_body, on_call=lambda lang: reached.append(lang))

    out = extract_pdf_text(b"%PDF-scanned")

    # OCR entrypoint was reached (the regression: previously it never was)...
    assert reached == ["eng+ara"]
    # ...and its output supersedes the tiny pdfplumber stamp.
    assert out["method"] == "ocr"
    assert out["chars"] >= _LOW_CHARS
    assert "Recovered scanned regulatory body text" in out["text"]
    assert out["error"] == ""


# ── control: rich pdfplumber text still short-circuits before OCR ─────────────

def test_pdfplumber_rich_text_returns_early_without_ocr(monkeypatch):
    rich = "Full extracted regulatory circular body. " * 40  # > 1000 chars
    assert len(rich) >= 1000

    _install_pypdf_raises(monkeypatch, ValueError("no text layer"))
    _install_fake_pdfplumber(monkeypatch, pages_text=[rich])

    def _must_not_run(lang):  # pragma: no cover - guarded against
        raise AssertionError("OCR must not run when pdfplumber returns rich text")

    _install_fake_ocr(monkeypatch, ocr_text="unused", on_call=_must_not_run)

    out = extract_pdf_text(b"%PDF-rich")

    assert out["method"] == "pdfplumber"
    assert out["quality"] == "good"
    assert "Full extracted regulatory circular body." in out["text"]
    assert out["error"] == ""
