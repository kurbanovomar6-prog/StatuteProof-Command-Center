"""Tests for audit_export.py period-based Audit Vault — Feature 5."""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.audit_export import build_period_audit_vault, validate_date_range


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
