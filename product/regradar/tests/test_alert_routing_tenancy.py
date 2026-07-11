"""Cross-tenant leak regression for the alert-routing / delivery pipeline.

Round-5 finding: the approved-alert candidate pool (`load_approved_alert_candidates`
→ `list_alert_drafts`) is GLOBAL — it globs every source's alert draft with no
owner filter. `build_routing_preview_for_user` scored those against a caller's
profile, so a victim's PRIVATE custom source (name, URL, executive summary) could
surface in any user's delivery preview / digest / Telegram+email delivery.

The fix scopes the pool at the single chokepoint (`load_approved_alert_candidates`
now takes user_id and drops drafts for custom sources the user does not own) and
`build_routing_preview_for_user` passes the user through, so preview, send-preview,
and both digest paths inherit the scope.

These tests pin BOTH: (1) the chokepoint filter, and (2) the wiring that makes the
preview builder pass user_id — a future edit that drops either reopens the leak
and fails here.
"""
from __future__ import annotations

import sys
from pathlib import Path

PRODUCT_DIR = str(Path(__file__).resolve().parents[1])
if PRODUCT_DIR not in sys.path:
    sys.path.insert(0, PRODUCT_DIR)

import app.alert_routing as alert_routing

_VICTIM_NAME = "ACME Internal Compliance Feed"
_VICTIM_URL = "https://acme-private.example/regulatory-inbox"
_OWNER_ID = 1
_ATTACKER_ID = 2

# custom-A owned by user 1 (denied to user 2); official-X shared.
_SOURCES = [
    {"source_id": "custom-A", "custom": True, "owner_user_id": _OWNER_ID,
     "name": _VICTIM_NAME, "url": _VICTIM_URL, "jurisdiction": "AE",
     "enabled": True, "category": "financial_regulator", "status": "active"},
    {"source_id": "official-X", "name": "CBUAE — Public Notices",
     "url": "https://www.centralbank.ae/en/notices", "jurisdiction": "AE",
     "enabled": True, "category": "central_bank", "status": "active"},
]

_DRAFTS = [
    {"alert_id": "draft-custom-A", "source_id": "custom-A",
     "source_name": _VICTIM_NAME, "source_url": _VICTIM_URL, "risk_level": "HIGH",
     "executive_summary": "MLRO flagged: do not disclose to client",
     "detected_at": "2026-07-01T00:00:00Z"},
    {"alert_id": "draft-official-X", "source_id": "official-X",
     "source_name": "CBUAE — Public Notices", "risk_level": "HIGH",
     "executive_summary": "Public notice update", "detected_at": "2026-07-01T00:00:00Z"},
]


def _patch_pool(monkeypatch) -> None:
    monkeypatch.setattr("app.source_intake.load_sources_json", lambda: list(_SOURCES))
    monkeypatch.setattr("app.alert_review.list_alert_drafts", lambda *a, **k: [dict(d) for d in _DRAFTS])
    # Every draft is approved & recent.
    monkeypatch.setattr(
        "app.alert_review.latest_review_for",
        lambda alert_id, *a, **k: {"new_status": "APPROVED_FOR_URGENT", "reviewed_at_utc": "2026-07-02T00:00:00Z"},
    )
    monkeypatch.setattr(alert_routing, "_get_approved_statuses", lambda: {"APPROVED_FOR_URGENT", "APPROVED_FOR_WEEKLY"})


def _ids(candidates) -> set[str]:
    return {str(c.get("source_id") or "") for c in candidates}


def test_candidate_pool_excludes_cross_tenant_custom_source(monkeypatch):
    _patch_pool(monkeypatch)

    # Attacker (user 2, not owner of custom-A): victim's custom source is dropped,
    # official source remains.
    attacker = alert_routing.load_approved_alert_candidates(days=30, user_id=_ATTACKER_ID)
    ids = _ids(attacker)
    assert "custom-A" not in ids
    assert "official-X" in ids
    blob = repr(attacker)
    assert _VICTIM_NAME not in blob and _VICTIM_URL not in blob

    # Owner (user 1): sees their own custom source AND the official source.
    owner = alert_routing.load_approved_alert_candidates(days=30, user_id=_OWNER_ID)
    assert _ids(owner) == {"custom-A", "official-X"}


def test_candidate_pool_unscoped_when_no_user(monkeypatch):
    """Backward-compat: with no user_id the pool is unfiltered (internal callers)."""
    _patch_pool(monkeypatch)
    both = alert_routing.load_approved_alert_candidates(days=30)
    assert _ids(both) == {"custom-A", "official-X"}


def test_preview_builder_passes_user_id_to_pool(monkeypatch):
    """Wiring guard: build_routing_preview_for_user must scope the pool to the
    target user, else preview/send/digest silently re-globalise the pool.
    """
    seen: dict = {}

    def fake_loader(days, *, user_id=None):
        seen["user_id"] = user_id
        return []

    monkeypatch.setattr(alert_routing, "load_approved_alert_candidates", fake_loader)
    monkeypatch.setattr(alert_routing, "user_profile_to_routing_profile", lambda uid: {"onboarding_completed": True})
    monkeypatch.setattr(alert_routing, "get_telegram_link", lambda uid: {"telegram_chat_id": None})
    monkeypatch.setattr(alert_routing, "get_sent_alert_ids_for_user", lambda uid: set())

    alert_routing.build_routing_preview_for_user(_ATTACKER_ID, days=30)
    assert seen["user_id"] == _ATTACKER_ID
