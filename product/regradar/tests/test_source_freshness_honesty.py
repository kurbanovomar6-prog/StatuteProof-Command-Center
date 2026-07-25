"""A source that has not been checked recently must not read as healthy.

`app/source_health_timeline.py` has carried `_is_stale` / `_days_since` since it
was written, and nothing outside that module ever called them. So "healthy" on
the customer-facing source table meant the registry's `status` field, which
defaults to "active" — a CONFIGURATION state — while the hand-written
`last_monitor_status` said MONITOR_OK on every alert-eligible row at a median
recorded check age of 36 days. Monitoring runs do not update those fields:
`app/mass_monitoring_runner.py` writes them into the activation QUEUE and sets
`sources_json_changed = False`.

These tests pin the rule the fix introduces: freshness is derived from the run
trail, the age is exposed rather than implied, and staleness overrides the
configured status instead of hiding behind it.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api  # noqa: E402,F401  (resolves the api ⇄ mixin import chain first)
from app.source_health_timeline import (  # noqa: E402
    FRESHNESS_FRESH,
    FRESHNESS_NEVER_RUN,
    FRESHNESS_STALE,
    FRESHNESS_UNKNOWN,
    STALE_AFTER_DAYS,
    check_freshness,
)

from test_api_coverage_uplift import _auth_as, _last, _make_handler  # noqa: E402


def _ago(days: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


# ── the verdict itself ──────────────────────────────────────────────────────


def test_a_recent_check_is_fresh():
    verdict = check_freshness(_ago(1))
    assert verdict["state"] == FRESHNESS_FRESH
    assert verdict["age_days"] < 2


def test_an_old_check_is_stale_and_reports_its_age():
    verdict = check_freshness(_ago(36))
    assert verdict["state"] == FRESHNESS_STALE
    assert 35 < verdict["age_days"] < 37


def test_no_run_at_all_is_never_run_not_fresh():
    """The strongest available statement is that we have never checked it."""
    verdict = check_freshness(None)
    assert verdict["state"] == FRESHNESS_NEVER_RUN
    assert verdict["age_days"] is None


def test_an_unparseable_timestamp_is_not_reported_as_fresh():
    """An unreadable date is not evidence of a recent check."""
    verdict = check_freshness("not-a-timestamp")
    assert verdict["state"] == FRESHNESS_UNKNOWN
    assert verdict["state"] != FRESHNESS_FRESH


def test_the_threshold_is_reported_so_a_caller_need_not_guess_it():
    assert check_freshness(_ago(1))["stale_after_days"] == STALE_AFTER_DAYS


# ── the customer-facing surface ─────────────────────────────────────────────


def _status_row(monkeypatch, *, run: dict | None, registry_status: str = "active") -> dict:
    import app.source_health_timeline as sht
    import app.source_readiness as sr
    import app.source_runs as srun

    _auth_as(monkeypatch, {"id": 5})
    src = {
        "source_id": "AE-x", "name": "Regulator X", "enabled": True,
        "category": "financial_regulator", "url": "https://x.example",
        "status": registry_status,
        # The stale hand-written assertion this axis exists to stop trusting:
        "last_monitor_status": "MONITOR_OK",
    }
    monkeypatch.setattr(sr, "load_market_sources", lambda market: [src])
    monkeypatch.setattr(
        srun, "latest_runs",
        lambda market, include_skipped=False: ({"AE-x": run} if run else {}),
    )
    monkeypatch.setattr(
        sht, "build_source_timeline",
        lambda source_id, org_id=None, limit=200: {"total_events": 0},
    )
    handler = _make_handler("GET", "/api/sources/status?market=AE")
    handler._visible_sources_for = lambda user, sources: sources  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 5  # type: ignore[method-assign]
    handler._handle_sources_status()
    data, status, _ = _last(handler)
    assert status == 200, data
    return data


def test_a_stale_source_does_not_report_status_active(monkeypatch):
    data = _status_row(monkeypatch, run={
        "change_status": "UNCHANGED", "timestamp_utc": _ago(36),
        "access_status": "ok", "extraction_quality": "GOOD",
    })
    row = data["sources"][0]

    assert row["status"] == FRESHNESS_STALE
    assert row["status"] != "active"
    assert row["freshness"] == FRESHNESS_STALE
    assert 35 < row["last_run_age_days"] < 37
    # The configured state is still available — replaced in the headline, not lost.
    assert row["configured_status"] == "active"


def test_a_source_with_no_run_reports_never_run(monkeypatch):
    data = _status_row(monkeypatch, run=None)
    row = data["sources"][0]

    assert row["status"] == FRESHNESS_NEVER_RUN
    assert row["freshness"] == FRESHNESS_NEVER_RUN
    assert row["last_run_age_days"] is None
    assert row["change_status"] == "NOT_RUN"


def test_a_freshly_checked_source_keeps_its_configured_status(monkeypatch):
    """The rule only overrides when freshness cannot back the claim."""
    data = _status_row(monkeypatch, run={
        "change_status": "UNCHANGED", "timestamp_utc": _ago(1),
        "access_status": "ok", "extraction_quality": "GOOD",
    })
    row = data["sources"][0]

    assert row["freshness"] == FRESHNESS_FRESH
    assert row["status"] == "active"


def test_the_response_summarises_freshness_so_it_cannot_be_missed(monkeypatch):
    data = _status_row(monkeypatch, run={
        "change_status": "UNCHANGED", "timestamp_utc": _ago(36),
        "access_status": "ok", "extraction_quality": "GOOD",
    })

    assert data["freshness_summary"] == {FRESHNESS_STALE: 1}


def test_the_registry_monitor_ok_field_cannot_make_a_stale_row_look_healthy(monkeypatch):
    """The row asserts MONITOR_OK in the registry; the surface must ignore it."""
    data = _status_row(monkeypatch, run={
        "change_status": "UNCHANGED", "timestamp_utc": _ago(90),
        "access_status": "ok", "extraction_quality": "GOOD",
    })
    row = data["sources"][0]

    assert row["freshness"] == FRESHNESS_STALE
    assert "MONITOR_OK" not in str(row.get("status"))
