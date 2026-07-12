"""Tests for the Public Evidence Verifier (POST /api/verify + app.public_verify).

The verifier is the no-login moat: it re-checks the integrity of a record the
CALLER submits, using only standard SHA-256, and never reads the server's
evidence store. These tests build genuine records via the product's real hashing
code paths (``compute_record_hash``, ``stable_normalized_hash``,
``normalize_for_change_hash``, and a real canonical ``evidence-record.json`` from
``create_canonical_evidence_record``) so the self-consistency check is real, not
faked.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.api as api
from app.api import _Handler, _RateLimiter
from app.public_verify import (
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_SKIPPED,
    verify_submission,
)
from app.source_runs import compute_record_hash
from app.text_normalization import normalize_for_change_hash, stable_content_hash, stable_normalized_hash

RAW_TEXT = (
    "Article 1. Licensed entities must maintain complete transaction records.\n"
    "Article 2. Suspicious activity reports are due within five business days.\n"
    "Article 3. Records must be retained for a minimum of five years.\n"
)


# ── genuine record builders (real product code paths, nothing faked) ─────────────

def _genuine_trail_record() -> tuple[dict, str, str]:
    """A source-run trail record whose hashes all come from real product code.

    Mirrors the shape the open spec §2 describes and that
    ``tools/verify_evidence_trail.py`` verifies. The ``record_hash`` is stamped by
    the product's own ``compute_record_hash`` so ``record_hash_self_consistent`` is
    a genuine check, not a hand-written digest.
    """
    normalized = normalize_for_change_hash(RAW_TEXT)
    record = {
        "source_id": "AE-test-source",
        "timestamp_utc": "2026-07-12T00:00:00Z",
        "change_status": "FIRST_SEEN",
        "raw_hash": hashlib.sha256(RAW_TEXT.encode("utf-8")).hexdigest(),
        "normalized_hash": stable_normalized_hash(RAW_TEXT),
        "content_hash": stable_content_hash(RAW_TEXT),
        "prev_record_hash": "",
    }
    record["record_hash"] = compute_record_hash(record, "")
    return record, RAW_TEXT, normalized


def _status_of(result: dict, check_name: str) -> str:
    for check in result["checks"]:
        if check["name"] == check_name:
            return check["status"]
    raise AssertionError(f"check {check_name!r} not present in {result['checks']}")


# ── pure verifier: happy path ────────────────────────────────────────────────────

def test_valid_record_verifies_true():
    record, raw, normalized = _genuine_trail_record()

    result = verify_submission(record, raw=raw, normalized=normalized)

    assert result["ok"] is True
    assert result["verified"] is True
    assert result["spec_url"] == "/verify-spec"
    assert "Not legal advice" in result["disclaimer"]
    # Every one of the six checks is genuinely a pass (nothing skipped, nothing failed).
    for name in (
        "record_is_object",
        "hash_formats",
        "record_hash_self_consistent",
        "raw_bytes_match",
        "normalized_bytes_match",
        "normalization_reproducible",
    ):
        assert _status_of(result, name) == STATUS_PASS, (name, result["checks"])


def test_matching_raw_and_normalized_pass_reproducibility():
    record, raw, normalized = _genuine_trail_record()

    result = verify_submission(record, raw=raw, normalized=normalized)

    assert _status_of(result, "raw_bytes_match") == STATUS_PASS
    assert _status_of(result, "normalized_bytes_match") == STATUS_PASS
    assert _status_of(result, "normalization_reproducible") == STATUS_PASS


# ── pure verifier: tamper detection ──────────────────────────────────────────────

def test_tampered_field_fails_record_hash_self_consistency():
    record, _, _ = _genuine_trail_record()
    # Alter an identifying field WITHOUT re-stamping record_hash — exactly the
    # in-place tamper the chain hash is designed to catch.
    record["change_status"] = "UNCHANGED"

    result = verify_submission(record)

    assert result["verified"] is False
    assert _status_of(result, "record_hash_self_consistent") == STATUS_FAIL


def test_bad_hash_format_fails_hash_formats():
    record, _, _ = _genuine_trail_record()
    record["raw_hash"] = "sha256:NOT-A-VALID-HEX-DIGEST"

    # No raw submitted, so raw_bytes_match stays skipped and hash_formats is the
    # isolated failing check.
    result = verify_submission(record)

    assert result["verified"] is False
    assert _status_of(result, "hash_formats") == STATUS_FAIL


def test_raw_bytes_that_do_not_match_fail_raw_bytes_match():
    record, _, _ = _genuine_trail_record()

    result = verify_submission(record, raw="tampered raw content")

    assert result["verified"] is False
    assert _status_of(result, "raw_bytes_match") == STATUS_FAIL


def test_uppercase_hex_is_rejected_by_hash_formats():
    record, _, _ = _genuine_trail_record()
    record["normalized_hash"] = record["normalized_hash"].upper()

    result = verify_submission(record)

    assert _status_of(result, "hash_formats") == STATUS_FAIL


# ── pure verifier: shape handling / fail-closed ──────────────────────────────────

def test_non_object_record_is_fail_closed_not_raised():
    result = verify_submission("not-a-record")

    assert result["ok"] is True
    assert result["verified"] is False
    assert _status_of(result, "record_is_object") == STATUS_FAIL


def test_prefixed_hashes_accepted_and_optional_inputs_skipped():
    # A record carrying only a normalized hash (sha256:-prefixed) and no raw/record
    # hash — like a canonical evidence-record.json — verifies what it can and
    # skips the rest.
    normalized = normalize_for_change_hash(RAW_TEXT)
    normalized_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    record = {"content": {"current_hash": f"sha256:{normalized_hash}"}}

    result = verify_submission(record, normalized=normalized)

    assert result["verified"] is True
    assert _status_of(result, "normalized_bytes_match") == STATUS_PASS
    assert _status_of(result, "record_hash_self_consistent") == STATUS_SKIPPED
    assert _status_of(result, "raw_bytes_match") == STATUS_SKIPPED
    assert _status_of(result, "normalization_reproducible") == STATUS_SKIPPED


def test_real_canonical_evidence_record_verifies(tmp_path):
    """A genuine canonical evidence-record.json (the object shipped in an Evidence
    Pack) verifies against its own normalized snapshot bytes."""
    from app.evidence_records import create_canonical_evidence_record

    text = "Official regulatory text captured for canonical evidence verification."
    run_dir = tmp_path / "data" / "source_snapshots" / "2026-07-12" / "AE" / "cbuae-test" / "run-verify-1"
    run_dir.mkdir(parents=True, exist_ok=True)
    normalized = normalize_for_change_hash(text)
    (run_dir / "raw.txt").write_text(text, encoding="utf-8")
    (run_dir / "normalized.txt").write_text(normalized, encoding="utf-8")
    (run_dir / "metadata.json").write_text(json.dumps({"provider": "fixture"}), encoding="utf-8")
    (run_dir / "proof.json").write_text(json.dumps({"proof_quality": "GOOD"}), encoding="utf-8")

    run = {
        "run_id": "run-verify-1",
        "timestamp_utc": "2026-07-12T10:00:00Z",
        "market": "AE",
        "source_id": "cbuae-test",
        "source_name": "CBUAE Test Source",
        "category": "regulatory",
        "official_url": "https://example.gov/cbuae-test",
        "access_status": "accessible",
        "fetch_method": "fixture",
        "extraction_quality": "GOOD",
        "change_status": "FIRST_SEEN",
        "normalized_hash": stable_normalized_hash(normalized),
        "snapshot_raw_path": str((run_dir / "raw.txt").relative_to(tmp_path)),
        "snapshot_normalized_path": str((run_dir / "normalized.txt").relative_to(tmp_path)),
        "snapshot_metadata_path": str((run_dir / "metadata.json").relative_to(tmp_path)),
        "proof_block_path": str((run_dir / "proof.json").relative_to(tmp_path)),
    }
    record = create_canonical_evidence_record(run, base_dir=tmp_path)

    # The customer holds record.json + normalized.txt; verify their bytes.
    result = verify_submission(record, normalized=normalized)

    assert result["verified"] is True
    assert _status_of(result, "normalized_bytes_match") == STATUS_PASS
    # A canonical record now seals its own content block (content-sha256-v1), so
    # record_hash_self_consistent is a genuine PASS. raw_bytes_match stays skipped
    # here only because this caller submitted normalized bytes but no raw.txt.
    assert _status_of(result, "record_hash_self_consistent") == STATUS_PASS
    assert _status_of(result, "raw_bytes_match") == STATUS_SKIPPED


def test_tampered_normalized_bytes_fail_against_canonical_record(tmp_path):
    from app.evidence_records import create_canonical_evidence_record

    text = "Second official regulatory text for canonical evidence tamper check."
    run_dir = tmp_path / "data" / "source_snapshots" / "2026-07-12" / "AE" / "cbuae-test2" / "run-verify-2"
    run_dir.mkdir(parents=True, exist_ok=True)
    normalized = normalize_for_change_hash(text)
    (run_dir / "raw.txt").write_text(text, encoding="utf-8")
    (run_dir / "normalized.txt").write_text(normalized, encoding="utf-8")
    (run_dir / "metadata.json").write_text(json.dumps({"provider": "fixture"}), encoding="utf-8")
    (run_dir / "proof.json").write_text(json.dumps({"proof_quality": "GOOD"}), encoding="utf-8")
    run = {
        "run_id": "run-verify-2",
        "timestamp_utc": "2026-07-12T11:00:00Z",
        "market": "AE",
        "source_id": "cbuae-test2",
        "source_name": "CBUAE Test Source 2",
        "category": "regulatory",
        "official_url": "https://example.gov/cbuae-test2",
        "access_status": "accessible",
        "fetch_method": "fixture",
        "extraction_quality": "GOOD",
        "change_status": "FIRST_SEEN",
        "normalized_hash": stable_normalized_hash(normalized),
        "snapshot_raw_path": str((run_dir / "raw.txt").relative_to(tmp_path)),
        "snapshot_normalized_path": str((run_dir / "normalized.txt").relative_to(tmp_path)),
        "snapshot_metadata_path": str((run_dir / "metadata.json").relative_to(tmp_path)),
        "proof_block_path": str((run_dir / "proof.json").relative_to(tmp_path)),
    }
    record = create_canonical_evidence_record(run, base_dir=tmp_path)

    result = verify_submission(record, normalized=normalized + " EXTRA TAMPERED LINE")

    assert result["verified"] is False
    assert _status_of(result, "normalized_bytes_match") == STATUS_FAIL


# ── HTTP endpoint: no auth, fail-closed, rate limiting ───────────────────────────

def _bare_handler() -> _Handler:
    handler = _Handler.__new__(_Handler)
    handler.headers = {}
    return handler


def test_endpoint_requires_no_auth(monkeypatch):
    """POST /api/verify must work with no session — and must never call require_auth."""
    called = {"auth": False}

    def _tripwire(_handler):
        called["auth"] = True
        return None

    monkeypatch.setattr(api, "require_auth", _tripwire)

    record, raw, normalized = _genuine_trail_record()
    handler = _bare_handler()
    monkeypatch.setattr(handler, "_rate_limited", lambda *a, **k: False)
    monkeypatch.setattr(
        handler,
        "_read_json_strict",
        lambda: ({"record": record, "raw": raw, "normalized": normalized}, None),
    )
    captured: dict = {}
    handler._send_json = lambda data, status=200, **kw: captured.update(data=data, status=status)  # type: ignore[method-assign]

    handler._handle_public_verify()

    assert called["auth"] is False, "the public verifier must not gate on authentication"
    assert captured["status"] == 200
    assert captured["data"]["ok"] is True
    assert captured["data"]["verified"] is True


def test_endpoint_missing_record_is_400(monkeypatch):
    handler = _bare_handler()
    monkeypatch.setattr(handler, "_rate_limited", lambda *a, **k: False)
    monkeypatch.setattr(handler, "_read_json_strict", lambda: ({"raw": "x"}, None))
    captured: dict = {}
    handler._send_json = lambda data, status=200, **kw: captured.update(data=data, status=status)  # type: ignore[method-assign]

    handler._handle_public_verify()

    assert captured["status"] == 400
    assert captured["data"]["ok"] is False


def test_endpoint_malformed_body_is_400_not_500(monkeypatch):
    handler = _bare_handler()
    monkeypatch.setattr(handler, "_rate_limited", lambda *a, **k: False)
    # Simulate _read_json_strict rejecting invalid JSON.
    monkeypatch.setattr(handler, "_read_json_strict", lambda: (None, "Invalid JSON."))
    captured: dict = {}
    handler._send_json = lambda data, status=200, **kw: captured.update(data=data, status=status)  # type: ignore[method-assign]

    handler._handle_public_verify()

    assert captured["status"] == 400
    assert captured["data"]["ok"] is False


def test_endpoint_non_string_raw_is_400(monkeypatch):
    record, _, _ = _genuine_trail_record()
    handler = _bare_handler()
    monkeypatch.setattr(handler, "_rate_limited", lambda *a, **k: False)
    monkeypatch.setattr(handler, "_read_json_strict", lambda: ({"record": record, "raw": 123}, None))
    captured: dict = {}
    handler._send_json = lambda data, status=200, **kw: captured.update(data=data, status=status)  # type: ignore[method-assign]

    handler._handle_public_verify()

    assert captured["status"] == 400


def test_endpoint_rate_limit_triggers_after_n_calls(monkeypatch):
    record, raw, normalized = _genuine_trail_record()
    # Fresh 2-per-window limiter so the third call is throttled deterministically.
    monkeypatch.setattr(api, "_VERIFY_LIMITER", _RateLimiter(2, 3600))

    statuses: list[int] = []

    def _run_once() -> None:
        handler = _bare_handler()
        monkeypatch.setattr(
            handler,
            "_read_json_strict",
            lambda: ({"record": record, "raw": raw, "normalized": normalized}, None),
        )
        captured: dict = {}
        handler._send_json = lambda data, status=200, **kw: captured.update(data=data, status=status)  # type: ignore[method-assign]
        handler._handle_public_verify()
        statuses.append(captured["status"])

    _run_once()
    _run_once()
    _run_once()

    assert statuses[0] == 200
    assert statuses[1] == 200
    assert statuses[2] == 429
