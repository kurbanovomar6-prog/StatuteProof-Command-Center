"""Tests for the self-serve Evidence Pack (Feature 6-evidence-pack).

Covers: pack assembly for a date range, manifest ↔ included-snapshot hash
agreement, source-scoping (never leak another source), the bundled standalone
verify.py actually PASSING on a clean pack and FAILING on a tampered snapshot
(run as a real subprocess), disclaimer presence, the forbidden-claims guard, and
the API handler's auth-scoping (401 unauthenticated).
"""

from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.api as api
import app.api_reports as api_reports
from app.api import _Handler
from app.evidence_assessment import LEGAL_DISCLAIMER
from app.evidence_records import create_canonical_evidence_record
from app.public_verify import verify_submission
from app.evidence_pack import (
    EvidencePackError,
    FULL_LEGAL_DISCLAIMER,
    assert_no_forbidden_claims,
    build_evidence_pack,
)


# ── fixtures ────────────────────────────────────────────────────────────────────

def _write(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _make_record(
    base: Path,
    *,
    source_id: str,
    run_id: str,
    timestamp: str,
    market: str = "AE",
    text: str = "Current official regulatory text captured for evidence.",
) -> dict:
    """Create a genuine complete/VERIFIED canonical evidence record via the
    product writer, so the pack is exercised against real evidence objects."""
    run_dir = base / "data" / "source_snapshots" / timestamp[:10] / market / source_id / run_id
    normalized_hash = _write(run_dir / "normalized.txt", text)
    _write(run_dir / "raw.txt", f"<main>{text}</main>")
    _write(run_dir / "metadata.json", json.dumps({"provider": "fixture"}, sort_keys=True))
    _write(run_dir / "proof.json", json.dumps({"proof_quality": "GOOD"}, sort_keys=True))
    run = {
        "run_id": run_id,
        "timestamp_utc": timestamp,
        "market": market,
        "source_id": source_id,
        "source_name": f"{source_id} Source",
        "category": "regulatory",
        "official_url": f"https://example.gov/{source_id}",
        "access_status": "accessible",
        "fetch_method": "fixture",
        "extraction_quality": "GOOD",
        "change_status": "FIRST_SEEN",
        "normalized_hash": normalized_hash,
        "snapshot_raw_path": str((run_dir / "raw.txt").relative_to(base)),
        "snapshot_normalized_path": str((run_dir / "normalized.txt").relative_to(base)),
        "snapshot_metadata_path": str((run_dir / "metadata.json").relative_to(base)),
        "proof_block_path": str((run_dir / "proof.json").relative_to(base)),
    }
    return create_canonical_evidence_record(run, base_dir=base)


def _run_dict(base: Path, *, source_id: str, run_id: str, timestamp: str,
              text: str, change_status: str, market: str = "AE") -> dict:
    run_dir = base / "data" / "source_snapshots" / timestamp[:10] / market / source_id / run_id
    normalized_hash = _write(run_dir / "normalized.txt", text)
    _write(run_dir / "raw.txt", f"<main>{text}</main>")
    _write(run_dir / "metadata.json", json.dumps({"provider": "fixture"}, sort_keys=True))
    _write(run_dir / "proof.json", json.dumps({"proof_quality": "GOOD"}, sort_keys=True))
    return {
        "run_id": run_id,
        "timestamp_utc": timestamp,
        "market": market,
        "source_id": source_id,
        "source_name": f"{source_id} Source",
        "category": "regulatory",
        "official_url": f"https://example.gov/{source_id}",
        "access_status": "accessible",
        "fetch_method": "fixture",
        "extraction_quality": "GOOD",
        "change_status": change_status,
        "normalized_hash": normalized_hash,
        "snapshot_raw_path": str((run_dir / "raw.txt").relative_to(base)),
        "snapshot_normalized_path": str((run_dir / "normalized.txt").relative_to(base)),
        "snapshot_metadata_path": str((run_dir / "metadata.json").relative_to(base)),
        "proof_block_path": str((run_dir / "proof.json").relative_to(base)),
    }


def _make_changed(base: Path, *, source_id: str, run_id: str, timestamp: str,
                  previous_text: str, current_text: str) -> dict:
    """Create a CHANGED record (with a real sealed diff artifact) vs a prior state."""
    previous_run = _run_dict(base, source_id=source_id, run_id=f"{run_id}-prev",
                             timestamp="2026-02-01T09:00:00Z", text=previous_text,
                             change_status="FIRST_SEEN")
    run = _run_dict(base, source_id=source_id, run_id=run_id, timestamp=timestamp,
                    text=current_text, change_status="CHANGED")
    return create_canonical_evidence_record(run, previous_run, base_dir=base)


def _read_zip(pack_path: str) -> dict[str, bytes]:
    with zipfile.ZipFile(pack_path, "r") as zf:
        return {name: zf.read(name) for name in zf.namelist()}


# ── pack assembly ───────────────────────────────────────────────────────────────

def test_build_evidence_pack_assembles_zip_for_range(tmp_path):
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")

    result = build_evidence_pack(
        ["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path
    )

    assert result["status"] == "ok", result
    assert result["record_count"] == 1
    assert result["pack_path"].endswith(".zip")
    assert Path(result["pack_path"]).exists()

    names = set(_read_zip(result["pack_path"]).keys())
    assert "manifest.json" in names
    assert "verify.py" in names
    assert "HOW-TO-VERIFY.md" in names
    assert "DISCLAIMER.txt" in names
    assert any(n.endswith("/raw.txt") for n in names)
    assert any(n.endswith("/normalized.txt") for n in names)


def test_build_evidence_pack_empty_when_no_records(tmp_path):
    result = build_evidence_pack(
        ["nonexistent-source-zzz"], "2026-01-01", "2026-01-31", base_dir=tmp_path
    )
    assert result["status"] == "empty"
    assert result["record_count"] == 0


def test_build_evidence_pack_error_on_empty_source_ids(tmp_path):
    result = build_evidence_pack([], "2026-01-01", "2026-01-31", base_dir=tmp_path)
    assert result["status"] == "error"


def test_build_evidence_pack_error_on_bad_date_range(tmp_path):
    result = build_evidence_pack(
        ["cbuae-test"], "2026-06-30", "2026-01-01", base_dir=tmp_path
    )
    assert result["status"] == "error"


def test_out_of_range_record_is_excluded(tmp_path):
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-jan", timestamp="2026-01-10T10:00:00Z")

    result = build_evidence_pack(
        ["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path
    )
    assert result["status"] == "empty"


# ── availability guard: bounded record materialization ──────────────────────────

def test_pack_rejects_oversized_selection(tmp_path):
    """More records than the cap → reject the whole selection, never truncate.

    The collector stops one past the cap, so an over-cap request never loads an
    unbounded number of records' bytes into memory (the OOM guard). Rejecting (vs
    silently truncating) keeps the pack honest — a partial pack shipped under a
    clean manifest would be misleading evidence.
    """
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-a", timestamp="2026-03-10T10:00:00Z")
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-b", timestamp="2026-03-12T10:00:00Z")

    result = build_evidence_pack(
        ["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path, max_records=1
    )

    assert result["status"] == "too_large", result
    assert result["max_records"] == 1
    assert "pack_path" not in result
    assert "narrow" in result["message"].lower()


def test_pack_exactly_at_cap_still_builds(tmp_path):
    """Boundary: a selection with exactly max_records records builds normally."""
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-a", timestamp="2026-03-10T10:00:00Z")

    result = build_evidence_pack(
        ["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path, max_records=1
    )

    assert result["status"] == "ok", result
    assert result["record_count"] == 1


# ── manifest ↔ snapshot integrity ───────────────────────────────────────────────

def test_manifest_matches_included_snapshots(tmp_path):
    record = _make_record(
        tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z"
    )
    result = build_evidence_pack(
        ["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path
    )
    contents = _read_zip(result["pack_path"])
    manifest = json.loads(contents["manifest.json"])

    assert manifest["hash_algorithm"] == "sha256"
    assert manifest["record_count"] == 1
    entry = manifest["records"][0]

    raw_file = entry["raw_snapshot_file"]
    norm_file = entry["normalized_snapshot_file"]
    assert raw_file in contents and norm_file in contents

    # Manifest hashes equal the SHA-256 of the bytes actually shipped.
    assert hashlib.sha256(contents[raw_file]).hexdigest() == entry["raw_hash"]
    assert hashlib.sha256(contents[norm_file]).hexdigest() == entry["normalized_hash"]

    # And the normalized hash equals the hash the product recorded at capture.
    recorded = record["content"]["current_hash"].replace("sha256:", "")
    assert entry["normalized_hash"] == recorded


def test_pack_excludes_record_with_tampered_raw_snapshot(tmp_path):
    """A post-capture edit to raw.txt must NOT ship as a clean pack.

    Regression: the pack recomputed raw_hash from disk and never compared it to
    the capture-time content.raw_hash, so a raw tamper printed PASS. The record
    is now excluded when raw bytes diverge from the sealed raw_hash — mirroring
    the normalized-side protection.
    """
    record = _make_record(
        tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z"
    )
    # The pack reads the canonical evidence-tree copy, not the source snapshot.
    raw_rel = record["files"]["raw_path"]
    raw_path = tmp_path / raw_rel
    assert raw_path.exists()
    raw_path.write_text("<main>FABRICATED regulatory text</main>", encoding="utf-8")

    result = build_evidence_pack(
        ["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path
    )
    assert result["status"] == "empty"
    assert result["record_count"] == 0


# ── source-scoping (data-level auth boundary) ────────────────────────────────────

def test_pack_never_includes_a_non_requested_source(tmp_path):
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-a", timestamp="2026-03-15T10:00:00Z")
    _make_record(tmp_path, source_id="dfsa-test", run_id="run-b", timestamp="2026-03-16T10:00:00Z")

    result = build_evidence_pack(
        ["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path
    )
    manifest = json.loads(_read_zip(result["pack_path"])["manifest.json"])

    assert result["record_count"] == 1
    assert manifest["source_ids"] == ["cbuae-test"]
    assert {r["source_id"] for r in manifest["records"]} == {"cbuae-test"}


# ── the standalone verify.py must genuinely work ─────────────────────────────────

def _extract(pack_path: str, dest: Path) -> Path:
    with zipfile.ZipFile(pack_path, "r") as zf:
        zf.extractall(dest)
    return dest


def test_bundled_verify_py_passes_on_clean_pack(tmp_path):
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = build_evidence_pack(
        ["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path
    )
    extracted = _extract(result["pack_path"], tmp_path / "clean")

    proc = subprocess.run(
        [sys.executable, "verify.py"],
        cwd=extracted,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "RESULT: PASS" in proc.stdout
    assert "FAIL" not in proc.stdout


def test_bundled_verify_py_fails_on_tampered_snapshot(tmp_path):
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = build_evidence_pack(
        ["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path
    )
    extracted = _extract(result["pack_path"], tmp_path / "tampered")

    # Tamper a single normalized snapshot inside the extracted pack.
    target = next(extracted.glob("snapshots/*/normalized.txt"))
    target.write_text(target.read_text(encoding="utf-8") + "TAMPERED", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, "verify.py"],
        cwd=extracted,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "RESULT: FAIL" in proc.stdout
    assert "FAIL" in proc.stdout


def test_bundled_verify_py_fails_when_raw_forged_and_manifest_hash_relabeled(tmp_path):
    """Byte-to-SEAL: fabricating raw.txt AND rewriting only the UNSEALED manifest
    hash to match it must still FAIL — the sealed content.raw_hash is the authority.

    Regression: verify.py re-hashed each snapshot but compared the result against
    the per-record hash in manifest.json, which is unsealed. A holder of a genuine
    pack could replace snapshots/<id>/raw.txt with fabricated regulator text,
    update ONLY that record's raw_hash in manifest.json, leave evidence-record.json
    untouched, and print RESULT: PASS over forged official-source bytes — while the
    online /api/verify (which anchors on content.raw_hash) was never fooled. The
    verifier now checks each snapshot against the SEALED content.raw_hash inside the
    bundled evidence-record.json, whose authenticity check_record_seal proves.
    """
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = build_evidence_pack(
        ["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path
    )
    extracted = _extract(result["pack_path"], tmp_path / "forged")

    # Sanity: the untouched pack verifies clean.
    proc = subprocess.run([sys.executable, "verify.py"], cwd=extracted, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "RESULT: PASS" in proc.stdout

    # Fabricate the RAW snapshot with forged regulator text.
    raw_target = next(extracted.glob("snapshots/*/raw.txt"))
    forged = b"<main>FABRICATED official-source regulatory text</main>"
    raw_target.write_bytes(forged)

    # Relabel ONLY the unsealed manifest hash so it matches the fabricated bytes.
    # evidence-record.json (the sealed record) is left completely untouched.
    manifest_path = extracted / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    forged_hash = hashlib.sha256(forged).hexdigest()
    manifest["records"][0]["raw_hash"] = forged_hash
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    proc = subprocess.run([sys.executable, "verify.py"], cwd=extracted, capture_output=True, text=True)
    # The sealed content.raw_hash still commits to the ORIGINAL bytes, so the
    # fabricated raw.txt no longer matches it — the pack must fail.
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "RESULT: FAIL" in proc.stdout
    assert "[raw]" in proc.stdout
    # The record self-seal itself is intact (evidence-record.json was untouched):
    # the failure is the raw bytes diverging from the SEALED content.raw_hash, not
    # a broken seal — proving the byte↔seal binding is what caught the forgery.
    assert "PASS  cbuae-test-run-001 [record_seal]" in proc.stdout or "[record_seal] record_hash recomputes" in proc.stdout


# ── sealed-diff parity with the Regulator Binder (CHANGED records) ───────────────

def _changed_pack(tmp_path):
    _make_changed(
        tmp_path, source_id="dfsa-test", run_id="run-changed", timestamp="2026-03-20T10:00:00Z",
        previous_text="Original rulebook clause A applies to firms.",
        current_text="Amended rulebook clause A applies to firms and branches.",
    )
    result = build_evidence_pack(["dfsa-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    assert result["status"] == "ok", result
    return result


def test_changed_record_pack_ships_diff_and_seal_hashes(tmp_path):
    """A CHANGED record's pack must ship diff.txt and surface diff_hash +
    previous_hash + record_hash — the same sealed-diff material the Binder ships,
    so the pack and binder do not disagree about what is verifiable."""
    result = _changed_pack(tmp_path)
    contents = _read_zip(result["pack_path"])
    manifest = json.loads(contents["manifest.json"])
    row = manifest["records"][0]

    # The sealed redline rides along and is referenced by the manifest row.
    assert "diff_file" in row
    assert row["diff_file"] in contents
    diff_bytes = contents[row["diff_file"]]
    assert b"@@" in diff_bytes or b"##" in diff_bytes or b"---" in diff_bytes

    # diff_hash + previous_hash + record_hash are surfaced and internally consistent.
    assert hashlib.sha256(diff_bytes).hexdigest() == row["diff_hash"]
    assert row["previous_hash"]
    assert row["record_hash"]

    # The manifest hashes equal what the product sealed into the record itself.
    rec_bytes = contents[row["evidence_record_file"]]
    sealed = json.loads(rec_bytes)
    assert row["diff_hash"] == sealed["content"]["diff_hash"].replace("sha256:", "")
    assert row["previous_hash"] == sealed["content"]["previous_hash"].replace("sha256:", "")
    assert row["record_hash"] == sealed["record_hash"].replace("sha256:", "")


def test_pack_changed_record_verifies_sealed_diff_through_public_verify(tmp_path):
    """End-to-end: a customer's auditor can take the pack's own bytes (record +
    normalized + diff.txt) and run the SAME canonical sealed-diff check the Verify
    page runs (app.public_verify), and it passes."""
    result = _changed_pack(tmp_path)
    contents = _read_zip(result["pack_path"])
    row = json.loads(contents["manifest.json"])["records"][0]

    record = json.loads(contents[row["evidence_record_file"]])
    normalized = contents[row["normalized_snapshot_file"]].decode("utf-8")
    diff = contents[row["diff_file"]].decode("utf-8")

    report = verify_submission(record, normalized=normalized, diff=diff)
    by_name = {c["name"]: c["status"] for c in report["checks"]}
    assert by_name["diff_bytes_match"] == "pass", report
    assert by_name["record_hash_self_consistent"] == "pass", report
    assert by_name["normalized_bytes_match"] == "pass", report
    assert report["verified"] is True, report


def test_pack_bundled_verify_checks_sealed_diff(tmp_path):
    """The bundled verify.py re-hashes the sealed diff and reports PASS on a clean
    pack, and FAIL if a single byte of diff.txt is altered."""
    result = _changed_pack(tmp_path)

    clean = _extract(result["pack_path"], tmp_path / "clean")
    proc = subprocess.run([sys.executable, "verify.py"], cwd=clean, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "RESULT: PASS" in proc.stdout
    assert "[diff]" in proc.stdout          # the sealed diff was actually checked
    assert "FAIL" not in proc.stdout

    tampered = _extract(result["pack_path"], tmp_path / "tampered")
    target = next(tampered.glob("snapshots/*/diff.txt"))
    target.write_text(target.read_text(encoding="utf-8") + "TAMPERED", encoding="utf-8")
    proc = subprocess.run([sys.executable, "verify.py"], cwd=tampered, capture_output=True, text=True)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "RESULT: FAIL" in proc.stdout
    assert "[diff]" in proc.stdout


def test_pack_excludes_changed_record_with_tampered_diff(tmp_path):
    """A post-seal edit to diff.txt must NOT ship as clean evidence — the record
    is excluded when its diff bytes diverge from the sealed content.diff_hash,
    mirroring the raw/normalized snapshot protections."""
    record = _make_changed(
        tmp_path, source_id="dfsa-test", run_id="run-changed", timestamp="2026-03-20T10:00:00Z",
        previous_text="Original rulebook clause A applies to firms.",
        current_text="Amended rulebook clause A applies to firms and branches.",
    )
    diff_rel = record["files"]["diff_path"]
    diff_path = tmp_path / diff_rel
    assert diff_path.exists()
    diff_path.write_text(diff_path.read_text(encoding="utf-8") + "\nFABRICATED", encoding="utf-8")

    result = build_evidence_pack(["dfsa-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    assert result["status"] == "empty"
    assert result["record_count"] == 0


def test_first_seen_pack_carries_no_diff_and_stays_valid(tmp_path):
    """A FIRST_SEEN record has no diff — the pack must not ship one nor force one,
    and both the bundled verify.py and public_verify still report it valid."""
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = build_evidence_pack(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    contents = _read_zip(result["pack_path"])
    row = json.loads(contents["manifest.json"])["records"][0]

    assert "diff_file" not in row
    assert "diff_hash" not in row
    assert not any(n.endswith("/diff.txt") for n in contents)

    # public_verify with no diff → diff check skipped, record still verified.
    record = json.loads(contents[row["evidence_record_file"]])
    normalized = contents[row["normalized_snapshot_file"]].decode("utf-8")
    report = verify_submission(record, normalized=normalized, diff=None)
    by_name = {c["name"]: c["status"] for c in report["checks"]}
    assert by_name["diff_bytes_match"] == "skipped", report
    assert report["verified"] is True, report

    extracted = _extract(result["pack_path"], tmp_path / "clean")
    proc = subprocess.run([sys.executable, "verify.py"], cwd=extracted, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "RESULT: PASS" in proc.stdout


def test_pack_and_binder_agree_on_changed_record(tmp_path):
    """The two customer deliverables must not disagree about what is verifiable:
    for the SAME CHANGED record, both ship the identical sealed diff bytes and both
    surface a record_hash that recomputes through the canonical verifier."""
    from app.regulator_binder import build_regulator_binder

    _make_changed(
        tmp_path, source_id="dfsa-test", run_id="run-changed", timestamp="2026-03-20T10:00:00Z",
        previous_text="Original rulebook clause A applies to firms.",
        current_text="Amended rulebook clause A applies to firms and branches.",
    )
    pack = build_evidence_pack(["dfsa-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    binder = build_regulator_binder(["dfsa-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    assert pack["status"] == "ok" and binder["status"] == "ok"

    p = _read_zip(pack["pack_path"])
    b = _read_zip(binder["binder_path"])
    prow = json.loads(p["manifest.json"])["records"][0]
    brow = json.loads(b["manifest.json"])["records"][0]

    # Identical sealed diff bytes and identical record self-seal across artifacts.
    assert p[prow["diff_file"]] == b[brow["diff_file"]]
    assert prow["record_hash"] == brow["record_hash"]

    # The same record verifies through public_verify from either artifact's bytes.
    for contents, row in ((p, prow), (b, brow)):
        record = json.loads(contents[row["evidence_record_file"]])
        diff = contents[row["diff_file"]].decode("utf-8")
        report = verify_submission(record, diff=diff)
        by_name = {c["name"]: c["status"] for c in report["checks"]}
        assert by_name["diff_bytes_match"] == "pass"
        assert by_name["record_hash_self_consistent"] == "pass"


# ── legal safety: disclaimer + forbidden claims ──────────────────────────────────

def test_disclaimer_present_across_pack(tmp_path):
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = build_evidence_pack(
        ["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path
    )
    contents = _read_zip(result["pack_path"])
    manifest = json.loads(contents["manifest.json"])

    assert manifest["legal_disclaimer"] == LEGAL_DISCLAIMER
    assert manifest["legal_notice"] == FULL_LEGAL_DISCLAIMER
    assert LEGAL_DISCLAIMER in contents["HOW-TO-VERIFY.md"].decode("utf-8")
    assert FULL_LEGAL_DISCLAIMER in contents["HOW-TO-VERIFY.md"].decode("utf-8")
    assert LEGAL_DISCLAIMER in contents["DISCLAIMER.txt"].decode("utf-8")
    assert "Not legal advice" in contents["verify.py"].decode("utf-8")
    assert result["disclaimer"] == LEGAL_DISCLAIMER


def test_pack_prose_has_no_forbidden_claims(tmp_path):
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = build_evidence_pack(
        ["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path
    )
    contents = _read_zip(result["pack_path"])
    # Neither authored artifact trips the shared forbidden-claims guard.
    assert_no_forbidden_claims(contents["HOW-TO-VERIFY.md"].decode("utf-8"))
    assert_no_forbidden_claims(contents["verify.py"].decode("utf-8"))


def test_forbidden_claims_guard_raises_on_banned_phrase():
    with pytest.raises(EvidencePackError):
        assert_no_forbidden_claims("This pack will guarantee compliance for you.")


def test_forbidden_claims_guard_allows_negated_disclaimer():
    # The disclaimers legitimately deny forbidden claims; they must not trip.
    assert_no_forbidden_claims(f"{LEGAL_DISCLAIMER}\n{FULL_LEGAL_DISCLAIMER}") is None


# ── API handler: auth-scoping ────────────────────────────────────────────────────

def _bare_handler() -> _Handler:
    return _Handler.__new__(_Handler)


def test_handler_rejects_unauthenticated(monkeypatch):
    monkeypatch.setattr(api, "require_auth", lambda handler: None)
    monkeypatch.setattr(api_reports, "require_auth", lambda handler: None)
    handler = _bare_handler()
    captured: dict = {}
    handler._send_json = lambda data, status=200, **kw: captured.update(data=data, status=status)  # type: ignore[method-assign]

    handler._handle_evidence_pack()

    assert captured["status"] == 401
    assert captured["data"]["ok"] is False


def test_handler_streams_zip_for_authenticated_client(monkeypatch, tmp_path):
    # A real (tiny) zip on disk that the handler will stream back.
    fake_zip = tmp_path / "evidence_pack_x.zip"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("manifest.json", "{}")
    fake_zip.write_bytes(buf.getvalue())

    monkeypatch.setattr(api, "require_auth", lambda handler: {"id": 1, "email": "c@x.io"})
    monkeypatch.setattr(api_reports, "require_auth", lambda handler: {"id": 1, "email": "c@x.io"})
    import app.evidence_pack as ep
    monkeypatch.setattr(
        ep,
        "build_evidence_pack",
        lambda *a, **k: {
            "status": "ok",
            "pack_path": str(fake_zip),
            "pack_filename": "evidence_pack_x.zip",
            "record_count": 1,
        },
    )

    handler = _bare_handler()
    monkeypatch.setattr(
        handler,
        "_read_json_strict",
        lambda: ({"source_ids": ["cbuae-test"], "date_from": "2026-03-01", "date_to": "2026-03-31"}, None),
    )
    # GROUP B authz/limits gates are exercised by their own tests; here we isolate
    # the streaming behavior, so let the rate-limit / capability / entitlement
    # checks pass through unchanged.
    monkeypatch.setattr(handler, "_rate_limited", lambda *a, **k: False)
    monkeypatch.setattr(handler, "_require_capability", lambda *a, **k: True)
    monkeypatch.setattr(handler, "_entitle_source_ids", lambda user, ids: ids)
    sent: dict = {}

    def _capture_bytes(body, content_type, status=200, extra_headers=None):
        sent.update(body=body, content_type=content_type, status=status, extra_headers=extra_headers)

    handler._send_bytes = _capture_bytes  # type: ignore[method-assign]
    handler._send_json = lambda data, status=200, **kw: sent.update(json=data, status=status)  # type: ignore[method-assign]

    expected_bytes = fake_zip.read_bytes()  # capture before the handler unlinks it
    handler._handle_evidence_pack()

    assert sent.get("content_type") == "application/zip"
    assert sent.get("body") == expected_bytes
    assert any("Content-Disposition" == k for k, _ in (sent.get("extra_headers") or []))
    # One-shot download: the generated ZIP is removed from disk after streaming.
    assert not fake_zip.exists()


def test_handler_413_when_selection_too_large(monkeypatch):
    """The handler maps the builder's too_large status to HTTP 413."""
    monkeypatch.setattr(api, "require_auth", lambda handler: {"id": 7, "email": "c@x.io"})
    monkeypatch.setattr(api_reports, "require_auth", lambda handler: {"id": 7, "email": "c@x.io"})
    handler = _bare_handler()
    monkeypatch.setattr(
        handler, "_read_json_strict",
        lambda: ({"source_ids": ["mine"], "date_from": "2026-03-01", "date_to": "2026-03-31"}, None),
    )
    monkeypatch.setattr(handler, "_rate_limited", lambda *a, **k: False)
    monkeypatch.setattr(handler, "_require_capability", lambda *a, **k: True)
    monkeypatch.setattr(handler, "_entitle_source_ids", lambda user, ids: ids)
    import app.evidence_pack as ep
    monkeypatch.setattr(
        ep, "build_evidence_pack",
        lambda *a, **k: {"status": "too_large", "max_records": 2000, "message": "narrow the selection"},
    )
    captured: dict = {}
    handler._send_json = lambda data, status=200, **kw: captured.update(data=data, status=status)  # type: ignore[method-assign]

    handler._handle_evidence_pack()

    assert captured["status"] == 413
    assert captured["data"]["ok"] is False
    assert captured["data"]["max_records"] == 2000


def test_handler_error_does_not_leak_internal_message(monkeypatch):
    """A builder error must return a generic 500 — never forward internal detail
    (e.g. an absolute server path in an OSError) to the client."""
    monkeypatch.setattr(api, "require_auth", lambda handler: {"id": 7, "email": "c@x.io"})
    monkeypatch.setattr(api_reports, "require_auth", lambda handler: {"id": 7, "email": "c@x.io"})
    handler = _bare_handler()
    monkeypatch.setattr(
        handler, "_read_json_strict",
        lambda: ({"source_ids": ["mine"], "date_from": "2026-03-01", "date_to": "2026-03-31"}, None),
    )
    monkeypatch.setattr(handler, "_rate_limited", lambda *a, **k: False)
    monkeypatch.setattr(handler, "_require_capability", lambda *a, **k: True)
    monkeypatch.setattr(handler, "_entitle_source_ids", lambda user, ids: ids)
    secret_path = "/srv/statuteproof/data/evidence_packs"
    import app.evidence_pack as ep
    monkeypatch.setattr(
        ep, "build_evidence_pack",
        lambda *a, **k: {"status": "error", "message": f"[Errno 13] Permission denied: '{secret_path}'"},
    )
    captured: dict = {}
    handler._send_json = lambda data, status=200, **kw: captured.update(data=data, status=status)  # type: ignore[method-assign]

    handler._handle_evidence_pack()

    assert captured["status"] == 500
    assert secret_path not in json.dumps(captured["data"])
    assert captured["data"]["message"] == "Failed to build the evidence pack."


def test_pack_ships_rfc3161_sidecars_when_present(tmp_path):
    """When the chain-head RFC 3161 token exists, the pack must carry it (and
    say so in the manifest + HOW-TO-VERIFY) — the token in the CUSTOMER'S hands
    is what makes 'provable when you knew' third-party-attestable (EV-8)."""
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "evidence_chain_head.tsr").write_bytes(b"\x30\x03fake-der")
    (tmp_path / "data" / "evidence_chain_head.tsr.json").write_text("{}", encoding="utf-8")

    result = build_evidence_pack(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)

    assert result["status"] == "ok", result
    names = set(_read_zip(result["pack_path"]).keys())
    assert "timestamp/evidence_chain_head.tsr" in names
    assert "timestamp/evidence_chain_head.tsr.json" in names
    ext = result["manifest"].get("external_timestamp")
    assert ext and ext.get("included") is True
    readme = _read_zip(result["pack_path"])["HOW-TO-VERIFY.md"].decode("utf-8")
    assert "RFC 3161 timestamp (included)" in readme


# ── bundled verify.py: record self-seal + capture-metadata cross-check ───────────

def test_bundled_verify_py_checks_record_self_seal(tmp_path):
    """The bundled verify.py recomputes the record self-seal over the bundled
    evidence-record.json content block and cross-checks capture metadata, printing
    PASS for both on a clean pack (never SKIP for a modern sealed record)."""
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = build_evidence_pack(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    extracted = _extract(result["pack_path"], tmp_path / "clean")

    proc = subprocess.run([sys.executable, "verify.py"], cwd=extracted, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "RESULT: PASS" in proc.stdout
    assert "[record_seal]" in proc.stdout           # the self-seal was actually recomputed
    assert "[capture_metadata]" in proc.stdout      # the metadata cross-check ran
    # A modern sealed record must genuinely PASS these, not be skipped.
    assert "PASS  cbuae-test-run-001 [record_seal]" in proc.stdout or "[record_seal] record_hash recomputes" in proc.stdout
    assert "FAIL" not in proc.stdout


def test_bundled_verify_py_fails_on_tampered_evidence_record(tmp_path):
    """Editing the bundled evidence-record.json content (leaving raw/normalized
    untouched) must make verify.py FAIL: the snapshot re-hashes still pass, but the
    record self-seal no longer recomputes from the altered content block.

    Regression: verify.py previously only re-hashed raw/normalized/diff and never
    recomputed the record self-seal, so a tampered evidence-record.json shipped
    as PASS."""
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = build_evidence_pack(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    extracted = _extract(result["pack_path"], tmp_path / "tampered")

    # Tamper a SEALED field inside the bundled record's content block, leaving the
    # snapshots (raw.txt/normalized.txt) byte-for-byte intact.
    rec_file = next(extracted.glob("snapshots/*/evidence-record.json"))
    record = json.loads(rec_file.read_text(encoding="utf-8"))
    record["content"]["source_url"] = "https://evil.example/injected"
    rec_file.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")

    proc = subprocess.run([sys.executable, "verify.py"], cwd=extracted, capture_output=True, text=True)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "RESULT: FAIL" in proc.stdout
    assert "[record_seal]" in proc.stdout


def test_bundled_verify_py_fails_on_display_metadata_edit(tmp_path):
    """Editing a DISPLAY field (run.timestamp) while leaving the sealed
    content.captured_at AND the record_hash untouched must FAIL the capture-metadata
    cross-check — mirroring app.public_verify._check_capture_metadata_consistent.

    This is the case the record-hash recompute alone cannot catch: the display
    field is not inside the sealed content block, so tampering it leaves the seal
    self-consistent; the cross-check against the sealed copy is what flags it."""
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = build_evidence_pack(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    extracted = _extract(result["pack_path"], tmp_path / "meta")

    rec_file = next(extracted.glob("snapshots/*/evidence-record.json"))
    record = json.loads(rec_file.read_text(encoding="utf-8"))
    # Only touch the DISPLAY timestamp; content.captured_at and record_hash stay put.
    record.setdefault("run", {})["timestamp"] = "1999-01-01T00:00:00Z"
    rec_file.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")

    proc = subprocess.run([sys.executable, "verify.py"], cwd=extracted, capture_output=True, text=True)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "RESULT: FAIL" in proc.stdout
    assert "[capture_metadata]" in proc.stdout
    # The record self-seal itself still recomputes (content block was untouched),
    # proving it is the cross-check — not the hash recompute — that caught this.
    assert "PASS  cbuae-test-run-001 [record_seal]" in proc.stdout or "[record_seal] record_hash recomputes" in proc.stdout


def test_bundled_verify_py_record_seal_matches_public_verify(tmp_path):
    """The inlined canonical_record_hash in verify.py must agree with the product's
    app.public_verify: the SAME bundled record verifies as record_hash_self_consistent
    through public_verify, and verify.py's inlined recompute reaches the same verdict."""
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = build_evidence_pack(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    contents = _read_zip(result["pack_path"])
    row = json.loads(contents["manifest.json"])["records"][0]
    record = json.loads(contents[row["evidence_record_file"]])

    report = verify_submission(record)
    by_name = {c["name"]: c["status"] for c in report["checks"]}
    assert by_name["record_hash_self_consistent"] == "pass", report
    assert by_name["capture_metadata_consistent"] == "pass", report

    # verify.py's inlined recompute reaches the same PASS verdict (subprocess run).
    extracted = _extract(result["pack_path"], tmp_path / "agree")
    proc = subprocess.run([sys.executable, "verify.py"], cwd=extracted, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "[record_seal] record_hash recomputes" in proc.stdout


# ── bundled verify.py: full-record attribution seal ──────────────────────────────

def test_bundled_verify_py_checks_attribution_seal_on_clean_pack(tmp_path):
    """The bundled verify.py recomputes the full-record attribution seal
    (regulator, source name, change summary, line counts, run status, review
    status) and PASSes it on a clean modern record — never SKIP for a sealed
    record."""
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = build_evidence_pack(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    extracted = _extract(result["pack_path"], tmp_path / "clean")

    proc = subprocess.run([sys.executable, "verify.py"], cwd=extracted, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "RESULT: PASS" in proc.stdout
    assert "[attribution_seal] attribution_hash recomputes" in proc.stdout
    assert "FAIL" not in proc.stdout


def test_bundled_verify_py_fails_on_forged_regulator(tmp_path):
    """Flipping the DISPLAY regulator (CBUAE -> VARA) in the bundled record while
    leaving the content block, snapshots, and capture metadata byte-identical must
    make verify.py FAIL on the attribution seal.

    Regression: verify.py previously never recomputed attribution_hash, so a record
    with a forged regulator passed OFFLINE (RESULT: PASS) while the ONLINE
    /api/verify correctly failed it — a real gap in the trust-no-one artifact."""
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = build_evidence_pack(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    extracted = _extract(result["pack_path"], tmp_path / "forge-regulator")

    rec_file = next(extracted.glob("snapshots/*/evidence-record.json"))
    record = json.loads(rec_file.read_text(encoding="utf-8"))
    assert record["source"]["regulator"] == "CBUAE"
    record["source"]["regulator"] = "VARA"  # forge the attributed regulator
    rec_file.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")

    proc = subprocess.run([sys.executable, "verify.py"], cwd=extracted, capture_output=True, text=True)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "RESULT: FAIL" in proc.stdout
    assert "[attribution_seal] attribution_hash does NOT recompute" in proc.stdout
    # The content self-seal itself still recomputes (content block untouched),
    # proving it is the attribution seal — not the record seal — that caught this.
    assert "[record_seal] record_hash recomputes" in proc.stdout


def test_bundled_verify_py_fails_on_forged_change_summary(tmp_path):
    """Rewriting the DISPLAY change summary in the bundled record must FAIL the
    attribution seal even though the content block is untouched."""
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = build_evidence_pack(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    extracted = _extract(result["pack_path"], tmp_path / "forge-summary")

    rec_file = next(extracted.glob("snapshots/*/evidence-record.json"))
    record = json.loads(rec_file.read_text(encoding="utf-8"))
    record.setdefault("change", {})["summary"] = "Fabricated: no material change occurred."
    rec_file.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")

    proc = subprocess.run([sys.executable, "verify.py"], cwd=extracted, capture_output=True, text=True)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "RESULT: FAIL" in proc.stdout
    assert "[attribution_seal] attribution_hash does NOT recompute" in proc.stdout


def test_bundled_verify_py_fails_on_forged_review_status(tmp_path):
    """Marking a pending record 'approved' in the bundled record must FAIL the
    attribution seal — the review status is a DISPLAY field the content-only
    record_hash leaves forgeable, so only the attribution seal catches it."""
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = build_evidence_pack(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    extracted = _extract(result["pack_path"], tmp_path / "forge-review")

    rec_file = next(extracted.glob("snapshots/*/evidence-record.json"))
    record = json.loads(rec_file.read_text(encoding="utf-8"))
    assert record["review"]["review_status"] == "pending"
    record["review"]["review_status"] = "approved"  # forge the human-review verdict
    rec_file.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")

    proc = subprocess.run([sys.executable, "verify.py"], cwd=extracted, capture_output=True, text=True)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "RESULT: FAIL" in proc.stdout
    assert "[attribution_seal] attribution_hash does NOT recompute" in proc.stdout


def test_bundled_verify_py_reports_limited_scope_for_legacy_attribution(tmp_path):
    """A record stripped of its attribution_hash but still displaying forgeable
    attribution fields must NOT print an unqualified PASS over them: verify.py
    reports LIMITED SCOPE (a SKIP naming the unsealed fields), mirroring the online
    verifier's downgrade — otherwise the offline artifact would over-claim."""
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = build_evidence_pack(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    extracted = _extract(result["pack_path"], tmp_path / "legacy-attr")

    rec_file = next(extracted.glob("snapshots/*/evidence-record.json"))
    record = json.loads(rec_file.read_text(encoding="utf-8"))
    # Drop only the attribution seal; content seal + display fields remain.
    record.pop("attribution_hash", None)
    record.pop("attribution_hash_method", None)
    rec_file.write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")

    proc = subprocess.run([sys.executable, "verify.py"], cwd=extracted, capture_output=True, text=True)
    # No FAIL: absence of the seal is honestly reported, not treated as tampering.
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "[attribution_seal] LIMITED SCOPE" in proc.stdout
    # It must NOT claim an unqualified attribution PASS over the forgeable fields.
    assert "[attribution_seal] attribution_hash recomputes" not in proc.stdout


def test_pack_without_token_has_no_timestamp_section(tmp_path):
    """No token → no timestamp/ entries and no manifest/README mention: the pack
    must never imply an external timestamp the operator has not produced."""
    _make_record(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")

    result = build_evidence_pack(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)

    assert result["status"] == "ok", result
    names = set(_read_zip(result["pack_path"]).keys())
    assert not any(n.startswith("timestamp/") for n in names)
    assert "external_timestamp" not in result["manifest"]
    readme = _read_zip(result["pack_path"])["HOW-TO-VERIFY.md"].decode("utf-8")
    assert "RFC 3161 timestamp (included)" not in readme
