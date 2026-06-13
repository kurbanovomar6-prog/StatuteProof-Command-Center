"""
PDF extraction providers.

Priority:
  1. PyMuPDF (fitz) — best quality, handles complex layouts
  2. pdfplumber     — best for tables and structured layouts
  3. pypdf          — text-only fallback

All return uniform ProviderResult dicts.
"""

from __future__ import annotations

import time


def _provider_result(
    *,
    provider_name: str,
    success: bool,
    dependency_available: bool,
    content: str = "",
    page_count: int = 0,
    confidence: str = "unknown",
    warnings: list[str] | None = None,
    error: str = "",
    elapsed_ms: int = 0,
) -> dict:
    return {
        "provider_name": provider_name,
        "success": success,
        "dependency_available": dependency_available,
        "content": content,
        "page_count": page_count,
        "confidence": confidence,
        "warnings": warnings or [],
        "error": error,
        "elapsed_ms": elapsed_ms,
    }


def pymupdf_extract(pdf_bytes: bytes) -> dict:
    """Extract text from PDF bytes using PyMuPDF (fitz)."""
    t0 = time.monotonic()
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        parts = []
        for page in doc:
            parts.append(page.get_text())
        doc.close()
        text = "\n".join(parts)
        ms = int((time.monotonic() - t0) * 1000)
        return _provider_result(
            provider_name="pymupdf",
            success=bool(text.strip()),
            dependency_available=True,
            content=text,
            page_count=len(parts),
            confidence="high",
            elapsed_ms=ms,
        )
    except ImportError:
        return _provider_result(
            provider_name="pymupdf",
            success=False,
            dependency_available=False,
            error="PyMuPDF not installed. Install: pip install PyMuPDF",
            elapsed_ms=int((time.monotonic() - t0) * 1000),
        )
    except Exception as exc:
        return _provider_result(
            provider_name="pymupdf",
            success=False,
            dependency_available=True,
            error=str(exc),
            elapsed_ms=int((time.monotonic() - t0) * 1000),
        )


def pdfplumber_extract(pdf_bytes: bytes) -> dict:
    """Extract text from PDF bytes using pdfplumber (good for tables)."""
    t0 = time.monotonic()
    try:
        import io
        import pdfplumber
        parts = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                text = page.extract_text() or ""
                if text:
                    parts.append(text)
        text = "\n".join(parts)
        ms = int((time.monotonic() - t0) * 1000)
        return _provider_result(
            provider_name="pdfplumber",
            success=bool(text.strip()),
            dependency_available=True,
            content=text,
            page_count=page_count,
            confidence="high",
            elapsed_ms=ms,
        )
    except ImportError:
        return _provider_result(
            provider_name="pdfplumber",
            success=False,
            dependency_available=False,
            error="pdfplumber not installed. Install: pip install pdfplumber",
            elapsed_ms=int((time.monotonic() - t0) * 1000),
        )
    except Exception as exc:
        return _provider_result(
            provider_name="pdfplumber",
            success=False,
            dependency_available=True,
            error=str(exc),
            elapsed_ms=int((time.monotonic() - t0) * 1000),
        )


def pypdf_extract(pdf_bytes: bytes) -> dict:
    """Extract text from PDF bytes using pypdf (text-only fallback)."""
    t0 = time.monotonic()
    try:
        import io
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        parts = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text:
                parts.append(text)
        text = "\n".join(parts)
        ms = int((time.monotonic() - t0) * 1000)
        return _provider_result(
            provider_name="pypdf",
            success=bool(text.strip()),
            dependency_available=True,
            content=text,
            page_count=len(reader.pages),
            confidence="medium",
            elapsed_ms=ms,
        )
    except ImportError:
        return _provider_result(
            provider_name="pypdf",
            success=False,
            dependency_available=False,
            error="pypdf not installed. Install: pip install pypdf",
            elapsed_ms=int((time.monotonic() - t0) * 1000),
        )
    except Exception as exc:
        return _provider_result(
            provider_name="pypdf",
            success=False,
            dependency_available=True,
            error=str(exc),
            elapsed_ms=int((time.monotonic() - t0) * 1000),
        )


def best_pdf_extract(pdf_bytes: bytes) -> dict:
    """Run PDF extraction cascade and return best result."""
    for fn in [pymupdf_extract, pdfplumber_extract, pypdf_extract]:
        result = fn(pdf_bytes)
        if result["success"]:
            return result
    return _provider_result(
        provider_name="none",
        success=False,
        dependency_available=True,
        error="All PDF extraction providers failed.",
    )
