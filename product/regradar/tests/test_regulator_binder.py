"""Tests for the Regulator-ready Evidence Binder (branch tenten).

Covers: period+source binder assembly, inclusion of the sealed evidence records +
raw/normalized snapshots + per-run diffs, the binder-level content hash
recomputation, the embedded standalone verify.py genuinely verifying an included
record (seal + snapshots + binder hash) as a real subprocess and FAILING on a
tampered record/snapshot, data-level source scoping, empty-range handling, the
COVER.md legal-safety guard + verbatim disclaimer, and the API handler's
owner-scope / capability / auth gating.

Fixtures build genuine complete/VERIFIED canonical evidence records through the
product writer, so the binder is exercised against real evidence objects.
"""

from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.api as api
import app.api_reports as api_reports
from app.api import _Handler
from app.evidence_assessment import LEGAL_DISCLAIMER
from app.evidence_records import create_canonical_evidence_record
from app.regulator_binder import (
    SHORT_MONITORING_DISCLAIMER,
    _binder_content_hash,
    build_regulator_binder,
)
from app.legal_safety import assert_no_forbidden_claims


# ── fixtures ────────────────────────────────────────────────────────────────────

def _write(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def _make_first_seen(base: Path, *, source_id: str, run_id: str, timestamp: str,
                     text: str = "Current official regulatory text captured for evidence.") -> dict:
    run = _run_dict(base, source_id=source_id, run_id=run_id, timestamp=timestamp,
                    text=text, change_status="FIRST_SEEN")
    return create_canonical_evidence_record(run, base_dir=base)


def _make_changed(base: Path, *, source_id: str, run_id: str, timestamp: str,
                  previous_text: str, current_text: str) -> dict:
    """Create a CHANGED record (with a real diff artifact) against a prior state."""
    previous_run = _run_dict(base, source_id=source_id, run_id=f"{run_id}-prev",
                             timestamp="2026-02-01T09:00:00Z", text=previous_text,
                             change_status="FIRST_SEEN")
    run = _run_dict(base, source_id=source_id, run_id=run_id, timestamp=timestamp,
                    text=current_text, change_status="CHANGED")
    return create_canonical_evidence_record(run, previous_run, base_dir=base)


def _read_zip(pack_path: str) -> dict[str, bytes]:
    with zipfile.ZipFile(pack_path, "r") as zf:
        return {name: zf.read(name) for name in zf.namelist()}


def _extract(pack_path: str, dest: Path) -> Path:
    with zipfile.ZipFile(pack_path, "r") as zf:
        zf.extractall(dest)
    return dest


# ── binder assembly ─────────────────────────────────────────────────────────────

def test_build_binder_assembles_expected_files(tmp_path):
    _make_first_seen(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")

    result = build_regulator_binder(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)

    assert result["status"] == "ok", result
    assert result["record_count"] == 1
    assert result["binder_path"].endswith(".zip")
    assert Path(result["binder_path"]).exists()

    names = set(_read_zip(result["binder_path"]).keys())
    assert "manifest.json" in names
    assert "COVER.md" in names
    assert "HOW-TO-VERIFY.md" in names
    assert "verify.py" in names
    assert "DISCLAIMER.txt" in names
    assert any(n.endswith("/raw.txt") for n in names)
    assert any(n.endswith("/normalized.txt") for n in names)
    assert any(n.endswith("/evidence-record.json") for n in names)


def test_binder_includes_sealed_record_and_diff_for_changed(tmp_path):
    _make_changed(
        tmp_path,
        source_id="dfsa-test",
        run_id="run-changed",
        timestamp="2026-03-20T10:00:00Z",
        previous_text="Original rulebook clause A applies to firms.",
        current_text="Amended rulebook clause A applies to firms and branches.",
    )

    result = build_regulator_binder(["dfsa-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    assert result["status"] == "ok", result
    assert result["diff_count"] == 1

    contents = _read_zip(result["binder_path"])
    manifest = json.loads(contents["manifest.json"])
    row = manifest["records"][0]

    # The sealed evidence record is embedded and carries a record_hash.
    rec_bytes = contents[row["evidence_record_file"]]
    sealed = json.loads(rec_bytes)
    assert sealed.get("record_hash")
    assert sealed["record_hash_method"] == "content-sha256-v1"
    assert row["record_hash"] == sealed["record_hash"].replace("sha256:", "")

    # The diff artifact rides along and is referenced by the manifest row.
    assert "diff_file" in row
    assert row["diff_file"] in contents
    assert b"@@" in contents[row["diff_file"]] or b"---" in contents[row["diff_file"]]


def test_empty_range_returns_empty_not_a_fake_pack(tmp_path):
    result = build_regulator_binder(["nope-zzz"], "2026-01-01", "2026-01-31", base_dir=tmp_path)
    assert result["status"] == "empty"
    assert result["record_count"] == 0
    assert "binder_path" not in result


def test_out_of_range_record_excluded(tmp_path):
    _make_first_seen(tmp_path, source_id="cbuae-test", run_id="run-jan", timestamp="2026-01-10T10:00:00Z")
    result = build_regulator_binder(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    assert result["status"] == "empty"


# ── availability guard: bounded record materialization ──────────────────────────

def test_binder_rejects_oversized_selection(tmp_path):
    """More records than the cap → reject the whole selection, never truncate.

    The collector stops one past the cap, so an over-cap request never loads an
    unbounded number of records' bytes into memory (the OOM guard). Rejecting (vs
    silently truncating) keeps the binder honest — a partial binder would be
    misleading evidence.
    """
    _make_first_seen(tmp_path, source_id="cbuae-test", run_id="run-a", timestamp="2026-03-10T10:00:00Z")
    _make_first_seen(tmp_path, source_id="cbuae-test", run_id="run-b", timestamp="2026-03-12T10:00:00Z")

    result = build_regulator_binder(
        ["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path, max_records=1
    )

    assert result["status"] == "too_large", result
    assert result["max_records"] == 1
    assert "binder_path" not in result
    assert "narrow" in result["message"].lower()


def test_binder_exactly_at_cap_still_builds(tmp_path):
    """Boundary: a selection with exactly max_records records builds normally."""
    _make_first_seen(tmp_path, source_id="cbuae-test", run_id="run-a", timestamp="2026-03-10T10:00:00Z")

    result = build_regulator_binder(
        ["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path, max_records=1
    )

    assert result["status"] == "ok", result
    assert result["record_count"] == 1


def test_error_on_empty_source_ids(tmp_path):
    result = build_regulator_binder([], "2026-01-01", "2026-01-31", base_dir=tmp_path)
    assert result["status"] == "error"


def test_error_on_bad_date_range(tmp_path):
    result = build_regulator_binder(["cbuae-test"], "2026-06-30", "2026-01-01", base_dir=tmp_path)
    assert result["status"] == "error"


# ── data-level source scoping ────────────────────────────────────────────────────

def test_binder_never_includes_a_non_requested_source(tmp_path):
    _make_first_seen(tmp_path, source_id="cbuae-test", run_id="run-a", timestamp="2026-03-15T10:00:00Z")
    _make_first_seen(tmp_path, source_id="dfsa-test", run_id="run-b", timestamp="2026-03-16T10:00:00Z")

    result = build_regulator_binder(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    manifest = json.loads(_read_zip(result["binder_path"])["manifest.json"])

    assert result["record_count"] == 1
    assert manifest["source_ids"] == ["cbuae-test"]
    assert {r["source_id"] for r in manifest["records"]} == {"cbuae-test"}


# ── binder content hash ──────────────────────────────────────────────────────────

def test_manifest_binder_hash_recomputes_from_record_hashes(tmp_path):
    _make_first_seen(tmp_path, source_id="cbuae-test", run_id="run-1", timestamp="2026-03-10T10:00:00Z")
    _make_first_seen(tmp_path, source_id="cbuae-test", run_id="run-2", timestamp="2026-03-11T10:00:00Z")

    result = build_regulator_binder(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    manifest = json.loads(_read_zip(result["binder_path"])["manifest.json"])

    assert manifest["record_count"] == 2
    record_hashes = [r["record_hash"] for r in manifest["records"]]
    recomputed = _binder_content_hash(record_hashes)
    assert recomputed == manifest["binder_content_hash"]
    assert recomputed == result["binder_content_hash"]

    # Independent recomputation matching the documented method (sorted, \n-joined).
    bare = sorted(h.replace("sha256:", "") for h in record_hashes)
    manual = hashlib.sha256("\n".join(bare).encode("utf-8")).hexdigest()
    assert manual == manifest["binder_content_hash"]


# ── the embedded verify.py must genuinely work ───────────────────────────────────

def test_bundled_verify_py_passes_on_clean_binder(tmp_path):
    _make_changed(
        tmp_path, source_id="cbuae-test", run_id="run-c", timestamp="2026-03-18T10:00:00Z",
        previous_text="Old text.", current_text="New amended text.",
    )
    result = build_regulator_binder(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    extracted = _extract(result["binder_path"], tmp_path / "clean")

    proc = subprocess.run([sys.executable, "verify.py"], cwd=extracted, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "RESULT: PASS" in proc.stdout
    assert "[seal]" in proc.stdout                # the record self-seal was checked
    assert "binder_content_hash=" in proc.stdout  # the binder hash was checked
    assert "FAIL" not in proc.stdout


def test_bundled_verify_py_fails_on_tampered_snapshot(tmp_path):
    _make_first_seen(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = build_regulator_binder(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    extracted = _extract(result["binder_path"], tmp_path / "tampered")

    target = next(extracted.glob("snapshots/*/normalized.txt"))
    target.write_text(target.read_text(encoding="utf-8") + "TAMPERED", encoding="utf-8")

    proc = subprocess.run([sys.executable, "verify.py"], cwd=extracted, capture_output=True, text=True)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "RESULT: FAIL" in proc.stdout


def test_bundled_verify_py_fails_on_tampered_record_seal(tmp_path):
    _make_first_seen(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = build_regulator_binder(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    extracted = _extract(result["binder_path"], tmp_path / "tampered-seal")

    # Alter a field INSIDE the sealed content block; record_hash must no longer
    # recompute, so the [seal] check must FAIL even though the snapshots are intact.
    record_file = next(extracted.glob("snapshots/*/evidence-record.json"))
    sealed = json.loads(record_file.read_text(encoding="utf-8"))
    sealed["content"]["raw_hash"] = "sha256:" + ("0" * 64)
    record_file.write_text(json.dumps(sealed, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    proc = subprocess.run([sys.executable, "verify.py"], cwd=extracted, capture_output=True, text=True)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "RESULT: FAIL" in proc.stdout
    assert "[seal]" in proc.stdout


# ── legal safety: COVER.md ───────────────────────────────────────────────────────

def test_cover_md_has_verbatim_disclaimer_and_clears_guard(tmp_path):
    _make_first_seen(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = build_regulator_binder(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    contents = _read_zip(result["binder_path"])
    cover = contents["COVER.md"].decode("utf-8")

    assert SHORT_MONITORING_DISCLAIMER in cover
    assert cover.rstrip().endswith(SHORT_MONITORING_DISCLAIMER)
    assert LEGAL_DISCLAIMER in cover
    # A timestamped timeline entry for the captured change is present.
    assert "2026-03-15T10:00:00Z" in cover
    # The authored prose clears the shared forbidden-claims guard.
    assert_no_forbidden_claims(cover, label="cover")
    assert_no_forbidden_claims(contents["HOW-TO-VERIFY.md"].decode("utf-8"), label="how-to")
    assert_no_forbidden_claims(contents["verify.py"].decode("utf-8"), label="verify")


# ── Stage-3: sealed reviewer-decision chain segment (additive, org-scoped) ───────

def _seal_decision(tmp_path, monkeypatch, *, org_id, decided_at, kind="reviewed",
                   statement="Reviewed the change against our licence scope.",
                   source_id="cbuae-test", alert_id="alert-1"):
    """Seal one decision into an isolated decision DB pointed at ``tmp_path``."""
    import app.db as app_db
    import app.decision_records as dr

    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "decisions.db"))
    monkeypatch.setattr(dr, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(dr, "_decided_at_utc", lambda: decided_at)
    reviewed = {
        "evidence_record_id": "rec_cbuae_1",
        "record_hash": "sha256:" + "a" * 64,
        "source_id": source_id,
        "source_name": "CBUAE Test Source",
        "official_url": "https://example.gov/cbuae-test",
        "alert_id": alert_id,
    }
    return dr.seal_decision(101, org_id, display_name="A. Rahman", reviewed=reviewed,
                            kind=kind, statement=statement)


def test_binder_omits_decisions_without_org_id(tmp_path):
    """No org_id → no decision section (dormant/additive, no regression)."""
    _make_first_seen(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = build_regulator_binder(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    assert result["status"] == "ok"
    assert result["decision_count"] == 0
    manifest = json.loads(_read_zip(result["binder_path"])["manifest.json"])
    assert "decisions" not in manifest
    assert not any(n.startswith("decisions/") for n in _read_zip(result["binder_path"]))


def test_binder_embeds_and_verifies_decision_chain(tmp_path, monkeypatch):
    _make_first_seen(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    assert _seal_decision(tmp_path, monkeypatch, org_id=42, decided_at="2026-03-20T09:00:00.000000Z")
    assert _seal_decision(tmp_path, monkeypatch, org_id=42, decided_at="2026-03-21T09:00:00.000000Z",
                          kind="acknowledged", statement="Acknowledged; forwarded to MLRO.")

    result = build_regulator_binder(["cbuae-test"], "2026-03-01", "2026-03-31",
                                    base_dir=tmp_path, org_id=42)
    assert result["status"] == "ok", result
    assert result["decision_count"] == 2

    contents = _read_zip(result["binder_path"])
    manifest = json.loads(contents["manifest.json"])
    assert "decisions" in manifest
    drecords = manifest["decisions"]["records"]
    assert len(drecords) == 2
    assert manifest["decisions"]["segment_anchor_prev_hash"] == ""  # genesis
    for row in drecords:
        assert row["decision_file"] in contents

    # The embedded verify.py verifies the decision chain (seal + prev linkage).
    extracted = _extract(result["binder_path"], tmp_path / "clean")
    proc = subprocess.run([sys.executable, "verify.py"], cwd=extracted, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "RESULT: PASS" in proc.stdout
    assert "[decision seal]" in proc.stdout
    assert "[decision link]" in proc.stdout
    assert "decision_chain_hash=" in proc.stdout
    assert "FAIL" not in proc.stdout


def test_binder_decision_chain_hash_is_reproducible(tmp_path, monkeypatch):
    _make_first_seen(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    _seal_decision(tmp_path, monkeypatch, org_id=42, decided_at="2026-03-20T09:00:00.000000Z")
    _seal_decision(tmp_path, monkeypatch, org_id=42, decided_at="2026-03-21T09:00:00.000000Z")

    result = build_regulator_binder(["cbuae-test"], "2026-03-01", "2026-03-31",
                                    base_dir=tmp_path, org_id=42)
    manifest = json.loads(_read_zip(result["binder_path"])["manifest.json"])
    decisions = manifest["decisions"]
    seals = [r["record_hash"] for r in decisions["records"]]
    bare = sorted(h.replace("sha256:", "") for h in seals)
    manual = hashlib.sha256("\n".join(bare).encode("utf-8")).hexdigest()
    assert manual == decisions["decision_chain_hash"]


def test_binder_verify_py_fails_on_tampered_decision(tmp_path, monkeypatch):
    _make_first_seen(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    _seal_decision(tmp_path, monkeypatch, org_id=42, decided_at="2026-03-20T09:00:00.000000Z")

    result = build_regulator_binder(["cbuae-test"], "2026-03-01", "2026-03-31",
                                    base_dir=tmp_path, org_id=42)
    assert result["status"] == "ok"
    extracted = _extract(result["binder_path"], tmp_path / "tampered")

    dfile = next(extracted.glob("decisions/*/decision-record.json"))
    sealed = json.loads(dfile.read_text(encoding="utf-8"))
    sealed["content"]["decision"]["statement"] = "TAMPERED statement not sealed by the reviewer."
    dfile.write_text(json.dumps(sealed, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    proc = subprocess.run([sys.executable, "verify.py"], cwd=extracted, capture_output=True, text=True)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "RESULT: FAIL" in proc.stdout
    assert "[decision seal]" in proc.stdout


def test_binder_decision_out_of_period_excluded(tmp_path, monkeypatch):
    _make_first_seen(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    # Decision dated OUTSIDE the binder period → no decision section.
    _seal_decision(tmp_path, monkeypatch, org_id=42, decided_at="2026-08-01T09:00:00.000000Z")

    result = build_regulator_binder(["cbuae-test"], "2026-03-01", "2026-03-31",
                                    base_dir=tmp_path, org_id=42)
    assert result["status"] == "ok"
    assert result["decision_count"] == 0
    manifest = json.loads(_read_zip(result["binder_path"])["manifest.json"])
    assert "decisions" not in manifest


def test_binder_decision_cover_clears_guard_and_omits_user_statement(tmp_path, monkeypatch):
    _make_first_seen(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    secret_words = "Reviewer verbatim words that must not appear in the guarded cover."
    _seal_decision(tmp_path, monkeypatch, org_id=42, decided_at="2026-03-20T09:00:00.000000Z",
                   statement=secret_words)

    result = build_regulator_binder(["cbuae-test"], "2026-03-01", "2026-03-31",
                                    base_dir=tmp_path, org_id=42)
    contents = _read_zip(result["binder_path"])
    cover = contents["COVER.md"].decode("utf-8")

    assert "detected → reviewed → decided" in cover
    # The reviewer's verbatim statement is NEVER placed into the guarded COVER.md …
    assert secret_words not in cover
    # … but it IS sealed, verbatim, inside its own (unguarded) decision-record.json.
    dfile = next(n for n in contents if n.startswith("decisions/") and n.endswith(".json"))
    assert secret_words in contents[dfile].decode("utf-8")
    assert_no_forbidden_claims(cover, label="cover-with-decisions")


def test_manifest_points_at_the_verification_spec(tmp_path):
    _make_first_seen(tmp_path, source_id="cbuae-test", run_id="run-001", timestamp="2026-03-15T10:00:00Z")
    result = build_regulator_binder(["cbuae-test"], "2026-03-01", "2026-03-31", base_dir=tmp_path)
    manifest = json.loads(_read_zip(result["binder_path"])["manifest.json"])
    assert manifest["spec_reference"] == "docs/EVIDENCE-VERIFICATION-SPEC.md"
    assert manifest["hash_algorithm"] == "sha256"
    assert manifest["record_hash_method"] == "content-sha256-v1"


# ── API handler: auth / capability / owner-scope gating ──────────────────────────

def _bare_handler() -> _Handler:
    return _Handler.__new__(_Handler)


def test_handler_rejects_unauthenticated(monkeypatch):
    monkeypatch.setattr(api, "require_auth", lambda handler: None)
    monkeypatch.setattr(api_reports, "require_auth", lambda handler: None)
    handler = _bare_handler()
    captured: dict = {}
    handler._send_json = lambda data, status=200, **kw: captured.update(data=data, status=status)  # type: ignore[method-assign]

    handler._handle_regulator_binder()

    assert captured["status"] == 401
    assert captured["data"]["ok"] is False


def test_handler_403_when_no_source_in_owner_scope(monkeypatch):
    monkeypatch.setattr(api, "require_auth", lambda handler: {"id": 7, "email": "c@x.io"})
    monkeypatch.setattr(api_reports, "require_auth", lambda handler: {"id": 7, "email": "c@x.io"})
    handler = _bare_handler()
    monkeypatch.setattr(
        handler,
        "_read_json_strict",
        lambda: ({"source_ids": ["someone-elses-custom"], "date_from": "2026-03-01", "date_to": "2026-03-31"}, None),
    )
    monkeypatch.setattr(handler, "_rate_limited", lambda *a, **k: False)
    monkeypatch.setattr(handler, "_require_capability", lambda *a, **k: True)
    # Owner-scope drops the source the caller does not own → nothing entitled.
    monkeypatch.setattr(handler, "_entitle_source_ids", lambda user, ids: [])
    captured: dict = {}
    handler._send_json = lambda data, status=200, **kw: captured.update(data=data, status=status)  # type: ignore[method-assign]

    handler._handle_regulator_binder()

    assert captured["status"] == 403
    assert captured["data"]["ok"] is False


def test_handler_only_builds_with_entitled_sources(monkeypatch):
    """Owner-scope must clip source_ids BEFORE the builder ever sees them."""
    monkeypatch.setattr(api, "require_auth", lambda handler: {"id": 7, "email": "c@x.io"})
    monkeypatch.setattr(api_reports, "require_auth", lambda handler: {"id": 7, "email": "c@x.io"})
    handler = _bare_handler()
    monkeypatch.setattr(
        handler,
        "_read_json_strict",
        lambda: ({"source_ids": ["mine", "not-mine"], "date_from": "2026-03-01", "date_to": "2026-03-31"}, None),
    )
    monkeypatch.setattr(handler, "_rate_limited", lambda *a, **k: False)
    monkeypatch.setattr(handler, "_require_capability", lambda *a, **k: True)
    monkeypatch.setattr(handler, "_entitle_source_ids", lambda user, ids: ["mine"])  # drop not-mine

    seen: dict = {}
    import app.regulator_binder as rb
    monkeypatch.setattr(
        rb, "build_regulator_binder",
        lambda source_ids, date_from, date_to: seen.update(source_ids=source_ids)
        or {"status": "empty", "record_count": 0, "message": "none"},
    )
    captured: dict = {}
    handler._send_json = lambda data, status=200, **kw: captured.update(data=data, status=status)  # type: ignore[method-assign]

    handler._handle_regulator_binder()

    assert seen["source_ids"] == ["mine"]      # not-mine never reached the builder
    assert captured["status"] == 404           # empty → 404


def test_handler_streams_zip_for_authenticated_client(monkeypatch, tmp_path):
    fake_zip = tmp_path / "regulator_binder_x.zip"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("manifest.json", "{}")
    fake_zip.write_bytes(buf.getvalue())

    monkeypatch.setattr(api, "require_auth", lambda handler: {"id": 1, "email": "c@x.io"})
    monkeypatch.setattr(api_reports, "require_auth", lambda handler: {"id": 1, "email": "c@x.io"})
    import app.regulator_binder as rb
    monkeypatch.setattr(
        rb, "build_regulator_binder",
        lambda *a, **k: {
            "status": "ok",
            "binder_path": str(fake_zip),
            "binder_filename": "regulator_binder_x.zip",
            "record_count": 1,
        },
    )

    handler = _bare_handler()
    monkeypatch.setattr(
        handler,
        "_read_json_strict",
        lambda: ({"source_ids": ["cbuae-test"], "date_from": "2026-03-01", "date_to": "2026-03-31"}, None),
    )
    monkeypatch.setattr(handler, "_rate_limited", lambda *a, **k: False)
    monkeypatch.setattr(handler, "_require_capability", lambda *a, **k: True)
    monkeypatch.setattr(handler, "_entitle_source_ids", lambda user, ids: ids)
    sent: dict = {}

    def _capture_bytes(body, content_type, status=200, extra_headers=None):
        sent.update(body=body, content_type=content_type, status=status, extra_headers=extra_headers)

    handler._send_bytes = _capture_bytes  # type: ignore[method-assign]
    handler._send_json = lambda data, status=200, **kw: sent.update(json=data, status=status)  # type: ignore[method-assign]

    expected_bytes = fake_zip.read_bytes()  # capture before the handler unlinks it
    handler._handle_regulator_binder()

    assert sent.get("content_type") == "application/zip"
    assert sent.get("body") == expected_bytes
    assert any("Content-Disposition" == k for k, _ in (sent.get("extra_headers") or []))
    # One-shot download: the generated ZIP is removed from disk after streaming.
    assert not fake_zip.exists()


def test_handler_413_when_selection_too_large(monkeypatch):
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
    import app.regulator_binder as rb
    monkeypatch.setattr(
        rb, "build_regulator_binder",
        lambda *a, **k: {"status": "too_large", "max_records": 2000, "message": "narrow the selection"},
    )
    captured: dict = {}
    handler._send_json = lambda data, status=200, **kw: captured.update(data=data, status=status)  # type: ignore[method-assign]

    handler._handle_regulator_binder()

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
    secret_path = "/srv/statuteproof/data/regulator_binders"
    import app.regulator_binder as rb
    monkeypatch.setattr(
        rb, "build_regulator_binder",
        lambda *a, **k: {"status": "error", "message": f"[Errno 13] Permission denied: '{secret_path}'"},
    )
    captured: dict = {}
    handler._send_json = lambda data, status=200, **kw: captured.update(data=data, status=status)  # type: ignore[method-assign]

    handler._handle_regulator_binder()

    assert captured["status"] == 500
    assert secret_path not in json.dumps(captured["data"])
    assert captured["data"]["message"] == "Failed to build regulator binder."
