"""
Optional analysis tool providers.

All gracefully degrade when dependency is not installed.
These are helpers for metadata extraction and structured diffing.

Tools:
  - htmldate    — extract publication/modification date from HTML
  - courlan     — canonicalize and validate URLs
  - deepdiff    — structured JSON/dict diff for evidence comparison
"""

from __future__ import annotations

import time


# ── htmldate ─────────────────────────────────────────────────────────────────

def extract_date_from_html(html: str) -> dict:
    """Extract the most likely publication date from HTML using htmldate."""
    t0 = time.monotonic()
    try:
        from htmldate import find_date
        date_str = find_date(html, original_date=False, extensive_search=False) or ""
        ms = int((time.monotonic() - t0) * 1000)
        return {
            "provider": "htmldate",
            "available": True,
            "success": bool(date_str),
            "date": date_str,
            "error": "",
            "elapsed_ms": ms,
        }
    except ImportError:
        return {
            "provider": "htmldate",
            "available": False,
            "success": False,
            "date": "",
            "error": "htmldate not installed. Install: pip install htmldate",
            "elapsed_ms": int((time.monotonic() - t0) * 1000),
        }
    except Exception as exc:
        return {
            "provider": "htmldate",
            "available": True,
            "success": False,
            "date": "",
            "error": str(exc),
            "elapsed_ms": int((time.monotonic() - t0) * 1000),
        }


# ── courlan ───────────────────────────────────────────────────────────────────

def canonicalize_url(url: str) -> dict:
    """Canonicalize and validate a URL using courlan."""
    t0 = time.monotonic()
    try:
        from courlan import check_url, clean_url
        cleaned = clean_url(url) or url
        is_valid = bool(check_url(cleaned))
        ms = int((time.monotonic() - t0) * 1000)
        return {
            "provider": "courlan",
            "available": True,
            "success": is_valid,
            "canonical_url": cleaned,
            "is_valid": is_valid,
            "error": "",
            "elapsed_ms": ms,
        }
    except ImportError:
        # Graceful fallback: basic urllib validation
        from urllib.parse import urlparse
        parsed = urlparse(url)
        is_valid = bool(parsed.scheme in ("http", "https") and parsed.netloc)
        return {
            "provider": "courlan_fallback_urllib",
            "available": False,
            "success": is_valid,
            "canonical_url": url,
            "is_valid": is_valid,
            "error": "courlan not installed. Install: pip install courlan",
            "elapsed_ms": int((time.monotonic() - t0) * 1000),
        }
    except Exception as exc:
        return {
            "provider": "courlan",
            "available": True,
            "success": False,
            "canonical_url": url,
            "is_valid": False,
            "error": str(exc),
            "elapsed_ms": int((time.monotonic() - t0) * 1000),
        }


# ── deepdiff ──────────────────────────────────────────────────────────────────

def structured_diff(old: dict, new: dict) -> dict:
    """
    Compute a structured diff between two dicts using deepdiff.

    Falls back to basic key-level comparison if deepdiff is not installed.
    """
    t0 = time.monotonic()
    try:
        from deepdiff import DeepDiff
        diff = DeepDiff(old, new, ignore_order=True, verbose_level=0)
        ms = int((time.monotonic() - t0) * 1000)
        has_changes = bool(diff)
        return {
            "provider": "deepdiff",
            "available": True,
            "success": True,
            "has_changes": has_changes,
            "diff": diff.to_dict() if has_changes else {},
            "error": "",
            "elapsed_ms": ms,
        }
    except ImportError:
        # Fallback: shallow key comparison
        added = {k: new[k] for k in new if k not in old}
        removed = {k: old[k] for k in old if k not in new}
        changed = {k: {"old": old[k], "new": new[k]} for k in old if k in new and old[k] != new[k]}
        has_changes = bool(added or removed or changed)
        return {
            "provider": "deepdiff_fallback_shallow",
            "available": False,
            "success": True,
            "has_changes": has_changes,
            "diff": {"added": added, "removed": removed, "changed": changed},
            "error": "deepdiff not installed. Install: pip install deepdiff",
            "elapsed_ms": int((time.monotonic() - t0) * 1000),
        }
    except Exception as exc:
        return {
            "provider": "deepdiff",
            "available": True,
            "success": False,
            "has_changes": False,
            "diff": {},
            "error": str(exc),
            "elapsed_ms": int((time.monotonic() - t0) * 1000),
        }
