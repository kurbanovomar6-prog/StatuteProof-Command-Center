"""
RegRadar — document extraction engine.

Discovers PDF/DOC/DOCX links on regulatory pages, safely downloads and
extracts text.  All functions fail gracefully — no crash, no mandatory
dependencies beyond requests + BeautifulSoup (already required by the
project).

PDF extraction requires:  pip install pypdf
DOCX extraction requires: pip install python-docx   (listed, not extracted yet)

Public API
----------
find_document_links(html, base_url)                          → dict
fetch_document(url, timeout, max_bytes)                      → dict
extract_pdf_text(file_bytes)                                 → dict
extract_documents_from_page(html, base_url, max_docs=10)     → dict
"""

from __future__ import annotations

import logging
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from app.adapters.base import _FETCH_CHUNK_BYTES, _guarded_get
from app.config import REQUESTS_UA

logger = logging.getLogger(__name__)

# ── Quality thresholds ────────────────────────────────────────────────────────

_GOOD_CHARS = 1_000
_LOW_CHARS  =   100

# ── Document extension sets ───────────────────────────────────────────────────

_PDF_EXTS  = frozenset({".pdf"})
_DOC_EXTS  = frozenset({".doc"})
_DOCX_EXTS = frozenset({".docx"})
_XLSX_EXTS = frozenset({".xlsx", ".xls"})
_ALL_EXTS  = _PDF_EXTS | _DOC_EXTS | _DOCX_EXTS | _XLSX_EXTS

_MAX_BYTES_DEFAULT = 10_000_000   # 10 MB

# Anchor-text pattern that suggests a PDF download even without a .pdf extension
_PDF_ANCHOR_RE = re.compile(
    r'\b(download|pdf|circular|notice|guidance|regulation|decision|resolution)\b',
    re.I,
)


def _quality(chars: int) -> str:
    if chars >= _GOOD_CHARS:
        return "good"
    if chars >= _LOW_CHARS:
        return "low_content"
    return "failed"


def _doc_ext(url: str) -> str:
    path = urlparse(url).path.lower()
    for ext in _ALL_EXTS:
        if path.endswith(ext):
            return ext
    return ""


def _normalise_text(text: str) -> str:
    """Normalise whitespace and collapse repeated blank lines."""
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [ln.rstrip() for ln in text.split("\n")]
    return "\n".join(lines).strip()


# ── Priority scoring for PDF links ───────────────────────────────────────────

def _priority_score(link_info: dict) -> int:
    """Score PDF links by anchor text quality for regulatory content."""
    anchor = link_info.get("anchor_text", "").lower()
    score = 0
    # Date pattern in anchor text
    if re.search(r'\d{4}|\d{1,2}[\/\-]\d{1,2}', anchor):
        score += 2
    # Regulatory keywords
    if any(kw in anchor for kw in ["circular", "notice", "regulation", "guidance", "decision", "resolution", "law"]):
        score += 1
    # Generic/noise anchors
    if any(kw in anchor for kw in ["download", "click here", "here", "pdf", "attachment"]):
        score -= 1
    return score


# ── Link discovery ─────────────────────────────────────────────────────────────

def find_document_links(html: str, base_url: str) -> dict:
    """
    Parse HTML and return categorised document link lists.

    Returns
    -------
    {
      "pdf_links":          [...],   # up to 20
      "doc_links":          [...],   # up to 20
      "docx_links":         [...],   # up to 20
      "xlsx_links":         [...],   # up to 20
      "all_document_links": [...]    # union, up to 60
    }
    All entries are deduplicated absolute http/https URLs.
    """
    empty = {
        "pdf_links": [], "doc_links": [], "docx_links": [],
        "xlsx_links": [], "all_document_links": [],
    }
    if not html:
        return empty

    soup = BeautifulSoup(html, "html.parser")
    seen:       set[str]   = set()
    pdf_items:  list[dict] = []   # {"url": ..., "anchor_text": ...}
    docs:       list[str]  = []
    docxs:      list[str]  = []
    xlsxs:      list[str]  = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
            continue
        try:
            full = urljoin(base_url, href)
            p    = urlparse(full)
            if p.scheme not in ("http", "https") or not p.netloc:
                continue
            if full in seen:
                continue
            ext = _doc_ext(full)
            if not ext:
                continue
            seen.add(full)
            if ext in _PDF_EXTS:
                pdf_items.append({"url": full, "anchor_text": tag.get_text(strip=True)})
            elif ext in _DOC_EXTS:
                docs.append(full)
            elif ext in _DOCX_EXTS:
                docxs.append(full)
            elif ext in _XLSX_EXTS:
                xlsxs.append(full)
        except Exception:
            continue

    # Second pass: collect extensionless links whose anchor text looks like a PDF
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
            continue
        try:
            resolved = urljoin(base_url, href)
            p = urlparse(resolved)
            if p.scheme not in ("http", "https") or not p.netloc:
                continue
            if resolved in seen:
                continue
            # Skip links that already have a known document extension
            if _doc_ext(resolved):
                continue
            anchor_text = a_tag.get_text(strip=True)
            if _PDF_ANCHOR_RE.search(anchor_text):
                seen.add(resolved)
                pdf_items.append({
                    "url":          resolved,
                    "anchor_text":  anchor_text,
                    "needs_ct_check": True,
                })
        except Exception:
            continue

    # Sort PDFs by regulatory signal quality before capping at 20
    pdf_items.sort(key=_priority_score, reverse=True)
    pdfs = [item["url"] for item in pdf_items]

    all_docs = pdfs + docs + docxs + xlsxs
    return {
        "pdf_links":          pdfs[:20],
        "doc_links":          docs[:20],
        "docx_links":         docxs[:20],
        "xlsx_links":         xlsxs[:20],
        "all_document_links": all_docs[:60],
    }


# ── Safe document fetch ───────────────────────────────────────────────────────

def fetch_document(
    url:       str,
    timeout:   int = 20,
    max_bytes: int = _MAX_BYTES_DEFAULT,
) -> dict:
    """
    Download a document URL safely with size limit and streaming.

    Returns
    -------
    {
      "url":          url,
      "status":       "ok" | "failed" | "skipped",
      "http_status":  int | None,
      "content_type": str,
      "bytes":        int,
      "data":         bytes,
      "error":        str
    }
    """
    result: dict = {
        "url":          url,
        "status":       "failed",
        "http_status":  None,
        "content_type": "",
        "bytes":        0,
        "data":         b"",
        "error":        "",
    }

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        result["status"] = "skipped"
        result["error"]  = f"Unsupported scheme: {parsed.scheme!r}"
        return result

    # SSRF-guarded fetch: every redirect hop is resolved and vetted BEFORE
    # connecting, and dialled via a pinned IP (see app/adapters/base._guarded_get).
    # A document link parsed out of an untrusted regulator page that 30x-redirects
    # to cloud metadata / loopback / RFC1918 is rejected here instead of being
    # transparently followed by requests(allow_redirects=True).
    resp = _guarded_get(
        url,
        headers={
            "User-Agent":      REQUESTS_UA,
            "Accept":          "application/pdf,application/octet-stream,*/*",
            # English-first with wildcard (mirrors the Tier-1 scraper headers):
            # this path serves UAE/GCC regulator document hosts, and a
            # ru-RU-first fingerprint was a bot-wall trigger / wrong content
            # negotiation there (audit 2026-07-20). The wildcard keeps
            # non-English document hosts serving a body.
            "Accept-Language": "en-US,en;q=0.9,*;q=0.5",
        },
        timeout=timeout,
        verify=True,
        label="document_extractor",
    )
    if resp is None:
        # Guard blocked the target (non-public / disallowed scheme), the host
        # did not resolve, a redirect had no Location or exceeded the cap, or
        # the transport failed. _guarded_get has already logged the reason.
        result["error"] = "fetch blocked or failed (SSRF guard / transport)"
        return result

    try:
        with resp:
            result["http_status"]  = resp.status_code
            result["content_type"] = resp.headers.get("content-type", "").split(";")[0].strip()

            if not resp.ok:
                result["error"] = f"HTTP {resp.status_code}"
                return result

            # Content-Length guard (skip before streaming)
            cl = resp.headers.get("content-length")
            if cl:
                try:
                    if int(cl) > max_bytes:
                        result["status"] = "skipped"
                        result["error"]  = (
                            f"File too large: Content-Length {int(cl):,} > "
                            f"limit {max_bytes:,} bytes"
                        )
                        return result
                except ValueError:
                    pass

            # Stream with running size cap
            chunks: list[bytes] = []
            total = 0
            for chunk in resp.iter_content(chunk_size=_FETCH_CHUNK_BYTES):
                if chunk:
                    total += len(chunk)
                    if total > max_bytes:
                        result["status"] = "skipped"
                        result["error"]  = (
                            f"File too large: stopped at {total:,} bytes "
                            f"(limit {max_bytes:,})"
                        )
                        return result
                    chunks.append(chunk)

            result["data"]   = b"".join(chunks)
            result["bytes"]  = len(result["data"])
            result["status"] = "ok"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    return result


# ── PDF text extraction ───────────────────────────────────────────────────────

def extract_pdf_text(file_bytes: bytes) -> dict:
    """
    Extract text from PDF bytes.  Tries pypdf first, pdfplumber as fallback.

    Returns
    -------
    {
      "text":    str,
      "chars":   int,
      "quality": "good" | "low_content" | "failed",
      "method":  "pypdf" | "pdfplumber" | "none",
      "error":   str
    }
    Never raises.
    """
    result: dict = {
        "text":    "",
        "chars":   0,
        "quality": "failed",
        "method":  "none",
        "error":   "",
    }

    if not file_bytes:
        result["error"] = "empty input"
        return result

    # ── pypdf ───────────────────────────────────────────────────────────────
    try:
        import pypdf       # type: ignore[import-untyped]
        import io as _io

        reader = pypdf.PdfReader(_io.BytesIO(file_bytes))
        parts: list[str] = []
        for page in reader.pages:
            t = page.extract_text()
            if t and t.strip():
                parts.append(t.strip())
        text = _normalise_text("\n\n".join(parts))
        if text and len(text) >= _LOW_CHARS:
            result.update(
                text=text, chars=len(text),
                quality=_quality(len(text)), method="pypdf",
            )
            return result
        # pypdf gave something too short — still record method, try fallback
        if text:
            result.update(
                text=text, chars=len(text),
                quality=_quality(len(text)), method="pypdf",
            )
    except ImportError:
        logger.debug("document_extractor: pypdf not installed")
    except Exception as exc:
        result["error"] = f"pypdf: {str(exc)[:120]}"
        logger.debug("document_extractor: pypdf failed: %s", exc)

    # ── pdfplumber fallback ─────────────────────────────────────────────────
    try:
        import pdfplumber  # type: ignore[import-untyped]
        import io as _io

        with pdfplumber.open(_io.BytesIO(file_bytes)) as pdf:
            parts = []
            for page in pdf.pages:
                t = page.extract_text()
                if t and t.strip():
                    parts.append(t.strip())
        text = _normalise_text("\n\n".join(parts))
        if text and len(text) >= _LOW_CHARS:
            result.update(
                text=text, chars=len(text),
                quality=_quality(len(text)), method="pdfplumber", error="",
            )
            return result
        # pdfplumber gave something too short — record method, fall through to OCR
        if text:
            result.update(
                text=text, chars=len(text),
                quality=_quality(len(text)), method="pdfplumber", error="",
            )
    except ImportError:
        logger.debug("document_extractor: pdfplumber not installed")
    except Exception as exc:
        prev = result["error"]
        result["error"] = (prev + " | " if prev else "") + f"pdfplumber: {str(exc)[:120]}"
        logger.debug("document_extractor: pdfplumber failed: %s", exc)

    # ── OCR fallback for scanned PDFs ──────────────────────────────────────
    if result["chars"] < _LOW_CHARS:
        logger.debug("document_extractor: attempting OCR fallback (chars so far: %d)", result["chars"])
        try:
            import pytesseract        # type: ignore[import-untyped]
            from PIL import Image     # type: ignore[import-untyped]
            import fitz               # type: ignore[import-untyped]  # PyMuPDF

            doc_pdf = fitz.open(stream=file_bytes, filetype="pdf")
            ocr_texts: list[str] = []
            for page_num in range(min(doc_pdf.page_count, 10)):  # max 10 pages
                page = doc_pdf[page_num]
                pix  = page.get_pixmap(dpi=150)
                img  = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                page_text = pytesseract.image_to_string(img, lang="eng+ara")
                if page_text.strip():
                    ocr_texts.append(page_text)
            doc_pdf.close()
            if ocr_texts:
                text = _normalise_text("\n\n".join(ocr_texts))
                result.update(
                    text=text,
                    chars=len(text),
                    quality=_quality(len(text)),
                    method="ocr",
                    error="",
                )
                logger.info("document_extractor: OCR produced %d chars", len(text))
        except ImportError:
            pass  # OCR dependencies not installed — skip silently
        except Exception as ocr_err:
            logger.warning("document_extractor: OCR fallback failed: %s", ocr_err)

    # ── Both unavailable/failed ─────────────────────────────────────────────
    if result["method"] == "none" and not result["error"]:
        result["error"] = "no PDF library available — install pypdf"

    return result


# ── Page-level extraction ─────────────────────────────────────────────────────

def extract_documents_from_page(
    html:     str,
    base_url: str,
    max_docs: int = 10,
) -> dict:
    """
    Discover document links in HTML and extract text from up to max_docs PDFs.

    DOC/DOCX/XLSX links are discovered and counted but not yet extracted.

    Returns
    -------
    {
      "documents_found":     int,    # total doc links on page
      "documents_processed": int,    # PDFs attempted
      "pdf_processed":       int,    # PDFs attempted
      "doc_links":           int,    # .doc count
      "docx_links":          int,    # .docx count
      "combined_text":       str,
      "combined_chars":      int,
      "quality":             str,
      "items":               list[dict]
    }
    Never raises.
    """
    links = find_document_links(html, base_url)
    pdfs  = links["pdf_links"]
    docs  = links["doc_links"]
    docxs = links["docx_links"]

    items:       list[dict] = []
    text_blocks: list[str]  = []

    for doc_index, pdf_url in enumerate(pdfs[:max_docs], start=1):
        item: dict = {
            "url":     pdf_url,
            "type":    "pdf",
            "chars":   0,
            "quality": "failed",
            "method":  "none",
            "error":   "",
        }

        fetch = fetch_document(pdf_url)
        if fetch["status"] == "ok" and fetch["data"]:
            extr = extract_pdf_text(fetch["data"])
            item.update(
                chars=extr["chars"],
                quality=extr["quality"],
                method=extr["method"],
                error=extr["error"],
            )
            if extr["text"]:
                text_blocks.append(
                    f"[Document {doc_index}]\n{extr['text']}"
                )
        else:
            item["error"] = fetch.get("error", "download failed")
            logger.debug(
                "document_extractor: fetch failed for %s: %s",
                pdf_url, item["error"],
            )

        items.append(item)

    combined       = "\n\n".join(text_blocks)
    combined_chars = len(combined)

    return {
        "documents_found":     len(links["all_document_links"]),
        "documents_processed": len(items),
        "pdf_links_count":     len(pdfs),
        "pdf_processed":       len(items),
        "doc_links":           len(docs),
        "docx_links":          len(docxs),
        "combined_text":       combined,
        "combined_chars":      combined_chars,
        "quality":             _quality(combined_chars),
        "items":               items,
    }
