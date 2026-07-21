"""Cross-tenant scoping for the DASHBOARD / LISTING source endpoints.

The paid EXPORT paths were already owner-scoped (see
``test_export_authz_limits.py``). A re-review found the SAME cross-tenant leak
class on the authenticated LISTING / READINESS endpoints, which were never
scoped: a victim's *private* custom source (source_id + name + private URL) was
returned verbatim to ANY authenticated user, including free accounts.

This module covers the comprehensive fix:

FIX 1 — owner-scoping of source listings via the shared ``_visible_sources_for``
        / ``_source_visible_to`` helpers:
          * GET /api/sources/status  — victim's custom source is absent for
            another tenant, official sources still appear.
          * GET /api/sources/summary — the aggregate count excludes another
            tenant's custom source.
          * GET /api/sources/timeline?source_id=<victim custom> — 404, and the
            timeline builder is never reached (no name/url/health leak).
          * GET /api/evidence        — evidence rows for a victim's custom source
            are dropped for another tenant.

FIX 2 — hardening:
          * ``append_source_to_json`` dedupes on source_id (not just URL).
          * ``_entitle_source_ids`` fail-closes: a duplicate/attacker row for a
            source_id cannot flip ownership.

FIX 3 — deploy-safety: ``activate-plan --list`` shows plan intent vs. activated
        plan so the operator can see who needs (re-)activation after a deploy.

Every test fails before the corresponding fix and passes after it.
"""

from __future__ import annotations

import json
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api as api
import app.api_evidence as api_evidence
import app.db as app_db
from app.api import _Handler


# ── handler harness (mirrors test_export_authz_limits.py) ────────────────────

def _make_handler(method: str = "GET", path: str = "/") -> _Handler:
    header_map = {"Content-Length": "0", "X-Real-IP": "10.0.0.5"}
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


def _last_payload(handler: _Handler) -> dict:
    return handler._sent[-1][0]  # type: ignore[attr-defined]


def _auth(monkeypatch, user_id: int) -> None:
    monkeypatch.setattr(api, "require_auth", lambda handler: {"id": user_id, "email": "u@x.io"})
    monkeypatch.setattr(api_evidence, "require_auth", lambda handler: {"id": user_id, "email": "u@x.io"})


# User 1 (victim) owns a PRIVATE custom source; user 2 must never see it.
_VICTIM_NAME = "ACME Internal Compliance Feed"
_VICTIM_URL = "https://acme-private.example/regulatory-inbox"

_SOURCES = [
    {
        "source_id": "custom-A",
        "custom": True,
        "owner_user_id": 1,
        "name": _VICTIM_NAME,
        "url": _VICTIM_URL,
        "jurisdiction": "AE",
        "enabled": True,
        "category": "financial_regulator",
        "status": "active",
    },
    {
        "source_id": "official-X",
        "name": "CBUAE — Public Notices",
        "url": "https://www.centralbank.ae/en/notices",
        "jurisdiction": "AE",
        "enabled": True,
        "category": "central_bank",
        "status": "active",
    },
]


def _patch_common(monkeypatch) -> None:
    """Point every sources.json reader at the two-tenant fixture."""
    monkeypatch.setattr("app.source_intake.load_sources_json", lambda: _SOURCES)
    monkeypatch.setattr("app.source_readiness.load_market_sources", lambda market: list(_SOURCES))
    monkeypatch.setattr("app.source_runs.latest_runs", lambda market=None, *a, **k: {})
    monkeypatch.setattr(
        "app.source_health_timeline.build_source_timeline",
        lambda sid, **k: {"total_events": 0, "ok": True, "source_id": sid},
    )


# ── FIX 1 — /api/sources/status ──────────────────────────────────────────────

def test_sources_status_hides_other_tenants_custom_source(monkeypatch):
    _patch_common(monkeypatch)
    _auth(monkeypatch, user_id=2)  # caller is NOT the owner
    handler = _make_handler("GET", "/api/sources/status?market=AE")
    handler._handle_sources_status()

    payload = _last_payload(handler)
    ids = {s["source_id"] for s in payload["sources"]}
    assert "custom-A" not in ids               # victim's private source is gone
    assert "official-X" in ids                 # shared/official still visible
    blob = json.dumps(payload)
    assert _VICTIM_NAME not in blob            # name never leaks
    assert _VICTIM_URL not in blob             # private URL never leaks


def test_sources_status_shows_owner_their_own_custom_source(monkeypatch):
    _patch_common(monkeypatch)
    _auth(monkeypatch, user_id=1)  # caller IS the owner
    handler = _make_handler("GET", "/api/sources/status?market=AE")
    handler._handle_sources_status()

    ids = {s["source_id"] for s in _last_payload(handler)["sources"]}
    assert ids == {"custom-A", "official-X"}   # owner sees both


# ── FIX 1 — /api/sources/summary ─────────────────────────────────────────────

def test_sources_summary_excludes_other_tenants_custom_from_counts(monkeypatch):
    """The handler must pass the caller's denied custom ids to the summary."""
    _patch_common(monkeypatch)
    _auth(monkeypatch, user_id=2)
    seen: dict = {}

    def _capture(market, *, excluded_source_ids=None, **k):
        seen["excluded"] = set(excluded_source_ids or set())
        return {"ok": True, "market": market, "enabled_count": 0}

    monkeypatch.setattr("app.source_summary.build_sources_summary", _capture)
    handler = _make_handler("GET", "/api/sources/summary?market=AE")
    handler._handle_sources_summary()
    assert "custom-A" in seen["excluded"]      # victim's source excluded for user 2
    assert "official-X" not in seen["excluded"]


def test_sources_summary_owner_excludes_nothing(monkeypatch):
    _patch_common(monkeypatch)
    _auth(monkeypatch, user_id=1)  # owner
    seen: dict = {}

    def _capture(market, *, excluded_source_ids=None, **k):
        seen["excluded"] = set(excluded_source_ids or set())
        return {"ok": True}

    monkeypatch.setattr("app.source_summary.build_sources_summary", _capture)
    handler = _make_handler("GET", "/api/sources/summary?market=AE")
    handler._handle_sources_summary()
    assert seen["excluded"] == set()           # owner excludes nothing


def test_build_sources_summary_drops_excluded_custom_source(tmp_path):
    """Unit: the count logic itself honours excluded_source_ids."""
    from app.source_summary import build_sources_summary

    (tmp_path / "sources.json").write_text(json.dumps([
        {"source_id": "custom-A", "custom": True, "owner_user_id": 1,
         "jurisdiction": "AE", "enabled": True, "monitoring_mode": "fresh_alert",
         "alert_eligible": True, "status": "active"},
        {"source_id": "off-1", "jurisdiction": "AE", "enabled": True,
         "monitoring_mode": "fresh_alert", "alert_eligible": True, "status": "active"},
    ]), encoding="utf-8")

    full = build_sources_summary("AE", base_dir=tmp_path)
    scoped = build_sources_summary("AE", base_dir=tmp_path, excluded_source_ids={"custom-A"})
    assert full["enabled_count"] == 2
    assert scoped["enabled_count"] == 1        # custom-A dropped from the count


# ── FIX 1 — /api/sources/timeline ────────────────────────────────────────────

def test_timeline_refuses_other_tenants_custom_source(monkeypatch):
    _patch_common(monkeypatch)
    _auth(monkeypatch, user_id=2)  # not the owner
    # The timeline builder must never be reached for a denied source_id.
    monkeypatch.setattr(
        "app.source_health_timeline.build_source_timeline",
        lambda *a, **k: pytest.fail("cross-tenant timeline reached the builder"),
    )
    handler = _make_handler("GET", "/api/sources/timeline?source_id=custom-A")
    handler._handle_source_timeline_get()
    assert 404 in _statuses(handler)           # absent, not confirmed to exist
    assert _VICTIM_NAME not in json.dumps(_last_payload(handler))


def test_timeline_allows_official_source(monkeypatch):
    _patch_common(monkeypatch)
    _auth(monkeypatch, user_id=2)
    called: dict = {}
    monkeypatch.setattr(
        "app.source_health_timeline.build_source_timeline",
        lambda sid, **k: called.setdefault("sid", sid) or {"ok": True, "source_id": sid},
    )
    handler = _make_handler("GET", "/api/sources/timeline?source_id=official-X")
    handler._handle_source_timeline_get()
    assert called.get("sid") == "official-X"
    assert 404 not in _statuses(handler)


def test_timeline_allows_owner_their_own_custom_source(monkeypatch):
    _patch_common(monkeypatch)
    _auth(monkeypatch, user_id=1)  # owner
    called: dict = {}
    monkeypatch.setattr(
        "app.source_health_timeline.build_source_timeline",
        lambda sid, **k: called.setdefault("sid", sid) or {"ok": True, "source_id": sid},
    )
    handler = _make_handler("GET", "/api/sources/timeline?source_id=custom-A")
    handler._handle_source_timeline_get()
    assert called.get("sid") == "custom-A"
    assert 404 not in _statuses(handler)


# ── FIX 1 — /api/evidence (source-run listing echoes name + url) ─────────────

def test_evidence_list_drops_other_tenants_custom_source_runs(monkeypatch, tmp_path):
    _patch_common(monkeypatch)
    _auth(monkeypatch, user_id=2)  # not the owner
    runs_dir = tmp_path / "data" / "source_runs"
    runs_dir.mkdir(parents=True)
    (runs_dir / "source_runs.jsonl").write_text(
        json.dumps({"run_id": "r-A", "source_id": "custom-A", "market": "AE",
                    "source_name": _VICTIM_NAME, "official_url": _VICTIM_URL}) + "\n"
        + json.dumps({"run_id": "r-X", "source_id": "official-X", "market": "AE",
                      "source_name": "CBUAE", "official_url": "https://centralbank.ae"}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(api, "BASE_DIR", tmp_path)
    monkeypatch.setattr(api_evidence, "BASE_DIR", tmp_path)
    handler = _make_handler("GET", "/api/evidence?market=AE")
    handler._handle_evidence_list()

    payload = _last_payload(handler)
    ids = {r["source_id"] for r in payload["evidence"]}
    assert "custom-A" not in ids
    assert "official-X" in ids
    assert _VICTIM_NAME not in json.dumps(payload)
    assert _VICTIM_URL not in json.dumps(payload)


# ── FIX 1 — shared helper unit tests (fail-closed on duplicate rows) ──────────

def test_visible_sources_for_filters_and_is_failclosed(monkeypatch):
    monkeypatch.setattr(
        "app.source_intake.load_sources_json",
        lambda: [
            {"source_id": "custom-A", "custom": True, "owner_user_id": 1},
            # attacker duplicate row for the SAME id, owned by user 2:
            {"source_id": "custom-A", "custom": True, "owner_user_id": 2},
            {"source_id": "custom-B", "custom": True, "owner_user_id": 2},
            {"source_id": "official-X"},
        ],
    )
    handler = _make_handler()
    rows = [
        {"source_id": "custom-A", "custom": True, "owner_user_id": 1, "name": "A"},
        {"source_id": "custom-B", "custom": True, "owner_user_id": 2, "name": "B"},
        {"source_id": "official-X", "name": "X"},
    ]
    # User 1: the conflicting duplicate row for custom-A fail-closes it; only the
    # shared official source survives — an attacker row cannot expose it.
    visible_ids = {s["source_id"] for s in handler._visible_sources_for({"id": 1}, rows)}
    assert visible_ids == {"official-X"}


def test_source_visible_to_denies_cross_tenant_custom(monkeypatch):
    monkeypatch.setattr(
        "app.source_intake.load_sources_json",
        lambda: [{"source_id": "custom-B", "custom": True, "owner_user_id": 2}],
    )
    handler = _make_handler()
    assert handler._source_visible_to({"id": 1}, "custom-B") is False   # not owner
    assert handler._source_visible_to({"id": 2}, "custom-B") is True    # owner
    assert handler._source_visible_to({"id": 1}, "official-anything") is True


# ── FIX 2 — append_source_to_json dedupes on source_id ───────────────────────

def _seed_sources(monkeypatch, tmp_path, rows) -> Path:
    path = tmp_path / "sources.json"
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    monkeypatch.setattr("app.source_tester._SOURCES_PATH", path)
    return path


def test_append_source_rejects_duplicate_source_id(monkeypatch, tmp_path):
    from app.source_tester import append_source_to_json

    path = _seed_sources(monkeypatch, tmp_path, [
        {"source_id": "custom-dup", "url": "https://one.example/a"},
    ])
    # Same source_id, DIFFERENT url — must be refused (id uniqueness, not just URL).
    ok = append_source_to_json({"source_id": "custom-dup", "url": "https://two.example/b"})
    assert ok is False
    entries = json.loads(path.read_text(encoding="utf-8"))
    assert len(entries) == 1                    # nothing appended


def test_append_source_rejects_duplicate_url(monkeypatch, tmp_path):
    from app.source_tester import append_source_to_json

    path = _seed_sources(monkeypatch, tmp_path, [
        {"source_id": "custom-1", "url": "https://dup.example/a"},
    ])
    ok = append_source_to_json({"source_id": "custom-2", "url": "https://dup.example/a/"})
    assert ok is False                          # trailing-slash-normalised URL dupe
    assert len(json.loads(path.read_text(encoding="utf-8"))) == 1


def test_append_source_adds_unique_source(monkeypatch, tmp_path):
    from app.source_tester import append_source_to_json

    path = _seed_sources(monkeypatch, tmp_path, [
        {"source_id": "custom-1", "url": "https://one.example/a"},
    ])
    ok = append_source_to_json({"source_id": "custom-2", "url": "https://two.example/b"})
    assert ok is True
    entries = json.loads(path.read_text(encoding="utf-8"))
    assert {e["source_id"] for e in entries} == {"custom-1", "custom-2"}


# ── FIX 2 — _entitle_source_ids fail-closes on any owner mismatch ─────────────

def test_entitle_denies_when_duplicate_row_conflicts_ownership(monkeypatch):
    """An attacker row for a victim's source_id must NOT flip entitlement."""
    from app.plan import PLAN_CAPABILITIES
    import app.plan as plan

    caps = PLAN_CAPABILITIES["consultant"]
    monkeypatch.setattr(
        plan, "get_plan_state",
        lambda uid: {"active_capabilities": caps, "capabilities": caps},
    )
    monkeypatch.setattr(
        "app.source_intake.load_sources_json",
        lambda: [
            {"source_id": "custom-A", "custom": True, "owner_user_id": 1},   # victim
            {"source_id": "custom-A", "custom": True, "owner_user_id": 2},   # attacker dup
        ],
    )
    handler = _make_handler()
    # Attacker (user 2) planted a duplicate row for the victim's id and now asks
    # for it. Fail-closed semantics deny it (last-write-wins would have granted).
    assert handler._entitle_source_ids({"id": 2}, ["custom-A"]) == []
    # The victim also fail-closes on the conflicting id — nobody can use it.
    assert handler._entitle_source_ids({"id": 1}, ["custom-A"]) == []


# ── FIX 3 — activate-plan --list ─────────────────────────────────────────────

@pytest.fixture()
def _activation_db(tmp_path, monkeypatch):
    monkeypatch.setattr(app_db, "DB_PATH", str(tmp_path / "activation.db"))
    return tmp_path / "activation.db"


def _new_user(email: str) -> int:
    from app.auth import create_user

    return int(create_user(email, "password-123")["id"])


def test_list_user_plans_flags_who_needs_activation(_activation_db):
    from app.db import ensure_auth_tables
    from app.plan import activate_plan, list_user_plans, set_plan_intent

    ensure_auth_tables()
    paid_pending = _new_user("pending@x.io")
    paid_active = _new_user("active@x.io")
    free_user = _new_user("free@x.io")

    set_plan_intent(paid_pending, "professional")   # intent only — NOT activated
    set_plan_intent(paid_active, "consultant")
    activate_plan(paid_active, "consultant")         # founder-activated

    rows = {r["id"]: r for r in list_user_plans()}
    assert rows[paid_pending]["needs_activation"] is True
    assert rows[paid_pending]["activated_plan"] == "evidence_preview"
    assert rows[paid_active]["needs_activation"] is False
    assert rows[paid_active]["activated_plan"] == "consultant"
    assert rows[free_user]["needs_activation"] is False


def test_activate_plan_cli_list_runs(_activation_db, capsys):
    import run
    from app.db import ensure_auth_tables
    from app.plan import set_plan_intent

    ensure_auth_tables()
    uid = _new_user("cli-list@x.io")
    set_plan_intent(uid, "professional")

    with pytest.raises(SystemExit) as exc:
        run._cmd_activate_plan(["--list"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "cli-list@x.io" in out
    assert "need (re-)activation" in out
    assert f"--user {uid} --plan professional" in out   # actionable command printed
