"""Password-reset / email-verification link origin must resist Host-header poisoning.

`_handle_auth_forgot_password` mints a single-use reset token and emails a
`/reset-password?token=...` link. If that link's origin is derived from the
attacker-controllable request `Host` header, an attacker can POST forgot-password
for a victim and have the genuine StatuteProof email point at a hostile domain
that harvests the live token (account takeover). `_public_base_url` closes this by
preferring an explicitly configured origin (STATUTEPROOF_PUBLIC_BASE_URL) and only
falling back to the request Host when none is set.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.api import _Handler  # noqa: E402


def _handler_with_host(host: str) -> _Handler:
    handler = _Handler.__new__(_Handler)
    headers = MagicMock()
    headers.get = lambda key, default="": host if key == "Host" else default
    handler.headers = headers  # type: ignore[attr-defined]
    return handler


def test_public_base_url_prefers_configured_origin_over_poisoned_host(monkeypatch):
    monkeypatch.setenv("STATUTEPROOF_PUBLIC_BASE_URL", "https://statuteproof.com")
    handler = _handler_with_host("evil.attacker.example")
    assert handler._public_base_url() == "https://statuteproof.com"


def test_public_base_url_strips_trailing_slash(monkeypatch):
    monkeypatch.setenv("STATUTEPROOF_PUBLIC_BASE_URL", "https://statuteproof.com/")
    handler = _handler_with_host("evil.attacker.example")
    assert handler._public_base_url() == "https://statuteproof.com"


def test_public_base_url_falls_back_to_host_when_unset(monkeypatch):
    monkeypatch.delenv("STATUTEPROOF_PUBLIC_BASE_URL", raising=False)
    handler = _handler_with_host("localhost:5001")
    assert handler._public_base_url() == "http://localhost:5001"


def test_reset_link_cannot_be_poisoned_when_configured(monkeypatch):
    """End-to-end shape: the reset link uses the configured origin, never the
    poisoned Host, so a harvested token can only be replayed against our own site."""
    monkeypatch.setenv("STATUTEPROOF_PUBLIC_BASE_URL", "https://statuteproof.com")
    handler = _handler_with_host("evil.attacker.example")
    reset_url = f"{handler._public_base_url()}/reset-password?token=LIVE-TOKEN"
    assert reset_url == "https://statuteproof.com/reset-password?token=LIVE-TOKEN"
    assert "evil.attacker.example" not in reset_url
