"""
RegRadar — Multi-strategy HTML extraction layer.

extract_best_text(html, url) tries up to four strategies and picks the
highest-scoring result.  Strategies that are not installed are silently
skipped; the existing BeautifulSoup parser always runs as the baseline.

Strategy order
--------------
1. BeautifulSoup (always available — existing parser)
2. Trafilatura    (if ``pip install trafilatura``)
3. readability-lxml (if ``pip install readability-lxml``)
4. Crawl4AI       (if installed AND ENABLE_CRAWL4AI_EXTRACTOR=true)

Scoring (Step 8 from spec)
--------------------------
    score = len(text) + unique_paragraphs * 200 - duplicate_paragraphs * 100

"Good" quality wins over a higher score from a "low_content" result, so
long boilerplate-heavy outputs are deprioritised.

Quality thresholds
------------------
    good          >= 1 000 chars
    low_content   >= 100  chars
    failed        <  100  chars
"""

from __future__ import annotations

import asyncio
import logging
import re

from app.parser import extract_text

logger = logging.getLogger(__name__)

_GOOD_CHARS   = 1_000
_LOW_CHARS    = 100
_MIN_PARA_LEN = 30

_HSPACE_RE = re.compile(r"[ \t]+")
_PARA_SEP  = re.compile(r"\n{2,}")


# ── quality / scoring helpers ─────────────────────────────────────────────────

def _quality(chars: int) -> str:
    if chars >= _GOOD_CHARS:
        return "good"
    if chars >= _LOW_CHARS:
        return "low_content"
    return "failed"


def _normalize(text: str) -> str:
    """Collapse horizontal whitespace; preserve paragraph breaks."""
    lines = [_HSPACE_RE.sub(" ", line).strip() for line in text.splitlines()]
    return "\n".join(lines).strip()


def _deduplicate(text: str) -> str:
    """Remove exact-duplicate paragraphs (split on blank lines)."""
    paras  = _PARA_SEP.split(text)
    seen:  set[str] = set()
    out:   list[str] = []
    for p in paras:
        p = p.strip()
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return "\n\n".join(out)


def _score(text: str) -> float:
    """
    Score a candidate:  chars + unique_paragraphs*200 - duplicate_paragraphs*100

    Higher is better.  Boilerplate-heavy outputs score lower because
    duplicate paragraphs are penalised.
    """
    if not text:
        return 0.0
    lines = [l.strip() for l in text.splitlines() if len(l.strip()) >= _MIN_PARA_LEN]
    seen:  set[str] = set()
    unique = 0
    dupes  = 0
    for line in lines:
        if line in seen:
            dupes += 1
        else:
            seen.add(line)
            unique += 1
    return float(len(text) + unique * 200 - dupes * 100)


# ── individual strategies ─────────────────────────────────────────────────────

def _try_beautifulsoup(html: str) -> str:
    """Always available — delegates to the existing BeautifulSoup parser."""
    try:
        raw = extract_text(html)
        return _deduplicate(_normalize(raw))
    except Exception as exc:
        logger.debug("extractors: BeautifulSoup error: %s", exc)
        return ""


def _try_trafilatura(html: str) -> str | None:
    """
    Trafilatura — specialised web content extractor.
    Install: pip install trafilatura
    Returns None if not installed or extraction fails.
    """
    try:
        import trafilatura  # type: ignore[import-untyped]
    except ImportError:
        return None
    try:
        result = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            favor_precision=False,
        )
        if not result:
            return None
        return _deduplicate(_normalize(result))
    except Exception as exc:
        logger.debug("extractors: trafilatura error: %s", exc)
        return None


def _try_readability(html: str) -> str | None:
    """
    readability-lxml — Readability algorithm port.
    Install: pip install readability-lxml
    Returns None if not installed or extraction fails.
    """
    try:
        from readability import Document  # type: ignore[import-untyped]
    except ImportError:
        return None
    try:
        from bs4 import BeautifulSoup as _BS

        doc      = Document(html)
        summary  = doc.summary()   # returns HTML of main content
        if not summary:
            return None
        soup     = _BS(summary, "html.parser")
        raw_text = soup.get_text(separator="\n")
        if not raw_text or not raw_text.strip():
            return None
        return _deduplicate(_normalize(raw_text))
    except Exception as exc:
        logger.debug("extractors: readability error: %s", exc)
        return None


def _try_crawl4ai(url: str) -> str | None:
    """
    Crawl4AI — AI-ready async web crawler (experimental).
    Install: pip install crawl4ai
    Enabled: ENABLE_CRAWL4AI_EXTRACTOR=true in environment.

    NOTE: this strategy re-fetches the URL via a headless browser.
    It is only attempted when all other strategies return low-quality results
    and an explicit opt-in flag is set.

    Returns None if not installed, flag is off, or extraction fails.
    """
    try:
        from app.config import ENABLE_CRAWL4AI_EXTRACTOR
        if not ENABLE_CRAWL4AI_EXTRACTOR:
            return None
    except Exception:
        return None

    if not url or not url.startswith(("http://", "https://")):
        return None

    try:
        import crawl4ai as _c4  # noqa: F401  — check installed
    except ImportError:
        return None

    async def _run() -> str | None:
        try:
            from crawl4ai import AsyncWebCrawler  # type: ignore[import-untyped]
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(url=url)
                success = getattr(result, "success", False)
                if not success:
                    return None
                # Handle both string markdown and MarkdownGenerationResult objects
                md = getattr(result, "markdown", None)
                if md is None:
                    return None
                # Newer Crawl4AI wraps markdown in an object
                if hasattr(md, "raw_markdown"):
                    md = md.raw_markdown
                if not md:
                    return None
                return _deduplicate(_normalize(str(md)))
        except Exception as exc:
            logger.debug("extractors: crawl4ai inner error: %s", exc)
            return None

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.debug("extractors: crawl4ai asyncio.run error: %s", exc)
        return None


# ── public API ────────────────────────────────────────────────────────────────

def extract_best_text(html: str, url: str = "") -> dict:
    """
    Run all available extraction strategies on `html` and return the best.

    Parameters
    ----------
    html : str
        Raw HTML already fetched from `url`.
    url : str
        Source URL — passed to Crawl4AI only when other strategies fail and
        ENABLE_CRAWL4AI_EXTRACTOR is true.

    Returns
    -------
    dict
        text             — best extracted text (empty string on total failure)
        method           — winning strategy name
        extracted_chars  — character count of winning text
        quality          — "good" | "low_content" | "failed"
        candidates       — list of all tried candidates:
                           [{"method": str, "chars": int, "quality": str}, ...]
    """
    if not html:
        return {
            "text":            "",
            "method":          "none",
            "extracted_chars": 0,
            "quality":         "failed",
            "candidates":      [],
        }

    # ── 1. Run synchronous strategies ─────────────────────────────────────
    raw: list[tuple[str, str]] = []   # (method_name, text)

    raw.append(("beautifulsoup", _try_beautifulsoup(html)))

    traf = _try_trafilatura(html)
    if traf is not None:
        raw.append(("trafilatura", traf))

    read = _try_readability(html)
    if read is not None:
        raw.append(("readability", read))

    # ── 2. Crawl4AI: last resort, only when everything else is low ─────────
    best_so_far = max((len(t) for _, t in raw if t), default=0)
    if best_so_far < _GOOD_CHARS and url:
        c4ai = _try_crawl4ai(url)
        if c4ai is not None:
            raw.append(("crawl4ai", c4ai))

    # ── 3. Build candidate metadata ────────────────────────────────────────
    candidates: list[dict] = [
        {
            "method":  method,
            "chars":   len(text) if text else 0,
            "quality": _quality(len(text) if text else 0),
        }
        for method, text in raw
    ]

    # ── 4. Select best by score; prefer "good" quality over bare length ────
    viable = [
        (method, text, _score(text))
        for method, text in raw
        if text and len(text) >= _LOW_CHARS
    ]

    if viable:
        viable.sort(key=lambda x: x[2], reverse=True)
        best_method, best_text, _ = viable[0]

        # Promote first "good"-quality candidate if top scorer is not "good"
        if len(best_text) < _GOOD_CHARS:
            for method, text, _ in viable:
                if len(text) >= _GOOD_CHARS:
                    best_method, best_text = method, text
                    break
    else:
        # Every strategy returned trivially short text — fall back to BS4
        bs_text = next((t for m, t in raw if m == "beautifulsoup"), "")
        best_method = "beautifulsoup"
        best_text   = bs_text

    best_chars = len(best_text)
    logger.info(
        "extractors: best=%s chars=%d quality=%s (tried %d strategies)",
        best_method, best_chars, _quality(best_chars), len(raw),
    )

    return {
        "text":            best_text,
        "method":          best_method,
        "extracted_chars": best_chars,
        "quality":         _quality(best_chars),
        "candidates":      candidates,
    }
