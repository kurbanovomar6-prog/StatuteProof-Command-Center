"""Behavioral coverage uplift for app/coverage.py — the coverage-matrix
computation that feeds customer-facing source counts and the score/label grading
shown in the dashboard and HTML/JSON exports.

Focus areas (all in-process, no network / no DB / no AI):
  * scoring primitives (_source_pts, _source_scores, _max_pts, _score)
  * score / coverage-level label grading (all four bands + the restricted
    downgrade guard, including the "weak stays weak" branch)
  * the enabled / disabled / restricted bucket partition (no double-count)
  * audit-JSON merge precedence (audit record wins over metadata by url)
  * _load_latest_audit_json: missing dir, no candidates, valid, corrupt
  * generate_coverage_report end-to-end shape with an audit merge
  * print_coverage_report (metadata-only warning, filters, hit/miss)
  * export_coverage_json / build_coverage_html / export_coverage_html

Mirrors the fixture style of tests/test_coverage_grading.py (monkeypatch
load_sources / _load_latest_audit_json, small in-memory record lists).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.coverage as cov
from app.coverage import (
    _coverage_level_label,
    _group_metrics,
    _max_pts,
    _score,
    _score_label,
    _source_pts,
    _source_scores,
    build_coverage_html,
    export_coverage_html,
    export_coverage_json,
    generate_coverage_report,
    print_coverage_report,
)


# ── scoring primitives ─────────────────────────────────────────────────────────

def test_source_pts_matches_quality_enabled_matrix():
    """_source_pts returns the documented point value per (quality, enabled)."""
    assert _source_pts({"extraction_quality": "good", "enabled": True}) == 4.0
    assert _source_pts({"extraction_quality": "good", "enabled": False}) == 2.0
    assert _source_pts({"extraction_quality": "low_content", "enabled": True}) == 1.0
    assert _source_pts({"extraction_quality": "low_content", "enabled": False}) == 0.0
    assert _source_pts({"extraction_quality": "failed", "enabled": True}) == -1.0
    assert _source_pts({"extraction_quality": "failed", "enabled": False}) == 0.0
    assert _source_pts({"extraction_quality": "unknown", "enabled": True}) == 2.0
    assert _source_pts({"extraction_quality": "unknown", "enabled": False}) == 1.0


def test_source_pts_defaults_to_unknown_disabled_when_fields_absent():
    """A bare record defaults to (unknown, disabled) → 1.0 point."""
    assert _source_pts({}) == 1.0


def test_source_pts_restricted_status_scores_zero():
    """A restricted source contributes zero points even if quality is good+enabled."""
    rec = {
        "extraction_quality": "good",
        "enabled": True,
        "source_status": "disabled_external_access",
    }
    assert _source_pts(rec) == 0.0


def test_source_scores_excludes_restricted_statuses():
    """Restricted statuses are dropped from the score denominator; others count."""
    assert _source_scores({"source_status": ""}) is True
    assert _source_scores({"source_status": "disabled_external_access"}) is False
    assert _source_scores({"source_status": "disabled_navigation_only"}) is False


def test_max_pts_uses_4_per_enabled_2_per_disabled():
    assert _max_pts(3, 2) == 4 * 3 + 2 * 2  # 16.0
    assert _max_pts(0, 0) == 0.0


def test_score_clamps_and_handles_zero_denominator():
    """_score is percentage-of-max, clamped to [0, 100], 0 when max <= 0."""
    assert _score(0.0, 0.0) == 0          # zero denominator guard
    assert _score(8.0, 8.0) == 100        # perfect
    assert _score(4.0, 8.0) == 50         # half
    assert _score(-5.0, 8.0) == 0         # negative pts clamped up to 0
    assert _score(20.0, 8.0) == 100       # over-max clamped down to 100


def test_score_label_bands():
    """All four grade bands are exercised at their boundaries."""
    assert _score_label(85) == "strong"
    assert _score_label(84) == "usable"
    assert _score_label(65) == "usable"
    assert _score_label(64) == "limited"
    assert _score_label(40) == "limited"
    assert _score_label(39) == "weak"
    assert _score_label(0) == "weak"


# ── coverage-level downgrade guard ─────────────────────────────────────────────

def test_coverage_level_label_no_downgrade_below_absolute_threshold():
    """Fewer than 4 restricted sources never triggers a downgrade."""
    assert _coverage_level_label("strong", restricted_count=3, total=4) == "strong"


def test_coverage_level_label_no_downgrade_when_ratio_below_half():
    """>=4 restricted but <50% of total keeps the original label."""
    assert _coverage_level_label("strong", restricted_count=4, total=10) == "strong"


def test_coverage_level_label_downgrades_strong_to_limited_on_majority():
    """>=4 restricted AND >=50% of total downgrades strong/usable to limited."""
    assert _coverage_level_label("strong", restricted_count=5, total=7) == "limited"
    assert _coverage_level_label("usable", restricted_count=6, total=8) == "limited"


def test_coverage_level_label_weak_stays_weak_even_when_restricted_majority():
    """A weak/limited label is not 'upgraded' by the downgrade guard."""
    # restricted majority, but label is already weak → returned unchanged.
    assert _coverage_level_label("weak", restricted_count=5, total=7) == "weak"
    assert _coverage_level_label("limited", restricted_count=5, total=7) == "limited"


# ── bucket partition (mode bucketing) ──────────────────────────────────────────

def test_group_metrics_buckets_partition_total_no_double_count():
    """enabled + disabled + restricted must equal total exactly."""
    records = [
        {"source_status": "", "enabled": True, "extraction_quality": "good"},
        {"source_status": "", "enabled": True, "extraction_quality": "low_content"},
        {"source_status": "", "enabled": False, "extraction_quality": "good"},
        {"source_status": "disabled_external_access", "enabled": False,
         "extraction_quality": "unknown"},
        {"source_status": "disabled_navigation_only", "enabled": True,
         "extraction_quality": "good"},
    ]
    m = _group_metrics(records)
    assert m["total"] == 5
    assert m["restricted"] == 2
    assert m["enabled"] == 2      # the enabled+restricted one is NOT counted enabled
    assert m["disabled"] == 1
    assert m["enabled"] + m["disabled"] + m["restricted"] == m["total"]


def test_group_metrics_quality_tallies_and_failed_excludes_restricted():
    """good/low/failed/unknown tallies; a restricted 'failed' is not counted failed."""
    records = [
        {"source_status": "", "enabled": True, "extraction_quality": "good"},
        {"source_status": "", "enabled": True, "extraction_quality": "low_content"},
        {"source_status": "", "enabled": True, "extraction_quality": "failed"},
        {"source_status": "disabled_external_access", "enabled": False,
         "extraction_quality": "failed"},   # restricted → not a "failed" tally
        {"source_status": "", "enabled": False, "extraction_quality": "unknown"},
        {"source_status": "", "enabled": True, "extraction_quality": "good",
         "requires_adapter": True},
    ]
    m = _group_metrics(records)
    assert m["good"] == 2
    assert m["low_content"] == 1
    assert m["failed"] == 1          # restricted-failed excluded
    assert m["unknown"] == 1
    assert m["needs_adapter"] == 1


def test_group_metrics_empty_records_scores_zero():
    """No records → zero score, weak label, no divide-by-zero."""
    m = _group_metrics([])
    assert m["total"] == 0
    assert m["score"] == 0
    assert m["score_label"] == "weak"


# ── audit merge + end-to-end report ────────────────────────────────────────────

_SOURCES = [
    {"name": "CBUAE", "url": "https://cbuae.example/a", "jurisdiction": "AE",
     "category": "central_bank", "enabled": True, "status": ""},
    {"name": "VARA", "url": "https://vara.example/b", "jurisdiction": "AE",
     "category": "financial_regulator", "enabled": True, "status": ""},
    {"name": "SAMA", "url": "https://sama.example/c", "jurisdiction": "SA",
     "category": "central_bank", "enabled": False, "status": ""},
]


def _audit(sources: list[dict]) -> dict:
    return {"generated": "2026-07-20", "sources": sources}


def test_generate_report_audit_record_wins_over_metadata(monkeypatch):
    """When an audit record matches a source url, its quality merges in; unmatched
    sources fall back to 'unknown' metadata-only records."""
    audit = _audit([
        {"url": "https://cbuae.example/a", "jurisdiction": "AE",
         "category": "central_bank", "enabled": True,
         "extraction_quality": "good", "best_extractor": "adapter:cbuae",
         "requires_adapter": True, "source_status": ""},
    ])
    monkeypatch.setattr(cov, "load_sources", lambda: list(_SOURCES))
    monkeypatch.setattr(cov, "_load_latest_audit_json",
                        lambda: (audit, Path("source_audit_2026-07-20.json")))

    report = generate_coverage_report(use_existing_audit=True)

    assert report["audit_source"] == "source_audit_2026-07-20.json"
    assert report["audit_date"] == "2026-07-20"
    assert report["total_sources"] == 3
    # the one merged audit record is good + built by an adapter
    assert report["good_sources"] == 1
    assert report["adapter_resolved"] == 1
    # the two unmatched sources fall back to unknown quality
    assert report["unknown_quality"] == 2
    # AE jurisdiction bucket exists with both AE sources
    assert report["by_jurisdiction"]["AE"]["total"] == 2
    assert report["by_jurisdiction"]["AE"]["name"] == "UAE"
    assert report["by_jurisdiction"]["AE"]["region"] == "Middle East & Türkiye"


def test_generate_report_metadata_only_when_no_audit(monkeypatch):
    """No audit JSON → audit_source 'metadata_only' and all quality unknown."""
    monkeypatch.setattr(cov, "load_sources", lambda: list(_SOURCES))
    monkeypatch.setattr(cov, "_load_latest_audit_json", lambda: (None, None))

    report = generate_coverage_report(use_existing_audit=True)

    assert report["audit_source"] == "metadata_only"
    assert report["unknown_quality"] == 3
    assert report["good_sources"] == 0
    # enabled=2 (CBUAE, VARA), disabled=1 (SAMA), no restricted
    assert report["enabled_sources"] == 2
    assert report["disabled_sources"] == 1
    assert report["restricted_sources"] == 0
    assert (report["enabled_sources"] + report["disabled_sources"]
            + report["restricted_sources"] == report["total_sources"])
    # category + region groupings are present
    assert "central_bank" in report["by_category"]
    assert "Middle East & Türkiye" in report["by_region"]


def test_generate_report_use_existing_false_skips_audit_load(monkeypatch):
    """use_existing_audit=False must not consult the audit loader at all."""
    monkeypatch.setattr(cov, "load_sources", lambda: list(_SOURCES))

    def _boom():
        raise AssertionError("audit loader must not be called when use_existing=False")

    monkeypatch.setattr(cov, "_load_latest_audit_json", _boom)

    report = generate_coverage_report(use_existing_audit=False)
    assert report["audit_source"] == "metadata_only"


# ── _load_latest_audit_json ────────────────────────────────────────────────────

def test_load_latest_audit_missing_dir(monkeypatch, tmp_path):
    """Non-existent reports dir → (None, None)."""
    monkeypatch.setattr(cov, "_REPORTS_DIR", tmp_path / "does_not_exist")
    assert cov._load_latest_audit_json() == (None, None)


def test_load_latest_audit_no_candidates(monkeypatch, tmp_path):
    """Existing dir with no source_audit_*.json → (None, None)."""
    monkeypatch.setattr(cov, "_REPORTS_DIR", tmp_path)
    (tmp_path / "unrelated.txt").write_text("x", encoding="utf-8")
    assert cov._load_latest_audit_json() == (None, None)


def test_load_latest_audit_picks_most_recent_valid(monkeypatch, tmp_path):
    """Most recently modified valid audit file is parsed and returned."""
    monkeypatch.setattr(cov, "_REPORTS_DIR", tmp_path)
    old = tmp_path / "source_audit_2026-01-01.json"
    new = tmp_path / "source_audit_2026-07-20.json"
    old.write_text(json.dumps({"sources": [], "tag": "old"}), encoding="utf-8")
    new.write_text(json.dumps({"sources": [], "tag": "new"}), encoding="utf-8")
    # ensure `new` has the later mtime regardless of write order
    import os
    os.utime(new, (10**10, 10**10))
    os.utime(old, (10**9, 10**9))

    data, path = cov._load_latest_audit_json()
    assert data is not None and path is not None
    assert data["tag"] == "new"
    assert path.name == "source_audit_2026-07-20.json"


def test_load_latest_audit_corrupt_json_returns_none(monkeypatch, tmp_path):
    """A corrupt audit file is caught and yields (None, None) rather than raising."""
    monkeypatch.setattr(cov, "_REPORTS_DIR", tmp_path)
    (tmp_path / "source_audit_bad.json").write_text("{not valid json", encoding="utf-8")
    assert cov._load_latest_audit_json() == (None, None)


# ── print_coverage_report ──────────────────────────────────────────────────────

def _report(monkeypatch, sources, audit=None):
    monkeypatch.setattr(cov, "load_sources", lambda: list(sources))
    loader = (lambda: (audit, Path("source_audit_x.json"))) if audit else (lambda: (None, None))
    monkeypatch.setattr(cov, "_load_latest_audit_json", loader)
    return generate_coverage_report(use_existing_audit=bool(audit))


def test_print_report_metadata_warning(monkeypatch, capsys):
    """Metadata-only report prints the 'No source audit JSON found' warning."""
    report = _report(monkeypatch, _SOURCES)
    print_coverage_report(report)
    out = capsys.readouterr().out
    assert "No source audit JSON found" in out
    assert "Overall Coverage Score" in out
    assert "By Jurisdiction" in out
    assert "By Category" in out


def test_print_report_with_audit_and_restricted(monkeypatch, capsys):
    """A report built from an audit prints the audit source line and, when
    present, the externally-restricted summary row."""
    sources = [
        {"name": "R", "url": "https://r.example", "jurisdiction": "AE",
         "category": "central_bank", "enabled": True,
         "status": "disabled_external_access"},
        {"name": "G", "url": "https://g.example", "jurisdiction": "AE",
         "category": "central_bank", "enabled": True, "status": ""},
    ]
    audit = _audit([
        {"url": "https://r.example", "jurisdiction": "AE", "category": "central_bank",
         "enabled": True, "extraction_quality": "unknown",
         "source_status": "disabled_external_access"},
        {"url": "https://g.example", "jurisdiction": "AE", "category": "central_bank",
         "enabled": True, "extraction_quality": "good"},
    ])
    report = _report(monkeypatch, sources, audit)
    assert report["restricted_sources"] == 1
    print_coverage_report(report)
    out = capsys.readouterr().out
    assert "Audit source: source_audit_x.json" in out
    assert "Externally restricted" in out


def test_print_report_jurisdiction_filter_hit_and_miss(monkeypatch, capsys):
    """Jurisdiction filter narrows output; an unknown code prints a not-found line."""
    report = _report(monkeypatch, _SOURCES)

    print_coverage_report(report, jurisdiction="ae")
    out_hit = capsys.readouterr().out
    assert "AE" in out_hit

    print_coverage_report(report, jurisdiction="zz")
    out_miss = capsys.readouterr().out
    assert "No jurisdiction 'ZZ' found" in out_miss


def test_print_report_category_filter_miss(monkeypatch, capsys):
    """Unknown category prints a not-found line."""
    report = _report(monkeypatch, _SOURCES)
    print_coverage_report(report, category="does_not_exist")
    out = capsys.readouterr().out
    assert "No category 'does_not_exist' found" in out


# ── JSON / HTML exporters ──────────────────────────────────────────────────────

def test_export_coverage_json_writes_file(monkeypatch, tmp_path):
    """export_coverage_json writes a coverage_<date>.json that round-trips."""
    report = _report(monkeypatch, _SOURCES)
    path = export_coverage_json(report, reports_dir=tmp_path)
    assert path.exists()
    assert path.parent == tmp_path
    assert path.name.startswith("coverage_") and path.name.endswith(".json")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["total_sources"] == report["total_sources"]
    assert loaded["coverage_score"] == report["coverage_score"]
    # internal _source key must never be serialised
    assert "_source" not in loaded


def test_build_coverage_html_contains_scores_and_tables(monkeypatch):
    """build_coverage_html renders the score, jurisdiction rows and category rows."""
    report = _report(monkeypatch, _SOURCES)
    html = build_coverage_html(report)
    assert html.startswith("<!DOCTYPE html>")
    assert "StatuteProof — Coverage Report" in html
    assert str(report["coverage_score"]) in html
    # jurisdiction + category names surface in the tables
    assert "UAE" in html
    assert "Central Bank" in html
    # metadata-only banner is shown when no audit backed the report
    assert "No source audit found" in html


def test_build_coverage_html_shows_restricted_and_audit_label(monkeypatch):
    """When an audit backs the report, the audit label (not the warning) shows."""
    audit = _audit([
        {"url": "https://cbuae.example/a", "jurisdiction": "AE",
         "category": "central_bank", "enabled": True,
         "extraction_quality": "good", "source_status": ""},
    ])
    report = _report(monkeypatch, _SOURCES, audit)
    html = build_coverage_html(report)
    assert "Source audit: source_audit_x.json" in html
    assert "No source audit found" not in html


def test_export_coverage_html_writes_file(monkeypatch, tmp_path):
    """export_coverage_html writes coverage_<date>.html with the rendered body."""
    report = _report(monkeypatch, _SOURCES)
    path = export_coverage_html(report, reports_dir=tmp_path)
    assert path.exists()
    assert path.name.startswith("coverage_") and path.name.endswith(".html")
    body = path.read_text(encoding="utf-8")
    assert "StatuteProof — Coverage Report" in body


# ── insight generators (strengths / gaps / recommendations) ────────────────────

def test_report_surfaces_strengths_for_strong_jurisdiction(monkeypatch):
    """A jurisdiction with multiple good enabled sources yields a strength line."""
    sources = [
        {"name": "A", "url": "https://a.example", "jurisdiction": "AE",
         "category": "central_bank", "enabled": True, "status": ""},
        {"name": "B", "url": "https://b.example", "jurisdiction": "AE",
         "category": "central_bank", "enabled": True, "status": ""},
    ]
    audit = _audit([
        {"url": "https://a.example", "jurisdiction": "AE", "category": "central_bank",
         "enabled": True, "extraction_quality": "good"},
        {"url": "https://b.example", "jurisdiction": "AE", "category": "central_bank",
         "enabled": True, "extraction_quality": "good"},
    ])
    report = _report(monkeypatch, sources, audit)
    joined = " ".join(report["top_strengths"])
    assert "UAE" in joined
    assert isinstance(report["top_strengths"], list)
    assert len(report["top_strengths"]) >= 1


def test_report_surfaces_gaps_for_unmonitored_jurisdiction(monkeypatch):
    """A jurisdiction mapped but with nothing enabled produces a gap line and a
    recommendation to activate vetted sources."""
    sources = [
        {"name": "X", "url": "https://x.example", "jurisdiction": "SA",
         "category": "central_bank", "enabled": False, "status": ""},
        {"name": "Y", "url": "https://y.example", "jurisdiction": "SA",
         "category": "central_bank", "enabled": False, "status": ""},
    ]
    report = _report(monkeypatch, sources)
    gaps = " ".join(report["top_gaps"])
    recs = " ".join(report["recommendations"])
    assert "Saudi Arabia" in gaps
    assert "none actively monitored" in gaps
    # recommendation engine suggests activating vetted sources
    assert "activating vetted sources" in recs
    # the always-appended source-audit recommendation is present
    assert any("source-audit" in r for r in report["recommendations"])


def test_report_surfaces_failed_and_adapter_insights(monkeypatch):
    """A weak jurisdiction with >=2 failed sources and adapter needs triggers the
    failed-sources gap, the fix/validate recommendation, the low-score gap, and
    the custom-adapter recommendation/category gap."""
    sources = [
        {"name": f"F{i}", "url": f"https://f{i}.example", "jurisdiction": "SA",
         "category": "central_bank", "enabled": True, "status": ""}
        for i in range(5)
    ]
    audit = _audit([
        {"url": f"https://f{i}.example", "jurisdiction": "SA",
         "category": "central_bank", "enabled": True,
         "extraction_quality": "failed", "requires_adapter": True}
        for i in range(5)
    ])
    report = _report(monkeypatch, sources, audit)

    assert report["failed_sources"] == 5
    assert report["needs_adapter"] == 5
    # score should be low (all enabled sources failed → negative pts clamped to 0)
    assert report["coverage_score"] < 40
    assert report["by_jurisdiction"]["SA"]["score_label"] == "weak"

    gaps = " ".join(report["top_gaps"])
    recs = " ".join(report["recommendations"])
    assert "failed" in gaps                     # failed>=2 gap (line 295)
    assert "significant coverage gap" in gaps    # score<40 & total>=3 gap (line 304)
    assert "custom adapters" in gaps             # category needs_adapter>=3 gap (line 311)
    assert "most likely DNS or SSL" in recs      # weak_j recommendation (lines 330-331)
    assert "need custom adapters" in recs        # needs_adapter>=5 recommendation (line 343)


def test_report_recommends_validating_good_disabled_sources(monkeypatch):
    """A jurisdiction with good-quality DISABLED sources (good > enabled) and a
    decent score triggers the 'validate before enabling' recommendation."""
    sources = [
        {"name": "D1", "url": "https://d1.example", "jurisdiction": "AE",
         "category": "central_bank", "enabled": True, "status": ""},
        {"name": "D2", "url": "https://d2.example", "jurisdiction": "AE",
         "category": "central_bank", "enabled": False, "status": ""},
    ]
    audit = _audit([
        {"url": "https://d1.example", "jurisdiction": "AE", "category": "central_bank",
         "enabled": True, "extraction_quality": "good"},
        {"url": "https://d2.example", "jurisdiction": "AE", "category": "central_bank",
         "enabled": False, "extraction_quality": "good"},  # good but disabled
    ])
    report = _report(monkeypatch, sources, audit)
    assert report["by_jurisdiction"]["AE"]["good"] > report["by_jurisdiction"]["AE"]["enabled"]
    recs = " ".join(report["recommendations"])
    assert "validate before enabling" in recs    # high_q_disabled recommendation (line 353)
