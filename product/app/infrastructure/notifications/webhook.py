"""
webhook.py — HTTP Webhook push-уведомления RegRadar.

Назначение: отправка JSON-события на настроенные endpoint-ы при обнаружении
критических регуляторных актов. Интегрируется с любой системой:
Slack, Microsoft Teams, Zapier, n8n, корпоративные системы.

Конфигурация (.env):
  WEBHOOK_URLS  — URL-адреса через запятую
                  (https://hooks.slack.com/... , https://yourapp.com/api/webhook)
  WEBHOOK_SECRET — HMAC-SHA256 секрет для подписи payload (опционально)

Slack Incoming Webhook поддерживается автоматически:
  если URL содержит "hooks.slack.com" — форматируется как Slack Block Kit.
"""

import hashlib
import hmac
import json
import logging
import os
import threading
import time
import urllib.request
from datetime import datetime

log = logging.getLogger(__name__)

_WEBHOOK_URLS   = [u.strip() for u in os.getenv("WEBHOOK_URLS", "").split(",") if u.strip()]
_WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
_BASE_URL       = os.getenv("REGRADA_BASE_URL", "http://localhost:8080")

_JUR_FLAGS = {"RU": "🇷🇺", "KZ": "🇰🇿", "AZ": "🇦🇿", "BY": "🇧🇾", "UZ": "🇺🇿"}
_LEVEL_COLORS_HEX = {
    "CRITICAL": "#dc2626", "HIGH": "#ea580c",
    "MEDIUM":   "#ca8a04", "LOW":  "#16a34a",
}


def _sign_payload(payload_bytes: bytes) -> str:
    """HMAC-SHA256 подпись payload для верификации на стороне получателя."""
    if not _WEBHOOK_SECRET:
        return ""
    return "sha256=" + hmac.new(
        _WEBHOOK_SECRET.encode(), payload_bytes, hashlib.sha256
    ).hexdigest()


def _build_slack_payload(reg: dict) -> dict:
    """Форматирует Slack Block Kit сообщение."""
    level  = reg.get("critical_level", "HIGH")
    jur    = reg.get("jurisdiction", "")
    flag   = _JUR_FLAGS.get(jur, "🌐")
    title  = (reg.get("title") or "—")[:200]
    eff    = reg.get("effective_date") or "—"
    rid    = reg.get("id", "")
    url    = reg.get("source_url", "")
    color  = _LEVEL_COLORS_HEX.get(level, "#6b7280")
    dash   = f"{_BASE_URL}/regulations/{rid}" if rid else _BASE_URL

    return {
        "attachments": [{
            "color": color,
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"⚠️ RegRadar | {level}: {flag} {jur}"}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{title}*"}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Вступает в силу:*\n{eff}"},
                        {"type": "mrkdwn", "text": f"*Источник:*\n{'<' + url + '|Открыть>' if url else '—'}"},
                    ]
                },
                {
                    "type": "actions",
                    "elements": [{
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Открыть в RegRadar"},
                        "url": dash,
                        "style": "primary",
                    }]
                },
                {
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": f"RegRadar Enterprise · {datetime.utcnow().strftime('%d.%m.%Y %H:%M')} UTC"}]
                }
            ]
        }]
    }


def _build_generic_payload(reg: dict) -> dict:
    """Стандартный JSON-payload для non-Slack webhook endpoints."""
    return {
        "event":       "regulation.detected",
        "timestamp":   datetime.utcnow().isoformat() + "Z",
        "source":      "RegRadar Enterprise",
        "regulation": {
            "id":             reg.get("id"),
            "title":          reg.get("title"),
            "jurisdiction":   reg.get("jurisdiction"),
            "critical_level": reg.get("critical_level"),
            "effective_date": reg.get("effective_date"),
            "summary":        (reg.get("summary") or "")[:300],
            "source_url":     reg.get("source_url"),
            "dashboard_url":  f"{_BASE_URL}/regulations/{reg.get('id')}" if reg.get("id") else _BASE_URL,
        }
    }


def _post_to_url(url: str, reg: dict) -> bool:
    """Отправляет payload на один webhook URL."""
    try:
        is_slack = "hooks.slack.com" in url
        payload  = _build_slack_payload(reg) if is_slack else _build_generic_payload(reg)
        body     = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        sig      = _sign_payload(body)

        headers = {"Content-Type": "application/json"}
        if sig:
            headers["X-RegRadar-Signature"] = sig
        headers["X-RegRadar-Event"] = "regulation.detected"

        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=8) as resp:
            status = resp.status
            if status < 300:
                log.info("webhook: POST %s → %d", url[:60], status)
                return True
            log.warning("webhook: POST %s → HTTP %d", url[:60], status)
            return False

    except Exception as exc:
        log.warning("webhook: ошибка POST %s — %s", url[:60], str(exc)[:80])
        return False


def notify_regulation(reg: dict) -> None:
    """
    Публичный API: отправляет webhook на все настроенные URL (неблокирующий).

    reg — словарь регуляторного акта.
    """
    if not _WEBHOOK_URLS:
        return

    level = reg.get("critical_level", "LOW")
    if level not in ("CRITICAL", "HIGH"):
        return

    def _dispatch():
        for url in _WEBHOOK_URLS:
            _post_to_url(url, reg)
            time.sleep(0.2)  # небольшая задержка между запросами

    t = threading.Thread(target=_dispatch, daemon=True, name="webhook-dispatch")
    t.start()
