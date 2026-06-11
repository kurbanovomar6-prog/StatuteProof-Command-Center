"""
email_digest.py — Автоматические email-дайджесты RegRadar.

Назначение: отправка HTML-отчётов на email клиентов по расписанию.
Использует встроенный smtplib (без внешних зависимостей).

Конфигурация (.env):
  SMTP_HOST       — сервер отправки (smtp.gmail.com / mail.ru / smtp.yandex.ru)
  SMTP_PORT       — порт (587 для TLS, 465 для SSL)
  SMTP_USER       — логин/email отправителя
  SMTP_PASSWORD   — пароль / app-password
  SMTP_FROM       — email отправителя (по умолчанию = SMTP_USER)
  DIGEST_EMAILS   — получатели через запятую (ceo@bank.ru,cfo@bank.ru)

Вызывается Celery beat по расписанию (daily / weekly).
"""

import logging
import os
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger(__name__)

_SMTP_HOST     = os.getenv("SMTP_HOST", "")
_SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
_SMTP_USER     = os.getenv("SMTP_USER", "")
_SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
_SMTP_FROM     = os.getenv("SMTP_FROM", _SMTP_USER)
_DIGEST_EMAILS = [e.strip() for e in os.getenv("DIGEST_EMAILS", "").split(",") if e.strip()]
_BASE_URL      = os.getenv("REGRADA_BASE_URL", "http://localhost:8080")

_COMPANY_NAME  = os.getenv("COMPANY_NAME", "Ваша Компания")

# ── Флаги и цвета ──────────────────────────────────────────────────────────────
_JUR_FLAGS = {"RU": "🇷🇺", "KZ": "🇰🇿", "AZ": "🇦🇿", "BY": "🇧🇾", "UZ": "🇺🇿"}
_LEVEL_COLORS = {
    "CRITICAL": "#dc2626",
    "HIGH":     "#ea580c",
    "MEDIUM":   "#ca8a04",
    "LOW":      "#16a34a",
}


def _render_html(
    regulations: list[dict],
    days: int,
    total_risk: int = 0,
) -> str:
    """Рендерит HTML-письмо с дайджестом регуляторных изменений."""

    now_str  = datetime.utcnow().strftime("%d.%m.%Y")
    critical = [r for r in regulations if r.get("critical_level") == "CRITICAL"]
    high     = [r for r in regulations if r.get("critical_level") == "HIGH"]
    risk_fmt = f"${total_risk:,.0f}" if total_risk else "—"

    # ── Строки таблицы топ-регуляторных актов ─────────────────────────────────
    rows_html = ""
    for r in regulations[:10]:
        level  = r.get("critical_level", "LOW")
        color  = _LEVEL_COLORS.get(level, "#6b7280")
        flag   = _JUR_FLAGS.get(r.get("jurisdiction", ""), "🌐")
        title  = (r.get("title") or "—")[:120]
        eff    = r.get("effective_date") or "—"
        rid    = r.get("id", "")
        link   = f"{_BASE_URL}/regulations/{rid}" if rid else _BASE_URL
        rows_html += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #1e293b;color:#94a3b8;">{flag} {r.get("jurisdiction","")}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #1e293b;">
            <a href="{link}" style="color:#38bdf8;text-decoration:none;">{title}</a>
          </td>
          <td style="padding:8px 12px;border-bottom:1px solid #1e293b;text-align:center;">
            <span style="background:{color};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:bold;">{level}</span>
          </td>
          <td style="padding:8px 12px;border-bottom:1px solid #1e293b;color:#94a3b8;white-space:nowrap;">{eff}</td>
        </tr>"""

    if not rows_html:
        rows_html = '<tr><td colspan="4" style="padding:16px;text-align:center;color:#64748b;">Новых актов за период не найдено</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RegRadar — Дайджест</title>
</head>
<body style="margin:0;padding:0;background:#0f172a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#e2e8f0;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0f172a;padding:32px 0;">
<tr><td align="center">
<table width="640" cellpadding="0" cellspacing="0" style="background:#1e293b;border-radius:12px;overflow:hidden;border:1px solid #334155;">

  <!-- HEADER -->
  <tr>
    <td style="background:linear-gradient(135deg,#1e40af,#0f172a);padding:32px 40px;">
      <h1 style="margin:0;font-size:26px;font-weight:800;color:#fff;letter-spacing:-0.5px;">
        📋 RegRadar Enterprise
      </h1>
      <p style="margin:8px 0 0;color:#93c5fd;font-size:14px;">
        Регуляторный дайджест · {now_str} · {_COMPANY_NAME}
      </p>
    </td>
  </tr>

  <!-- KPI CARDS -->
  <tr>
    <td style="padding:24px 40px 0;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td width="33%" style="padding:0 8px 0 0;">
            <div style="background:#0f172a;border:1px solid #334155;border-radius:8px;padding:16px;text-align:center;">
              <div style="font-size:28px;font-weight:800;color:#38bdf8;">{len(regulations)}</div>
              <div style="font-size:11px;color:#64748b;margin-top:4px;text-transform:uppercase;letter-spacing:1px;">Новых актов</div>
            </div>
          </td>
          <td width="33%" style="padding:0 4px;">
            <div style="background:#0f172a;border:1px solid #dc2626;border-radius:8px;padding:16px;text-align:center;">
              <div style="font-size:28px;font-weight:800;color:#f87171;">{len(critical)}</div>
              <div style="font-size:11px;color:#64748b;margin-top:4px;text-transform:uppercase;letter-spacing:1px;">Критических</div>
            </div>
          </td>
          <td width="33%" style="padding:0 0 0 8px;">
            <div style="background:#0f172a;border:1px solid #334155;border-radius:8px;padding:16px;text-align:center;">
              <div style="font-size:28px;font-weight:800;color:#34d399;">{risk_fmt}</div>
              <div style="font-size:11px;color:#64748b;margin-top:4px;text-transform:uppercase;letter-spacing:1px;">Риск-экспозиция</div>
            </div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- SUMMARY -->
  <tr>
    <td style="padding:24px 40px 0;">
      <p style="margin:0;line-height:1.7;color:#cbd5e1;">
        За последние <b>{days} дн.</b> система <b>RegRadar</b> обнаружила
        <b style="color:#38bdf8;">{len(regulations)}</b> регуляторных изменений.
        Из них <b style="color:#f87171;">{len(critical)}</b> критических и
        <b style="color:#fb923c;">{len(high)}</b> высокого уровня.
        Суммарный контролируемый финансовый риск: <b style="color:#34d399;">{risk_fmt}</b>.
      </p>
    </td>
  </tr>

  <!-- TABLE -->
  <tr>
    <td style="padding:24px 40px 0;">
      <h3 style="margin:0 0 12px;font-size:14px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;">
        Актуальные изменения
      </h3>
      <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #334155;border-radius:8px;overflow:hidden;">
        <tr style="background:#0f172a;">
          <th style="padding:10px 12px;text-align:left;font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:1px;">Юрисдикция</th>
          <th style="padding:10px 12px;text-align:left;font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:1px;">Документ</th>
          <th style="padding:10px 12px;text-align:center;font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:1px;">Уровень</th>
          <th style="padding:10px 12px;text-align:left;font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:1px;">Дата</th>
        </tr>
        {rows_html}
      </table>
    </td>
  </tr>

  <!-- CTA BUTTON -->
  <tr>
    <td style="padding:32px 40px;text-align:center;">
      <a href="{_BASE_URL}" style="display:inline-block;background:#1d4ed8;color:#fff;text-decoration:none;padding:14px 32px;border-radius:8px;font-weight:700;font-size:15px;">
        Открыть RegRadar Dashboard →
      </a>
    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td style="background:#0f172a;padding:20px 40px;border-top:1px solid #1e293b;">
      <p style="margin:0;font-size:11px;color:#475569;text-align:center;line-height:1.6;">
        Отчёт сформирован автоматически системой <b>RegRadar Enterprise</b>.<br>
        Данные из регуляторных источников СНГ: ЦБР, НБК, ЦБА, НБРБ, ЦБУ.<br>
        Конфиденциально — предназначен для топ-менеджмента.
      </p>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""


def send_digest(regulations: list[dict], days: int = 7, total_risk: int = 0) -> bool:
    """
    Отправляет HTML-дайджест на все email из DIGEST_EMAILS.

    regulations — список регуляторных актов за период
    days        — период анализа (для заголовка)
    total_risk  — суммарный финансовый риск в USD

    Возвращает True если письмо успешно отправлено хотя бы одному получателю.
    """
    if not _SMTP_HOST or not _SMTP_USER or not _DIGEST_EMAILS:
        log.debug("email_digest: SMTP не настроен или нет получателей — пропускаем")
        return False

    html_body = _render_html(regulations, days, total_risk)
    now_str   = datetime.utcnow().strftime("%d.%m.%Y")
    subject   = f"RegRadar | Регуляторный дайджест {now_str} — {len(regulations)} актов"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"RegRadar <{_SMTP_FROM}>"
        msg["To"]      = ", ".join(_DIGEST_EMAILS)
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        context = ssl.create_default_context()

        if _SMTP_PORT == 465:
            with smtplib.SMTP_SSL(_SMTP_HOST, _SMTP_PORT, context=context) as srv:
                srv.login(_SMTP_USER, _SMTP_PASSWORD)
                srv.sendmail(_SMTP_FROM, _DIGEST_EMAILS, msg.as_string())
        else:
            with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as srv:
                srv.ehlo()
                srv.starttls(context=context)
                srv.login(_SMTP_USER, _SMTP_PASSWORD)
                srv.sendmail(_SMTP_FROM, _DIGEST_EMAILS, msg.as_string())

        log.info(
            "email_digest: отправлен на %d адресов (%s)",
            len(_DIGEST_EMAILS), now_str,
        )
        return True

    except Exception as exc:
        log.error("email_digest: ошибка SMTP — %s", str(exc)[:200])
        return False
