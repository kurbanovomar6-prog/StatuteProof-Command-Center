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
from app.api import _Handler
from app.evidence_assessment import LEGAL_DISCLAIMER
from app.evidence_records import create_canonical_evidence_record
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
    sent: dict = {}

    def _capture_bytes(body, content_type, status=200, extra_headers=None):
        sent.update(body=body, content_type=content_type, status=status, extra_headers=extra_headers)

    handler._send_bytes = _capture_bytes  # type: ignore[method-assign]
    handler._send_json = lambda data, status=200, **kw: sent.update(json=data, status=status)  # type: ignore[method-assign]

    handler._handle_evidence_pack()

    assert sent.get("content_type") == "application/zip"
    assert sent.get("body") == fake_zip.read_bytes()
    assert any("Content-Disposition" == k for k, _ in (sent.get("extra_headers") or []))
