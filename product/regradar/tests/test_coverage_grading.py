"""
Regression tests for coverage grading bugs (group G6-discovery-coverage).

Bug 1 — `_coverage_level_label`'s ratio guard (restricted/total < 0.5) never
        fired because every caller omitted `total`, so any group with >= 4
        externally-restricted sources was wrongly capped at "limited" even when
        those sources were a small fraction of the inventory.

Bug 2 — the global inventory `enabled` count spanned ALL records (including
        restricted ones), so `disabled = total - enabled - restricted`
        double-subtracted any source that was BOTH restricted-status AND
        enabled=True, yielding a negative "Disabled / mapped" figure.

Local, deterministic, no network / no DB / no AI.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.coverage as cov
from app.coverage import _group_metrics


# ── Bug 1: ratio guard must not downgrade a low-proportion restricted group ────

def test_group_metrics_keeps_strong_label_when_restricted_below_half():
    """
    A group of 10 sources: 4 externally restricted (40 %), 6 good + enabled.

    Restricted count (4) is >= the absolute threshold, but restricted/total is
    0.4 (< 0.5), so the strong score label must be preserved. Before the fix
    `_group_metrics` called `_coverage_level_label(label, restricted)` with no
    `total`, the ratio guard could never run, and the label was capped at
    "limited".
    """
    records: list[dict] = []
    for _ in range(4):
        records.append(
            {"source_status": "disabled_external_access", "enabled": False,
             "extraction_quality": "unknown"}
        )
    for _ in range(6):
        records.append(
            {"source_status": "", "enabled": True, "extraction_quality": "good"}
        )

    m = _group_metrics(records)

    assert m["total"] == 10
    assert m["restricted"] == 4
    assert m["score"] >= 85, m["score"]
    # The bug capped this at "limited"; with the ratio guard active it stays strong.
    assert m["score_label"] == "strong", m["score_label"]


def test_group_metrics_still_downgrades_when_restricted_majority():
    """
    Sanity floor: when restricted sources ARE a majority (>= 50 % and >= 4),
    the downgrade to "limited" must still apply.
    """
    records: list[dict] = []
    for _ in range(5):
        records.append(
            {"source_status": "disabled_external_access", "enabled": False,
             "extraction_quality": "unknown"}
        )
    for _ in range(2):
        records.append(
            {"source_status": "", "enabled": True, "extraction_quality": "good"}
        )

    m = _group_metrics(records)

    assert m["restricted"] == 5
    assert m["total"] == 7  # 5/7 = 0.71 >= 0.5
    assert m["score_label"] == "limited", m["score_label"]


# ── Bug 2: disabled count must never go negative ───────────────────────────────

def test_disabled_sources_never_negative_with_restricted_enabled(monkeypatch):
    """
    A source that is BOTH restricted-status and enabled=True must be counted in
    exactly one inventory bucket. Before the fix it landed in both `enabled` and
    `restricted`, and `disabled = total - enabled - restricted` went negative.
    """
    fake_sources = [
        {"name": "R1", "url": "https://a.example", "jurisdiction": "AE",
         "category": "central_bank", "enabled": True,
         "status": "disabled_external_access"},
        {"name": "R2", "url": "https://b.example", "jurisdiction": "AE",
         "category": "central_bank", "enabled": True,
         "status": "disabled_navigation_only"},
        {"name": "N1", "url": "https://c.example", "jurisdiction": "AE",
         "category": "central_bank", "enabled": False, "status": ""},
    ]
    monkeypatch.setattr(cov, "load_sources", lambda: fake_sources)
    monkeypatch.setattr(cov, "_load_latest_audit_json", lambda: (None, None))

    report = cov.generate_coverage_report(use_existing_audit=False)

    assert report["total_sources"] == 3
    assert report["restricted_sources"] == 2
    # restricted sources are not counted as enabled inventory
    assert report["enabled_sources"] == 0
    assert report["disabled_sources"] == 1
    assert report["disabled_sources"] >= 0
    # buckets partition the total exactly
    assert (
        report["enabled_sources"]
        + report["disabled_sources"]
        + report["restricted_sources"]
        == report["total_sources"]
    )
