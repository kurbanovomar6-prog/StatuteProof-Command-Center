"""
API endpoint discovery for SPA websites.
Tests well-known public API paths. Only public, unauthenticated endpoints.
No auth bypass, no token circumvention.
"""
import json
import logging
from urllib.parse import urlparse

import requests as _req

from app.config import REQUESTS_UA
from app.source_tester import validate_public_url

logger = logging.getLogger(__name__)

_API_TIMEOUT = 10

_API_PATHS = [
    "/api/news", "/api/publications", "/api/announcements",
    "/api/content", "/api/documents", "/api/regulations",
    "/api/decisions", "/api/search", "/api/articles",
    "/wp-json/wp/v2/posts", "/wp-json/wp/v2/pages",
    "/api/v1/news", "/api/v2/publications",
    "/api/v1/publications", "/api/v1/regulations",
]


def _is_json_with_content(text: str) -> tuple[bool, int]:
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return False, 0
    if isinstance(data, list) and len(data) > 0:
        return True, len(data)
    if isinstance(data, dict):
        for key in ("results", "items", "data", "content", "posts", "publications"):
            val = data.get(key)
            if isinstance(val, list) and len(val) > 0:
                return True, len(val)
    return False, 0


def discover_api_endpoints(base_url: str) -> list[dict]:
    """
    Test well-known API paths on the base URL's domain.
    Returns list of dicts for each working endpoint with content.
    Only same-domain, public, unauthenticated endpoints.
    """
    parsed = urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    found: list[dict] = []
    headers = {"User-Agent": REQUESTS_UA, "Accept": "application/json, */*;q=0.8"}

    for path in _API_PATHS:
        candidate = origin + path
        safe, _ = validate_public_url(candidate)
        if not safe:
            continue
        try:
            resp = _req.get(candidate, headers=headers, timeout=_API_TIMEOUT, allow_redirects=True)
            if not resp.ok:
                continue
            ct = resp.headers.get("content-type", "").lower()
            if "json" not in ct and not resp.text.strip().startswith(("[", "{")):
                continue
            is_useful, item_count = _is_json_with_content(resp.text)
            if is_useful:
                ep_type = "wordpress" if "wp-json" in path else "rest_api"
                found.append({"url": candidate, "type": ep_type, "status": "ok", "item_count": item_count})
                if len(found) >= 3:
                    break
        except Exception as exc:
            logger.debug("api_discovery: %s: %s", candidate, exc)
    return found
