"""Tests for review_queue.py accountability logging — Feature 2."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from app.review_queue import build_review_queue, record_review_action


# ── Test 1: build_review_queue records include action_taken field ──────────────

def test_queue_rows_include_action_taken_field():
    """Every row returned by build_review_queue must have an action_taken key (value None when not actioned)."""
    result = build_review_queue(market="AE", status="all", limit=5)
    assert result["ok"] is True
    for row in result["queue"]:
        assert "action_taken" in row, f"Missing action_taken in row: {row.get('evidence_record_id')}"
        # Unactioned records must have None (not missing)
        if row["action_taken"] is not None:
            assert row["action_taken"] in {"accepted", "not_applicable", "escalated"}


# ── Test 2: record_review_action with valid inputs ────────────────────────────

def test_record_review_action_valid():
    """Valid inputs must return status=ok with an ISO 8601 action_timestamp."""
    import re
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        result = record_review_action(
            "test-record-001",
            "accepted",
            "reviewer@statuteproof.com",
            reason="Reviewed and confirmed no material change.",
            base_dir=base,
        )
    assert result["status"] == "ok"
    assert result["record_id"] == "test-record-001"
    assert result["action"] == "accepted"
    # action_timestamp must be ISO 8601
    ts = result.get("action_timestamp", "")
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", ts), f"Not ISO 8601: {ts}"


# ── Test 3: invalid action value returns status=error ─────────────────────────

def test_record_review_action_invalid_action():
    """An unrecognised action string must return status=error."""
    with tempfile.TemporaryDirectory() as tmp:
        result = record_review_action(
            "test-record-002",
            "delete",  # not a valid action
            "reviewer@statuteproof.com",
            base_dir=Path(tmp),
        )
    assert result["status"] == "error"
    assert "action" in result["message"].lower() or "invalid" in result["message"].lower()


# ── Test 4: empty user_id returns status=error ────────────────────────────────

def test_record_review_action_empty_user_id():
    """An empty user_id must return status=error."""
    with tempfile.TemporaryDirectory() as tmp:
        result = record_review_action(
            "test-record-003",
            "escalated",
            "",  # empty user_id
            base_dir=Path(tmp),
        )
    assert result["status"] == "error"
    assert "user_id" in result["message"].lower()


# ── Test 5: reason longer than 500 chars is truncated ─────────────────────────

def test_record_review_action_truncates_long_reason():
    """A reason longer than 500 characters must be truncated to 500 chars in the log."""
    long_reason = "x" * 1000
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        result = record_review_action(
            "test-record-004",
            "not_applicable",
            "reviewer@test.com",
            reason=long_reason,
            base_dir=base,
        )
        assert result["status"] == "ok"
        # Verify the log file has the truncated reason
        log_path = base / "data" / "review_actions" / "review_actions.jsonl"
        assert log_path.exists()
        last_line = log_path.read_text(encoding="utf-8").strip().splitlines()[-1]
        entry = json.loads(last_line)
        assert len(entry["reason"]) == 500
