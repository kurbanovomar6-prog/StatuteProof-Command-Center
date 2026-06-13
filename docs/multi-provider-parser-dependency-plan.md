# Multi-Provider Parser Dependency Plan

**Date:** 2026-06-13
**Scope:** StatuteProof RegRadar — `product/regradar/app/providers/`

---

## Overview

The Universal Source Intake Engine uses a cascading provider architecture for both HTML and PDF extraction. Each provider is wrapped in a graceful-degradation module. The cascade always falls back to a working provider rather than raising an unhandled exception.

---

## HTML Extraction Providers

File: `app/providers/html_extraction.py`

| Priority | Provider | Package | Status | Confidence |
|----------|----------|---------|--------|------------|
| 1 | selectolax (CSS selector) | `selectolax` | Optional — not installed | medium |
| 2 | trafilatura | `trafilatura` | **Installed** | high |
| 3 | readability-lxml | `readability-lxml` | **Installed** | medium |
| 4 | BeautifulSoup4 | `beautifulsoup4` | **Installed (required)** | low |

**Cascade rule:** `best_html_extract()` returns the result with the longest content. If `content_selector` is provided, selectolax runs first. All others run in priority order and the best (longest) result wins.

**Result schema** (all providers return):
```python
{
    "provider_name": str,
    "success": bool,
    "dependency_available": bool,
    "content": str,
    "confidence": "high" | "medium" | "low" | "unknown",
    "warnings": list[str],
    "error": str,
    "elapsed_ms": int,
    "metadata": dict,
}
```

**Selectolax install note:** `pip install selectolax` — enables per-source CSS selector extraction without Playwright. Useful for sites with stable structural selectors (e.g., `#main-content`, `article.legislation`).

---

## PDF Extraction Providers

File: `app/providers/pdf_extraction.py`

| Priority | Provider | Package | Status | Confidence |
|----------|----------|---------|--------|------------|
| 1 | PyMuPDF | `PyMuPDF` (`fitz`) | **Installed** | high |
| 2 | pdfplumber | `pdfplumber` | **Installed** | high (tables) |
| 3 | pypdf | `pypdf` | **Installed** | medium |

**Cascade rule:** `best_pdf_extract()` tries each provider in order and returns the first successful result. If all fail, returns `provider_name="none"`, `success=False`.

**Result schema:**
```python
{
    "provider_name": str,
    "success": bool,
    "dependency_available": bool,
    "content": str,
    "page_count": int,
    "confidence": "high" | "medium" | "low" | "unknown",
    "warnings": list[str],
    "error": str,
    "elapsed_ms": int,
}
```

**Notes:**
- PyMuPDF handles complex multi-column layouts and footnotes well.
- pdfplumber excels at table extraction (regulatory tables, schedules).
- pypdf is text-only with no layout awareness — last resort.

---

## Optional Analysis Tools

File: `app/providers/optional_tools.py`

| Tool | Package | Status | Fallback |
|------|---------|--------|----------|
| `structured_diff` | `deepdiff` | Optional — **not installed** | Shallow key comparison (added/removed/changed dicts) |
| `extract_date_from_html` | `htmldate` | Optional — **not installed** | Returns `success=False`, empty date |
| `canonicalize_url` | `courlan` | Optional — **not installed** | urllib.parse fallback (scheme + netloc validation) |

**Install to enable enhanced features:**
```bash
pip install deepdiff htmldate courlan
```

**deepdiff** is the most useful optional dep — enables structured JSON diff for evidence comparison between monitoring runs. The shallow fallback is sufficient for basic change detection but misses nested key changes.

---

## Requirements.txt Status

```
# Installed and required
beautifulsoup4   trafilatura   readability-lxml   pypdf

# Installed and available (added 2026-06-13)
PyMuPDF          pdfplumber

# Optional — not installed
selectolax       deepdiff       htmldate       courlan
```

`htmldate` and `courlan` entries are commented out in `requirements.txt` as they are not yet verified for compatibility with Python 3.14. Install manually if needed.

---

## Integration Points

The providers are **not yet wired into `source_intake.py`** directly. The intake engine currently uses `app.extractors.extract_best_text()` for HTML extraction. The providers package is:

1. Tested independently (48 tests, all passing)
2. Available for import by any future intake or monitoring code
3. Used by the `/api/custom-sources/test` endpoint indirectly via `extract_best_text`

**Next integration step:** Wire `best_html_extract()` into `extract_best_text()` in `app/extractors.py` and expose `provider_name` in the extraction result for better observability.

---

## Graceful Degradation Guarantee

Every provider function:
- Wraps `import` in `try/except ImportError` — missing dep never crashes
- Wraps execution in `try/except Exception` — runtime errors return `success=False` with error string
- Returns `dependency_available: False` when the dep is missing
- Returns a timing `elapsed_ms` on every path including failure paths

This means the intake engine degrades cleanly: fewer providers installed → lower confidence score → but no exceptions raised, no crashes.
