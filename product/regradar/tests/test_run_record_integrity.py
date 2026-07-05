"""
Regression tests for the monitor→evidence recording path.

Defect D1: run_pipeline computes the normalized content hash but never
attaches it to the run record, so classify_change cannot compare hashes,
CHANGED runs are recorded as UNCHANGED, proof blocks are INCOMPLETE, and
the alert-draft gate never fires.

Defect D2: pipeline extraction_quality is lowercase ("good"/"low_content"/
"failed") while classify_change compares against uppercase _GOOD_ORDER keys,
producing false QUALITY_DROP downgrades and missing real failures.

No network calls — fetch/extract/db are patched.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from app.source_runs import classify_change


# ── D2: classify_change must treat quality labels case-insensitively ────────

def _rec(quality: str, *, nhash: str = "aaa", chars: int = 5000, nchars: int = 4000) -> dict:
    return {
        "extraction_quality": quality,
        "extracted_chars": chars,
        "normalized_chars": nchars,
        "normalized_hash": nhash,
    }


def test_lowercase_good_after_uppercase_good_same_hash_is_unchanged():
    current = _rec("good", nhash="aaa")
    previous = _rec("GOOD", nhash="aaa")
    assert classify_change(current, previous) == "UNCHANGED"


def test_lowercase_good_with_different_hash_is_changed():
    current = _rec("good", nhash="bbb")
    previous = _rec("GOOD", nhash="aaa")
    assert classify_change(current, previous) == "CHANGED"


def test_lowercase_failed_is_classified_failed():
    current = _rec("failed", nhash="", chars=0, nchars=0)
    previous = _rec("GOOD", nhash="aaa")
    assert classify_change(current, previous) == "FAILED"


def test_low_content_after_good_is_quality_drop():
    # low_content maps to THIN — dropping from GOOD must stay a QUALITY_DROP.
    current = _rec("low_content", nhash="bbb", chars=300, nchars=900)
    previous = _rec("GOOD", nhash="aaa")
    assert classify_change(current, previous) == "QUALITY_DROP"


def test_real_quality_drop_still_detected_by_char_collapse():
    # Genuine collapse in extracted volume must remain QUALITY_DROP
    # regardless of label casing (validator must not be weakened).
    current = _rec("good", nhash="bbb", chars=1000, nchars=4000)
    previous = _rec("GOOD", nhash="aaa", chars=5000, nchars=4000)
    assert classify_change(current, previous) == "QUALITY_DROP"


# ── D1: run record must carry the hashes the pipeline computed ──────────────

_HTML = "<html><body>" + ("<p>Regulatory obligation paragraph.</p>" * 60) + "</body></html>"
_TEXT = "\n\n".join(f"Regulatory obligation paragraph {i}." for i in range(60))


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


def test_changed_run_record_carries_normalized_hash_and_is_recorded_changed(isolated_dirs):
    from app.pipeline import init_pipeline, run_pipeline_for_source

    source = {
        "name": "Test Regulator Source",
        "url": "https://example.gov.ae/rules",
        "jurisdiction": "AE",
        "category": "financial_regulator",
        "enabled": True,
    }

    previous_doc = {
        "content": "Old regulatory text that differs entirely.",
        "content_hash": "0" * 64,
    }

    # Seed a prior run in the evidence trail (as the intake path records it,
    # uppercase quality) so classification compares against a real baseline.
    import json as _json
    import app.source_runs as sr
    sr._RUN_DIR.mkdir(parents=True, exist_ok=True)
    prev_snap_dir = isolated_dirs / "data" / "source_snapshots" / "2026-06-20" / "AE" / "AE-test-regulator-source" / "seed0001"
    prev_snap_dir.mkdir(parents=True, exist_ok=True)
    (prev_snap_dir / "normalized.txt").write_text(
        "Old regulatory text that differs entirely.", encoding="utf-8")
    sr._RUN_FILE.write_text(_json.dumps({
        "run_id": "seed0001",
        "source_id": "AE-test-regulator-source",
        "official_url": "https://example.gov.ae/rules",
        "url": "https://example.gov.ae/rules",
        "change_status": "FIRST_SEEN",
        "extraction_quality": "GOOD",
        "extracted_chars": 2500,
        "normalized_chars": 2200,
        "normalized_hash": "f" * 64,
        "raw_hash": "e" * 64,
        "snapshot_normalized_path": "data/source_snapshots/2026-06-20/AE/AE-test-regulator-source/seed0001/normalized.txt",
        "timestamp_utc": "2026-06-20T10:00:00+00:00",
    }) + "\n", encoding="utf-8")
    sr._CACHE_VALID = False

    init_pipeline(0)
    with patch("app.pipeline.fetch_page", return_value=_HTML), \
         patch("app.pipeline.extract_best_text", return_value={"text": _TEXT, "method": "test"}), \
         patch("app.pipeline.get_latest_document", return_value=previous_doc), \
         patch("app.pipeline.save_document", return_value=None), \
         patch("app.telegram.send_telegram_alert", return_value=False), \
         patch("app.pipeline.get_adapter_for_url", return_value=None):
        result = run_pipeline_for_source(source)

    assert result.get("changed") is True

    record = result.get("run_record")
    assert record, "changed run must append a run record"

    # The hash computed for change detection must be preserved in the record.
    assert record.get("normalized_hash"), "run record lost the normalized hash"
    assert record.get("normalized_chars"), "run record lost normalized_chars"

    # With hashes present, classification must not silently downgrade.
    assert record.get("change_status") == "CHANGED", (
        f"pipeline detected a change but the evidence trail recorded "
        f"{record.get('change_status')!r}"
    )

    # Proof artifact must carry the hash and not be INCOMPLETE.
    proof_path = record.get("proof_block_path")
    assert proof_path, "proof artifact missing"
    import json
    proof = json.loads((isolated_dirs / proof_path).read_text(encoding="utf-8")) \
        if not Path(proof_path).is_absolute() else json.loads(Path(proof_path).read_text(encoding="utf-8"))
    assert proof.get("normalized_hash") == record.get("normalized_hash")
    assert proof.get("proof_quality") != "INCOMPLETE"
