"""
Cycle-2 email guardrails (owner spec):

- A MISCONFIGURED provider (selected but missing required keys) must fail
  loudly: status "error", no silent outbox fallback, failed attempt recorded.
- Configured-but-disabled providers still queue to outbox (operator choice) —
  that path must keep working AND record the attempt.
- STATUTEPROOF_EMAIL_DRY_RUN routes through the provider path with zero
  network I/O and records a dry_run attempt (future prod smoke test).
- Every deliver_brief_email outcome appends a delivery-attempt row.
"""

from __future__ import annotations

import json
import logging
import sys
import tempfile
import urllib.error
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.email_delivery import build_monitoring_brief_email, deliver_brief_email

def _payload() -> dict:
    return build_monitoring_brief_email(
        brief_markdown="## Change detected\n\nTest body.",
        source_name="Test Source",
        risk_level="MEDIUM",
        client_name="Test Corp",
        client_email="mlro@example.com",
    )


def _attempts(base: Path) -> list[dict]:
    path = base / "data" / "email_outbox" / "delivery_status.jsonl"
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def test_misconfigured_provider_fails_loudly_no_outbox_fallback(caplog):
    env = {
        "STATUTEPROOF_EMAIL_PROVIDER": "postmark",
        "STATUTEPROOF_EMAIL_SEND_ENABLED": "true",
        # POSTMARK_SERVER_TOKEN and STATUTEPROOF_EMAIL_FROM deliberately missing
    }
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        with caplog.at_level(logging.ERROR, logger="app.email_delivery"):
            result = deliver_brief_email(_payload(), source_id="s1", env=env, base_dir=base)

        assert result["status"] == "error", "misconfig must not silently queue to outbox"
        assert "missing" in json.dumps(result).lower()
        outbox = list((base / "data" / "outbox").glob("*.json")) if (base / "data" / "outbox").exists() else []
        assert outbox == [], "no outbox fallback on misconfiguration"

        rows = _attempts(base)
        assert rows, "failed delivery attempt must be recorded"
        assert rows[-1]["status"] == "failed_configuration"
        assert "EMAIL DELIVERY MISCONFIGURED" in caplog.text


def test_configured_but_disabled_queues_and_records_attempt():
    env = {
        "STATUTEPROOF_EMAIL_PROVIDER": "postmark",
        "STATUTEPROOF_EMAIL_FROM": "noreply@statuteproof.com",
        "POSTMARK_SERVER_TOKEN": "test-token",
        "STATUTEPROOF_EMAIL_SEND_ENABLED": "false",
    }
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        result = deliver_brief_email(_payload(), source_id="s2", env=env, base_dir=base)
        assert result["status"] == "queued_local"
        assert result.get("reason") == "send_not_enabled"
        rows = _attempts(base)
        assert rows and rows[-1]["status"] == "queued_local"


def test_dry_run_touches_no_network_and_records_attempt():
    env = {
        "STATUTEPROOF_EMAIL_PROVIDER": "postmark",
        "STATUTEPROOF_EMAIL_FROM": "noreply@statuteproof.com",
        "POSTMARK_SERVER_TOKEN": "test-token",
        "STATUTEPROOF_EMAIL_SEND_ENABLED": "true",
        "STATUTEPROOF_EMAIL_DRY_RUN": "true",
    }

    def _no_network(*a, **k):
        raise AssertionError("network I/O attempted during DRY_RUN")

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        with patch("urllib.request.urlopen", side_effect=_no_network):
            result = deliver_brief_email(_payload(), source_id="s3", env=env, base_dir=base)
        assert result["status"] == "dry_run"
        assert result["provider"] == "postmark"
        rows = _attempts(base)
        assert rows and rows[-1]["status"] == "dry_run"


def test_provider_http_error_records_failed_attempt():
    env = {
        "STATUTEPROOF_EMAIL_PROVIDER": "postmark",
        "STATUTEPROOF_EMAIL_FROM": "noreply@statuteproof.com",
        "POSTMARK_SERVER_TOKEN": "bad-token",
        "STATUTEPROOF_EMAIL_SEND_ENABLED": "true",
    }
    from email.message import Message
    http_err = urllib.error.HTTPError(
        url="https://api.postmarkapp.com/email", code=401,
        msg="Unauthorized", hdrs=Message(), fp=None,
    )
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        with patch("urllib.request.urlopen", side_effect=http_err):
            result = deliver_brief_email(_payload(), source_id="s4", env=env, base_dir=base)
        assert result["status"] == "error"
        rows = _attempts(base)
        assert rows and rows[-1]["status"] == "error"


def test_outbox_default_records_attempt():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        result = deliver_brief_email(_payload(), source_id="s5", env={}, base_dir=base)
        assert result["status"] == "queued_local"
        rows = _attempts(base)
        assert rows and rows[-1]["status"] == "queued_local"
        assert rows[-1]["provider"] == "local_outbox"
