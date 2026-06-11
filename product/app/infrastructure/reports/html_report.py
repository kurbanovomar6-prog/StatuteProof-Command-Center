"""
html_report.py — RegRadar Enterprise: pixel-perfect HTML executive report.

Architecture: pure semantic HTML5 + CSS, no JavaScript required.
Rendering: serve directly (browser) or pipe through WeasyPrint (PDF).

Table layout is 100% <table>-based — no absolute positioning, no transforms,
no negative margins.  All section breaks use break-inside: avoid so the
report never splits a header from its first data row across a printed page.

Usage:
  from app.infrastructure.reports.html_report import generate_html_report
  html_bytes = generate_html_report(days=30, jurisdiction="RU")
  Path("report.html").write_bytes(html_bytes)

  # PDF via WeasyPrint (optional, pip install weasyprint):
  from weasyprint import HTML
  pdf = HTML(string=html_bytes.decode()).write_pdf()
"""

import html as _html_mod
import logging
import re
from datetime import datetime

log = logging.getLogger(__name__)

_JUR_NAMES = {
    "RU": "Россия",
    "KZ": "Казахстан",
    "AZ": "Азербайджан",
    "BY": "Беларусь",
    "UZ": "Узбекистан",
}
_JUR_FLAGS = {
    "RU": "RU", "KZ": "KZ", "AZ": "AZ", "BY": "BY", "UZ": "UZ",
}
_LEVEL_BADGE = {
    "CRITICAL": ('<span class="badge badge-critical">CRITICAL</span>', "#dc2626"),
    "HIGH":     ('<span class="badge badge-high">HIGH</span>',     "#ea580c"),
    "MEDIUM":   ('<span class="badge badge-medium">MEDIUM</span>', "#ca8a04"),
    "LOW":      ('<span class="badge badge-low">LOW</span>',       "#16a34a"),
}

# Stripped prefix injected by Telegram intel collector
_TELEGRAM_PREFIX = re.compile(r"^[🔴🟠🟡🟢]\s*\[TELEGRAM_INTEL\]\s*", re.UNICODE)


def _e(text: str) -> str:
    """HTML-escape a plain string."""
    return _html_mod.escape(str(text or "—"))


def _clean_title(title: str) -> str:
    """Remove collector prefixes before display."""
    return _TELEGRAM_PREFIX.sub("", title).strip()


def _fmt_usd(amount: int | float) -> str:
    return f"${amount:,.0f}"


# ── CSS ───────────────────────────────────────────────────────────────────────

_CSS = """
/* ══════════════════════════════════════════════════════════
   RegRadar Enterprise — Night City Minimal Report Stylesheet
   Version: 2.0 (V-for-Table architectural overhaul)
   ══════════════════════════════════════════════════════════ */

/* ── Core reset ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* ── Base typography ── */
body {
  font-family: 'Inter', 'Segoe UI', 'Arial Unicode MS', 'Noto Sans',
               -apple-system, Helvetica, Arial, sans-serif;
  font-size: 10pt;
  line-height: 1.5;
  color: #334155;
  background: #e2e8f0;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

/* ── Page wrapper — A4 width, centered ── */
.page {
  max-width: 210mm;
  margin: 0 auto;
  background: #ffffff;
  box-shadow: 0 0 0 1px rgba(15,23,42,.06), 0 8px 40px rgba(15,23,42,.14);
  border-radius: 2px;
}

/* ── Print rules ── */
@page {
  size: A4 portrait;
  margin: 0;
}
@media print {
  body   { background: #fff; }
  .page  { box-shadow: none; max-width: 100%; border-radius: 0; }
}

/* ════════════════════════════════════════════════
   COVER BANNER
   ════════════════════════════════════════════════ */
.cover {
  background: #0f172a;
  padding: 36px 44px 30px;
  overflow: hidden;
  position: relative;
}
/* Decorative radial glow — top-right */
.cover::after {
  content: '';
  position: absolute;
  top: -60px; right: -60px;
  width: 260px; height: 260px;
  border-radius: 50%;
  background: radial-gradient(circle at center,
    rgba(56,189,248,.18) 0%,
    rgba(168,85,247,.06) 50%,
    transparent 70%);
  pointer-events: none;
}

.cover-brand {
  font-size: 23pt;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: -0.4px;
  line-height: 1.15;
}
.cover-platform {
  color: #93c5fd;
  font-size: 10.5pt;
  margin-top: 5px;
  letter-spacing: 0.2px;
}

/* Metadata row — uses a lean <table> to guarantee alignment without flexbox */
.cover-meta-table {
  margin-top: 18px;
  border-collapse: collapse;
  border-spacing: 0;
}
.cover-meta-table td {
  padding: 0 40px 0 0;
  vertical-align: top;
  white-space: nowrap;
}
.cover-meta-label { font-size: 8pt; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; }
.cover-meta-value { font-size: 10pt; color: #e2e8f0; font-weight: 600; margin-top: 2px; }

.cover-badge {
  display: inline-block;
  margin-top: 18px;
  padding: 3px 12px;
  background: rgba(220,38,38,.18);
  border: 1px solid rgba(220,38,38,.45);
  border-radius: 4px;
  color: #fca5a5;
  font-size: 8pt;
  font-weight: 700;
  letter-spacing: 0.7px;
  text-transform: uppercase;
}

/* ════════════════════════════════════════════════
   SECTION SCAFFOLD
   ════════════════════════════════════════════════ */
.section {
  padding: 26px 44px;
  break-inside: avoid;   /* keep section intact across print pages */
  page-break-inside: avoid;
}
.section + .section {
  border-top: 1px solid #f1f5f9;
}

/* Section heading + its accent rule as a unit — never breaks */
.section-head {
  break-inside: avoid;
  page-break-inside: avoid;
  margin-bottom: 14px;
}
.section-title {
  font-size: 13pt;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 6px;
}
.section-rule {
  height: 2px;
  border: none;
  margin: 0;
  border-radius: 2px;
}
.rule-blue   { background: linear-gradient(90deg, #38bdf8 0%, transparent 85%); }
.rule-red    { background: linear-gradient(90deg, #dc2626 0%, transparent 85%); }
.rule-purple { background: linear-gradient(90deg, #a855f7 0%, transparent 85%); }
.rule-green  { background: linear-gradient(90deg, #10b981 0%, transparent 85%); }

/* ════════════════════════════════════════════════
   KPI CARDS — 4-column <table> grid
   (table-based so columns never collapse or wrap)
   ════════════════════════════════════════════════ */
.kpi-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 10px 0;
  table-layout: fixed;
}
.kpi-card {
  background: #f8fafc;
  border-radius: 8px;
  border-width: 1.5px;
  border-style: solid;
  padding: 14px 12px 12px;
  text-align: center;
  vertical-align: middle;
}
.kpi-card.blue   { border-color: #38bdf8; }
.kpi-card.red    { border-color: #dc2626; }
.kpi-card.green  { border-color: #10b981; }
.kpi-card.purple { border-color: #a855f7; }

.kpi-value {
  display: block;
  font-size: 19pt;
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.5px;
}
.kpi-card.blue   .kpi-value { color: #38bdf8; }
.kpi-card.red    .kpi-value { color: #dc2626; }
.kpi-card.green  .kpi-value { color: #10b981; }
.kpi-card.purple .kpi-value { color: #a855f7; }

.kpi-label {
  display: block;
  font-size: 7pt;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-top: 6px;
}

/* ════════════════════════════════════════════════
   SUMMARY PARAGRAPH
   ════════════════════════════════════════════════ */
.summary {
  font-size: 10.5pt;
  line-height: 1.8;
  color: #334155;
}
.summary strong { color: #1e293b; }
.hl-blue   { color: #0369a1; font-weight: 700; }
.hl-red    { color: #dc2626; font-weight: 700; }
.hl-green  { color: #16a34a; font-weight: 700; }
.hl-purple { color: #7c3aed; font-weight: 700; }

/* ════════════════════════════════════════════════
   CORE DATA TABLE — used for ALL tabular data
   Architecture: thead locks above tbody always.
   break-inside: avoid prevents a header orphaned
   without at least one data row on the same page.
   ════════════════════════════════════════════════ */
.data-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 9pt;
  break-inside: avoid;        /* CSS Fragmentation Level 3 */
  page-break-inside: avoid;  /* Legacy browsers / WeasyPrint compat */
  border-radius: 6px;
  overflow: hidden;
}

/* Thead always rendered; browser/WeasyPrint repeats on multi-page tables */
.data-table thead { display: table-header-group; }

.data-table thead th {
  background: #0f172a;
  color: #ffffff;
  font-weight: 600;
  font-size: 8pt;
  text-align: left;
  padding: 10px 14px;
  letter-spacing: 0.3px;
  white-space: nowrap;
  border: none;
}
.data-table thead th.c { text-align: center; }
.data-table thead th.r { text-align: right; }

/* Zebra rows — controlled via nth-child on <tr>, NOT on <tbody> */
.data-table tbody tr:nth-child(odd)  { background: #f8fafc; }
.data-table tbody tr:nth-child(even) { background: #ffffff; }

.data-table tbody td {
  padding: 9px 14px;
  border-bottom: 1px solid #e2e8f0;
  vertical-align: middle;
  color: #334155;
  word-break: break-word;
}
.data-table tbody td.c   { text-align: center; }
.data-table tbody td.r   { text-align: right; }
.data-table tbody td.num {
  font-size: 11pt;
  font-weight: 800;
  text-align: center;
  color: #1e293b;
}
.data-table tbody td.muted { color: #64748b; font-size: 8.5pt; }
.data-table tbody tr.top-1 td { font-weight: 600; }

/* Incident summary sub-row (spans full width below incident title) */
.incident-sub {
  font-size: 8pt;
  color: #64748b;
  font-style: italic;
  padding: 0 14px 10px 32px;
  border-bottom: 1px solid #e2e8f0;
}
.incident-sub:last-child { border-bottom: none; }

/* Critical value — red text inside normal cell */
.crit-val { color: #dc2626; font-weight: 700; }

/* ════════════════════════════════════════════════
   BADGES
   ════════════════════════════════════════════════ */
.badge {
  display: inline-block;
  padding: 2px 9px;
  border-radius: 4px;
  font-size: 7.5pt;
  font-weight: 700;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  white-space: nowrap;
  line-height: 1.4;
}
.badge-critical { background: #dc2626; color: #fff; }
.badge-high     { background: #ea580c; color: #fff; }
.badge-medium   { background: #ca8a04; color: #fff; }
.badge-low      { background: #16a34a; color: #fff; }

/* ════════════════════════════════════════════════
   JURISDICTION CHIP
   ════════════════════════════════════════════════ */
.jur {
  display: inline-block;
  padding: 2px 7px;
  background: #1e293b;
  color: #93c5fd;
  border-radius: 3px;
  font-size: 8pt;
  font-weight: 700;
  letter-spacing: 0.6px;
}

/* ════════════════════════════════════════════════
   AI EFFICIENCY TABLE
   ════════════════════════════════════════════════ */
.ai-table {
  width: 100%;
  border-collapse: collapse;
}
.ai-table tr {
  border-bottom: 1px solid #f1f5f9;
  break-inside: avoid;
  page-break-inside: avoid;
}
.ai-table tr:last-child { border-bottom: none; }
.ai-table td {
  padding: 9px 2px;
  font-size: 9.5pt;
  vertical-align: middle;
}
.ai-table .ai-label { color: #64748b; width: 65%; }
.ai-table .ai-value {
  text-align: right;
  font-weight: 700;
  font-size: 10.5pt;
  color: #1e293b;
}

/* ════════════════════════════════════════════════
   REPORT FOOTER
   ════════════════════════════════════════════════ */
.report-footer {
  background: #0f172a;
  padding: 18px 44px;
  border-top: 2px solid #1e40af;
  break-inside: avoid;
  page-break-inside: avoid;
}
.report-footer p {
  font-size: 8pt;
  color: #475569;
  text-align: center;
  line-height: 1.75;
}
.report-footer strong { color: #94a3b8; }

/* ── Utility ── */
.no-break { break-inside: avoid; page-break-inside: avoid; }
.mt8  { margin-top: 8px; }
.mt12 { margin-top: 12px; }
.mt20 { margin-top: 20px; }
"""


# ── HTML TEMPLATE ────────────────────────────────────────────────────────────

def _render_html(data: dict, jurisdiction: str | None, days: int) -> str:
    now         = datetime.utcnow()
    jur_label   = _JUR_NAMES.get(jurisdiction, "Все юрисдикции СНГ") if jurisdiction else "Все юрисдикции СНГ"
    generated   = now.strftime("%d.%m.%Y %H:%M") + " UTC"

    # ── KPI VALUES ──────────────────────────────────────────────────────────
    total_count     = data["total_count"]
    critical_count  = data["critical_count"]
    risk_exposure   = data["risk_exposure"]
    prevented_fines = min(data["prevented_fines"], risk_exposure)
    ai_processed    = data["ai_processed"]
    hours_saved     = data["hours_saved"]

    # ── SUMMARY PARAGRAPH ───────────────────────────────────────────────────
    summary_html = (
        f"За отчётный период система <strong>RegRadar</strong> обнаружила "
        f"<span class='hl-blue'>{total_count}</span> регуляторных изменений. "
        f"Выявлено <span class='hl-red'>{critical_count} критических</span> рисков "
        f"(+{data['high_count']} высокого уровня). "
        f"Общий объём контролируемого финансового риска: "
        f"<span class='hl-green'>{_fmt_usd(risk_exposure)}</span>. "
        f"Предотвращено потенциальных штрафов благодаря автоматизации: "
        f"<span class='hl-purple'>{_fmt_usd(prevented_fines)}</span>."
    )

    # ── TOP-3 INCIDENTS TABLE ROWS ───────────────────────────────────────────
    top3_rows = ""
    for i, inc in enumerate(data["top3_critical"][:3], 1):
        title   = _e(_clean_title(inc["title"]))
        jur     = _e(inc["jurisdiction"])
        eff     = _e(inc["effective_date"][:10] if inc["effective_date"] else "—")
        summary = _e(inc.get("summary", ""))[:200]
        row_cls = "top-1" if i == 1 else ""

        top3_rows += f"""
        <tr class="{row_cls}">
          <td class="num" style="width:4%">{i}</td>
          <td style="width:10%"><span class="jur">{jur}</span></td>
          <td style="width:66%;padding-bottom:{'0' if summary else '9px'}">{title}</td>
          <td class="c muted" style="width:20%;white-space:nowrap">{eff}</td>
        </tr>"""
        if summary:
            top3_rows += f"""
        <tr class="no-break">
          <td colspan="4" class="incident-sub">{summary}</td>
        </tr>"""

    if not top3_rows:
        top3_rows = (
            '<tr><td colspan="4" style="padding:14px;text-align:center;'
            'color:#64748b;font-style:italic;">Критических инцидентов за период не выявлено.</td></tr>'
        )

    # ── JURISDICTION TABLE ROWS ─────────────────────────────────────────────
    jur_rows = ""
    for jur_code, stats in data["by_jurisdiction"].items():
        name  = _e(_JUR_NAMES.get(jur_code, jur_code))
        code  = _e(jur_code)
        count = stats["count"]
        crit  = stats["critical"]
        crit_cell = (
            f'<span class="crit-val">{crit}</span>' if crit > 0 else str(crit)
        )
        jur_rows += f"""
        <tr>
          <td>{name} <span class="jur">{code}</span></td>
          <td class="c">{count}</td>
          <td class="c">{crit_cell}</td>
        </tr>"""

    if not jur_rows:
        jur_rows = '<tr><td colspan="3" style="padding:14px;color:#64748b;font-style:italic;">Нет данных.</td></tr>'

    # ── AI EFFICIENCY ROWS ──────────────────────────────────────────────────
    cost_saved = hours_saved * 80
    ai_rows = [
        ("Документов обработано AI",             f"{ai_processed}"),
        ("Сэкономлено рабочих часов",            f"{hours_saved:.1f}&nbsp;ч"),
        ("Формула расчёта",                      f"{ai_processed}&nbsp;×&nbsp;1.5&nbsp;ч/документ"),
        ("Оценочная экономия (при $80/ч юриста)", _fmt_usd(cost_saved)),
    ]
    ai_html = ""
    for label, value in ai_rows:
        ai_html += f"""
        <tr>
          <td class="ai-label">{label}</td>
          <td class="ai-value">{value}</td>
        </tr>"""

    # ── ASSEMBLE FULL HTML ───────────────────────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RegRadar Enterprise — Исполнительный отчёт</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>{_CSS}</style>
</head>
<body>
<div class="page">

  <!-- ══════════════════════ COVER BANNER ══════════════════════ -->
  <div class="cover">
    <div class="cover-brand">RegRadar Enterprise</div>
    <div class="cover-platform">Regulatory Intelligence Platform · CIS Markets</div>

    <table class="cover-meta-table">
      <tr>
        <td>
          <div class="cover-meta-label">Юрисдикция</div>
          <div class="cover-meta-value">{_e(jur_label)}</div>
        </td>
        <td>
          <div class="cover-meta-label">Период анализа</div>
          <div class="cover-meta-value">{_e(data['period_start'])} — {_e(data['period_end'])}</div>
        </td>
        <td>
          <div class="cover-meta-label">Сформирован</div>
          <div class="cover-meta-value">{_e(generated)}</div>
        </td>
      </tr>
    </table>

    <div class="cover-badge">Конфиденциально — только для топ-менеджмента</div>
  </div>

  <!-- ══════════════════════ SUMMARY ══════════════════════ -->
  <div class="section">
    <div class="section-head">
      <div class="section-title">Сводка</div>
      <hr class="section-rule rule-blue">
    </div>
    <p class="summary">{summary_html}</p>
  </div>

  <!-- ══════════════════════ KPI CARDS ══════════════════════ -->
  <div class="section" style="padding-top:0">
    <table class="kpi-table">
      <colgroup>
        <col style="width:25%"><col style="width:25%">
        <col style="width:25%"><col style="width:25%">
      </colgroup>
      <tbody>
        <tr>
          <td class="kpi-card blue">
            <span class="kpi-value">{total_count}</span>
            <span class="kpi-label">Обнаружено НПА</span>
          </td>
          <td class="kpi-card red">
            <span class="kpi-value">{critical_count}</span>
            <span class="kpi-label">Критических</span>
          </td>
          <td class="kpi-card green">
            <span class="kpi-value" style="font-size:14pt">{_fmt_usd(risk_exposure)}</span>
            <span class="kpi-label">Риск (USD)</span>
          </td>
          <td class="kpi-card purple">
            <span class="kpi-value">{hours_saved:.0f}&nbsp;ч</span>
            <span class="kpi-label">Часов сэкономлено</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- ══════════════════════ TOP-3 INCIDENTS ══════════════════════ -->
  <div class="section no-break">
    <div class="section-head">
      <div class="section-title">Топ-3 критических инцидента</div>
      <hr class="section-rule rule-red">
    </div>

    <!--
      V-for-Table fix:
      Strict <table> with fixed layout.
      thead is a separate element so the browser/WeasyPrint
      guarantees it always renders above tbody rows.
      No absolute positioning, no transform, no negative margins.
    -->
    <table class="data-table">
      <colgroup>
        <col style="width:4%">
        <col style="width:10%">
        <col style="width:66%">
        <col style="width:20%">
      </colgroup>
      <thead>
        <tr>
          <th class="c">#</th>
          <th>Юрисдикция</th>
          <th>Заголовок документа</th>
          <th class="c">Дата вступления</th>
        </tr>
      </thead>
      <tbody>{top3_rows}
      </tbody>
    </table>
  </div>

  <!-- ══════════════════════ BY JURISDICTION ══════════════════════ -->
  <div class="section no-break">
    <div class="section-head">
      <div class="section-title">Статистика по юрисдикциям</div>
      <hr class="section-rule rule-blue">
    </div>

    <!--
      break-inside: avoid on this table guarantees the header row
      never sits alone at the bottom of a printed page.
    -->
    <table class="data-table" style="break-inside:avoid;page-break-inside:avoid">
      <colgroup>
        <col style="width:55%">
        <col style="width:22.5%">
        <col style="width:22.5%">
      </colgroup>
      <thead>
        <tr>
          <th>Юрисдикция</th>
          <th class="c">Обнаружено</th>
          <th class="c">Критических</th>
        </tr>
      </thead>
      <tbody>{jur_rows}
      </tbody>
    </table>
  </div>

  <!-- ══════════════════════ AI EFFICIENCY ══════════════════════ -->
  <div class="section no-break">
    <div class="section-head">
      <div class="section-title">Эффективность AI-автоматизации</div>
      <hr class="section-rule rule-purple">
    </div>

    <table class="ai-table">{ai_html}
    </table>
  </div>

  <!-- ══════════════════════ FOOTER ══════════════════════ -->
  <div class="report-footer">
    <p>
      <strong>RegRadar Enterprise</strong> — Automated Regulatory Intelligence · CIS Markets<br>
      Источники: ЦБР (Россия) · НБК (Казахстан) · ЦБА (Азербайджан) · НБРБ (Беларусь) · ЦБУ (Узбекистан)<br>
      Отчёт сформирован автоматически {_e(generated)} · Конфиденциально
    </p>
  </div>

</div><!-- .page -->
</body>
</html>"""


# ── PUBLIC API ────────────────────────────────────────────────────────────────

def generate_html_report(
    days: int = 30,
    jurisdiction: str | None = None,
) -> bytes:
    """
    Generate a branded HTML executive report from live DB data.

    Returns UTF-8 encoded bytes suitable for:
      - Serving via FastAPI Response(media_type="text/html")
      - Converting to PDF via WeasyPrint: HTML(string=...).write_pdf()
      - Saving to disk for email attachment
    """
    from app.infrastructure.reports.executive_report import _fetch_report_data
    data = _fetch_report_data(days, jurisdiction)
    html = _render_html(data, jurisdiction, days)
    log.info(
        "html_report: generated %d bytes (days=%d, jur=%s)",
        len(html), days, jurisdiction or "all",
    )
    return html.encode("utf-8")
