"""
G-hashchain — tamper-evident hash chain over the evidence trail.

The evidence trail is "append-only by convention" (a flat JSONL file). The hash
chain makes it "append-only by construction": every appended record carries
``prev_record_hash`` (the record_hash of the immediately preceding trail line)
and ``record_hash`` (sha256 over this record's identifying fields, folding in
prev_record_hash). Inserting, deleting, reordering, or editing an identifying
field of any middle record breaks the link there, detectable by recomputation.

These tests lock:

  * a fresh trail (records appended via the real pipeline write path) builds a
    valid chain that verifies clean;
  * the chain is ADDITIVE — record_hash never changes normalized_hash /
    content_hash, so it can't cause a spurious CHANGED and doesn't invalidate
    baselines;
  * tampering with a middle record's identifying content breaks verification at
    exactly that link (and the FIRST break is reported);
  * inserting / deleting / reordering records breaks the chain;
  * retention compaction (heartbeat + QUALITY_DROP) re-links survivors so the
    chain stays verifiable, and stays idempotent;
  * legacy pre-chain records (no record_hash) are tolerated — the chain starts
    at the first record that carries a record_hash;
  * the ``--chain`` CLI mode reports the chain verdict and exit code.

Hermetic: no network. Snapshots and the trail are written into an isolated
tmp_path dir.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

import app.source_runs as sr
from tools import verify_evidence_trail as vt


# ── isolated trail fixture ───────────────────────────────────────────────────

@pytest.fixture
def isolated_trail(tmp_path, monkeypatch):
    monkeypatch.setattr(sr, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(sr, "_RUN_DIR", tmp_path / "data" / "source_runs")
    monkeypatch.setattr(sr, "_RUN_FILE", tmp_path / "data" / "source_runs" / "source_runs.jsonl")
    monkeypatch.setattr(sr, "_SNAPSHOT_DIR", tmp_path / "data" / "source_snapshots")
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None
    (tmp_path / "data" / "source_runs").mkdir(parents=True, exist_ok=True)
    yield tmp_path
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None


def _long_text(marker: str) -> str:
    body = "\n\n".join(
        f"Regulatory obligation paragraph {i} for {marker}." for i in range(60)
    )
    return f"Circular {marker} — Published 2026-06-01\n\n{body}\n"


def _seed(source_id: str, run_id: str, text: str) -> dict:
    """Append a real snapshot + trail record via the pipeline's write path."""
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


def _rewrite(records: list[dict]) -> None:
    """Rewrite the trail file from a list of record dicts (test tamper helper)."""
    sr._RUN_FILE.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in records) + "\n",
        encoding="utf-8",
    )
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None


# ── fresh trail builds a valid chain ─────────────────────────────────────────

def test_fresh_trail_builds_valid_chain(isolated_trail):
    _seed("AE-one", "run00001", _long_text("A"))
    _seed("AE-two", "run00002", _long_text("B"))
    _seed("AE-one", "run00003", _long_text("C"))

    records = sr._read_runs()
    # First record links from "" ; each subsequent links from the prior hash.
    assert records[0]["prev_record_hash"] == ""
    assert records[0]["record_hash"]
    for prior, rec in zip(records, records[1:]):
        assert rec["prev_record_hash"] == prior["record_hash"]
        assert rec["record_hash"] and rec["record_hash"] != prior["record_hash"]

    chain = vt.verify_chain(records)
    assert chain.ok is True
    assert chain.status == vt.CHAIN_OK
    assert chain.checked == 3


def test_chain_is_additive_does_not_change_content_hashes(isolated_trail):
    """record_hash must not alter normalized_hash / content_hash (no spurious CHANGED)."""
    from app.text_normalization import normalize_for_change_hash, stable_normalized_hash

    text = _long_text("A")
    rec = _seed("AE-one", "run00001", text)

    # normalized_hash still equals what the pipeline computes from the raw text —
    # chaining did not touch it.
    combined = text  # single-source, no PDF → combined_raw_text == text
    assert rec["normalized_hash"] == stable_normalized_hash(combined)
    # record_hash is present and distinct from the content hashes.
    assert rec["record_hash"]
    assert rec["record_hash"] != rec["normalized_hash"]
    assert rec["record_hash"] != rec.get("content_hash")


def test_verify_trail_ok_includes_chain(isolated_trail):
    _seed("AE-one", "run00001", _long_text("A"))
    _seed("AE-two", "run00002", _long_text("B"))
    report = vt.verify_trail()
    assert report.ok is True
    assert report.chain.status == vt.CHAIN_OK
    assert report.chain.checked == 2


# ── tampering breaks the chain at that link ──────────────────────────────────

def test_tamper_middle_record_breaks_chain_at_that_link(isolated_trail):
    _seed("AE-one", "run00001", _long_text("A"))
    _seed("AE-two", "run00002", _long_text("B"))
    _seed("AE-three", "run00003", _long_text("C"))

    records = sr._read_runs()
    # Edit an identifying field of the MIDDLE record without recomputing its hash.
    tampered = [dict(r) for r in records]
    tampered[1]["change_status"] = "TAMPERED"
    _rewrite(tampered)

    chain = vt.verify_chain(sr._read_runs())
    assert chain.ok is False
    assert chain.status == vt.CHAIN_BROKEN
    # First break is at the tampered record (chained index 1), and it is the
    # record_hash that no longer recomputes.
    assert chain.break_index == 1
    assert chain.break_run_id == "run00002"
    assert "record_hash does not recompute" in (chain.reason or "")


def test_tamper_normalized_hash_field_breaks_chain(isolated_trail):
    """normalized_hash is an identifying field — editing it breaks the chain."""
    _seed("AE-one", "run00001", _long_text("A"))
    _seed("AE-two", "run00002", _long_text("B"))

    records = sr._read_runs()
    tampered = [dict(r) for r in records]
    tampered[0]["normalized_hash"] = "0" * 64
    _rewrite(tampered)

    chain = vt.verify_chain(sr._read_runs())
    assert chain.ok is False
    assert chain.break_index == 0
    assert chain.break_run_id == "run00001"


def test_deleting_a_record_breaks_chain(isolated_trail):
    _seed("AE-one", "run00001", _long_text("A"))
    _seed("AE-two", "run00002", _long_text("B"))
    _seed("AE-three", "run00003", _long_text("C"))

    records = sr._read_runs()
    # Drop the middle record → record 3's prev pointer no longer matches record 1.
    _rewrite([records[0], records[2]])

    chain = vt.verify_chain(sr._read_runs())
    assert chain.ok is False
    assert chain.status == vt.CHAIN_BROKEN
    # The surviving second record (run00003) is where the prev pointer diverges.
    assert chain.break_index == 1
    assert chain.break_run_id == "run00003"
    assert "prev_record_hash" in (chain.reason or "")


def test_reordering_records_breaks_chain(isolated_trail):
    _seed("AE-one", "run00001", _long_text("A"))
    _seed("AE-two", "run00002", _long_text("B"))
    _seed("AE-three", "run00003", _long_text("C"))

    records = sr._read_runs()
    _rewrite([records[0], records[2], records[1]])  # swap last two

    chain = vt.verify_chain(sr._read_runs())
    assert chain.ok is False
    assert chain.status == vt.CHAIN_BROKEN


def test_cli_reports_broken_chain_exit_one(isolated_trail, capsys):
    _seed("AE-one", "run00001", _long_text("A"))
    _seed("AE-two", "run00002", _long_text("B"))
    records = sr._read_runs()
    tampered = [dict(r) for r in records]
    tampered[0]["change_status"] = "TAMPERED"
    _rewrite(tampered)

    exit_code = vt.run_cli([])
    out = capsys.readouterr().out
    assert exit_code == 1
    assert "Hash chain: BROKEN" in out
    assert "RESULT: FAIL" in out


# ── --chain CLI mode ─────────────────────────────────────────────────────────

def test_chain_cli_mode_pass(isolated_trail, capsys):
    _seed("AE-one", "run00001", _long_text("A"))
    _seed("AE-two", "run00002", _long_text("B"))
    exit_code = vt.run_cli(["--chain"])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Hash chain: intact" in out
    assert "RESULT: PASS" in out


def test_chain_cli_mode_json(isolated_trail, capsys):
    _seed("AE-one", "run00001", _long_text("A"))
    exit_code = vt.run_cli(["--chain", "--json"])
    out = capsys.readouterr().out
    assert exit_code == 0
    payload = json.loads(out)
    assert payload["status"] == vt.CHAIN_OK
    assert payload["ok"] is True
    assert payload["checked"] == 1


# ── legacy pre-chain records are tolerated ───────────────────────────────────

def test_legacy_records_without_record_hash_are_tolerated(isolated_trail):
    """A trail of only legacy records (no record_hash) is CHAIN_EMPTY, not broken."""
    legacy = [
        {"source_id": "AE-old", "run_id": "leg1", "change_status": "FIRST_SEEN",
         "normalized_hash": "a" * 64, "timestamp_utc": "2026-01-01T00:00:00+00:00"},
        {"source_id": "AE-old", "run_id": "leg2", "change_status": "UNCHANGED",
         "normalized_hash": "a" * 64, "timestamp_utc": "2026-01-02T00:00:00+00:00"},
    ]
    _rewrite(legacy)
    chain = vt.verify_chain(sr._read_runs())
    assert chain.status == vt.CHAIN_EMPTY
    assert chain.ok is True
    assert chain.checked == 0


def test_chain_starts_at_first_record_hash_bearing_record(isolated_trail):
    """Legacy records BEFORE the first chained record are skipped; chain begins there."""
    legacy = {
        "source_id": "AE-old", "run_id": "leg1", "change_status": "FIRST_SEEN",
        "normalized_hash": "a" * 64, "timestamp_utc": "2026-01-01T00:00:00+00:00",
    }
    _rewrite([legacy])
    # Append real chained records after the legacy record.
    _seed("AE-one", "run00001", _long_text("A"))
    _seed("AE-one", "run00002", _long_text("B"))

    records = sr._read_runs()
    # The first chained record links from "" (chain begins fresh after legacy).
    first_chained = next(r for r in records if r.get("record_hash"))
    assert first_chained["prev_record_hash"] == ""

    chain = vt.verify_chain(records)
    assert chain.ok is True
    assert chain.status == vt.CHAIN_OK
    assert chain.checked == 2  # only the two chained records counted


def test_legacy_record_after_chain_started_breaks_chain(isolated_trail):
    """Once chained, a record without record_hash is a break (chain must be continuous)."""
    _seed("AE-one", "run00001", _long_text("A"))
    _seed("AE-one", "run00002", _long_text("B"))
    records = sr._read_runs()
    # Insert a legacy (unchained) record between the two chained records.
    legacy = {
        "source_id": "AE-x", "run_id": "legX", "change_status": "UNCHANGED",
        "normalized_hash": "b" * 64, "timestamp_utc": "2026-06-01T00:00:00+00:00",
    }
    _rewrite([records[0], legacy, records[1]])

    chain = vt.verify_chain(sr._read_runs())
    assert chain.ok is False
    assert chain.break_run_id == "legX"
    assert "no record_hash" in (chain.reason or "")


# ── retention compaction keeps the chain verifiable ──────────────────────────

def _monkeytime(monkeypatch, ts: datetime) -> None:
    monkeypatch.setattr(sr, "now_utc", lambda: ts.isoformat())


NOW = datetime(2026, 7, 5, 12, 0, 0, tzinfo=timezone.utc)


def test_heartbeat_compaction_keeps_chain_verifiable(isolated_trail, monkeypatch):
    from app.retention import compact_heartbeats

    source = {
        "id": "src-a", "name": "T", "url": "https://ex.gov.ae/a",
        "jurisdiction": "AE", "category": "financial_regulator",
    }
    old = NOW - timedelta(days=45)
    # First record classifies FIRST_SEEN (no prior) → kept forever; the next 3
    # are UNCHANGED heartbeats on the same old UTC day (compact to last-of-day);
    # plus 1 recent heartbeat (kept, < threshold).
    for h in (1, 6, 12, 23):
        _monkeytime(monkeypatch, old.replace(hour=h))
        sr.record_heartbeat(source, normalized_hash="a" * 64, extracted_chars=1000,
                            normalized_chars=900, extraction_quality="GOOD")
    _monkeytime(monkeypatch, NOW - timedelta(days=2))
    sr.record_heartbeat(source, normalized_hash="a" * 64, extracted_chars=1000,
                        normalized_chars=900, extraction_quality="GOOD")

    assert vt.verify_chain(sr._read_runs()).ok is True

    stats = compact_heartbeats(days_threshold=30, now=NOW)
    assert stats["removed"] == 2  # 3 old same-day heartbeats → 1 last-of-day survivor

    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None
    chain = vt.verify_chain(sr._read_runs())
    assert chain.ok is True, chain.reason
    assert chain.status == vt.CHAIN_OK
    assert chain.checked == 3  # FIRST_SEEN + 1 old heartbeat survivor + 1 recent

    # Compaction is idempotent AND leaves the chain intact.
    first = sr._RUN_FILE.read_bytes()
    stats2 = compact_heartbeats(days_threshold=30, now=NOW)
    assert stats2["removed"] == 0
    assert sr._RUN_FILE.read_bytes() == first
    assert vt.verify_chain(sr._read_runs()).ok is True


def test_quality_drop_compaction_keeps_chain_verifiable(isolated_trail, monkeypatch):
    from app.retention import compact_quality_drop_repeats

    source = {
        "id": "src-a", "name": "T", "url": "https://ex.gov.ae/a",
        "jurisdiction": "AE", "category": "financial_regulator",
    }
    old = NOW - timedelta(days=45)

    def _append_status(ts: datetime, status: str) -> None:
        _monkeytime(monkeypatch, ts)
        rec = {
            "run_id": f"r{ts.hour:02d}",
            "source_id": "src-a",
            "official_url": source["url"],
            "change_status": status,
            "normalized_hash": "a" * 64,
            "content_hash": "a" * 64,
            "timestamp_utc": ts.isoformat(),
        }
        # Chain-append directly (bypass classify_change so we control statuses).
        sr._locked_append_record(rec)
        sr._CACHE_VALID = False
        sr._RUNS_CACHE = None

    # Transition (kept forever) + a run of old repeats over one day + recovery.
    _append_status(old.replace(hour=1), "QUALITY_DROP")   # transition
    _append_status(old.replace(hour=6), "QUALITY_DROP")   # old repeat
    _append_status(old.replace(hour=12), "QUALITY_DROP")  # old repeat
    _append_status(old.replace(hour=23), "QUALITY_DROP")  # old repeat (last-of-day)

    assert vt.verify_chain(sr._read_runs()).ok is True

    stats = compact_quality_drop_repeats(days_threshold=30, now=NOW)
    assert stats["removed"] == 2  # 3 old repeats → 1 last-of-day survivor

    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None
    chain = vt.verify_chain(sr._read_runs())
    assert chain.ok is True, chain.reason
    assert chain.status == vt.CHAIN_OK

    # Idempotent, chain still intact.
    first = sr._RUN_FILE.read_bytes()
    stats2 = compact_quality_drop_repeats(days_threshold=30, now=NOW)
    assert stats2["removed"] == 0
    assert sr._RUN_FILE.read_bytes() == first
    assert vt.verify_chain(sr._read_runs()).ok is True


def test_relink_chain_helper_produces_valid_chain(isolated_trail):
    """relink_chain over a survivor subset yields a chain that verifies clean."""
    _seed("AE-one", "run00001", _long_text("A"))
    _seed("AE-two", "run00002", _long_text("B"))
    _seed("AE-three", "run00003", _long_text("C"))
    records = sr._read_runs()

    # Simulate dropping the middle record, then re-link the survivors.
    survivors = [dict(records[0]), dict(records[2])]
    sr.relink_chain(survivors)

    assert survivors[0]["prev_record_hash"] == ""
    assert survivors[1]["prev_record_hash"] == survivors[0]["record_hash"]
    chain = vt.verify_chain(survivors)
    assert chain.ok is True
    assert chain.checked == 2


def test_relink_chain_noop_on_legacy_records(isolated_trail):
    """relink_chain does not manufacture a chain over legacy (unchained) records."""
    legacy = [
        {"source_id": "AE-old", "run_id": "leg1", "change_status": "FIRST_SEEN"},
        {"source_id": "AE-old", "run_id": "leg2", "change_status": "UNCHANGED"},
    ]
    sr.relink_chain(legacy)
    assert "record_hash" not in legacy[0]
    assert "record_hash" not in legacy[1]
