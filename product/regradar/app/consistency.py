"""
Baseline consistency check (owner decision 2).

The JSONL evidence trail is the single source of truth for content hashes;
SQLite `documents` is a derived index. This check detects divergence between
the two stores and logs it loudly. It NEVER heals anything — divergence means
a bug or manual interference and must be investigated by a human.

Called at API startup and scheduler startup.
"""

from __future__ import annotations

import logging

from app.db import get_latest_document
from app.source_runs import latest_runs

logger = logging.getLogger(__name__)


def check_baseline_consistency() -> list[dict]:
    """
    Compare the latest trail hash per source against the latest SQLite
    documents hash for the same URL.

    Returns a list of divergences (empty = consistent). Sources whose trail
    records carry no hash (legacy pre-fix history) are skipped — they are
    documented history, not divergence. URLs with no SQLite row are skipped:
    the derived index is populated lazily on the next run.
    """
    divergences: list[dict] = []
    checked = 0

    for source_id, record in latest_runs().items():
        trail_hash = record.get("normalized_hash") or record.get("content_hash")
        if not trail_hash:
            continue  # legacy record without hash — documented history
        url = record.get("official_url") or record.get("url")
        if not url:
            continue
        doc = get_latest_document(url)
        if doc is None:
            continue  # derived index not yet populated for this source
        sqlite_hash = doc["content_hash"]
        checked += 1
        if sqlite_hash and sqlite_hash != trail_hash:
            divergence = {
                "source_id": source_id,
                "url": url,
                "jsonl_hash": trail_hash,
                "sqlite_hash": sqlite_hash,
                "trail_timestamp": record.get("timestamp_utc"),
            }
            divergences.append(divergence)
            logger.error(
                "BASELINE DIVERGENCE: source=%s jsonl=%s sqlite=%s url=%s — "
                "evidence trail is authoritative; investigate before trusting "
                "change classifications for this source",
                source_id, trail_hash[:12], str(sqlite_hash)[:12], url,
            )

    if divergences:
        logger.error(
            "BASELINE DIVERGENCE TOTAL: %d of %d checked source(s) diverged. "
            "No auto-heal performed.",
            len(divergences), checked,
        )
    else:
        logger.info(
            "Baseline consistency: OK (%d source(s) with comparable hashes)",
            checked,
        )
    return divergences
