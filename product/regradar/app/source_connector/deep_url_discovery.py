"""
Deep URL discovery — systematic path probing for regulatory content.
Probes well-known regulatory paths on a domain, ranks them by
extraction quality and regulatory relevance, returns the best monitoring URL.
"""
import logging
from urllib.parse import urlparse

import requests as _req

from app.config import REQUESTS_UA
from app.extractors import extract_best_text
from app.source_tester import validate_public_url

logger = logging.getLogger(__name__)

_PROBE_TIMEOUT = 12

_PROBE_PATHS = [
    "/news", "/announcements", "/press-releases", "/press-release",
    "/publications", "/documents", "/regulations", "/circulars",
    "/guidelines", "/legal-framework", "/laws", "/decisions",
    "/consultation", "/consultations", "/reports",
    "/supervision", "/licensing", "/enforcement",
    "/aml", "/tax", "/data-protection", "/cybersecurity",
    "/en/news", "/en/announcements", "/en/publications", "/en/regulations",
    "/en/press-releases", "/en/circulars", "/en/guidelines",
    "/en/documents", "/en/laws", "/en/decisions", "/en/reports",
    "/media", "/media-centre", "/media-center",
    "/newsroom", "/news-room",
    "/official-documents", "/regulatory-documents",
]

_REGULATORY_KW = frozenset({
    "regulation", "regulatory", "circular", "notice", "guideline",
    "consultation", "publication", "compliance", "legislation",
    "law", "act", "decree", "order", "decision", "directive",
    "enforcement", "supervision", "license", "anti-money", "aml",
    "tax", "privacy", "press release", "announcement",
    "закон", "постановление", "приказ", "нормативн", "регуляци",
})


def _regulatory_score(text: str) -> int:
    lower = text.lower()
    return sum(1 for kw in _REGULATORY_KW if kw in lower)


def discover_deep_urls(base_url: str, max_probes: int = 20) -> list[dict]:
    """
    Probe well-known regulatory paths on the base URL's domain.
    Returns list of candidates sorted by quality desc, regulatory_score desc, chars desc.
    Only same-domain URLs. Safe crawl limits enforced.
    """
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    results: list[dict] = []
    probed: set[str] = set()
    headers = {"User-Agent": REQUESTS_UA, "Accept-Language": "en,ru;q=0.8"}

    for path in _PROBE_PATHS[:max_probes]:
        candidate = origin + path
        if candidate in probed:
            continue
        probed.add(candidate)

        safe, _ = validate_public_url(candidate)
        if not safe:
            continue
        try:
            resp = _req.get(candidate, headers=headers, timeout=_PROBE_TIMEOUT, allow_redirects=True)
            if not resp.ok:
                continue
            extr = extract_best_text(resp.text, candidate)
            chars = extr.get("extracted_chars", 0)
            text  = extr.get("text", "")
            if chars < 100:
                continue
            quality = "good" if chars >= 1000 else "low_content"
            results.append({
                "url":              candidate,
                "chars":            chars,
                "quality":          quality,
                "regulatory_score": _regulatory_score(text),
                "method":           extr.get("method", "none"),
            })
        except Exception as exc:
            logger.debug("deep_url: %s: %s", candidate, exc)
            continue

    def _sort_key(r: dict) -> tuple:
        q_rank = {"good": 0, "low_content": 1}
        return (q_rank.get(r["quality"], 2), -r["regulatory_score"], -r["chars"])

    results.sort(key=_sort_key)
    return results
