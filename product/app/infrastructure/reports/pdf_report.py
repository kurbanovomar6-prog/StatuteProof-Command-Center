"""
pdf_report.py — Профессиональный PDF-генератор исполнительных отчётов RegRadar.

Формат: branded PDF с обложкой, KPI-блоками, таблицами, брендингом.
Библиотека: fpdf2 (чистый Python, без системных зависимостей).

Возвращает: bytes (PDF-файл) — можно стримить через FastAPI FileResponse.

Использование:
  from app.infrastructure.reports.pdf_report import generate_pdf_report
  pdf_bytes = generate_pdf_report(days=30, jurisdiction="RU")
  Path("report.pdf").write_bytes(pdf_bytes)
"""

import io
import logging
from datetime import datetime

log = logging.getLogger(__name__)

_JUR_NAMES = {
    "RU": "Россия", "KZ": "Казахстан",
    "AZ": "Азербайджан", "BY": "Беларусь", "UZ": "Узбекистан",
}
_LEVEL_COLORS_RGB = {
    "CRITICAL": (220, 38, 38),
    "HIGH":     (234, 88, 12),
    "MEDIUM":   (202, 138, 4),
    "LOW":      (22, 163, 74),
}


def _get_report_data(days: int, jurisdiction) -> dict:
    """Загружает данные из БД через executive_report._fetch_report_data."""
    from app.infrastructure.reports.executive_report import _fetch_report_data
    return _fetch_report_data(days, jurisdiction)


def generate_pdf_report(
    days: int = 30,
    jurisdiction: str | None = None,
) -> bytes:
    """
    Генерирует брендированный PDF исполнительного отчёта.

    Возвращает bytes PDF-файла.
    Бросает ImportError если fpdf2 не установлен.
    """
    try:
        from fpdf import FPDF, XPos, YPos
    except ImportError as exc:
        raise ImportError("Установите fpdf2: pip install fpdf2") from exc

    data      = _get_report_data(days, jurisdiction)
    now       = datetime.utcnow()
    jur_label = _JUR_NAMES.get(jurisdiction, "Все юрисдикции СНГ") if jurisdiction else "Все юрисдикции СНГ"

    # ── Инициализация PDF ─────────────────────────────────────────────────────
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    # Ищем Unicode-шрифт с поддержкой кириллицы
    import os
    _FONT_CANDIDATES = [
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    _FONT_PATH = next((p for p in _FONT_CANDIDATES if os.path.exists(p)), None)
    _FONT_NAME = "UniFont"

    if _FONT_PATH:
        pdf.add_font(_FONT_NAME, style="",  fname=_FONT_PATH, uni=True)
        pdf.add_font(_FONT_NAME, style="B", fname=_FONT_PATH, uni=True)
        pdf.add_font(_FONT_NAME, style="I", fname=_FONT_PATH, uni=True)
    else:
        _FONT_NAME = "Helvetica"  # fallback без кириллицы

    def _font(style="", size=10):
        pdf.set_font(_FONT_NAME, style=style, size=size)

    # ── ОБЛОЖКА ───────────────────────────────────────────────────────────────
    # Тёмный фон заголовка
    pdf.set_fill_color(15, 23, 42)    # #0f172a
    pdf.rect(0, 0, 210, 80, style="F")

    # Логотип / название
    pdf.set_xy(20, 18)
    _font("B", 28)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, "RegRadar Enterprise", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_xy(20, 34)
    _font("", 12)
    pdf.set_text_color(147, 197, 253)  # #93c5fd
    pdf.cell(0, 7, "Regulatory Intelligence Platform | CIS Markets")

    # Период и юрисдикция
    pdf.set_xy(20, 50)
    _font("B", 11)
    pdf.set_text_color(226, 232, 240)  # #e2e8f0
    pdf.cell(0, 6, f"Исполнительный отчёт | {jur_label}")
    pdf.set_xy(20, 58)
    _font("", 10)
    pdf.set_text_color(148, 163, 184)  # #94a3b8
    pdf.cell(0, 5, f"Период: {data['period_start']} — {data['period_end']}  |  Сформирован: {now.strftime('%d.%m.%Y %H:%M')} UTC")

    # Конфиденциальная пометка
    pdf.set_xy(20, 68)
    _font("I", 9)
    pdf.set_text_color(220, 38, 38)
    pdf.cell(0, 5, "КОНФИДЕНЦИАЛЬНО — предназначен для топ-менеджмента")

    # ── СВОДНЫЙ ПАРАГРАФ ─────────────────────────────────────────────────────
    pdf.set_xy(20, 90)
    _font("B", 13)
    pdf.set_text_color(30, 41, 59)     # #1e293b
    pdf.cell(0, 8, "Сводка", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Горизонтальный разделитель
    pdf.set_draw_color(56, 189, 248)   # #38bdf8
    pdf.set_line_width(0.8)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(5)

    summary_text = (
        f"За отчетный период система RegRadar обнаружила "
        f"{data['total_count']} регуляторных изменений. "
        f"Выявлено {data['critical_count']} критических рисков "
        f"(+{data['high_count']} высокого уровня). "
        f"Общий объём контролируемого финансового риска: "
        f"${data['risk_exposure']:,.0f}. "
        f"Предотвращено потенциальных штрафов благодаря автоматизации: "
        f"${data['prevented_fines']:,.0f}."
    )

    _font("", 10)
    pdf.set_text_color(51, 65, 85)     # #334155
    pdf.multi_cell(0, 6, summary_text)
    pdf.ln(6)

    # ── KPI БЛОКИ (4 карточки в ряд) ─────────────────────────────────────────
    _font("B", 13)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 8, "Ключевые показатели", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_draw_color(56, 189, 248)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(5)

    kpi_y = pdf.get_y()
    kpis = [
        ("Обнаружено НПА",   str(data["total_count"]),           (56, 189, 248)),
        ("Критических",      str(data["critical_count"]),         (220, 38, 38)),
        ("Риск (USD)",        f"${data['risk_exposure']:,.0f}",   (52, 211, 153)),
        ("Часов сэкономлено", f"{data['hours_saved']:.0f} ч",    (168, 85, 247)),
    ]

    card_w = 40
    card_h = 22
    gap    = 5
    start_x = 20

    for i, (label, value, color) in enumerate(kpis):
        x = start_x + i * (card_w + gap)
        # Граница карточки
        pdf.set_draw_color(*color)
        pdf.set_fill_color(248, 250, 252)
        pdf.set_line_width(0.6)
        pdf.rect(x, kpi_y, card_w, card_h, style="DF")
        # Значение
        pdf.set_xy(x + 2, kpi_y + 2)
        _font("B", 14)
        pdf.set_text_color(*color)
        pdf.cell(card_w - 4, 9, value, align="C")
        # Подпись
        pdf.set_xy(x + 2, kpi_y + 12)
        _font("", 7)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(card_w - 4, 5, label, align="C")

    pdf.set_y(kpi_y + card_h + 10)

    # ── ТОП-3 КРИТИЧЕСКИХ ─────────────────────────────────────────────────────
    _font("B", 13)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 8, "Топ-3 критических инцидента", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_draw_color(220, 38, 38)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(4)

    if data["top3_critical"]:
        # Заголовки таблицы
        pdf.set_fill_color(15, 23, 42)
        pdf.set_text_color(255, 255, 255)
        _font("B", 8)
        col_widths = [8, 16, 110, 26]
        headers    = ["#", "Юрисдикция", "Заголовок", "Дата"]
        for w, h in zip(col_widths, headers):
            pdf.cell(w, 7, h, border=0, fill=True, align="C")
        pdf.ln()

        # Строки данных
        for i, inc in enumerate(data["top3_critical"][:3], 1):
            pdf.set_fill_color(248, 250, 252) if i % 2 else pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(51, 65, 85)
            _font("B" if i == 1 else "", 7)

            pdf.cell(col_widths[0], 8, str(i), border="B", fill=True, align="C")
            pdf.cell(col_widths[1], 8, inc["jurisdiction"], border="B", fill=True, align="C")

            title_trunc = (inc["title"] or "—")[:90]
            pdf.cell(col_widths[2], 8, title_trunc, border="B", fill=True)
            pdf.cell(col_widths[3], 8, str(inc["effective_date"])[:12], border="B", fill=True, align="C")
            pdf.ln()

            if inc.get("summary"):
                _font("I", 7)
                pdf.set_text_color(100, 116, 139)
                pdf.set_x(28)
                pdf.multi_cell(152, 5, (inc["summary"])[:180])
    else:
        _font("I", 10)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 8, "Критических инцидентов за отчётный период не выявлено.")
        pdf.ln()

    pdf.ln(6)

    # ── СТАТИСТИКА ПО ЮРИСДИКЦИЯМ ─────────────────────────────────────────────
    if data["by_jurisdiction"]:
        _font("B", 13)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 8, "Статистика по юрисдикциям", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_draw_color(56, 189, 248)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(4)

        pdf.set_fill_color(15, 23, 42)
        pdf.set_text_color(255, 255, 255)
        _font("B", 9)
        pdf.cell(80, 7, "Юрисдикция", border=0, fill=True)
        pdf.cell(40, 7, "Обнаружено", border=0, fill=True, align="C")
        pdf.cell(40, 7, "Критических", border=0, fill=True, align="C")
        pdf.ln()

        for i, (jur, stats) in enumerate(data["by_jurisdiction"].items()):
            pdf.set_fill_color(248, 250, 252) if i % 2 else pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(51, 65, 85)
            _font("", 9)
            name = _JUR_NAMES.get(jur, jur)
            pdf.cell(80, 7, f"{name} ({jur})", border="B", fill=True)
            pdf.cell(40, 7, str(stats["count"]), border="B", fill=True, align="C")

            crit_val = stats["critical"]
            if crit_val > 0:
                pdf.set_text_color(220, 38, 38)
            pdf.cell(40, 7, str(crit_val), border="B", fill=True, align="C")
            pdf.set_text_color(51, 65, 85)
            pdf.ln()

        pdf.ln(6)

    # ── ЭФФЕКТИВНОСТЬ AI ─────────────────────────────────────────────────────
    _font("B", 13)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 8, "Эффективность AI-автоматизации", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_draw_color(168, 85, 247)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(5)

    ai_rows = [
        ("Документов обработано AI",               str(data["ai_processed"])),
        ("Сэкономлено рабочих часов",               f"{data['hours_saved']:.1f} ч"),
        ("Формула расчёта",                         f"{data['ai_processed']} × 1.5 ч/документ"),
        ("Оценочная экономия (при $80/ч юриста)",   f"${data['hours_saved'] * 80:,.0f}"),
    ]

    for label, val in ai_rows:
        _font("", 10)
        pdf.set_text_color(51, 65, 85)
        pdf.cell(120, 7, label)
        _font("B", 10)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(50, 7, val, align="R")
        pdf.ln()

    # ── ФУТЕР ─────────────────────────────────────────────────────────────────
    pdf.set_y(-25)
    pdf.set_draw_color(203, 213, 225)
    pdf.set_line_width(0.4)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(3)
    _font("I", 8)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(
        0, 5,
        f"RegRadar Enterprise — Automated Regulatory Intelligence | {now.strftime('%d.%m.%Y')}",
        align="C",
    )

    # ── Сериализация в bytes ───────────────────────────────────────────────────
    buf = io.BytesIO()
    pdf.output(buf)
    buf.seek(0)
    pdf_bytes = buf.read()

    log.info(
        "pdf_report: сгенерирован PDF %d байт (days=%d, jur=%s)",
        len(pdf_bytes), days, jurisdiction or "all",
    )
    return pdf_bytes
