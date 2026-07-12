"""Every routed alert binds to its sealed canonical evidence record.

Roadmap item: "signal not noise — each alert carries its proof". A routing /
preview match carries an additive ``proof`` block lifted from the canonical
evidence record (record id + self-seal ``record_hash`` + run id + normalized
hash + diff availability), so a customer can re-check the hashes without
trusting StatuteProof. Fail-soft is part of the contract: a candidate with no
resolvable sealed record yields ``proof: None`` and the alert flows unchanged.

Records are built via the REAL writer (``create_canonical_evidence_record``) —
no hand-faked digests — mirroring tests/test_canonical_record_hash.py.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db
from app.alert_proof import build_proof_for_candidate, run_id_from_proof_block
from app.evidence_records import create_canonical_evidence_record
from app.text_normalization import normalize_for_change_hash


# ── Fixture helpers (real writer, real snapshot layout) ────────────────────────

def _write_run(
    tmp_path: Path,
    *,
    source_id: str,
    run_id: str,
    text: str,
    change_status: str = "FIRST_SEEN",
) -> dict:
    """Write snapshot artifacts in the pipeline's layout and return the run record."""
    run_dir = tmp_path / "data" / "source_snapshots" / "2026-07-12" / "AE" / source_id / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    normalized = normalize_for_change_hash(text)
    (run_dir / "raw.txt").write_text(text, encoding="utf-8")
    (run_dir / "normalized.txt").write_text(normalized, encoding="utf-8")
    (run_dir / "metadata.json").write_text(json.dumps({"provider": "fixture"}), encoding="utf-8")
    (run_dir / "proof.json").write_text(json.dumps({"proof_quality": "GOOD"}), encoding="utf-8")
    return {
        "run_id": run_id,
        "timestamp_utc": "2026-07-12T10:00:00Z",
        "market": "AE",
        "source_id": source_id,
        "source_name": "CBUAE Proof Binding Test Source",
        "category": "regulatory",
        "official_url": "https://example.gov/proof-binding",
        "access_status": "accessible",
        "fetch_method": "fixture",
        "extraction_quality": "GOOD",
        "change_status": change_status,
        "normalized_hash": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "snapshot_raw_path": str((run_dir / "raw.txt").relative_to(tmp_path)),
        "snapshot_normalized_path": str((run_dir / "normalized.txt").relative_to(tmp_path)),
        "snapshot_metadata_path": str((run_dir / "metadata.json").relative_to(tmp_path)),
        "proof_block_path": str((run_dir / "proof.json").relative_to(tmp_path)),
    }


def _candidate_for_run(run: dict) -> dict:
    """An approved alert candidate shaped like a real draft (proof_block carried)."""
    return {
        "alert_id": f"draft-{run['run_id']}",
        "source_id": run["source_id"],
        "source_name": run["source_name"],
        "source_url": run["official_url"],
        "market": "AE",
        "risk_level": "MEDIUM",
        "change_type": "CIRCULAR_UPDATE",
        "review_status": "APPROVED_FOR_WEEKLY",
        "checked_at_utc": run["timestamp_utc"],
        "detected_at": run["timestamp_utc"],
        "executive_summary": "Reviewed source change summary for the proof-binding test.",
        "added_chunks": ["Firms are asked to review the updated reporting form."],
        "removed_chunks": [],
        "proof_block": {
            "source_id": run["source_id"],
            "official_url": run["official_url"],
            "normalized_hash": run["normalized_hash"],
            "snapshot_raw_path": run["snapshot_raw_path"],
            "snapshot_normalized_path": run["snapshot_normalized_path"],
            "proof_quality": "GOOD",
        },
    }


def _sealed_record(tmp_path: Path, *, source_id: str = "AE-cbuae-proof", run_id: str = "run00001") -> tuple[dict, dict]:
    """Create a genuine sealed canonical record; return (record, run_record)."""
    run = _write_run(
        tmp_path,
        source_id=source_id,
        run_id=run_id,
        text="Official regulatory text for the alert proof-binding tests.\n",
    )
    record = create_canonical_evidence_record(run, base_dir=tmp_path)
    return record, run


# ── run-id recovery ───────────────────────────────────────────────────────────

def test_run_id_recovered_from_snapshot_parent_dir(tmp_path):
    _record, run = _sealed_record(tmp_path)
    candidate = _candidate_for_run(run)
    assert run_id_from_proof_block(candidate["proof_block"]) == run["run_id"]


def test_run_id_empty_when_no_snapshot_paths():
    assert run_id_from_proof_block({"official_url": "https://example.gov"}) == ""
    assert run_id_from_proof_block(None) == ""


# ── proof block lifted from the real sealed record ───────────────────────────

def test_proof_block_lifts_real_seal_from_canonical_record(tmp_path):
    record, run = _sealed_record(tmp_path)
    proof = build_proof_for_candidate(_candidate_for_run(run), base_dir=tmp_path)

    assert proof is not None
    assert proof["evidence_record_id"] == record["record_id"]
    assert proof["record_hash"] == record["record_hash"]
    assert proof["record_hash"].startswith("sha256:")
    assert proof["run_id"] == run["run_id"]
    assert proof["normalized_hash"] == record["content"]["current_hash"]
    # FIRST_SEEN records carry no diff artifact.
    assert proof["diff_available"] is False


def test_proof_block_reports_diff_available_for_changed_record(tmp_path):
    source_id = "AE-cbuae-proof-changed"
    first = _write_run(
        tmp_path,
        source_id=source_id,
        run_id="run00001",
        text="Original obligations text before the change.\n",
    )
    changed = _write_run(
        tmp_path,
        source_id=source_id,
        run_id="run00002",
        text="Original obligations text before the change.\nFirms must file by 1 September 2026.\n",
        change_status="CHANGED",
    )
    create_canonical_evidence_record(changed, previous_run=first, base_dir=tmp_path)

    proof = build_proof_for_candidate(_candidate_for_run(changed), base_dir=tmp_path)
    assert proof is not None
    assert proof["diff_available"] is True


# ── fail-soft paths: proof is None, never an exception ────────────────────────

def test_no_evidence_record_yields_none(tmp_path):
    run = _write_run(tmp_path, source_id="AE-no-record", run_id="run99999", text="text\n")
    # No canonical record was written for this run.
    assert build_proof_for_candidate(_candidate_for_run(run), base_dir=tmp_path) is None


def test_candidate_without_proof_block_yields_none(tmp_path):
    assert build_proof_for_candidate({"source_id": "AE-x", "alert_id": "draft-x"}, base_dir=tmp_path) is None
    assert build_proof_for_candidate({}, base_dir=tmp_path) is None
    assert build_proof_for_candidate(None, base_dir=tmp_path) is None  # type: ignore[arg-type]


def test_unsealed_legacy_record_yields_none(tmp_path):
    """A record without its self-seal must not be presented as 'sealed evidence'."""
    record, run = _sealed_record(tmp_path, source_id="AE-legacy-unsealed")
    record_path = next((tmp_path / "evidence").glob("*/AE-legacy-unsealed/*/evidence-record.json"))
    legacy = json.loads(record_path.read_text(encoding="utf-8"))
    legacy.pop("record_hash", None)
    legacy.pop("record_hash_method", None)
    record_path.write_text(json.dumps(legacy), encoding="utf-8")

    assert build_proof_for_candidate(_candidate_for_run(run), base_dir=tmp_path) is None


def test_non_complete_record_yields_none(tmp_path):
    """A quarantined (integrity_error) record is not presentable proof."""
    _record, run = _sealed_record(tmp_path, source_id="AE-quarantined")
    record_path = next((tmp_path / "evidence").glob("*/AE-quarantined/*/evidence-record.json"))
    tampered = json.loads(record_path.read_text(encoding="utf-8"))
    tampered["record_status"] = "integrity_error"
    record_path.write_text(json.dumps(tampered), encoding="utf-8")

    assert build_proof_for_candidate(_candidate_for_run(run), base_dir=tmp_path) is None


def test_unsafe_path_segments_are_rejected(tmp_path):
    _record, run = _sealed_record(tmp_path)
    candidate = _candidate_for_run(run)
    candidate["source_id"] = "../evidence"
    assert build_proof_for_candidate(candidate, base_dir=tmp_path) is None

    candidate = _candidate_for_run(run)
    candidate["proof_block"]["snapshot_normalized_path"] = "data/x/*/normalized.txt"
    assert build_proof_for_candidate(candidate, base_dir=tmp_path) is None


# ── routing layer: normalize + full preview carry the proof block ─────────────

def test_normalize_alert_for_routing_carries_proof(tmp_path, monkeypatch):
    import app.evidence_records as evidence_records
    from app.alert_routing import normalize_alert_for_routing

    monkeypatch.setattr(evidence_records, "_BASE_DIR", tmp_path)
    record, run = _sealed_record(tmp_path)

    normalized = normalize_alert_for_routing(_candidate_for_run(run))
    assert normalized["proof"] is not None
    assert normalized["proof"]["evidence_record_id"] == record["record_id"]
    assert normalized["proof"]["record_hash"] == record["record_hash"]


def test_normalize_alert_for_routing_is_fail_soft_without_record(tmp_path, monkeypatch):
    import app.evidence_records as evidence_records
    from app.alert_routing import normalize_alert_for_routing

    monkeypatch.setattr(evidence_records, "_BASE_DIR", tmp_path)
    run = _write_run(tmp_path, source_id="AE-orphan", run_id="run77777", text="text\n")

    normalized = normalize_alert_for_routing(_candidate_for_run(run))
    # The alert still flows with every existing field intact.
    assert normalized["proof"] is None
    assert normalized["alert_id"] == f"draft-{run['run_id']}"
    assert normalized["source_url"] == run["official_url"]
    assert normalized["risk_level"] == "MEDIUM"


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "proof-binding.db"))
    yield tmp_path


def test_preview_match_carries_proof_and_fail_soft(isolated_db, monkeypatch):
    """End-to-end preview: sealed candidate carries the real seal; an orphan
    candidate flows with proof None (fail-soft) instead of being dropped."""
    import app.alert_routing as alert_routing
    import app.evidence_records as evidence_records
    from app.auth import create_user

    tmp_path = isolated_db
    monkeypatch.setattr(evidence_records, "_BASE_DIR", tmp_path)

    record, sealed_run = _sealed_record(tmp_path)
    orphan_run = _write_run(tmp_path, source_id="AE-orphan-2", run_id="run55555", text="text\n")

    candidates = [_candidate_for_run(sealed_run), _candidate_for_run(orphan_run)]
    monkeypatch.setattr(
        alert_routing, "load_approved_alert_candidates", lambda days, user_id=None: candidates
    )

    user_id = int(create_user("proof-binding@test.co", "password-123")["id"])
    preview = alert_routing.build_routing_preview_for_user(user_id)

    matches = {m["alert_id"]: m for m in preview["matches"]}
    assert set(matches) == {f"draft-{sealed_run['run_id']}", f"draft-{orphan_run['run_id']}"}

    sealed_match = matches[f"draft-{sealed_run['run_id']}"]
    assert sealed_match["proof"]["evidence_record_id"] == record["record_id"]
    assert sealed_match["proof"]["record_hash"] == record["record_hash"]
    assert sealed_match["proof"]["run_id"] == sealed_run["run_id"]

    orphan_match = matches[f"draft-{orphan_run['run_id']}"]
    assert orphan_match["proof"] is None
    # Fail-soft: the orphan alert still scored and flowed through routing.
    assert "score" in orphan_match and "matched" in orphan_match


def test_safe_segment_re_rejects_all_dot_segments():
    # A crafted source_id/run_id must never be a traversal step in the evidence
    # glob — the all-dots guard matches the sibling evidence_pack/evidence_room
    # sites (code review 2026-07-13).
    from app.alert_proof import _SAFE_SEGMENT_RE

    for bad in (".", "..", "...", "...."):
        assert not _SAFE_SEGMENT_RE.match(bad), bad
    for ok in ("AE-cbuae-rulebook", "intake-20260712T090000Z", "a.b_c-1"):
        assert _SAFE_SEGMENT_RE.match(ok), ok
