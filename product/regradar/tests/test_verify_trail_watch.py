"""
Tests for tools/verify_trail_watch.py — the continuous evidence-trail
self-check that makes the "evidence-backed" claim actually verify itself.

The wrapper runs the read-only verifier (tools/verify_evidence_trail.py) and,
on ANY divergence — a snapshot hash that no longer matches its stored evidence
hash, OR a broken tamper-evident chain link — pages the founder via
app.ops_alert.notify_founder(). On a clean trail it exits 0 quietly.

Strategy mirrors test_verify_evidence_trail.py: seed a tiny trail with the REAL
pipeline write path, spy on ops_alert.notify_founder (never touch the network),
and assert:

  * a clean trail → NO founder alert, exit 0,
  * a tampered snapshot → exactly ONE founder alert naming the divergence, exit 1,
  * a broken hash chain → exactly ONE founder alert naming the chain break, exit 1,
  * the alert is strictly best-effort — a notify_founder that RAISES is swallowed
    and the run still returns 1 (a watchdog must never crash on its own alert).

No network: notify_founder is patched; snapshots are written to an isolated dir.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

import app.ops_alert as ops_alert
import app.source_runs as sr
from tools import verify_trail_watch as vtw


# ── isolated trail fixture (mirrors test_verify_evidence_trail.py) ────────────

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


@pytest.fixture
def alert_spy(monkeypatch):
    """Capture every founder alert text; never hit the network."""
    calls: list[str] = []
    monkeypatch.setattr(ops_alert, "notify_founder", lambda t: calls.append(t) or True)
    return calls


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
    body = "\n\n".join(
        f"Regulatory obligation paragraph {i} for {marker}." for i in range(60)
    )
    return f"Circular {marker} — Published 2026-06-01\n\n{body}\n"


# ── clean trail → no alert, exit 0 ───────────────────────────────────────────

def test_clean_trail_no_alert_exit_zero(isolated_trail, alert_spy, capsys):
    _seed_source_run(source_id="AE-one", run_id="run00001", text=_long_text("A"))
    _seed_source_run(source_id="AE-two", run_id="run00002", text=_long_text("B"))

    exit_code = vtw.run_watch([])

    assert exit_code == 0
    assert alert_spy == [], "a clean trail must never page the founder"
    out = capsys.readouterr().out
    assert "intact" in out.lower()


def test_empty_trail_no_alert_exit_zero(isolated_trail, alert_spy):
    # Nothing recorded yet — an empty trail is clean, not a failure.
    assert vtw.run_watch([]) == 0
    assert alert_spy == []


# ── tampered snapshot → one alert naming the divergence, exit 1 ──────────────

def test_tampered_snapshot_alerts_once_exit_one(isolated_trail, alert_spy, capsys):
    rec = _seed_source_run(source_id="AE-one", run_id="run00001", text=_long_text("A"))
    _seed_source_run(source_id="AE-two", run_id="run00002", text=_long_text("B"))

    # Flip a single bit of the normalized snapshot → bytes no longer hash-match.
    norm_path = isolated_trail / rec["snapshot_normalized_path"]
    data = bytearray(norm_path.read_bytes())
    data[0] ^= 0x01
    norm_path.write_bytes(bytes(data))

    exit_code = vtw.run_watch([])

    assert exit_code == 1
    assert len(alert_spy) == 1, "a divergent trail must page the founder exactly once"
    body = alert_spy[0]
    assert "INTEGRITY FAILURE" in body
    assert "AE-one" in body and "run00001" in body
    # The intact record must not be named as diverging.
    assert "AE-two" not in body
    # Nothing leaks to stdout as an all-clear.
    assert "intact" not in capsys.readouterr().out.lower()


def test_tampered_raw_snapshot_alerts(isolated_trail, alert_spy):
    rec = _seed_source_run(source_id="AE-one", run_id="run00001", text=_long_text("A"))
    raw_path = isolated_trail / rec["snapshot_raw_path"]
    raw_path.write_bytes(raw_path.read_bytes() + b"TAMPER")

    assert vtw.run_watch([]) == 1
    assert len(alert_spy) == 1
    assert "AE-one" in alert_spy[0]


# ── broken hash chain → one alert naming the chain break, exit 1 ─────────────

def test_broken_chain_alerts_once_exit_one(isolated_trail, alert_spy):
    _seed_source_run(source_id="AE-one", run_id="run00001", text=_long_text("A"))
    _seed_source_run(source_id="AE-two", run_id="run00002", text=_long_text("B"))

    # Rewrite the trail with the second record's prev pointer corrupted in place
    # (delete-then-edit WITHOUT relinking) → the chain's link invariant breaks.
    lines = sr._RUN_FILE.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    import json as _json

    rec2 = _json.loads(lines[1])
    rec2["prev_record_hash"] = "0" * 64  # no longer equals rec1.record_hash
    lines[1] = _json.dumps(rec2, ensure_ascii=False)
    sr._RUN_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    sr._CACHE_VALID = False
    sr._RUNS_CACHE = None

    exit_code = vtw.run_watch([])

    assert exit_code == 1
    assert len(alert_spy) == 1
    assert "chain BROKEN" in alert_spy[0]


# ── best-effort: an alert that RAISES is swallowed, run still returns 1 ───────

def test_alert_failure_is_swallowed_still_exit_one(isolated_trail, monkeypatch):
    rec = _seed_source_run(source_id="AE-one", run_id="run00001", text=_long_text("A"))
    norm_path = isolated_trail / rec["snapshot_normalized_path"]
    norm_path.write_bytes(norm_path.read_bytes() + b"X")

    def _boom(_text):  # notify_founder that misbehaves
        raise RuntimeError("telegram exploded")

    monkeypatch.setattr(ops_alert, "notify_founder", _boom)

    # Must not raise, and must still report the divergence via exit code.
    assert vtw.run_watch([]) == 1


# ── summary builder shape ────────────────────────────────────────────────────

def test_summary_caps_detail_lines(isolated_trail):
    # More divergences than the detail cap → the surplus is summarised, not dumped.
    recs = []
    for i in range(vtw._MAX_DETAIL_LINES + 3):
        r = _seed_source_run(source_id=f"AE-{i:02d}", run_id=f"run{i:05d}", text=_long_text(str(i)))
        recs.append(r)
    for r in recs:
        p = isolated_trail / r["snapshot_normalized_path"]
        p.write_bytes(p.read_bytes() + b"Z")

    report = vtw.vt.verify_trail()
    summary = vtw.build_divergence_summary(report)
    assert "and 3 more" in summary
    assert summary.startswith("\U0001F6A8")
