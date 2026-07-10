"""Regression tests for two audit-vault date-handling bugs (G4-api).

1. validate_date_range must not raise on Feb 29 of a leap year (the year-2
   fallback date is never a leap year, so date(year-2, 2, 29) would crash).
2. _fetch_runs_for_vault must keep records timestamped at the final second of
   date_to even when the stored timestamp is offset-aware ('+00:00').
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

from app.audit_export import build_period_audit_vault, validate_date_range
from app.audit_export import _fetch_runs_for_vault


# ── Bug 1: leap-day ValueError ────────────────────────────────────────────────

class _FebTwentyNine(date):
    """A date subclass whose today() is fixed to a leap-day (2028-02-29)."""

    @classmethod
    def today(cls):  # type: ignore[override]
        return date(2028, 2, 29)


def test_validate_date_range_no_crash_on_leap_day():
    """On 2028-02-29, validate_date_range must return cleanly, not raise ValueError."""
    with patch("app.audit_export.date", _FebTwentyNine):
        # Pre-fix: date(2026, 2, 29) raises ValueError; post-fix it must not.
        ok, msg = validate_date_range("2028-02-01", "2028-02-28")
    assert ok is True
    assert msg == ""


def test_validate_date_range_leap_day_two_year_boundary():
    """The two-years-ago cutoff still rejects dates older than that on a leap day."""
    with patch("app.audit_export.date", _FebTwentyNine):
        ok, msg = validate_date_range("2025-01-01", "2028-02-28")
    assert ok is False
    assert "2 years" in msg


# ── Bug 2: offset-aware timestamp dropped at final second of date_to ─────────

def test_naive_ts_strips_utc_offset():
    """Offset-aware and 'Z' timestamps normalize to a naive seconds string."""
    from app.audit_export import _naive_ts
    assert _naive_ts("2026-07-11T23:59:59+00:00") == "2026-07-11T23:59:59"
    assert _naive_ts("2026-07-11T23:59:59Z") == "2026-07-11T23:59:59"
    assert _naive_ts("2026-07-11T23:59:59") == "2026-07-11T23:59:59"
    assert _naive_ts("2026-07-11T12:00:00-05:00") == "2026-07-11T12:00:00"


def test_fetch_runs_keeps_final_second_offset_aware(tmp_path: Path):
    """A record at date_to's final second with '+00:00' must be included."""
    runs_dir = tmp_path / "data" / "source_runs"
    runs_dir.mkdir(parents=True)
    record = {
        "source_id": "AE-1",
        "run_id": "r-final-second",
        "timestamp_utc": "2026-07-11T23:59:59+00:00",
        "change_status": "CHANGED",
    }
    (runs_dir / "source_runs.jsonl").write_text(
        json.dumps(record) + "\n", encoding="utf-8"
    )

    matching = _fetch_runs_for_vault(
        tmp_path, ["AE-1"], date_from="2026-07-11", date_to="2026-07-11"
    )

    run_ids = [r.get("run_id") for r in matching]
    assert "r-final-second" in run_ids, (
        "Record at the final second of date_to was dropped because its "
        "offset-aware timestamp sorted after the naive upper bound."
    )
