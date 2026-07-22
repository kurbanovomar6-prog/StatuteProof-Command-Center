"""Coverage for app.source_runs.restricted_record.

restricted_record() builds the evidence record for a bot-walled / externally
blocked host — the record that ships when a source is marked restricted in
sources.json. Every other test in the suite monkeypatch-stubs it away
(see test_source_readiness_coverage.py), so the real body — market ``.upper()``
casing, ``"; ".join(limitations_notes)``, and the empty-text
``write_snapshots(raw_text="")`` — is never exercised. A regression there would
ship a corrupt restricted evidence record for bot-walled hosts with a fully
green suite. These tests call the REAL function and assert the record fields,
the null hashes, and the on-disk snapshot files.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def runs(tmp_path, monkeypatch):
    """app.source_runs pointed at an isolated tmp artifact tree."""
    import app.source_runs as sr

    monkeypatch.setattr(sr, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(sr, "_RUN_DIR", tmp_path / "data" / "source_runs")
    monkeypatch.setattr(
        sr, "_RUN_FILE", tmp_path / "data" / "source_runs" / "source_runs.jsonl"
    )
    monkeypatch.setattr(
        sr, "_SNAPSHOT_DIR", tmp_path / "data" / "source_snapshots"
    )
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None
    yield sr
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None


def _bot_walled_source(**overrides) -> dict:
    src = {
        "id": "ae-difc",
        "name": "DIFC — Rulebook",
        "jurisdiction": "ae",          # lowercase on purpose — must be upper-cased
        "category": "financial_regulator",
        "url": "https://www.difc.ae/rulebook",
        "status": "disabled_external_access",
    }
    src.update(overrides)
    return src


# ── record field correctness ───────────────────────────────────────────────

def test_restricted_record_marks_source_restricted_and_failed(runs):
    rec = runs.restricted_record(
        run_id="run-1",
        source=_bot_walled_source(),
        limitations_notes=["Bot wall detected"],
    )

    assert rec["access_status"] == "restricted"
    assert rec["fetch_method"] == "failed"
    assert rec["extraction_quality"] == "FAILED"
    assert rec["extracted_chars"] == 0
    assert rec["raw_chars"] == 0
    assert rec["normalized_chars"] == 0
    assert rec["error"] == "Source is marked restricted/blocked in sources.json."
    assert rec["pipeline_version"] == "4.2"


def test_restricted_record_upper_cases_market(runs):
    """The lowercase jurisdiction must be normalized to an upper-case market.

    This is the casing the snapshot path and every downstream jurisdiction
    filter binds to — a regression that dropped ``.upper()`` would fragment
    the evidence tree.
    """
    rec = runs.restricted_record(
        run_id="run-2",
        source=_bot_walled_source(jurisdiction="ae"),
        limitations_notes=[],
    )

    assert rec["market"] == "AE"
    assert rec["jurisdiction"] == "AE"


def test_restricted_record_missing_jurisdiction_yields_empty_market(runs):
    src = _bot_walled_source()
    src.pop("jurisdiction")
    rec = runs.restricted_record(run_id="run-3", source=src, limitations_notes=[])

    assert rec["market"] == ""
    assert rec["jurisdiction"] == ""


def test_restricted_record_all_hashes_are_null(runs):
    rec = runs.restricted_record(
        run_id="run-4",
        source=_bot_walled_source(),
        limitations_notes=["blocked"],
    )

    for key in ("raw_hash", "normalized_hash", "pdf_text_hash", "content_hash"):
        assert rec[key] is None, key
    assert rec["pdf_links_count"] == 0
    assert rec["pdf_extracted_chars"] == 0
    assert rec["title"] is None
    assert rec["publication_date"] is None


def test_restricted_record_joins_limitations_notes(runs):
    rec = runs.restricted_record(
        run_id="run-5",
        source=_bot_walled_source(),
        limitations_notes=["Cloudflare wall", "403 on fetch", "geo-blocked"],
    )

    assert rec["limitations_notes"] == "Cloudflare wall; 403 on fetch; geo-blocked"


def test_restricted_record_empty_notes_join_to_empty_string(runs):
    rec = runs.restricted_record(
        run_id="run-6",
        source=_bot_walled_source(),
        limitations_notes=[],
    )

    assert rec["limitations_notes"] == ""


def test_restricted_record_uses_make_source_id(runs):
    rec = runs.restricted_record(
        run_id="run-7",
        source=_bot_walled_source(id="ae-difc"),
        limitations_notes=[],
    )
    assert rec["source_id"] == "ae-difc"
    assert rec["source_name"] == "DIFC — Rulebook"
    assert rec["official_url"] == "https://www.difc.ae/rulebook"
    assert rec["final_url"] == rec["official_url"]


def test_restricted_record_derives_source_id_when_absent(runs):
    src = _bot_walled_source()
    src.pop("id")
    rec = runs.restricted_record(run_id="run-8", source=src, limitations_notes=[])
    # make_source_id => "<MARKET>-<slug(name)>"
    assert rec["source_id"].startswith("AE-")
    assert rec["source_id"] == runs.make_source_id(src)


# ── on-disk snapshot correctness ────────────────────────────────────────────

def test_restricted_record_writes_empty_snapshot_files(runs):
    rec = runs.restricted_record(
        run_id="run-9",
        source=_bot_walled_source(),
        limitations_notes=["blocked"],
    )

    base = Path(runs._BASE_DIR)

    raw_path = base / rec["snapshot_raw_path"]
    norm_path = base / rec["snapshot_normalized_path"]
    meta_path = base / rec["snapshot_metadata_path"]

    assert raw_path.is_file()
    assert norm_path.is_file()
    assert meta_path.is_file()

    # bot-walled host: no text was captured — both text snapshots are empty
    assert raw_path.read_text(encoding="utf-8") == ""
    assert norm_path.read_text(encoding="utf-8") == ""

    # no PDF snapshot is written for a restricted record
    assert rec["snapshot_pdf_text_path"] is None


def test_restricted_record_snapshot_paths_are_relative(runs):
    rec = runs.restricted_record(
        run_id="run-10",
        source=_bot_walled_source(),
        limitations_notes=[],
    )
    # stored paths must be relative to _BASE_DIR (portable evidence tree)
    assert not Path(rec["snapshot_raw_path"]).is_absolute()
    assert rec["snapshot_raw_path"].startswith("data/source_snapshots")
    # the market segment of the path is upper-cased
    assert "/AE/" in rec["snapshot_raw_path"]


def test_restricted_record_metadata_marks_restricted(runs):
    rec = runs.restricted_record(
        run_id="run-11",
        source=_bot_walled_source(),
        limitations_notes=[],
    )
    meta_path = Path(runs._BASE_DIR) / rec["snapshot_metadata_path"]
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    assert meta["restricted"] is True
    assert meta["run_id"] == "run-11"
    assert meta["source_id"] == rec["source_id"]
    assert meta["official_url"] == "https://www.difc.ae/rulebook"
    assert meta["source_name"] == "DIFC — Rulebook"
    assert meta["timestamp_utc"] == rec["timestamp_utc"]
