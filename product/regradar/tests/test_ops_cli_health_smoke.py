"""Smoke / interface tests for the operator ops + health cluster.

app.health.run_source_health_check, app.source_audit.run_audit and
app.coverage_plan.generate_coverage_plan are the operator diagnostics. They
sit on the same prod stack as the pipeline (scraper.fetch_page +
adapters.registry.get_adapter_for_url + extractors.extract_best_text) yet the
cluster is ~0% covered. A scraper/adapter/extractor interface refactor would
break the operator health probe at runtime while the whole suite stays green.

These tests monkeypatch the network boundary only (fetch_page +
get_adapter_for_url) and let the real extractor/verdict logic run, so an
interface break fails a test instead of shipping silently.
"""
from __future__ import annotations

import json
from datetime import date

import pytest


# ── fakes for the network boundary ──────────────────────────────────────────

class _FakeAdapter:
    name = "fake"

    def __init__(self, text: str | None):
        self._text = text

    def fetch_content(self, url: str, source: dict | None = None) -> str | None:
        return self._text


def _quality_adapter_text() -> str:
    # >= 500 chars and >= 3 double-newline paragraphs => is_quality_content True
    para = (
        "The regulator published an updated circular describing the revised "
        "reporting obligations for licensed financial institutions operating "
        "within the jurisdiction and their compliance officers. "
    )
    return "\n\n".join([para, para, para])


def _rich_html() -> str:
    para = (
        "<p>The authority has issued guidance clarifying the anti money "
        "laundering obligations applicable to designated non financial "
        "businesses and professions, including the requirement to maintain "
        "records and to report suspicious transactions to the financial "
        "intelligence unit without delay.</p>"
    )
    return "<html><body><main>" + (para * 8) + "</main></body></html>"


def _src(**kw) -> dict:
    base = {
        "name": "Test Source",
        "url": "https://example.gov.ae/reg",
        "jurisdiction": "AE",
        "category": "financial_regulator",
        "enabled": True,
        "status": "active",
    }
    base.update(kw)
    return base


# ── run_source_health_check ─────────────────────────────────────────────────

def _patch_health(monkeypatch, *, sources, adapter=None, fetch=None):
    import app.health as health

    monkeypatch.setattr(health, "load_sources", lambda: sources)
    monkeypatch.setattr(
        health, "get_adapter_for_url", lambda url, source=None: adapter
    )
    if fetch is not None:
        monkeypatch.setattr(health, "fetch_page", fetch)
    return health


def test_health_check_adapter_path_passes(monkeypatch):
    health = _patch_health(
        monkeypatch,
        sources=[_src()],
        adapter=_FakeAdapter(_quality_adapter_text()),
        fetch=lambda url, **kw: pytest.fail("adapter content should short-circuit fetch"),
    )

    results = health.run_source_health_check()

    assert len(results) == 1
    rec = results[0]
    assert rec["verdict"] == "PASS"
    assert rec["extraction_method"] == "adapter:fake"
    assert rec["extraction_quality"] == "good"
    assert rec["error"] is None
    # shape contract the CLI printer relies on
    assert set(rec) >= {
        "name", "jurisdiction", "category", "enabled", "status",
        "extracted_chars", "extraction_quality", "extraction_method",
        "verdict", "error",
    }


def test_health_check_generic_scraper_path_runs_real_extractor(monkeypatch):
    """Adapter absent => real extract_best_text runs on the fetched HTML."""
    health = _patch_health(
        monkeypatch,
        sources=[_src()],
        adapter=None,
        fetch=lambda url, **kw: _rich_html(),
    )

    results = health.run_source_health_check()

    rec = results[0]
    assert rec["error"] is None
    assert rec["extracted_chars"] > 0
    assert rec["extraction_method"] != "none"
    # real extractor produced substantial content -> not a FAIL
    assert rec["verdict"] in {"PASS", "WARN"}


def test_health_check_fetch_error_is_fail_not_raise(monkeypatch):
    def _boom(url, **kw):
        raise RuntimeError("connection reset")

    health = _patch_health(
        monkeypatch, sources=[_src()], adapter=None, fetch=_boom
    )

    results = health.run_source_health_check()

    rec = results[0]
    assert rec["verdict"] == "FAIL"
    assert rec["error"] is not None
    assert "connection reset" in rec["error"]


def test_health_check_disabled_source_is_skip(monkeypatch):
    health = _patch_health(
        monkeypatch,
        sources=[_src(enabled=False)],
        adapter=_FakeAdapter(_quality_adapter_text()),
        fetch=lambda url, **kw: _rich_html(),
    )

    results = health.run_source_health_check()

    assert results[0]["verdict"] == "SKIP"


def test_health_check_no_sources_returns_empty(monkeypatch):
    health = _patch_health(monkeypatch, sources=[])
    assert health.run_source_health_check() == []


def test_health_check_one_bad_source_never_aborts_the_rest(monkeypatch):
    calls = {"n": 0}

    def _fetch(url, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            raise TimeoutError("slow")
        return _rich_html()

    health = _patch_health(
        monkeypatch,
        sources=[_src(name="bad"), _src(name="good")],
        adapter=None,
        fetch=_fetch,
    )

    results = health.run_source_health_check()

    assert len(results) == 2
    assert results[0]["verdict"] == "FAIL"
    assert results[1]["error"] is None


# ── run_audit ───────────────────────────────────────────────────────────────

def test_run_audit_shapes_records_and_flags_failed_source(monkeypatch):
    import app.health as health
    import app.source_audit as audit

    # audit reuses health._check_one; patch the shared network boundary + its loader
    monkeypatch.setattr(health, "get_adapter_for_url", lambda url, source=None: None)
    monkeypatch.setattr(
        health, "fetch_page",
        lambda url, **kw: (_ for _ in ()).throw(RuntimeError("blocked")),
    )
    monkeypatch.setattr(
        audit, "load_sources",
        lambda: [_src(name="Blocked CB", category="central_bank")],
    )

    records = audit.run_audit(verbose=False)

    assert len(records) == 1
    r = records[0]
    assert r["verdict"] == "cannot_monitor"
    assert r["requires_adapter"] is True
    assert r["priority"] == "HIGH"          # enabled + failing + important category
    assert r["extraction_quality"] == "failed"
    assert r["suggested_next_step"]         # non-empty guidance string
    assert set(r) >= {
        "name", "url", "jurisdiction", "category", "enabled",
        "source_status", "extracted_chars", "extraction_quality",
        "best_extractor", "verdict", "requires_adapter", "priority",
        "suggested_next_step", "error",
    }


def test_run_audit_good_source_needs_no_adapter(monkeypatch):
    import app.health as health
    import app.source_audit as audit

    monkeypatch.setattr(
        health, "get_adapter_for_url",
        lambda url, source=None: _FakeAdapter(_quality_adapter_text() * 3),
    )
    monkeypatch.setattr(
        health, "fetch_page",
        lambda url, **kw: pytest.fail("adapter content should short-circuit fetch"),
    )
    monkeypatch.setattr(audit, "load_sources", lambda: [_src()])

    records = audit.run_audit(verbose=False)

    r = records[0]
    assert r["requires_adapter"] is False
    assert r["verdict"] == "can_monitor"
    assert r["priority"] == "NONE"
    assert r["error"] is None


# ── generate_coverage_plan ──────────────────────────────────────────────────

def _write_reports(reports_dir):
    reports_dir.mkdir(parents=True, exist_ok=True)
    coverage = {
        "coverage_score": 55,
        "score_label": "limited",
        "total_sources": 3,
        "enabled_sources": 1,
        "good_sources": 2,
        "failed_sources": 1,
        "by_jurisdiction": {
            "AE": {
                "score": 55, "score_label": "limited",
                "total": 3, "enabled": 1, "good": 2, "failed": 1,
                "needs_adapter": 1,
            },
        },
        "by_category": {
            "central_bank": {
                "score": 40, "score_label": "limited", "label": "Central Bank",
                "total": 2, "enabled": 1, "good": 1, "failed": 1,
                "needs_adapter": 1,
            },
        },
    }
    audit = {
        "sources": [
            {
                "name": "Good disabled CB", "url": "https://cb.example.ae",
                "jurisdiction": "AE", "category": "central_bank",
                "enabled": False, "extraction_quality": "good",
                "extracted_chars": 4200, "best_extractor": "readability",
                "requires_adapter": False, "suggested_next_step": "",
                "error": None,
            },
            {
                "name": "Failed AML", "url": "https://aml.example.ae",
                "jurisdiction": "AE", "category": "aml",
                "enabled": True, "extraction_quality": "failed",
                "extracted_chars": 0, "best_extractor": "none",
                "requires_adapter": True,
                "suggested_next_step": "Build adapter.",
                "error": "TimeoutError: slow",
            },
        ],
    }
    (reports_dir / "coverage_2026-07-21.json").write_text(
        json.dumps(coverage), encoding="utf-8"
    )
    (reports_dir / f"source_audit_{date.today().isoformat()}.json").write_text(
        json.dumps(audit), encoding="utf-8"
    )


def test_generate_coverage_plan_builds_expected_shape(tmp_path, monkeypatch):
    import app.coverage_plan as cp

    reports = tmp_path / "reports"
    _write_reports(reports)
    monkeypatch.setattr(cp, "_REPORTS_DIR", reports)

    plan = cp.generate_coverage_plan()

    assert plan["overall_score"] == 55
    assert plan["overall_label"] == "limited"
    assert plan["target_score"] == 70          # min(55 + 15, 85)
    assert isinstance(plan["priority_jurisdictions"], list)
    assert isinstance(plan["quick_wins"], list)
    # the good disabled central-bank source is a quick win
    assert any(w["name"] == "Good disabled CB" for w in plan["quick_wins"])
    # the failed enabled AML source is a URL/adapter fix task
    assert any(t["name"] == "Failed AML" for t in plan["source_fix_tasks"])
    # roadmap has the three horizons
    roadmap = plan["roadmap"]
    assert set(roadmap) == {"next_7_days", "next_30_days", "next_90_days"}
    assert all(roadmap[k] for k in roadmap)     # each horizon has items
    assert "not a guarantee" in plan["disclaimer"]


def test_generate_coverage_plan_missing_reports_dir_raises(tmp_path, monkeypatch):
    import app.coverage_plan as cp

    monkeypatch.setattr(cp, "_REPORTS_DIR", tmp_path / "nope")

    with pytest.raises(ValueError, match="reports/ directory not found"):
        cp.generate_coverage_plan()


def test_generate_coverage_plan_missing_coverage_json_raises(tmp_path, monkeypatch):
    import app.coverage_plan as cp

    reports = tmp_path / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    # only an audit file, no coverage_*.json
    (reports / f"source_audit_{date.today().isoformat()}.json").write_text(
        json.dumps({"sources": []}), encoding="utf-8"
    )
    monkeypatch.setattr(cp, "_REPORTS_DIR", reports)

    with pytest.raises(ValueError, match="No coverage JSON"):
        cp.generate_coverage_plan()
