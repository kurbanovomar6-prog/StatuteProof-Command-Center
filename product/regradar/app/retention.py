"""
Evidence-trail retention (owner decision 1 + signal-max F5).

CHANGED / FIRST_SEEN / FAILED records are kept forever.
UNCHANGED heartbeat records older than `days_threshold` are compacted to one
per source per UTC day (the last one of that day survives — it carries the
same hash as the ones it replaces, so no evidence is lost, only repetition).

QUALITY_DROP (F5): transition records — episode starts, where the previous
same-source record was NOT QUALITY_DROP — are kept forever. Steady-state
repeats (consecutive QUALITY_DROPs) older than the threshold compact like
heartbeats: last one per source per UTC day survives.

Both jobs are idempotent: running twice produces a byte-identical file.
Rewrites are atomic (temp file + rename) under the same lock discipline as
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


def compact_quality_drop_repeats(days_threshold: int = 30, now: datetime | None = None) -> dict:
    """
    F5: compact steady-state QUALITY_DROP repeats older than the threshold.

    A QUALITY_DROP is a TRANSITION (kept forever) when the chronologically
    previous record for the same source is not QUALITY_DROP. Consecutive
    repeats older than `days_threshold` keep only the last one per source
    per UTC day. Returns {"kept": n, "removed": n}.
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

            # Pass 1: mark repeats (previous same-source record is also
            # QUALITY_DROP) — file order is append-only chronological.
            prev_status: dict[str, str] = {}
            is_repeat: dict[int, bool] = {}
            for idx, rec in enumerate(records):
                sid = str(rec.get("source_id"))
                status = str(rec.get("change_status") or "")
                if status == "QUALITY_DROP":
                    is_repeat[idx] = prev_status.get(sid) == "QUALITY_DROP"
                prev_status[sid] = status

            # Pass 2: among OLD repeats, the last per (source, utc-day) wins.
            last_of_day: dict[tuple, int] = {}
            for idx, rec in enumerate(records):
                if not is_repeat.get(idx):
                    continue
                ts = _parse_ts(rec.get("timestamp_utc"))
                if ts is None or ts >= cutoff:
                    continue
                last_of_day[(rec.get("source_id"), ts.date().isoformat())] = idx

            keep: list[int] = []
            for idx, rec in enumerate(records):
                if not is_repeat.get(idx):
                    keep.append(idx)  # non-QD and transitions: forever
                    continue
                ts = _parse_ts(rec.get("timestamp_utc"))
                if ts is None or ts >= cutoff:
                    keep.append(idx)
                    continue
                if last_of_day.get((rec.get("source_id"), ts.date().isoformat())) == idx:
                    keep.append(idx)

            removed = len(records) - len(keep)
            if removed > 0:
                tmp_path = run_file.with_suffix(".jsonl.qd-compact-tmp")
                with tmp_path.open("w", encoding="utf-8") as tmp:
                    for idx in keep:
                        tmp.write(lines[idx] + "\n")
                    tmp.flush()
                    os.fsync(tmp.fileno())
                os.replace(tmp_path, run_file)
                source_runs._CACHE_VALID = False
                source_runs._RUNS_CACHE = None
            logger.info(
                "QUALITY_DROP compaction: kept=%d removed=%d (threshold=%dd)",
                len(keep), removed, days_threshold,
            )
            return {"kept": len(keep), "removed": removed}
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


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
