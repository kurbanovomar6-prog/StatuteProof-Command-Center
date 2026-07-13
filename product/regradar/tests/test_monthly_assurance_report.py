"""Tests for monthly_assurance_report.py — Feature 1."""

from __future__ import annotations

from app.evidence_assessment import LEGAL_DISCLAIMER
from app import monthly_assurance_report as mar
from app.monthly_assurance_report import (
    _zero_stats,
    compute_monthly_stats,
    render_assurance_report_markdown,
)

_REQUIRED_KEYS = {
    "period_label",
    "year",
    "month",
    "sources_checked",
    "total_runs",
    "successful_runs",
    "changes_detected",
    "high_risk_count",
    "medium_risk_count",
    "low_risk_count",
    "non_material_count",
    "unreviewed_count",
    "sources_with_errors",
    "uptime_pct",
    "generated_at_utc",
    "is_estimate",
}

_FORBIDDEN_PHRASES = (
    "guarantee compliance",
    "guaranteed compliance",
    "prevent fines",
    "never miss",
    "legal advice",
    "certified by",
    "regulator certified",
    "100% accurate",
    "we handle compliance for you",
    "automated compliance decisions",
    "avoid all penalties",
)


def _sample_stats(**overrides) -> dict:
    base = _zero_stats(2026, 6, is_estimate=False)
    base.update(overrides)
    return base


# ── Test 1: compute_monthly_stats returns correct shape ───────────────────────

def test_compute_monthly_stats_returns_required_keys():
    """compute_monthly_stats must return a dict containing all required keys."""
    stats = compute_monthly_stats(None, 2026, 6)
    missing = _REQUIRED_KEYS - set(stats.keys())
    assert missing == set(), f"Missing keys: {missing}"


# ── Test 2: no-data period returns zero-counts + is_estimate=True ─────────────

def test_compute_monthly_stats_no_data_returns_zeros():
    """When no DB rows exist for the period, all counts must be 0 and is_estimate=True."""
    # Use a future month that has no data
    stats = compute_monthly_stats(None, 2099, 12)
    assert stats["is_estimate"] is True
    assert stats["total_runs"] == 0
    assert stats["sources_checked"] == 0
    assert stats["changes_detected"] == 0
    assert stats["high_risk_count"] == 0


# ── Test 3: uptime_pct is None when total_runs == 0 ──────────────────────────

def test_compute_monthly_stats_uptime_none_when_no_runs():
    """uptime_pct must be None (not 0.0) when total_runs == 0."""
    stats = compute_monthly_stats(None, 2099, 11)
    assert stats["total_runs"] == 0
    assert stats["uptime_pct"] is None


# ── Test 4: render_assurance_report_markdown contains LEGAL_DISCLAIMER ────────

def test_render_contains_legal_disclaimer():
    """The rendered report must include the full LEGAL_DISCLAIMER text."""
    stats = _sample_stats()
    report = render_assurance_report_markdown(stats)
    assert LEGAL_DISCLAIMER in report, "LEGAL_DISCLAIMER missing from rendered report"


# ── Test 5: forbidden phrases are absent ─────────────────────────────────────

def test_render_contains_no_forbidden_phrases():
    """None of the forbidden claim phrases may appear outside the disclaimer block."""
    stats = _sample_stats()
    report = render_assurance_report_markdown(stats)
    # Remove the disclaimer section before checking — the disclaimer legitimately
    # uses words like "legal advice" to deny them ("Not legal advice").
    # Split on the separator before the disclaimer.
    if "**Disclaimer:**" in report:
        content_section = report.split("**Disclaimer:**")[0]
    else:
        content_section = report
    content_lower = content_section.lower()
    for phrase in _FORBIDDEN_PHRASES:
        assert phrase not in content_lower, f"Forbidden phrase in report content: '{phrase}'"


# ── Test 6: period_label appears in H1 ───────────────────────────────────────

def test_render_contains_period_label_in_h1():
    """The H1 heading must contain the period_label string."""
    stats = _sample_stats(period_label="June 2026")
    report = render_assurance_report_markdown(stats)
    assert "# Monthly Monitoring Assurance Report — June 2026" in report


# ── Test 7: estimate warning present when is_estimate=True ───────────────────

def test_render_adds_estimate_warning_when_estimate():
    """When is_estimate=True, the report must include the partial-data warning."""
    stats = _sample_stats(is_estimate=True)
    report = render_assurance_report_markdown(stats)
    assert "may be partial" in report
    assert "fewer than 20 runs" in report


# ── Test 8: estimate warning absent when is_estimate=False ───────────────────

def test_render_omits_estimate_warning_when_not_estimate():
    """When is_estimate=False, no partial-data warning should appear."""
    stats = _sample_stats(is_estimate=False)
    report = render_assurance_report_markdown(stats)
    assert "may be partial" not in report
    assert "fewer than 20 runs" not in report


# ── Test 9: review status never fabricates a "0 pending" claim ───────────────

def test_zero_stats_review_count_is_unknown_not_zero():
    """A period with no measured backlog must not assert 0 pending review."""
    stats = _zero_stats(2026, 6, is_estimate=True)
    assert stats["unreviewed_count"] is None


def test_render_unknown_review_count_points_to_queue_not_zero():
    stats = _sample_stats(unreviewed_count=None)
    report = render_assurance_report_markdown(stats)
    assert "0 change(s) pending human review" not in report
    assert "review queue" in report.lower()


def test_render_known_review_count_is_shown():
    stats = _sample_stats(unreviewed_count=3)
    report = render_assurance_report_markdown(stats)
    assert "3 change(s) pending human review" in report


# ── Test 10: source scoping resolves slugs to URLs (not slug==url) ───────────

def test_source_scoping_resolves_slug_to_url(monkeypatch):
    """compute_monthly_stats must translate source-id slugs to their configured
    URLs before filtering the documents table, which keys on url."""
    captured = {}

    class _FakeCursor:
        def fetchall(self):
            return []

    class _FakeConn:
        row_factory = None

        def execute(self, sql, params):
            captured["sql"] = sql
            captured["params"] = list(params)
            return _FakeCursor()

        def close(self):
            pass

    monkeypatch.setattr(mar, "_urls_for_source_ids", lambda ids: ["https://reg.example/aml"])
    monkeypatch.setattr(mar.Path, "exists", lambda self: True)
    monkeypatch.setattr(mar.sqlite3, "connect", lambda *a, **k: _FakeConn())

    compute_monthly_stats(["AE-some-slug"], 2026, 6)
    # The resolved URL — not the slug — must be in the query params.
    assert "https://reg.example/aml" in captured["params"]
    assert "AE-some-slug" not in captured["params"]


def test_source_scoping_unresolvable_returns_zero_not_full_table(monkeypatch):
    """If named sources resolve to no known URL, return zero stats — never widen
    back to the whole (cross-tenant) documents table."""
    monkeypatch.setattr(mar, "_urls_for_source_ids", lambda ids: [])
    monkeypatch.setattr(mar.Path, "exists", lambda self: True)

    def _boom(*a, **k):
        raise AssertionError("DB must not be queried when scope resolves to nothing")

    monkeypatch.setattr(mar.sqlite3, "connect", _boom)
    stats = compute_monthly_stats(["AE-unknown"], 2026, 6)
    assert stats["total_runs"] == 0
    assert stats["is_estimate"] is True
