"""Behavioral coverage for app.telegram — the paid alert-delivery module.

These tests exercise the runtime-critical paths that existing suites do not:

* ``send_telegram_message`` — the actual HTTP send, the Markdown->plain-text
  retry on a 400 parse error, timeout handling, generic-exception handling, and
  the missing-token / missing-chat_id guards.
* ``_safe`` — dynamic-content truncation + Markdown-marker stripping.
* ``_requires_human_review`` — the bool-confidence guard and numeric-string
  confidence parsing branches.
* ``_deliver_alert_to_subscribed_users`` — recipient-resolution failure (fail
  to 0) and a per-recipient send that raises (counted, never propagated).
* ``send_telegram_alert`` — below-threshold skip, and the pilot founder-chat
  fallback (admin bot) plus its email fallback when the founder send fails.

All network I/O is mocked; no live endpoint is ever contacted.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PRODUCT_DIR = str(Path(__file__).resolve().parents[1])
if PRODUCT_DIR not in sys.path:
    sys.path.insert(0, PRODUCT_DIR)

import app.telegram as tg


class _FakeResp:
    """Minimal stand-in for a ``requests`` Response."""

    def __init__(self, status_code=200, payload=None, content=b"{}"):
        self.status_code = status_code
        self._payload = payload if payload is not None else {"ok": True}
        self.content = content

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise tg.requests.HTTPError(f"HTTP {self.status_code}")


# ══════════════════════════════════════════════════════════════════════════
# send_telegram_message — HTTP send, retry, timeout, error handling
# ══════════════════════════════════════════════════════════════════════════

def test_send_message_returns_true_on_ok(monkeypatch):
    calls = []
    monkeypatch.setattr("app.telegram_settings.get_token", lambda: "TOK")

    def _post(url, json, timeout):
        calls.append((url, json))
        return _FakeResp(200, {"ok": True})

    monkeypatch.setattr(tg.requests, "post", _post)

    assert tg.send_telegram_message("999", "hello") is True
    # Correct bot URL + chat_id stringified + preview disabled.
    url, payload = calls[0]
    assert url == "https://api.telegram.org/botTOK/sendMessage"
    assert payload["chat_id"] == "999"
    assert payload["disable_web_page_preview"] is True
    # No parse_mode was requested, so none is sent.
    assert "parse_mode" not in payload


def test_send_message_skipped_when_token_missing(monkeypatch):
    monkeypatch.setattr("app.telegram_settings.get_token", lambda: "")
    # requests.post must never be reached.
    monkeypatch.setattr(
        tg.requests, "post",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no send without token")),
    )
    assert tg.send_telegram_message("999", "hello") is False


def test_send_message_skipped_when_chat_id_blank(monkeypatch):
    monkeypatch.setattr("app.telegram_settings.get_token", lambda: "TOK")
    monkeypatch.setattr(
        tg.requests, "post",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no send without chat_id")),
    )
    assert tg.send_telegram_message("   ", "hello") is False


def test_send_message_markdown_parse_error_retries_as_plaintext(monkeypatch):
    monkeypatch.setattr("app.telegram_settings.get_token", lambda: "TOK")
    seen_modes = []

    def _post(url, json, timeout):
        seen_modes.append(json.get("parse_mode"))
        if json.get("parse_mode") == "Markdown":
            return _FakeResp(400, {"ok": False, "description": "can't parse entities"})
        return _FakeResp(200, {"ok": True})

    monkeypatch.setattr(tg.requests, "post", _post)

    assert tg.send_telegram_message("999", "*bad* markup", parse_mode="Markdown") is True
    # First attempt with Markdown (rejected), retried without parse_mode.
    assert seen_modes == ["Markdown", None]


def test_send_message_non_400_error_does_not_retry(monkeypatch):
    monkeypatch.setattr("app.telegram_settings.get_token", lambda: "TOK")
    attempts = []

    def _post(url, json, timeout):
        attempts.append(json.get("parse_mode"))
        # 403 (e.g. bot blocked) is not a parse error -> no plain-text retry.
        return _FakeResp(403, {"ok": False, "description": "bot was blocked"})

    monkeypatch.setattr(tg.requests, "post", _post)

    assert tg.send_telegram_message("999", "x", parse_mode="Markdown") is False
    assert attempts == ["Markdown"]  # never retried


def test_send_message_timeout_returns_false(monkeypatch):
    monkeypatch.setattr("app.telegram_settings.get_token", lambda: "TOK")

    def _post(url, json, timeout):
        raise tg.requests.Timeout("slow")

    monkeypatch.setattr(tg.requests, "post", _post)
    assert tg.send_telegram_message("999", "x") is False


def test_send_message_generic_exception_returns_false(monkeypatch):
    monkeypatch.setattr("app.telegram_settings.get_token", lambda: "TOK")

    def _post(url, json, timeout):
        raise ValueError("socket exploded")

    monkeypatch.setattr(tg.requests, "post", _post)
    assert tg.send_telegram_message("999", "x") is False


def test_send_message_empty_content_response_treated_as_no_json(monkeypatch):
    monkeypatch.setattr("app.telegram_settings.get_token", lambda: "TOK")

    def _post(url, json, timeout):
        # content == b"" -> module skips .json() and treats data as {}
        return _FakeResp(200, payload={"boom": "should-not-read"}, content=b"")

    monkeypatch.setattr(tg.requests, "post", _post)
    # data.get("ok") is falsy because data == {} -> API-error branch -> False.
    assert tg.send_telegram_message("999", "x") is False


# ══════════════════════════════════════════════════════════════════════════
# _safe — truncation + Markdown-marker stripping of dynamic content
# ══════════════════════════════════════════════════════════════════════════

def test_safe_strips_markdown_markers():
    out = tg._safe("*bold* _it_ `code` [link]", 100)
    for marker in ("*", "_", "`", "[", "]"):
        assert marker not in out
    assert "bold" in out and "code" in out


def test_safe_truncates_and_appends_ellipsis():
    out = tg._safe("x" * 50, 10)
    assert out == "x" * 10 + "…"
    assert len(out) == 11  # 10 chars + one ellipsis glyph


def test_safe_returns_short_text_unchanged():
    assert tg._safe("short", 100) == "short"


# ══════════════════════════════════════════════════════════════════════════
# _requires_human_review — confidence-branch edge cases
# ══════════════════════════════════════════════════════════════════════════

def test_review_gate_bool_confidence_is_ignored_not_treated_as_number():
    # bool is a subclass of int; confidence=True must NOT be read as 1.0 (pass)
    # nor crash — it is nulled and, with a clean MEDIUM run, no hold is required.
    assert tg._requires_human_review(
        {"risk_level": "MEDIUM", "confidence": True}
    ) == ""


def test_review_gate_numeric_string_below_floor_holds():
    reason = tg._requires_human_review(
        {"risk_level": "MEDIUM", "confidence": "0.42"}
    )
    assert "0.42" in reason and "0.7" in reason


def test_review_gate_numeric_string_above_floor_passes():
    assert tg._requires_human_review(
        {"risk_level": "MEDIUM", "confidence": "0.95"}
    ) == ""


def test_review_gate_unparseable_string_confidence_passes():
    # Non-numeric, non-"low" string cannot be scored -> no hold on that axis.
    assert tg._requires_human_review(
        {"risk_level": "MEDIUM", "confidence": "n/a"}
    ) == ""


def test_review_gate_high_risk_always_holds():
    assert tg._requires_human_review({"risk_level": "HIGH"}).startswith("risk_level HIGH")


def test_review_gate_review_required_flag_holds():
    reason = tg._requires_human_review(
        {"risk_level": "MEDIUM", "review_required": True, "confidence": "high"}
    )
    assert reason == "review_required flag set"


# ══════════════════════════════════════════════════════════════════════════
# _deliver_alert_to_subscribed_users — resolution failure + per-send raise
# ══════════════════════════════════════════════════════════════════════════

def test_deliver_returns_zero_when_recipient_resolution_raises(monkeypatch):
    # get_all_linked_chat_ids blowing up must fail to 0, never propagate.
    monkeypatch.setattr(
        "app.telegram_pairing.get_all_linked_chat_ids",
        lambda: (_ for _ in ()).throw(RuntimeError("db down")),
    )
    assert tg._deliver_alert_to_subscribed_users("msg", source_id="official-x") == 0


def test_deliver_counts_only_successful_sends_when_one_raises(monkeypatch):
    monkeypatch.setattr("app.telegram_pairing.get_all_linked_chat_ids", lambda: ["a", "b", "c"])
    monkeypatch.setattr("app.telegram_pairing.alerts_require_plan", lambda: False)

    def _send(chat_id, msg, **kw):
        if chat_id == "b":
            raise RuntimeError("transient send failure")
        return True

    monkeypatch.setattr(tg, "send_telegram_message", _send)
    # a and c succeed; b raises inside the loop but is swallowed and not counted.
    assert tg._deliver_alert_to_subscribed_users("msg", source_id="official-x") == 2


def test_deliver_returns_zero_when_no_recipients(monkeypatch):
    monkeypatch.setattr("app.telegram_pairing.get_all_linked_chat_ids", lambda: [])
    monkeypatch.setattr("app.telegram_pairing.alerts_require_plan", lambda: False)
    monkeypatch.setattr(
        tg, "send_telegram_message",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no send with empty list")),
    )
    assert tg._deliver_alert_to_subscribed_users("msg", source_id="official-x") == 0


# ══════════════════════════════════════════════════════════════════════════
# send_telegram_alert — threshold skip + founder-chat pilot fallback
# ══════════════════════════════════════════════════════════════════════════

def test_alert_below_threshold_is_skipped():
    assert tg.send_telegram_alert({"risk_level": "LOW"}) is False


def _clean_medium_result():
    return {
        "risk_level": "MEDIUM",
        "review_required": False,
        "confidence": "high",
        "risk_details": {"rule": "MEDIUM_SINGLE_STRONG",
                         "matched_keywords": ["licence"], "matched_context": []},
        "source_name": "Src", "url": "https://x.gov.ae", "jurisdiction": "AE",
        "added": ["A new licence category was introduced for market operators."],
        "removed": [],
        "checked_at_utc": "2026-07-11T10:00:00Z",
        "normalized_hash": "a" * 64,
    }


def test_founder_fallback_skipped_when_admin_creds_absent(monkeypatch):
    monkeypatch.delenv("ALERT_DRY_RUN", raising=False)
    # No subscribed users AND no admin creds -> pilot fallback unavailable.
    monkeypatch.setattr(tg, "_deliver_alert_to_subscribed_users", lambda m, **kw: 0)
    monkeypatch.setattr(tg, "TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setattr(tg, "TELEGRAM_CHAT_ID", "")
    monkeypatch.setattr(
        tg.requests, "post",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not send")),
    )
    assert tg.send_telegram_alert(_clean_medium_result()) is False


def test_founder_fallback_delivers_when_no_subscribers(monkeypatch):
    monkeypatch.delenv("ALERT_DRY_RUN", raising=False)
    monkeypatch.setattr(tg, "_deliver_alert_to_subscribed_users", lambda m, **kw: 0)
    monkeypatch.setattr(tg, "TELEGRAM_BOT_TOKEN", "ADMIN")
    monkeypatch.setattr(tg, "TELEGRAM_CHAT_ID", "FOUNDER")

    posted = []

    def _post(url, json, timeout):
        posted.append((url, json))
        return _FakeResp(200, {"ok": True})

    monkeypatch.setattr(tg.requests, "post", _post)

    assert tg.send_telegram_alert(_clean_medium_result()) is True
    url, payload = posted[0]
    assert url == "https://api.telegram.org/botADMIN/sendMessage"
    assert payload["chat_id"] == "FOUNDER"
    assert payload["parse_mode"] == "Markdown"


def test_founder_send_not_ok_triggers_email_fallback_and_returns_false(monkeypatch):
    monkeypatch.delenv("ALERT_DRY_RUN", raising=False)
    monkeypatch.setattr(tg, "_deliver_alert_to_subscribed_users", lambda m, **kw: 0)
    monkeypatch.setattr(tg, "TELEGRAM_BOT_TOKEN", "ADMIN")
    monkeypatch.setattr(tg, "TELEGRAM_CHAT_ID", "FOUNDER")

    # Founder send returns ok:false -> tg_err set -> email fallback attempted.
    monkeypatch.setattr(
        tg.requests, "post",
        lambda url, json, timeout: _FakeResp(200, {"ok": False, "description": "chat not found"}),
    )

    email_calls = {}
    monkeypatch.setattr(
        "app.email_delivery.build_monitoring_brief_email",
        lambda **kw: {"payload": kw},
    )

    def _deliver(payload, source_id):
        email_calls["source_id"] = source_id
        return {"status": "queued_local"}

    monkeypatch.setattr("app.email_delivery.deliver_brief_email", _deliver)

    result = _clean_medium_result()
    result["source_id"] = "official-x"
    assert tg.send_telegram_alert(result) is False
    # The email fallback was reached for a MEDIUM (threshold) run.
    assert email_calls.get("source_id") == "official-x"


def test_founder_send_timeout_triggers_email_fallback(monkeypatch):
    monkeypatch.delenv("ALERT_DRY_RUN", raising=False)
    monkeypatch.setattr(tg, "_deliver_alert_to_subscribed_users", lambda m, **kw: 0)
    monkeypatch.setattr(tg, "TELEGRAM_BOT_TOKEN", "ADMIN")
    monkeypatch.setattr(tg, "TELEGRAM_CHAT_ID", "FOUNDER")

    def _post(url, json, timeout):
        raise tg.requests.Timeout("timed out")

    monkeypatch.setattr(tg.requests, "post", _post)

    reached = {"n": 0}
    monkeypatch.setattr(
        "app.email_delivery.build_monitoring_brief_email", lambda **kw: {"ok": True}
    )

    def _deliver(payload, source_id):
        reached["n"] += 1
        return {"status": "queued_local"}

    monkeypatch.setattr("app.email_delivery.deliver_brief_email", _deliver)

    assert tg.send_telegram_alert(_clean_medium_result()) is False
    assert reached["n"] == 1


def test_founder_email_fallback_failure_is_swallowed(monkeypatch):
    # Even if the email fallback itself raises, send_telegram_alert must not
    # propagate — it returns False cleanly.
    monkeypatch.delenv("ALERT_DRY_RUN", raising=False)
    monkeypatch.setattr(tg, "_deliver_alert_to_subscribed_users", lambda m, **kw: 0)
    monkeypatch.setattr(tg, "TELEGRAM_BOT_TOKEN", "ADMIN")
    monkeypatch.setattr(tg, "TELEGRAM_CHAT_ID", "FOUNDER")
    monkeypatch.setattr(
        tg.requests, "post",
        lambda url, json, timeout: _FakeResp(200, {"ok": False, "description": "nope"}),
    )
    monkeypatch.setattr(
        "app.email_delivery.build_monitoring_brief_email",
        lambda **kw: (_ for _ in ()).throw(RuntimeError("email builder down")),
    )
    assert tg.send_telegram_alert(_clean_medium_result()) is False


def test_dry_run_reports_not_sent_and_never_broadcasts(monkeypatch):
    monkeypatch.setenv("ALERT_DRY_RUN", "1")
    monkeypatch.setattr(
        tg, "_deliver_alert_to_subscribed_users",
        lambda m, **kw: (_ for _ in ()).throw(AssertionError("dry-run must not broadcast")),
    )
    monkeypatch.setattr(
        tg.requests, "post",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("dry-run must not send")),
    )
    assert tg.send_telegram_alert(_clean_medium_result()) is False
