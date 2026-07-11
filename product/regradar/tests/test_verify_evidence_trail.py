"""
Tests for tools/verify_evidence_trail.py — the read-only evidence-trail
integrity verifier (the "hashes prove content" keystone).

Strategy: seed a tiny evidence trail using the REAL pipeline write path
(``record_from_source_result`` writes raw.txt / normalized.txt and computes
the stored hashes; ``append_run`` appends the JSONL record). Then verify:

  * a clean trail verifies with exit 0 / all-pass,
  * corrupting one snapshot byte makes that record divergent + exit 1,
  * a rebaseline-flavor hash (stable_content_hash(normalize_for_change_hash))
    still verifies (both hash flavors are accepted),
  * legacy records without snapshot paths are 'unverifiable', not 'failed',
  * a source-id filter scopes verification.

No network: snapshots are written directly to the isolated trail dir.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

import app.source_runs as sr
from app.text_normalization import normalize_for_change_hash, stable_content_hash
from tools import verify_evidence_trail as vt


# ── isolated trail fixture (mirrors test_run_record_integrity.py) ────────────

@pytest.fixture
def isolated_trail(tmp_path, monkeypatch):
    monkeypatch.setattr(sr, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(sr, "_RUN_DIR", tmp_path / "data" / "source_runs")
    monkeypatch.setattr(sr, "_RUN_FILE", tmp_path / "data" / "source_runs" / "source_runs.jsonl")
    monkeypatch.setattr(sr, "_SNAPSHOT_DIR", tmp_path / "data" / "source_snapshots")
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None
    yield tmp_path
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None


def _seed_source_run(*, source_id: str, run_id: str, text: str) -> dict:
    """Write a real snapshot + trail record via the pipeline's own write path."""
    source = {
        "id": source_id,
        "name": "Test Regulator",
        "url": "https://example.gov.ae/rules",
        "jurisdiction": "AE",
        "category": "financial_regulator",
    }
    result = {
        "url": source["url"],
        "final_url": source["url"],
        "status": "ok",
        "extracted_text": text,
        "extracted_chars": len(text),
        "fetch_method": "test",
        "reason": "",
    }
    record = sr.record_from_source_result(run_id=run_id, source=source, result=result)
    return sr.append_run(record)


def _long_text(marker: str) -> str:
    # Enough content to clear normalization/quality thresholds and produce
    # non-empty raw + normalized snapshots.
    body = "\n\n".join(
        f"Regulatory obligation paragraph {i} for {marker}." for i in range(60)
    )
    return f"Circular {marker} — Published 2026-06-01\n\n{body}\n"


# ── clean trail verifies ─────────────────────────────────────────────────────

def test_clean_trail_all_pass_exit_zero(isolated_trail, capsys):
    _seed_source_run(source_id="AE-one", run_id="run00001", text=_long_text("A"))
    _seed_source_run(source_id="AE-two", run_id="run00002", text=_long_text("B"))

    report = vt.verify_trail()
    assert report.ok is True
    assert report.divergent == []
    assert len(report.verified) == 2
    # Both raw and normalized hashes checked on each record.
    for r in report.verified:
        kinds = {c.kind for c in r.checks}
        assert kinds == {"raw", "normalized"}
        assert all(c.matched for c in r.checks)

    # CLI returns 0 and prints PASS.
    exit_code = vt.run_cli([])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "RESULT: PASS" in out


def test_verify_record_matches_pipeline_stored_hashes(isolated_trail):
    rec = _seed_source_run(source_id="AE-one", run_id="run00001", text=_long_text("A"))
    result = vt.verify_record(rec)
    assert result.status == vt.STATUS_VERIFIED
    # The stored normalized_hash equals sha256(normalized.txt) on the monitor path.
    norm_check = next(c for c in result.checks if c.kind == "normalized")
    assert norm_check.matched
    assert norm_check.recomputed_hash == rec["normalized_hash"]


# ── corruption is detected ───────────────────────────────────────────────────

def test_corrupted_normalized_snapshot_is_divergent_exit_one(isolated_trail, capsys):
    rec = _seed_source_run(source_id="AE-one", run_id="run00001", text=_long_text("A"))
    _seed_source_run(source_id="AE-two", run_id="run00002", text=_long_text("B"))

    # Corrupt one byte of the normalized snapshot for AE-one.
    norm_path = isolated_trail / rec["snapshot_normalized_path"]
    data = bytearray(norm_path.read_bytes())
    data[0] = data[0] ^ 0x01  # flip a single bit → different bytes, same length
    norm_path.write_bytes(bytes(data))

    report = vt.verify_trail()
    assert report.ok is False
    assert len(report.divergent) == 1
    assert report.divergent[0].source_id == "AE-one"
    assert report.divergent[0].run_id == "run00001"
    # The clean record is still verified.
    assert {r.source_id for r in report.verified} == {"AE-two"}

    exit_code = vt.run_cli([])
    out = capsys.readouterr().out
    assert exit_code == 1
    assert "RESULT: FAIL" in out
    assert "AE-one" in out


def test_corrupted_raw_snapshot_is_divergent(isolated_trail):
    rec = _seed_source_run(source_id="AE-one", run_id="run00001", text=_long_text("A"))
    raw_path = isolated_trail / rec["snapshot_raw_path"]
    raw_path.write_bytes(rec_bytes := (raw_path.read_bytes() + b"TAMPER"))
    assert rec_bytes  # sanity

    result = vt.verify_record(rec)
    assert result.status == vt.STATUS_DIVERGENT
    raw_check = next(c for c in result.checks if c.kind == "raw")
    assert raw_check.matched is False
    assert "raw_hash" in (result.reason or "")


def test_truncated_snapshot_is_divergent(isolated_trail):
    rec = _seed_source_run(source_id="AE-one", run_id="run00001", text=_long_text("A"))
    norm_path = isolated_trail / rec["snapshot_normalized_path"]
    norm_path.write_bytes(norm_path.read_bytes()[:-20])  # drop trailing bytes

    result = vt.verify_record(rec)
    assert result.status == vt.STATUS_DIVERGENT


# ── rebaseline flavor B hash still verifies ──────────────────────────────────

def test_rebaseline_flavor_normalized_hash_verifies(isolated_trail):
    rec = _seed_source_run(source_id="AE-one", run_id="run00001", text=_long_text("A"))
    # Overwrite the record's normalized_hash with the rebaseline flavor
    # (stable_content_hash(normalize_for_change_hash(raw))) exactly as
    # rebaseline_source() does. The snapshot bytes are unchanged.
    raw_text = (isolated_trail / rec["snapshot_raw_path"]).read_text(encoding="utf-8")
    flavor_a = rec["normalized_hash"]  # monitor-path hash stored by the pipeline
    flavor_b = stable_content_hash(normalize_for_change_hash(raw_text))
    assert flavor_b != flavor_a, "the two flavors must differ or this test is vacuous"

    rec = dict(rec)
    rec["normalized_hash"] = flavor_b

    result = vt.verify_record(rec)
    assert result.status == vt.STATUS_VERIFIED, result.reason
    norm_check = next(c for c in result.checks if c.kind == "normalized")
    assert norm_check.matched


# ── legacy / unverifiable records never fail ─────────────────────────────────

def test_record_without_snapshot_paths_is_unverifiable(isolated_trail):
    legacy = {
        "source_id": "AE-legacy",
        "run_id": "legacy01",
        "normalized_hash": "deadbeef" * 8,
        "raw_hash": "cafef00d" * 8,
        # no snapshot_* paths — heartbeat / pre-snapshot record
    }
    result = vt.verify_record(legacy)
    assert result.status == vt.STATUS_UNVERIFIABLE
    assert "no snapshot paths" in (result.reason or "")


def test_missing_snapshot_files_are_unverifiable_not_divergent(isolated_trail):
    rec = _seed_source_run(source_id="AE-one", run_id="run00001", text=_long_text("A"))
    # Delete the snapshot files but keep the trail record (compaction/legacy).
    (isolated_trail / rec["snapshot_raw_path"]).unlink()
    (isolated_trail / rec["snapshot_normalized_path"]).unlink()

    result = vt.verify_record(rec)
    assert result.status == vt.STATUS_UNVERIFIABLE
    assert report_ok_when_only_unverifiable(isolated_trail)


def report_ok_when_only_unverifiable(base) -> bool:
    report = vt.verify_trail()
    return report.ok and report.divergent == []


def test_empty_trail_passes(isolated_trail, capsys):
    report = vt.verify_trail()
    assert report.ok is True
    assert report.records == []
    assert vt.run_cli([]) == 0
    assert "PASS" in capsys.readouterr().out


# ── source-id filter ─────────────────────────────────────────────────────────

def test_source_id_filter_scopes_verification(isolated_trail):
    _seed_source_run(source_id="AE-one", run_id="run00001", text=_long_text("A"))
    rec_b = _seed_source_run(source_id="AE-two", run_id="run00002", text=_long_text("B"))

    # Corrupt AE-two only.
    norm_path = isolated_trail / rec_b["snapshot_normalized_path"]
    norm_path.write_bytes(norm_path.read_bytes() + b"X")

    # Filtering to AE-one hides the AE-two divergence → PASS.
    only_one = vt.verify_trail(source_id="AE-one")
    assert only_one.ok is True
    assert len(only_one.records) == 1

    # Filtering to AE-two surfaces the divergence → FAIL.
    only_two = vt.verify_trail(source_id="AE-two")
    assert only_two.ok is False
    assert len(only_two.divergent) == 1


def test_json_output_shape(isolated_trail, capsys):
    _seed_source_run(source_id="AE-one", run_id="run00001", text=_long_text("A"))
    exit_code = vt.run_cli(["--json"])
    out = capsys.readouterr().out
    assert exit_code == 0
    import json
    payload = json.loads(out)
    assert payload["ok"] is True
    assert payload["totals"]["records"] == 1
    assert "AE-one" in payload["per_source"]
