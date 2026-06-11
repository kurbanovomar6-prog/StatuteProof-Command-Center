"""Language version discovery for regulatory websites."""
import logging
from urllib.parse import urlparse

import requests as _req

from app.config import REQUESTS_UA
from app.extractors import extract_best_text
from app.source_tester import validate_public_url

logger = logging.getLogger(__name__)

_LANG_TIMEOUT = 12

_LANG_PATHS = [
    ("/en",      "English"),
    ("/en/",     "English"),
    ("/en-US",   "English"),
    ("/english", "English"),
    ("/ru",      "Russian"),
    ("/ru/",     "Russian"),
    ("/ar",      "Arabic"),
    ("/ar/",     "Arabic"),
    ("/tr",      "Turkish"),
    ("/az",      "Azerbaijani"),
    ("/ka",      "Georgian"),
    ("/kk",      "Kazakh"),
    ("/hy",      "Armenian"),
    ("/uz",      "Uzbek"),
]


def discover_language_versions(base_url: str, max_tests: int = 6) -> list[dict]:
    """
    Test language variants of the base URL.
    Returns list sorted by chars descending (best content first).
    """
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    tested: set[str] = set()
    results: list[dict] = []
    headers = {"User-Agent": REQUESTS_UA, "Accept-Language": "en,ru;q=0.8"}

    for lang_path, language in _LANG_PATHS[:max_tests]:
        candidate = origin + lang_path
        if candidate in tested or candidate.rstrip("/") == base_url.rstrip("/"):
            continue
        tested.add(candidate)
        safe, _ = validate_public_url(candidate)
        if not safe:
            continue
        try:
            resp = _req.get(candidate, headers=headers, timeout=_LANG_TIMEOUT, allow_redirects=True)
            if not resp.ok:
                continue
            extr = extract_best_text(resp.text, candidate)
            chars = extr.get("extracted_chars", 0)
            if chars < 100:
                continue
            results.append({
                "url":      candidate,
                "language": language,
                "chars":    chars,
                "quality":  "good" if chars >= 1000 else "low_content",
            })
        except Exception as exc:
            logger.debug("lang_discovery: %s: %s", candidate, exc)
    results.sort(key=lambda r: -r["chars"])
    return results
