"""
Owner decision 1 (retention): CHANGED records are kept forever; unchanged
heartbeats older than 30 days are compacted to one per day per source.
The compaction job must be idempotent — running it twice yields the same file.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

NOW = datetime(2026, 7, 5, 12, 0, 0, tzinfo=timezone.utc)


def _hb(source_id: str, ts: datetime, run_id: str) -> dict:
    return {
        "record_type": "heartbeat",
        "run_id": run_id,
        "source_id": source_id,
        "official_url": f"https://example.gov.ae/{source_id}",
        "change_status": "UNCHANGED",
        "normalized_hash": "a" * 64,
        "timestamp_utc": ts.isoformat(),
    }


def _changed(source_id: str, ts: datetime, run_id: str) -> dict:
    return {
        "run_id": run_id,
        "source_id": source_id,
        "official_url": f"https://example.gov.ae/{source_id}",
        "change_status": "CHANGED",
        "normalized_hash": "b" * 64,
        "timestamp_utc": ts.isoformat(),
    }


@pytest.fixture
def trail(tmp_path, monkeypatch):
    import app.source_runs as sr
    monkeypatch.setattr(sr, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(sr, "_RUN_DIR", tmp_path / "data" / "source_runs")
    monkeypatch.setattr(sr, "_RUN_FILE", tmp_path / "data" / "source_runs" / "source_runs.jsonl")
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None
    sr._RUN_DIR.mkdir(parents=True, exist_ok=True)

    old = NOW - timedelta(days=45)
    # Append-only trail ⇒ strictly chronological, sources interleaved.
    records = [
        _hb("src-b", old.replace(hour=1), "b1"),
        _hb("src-b", old.replace(hour=2), "b2"),
        # FAILED records are never dropped
        {**_changed("src-b", old.replace(hour=3), "bf1"), "change_status": "FAILED"},
        # Old day 1: three heartbeats for src-a → keep only the LAST of the day
        _hb("src-a", old.replace(hour=6), "a1"),
        _hb("src-a", old.replace(hour=12), "a2"),
        # A CHANGED record — kept forever
        _changed("src-a", old.replace(hour=15), "ac1"),
        _hb("src-a", old.replace(hour=23), "a3"),
        # Old day 2 for src-a: single heartbeat → kept
        _hb("src-a", (old + timedelta(days=1)).replace(hour=9), "a4"),
        # Recent heartbeats (< 30 days) → all kept
        _hb("src-a", NOW - timedelta(days=2, hours=3), "a6"),
        _hb("src-a", NOW - timedelta(days=2), "a5"),
    ]
    sr._RUN_FILE.write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n",
        encoding="utf-8",
    )
    sr._CACHE_VALID = False
    yield sr._RUN_FILE
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None


def _load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()]


def test_compaction_keeps_changed_and_recent_drops_old_duplicates(trail):
    from app.retention import compact_heartbeats

    stats = compact_heartbeats(days_threshold=30, now=NOW)
    records = _load(trail)
    ids = [r["run_id"] for r in records]

    # CHANGED + FAILED kept forever
    assert "ac1" in ids and "bf1" in ids
    # Old day with 3 heartbeats → only the last of that day survives
    assert "a3" in ids and "a1" not in ids and "a2" not in ids
    # Single old heartbeat on its own day survives
    assert "a4" in ids
    # src-b old duplicates → last kept
    assert "b2" in ids and "b1" not in ids
    # Recent heartbeats untouched
    assert "a5" in ids and "a6" in ids
    # Stats are truthful
    assert stats["removed"] == 3
    assert stats["kept"] == len(records)


def test_compaction_is_idempotent(trail):
    from app.retention import compact_heartbeats

    compact_heartbeats(days_threshold=30, now=NOW)
    first = trail.read_text(encoding="utf-8")
    stats2 = compact_heartbeats(days_threshold=30, now=NOW)
    second = trail.read_text(encoding="utf-8")

    assert first == second, "second run must be a byte-identical no-op"
    assert stats2["removed"] == 0


def test_compaction_preserves_chronological_order(trail):
    from app.retention import compact_heartbeats

    compact_heartbeats(days_threshold=30, now=NOW)
    records = _load(trail)
    stamps = [r["timestamp_utc"] for r in records]
    assert stamps == sorted(stamps), "trail must stay chronologically ordered"


def test_compaction_never_touches_non_heartbeat_records(trail):
    from app.retention import compact_heartbeats

    before = [r for r in _load(trail) if r.get("record_type") != "heartbeat"]
    compact_heartbeats(days_threshold=30, now=NOW)
    after = [r for r in _load(trail) if r.get("record_type") != "heartbeat"]
    assert before == after
