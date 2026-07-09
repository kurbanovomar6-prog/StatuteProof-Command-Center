"""Eval finding N1 — the run-trail cache must notice cross-process writes.

Deployed topology runs the API and the scheduler as separate processes;
the API's cached _read_runs() never saw runs the scheduler appended
(proven live in the 2026-07-06 evaluation: /api/briefs/generate returned
"No CHANGED run record found" for a record that existed on disk, and
succeeded after a process restart).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


@pytest.fixture
def trail(tmp_path, monkeypatch):
    import app.source_runs as sr

    monkeypatch.setattr(sr, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(sr, "_RUN_DIR", tmp_path / "data" / "source_runs")
    monkeypatch.setattr(sr, "_RUN_FILE", tmp_path / "data" / "source_runs" / "source_runs.jsonl")
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None
    sr._RUN_DIR.mkdir(parents=True, exist_ok=True)
    yield sr
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None


def _rec(run_id: str, status: str = "CHANGED") -> str:
    return json.dumps(
        {
            "run_id": run_id,
            "source_id": "AE-x",
            "change_status": status,
            "normalized_hash": "a" * 64,
            "timestamp_utc": f"2026-07-06T10:00:0{run_id[-1]}+00:00",
        }
    )


def test_external_append_is_visible_without_restart(trail):
    sr = trail
    sr._RUN_FILE.write_text(_rec("r1") + "\n", encoding="utf-8")
    assert len(sr._read_runs()) == 1

    # Simulate the scheduler process appending while we hold a warm cache.
    with sr._RUN_FILE.open("a", encoding="utf-8") as fh:
        fh.write(_rec("r2") + "\n")

    runs = sr._read_runs()
    assert len(runs) == 2, "cache must notice the cross-process append"
    assert runs[-1]["run_id"] == "r2"


def test_external_rewrite_is_visible(trail):
    sr = trail
    sr._RUN_FILE.write_text(_rec("r1") + "\n" + _rec("r2") + "\n", encoding="utf-8")
    assert len(sr._read_runs()) == 2
    # Compaction rewrites the file (same length trap avoided: content differs).
    sr._RUN_FILE.write_text(_rec("r9") + "\n", encoding="utf-8")
    runs = sr._read_runs()
    assert len(runs) == 1 and runs[0]["run_id"] == "r9"


def test_same_process_cache_still_serves_when_unchanged(trail):
    sr = trail
    sr._RUN_FILE.write_text(_rec("r1") + "\n", encoding="utf-8")
    first = sr._read_runs()
    second = sr._read_runs()
    assert second is first, "unchanged file must be served from cache (no re-parse)"
