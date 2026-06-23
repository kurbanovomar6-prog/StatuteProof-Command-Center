"""
RegRadar — adapter research engine.

Investigates a single source to help plan a custom adapter.
No AI, no Telegram, no DB writes, no sources.json modification.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests as _req
from bs4 import BeautifulSoup

from app.config import HTTP_TIMEOUT_S, REQUESTS_UA
from app.extractors import extract_best_text
from app.scraper import _fetch_via_playwright, is_low_content_html

logger = logging.getLogger(__name__)

_SOURCES_PATH = Path(__file__).parent.parent / "sources.json"
_SEP2 = "═" * 68

# Path keywords that suggest relevant regulatory content pages
_CONTENT_KEYWORDS = (
    "press", "news", "document", "legal", "act", "publication",
    "normative", "regulation", "order", "decision", "resolution",
    "announce", "circular", "letter", "bulletin", "review",
    "press-release", "press_release",
)

# Path/extension patterns that suggest structured data endpoints
_API_RSS_KEYWORDS = (
    "/rss", "/feed", "/api", "/search",
    ".rss", ".json",
    "/press", "/news", "/documents", "/legal", "/acts",
    "/publications", "/regulation", "/regulations",
)

# Sitemap and robots paths to probe
_DISCOVERY_PATHS = (
    "/sitemap.xml",
    "/sitemap_index.xml",
    "/sitemap/",
    "/robots.txt",
)

_PROBE_TIMEOUT_S = 8


# ── Source lookup ─────────────────────────────────────────────────────────────

def _load_sources() -> list[dict]:
    try:
        return json.loads(_SOURCES_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error("adapter-research: cannot read sources.json: %s", exc)
        return []


def find_sources(query: str) -> list[dict]:
    """
    Return all sources whose name / url / category / jurisdiction
    contain the query string (case-insensitive substring match).
    """
    q = query.lower().strip()
    results = []
    for s in _load_sources():
        haystack = " ".join([
            s.get("name",         ""),
            s.get("url",          ""),
            s.get("category",     ""),
            s.get("jurisdiction", ""),
        ]).lower()
        if q in haystack:
            results.append(s)
    return results


# ── URL helpers ───────────────────────────────────────────────────────────────

def _base_url(url: str) -> str:
    """Return scheme://netloc (no path) for constructing probe URLs."""
    try:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}"
    except Exception:
        return url


def _same_domain(url: str, base: str) -> bool:
    try:
        return urlparse(url).netloc == urlparse(base).netloc
    except Exception:
        return False


# ── Link categorisation ───────────────────────────────────────────────────────

def _categorise_links(html: str, page_url: str) -> dict:
    """
    Parse all hrefs from `html` and split into four buckets:

    internal_links   — same-domain hrefs
    pdf_links        — .pdf hrefs
    api_rss_links    — hrefs that look like APIs, feeds, or search endpoints
    relevant_links   — internal hrefs whose path contains regulatory keywords
    """
    if not html:
        return {"all_count": 0, "internal_links": [],
                "pdf_links": [], "api_rss_links": [], "relevant_links": []}

    base = _base_url(page_url)
    soup = BeautifulSoup(html, "html.parser")
    seen:     set[str]  = set()
    all_hrefs: list[str] = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
            continue
        try:
            full = urljoin(page_url, href)
            p    = urlparse(full)
            if p.scheme not in ("http", "https") or not p.netloc:
                continue
            if full not in seen:
                seen.add(full)
                all_hrefs.append(full)
        except Exception:
            continue

    def _is_pdf(u: str) -> bool:
        return urlparse(u).path.lower().endswith(".pdf")

    def _is_api_rss(u: str) -> bool:
        ul = u.lower()
        return any(kw in ul for kw in _API_RSS_KEYWORDS)

    def _is_relevant(u: str) -> bool:
        if not _same_domain(u, base):
            return False
        path = urlparse(u).path.lower()
        return any(kw in path for kw in _CONTENT_KEYWORDS)

    internal = [u for u in all_hrefs if _same_domain(u, base)]
    pdfs     = [u for u in all_hrefs if _is_pdf(u)]
    api_rss  = [u for u in all_hrefs if _is_api_rss(u)]
    relevant = [u for u in internal  if _is_relevant(u)]

    return {
        "all_count":      len(all_hrefs),
        "internal_links": internal[:50],
        "pdf_links":      pdfs[:20],
        "api_rss_links":  api_rss[:20],
        "relevant_links": relevant[:20],
    }


# ── Sitemap probing ───────────────────────────────────────────────────────────

def _probe_discovery_paths(base: str) -> list[dict]:
    """
    HEAD then GET each standard discovery path.
    Returns only paths that returned HTTP 200 and non-trivial content.
    """
    found = []
    for path in _DISCOVERY_PATHS:
        url = base.rstrip("/") + path
        try:
            resp = _req.get(
                url,
                headers={"User-Agent": REQUESTS_UA},
                timeout=_PROBE_TIMEOUT_S,
                allow_redirects=True,
            )
            if resp.status_code == 200 and len(resp.text) > 200:
                ct = resp.headers.get("content-type", "").split(";")[0].strip()
                found.append({
                    "path":         path,
                    "url":          url,
                    "status":       resp.status_code,
                    "content_type": ct,
                    "size":         len(resp.text),
                })
        except Exception:
            pass   # unreachable path — expected and fine
    return found


# ── Recommendation builder ────────────────────────────────────────────────────

def _build_recommendation(
    *,
    extracted_chars: int,
    fetch_ok:        bool,
    error:           str | None,
    pdf_links:       list[str],
    api_rss_links:   list[str],
    sitemap_found:   list[dict],
    relevant_links:  list[str],
) -> dict:
    """Map research findings to a verdict + suggested adapter strategy."""

    # ── Fetch failure ───────────────────────────────────────────────────────
    if not fetch_ok:
        err = (error or "").lower()
        if any(k in err for k in ("name_not_resolved", "gaierror", "nameresolution", "name resolution")):
            return {
                "verdict":            "find_better_url",
                "reason":             "Domain does not resolve — URL is outdated or incorrect.",
                "suggested_strategy": "Find the correct official URL or updated domain for this regulator.",
            }
        if any(k in err for k in ("ssl", "certificate", "cert_", "verify failed")):
            return {
                "verdict":            "find_better_url",
                "reason":             "SSL/TLS certificate error prevents fetching.",
                "suggested_strategy": (
                    "Check alternate official domain, http/https variant, "
                    "or locate the source through the regulator's main website."
                ),
            }
        return {
            "verdict":            "find_better_url",
            "reason":             f"Page could not be fetched: {(error or 'unknown')[:120]}",
            "suggested_strategy": "Test URL manually in a browser; find a publicly accessible alternative.",
        }

    # ── Extraction already good ─────────────────────────────────────────────
    if extracted_chars >= 1_000:
        return {
            "verdict":            "generic_ok",
            "reason":             f"Extracted {extracted_chars:,} chars — generic extractor is sufficient.",
            "suggested_strategy": (
                "No custom adapter required. "
                "If content is still below the 1 000-char threshold in monitoring, "
                "check whether the source requires a deeper page (a press-release index rather than the homepage)."
            ),
        }

    # ── PDF-first sources ───────────────────────────────────────────────────
    if pdf_links:
        return {
            "verdict":            "pdf_extraction_needed",
            "reason":             (
                f"Only {extracted_chars:,} chars from HTML, "
                f"but {len(pdf_links)} PDF link(s) found. "
                "Regulatory documents are likely published as PDFs."
            ),
            "suggested_strategy": (
                "Build adapter that follows PDF links and extracts text from each document. "
                "Prioritise recently dated filenames or a /documents/ index page."
            ),
        }

    # ── Sitemap found ───────────────────────────────────────────────────────
    smap = next((s for s in sitemap_found if "sitemap" in s["path"]), None)
    if smap:
        return {
            "verdict":            "needs_custom_adapter",
            "reason":             (
                f"Only {extracted_chars:,} chars from main page, "
                f"but sitemap found at {smap['url']} ({smap['size']:,} chars)."
            ),
            "suggested_strategy": (
                "Use official sitemap to discover document/press pages. "
                "Build a sitemap-walker adapter that fetches and extracts individual items."
            ),
        }

    # ── API / RSS endpoints ─────────────────────────────────────────────────
    if api_rss_links:
        return {
            "verdict":            "endpoint_research_needed",
            "reason":             (
                f"Only {extracted_chars:,} chars from main page, "
                f"but {len(api_rss_links)} API/RSS-like link(s) detected."
            ),
            "suggested_strategy": (
                "Investigate the API/RSS endpoints found in the links section. "
                "Build a lightweight adapter that reads structured data directly "
                "instead of parsing HTML."
            ),
        }

    # ── Relevant content links ──────────────────────────────────────────────
    if relevant_links:
        return {
            "verdict":            "needs_custom_adapter",
            "reason":             (
                f"Only {extracted_chars:,} chars from main page, "
                f"but {len(relevant_links)} relevant content link(s) found "
                "(press / news / documents section)."
            ),
            "suggested_strategy": (
                "Build adapter that follows press/news/document article links and "
                "combines latest item texts for change detection."
            ),
        }

    # ── No useful signals ───────────────────────────────────────────────────
    return {
        "verdict":            "needs_custom_adapter",
        "reason":             (
            f"Only {extracted_chars:,} chars extracted. "
            "Site may be heavily JS-rendered or require authentication."
        ),
        "suggested_strategy": (
            "Inspect the site manually in a browser. "
            "Locate a dedicated press/news/documents section and test its URL with "
            "'python run.py test-source <section-url>'. "
            "Build a custom adapter once a stable content URL is identified."
        ),
    }


# ── Main research entry point ─────────────────────────────────────────────────

def run_adapter_research(query: str) -> dict | None:
    """
    Full research run for one source.

    Returns the research result dict, or None if no source matched the query.
    Never raises — all errors are captured inside the result.
    """
    matches = find_sources(query)

    if not matches:
        print(f"\n  No source found matching {query!r}.", flush=True)
        print("  Tip: use 'python run.py sources' to list all available sources.", flush=True)
        return None

    if len(matches) > 1:
        print(f"\n  Multiple sources match {query!r}:", flush=True)
        for m in matches:
            print(f"    • {m['name']}  ({m['url']})", flush=True)
        print("  → Researching the first match. Use a more specific query to target another.\n",
              flush=True)

    source = matches[0]
    url    = source.get("url", "")
    base   = _base_url(url)

    result: dict = {
        "source":        source,
        "http_status":   None,
        "final_url":     url,
        "content_type":  "",
        "raw_html_len":  0,
        "fetch_ok":      False,
        "fetch_error":   None,
        "extraction":    None,
        "links":         None,
        "sitemap_found": [],
        "pdf_extraction": None,
        "recommendation": None,
    }

    # ── Tier 1 — requests ───────────────────────────────────────────────────
    tier1_html: str | None = None
    try:
        resp = _req.get(
            url,
            headers={"User-Agent": REQUESTS_UA, "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"},
            timeout=HTTP_TIMEOUT_S,
            allow_redirects=True,
        )
        result["http_status"]  = resp.status_code
        result["final_url"]    = str(resp.url)
        result["content_type"] = resp.headers.get("content-type", "").split(";")[0].strip()
        if resp.ok:
            tier1_html = resp.text
    except _req.RequestException as exc:
        result["fetch_error"] = str(exc)
        print(f"  Tier 1 failed: {type(exc).__name__} — trying Playwright …", flush=True)

    # ── Tier 2 — Playwright fallback ────────────────────────────────────────
    raw_html: str | None = None
    if tier1_html and not is_low_content_html(tier1_html):
        raw_html = tier1_html
    else:
        if tier1_html:
            print("  Tier 1 low content — escalating to Playwright …", flush=True)
        try:
            raw_html = _fetch_via_playwright(url)
            if result["http_status"] is None:
                result["http_status"] = 200
            result["fetch_error"] = None     # Playwright recovered
        except Exception as pw_exc:
            logger.debug("Playwright fetch failed for %s: %s", url, pw_exc)
            if tier1_html:
                raw_html = tier1_html        # best-effort fallback
            else:
                if not result["fetch_error"]:
                    result["fetch_error"] = str(pw_exc)

    if raw_html:
        result["raw_html_len"] = len(raw_html)
        result["fetch_ok"]     = True

    # ── Extraction ──────────────────────────────────────────────────────────
    if raw_html:
        result["extraction"] = extract_best_text(raw_html, url)

    extracted_chars = (result["extraction"] or {}).get("extracted_chars", 0)

    # ── Link categorisation ─────────────────────────────────────────────────
    if raw_html:
        result["links"] = _categorise_links(raw_html, url)

    # ── Sitemap / discovery probing ─────────────────────────────────────────
    print("  Probing sitemap / discovery paths …", flush=True)
    result["sitemap_found"] = _probe_discovery_paths(base)

    # ── PDF extraction (when HTML is low-content and PDFs are found) ───────
    lnk = result["links"] or {}
    pdf_links = lnk.get("pdf_links", [])
    if pdf_links and extracted_chars < 1_000 and raw_html:
        print(
            f"  PDF links found ({len(pdf_links)}) — extracting up to 3 …",
            flush=True,
        )
        try:
            from app.document_extractor import extract_documents_from_page
            result["pdf_extraction"] = extract_documents_from_page(
                raw_html, url, max_docs=3,
            )
        except Exception as exc:
            logger.warning("adapter-research: PDF extraction error: %s", exc)
            result["pdf_extraction"] = {"error": str(exc)}

    # ── Build recommendation ────────────────────────────────────────────────
    lnk = result["links"] or {}
    result["recommendation"] = _build_recommendation(
        extracted_chars = extracted_chars,
        fetch_ok        = result["fetch_ok"],
        error           = result["fetch_error"],
        pdf_links       = lnk.get("pdf_links",    []),
        api_rss_links   = lnk.get("api_rss_links", []),
        sitemap_found   = result["sitemap_found"],
        relevant_links  = lnk.get("relevant_links", []),
    )

    return result


# ── Terminal report ───────────────────────────────────────────────────────────

def print_research_report(result: dict) -> None:
    s    = result["source"]
    extr = result["extraction"] or {}
    lnk  = result["links"]      or {}
    rec  = result["recommendation"] or {}

    print()
    print(_SEP2)
    print("  StatuteProof — Adapter Research")
    print(_SEP2)

    # ── Source ──────────────────────────────────────────────────────────────
    print()
    print("  Source:")
    print(f"    Name         : {s.get('name', '?')}")
    print(f"    URL          : {s.get('url',  '?')}")
    print(f"    Jurisdiction : {s.get('jurisdiction', '?')}")
    print(f"    Category     : {s.get('category', '?')}")
    print(f"    Enabled      : {s.get('enabled', False)}")
    print(f"    Status       : {s.get('status', '?')}")

    # ── Fetch ───────────────────────────────────────────────────────────────
    print()
    print("  Fetch:")
    print(f"    HTTP status  : {result['http_status'] or 'failed'}")
    if result["final_url"] and result["final_url"] != s.get("url", ""):
        print(f"    Final URL    : {result['final_url']}")
    print(f"    Content type : {result['content_type'] or 'unknown'}")
    print(f"    HTML length  : {result['raw_html_len']:,} chars")
    if result["fetch_error"] and not result["fetch_ok"]:
        # Truncate long error messages; never print secrets
        err_display = result["fetch_error"]
        if len(err_display) > 160:
            err_display = err_display[:160] + " …"
        print(f"    Error        : {err_display}")

    # ── Extraction ──────────────────────────────────────────────────────────
    print()
    print("  Extraction:")
    if extr:
        best = extr.get("method", "none")
        print(f"    Best extractor  : {best}")
        print(f"    Extracted chars : {extr.get('extracted_chars', 0):,}")
        print(f"    Quality         : {extr.get('quality', 'failed')}")
        cands = extr.get("candidates", [])
        if cands:
            print("    Candidates:")
            for c in cands:
                star = "★" if c["method"] == best else " "
                print(f"      {star} {c['method']:16} {c['chars']:6,}c  {c['quality']}")
    else:
        print("    No extraction — fetch failed.")

    # ── Discovery ───────────────────────────────────────────────────────────
    print()
    print("  Discovery:")
    all_n    = lnk.get("all_count",      0)
    internal = lnk.get("internal_links", [])
    relevant = lnk.get("relevant_links", [])
    pdfs     = lnk.get("pdf_links",      [])
    api_rss  = lnk.get("api_rss_links",  [])

    print(f"    Internal links found       : {len(internal)}  (of {all_n} total)")

    print(f"    Relevant content links     : {len(relevant)}")
    for u in relevant[:20]:
        print(f"      • {u}")

    print(f"    PDF links                  : {len(pdfs)}")
    for u in pdfs[:10]:
        print(f"      • {u}")

    print(f"    API / RSS / search links   : {len(api_rss)}")
    for u in api_rss[:10]:
        print(f"      • {u}")

    sm = result["sitemap_found"]
    print(f"    Sitemap / robots found     : {len(sm)}")
    for item in sm:
        print(f"      • {item['url']}  [{item['content_type']}  {item['size']:,} chars]")

    # ── PDF Extraction ──────────────────────────────────────────────────────
    pdf_extr = result.get("pdf_extraction")
    if pdf_extr and not pdf_extr.get("error"):
        print()
        print("  PDF Extraction:")
        print(f"    PDFs found           : {pdf_extr.get('documents_found', 0)}")
        print(f"    PDFs processed       : {pdf_extr.get('pdf_processed', 0)}")
        print(f"    Combined chars       : {pdf_extr.get('combined_chars', 0):,}")
        print(f"    Quality              : {pdf_extr.get('quality', 'failed')}")
        for item in pdf_extr.get("items", []):
            fn    = item["url"].split("/")[-1][:50]
            chars = item.get("chars", 0)
            qual  = item.get("quality", "failed")
            meth  = item.get("method", "none")
            err   = item.get("error", "")
            if err:
                print(f"      ✗ {fn}  error: {err[:60]}")
            else:
                print(f"      ✓ {fn}  {chars:,}c  {qual}  [{meth}]")

    # ── Recommendation ──────────────────────────────────────────────────────
    print()
    print("  Recommendation:")
    print(f"    Verdict           : {rec.get('verdict', 'unknown')}")
    print(f"    Reason            : {rec.get('reason', '')}")
    print(f"    Suggested strategy: {rec.get('suggested_strategy', '')}")

    print()
    print(_SEP2)
