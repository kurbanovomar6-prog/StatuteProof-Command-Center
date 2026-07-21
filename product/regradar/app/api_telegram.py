"""Telegram account-pairing request handlers, extracted from ``app.api``.

This module holds one cohesive slice of the HTTP surface — the customer-facing
Telegram pairing endpoints (generate / status / unlink / test) — as a mixin that
``app.api._Handler`` inherits. The method bodies are byte-identical to their
former inline definitions; only their host class/file changed.

The names the moved bodies read as bare globals are imported here FROM
``app.api`` so they are the SAME objects the rest of the handler uses (and so
tests that monkeypatch ``app.api_telegram.<name>`` steer these methods exactly
as they previously steered ``app.api.<name>``). Shared per-request helpers
(``_send_json``, ``_rate_limited``) stay on ``_Handler`` and are reached through
``self``.
"""
from __future__ import annotations

from app.api import (
    TELEGRAM_ALERTS_BOT_USERNAME,
    _PAIR_GENERATE_LIMITER,
    _TELEGRAM_TEST_LIMITER,
    create_pairing_code,
    get_pairing_status,
    get_telegram_link,
    logger,
    require_auth,
    send_telegram_message,
    touch_telegram_test_sent,
    unlink_telegram,
)


class _TelegramHandlerMixin:
    """Telegram account-pairing endpoint handlers for ``_Handler``."""

    def _telegram_instructions(self, code: str) -> str:
        # The /start CODE listener runs on the ALERTS bot (telegram_settings.get_token
        # prefers TELEGRAM_ALERTS_BOT_TOKEN = @statuteproofalerts_bot), NOT the
        # founder-only admin bot. Direct the customer at the alerts bot or pairing
        # silently fails. TELEGRAM_ALERTS_BOT_USERNAME falls back to the legacy
        # TELEGRAM_BOT_USERNAME in single-bot dev, so this is safe there too.
        if TELEGRAM_ALERTS_BOT_USERNAME:
            return f"Send /start {code} to @{TELEGRAM_ALERTS_BOT_USERNAME} in Telegram."
        return f"Send /start {code} to our Telegram bot."

    def _handle_telegram_pair_generate(self) -> None:
        if self._rate_limited(_PAIR_GENERATE_LIMITER, "telegram_pair_generate"):
            return

        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            result = create_pairing_code(int(user["id"]))
            self._send_json({
                "ok": True,
                "code": result["code"],
                "expires_at": result["expires_at"],
                "bot_username": TELEGRAM_ALERTS_BOT_USERNAME or "",
                "instructions": self._telegram_instructions(result["code"]),
            })
        except Exception as exc:
            logger.error("Telegram pair generate failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_telegram_pair_status(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            status = get_pairing_status(int(user["id"]))
            self._send_json({"ok": True, **status})
        except Exception as exc:
            logger.error("Telegram pair status failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_telegram_pair_unlink(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            unlink_telegram(int(user["id"]))
            self._send_json({"ok": True})
        except Exception as exc:
            logger.error("Telegram pair unlink failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_telegram_account_test(self) -> None:
        if self._rate_limited(_TELEGRAM_TEST_LIMITER, "telegram_account_test"):
            return

        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            link = get_telegram_link(int(user["id"]))
            chat_id = link.get("telegram_chat_id")
            if not chat_id:
                self._send_json({
                    "ok": False,
                    "message": "Telegram is not connected. Generate a pairing code first.",
                }, 400)
                return

            ok = send_telegram_message(
                str(chat_id),
                "✅ StatuteProof Telegram test message delivered to your connected account.",
            )
            if ok:
                touch_telegram_test_sent(int(user["id"]))
                self._send_json({"ok": True, "message": "Test message sent to your Telegram."})
            else:
                self._send_json({
                    "ok": False,
                    "message": "Could not send Telegram test message. Check bot configuration.",
                }, 502)
        except Exception as exc:
            logger.error("Account Telegram test failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)
