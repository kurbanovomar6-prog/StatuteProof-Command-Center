"""
Source Connection Strategy Engine — full onboarding orchestrator.

run_source_onboarding(url, ...) runs all 9 discovery stages.
"""
import logging
from datetime import date

from app.source_tester import validate_public_url
from app.source_discovery import discover_source_capabilities
from app.source_connector.deep_url_discovery import discover_deep_urls
from app.source_connector.quality_scoring import score_source
from app.source_connector.api_discovery import discover_api_endpoints
from app.source_connector.language_discovery import discover_language_versions

logger = logging.getLogger(__name__)


def run_source_onboarding(
    url: str,
    jurisdiction: str = "",
    category: str = "",
    name: str = "",
) -> dict:
    """
    Full multi-stage source onboarding.

    Stages:
      1. Safety validation
      2-8. 6-layer discovery engine (HTML, JS, sitemap, RSS, documents)
      9. Deep URL path probing (find better URL on same domain)
      10. Language version fallback
      11. API endpoint hints (SPA)
      12. Quality scoring (0-100)
    """
    try:
        from app.scraper import fetch_page
        from app.extractors import extract_best_text as _extract_best_text
        _has_scraper = True
    except Exception:
        _has_scraper = False

    safe, safety_msg = validate_public_url(url)
    if not safe:
        return {
            "submitted_url": url, "best_monitoring_url": url, "safe": False,
            "stages": {}, "tested_methods": [],
            "quality_score": 0, "quality_label": "unusable",
            "recommended_status": "disabled", "connection_method": "unavailable",
            "verdict": "cannot_monitor", "reason": safety_msg,
            "rss_feeds_found": 0, "sitemaps_found": 0,
            "documents_found": 0, "api_endpoints_found": 0,
            "extracted_chars": 0, "has_feed": False, "has_sitemap": False,
            "has_documents": False, "has_api": False,
            "deep_url_candidates": [], "language_versions": [],
            "jurisdiction": jurisdiction, "category": category, "name": name,
            "limitations": [safety_msg], "generated_at": str(date.today()),
        }

    import sys as _sys
    print(f"  [1/4] Core extraction (HTML + Playwright + feeds + sitemap + documents)…", file=_sys.stderr, flush=True)
    discovery = discover_source_capabilities(url, deep=True)

    page     = discovery["page"]
    feeds    = discovery["feeds"]
    sitemaps = discovery["sitemaps"]
    docs     = discovery["documents"]
    caps     = discovery["capabilities"]

    tested_methods = ["static_html"]
    if page.get("used_playwright"):
        tested_methods.append("playwright")
    tested_methods += ["sitemap_discovery", "rss_discovery", "document_discovery"]

    print(f"  [2/4] Deep URL path probing (up to 20 paths)…", file=_sys.stderr, flush=True)
    deep_urls = discover_deep_urls(url, max_probes=20)
    tested_methods.append("deep_url_discovery")

    print(f"  [3/4] Language version discovery…", file=_sys.stderr, flush=True)
    lang_versions = discover_language_versions(url, max_tests=4)
    tested_methods.append("language_fallback")

    print(f"  [4/4] API endpoint hints…", file=_sys.stderr, flush=True)
    api_endpoints = discover_api_endpoints(url)
    tested_methods.append("api_discovery")

    # If discovery extraction failed, fall back to health-check scraper path
    discovery_chars = page.get("extracted_chars", 0)
    if discovery_chars == 0 and _has_scraper:
        try:
            _html = fetch_page(url)
            _extr = _extract_best_text(_html, url)
            if _extr.get("extracted_chars", 0) > 0:
                discovery_chars = _extr["extracted_chars"]
                page = dict(page)
                page["extracted_chars"] = discovery_chars
                page["quality"]         = _extr.get("quality", page.get("quality", "failed"))
                page["best_extractor"]  = _extr.get("method", page.get("best_extractor", "none"))
        except Exception:
            pass

    # Find best monitoring URL
    best_url   = url
    best_chars = discovery_chars

    for candidate in deep_urls:
        if candidate["quality"] == "good" and candidate["chars"] > best_chars * 1.3:
            best_url   = candidate["url"]
            best_chars = candidate["chars"]
            break

    if lang_versions and lang_versions[0]["quality"] == "good":
        lang_chars = lang_versions[0]["chars"]
        if lang_chars > best_chars * 1.2:
            best_url   = lang_versions[0]["url"]
            best_chars = lang_chars

    has_feed = bool(feeds)
    has_sm   = any(s.get("links_found", 0) > 0 for s in sitemaps)
    has_docs = docs.get("extractable_documents", 0) > 0
    has_api  = bool(api_endpoints)

    quality_result = score_source(
        extracted_chars = best_chars,
        has_feed        = has_feed,
        has_sitemap     = has_sm,
        has_documents   = has_docs,
        has_api         = has_api,
        used_playwright = page.get("used_playwright", False),
    )

    if has_feed:
        connection_method = "rss"
    elif has_api:
        connection_method = "api_endpoint"
    elif caps.get("html_monitoring"):
        connection_method = "static_html"
    elif caps.get("js_html_monitoring"):
        connection_method = "playwright"
    elif has_sm:
        connection_method = "sitemap"
    elif has_docs:
        connection_method = "document_feed"
    elif best_url != url:
        connection_method = "deep_url"
    else:
        connection_method = "custom_adapter"

    verdict = discovery["verdict"]
    reason  = discovery["reason"]

    # If scraper fallback recovered content, upgrade verdict from cannot_monitor
    if verdict == "cannot_monitor" and best_chars >= 500:
        verdict = "can_monitor"
        reason  = f"Content recoverable via two-tier scraper ({best_chars:,} chars)."

    # Structural signals can upgrade verdict, but ONLY when we have some extractable content.
    # A sitemap or doc link alone (with 0c) does not make a source monitorable.
    if verdict in ("needs_adapter", "cannot_monitor") and best_chars >= 200 and (best_url != url or has_api or has_sm or has_docs):
        verdict = "can_monitor"
        if best_url != url:
            reason = f"Better monitoring URL found: {best_url}"
        elif has_sm:
            reason = "Sitemap-based monitoring available."
        elif has_docs:
            reason = "Document feed monitoring available."

    score = quality_result["score"]
    if verdict == "can_monitor" and score >= 45:
        recommended_status = "active"
    elif verdict == "can_monitor" and score >= 20:
        recommended_status = "limited"
    elif verdict == "can_monitor":
        recommended_status = "mapped"
    elif verdict == "needs_adapter":
        recommended_status = "adapter_required"
    else:
        recommended_status = "disabled"

    limitations: list[str] = []
    if page.get("used_playwright"):
        limitations.append("Requires Playwright rendering (JS-rendered site)")
    if not has_feed and not has_sm and score < 65:
        limitations.append("No RSS feed or sitemap found for structured monitoring")
    if best_chars < 1000 and verdict != "cannot_monitor":
        limitations.append(f"Low content extraction ({best_chars:,} chars)")

    return {
        "submitted_url":        url,
        "best_monitoring_url":  best_url,
        "safe":                 True,
        "stages": {
            "static_html":      {"chars": discovery_chars, "quality": page.get("quality", "failed"), "extractor": page.get("best_extractor", "none")},
            "playwright":       {"used": page.get("used_playwright", False)},
            "deep_urls":        {"candidates_found": len(deep_urls), "best": deep_urls[0] if deep_urls else None},
            "language_fallback":{"versions_found": len(lang_versions), "best": lang_versions[0] if lang_versions else None},
            "rss_feeds":        {"found": len(feeds), "feeds": feeds[:3]},
            "sitemaps":         {"found": len(sitemaps), "sitemaps": sitemaps},
            "documents":        {"pdf_links": docs.get("pdf_links_found", 0), "extractable": docs.get("extractable_documents", 0)},
            "api_endpoints":    {"found": len(api_endpoints), "endpoints": api_endpoints[:3]},
        },
        "tested_methods":       tested_methods,
        "extracted_chars":      best_chars,
        "quality_score":        score,
        "quality_label":        quality_result["label"],
        "quality_breakdown":    quality_result["breakdown"],
        "has_feed":             has_feed,
        "has_sitemap":          has_sm,
        "has_documents":        has_docs,
        "has_api":              has_api,
        "rss_feeds_found":      len(feeds),
        "sitemaps_found":       len(sitemaps),
        "documents_found":      docs.get("pdf_links_found", 0),
        "api_endpoints_found":  len(api_endpoints),
        "deep_url_candidates":  deep_urls[:5],
        "language_versions":    lang_versions[:3],
        "recommended_status":   recommended_status,
        "connection_method":    connection_method,
        "verdict":              verdict,
        "reason":               reason,
        "limitations":          limitations,
        "jurisdiction":         jurisdiction,
        "category":             category,
        "name":                 name,
        "generated_at":         str(date.today()),
    }
