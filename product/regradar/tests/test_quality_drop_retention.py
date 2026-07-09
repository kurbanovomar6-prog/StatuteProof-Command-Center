"""F5 — QUALITY_DROP retention (owner decision, signal-max sprint).

Transition records (episode starts — previous same-source record was not
QUALITY_DROP) are kept forever. Steady-state repeats (consecutive
QUALITY_DROPs) older than the threshold are compacted like heartbeats:
last one per source per UTC day survives. Idempotent, atomic.

Real-trail split measured 2026-07-06: 122 QUALITY_DROP records =
103 transitions + 19 steady-state repeats.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

NOW = datetime(2026, 7, 5, 12, 0, 0, tzinfo=timezone.utc)


def _rec(source_id: str, ts: datetime, run_id: str, status: str) -> dict:
    return {
        "run_id": run_id,
        "source_id": source_id,
        "official_url": f"https://example.gov.ae/{source_id}",
        "change_status": status,
        "normalized_hash": "a" * 64,
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
    records = [
        # src-a: episode start (transition) then a run of old repeats over
        # two days, then recovery.
        _rec("src-a", old.replace(hour=1), "t1", "QUALITY_DROP"),      # transition — forever
        _rec("src-a", old.replace(hour=6), "r1", "QUALITY_DROP"),      # old repeat day1
        _rec("src-a", old.replace(hour=12), "r2", "QUALITY_DROP"),     # old repeat day1
        _rec("src-a", old.replace(hour=23), "r3", "QUALITY_DROP"),     # old repeat day1 (last-of-day)
        _rec("src-a", (old + timedelta(days=1)).replace(hour=9), "r4", "QUALITY_DROP"),  # day2 (last-of-day)
        _rec("src-a", (old + timedelta(days=1)).replace(hour=15), "rec1", "FIRST_SEEN"),  # recovery — forever
        # New episode after recovery → transition again, kept even though old.
        _rec("src-a", (old + timedelta(days=2)).replace(hour=9), "t2", "QUALITY_DROP"),
        # src-b: recent repeats (< 30 days) — all kept.
        _rec("src-b", NOW - timedelta(days=3, hours=2), "bt1", "QUALITY_DROP"),
        _rec("src-b", NOW - timedelta(days=3), "br1", "QUALITY_DROP"),
        _rec("src-b", NOW - timedelta(days=2), "br2", "QUALITY_DROP"),
    ]
    sr._RUN_FILE.write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n",
        encoding="utf-8",
    )
    sr._CACHE_VALID = False
    yield sr._RUN_FILE
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None


def _run_ids(path: Path) -> list[str]:
    return [json.loads(line)["run_id"] for line in path.read_text().splitlines() if line.strip()]


def test_transitions_kept_forever_repeats_compacted(trail):
    from app.retention import compact_quality_drop_repeats

    stats = compact_quality_drop_repeats(days_threshold=30, now=NOW)
    ids = _run_ids(trail)
    # transitions + recovery + new-episode transition survive
    for must_keep in ("t1", "rec1", "t2"):
        assert must_keep in ids, f"{must_keep} must be kept forever"
    # old repeats compacted to last-of-day: r3 (day1), r4 (day2) survive
    assert "r3" in ids and "r4" in ids
    assert "r1" not in ids and "r2" not in ids
    # recent records untouched
    for recent in ("bt1", "br1", "br2"):
        assert recent in ids
    assert stats["removed"] == 2


def test_idempotent(trail):
    from app.retention import compact_quality_drop_repeats

    compact_quality_drop_repeats(days_threshold=30, now=NOW)
    first = trail.read_bytes()
    stats = compact_quality_drop_repeats(days_threshold=30, now=NOW)
    assert trail.read_bytes() == first, "second run must be byte-identical"
    assert stats["removed"] == 0


def test_missing_file_safe(tmp_path, monkeypatch):
    import app.source_runs as sr
    from app.retention import compact_quality_drop_repeats

    monkeypatch.setattr(sr, "_RUN_DIR", tmp_path / "data" / "source_runs")
    monkeypatch.setattr(sr, "_RUN_FILE", tmp_path / "data" / "source_runs" / "source_runs.jsonl")
    assert compact_quality_drop_repeats(days_threshold=30, now=NOW) == {"kept": 0, "removed": 0}
