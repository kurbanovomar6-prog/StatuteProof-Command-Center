"""
Evidence-trail retention (owner decision 1).

CHANGED / FIRST_SEEN / FAILED / QUALITY_DROP records are kept forever.
UNCHANGED heartbeat records older than `days_threshold` are compacted to one
per source per UTC day (the last one of that day survives — it carries the
same hash as the ones it replaces, so no evidence is lost, only repetition).

The job is idempotent: running it twice produces a byte-identical file.
The rewrite is atomic (temp file + rename) under the same lock discipline as
append_run, so a concurrent monitor run cannot interleave a partial file.
"""

from __future__ import annotations

import fcntl
import json
import logging
import os
from datetime import datetime, timedelta, timezone

import app.source_runs as source_runs

logger = logging.getLogger(__name__)

_KEEP_FOREVER = {"CHANGED", "FIRST_SEEN", "FAILED", "QUALITY_DROP"}


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts


def compact_heartbeats(days_threshold: int = 30, now: datetime | None = None) -> dict:
    """
    Compact old heartbeats in the run trail. Returns {"kept": n, "removed": n}.

    Only records with record_type == "heartbeat" are ever candidates for
    removal; anything else — including records with unparseable timestamps —
    is kept unconditionally.
    """
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days_threshold)
    run_file = source_runs.source_run_path()
    if not run_file.exists():
        return {"kept": 0, "removed": 0}

    with run_file.open("r+", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            lines = fh.read().splitlines()
            records = [json.loads(line) for line in lines if line.strip()]

            # Last old heartbeat per (source_id, utc-date) survives.
            last_of_day: dict[tuple, int] = {}
            for idx, rec in enumerate(records):
                if rec.get("record_type") != "heartbeat":
                    continue
                ts = _parse_ts(rec.get("timestamp_utc"))
                if ts is None or ts >= cutoff:
                    continue
                key = (rec.get("source_id"), ts.date().isoformat())
                last_of_day[key] = idx  # later index wins

            keep: list[int] = []
            for idx, rec in enumerate(records):
                if rec.get("record_type") != "heartbeat":
                    keep.append(idx)
                    continue
                if rec.get("change_status") in _KEEP_FOREVER:
                    keep.append(idx)  # defensive: misclassified heartbeat
                    continue
                ts = _parse_ts(rec.get("timestamp_utc"))
                if ts is None or ts >= cutoff:
                    keep.append(idx)
                    continue
                key = (rec.get("source_id"), ts.date().isoformat())
                if last_of_day.get(key) == idx:
                    keep.append(idx)

            removed = len(records) - len(keep)
            if removed > 0:
                tmp_path = run_file.with_suffix(".jsonl.compact-tmp")
                with tmp_path.open("w", encoding="utf-8") as tmp:
                    for idx in keep:
                        tmp.write(lines[idx] + "\n")
                    tmp.flush()
                    os.fsync(tmp.fileno())
                os.replace(tmp_path, run_file)
                source_runs._CACHE_VALID = False
                source_runs._RUNS_CACHE = None
            logger.info(
                "Heartbeat compaction: kept=%d removed=%d (threshold=%dd)",
                len(keep), removed, days_threshold,
            )
            return {"kept": len(keep), "removed": removed}
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)
