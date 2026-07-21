"""Behavioral coverage for ``app.source_readiness``.

This module exercises the source-readiness gating logic that decides whether a
market is fresh-alert / pilot eligible, plus the pure helpers, source/audit
loaders, run-record overlay, and the terminal + HTML renderers.

All I/O is either fed via monkeypatched module paths (``_SOURCES_JSON`` /
``_REPORTS_DIR``) or via mocked ``app.source_runs`` / ``app.source_tester``
callables — no network, subprocess, or real report/data files are touched.
Every test asserts real return values / status transitions / gating decisions.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.source_readiness as sr


# ── customer_quality — boundary conditions ───────────────────────────────────

@pytest.mark.parametrize(
    "chars,expected",
    [
        (2_000, "GOOD"),        # exactly the GOOD threshold
        (2_001, "GOOD"),
        (1_999, "MEDIUM"),      # one below GOOD
        (800, "MEDIUM"),        # exactly the MEDIUM threshold
        (799, "THIN"),          # one below MEDIUM
        (1, "THIN"),            # any positive content is THIN not FAILED
        (0, "FAILED"),          # no content
        (-5, "FAILED"),         # defensive: negative treated as failed
    ],
)
def test_customer_quality_boundaries(chars, expected):
    assert sr.customer_quality(chars) == expected


def test_customer_quality_label_known_and_unknown():
    assert sr.customer_quality_label("GOOD") == "✅ Good"
    assert sr.customer_quality_label("FAILED") == "❌ Failed"
    # Unknown quality strings pass through unchanged.
    assert sr.customer_quality_label("WEIRD") == "WEIRD"


# ── load_market_sources ──────────────────────────────────────────────────────

def test_load_market_sources_filters_by_jurisdiction_case_insensitive(monkeypatch, tmp_path):
    src_file = tmp_path / "sources.json"
    src_file.write_text(json.dumps([
        {"name": "CBUAE", "jurisdiction": "AE"},
        {"name": "SAMA", "jurisdiction": "sa"},          # lower-case in file
        {"name": "DFSA", "jurisdiction": "AE"},
        {"name": "NoJur"},                               # missing jurisdiction
    ]), encoding="utf-8")
    monkeypatch.setattr(sr, "_SOURCES_JSON", src_file)

    ae = sr.load_market_sources("ae")                    # lower-case query
    assert {s["name"] for s in ae} == {"CBUAE", "DFSA"}
    assert sr.load_market_sources("SA") == [{"name": "SAMA", "jurisdiction": "sa"}]


def test_load_market_sources_missing_file_returns_empty(monkeypatch, tmp_path):
    monkeypatch.setattr(sr, "_SOURCES_JSON", tmp_path / "does_not_exist.json")
    assert sr.load_market_sources("AE") == []


# ── load_latest_audit ────────────────────────────────────────────────────────

def test_load_latest_audit_no_reports_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(sr, "_REPORTS_DIR", tmp_path / "missing")
    assert sr.load_latest_audit("AE") == {}


def test_load_latest_audit_no_audit_files(monkeypatch, tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    monkeypatch.setattr(sr, "_REPORTS_DIR", reports)
    assert sr.load_latest_audit("AE") == {}


def test_load_latest_audit_picks_newest_and_filters_jurisdiction(monkeypatch, tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    # Older file (should be ignored — glob sorted reverse picks the later name).
    (reports / "source_audit_2026-01-01.json").write_text(
        json.dumps({"sources": [{"name": "OLD", "jurisdiction": "AE",
                                  "extracted_chars": 10}]}), encoding="utf-8")
    (reports / "source_audit_2026-02-01.json").write_text(
        json.dumps({"sources": [
            {"name": "CBUAE", "jurisdiction": "AE", "extracted_chars": 3000},
            {"name": "SAMA", "jurisdiction": "SA", "extracted_chars": 500},
        ]}), encoding="utf-8")
    monkeypatch.setattr(sr, "_REPORTS_DIR", reports)

    audit = sr.load_latest_audit("ae")
    assert set(audit) == {"CBUAE"}                       # newest file, AE only
    assert audit["CBUAE"]["extracted_chars"] == 3000
    assert "OLD" not in audit                            # older file ignored


def test_load_latest_audit_bad_json_returns_empty(monkeypatch, tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "source_audit_2026-02-01.json").write_text("{ not valid json",
                                                          encoding="utf-8")
    monkeypatch.setattr(sr, "_REPORTS_DIR", reports)
    assert sr.load_latest_audit("AE") == {}


# ── build_readiness_report — shared harness ──────────────────────────────────

def _patch_report_deps(monkeypatch, sources, audit=None, history=None):
    """Point build_readiness_report at synthetic data with no live I/O.

    ``build_readiness_report`` imports from ``app.source_runs`` /
    ``app.source_tester`` at call time, so patching those module attributes is
    sufficient. ``latest_runs`` returns the (source_id -> record) history map.
    """
    import app.source_runs as runs

    monkeypatch.setattr(sr, "load_market_sources", lambda jur: list(sources))
    monkeypatch.setattr(sr, "load_latest_audit", lambda jur: dict(audit or {}))
    monkeypatch.setattr(runs, "latest_runs", lambda jur, *a, **k: dict(history or {}))


def _src(name, category, source_id, status="active", jurisdiction="AE", url="https://x.example"):
    return {"name": name, "category": category, "source_id": source_id,
            "status": status, "jurisdiction": jurisdiction, "url": url}


# ── build_readiness_report — verdict gating (no record_run) ───────────────────

def test_report_free_check_ready_with_two_good_p0(monkeypatch):
    """>=2 P0 sources GOOD/MEDIUM => FREE_CHECK_READY."""
    sources = [
        _src("CBUAE", "central_bank", "ae-cbuae"),
        _src("UAEFIU", "aml", "ae-fiu"),
    ]
    audit = {
        "CBUAE": {"extracted_chars": 3000},
        "UAEFIU": {"extracted_chars": 2500},
    }
    _patch_report_deps(monkeypatch, sources, audit)

    report = sr.build_readiness_report("AE")

    assert report["pilot_verdict"] == "FREE_CHECK_READY"
    assert report["sources_active"] == 2
    assert report["sources_blocked"] == 0
    assert len(report["p0_sources"]) == 2
    assert all(s["quality"] == "GOOD" for s in report["p0_sources"])
    assert report["run_id"] is None                      # record_run defaulted False


def test_report_pilot_ready_when_four_good_but_fewer_than_two_p0(monkeypatch):
    """1 P0 GOOD + 3 P1 GOOD => 4 GOOD/MEDIUM pilot sources but only 1 P0 => PILOT_READY."""
    sources = [
        _src("CBUAE", "central_bank", "ae-cbuae"),
        _src("MoF", "finance_ministry", "ae-mof"),
        _src("Acts", "legal_acts", "ae-acts"),
        _src("LegalDB", "legal_database", "ae-legaldb"),
    ]
    audit = {n: {"extracted_chars": 3000} for n in ("CBUAE", "MoF", "Acts", "LegalDB")}
    _patch_report_deps(monkeypatch, sources, audit)

    report = sr.build_readiness_report("AE")

    assert report["pilot_ready"] is True
    assert report["pilot_verdict"] == "PILOT_READY"
    assert len(report["p1_sources"]) == 3
    assert "PILOT_READY" not in report["pilot_note"]      # note is prose, not verdict token
    assert "pilot" in report["pilot_note"].lower()


def test_report_needs_more_work_when_too_few_good(monkeypatch):
    """1 GOOD P0 + THIN P1 => not enough for pilot => NEEDS_MORE_WORK."""
    sources = [
        _src("CBUAE", "central_bank", "ae-cbuae"),
        _src("MoF", "finance_ministry", "ae-mof"),
    ]
    audit = {
        "CBUAE": {"extracted_chars": 3000},              # GOOD (1 P0)
        "MoF": {"extracted_chars": 100},                 # THIN
    }
    _patch_report_deps(monkeypatch, sources, audit)

    report = sr.build_readiness_report("AE")

    assert report["pilot_ready"] is False
    assert report["pilot_verdict"] == "NEEDS_MORE_WORK"
    # THIN source gets a low-content limitation.
    mof = next(s for s in report["p1_sources"] if s["name"] == "MoF")
    assert mof["quality"] == "THIN"
    assert any("Low content" in lim for lim in mof["limitations"])


def test_report_failed_source_gets_extraction_limitation_and_error(monkeypatch):
    sources = [_src("DeadSrc", "central_bank", "ae-dead")]
    audit = {"DeadSrc": {"extracted_chars": 0, "error": "HTTP 503 upstream"}}
    _patch_report_deps(monkeypatch, sources, audit)

    report = sr.build_readiness_report("AE")

    entry = report["p0_sources"][0]
    assert entry["quality"] == "FAILED"
    assert any("Extraction failed" in lim for lim in entry["limitations"])
    assert entry["error"] == "HTTP 503 upstream"
    assert any("Last error" in lim for lim in entry["limitations"])


def test_report_categorizes_uncategorized_source_as_p2(monkeypatch):
    sources = [_src("Registry", "company_registry", "ae-reg"),
               _src("Misc", "other", "ae-misc")]
    audit = {"Registry": {"extracted_chars": 3000},
             "Misc": {"extracted_chars": 3000}}
    _patch_report_deps(monkeypatch, sources, audit)

    report = sr.build_readiness_report("AE")

    p2_ids = {s["source_id"] for s in report["p2_sources"]}
    assert p2_ids == {"ae-reg", "ae-misc"}               # neither P0 nor P1
    assert report["p0_sources"] == []
    assert report["p1_sources"] == []


# ── build_readiness_report — blocked / restricted handling ───────────────────

def test_report_external_access_source_is_blocked_and_restricted(monkeypatch):
    sources = [_src("DIFC", "financial_regulator", "ae-difc",
                    status="disabled_external_access")]
    _patch_report_deps(monkeypatch, sources)

    report = sr.build_readiness_report("AE")

    assert report["sources_active"] == 0
    assert report["sources_blocked"] == 1
    assert report["sources_restricted"] == 1
    assert len(report["blocked_sources"]) == 1
    blocked = report["blocked_sources"][0]
    assert any("Geo-blocked" in lim for lim in blocked["limitations"])
    assert report["limitations"]                          # top-level limitation recorded
    assert "DIFC" in report["limitations"][0]


def test_report_navigation_only_source_blocked_not_restricted(monkeypatch):
    sources = [_src("SPA", "financial_regulator", "ae-spa",
                    status="disabled_navigation_only")]
    _patch_report_deps(monkeypatch, sources)

    report = sr.build_readiness_report("AE")

    assert report["sources_blocked"] == 1
    assert report["sources_restricted"] == 0             # navigation-only != restricted
    assert any("Navigation-only" in lim
               for lim in report["blocked_sources"][0]["limitations"])


def test_report_blocked_source_uses_history_when_present(monkeypatch):
    """A restricted source with prior history overlays that run's evidence."""
    sources = [_src("SPA", "financial_regulator", "ae-spa",
                    status="disabled_navigation_only")]
    history = {"ae-spa": {
        "timestamp_utc": "2026-07-20T00:00:00Z",
        "change_status": "unchanged",
        "extracted_chars": 1500,
        "extraction_quality": "MEDIUM",
        "pdf_links_count": 2,
        "pdf_extracted_chars": 900,
    }}
    _patch_report_deps(monkeypatch, sources, history=history)

    report = sr.build_readiness_report("AE")

    blocked = report["blocked_sources"][0]
    assert blocked["last_run"] == "2026-07-20T00:00:00Z"
    assert blocked["chars"] == 1500
    assert blocked["change_status"] == "unchanged"
    assert blocked["pdf_extracted_chars"] == 900


# ── build_readiness_report — active source overlays history ──────────────────

def test_report_active_source_overlays_history_quality(monkeypatch):
    """With no live run, a stored run record supplies chars/quality via overlay."""
    sources = [_src("CBUAE", "central_bank", "ae-cbuae")]
    audit = {"CBUAE": {"extracted_chars": 100}}          # audit alone would be THIN
    history = {"ae-cbuae": {
        "timestamp_utc": "2026-07-20T01:00:00Z",
        "change_status": "changed",
        "extracted_chars": 5000,
        "extraction_quality": "GOOD",
    }}
    _patch_report_deps(monkeypatch, sources, audit, history)

    report = sr.build_readiness_report("AE")

    entry = report["p0_sources"][0]
    assert entry["chars"] == 5000                        # history wins over audit
    assert entry["quality"] == "GOOD"
    assert entry["change_status"] == "changed"


# ── build_readiness_report — record_run=True (mocked tester) ─────────────────

def test_report_record_run_calls_tester_and_records(monkeypatch):
    """record_run=True runs the (mocked) tester and appends a run record."""
    import app.source_runs as runs
    import app.source_tester as tester

    sources = [_src("CBUAE", "central_bank", "ae-cbuae")]
    _patch_report_deps(monkeypatch, sources)

    calls = {"tested": [], "appended": 0}

    def _fake_test(url, **kw):
        calls["tested"].append(url)
        return {"url": url, "status": "ok", "extracted_chars": 4000,
                "extraction_quality": "GOOD"}

    def _fake_record(run_id, source, result, limitations_notes):
        return {"timestamp_utc": "2026-07-21T00:00:00Z", "change_status": "new",
                "extracted_chars": result["extracted_chars"],
                "extraction_quality": result["extraction_quality"]}

    def _fake_append(record):
        calls["appended"] += 1
        return record

    monkeypatch.setattr(tester, "test_source_url", _fake_test)
    monkeypatch.setattr(runs, "record_from_source_result", _fake_record)
    monkeypatch.setattr(runs, "append_run", _fake_append)

    report = sr.build_readiness_report("AE", record_run=True)

    assert calls["tested"] == ["https://x.example"]      # tester was invoked
    assert calls["appended"] == 1
    assert report["record_run"] is True
    assert report["run_id"] is not None
    entry = report["p0_sources"][0]
    assert entry["chars"] == 4000 and entry["quality"] == "GOOD"


def test_report_record_run_tester_exception_yields_failed(monkeypatch):
    """A tester exception is caught and recorded as a FAILED extraction."""
    import app.source_runs as runs
    import app.source_tester as tester

    sources = [_src("CBUAE", "central_bank", "ae-cbuae")]
    _patch_report_deps(monkeypatch, sources)

    def _boom(url, **kw):
        raise ConnectionError("dns failure")

    captured = {}

    def _fake_record(run_id, source, result, limitations_notes):
        captured["result"] = result
        return {"extracted_chars": result["extracted_chars"],
                "extraction_quality": result["extraction_quality"],
                "error": result.get("error")}

    monkeypatch.setattr(tester, "test_source_url", _boom)
    monkeypatch.setattr(runs, "record_from_source_result", _fake_record)
    monkeypatch.setattr(runs, "append_run", lambda record: record)

    report = sr.build_readiness_report("AE", record_run=True)

    # The synthesized failed result flows through to the record.
    assert captured["result"]["extraction_quality"] == "failed"
    assert "ConnectionError" in captured["result"]["error"]
    entry = report["p0_sources"][0]
    assert entry["quality"] == "failed"


def test_report_record_run_navigation_only_runs_tester(monkeypatch):
    """record_run + navigation-only restricted source still probes via the tester."""
    import app.source_runs as runs
    import app.source_tester as tester

    sources = [_src("SPA", "financial_regulator", "ae-spa",
                    status="disabled_navigation_only")]
    _patch_report_deps(monkeypatch, sources)

    calls = {"tested": []}
    monkeypatch.setattr(tester, "test_source_url",
                        lambda url, **kw: calls["tested"].append(url) or {"extracted_chars": 0})
    monkeypatch.setattr(runs, "record_from_source_result",
                        lambda **kw: {"extraction_quality": "THIN", "extracted_chars": 50})
    monkeypatch.setattr(runs, "append_run", lambda record: record)

    report = sr.build_readiness_report("AE", record_run=True)

    assert calls["tested"] == ["https://x.example"]      # nav-only still gets probed
    assert report["blocked_sources"][0]["chars"] == 50


def test_report_record_run_navigation_only_tester_exception_falls_back(monkeypatch):
    """A tester failure on a nav-only source falls back to a restricted_record."""
    import app.source_runs as runs
    import app.source_tester as tester

    sources = [_src("SPA", "financial_regulator", "ae-spa",
                    status="disabled_navigation_only")]
    _patch_report_deps(monkeypatch, sources)

    captured = {}
    monkeypatch.setattr(tester, "test_source_url",
                        lambda url, **kw: (_ for _ in ()).throw(TimeoutError("slow")))
    monkeypatch.setattr(runs, "record_from_source_result",
                        lambda **kw: pytest.fail("should not reach record_from_source_result"))

    def _restricted(run_id, source, limitations_notes):
        captured["notes"] = limitations_notes
        return {"extraction_quality": "FAILED", "extracted_chars": 0}

    monkeypatch.setattr(runs, "restricted_record", _restricted)
    monkeypatch.setattr(runs, "append_run", lambda record: record)

    report = sr.build_readiness_report("AE", record_run=True)

    assert any("Diagnostic failed" in n for n in captured["notes"])
    assert report["blocked_sources"][0]["source_id"] == "ae-spa"


def test_report_record_run_external_access_uses_restricted_record(monkeypatch):
    """record_run + external-access source records WITHOUT any network call."""
    import app.source_runs as runs
    import app.source_tester as tester

    sources = [_src("DIFC", "financial_regulator", "ae-difc",
                    status="disabled_external_access")]
    _patch_report_deps(monkeypatch, sources)

    monkeypatch.setattr(tester, "test_source_url",
                        lambda *a, **k: pytest.fail("external-access must not hit the network"))
    calls = {"restricted": 0}

    def _restricted(run_id, source, limitations_notes):
        calls["restricted"] += 1
        return {"timestamp_utc": "2026-07-21T03:00:00Z", "extracted_chars": 0}

    monkeypatch.setattr(runs, "restricted_record", _restricted)
    monkeypatch.setattr(runs, "append_run", lambda record: record)

    report = sr.build_readiness_report("AE", record_run=True)

    assert calls["restricted"] == 1
    assert report["sources_restricted"] == 1
    assert report["blocked_sources"][0]["last_run"] == "2026-07-21T03:00:00Z"


def test_report_history_error_appended_when_entry_lacks_error(monkeypatch):
    """audit has no error but the overlaid history record carries one => 'Last error' note."""
    sources = [_src("CBUAE", "central_bank", "ae-cbuae")]
    audit = {"CBUAE": {"extracted_chars": 3000}}         # no error in audit
    history = {"ae-cbuae": {
        "extracted_chars": 3000, "extraction_quality": "GOOD",
        "error": "stale certificate",
    }}
    _patch_report_deps(monkeypatch, sources, audit, history)

    report = sr.build_readiness_report("AE")

    entry = report["p0_sources"][0]
    assert entry["error"] == "stale certificate"
    assert any("Last error" in lim for lim in entry["limitations"])


# ── _apply_run_record — direct overlay unit ──────────────────────────────────

def test_apply_run_record_overlays_all_fields():
    entry = {
        "quality": "THIN", "quality_label": "old", "chars": 0, "limitations": [],
    }
    record = {
        "timestamp_utc": "2026-07-21T02:00:00Z",
        "change_status": "changed",
        "extracted_chars": 2200,
        "extraction_quality": "GOOD",
        "pdf_links_count": 3,
        "pdf_extracted_chars": 1200,
        "error": "minor warn",
        "limitations_notes": "adapter fallback used",
    }
    sr._apply_run_record(entry, record)

    assert entry["last_run"] == "2026-07-21T02:00:00Z"
    assert entry["change_status"] == "changed"
    assert entry["chars"] == 2200
    assert entry["quality"] == "GOOD"
    assert entry["quality_label"] == "✅ Good"
    assert entry["pdf_links_count"] == 3
    assert entry["pdf_extracted_chars"] == 1200
    assert entry["error"] == "minor warn"
    assert "adapter fallback used" in entry["limitations"]


def test_apply_run_record_keeps_existing_quality_when_record_lacks_it():
    entry = {"quality": "MEDIUM", "quality_label": "⚡ Medium",
             "chars": 900, "limitations": []}
    sr._apply_run_record(entry, {"extracted_chars": None})   # no extraction_quality key
    assert entry["quality"] == "MEDIUM"                      # falls back to existing
    assert entry["chars"] == 0                               # None coerced to 0


def test_apply_run_record_does_not_duplicate_limitation_note():
    entry = {"quality": "GOOD", "chars": 3000, "limitations": ["dup note"]}
    sr._apply_run_record(entry, {"limitations_notes": "dup note"})
    assert entry["limitations"].count("dup note") == 1       # not appended twice


# ── renderers ────────────────────────────────────────────────────────────────

def _minimal_report(verdict="FREE_CHECK_READY"):
    entry = {"name": "CBUAE", "category": "central_bank", "url": "https://x",
             "status": "active", "chars": 3000, "quality": "GOOD",
             "quality_label": "✅ Good", "error": None, "limitations": ["note"],
             "last_run": "2026-07-21T00:00:00Z", "change_status": "changed",
             "pdf_links_count": 1, "pdf_extracted_chars": 500, "source_id": "ae-cbuae"}
    blocked = {"name": "DIFC", "category": "financial_regulator", "url": "https://y",
               "status": "disabled_external_access", "chars": 0, "quality": "FAILED",
               "quality_label": "❌ Failed", "error": None,
               "limitations": ["Geo-blocked"], "source_id": "ae-difc"}
    return {
        "market": "AE", "profile": "fintech", "generated_at": "2026-07-21T00:00:00Z",
        "sources_active": 1, "sources_blocked": 1, "sources_restricted": 1,
        "p0_sources": [entry], "p1_sources": [], "p2_sources": [],
        "blocked_sources": [blocked], "pilot_ready": True,
        "pilot_verdict": verdict, "pilot_note": "note prose",
        "limitations": ["DIFC: Geo-blocked"], "record_run": False, "run_id": None,
    }


def test_render_readiness_terminal_prints_verdict_and_sources(capsys):
    sr.render_readiness_terminal(_minimal_report("FREE_CHECK_READY"))
    out = capsys.readouterr().out
    assert "Source Readiness Report" in out
    assert "FREE_CHECK_READY" in out
    assert "CBUAE" in out
    assert "DIFC" in out                                  # blocked section rendered
    assert "PDF text:" in out                             # pdf_extracted_chars branch


def test_render_readiness_terminal_handles_pilot_ready_and_needs_work(capsys):
    sr.render_readiness_terminal(_minimal_report("NEEDS_MORE_WORK"))
    out = capsys.readouterr().out
    assert "NEEDS_MORE_WORK" in out


def test_export_readiness_html_writes_file(monkeypatch, tmp_path):
    monkeypatch.setattr(sr, "_REPORTS_DIR", tmp_path / "reports")
    path = sr.export_readiness_html(_minimal_report("FREE_CHECK_READY"))

    assert path.exists()
    assert path.parent == tmp_path / "reports"
    html = path.read_text(encoding="utf-8")
    assert "StatuteProof" in html
    assert "FREE CHECK READY" in html                    # verdict underscores replaced
    assert "CBUAE" in html
    assert "DIFC" in html
    assert "Not legal advice" in html                    # disclaimer present


def test_export_readiness_html_verdict_colors(monkeypatch, tmp_path):
    monkeypatch.setattr(sr, "_REPORTS_DIR", tmp_path / "reports")
    p_pilot = sr.export_readiness_html(_minimal_report("PILOT_READY"))
    assert "#f5c616" in p_pilot.read_text(encoding="utf-8")   # PILOT_READY colour
    p_needs = sr.export_readiness_html(_minimal_report("NEEDS_MORE_WORK"))
    assert "#f55" in p_needs.read_text(encoding="utf-8")      # fallback colour
