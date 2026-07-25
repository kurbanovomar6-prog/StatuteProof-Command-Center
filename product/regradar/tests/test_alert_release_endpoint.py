"""Releasing an alert over HTTP, and the safety gate that was missing.

Releasing used to require SSH: `run.py alert-review approve` was the only caller
of review_alert able to name an approve_* action. Measured with
tools/measure_alert_release_axis.py — every candidate route returned 404.

The gate this endpoint fronts is the one standing between a draft and every
customer's Telegram, so most of what is pinned here is refusal, not success.

THE BUG THIS FILE EXISTS FOR: review_alert applied its safety-issue block ONLY
to approve_urgent. But "weekly" is a cadence, not a smaller blast radius —
alert_routing._get_approved_statuses admits both approved statuses, and
digest_cadence._is_instant routes on risk_level, never on send_decision. So
approving a HIGH-risk draft with INCOMPLETE proof "for weekly" was a
zero-friction instant send to every matched customer, and the option that reads
as the cautious one was the unguarded one.
"""

from __future__ import annotations

import json
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.alert_review as alert_review  # noqa: E402
import app.api as api  # noqa: E402
import app.api_alert_review as api_alert_review  # noqa: E402
from app.api import _Handler  # noqa: E402

FOUNDER = {"id": 1, "email": "founder@statuteproof.com"}


def _handler(method: str, path: str, body: dict | None = None) -> _Handler:
    raw = json.dumps(body or {}).encode("utf-8")
    header_map = {"Content-Length": str(len(raw)), "X-Real-IP": "10.0.0.9"}

    h = _Handler.__new__(_Handler)
    h.command = method
    h.path = path
    h.request = MagicMock()
    h.client_address = ("127.0.0.1", 9999)
    h.server = MagicMock()
    h.rfile = BytesIO(raw)
    h.wfile = BytesIO()
    h.close_connection = False
    hdrs = MagicMock()
    hdrs.get = lambda key, default="": header_map.get(key, default)
    h.headers = hdrs
    sent: list[tuple[dict, int]] = []
    h._send_json = lambda data, status=200, **kw: sent.append((data, status))  # type: ignore[method-assign]
    h._sent = sent  # type: ignore[attr-defined]
    return h


def _post(body: dict) -> tuple[dict, int]:
    h = _handler("POST", "/api/admin/alert-review", body)
    h.do_POST()
    return h._sent[-1]  # type: ignore[attr-defined]


def _get_queue() -> tuple[dict, int]:
    h = _handler("GET", "/api/admin/alert-review-queue")
    h.do_GET()
    return h._sent[-1]  # type: ignore[attr-defined]


def _write_draft(base: Path, alert_id: str, *, risky: bool) -> None:
    folder = base / "data" / "source_snapshots" / "2026-07-26" / "AE" / "AE-vara" / alert_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "diff.json").write_text(json.dumps({"diff_quality": "GOOD"}), encoding="utf-8")
    (folder / "alert_draft.json").write_text(json.dumps({
        "alert_id": alert_id,
        "review_status": "DRAFT",
        "send_decision": "HOLD_FOR_REVIEW",
        "market": "AE",
        "source_id": "AE-vara",
        "source_name": "VARA",
        "checked_at_utc": "2026-07-26T10:00:00+00:00",
        "change_type": "LICENSING",
        # HIGH risk is exactly what makes an approval dispatch INSTANTLY.
        "risk_level": "HIGH" if risky else "MEDIUM",
        "confidence": "LOW" if risky else "MEDIUM",
        "limitations": [],
        "proof_block": {
            "proof_quality": "INCOMPLETE" if risky else "GOOD",
            "meaningful_change_detected": True,
            "diff_json_path": f"data/source_snapshots/2026-07-26/AE/AE-vara/{alert_id}/diff.json",
        },
    }, indent=2), encoding="utf-8")


@pytest.fixture()
def founder_session(tmp_path, monkeypatch):
    """Two drafts on disk, an authenticated founder, and no rate limiting."""
    monkeypatch.setattr(alert_review, "_BASE_DIR", tmp_path)
    monkeypatch.setattr(
        alert_review, "_REVIEW_FILE", tmp_path / "data" / "alert_reviews" / "reviews.jsonl"
    )
    monkeypatch.setattr(api, "require_auth", lambda handler: dict(FOUNDER))
    monkeypatch.setattr(api_alert_review, "require_auth", lambda handler: dict(FOUNDER))
    monkeypatch.setattr(_Handler, "_admin_guard", lambda self, user, **kw: True)
    monkeypatch.setattr(_Handler, "_rate_limited", lambda self, *a, **k: False)

    _write_draft(tmp_path, "draft-clean", risky=False)
    _write_draft(tmp_path, "draft-risky", risky=True)
    return tmp_path


# ── the safety gate that was missing ────────────────────────────────────────


def test_a_weekly_approval_is_safety_gated_like_an_urgent_one(founder_session):
    """The bug: "weekly" gated nothing, yet a HIGH-risk weekly approval sends
    INSTANTLY to every matched customer."""
    body, status = _post({"alert_id": "draft-risky", "action": "approve_weekly"})

    assert status == 409, body
    assert body["code"] == "safety_blocked"
    assert "proof_quality is INCOMPLETE" in body["safety_issues"]
    assert "confidence is LOW" in body["safety_issues"]
    assert alert_review.latest_review_for("draft-risky") is None, (
        "a blocked approval must leave no review record"
    )


def test_the_cli_gets_the_same_gate(founder_session):
    """The fix lives in review_alert, not the handler, so the SSH path — the one
    actually used in production today — is protected too."""
    with pytest.raises(alert_review.ApprovalBlocked) as caught:
        alert_review.review_alert(
            alert_id="draft-risky", action="approve_weekly",
            reviewer="Omar", note="", base_dir=founder_session,
            review_file=founder_session / "data" / "alert_reviews" / "reviews.jsonl",
        )
    assert "proof_quality is INCOMPLETE" in caught.value.safety_issues


def test_forcing_without_a_note_is_refused(founder_session):
    body, status = _post({
        "alert_id": "draft-risky", "action": "approve_weekly", "force": True,
    })
    assert status == 400, body
    assert alert_review.latest_review_for("draft-risky") is None


def test_forcing_with_a_note_releases_and_records_why(founder_session):
    body, status = _post({
        "alert_id": "draft-risky", "action": "approve_weekly", "force": True,
        "note": "Confirmed against the regulator page by hand.",
    })
    assert status == 200, body
    record = alert_review.latest_review_for("draft-risky") or {}
    assert record["force"] is True
    assert "by hand" in record["review_note"]
    assert record["safety_issues"], "the override must record what was overridden"


def test_force_must_be_a_real_boolean(founder_session):
    """Python truthiness would read the string "false" as True — a typo would
    silently become a safety override."""
    body, status = _post({
        "alert_id": "draft-risky", "action": "approve_weekly", "force": "false",
        "note": "n",
    })
    assert status == 400, body


# ── attribution ─────────────────────────────────────────────────────────────


def test_the_reviewer_comes_from_the_session_not_the_body(founder_session):
    _post({"alert_id": "draft-clean", "action": "approve_weekly", "note": "ok"})

    record = alert_review.latest_review_for("draft-clean") or {}
    assert record["reviewer"] == FOUNDER["email"]


def test_a_supplied_reviewer_is_refused_not_ignored(founder_session):
    """Silently dropping it would let a caller believe they had attributed the
    decision to someone else."""
    body, status = _post({
        "alert_id": "draft-clean", "action": "approve_weekly",
        "reviewer": "Someone Else",
    })
    assert status == 400, body
    assert body["code"] == "forbidden_field"
    assert alert_review.latest_review_for("draft-clean") is None


@pytest.mark.parametrize("field", ["base_dir", "review_file"])
def test_the_body_cannot_redirect_where_the_trail_is_written(founder_session, field):
    body, status = _post({
        "alert_id": "draft-clean", "action": "approve_weekly", field: "/tmp/evil",
    })
    assert status == 400, body


# ── refusals ────────────────────────────────────────────────────────────────


def test_an_unknown_action_is_refused(founder_session):
    body, status = _post({"alert_id": "draft-clean", "action": "approve_everything"})
    assert status == 400, body
    assert body["code"] == "unknown_action"


def test_a_missing_alert_is_a_clean_404(founder_session):
    body, status = _post({"alert_id": "no-such-draft", "action": "reject"})
    assert status == 404, body


def test_an_unauthenticated_caller_is_refused(founder_session, monkeypatch):
    monkeypatch.setattr(api, "require_auth", lambda handler: None)
    monkeypatch.setattr(api_alert_review, "require_auth", lambda handler: None)

    assert _post({"alert_id": "draft-clean", "action": "approve_weekly"})[1] == 401
    assert _get_queue()[1] == 401


def test_a_non_founder_cannot_release_and_learns_nothing(founder_session, monkeypatch):
    """The guard runs before the draft lookup, so a refused caller cannot use the
    endpoint to discover which alert ids exist."""
    refused: list[tuple[dict, int]] = []

    def _deny(self, user, **kw):
        # Faithful to the real guard, which sends its own generic 403 and audits
        # the denial before returning False.
        self._send_json({"ok": False, "message": "Not available."}, 403)
        return False

    monkeypatch.setattr(_Handler, "_admin_guard", _deny)

    for alert_id in ("draft-clean", "definitely-not-a-real-alert"):
        body, status = _post({"alert_id": alert_id, "action": "approve_weekly"})
        refused.append((body, status))

    assert all(s != 200 for _, s in refused)
    assert refused[0] == refused[1], "the responses differ — that is an existence oracle"
    assert alert_review.latest_review_for("draft-clean") is None


# ── the queue ───────────────────────────────────────────────────────────────


def test_the_queue_states_the_real_blast_radius(founder_session):
    """A HIGH-risk draft dispatches instantly whichever approval is chosen, so
    the queue must not let the operator believe "weekly" means later."""
    body, status = _get_queue()
    assert status == 200

    risky = next(r for r in body["alerts"] if r["alert_id"] == "draft-risky")
    assert "instant" in risky["delivery_if_approved"].lower()
    assert risky["safety_issues"]


def test_one_unreadable_draft_does_not_blank_the_queue(founder_session):
    """A monitoring run killed mid-write leaves a draft truncated inside a
    multi-byte character. That used to abort the whole scan, taking every other
    alert down with it — and the only fix was a shell, which is the dependency
    this endpoint exists to remove."""
    broken = founder_session / "data" / "source_snapshots" / "2026-07-26" / "AE" / "AE-vara" / "broken"
    broken.mkdir(parents=True, exist_ok=True)
    (broken / "alert_draft.json").write_bytes(b'{"alert_id": "x\xff\xfe')

    body, status = _get_queue()
    assert status == 200, body
    assert {r["alert_id"] for r in body["alerts"]} >= {"draft-clean", "draft-risky"}

    # And the other alerts stay releasable.
    assert _post({"alert_id": "draft-clean", "action": "approve_weekly", "note": "ok"})[1] == 200


def test_an_approved_alert_leaves_the_actionable_queue(founder_session):
    _post({"alert_id": "draft-clean", "action": "approve_weekly", "note": "ok"})

    body, _ = _get_queue()
    assert "draft-clean" not in {r["alert_id"] for r in body["alerts"]}

    h = _handler("GET", "/api/admin/alert-review-queue?all=1")
    h.do_GET()
    assert "draft-clean" in {r["alert_id"] for r in h._sent[-1][0]["alerts"]}  # type: ignore[attr-defined]


# ── the response ────────────────────────────────────────────────────────────


def test_the_response_does_not_leak_server_paths(founder_session):
    body, status = _post({"alert_id": "draft-clean", "action": "approve_weekly", "note": "ok"})
    assert status == 200
    assert not [k for k in body["record"] if k.endswith("_path")]
    assert str(founder_session) not in json.dumps(body)


def test_success_says_recorded_not_sent(founder_session):
    """Delivery is gated again downstream, so a 200 here is a decision — claiming
    it was sent would be a promise this endpoint cannot keep."""
    body, _ = _post({"alert_id": "draft-clean", "action": "approve_urgent", "note": "ok"})
    assert "recorded" in body["message"].lower()
    assert "sent" not in body["message"].lower()
