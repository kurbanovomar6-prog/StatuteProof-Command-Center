"""Tests for email_delivery.py activation features — Feature 4."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from app.email_delivery import build_monitoring_brief_email, deliver_brief_email
from app.evidence_assessment import LEGAL_DISCLAIMER

_FORBIDDEN_SUBJECT_WORDS = ("guarantee", "certified", "legal advice", "prevent fines")


def _sample_payload(**overrides) -> dict:
    base = build_monitoring_brief_email(
        brief_markdown="## Change detected\n\nMinor update to the page.",
        source_name="CBUAE Publications",
        risk_level="LOW",
        client_name="Test Corp",
        client_email="test@example.com",
    )
    base.update(overrides)
    return base


# ── Test 1: body_text includes disclaimer ─────────────────────────────────────

def test_build_monitoring_brief_email_includes_disclaimer_in_body_text():
    """build_monitoring_brief_email must include LEGAL_DISCLAIMER in body_text."""
    payload = build_monitoring_brief_email(
        brief_markdown="Some brief content.",
        source_name="DFSA Publications",
        risk_level="MEDIUM",
    )
    assert LEGAL_DISCLAIMER in payload["body_text"]


# ── Test 2: body_html includes disclaimer ─────────────────────────────────────

def test_build_monitoring_brief_email_includes_disclaimer_in_body_html():
    """build_monitoring_brief_email must include LEGAL_DISCLAIMER in body_html."""
    payload = build_monitoring_brief_email(
        brief_markdown="Some brief content.",
        source_name="DFSA Publications",
        risk_level="HIGH",
    )
    assert LEGAL_DISCLAIMER in payload["body_html"]


# ── Test 3: subject does not contain forbidden words ─────────────────────────

def test_build_monitoring_brief_email_subject_no_forbidden_words():
    """The email subject must not contain any forbidden claim phrases."""
    payload = build_monitoring_brief_email(
        brief_markdown="Brief content.",
        source_name="VARA Website",
        risk_level="HIGH",
    )
    subject_lower = payload["subject"].lower()
    for word in _FORBIDDEN_SUBJECT_WORDS:
        assert word.lower() not in subject_lower, f"Forbidden word in subject: '{word}'"


# ── Test 4: disclaimer not duplicated when already in brief ───────────────────

def test_build_monitoring_brief_email_no_duplicate_disclaimer():
    """When brief_markdown already contains LEGAL_DISCLAIMER, it must not be duplicated."""
    brief_with_disclaimer = f"Some content.\n\n{LEGAL_DISCLAIMER}"
    payload = build_monitoring_brief_email(
        brief_markdown=brief_with_disclaimer,
        source_name="CBUAE",
        risk_level="LOW",
    )
    count = payload["body_text"].count(LEGAL_DISCLAIMER)
    assert count == 1, f"LEGAL_DISCLAIMER appears {count} times; expected exactly 1"


# ── Test 5: local_outbox writes a .json file ──────────────────────────────────

def test_deliver_brief_email_local_outbox_writes_json_file():
    """With local_outbox provider, deliver_brief_email must write a .json file to outbox."""
    payload = _sample_payload()
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        env = {"STATUTEPROOF_EMAIL_PROVIDER": "local_outbox"}
        result = deliver_brief_email(payload, source_id="cbuae-test", env=env, base_dir=base)
        # Check inside the with-block so the temp dir still exists
        assert result["status"] == "queued_local"
        outbox_path = Path(result["outbox_path"])
        assert outbox_path.exists(), f"Outbox file not found: {outbox_path}"
        assert outbox_path.suffix == ".json"
        data = json.loads(outbox_path.read_text(encoding="utf-8"))
        assert "subject" in data


# ── Test 6: send_enabled=false queues locally with reason ─────────────────────

def test_deliver_brief_email_send_disabled_queues_locally():
    """When SEND_ENABLED is not true and provider is non-local, queue locally with reason=send_not_enabled."""
    payload = _sample_payload()
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        env = {
            "STATUTEPROOF_EMAIL_PROVIDER": "sendgrid",
            "STATUTEPROOF_EMAIL_FROM": "noreply@statuteproof.com",
            "SENDGRID_API_KEY": "test-key-123",
            "STATUTEPROOF_EMAIL_SEND_ENABLED": "false",
        }
        result = deliver_brief_email(payload, source_id="test-source", env=env, base_dir=base)
    assert result["status"] == "queued_local"
    assert result.get("reason") == "send_not_enabled"
