"""Tests for audit_export.py period-based Audit Vault — Feature 5."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.api as api
import app.api_reports as api_reports
from app.api import _Handler
from app.audit_export import build_period_audit_vault, validate_date_range


def _write_runs_jsonl(base: Path, rows: list[dict]) -> None:
    runs_dir = base / "data" / "source_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "source_runs.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )


def _run_row(i: int, *, source_id: str = "cbuae-test") -> dict:
    return {
        "run_id": f"test-run-{i:03d}",
        "source_id": source_id,
        "official_url": f"https://cbuae.gov.ae/test-{i}",
        "timestamp_utc": f"2026-03-{10 + i:02d}T10:00:00",
        "change_status": "CHANGED",
        "extraction_quality": "OK",
        "normalized_hash": f"hash{i}",
        "content_hash": f"hash{i}",
        "market": "AE",
    }


# ── Test 1: validate_date_range with valid dates ──────────────────────────────

def test_validate_date_range_valid():
    """Valid recent date range (both dates in the past) must return (True, '')."""
    ok, msg = validate_date_range("2026-01-01", "2026-06-01")
    assert ok is True
    assert msg == ""


# ── Test 2: validate_date_range with date_from > date_to ─────────────────────

def test_validate_date_range_from_after_to():
    """date_from > date_to must return (False, non-empty error message)."""
    ok, msg = validate_date_range("2026-06-30", "2026-01-01")
    assert ok is False
    assert len(msg) > 0


# ── Test 3: validate_date_range with invalid format ───────────────────────────

def test_validate_date_range_invalid_format():
    """Non-ISO date strings must return (False, non-empty error message)."""
    ok, msg = validate_date_range("30/01/2026", "2026-06-30")
    assert ok is False
    assert len(msg) > 0


# ── Test 4: empty source_ids returns error ────────────────────────────────────

def test_build_period_audit_vault_empty_source_ids():
    """An empty source_ids list must return status='error'."""
    with tempfile.TemporaryDirectory() as tmp:
        result = build_period_audit_vault(
            source_ids=[],
            date_from="2026-01-01",
            date_to="2026-06-30",
            base_dir=Path(tmp),
        )
    assert result["status"] == "error"
    assert "source_ids" in result["message"].lower() or "empty" in result["message"].lower()


# ── Test 5: no matching records returns status="empty" ────────────────────────

def test_build_period_audit_vault_no_records():
    """When no records match, build_period_audit_vault must return status='empty'."""
    with tempfile.TemporaryDirectory() as tmp:
        result = build_period_audit_vault(
            source_ids=["nonexistent-source-xyz-99999"],
            date_from="2026-01-01",
            date_to="2026-01-31",
            base_dir=Path(tmp),
        )
    assert result["status"] == "empty"
    assert result["record_count"] == 0


# ── Test 6: valid inputs with mock data returns status="ok" with .zip ─────────

def test_build_period_audit_vault_with_mock_data_returns_zip():
    """With matching run records, build_period_audit_vault must return status='ok' and a .zip path."""
    import json

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)

        # Write a mock source_runs.jsonl entry
        runs_dir = base / "data" / "source_runs"
        runs_dir.mkdir(parents=True, exist_ok=True)
        mock_run = {
            "run_id": "test-run-001",
            "source_id": "cbuae-test",
            "official_url": "https://cbuae.gov.ae/test",
            "timestamp_utc": "2026-03-15T10:00:00",
            "change_status": "CHANGED",
            "extraction_quality": "OK",
            "normalized_hash": "abc123def456",
            "content_hash": "abc123def456",
            "market": "AE",
        }
        (runs_dir / "source_runs.jsonl").write_text(
            json.dumps(mock_run) + "\n",
            encoding="utf-8",
        )

        result = build_period_audit_vault(
            source_ids=["cbuae-test"],
            date_from="2026-03-01",
            date_to="2026-03-31",
            base_dir=base,
        )

    assert result["status"] == "ok", f"Unexpected status: {result}"
    assert result["record_count"] >= 1
    vault_path = result["vault_path"]
    assert vault_path.endswith(".zip"), f"vault_path does not end with .zip: {vault_path}"


# ── availability guard: bounded record materialization ──────────────────────────

def test_build_period_audit_vault_rejects_oversized_selection():
    """More matching run records than the cap → reject, never truncate.

    The fetcher stops one past the cap, so an over-cap request never materializes
    an unbounded number of run records (nor triggers unbounded per-record pack
    generation). Rejecting keeps the vault honest — a partial vault would be
    misleading evidence.
    """
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        _write_runs_jsonl(base, [_run_row(1), _run_row(2)])

        result = build_period_audit_vault(
            source_ids=["cbuae-test"],
            date_from="2026-03-01",
            date_to="2026-03-31",
            base_dir=base,
            max_records=1,
        )

    assert result["status"] == "too_large", result
    assert result["max_records"] == 1
    assert "vault_path" not in result
    assert "narrow" in result["message"].lower()


def test_build_period_audit_vault_exactly_at_cap_still_builds():
    """Boundary: a selection with exactly max_records records builds normally."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        _write_runs_jsonl(base, [_run_row(1)])

        result = build_period_audit_vault(
            source_ids=["cbuae-test"],
            date_from="2026-03-01",
            date_to="2026-03-31",
            base_dir=base,
            max_records=1,
        )

    assert result["status"] == "ok", result
    assert result["record_count"] == 1


# ── API handler: too_large → 413, error → generic 500 (no info leak) ─────────────

def _bare_handler() -> _Handler:
    return _Handler.__new__(_Handler)


def test_audit_vault_handler_413_when_selection_too_large(monkeypatch):
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
    monkeypatch.setattr(
        "app.audit_export.build_period_audit_vault",
        lambda *a, **k: {"status": "too_large", "max_records": 2000, "message": "narrow the selection"},
    )
    captured: dict = {}
    handler._send_json = lambda data, status=200, **kw: captured.update(data=data, status=status)  # type: ignore[method-assign]

    handler._handle_audit_vault()

    assert captured["status"] == 413
    assert captured["data"]["ok"] is False
    assert captured["data"]["max_records"] == 2000


def test_audit_vault_handler_error_does_not_leak_internal_message(monkeypatch):
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
    secret_path = "/srv/statuteproof/data/audit_vaults"
    monkeypatch.setattr(
        "app.audit_export.build_period_audit_vault",
        lambda *a, **k: {"status": "error", "message": f"[Errno 13] Permission denied: '{secret_path}'"},
    )
    captured: dict = {}
    handler._send_json = lambda data, status=200, **kw: captured.update(data=data, status=status)  # type: ignore[method-assign]

    handler._handle_audit_vault()

    assert captured["status"] == 500
    assert secret_path not in json.dumps(captured["data"])
    assert captured["data"]["message"] == "Failed to build the audit vault."
