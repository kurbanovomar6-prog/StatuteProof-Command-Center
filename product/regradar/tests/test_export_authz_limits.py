"""GROUP B — authz / tenancy / DoS hardening for the paid export paths.

Covers three security-review findings:

1. PLAN / CAPABILITY GATING (#2 CRITICAL) — the paid-export handlers must reject
   a free (``evidence_preview``) account and must clip caller-supplied
   ``source_ids`` to the plan's ``source_limit`` and to sources the user owns.
2. CUSTOM-SOURCE TENANCY (#3 CRITICAL) — ``/api/custom-sources`` must only list
   the caller's own custom sources; another customer's (and legacy/unowned)
   custom sources must never leak.
3. EXPORT RATE LIMITS + CAPS (#4 HIGH DoS) — heavy export endpoints are behind a
   shared per-IP limiter, and the date-range width + ``source_ids`` length are
   capped so a single request cannot fan out into unbounded work.

Every test fails before the corresponding fix and passes after it.
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api as api
import app.db as app_db
import app.plan as plan
from app.api import _Handler, _RateLimiter
from app.plan import PLAN_CAPABILITIES


# ── handler harness ──────────────────────────────────────────────────────────

def _make_handler(method: str = "POST", path: str = "/", *, real_ip: str = "10.0.0.5") -> _Handler:
    """Minimal handler with just enough header plumbing for these paths.

    ``headers.get`` answers Content-Length / X-Real-IP / Cookie / Origin / Host
    so ``_client_ip`` (rate limiting) and ``require_auth`` do not explode on a
    bare instance.
    """
    header_map = {"Content-Length": "0", "X-Real-IP": real_ip}
    handler = _Handler.__new__(_Handler)
    handler.command = method
    handler.path = path
    handler.request = MagicMock()
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(b"")
    handler.wfile = BytesIO()
    handler.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": header_map.get(key, default)
    handler.headers = hdrs

    sent: list[tuple[dict, int]] = []
    handler._send_json = lambda data, status=200, **kw: sent.append((data, status))  # type: ignore[method-assign]
    handler._sent = sent  # type: ignore[attr-defined]
    return handler


def _statuses(handler: _Handler) -> list[int]:
    return [s for _, s in handler._sent]  # type: ignore[attr-defined]


def _patch_plan(monkeypatch, plan_name: str) -> None:
    """Force ``get_plan_state`` to report ``plan_name`` as the ACTIVATED plan.

    Entitlements follow ``active_capabilities`` (the plan a founder has actually
    activated), NOT the self-selected ``capabilities`` — so these handler/authz
    tests model an account whose plan has genuinely been activated. Both keys are
    populated so any consumer sees a coherent, activated state.
    """
    caps = PLAN_CAPABILITIES[plan_name]
    state = {
        "active_plan_name": plan_name,
        "active_capabilities": caps,
        "requested_capabilities": None,
        "capabilities": caps,
    }
    monkeypatch.setattr(plan, "get_plan_state", lambda uid: state)


def _auth(monkeypatch, user_id: int = 1) -> None:
    monkeypatch.setattr(api, "require_auth", lambda handler: {"id": user_id, "email": "u@x.io"})


# ── 1a. plan capability helpers (pure) ───────────────────────────────────────

def test_free_plan_has_no_paid_export_capabilities(monkeypatch):
    _patch_plan(monkeypatch, "evidence_preview")
    assert plan.has_capability(1, "audit_export") is False
    assert plan.has_capability(1, "pdf_export") is False
    assert plan.source_limit_for(1) == 0


def test_starter_pilot_still_has_no_audit_export(monkeypatch):
    _patch_plan(monkeypatch, "starter_pilot")
    assert plan.has_capability(1, "audit_export") is False
    assert plan.has_capability(1, "pdf_export") is False
    assert plan.source_limit_for(1) == 3


def test_professional_plan_unlocks_paid_exports(monkeypatch):
    _patch_plan(monkeypatch, "professional")
    assert plan.has_capability(1, "audit_export") is True
    assert plan.has_capability(1, "pdf_export") is True
    assert plan.source_limit_for(1) == 172


def test_capabilities_fail_closed_when_lookup_raises(monkeypatch):
    def _boom(uid):
        raise RuntimeError("db down")

    monkeypatch.setattr(plan, "get_plan_state", _boom)
    # A broken plan lookup must deny, never grant.
    assert plan.has_capability(1, "audit_export") is False
    assert plan.source_limit_for(1) == 0


# ── 1b. capability gating at the handler boundary ────────────────────────────

def test_evidence_pack_blocks_free_account(monkeypatch):
    _auth(monkeypatch)
    _patch_plan(monkeypatch, "evidence_preview")
    handler = _make_handler("POST", "/api/evidence/pack")
    monkeypatch.setattr(
        handler, "_read_json_strict",
        lambda: ({"source_ids": ["cbuae"], "date_from": "2026-03-01", "date_to": "2026-03-31"}, None),
    )
    # If the gate ever regresses, this must not reach the builder.
    monkeypatch.setattr(
        "app.evidence_pack.build_evidence_pack",
        lambda *a, **k: pytest.fail("free account reached build_evidence_pack"),
    )
    handler._handle_evidence_pack()
    assert 403 in _statuses(handler)


def test_audit_vault_blocks_free_account(monkeypatch):
    _auth(monkeypatch)
    _patch_plan(monkeypatch, "evidence_preview")
    handler = _make_handler("POST", "/api/audit/vault")
    monkeypatch.setattr(
        handler, "_read_json_strict",
        lambda: ({"source_ids": ["cbuae"], "date_from": "2026-03-01", "date_to": "2026-03-31"}, None),
    )
    monkeypatch.setattr(
        "app.audit_export.build_period_audit_vault",
        lambda *a, **k: pytest.fail("free account reached build_period_audit_vault"),
    )
    handler._handle_audit_vault()
    assert 403 in _statuses(handler)


def test_change_register_export_blocks_free_account(monkeypatch):
    _auth(monkeypatch)
    _patch_plan(monkeypatch, "evidence_preview")
    handler = _make_handler("POST", "/api/change-register/export")
    monkeypatch.setattr(
        handler, "_read_json_strict",
        lambda: ({"date_from": "", "date_to": ""}, None),
    )
    monkeypatch.setattr(
        "app.change_register.build_change_register_export",
        lambda *a, **k: pytest.fail("free account reached change register builder"),
    )
    handler._handle_change_register_export()
    assert 403 in _statuses(handler)


def test_coverage_certificate_pdf_blocks_free_account(monkeypatch):
    _auth(monkeypatch)
    _patch_plan(monkeypatch, "evidence_preview")
    handler = _make_handler("GET", "/api/reports/coverage-certificate?format=pdf&year=2026&month=3")
    monkeypatch.setattr(
        "app.coverage_certificate.generate_coverage_certificate_pdf",
        lambda *a, **k: pytest.fail("free account reached PDF generation"),
    )
    handler._handle_coverage_certificate()
    assert 403 in _statuses(handler)


def test_coverage_certificate_markdown_allowed_for_free_account(monkeypatch):
    """Non-PDF coverage stays available in-dashboard for any authenticated user."""
    _auth(monkeypatch)
    _patch_plan(monkeypatch, "evidence_preview")
    handler = _make_handler("GET", "/api/reports/coverage-certificate?format=markdown&year=2026&month=3")
    monkeypatch.setattr("app.coverage_certificate.enabled_source_ids", lambda *a, **k: ["off-1"])
    monkeypatch.setattr("app.coverage_certificate.build_coverage_certificate", lambda **k: {"summary": "ok"})
    monkeypatch.setattr("app.coverage_certificate.render_coverage_certificate_markdown", lambda c: "# report")
    handler._handle_coverage_certificate()
    assert 403 not in _statuses(handler)


def test_evidence_pack_allows_professional_account(monkeypatch, tmp_path):
    _auth(monkeypatch)
    _patch_plan(monkeypatch, "professional")
    fake_zip = tmp_path / "pack.zip"
    fake_zip.write_bytes(b"PK\x05\x06" + b"\x00" * 18)
    monkeypatch.setattr(
        "app.evidence_pack.build_evidence_pack",
        lambda *a, **k: {"status": "ok", "pack_path": str(fake_zip), "pack_filename": "pack.zip", "record_count": 1},
    )
    handler = _make_handler("POST", "/api/evidence/pack")
    monkeypatch.setattr(
        handler, "_read_json_strict",
        lambda: ({"source_ids": ["cbuae"], "date_from": "2026-03-01", "date_to": "2026-03-31"}, None),
    )
    got: dict = {}
    handler._send_bytes = lambda body, content_type, status=200, extra_headers=None: got.update(  # type: ignore[method-assign]
        body=body, content_type=content_type
    )
    handler._handle_evidence_pack()
    assert got.get("content_type") == "application/zip"
    assert 403 not in _statuses(handler)


# ── 1c. source_ids entitlement clipping ──────────────────────────────────────

def test_entitle_drops_custom_source_owned_by_another_user(monkeypatch):
    _patch_plan(monkeypatch, "consultant")  # generous source_limit
    monkeypatch.setattr(
        "app.source_intake.load_sources_json",
        lambda: [
            {"source_id": "custom-A", "custom": True, "owner_user_id": 1},
            {"source_id": "custom-B", "custom": True, "owner_user_id": 2},
            {"source_id": "official-X"},
        ],
    )
    handler = _make_handler()
    entitled = handler._entitle_source_ids({"id": 1}, ["custom-A", "custom-B", "official-X"])
    # User 1 keeps their own custom source + the shared official one; user 2's is gone.
    assert entitled == ["custom-A", "official-X"]


def test_entitle_drops_legacy_unowned_custom_source(monkeypatch):
    _patch_plan(monkeypatch, "consultant")
    monkeypatch.setattr(
        "app.source_intake.load_sources_json",
        lambda: [{"source_id": "custom-legacy", "custom": True}],  # no owner_user_id
    )
    handler = _make_handler()
    entitled = handler._entitle_source_ids({"id": 1}, ["custom-legacy"])
    assert entitled == []


def test_entitle_caps_to_plan_source_limit(monkeypatch):
    _patch_plan(monkeypatch, "starter_pilot")  # source_limit == 3
    monkeypatch.setattr("app.source_intake.load_sources_json", lambda: [])
    handler = _make_handler()
    entitled = handler._entitle_source_ids({"id": 1}, [f"off-{i}" for i in range(10)])
    assert entitled == ["off-0", "off-1", "off-2"]


def test_evidence_pack_rejects_when_all_sources_out_of_scope(monkeypatch):
    _auth(monkeypatch, user_id=1)
    _patch_plan(monkeypatch, "professional")
    monkeypatch.setattr(
        "app.source_intake.load_sources_json",
        lambda: [{"source_id": "custom-B", "custom": True, "owner_user_id": 2}],
    )
    monkeypatch.setattr(
        "app.evidence_pack.build_evidence_pack",
        lambda *a, **k: pytest.fail("out-of-scope source reached the builder"),
    )
    handler = _make_handler("POST", "/api/evidence/pack")
    monkeypatch.setattr(
        handler, "_read_json_strict",
        lambda: ({"source_ids": ["custom-B"], "date_from": "2026-03-01", "date_to": "2026-03-31"}, None),
    )
    handler._handle_evidence_pack()
    assert 403 in _statuses(handler)


def test_evidence_pack_clips_before_calling_builder(monkeypatch):
    """The builder must receive only the entitled subset, never the raw input."""
    _auth(monkeypatch, user_id=1)
    _patch_plan(monkeypatch, "professional")
    monkeypatch.setattr(
        "app.source_intake.load_sources_json",
        lambda: [
            {"source_id": "custom-A", "custom": True, "owner_user_id": 1},
            {"source_id": "custom-B", "custom": True, "owner_user_id": 2},
        ],
    )
    seen: dict = {}

    def _capture(source_ids, date_from, date_to, **k):
        seen["source_ids"] = list(source_ids)
        return {"status": "empty", "record_count": 0, "message": "none"}

    monkeypatch.setattr("app.evidence_pack.build_evidence_pack", _capture)
    handler = _make_handler("POST", "/api/evidence/pack")
    monkeypatch.setattr(
        handler, "_read_json_strict",
        lambda: ({"source_ids": ["custom-A", "custom-B"], "date_from": "2026-03-01", "date_to": "2026-03-31"}, None),
    )
    handler._handle_evidence_pack()
    assert seen["source_ids"] == ["custom-A"]  # custom-B (owner 2) removed


# ── 2. custom-source tenancy on the list endpoint ────────────────────────────

_TWO_USER_SOURCES = [
    {"source_id": "custom-A", "custom": True, "owner_user_id": 1, "name": "A"},
    {"source_id": "custom-B", "custom": True, "owner_user_id": 2, "name": "B"},
    {"source_id": "custom-legacy", "custom": True, "name": "legacy"},  # no owner
    {"source_id": "official-X", "name": "official"},
]


def _list_for_user(monkeypatch, user_id: int) -> list[dict]:
    monkeypatch.setattr(api, "require_auth", lambda handler: {"id": user_id, "email": "u@x.io"})
    monkeypatch.setattr("app.source_intake.load_sources_json", lambda: _TWO_USER_SOURCES)
    handler = _make_handler("GET", "/api/custom-sources")
    captured: dict = {}
    handler._send_json = lambda data, status=200, **kw: captured.update(data=data, status=status)  # type: ignore[method-assign]
    handler._handle_custom_sources_list()
    return captured["data"]["sources"]


def test_custom_sources_list_isolates_by_owner(monkeypatch):
    a_sources = _list_for_user(monkeypatch, 1)
    ids_a = {s["source_id"] for s in a_sources}
    assert ids_a == {"custom-A"}
    assert "custom-B" not in ids_a  # never leak another customer's source

    b_sources = _list_for_user(monkeypatch, 2)
    ids_b = {s["source_id"] for s in b_sources}
    assert ids_b == {"custom-B"}


def test_custom_sources_list_hides_legacy_unowned(monkeypatch):
    # A user who owns nothing must see nothing — legacy/unowned sources are not
    # attributed to an arbitrary caller.
    sources = _list_for_user(monkeypatch, 999)
    assert sources == []


def test_custom_source_add_stamps_owner(monkeypatch):
    """A newly added custom source records the creating user as its owner."""
    _auth(monkeypatch, user_id=7)
    saved: dict = {}
    monkeypatch.setattr("app.source_tester.validate_public_url", lambda url: (True, ""))
    monkeypatch.setattr("app.source_tester.source_url_exists", lambda url: False)
    monkeypatch.setattr("app.source_intake.load_sources_json", lambda: [])
    monkeypatch.setattr(
        "app.source_intake.run_source_intake",
        lambda *a, **k: {"status": "CONFIRMED_ACCESSIBLE"},
    )
    monkeypatch.setattr("app.source_tester.append_source_to_json", lambda src: saved.update(src) or True)
    handler = _make_handler("POST", "/api/custom-sources")
    monkeypatch.setattr(
        handler, "_read_json",
        lambda: {"url": "https://regulator.example.ae/rules", "name": "R", "legal_confirmed": True},
    )
    handler._handle_custom_sources_add()
    assert saved.get("owner_user_id") == 7
    assert saved.get("custom") is True


# ── 3. rate limits + caps (DoS) ──────────────────────────────────────────────

def test_export_endpoints_share_a_rate_limiter(monkeypatch):
    """A burst of heavy exports from one IP is throttled after the cap."""
    monkeypatch.setattr(api, "_EXPORT_LIMITER", _RateLimiter(2, 3600))
    _auth(monkeypatch)
    _patch_plan(monkeypatch, "professional")
    monkeypatch.setattr(
        "app.evidence_pack.build_evidence_pack",
        lambda *a, **k: {"status": "empty", "record_count": 0, "message": "none"},
    )
    monkeypatch.setattr("app.source_intake.load_sources_json", lambda: [])

    statuses: list[int] = []
    for _ in range(3):
        handler = _make_handler("POST", "/api/evidence/pack", real_ip="203.0.113.42")
        monkeypatch.setattr(
            handler, "_read_json_strict",
            lambda: ({"source_ids": ["off-1"], "date_from": "2026-03-01", "date_to": "2026-03-31"}, None),
        )
        handler._handle_evidence_pack()
        statuses.append(_statuses(handler)[-1])
    # First two allowed through the limiter; the third is rejected with 429.
    assert statuses[2] == 429
    assert statuses.count(429) == 1


def test_rate_limit_keyed_per_ip(monkeypatch):
    """A throttled IP does not throttle a different IP."""
    monkeypatch.setattr(api, "_EXPORT_LIMITER", _RateLimiter(1, 3600))
    _auth(monkeypatch)
    _patch_plan(monkeypatch, "professional")
    monkeypatch.setattr(
        "app.evidence_pack.build_evidence_pack",
        lambda *a, **k: {"status": "empty", "record_count": 0, "message": "none"},
    )
    monkeypatch.setattr("app.source_intake.load_sources_json", lambda: [])

    def _call(ip: str) -> int:
        handler = _make_handler("POST", "/api/evidence/pack", real_ip=ip)
        monkeypatch.setattr(
            handler, "_read_json_strict",
            lambda: ({"source_ids": ["off-1"], "date_from": "2026-03-01", "date_to": "2026-03-31"}, None),
        )
        handler._handle_evidence_pack()
        return _statuses(handler)[-1]

    _call("198.51.100.1")  # exhausts IP #1
    assert _call("198.51.100.1") == 429  # IP #1 now throttled
    assert _call("198.51.100.2") != 429  # a different IP is unaffected


def test_validate_date_range_rejects_over_wide_window():
    from app.audit_export import validate_date_range, MAX_RANGE_DAYS

    today = date.today()
    d_from = today - timedelta(days=MAX_RANGE_DAYS + 5)
    ok, msg = validate_date_range(d_from.isoformat(), today.isoformat())
    assert ok is False
    assert str(MAX_RANGE_DAYS) in msg


def test_validate_date_range_allows_window_at_the_cap():
    from app.audit_export import validate_date_range, MAX_RANGE_DAYS

    today = date.today()
    d_from = today - timedelta(days=MAX_RANGE_DAYS)  # exactly at the cap
    ok, _ = validate_date_range(d_from.isoformat(), today.isoformat())
    assert ok is True


def test_register_date_range_rejects_over_wide_window():
    from app.change_register import validate_register_date_range, MAX_REGISTER_RANGE_DAYS

    ok, msg = validate_register_date_range("2024-01-01", "2026-01-01")  # ~731 days
    assert ok is False
    assert str(MAX_REGISTER_RANGE_DAYS) in msg


def test_register_date_range_unbounded_side_still_allowed():
    from app.change_register import validate_register_date_range

    # A one-sided (unbounded) range is not subject to the width cap.
    ok, _ = validate_register_date_range("2020-01-01", "")
    assert ok is True


def test_validate_source_ids_rejects_over_long_list():
    from app.audit_export import validate_source_ids, MAX_SOURCE_IDS

    ok, msg = validate_source_ids([f"s-{i}" for i in range(MAX_SOURCE_IDS + 1)])
    assert ok is False
    assert str(MAX_SOURCE_IDS) in msg


def test_validate_source_ids_accepts_reasonable_list():
    from app.audit_export import validate_source_ids

    ok, msg = validate_source_ids(["a", "b", "c"])
    assert ok is True and msg == ""


def test_evidence_pack_rejects_over_long_source_ids(monkeypatch):
    from app.audit_export import MAX_SOURCE_IDS

    _auth(monkeypatch)
    _patch_plan(monkeypatch, "professional")
    monkeypatch.setattr(
        "app.evidence_pack.build_evidence_pack",
        lambda *a, **k: pytest.fail("over-long source_ids reached the builder"),
    )
    handler = _make_handler("POST", "/api/evidence/pack")
    monkeypatch.setattr(
        handler, "_read_json_strict",
        lambda: (
            {"source_ids": [f"s-{i}" for i in range(MAX_SOURCE_IDS + 1)],
             "date_from": "2026-03-01", "date_to": "2026-03-31"},
            None,
        ),
    )
    handler._handle_evidence_pack()
    assert 400 in _statuses(handler)


def test_build_evidence_pack_rejects_over_long_source_ids():
    from app.evidence_pack import build_evidence_pack
    from app.audit_export import MAX_SOURCE_IDS

    result = build_evidence_pack(
        [f"s-{i}" for i in range(MAX_SOURCE_IDS + 1)], "2026-03-01", "2026-03-31"
    )
    assert result["status"] == "error"
    assert str(MAX_SOURCE_IDS) in result["message"]


# ── 4. BLOCK-1 — ACTIVATED-state model (self-select must NOT grant caps) ──────
#
# The entitlement gate reads the ACTIVATED plan, never the self-selected plan
# intent. A user can POST plan_name=consultant with no payment, but until a
# founder runs the activate-plan CLI they keep evidence_preview capabilities.

@pytest.fixture()
def _activation_db(tmp_path, monkeypatch):
    """Isolated SQLite DB so plan activation can be exercised end-to-end."""
    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "activation.db"))
    return tmp_path / "activation.db"


def _new_user_id(email: str = "self@x.io") -> int:
    from app.auth import create_user

    return int(create_user(email, "password-123")["id"])


def test_self_selected_paid_plan_grants_nothing_until_activated(_activation_db):
    from app.plan import activate_plan, has_capability, set_plan_intent, source_limit_for

    uid = _new_user_id()
    # User self-selects the top plan — no payment, no founder, no admin.
    set_plan_intent(uid, "consultant")
    # BEFORE activation: still free-tier. This is the bypass being closed.
    assert has_capability(uid, "audit_export") is False
    assert has_capability(uid, "pdf_export") is False
    assert source_limit_for(uid) == 0

    # AFTER the founder-only CLI-backed activation: paid caps unlock.
    activate_plan(uid, "consultant")
    assert has_capability(uid, "audit_export") is True
    assert source_limit_for(uid) == 999


def test_cli_activation_flips_active_plan_state(_activation_db):
    from app.plan import activate_plan, get_plan_state, set_plan_intent

    uid = _new_user_id("cli@x.io")
    set_plan_intent(uid, "professional")
    before = get_plan_state(uid)
    assert before["active_plan_name"] == "evidence_preview"
    assert before["status"] == "pending_manual_activation"
    assert before["active_capabilities"]["audit_export"] is False

    after = activate_plan(uid, "professional")
    assert after["active_plan_name"] == "professional"
    assert after["status"] == "active"
    assert after["active_capabilities"]["audit_export"] is True
    assert after["active_capabilities"]["source_limit"] == 172


def test_evidence_pack_refused_for_self_selected_unactivated_account(_activation_db, monkeypatch):
    from app.plan import set_plan_intent

    uid = _new_user_id("pack@x.io")
    set_plan_intent(uid, "consultant")  # self-selected, NOT activated
    monkeypatch.setattr(api, "require_auth", lambda handler: {"id": uid, "email": "pack@x.io"})
    monkeypatch.setattr(
        "app.evidence_pack.build_evidence_pack",
        lambda *a, **k: pytest.fail("unactivated self-selected account reached the builder"),
    )
    handler = _make_handler("POST", "/api/evidence/pack")
    monkeypatch.setattr(
        handler, "_read_json_strict",
        lambda: ({"source_ids": ["cbuae"], "date_from": "2026-03-01", "date_to": "2026-03-31"}, None),
    )
    handler._handle_evidence_pack()
    assert 403 in _statuses(handler)


# ── 5. BLOCK-2 — change register default (no source_id) tenancy clip ──────────

def test_change_register_default_export_excludes_other_tenants_custom_source(monkeypatch):
    """A default (source_id-less) export must still exclude user A's custom source."""
    # User B is the caller; user A (id 1) owns custom-A.
    _auth(monkeypatch, user_id=2)
    _patch_plan(monkeypatch, "professional")
    monkeypatch.setattr(
        "app.source_intake.load_sources_json",
        lambda: [
            {"source_id": "custom-A", "custom": True, "owner_user_id": 1},
            {"source_id": "official-X"},
        ],
    )
    seen: dict = {}

    def _capture(*, excluded_source_ids=None, **k):
        seen["excluded"] = set(excluded_source_ids or set())
        return {"status": "ok", "row_count": 0, "exports": {}, "meta": {}, "disclaimer": "d", "message": "m"}

    monkeypatch.setattr("app.change_register.build_change_register_export", _capture)
    handler = _make_handler("POST", "/api/change-register/export")
    monkeypatch.setattr(
        handler, "_read_json_strict",
        lambda: ({"date_from": "", "date_to": ""}, None),  # NO source_id filter
    )
    handler._handle_change_register_export()
    # custom-A (owned by user 1) is excluded even though the caller named no source.
    assert "custom-A" in seen["excluded"]
    assert "official-X" not in seen["excluded"]


# ── 6. BLOCK-3 — monthly assurance report gate + entitlement ──────────────────

def test_monthly_assurance_blocks_free_account(monkeypatch):
    _auth(monkeypatch)
    _patch_plan(monkeypatch, "evidence_preview")
    monkeypatch.setattr(
        "app.monthly_assurance_report.compute_monthly_stats",
        lambda *a, **k: pytest.fail("free account reached compute_monthly_stats"),
    )
    handler = _make_handler("GET", "/api/reports/monthly-assurance?year=2026&month=3&source_ids=cbuae")
    handler._handle_monthly_assurance_report()
    assert 403 in _statuses(handler)


def test_monthly_assurance_clips_source_ids_to_owner(monkeypatch):
    """A paid caller's named sources are clipped; another tenant's custom source is dropped."""
    _auth(monkeypatch, user_id=1)
    _patch_plan(monkeypatch, "professional")
    monkeypatch.setattr(
        "app.source_intake.load_sources_json",
        lambda: [
            {"source_id": "custom-A", "custom": True, "owner_user_id": 1},
            {"source_id": "custom-B", "custom": True, "owner_user_id": 2},
        ],
    )
    seen: dict = {}

    def _capture(source_ids, year, month):
        seen["source_ids"] = list(source_ids) if source_ids else source_ids
        return {"is_estimate": True, "total_runs": 0}

    monkeypatch.setattr("app.monthly_assurance_report.compute_monthly_stats", _capture)
    monkeypatch.setattr(
        "app.monthly_assurance_report.render_assurance_report_markdown",
        lambda stats, client_name="": "# report",
    )
    handler = _make_handler(
        "GET", "/api/reports/monthly-assurance?year=2026&month=3&source_ids=custom-A,custom-B"
    )
    handler._handle_monthly_assurance_report()
    assert seen["source_ids"] == ["custom-A"]  # custom-B (owner 2) removed
    assert 403 not in _statuses(handler)


def test_monthly_assurance_refuses_when_all_named_sources_out_of_scope(monkeypatch):
    _auth(monkeypatch, user_id=1)
    _patch_plan(monkeypatch, "professional")
    monkeypatch.setattr(
        "app.source_intake.load_sources_json",
        lambda: [{"source_id": "custom-B", "custom": True, "owner_user_id": 2}],
    )
    monkeypatch.setattr(
        "app.monthly_assurance_report.compute_monthly_stats",
        lambda *a, **k: pytest.fail("out-of-scope source reached compute_monthly_stats"),
    )
    handler = _make_handler(
        "GET", "/api/reports/monthly-assurance?year=2026&month=3&source_ids=custom-B"
    )
    handler._handle_monthly_assurance_report()
    assert 403 in _statuses(handler)


# ── 7. BLOCK-4a — coverage certificate default scope excludes non-owned custom ─

def test_coverage_certificate_default_scope_excludes_other_tenants_custom(monkeypatch):
    _auth(monkeypatch, user_id=1)
    _patch_plan(monkeypatch, "professional")
    # enabled_source_ids returns a global set that includes another tenant's custom source.
    monkeypatch.setattr(
        "app.coverage_certificate.enabled_source_ids", lambda *a, **k: ["official-X", "custom-B"]
    )
    monkeypatch.setattr(
        "app.source_intake.load_sources_json",
        lambda: [{"source_id": "custom-B", "custom": True, "owner_user_id": 2}],
    )
    seen: dict = {}

    def _capture(*, period_start, period_end, source_ids, client_name):
        seen["source_ids"] = list(source_ids) if source_ids else source_ids
        return {"summary": "ok"}

    monkeypatch.setattr("app.coverage_certificate.build_coverage_certificate", _capture)
    monkeypatch.setattr("app.coverage_certificate.render_coverage_certificate_markdown", lambda c: "# r")
    handler = _make_handler("GET", "/api/reports/coverage-certificate?format=markdown&year=2026&month=3")
    handler._handle_coverage_certificate()
    assert seen["source_ids"] == ["official-X"]  # custom-B (owner 2) excluded from default set


# ── 8. BLOCK-4b — evidence-export IDOR: cross-tenant custom source refused ─────

def test_evidence_export_refuses_other_tenants_custom_source(monkeypatch):
    _auth(monkeypatch, user_id=2)  # caller is user 2
    # The record's source is custom-A, owned by user 1.
    monkeypatch.setattr(
        "app.evidence_assessment.find_evidence_record",
        lambda evidence_id: {"run_id": evidence_id, "source_id": "custom-A"},
    )
    monkeypatch.setattr(
        "app.source_intake.load_sources_json",
        lambda: [{"source_id": "custom-A", "custom": True, "owner_user_id": 1}],
    )
    handler = _make_handler("GET", "/api/evidence/export?run_id=run_custom_A_1")
    # The tenancy guard fires before any export work happens.
    monkeypatch.setattr(
        handler, "_write_evidence_export",
        lambda *a, **k: pytest.fail("cross-tenant custom-source export reached the writer"),
    )
    handler._handle_evidence_export_get()
    assert 403 in _statuses(handler)


def test_evidence_export_allows_official_source(monkeypatch):
    _auth(monkeypatch, user_id=2)
    monkeypatch.setattr(
        "app.evidence_assessment.find_evidence_record",
        lambda evidence_id: {"run_id": evidence_id, "source_id": "official-X"},
    )
    monkeypatch.setattr(
        "app.source_intake.load_sources_json",
        lambda: [{"source_id": "custom-A", "custom": True, "owner_user_id": 1}],
    )
    called: dict = {}
    handler = _make_handler("GET", "/api/evidence/export?run_id=run_official_1")
    monkeypatch.setattr(
        handler, "_write_evidence_export",
        lambda evidence_id, **k: called.update(evidence_id=evidence_id),
    )
    handler._handle_evidence_export_get()
    # Official (shared) source is not tenancy-denied; export proceeds.
    assert called.get("evidence_id") == "run_official_1"
    assert 403 not in _statuses(handler)
