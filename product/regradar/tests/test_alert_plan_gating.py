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
