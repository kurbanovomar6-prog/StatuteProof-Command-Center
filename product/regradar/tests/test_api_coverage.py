"""Behavioral coverage for previously-untested ``app/api.py`` handlers.

This file extends ``tests/test_api_coverage_uplift.py`` — it reuses that file's
real-``_Handler`` harness (``_make_handler`` / ``_last`` / ``_auth_as``) and the
same monkeypatch-at-the-``app.api``-boundary discipline — but targets a
different set of read/write handlers that the uplift file did not exercise:

  * GET  /api/auth/me, /api/auth/google/status      — session read + config probe
  * GET/POST /api/alerts/action-log                 — per-alert review decisions
  * GET/POST/PUT /api/alerts/checklist              — the owner-scoped to-do list
  * GET  /api/sources/summary                       — cross-tenant count aggregate
  * GET  /api/sources/timeline                      — source-visibility 404 gate
  * GET  /api/evidence/review(+history)             — IDOR 403 scope gate
  * POST /api/evidence/assess                       — review-write IDOR gate
  * GET  /api/reviews/queue, /api/canonical-evidence
  * GET  /api/audit-log                             — owner-only + fail-closed org
  * GET  /api/reports/monthly-assurance, coverage-certificate
  * POST /api/audit-vault, /api/evidence/pack, /api/reports/change-register

Every test asserts REAL behavior (status codes, denials, value mapping). All
network / heavy builders are monkeypatched at their import boundary, so no
network, no PDF/ZIP generation, and no real plan DB is touched on mocked paths.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api as api
import app.api_alerts as api_alerts
import app.api_auth as api_auth
from app.api import _Handler

# Reuse the proven harness from the sibling uplift suite (pytest "prepend"
# import mode puts tests/ on sys.path, so this bare import resolves).
from test_api_coverage_uplift import _auth_as, _last, _make_handler  # noqa: E402


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/auth/me + /api/auth/google/status
# ══════════════════════════════════════════════════════════════════════════════

def test_auth_me_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/auth/me")
    handler._handle_auth_me()
    data, status, _ = _last(handler)
    assert status == 401
    assert data["ok"] is False


def test_auth_me_returns_public_user(monkeypatch):
    _auth_as(monkeypatch, {"id": 12, "email": "u@e.com", "password_hash": "SECRET"})
    monkeypatch.setattr(api_auth, "make_public_user", lambda u: {"id": u["id"], "email": u["email"]})
    handler = _make_handler("GET", "/api/auth/me")
    handler._handle_auth_me()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["user"] == {"id": 12, "email": "u@e.com"}
    assert "password_hash" not in data["user"]  # never leak the hash


@pytest.mark.parametrize("available", [True, False])
def test_google_status_reflects_configuration(monkeypatch, available):
    monkeypatch.setattr(api_auth, "google_oauth_available", lambda: available)
    handler = _make_handler("GET", "/api/auth/google/status")
    handler._handle_auth_google_status()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["available"] is available


# ══════════════════════════════════════════════════════════════════════════════
# GET/POST /api/alerts/action-log — per-alert act/monitor/no_action decisions
# ══════════════════════════════════════════════════════════════════════════════

def test_action_log_get_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/alerts/action-log?alert_id=a1")
    handler._handle_alert_action_log_get()
    _, status, _ = _last(handler)
    assert status == 401


def test_action_log_get_missing_alert_id_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/alerts/action-log")
    handler._handle_alert_action_log_get()
    data, status, _ = _last(handler)
    assert status == 400
    assert "alert_id required" in data["message"]


def test_action_log_get_scopes_to_caller(monkeypatch):
    seen = {}

    def _get(uid, alert_id):
        seen["args"] = (uid, alert_id)
        return [{"decision": "monitor"}]

    _auth_as(monkeypatch, {"id": 44})
    monkeypatch.setattr(api_alerts, "get_action_log", _get)
    handler = _make_handler("GET", "/api/alerts/action-log?alert_id=alert-9")
    handler._handle_alert_action_log_get()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["entries"] == [{"decision": "monitor"}]
    assert seen["args"] == (44, "alert-9")  # never another tenant's log


def test_action_log_post_rbac_denied_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/alerts/action-log",
                            {"alert_id": "a1", "decision": "act"})
    handler._rbac_guard = lambda user, action, **kw: (  # type: ignore[method-assign]
        handler._sent.append(({"ok": False}, 403, None)) or False
    )
    handler._handle_alert_action_log_post()
    _, status, _ = _last(handler)
    assert status == 403


def test_action_log_post_missing_alert_id_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/alerts/action-log", {"decision": "act"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_alert_action_log_post()
    data, status, _ = _last(handler)
    assert status == 400
    assert "alert_id required" in data["message"]


def test_action_log_post_invalid_decision_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/alerts/action-log",
                            {"alert_id": "a1", "decision": "explode"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_alert_action_log_post()
    data, status, _ = _last(handler)
    assert status == 400
    assert "act, monitor, or no_action" in data["message"]


def test_action_log_post_save_failure_is_500(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(api_alerts, "save_action_log_entry", lambda *a, **k: None)
    handler = _make_handler("POST", "/api/alerts/action-log",
                            {"alert_id": "a1", "decision": "act"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_alert_action_log_post()
    _, status, _ = _last(handler)
    assert status == 500


def test_action_log_post_success_is_201_and_scoped(monkeypatch):
    seen = {}

    def _save(uid, alert_id, decision, notes, reviewer):
        seen["args"] = (uid, alert_id, decision)
        return {"id": 1, "decision": decision}

    _auth_as(monkeypatch, {"id": 88})
    monkeypatch.setattr(api_alerts, "save_action_log_entry", _save)
    handler = _make_handler("POST", "/api/alerts/action-log",
                            {"alert_id": "a1", "decision": "no_action", "notes": "x"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_alert_action_log_post()
    data, status, _ = _last(handler)
    assert status == 201
    assert data["entry"]["decision"] == "no_action"
    assert seen["args"] == (88, "a1", "no_action")


# ══════════════════════════════════════════════════════════════════════════════
# GET/POST/PUT /api/alerts/checklist — owner-scoped review to-do list
# ══════════════════════════════════════════════════════════════════════════════

def test_checklist_get_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/alerts/checklist?alert_id=a1")
    handler._handle_alert_checklist_get()
    _, status, _ = _last(handler)
    assert status == 401


def test_checklist_get_invalid_alert_id_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(api_alerts, "checklist_valid_alert_id", lambda aid: False)
    handler = _make_handler("GET", "/api/alerts/checklist?alert_id=@@@")
    handler._handle_alert_checklist_get()
    data, status, _ = _last(handler)
    assert status == 400
    assert "Invalid alert_id" in data["message"]


def test_checklist_get_scopes_to_caller_and_returns_framing(monkeypatch):
    seen = {}

    def _list(uid, alert_id):
        seen["args"] = (uid, alert_id)
        return [{"id": 1, "text": "call MLRO"}]

    _auth_as(monkeypatch, {"id": 33})
    monkeypatch.setattr(api_alerts, "checklist_valid_alert_id", lambda aid: True)
    monkeypatch.setattr(api_alerts, "list_checklist_items", _list)
    monkeypatch.setattr(api_alerts, "CHECKLIST_FRAMING", {"note": "your words"})
    handler = _make_handler("GET", "/api/alerts/checklist?alert_id=a1")
    handler._handle_alert_checklist_get()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["items"][0]["text"] == "call MLRO"
    assert data["framing"] == {"note": "your words"}
    assert seen["args"] == (33, "a1")


def test_checklist_add_empty_text_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(api_alerts, "checklist_valid_alert_id", lambda aid: True)
    handler = _make_handler("POST", "/api/alerts/checklist",
                            {"alert_id": "a1", "text": "   "})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_alert_checklist_add()
    data, status, _ = _last(handler)
    assert status == 400
    assert "review action is required" in data["message"]


def test_checklist_add_full_list_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(api_alerts, "checklist_valid_alert_id", lambda aid: True)
    monkeypatch.setattr(api_alerts, "add_checklist_item", lambda *a, **k: None)
    handler = _make_handler("POST", "/api/alerts/checklist",
                            {"alert_id": "a1", "text": "do the thing"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_alert_checklist_add()
    data, status, _ = _last(handler)
    assert status == 400
    assert "checklist may be full" in data["message"]


def test_checklist_add_success_is_201_and_scoped(monkeypatch):
    seen = {}

    def _add(uid, alert_id, text, assignee, due_date):
        seen["args"] = (uid, alert_id, text)
        return {"id": 5, "text": text}

    _auth_as(monkeypatch, {"id": 77})
    monkeypatch.setattr(api_alerts, "checklist_valid_alert_id", lambda aid: True)
    monkeypatch.setattr(api_alerts, "add_checklist_item", _add)
    handler = _make_handler("POST", "/api/alerts/checklist",
                            {"alert_id": "a1", "text": "file SAR"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_alert_checklist_add()
    data, status, _ = _last(handler)
    assert status == 201
    assert data["item"]["text"] == "file SAR"
    assert seen["args"] == (77, "a1", "file SAR")


def test_checklist_update_invalid_item_id_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("PUT", "/api/alerts/checklist",
                            {"item_id": "not-an-int", "status": "done"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_alert_checklist_update()
    data, status, _ = _last(handler)
    assert status == 400
    assert "Invalid item_id" in data["message"]


def test_checklist_update_delete_success(monkeypatch):
    seen = {}

    def _del(uid, item_id):
        seen["args"] = (uid, item_id)
        return True

    _auth_as(monkeypatch, {"id": 9})
    monkeypatch.setattr(api_alerts, "delete_checklist_item", _del)
    handler = _make_handler("PUT", "/api/alerts/checklist",
                            {"item_id": 3, "delete": True})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_alert_checklist_update()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["deleted"] == 3
    assert seen["args"] == (9, 3)  # only the caller's item is deleted


def test_checklist_update_delete_not_found_is_404(monkeypatch):
    _auth_as(monkeypatch, {"id": 9})
    monkeypatch.setattr(api_alerts, "delete_checklist_item", lambda uid, iid: False)
    handler = _make_handler("PUT", "/api/alerts/checklist",
                            {"item_id": 3, "delete": True})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_alert_checklist_update()
    _, status, _ = _last(handler)
    assert status == 404  # cross-user probe gets no oracle


def test_checklist_update_nothing_to_update_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 9})
    handler = _make_handler("PUT", "/api/alerts/checklist", {"item_id": 3})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_alert_checklist_update()
    data, status, _ = _last(handler)
    assert status == 400
    assert "Nothing to update" in data["message"]


def test_checklist_update_not_found_is_404(monkeypatch):
    _auth_as(monkeypatch, {"id": 9})
    monkeypatch.setattr(api_alerts, "update_checklist_item", lambda uid, iid, **kw: None)
    handler = _make_handler("PUT", "/api/alerts/checklist",
                            {"item_id": 3, "status": "done"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_alert_checklist_update()
    _, status, _ = _last(handler)
    assert status == 404


def test_checklist_update_success_passes_only_supplied_fields(monkeypatch):
    seen = {}

    def _upd(uid, item_id, **kwargs):
        seen["kwargs"] = kwargs
        return {"id": item_id, **kwargs}

    _auth_as(monkeypatch, {"id": 9})
    monkeypatch.setattr(api_alerts, "update_checklist_item", _upd)
    handler = _make_handler("PUT", "/api/alerts/checklist",
                            {"item_id": 3, "status": "done"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._handle_alert_checklist_update()
    data, status, _ = _last(handler)
    assert status == 200
    # immutable-by-omission: assignee/text/due_date were NOT supplied, so absent.
    assert seen["kwargs"] == {"status": "done"}


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/sources/summary — cross-tenant count aggregate
# ══════════════════════════════════════════════════════════════════════════════

def test_sources_summary_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/sources/summary")
    handler._handle_sources_summary()
    _, status, _ = _last(handler)
    assert status == 401


def test_sources_summary_excludes_denied_custom_sources(monkeypatch):
    import app.source_summary as ss

    seen = {}

    def _build(market, excluded_source_ids):
        seen["market"] = market
        seen["excluded"] = excluded_source_ids
        return {"ok": True, "market": market, "total": 5}

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(ss, "build_sources_summary", _build)
    handler = _make_handler("GET", "/api/sources/summary?market=ae")
    handler._denied_custom_source_ids = lambda user: {"other-tenant"}  # type: ignore[method-assign]
    handler._handle_sources_summary()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["market"] == "AE"  # upper-cased
    assert seen["excluded"] == {"other-tenant"}  # cross-tenant exclusion propagated


def test_sources_summary_internal_error_is_500(monkeypatch):
    import app.source_summary as ss

    _auth_as(monkeypatch, {"id": 1})

    def _boom(market, excluded_source_ids):
        raise RuntimeError("summary store down")

    monkeypatch.setattr(ss, "build_sources_summary", _boom)
    handler = _make_handler("GET", "/api/sources/summary")
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    handler._handle_sources_summary()
    _, status, _ = _last(handler)
    assert status == 500


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/sources/timeline — source-visibility 404 gate (no existence oracle)
# ══════════════════════════════════════════════════════════════════════════════

def test_source_timeline_missing_id_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/sources/timeline")
    handler._handle_source_timeline_get()
    data, status, _ = _last(handler)
    assert status == 400
    assert "source_id is required" in data["message"]


def test_source_timeline_other_tenant_source_is_404(monkeypatch):
    """A source the caller cannot see returns 404 (never 403) — no existence oracle."""
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/sources/timeline?source_id=secret-custom")
    handler._source_visible_to = lambda user, sid: False  # type: ignore[method-assign]
    handler._handle_source_timeline_get()
    data, status, _ = _last(handler)
    assert status == 404
    assert "Source not found" in data["message"]


def test_source_timeline_success(monkeypatch):
    import app.source_health_timeline as sht

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(sht, "build_source_timeline",
                        lambda sid, org_id, limit: {"ok": True, "source_id": sid, "limit": limit})
    handler = _make_handler("GET", "/api/sources/timeline?source_id=cbuae&limit=999")
    handler._source_visible_to = lambda user, sid: True  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 7  # type: ignore[method-assign]
    handler._handle_source_timeline_get()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["source_id"] == "cbuae"
    assert data["limit"] == 200  # clamped to the 200 ceiling


def test_source_timeline_value_error_is_400(monkeypatch):
    import app.source_health_timeline as sht

    _auth_as(monkeypatch, {"id": 1})

    def _boom(sid, org_id, limit):
        raise ValueError("bad source")

    monkeypatch.setattr(sht, "build_source_timeline", _boom)
    handler = _make_handler("GET", "/api/sources/timeline?source_id=x")
    handler._source_visible_to = lambda user, sid: True  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: None  # type: ignore[method-assign]
    handler._handle_source_timeline_get()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "bad source"


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/evidence/review + review-history — IDOR 403 scope gate
# ══════════════════════════════════════════════════════════════════════════════

def test_evidence_review_missing_id_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/evidence/review")
    handler._handle_evidence_review_get()
    data, status, _ = _last(handler)
    assert status == 400
    assert "evidence_record_id is required" in data["message"]


def test_evidence_review_out_of_scope_is_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/evidence/review?evidence_record_id=other-tenant")
    handler._evidence_source_out_of_scope = lambda user, eid: True  # type: ignore[method-assign]
    handler._handle_evidence_review_get()
    data, status, _ = _last(handler)
    assert status == 403
    assert "not in your scope" in data["message"]


def test_evidence_review_success(monkeypatch):
    import app.evidence_assessment as ea

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(ea, "latest_assessment_for",
                        lambda eid, org_id: {"impact_level": "high"})
    handler = _make_handler("GET", "/api/evidence/review?run_id=r1")
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 4  # type: ignore[method-assign]
    handler._handle_evidence_review_get()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["assessment"]["impact_level"] == "high"
    assert data["evidence_record_id"] == "r1"


def test_evidence_review_history_out_of_scope_is_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("GET", "/api/evidence/review-history?run_id=other")
    handler._evidence_source_out_of_scope = lambda user, eid: True  # type: ignore[method-assign]
    handler._handle_evidence_review_history_get()
    _, status, _ = _last(handler)
    assert status == 403


def test_evidence_review_history_success(monkeypatch):
    import app.source_health_timeline as sht

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(sht, "build_evidence_review_history",
                        lambda eid, org_id: {"ok": True, "history": []})
    handler = _make_handler("GET", "/api/evidence/review-history?run_id=r1")
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 4  # type: ignore[method-assign]
    handler._handle_evidence_review_history_get()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/evidence/assess — review-write IDOR gate
# ══════════════════════════════════════════════════════════════════════════════

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


def test_evidence_assess_out_of_scope_is_403(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler("POST", "/api/evidence/assess",
                            {"evidence_record_id": "other-tenant", "impact_level": "high"})
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
    handler = _make_handler("POST", "/api/evidence/assess",
                            {"evidence_record_id": "r1"})
    handler._rbac_guard = lambda user, action, **kw: True  # type: ignore[method-assign]
    handler._evidence_source_out_of_scope = lambda user, eid: False  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 1  # type: ignore[method-assign]
    handler._handle_evidence_assess()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "impact_level is required"


def test_evidence_assess_success_is_201(monkeypatch):
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
    handler._caller_org_id = lambda user: 2  # type: ignore[method-assign]
    handler._handle_evidence_assess()
    data, status, _ = _last(handler)
    assert status == 201
    assert data["assessment"]["impact_level"] == "high"
    assert seen["kwargs"]["reviewer_user_id"] == 55  # attributed to the caller


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/reviews/queue + /api/canonical-evidence
# ══════════════════════════════════════════════════════════════════════════════

def test_reviews_queue_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/reviews/queue")
    handler._handle_reviews_queue_get()
    _, status, _ = _last(handler)
    assert status == 401


def test_reviews_queue_success_propagates_tenancy_scope(monkeypatch):
    import app.review_queue as rq

    seen = {}

    def _build(**kwargs):
        seen["kwargs"] = kwargs
        return {"ok": True, "queue": []}

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(rq, "build_review_queue", _build)
    handler = _make_handler("GET", "/api/reviews/queue?limit=oops")
    handler._denied_custom_source_ids = lambda user: {"denied-src"}  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 3  # type: ignore[method-assign]
    handler._handle_reviews_queue_get()
    data, status, _ = _last(handler)
    assert status == 200
    assert seen["kwargs"]["excluded_source_ids"] == {"denied-src"}
    assert seen["kwargs"]["org_id"] == 3
    assert seen["kwargs"]["limit"] == 50  # non-int limit falls back to default


def test_reviews_queue_internal_error_is_500(monkeypatch):
    import app.review_queue as rq

    _auth_as(monkeypatch, {"id": 1})

    def _boom(**kwargs):
        raise RuntimeError("queue down")

    monkeypatch.setattr(rq, "build_review_queue", _boom)
    handler = _make_handler("GET", "/api/reviews/queue")
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: None  # type: ignore[method-assign]
    handler._handle_reviews_queue_get()
    _, status, _ = _last(handler)
    assert status == 500


def test_canonical_evidence_get_success(monkeypatch):
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


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/audit-log — owner-only + fail-closed on unresolved org
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
    monkeypatch.setattr(api.rbac_runtime, "resolve_principal",
                        lambda user: _FakePrincipal("auditor", 5))
    handler = _make_handler("GET", "/api/audit-log")
    handler._handle_audit_log_get()
    data, status, _ = _last(handler)
    assert status == 403
    assert "workspace owner" in data["message"]


def test_audit_log_unresolved_org_fails_closed_403(monkeypatch):
    """An owner whose org_id is None must NOT get a scope-less read (cross-tenant)."""
    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(api.rbac_runtime, "resolve_principal",
                        lambda user: _FakePrincipal(api.rbac_runtime.ROLE_OWNER, None))
    monkeypatch.setattr(api.rbac_runtime, "read_access_log",
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
    monkeypatch.setattr(api.rbac_runtime, "resolve_principal",
                        lambda user: _FakePrincipal(api.rbac_runtime.ROLE_OWNER, 42))
    monkeypatch.setattr(api.rbac_runtime, "read_access_log", _read)
    handler = _make_handler("GET", "/api/audit-log?limit=xyz")
    handler._handle_audit_log_get()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["org_id"] == 42
    assert data["count"] == 1
    assert seen["args"] == (100, 42)  # bad limit -> default 100, org enforced


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/reports/monthly-assurance — paid deliverable gate + period parse
# ══════════════════════════════════════════════════════════════════════════════

def test_monthly_assurance_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/reports/monthly-assurance")
    handler._handle_monthly_assurance_report()
    _, status, _ = _last(handler)
    assert status == 401


def test_monthly_assurance_capability_denied_403(monkeypatch):
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(plan, "has_capability", lambda uid, cap: False)
    handler = _make_handler("GET", "/api/reports/monthly-assurance")
    handler._handle_monthly_assurance_report()
    _, status, _ = _last(handler)
    assert status == 403  # free/unactivated account cannot pull the paid report


def test_monthly_assurance_invalid_month_is_400(monkeypatch):
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(plan, "has_capability", lambda uid, cap: True)
    handler = _make_handler("GET", "/api/reports/monthly-assurance?year=2026&month=abc")
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_monthly_assurance_report()
    data, status, _ = _last(handler)
    assert status == 400
    assert "Invalid year or month" in data["message"]


def test_monthly_assurance_named_sources_none_in_scope_is_403(monkeypatch):
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(plan, "has_capability", lambda uid, cap: True)
    handler = _make_handler(
        "GET", "/api/reports/monthly-assurance?source_ids=other-tenant-src")
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._entitle_source_ids = lambda user, ids: []  # type: ignore[method-assign]
    handler._handle_monthly_assurance_report()
    data, status, _ = _last(handler)
    assert status == 403
    assert "plan scope" in data["message"]


def test_monthly_assurance_markdown_success(monkeypatch):
    import app.monthly_assurance_report as mar
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(plan, "has_capability", lambda uid, cap: True)
    monkeypatch.setattr(mar, "compute_monthly_stats", lambda sids, y, m: {"count": 3})
    monkeypatch.setattr(mar, "render_assurance_report_markdown",
                        lambda stats, client_name: "# Report")
    handler = _make_handler("GET", "/api/reports/monthly-assurance?year=2026&month=7")
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_monthly_assurance_report()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["status"] == "ok"
    assert data["report"] == "# Report"


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/reports/coverage-certificate — auth + period parse
# ══════════════════════════════════════════════════════════════════════════════

def test_coverage_certificate_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("GET", "/api/reports/coverage-certificate")
    handler._handle_coverage_certificate()
    _, status, _ = _last(handler)
    assert status == 401


def test_coverage_certificate_invalid_month_is_400(monkeypatch):
    _auth_as(monkeypatch, {"id": 1})
    handler = _make_handler(
        "GET", "/api/reports/coverage-certificate?year=2026&month=13")
    handler._handle_coverage_certificate()
    data, status, _ = _last(handler)
    assert status == 400
    assert "Invalid period" in data["message"]


def test_coverage_certificate_markdown_success(monkeypatch):
    import app.coverage_certificate as cc

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(cc, "enabled_source_ids", lambda: [])
    monkeypatch.setattr(cc, "month_period", lambda y, m: ("2026-07-01", "2026-07-31"))
    monkeypatch.setattr(cc, "build_coverage_certificate",
                        lambda **kw: {"period_start": kw["period_start"]})
    monkeypatch.setattr(cc, "render_coverage_certificate_markdown",
                        lambda cert: "# Certificate")
    handler = _make_handler(
        "GET", "/api/reports/coverage-certificate?year=2026&month=7")
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_coverage_certificate()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["report"] == "# Certificate"


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/audit-vault — validation pipeline + builder status mapping
# ══════════════════════════════════════════════════════════════════════════════

def test_audit_vault_unauthenticated_is_401(monkeypatch):
    _auth_as(monkeypatch, None)
    handler = _make_handler("POST", "/api/audit-vault", {"source_ids": ["s1"]})
    handler._handle_audit_vault()
    _, status, _ = _last(handler)
    assert status == 401


def test_audit_vault_invalid_source_ids_is_400(monkeypatch):
    import app.audit_export as ax

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(ax, "validate_source_ids", lambda ids: (False, "source_ids required"))
    handler = _make_handler("POST", "/api/audit-vault", {"source_ids": []})
    handler._handle_audit_vault()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "source_ids required"


def test_audit_vault_none_in_scope_is_403(monkeypatch):
    import app.audit_export as ax
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(ax, "validate_source_ids", lambda ids: (True, ""))
    monkeypatch.setattr(ax, "validate_date_range", lambda a, b: (True, ""))
    monkeypatch.setattr(plan, "has_capability", lambda uid, cap: True)
    handler = _make_handler("POST", "/api/audit-vault",
                            {"source_ids": ["other"], "date_from": "2026-01-01", "date_to": "2026-02-01"})
    handler._entitle_source_ids = lambda user, ids: []  # type: ignore[method-assign]
    handler._handle_audit_vault()
    data, status, _ = _last(handler)
    assert status == 403
    assert "plan scope" in data["message"]


@pytest.mark.parametrize(
    "builder_status,expected_status",
    [("too_large", 413), ("empty", 404), ("error", 500), ("ok", 200)],
)
def test_audit_vault_builder_status_mapping(monkeypatch, builder_status, expected_status):
    import app.audit_export as ax
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(ax, "validate_source_ids", lambda ids: (True, ""))
    monkeypatch.setattr(ax, "validate_date_range", lambda a, b: (True, ""))
    monkeypatch.setattr(plan, "has_capability", lambda uid, cap: True)
    monkeypatch.setattr(ax, "build_period_audit_vault",
                        lambda sids, df, dt: {"status": builder_status, "message": "m", "max_records": 10})
    handler = _make_handler("POST", "/api/audit-vault",
                            {"source_ids": ["s1"], "date_from": "2026-01-01", "date_to": "2026-02-01"})
    handler._entitle_source_ids = lambda user, ids: ["s1"]  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_audit_vault()
    _, status, _ = _last(handler)
    assert status == expected_status


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/evidence/pack — builder status mapping + missing-file 500
# ══════════════════════════════════════════════════════════════════════════════

def test_evidence_pack_empty_selection_is_404(monkeypatch):
    import app.audit_export as ax
    import app.evidence_pack as ep
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(ax, "validate_source_ids", lambda ids: (True, ""))
    monkeypatch.setattr(ax, "validate_date_range", lambda a, b: (True, ""))
    monkeypatch.setattr(plan, "has_capability", lambda uid, cap: True)
    monkeypatch.setattr(ep, "build_evidence_pack",
                        lambda sids, df, dt: {"status": "empty", "message": "no records"})
    handler = _make_handler("POST", "/api/evidence/pack",
                            {"source_ids": ["s1"], "date_from": "2026-01-01", "date_to": "2026-02-01"})
    handler._entitle_source_ids = lambda user, ids: ["s1"]  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_evidence_pack()
    _, status, _ = _last(handler)
    assert status == 404


def test_evidence_pack_missing_generated_file_is_500(monkeypatch):
    import app.audit_export as ax
    import app.evidence_pack as ep
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(ax, "validate_source_ids", lambda ids: (True, ""))
    monkeypatch.setattr(ax, "validate_date_range", lambda a, b: (True, ""))
    monkeypatch.setattr(plan, "has_capability", lambda uid, cap: True)
    # ok status but the pack path does not exist on disk -> 500, never a broken download.
    monkeypatch.setattr(ep, "build_evidence_pack",
                        lambda sids, df, dt: {"status": "ok", "pack_path": "/nonexistent/pack.zip"})
    handler = _make_handler("POST", "/api/evidence/pack",
                            {"source_ids": ["s1"], "date_from": "2026-01-01", "date_to": "2026-02-01"})
    handler._entitle_source_ids = lambda user, ids: ["s1"]  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_evidence_pack()
    data, status, _ = _last(handler)
    assert status == 500
    assert "not generated" in data["message"]


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/reports/change-register — capability gate + tenancy + date range
# ══════════════════════════════════════════════════════════════════════════════

def test_change_register_capability_denied_403(monkeypatch):
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(plan, "has_capability", lambda uid, cap: False)
    handler = _make_handler("POST", "/api/reports/change-register", {})
    handler._handle_change_register_export()
    _, status, _ = _last(handler)
    assert status == 403


def test_change_register_source_not_in_scope_is_403(monkeypatch):
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(plan, "has_capability", lambda uid, cap: True)
    handler = _make_handler("POST", "/api/reports/change-register",
                            {"source_id": "other-tenant-src"})
    # The named custom source is not entitled to this caller -> 403.
    handler._entitle_source_ids = lambda user, ids: []  # type: ignore[method-assign]
    handler._handle_change_register_export()
    data, status, _ = _last(handler)
    assert status == 403
    assert "not in your plan scope" in data["message"]


def test_change_register_invalid_date_range_is_400(monkeypatch):
    import app.change_register as cr
    import app.plan as plan

    _auth_as(monkeypatch, {"id": 1})
    monkeypatch.setattr(plan, "has_capability", lambda uid, cap: True)
    monkeypatch.setattr(cr, "validate_register_date_range",
                        lambda a, b: (False, "date_from after date_to"))
    handler = _make_handler("POST", "/api/reports/change-register",
                            {"date_from": "2026-05-01", "date_to": "2026-01-01"})
    handler._entitle_source_ids = lambda user, ids: ids  # type: ignore[method-assign]
    handler._denied_custom_source_ids = lambda user: set()  # type: ignore[method-assign]
    handler._handle_change_register_export()
    data, status, _ = _last(handler)
    assert status == 400
    assert data["message"] == "date_from after date_to"


def test_change_register_success_scopes_to_caller(monkeypatch):
    import app.change_register as cr
    import app.plan as plan

    seen = {}

    def _build(**kwargs):
        seen["kwargs"] = kwargs
        return {"status": "ok", "csv_path": "/x.csv"}

    _auth_as(monkeypatch, {"id": 66})
    monkeypatch.setattr(plan, "has_capability", lambda uid, cap: True)
    monkeypatch.setattr(cr, "validate_register_date_range", lambda a, b: (True, ""))
    monkeypatch.setattr(cr, "build_change_register_export", _build)
    handler = _make_handler("POST", "/api/reports/change-register", {})
    handler._entitle_source_ids = lambda user, ids: ids  # type: ignore[method-assign]
    handler._denied_custom_source_ids = lambda user: {"denied"}  # type: ignore[method-assign]
    handler._caller_org_id = lambda user: 8  # type: ignore[method-assign]
    handler._rbac_log_export = lambda *a, **k: None  # type: ignore[method-assign]
    handler._handle_change_register_export()
    data, status, _ = _last(handler)
    assert status == 200
    assert data["ok"] is True
    assert seen["kwargs"]["user_id"] == 66  # decision column scoped to caller
    assert seen["kwargs"]["excluded_source_ids"] == {"denied"}
    assert seen["kwargs"]["org_id"] == 8
