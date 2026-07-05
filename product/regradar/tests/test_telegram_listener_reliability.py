"""
Regression tests for defect D5: the Telegram pairing listener retried
failed getUpdates calls in a tight loop with no backoff (438MB log in two
weeks) and logged the raw exception message, which embeds the bot token
inside the getUpdates URL.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.telegram_onboarding import fetch_updates, _failure_backoff_seconds

_TOKEN = "1234567:AAG-fake-token-for-tests"


def test_fetch_updates_failure_log_never_contains_token(caplog):
    exc = ConnectionError(
        f"HTTPSConnectionPool(host='api.telegram.org', port=443): Max retries "
        f"exceeded with url: /bot{_TOKEN}/getUpdates?timeout=30"
    )
    with patch("app.telegram_onboarding.requests.get", side_effect=exc):
        with caplog.at_level(logging.WARNING, logger="app.telegram_onboarding"):
            fetch_updates(_TOKEN, offset=0, timeout=0)
    assert caplog.text, "failure must still be logged"
    assert _TOKEN not in caplog.text, "bot token leaked into the log"


def test_fetch_updates_returns_none_on_transport_error():
    with patch("app.telegram_onboarding.requests.get", side_effect=ConnectionError("boom")):
        assert fetch_updates(_TOKEN, offset=0, timeout=0) is None


def test_fetch_updates_returns_list_on_success():
    class _Resp:
        def json(self):
            return {"ok": True, "result": [{"update_id": 7}]}

    with patch("app.telegram_onboarding.requests.get", return_value=_Resp()):
        assert fetch_updates(_TOKEN, offset=0, timeout=0) == [{"update_id": 7}]


def test_failure_backoff_grows_and_caps():
    assert _failure_backoff_seconds(1) >= 1
    assert _failure_backoff_seconds(2) > _failure_backoff_seconds(1)
    assert _failure_backoff_seconds(30) <= 60, "backoff must cap (<= 60s)"
    # No zero/negative sleeps that would recreate the tight loop.
    assert all(_failure_backoff_seconds(n) > 0 for n in range(1, 10))
