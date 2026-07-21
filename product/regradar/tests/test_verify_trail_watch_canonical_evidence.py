"""
Tests for the canonical-evidence pass added to tools/verify_trail_watch.py.

run_watch() re-verifies the source-evidence trail and the sealed decision chain,
and now ALSO re-validates every customer-held canonical
``evidence/**/evidence-record.json`` on the same daily timer. This pass walks
``app.evidence_records.list_canonical_evidence_records`` and re-runs
``app.evidence_records.validate_evidence_record`` — which re-hashes the sealed
raw/normalized/diff artifacts against their stored values AND enforces the record
self-seal. A record that no longer re-validates is POSITIVE tamper: page the
founder best-effort and force exit 1. A missing/unreadable tree is best-effort:
never a false alarm.

Strategy mirrors test_verify_trail_watch.py: keep the source trail and decision
store empty+isolated so the ONLY signal comes from the canonical evidence tree,
spy on ops_alert.notify_founder (never hit the network), and assert:

  * a clean canonical tree → NO founder alert, exit 0,
  * a tampered sealed artifact → exactly ONE founder alert naming the record,
    exit 1,
  * a tampered record self-seal → exactly ONE founder alert, exit 1,
  * a missing evidence tree → best-effort, no alarm, exit 0,
  * a list-time failure (our own infra hiccup) → swallowed, no alarm, exit 0.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

import app.db as app_db
import app.decision_records as decision_records
import app.evidence_records as evidence_records
import app.ops_alert as ops_alert
import app.source_runs as sr
from app.evidence_records import canonical_record_hash
from tools import verify_trail_watch as vtw


# ── isolation fixture ─────────────────────────────────────────────────────────
#
# The canonical-evidence pass anchors to source_runs._BASE_DIR (the same base dir
# the rest of the watchdog uses). Isolating that — plus the source-runs trail and
# the decision store — means the ONLY thing the watchdog can page about is the
# canonical evidence tree we seed under tmp_path/evidence.

@pytest.fixture
def isolated_base(tmp_path, monkeypatch):
    monkeypatch.setattr(sr, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(sr, "_RUN_DIR", tmp_path / "data" / "source_runs")
    monkeypatch.setattr(sr, "_RUN_FILE", tmp_path / "data" / "source_runs" / "source_runs.jsonl")
    monkeypatch.setattr(sr, "_SNAPSHOT_DIR", tmp_path / "data" / "source_snapshots")
    # Keep evidence_records' own default base consistent with the anchored base,
    # so any default-base call resolves the isolated tree too.
    monkeypatch.setattr(evidence_records, "_BASE_DIR", tmp_path)
    # Empty, isolated decision store so the decision-chain pass never pages.
    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "decisions.db"))
    monkeypatch.setattr(decision_records, "_BASE_DIR", tmp_path)
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


# ── canonical evidence record seeding ────────────────────────────────────────

def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_canonical_record(
    base: Path,
    *,
    source_id: str = "AE-dfsa-test",
    record_id: str = "evr_dfsa_test_20260620T000000Z",
    seal: bool = False,
) -> dict:
    """Write a complete, valid canonical evidence-record.json under base/evidence.

    Mirrors the artifacts create_canonical_evidence_record seals: the normalized
    current/previous snapshots feed content.current_hash / previous_hash. When
    ``seal`` is set, a self-seal (record_hash over the content block) is added so
    a tampered self-seal can be exercised too.
    """
    import hashlib

    record_dir = base / "evidence" / "dfsa" / source_id / "run_20260620T000000Z"
    current_text = "Current official DFSA regulatory text for the watchdog test."
    previous_text = "Previous official DFSA regulatory text for the watchdog test."
    _write(record_dir / "current.normalized.txt", current_text)
    _write(record_dir / "previous.normalized.txt", previous_text)
    _write(record_dir / "raw.html", "<main>Current official DFSA regulatory text</main>")
    _write(record_dir / "snapshot.html", "<html><body><main>x</main></body></html>")
    _write(record_dir / "metadata.json", json.dumps({"provider": "fixture"}, sort_keys=True))
    _write(record_dir / "diff.txt", "- Previous official DFSA regulatory text\n+ Current official DFSA regulatory text\n")

    current_hash = hashlib.sha256(current_text.encode("utf-8")).hexdigest()
    previous_hash = hashlib.sha256(previous_text.encode("utf-8")).hexdigest()

    content = {
        "previous_hash": f"sha256:{previous_hash}",
        "current_hash": f"sha256:{current_hash}",
        "raw_content_path": str((record_dir / "raw.html").relative_to(base)),
        "normalized_current_path": str((record_dir / "current.normalized.txt").relative_to(base)),
        "normalized_previous_path": str((record_dir / "previous.normalized.txt").relative_to(base)),
    }
    record = {
        "schema_version": "2.0",
        "record_id": record_id,
        "record_status": "complete",
        "source": {
            "source_id": source_id,
            "regulator": "DFSA",
            "official_url": "https://www.dfsa.ae/example",
            "source_name": "DFSA Test Source",
        },
        "run": {
            "run_id": "run_20260620T000000Z",
            "timestamp": "2026-06-20T00:00:00Z",
            "status": "CHANGED",
        },
        "content": content,
        "change": {
            "diff_path": str((record_dir / "diff.txt").relative_to(base)),
            "summary": "Evidence-only DFSA fixture summary.",
            "lines_added": 1,
            "lines_removed": 1,
        },
        "files": {
            "snapshot_path": str((record_dir / "snapshot.html").relative_to(base)),
            "raw_path": str((record_dir / "raw.html").relative_to(base)),
            "normalized_path": str((record_dir / "current.normalized.txt").relative_to(base)),
            "previous_path": str((record_dir / "previous.normalized.txt").relative_to(base)),
            "metadata_path": str((record_dir / "metadata.json").relative_to(base)),
            "diff_path": str((record_dir / "diff.txt").relative_to(base)),
        },
        "integrity": {
            "hash_verified": True,
            "integrity_status": "VERIFIED",
            "verified_at": "2026-06-20T00:01:00Z",
        },
        "review": {
            "human_review_required": True,
            "review_status": "approved",
            "review_reason": "Customer-facing brief requires human review.",
        },
    }
    if seal:
        record["record_hash"] = f"sha256:{canonical_record_hash(content)}"
        record["record_hash_method"] = evidence_records.RECORD_HASH_METHOD

    (record_dir / "evidence-record.json").write_text(
        json.dumps(record, indent=2, sort_keys=True), encoding="utf-8"
    )
    return record


def _record_path(base: Path, record: dict) -> Path:
    src = record["source"]["source_id"]
    return base / "evidence" / "dfsa" / src / "run_20260620T000000Z" / "evidence-record.json"


# ── clean canonical tree → no alert, exit 0 ──────────────────────────────────

def test_clean_canonical_evidence_no_alert_exit_zero(isolated_base, alert_spy):
    record = _seed_canonical_record(isolated_base)
    # Sanity: the seeded record really does validate before we watch it.
    assert evidence_records.validate_evidence_record(record, base_dir=isolated_base)["valid"]

    exit_code = vtw.run_watch([])

    assert exit_code == 0
    assert alert_spy == [], "a clean canonical evidence tree must never page the founder"


def test_missing_evidence_tree_no_alert_exit_zero(isolated_base, alert_spy):
    # No evidence/ dir at all — a missing tree is best-effort, not a failure.
    assert not (isolated_base / "evidence").exists()

    assert vtw.run_watch([]) == 0
    assert alert_spy == []


# ── tampered sealed artifact → one alert naming the record, exit 1 ───────────

def test_tampered_normalized_artifact_pages_founder_exit_one(
    isolated_base, alert_spy
):
    record = _seed_canonical_record(isolated_base)
    # Flip the normalized current snapshot — the bytes no longer hash-match the
    # sealed content.current_hash, so validation fails.
    norm = isolated_base / record["content"]["normalized_current_path"]
    data = bytearray(norm.read_bytes())
    data[0] ^= 0x01
    norm.write_bytes(bytes(data))

    exit_code = vtw.run_watch([])

    assert exit_code == 1
    assert len(alert_spy) == 1, "a tampered evidence record must page the founder exactly once"
    body = alert_spy[0]
    assert body.startswith("\U0001F6A8")
    assert "INTEGRITY FAILURE" in body
    assert record["record_id"] in body
    assert record["source"]["source_id"] in body


def test_tampered_record_self_seal_pages_founder_exit_one(isolated_base, alert_spy):
    # A self-sealed record whose content block is edited in place after sealing:
    # every artifact still hash-matches, but the record_hash no longer recomputes.
    record = _seed_canonical_record(isolated_base, seal=True)
    path = _record_path(isolated_base, record)
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    on_disk["content"]["current_hash"] = "sha256:" + "b" * 64  # break the self-seal
    path.write_text(json.dumps(on_disk, indent=2, sort_keys=True), encoding="utf-8")

    exit_code = vtw.run_watch([])

    assert exit_code == 1
    assert len(alert_spy) == 1
    assert record["record_id"] in alert_spy[0]


# ── benign non-certified records are NOT tamper → no page, exit 0 ────────────

def test_uncertified_record_is_not_tamper_no_alert_exit_zero(
    isolated_base, alert_spy
):
    """A record that fails validation for a NON-tamper reason must never page.

    validate_evidence_record is a completeness + brief-eligibility gate as well
    as a tamper check. The product legitimately writes records it never certified
    — most notably the VARA-mojibake QUARANTINE record
    (record_status='integrity_error', written whenever normalized content is
    undecodable/empty). Those fail validation (record_status must be complete,
    integrity not VERIFIED, content unreadable) with NO hash/self-seal mismatch.
    Every sealed artifact still hash-matches, so this is a normal, untampered
    state — not tamper. The watchdog must not page the founder on it, or it would
    false-alarm on every scheduled run for as long as any such record exists.
    """
    record = _seed_canonical_record(isolated_base)
    path = _record_path(isolated_base, record)
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    # Turn the seeded record into a legitimate quarantine record WITHOUT touching
    # any sealed artifact: the raw/normalized/diff bytes still hash-match, so the
    # only validation errors are completeness/integrity-status ones — no mismatch.
    on_disk["record_status"] = "integrity_error"
    on_disk["integrity"] = {
        "hash_verified": False,
        "integrity_status": "FAILED",
        "verified_at": "2026-06-20T00:01:00Z",
    }
    path.write_text(json.dumps(on_disk, indent=2, sort_keys=True), encoding="utf-8")

    # Guard the test's own premise: validation fails, but NOT for a "does not
    # match" (hash/self-seal) reason.
    reloaded = json.loads(path.read_text(encoding="utf-8"))
    validation = evidence_records.validate_evidence_record(
        reloaded, base_dir=isolated_base
    )
    assert not validation["valid"]
    assert not any("does not match" in e for e in validation["errors"])

    exit_code = vtw.run_watch([])

    assert exit_code == 0
    assert alert_spy == [], (
        "a legitimate non-certified record (quarantine) is not tamper and must "
        "never page the founder"
    )


# ── best-effort: infra failures are swallowed, never a false alarm ───────────

def test_missing_dir_via_list_is_best_effort(isolated_base, alert_spy, monkeypatch):
    # Simulate an unreadable tree: list_canonical_evidence_records raises. That is
    # our own infra hiccup, never positive tamper — no page, clean verdict stands.
    def _boom(*_args, **_kwargs):
        raise OSError("evidence dir unreadable")

    monkeypatch.setattr(evidence_records, "list_canonical_evidence_records", _boom)

    exit_code = vtw.run_watch([])
    assert exit_code == 0
    assert alert_spy == []


def test_alert_failure_is_swallowed_still_exit_one(isolated_base, monkeypatch):
    # A notify_founder that RAISES must be swallowed; the divergence is still
    # reported via the exit code (a watchdog must never crash on its own alert).
    record = _seed_canonical_record(isolated_base)
    norm = isolated_base / record["content"]["normalized_current_path"]
    norm.write_bytes(norm.read_bytes() + b"TAMPER")

    def _explode(_text):
        raise RuntimeError("telegram exploded")

    monkeypatch.setattr(ops_alert, "notify_founder", _explode)

    assert vtw.run_watch([]) == 1


# ── summary builder shape ────────────────────────────────────────────────────

def test_canonical_evidence_summary_caps_detail_lines():
    tampered = [
        {"record_id": f"evr_{i}", "source_id": f"AE-{i}", "errors": ["hash mismatch"]}
        for i in range(vtw._MAX_DETAIL_LINES + 4)
    ]
    summary = vtw.build_canonical_evidence_divergence_summary(tampered)
    assert summary.startswith("\U0001F6A8")
    assert "INTEGRITY FAILURE" in summary
    assert "and 4 more" in summary
