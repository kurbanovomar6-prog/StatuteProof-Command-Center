"""
Owner decisions 1+2+3 (production readiness sprint):

D6  — every monitor run writes a record; unchanged runs write a compact
      heartbeat {timestamp, source_id, normalized_hash, status, proof_url,
      run_id}.
D2b — the JSONL evidence trail normalized_hash is the single source of truth
      for classification; SQLite `documents` is a derived index updated in
      the same step from the same hash. Both stores must agree after every
      run type. A consistency check detects divergence and logs loudly.
D8  — artifact base dir resolved from config/env, never hardcoded.

No network — fetch/extract/db patched.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from app.text_normalization import normalize_for_change_hash, stable_content_hash

_TEXT = "\n\n".join(f"Regulatory obligation paragraph {i}." for i in range(60))
_HTML = "<html><body>irrelevant — extract is patched</body></html>"
_CANON_HASH = stable_content_hash(normalize_for_change_hash(_TEXT))

_SOURCE = {
    "name": "Test Regulator Source",
    "url": "https://example.gov.ae/rules",
    "jurisdiction": "AE",
    "category": "financial_regulator",
    "enabled": True,
}
_SOURCE_ID = "AE-test-regulator-source"


@pytest.fixture
def isolated_dirs(tmp_path, monkeypatch):
    import app.source_runs as sr
    monkeypatch.setattr(sr, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(sr, "_RUN_DIR", tmp_path / "data" / "source_runs")
    monkeypatch.setattr(sr, "_RUN_FILE", tmp_path / "data" / "source_runs" / "source_runs.jsonl")
    monkeypatch.setattr(sr, "_SNAPSHOT_DIR", tmp_path / "data" / "source_snapshots")
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None
    yield tmp_path
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None


def _seed_previous(tmp_path, normalized_hash: str, text: str = "old text") -> None:
    import app.source_runs as sr
    sr._RUN_DIR.mkdir(parents=True, exist_ok=True)
    snap_dir = tmp_path / "data" / "source_snapshots" / "2026-06-20" / "AE" / _SOURCE_ID / "seed0001"
    snap_dir.mkdir(parents=True, exist_ok=True)
    (snap_dir / "normalized.txt").write_text(text, encoding="utf-8")
    sr._RUN_FILE.write_text(json.dumps({
        "run_id": "seed0001",
        "source_id": _SOURCE_ID,
        "official_url": _SOURCE["url"],
        "url": _SOURCE["url"],
        "change_status": "FIRST_SEEN",
        "extraction_quality": "GOOD",
        "extracted_chars": 2500,
        "normalized_chars": 2200,
        "normalized_hash": normalized_hash,
        "raw_hash": "e" * 64,
        "snapshot_normalized_path": "data/source_snapshots/2026-06-20/AE/AE-test-regulator-source/seed0001/normalized.txt",
        "timestamp_utc": "2026-06-20T10:00:00+00:00",
    }) + "\n", encoding="utf-8")
    sr._CACHE_VALID = False


def _run(source=_SOURCE, latest_doc=None, saved: list | None = None):
    """Run the pipeline with fetch/extract/db patched; capture save_document calls."""
    from app.pipeline import init_pipeline, run_pipeline_for_source
    init_pipeline(0)
    captured = saved if saved is not None else []

    def _fake_save(url, content, content_hash=None, **kw):
        captured.append({"url": url, "content": content, "content_hash": content_hash, **kw})

    with patch("app.pipeline.fetch_page", return_value=_HTML), \
         patch("app.pipeline.extract_best_text", return_value={"text": _TEXT, "method": "test"}), \
         patch("app.pipeline.get_latest_document", return_value=latest_doc), \
         patch("app.pipeline.save_document", side_effect=_fake_save), \
         patch("app.telegram.send_telegram_alert", return_value=False), \
         patch("app.pipeline.get_adapter_for_url", return_value=None):
        result = run_pipeline_for_source(source)
    return result, captured


def _trail_records():
    import app.source_runs as sr
    if not sr._RUN_FILE.exists():
        return []
    return [json.loads(l) for l in sr._RUN_FILE.read_text(encoding="utf-8").splitlines()]


# ── D6: heartbeats ───────────────────────────────────────────────────────────

def test_unchanged_run_writes_compact_heartbeat(isolated_dirs):
    _seed_previous(isolated_dirs, _CANON_HASH)

    result, _ = _run()

    assert result.get("changed") is False
    records = _trail_records()
    assert len(records) == 2, "unchanged run must append a heartbeat record"
    hb = records[-1]
    assert hb.get("record_type") == "heartbeat"
    assert hb.get("change_status") == "UNCHANGED"
    assert hb.get("source_id") == _SOURCE_ID
    assert hb.get("normalized_hash") == _CANON_HASH
    assert hb.get("run_id")
    assert hb.get("timestamp_utc")
    assert hb.get("official_url") == _SOURCE["url"]


def test_heartbeat_becomes_next_baseline(isolated_dirs):
    _seed_previous(isolated_dirs, _CANON_HASH)
    _run()  # heartbeat appended

    import app.source_runs as sr
    prev = sr.previous_run(_SOURCE_ID)
    assert prev.get("record_type") == "heartbeat"
    assert prev.get("normalized_hash") == _CANON_HASH


# ── Decision 2: canonical baseline = JSONL; SQLite derived, same hash ────────

def test_unchanged_vs_jsonl_wins_over_divergent_sqlite(isolated_dirs):
    """The VARA case: SQLite holds a different hash (raw-content hashing).
    JSONL hash matches → run is UNCHANGED regardless of SQLite."""
    _seed_previous(isolated_dirs, _CANON_HASH)
    divergent_doc = {"content": "old", "content_hash": "0" * 64}

    result, saved = _run(latest_doc=divergent_doc)

    assert result.get("changed") is False, (
        "JSONL trail is canonical — divergent SQLite hash must not force CHANGED"
    )
    # Derived index realigned in the same step with the SAME canonical hash.
    assert saved, "divergent SQLite index must be realigned"
    assert saved[-1]["content_hash"] == _CANON_HASH


def test_unchanged_with_agreeing_sqlite_writes_no_new_document_row(isolated_dirs):
    _seed_previous(isolated_dirs, _CANON_HASH)
    agreeing_doc = {"content": _TEXT, "content_hash": _CANON_HASH}

    result, saved = _run(latest_doc=agreeing_doc)

    assert result.get("changed") is False
    assert saved == [], "no divergence → no derived-index write"


def test_changed_run_stores_same_canonical_hash_in_both_stores(isolated_dirs):
    _seed_previous(isolated_dirs, "1" * 64, text="Entirely different old text.")
    old_doc = {"content": "Entirely different old text.", "content_hash": "1" * 64}

    result, saved = _run(latest_doc=old_doc)

    assert result.get("changed") is True
    rec = result.get("run_record") or {}
    assert rec.get("change_status") == "CHANGED"
    assert rec.get("normalized_hash") == _CANON_HASH
    assert saved and saved[-1]["content_hash"] == _CANON_HASH, (
        "SQLite derived index must receive the same canonical hash in the same step"
    )


def test_failed_fetch_writes_to_neither_store(isolated_dirs):
    _seed_previous(isolated_dirs, _CANON_HASH)
    from app.pipeline import init_pipeline, run_pipeline_for_source
    init_pipeline(0)
    saved: list = []
    with patch("app.pipeline.fetch_page", side_effect=ConnectionError("down")), \
         patch("app.pipeline.save_document", side_effect=lambda **kw: saved.append(kw)), \
         patch("app.pipeline.get_adapter_for_url", return_value=None):
        with pytest.raises(ConnectionError):
            run_pipeline_for_source(_SOURCE)
    assert saved == []
    assert len(_trail_records()) == 1, "failed fetch must not append a run record here"


# ── Consistency check ────────────────────────────────────────────────────────

def test_consistency_check_detects_divergence_and_logs_loudly(isolated_dirs, caplog):
    import logging
    _seed_previous(isolated_dirs, _CANON_HASH)
    from app.consistency import check_baseline_consistency

    divergent_doc = {"content": "x", "content_hash": "0" * 64}
    with patch("app.consistency.get_latest_document", return_value=divergent_doc):
        with caplog.at_level(logging.ERROR, logger="app.consistency"):
            divergences = check_baseline_consistency()

    assert len(divergences) == 1
    d = divergences[0]
    assert d["source_id"] == _SOURCE_ID
    assert d["jsonl_hash"] == _CANON_HASH
    assert d["sqlite_hash"] == "0" * 64
    assert "BASELINE DIVERGENCE" in caplog.text, "divergence must be logged loudly"


def test_consistency_check_clean_when_stores_agree(isolated_dirs, caplog):
    import logging
    _seed_previous(isolated_dirs, _CANON_HASH)
    from app.consistency import check_baseline_consistency

    agreeing_doc = {"content": "x", "content_hash": _CANON_HASH}
    with patch("app.consistency.get_latest_document", return_value=agreeing_doc):
        with caplog.at_level(logging.ERROR, logger="app.consistency"):
            divergences = check_baseline_consistency()

    assert divergences == []
    assert "BASELINE DIVERGENCE" not in caplog.text


# ── D8: base dir from config/env only ────────────────────────────────────────

def test_changed_run_artifacts_stay_inside_configured_base_dir(isolated_dirs):
    _seed_previous(isolated_dirs, "1" * 64, text="Entirely different old text.")
    old_doc = {"content": "Entirely different old text.", "content_hash": "1" * 64}

    repo_base = Path(__file__).resolve().parents[1]
    real_dir = repo_base / "data" / "source_snapshots" / "2026-07-05" / "AE" / _SOURCE_ID
    assert not real_dir.exists(), "pre-condition: no stale test artifacts in repo data"

    result, _ = _run(latest_doc=old_doc)

    assert result.get("changed") is True
    # Alert artifacts must live under the configured base, not the repo.
    ad = result.get("alert_draft_json_path")
    assert ad, "changed run should produce an alert draft"
    assert str(isolated_dirs) in str(Path(ad).resolve()), (
        f"alert draft written outside configured base dir: {ad}"
    )
    assert not real_dir.exists(), "artifacts leaked into the repo data dir (D8)"


def test_base_dir_env_override(monkeypatch, tmp_path):
    """STATUTEPROOF_BASE_DIR must control source_runs paths at import time."""
    import importlib
    monkeypatch.setenv("STATUTEPROOF_BASE_DIR", str(tmp_path))
    import app.source_runs as sr
    importlib.reload(sr)
    try:
        assert Path(sr._BASE_DIR) == tmp_path
        assert str(sr._RUN_FILE).startswith(str(tmp_path))
    finally:
        monkeypatch.delenv("STATUTEPROOF_BASE_DIR")
        importlib.reload(sr)
