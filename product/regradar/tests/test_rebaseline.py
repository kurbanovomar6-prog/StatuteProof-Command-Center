"""
Defect D — rebaseline(source_id) primitive.

Repairing a poisoned baseline (VARA mojibake incident, 2026-07-10) must not
require stopping the scheduler or running a full suppressed cycle. These tests
prove the single-source primitive:

  1. clean content  -> a fresh FIRST_SEEN baseline record with a new normalized
     hash is appended, no alert queued;
  2. mojibake body  -> refused, NOTHING appended to the trail;
  3. unknown id     -> clean error result, NOTHING appended;
  4. thin content   -> refused by the quality gate, NOTHING appended.

Fixture pattern (trail -> tmp_path) and fetch/extract seams
(app.pipeline.fetch_page / app.pipeline.extract_best_text) mirror
tests/test_alert_dedup.py.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

_SOURCE = {
    "name": "Rebaseline Source",
    "url": "https://example.gov.ae/rebaseline",
    "jurisdiction": "AE",
    "category": "aml",
    "enabled": True,
}

# >= 2000 chars AND >= 3 paragraphs so it passes the pipeline quality gate
# and classifies as GOOD (record_from_source_result GOOD threshold is 2000).
_CLEAN_TEXT = "\n\n".join(
    f"Obligation paragraph {i}: licensed entities must maintain records "
    f"and report material changes to the regulator within the stated period."
    for i in range(24)
)

# The mojibake signature: saturated with U+FFFD replacement characters.
_MOJIBAKE_TEXT = ("�" * 400) + "some stray latin letters here and there abcdef"

# Passes is_mostly_unreadable (readable) but is too thin for the quality gate.
_THIN_TEXT = "Short notice."


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
    # Make exactly one source resolvable by id, without touching real sources.json.
    monkeypatch.setattr("app.sources.load_sources", lambda *a, **k: [_SOURCE])
    yield sr
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None


def _source_id(sr) -> str:
    return sr.make_source_id(_SOURCE)


def _trail_lines(sr) -> list[str]:
    if not sr._RUN_FILE.exists():
        return []
    return [ln for ln in sr._RUN_FILE.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _queued_alerts(sr) -> list[Path]:
    queue_dir = sr._BASE_DIR / "data" / "alert_queue"
    return list(queue_dir.glob("*.json")) if queue_dir.exists() else []


def test_rebaseline_writes_new_baseline_for_known_source(trail):
    sid = _source_id(trail)
    with patch("app.pipeline.fetch_page", return_value="<html>x</html>"), \
         patch("app.pipeline.extract_best_text",
               return_value={"text": _CLEAN_TEXT, "method": "test"}):
        result = trail.rebaseline_source(sid)

    # Result contract
    assert result["status"] == "rebaselined"
    assert result["source_id"] == sid
    assert result["change_status"] == "FIRST_SEEN"
    assert result["normalized_hash"], "a baseline must carry a normalized hash"

    # Exactly one trail record was appended, and it is the new baseline.
    lines = _trail_lines(trail)
    assert len(lines) == 1, "rebaseline must append exactly one record"

    rec = trail.previous_run(sid)
    assert rec is not None
    assert rec["change_status"] == "FIRST_SEEN"
    assert rec["rebaseline"] is True
    assert rec["source_id"] == sid
    assert rec["normalized_hash"] == result["normalized_hash"]
    assert rec["extraction_quality"] == "GOOD"

    # No alert was ever queued.
    assert _queued_alerts(trail) == []


def test_rebaseline_supersedes_a_poisoned_baseline(trail):
    """A clean rebaseline must become the canonical baseline after a bad one."""
    sid = _source_id(trail)

    # Seed a poisoned prior baseline record directly in the trail.
    import json
    trail._RUN_FILE.write_text(
        json.dumps({
            "run_id": "poison01",
            "source_id": sid,
            "official_url": _SOURCE["url"],
            "change_status": "FIRST_SEEN",
            "normalized_hash": "d" * 64,
            "extraction_quality": "FAILED",
            "timestamp_utc": "2026-07-10T00:00:00+00:00",
        }) + "\n",
        encoding="utf-8",
    )
    trail._CACHE_VALID = False

    with patch("app.pipeline.fetch_page", return_value="<html>x</html>"), \
         patch("app.pipeline.extract_best_text",
               return_value={"text": _CLEAN_TEXT, "method": "test"}):
        result = trail.rebaseline_source(sid)

    assert result["status"] == "rebaselined"
    # previous_run returns the LAST record — the new baseline, not the poison.
    latest = trail.previous_run(sid)
    assert latest["run_id"] == result["run_id"]
    assert latest["normalized_hash"] == result["normalized_hash"]
    assert latest["normalized_hash"] != "d" * 64
    assert latest["extraction_quality"] == "GOOD"


def test_rebaseline_from_mojibake_is_refused_and_writes_nothing(trail):
    sid = _source_id(trail)
    with patch("app.pipeline.fetch_page", return_value="<html>x</html>"), \
         patch("app.pipeline.extract_best_text",
               return_value={"text": _MOJIBAKE_TEXT, "method": "test"}):
        result = trail.rebaseline_source(sid)

    assert result["status"] == "refused"
    assert result["reason"] == "undecodable_content"
    # Nothing written: no trail record, no snapshot dir, no alert.
    assert _trail_lines(trail) == []
    assert trail.previous_run(sid) is None
    assert _queued_alerts(trail) == []


def test_rebaseline_from_thin_content_is_refused_and_writes_nothing(trail):
    sid = _source_id(trail)
    with patch("app.pipeline.fetch_page", return_value="<html>x</html>"), \
         patch("app.pipeline.extract_best_text",
               return_value={"text": _THIN_TEXT, "method": "test"}):
        result = trail.rebaseline_source(sid)

    assert result["status"] == "refused"
    assert result["reason"] == "low_quality"
    assert _trail_lines(trail) == []
    assert trail.previous_run(sid) is None


def test_rebaseline_from_empty_content_is_refused_and_writes_nothing(trail):
    sid = _source_id(trail)
    with patch("app.pipeline.fetch_page", return_value="<html></html>"), \
         patch("app.pipeline.extract_best_text",
               return_value={"text": "", "method": "none"}):
        result = trail.rebaseline_source(sid)

    assert result["status"] == "refused"
    assert result["reason"] == "empty_content"
    assert _trail_lines(trail) == []


def test_rebaseline_unknown_source_id_errors_cleanly(trail):
    # Fetch/extract must never be called for an unknown id.
    with patch("app.pipeline.fetch_page", side_effect=AssertionError("must not fetch")), \
         patch("app.pipeline.extract_best_text", side_effect=AssertionError("must not extract")):
        result = trail.rebaseline_source("XX-does-not-exist")

    assert result["status"] == "not_found"
    assert result["source_id"] == "XX-does-not-exist"
    assert _trail_lines(trail) == []


def test_rebaseline_fetch_failure_is_refused_and_writes_nothing(trail):
    sid = _source_id(trail)
    with patch("app.pipeline.fetch_page", side_effect=TimeoutError("page timed out")):
        result = trail.rebaseline_source(sid)

    assert result["status"] == "refused"
    assert result["reason"] == "fetch_failed"
    assert _trail_lines(trail) == []
    assert trail.previous_run(sid) is None


# ── Integration gate: the rebaselined baseline must match what the LIVE ──────
# pipeline computes and compares. These are the reviewer's retest criteria —
# they exercise the REAL run_pipeline classification, not previous_run alone.
# Genuinely CHANGED content adds a distinct penalty clause so the normalized
# hash differs from the clean baseline.
_CHANGED_TEXT = (
    "NEW: material sanction and penalty clause introduced by the regulator "
    "with immediate effect for all licensed entities.\n\n" + _CLEAN_TEXT
)


def test_rebaseline_then_unchanged_sweep_is_not_changed_and_alerts_zero(trail, tmp_path):
    """
    After rebaseline on clean content, a byte-identical monitor sweep MUST
    classify changed=False and queue ZERO alerts. Before the hash-flavor fix
    this returned changed=True and fired a spurious CHANGED alert.
    """
    from app.pipeline import init_pipeline, run_pipeline_for_source

    sid = _source_id(trail)

    # 1. Rebaseline on clean content — writes the canonical baseline + snapshot.
    with patch("app.pipeline.fetch_page", return_value="<html>x</html>"), \
         patch("app.pipeline.extract_best_text",
               return_value={"text": _CLEAN_TEXT, "method": "test"}), \
         patch("app.db.save_document", return_value=None):
        rb = trail.rebaseline_source(sid)
    assert rb["status"] == "rebaselined"
    assert len(_trail_lines(trail)) == 1, "rebaseline appends exactly one baseline record"

    baseline_hash = trail.previous_run(sid)["normalized_hash"]

    # 2. Next sweep on BYTE-IDENTICAL content → the real pipeline classification.
    sends = []
    init_pipeline(0)
    with patch("app.pipeline.fetch_page", return_value="<html>x</html>"), \
         patch("app.pipeline.extract_best_text",
               return_value={"text": _CLEAN_TEXT, "method": "test"}), \
         patch("app.pipeline.get_adapter_for_url", return_value=None), \
         patch("app.pipeline.get_latest_document", return_value=None), \
         patch("app.pipeline.save_document", return_value=None), \
         patch("app.telegram.send_telegram_alert",
               side_effect=lambda p: sends.append(p) or True):
        result = run_pipeline_for_source(_SOURCE)

    # The canonical hashes must match, so the sweep is UNCHANGED.
    assert result["normalized_hash"] == baseline_hash, \
        "rebaseline baseline hash must equal the pipeline's new_hash"
    assert result["changed"] is False, \
        "a byte-identical sweep after rebaseline must NOT be CHANGED"
    # ZERO alerts: no Telegram send and no CHANGED record in the trail queue.
    assert sends == [], "no Telegram alert may fire on an unchanged sweep"
    assert _queued_alerts(trail) == [], "no CHANGED alert may be queued"
    # The heartbeat recorded UNCHANGED, never CHANGED.
    hb = trail.previous_run(sid)
    assert hb["change_status"] in ("UNCHANGED", "FIRST_SEEN")
    assert hb["change_status"] != "CHANGED"


def test_rebaseline_then_genuinely_changed_sweep_is_changed(trail, tmp_path):
    """Regression guard: real changes after a rebaseline still classify CHANGED."""
    from app.pipeline import init_pipeline, run_pipeline_for_source

    sid = _source_id(trail)

    with patch("app.pipeline.fetch_page", return_value="<html>x</html>"), \
         patch("app.pipeline.extract_best_text",
               return_value={"text": _CLEAN_TEXT, "method": "test"}), \
         patch("app.db.save_document", return_value=None):
        rb = trail.rebaseline_source(sid)
    assert rb["status"] == "rebaselined"
    baseline_hash = trail.previous_run(sid)["normalized_hash"]

    init_pipeline(0)
    with patch("app.pipeline.fetch_page", return_value="<html>x</html>"), \
         patch("app.pipeline.extract_best_text",
               return_value={"text": _CHANGED_TEXT, "method": "test"}), \
         patch("app.pipeline.get_adapter_for_url", return_value=None), \
         patch("app.pipeline.get_latest_document", return_value=None), \
         patch("app.pipeline.save_document", return_value=None), \
         patch("app.telegram.send_telegram_alert", return_value=True):
        result = run_pipeline_for_source(_SOURCE)

    assert result["normalized_hash"] != baseline_hash, \
        "changed content must produce a different canonical hash"
    assert result["changed"] is True, "a genuine change after rebaseline must be CHANGED"
    assert result["is_new"] is False, "this is a change vs the rebaseline, not a first-seen"


def test_rebaseline_adapter_branch_then_unchanged_sweep(trail, tmp_path):
    """
    N1: exercise the ADAPTER branch of _rebaseline_fetch (not the generic
    fallback). An adapter-backed source rebaselined via its adapter, then swept
    by the real pipeline using the SAME adapter, must classify changed=False
    with zero alerts — proving rebaseline baselines the exact text (and hash)
    the monitor will compute for an adapter-backed source.
    """
    from app.pipeline import init_pipeline, run_pipeline_for_source

    sid = _source_id(trail)

    class _FakeAdapter:
        name = "fake_rebaseline_adapter"

        def fetch_content(self, url, source=None):
            return _CLEAN_TEXT

    fake = _FakeAdapter()

    # 1. Rebaseline through the adapter branch of _rebaseline_fetch.
    #    _rebaseline_fetch does `from app.adapters.registry import get_adapter_for_url`
    #    at call time, so patch it there. fetch_page must NOT be reached.
    with patch("app.adapters.registry.get_adapter_for_url", return_value=fake), \
         patch("app.pipeline.fetch_page",
               side_effect=AssertionError("adapter branch must not fall through")), \
         patch("app.db.save_document", return_value=None):
        rb = trail.rebaseline_source(sid)
    assert rb["status"] == "rebaselined"
    assert len(_trail_lines(trail)) == 1
    baseline_hash = trail.previous_run(sid)["normalized_hash"]

    # 2. Next sweep uses the SAME adapter via the real pipeline.
    sends = []
    init_pipeline(0)
    with patch("app.pipeline.get_adapter_for_url", return_value=fake), \
         patch("app.pipeline.get_latest_document", return_value=None), \
         patch("app.pipeline.save_document", return_value=None), \
         patch("app.telegram.send_telegram_alert",
               side_effect=lambda p: sends.append(p) or True):
        result = run_pipeline_for_source(_SOURCE)

    assert result["normalized_hash"] == baseline_hash, \
        "adapter-baselined hash must equal the pipeline's adapter-path new_hash"
    assert result["changed"] is False, \
        "a byte-identical adapter sweep after rebaseline must NOT be CHANGED"
    assert sends == [], "no Telegram alert may fire on an unchanged adapter sweep"
    assert _queued_alerts(trail) == [], "no CHANGED alert may be queued"


def test_rebaseline_reports_no_baseline_divergence(trail):
    """
    check_baseline_consistency() must report no divergence for a freshly
    rebaselined source: the SQLite derived index carries the same canonical
    hash the trail records. Proves the save_document(url, content_hash=new_hash)
    alignment. Also proves the OLD normalized-flavor hash WOULD have diverged.
    """
    from app.text_normalization import normalize_for_change_hash, stable_content_hash, stable_normalized_hash
    import app.consistency as consistency

    sid = _source_id(trail)

    saved = {}
    def _fake_save(url, content, content_hash=None, **kw):
        saved["url"] = url
        saved["content_hash"] = content_hash

    with patch("app.pipeline.fetch_page", return_value="<html>x</html>"), \
         patch("app.pipeline.extract_best_text",
               return_value={"text": _CLEAN_TEXT, "method": "test"}), \
         patch("app.db.save_document", side_effect=_fake_save):
        rb = trail.rebaseline_source(sid)

    assert rb["status"] == "rebaselined"
    canonical = stable_content_hash(normalize_for_change_hash(_CLEAN_TEXT))
    # rebaseline wrote the canonical (content-flavor) hash to SQLite.
    assert saved["content_hash"] == canonical
    # The OLD buggy flavor would NOT match — this is the bug the fix closes.
    assert stable_normalized_hash(_CLEAN_TEXT) != canonical

    trail_hash = trail.previous_run(sid)["normalized_hash"]
    assert trail_hash == canonical

    # check_baseline_consistency reads latest_runs() (monkeypatched trail) and
    # get_latest_document() (SQLite row); with the aligned hash there is no
    # divergence.
    with patch.object(
        consistency, "get_latest_document",
        return_value={"content_hash": saved["content_hash"]},
    ):
        divergences = consistency.check_baseline_consistency()

    assert divergences == [], \
        "a freshly rebaselined source must not report baseline divergence"
