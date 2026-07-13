"""The redline (diff.txt) is sealed and independently verifiable.

Before this, a CHANGED record stored diff.txt but never hashed it, so a
post-capture edit to the redline shipped under a clean seal. Now
``create_canonical_evidence_record`` writes ``content.diff_hash`` (covered by
``record_hash``), and the public verifier exposes a ``diff_bytes_match`` check so
an auditor can prove the submitted diff.txt is the sealed one. All additive:
legacy records without ``diff_hash`` still verify — the diff check simply skips.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.evidence_records import create_canonical_evidence_record  # noqa: E402
from app.public_verify import verify_submission  # noqa: E402
from app.record_hashing import canonical_record_hash  # noqa: E402


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return _sha256_text(text)


_CURRENT = "Current official DFSA regulatory text — amended section 7."
_PREVIOUS = "Previous official DFSA regulatory text — section 7 original."


def _changed_run_with_previous(base: Path) -> tuple[dict, dict]:
    """A CHANGED run plus its previous run, so the canonical record gets a diff."""
    cur_dir = base / "data" / "source_snapshots" / "2026-06-20" / "AE" / "AE-dfsa-diff" / "run-cur"
    prev_dir = base / "data" / "source_snapshots" / "2026-06-19" / "AE" / "AE-dfsa-diff" / "run-prev"
    cur_hash = _write(cur_dir / "normalized.txt", _CURRENT)
    _write(cur_dir / "raw.txt", f"<main>{_CURRENT}</main>")
    _write(cur_dir / "metadata.json", json.dumps({"provider": "fixture"}, sort_keys=True))
    _write(cur_dir / "proof.json", json.dumps({"proof_quality": "LIMITED"}, sort_keys=True))
    prev_hash = _write(prev_dir / "normalized.txt", _PREVIOUS)

    run = {
        "run_id": "run-cur",
        "timestamp_utc": "2026-06-20T00:00:00Z",
        "market": "AE",
        "source_id": "AE-dfsa-diff",
        "source_name": "DFSA Diff Source",
        "category": "regulatory",
        "official_url": "https://www.dfsa.ae/example",
        "access_status": "accessible",
        "fetch_method": "fixture",
        "extraction_quality": "GOOD",
        "change_status": "CHANGED",
        "normalized_hash": cur_hash,
        "snapshot_raw_path": str((cur_dir / "raw.txt").relative_to(base)),
        "snapshot_normalized_path": str((cur_dir / "normalized.txt").relative_to(base)),
        "snapshot_metadata_path": str((cur_dir / "metadata.json").relative_to(base)),
        "proof_block_path": str((cur_dir / "proof.json").relative_to(base)),
    }
    previous_run = {
        "run_id": "run-prev",
        "normalized_hash": prev_hash,
        "snapshot_normalized_path": str((prev_dir / "normalized.txt").relative_to(base)),
    }
    return run, previous_run


def test_changed_record_seals_diff_hash_and_record_hash_covers_it(tmp_path):
    run, previous_run = _changed_run_with_previous(tmp_path)
    record = create_canonical_evidence_record(run, previous_run, base_dir=tmp_path)

    # 1. diff.txt exists and content.diff_hash is its sha256.
    diff_rel = record["files"]["diff_path"]
    diff_path = tmp_path / diff_rel
    assert diff_path.exists()
    on_disk = hashlib.sha256(diff_path.read_bytes()).hexdigest()
    assert record["content"]["diff_hash"] == f"sha256:{on_disk}"

    # 2. record_hash covers content (incl. diff_hash): recomputing the seal over
    #    the content block reproduces record_hash, so diff_hash is tamper-evident
    #    at the seal level.
    assert record["record_hash"] == f"sha256:{canonical_record_hash(record['content'])}"

    # 3. Flipping diff_hash breaks record-hash self-consistency (public verifier).
    tampered = json.loads(json.dumps(record))
    tampered["content"]["diff_hash"] = "sha256:" + "0" * 64
    res = verify_submission(tampered)
    self_consistent = next(c for c in res["checks"] if c["name"] == "record_hash_self_consistent")
    assert self_consistent["status"] == "fail"


def test_public_verify_diff_bytes_match_pass_and_tamper_fail(tmp_path):
    run, previous_run = _changed_run_with_previous(tmp_path)
    record = create_canonical_evidence_record(run, previous_run, base_dir=tmp_path)
    diff_text = (tmp_path / record["files"]["diff_path"]).read_text(encoding="utf-8")

    # Correct diff.txt → diff_bytes_match passes.
    ok = verify_submission(record, diff=diff_text)
    diff_check = next(c for c in ok["checks"] if c["name"] == "diff_bytes_match")
    assert diff_check["status"] == "pass"

    # Tampered redline → diff_bytes_match fails and the whole submission is not verified.
    bad = verify_submission(record, diff=diff_text + "\n+ injected line the regulator never published")
    bad_check = next(c for c in bad["checks"] if c["name"] == "diff_bytes_match")
    assert bad_check["status"] == "fail"
    assert bad["verified"] is False


def test_legacy_record_without_diff_hash_still_verifies(tmp_path):
    # A record predating diff_hash: build a self-consistent minimal record and
    # submit a diff. The diff check SKIPS (no diff_hash), and verification still
    # succeeds on the other checks — proving the change is backward-compatible.
    content = {"current_hash": f"sha256:{_sha256_text(_CURRENT)}"}
    record = {
        "record_hash": f"sha256:{canonical_record_hash(content)}",
        "record_hash_method": "content-sha256-v1",
        "content": content,
    }
    res = verify_submission(record, normalized=_CURRENT, diff="some diff text")
    diff_check = next(c for c in res["checks"] if c["name"] == "diff_bytes_match")
    assert diff_check["status"] == "skipped"
    assert res["verified"] is True  # record_hash + normalized_bytes still pass


def test_no_diff_submitted_skips(tmp_path):
    run, previous_run = _changed_run_with_previous(tmp_path)
    record = create_canonical_evidence_record(run, previous_run, base_dir=tmp_path)
    res = verify_submission(record)  # no diff submitted
    diff_check = next(c for c in res["checks"] if c["name"] == "diff_bytes_match")
    assert diff_check["status"] == "skipped"


# ── sealed capture metadata (WHEN / WHERE) ────────────────────────────────────

def test_capture_time_and_source_url_are_sealed_into_content(tmp_path):
    run, previous_run = _changed_run_with_previous(tmp_path)
    record = create_canonical_evidence_record(run, previous_run, base_dir=tmp_path)
    # The capture time and source URL now live INSIDE content and match the display.
    assert record["content"]["captured_at"] == record["run"]["timestamp"]
    assert record["content"]["source_url"] == record["source"]["official_url"]
    # ...and record_hash covers them (recomputing the seal reproduces record_hash).
    assert record["record_hash"] == f"sha256:{canonical_record_hash(record['content'])}"


def test_verify_capture_metadata_consistent_passes_for_untampered(tmp_path):
    run, previous_run = _changed_run_with_previous(tmp_path)
    record = create_canonical_evidence_record(run, previous_run, base_dir=tmp_path)
    res = verify_submission(record)
    check = next(c for c in res["checks"] if c["name"] == "capture_metadata_consistent")
    assert check["status"] == "pass"


def test_verify_detects_display_timestamp_tampering(tmp_path):
    run, previous_run = _changed_run_with_previous(tmp_path)
    record = create_canonical_evidence_record(run, previous_run, base_dir=tmp_path)
    # Editing the DISPLAY run.timestamp does NOT break record_hash (which covers
    # only content) — but it now diverges from the sealed content.captured_at, so
    # capture_metadata_consistent fails and the submission is not verified.
    tampered = json.loads(json.dumps(record))
    tampered["run"]["timestamp"] = "2020-01-01T00:00:00Z"
    res = verify_submission(tampered)
    check = next(c for c in res["checks"] if c["name"] == "capture_metadata_consistent")
    assert check["status"] == "fail"
    assert res["verified"] is False


def test_verify_capture_metadata_skips_for_legacy_record(tmp_path):
    content = {"current_hash": f"sha256:{_sha256_text(_CURRENT)}"}
    record = {
        "record_hash": f"sha256:{canonical_record_hash(content)}",
        "record_hash_method": "content-sha256-v1",
        "content": content,
        "run": {"timestamp": "2026-06-20T00:00:00Z"},
        "source": {"official_url": "https://dfsa.ae/x"},
    }
    res = verify_submission(record, normalized=_CURRENT)
    check = next(c for c in res["checks"] if c["name"] == "capture_metadata_consistent")
    assert check["status"] == "skipped"
    assert res["verified"] is True
