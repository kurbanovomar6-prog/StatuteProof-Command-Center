"""
HTML extraction providers.

Wrappers around optional and required HTML extraction libraries.
Each returns a uniform ProviderResult dict.
All gracefully degrade when optional dependency is missing.

Provider priority (orchestrated by source_intake.py):
  1. trafilatura     — required, best semantic extraction
  2. readability     — required fallback
  3. selectolax      — optional CSS selector extraction
  4. bs4             — required last-resort fallback
"""

from __future__ import annotations

import time
from typing import Any


def _provider_result(
    *,
    provider_name: str,
    success: bool,
    dependency_available: bool,
    content: str = "",
    confidence: str = "unknown",
    warnings: list[str] | None = None,
    error: str = "",
    elapsed_ms: int = 0,
    metadata: dict | None = None,
) -> dict:
    return {
        "provider_name": provider_name,
        "success": success,
        "dependency_available": dependency_available,
        "requires_dependency": provider_name,
        "content": content,
        "confidence": confidence,
        "warnings": warnings or [],
        "error": error,
        "elapsed_ms": elapsed_ms,
        "metadata": metadata or {},
    }


def trafilatura_extract(html: str) -> dict:
    t0 = time.monotonic()
    try:
        import trafilatura
        text = trafilatura.extract(html, include_comments=False, include_tables=True) or ""
        ms = int((time.monotonic() - t0) * 1000)
        return _provider_result(
            provider_name="trafilatura",
            success=bool(text.strip()),
            dependency_available=True,
            content=text,
            confidence="high" if len(text) > 500 else "medium",
            elapsed_ms=ms,
        )
    except ImportError:
        return _provider_result(
            provider_name="trafilatura",
            success=False,
            dependency_available=False,
            error="trafilatura not installed. Install: pip install trafilatura",
            elapsed_ms=int((time.monotonic() - t0) * 1000),
        )
    except Exception as exc:
        return _provider_result(
            provider_name="trafilatura",
            success=False,
            dependency_available=True,
            error=str(exc),
            elapsed_ms=int((time.monotonic() - t0) * 1000),
        )


def readability_extract(html: str) -> dict:
    t0 = time.monotonic()
    try:
        from readability import Document
        doc = Document(html)
        # strip residual HTML tags from readability output
        content_html = doc.summary()
        from bs4 import BeautifulSoup
        text = BeautifulSoup(content_html, "html.parser").get_text(separator=" ", strip=True)
        ms = int((time.monotonic() - t0) * 1000)
        return _provider_result(
            provider_name="readability",
            success=bool(text.strip()),
            dependency_available=True,
            content=text,
            confidence="medium" if len(text) > 200 else "low",
            elapsed_ms=ms,
        )
    except ImportError:
        return _provider_result(
            provider_name="readability",
            success=False,
            dependency_available=False,
            error="readability-lxml not installed. Install: pip install readability-lxml",
            elapsed_ms=int((time.monotonic() - t0) * 1000),
        )
    except Exception as exc:
        return _provider_result(
            provider_name="readability",
            success=False,
            dependency_available=True,
            error=str(exc),
            elapsed_ms=int((time.monotonic() - t0) * 1000),
        )


def selectolax_extract(html: str, selector: str = "main, article, .content, #content") -> dict:
    """Extract from a CSS selector using selectolax (fast C-extension parser)."""
    t0 = time.monotonic()
    try:
        from selectolax.parser import HTMLParser
        parser = HTMLParser(html)
        parts = []
        for sel in selector.split(","):
            sel = sel.strip()
            for node in parser.css(sel):
                text = node.text(separator="\n", strip=True)
                if text:
                    parts.append(text)
        text = "\n\n".join(parts)
        ms = int((time.monotonic() - t0) * 1000)
        return _provider_result(
            provider_name="selectolax",
            success=bool(text.strip()),
            dependency_available=True,
            content=text,
            confidence="medium",
            elapsed_ms=ms,
            metadata={"selector": selector},
        )
    except ImportError:
        return _provider_result(
            provider_name="selectolax",
            success=False,
            dependency_available=False,
            error="selectolax not installed. Install: pip install selectolax",
            elapsed_ms=int((time.monotonic() - t0) * 1000),
        )
    except Exception as exc:
        return _provider_result(
            provider_name="selectolax",
            success=False,
            dependency_available=True,
            error=str(exc),
            elapsed_ms=int((time.monotonic() - t0) * 1000),
        )


def bs4_extract(html: str) -> dict:
    """BeautifulSoup fallback — strips noise tags and returns visible text."""
    t0 = time.monotonic()
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        ms = int((time.monotonic() - t0) * 1000)
        return _provider_result(
            provider_name="bs4",
            success=bool(text.strip()),
            dependency_available=True,
            content=text,
            confidence="low",
            elapsed_ms=ms,
        )
    except ImportError:
        return _provider_result(
            provider_name="bs4",
            success=False,
            dependency_available=False,
            error="beautifulsoup4 not installed.",
            elapsed_ms=int((time.monotonic() - t0) * 1000),
        )
    except Exception as exc:
        return _provider_result(
            provider_name="bs4",
            success=False,
            dependency_available=True,
            error=str(exc),
            elapsed_ms=int((time.monotonic() - t0) * 1000),
        )


def best_html_extract(html: str, content_selector: str | None = None) -> dict:
    """
    Run extraction cascade and return the best result.

    Order:
      1. selectolax with content_selector (if provided and available)
      2. trafilatura
      3. readability
      4. bs4
    """
    candidates = []

    if content_selector:
        r = selectolax_extract(html, content_selector)
        if r["success"] and r["dependency_available"]:
            candidates.append(r)

    for fn in [trafilatura_extract, readability_extract, bs4_extract]:
        r = fn(html)
        if r["success"]:
            candidates.append(r)

    if not candidates:
        return _provider_result(
            provider_name="none",
            success=False,
            dependency_available=True,
            error="All HTML extraction providers failed.",
        )

    # Pick longest content (most content = better)
    return max(candidates, key=lambda r: len(r["content"]))
