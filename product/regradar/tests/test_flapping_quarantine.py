"""
Defect C (2026-07-11): flapping-source alert quarantine.

Eight sources (a DIFC cluster + FTA Corporate Tax + MoE AML) changed with a
NEW normalized_hash on consecutive monitoring cycles — dynamic page chrome, not
real regulatory change. The hash-dedup gate does NOT help because the hash is
different every sweep, so each flip fired a fresh HIGH/MEDIUM alert.

Policy: if a source produced CHANGED with a DISTINCT new normalized_hash for K
consecutive recent runs (default 3, env FLAPPING_MAX_CONSECUTIVE), suppress the
customer alert with reason "flapping_quarantine". A genuine single change
(streak < K) still alerts. A source that stabilised (same hash twice) then later
produced a real change alerts again.

Fixtures mirror tests/test_alert_dedup.py — monkeypatch source_runs paths to
tmp_path and write trail records directly as JSONL.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

NOW = datetime(2026, 7, 11, 14, 0, 0, tzinfo=timezone.utc)
SID = "AE-flapping-source"


@pytest.fixture
def trail(tmp_path, monkeypatch):
    import app.source_runs as sr
    monkeypatch.setattr(sr, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(sr, "_RUN_DIR", tmp_path / "data" / "source_runs")
    monkeypatch.setattr(sr, "_RUN_FILE", tmp_path / "data" / "source_runs" / "source_runs.jsonl")
    monkeypatch.setattr(sr, "_SNAPSHOT_DIR", tmp_path / "data" / "source_snapshots")
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None
    sr._RUN_DIR.mkdir(parents=True, exist_ok=True)
    yield sr
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None


def _write(sr, records):
    sr._RUN_FILE.write_text(
        "\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    sr._CACHE_VALID = False


def _rec(hash_, ts, *, alert_sent=False, status="CHANGED", source_id=SID):
    return {
        "run_id": f"r{abs(hash((hash_, ts))) % 10**8}",
        "source_id": source_id,
        "official_url": "https://example.gov.ae/x",
        "change_status": status,
        "normalized_hash": hash_,
        "alert_sent": alert_sent,
        "timestamp_utc": ts.isoformat(),
    }


def test_three_consecutive_distinct_hash_changes_are_quarantined(trail):
    """Two prior distinct-hash CHANGED runs + this new distinct hash = streak 3."""
    from app.alert_dedup import should_send_alert
    _write(trail, [
        _rec("a" * 64, NOW - timedelta(hours=6), status="FIRST_SEEN"),
        _rec("b" * 64, NOW - timedelta(hours=4)),  # distinct vs a
        _rec("c" * 64, NOW - timedelta(hours=2)),  # distinct vs b
    ])
    # new hash 'd' is distinct vs 'c' -> streak of 3 CHANGED distinct hashes
    ok, reason = should_send_alert(SID, "d" * 64, now=NOW)
    assert ok is False
    assert reason == "flapping_quarantine"


def test_single_genuine_change_still_alerts(trail):
    """A lone new hash after a stable history is a genuine change — must alert."""
    from app.alert_dedup import should_send_alert
    _write(trail, [
        _rec("a" * 64, NOW - timedelta(days=30), status="FIRST_SEEN"),
    ])
    ok, reason = should_send_alert(SID, "b" * 64, now=NOW)
    assert ok is True
    assert reason == ""


def test_two_consecutive_distinct_changes_not_yet_quarantined(trail):
    """Streak of 2 (< default K=3) is still a real change — must alert."""
    from app.alert_dedup import should_send_alert
    _write(trail, [
        _rec("a" * 64, NOW - timedelta(hours=4), status="FIRST_SEEN"),
        _rec("b" * 64, NOW - timedelta(hours=2)),  # distinct vs a
    ])
    # new hash 'c' distinct vs 'b' -> streak of 2, below threshold
    ok, reason = should_send_alert(SID, "c" * 64, now=NOW)
    assert ok is True
    assert reason == ""


def test_flapped_then_stabilised_then_real_change_alerts(trail):
    """
    Flapped (a,b,c distinct), then STABILISED (c repeated twice — same hash
    breaks the streak), then a later genuine change 'e'. The stabilisation
    resets the streak, so the real change must alert.
    """
    from app.alert_dedup import should_send_alert
    _write(trail, [
        _rec("a" * 64, NOW - timedelta(hours=10), status="FIRST_SEEN"),
        _rec("b" * 64, NOW - timedelta(hours=8)),   # distinct
        _rec("c" * 64, NOW - timedelta(hours=6)),   # distinct (flapping tip)
        _rec("c" * 64, NOW - timedelta(hours=4), status="UNCHANGED"),  # stabilised
        _rec("d" * 64, NOW - timedelta(hours=2)),   # one real change after stabilising
    ])
    # new hash 'e' distinct vs 'd'; the run before 'd' had the SAME hash 'd'?
    # No — 'd' is preceded by 'c' (UNCHANGED, same hash as the CHANGED 'c'),
    # which breaks the streak. So walking back: e(new)->d distinct (streak 2),
    # d's predecessor is the UNCHANGED 'c' run -> not CHANGED, streak stops at 2.
    ok, reason = should_send_alert(SID, "e" * 64, now=NOW)
    assert ok is True
    assert reason == ""


def test_repeated_same_hash_breaks_streak(trail):
    """
    Three CHANGED runs but the last two share a hash (source stabilised on b).
    A new distinct hash gives streak: new(1) -> b distinct (2) -> b same as
    previous b (stop). Streak 2 < 3 — must alert.
    """
    from app.alert_dedup import should_send_alert
    _write(trail, [
        _rec("a" * 64, NOW - timedelta(hours=6), status="FIRST_SEEN"),
        _rec("b" * 64, NOW - timedelta(hours=4)),  # distinct vs a
        _rec("b" * 64, NOW - timedelta(hours=2)),  # SAME as previous b
    ])
    ok, reason = should_send_alert(SID, "c" * 64, now=NOW)
    assert ok is True
    assert reason == ""


def test_flapping_threshold_configurable_via_env(trail, monkeypatch):
    """FLAPPING_MAX_CONSECUTIVE=2 quarantines a shorter streak."""
    from app.alert_dedup import should_send_alert
    monkeypatch.setenv("FLAPPING_MAX_CONSECUTIVE", "2")
    _write(trail, [
        _rec("a" * 64, NOW - timedelta(hours=4), status="FIRST_SEEN"),
        _rec("b" * 64, NOW - timedelta(hours=2)),  # distinct vs a
    ])
    # new hash 'c' distinct vs 'b' -> streak 2, meets K=2
    ok, reason = should_send_alert(SID, "c" * 64, now=NOW)
    assert ok is False
    assert reason == "flapping_quarantine"


def test_flapping_threshold_env_below_two_uses_default(trail, monkeypatch):
    """K<2 would silence every genuine change — clamp to the default (3)."""
    from app.alert_dedup import should_send_alert
    monkeypatch.setenv("FLAPPING_MAX_CONSECUTIVE", "1")
    _write(trail, [
        _rec("a" * 64, NOW - timedelta(days=30), status="FIRST_SEEN"),
    ])
    # single genuine change must NOT be quarantined despite the bad env value
    ok, reason = should_send_alert(SID, "b" * 64, now=NOW)
    assert ok is True
    assert reason == ""


def test_flapping_explicit_kwarg_overrides_env(trail):
    """The flapping_max_consecutive kwarg wins over the env default."""
    from app.alert_dedup import should_send_alert
    _write(trail, [
        _rec("a" * 64, NOW - timedelta(hours=4), status="FIRST_SEEN"),
        _rec("b" * 64, NOW - timedelta(hours=2)),
    ])
    ok, reason = should_send_alert(SID, "c" * 64, flapping_max_consecutive=2, now=NOW)
    assert ok is False and reason == "flapping_quarantine"


def test_flapping_is_per_source(trail):
    """Another source's flapping history does not quarantine this source."""
    from app.alert_dedup import should_send_alert
    _write(trail, [
        _rec("a" * 64, NOW - timedelta(hours=6), source_id="AE-other", status="FIRST_SEEN"),
        _rec("b" * 64, NOW - timedelta(hours=4), source_id="AE-other"),
        _rec("c" * 64, NOW - timedelta(hours=2), source_id="AE-other"),
    ])
    ok, reason = should_send_alert(SID, "d" * 64, now=NOW)
    assert ok is True
    assert reason == ""


def test_exact_hash_gate_precedes_flapping(trail):
    """
    A previously-alerted hash reappearing is deduped by hash_already_alerted,
    not reclassified as flapping (oscillation A->B->A case).
    """
    from app.alert_dedup import should_send_alert
    _write(trail, [
        _rec("a" * 64, NOW - timedelta(hours=6), alert_sent=True),
        _rec("b" * 64, NOW - timedelta(hours=4), alert_sent=True),
        _rec("c" * 64, NOW - timedelta(hours=2), alert_sent=True),
    ])
    ok, reason = should_send_alert(SID, "a" * 64, now=NOW)
    assert ok is False
    assert reason == "hash_already_alerted"
