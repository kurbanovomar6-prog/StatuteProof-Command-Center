"""
A-durability keystone tests.

The product promise is that a durable evidence record backs every customer
alert. These tests lock the invariant "alert sent can NEVER outrun evidence
recorded" plus the scraper-break shrink guard:

(i)   a CHANGED run whose append_run() fails must NOT send a Telegram alert and
      must report telegram_sent=False (no alert without durable evidence);
(ii)  _locked_append_line() fsyncs the record to disk before returning
      (durability of the append itself);
(iii) a large content shrink (likely scraper break) suppresses the alert AND
      does not overwrite the baseline (no save_document of shrunk content, no
      superseding trail record);
(iv)  a normal CHANGED run still alerts exactly once AND records the evidence
      BEFORE it sends (correct ordering on the happy path).

Hermetic: no network, no real Telegram. Fetch/extract/db/telegram patched and
the evidence trail redirected to tmp_path.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from app.text_normalization import normalize_for_change_hash, stable_content_hash

# Baseline content (large) and a genuine, risk-bearing CHANGED body.
_BASE_TEXT = "\n\n".join(f"Regulatory obligation paragraph {i}." for i in range(80))
_CHANGED_TEXT = (
    "NEW penalty clause: a sanction and fine apply for non-compliance.\n\n"
    + _BASE_TEXT
)
_HTML = "<html><body>irrelevant — extract is patched</body></html>"

_BASE_HASH = stable_content_hash(normalize_for_change_hash(_BASE_TEXT))

_SOURCE = {
    "name": "Durability Source",
    "url": "https://example.gov.ae/durability",
    "jurisdiction": "AE",
    "category": "financial_regulator",
    "enabled": True,
}
_SOURCE_ID = "AE-durability-source"


@pytest.fixture
def isolated_dirs(tmp_path, monkeypatch):
    import app.source_runs as sr

    monkeypatch.setattr(sr, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(sr, "_RUN_DIR", tmp_path / "data" / "source_runs")
    monkeypatch.setattr(sr, "_RUN_FILE", tmp_path / "data" / "source_runs" / "source_runs.jsonl")
    monkeypatch.setattr(sr, "_SNAPSHOT_DIR", tmp_path / "data" / "source_snapshots")
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None
    sr._RUN_DIR.mkdir(parents=True, exist_ok=True)
    yield tmp_path
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None


def _seed_baseline(
    tmp_path,
    normalized_hash: str,
    *,
    text: str = "old text",
    extracted_chars: int = 3000,
    normalized_chars: int = 2600,
) -> None:
    """Seed a FIRST_SEEN baseline record + snapshot so the next run is a diff."""
    import app.source_runs as sr

    snap_dir = tmp_path / "data" / "source_snapshots" / "2026-06-20" / "AE" / _SOURCE_ID / "seed0001"
    snap_dir.mkdir(parents=True, exist_ok=True)
    (snap_dir / "normalized.txt").write_text(text, encoding="utf-8")
    sr._RUN_FILE.write_text(
        json.dumps(
            {
                "run_id": "seed0001",
                "source_id": _SOURCE_ID,
                "official_url": _SOURCE["url"],
                "url": _SOURCE["url"],
                "change_status": "FIRST_SEEN",
                "extraction_quality": "GOOD",
                "extracted_chars": extracted_chars,
                "normalized_chars": normalized_chars,
                "normalized_hash": normalized_hash,
                "raw_hash": "e" * 64,
                "snapshot_normalized_path": (
                    "data/source_snapshots/2026-06-20/AE/AE-durability-source/seed0001/normalized.txt"
                ),
                "timestamp_utc": "2026-06-20T10:00:00+00:00",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    sr._CACHE_VALID = False


def _trail_records():
    import app.source_runs as sr

    if not sr._RUN_FILE.exists():
        return []
    return [
        json.loads(line)
        for line in sr._RUN_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


# ══════════════════════════════════════════════════════════════════════════
# (i) A CHANGED run whose append_run fails must NOT send an alert
# ══════════════════════════════════════════════════════════════════════════
def test_changed_run_with_failed_append_does_not_alert(isolated_dirs):
    """
    The keystone invariant: if the evidence append fails, no alert may go out
    and telegram_sent must be False. Otherwise "alert sent" outran
    "evidence recorded".
    """
    from app.pipeline import init_pipeline, run_pipeline_for_source

    _seed_baseline(isolated_dirs, _BASE_HASH)
    init_pipeline(0)

    sends: list = []

    def _boom(*_a, **_k):
        raise RuntimeError("disk full — append_run failed")

    with patch("app.pipeline.ENABLE_TELEGRAM_ALERTS", True), patch(
        "app.pipeline.fetch_page", return_value=_HTML
    ), patch(
        "app.pipeline.extract_best_text", return_value={"text": _CHANGED_TEXT, "method": "t"}
    ), patch(
        "app.pipeline.get_latest_document", return_value={"content": _BASE_TEXT, "content_hash": _BASE_HASH}
    ), patch(
        "app.pipeline.save_document", return_value=None
    ), patch(
        "app.telegram.send_telegram_alert", side_effect=lambda p: sends.append(p) or True
    ), patch(
        "app.pipeline.get_adapter_for_url", return_value=None
    ), patch(
        "app.source_runs.append_run", side_effect=_boom
    ):
        result = run_pipeline_for_source(_SOURCE)

    assert result["changed"] is True, "run itself detected a change"
    assert sends == [], "a failed evidence append must NOT let an alert go out"
    assert result.get("telegram_sent") is False, (
        "telegram_sent must stay False when evidence was not durably recorded"
    )
    # No CHANGED record landed in the trail (append raised) — baseline intact.
    records = _trail_records()
    assert all(r.get("change_status") != "CHANGED" for r in records), (
        "no CHANGED evidence should be persisted when the append failed"
    )


# ══════════════════════════════════════════════════════════════════════════
# (ii) _locked_append_line fsyncs the record before returning
# ══════════════════════════════════════════════════════════════════════════
def test_locked_append_line_fsyncs(isolated_dirs):
    import app.source_runs as sr

    fsynced_fds: list = []
    real_fsync = sr.os.fsync

    def _spy_fsync(fd):
        fsynced_fds.append(fd)
        return real_fsync(fd)

    with patch.object(sr.os, "fsync", side_effect=_spy_fsync):
        sr._locked_append_line(
            json.dumps({"source_id": _SOURCE_ID, "change_status": "CHANGED", "n": 1}) + "\n"
        )

    assert fsynced_fds, "os.fsync must be called so the evidence record is durable on disk"
    # And the record actually landed.
    records = _trail_records()
    assert any(r.get("change_status") == "CHANGED" and r.get("n") == 1 for r in records)


def test_locked_append_line_fsyncs_on_relock_fallback(isolated_dirs):
    """The last-ditch fallback path must fsync too."""
    import app.source_runs as sr

    fsynced_fds: list = []
    real_fsync = sr.os.fsync

    def _spy_fsync(fd):
        fsynced_fds.append(fd)
        return real_fsync(fd)

    # Force every relock attempt to see an inode mismatch so the loop exhausts
    # and the code drops into the last-ditch fallback append.
    real_stat = sr.os.stat

    class _FakeStat:
        st_ino = -12345  # never equals a real fd inode

    def _mismatch_stat(path, *a, **k):
        if str(path) == str(sr._RUN_FILE):
            return _FakeStat()
        return real_stat(path, *a, **k)

    with patch.object(sr.os, "stat", side_effect=_mismatch_stat), patch.object(
        sr.os, "fsync", side_effect=_spy_fsync
    ):
        sr._locked_append_line(
            json.dumps({"source_id": _SOURCE_ID, "change_status": "CHANGED", "n": 2}) + "\n"
        )

    assert fsynced_fds, "fallback append path must also fsync the record"
    records = _trail_records()
    assert any(r.get("change_status") == "CHANGED" and r.get("n") == 2 for r in records)


# ══════════════════════════════════════════════════════════════════════════
# (iii) A large content shrink suppresses the alert and keeps the baseline
# ══════════════════════════════════════════════════════════════════════════
# A truncated fetch: real regulatory paragraphs, but only a fraction of the
# baseline (≈10% of the length) — passes the error-page/unreadable guards yet
# trips the content-shrink guard. This is the scraper-break shape we must catch.
_SHRUNK_TEXT = "\n\n".join(f"Regulatory obligation paragraph {i}." for i in range(8))


def test_content_shrink_suppresses_alert_and_preserves_baseline(isolated_dirs):
    """
    A drastic content-length drop (scraper break) must: send no alert, not call
    save_document with the shrunk content, and not append a superseding trail
    record — the true baseline hash survives for the next healthy sweep.
    """
    from app.pipeline import init_pipeline, run_pipeline_for_source

    # Baseline is large; the fetched body this run is tiny (~40 chars).
    _seed_baseline(
        isolated_dirs,
        _BASE_HASH,
        text=normalize_for_change_hash(_BASE_TEXT),
        extracted_chars=len(_BASE_TEXT),
        normalized_chars=len(normalize_for_change_hash(_BASE_TEXT)),
    )
    init_pipeline(0)

    sends: list = []
    saved: list = []

    def _capture_save(url, content, content_hash=None, **kw):
        saved.append({"url": url, "content": content, "content_hash": content_hash})

    with patch("app.pipeline.ENABLE_TELEGRAM_ALERTS", True), patch(
        "app.pipeline.fetch_page", return_value=_HTML
    ), patch(
        "app.pipeline.extract_best_text", return_value={"text": _SHRUNK_TEXT, "method": "t"}
    ), patch(
        "app.pipeline.get_latest_document", return_value={"content": _BASE_TEXT, "content_hash": _BASE_HASH}
    ), patch(
        "app.pipeline.save_document", side_effect=_capture_save
    ), patch(
        "app.telegram.send_telegram_alert", side_effect=lambda p: sends.append(p) or True
    ), patch(
        "app.pipeline.get_adapter_for_url", return_value=None
    ):
        result = run_pipeline_for_source(_SOURCE)

    assert sends == [], "a shrunk (scraper-break) run must not alert"
    assert result.get("shrink_suppressed") is True
    assert result.get("changed") is False, "shrink is treated as a non-change (quality drop)"
    # save_document must NOT have persisted the shrunk content.
    shrunk_saves = [s for s in saved if _SHRUNK_TEXT in (s.get("content") or "")]
    assert shrunk_saves == [], "shrunk content must never overwrite the baseline in SQLite"
    # The trail must NOT gain a superseding CHANGED record — baseline hash stands.
    records = _trail_records()
    assert all(r.get("change_status") != "CHANGED" for r in records)
    latest_hash = records[-1].get("normalized_hash") if records else None
    assert latest_hash == _BASE_HASH, "the true baseline hash must survive the scraper break"


# ══════════════════════════════════════════════════════════════════════════
# (iv) A normal CHANGED run alerts once AND records evidence BEFORE sending
# ══════════════════════════════════════════════════════════════════════════
def test_normal_changed_run_records_evidence_before_alert(isolated_dirs):
    from app.pipeline import init_pipeline, run_pipeline_for_source
    import app.source_runs as sr

    _seed_baseline(isolated_dirs, _BASE_HASH)
    init_pipeline(0)

    order: list = []
    real_append = sr.append_run

    def _record_append(record):
        order.append("append")
        return real_append(record)

    def _record_send(payload):
        order.append("send")
        return True

    with patch("app.pipeline.ENABLE_TELEGRAM_ALERTS", True), patch(
        "app.pipeline.fetch_page", return_value=_HTML
    ), patch(
        "app.pipeline.extract_best_text", return_value={"text": _CHANGED_TEXT, "method": "t"}
    ), patch(
        "app.pipeline.get_latest_document", return_value={"content": _BASE_TEXT, "content_hash": _BASE_HASH}
    ), patch(
        "app.pipeline.save_document", return_value=None
    ), patch(
        "app.source_runs.append_run", side_effect=_record_append
    ), patch(
        "app.telegram.send_telegram_alert", side_effect=_record_send
    ), patch(
        "app.pipeline.get_adapter_for_url", return_value=None
    ):
        result = run_pipeline_for_source(_SOURCE)

    assert result["changed"] is True
    assert result.get("telegram_sent") is True, "a genuine change must alert"
    assert order == ["append", "send"], (
        f"evidence must be appended BEFORE the alert is sent; got order={order}"
    )
    # The durable CHANGED record carries alert_sent=True (A1 dedup state).
    changed = [r for r in _trail_records() if r.get("change_status") == "CHANGED"]
    assert len(changed) == 1, "exactly one CHANGED evidence record must be recorded"
    assert changed[0].get("alert_sent") is True, (
        "the persisted evidence record must mark that this run alerted"
    )


def test_moderate_removal_still_alerts_not_suppressed(isolated_dirs):
    """
    A genuine 'content removed' change that stays ABOVE the shrink thresholds
    (raw > 40%, normalized > 70% of baseline) must NOT be suppressed — the guard
    only catches scraper breaks, not real regulatory removals.
    """
    from app.pipeline import init_pipeline, run_pipeline_for_source

    # Baseline of 80 paragraphs; this run drops to 65 (~81% of raw, ~81% norm)
    # AND adds risk-bearing wording so it classifies MEDIUM/HIGH.
    moderate = (
        "NEW penalty clause: a sanction and fine apply for non-compliance.\n\n"
        + "\n\n".join(f"Regulatory obligation paragraph {i}." for i in range(65))
    )
    _seed_baseline(
        isolated_dirs,
        _BASE_HASH,
        text=normalize_for_change_hash(_BASE_TEXT),
        extracted_chars=len(_BASE_TEXT),
        normalized_chars=len(normalize_for_change_hash(_BASE_TEXT)),
    )
    init_pipeline(0)

    sends: list = []
    with patch("app.pipeline.ENABLE_TELEGRAM_ALERTS", True), patch(
        "app.pipeline.fetch_page", return_value=_HTML
    ), patch(
        "app.pipeline.extract_best_text", return_value={"text": moderate, "method": "t"}
    ), patch(
        "app.pipeline.get_latest_document", return_value={"content": _BASE_TEXT, "content_hash": _BASE_HASH}
    ), patch(
        "app.pipeline.save_document", return_value=None
    ), patch(
        "app.telegram.send_telegram_alert", side_effect=lambda p: sends.append(p) or True
    ), patch(
        "app.pipeline.get_adapter_for_url", return_value=None
    ):
        result = run_pipeline_for_source(_SOURCE)

    assert result.get("shrink_suppressed") is not True, "moderate removal is a real change"
    assert result["changed"] is True
    assert len(sends) == 1, "a genuine above-threshold change must still alert"


def test_detect_content_shrink_thresholds():
    """Unit-lock the shrink thresholds (mirror classify_change's QUALITY_DROP)."""
    from app.pipeline import _detect_content_shrink

    # Raw drop below 40% trips.
    assert _detect_content_shrink(
        prev_raw_chars=1000, prev_normalized_chars=900,
        new_raw_chars=300, new_normalized_chars=800,
    )
    # Normalized drop below 70% trips even if raw is fine.
    assert _detect_content_shrink(
        prev_raw_chars=1000, prev_normalized_chars=1000,
        new_raw_chars=900, new_normalized_chars=600,
    )
    # Just above both thresholds — no trip.
    assert _detect_content_shrink(
        prev_raw_chars=1000, prev_normalized_chars=1000,
        new_raw_chars=500, new_normalized_chars=800,
    ) is None
    # No known previous size — never trips (first run / missing data).
    assert _detect_content_shrink(
        prev_raw_chars=None, prev_normalized_chars=None,
        new_raw_chars=1, new_normalized_chars=1,
    ) is None
    assert _detect_content_shrink(
        prev_raw_chars=0, prev_normalized_chars=0,
        new_raw_chars=1, new_normalized_chars=1,
    ) is None


def test_normal_changed_run_alerts_exactly_once(isolated_dirs):
    """A durable CHANGED run sends exactly one alert (no double-fire)."""
    from app.pipeline import init_pipeline, run_pipeline_for_source

    _seed_baseline(isolated_dirs, _BASE_HASH)
    init_pipeline(0)

    sends: list = []
    with patch("app.pipeline.ENABLE_TELEGRAM_ALERTS", True), patch(
        "app.pipeline.fetch_page", return_value=_HTML
    ), patch(
        "app.pipeline.extract_best_text", return_value={"text": _CHANGED_TEXT, "method": "t"}
    ), patch(
        "app.pipeline.get_latest_document", return_value={"content": _BASE_TEXT, "content_hash": _BASE_HASH}
    ), patch(
        "app.pipeline.save_document", return_value=None
    ), patch(
        "app.telegram.send_telegram_alert", side_effect=lambda p: sends.append(p) or True
    ), patch(
        "app.pipeline.get_adapter_for_url", return_value=None
    ):
        run_pipeline_for_source(_SOURCE)

    assert len(sends) == 1, "a genuine change must alert exactly once"
