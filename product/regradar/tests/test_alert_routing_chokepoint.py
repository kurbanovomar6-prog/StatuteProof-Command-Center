"""Fail-closed / legal-safety branches of the shared alert-delivery choke point.

``app.alert_routing.send_preview_alert_to_user`` is the single per-user choke
point that BOTH the dashboard handler (POST /api/delivery/send-preview-alert)
and the scheduler's instant/digest dispatch funnel through. Three guards on
that path must fail SAFE, and this module drives each one directly (in-process,
no network) so a future regression that quietly re-opens the hole fails loudly:

  * ``_is_still_approved`` — a preview only ships while the review is still an
    approved status; a missing review, a rescinded status, OR an import failure
    of the review module must all read as NOT approved (fail closed).

  * ``_official_alert_blocked_by_plan`` — the per-user paid-content gate. Any
    unexpected internal failure must gate the alert as OFFICIAL (return True),
    never fall open and deliver the paid deliverable to a free account.

  * SF-4 hold — the final-bytes forbidden-claims guard. If
    ``build_alert_telegram_message`` raises ``ForbiddenClaimError`` on the very
    bytes about to ship (a reviewer missed a banned phrase, or the draft echoed
    source text), the send path must HOLD the alert for review — record it and
    return code ``held_forbidden`` — instead of delivering it or 500-ing.

Pure-additive coverage: no production code is changed here.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import alert_routing
from app.legal_safety import ForbiddenClaimError


# --------------------------------------------------------------------------- #
# _is_still_approved — negative + import-fail fail closed (lines 652-657)
# --------------------------------------------------------------------------- #

def test_is_still_approved_false_when_no_review(monkeypatch):
    """No review row for the alert id → not approved."""
    import app.alert_review as alert_review

    monkeypatch.setattr(alert_review, "latest_review_for", lambda alert_id: None)

    assert alert_routing._is_still_approved("alert-1") is False


def test_is_still_approved_false_for_rescinded_status(monkeypatch):
    """A review that exists but is no longer an approved status → not approved."""
    import app.alert_review as alert_review

    monkeypatch.setattr(
        alert_review,
        "latest_review_for",
        lambda alert_id: {"new_status": "REJECTED"},
    )

    assert alert_routing._is_still_approved("alert-1") is False


def test_is_still_approved_false_when_review_module_unimportable(monkeypatch):
    """If the review module can't be imported, the guard must read NOT approved.

    Drives the ``except Exception: return False`` at lines 654-655 by replacing
    ``app.alert_review`` in sys.modules with a module object that lacks
    ``latest_review_for`` — so the in-function ``from app.alert_review import
    latest_review_for`` raises ImportError.
    """
    broken = types.ModuleType("app.alert_review")  # no latest_review_for attr
    monkeypatch.setitem(sys.modules, "app.alert_review", broken)

    assert alert_routing._is_still_approved("alert-1") is False


def test_is_still_approved_true_for_approved_status(monkeypatch):
    """Positive control: proves the negative assertions above are not tautologies."""
    import app.alert_review as alert_review

    monkeypatch.setattr(
        alert_review,
        "latest_review_for",
        lambda alert_id: {"new_status": alert_review.STATUS_APPROVED_URGENT},
    )

    assert alert_routing._is_still_approved("alert-1") is True


# --------------------------------------------------------------------------- #
# _official_alert_blocked_by_plan — fail CLOSED on exception (lines 691-693)
# --------------------------------------------------------------------------- #

def test_official_alert_blocked_fail_closed_on_exception(monkeypatch):
    """Any unexpected internal failure gates the alert as OFFICIAL (True).

    ``alerts_require_plan`` is made to raise, so the outer ``try`` in
    ``_official_alert_blocked_by_plan`` blows up and the fail-closed
    ``except Exception: return True`` at lines 691-693 must run.
    """
    import app.telegram_pairing as telegram_pairing

    def _boom() -> bool:
        raise RuntimeError("plan backend unavailable")

    monkeypatch.setattr(telegram_pairing, "alerts_require_plan", _boom)

    assert alert_routing._official_alert_blocked_by_plan(42, "src-1") is True


def test_official_alert_not_blocked_when_plan_not_required(monkeypatch):
    """Control: with gating switched OFF the choke returns False (does not block).

    Proves the True above is a genuine reaction to failure, not an
    unconditional deny.
    """
    import app.telegram_pairing as telegram_pairing

    monkeypatch.setattr(telegram_pairing, "alerts_require_plan", lambda: False)

    assert alert_routing._official_alert_blocked_by_plan(42, "src-1") is False


def test_official_alert_blocked_when_required_and_user_not_eligible(monkeypatch):
    """Control: gating ON + ineligible user + official source → blocked (True).

    Exercises the normal-path deny at line 690 so the exception test is not the
    only True-producing branch under coverage.
    """
    import app.tenancy as tenancy
    import app.telegram_pairing as telegram_pairing

    monkeypatch.setattr(telegram_pairing, "alerts_require_plan", lambda: True)
    monkeypatch.setattr(tenancy, "is_custom_source", lambda source_id: False)
    monkeypatch.setattr(telegram_pairing, "plan_eligible_user_ids", lambda ids: [])

    assert alert_routing._official_alert_blocked_by_plan(42, "src-1") is True


# --------------------------------------------------------------------------- #
# SF-4 — send_preview_alert_to_user HOLDS on ForbiddenClaimError (926-947)
# --------------------------------------------------------------------------- #

def _wire_deliverable_preview(monkeypatch):
    """Drive send_preview_alert_to_user to the message-build step.

    Stubs every guard BEFORE the SF-4 build so the alert reaches
    ``build_alert_telegram_message`` as "ready, approved, in-plan, connected".
    Returns spies for the delivery primitives so a test can assert nothing
    actually shipped.
    """
    match = {
        "alert_id": "A-1",
        "source_id": 7,
        "delivery_ready": True,
        "title": "Reviewed change",
        "score": 91,
        "review_status": "APPROVED_FOR_URGENT",
    }
    monkeypatch.setattr(
        alert_routing,
        "build_routing_preview_for_user",
        lambda user_id: {"matches": [match]},
    )
    monkeypatch.setattr(
        alert_routing, "_official_alert_blocked_by_plan", lambda user_id, source_id: False
    )
    monkeypatch.setattr(alert_routing, "_is_still_approved", lambda alert_id: True)
    monkeypatch.setattr(
        alert_routing, "get_telegram_link", lambda user_id: {"telegram_chat_id": "555"}
    )
    monkeypatch.setattr(
        alert_routing, "user_profile_to_routing_profile", lambda user_id: {"markets": ["UAE"]}
    )

    delivery_calls: list = []
    monkeypatch.setattr(
        alert_routing,
        "create_delivery_log",
        lambda *a, **k: delivery_calls.append((a, k)) or {"created": True, "id": 1},
    )
    sent: list = []
    monkeypatch.setattr(
        alert_routing,
        "send_telegram_message",
        lambda *a, **k: sent.append((a, k)) or True,
    )
    return match, delivery_calls, sent


def test_send_preview_holds_alert_on_forbidden_claim(monkeypatch, tmp_path):
    """A banned claim in the FINAL bytes → hold + code 'held_forbidden', no send.

    ``build_alert_telegram_message`` raises ``ForbiddenClaimError`` on the bytes
    about to ship. The choke point must:
      * NOT deliver (no delivery log created, no telegram send),
      * durably record the hold via ``record_held_alert``,
      * return ``{"ok": False, "code": "held_forbidden"}``.
    """
    import app.review_queue as review_queue

    match, delivery_calls, sent = _wire_deliverable_preview(monkeypatch)

    def _raise_forbidden(user_profile, alert_match):
        raise ForbiddenClaimError("guarantee compliance")

    monkeypatch.setattr(alert_routing, "build_alert_telegram_message", _raise_forbidden)
    # Redirect the durable hold store into the test's tmp dir so the real
    # record_held_alert runs end-to-end (genuine, not mocked) and is verifiable.
    monkeypatch.setattr(review_queue, "_BASE_DIR", tmp_path)

    result = alert_routing.send_preview_alert_to_user(99, "A-1")

    # Held, not delivered.
    assert result["ok"] is False
    assert result["code"] == "held_forbidden"
    assert delivery_calls == [], "must not create a delivery log for a held alert"
    assert sent == [], "must not send a telegram message for a held alert"

    # Durably recorded for human review, with the failing context preserved.
    holds = review_queue.list_held_alerts(base_dir=tmp_path)
    assert len(holds) == 1
    hold = holds[0]
    assert hold["reason"] == "forbidden_claim_in_reviewed_preview"
    assert hold["customer_delivery_approved"] is False
    assert hold["context"]["alert_id"] == "A-1"
    assert hold["context"]["user_id"] == 99
    assert hold["context"]["source_id"] == 7
    assert "guarantee compliance" in hold["context"]["detail"]


def test_send_preview_hold_survives_record_failure(monkeypatch, tmp_path):
    """Even if the hold-store write itself fails, the path still WITHHOLDS.

    Exercises the defensive inner ``except`` (lines 945-946): a failure to
    persist the hold must not turn into a delivery or a 500 — the caller still
    gets ``held_forbidden`` and nothing ships.
    """
    import app.review_queue as review_queue

    _match, delivery_calls, sent = _wire_deliverable_preview(monkeypatch)

    monkeypatch.setattr(
        alert_routing,
        "build_alert_telegram_message",
        lambda user_profile, alert_match: (_ for _ in ()).throw(
            ForbiddenClaimError("prevent fines")
        ),
    )

    def _hold_boom(*a, **k):
        raise RuntimeError("hold store offline")

    monkeypatch.setattr(review_queue, "record_held_alert", _hold_boom)

    result = alert_routing.send_preview_alert_to_user(99, "A-1")

    assert result["ok"] is False
    assert result["code"] == "held_forbidden"
    assert delivery_calls == []
    assert sent == []
