"""
RegRadar — Optional document text extraction.

extract_pdf_text(file_bytes)  → str   (requires: pip install pypdf)
extract_docx_text(file_bytes) → str   (requires: pip install python-docx)
extract_xlsx_text(file_bytes) → str   (requires: pip install openpyxl)

All functions return empty string when the library is missing or extraction
fails — no crash, no mandatory dependency.  Only in-memory bytes are processed;
no local files are opened and no macros are executed.

Install:
    .venv/bin/python -m pip install pypdf python-docx openpyxl
"""

from __future__ import annotations

import io
import logging

logger = logging.getLogger(__name__)


def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from PDF bytes. Returns '' if pypdf is not installed."""
    if not file_bytes:
        return ""
    try:
        import pypdf  # type: ignore[import-untyped]
    except ImportError:
        logger.debug("document_extractors: pypdf not installed — PDF extraction skipped")
        return ""
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        parts: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                parts.append(text.strip())
        return "\n\n".join(parts)
    except Exception as exc:
        logger.debug("document_extractors: PDF extraction failed: %s", exc)
        return ""


def extract_docx_text(file_bytes: bytes) -> str:
    """Extract text from DOCX bytes. Returns '' if python-docx is not installed."""
    if not file_bytes:
        return ""
    try:
        import docx  # type: ignore[import-untyped]
    except ImportError:
        logger.debug("document_extractors: python-docx not installed — DOCX extraction skipped")
        return ""
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as exc:
        logger.debug("document_extractors: DOCX extraction failed: %s", exc)
        return ""


def extract_xlsx_text(file_bytes: bytes) -> str:
    """Extract text from XLSX/XLS bytes. Returns '' if openpyxl is not installed."""
    if not file_bytes:
        return ""
    try:
        import openpyxl  # type: ignore[import-untyped]
    except ImportError:
        logger.debug("document_extractors: openpyxl not installed — XLSX extraction skipped")
        return ""
    try:
        wb = openpyxl.load_workbook(
            io.BytesIO(file_bytes), read_only=True, data_only=True
        )
        parts: list[str] = []
        for sheet in wb.worksheets:
            for row in sheet.iter_rows(values_only=True):
                cells = [str(c) for c in row if c is not None and str(c).strip()]
                if cells:
                    parts.append("  ".join(cells))
        return "\n".join(parts)
    except Exception as exc:
        logger.debug("document_extractors: XLSX extraction failed: %s", exc)
        return ""
