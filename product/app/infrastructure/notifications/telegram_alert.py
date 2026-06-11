"""
telegram_alert.py — Push-уведомления RegRadar в Telegram.

Назначение: мгновенная отправка форматированного алерта в Telegram-чат
клиента при обнаружении CRITICAL или HIGH регуляторного документа.

Конфигурация (.env):
  TELEGRAM_BOT_TOKEN     — токен бота (получить у @BotFather)
  TELEGRAM_ALERT_CHAT_ID — ID чата, канала или группы (-100xxxx / @channel)
  TELEGRAM_MIN_LEVEL     — минимальный уровень для алерта (CRITICAL / HIGH, default=CRITICAL)

Использование в pipeline:
  from app.infrastructure.notifications.telegram_alert import notify_regulation
  notify_regulation(regulation_data)   # неблокирующий вызов через threading

Форматирование: HTML-разметка Telegram (жирный, курсив, ссылки).
"""

import logging
import os
import threading
from datetime import datetime

log = logging.getLogger(__name__)

_BOT_TOKEN     = os.getenv("TELEGRAM_BOT_TOKEN", "")
_CHAT_ID       = os.getenv("TELEGRAM_ALERT_CHAT_ID", "")
_MIN_LEVEL     = os.getenv("TELEGRAM_MIN_LEVEL", "CRITICAL").upper()
_BASE_URL      = os.getenv("REGRADA_BASE_URL", "http://localhost:8080")

# Флаги юрисдикций для визуального оформления
_JUR_FLAGS = {
    "RU": "🇷🇺", "KZ": "🇰🇿", "AZ": "🇦🇿", "BY": "🇧🇾", "UZ": "🇺🇿",
}

# Цвет-эмодзи по уровню риска
_LEVEL_EMOJI = {
    "CRITICAL": "🚨", "HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢",
}

_LEVEL_PRIORITY = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


def _should_alert(level: str) -> bool:
    """Проверяет нужно ли отправлять алерт по данному уровню риска."""
    return _LEVEL_PRIORITY.get(level, 0) >= _LEVEL_PRIORITY.get(_MIN_LEVEL, 4)


def _build_message(reg: dict) -> str:
    """
    Формирует HTML-сообщение Telegram по данным регуляторного документа.

    reg — словарь с ключами: id, title, jurisdiction, critical_level,
          effective_date, summary, source_url, ai_fines (опционально)
    """
    level    = reg.get("critical_level", "HIGH")
    jur      = reg.get("jurisdiction", "??")
    flag     = _JUR_FLAGS.get(jur, "🌐")
    emoji    = _LEVEL_EMOJI.get(level, "⚠️")
    reg_id   = reg.get("id", "—")
    title    = (reg.get("title") or "Без названия")[:180]
    eff_date = reg.get("effective_date") or "—"
    summary  = (reg.get("summary") or "")[:320]
    url      = reg.get("source_url", "")
    fines    = reg.get("ai_fines") or reg.get("fines") or ""

    # Строим текст штрафа если есть
    fines_line = ""
    if fines and fines not in ("N/A", "-", "—", ""):
        fines_line = f"\n💰 <b>Штраф/риск:</b> {fines}"

    # Ссылка на карточку в дашборде
    dashboard_link = f"{_BASE_URL}/regulations/{reg_id}" if reg_id != "—" else _BASE_URL

    msg = (
        f"{emoji} <b>RegRadar | {level}</b>\n"
        f"{flag} <b>{jur}</b> — #{reg_id}\n"
        f"{'─' * 32}\n"
        f"📋 <b>{title}</b>\n"
        f"\n"
        f"📅 <b>Вступает в силу:</b> {eff_date}"
        f"{fines_line}\n"
        f"\n"
    )

    if summary:
        msg += f"📝 {summary}\n\n"

    if url:
        msg += f'🔗 <a href="{url}">Источник документа</a>\n'

    msg += f'📊 <a href="{dashboard_link}">Открыть в RegRadar</a>\n'
    msg += f"\n<i>RegRadar Enterprise · {datetime.utcnow().strftime('%d.%m.%Y %H:%M')} UTC</i>"

    return msg


def _send_sync(message: str) -> bool:
    """
    Синхронная отправка сообщения через Telegram Bot API (requests-based).
    Возвращает True при успехе.
    """
    if not _BOT_TOKEN or not _CHAT_ID:
        log.debug("telegram_alert: BOT_TOKEN или CHAT_ID не настроены — алерт пропущен")
        return False

    try:
        import urllib.request
        import urllib.parse
        import json as _json

        payload = _json.dumps({
            "chat_id":    _CHAT_ID,
            "text":       message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"https://api.telegram.org/bot{_BOT_TOKEN}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = _json.loads(resp.read())
            if result.get("ok"):
                log.info("telegram_alert: сообщение отправлено в чат %s", _CHAT_ID)
                return True
            log.warning("telegram_alert: API вернул ошибку — %s", result)
            return False

    except Exception as exc:
        log.error("telegram_alert: ошибка отправки — %s", str(exc)[:120])
        return False


def notify_regulation(reg: dict) -> None:
    """
    Публичный API: отправляет алерт в Telegram (неблокирующий).
    Запускается в отдельном daemon-потоке чтобы не тормозить pipeline.

    Параметры:
      reg — словарь регуляторного акта (поля из DB или AI-extractor)
    """
    level = reg.get("critical_level", "LOW")
    if not _should_alert(level):
        return

    message = _build_message(reg)

    t = threading.Thread(
        target=_send_sync,
        args=(message,),
        daemon=True,
        name=f"tg-alert-{reg.get('id', 'x')}",
    )
    t.start()


def send_daily_digest(regulations: list[dict], days: int = 1) -> bool:
    """
    Отправляет сводный дайджест за период (вызывается Celery beat ежедневно).

    regulations — список регуляторных актов за период
    """
    if not _BOT_TOKEN or not _CHAT_ID:
        return False

    if not regulations:
        return False

    critical = [r for r in regulations if r.get("critical_level") == "CRITICAL"]
    high     = [r for r in regulations if r.get("critical_level") == "HIGH"]

    lines = [
        f"📊 <b>RegRadar | Дайджест за {days} дн.</b>",
        f"{'─' * 32}",
        f"🔢 Всего документов: <b>{len(regulations)}</b>",
        f"🚨 Критических: <b>{len(critical)}</b>",
        f"🔴 Высоких: <b>{len(high)}</b>",
        "",
    ]

    if critical:
        lines.append("⚠️ <b>Требуют немедленного внимания:</b>")
        for r in critical[:5]:
            flag  = _JUR_FLAGS.get(r.get("jurisdiction", ""), "🌐")
            title = (r.get("title") or "—")[:100]
            lines.append(f"  {flag} #{r.get('id')} — {title}")
        lines.append("")

    lines.append(f'📊 <a href="{_BASE_URL}">Открыть RegRadar Dashboard</a>')
    lines.append(f"\n<i>{datetime.utcnow().strftime('%d.%m.%Y')} UTC</i>")

    return _send_sync("\n".join(lines))


def send_text(text: str) -> bool:
    """Отправляет произвольный текст (для тестирования и системных уведомлений)."""
    return _send_sync(text)
