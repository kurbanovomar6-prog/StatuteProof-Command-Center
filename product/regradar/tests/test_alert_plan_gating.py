"""Plan-gating of the official-source Telegram broadcast.

Audit 2026-07-20 product_readiness HIGH: `_deliver_alert_to_subscribed_users`
resolved recipients via ``get_all_linked_chat_ids()`` with NO plan check, so
free (evidence_preview) accounts received the paid core deliverable the moment
they paired a Telegram chat.

Fix under test: the official-source broadcast is now gated behind the
``STATUTEPROOF_ALERTS_REQUIRE_PLAN`` env flag (default ON). Eligibility is a
FILTER on top of ``get_all_linked_chat_ids()``'s return value
(``telegram_pairing.filter_plan_eligible_chat_ids``):

  * founder-ACTIVATED paid plans (starter_pilot / professional / consultant,
    via the ``official_alerts`` capability) pass;
  * free accounts are dropped;
  * operator emails listed in ``STATUTEPROOF_ALERT_PLAN_EXEMPT_EMAILS`` pass
    regardless of plan;
  * chat_ids that do not resolve to any user_profiles row pass through
    (deliberate fail-open for unresolvable ids only — see the filter docstring).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import db


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "gate.db"))
    # The gate defaults to ON — make sure no ambient env leaks into tests
    # that do not set the flag themselves.
    monkeypatch.delenv("STATUTEPROOF_ALERTS_REQUIRE_PLAN", raising=False)
    monkeypatch.delenv("STATUTEPROOF_ALERT_PLAN_EXEMPT_EMAILS", raising=False)
    yield tmp_path / "gate.db"


def _make_paired_user(email: str, chat_id: str, *, alerts_enabled: bool = True) -> int:
    """Create a user, pair a Telegram chat, and set the alerts flag.

    (Mirrors tests/test_alert_delivery_g3.py.)
    """
    from app.auth import create_user
    from app.telegram_pairing import create_pairing_code, consume_pairing_code
    from app.profile import update_profile

    user = create_user(email, "password-123")
    user_id = int(user["id"])
    code = create_pairing_code(user_id)["code"]
    result = consume_pairing_code(code, chat_id, {"username": "tester"})
    assert result == "ok"
    update_profile(user_id, {"telegram_alerts_enabled": 1 if alerts_enabled else 0})
    return user_id


def _capture_sends(monkeypatch):
    """Patch tg.send_telegram_message to capture recipient chat_ids."""
    import app.telegram as tg

    sent_to: list[str] = []

    def _fake_send(chat_id: str, text: str, parse_mode: str | None = None) -> bool:
        sent_to.append(str(chat_id))
        return True

    monkeypatch.setattr(tg, "send_telegram_message", _fake_send)
    return tg, sent_to


def test_free_paired_user_is_excluded_from_official_broadcast_by_default(
    isolated_db, monkeypatch
):
    """Flag unset (default ON): the free account is dropped, the paid one kept."""
    from app.plan import activate_plan

    tg, sent_to = _capture_sends(monkeypatch)

    _make_paired_user("free@co.com", "100001", alerts_enabled=True)
    paid_id = _make_paired_user("paid@co.com", "100002", alerts_enabled=True)
    activate_plan(paid_id, "professional")

    reached = tg._deliver_alert_to_subscribed_users("official notice")
    assert reached == 1
    assert sent_to == ["100002"]


def test_starter_pilot_activated_user_receives(isolated_db, monkeypatch):
    from app.plan import activate_plan

    tg, sent_to = _capture_sends(monkeypatch)

    uid = _make_paired_user("pilot@co.com", "200001", alerts_enabled=True)
    activate_plan(uid, "starter_pilot")

    reached = tg._deliver_alert_to_subscribed_users("official notice")
    assert reached == 1
    assert sent_to == ["200001"]


def test_activation_flips_free_user_to_receiving(isolated_db, monkeypatch):
    """The funnel proof: excluded while free, included after activate-plan."""
    from app.plan import activate_plan

    tg, sent_to = _capture_sends(monkeypatch)

    uid = _make_paired_user("convert@co.com", "300001", alerts_enabled=True)

    assert tg._deliver_alert_to_subscribed_users("official notice") == 0
    assert sent_to == []

    activate_plan(uid, "professional")

    assert tg._deliver_alert_to_subscribed_users("official notice") == 1
    assert sent_to == ["300001"]


def test_flag_off_restores_ungated_broadcast(isolated_db, monkeypatch):
    """STATUTEPROOF_ALERTS_REQUIRE_PLAN=0 — the owner's conscious flip back to
    the ungated pilot behavior: free + paid both reached."""
    from app.plan import activate_plan

    monkeypatch.setenv("STATUTEPROOF_ALERTS_REQUIRE_PLAN", "0")
    tg, sent_to = _capture_sends(monkeypatch)

    _make_paired_user("free@co.com", "400001", alerts_enabled=True)
    paid_id = _make_paired_user("paid@co.com", "400002", alerts_enabled=True)
    activate_plan(paid_id, "professional")

    reached = tg._deliver_alert_to_subscribed_users("official notice")
    assert reached == 2
    assert set(sent_to) == {"400001", "400002"}


def test_exempt_operator_email_receives_despite_free_plan(isolated_db, monkeypatch):
    """Founder/operator exemption via STATUTEPROOF_ALERT_PLAN_EXEMPT_EMAILS."""
    monkeypatch.setenv(
        "STATUTEPROOF_ALERT_PLAN_EXEMPT_EMAILS", "founder@statuteproof.com"
    )
    tg, sent_to = _capture_sends(monkeypatch)

    _make_paired_user("founder@statuteproof.com", "500001", alerts_enabled=True)
    _make_paired_user("free@co.com", "500002", alerts_enabled=True)

    reached = tg._deliver_alert_to_subscribed_users("official notice")
    assert reached == 1
    assert sent_to == ["500001"]


def test_unresolvable_chat_ids_pass_through_filter(isolated_db):
    """Chat ids with no user_profiles row PASS THROUGH the filter.

    Deliberate fail-open for unresolvable ids only: monkeypatched tenancy tests
    (test_telegram_delivery_tenancy.py / test_deadline_radar_tenancy.py) inject
    fake chat ids that exist in no DB and must keep reaching their targets. In
    production every broadcast chat_id comes from the same user_profiles table
    the filter reads, so a real free user always resolves — and is gated.
    """
    from app.telegram_pairing import filter_plan_eligible_chat_ids

    assert filter_plan_eligible_chat_ids(["notindb1"]) == ["notindb1"]


# ---------------------------------------------------------------------------
# Audit 07-20 FIX 4/5: the gate was wired in ONE place only, while two LIVE
# scheduler paths still delivered the same official-source content to free
# accounts — scheduler.py runs both every cycle.
#
#   * digest_cadence.run_scheduled_digests  -> get_linked_alert_user_ids()
#   * deadline_radar.send_due_reminders     -> get_all_linked_chat_ids()
# ---------------------------------------------------------------------------


def _preview_with_one_high(alert_id: str = "h1") -> dict:
    return {
        "ok": True,
        "profile_ready": True,
        "not_ready_reasons": [],
        "matches": [
            {
                "alert_id": alert_id,
                "source_id": "AE-1",
                "source_name": "DFSA",
                "market": "DIFC",
                "jurisdiction": "DIFC",
                "change_type": "Regulatory update",
                "risk_level": "HIGH",
                "score": 40,
                "matched": True,
                "delivery_ready": True,
                "executive_summary": "A monitored change.",
                "source_url": "https://example.gov.ae/x",
                "reviewed_at": "2026-07-10T10:00:00+00:00",
            }
        ],
    }


def _capture_scheduled_dispatch(monkeypatch):
    """Patch the digest dispatcher's alert send to capture the user_ids reached."""
    import app.digest_cadence as dc

    fired: list[int] = []

    monkeypatch.setattr(dc, "build_routing_preview_for_user", lambda uid, days: _preview_with_one_high())

    def _fake_send_preview(uid, alert_id):
        fired.append(int(uid))
        return {"ok": True}

    monkeypatch.setattr(dc, "send_preview_alert_to_user", _fake_send_preview)
    return dc, fired


def test_free_paired_user_gets_nothing_from_scheduled_digests(isolated_db, tmp_path, monkeypatch):
    """FIX 4: run_scheduled_digests must not dispatch to a FREE paired account."""
    from app.plan import activate_plan

    dc, fired = _capture_scheduled_dispatch(monkeypatch)

    _make_paired_user("free-digest@co.com", "610001", alerts_enabled=True)
    paid_id = _make_paired_user("paid-digest@co.com", "610002", alerts_enabled=True)
    activate_plan(paid_id, "professional")

    summary = dc.run_scheduled_digests(send_fn=lambda c, t: True, base_dir=tmp_path)

    assert summary["users"] == 1
    assert fired == [paid_id]


def test_exempt_operator_still_receives_scheduled_digests(isolated_db, tmp_path, monkeypatch):
    """FIX 4: the operator exemption applies to the scheduled path too."""
    monkeypatch.setenv("STATUTEPROOF_ALERT_PLAN_EXEMPT_EMAILS", "founder@statuteproof.com")
    dc, fired = _capture_scheduled_dispatch(monkeypatch)

    exempt_id = _make_paired_user("founder@statuteproof.com", "620001", alerts_enabled=True)
    _make_paired_user("free-digest2@co.com", "620002", alerts_enabled=True)

    summary = dc.run_scheduled_digests(send_fn=lambda c, t: True, base_dir=tmp_path)

    assert summary["users"] == 1
    assert fired == [exempt_id]


def test_flag_off_restores_ungated_scheduled_digests(isolated_db, tmp_path, monkeypatch):
    """FIX 4: the owner's conscious flip back reaches free accounts again."""
    monkeypatch.setenv("STATUTEPROOF_ALERTS_REQUIRE_PLAN", "0")
    dc, fired = _capture_scheduled_dispatch(monkeypatch)

    free_id = _make_paired_user("free-digest3@co.com", "630001", alerts_enabled=True)
    paid_id = _make_paired_user("paid-digest3@co.com", "630002", alerts_enabled=True)
    from app.plan import activate_plan

    activate_plan(paid_id, "professional")

    summary = dc.run_scheduled_digests(send_fn=lambda c, t: True, base_dir=tmp_path)

    assert summary["users"] == 2
    assert set(fired) == {free_id, paid_id}


def _seed_due_deadline(tmp_path):
    from datetime import date

    from app import deadline_radar as dr

    dr.record_deadline(
        evidence_record_id="run_gate",
        deadline_date=date(2026, 9, 1).isoformat(),
        deadline_kind="effective",
        extracted_from_diff_excerpt="effective from 1 September 2026",
        source_id="AE-x",
        regulator="DFSA",
        source_name="DFSA",
        official_url="https://dfsa.example/x",
        base_dir=tmp_path,
    )
    return date(2026, 9, 1)


def test_free_paired_chat_excluded_from_deadline_reminder_broadcast(isolated_db, tmp_path, monkeypatch):
    """FIX 5: the reminder broadcast pool carries official URLs + verbatim diff
    excerpts — paid deliverable content — so it is plan-gated like the alert
    broadcast."""
    from datetime import timedelta

    from app import deadline_radar as dr
    from app.plan import activate_plan

    _make_paired_user("free-radar@co.com", "710001", alerts_enabled=True)
    paid_id = _make_paired_user("paid-radar@co.com", "710002", alerts_enabled=True)
    activate_plan(paid_id, "professional")

    deadline = _seed_due_deadline(tmp_path)
    sent_to: list[str] = []

    summary = dr.send_due_reminders(
        as_of=deadline - timedelta(days=30),
        base_dir=tmp_path,
        send_fn=lambda chat_id, text: (sent_to.append(str(chat_id)), True)[1],
        require_review_approval=False,
    )

    assert [s["lead_stage"] for s in summary["sent"]] == [30]
    assert sent_to == ["710002"]


def test_explicit_recipients_override_stays_ungated_for_deadline_reminders(
    isolated_db, tmp_path, monkeypatch
):
    """FIX 5: operator/test-driven ``recipients=`` sends are deliberately NOT
    gated — only the auto-resolved broadcast pool is."""
    from datetime import timedelta

    from app import deadline_radar as dr

    free_user_chat = "720001"
    _make_paired_user("free-radar2@co.com", free_user_chat, alerts_enabled=True)

    deadline = _seed_due_deadline(tmp_path)
    sent_to: list[str] = []

    summary = dr.send_due_reminders(
        as_of=deadline - timedelta(days=30),
        base_dir=tmp_path,
        send_fn=lambda chat_id, text: (sent_to.append(str(chat_id)), True)[1],
        recipients=[free_user_chat],
        require_review_approval=False,
    )

    assert [s["lead_stage"] for s in summary["sent"]] == [30]
    assert sent_to == [free_user_chat]


# ---------------------------------------------------------------------------
# Audit 07-20 FIX 6: the DASHBOARD path (POST /api/delivery/send-preview-alert
# -> alert_routing.send_preview_alert_to_user) had NO plan check at all, so an
# authenticated FREE account could make the product deliver official-source
# content to its own Telegram. This is the per-user CHOKE POINT — the scheduler
# funnels through it too — so the gate lives inside the sender.
# ---------------------------------------------------------------------------


def _stub_dashboard_send(monkeypatch, *, source_id: str = "AE-1", alert_id: str = "dash-1"):
    """Stub the per-user send path down to the Telegram call and capture sends."""
    import app.alert_routing as ar

    match = {
        "alert_id": alert_id,
        "source_id": source_id,
        "source_name": "DFSA",
        "source_url": "https://example.ae/x",
        "title": "Reviewed alert",
        "risk_level": "MEDIUM",
        "change_type": "REGULATORY_UPDATE",
        "market": "AE",
        "jurisdiction": "AE",
        "topics": ["aml"],
        "executive_summary": "Something changed.",
        "limitations": [],
        "score": 85,
        "matched": True,
        "delivery_ready": True,
        "reviewed_at": "2026-07-10T00:00:00+00:00",
    }
    monkeypatch.setattr(
        ar, "build_routing_preview_for_user", lambda uid, days=14: {"matches": [dict(match)]}
    )
    monkeypatch.setattr(ar, "_is_still_approved", lambda aid: True)

    sent_to: list[str] = []

    def _ok(chat_id, text):
        sent_to.append(str(chat_id))
        return True

    monkeypatch.setattr(ar, "send_telegram_message", _ok)
    return ar, sent_to


def test_free_user_dashboard_send_is_refused(isolated_db, monkeypatch):
    """FIX 6 (the leak): free account, official source -> refused, nothing sent."""
    ar, sent_to = _stub_dashboard_send(monkeypatch)
    user_id = _make_paired_user("free-dash@co.com", "990001", alerts_enabled=True)

    result = ar.send_preview_alert_to_user(user_id, "dash-1")

    assert result["ok"] is False
    assert result["code"] == "plan_required"
    assert sent_to == []


def test_paid_user_dashboard_send_still_delivers(isolated_db, monkeypatch):
    from app.plan import activate_plan

    ar, sent_to = _stub_dashboard_send(monkeypatch)
    user_id = _make_paired_user("paid-dash@co.com", "990002", alerts_enabled=True)
    activate_plan(user_id, "professional")

    result = ar.send_preview_alert_to_user(user_id, "dash-1")

    assert result["ok"] is True
    assert sent_to == ["990002"]


def test_exempt_operator_dashboard_send_still_delivers(isolated_db, monkeypatch):
    monkeypatch.setenv("STATUTEPROOF_ALERT_PLAN_EXEMPT_EMAILS", "founder@statuteproof.com")
    ar, sent_to = _stub_dashboard_send(monkeypatch)
    user_id = _make_paired_user("founder@statuteproof.com", "990003", alerts_enabled=True)

    result = ar.send_preview_alert_to_user(user_id, "dash-1")

    assert result["ok"] is True
    assert sent_to == ["990003"]


def test_custom_source_alert_stays_ungated_for_free_owner(isolated_db, monkeypatch):
    """A customer's own PRIVATE custom source is not the paid official-source
    deliverable — the owner keeps receiving it on the free tier."""
    ar, sent_to = _stub_dashboard_send(monkeypatch, source_id="custom-abcd1234")
    user_id = _make_paired_user("free-custom@co.com", "990004", alerts_enabled=True)

    result = ar.send_preview_alert_to_user(user_id, "dash-1")

    assert result["ok"] is True
    assert sent_to == ["990004"]


def test_unclassifiable_source_is_treated_as_official_and_refused(isolated_db, monkeypatch):
    """Fail CLOSED: if the source cannot be classified it counts as OFFICIAL."""
    from app import tenancy

    def _boom(source_id):
        raise RuntimeError("source list unreadable")

    monkeypatch.setattr(tenancy, "is_custom_source", _boom)
    ar, sent_to = _stub_dashboard_send(monkeypatch, source_id="custom-abcd1234")
    user_id = _make_paired_user("free-unknown@co.com", "990005", alerts_enabled=True)

    result = ar.send_preview_alert_to_user(user_id, "dash-1")

    assert result["ok"] is False
    assert result["code"] == "plan_required"
    assert sent_to == []


def test_flag_off_restores_ungated_dashboard_send(isolated_db, monkeypatch):
    monkeypatch.setenv("STATUTEPROOF_ALERTS_REQUIRE_PLAN", "0")
    ar, sent_to = _stub_dashboard_send(monkeypatch)
    user_id = _make_paired_user("free-dash-off@co.com", "990006", alerts_enabled=True)

    result = ar.send_preview_alert_to_user(user_id, "dash-1")

    assert result["ok"] is True
    assert sent_to == ["990006"]


# ---------------------------------------------------------------------------
# Preview-surface entitlement: GET /api/delivery/preview returned the FULL
# official-source payload (title, executive summary, business action, official
# URL, verbatim diff excerpt) to any authenticated account, so a free account
# could read — and poll — exactly what POST /api/delivery/send-preview-alert
# refuses with 402.
#
# Fix under test: the preview surface serves a REDACTED view to accounts that
# are not plan-eligible (same flag, same eligibility helper as delivery):
# counts, source names, risk levels and dates stay; the paid official-source
# content is withheld and marked machine-readably. A free owner's own CUSTOM
# source stays fully visible — it is not the official-source deliverable.
# ---------------------------------------------------------------------------

from io import BytesIO  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402


def _full_match(source_id: str = "AE-1", alert_id: str = "prev-1") -> dict:
    return {
        "alert_id": alert_id,
        "source_id": source_id,
        "source_name": "DFSA",
        "source_url": "https://dfsa.example.ae/rulebook-change",
        "url": "https://dfsa.example.ae/rulebook-change",
        "title": "Rulebook amendment",
        "risk_level": "HIGH",
        "change_type": "REGULATORY_UPDATE",
        "market": "DIFC",
        "jurisdiction": "DIFC",
        "topics": ["aml"],
        "executive_summary": "The monitored page changed in section 5.3.",
        "business_action": "Review your AML procedures.",
        "diff_excerpt": "+ firms must ensure and evidence ongoing compliance",
        "proof": {"evidence_record_id": "rec-1", "record_hash": "abc123"},
        "score": 80,
        "matched": True,
        "delivery_ready": True,
        "not_ready_reasons": [],
        "limitations": [],
        "reviewed_at": "2026-07-10T10:00:00+00:00",
    }


def _preview_fixture(source_id: str = "AE-1") -> dict:
    return {
        "ok": True,
        "days": 14,
        "alerts_considered": 1,
        "matches": [_full_match(source_id)],
        "ranked_by": "profile_fit",
        "empty_state": None,
        "profile_ready": True,
        "not_ready_reasons": [],
    }


def _preview_handler(monkeypatch, user_id: int, source_id: str = "AE-1"):
    """Drive GET /api/delivery/preview for ``user_id`` with a stubbed builder."""
    import app.api as api

    handler = api._Handler.__new__(api._Handler)
    handler.command = "GET"
    handler.path = "/api/delivery/preview?days=14"
    handler.request = MagicMock()
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(b"")
    handler.wfile = BytesIO()
    handler.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": {"Content-Length": "0"}.get(key, default)
    handler.headers = hdrs
    sent: list[tuple[dict, int]] = []
    handler._send_json = lambda data, status=200, **kw: sent.append((data, status))

    monkeypatch.setattr(api, "require_auth", lambda h: {"id": int(user_id)})
    monkeypatch.setattr(
        api, "build_routing_preview_for_user", lambda uid, days=14: _preview_fixture(source_id)
    )
    handler._handle_delivery_preview()
    return sent[-1]


def test_free_account_preview_redacts_official_source_content(isolated_db, monkeypatch):
    """The leak: a free account read the paid deliverable through the preview."""
    user_id = _make_paired_user("free-preview@co.com", "810001", alerts_enabled=True)

    body, status = _preview_handler(monkeypatch, user_id)

    assert status == 200
    assert body["ok"] is True
    match = body["preview"]["matches"][0]
    # Withheld paid content — keys stay present so the UI cannot crash.
    assert match["diff_excerpt"] is None
    assert match["executive_summary"] == ""
    assert match["business_action"] == ""
    assert match["source_url"] is None
    assert match["url"] is None
    # `proof` is NOT withheld — see test_redacted_preview_keeps_the_sealed_proof_block.
    assert match["proof"] == {"evidence_record_id": "rec-1", "record_hash": "abc123"}
    # Kept: enough to prove monitoring is running and to price the upgrade.
    assert match["source_name"] == "DFSA"
    assert match["risk_level"] == "HIGH"
    assert match["alert_id"] == "prev-1"
    # Machine-readable marker for the frontend's upgrade state.
    assert match["plan_redacted"] is True
    assert match["delivery_ready"] is False
    redaction = body["preview"]["plan_redaction"]
    assert redaction["applied"] is True
    assert redaction["code"] == "plan_required"
    assert redaction["redacted_matches"] == 1


def test_paid_account_preview_keeps_official_source_content(isolated_db, monkeypatch):
    from app.plan import activate_plan

    user_id = _make_paired_user("paid-preview@co.com", "810002", alerts_enabled=True)
    activate_plan(user_id, "professional")

    body, status = _preview_handler(monkeypatch, user_id)

    assert status == 200
    match = body["preview"]["matches"][0]
    assert match["diff_excerpt"] == "+ firms must ensure and evidence ongoing compliance"
    assert match["executive_summary"] == "The monitored page changed in section 5.3."
    assert match["business_action"] == "Review your AML procedures."
    assert match["source_url"] == "https://dfsa.example.ae/rulebook-change"
    assert match["proof"] == {"evidence_record_id": "rec-1", "record_hash": "abc123"}
    assert match["plan_redacted"] is False
    assert match["delivery_ready"] is True
    assert body["preview"]["plan_redaction"]["applied"] is False


def test_free_owner_custom_source_preview_stays_fully_visible(isolated_db, monkeypatch):
    """A customer's own PRIVATE custom source is not the paid deliverable."""
    user_id = _make_paired_user("free-custom-preview@co.com", "810003", alerts_enabled=True)

    body, status = _preview_handler(monkeypatch, user_id, source_id="custom-abcd1234")

    assert status == 200
    match = body["preview"]["matches"][0]
    assert match["diff_excerpt"] == "+ firms must ensure and evidence ongoing compliance"
    assert match["executive_summary"] == "The monitored page changed in section 5.3."
    assert match["source_url"] == "https://dfsa.example.ae/rulebook-change"
    assert match["plan_redacted"] is False
    assert body["preview"]["plan_redaction"]["applied"] is False


def test_flag_off_restores_full_preview_for_free_account(isolated_db, monkeypatch):
    """Same switch as delivery: STATUTEPROOF_ALERTS_REQUIRE_PLAN=0 → today's
    ungated preview."""
    monkeypatch.setenv("STATUTEPROOF_ALERTS_REQUIRE_PLAN", "0")
    user_id = _make_paired_user("free-preview-off@co.com", "810004", alerts_enabled=True)

    body, status = _preview_handler(monkeypatch, user_id)

    assert status == 200
    match = body["preview"]["matches"][0]
    assert match["diff_excerpt"] == "+ firms must ensure and evidence ongoing compliance"
    assert match["executive_summary"] == "The monitored page changed in section 5.3."
    assert match["plan_redacted"] is False


def test_exempt_operator_preview_is_not_redacted(isolated_db, monkeypatch):
    monkeypatch.setenv("STATUTEPROOF_ALERT_PLAN_EXEMPT_EMAILS", "founder@statuteproof.com")
    user_id = _make_paired_user("founder@statuteproof.com", "810005", alerts_enabled=True)

    body, status = _preview_handler(monkeypatch, user_id)

    assert status == 200
    assert body["preview"]["matches"][0]["plan_redacted"] is False


# ---------------------------------------------------------------------------
# Sibling read surface: GET /api/alerts/redline renders the SEALED diff for one
# alert (added/removed text) behind require_auth only. The redacted preview
# still hands a free account every ``alert_id``, so redacting the preview alone
# left the paid diff one request away — the same content the delivery gate
# refuses with 402. Gated here on the SAME flag + eligibility helper.
# ---------------------------------------------------------------------------


def _redline_handler(monkeypatch, user_id: int, source_id: str = "AE-1"):
    """Drive GET /api/alerts/redline for ``user_id`` with a stubbed match."""
    import app.api as api
    import app.api_alerts as api_alerts
    import app.sealed_redline as sealed_redline

    handler = api._Handler.__new__(api._Handler)
    handler.command = "GET"
    handler.path = "/api/alerts/redline?alert_id=prev-1&days=14"
    handler.request = MagicMock()
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(b"")
    handler.wfile = BytesIO()
    handler.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": {"Content-Length": "0"}.get(key, default)
    handler.headers = hdrs
    sent: list[tuple[dict, int]] = []
    handler._send_json = lambda data, status=200, **kw: sent.append((data, status))

    monkeypatch.setattr(api, "require_auth", lambda h: {"id": int(user_id)})
    monkeypatch.setattr(api_alerts, "require_auth", lambda h: {"id": int(user_id)})
    monkeypatch.setattr(
        api_alerts,
        "find_routing_match_for_user",
        lambda uid, alert_id, days=14: _full_match(source_id),
    )
    monkeypatch.setattr(
        sealed_redline,
        "build_redline_for_match",
        lambda match, **kw: {
            "available": True,
            "blocks": [{"kind": "added", "text": "firms must ensure and evidence compliance"}],
        },
    )
    handler._rate_limited = lambda *a, **kw: False
    handler._handle_alert_redline_get()
    return sent[-1]


def test_free_account_redline_is_refused(isolated_db, monkeypatch):
    """The bypass: preview redaction is worthless if the diff is one GET away."""
    user_id = _make_paired_user("free-redline@co.com", "820001", alerts_enabled=True)

    body, status = _redline_handler(monkeypatch, user_id)

    assert status == 402
    assert body["ok"] is False
    assert body["reason"] == "plan_required"
    assert "redline" not in body


def test_paid_account_redline_is_served(isolated_db, monkeypatch):
    from app.plan import activate_plan

    user_id = _make_paired_user("paid-redline@co.com", "820002", alerts_enabled=True)
    activate_plan(user_id, "professional")

    body, status = _redline_handler(monkeypatch, user_id)

    assert status == 200
    assert body["redline"]["blocks"][0]["text"].startswith("firms must ensure")


def test_free_owner_custom_source_redline_is_served(isolated_db, monkeypatch):
    """A customer's own private source is not the official-source deliverable."""
    user_id = _make_paired_user("free-custom-redline@co.com", "820003", alerts_enabled=True)

    body, status = _redline_handler(monkeypatch, user_id, source_id="custom-abcd1234")

    assert status == 200
    assert body["redline"]["available"] is True


def test_flag_off_restores_ungated_redline(isolated_db, monkeypatch):
    monkeypatch.setenv("STATUTEPROOF_ALERTS_REQUIRE_PLAN", "0")
    user_id = _make_paired_user("free-redline-off@co.com", "820004", alerts_enabled=True)

    body, status = _redline_handler(monkeypatch, user_id)

    assert status == 200
    assert body["redline"]["available"] is True


# ---------------------------------------------------------------------------
# Round 2, finding 4: redaction must never DENY that a sealed record exists.
# The alerts UI branches on `proof` and renders "No sealed record is linked to
# this alert." when it is null — a FALSE statement about the evidence trail
# (the record exists; only the official-source content is withheld). The proof
# block carries no official-source text (record id + self-seal hash), so there
# is no entitlement reason to withhold it.
# ---------------------------------------------------------------------------


def test_redacted_preview_keeps_the_sealed_proof_block(isolated_db, monkeypatch):
    user_id = _make_paired_user("free-proof@co.com", "830001", alerts_enabled=True)

    body, status = _preview_handler(monkeypatch, user_id)

    assert status == 200
    match = body["preview"]["matches"][0]
    assert match["plan_redacted"] is True
    # Withheld content stays withheld …
    assert match["diff_excerpt"] is None
    # … but the evidence record is still declared to exist.
    assert match["proof"] == {"evidence_record_id": "rec-1", "record_hash": "abc123"}
    assert "proof" not in match["redacted_fields"]


# ---------------------------------------------------------------------------
# Round 2, findings 3 + 5: GET /api/evidence/diff returns the VERBATIM diff.md
# body of any run to any authenticated caller (tenancy check only). run_ids are
# discoverable through GET /api/evidence, so the same paid payload the preview
# now withholds and the redline now refuses with 402 was still two GETs away.
# Same flag, same eligibility helper — own custom sources stay readable.
# ---------------------------------------------------------------------------

_DIFF_TEXT = "# diff\n+ firms must ensure and evidence ongoing compliance\n"


def _evidence_diff_handler(monkeypatch, tmp_path, user_id: int, source_id: str = "AE-1"):
    import app.api as api
    import app.api_evidence as api_evidence

    runs_dir = tmp_path / "data" / "source_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "source_runs.jsonl").write_text(
        json.dumps({
            "run_id": "run-1",
            "source_id": source_id,
            "diff_md_path": "data/diffs/run-1.md",
            "change_status": "CHANGED",
        }) + "\n",
        encoding="utf-8",
    )
    diffs_dir = tmp_path / "data" / "diffs"
    diffs_dir.mkdir(parents=True, exist_ok=True)
    (diffs_dir / "run-1.md").write_text(_DIFF_TEXT, encoding="utf-8")

    handler = api._Handler.__new__(api._Handler)
    handler.command = "GET"
    handler.path = "/api/evidence/diff?run_id=run-1"
    handler.request = MagicMock()
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(b"")
    handler.wfile = BytesIO()
    handler.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": {"Content-Length": "0"}.get(key, default)
    handler.headers = hdrs
    sent: list[tuple[dict, int]] = []
    handler._send_json = lambda data, status=200, **kw: sent.append((data, status))

    monkeypatch.setattr(api, "BASE_DIR", tmp_path)
    monkeypatch.setattr(api_evidence, "BASE_DIR", tmp_path)
    monkeypatch.setattr(api, "require_auth", lambda h: {"id": int(user_id)})
    monkeypatch.setattr(api_evidence, "require_auth", lambda h: {"id": int(user_id)})
    monkeypatch.setattr(api._Handler, "_source_visible_to", lambda self, user, sid: True)
    handler._handle_evidence_diff_get()
    return sent[-1]


def test_free_account_evidence_diff_is_refused(isolated_db, monkeypatch, tmp_path):
    """The remaining bypass: the verbatim official-source diff, one GET away."""
    user_id = _make_paired_user("free-diff@co.com", "840001", alerts_enabled=True)

    body, status = _evidence_diff_handler(monkeypatch, tmp_path, user_id)

    assert status == 402
    assert body["ok"] is False
    assert body["reason"] == "plan_required"
    assert "ensure and evidence" not in json.dumps(body)


def test_paid_account_evidence_diff_is_served(isolated_db, monkeypatch, tmp_path):
    from app.plan import activate_plan

    user_id = _make_paired_user("paid-diff@co.com", "840002", alerts_enabled=True)
    activate_plan(user_id, "professional")

    body, status = _evidence_diff_handler(monkeypatch, tmp_path, user_id)

    assert status == 200
    assert body["diff_text"] == _DIFF_TEXT


def test_free_owner_custom_source_evidence_diff_is_served(isolated_db, monkeypatch, tmp_path):
    """A customer's own private source is not the official-source deliverable."""
    user_id = _make_paired_user("free-custom-diff@co.com", "840003", alerts_enabled=True)

    body, status = _evidence_diff_handler(
        monkeypatch, tmp_path, user_id, source_id="custom-abcd1234"
    )

    assert status == 200
    assert body["diff_text"] == _DIFF_TEXT


def test_flag_off_restores_ungated_evidence_diff(isolated_db, monkeypatch, tmp_path):
    monkeypatch.setenv("STATUTEPROOF_ALERTS_REQUIRE_PLAN", "0")
    user_id = _make_paired_user("free-diff-off@co.com", "840004", alerts_enabled=True)

    body, status = _evidence_diff_handler(monkeypatch, tmp_path, user_id)

    assert status == 200
    assert body["diff_text"] == _DIFF_TEXT


# ---------------------------------------------------------------------------
# Security review, round 3: the fourth read surface. POST /api/briefs/generate
# REBUILDS the paid official-source payload on demand — executive summary,
# business action and the official URL, from the run's diff artifact — behind
# require_auth + a tenancy check only, and "Monitoring Briefs" is an ungated
# page in the customer dashboard. source_ids are enumerable via
# GET /api/sources/status, so a free account could regenerate exactly the
# fields the preview now redacts and the redline/diff now refuse with 402.
# Same flag, same eligibility helper — own custom sources stay generatable.
# ---------------------------------------------------------------------------


def _brief_generate_handler(monkeypatch, tmp_path, user_id: int, source_id: str = "AE-1"):
    import app.api as api

    runs_dir = tmp_path / "data" / "source_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    (runs_dir / "source_runs.jsonl").write_text(
        json.dumps({
            "run_id": "run-1",
            "source_id": source_id,
            "source_name": "DFSA Rulebook",
            "official_url": "https://dfsa.example.ae/rulebook-change",
            "change_status": "CHANGED",
            "timestamp_utc": "2026-07-10T10:00:00+00:00",
        }) + "\n",
        encoding="utf-8",
    )

    handler = api._Handler.__new__(api._Handler)
    handler.command = "POST"
    handler.path = "/api/briefs/generate"
    handler.request = MagicMock()
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(b"")
    handler.wfile = BytesIO()
    handler.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": {"Content-Length": "0"}.get(key, default)
    handler.headers = hdrs
    sent: list[tuple[dict, int]] = []
    handler._send_json = lambda data, status=200, **kw: sent.append((data, status))

    monkeypatch.setattr(api, "BASE_DIR", tmp_path)
    monkeypatch.setattr(api, "require_auth", lambda h: {"id": int(user_id)})
    monkeypatch.setattr("app.config.ENABLE_AI_ANALYSIS", False, raising=False)
    monkeypatch.setattr(api._Handler, "_source_visible_to", lambda self, user, sid: True)
    handler._rate_limited = lambda *a, **kw: False
    handler._read_json_strict = lambda: ({"source_id": source_id, "run_id": "run-1"}, None)
    handler._handle_briefs_generate()
    return sent[-1]


def test_free_account_brief_generate_is_refused(isolated_db, monkeypatch, tmp_path):
    """The fourth bypass: the paid payload, regenerated on demand."""
    user_id = _make_paired_user("free-brief@co.com", "850001", alerts_enabled=True)

    body, status = _brief_generate_handler(monkeypatch, tmp_path, user_id)

    assert status == 402
    assert body["ok"] is False
    assert body["reason"] == "plan_required"
    blob = json.dumps(body)
    assert "dfsa.example.ae" not in blob
    assert "DFSA Rulebook" not in blob


def test_paid_account_brief_generate_is_served(isolated_db, monkeypatch, tmp_path):
    from app.plan import activate_plan

    user_id = _make_paired_user("paid-brief@co.com", "850002", alerts_enabled=True)
    activate_plan(user_id, "professional")

    body, status = _brief_generate_handler(monkeypatch, tmp_path, user_id)

    assert status == 200
    assert "DFSA Rulebook" in body["brief_markdown"]


def test_free_owner_custom_source_brief_generate_is_served(isolated_db, monkeypatch, tmp_path):
    """A customer's own private source is not the official-source deliverable."""
    user_id = _make_paired_user("free-custom-brief@co.com", "850003", alerts_enabled=True)

    body, status = _brief_generate_handler(
        monkeypatch, tmp_path, user_id, source_id="custom-abcd1234"
    )

    assert status == 200
    assert "DFSA Rulebook" in body["brief_markdown"]


def test_flag_off_restores_ungated_brief_generate(isolated_db, monkeypatch, tmp_path):
    monkeypatch.setenv("STATUTEPROOF_ALERTS_REQUIRE_PLAN", "0")
    user_id = _make_paired_user("free-brief-off@co.com", "850004", alerts_enabled=True)

    body, status = _brief_generate_handler(monkeypatch, tmp_path, user_id)

    assert status == 200
    assert "DFSA Rulebook" in body["brief_markdown"]


# ---------------------------------------------------------------------------
# Cycle-2 escalation (HIGH x2): the redaction lived in ONE handler, so every
# SIBLING reader re-opened the hole.
#
#   * GET /api/calendar/effective-dates served the verbatim diff excerpt (the
#     changed obligation text) + official_url of every OFFICIAL source to a
#     plan-blocked account — the most sellable slice of the deliverable.
#   * POST /api/decisions echoed match['source_url'] back as
#     content.reviewed.official_url to a non-eligible account.
#
# Fix under test: ONE choke point in app/alert_routing.py
# (``redact_official_item_for_plan``) that every reader passes its payload
# through, plus per-surface adapters. Same flag, same eligibility helper; a
# free owner's own CUSTOM source stays fully visible everywhere.
# ---------------------------------------------------------------------------


_CAL_EXCERPT = "+ firms must submit the return by 31 March 2027"
_CAL_URL = "https://dfsa.example.ae/rulebook-change"


def _calendar_result(source_id: str = "AE-1") -> dict:
    return {
        "dates": [
            {
                "date": "2027-03-31",
                "detected_type": "deadline",
                "type_label": "Deadline detected in the changed text",
                "raw_date_text": "31 March 2027",
                "date_ambiguous": False,
                "excerpt": _CAL_EXCERPT,
                "source_id": source_id,
                "source_name": "DFSA Rulebook",
                "regulator": "DFSA",
                "official_url": _CAL_URL,
                "evidence_record_id": "evr-1",
                "record_hash": "sha256:" + "a" * 64,
                "captured_at": "2026-07-10T10:00:00+00:00",
                "framing": "Detected in the changed text.",
                "disclaimer": "Not legal advice.",
                "days_until": 250,
            }
        ],
        "count": 1,
        "horizon": {"from": "2026-07-21", "to": "2027-07-21", "days": 365},
        "generated_at": "2026-07-21T00:00:00+00:00",
        "framing": "View framing.",
        "disclaimer": "Not legal advice.",
        "truncated": False,
    }


def _effective_dates_handler(monkeypatch, user_id: int, source_id: str = "AE-1"):
    """Drive GET /api/calendar/effective-dates with a stubbed builder."""
    import app.api as api
    import app.effective_dates as effective_dates

    handler = api._Handler.__new__(api._Handler)
    handler.command = "GET"
    handler.path = "/api/calendar/effective-dates?days=365"
    handler.request = MagicMock()
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(b"")
    handler.wfile = BytesIO()
    handler.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": {"Content-Length": "0"}.get(key, default)
    handler.headers = hdrs
    sent: list[tuple[dict, int]] = []
    handler._send_json = lambda data, status=200, **kw: sent.append((data, status))

    monkeypatch.setattr(api, "require_auth", lambda h: {"id": int(user_id)})
    monkeypatch.setattr(
        effective_dates, "upcoming_key_dates", lambda **kw: _calendar_result(source_id)
    )
    handler._rate_limited = lambda *a, **kw: False
    handler._denied_custom_source_ids = lambda user: set()
    handler._rbac_log_export = lambda *a, **kw: None
    handler._handle_effective_dates_calendar()
    return sent[-1]


def test_free_account_effective_dates_withholds_excerpt_and_official_url(
    isolated_db, monkeypatch
):
    """The bypass: the calendar handed over the changed obligation text."""
    user_id = _make_paired_user("free-cal@co.com", "860001", alerts_enabled=True)

    body, status = _effective_dates_handler(monkeypatch, user_id)

    assert status == 200
    item = body["dates"][0]
    assert item["excerpt"] == ""
    assert item["official_url"] == ""
    assert item["plan_redacted"] is True
    # Kept: the date, its type and the sealed verification pointer — the free
    # tier still sees honestly THAT monitoring found something.
    assert item["date"] == "2027-03-31"
    assert item["source_name"] == "DFSA Rulebook"
    assert item["record_hash"].startswith("sha256:")
    assert item["evidence_record_id"] == "evr-1"
    assert body["plan_redaction"]["applied"] is True
    assert body["plan_redaction"]["code"] == "plan_required"
    blob = json.dumps(body)
    assert _CAL_EXCERPT not in blob
    assert _CAL_URL not in blob


def test_paid_account_effective_dates_keeps_excerpt_and_official_url(
    isolated_db, monkeypatch
):
    from app.plan import activate_plan

    user_id = _make_paired_user("paid-cal@co.com", "860002", alerts_enabled=True)
    activate_plan(user_id, "professional")

    body, status = _effective_dates_handler(monkeypatch, user_id)

    assert status == 200
    item = body["dates"][0]
    assert item["excerpt"] == _CAL_EXCERPT
    assert item["official_url"] == _CAL_URL
    assert item["plan_redacted"] is False
    assert body["plan_redaction"]["applied"] is False


def test_free_owner_custom_source_effective_dates_stays_visible(isolated_db, monkeypatch):
    user_id = _make_paired_user("free-custom-cal@co.com", "860003", alerts_enabled=True)

    body, status = _effective_dates_handler(monkeypatch, user_id, source_id="custom-abcd1234")

    assert status == 200
    item = body["dates"][0]
    assert item["excerpt"] == _CAL_EXCERPT
    assert item["official_url"] == _CAL_URL
    assert body["plan_redaction"]["applied"] is False


def test_flag_off_restores_ungated_effective_dates(isolated_db, monkeypatch):
    monkeypatch.setenv("STATUTEPROOF_ALERTS_REQUIRE_PLAN", "0")
    user_id = _make_paired_user("free-cal-off@co.com", "860004", alerts_enabled=True)

    body, status = _effective_dates_handler(monkeypatch, user_id)

    assert status == 200
    assert body["dates"][0]["excerpt"] == _CAL_EXCERPT
    assert body["dates"][0]["official_url"] == _CAL_URL


# ── POST /api/decisions — the echoed field ───────────────────────────────────


_DECISION_URL = "https://rulebook.centralbank.ae/en/paid-only-page"


def _decision_match(source_id: str = "AE-1") -> dict:
    return {
        "alert_id": "draft-cbuae001",
        "source_id": source_id,
        "source_name": "CBUAE Rulebook",
        "source_url": _DECISION_URL,
        "proof": {
            "evidence_record_id": "evr_run9",
            "record_hash": "sha256:" + "a" * 64,
            "run_id": "run9",
        },
    }


def _decision_seal_handler(monkeypatch, tmp_path, user_id: int, source_id: str = "AE-1"):
    """Drive POST /api/decisions for ``user_id`` with a stubbed match."""
    import app.api as api
    import app.api_alerts as api_alerts
    import app.decision_records as decision_records

    monkeypatch.setattr(decision_records, "_BASE_DIR", tmp_path)

    handler = api._Handler.__new__(api._Handler)
    handler.command = "POST"
    handler.path = "/api/decisions"
    handler.request = MagicMock()
    handler.client_address = ("127.0.0.1", 9999)
    handler.server = MagicMock()
    handler.rfile = BytesIO(b"")
    handler.wfile = BytesIO()
    handler.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": {"Content-Length": "0"}.get(key, default)
    handler.headers = hdrs
    sent: list[tuple[dict, int]] = []
    handler._send_json = lambda data, status=200, **kw: sent.append((data, status))

    monkeypatch.setattr(api, "require_auth", lambda h: {"id": int(user_id), "email": "x@co.com"})
    monkeypatch.setattr(api_alerts, "require_auth", lambda h: {"id": int(user_id), "email": "x@co.com"})
    monkeypatch.setattr(
        api_alerts, "find_routing_match_for_user", lambda uid, alert_id, days=14: _decision_match(source_id)
    )
    handler._rate_limited = lambda *a, **kw: False
    handler._rbac_guard = lambda *a, **kw: True
    handler._read_json_strict = lambda: (
        {
            "alert_id": "draft-cbuae001",
            "kind": "reviewed",
            "statement": "I reviewed the diff against our licence scope.",
        },
        None,
    )
    handler._handle_alert_decisions_post()
    return sent[-1]


def test_free_account_decision_does_not_echo_official_url(isolated_db, monkeypatch, tmp_path):
    """The leak: the sealed decision echoed a redacted field straight back."""
    db.backfill_org_memberships()
    user_id = _make_paired_user("free-decision@co.com", "870001", alerts_enabled=True)
    db.backfill_org_memberships()

    body, status = _decision_seal_handler(monkeypatch, tmp_path, user_id)

    assert status == 201
    reviewed = body["decision"]["content"]["reviewed"]
    assert reviewed["official_url"] == ""
    # Identity + sealed pointer survive — the decision still binds to what was
    # reviewed, only the withheld field is empty.
    assert reviewed["alert_id"] == "draft-cbuae001"
    assert reviewed["evidence_record_id"] == "evr_run9"
    assert _DECISION_URL not in json.dumps(body)


def test_paid_account_decision_keeps_official_url(isolated_db, monkeypatch, tmp_path):
    from app.plan import activate_plan

    user_id = _make_paired_user("paid-decision@co.com", "870002", alerts_enabled=True)
    db.backfill_org_memberships()
    activate_plan(user_id, "professional")

    body, status = _decision_seal_handler(monkeypatch, tmp_path, user_id)

    assert status == 201
    assert body["decision"]["content"]["reviewed"]["official_url"] == _DECISION_URL


def test_free_owner_custom_source_decision_keeps_official_url(
    isolated_db, monkeypatch, tmp_path
):
    user_id = _make_paired_user("free-custom-decision@co.com", "870003", alerts_enabled=True)
    db.backfill_org_memberships()

    body, status = _decision_seal_handler(
        monkeypatch, tmp_path, user_id, source_id="custom-abcd1234"
    )

    assert status == 201
    assert body["decision"]["content"]["reviewed"]["official_url"] == _DECISION_URL


def test_flag_off_restores_decision_official_url(isolated_db, monkeypatch, tmp_path):
    monkeypatch.setenv("STATUTEPROOF_ALERTS_REQUIRE_PLAN", "0")
    user_id = _make_paired_user("free-decision-off@co.com", "870004", alerts_enabled=True)
    db.backfill_org_memberships()

    body, status = _decision_seal_handler(monkeypatch, tmp_path, user_id)

    assert status == 201
    assert body["decision"]["content"]["reviewed"]["official_url"] == _DECISION_URL


# ---------------------------------------------------------------------------
# Architectural guard: the lesson of this escalation is that redaction applied
# in ONE handler is re-opened by the next sibling reader. This test FAILS when a
# handler in app/api.py builds or forwards official-source excerpt-class content
# without routing it through an entitlement gate — so a NEW reader cannot be
# added without either gating it or consciously allowlisting it here.
# ---------------------------------------------------------------------------


# Tokens that mean "this handler touches official-source excerpt-class content"
# (verbatim changed text, the generated summary of it, or a builder that emits
# either).
_EXCERPT_MARKERS = (
    "diff_excerpt",
    "executive_summary",
    "upcoming_key_dates",
    "build_redline_for_match",
    "build_routing_preview_for_user",
    "find_routing_match_for_user",
)
# Any ONE of these in the handler body counts as "entitlement was considered".
_ENTITLEMENT_GATES = (
    "_official_alert_blocked_by_plan",
    "redact_preview_for_plan",
    "redact_effective_dates_for_plan",
    "redact_decision_reviewed_for_plan",
    "redact_official_item_for_plan",
    "_require_capability",
)
# Handlers that legitimately touch a marker without a plan gate, each with the
# reason. Adding to this set is a deliberate, reviewable act.
_ENTITLEMENT_EXEMPT_HANDLERS: dict[str, str] = {}


def _api_handler_bodies() -> dict[str, str]:
    import ast

    src = (Path(__file__).resolve().parents[1] / "app" / "api.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    lines = src.splitlines()
    bodies: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_handle_"):
            bodies[node.name] = "\n".join(lines[node.lineno - 1 : (node.end_lineno or node.lineno)])
    return bodies


def test_every_api_handler_touching_official_excerpts_is_entitlement_gated():
    ungated = []
    for name, body in _api_handler_bodies().items():
        if name in _ENTITLEMENT_EXEMPT_HANDLERS:
            continue
        if not any(marker in body for marker in _EXCERPT_MARKERS):
            continue
        if any(gate in body for gate in _ENTITLEMENT_GATES):
            continue
        ungated.append(name)

    assert ungated == [], (
        "These app/api.py handlers serve official-source excerpt-class content "
        f"with no entitlement gate: {ungated}. Route the payload through "
        "app.alert_routing.redact_official_item_for_plan (or a per-surface "
        "adapter built on it), or add an explicit reason to "
        "_ENTITLEMENT_EXEMPT_HANDLERS."
    )
