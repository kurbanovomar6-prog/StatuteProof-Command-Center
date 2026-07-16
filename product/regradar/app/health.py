"""
RegRadar v6 — source health check.

run_source_health_check() tests every source in sources.json —
enabled AND disabled — for extraction quality.

Rules:
- Never writes to the database.
- Never calls AI analysis.
- Never sends Telegram alerts.
- Uses the same adapter registry + scraper as the main pipeline.
- One failed source never aborts the rest.
"""

import logging
from typing import Any

from app.adapters.base import is_quality_content
from app.adapters.registry import get_adapter_for_url
from app.extractors import extract_best_text
from app.scraper import fetch_page
from app.sources import load_sources

logger = logging.getLogger(__name__)

# Source statuses that are externally restricted — shown as SKIP with a note
_SKIP_STATUSES: frozenset[str] = frozenset({
    "disabled_external_access",   # geo-block / JS SPA zero-extraction / protocol error
    "disabled_navigation_only",   # SPA returns only navigation/menu text
})


# ── helpers ───────────────────────────────────────────────────────────────────

def _quality_label(chars: int) -> str:
    if chars >= 500:
        return "good"
    if chars > 0:
        return "low_content"
    return "failed"


def _verdict(source: dict, quality: str, has_error: bool) -> str:
    enabled    = source.get("enabled", False)
    src_status = source.get("status", "active")

    if not enabled:
        return "SKIP"
    if has_error:
        return "FAIL"
    if quality == "good":
        return "PASS"
    # low_content OR status == limited → warn, not fail
    if quality == "low_content" or src_status == "limited":
        return "WARN"
    return "FAIL"


def _check_one(source: dict) -> dict[str, Any]:
    """
    Test a single source and return a health record. Never raises.
    """
    url  = source.get("url", "")
    name = source.get("name", url)

    record: dict[str, Any] = {
        "name":               name,
        "jurisdiction":       source.get("jurisdiction", ""),
        "category":           source.get("category", ""),
        "enabled":            source.get("enabled", False),
        "status":             source.get("status", "active"),
        "extracted_chars":    0,
        "extraction_quality": "failed",
        "extraction_method":  "none",
        "verdict":            "FAIL",
        "error":              None,
    }

    try:
        content: str | None = None
        method = "generic"

        # ── Step 0: try adapter (mirrors pipeline step 0) ─────────────
        adapter = get_adapter_for_url(url, source)
        if adapter is not None:
            try:
                adapter_text = adapter.fetch_content(url, source)
            except Exception as exc:
                logger.debug("Health: adapter %r error for %s: %s",
                             adapter.name, name, exc)
                adapter_text = None

            if is_quality_content(adapter_text):
                content = adapter_text
                method  = f"adapter:{adapter.name}"

        # ── Steps 1-2: generic scraper fallback ───────────────────────
        if content is None:
            html    = fetch_page(url, allow_proxy=True)
            _extr   = extract_best_text(html, url)
            content = _extr["text"]
            method  = _extr["method"]

        chars   = len(content) if content else 0
        quality = _quality_label(chars)

        record["extracted_chars"]    = chars
        record["extraction_quality"] = quality
        record["extraction_method"]  = method
        record["verdict"]            = _verdict(source, quality, False)

    except Exception as exc:
        error_msg = f"{type(exc).__name__}: {exc}"
        logger.warning("Health check failed for %s: %s", name, error_msg)
        record["error"]   = error_msg
        record["verdict"] = _verdict(source, "failed", True)

    return record


# ── public API ────────────────────────────────────────────────────────────────

def run_source_health_check() -> list[dict]:
    """
    Run a diagnostic fetch against every source in sources.json.

    Returns one health record per source, in file order.
    Both enabled and disabled sources are checked.

    No database writes, no AI calls, no Telegram alerts.
    """
    sources = load_sources()
    if not sources:
        logger.warning("Health check: no sources found in sources.json")
        return []

    total   = len(sources)
    results = []

    for idx, source in enumerate(sources, 1):
        name       = source.get("name", source.get("url", "?"))
        src_status = source.get("status", "active")
        if source.get("enabled"):
            enabled_marker = "enabled"
        elif src_status in _SKIP_STATUSES:
            enabled_marker = f"restricted:{src_status}"
        else:
            enabled_marker = "disabled"
        print(
            f"  [{idx}/{total}] {name[:50]}  ({enabled_marker}) ...",
            flush=True,
        )

        record = _check_one(source)
        results.append(record)

        verdict = record["verdict"]
        chars   = record["extracted_chars"]
        quality = record["extraction_quality"]
        method  = record["extraction_method"]
        error   = record.get("error")

        if error:
            print(f"         → {verdict}  ERROR: {error[:60]}", flush=True)
        else:
            print(
                f"         → {verdict}  {chars:,}c  {quality}"
                f"  [{method}]",
                flush=True,
            )

    return results
