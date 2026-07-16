"""
Auto-seal keystone tests (goal Phase 1.1).

The product promise is "seals each capture" — with NO operator step. Before
this fix the in-pipeline seal attempt gated on run_record_candidate
["proof_block_path"], a key never set before the gate, so the live path NEVER
sealed and the only working path was the manual batch command
`run.py create-canonical-evidence`.

These tests lock the repaired invariant:

(i)   a live FIRST_SEEN run auto-seals a canonical evidence record;
(ii)  a live CHANGED run auto-seals BEFORE the deferred alert send, and the
      sealed record is resolvable as the alert's ``proof`` block
      (alert_proof surfaces only record_status == "complete" records);
(iii) a seal failure is non-fatal — the alert still goes out (the trail
      append is the durability anchor; the batch command recovers the seal).

Hermetic: no network, no real Telegram; trail + evidence tree in tmp_path.
The seal call passes base_dir=source_runs._BASE_DIR, so isolating the trail
isolates the evidence tree too — asserted here by writing under tmp only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from app.text_normalization import normalize_for_change_hash, stable_content_hash

_BASE_TEXT = "\n\n".join(f"Regulatory obligation paragraph {i}." for i in range(80))
_CHANGED_TEXT = (
    "NEW penalty clause: a sanction and fine apply for non-compliance.\n\n"
    + _BASE_TEXT
)
_HTML = "<html><body>irrelevant — extract is patched</body></html>"

# Live-pipeline hash shape (flavor B): stable_content_hash over the normalized
# text — exactly the EV-3 case the seal must accept for the previous run.
_BASE_NORMALIZED = normalize_for_change_hash(_BASE_TEXT)
_BASE_HASH = stable_content_hash(_BASE_NORMALIZED)

_SOURCE = {
    "name": "Auto Seal Source",
    "url": "https://example.gov.ae/auto-seal",
    "jurisdiction": "AE",
    "category": "financial_regulator",
    "enabled": True,
}


def _source_id() -> str:
    from app.source_runs import make_source_id

    return make_source_id(_SOURCE)


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


def _seed_baseline(tmp_path) -> None:
    """Seed a FIRST_SEEN baseline whose snapshot satisfies the seal's
    previous-run integrity check (file re-hash vs normalized_hash, flavor B)."""
    import app.source_runs as sr

    sid = _source_id()
    snap_dir = tmp_path / "data" / "source_snapshots" / "2026-06-20" / "AE" / sid / "seed0001"
    snap_dir.mkdir(parents=True, exist_ok=True)
    (snap_dir / "normalized.txt").write_text(_BASE_NORMALIZED, encoding="utf-8")
    sr._RUN_FILE.write_text(
        json.dumps(
            {
                "run_id": "seed0001",
                "source_id": sid,
                "source_name": _SOURCE["name"],
                "official_url": _SOURCE["url"],
                "url": _SOURCE["url"],
                "change_status": "FIRST_SEEN",
                "extraction_quality": "GOOD",
                "extracted_chars": len(_BASE_TEXT),
                "normalized_chars": len(_BASE_NORMALIZED),
                "normalized_hash": _BASE_HASH,
                "raw_hash": "e" * 64,
                "snapshot_normalized_path": (
                    f"data/source_snapshots/2026-06-20/AE/{sid}/seed0001/normalized.txt"
                ),
                "timestamp_utc": "2026-06-20T10:00:00+00:00",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    sr._CACHE_VALID = False


def _sealed_record_paths(tmp_path) -> list[Path]:
    return sorted((tmp_path / "evidence").glob("*/*/*/evidence-record.json"))


def _run_live(monkeypatch_ctx_patches: list, alerts: bool):
    """Run run_pipeline_for_source under the standard hermetic patch set."""
    from app.pipeline import init_pipeline, run_pipeline_for_source

    init_pipeline(0)
    with patch("app.pipeline.ENABLE_TELEGRAM_ALERTS", alerts), patch(
        "app.pipeline.fetch_page", return_value=_HTML
    ), patch(
        "app.pipeline.get_adapter_for_url", return_value=None
    ), patch(
        "app.pipeline.save_document", return_value=None
    ):
        ctx_stack = []
        try:
            for p in monkeypatch_ctx_patches:
                ctx_stack.append(p.__enter__())
            return run_pipeline_for_source(_SOURCE)
        finally:
            for p in reversed(monkeypatch_ctx_patches):
                p.__exit__(None, None, None)


# ══════════════════════════════════════════════════════════════════════════
# (i) FIRST_SEEN auto-seals — no operator command
# ══════════════════════════════════════════════════════════════════════════
def test_first_seen_run_auto_seals(isolated_dirs):
    result = _run_live(
        [
            patch("app.pipeline.extract_best_text", return_value={"text": _BASE_TEXT, "method": "t"}),
            patch("app.pipeline.get_latest_document", return_value=None),
        ],
        alerts=False,
    )

    assert result.get("canonical_evidence_sealed") is True, (
        "a FIRST_SEEN live run must auto-seal without any operator command"
    )
    sealed = _sealed_record_paths(isolated_dirs)
    assert len(sealed) == 1, f"exactly one canonical record expected, got {sealed}"
    record = json.loads(sealed[0].read_text(encoding="utf-8"))
    assert record.get("record_status") == "complete"
    assert str(record.get("record_hash", "")).startswith("sha256:")


# ══════════════════════════════════════════════════════════════════════════
# (ii) CHANGED auto-seals BEFORE the alert send; alert can carry the proof
# ══════════════════════════════════════════════════════════════════════════
def test_changed_run_seals_before_alert_and_proof_resolves(isolated_dirs):
    _seed_baseline(isolated_dirs)

    sealed_at_send_time: list = []

    def _send_spy(payload):
        # Ordering keystone: at the moment the alert leaves, the canonical
        # sealed record must ALREADY exist on disk.
        sealed_at_send_time.append(len(_sealed_record_paths(isolated_dirs)))
        return True

    result = _run_live(
        [
            patch("app.pipeline.extract_best_text", return_value={"text": _CHANGED_TEXT, "method": "t"}),
            patch(
                "app.pipeline.get_latest_document",
                return_value={"content": _BASE_TEXT, "content_hash": _BASE_HASH},
            ),
            patch("app.telegram.send_telegram_alert", side_effect=_send_spy),
        ],
        alerts=True,
    )

    assert result["changed"] is True
    assert result.get("telegram_sent") is True, "a genuine change must alert"
    assert result.get("canonical_evidence_sealed") is True, (
        "a live CHANGED run must auto-seal — this was the dead-code gap: "
        "alerts used to go out with NO sealed record until a manual batch run"
    )
    assert sealed_at_send_time == [1], (
        "the sealed record must exist BEFORE the alert send "
        f"(records on disk at send time: {sealed_at_send_time})"
    )

    # The alert's proof block resolves from the sealed record — this is what
    # makes the customer-facing alert verifiable. Candidates carry the run's
    # snapshot proof block; alert_proof recovers the run id from a snapshot
    # path (.../<source_id>/<run_id>/<file>), exactly as routing does.
    run_id = result["run_record"]["run_id"]
    from app.alert_proof import build_proof_for_candidate

    proof = build_proof_for_candidate(
        {
            "source_id": _source_id(),
            "proof_block": {
                "snapshot_normalized_path": result["run_record"]["snapshot_normalized_path"],
            },
        },
        base_dir=isolated_dirs,
    )
    assert proof is not None, (
        "alert_proof must resolve the auto-sealed record (record_status complete)"
    )
    assert str(proof.get("record_hash", "")).startswith("sha256:")
    assert proof.get("run_id") == run_id


# ══════════════════════════════════════════════════════════════════════════
# (iii) A seal failure never blocks the alert
# ══════════════════════════════════════════════════════════════════════════
def test_seal_failure_does_not_block_alert(isolated_dirs):
    _seed_baseline(isolated_dirs)

    sends: list = []

    result = _run_live(
        [
            patch("app.pipeline.extract_best_text", return_value={"text": _CHANGED_TEXT, "method": "t"}),
            patch(
                "app.pipeline.get_latest_document",
                return_value={"content": _BASE_TEXT, "content_hash": _BASE_HASH},
            ),
            patch("app.telegram.send_telegram_alert", side_effect=lambda p: sends.append(p) or True),
            patch(
                "app.evidence_records.create_canonical_evidence_record",
                side_effect=RuntimeError("seal exploded"),
            ),
        ],
        alerts=True,
    )

    assert result["changed"] is True
    assert result.get("canonical_evidence_sealed") is False
    assert result.get("telegram_sent") is True and len(sends) == 1, (
        "the trail append is the durability anchor — a canonical-seal failure "
        "must never suppress the alert (batch command recovers the seal later)"
    )


# ══════════════════════════════════════════════════════════════════════════
# (iv) An idempotent duplicate ("already exists") is NOT a failure
# ══════════════════════════════════════════════════════════════════════════
def test_duplicate_seal_reports_sealed_not_failed(isolated_dirs):
    """A record sealed by a previous attempt IS sealed — the duplicate raise
    must report sealed=True (INFO), not pollute logs with the WARNING that
    matters for real integrity failures (silent-failure review, finding 2)."""
    from app.evidence_records import EvidenceRecordError

    _seed_baseline(isolated_dirs)

    result = _run_live(
        [
            patch("app.pipeline.extract_best_text", return_value={"text": _CHANGED_TEXT, "method": "t"}),
            patch(
                "app.pipeline.get_latest_document",
                return_value={"content": _BASE_TEXT, "content_hash": _BASE_HASH},
            ),
            patch(
                "app.evidence_records.create_canonical_evidence_record",
                side_effect=EvidenceRecordError("Canonical evidence record already exists: evidence/x"),
            ),
        ],
        alerts=False,
    )

    assert result.get("canonical_evidence_sealed") is True, (
        "an already-sealed duplicate must count as sealed, not as a failure"
    )


# ══════════════════════════════════════════════════════════════════════════
# (v) Seal deadman: systemic failure alerts the founder once, recovery clears
# ══════════════════════════════════════════════════════════════════════════
def test_seal_deadman_alerts_on_systemic_failure_and_recovery(isolated_dirs, monkeypatch):
    import app.monitor as mon

    state_file = isolated_dirs / "data" / "seal_deadman_state.json"
    monkeypatch.setattr(mon, "_SEAL_DEADMAN_STATE_FILE", state_file)

    notes: list = []
    monkeypatch.setattr("app.ops_alert.notify_founder", lambda text: notes.append(text) or True)

    base = {"cycle_id": "c1"}
    # All seals failed → one alert on the transition.
    mon._maybe_alert_seal_failures({**base, "seals_attempted": 3, "seals_failed": 3})
    assert len(notes) == 1 and "sealing FAILED" in notes[0]
    # Still failing → quiet (edge-triggered).
    mon._maybe_alert_seal_failures({**base, "seals_attempted": 2, "seals_failed": 2})
    assert len(notes) == 1
    # Recovery → one recovery note, flag cleared.
    mon._maybe_alert_seal_failures({**base, "seals_attempted": 4, "seals_failed": 0})
    assert len(notes) == 2 and "recovered" in notes[1]
    # No attempts → no state change, no alert.
    mon._maybe_alert_seal_failures({**base, "seals_attempted": 0, "seals_failed": 0})
    assert len(notes) == 2
