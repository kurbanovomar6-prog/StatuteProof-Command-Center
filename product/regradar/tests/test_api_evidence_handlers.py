"""Behavioral coverage for the ``_EvidenceHandlerMixin`` in ``app/api_evidence.py``.

Every test drives the REAL ``_Handler`` (built by the shared harness in
``tests/test_api_coverage_uplift.py``) and asserts REAL behavior — status codes,
the unauth 401 gate, tenancy/visibility 404, the plan/entitlement paywall,
IDOR 403 scope gates, the export rate-limiter/capability gates, disk-read
branches, and the internal-error 500 fall-throughs.

Discipline (see the ``app/api_evidence.py`` module docstring):
  * ``require_auth`` and ``_official_alert_blocked_by_plan`` are read as bare
    globals from ``app.api_evidence`` — patch THERE.
  * ``BASE_DIR`` / ``_EXPORT_LIMITER`` are SEPARATE bindings on
    ``app.api_evidence`` — repoint ``api_evidence.BASE_DIR`` for the on-disk
    evidence-list / diff handlers.
  * Function-local imports (``app.source_runs``, ``app.evidence_assessment``,
    ``app.review_queue``, ``app.audit_export``, ``app.source_health_timeline``)
    resolve against their source modules — patch there.
  * Per-request helpers (``_denied_custom_source_ids``, ``_source_visible_to``,
    ``_evidence_source_out_of_scope``, ``_caller_org_id``, ``_require_capability``,
    ``_rbac_log_export``, ``_rbac_guard``) live on ``_Handler`` and are overridden
    per instance exactly as the sibling suites do.

No network, no PDF/ZIP generation, and no real plan DB is touched.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api  # noqa: F401 — import the package entry first so app.api_evidence
import app.api_evidence as api_evidence  # is not initialized mid circular-import

# Reuse the proven real-_Handler harness from the sibling uplift suite.
from test_api_coverage_uplift import _auth_as, _last, _make_handler  # noqa: E402


def _seed_runs(monkeypatch, tmp_path: Path, records: list[dict]) -> Path:
    """Write source_runs.jsonl under a throwaway BASE_DIR and repoint the
    SEPARATE ``api_evidence.BASE_DIR`` binding the moved handlers read."""
    runs_dir = tmp_path / "data" / "source_runs"
    runs_dir.mkdir(parents=True)
    with (runs_dir / "source_runs.jsonl").open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")
    monkeypatch.setattr(api_evidence, "BASE_DIR", tmp_path)
    return tmp_path


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/evidence — source run records, market filter, cross-tenant exclusion
# ══════════════════════════════════════════════════════════════════════════════

def test_evidence_list_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/evidence")
    handler._handle_evidence_list()
    data, status, _ = _last(handler)
    assert status == 401
    assert data["ok"] is False


def test_evidence_list_filters_market_and_excludes_denied_sources(monkeypatch, tmp_path):
    _auth_as(monkeypatch, {"id": 1})
    _seed_runs(monkeypatch, tmp_path, [
        {"run_id": "r-ae-1", "source_id": "cbuae", "market": "AE",
         "timestamp_utc": "2026-07-01T00:00:00Z", "source_name": "CBUAE"},
        {"run_id": "r-ae-2", "source_id": "victim-custom", "market": "AE",
         "timestamp_utc": "2026-07-02T00:00:00Z"},  # denied — another tenant's private source
        {"run_id": "r-uk-1", "source_id": "fca", "market": "UK",
         "timestamp_utc": "2026-07-03T00:00:00Z"},  # wrong market
    ])
    handler = _make_handler("GET", "/api/evidence?market=ae")
    handler._denied_custom_source_ids = lambda user: {"victim-custom"}  # type: ignore[method-assign]
    handler._handle_evidence_list()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["market"] == "AE"
    returned_ids = {rec["run_id"] for rec in data["evidence"]}
    assert returned_ids == {"r-ae-1"}  # market-scoped AND cross-tenant filtered
    assert data["total"] == 1


def test_evidence_list_bad_limit_falls_back_and_sorts_newest_first(monkeypatch, tmp_path):
    _auth_as(monkeypatch, {"id": 1})
    _seed_runs(monkeypatch, tmp_path, [
        {"run_id": "old", "source_id": "cbuae", "market": "AE",
         "timestamp_utc": "2026-01-01T00:00:00Z"},
        {"run_id": "new", "source_id": "cbuae", "market": "AE",
         "timestamp_utc": "2026-12-01T00:00:00Z"},
    ])
    handler = _make_handler("GET", "/api/evidence?limit=not-a-number")
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    handler._handle_evidence_list()
    data, status, _ = _last(handler)
    assert status == 200
    assert [r["run_id"] for r in data["evidence"]] == ["new", "old"]  # reverse-chron


def test_evidence_list_marks_skipped_cycle(monkeypatch, tmp_path):
    _auth_as(monkeypatch, {"id": 1})
    _seed_runs(monkeypatch, tmp_path, [
        {"run_id": "skip", "source_id": "cbuae", "market": "AE",
         "failure_code": "CIRCUIT_OPEN", "limitations_notes": "breaker open",
         "timestamp_utc": "2026-07-01T00:00:00Z"},
    ])
    handler = _make_handler("GET", "/api/evidence")
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    handler._handle_evidence_list()
    data, status, _ = _last(handler)
    assert status == 200
    row = data["evidence"][0]
    assert row["not_fetched_this_cycle"] is True  # labelled, not a silent failed row
    assert row["limitations_notes"] == "breaker open"


def test_evidence_list_internal_error_is_500(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/evidence")

    def _boom(user):
        raise RuntimeError("scope store down")

    handler._denied_custom_source_ids = _boom  # type: ignore[method-assign]
    handler._handle_evidence_list()
    _, status, _ = _last(handler)
    assert status == 500


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/evidence/diff — tenancy 404, plan 402, disk branches
# ══════════════════════════════════════════════════════════════════════════════

def test_evidence_diff_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/evidence/diff?run_id=r1")
    handler._handle_evidence_diff_get()
    _, status, _ = _last(handler)
    assert status == 401


def test_evidence_diff_missing_run_id_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/evidence/diff")
    handler._handle_evidence_diff_get()
    data, status, _ = _last(handler)
    assert status == 400
    assert "run_id is required" in data["message"]


def test_evidence_diff_other_tenant_source_is_404(monkeypatch, tmp_path):
    """A diff for a source the caller cannot see returns the SAME 404 as no-diff
    — never confirming the run exists for a source out of scope."""
    _auth_as(monkeypatch, {"id": 1})
    _seed_runs(monkeypatch, tmp_path, [
        {"run_id": "r1", "source_id": "secret-custom", "diff_md_path": "x.md"},
    ])
    handler = _make_handler("GET", "/api/evidence/diff?run_id=r1")
    handler._source_visible_to = lambda user, sid: False  # type: ignore[method-assign]
    handler._handle_evidence_diff_get()
    data, status, _ = _last(handler)
    assert status == 404
    assert "No diff available" in data["message"]


def test_evidence_diff_plan_gated_is_402(monkeypatch, tmp_path):
    _auth_as(monkeypatch, {"id": 1})
    _seed_runs(monkeypatch, tmp_path, [
        {"run_id": "r1", "source_id": "cbuae", "diff_md_path": "x.md"},
    ])
    monkeypatch.setattr(api_evidence, "_official_alert_blocked_by_plan",
                        lambda uid, sid: True)
    handler = _make_handler("GET", "/api/evidence/diff?run_id=r1")
    handler._source_visible_to = lambda user, sid: True  # type: ignore[method-assign]
    handler._handle_evidence_diff_get()
    data, status, _ = _last(handler)
    assert status == 402
    assert data["reason"] == "plan_required"


def test_evidence_diff_no_diff_paths_is_404(monkeypatch, tmp_path):
    _auth_as(monkeypatch, {"id": 1})
    _seed_runs(monkeypatch, tmp_path, [
        {"run_id": "r1", "source_id": "cbuae"},  # no diff_md_path / diff_json_path
    ])
    monkeypatch.setattr(api_evidence, "_official_alert_blocked_by_plan",
                        lambda uid, sid: False)
    handler = _make_handler("GET", "/api/evidence/diff?run_id=r1")
    handler._source_visible_to = lambda user, sid: True  # type: ignore[method-assign]
    handler._handle_evidence_diff_get()
    _, status, _ = _last(handler)
    assert status == 404


def test_evidence_diff_file_missing_on_disk_is_404(monkeypatch, tmp_path):
    _auth_as(monkeypatch, {"id": 1})
    _seed_runs(monkeypatch, tmp_path, [
        {"run_id": "r1", "source_id": "cbuae", "diff_md_path": "gone/nope.md"},
    ])
    monkeypatch.setattr(api_evidence, "_official_alert_blocked_by_plan",
                        lambda uid, sid: False)
    handler = _make_handler("GET", "/api/evidence/diff?run_id=r1")
    handler._source_visible_to = lambda user, sid: True  # type: ignore[method-assign]
    handler._handle_evidence_diff_get()
    data, status, _ = _last(handler)
    assert status == 404
    assert "not found on disk" in data["message"]


def test_evidence_diff_success_returns_text(monkeypatch, tmp_path):
    _auth_as(monkeypatch, {"id": 1})
    base = _seed_runs(monkeypatch, tmp_path, [
        {"run_id": "r1", "source_id": "cbuae", "diff_md_path": "diffs/r1.md"},
    ])
    diff_dir = base / "diffs"
    diff_dir.mkdir()
    (diff_dir / "r1.md").write_text("- removed clause\n+ added clause", encoding="utf-8")
    monkeypatch.setattr(api_evidence, "_official_alert_blocked_by_plan",
                        lambda uid, sid: False)
    handler = _make_handler("GET", "/api/evidence/diff?run_id=r1")
    handler._source_visible_to = lambda user, sid: True  # type: ignore[method-assign]
    handler._handle_evidence_diff_get()
    data, status, _ = _last(handler)
    assert status == 200
    assert "added clause" in data["diff_text"]
    assert data["run_id"] == "r1"


def test_evidence_diff_internal_error_is_500(monkeypatch, tmp_path):
    _auth_as(monkeypatch, {"id": 1})
    _seed_runs(monkeypatch, tmp_path, [
        {"run_id": "r1", "source_id": "cbuae", "diff_md_path": "diffs/r1.md"},
    ])
    monkeypatch.setattr(api_evidence, "_official_alert_blocked_by_plan",
                        lambda uid, sid: False)
    handler = _make_handler("GET", "/api/evidence/diff?run_id=r1")

    def _boom(user, sid):
        raise RuntimeError("visibility store down")

    handler._source_visible_to = _boom  # type: ignore[method-assign]
    handler._handle_evidence_diff_get()
    _, status, _ = _last(handler)
    assert status == 500


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/evidence/review + review-history — auth, IDOR 403, error branches
# ══════════════════════════════════════════════════════════════════════════════

def test_evidence_review_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/evidence/review?run_id=r1")
    handler._handle_evidence_review_get()
    _, status, _ = _last(handler)
    assert status == 401


def test_evidence_review_missing_id_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/evidence/review")
    handler._handle_evidence_review_get()
    data, status, _ = _last(handler)
    assert status == 400
    assert "evidence_record_id is required" in data["message"]


def test_evidence_review_out_of_scope_is_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/evidence/review?run_id=other")
    handler._evidence_source_out_of_scope = lambda user, eid: True  # type: ignore[method-assign]
    handler._handle_evidence_review_get()
    data, status, _ = _last(handler)
    assert status == 403
    assert "not in your scope" in data["message"]


def test_evidence_review_success_scopes_to_org(monkeypatch):
    import app.evidence_assessment as ea

    seen = {}

    def _latest(eid, org_id):
        seen["args"] = (eid, org_id)
        return {"impact_level": "high"}

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(ea, "latest_assessment_for", _latest)
    handler = _make_handler("GET", "/api/evidence/review?run_id=r1")
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 9  # type: ignore[method-assign]
    handler._handle_evidence_review_get()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["assessment"]["impact_level"] == "high"
    assert seen["args"] == ("r1", 9)  # private per-tenant note scoped to caller org


def test_evidence_review_internal_error_is_500(monkeypatch):
    import app.evidence_assessment as ea

    _auth_as(monkeypatch, {"id": 1})

    def _boom(eid, org_id):
        raise RuntimeError("assessment store down")

    monkeypatch.setattr(ea, "latest_assessment_for", _boom)
    handler = _make_handler("GET", "/api/evidence/review?run_id=r1")
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 1  # type: ignore[method-assign]
    handler._handle_evidence_review_get()
    _, status, _ = _last(handler)
    assert status == 500


def test_evidence_review_history_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/evidence/review-history?run_id=r1")
    handler._handle_evidence_review_history_get()
    _, status, _ = _last(handler)
    assert status == 401


def test_evidence_review_history_success(monkeypatch):
    import app.source_health_timeline as sht

    seen = {}

    def _build(eid, org_id):
        seen["args"] = (eid, org_id)
        return {"ok": True, "history": [{"decision": "monitor"}]}

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(sht, "build_evidence_review_history", _build)
    handler = _make_handler("GET", "/api/evidence/review-history?run_id=r1")
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 6  # type: ignore[method-assign]
    handler._handle_evidence_review_history_get()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True
    assert seen["args"] == ("r1", 6)  # per-tenant history scoped to caller org


def test_evidence_review_history_missing_id_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/evidence/review-history")
    handler._handle_evidence_review_history_get()
    data, status, _ = _last(handler)
    assert status == 400
    assert "evidence_record_id is required" in data["message"]


def test_evidence_review_history_out_of_scope_is_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/evidence/review-history?run_id=other")
    handler._evidence_source_out_of_scope = lambda user, eid: True  # type: ignore[method-assign]
    handler._handle_evidence_review_history_get()
    _, status, _ = _last(handler)
    assert status == 403


def test_evidence_review_history_value_error_is_400(monkeypatch):
    import app.source_health_timeline as sht

    _auth_as(monkeypatch, {"id": 1})

    def _boom(eid, org_id):
        raise ValueError("unknown evidence record")

    monkeypatch.setattr(sht, "build_evidence_review_history", _boom)
    handler = _make_handler("GET", "/api/evidence/review-history?run_id=r1")
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 1  # type: ignore[method-assign]
    handler._handle_evidence_review_history_get()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "unknown evidence record"


def test_evidence_review_history_internal_error_is_500(monkeypatch):
    import app.source_health_timeline as sht

    _auth_as(monkeypatch, {"id": 1})

    def _boom(eid, org_id):
        raise RuntimeError("timeline store down")

    monkeypatch.setattr(sht, "build_evidence_review_history", _boom)
    handler = _make_handler("GET", "/api/evidence/review-history?run_id=r1")
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 1  # type: ignore[method-assign]
    handler._handle_evidence_review_history_get()
    _, status, _ = _last(handler)
    assert status == 500


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/evidence/assess — RBAC write gate + IDOR + error branches
# ══════════════════════════════════════════════════════════════════════════════

def test_evidence_assess_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("POST", "/api/evidence/assess", {"evidence_record_id": "r1"})
    handler._handle_evidence_assess()
    _, status, _ = _last(handler)
    assert status == 401


def test_evidence_assess_rbac_denied_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/evidence/assess",
                            {"evidence_record_id": "r1", "impact_level": "high"})
    handler._rbac_guard = lambda user, action, **kw: (  # type: ignore[method-assign]
        handler._sent.append(({"ok": False}, 403, None)) or False
    )
    handler._handle_evidence_assess()
    _, status, _ = _last(handler)
    assert status == 403


def test_evidence_assess_invalid_json_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/evidence/assess", raw=b"{not json")
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_evidence_assess()
    data, status, _ = _last(handler)
    assert status == 400
    assert "Invalid JSON" in data["message"]


def test_evidence_assess_out_of_scope_is_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/evidence/assess",
                            {"evidence_record_id": "other", "impact_level": "high"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._evidence_source_out_of_scope = lambda user, eid: True  # type: ignore[method-assign]
    handler._handle_evidence_assess()
    data, status, _ = _last(handler)
    assert status == 403
    assert "not in your scope" in data["message"]


def test_evidence_assess_value_error_is_400(monkeypatch):
    import app.evidence_assessment as ea

    _auth_as(monkeypatch, {"id": 1, "email": "u@e.com"})

    def _boom(**kwargs):
        raise ValueError("impact_level is required")

    monkeypatch.setattr(ea, "create_assessment", _boom)
    handler = _make_handler("POST", "/api/evidence/assess", {"evidence_record_id": "r1"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 1  # type: ignore[method-assign]
    handler._handle_evidence_assess()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "impact_level is required"


def test_evidence_assess_success_is_201_and_attributed(monkeypatch):
    import app.evidence_assessment as ea

    seen = {}

    def _create(**kwargs):
        seen["kwargs"] = kwargs
        return {"id": 1, "impact_level": kwargs["impact_level"]}

    _auth_as(monkeypatch, {"id": 55, "email": "rev@e.com"})
    monkeypatch.setattr(ea, "create_assessment", _create)
    handler = _make_handler("POST", "/api/evidence/assess",
                            {"evidence_record_id": "r1", "impact_level": "high", "note": "n"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 3  # type: ignore[method-assign]
    handler._handle_evidence_assess()
    data, status, _ = _last(handler)
    assert status == 201
    assert data["assessment"]["impact_level"] == "high"
    assert seen["kwargs"]["reviewer_user_id"] == 55  # attributed to caller
    assert seen["kwargs"]["org_id"] == 3


def test_evidence_assess_internal_error_is_500(monkeypatch):
    import app.evidence_assessment as ea

    _auth_as(monkeypatch, {"id": 1, "email": "u@e.com"})

    def _boom(**kwargs):
        raise RuntimeError("assessment write failed")

    monkeypatch.setattr(ea, "create_assessment", _boom)
    handler = _make_handler("POST", "/api/evidence/assess",
                            {"evidence_record_id": "r1", "impact_level": "high"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 1  # type: ignore[method-assign]
    handler._handle_evidence_assess()
    _, status, _ = _last(handler)
    assert status == 500


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/evidence/export — paywall + IDOR + delegation to _write_evidence_export
# ══════════════════════════════════════════════════════════════════════════════

def test_evidence_export_get_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/evidence/export?run_id=r1")
    handler._handle_evidence_export_get()
    _, status, _ = _last(handler)
    assert status == 401


def test_evidence_export_get_missing_id_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/evidence/export")
    handler._handle_evidence_export_get()
    data, status, _ = _last(handler)
    assert status == 400
    assert "evidence_record_id is required" in data["message"]


def test_evidence_export_get_out_of_scope_is_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/evidence/export?run_id=other")
    handler._evidence_source_out_of_scope = lambda user, eid: True  # type: ignore[method-assign]
    handler._handle_evidence_export_get()
    data, status, _ = _last(handler)
    assert status == 403
    assert "not in your scope" in data["message"]


def test_evidence_export_get_capability_denied_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/evidence/export?run_id=r1")
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._require_capability = lambda user, cap: (  # type: ignore[method-assign]
        handler._sent.append(({"ok": False}, 403, None)) or False
    )
    handler._handle_evidence_export_get()
    _, status, _ = _last(handler)
    assert status == 403  # free/unactivated account rejected before export work


def test_evidence_export_get_pdf_capability_denied_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/evidence/export?run_id=r1&format=pdf")
    caps = {}

    def _cap(user, cap):
        caps[cap] = caps.get(cap, 0) + 1
        if cap == "pdf_export":
            handler._sent.append(({"ok": False}, 403, None))
            return False
        return True

    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._require_capability = _cap  # type: ignore[method-assign]
    handler._handle_evidence_export_get()
    _, status, _ = _last(handler)
    assert status == 403
    assert caps["audit_export"] == 1 and caps["pdf_export"] == 1


def test_evidence_export_get_success_delegates_with_params(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    seen = {}

    def _write(evidence_id, *, export_format, customer_delivery, org_id):
        seen.update(id=evidence_id, fmt=export_format,
                    delivery=customer_delivery, org=org_id)
        handler._sent.append(({"ok": True}, 200, None))

    handler = _make_handler("GET",
                            "/api/evidence/export?run_id=r1&format=md_html&customer_delivery=true")
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._require_capability = lambda user, cap: True  # type: ignore[method-assign]
    rbac_calls = []
    handler._rbac_log_export = lambda user, resource_id: rbac_calls.append(resource_id)  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 7  # type: ignore[method-assign]
    handler._write_evidence_export = _write  # type: ignore[method-assign]
    handler._handle_evidence_export_get()
    _, status, _ = _last(handler)
    assert status == 200
    assert seen == {"id": "r1", "fmt": "md_html", "delivery": True, "org": 7}
    assert rbac_calls == ["r1"]  # authorized export recorded


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/evidence/export — mirror of the GET paywall + delegation
# ══════════════════════════════════════════════════════════════════════════════

def test_evidence_export_post_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("POST", "/api/evidence/export", {"run_id": "r1"})
    handler._handle_evidence_export_post()
    _, status, _ = _last(handler)
    assert status == 401


def test_evidence_export_post_invalid_json_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/evidence/export", raw=b"{not json")
    handler._handle_evidence_export_post()
    data, status, _ = _last(handler)
    assert status == 400
    assert "Invalid JSON" in data["message"]


def test_evidence_export_post_missing_id_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/evidence/export", {})
    handler._handle_evidence_export_post()
    data, status, _ = _last(handler)
    assert status == 400
    assert "evidence_record_id is required" in data["message"]


def test_evidence_export_post_out_of_scope_is_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/evidence/export", {"run_id": "other"})
    handler._evidence_source_out_of_scope = lambda user, eid: True  # type: ignore[method-assign]
    handler._handle_evidence_export_post()
    data, status, _ = _last(handler)
    assert status == 403
    assert "not in your scope" in data["message"]


def test_evidence_export_post_capability_denied_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/evidence/export", {"run_id": "r1"})
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._require_capability = lambda user, cap: (  # type: ignore[method-assign]
        handler._sent.append(({"ok": False}, 403, None)) or False
    )
    handler._handle_evidence_export_post()
    _, status, _ = _last(handler)
    assert status == 403  # free/unactivated account rejected before any export work


def test_evidence_export_post_success_delegates(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    seen = {}

    def _write(evidence_id, *, export_format, customer_delivery, org_id):
        seen.update(id=evidence_id, fmt=export_format,
                    delivery=customer_delivery, org=org_id)
        handler._sent.append(({"ok": True}, 200, None))

    handler = _make_handler("POST", "/api/evidence/export",
                            {"run_id": "r1", "format": "PDF", "customer_delivery": False})
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._require_capability = lambda user, cap: True  # type: ignore[method-assign]
    handler._rbac_log_export = lambda user, resource_id: None  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 4  # type: ignore[method-assign]
    handler._write_evidence_export = _write  # type: ignore[method-assign]
    handler._handle_evidence_export_post()
    _, status, _ = _last(handler)
    assert status == 200
    assert seen == {"id": "r1", "fmt": "pdf", "delivery": False, "org": 4}


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/evidence/export-download — streams the pack, disk + error branches
# ══════════════════════════════════════════════════════════════════════════════

def test_evidence_export_download_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/evidence/export-download?run_id=r1")
    handler._handle_evidence_export_download()
    _, status, _ = _last(handler)
    assert status == 401


def test_evidence_export_download_missing_id_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/evidence/export-download")
    handler._handle_evidence_export_download()
    data, status, _ = _last(handler)
    assert status == 400
    assert "evidence_record_id is required" in data["message"]


def test_evidence_export_download_out_of_scope_is_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/evidence/export-download?run_id=other")
    handler._evidence_source_out_of_scope = lambda user, eid: True  # type: ignore[method-assign]
    handler._handle_evidence_export_download()
    _, status, _ = _last(handler)
    assert status == 403


def test_evidence_export_download_capability_denied_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/evidence/export-download?run_id=r1")
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._require_capability = lambda user, cap: (  # type: ignore[method-assign]
        handler._sent.append(({"ok": False}, 403, None)) or False
    )
    handler._handle_evidence_export_download()
    _, status, _ = _last(handler)
    assert status == 403


def test_evidence_export_download_value_error_is_400(monkeypatch):
    import app.evidence_assessment as ea

    _auth_as(monkeypatch, {"id": 1})

    def _boom(eid):
        raise ValueError("no such evidence record")

    monkeypatch.setattr(ea, "find_evidence_record", _boom)
    handler = _make_handler("GET", "/api/evidence/export-download?run_id=r1")
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._require_capability = lambda user, cap: True  # type: ignore[method-assign]
    handler._rbac_log_export = lambda user, resource_id: None  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 1  # type: ignore[method-assign]
    handler._handle_evidence_export_download()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "no such evidence record"


def test_evidence_export_download_missing_generated_file_is_500(monkeypatch):
    import app.audit_export as ax
    import app.evidence_assessment as ea

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(ea, "find_evidence_record", lambda eid: {"run_id": eid})
    monkeypatch.setattr(ea, "latest_assessment_for", lambda eid, org_id: None)
    # Builder claims success but names a path that does not exist -> 500, never a broken stream.
    monkeypatch.setattr(ax, "write_audit_pack",
                        lambda record, assessment: {"md_path": "nowhere/pack.md"})
    handler = _make_handler("GET", "/api/evidence/export-download?run_id=r1")
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._require_capability = lambda user, cap: True  # type: ignore[method-assign]
    handler._rbac_log_export = lambda user, resource_id: None  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 1  # type: ignore[method-assign]
    handler._handle_evidence_export_download()
    data, status, _ = _last(handler)
    assert status == 500
    assert "not generated" in data["message"]


def test_evidence_export_download_success_streams_file(monkeypatch, tmp_path):
    import app.audit_export as ax
    import app.evidence_assessment as ea

    _auth_as(monkeypatch, {"id": 1})
    pack = tmp_path / "pack.md"
    pack.write_text("# Audit pack\nhash: abc", encoding="utf-8")
    monkeypatch.setattr(api_evidence, "BASE_DIR", tmp_path)
    monkeypatch.setattr(ea, "find_evidence_record", lambda eid: {"run_id": eid})
    monkeypatch.setattr(ea, "latest_assessment_for", lambda eid, org_id: None)
    monkeypatch.setattr(ax, "write_audit_pack",
                        lambda record, assessment: {"md_path": "pack.md"})
    handler = _make_handler("GET", "/api/evidence/export-download?run_id=r1")
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._require_capability = lambda user, cap: True  # type: ignore[method-assign]
    handler._rbac_log_export = lambda user, resource_id: None  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 1  # type: ignore[method-assign]
    # Success streams via the stdlib response machinery; capture the status line
    # and headers the mixin sets instead of standing up a full BaseHTTPRequestHandler.
    sent_headers: dict[str, str] = {}
    responses: list[int] = []
    handler.send_response = lambda code: responses.append(code)  # type: ignore[method-assign]
    handler.send_header = lambda k, v: sent_headers.__setitem__(k, v)  # type: ignore[method-assign]
    handler.end_headers = lambda: None  # type: ignore[method-assign]
    handler._handle_evidence_export_download()
    # Success streams raw bytes via wfile, not _send_json.
    assert responses == [200]
    assert sent_headers["Content-Type"] == "text/markdown; charset=utf-8"
    assert "attachment" in sent_headers["Content-Disposition"]
    assert b"Audit pack" in handler.wfile.getvalue()
    assert not handler._sent  # never fell through to a JSON error


def test_evidence_export_download_pdf_success_streams(monkeypatch, tmp_path):
    import app.audit_export as ax
    import app.evidence_assessment as ea

    _auth_as(monkeypatch, {"id": 1})
    pdf = tmp_path / "pack.pdf"
    pdf.write_bytes(b"%PDF-1.4 audit")
    monkeypatch.setattr(api_evidence, "BASE_DIR", tmp_path)
    monkeypatch.setattr(ea, "find_evidence_record", lambda eid: {"run_id": eid})
    monkeypatch.setattr(ea, "latest_assessment_for", lambda eid, org_id: None)
    monkeypatch.setattr(ax, "write_audit_pack_pdf",
                        lambda record, assessment: {"pdf_path": "pack.pdf"})
    handler = _make_handler("GET", "/api/evidence/export-download?run_id=r1&format=pdf")
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._require_capability = lambda user, cap: True  # type: ignore[method-assign]
    handler._rbac_log_export = lambda user, resource_id: None  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 1  # type: ignore[method-assign]
    sent_headers: dict[str, str] = {}
    responses: list[int] = []
    handler.send_response = lambda code: responses.append(code)  # type: ignore[method-assign]
    handler.send_header = lambda k, v: sent_headers.__setitem__(k, v)  # type: ignore[method-assign]
    handler.end_headers = lambda: None  # type: ignore[method-assign]
    handler._handle_evidence_export_download()
    assert responses == [200]
    assert sent_headers["Content-Type"] == "application/pdf"
    assert b"%PDF" in handler.wfile.getvalue()


def test_evidence_export_download_runtime_error_is_500(monkeypatch):
    import app.evidence_assessment as ea

    _auth_as(monkeypatch, {"id": 1})

    def _boom(eid):
        raise RuntimeError("pdf toolchain missing")

    monkeypatch.setattr(ea, "find_evidence_record", _boom)
    handler = _make_handler("GET", "/api/evidence/export-download?run_id=r1")
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._require_capability = lambda user, cap: True  # type: ignore[method-assign]
    handler._rbac_log_export = lambda user, resource_id: None  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 1  # type: ignore[method-assign]
    handler._handle_evidence_export_download()
    _, status, _ = _last(handler)
    assert status == 500


def test_evidence_export_download_generic_error_is_500(monkeypatch):
    import app.evidence_assessment as ea

    _auth_as(monkeypatch, {"id": 1})

    def _boom(eid):
        raise KeyError("corrupt record")

    monkeypatch.setattr(ea, "find_evidence_record", _boom)
    handler = _make_handler("GET", "/api/evidence/export-download?run_id=r1")
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._require_capability = lambda user, cap: True  # type: ignore[method-assign]
    handler._rbac_log_export = lambda user, resource_id: None  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 1  # type: ignore[method-assign]
    handler._handle_evidence_export_download()
    _, status, _ = _last(handler)
    assert status == 500


# ══════════════════════════════════════════════════════════════════════════════
# _write_evidence_export — the shared writer used by GET/POST export
# ══════════════════════════════════════════════════════════════════════════════

def test_write_evidence_export_customer_delivery_path(monkeypatch):
    import app.audit_export as ax

    seen = {}

    def _customer(evidence_id, *, export_format):
        seen["args"] = (evidence_id, export_format)
        return {"ok": True, "customer": True}

    monkeypatch.setattr(ax, "build_customer_audit_pack_export_response", _customer)
    handler = _make_handler("GET", "/api/evidence/export")
    handler._write_evidence_export("r1", export_format="md_html", customer_delivery=True)
    data, status, _ = _last(handler)
    assert status == 200
    assert data["customer"] is True
    assert seen["args"] == ("r1", "md_html")


def test_write_evidence_export_internal_delivery_attaches_org_assessment(monkeypatch):
    import app.audit_export as ax
    import app.evidence_assessment as ea

    seen = {}

    def _latest(eid, org_id):
        seen["org_id"] = org_id
        return {"impact_level": "medium"}

    monkeypatch.setattr(ea, "find_evidence_record", lambda eid: {"run_id": eid})
    monkeypatch.setattr(ea, "latest_assessment_for", _latest)
    monkeypatch.setattr(ax, "build_audit_pack_export_response",
                        lambda record, assessment, export_format: {"ok": True, "pack": True})
    handler = _make_handler("GET", "/api/evidence/export")
    handler._write_evidence_export("r1", export_format="md_html",
                                   customer_delivery=False, org_id=5)
    data, status, _ = _last(handler)
    assert status == 200
    assert data["evidence_record_id"] == "r1"
    assert seen["org_id"] == 5  # only the caller's own org assessment attached


def test_write_evidence_export_value_error_is_400(monkeypatch):
    import app.evidence_assessment as ea

    def _boom(eid):
        raise ValueError("record not found")

    monkeypatch.setattr(ea, "find_evidence_record", _boom)
    handler = _make_handler("GET", "/api/evidence/export")
    handler._write_evidence_export("r1", customer_delivery=False)
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "record not found"


def test_write_evidence_export_runtime_error_is_500(monkeypatch):
    import app.evidence_assessment as ea

    def _boom(eid):
        raise RuntimeError("pdf toolchain missing")

    monkeypatch.setattr(ea, "find_evidence_record", _boom)
    handler = _make_handler("GET", "/api/evidence/export")
    handler._write_evidence_export("r1", customer_delivery=False)
    _, status, _ = _last(handler)
    assert status == 500


def test_write_evidence_export_generic_error_is_500(monkeypatch):
    import app.evidence_assessment as ea

    def _boom(eid):
        raise KeyError("corrupt record")

    monkeypatch.setattr(ea, "find_evidence_record", _boom)
    handler = _make_handler("GET", "/api/evidence/export")
    handler._write_evidence_export("r1", customer_delivery=False)
    _, status, _ = _last(handler)
    assert status == 500


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/reviews/queue — tenancy scope + error branch
# ══════════════════════════════════════════════════════════════════════════════

def test_reviews_queue_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/reviews/queue")
    handler._handle_reviews_queue_get()
    _, status, _ = _last(handler)
    assert status == 401


def test_reviews_queue_success_propagates_scope_and_default_limit(monkeypatch):
    import app.review_queue as rq

    seen = {}

    def _build(**kwargs):
        seen["kwargs"] = kwargs
        return {"ok": True, "queue": []}

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(rq, "build_review_queue", _build)
    handler = _make_handler("GET", "/api/reviews/queue?limit=oops&market=uk")
    handler._denied_custom_source_ids = lambda user: {"denied-src"}  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 3  # type: ignore[method-assign]
    handler._handle_reviews_queue_get()
    data, status, _ = _last(handler)
    assert status == 200
    assert seen["kwargs"]["excluded_source_ids"] == {"denied-src"}
    assert seen["kwargs"]["org_id"] == 3
    assert seen["kwargs"]["market"] == "UK"
    assert seen["kwargs"]["limit"] == 50  # bad limit -> default


def test_reviews_queue_internal_error_is_500(monkeypatch):
    import app.review_queue as rq

    _auth_as(monkeypatch, {"id": 1})

    def _boom(**kwargs):
        raise RuntimeError("queue store down")

    monkeypatch.setattr(rq, "build_review_queue", _boom)
    handler = _make_handler("GET", "/api/reviews/queue")
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: None  # type: ignore[method-assign]
    handler._handle_reviews_queue_get()
    _, status, _ = _last(handler)
    assert status == 500


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/canonical-evidence — auth + tenancy exclusion + error branch
# ══════════════════════════════════════════════════════════════════════════════

def test_canonical_evidence_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/canonical-evidence")
    handler._handle_canonical_evidence_get()
    _, status, _ = _last(handler)
    assert status == 401


def test_canonical_evidence_success_excludes_denied(monkeypatch):
    import app.review_queue as rq

    seen = {}

    def _build(excluded_source_ids):
        seen["excluded"] = excluded_source_ids
        return {"ok": True, "records": []}

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(rq, "build_canonical_evidence_review_queue", _build)
    handler = _make_handler("GET", "/api/canonical-evidence")
    handler._denied_custom_source_ids = lambda user: {"x"}  # type: ignore[method-assign]
    handler._handle_canonical_evidence_get()
    data, status, _ = _last(handler)
    assert status == 200
    assert seen["excluded"] == {"x"}


def test_canonical_evidence_internal_error_is_500(monkeypatch):
    import app.review_queue as rq

    _auth_as(monkeypatch, {"id": 1})

    def _boom(excluded_source_ids):
        raise RuntimeError("canonical store down")

    monkeypatch.setattr(rq, "build_canonical_evidence_review_queue", _boom)
    handler = _make_handler("GET", "/api/canonical-evidence")
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    handler._handle_canonical_evidence_get()
    _, status, _ = _last(handler)
    assert status == 500


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/audit-log — owner-only + fail-closed org + error branch
# ══════════════════════════════════════════════════════════════════════════════

class _FakePrincipal:
    def __init__(self, role, org_id):
        self.role = role
        self.org_id = org_id


def test_audit_log_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/audit-log")
    handler._handle_audit_log_get()
    _, status, _ = _last(handler)
    assert status == 401


def test_audit_log_non_owner_is_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(api_evidence.rbac_runtime, "resolve_principal",
                        lambda user: _FakePrincipal("auditor", 5))
    handler = _make_handler("GET", "/api/audit-log")
    handler._handle_audit_log_get()
    data, status, _ = _last(handler)
    assert status == 403
    assert "workspace owner" in data["message"]


def test_audit_log_unresolved_org_fails_closed_403(monkeypatch):
    """An owner whose org_id is None must NOT get a scope-less (cross-tenant) read."""
    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(api_evidence.rbac_runtime, "resolve_principal",
                        lambda user: _FakePrincipal(api_evidence.rbac_runtime.ROLE_OWNER, None))
    monkeypatch.setattr(api_evidence.rbac_runtime, "read_access_log",
                        lambda **kw: pytest.fail("must NOT read the log with an unresolved org"))
    handler = _make_handler("GET", "/api/audit-log")
    handler._handle_audit_log_get()
    data, status, _ = _last(handler)
    assert status == 403
    assert "could not be resolved" in data["message"]


def test_audit_log_owner_success_scopes_to_org(monkeypatch):
    seen = {}

    def _read(limit, org_id):
        seen["args"] = (limit, org_id)
        return [{"action": "login"}]

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(api_evidence.rbac_runtime, "resolve_principal",
                        lambda user: _FakePrincipal(api_evidence.rbac_runtime.ROLE_OWNER, 42))
    monkeypatch.setattr(api_evidence.rbac_runtime, "read_access_log", _read)
    handler = _make_handler("GET", "/api/audit-log?limit=xyz")
    handler._handle_audit_log_get()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["org_id"] == 42
    assert data["count"] == 1
    assert seen["args"] == (100, 42)  # bad limit -> default 100, org enforced


def test_audit_log_internal_error_is_500(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})

    def _boom(user):
        raise RuntimeError("rbac backend down")

    monkeypatch.setattr(api_evidence.rbac_runtime, "resolve_principal", _boom)
    handler = _make_handler("GET", "/api/audit-log")
    handler._handle_audit_log_get()
    _, status, _ = _last(handler)
    assert status == 500
