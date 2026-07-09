"""
A1 (S1): duplicate alerting. Policy (owner):
- one alert per unique normalized_hash transition per source;
- a hash that has already been alerted for a source NEVER re-alerts
  (covers the DFSA title-oscillation A→B→A case from 2026-07-05);
- configurable cooldown (ALERT_COOLDOWN_HOURS, default 24h) between alerts
  for the same source even when the hash is new.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

NOW = datetime(2026, 7, 5, 14, 0, 0, tzinfo=timezone.utc)
SID = "AE-test-source"


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
        "run_id": f"r{abs(hash((hash_, ts)) ) % 10**8}",
        "source_id": source_id,
        "official_url": "https://example.gov.ae/x",
        "change_status": status,
        "normalized_hash": hash_,
        "alert_sent": alert_sent,
        "timestamp_utc": ts.isoformat(),
    }


def test_first_changed_hash_is_allowed(trail):
    from app.alert_dedup import should_send_alert
    _write(trail, [_rec("a" * 64, NOW - timedelta(days=3), status="FIRST_SEEN")])
    ok, reason = should_send_alert(SID, "b" * 64, now=NOW)
    assert ok is True and reason == ""


def test_same_hash_never_realerts(trail):
    from app.alert_dedup import should_send_alert
    _write(trail, [_rec("b" * 64, NOW - timedelta(days=5), alert_sent=True)])
    ok, reason = should_send_alert(SID, "b" * 64, now=NOW)
    assert ok is False
    assert reason == "hash_already_alerted"


def test_oscillation_back_to_previously_alerted_hash_is_suppressed(trail):
    """The 2026-07-05 case: A -> B (alerted) -> back to A (alerted before)."""
    from app.alert_dedup import should_send_alert
    _write(trail, [
        _rec("a" * 64, NOW - timedelta(days=6), alert_sent=True),
        _rec("b" * 64, NOW - timedelta(days=3), alert_sent=True),
    ])
    ok, reason = should_send_alert(SID, "a" * 64, now=NOW)
    assert ok is False and reason == "hash_already_alerted"


def test_new_hash_within_cooldown_is_suppressed(trail):
    from app.alert_dedup import should_send_alert
    _write(trail, [_rec("b" * 64, NOW - timedelta(minutes=34), alert_sent=True)])
    ok, reason = should_send_alert(SID, "c" * 64, now=NOW)
    assert ok is False and reason == "cooldown_active"


def test_new_hash_after_cooldown_is_allowed(trail):
    from app.alert_dedup import should_send_alert
    _write(trail, [_rec("b" * 64, NOW - timedelta(hours=25), alert_sent=True)])
    ok, reason = should_send_alert(SID, "c" * 64, now=NOW)
    assert ok is True


def test_cooldown_is_configurable_via_env(trail, monkeypatch):
    from app.alert_dedup import should_send_alert
    monkeypatch.setenv("ALERT_COOLDOWN_HOURS", "1")
    _write(trail, [_rec("b" * 64, NOW - timedelta(hours=2), alert_sent=True)])
    ok, _ = should_send_alert(SID, "c" * 64, now=NOW)
    assert ok is True, "2h old alert with 1h cooldown must not suppress"


def test_other_sources_do_not_interfere(trail):
    from app.alert_dedup import should_send_alert
    _write(trail, [_rec("b" * 64, NOW - timedelta(minutes=5), alert_sent=True,
                        source_id="AE-other-source")])
    ok, _ = should_send_alert(SID, "b" * 64, now=NOW)
    assert ok is True


# ── pipeline integration: second run with same hash sends nothing ───────────

_TEXT_V1 = "\n\n".join(f"Obligation paragraph {i}." for i in range(40))
_TEXT_V2 = "NEW penalty clause with sanction wording.\n\n" + _TEXT_V1

_SOURCE = {"name": "Dedup Source", "url": "https://example.gov.ae/dedup",
           "jurisdiction": "AE", "category": "aml", "enabled": True}


def test_pipeline_sends_once_then_suppresses_on_rerun(trail, tmp_path):
    from app.pipeline import init_pipeline, run_pipeline_for_source
    from app.text_normalization import normalize_for_change_hash, stable_content_hash
    import app.source_runs as sr

    v1_hash = stable_content_hash(normalize_for_change_hash(_TEXT_V1))
    # baseline record so the first run classifies CHANGED
    snap = tmp_path / "data" / "source_snapshots" / "2026-07-01" / "AE" / "AE-dedup-source" / "seed1"
    snap.mkdir(parents=True)
    (snap / "normalized.txt").write_text(normalize_for_change_hash(_TEXT_V1), encoding="utf-8")
    _write(trail, [{
        "run_id": "seed1", "source_id": "AE-dedup-source",
        "official_url": _SOURCE["url"], "url": _SOURCE["url"],
        "change_status": "FIRST_SEEN", "extraction_quality": "GOOD",
        "extracted_chars": len(_TEXT_V1), "normalized_chars": len(_TEXT_V1),
        "normalized_hash": v1_hash,
        "snapshot_normalized_path": "data/source_snapshots/2026-07-01/AE/AE-dedup-source/seed1/normalized.txt",
        "timestamp_utc": "2026-07-01T10:00:00+00:00",
    }])

    sends = []
    init_pipeline(0)
    # The alert path must not depend on the developer's .env — enable it
    # explicitly (hidden-dependency defect found in the signal-max sprint:
    # the test only passed when .env set ENABLE_TELEGRAM_ALERTS=true).
    with patch("app.pipeline.ENABLE_TELEGRAM_ALERTS", True), \
         patch("app.pipeline.fetch_page", return_value="<html>x</html>"), \
         patch("app.pipeline.extract_best_text", return_value={"text": _TEXT_V2, "method": "t"}), \
         patch("app.pipeline.get_latest_document", return_value={"content": _TEXT_V1, "content_hash": v1_hash}), \
         patch("app.pipeline.save_document", return_value=None), \
         patch("app.telegram.send_telegram_alert", side_effect=lambda p: sends.append(p) or True), \
         patch("app.pipeline.get_adapter_for_url", return_value=None):
        r1 = run_pipeline_for_source(_SOURCE)

    assert r1["changed"] is True
    assert len(sends) == 1, "first genuine change must alert exactly once"
    assert (r1.get("run_record") or {}).get("alert_sent") is True, \
        "trail must record that this run alerted"

    v2_hash = stable_content_hash(normalize_for_change_hash(_TEXT_V2))
    with patch("app.pipeline.ENABLE_TELEGRAM_ALERTS", True), \
         patch("app.pipeline.fetch_page", return_value="<html>x</html>"), \
         patch("app.pipeline.extract_best_text", return_value={"text": _TEXT_V2, "method": "t"}), \
         patch("app.pipeline.get_latest_document", return_value={"content": _TEXT_V2, "content_hash": v2_hash}), \
         patch("app.pipeline.save_document", return_value=None), \
         patch("app.telegram.send_telegram_alert", side_effect=lambda p: sends.append(p) or True), \
         patch("app.pipeline.get_adapter_for_url", return_value=None):
        r2 = run_pipeline_for_source(_SOURCE)

    assert r2["changed"] is False, "same hash re-run is unchanged (heartbeat)"
    assert len(sends) == 1, "re-run of the same hash must send ZERO new alerts"
