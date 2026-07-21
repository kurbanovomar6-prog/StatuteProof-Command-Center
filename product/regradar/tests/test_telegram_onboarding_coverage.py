"""
Behavioral coverage for the customer /start CODE pairing listener
(app.telegram_onboarding).

These tests exercise the onboarding path end-to-end in-process:
  - parsing a /start / /connect / /id command out of a Telegram update
  - consuming a valid vs expired vs invalid pairing code
  - the chat_id capture that gets handed to the pairing store
  - the /id command and its admin gating
  - the reply text (which must NOT leak the founder chat id or the bot token)

All network I/O (requests.get/post), the pairing store, and the table
setup are mocked — nothing here touches a live Telegram endpoint or SQLite.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import app.telegram_onboarding as onb
from app.telegram_onboarding import (
    _build_connect,
    _build_id,
    _build_pairing_result,
    _build_start,
    _build_unknown,
    _parse_command,
    _scrub_token,
    handle_update,
    run_listen_loop,
    send_reply,
)

_TOKEN = "1234567:AAG-fake-token-for-tests"
_FOUNDER_CHAT_ID = "999888777"  # the private admin/founder chat id


def _update(text: str, chat_id=12345, chat=None, sender=None, key="message"):
    msg = {"chat": chat if chat is not None else {"id": chat_id, "type": "private"}}
    if text is not None:
        msg["text"] = text
    if sender is not None:
        msg["from"] = sender
    return {key: msg, "update_id": 1}


# ---------------------------------------------------------------------------
# _parse_command
# ---------------------------------------------------------------------------

def test_parse_command_splits_command_and_argument():
    assert _parse_command("/start SP-ABC123") == ("/start", "SP-ABC123")


def test_parse_command_strips_bot_mention_and_lowercases():
    # Group chats deliver "/start@statuteproofalerts_bot CODE"
    assert _parse_command("/START@StatuteProofAlerts_bot SP-XYZ") == ("/start", "SP-XYZ")


def test_parse_command_no_argument():
    assert _parse_command("/id") == ("/id", "")


def test_parse_command_empty_text():
    assert _parse_command("   ") == ("", "")


# ---------------------------------------------------------------------------
# _build_* reply text
# ---------------------------------------------------------------------------

def test_build_pairing_result_ok_confirms_and_disclaims():
    reply = _build_pairing_result("ok")
    assert "connected" in reply.lower()
    assert "not legal advice" in reply.lower()


def test_build_pairing_result_expired():
    reply = _build_pairing_result("expired")
    assert "expired" in reply.lower()


def test_build_pairing_result_invalid_is_default_branch():
    reply = _build_pairing_result("anything-else")
    assert "invalid" in reply.lower()


def test_build_id_echoes_only_requester_chat_id_not_founder():
    reply = _build_id(12345)
    assert "12345" in reply
    # The /id reply must never expose the private founder/admin chat id.
    assert _FOUNDER_CHAT_ID not in reply


def test_build_start_and_connect_point_to_pairing_flow():
    assert "/start CODE" in _build_start()
    assert "/start CODE" in _build_connect()


def test_build_unknown_lists_commands():
    reply = _build_unknown()
    assert "/start CODE" in reply and "/connect CODE" in reply


# ---------------------------------------------------------------------------
# send_reply
# ---------------------------------------------------------------------------

def test_send_reply_success_returns_true_and_targets_only_sender():
    resp = MagicMock()
    resp.json.return_value = {"ok": True}
    with patch("app.telegram_onboarding.requests.post", return_value=resp) as post:
        assert send_reply(12345, "hi", _TOKEN) is True
    _, kwargs = post.call_args
    assert kwargs["json"]["chat_id"] == "12345"
    assert kwargs["json"]["parse_mode"] == "Markdown"


def test_send_reply_api_error_returns_false():
    resp = MagicMock()
    resp.json.return_value = {"ok": False, "description": "chat not found"}
    with patch("app.telegram_onboarding.requests.post", return_value=resp):
        assert send_reply(12345, "hi", _TOKEN) is False


def test_send_reply_transport_exception_returns_false():
    with patch("app.telegram_onboarding.requests.post", side_effect=ConnectionError("boom")):
        assert send_reply(12345, "hi", _TOKEN) is False


# ---------------------------------------------------------------------------
# handle_update — pairing path (the customer onboarding core)
# ---------------------------------------------------------------------------

def test_handle_update_valid_code_consumes_and_confirms():
    sender = {"username": "acme_mlro", "first_name": "Aisha"}
    upd = _update("/start SP-VALID1", chat_id=55501, sender=sender)
    with patch("app.telegram_onboarding.ensure_telegram_pairing_tables") as ensure, \
         patch("app.telegram_onboarding.consume_pairing_code", return_value="ok") as consume, \
         patch("app.telegram_onboarding.send_reply") as reply:
        handle_update(upd, _TOKEN)
    ensure.assert_called_once()
    # chat_id captured from the update and passed to the store as a string
    args, _ = consume.call_args
    assert args[0] == "SP-VALID1"
    assert args[1] == "55501"
    assert args[2]["username"] == "acme_mlro"
    # reply goes back to the sending chat only, with the success text
    assert reply.call_args[0][0] == 55501
    assert "connected" in reply.call_args[0][1].lower()


def test_handle_update_expired_code_reply():
    upd = _update("/start SP-OLD", chat_id=7)
    with patch("app.telegram_onboarding.ensure_telegram_pairing_tables"), \
         patch("app.telegram_onboarding.consume_pairing_code", return_value="expired"), \
         patch("app.telegram_onboarding.send_reply") as reply:
        handle_update(upd, _TOKEN)
    assert "expired" in reply.call_args[0][1].lower()


def test_handle_update_invalid_code_reply():
    upd = _update("/connect BADCODE", chat_id=7)
    with patch("app.telegram_onboarding.ensure_telegram_pairing_tables"), \
         patch("app.telegram_onboarding.consume_pairing_code", return_value="nope"), \
         patch("app.telegram_onboarding.send_reply") as reply:
        handle_update(upd, _TOKEN)
    assert "invalid" in reply.call_args[0][1].lower()


def test_handle_update_pairing_falls_back_to_chat_identity_when_no_sender():
    # channel_post has no "from"; identity should come off the chat object
    upd = _update("/start SP-CH", chat={"id": 900, "type": "channel", "title": "ACME Compliance"}, key="channel_post")
    with patch("app.telegram_onboarding.ensure_telegram_pairing_tables"), \
         patch("app.telegram_onboarding.consume_pairing_code", return_value="ok") as consume, \
         patch("app.telegram_onboarding.send_reply"):
        handle_update(upd, _TOKEN)
    assert consume.call_args[0][2]["username"] == "ACME Compliance"


# ---------------------------------------------------------------------------
# handle_update — help / info commands
# ---------------------------------------------------------------------------

def test_handle_update_bare_start_sends_welcome():
    upd = _update("/start", chat_id=7)
    with patch("app.telegram_onboarding.send_reply") as reply, \
         patch("app.telegram_onboarding.consume_pairing_code") as consume:
        handle_update(upd, _TOKEN)
    consume.assert_not_called()
    assert "Welcome to StatuteProof Alerts" in reply.call_args[0][1]


def test_handle_update_connect_no_arg_sends_help():
    upd = _update("/connect", chat_id=7)
    with patch("app.telegram_onboarding.send_reply") as reply:
        handle_update(upd, _TOKEN)
    assert "/start CODE" in reply.call_args[0][1]


def test_handle_update_unknown_text_sends_help():
    upd = _update("hello there", chat_id=7)
    with patch("app.telegram_onboarding.send_reply") as reply:
        handle_update(upd, _TOKEN)
    assert "StatuteProof Alerts bot is ready" in reply.call_args[0][1]


# ---------------------------------------------------------------------------
# handle_update — /id and admin gating
# ---------------------------------------------------------------------------

def test_handle_update_id_returns_own_chat_id_without_admin_restriction():
    upd = _update("/id", chat_id=42)
    with patch.object(onb, "_ADMIN_CHAT_IDS", frozenset()), \
         patch("app.telegram_onboarding.send_reply") as reply:
        handle_update(upd, _TOKEN)
    assert "42" in reply.call_args[0][1]
    assert _FOUNDER_CHAT_ID not in reply.call_args[0][1]


def test_handle_update_id_blocked_for_non_admin_when_allowlist_set():
    upd = _update("/id", chat_id=42)
    with patch.object(onb, "_ADMIN_CHAT_IDS", frozenset({"999"})), \
         patch("app.telegram_onboarding.send_reply") as reply:
        handle_update(upd, _TOKEN)
    assert reply.call_count == 1
    assert reply.call_args[0][1] == "Unauthorized."


def test_handle_update_id_allowed_for_admin_in_allowlist():
    upd = _update("/id", chat_id=999)
    with patch.object(onb, "_ADMIN_CHAT_IDS", frozenset({"999"})), \
         patch("app.telegram_onboarding.send_reply") as reply:
        handle_update(upd, _TOKEN)
    assert "999" in reply.call_args[0][1]
    assert reply.call_args[0][1] != "Unauthorized."


# ---------------------------------------------------------------------------
# handle_update — updates that must be silently ignored (no reply)
# ---------------------------------------------------------------------------

def test_handle_update_ignores_update_with_no_message():
    with patch("app.telegram_onboarding.send_reply") as reply:
        handle_update({"update_id": 1}, _TOKEN)
    reply.assert_not_called()


def test_handle_update_ignores_message_without_text():
    upd = _update(None, chat_id=7)  # e.g. a photo/sticker
    with patch("app.telegram_onboarding.send_reply") as reply:
        handle_update(upd, _TOKEN)
    reply.assert_not_called()


def test_handle_update_ignores_message_without_chat_id():
    upd = {"message": {"chat": {"type": "private"}, "text": "/start"}, "update_id": 1}
    with patch("app.telegram_onboarding.send_reply") as reply:
        handle_update(upd, _TOKEN)
    reply.assert_not_called()


# ---------------------------------------------------------------------------
# _scrub_token
# ---------------------------------------------------------------------------

def test_scrub_token_redacts_token():
    scrubbed = _scrub_token(f"url /bot{_TOKEN}/getUpdates", _TOKEN)
    assert _TOKEN not in scrubbed
    assert "<bot-token-redacted>" in scrubbed


def test_scrub_token_noop_when_token_empty():
    assert _scrub_token("no token here", "") == "no token here"


# ---------------------------------------------------------------------------
# run_listen_loop — long-poll driver
# ---------------------------------------------------------------------------

def test_run_listen_loop_processes_update_then_stops_on_keyboard_interrupt():
    upd = _update("/start SP-Z", chat_id=7)
    fetch = MagicMock(side_effect=[[upd], KeyboardInterrupt()])
    with patch("app.telegram_onboarding.ensure_telegram_pairing_tables") as ensure, \
         patch("app.telegram_onboarding.fetch_updates", fetch), \
         patch("app.telegram_onboarding.handle_update") as handle, \
         patch("builtins.print"):
        run_listen_loop(_TOKEN, bot_username="statuteproofalerts_bot")
    ensure.assert_called_once()
    handle.assert_called_once()
    # offset advances past the processed update on the next poll
    assert fetch.call_args_list[1].kwargs["offset"] == upd["update_id"] + 1


def test_run_listen_loop_backs_off_on_transport_failure():
    # None from fetch_updates => transport failure => sleep(backoff), no crash
    fetch = MagicMock(side_effect=[None, KeyboardInterrupt()])
    with patch("app.telegram_onboarding.ensure_telegram_pairing_tables"), \
         patch("app.telegram_onboarding.fetch_updates", fetch), \
         patch("app.telegram_onboarding.time.sleep") as sleep, \
         patch("builtins.print"):
        run_listen_loop(_TOKEN)
    sleep.assert_called_once()
    assert sleep.call_args[0][0] > 0


def test_run_listen_loop_skips_updates_with_no_message():
    fetch = MagicMock(side_effect=[[{"update_id": 5}], KeyboardInterrupt()])
    with patch("app.telegram_onboarding.ensure_telegram_pairing_tables"), \
         patch("app.telegram_onboarding.fetch_updates", fetch), \
         patch("app.telegram_onboarding.handle_update") as handle, \
         patch("builtins.print"):
        run_listen_loop(_TOKEN)
    handle.assert_not_called()
