"""Behavioral coverage for the sources + reports handler mixins.

Targets the two mixins extracted from ``app.api`` — ``_SourcesHandlerMixin``
(``app/api_sources.py``) and ``_ReportsHandlerMixin`` (``app/api_reports.py``) —
driving the REAL ``_Handler`` through the shared harness in
``tests/test_api_coverage_uplift.py``. Every test asserts REAL behavior: status
codes, the unauth 401 guard, plan-capability 403 gating, tenancy scoping
(entitled-source clipping / denied-custom exclusion), rate-limit early returns,
the format branches (json / html / pdf / markdown), and the fail-closed
error/empty branches.

A moved handler reads ``require_auth`` and its module-level globals from its OWN
module (``app.api_sources`` / ``app.api_reports``), so ``_auth_as`` patches
``require_auth`` there. Function-local imports inside the bodies
(``app.monthly_assurance_report``, ``app.source_intake`` …) are patched at their
source modules, which binds at call time. No network, no PDF/ZIP generation, and
no real plan DB is touched on the mocked paths.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api  # noqa: E402,F401  (import first: resolves the api ⇄ mixin import chain)
import app.api_reports as api_reports  # noqa: E402

# Reuse the proven harness (pytest "prepend" import mode puts tests/ on sys.path).
from test_api_coverage_uplift import _auth_as, _last, _make_handler  # noqa: E402


def _force_rate_limited(handler) -> None:
    """Make the shared limiter report "over limit" so the early 429 return fires."""
    handler._rate_limited = (  # type: ignore[method-assign]
        lambda limiter, label: (handler._sent.append(({"ok": False}, 429, None)) or True)
    )


# ══════════════════════════════════════════════════════════════════════════════
# api_sources.py — GET /api/sources/status
# ══════════════════════════════════════════════════════════════════════════════

def test_sources_status_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/sources/status?market=AE")
    handler._handle_sources_status()
    data, status, _ = _last(handler)
    assert status == 401
    assert data["ok"] is False


def test_sources_status_success_with_run_and_timeline_failure(monkeypatch):
    """A source with a recorded run reports its live status; a timeline build
    failure degrades to a 0 event count without failing the whole response."""
    import app.source_health_timeline as sht
    import app.source_readiness as sr
    import app.source_runs as srun

    _auth_as(monkeypatch, {"id": 5})
    src = {"source_id": "cbuae", "name": "CBUAE", "enabled": True,
           "category": "financial_regulator", "url": "https://c.example"}
    monkeypatch.setattr(sr, "load_market_sources", lambda market: [src])
    monkeypatch.setattr(
        srun, "latest_runs",
        lambda market, include_skipped=False: {
            "cbuae": {
                "change_status": "CHANGE_DETECTED",
                "timestamp_utc": "2026-07-01T00:00:00Z",
                "access_status": "ok",
                "extraction_quality": "GOOD",
                "normalized_hash": "abc",
                "proof_block_path": "/proof/x.json",
            }
        },
    )

    def _boom_timeline(source_id, org_id=None, limit=200):
        raise RuntimeError("timeline unavailable")

    monkeypatch.setattr(sht, "build_source_timeline", _boom_timeline)
    handler = _make_handler("GET", "/api/sources/status?market=ae")
    handler._visible_sources_for = lambda user, sources: sources  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 5  # type: ignore[method-assign]
    handler._handle_sources_status()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True
    row = data["sources"][0]
    assert row["change_status"] == "CHANGE_DETECTED"
    assert row["last_evidence_at"] == "2026-07-01T00:00:00Z"  # proof path present
    assert row["timeline_event_count"] == 0  # build failure degraded, not fatal
    assert data["last_run_at"] == "2026-07-01T00:00:00Z"
    assert data["summary"]["CHANGE_DETECTED"] == 1


def test_sources_status_internal_error_is_500(monkeypatch):
    import app.source_readiness as sr

    _auth_as(monkeypatch, {"id": 5})

    def _boom(market):
        raise RuntimeError("readiness exploded")

    monkeypatch.setattr(sr, "load_market_sources", _boom)
    handler = _make_handler("GET", "/api/sources/status")
    handler._handle_sources_status()
    data, status, _ = _last(handler)
    assert status == 500
    assert data["message"] == "Internal server error."


# ── GET /api/sources/timeline — limit-parse + generic error branches ──────────

def test_source_timeline_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/sources/timeline?source_id=cbuae")
    handler._handle_source_timeline_get()
    _, status, _ = _last(handler)
    assert status == 401


def test_source_timeline_bad_limit_defaults_and_succeeds(monkeypatch):
    """A non-integer ?limit= falls back to the default rather than erroring."""
    import app.source_health_timeline as sht

    _auth_as(monkeypatch, {"id": 1})
    seen = {}

    def _build(source_id, org_id=None, limit=100):
        seen["limit"] = limit
        return {"ok": True, "total_events": 0, "events": []}

    monkeypatch.setattr(sht, "build_source_timeline", _build)
    handler = _make_handler("GET", "/api/sources/timeline?source_id=cbuae&limit=notanint")
    handler._source_visible_to = lambda user, sid: True  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: None  # type: ignore[method-assign]
    handler._handle_source_timeline_get()
    data, status, _ = _last(handler)
    assert status == 200
    assert seen["limit"] == 100  # clamped default after the parse fallback


def test_source_timeline_generic_error_is_500(monkeypatch):
    import app.source_health_timeline as sht

    _auth_as(monkeypatch, {"id": 1})

    def _boom(source_id, org_id=None, limit=100):
        raise RuntimeError("index corrupt")

    monkeypatch.setattr(sht, "build_source_timeline", _boom)
    handler = _make_handler("GET", "/api/sources/timeline?source_id=cbuae")
    handler._source_visible_to = lambda user, sid: True  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: None  # type: ignore[method-assign]
    handler._handle_source_timeline_get()
    data, status, _ = _last(handler)
    assert status == 500
    assert data["message"] == "Internal server error."


# ── POST /api/source-test — rate-limit early return ───────────────────────────

def test_source_test_rate_limited_is_429(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/source-test", {"url": "https://ok.example"})
    _force_rate_limited(handler)
    handler._handle_source_test()
    _, status, _ = _last(handler)
    assert status == 429


# ── GET /api/custom-sources — list ────────────────────────────────────────────

def test_custom_sources_list_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/custom-sources")
    handler._handle_custom_sources_list()
    _, status, _ = _last(handler)
    assert status == 401


def test_custom_sources_list_returns_only_owned(monkeypatch):
    import app.source_intake as si

    _auth_as(monkeypatch, {"id": 44})
    monkeypatch.setattr(
        si, "load_sources_json",
        lambda: [
            {"source_id": "mine", "custom": True, "owner_user_id": 44},
            {"source_id": "theirs", "custom": True, "owner_user_id": 99},
            {"source_id": "legacy", "custom": True, "owner_user_id": None},
            {"source_id": "official", "custom": False},
        ],
    )
    handler = _make_handler("GET", "/api/custom-sources")
    handler._handle_custom_sources_list()
    data, status, _ = _last(handler)
    assert status == 200
    ids = [s["source_id"] for s in data["sources"]]
    assert ids == ["mine"]  # never another tenant's custom source, never legacy-unowned


def test_custom_sources_list_internal_error_is_500(monkeypatch):
    import app.source_intake as si

    _auth_as(monkeypatch, {"id": 44})

    def _boom():
        raise RuntimeError("intake read failed")

    monkeypatch.setattr(si, "load_sources_json", _boom)
    handler = _make_handler("GET", "/api/custom-sources")
    handler._handle_custom_sources_list()
    data, status, _ = _last(handler)
    assert status == 500
    assert "Failed to load custom sources" in data["message"]


# ── POST /api/custom-sources/discover ─────────────────────────────────────────

def test_custom_source_discover_rate_limited_is_429(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/custom-sources/discover", {"url": "https://x.example"})
    _force_rate_limited(handler)
    handler._handle_custom_source_discover()
    _, status, _ = _last(handler)
    assert status == 429


def test_custom_source_discover_empty_url_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/custom-sources/discover", {"url": "   "})
    handler._handle_custom_source_discover()
    data, status, _ = _last(handler)
    assert status == 400
    assert "URL is required" in data["message"]


def test_custom_source_discover_success(monkeypatch):
    import app.source_discovery as sd
    import app.source_tester as st

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(st, "validate_public_url", lambda url: (True, "ok"))
    monkeypatch.setattr(sd, "discover_source", lambda url, **kw: {"candidates": 3})
    handler = _make_handler("POST", "/api/custom-sources/discover", {"url": "https://x.example"})
    handler._handle_custom_source_discover()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True
    assert data["evidence_written"] is False  # discovery never seals evidence
    assert data["can_activate_monitoring"] is False


def test_custom_source_discover_internal_error_is_500(monkeypatch):
    import app.source_discovery as sd
    import app.source_tester as st

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(st, "validate_public_url", lambda url: (True, "ok"))

    def _boom(url, **kw):
        raise RuntimeError("discovery exploded")

    monkeypatch.setattr(sd, "discover_source", _boom)
    handler = _make_handler("POST", "/api/custom-sources/discover", {"url": "https://x.example"})
    handler._handle_custom_source_discover()
    data, status, _ = _last(handler)
    assert status == 500
    assert "Source discovery failed" in data["message"]


# ── POST /api/custom-sources/test ─────────────────────────────────────────────

def test_custom_source_test_rate_limited_is_429(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/custom-sources/test", {"url": "https://x.example"})
    _force_rate_limited(handler)
    handler._handle_custom_source_test()
    _, status, _ = _last(handler)
    assert status == 429


def test_custom_source_test_empty_url_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/custom-sources/test", {"url": ""})
    handler._handle_custom_source_test()
    data, status, _ = _last(handler)
    assert status == 400
    assert "URL is required" in data["message"]


def test_custom_source_test_blocked_url_is_400(monkeypatch):
    import app.source_tester as st

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(st, "validate_public_url", lambda url: (False, "private range"))
    handler = _make_handler("POST", "/api/custom-sources/test",
                            {"url": "http://169.254.169.254/"})
    handler._handle_custom_source_test()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["status"] == "BLOCKED"
    assert data["ok"] is False


def _full_intake_result() -> dict:
    """A run_source_intake result dict covering the fields the handler reads
    directly (non-.get keys must be present)."""
    return {
        "status": "CONFIRMED_ACCESSIBLE",
        "chars_normalized": 4200,
        "chars_raw": 8000,
        "pdf_chars": 0,
        "quality": "GOOD",
        "nav_shell_detected": False,
        "hash_collision": True,
        "notes": ["ok"],
        "normalized_hash": "hash-abc",
        "collision_source_id": "other-tenant-custom",
    }


def test_custom_source_test_success_hides_foreign_collision(monkeypatch):
    """The no-save test succeeds, but a hash collision against a source the
    caller cannot see must NOT disclose that source's id (tenancy oracle)."""
    import app.source_intake as si
    import app.source_tester as st

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(st, "validate_public_url", lambda url: (True, "ok"))
    monkeypatch.setattr(si, "load_sources_json", lambda: [])
    monkeypatch.setattr(si, "run_source_intake",
                        lambda source, all_sources, write_evidence: _full_intake_result())
    monkeypatch.setattr(
        si, "build_source_lab_contract",
        lambda result: {
            "can_save_for_validation": True,
            "can_activate_monitoring": False,
            "activation_readiness": "pending",
            "baseline_runs_completed": 0,
            "baseline_runs_required": 3,
        },
    )
    handler = _make_handler(
        "POST", "/api/custom-sources/test",
        {"url": "https://x.example", "content_selector": ".main",
         "wait_for_selector": "#ready", "expected_min_length": 500,
         "fetch_method": "playwright", "pdf_mode": True,
         "adapter_family": "html_listing", "adapter_name": "generic",
         "adapter_config": {"k": "v"}},
    )
    # The colliding source is NOT visible to this caller -> its id is scrubbed.
    handler._source_visible_to = lambda user, sid: False  # type: ignore[method-assign]
    handler._handle_custom_source_test()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True
    assert data["status"] == "CONFIRMED_ACCESSIBLE"
    assert data["hash_collision"] is True  # collision signal preserved
    assert data["collision_source_id"] == ""  # foreign source id withheld
    assert data["evidence_written"] is False


def test_custom_source_test_internal_error_is_500(monkeypatch):
    import app.source_intake as si
    import app.source_tester as st

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(st, "validate_public_url", lambda url: (True, "ok"))
    monkeypatch.setattr(si, "load_sources_json", lambda: [])

    def _boom(source, all_sources, write_evidence):
        raise RuntimeError("intake exploded")

    monkeypatch.setattr(si, "run_source_intake", _boom)
    handler = _make_handler("POST", "/api/custom-sources/test", {"url": "https://x.example"})
    handler._handle_custom_source_test()
    data, status, _ = _last(handler)
    assert status == 500
    assert "Source test failed" in data["message"]


# ── POST /api/custom-sources — add ────────────────────────────────────────────

def test_custom_sources_add_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("POST", "/api/custom-sources", {"url": "https://x.example"})
    handler._handle_custom_sources_add()
    _, status, _ = _last(handler)
    assert status == 401


def test_custom_sources_add_rate_limited_is_429(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/custom-sources", {"url": "https://x.example"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    _force_rate_limited(handler)
    handler._handle_custom_sources_add()
    _, status, _ = _last(handler)
    assert status == 429


def test_custom_sources_add_cap_check_failure_fails_closed_403(monkeypatch):
    """A broken plan-cap lookup must DENY (fail closed), never silently allow."""
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 1})

    def _boom(uid):
        raise RuntimeError("plan db down")

    monkeypatch.setattr(plan, "capabilities_for", _boom)
    handler = _make_handler("POST", "/api/custom-sources", {"url": "https://x.example"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._require_capability = lambda user, cap: True  # type: ignore[method-assign]
    handler._handle_custom_sources_add()
    data, status, _ = _last(handler)
    assert status == 403
    assert "custom-source limit" in data["message"]


def _prep_add_handler(monkeypatch, handler, cap=5, owned=0):
    """Stub the cap prefilter to PASS so add-body branches are reachable."""
    import app.plan as plan
    import app.source_intake as si

    monkeypatch.setattr(plan, "capabilities_for", lambda uid: {"custom_sources": cap})
    monkeypatch.setattr(si, "load_sources_json",
                        lambda: [{"custom": True, "owner_user_id": 1}] * owned)
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._require_capability = lambda user, capn: True  # type: ignore[method-assign]


def test_custom_sources_add_empty_url_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/custom-sources",
                            {"url": "  ", "legal_confirmed": True})
    _prep_add_handler(monkeypatch, handler)
    handler._handle_custom_sources_add()
    data, status, _ = _last(handler)
    assert status == 400
    assert "URL is required" in data["message"]


def test_custom_sources_add_requires_legal_confirmation(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/custom-sources",
                            {"url": "https://x.example", "legal_confirmed": False})
    _prep_add_handler(monkeypatch, handler)
    handler._handle_custom_sources_add()
    data, status, _ = _last(handler)
    assert status == 400
    assert "Legal confirmation is required" in data["message"]


def test_custom_sources_add_blocked_url_is_400(monkeypatch):
    import app.source_tester as st

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(st, "validate_public_url", lambda url: (False, "private range"))
    handler = _make_handler("POST", "/api/custom-sources",
                            {"url": "http://10.0.0.1/", "legal_confirmed": True})
    _prep_add_handler(monkeypatch, handler)
    handler._handle_custom_sources_add()
    data, status, _ = _last(handler)
    assert status == 400
    assert "URL blocked" in data["message"]


def test_custom_sources_add_readiness_not_confirmed_is_400(monkeypatch):
    import app.source_intake as si
    import app.source_tester as st

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(st, "validate_public_url", lambda url: (True, "ok"))
    monkeypatch.setattr(st, "source_url_exists_for_user", lambda url, uid: False)
    monkeypatch.setattr(
        si, "run_source_intake",
        lambda source, all_sources, write_evidence: {
            "status": "BLOCKED_HOST", "failure_reason": "bot wall",
            "remediation_hint": "try later",
        },
    )
    handler = _make_handler("POST", "/api/custom-sources",
                            {"url": "https://x.example", "legal_confirmed": True})
    _prep_add_handler(monkeypatch, handler)
    handler._handle_custom_sources_add()
    data, status, _ = _last(handler)
    assert status == 400
    assert "readiness test passes" in data["message"]
    assert data["readiness_status"] == "BLOCKED_HOST"


def test_custom_sources_add_append_conflict_is_409(monkeypatch):
    import app.plan as plan
    import app.source_intake as si
    import app.source_tester as st

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(st, "validate_public_url", lambda url: (True, "ok"))
    monkeypatch.setattr(st, "source_url_exists_for_user", lambda url, uid: False)
    monkeypatch.setattr(st, "append_source_to_json",
                        lambda src, owner_user_id, custom_cap: False)  # global uniqueness fails
    monkeypatch.setattr(
        si, "run_source_intake",
        lambda source, all_sources, write_evidence: {"status": "CONFIRMED_ACCESSIBLE"},
    )
    handler = _make_handler("POST", "/api/custom-sources",
                            {"url": "https://x.example", "legal_confirmed": True})
    _prep_add_handler(monkeypatch, handler)
    monkeypatch.setattr(plan, "capabilities_for", lambda uid: {"custom_sources": 5})
    handler._handle_custom_sources_add()
    data, status, _ = _last(handler)
    assert status == 409
    assert "could not be saved" in data["message"]


def test_custom_sources_add_success(monkeypatch):
    import app.plan as plan
    import app.source_intake as si
    import app.source_tester as st

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(st, "validate_public_url", lambda url: (True, "ok"))
    monkeypatch.setattr(st, "source_url_exists_for_user", lambda url, uid: False)
    saved = {}

    def _append(src, owner_user_id, custom_cap):
        saved["src"] = src
        saved["owner"] = owner_user_id
        return True

    monkeypatch.setattr(st, "append_source_to_json", _append)
    monkeypatch.setattr(
        si, "run_source_intake",
        lambda source, all_sources, write_evidence: {"status": "CONFIRMED_ACCESSIBLE"},
    )
    handler = _make_handler("POST", "/api/custom-sources",
                            {"url": "https://x.example", "name": "My Source",
                             "legal_confirmed": True})
    _prep_add_handler(monkeypatch, handler)
    monkeypatch.setattr(plan, "capabilities_for", lambda uid: {"custom_sources": 5})
    handler._handle_custom_sources_add()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True
    assert data["source_id"].startswith("custom-")
    assert saved["owner"] == 1  # tenancy stamp = creating user
    assert saved["src"]["enabled"] is False  # never active on creation


def test_custom_sources_add_internal_error_is_500(monkeypatch):
    import app.source_tester as st

    _auth_as(monkeypatch, {"id": 1})

    def _boom(url):
        raise RuntimeError("validator exploded")

    monkeypatch.setattr(st, "validate_public_url", _boom)
    handler = _make_handler("POST", "/api/custom-sources",
                            {"url": "https://x.example", "legal_confirmed": True})
    _prep_add_handler(monkeypatch, handler)
    handler._handle_custom_sources_add()
    data, status, _ = _last(handler)
    assert status == 500
    assert data["ok"] is False


# ══════════════════════════════════════════════════════════════════════════════
# api_reports.py — GET /api/reports/monthly-assurance
# ══════════════════════════════════════════════════════════════════════════════

def test_monthly_assurance_rate_limited_is_429(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/reports/monthly-assurance")
    _force_rate_limited(handler)
    handler._handle_monthly_assurance_report()
    _, status, _ = _last(handler)
    assert status == 429


def test_monthly_assurance_pdf_format_success(monkeypatch):
    import app.monthly_assurance_report as mar
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(plan, "has_capability", lambda uid, cap: True)
    monkeypatch.setattr(mar, "compute_monthly_stats", lambda sids, y, m: {"count": 1})
    monkeypatch.setattr(mar, "generate_monthly_report_pdf",
                        lambda stats, client_name: "/tmp/report.pdf")
    handler = _make_handler(
        "GET", "/api/reports/monthly-assurance?year=2026&month=7&format=pdf")
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_monthly_assurance_report()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["report_path"] == "/tmp/report.pdf"


def test_monthly_assurance_internal_error_is_500(monkeypatch):
    import app.monthly_assurance_report as mar
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(plan, "has_capability", lambda uid, cap: True)

    def _boom(sids, y, m):
        raise RuntimeError("stats exploded")

    monkeypatch.setattr(mar, "compute_monthly_stats", _boom)
    handler = _make_handler("GET", "/api/reports/monthly-assurance?year=2026&month=7")
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_monthly_assurance_report()
    data, status, _ = _last(handler)
    assert status == 500
    assert data["status"] == "error"


# ── GET /api/reports/coverage-certificate — format branches + errors ──────────

def test_coverage_certificate_rate_limited_is_429(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/reports/coverage-certificate")
    _force_rate_limited(handler)
    handler._handle_coverage_certificate()
    _, status, _ = _last(handler)
    assert status == 429


@pytest.mark.parametrize(
    "fmt,render_attr,payload_key",
    [
        ("json", None, "certificate"),
        ("html", "render_coverage_certificate_html", "report"),
    ],
)
def test_coverage_certificate_format_branches(monkeypatch, fmt, render_attr, payload_key):
    import app.coverage_certificate as cc

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(cc, "build_coverage_certificate", lambda **kw: {"cov": 1})
    if render_attr:
        monkeypatch.setattr(cc, render_attr, lambda cert: "RENDERED")
    handler = _make_handler(
        "GET",
        f"/api/reports/coverage-certificate?period_start=2026-07-01&period_end=2026-07-31&format={fmt}",
    )
    handler._entitle_source_ids = lambda user, ids: ids  # type: ignore[method-assign]
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_coverage_certificate()
    data, status, _ = _last(handler)
    assert status == 200
    assert payload_key in data


def test_coverage_certificate_pdf_requires_capability(monkeypatch):
    import app.coverage_certificate as cc
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(plan, "has_capability", lambda uid, cap: False)  # no pdf_export
    monkeypatch.setattr(cc, "enabled_source_ids", lambda: [])
    handler = _make_handler(
        "GET",
        "/api/reports/coverage-certificate?period_start=2026-07-01&period_end=2026-07-31&format=pdf",
    )
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    handler._handle_coverage_certificate()
    _, status, _ = _last(handler)
    assert status == 403  # paid PDF deliverable gated


def test_coverage_certificate_named_sources_are_entitlement_clipped(monkeypatch):
    import app.coverage_certificate as cc

    _auth_as(monkeypatch, {"id": 1})
    seen = {}

    def _build(**kw):
        seen["source_ids"] = kw["source_ids"]
        return {"cov": 1}

    monkeypatch.setattr(cc, "build_coverage_certificate", _build)
    monkeypatch.setattr(cc, "render_coverage_certificate_markdown", lambda cert: "# md")
    handler = _make_handler(
        "GET",
        "/api/reports/coverage-certificate?period_start=2026-07-01&period_end=2026-07-31"
        "&source_ids=mine,foreign",
    )
    handler._entitle_source_ids = lambda user, ids: ["mine"]  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_coverage_certificate()
    _, status, _ = _last(handler)
    assert status == 200
    assert seen["source_ids"] == ["mine"]  # foreign source clipped out


def test_coverage_certificate_value_error_is_400(monkeypatch):
    import app.coverage_certificate as cc

    _auth_as(monkeypatch, {"id": 1})

    def _bad(**kw):
        raise ValueError("period_start after period_end")

    monkeypatch.setattr(cc, "enabled_source_ids", lambda: [])
    monkeypatch.setattr(cc, "build_coverage_certificate", _bad)
    handler = _make_handler(
        "GET",
        "/api/reports/coverage-certificate?period_start=2026-07-31&period_end=2026-07-01",
    )
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_coverage_certificate()
    data, status, _ = _last(handler)
    assert status == 400
    assert "period_start after period_end" in data["message"]


def test_coverage_certificate_internal_error_is_500(monkeypatch):
    import app.coverage_certificate as cc

    _auth_as(monkeypatch, {"id": 1})

    def _boom(**kw):
        raise RuntimeError("builder exploded")

    monkeypatch.setattr(cc, "enabled_source_ids", lambda: [])
    monkeypatch.setattr(cc, "build_coverage_certificate", _boom)
    handler = _make_handler(
        "GET",
        "/api/reports/coverage-certificate?period_start=2026-07-01&period_end=2026-07-31",
    )
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_coverage_certificate()
    data, status, _ = _last(handler)
    assert status == 500
    assert data["status"] == "error"


# ── GET /api/calendar/effective-dates ─────────────────────────────────────────

def test_effective_dates_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/calendar/effective-dates")
    handler._handle_effective_dates_calendar()
    _, status, _ = _last(handler)
    assert status == 401


def test_effective_dates_rate_limited_is_429(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/calendar/effective-dates")
    _force_rate_limited(handler)
    handler._handle_effective_dates_calendar()
    _, status, _ = _last(handler)
    assert status == 429


def test_effective_dates_invalid_from_date_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/calendar/effective-dates?from=notadate")
    handler._handle_effective_dates_calendar()
    data, status, _ = _last(handler)
    assert status == 400
    assert "Invalid from/to date" in data["message"]


def test_effective_dates_invalid_days_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/calendar/effective-dates?days=lots")
    handler._handle_effective_dates_calendar()
    data, status, _ = _last(handler)
    assert status == 400
    assert "Invalid days" in data["message"]


def test_effective_dates_named_sources_none_in_scope_is_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler(
        "GET", "/api/calendar/effective-dates?source_ids=foreign")
    handler._entitle_source_ids = lambda user, ids: []  # type: ignore[method-assign]
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    handler._handle_effective_dates_calendar()
    data, status, _ = _last(handler)
    assert status == 403
    assert "plan scope" in data["message"]


def test_effective_dates_success_is_plan_redacted(monkeypatch):
    import app.effective_dates as ed

    _auth_as(monkeypatch, {"id": 7})
    monkeypatch.setattr(ed, "upcoming_key_dates", lambda **kw: {"items": [{"date": "2026-08-01"}]})
    redacted = {}

    def _redact(uid, result):
        redacted["uid"] = uid
        return {"items": [], "redacted": True}

    monkeypatch.setattr(api_reports, "redact_effective_dates_for_plan", _redact)
    handler = _make_handler("GET", "/api/calendar/effective-dates?days=30")
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_effective_dates_calendar()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True
    assert data["redacted"] is True  # routed through the plan redaction choke point
    assert redacted["uid"] == 7


def test_effective_dates_internal_error_is_500(monkeypatch):
    import app.effective_dates as ed

    _auth_as(monkeypatch, {"id": 7})

    def _boom(**kw):
        raise RuntimeError("dates exploded")

    monkeypatch.setattr(ed, "upcoming_key_dates", _boom)
    handler = _make_handler("GET", "/api/calendar/effective-dates?days=30")
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_effective_dates_calendar()
    data, status, _ = _last(handler)
    assert status == 500
    assert data["ok"] is False


# ── GET /api/digest/assurance-preview ─────────────────────────────────────────

def test_assurance_digest_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/digest/assurance-preview")
    handler._handle_assurance_digest_preview()
    _, status, _ = _last(handler)
    assert status == 401


def test_assurance_digest_rate_limited_is_429(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/digest/assurance-preview")
    _force_rate_limited(handler)
    handler._handle_assurance_digest_preview()
    _, status, _ = _last(handler)
    assert status == 429


def test_assurance_digest_success_default_scope(monkeypatch):
    import app.assurance_digest as ad
    import app.coverage_certificate as cc

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(cc, "enabled_source_ids", lambda: ["mine", "denied"])
    seen = {}

    def _build(**kw):
        seen["source_ids"] = kw["source_ids"]
        return {"digest": True}

    monkeypatch.setattr(ad, "build_assurance_digest", _build)
    monkeypatch.setattr(ad, "render_assurance_digest_markdown", lambda d: "# md")
    monkeypatch.setattr(ad, "render_assurance_digest_email_text", lambda d: "email")
    handler = _make_handler("GET", "/api/digest/assurance-preview?days=7")
    handler._denied_custom_source_ids = lambda user: {"denied"}  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_assurance_digest_preview()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True
    assert data["markdown"] == "# md"
    assert data["email_text"] == "email"
    assert seen["source_ids"] == ["mine"]  # denied custom source excluded from default scope


def test_assurance_digest_named_scope_entitlement_clipped(monkeypatch):
    import app.assurance_digest as ad

    _auth_as(monkeypatch, {"id": 1})
    seen = {}

    def _build(**kw):
        seen["source_ids"] = kw["source_ids"]
        return {"digest": True}

    monkeypatch.setattr(ad, "build_assurance_digest", _build)
    monkeypatch.setattr(ad, "render_assurance_digest_markdown", lambda d: "# md")
    monkeypatch.setattr(ad, "render_assurance_digest_email_text", lambda d: "email")
    handler = _make_handler(
        "GET",
        "/api/digest/assurance-preview?period_start=2026-07-01&period_end=2026-07-07"
        "&source_ids=mine,foreign&format=markdown",
    )
    handler._entitle_source_ids = lambda user, ids: ["mine"]  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_assurance_digest_preview()
    data, status, _ = _last(handler)
    assert status == 200
    assert seen["source_ids"] == ["mine"]
    assert "email_text" not in data  # format=markdown omits the email body


def test_assurance_digest_value_error_is_400(monkeypatch):
    import app.assurance_digest as ad
    import app.coverage_certificate as cc

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(cc, "enabled_source_ids", lambda: [])

    def _bad(**kw):
        raise ValueError("forbidden claim detected")

    monkeypatch.setattr(ad, "build_assurance_digest", _bad)
    handler = _make_handler("GET", "/api/digest/assurance-preview?days=7")
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_assurance_digest_preview()
    data, status, _ = _last(handler)
    assert status == 400
    assert "forbidden claim detected" in data["message"]


def test_assurance_digest_internal_error_is_500(monkeypatch):
    import app.assurance_digest as ad
    import app.coverage_certificate as cc

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(cc, "enabled_source_ids", lambda: [])

    def _boom(**kw):
        raise RuntimeError("digest exploded")

    monkeypatch.setattr(ad, "build_assurance_digest", _boom)
    handler = _make_handler("GET", "/api/digest/assurance-preview?days=7")
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_assurance_digest_preview()
    data, status, _ = _last(handler)
    assert status == 500
    assert data["ok"] is False


# ── POST /api/canonical-evidence/review — defensive body-None branch ──────────

def test_canonical_review_null_body_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/canonical-evidence/review", {})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._read_json_strict = lambda: (None, None)  # type: ignore[method-assign]
    handler._handle_canonical_evidence_review_action()
    data, status, _ = _last(handler)
    assert status == 400
    assert "Request body required" in data["message"]


# ── POST /api/audit-vault — read/validate/error branches ──────────────────────

def test_audit_vault_rate_limited_is_429(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/audit-vault", {"source_ids": ["s1"]})
    _force_rate_limited(handler)
    handler._handle_audit_vault()
    _, status, _ = _last(handler)
    assert status == 429


def test_audit_vault_invalid_json_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/audit-vault", raw=b"{not valid json")
    handler._handle_audit_vault()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "Invalid JSON."


def test_audit_vault_null_body_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/audit-vault", {})
    handler._read_json_strict = lambda: (None, None)  # type: ignore[method-assign]
    handler._handle_audit_vault()
    data, status, _ = _last(handler)
    assert status == 400
    assert "Request body required" in data["message"]


def test_audit_vault_invalid_date_range_is_400(monkeypatch):
    import app.audit_export as ax

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(ax, "validate_source_ids", lambda ids: (True, ""))
    monkeypatch.setattr(ax, "validate_date_range", lambda a, b: (False, "date_from after date_to"))
    handler = _make_handler("POST", "/api/audit-vault",
                            {"source_ids": ["s1"], "date_from": "2026-05-01", "date_to": "2026-01-01"})
    handler._require_capability = lambda user, cap: True  # type: ignore[method-assign]
    handler._handle_audit_vault()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "date_from after date_to"


def test_audit_vault_builder_exception_is_500(monkeypatch):
    import app.audit_export as ax

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(ax, "validate_source_ids", lambda ids: (True, ""))
    monkeypatch.setattr(ax, "validate_date_range", lambda a, b: (True, ""))

    def _boom(sids, df, dt):
        raise RuntimeError("vault exploded")

    monkeypatch.setattr(ax, "build_period_audit_vault", _boom)
    handler = _make_handler("POST", "/api/audit-vault",
                            {"source_ids": ["s1"], "date_from": "2026-01-01", "date_to": "2026-02-01"})
    handler._require_capability = lambda user, cap: True  # type: ignore[method-assign]
    handler._entitle_source_ids = lambda user, ids: ["s1"]  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_audit_vault()
    data, status, _ = _last(handler)
    assert status == 500
    assert data["message"] == "Internal server error."


# ── POST /api/evidence/pack — read/validate/error branches ────────────────────

def test_evidence_pack_invalid_json_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/evidence/pack", raw=b"{broken")
    handler._handle_evidence_pack()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "Invalid JSON."


def test_evidence_pack_null_body_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/evidence/pack", {})
    handler._read_json_strict = lambda: (None, None)  # type: ignore[method-assign]
    handler._handle_evidence_pack()
    data, status, _ = _last(handler)
    assert status == 400
    assert "Request body required" in data["message"]


def test_evidence_pack_invalid_date_range_is_400(monkeypatch):
    import app.audit_export as ax

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(ax, "validate_source_ids", lambda ids: (True, ""))
    monkeypatch.setattr(ax, "validate_date_range", lambda a, b: (False, "bad range"))
    handler = _make_handler("POST", "/api/evidence/pack",
                            {"source_ids": ["s1"], "date_from": "x", "date_to": "y"})
    handler._require_capability = lambda user, cap: True  # type: ignore[method-assign]
    handler._handle_evidence_pack()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "bad range"


def test_evidence_pack_builder_exception_is_500(monkeypatch):
    import app.audit_export as ax
    import app.evidence_pack as ep

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(ax, "validate_source_ids", lambda ids: (True, ""))
    monkeypatch.setattr(ax, "validate_date_range", lambda a, b: (True, ""))

    def _boom(sids, df, dt):
        raise RuntimeError("pack exploded")

    monkeypatch.setattr(ep, "build_evidence_pack", _boom)
    handler = _make_handler("POST", "/api/evidence/pack",
                            {"source_ids": ["s1"], "date_from": "2026-01-01", "date_to": "2026-02-01"})
    handler._require_capability = lambda user, cap: True  # type: ignore[method-assign]
    handler._entitle_source_ids = lambda user, ids: ["s1"]  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_evidence_pack()
    data, status, _ = _last(handler)
    assert status == 500
    assert data["message"] == "Internal server error."


# ── POST /api/reports/regulator-binder ────────────────────────────────────────

def test_regulator_binder_rate_limited_is_429(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/reports/regulator-binder", {"source_ids": ["s1"]})
    _force_rate_limited(handler)
    handler._handle_regulator_binder()
    _, status, _ = _last(handler)
    assert status == 429


def test_regulator_binder_invalid_json_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/reports/regulator-binder", raw=b"{oops")
    handler._handle_regulator_binder()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "Invalid JSON."


def test_regulator_binder_null_body_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/reports/regulator-binder", {})
    handler._read_json_strict = lambda: (None, None)  # type: ignore[method-assign]
    handler._handle_regulator_binder()
    data, status, _ = _last(handler)
    assert status == 400
    assert "Request body required" in data["message"]


def test_regulator_binder_invalid_source_ids_is_400(monkeypatch):
    import app.audit_export as ax

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(ax, "validate_source_ids", lambda ids: (False, "source_ids required"))
    handler = _make_handler("POST", "/api/reports/regulator-binder", {"source_ids": []})
    handler._handle_regulator_binder()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "source_ids required"


def test_regulator_binder_capability_denied_403(monkeypatch):
    import app.audit_export as ax
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(ax, "validate_source_ids", lambda ids: (True, ""))
    monkeypatch.setattr(plan, "has_capability", lambda uid, cap: False)
    handler = _make_handler("POST", "/api/reports/regulator-binder", {"source_ids": ["s1"]})
    handler._handle_regulator_binder()
    _, status, _ = _last(handler)
    assert status == 403


def test_regulator_binder_invalid_date_range_is_400(monkeypatch):
    import app.audit_export as ax

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(ax, "validate_source_ids", lambda ids: (True, ""))
    monkeypatch.setattr(ax, "validate_date_range", lambda a, b: (False, "bad range"))
    handler = _make_handler("POST", "/api/reports/regulator-binder",
                            {"source_ids": ["s1"], "date_from": "x", "date_to": "y"})
    handler._require_capability = lambda user, cap: True  # type: ignore[method-assign]
    handler._handle_regulator_binder()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "bad range"


def test_regulator_binder_missing_generated_file_is_500(monkeypatch):
    import app.audit_export as ax
    import app.regulator_binder as rb

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(ax, "validate_source_ids", lambda ids: (True, ""))
    monkeypatch.setattr(ax, "validate_date_range", lambda a, b: (True, ""))
    monkeypatch.setattr(
        rb, "build_regulator_binder",
        lambda sids, df, dt: {"status": "ok", "binder_path": "/nonexistent/binder.zip"},
    )
    handler = _make_handler("POST", "/api/reports/regulator-binder",
                            {"source_ids": ["s1"], "date_from": "2026-01-01", "date_to": "2026-02-01"})
    handler._require_capability = lambda user, cap: True  # type: ignore[method-assign]
    handler._entitle_source_ids = lambda user, ids: ["s1"]  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_regulator_binder()
    data, status, _ = _last(handler)
    assert status == 500
    assert "not generated" in data["message"]


def test_regulator_binder_builder_exception_is_500(monkeypatch):
    import app.audit_export as ax
    import app.regulator_binder as rb

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(ax, "validate_source_ids", lambda ids: (True, ""))
    monkeypatch.setattr(ax, "validate_date_range", lambda a, b: (True, ""))

    def _boom(sids, df, dt):
        raise RuntimeError("binder exploded")

    monkeypatch.setattr(rb, "build_regulator_binder", _boom)
    handler = _make_handler("POST", "/api/reports/regulator-binder",
                            {"source_ids": ["s1"], "date_from": "2026-01-01", "date_to": "2026-02-01"})
    handler._require_capability = lambda user, cap: True  # type: ignore[method-assign]
    handler._entitle_source_ids = lambda user, ids: ["s1"]  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_regulator_binder()
    data, status, _ = _last(handler)
    assert status == 500
    assert data["message"] == "Internal server error."


# ── POST /api/reports/change-register — auth / read / error branches ──────────

def test_change_register_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("POST", "/api/reports/change-register", {})
    handler._handle_change_register_export()
    _, status, _ = _last(handler)
    assert status == 401


def test_change_register_rate_limited_is_429(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/reports/change-register", {})
    _force_rate_limited(handler)
    handler._handle_change_register_export()
    _, status, _ = _last(handler)
    assert status == 429


def test_change_register_invalid_json_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/reports/change-register", raw=b"{nope")
    handler._handle_change_register_export()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "Invalid JSON."


def test_change_register_null_body_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/reports/change-register", {})
    handler._read_json_strict = lambda: (None, None)  # type: ignore[method-assign]
    handler._handle_change_register_export()
    data, status, _ = _last(handler)
    assert status == 400
    assert "Request body required" in data["message"]


def test_change_register_builder_error_is_400(monkeypatch):
    import app.change_register as cr
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(plan, "has_capability", lambda uid, cap: True)
    monkeypatch.setattr(cr, "validate_register_date_range", lambda a, b: (True, ""))
    monkeypatch.setattr(cr, "build_change_register_export",
                        lambda **kw: {"status": "error", "message": "bad filter"})
    handler = _make_handler("POST", "/api/reports/change-register", {})
    handler._entitle_source_ids = lambda user, ids: ids  # type: ignore[method-assign]
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: None  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_change_register_export()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["ok"] is False
    assert data["message"] == "bad filter"


def test_change_register_builder_exception_is_500(monkeypatch):
    import app.change_register as cr
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(plan, "has_capability", lambda uid, cap: True)
    monkeypatch.setattr(cr, "validate_register_date_range", lambda a, b: (True, ""))

    def _boom(**kw):
        raise RuntimeError("register exploded")

    monkeypatch.setattr(cr, "build_change_register_export", _boom)
    handler = _make_handler("POST", "/api/reports/change-register", {})
    handler._entitle_source_ids = lambda user, ids: ids  # type: ignore[method-assign]
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: None  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_change_register_export()
    data, status, _ = _last(handler)
    assert status == 500
