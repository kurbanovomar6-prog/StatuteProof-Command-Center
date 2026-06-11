"""
ytd_metrics.py — Year-to-Date Performance Module RegRadar Enterprise.

Назначение:
  Даёт клиенту точные данные для обоснования ROI подписки $500/мес:
  "Система предотвратила штрафов на $127,000 за год при стоимости $6,000."

Метрики YTD (Year-to-Date):
  total_processed_ytd       — всего обработанных документов с 1 января
  fines_prevented_ytd       — суммарный предотвращённый штраф (USD)
  avg_time_to_discovery_sec — среднее время обнаружения нового НПА
  cost_per_document_usd     — стоимость обработки одного документа AI-пайплайном
  roi_multiplier            — отношение saved_fines / subscription_cost

Стоимость обработки одного документа (cost_per_document_usd):
  LLM (GPT-4o-mini):  ~3 вызова × ~1500 токенов = 4500 токенов
    Input:  $0.15/1M → $0.000675
    Output: $0.60/1M → $0.000900
  OCR (tesseract):    $0.00 (локально)
  Итого ≈ $0.0016 на документ
  Константа _LLM_COST_PER_DOC может быть переопределена через env.

Снэпшоты:
  Таблица ytd_snapshots хранит агрегацию по (year, month, jurisdiction).
  Задача ytd_snapshot_task (Celery) обновляет текущий месяц ежедневно в 01:00.
"""

import logging
import os
from datetime import datetime
from typing import Optional

from sqlalchemy import text

log = logging.getLogger(__name__)

# ── Константы стоимости ──────────────────────────────────────────────────────
# $0.15/1M input + $0.60/1M output, ~4500 токен/документ × 3 стадии
_LLM_COST_PER_DOC   = float(os.getenv("LLM_COST_PER_DOC",   "0.0016"))
# Стоимость подписки в месяц для расчёта ROI
_SUBSCRIPTION_COST_MONTHLY = float(os.getenv("SUBSCRIPTION_COST_MONTHLY", "500.0"))

# Ставка юриста ($80/ч × 1.5 ч/документ = $120/документ)
_LAWYER_COST_PER_DOC = 120.0

_JUR_NAMES = {
    "RU": "Россия", "KZ": "Казахстан",
    "AZ": "Азербайджан", "BY": "Беларусь", "UZ": "Узбекистан",
}


def _get_engine():
    from app.infrastructure.db.session import engine
    return engine


def _ensure_ytd_schema() -> None:
    """Гарантирует существование таблицы ytd_snapshots."""
    engine = _get_engine()
    with engine.connect() as c:
        c.execute(text("""
            CREATE TABLE IF NOT EXISTS ytd_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                jurisdiction TEXT DEFAULT NULL,
                total_processed INTEGER DEFAULT 0,
                critical_count INTEGER DEFAULT 0,
                high_count INTEGER DEFAULT 0,
                fines_prevented_usd INTEGER DEFAULT 0,
                avg_time_to_discovery_sec REAL DEFAULT 0.0,
                avg_compute_cost_usd REAL DEFAULT 0.0,
                total_compute_cost_usd REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(year, month, jurisdiction)
            )
        """))
        c.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ytd_ym
            ON ytd_snapshots (year, month)
        """))
        c.commit()


# ── Вычисление time_to_discovery ─────────────────────────────────────────────

def compute_time_to_discovery(publication_date: str | None, extracted_at: datetime | None) -> int | None:
    """
    Вычисляет задержку обнаружения в секундах.
    Возвращает None если дата публикации недоступна.

    Формула: extracted_at - publication_date (в секундах).
    Чем меньше — тем быстрее система обнаружила новый НПА.
    """
    if not publication_date or not extracted_at:
        return None
    try:
        pub_dt = datetime.fromisoformat(publication_date[:10])
        return max(0, int((extracted_at - pub_dt).total_seconds()))
    except (ValueError, TypeError):
        return None


# ── Основная агрегация (текущий YTD) ─────────────────────────────────────────

def get_ytd_performance(jurisdiction: Optional[str] = None) -> dict:
    """
    Возвращает YTD-метрики производительности системы.

    Используется:
      - API endpoint GET /api/v1/analytics/ytd
      - Дашборд RegRadar (секция "Эффективность / ROI")
      - Исполнительный отчёт (раздел "Ценность продукта")

    Параметры:
      jurisdiction — фильтр по юрисдикции (None = все).

    Возвращает dict:
      {
        "period":                str,      "01.01.2026 — 20.05.2026"
        "total_processed":       int,
        "critical_count":        int,
        "high_count":            int,
        "fines_prevented_usd":   int,
        "fines_prevented_fmt":   str,      "$127,500"
        "avg_discovery_hours":   float,    среднее в часах
        "avg_discovery_label":   str,      "2.3 ч"
        "cost_per_document_usd": float,
        "total_compute_cost_usd":float,
        "lawyer_hours_saved":    float,    часов юриста
        "lawyer_cost_saved_usd": float,    в деньгах
        "roi_multiplier":        float,    fines_prevented / subscription_cost_ytd
        "roi_label":             str,      "ROI 21.2x"
        "subscription_cost_ytd": float,    months_ytd × monthly_rate
        "by_jurisdiction":       dict,
        "monthly_trend":         list,     последние 6 месяцев
        "generated_at":          str,
      }
    """
    _ensure_ytd_schema()
    engine = _get_engine()
    now    = datetime.utcnow()

    # Начало текущего года
    year_start = datetime(now.year, 1, 1).isoformat()
    jur_filter  = "AND jurisdiction = :jur" if jurisdiction else ""
    bind: dict  = {"year_start": year_start}
    if jurisdiction:
        bind["jur"] = jurisdiction

    try:
        with engine.connect() as c:
            # ── Основные счётчики ─────────────────────────────────────────
            main = c.execute(text(f"""
                SELECT
                    COUNT(*)                         AS total,
                    SUM(CASE WHEN critical_level='CRITICAL' THEN 1 ELSE 0 END) AS crits,
                    SUM(CASE WHEN critical_level='HIGH' THEN 1 ELSE 0 END)     AS highs,
                    COALESCE(SUM(fines_usd), 0)      AS fines_sum,
                    AVG(time_to_discovery_sec)        AS avg_disc,
                    COALESCE(SUM(compute_cost_usd), 0) AS compute_sum,
                    AVG(compute_cost_usd)              AS avg_compute
                FROM regulations
                WHERE extracted_at >= :year_start {jur_filter}
            """), bind).fetchone()

            total        = int(main[0] or 0)
            crits        = int(main[1] or 0)
            highs        = int(main[2] or 0)
            fines_sum    = int(main[3] or 0)
            avg_disc_sec = float(main[4] or 0)
            compute_sum  = float(main[5] or 0)
            avg_compute  = float(main[6] or _LLM_COST_PER_DOC)

            # Если fines_usd не заполнен — оценка по уровням
            if fines_sum == 0 and (crits + highs) > 0:
                fines_sum = crits * 2_500_000 + highs * 500_000

            # Если compute_cost_usd не заполнен — стандартная оценка
            if compute_sum == 0:
                compute_sum = total * _LLM_COST_PER_DOC
                avg_compute = _LLM_COST_PER_DOC

            # ── Разбивка по юрисдикциям ───────────────────────────────────
            jur_rows = c.execute(text(f"""
                SELECT jurisdiction,
                       COUNT(*) AS cnt,
                       SUM(CASE WHEN critical_level='CRITICAL' THEN 1 ELSE 0 END),
                       COALESCE(SUM(fines_usd), 0)
                FROM regulations
                WHERE extracted_at >= :year_start {jur_filter}
                GROUP BY jurisdiction
                ORDER BY COUNT(*) DESC
            """), bind).fetchall()

            # ── Тренд за последние 6 месяцев ─────────────────────────────
            trend_rows = c.execute(text(f"""
                SELECT
                    strftime('%Y-%m', extracted_at)  AS ym,
                    COUNT(*)                          AS cnt,
                    SUM(CASE WHEN critical_level='CRITICAL' THEN 1 ELSE 0 END),
                    COALESCE(SUM(fines_usd), 0)
                FROM regulations
                WHERE extracted_at >= date('now', '-6 months')
                  {jur_filter}
                GROUP BY ym
                ORDER BY ym ASC
            """), bind).fetchall()

    except Exception as exc:
        log.error("[YTD] get_ytd_performance: ошибка запроса — %s", exc)
        return _empty_ytd(jurisdiction, str(exc))

    # ── Производные метрики ───────────────────────────────────────────────────
    avg_disc_hours   = round(avg_disc_sec / 3600, 2) if avg_disc_sec else 0.0
    lawyer_hours     = round(total * 1.5, 1)
    lawyer_cost_usd  = round(lawyer_hours * 80, 2)  # $80/час юриста

    # Months since Jan 1 (минимум 1)
    months_ytd         = max(1, now.month)
    subscription_ytd   = round(months_ytd * _SUBSCRIPTION_COST_MONTHLY, 2)
    roi                = round(fines_sum / subscription_ytd, 2) if subscription_ytd > 0 else 0.0

    # Разбивка по юрисдикциям
    by_jur: dict = {}
    for row in jur_rows:
        jcode = row[0]
        jfines = int(row[3] or 0)
        if jfines == 0:
            jcrit = int(row[2] or 0)
            jfines = jcrit * 2_500_000
        by_jur[jcode] = {
            "name":     _JUR_NAMES.get(jcode, jcode),
            "count":    int(row[1]),
            "critical": int(row[2] or 0),
            "fines_usd": jfines,
        }

    # Тренд
    monthly_trend = [
        {
            "month":     row[0],
            "count":     int(row[1]),
            "critical":  int(row[2] or 0),
            "fines_usd": int(row[3] or 0),
        }
        for row in trend_rows
    ]

    period_start = f"01.01.{now.year}"
    period_end   = now.strftime("%d.%m.%Y")

    return {
        "period":                f"{period_start} — {period_end}",
        "jurisdiction":          jurisdiction or "все",
        "total_processed":       total,
        "critical_count":        crits,
        "high_count":            highs,
        "fines_prevented_usd":   fines_sum,
        "fines_prevented_fmt":   f"${fines_sum:,}",
        "avg_discovery_sec":     round(avg_disc_sec),
        "avg_discovery_hours":   avg_disc_hours,
        "avg_discovery_label":   f"{avg_disc_hours:.1f} ч" if avg_disc_hours else "нет данных",
        "cost_per_document_usd": round(avg_compute, 4),
        "total_compute_cost_usd": round(compute_sum, 2),
        "lawyer_hours_saved":    lawyer_hours,
        "lawyer_cost_saved_usd": lawyer_cost_usd,
        "roi_multiplier":        roi,
        "roi_label":             f"ROI {roi:.1f}x" if roi > 0 else "ROI — (нет данных)",
        "subscription_cost_ytd": subscription_ytd,
        "by_jurisdiction":       by_jur,
        "monthly_trend":         monthly_trend,
        "generated_at":          now.isoformat(),
    }


def _empty_ytd(jurisdiction: Optional[str], error: str) -> dict:
    now = datetime.utcnow()
    return {
        "period":                f"01.01.{now.year} — {now.strftime('%d.%m.%Y')}",
        "jurisdiction":          jurisdiction or "все",
        "total_processed":       0,
        "critical_count":        0,
        "high_count":            0,
        "fines_prevented_usd":   0,
        "fines_prevented_fmt":   "$0",
        "avg_discovery_hours":   0.0,
        "avg_discovery_label":   "нет данных",
        "cost_per_document_usd": _LLM_COST_PER_DOC,
        "total_compute_cost_usd": 0.0,
        "lawyer_hours_saved":    0.0,
        "lawyer_cost_saved_usd": 0.0,
        "roi_multiplier":        0.0,
        "roi_label":             "ROI — (нет данных)",
        "subscription_cost_ytd": 0.0,
        "by_jurisdiction":       {},
        "monthly_trend":         [],
        "generated_at":          now.isoformat(),
        "error":                 error,
    }


# ── Сохранение ежемесячного снэпшота ─────────────────────────────────────────

def save_ytd_snapshot(jurisdiction: Optional[str] = None) -> dict:
    """
    Вычисляет и сохраняет (UPSERT) снэпшот текущего месяца.
    Вызывается Celery ytd_snapshot_task ежедневно в 01:00.

    Логика UPSERT: если запись (year, month, jurisdiction) уже существует →
    обновляет существующую. Это позволяет ежедневно актуализировать данные
    текущего месяца без дублирования.

    Возвращает dict сохранённого снэпшота.
    """
    _ensure_ytd_schema()
    engine = _get_engine()
    now    = datetime.utcnow()
    year, month = now.year, now.month

    data = get_ytd_performance(jurisdiction)

    # Снэпшот за текущий месяц — данные только этого месяца
    month_start = datetime(year, month, 1).isoformat()
    jur_filter  = "AND jurisdiction = :jur" if jurisdiction else ""
    bind: dict  = {"month_start": month_start}
    if jurisdiction:
        bind["jur"] = jurisdiction

    try:
        with engine.connect() as c:
            row = c.execute(text(f"""
                SELECT
                    COUNT(*),
                    SUM(CASE WHEN critical_level='CRITICAL' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN critical_level='HIGH' THEN 1 ELSE 0 END),
                    COALESCE(SUM(fines_usd), 0),
                    AVG(time_to_discovery_sec),
                    AVG(compute_cost_usd),
                    COALESCE(SUM(compute_cost_usd), 0)
                FROM regulations
                WHERE extracted_at >= :month_start {jur_filter}
            """), bind).fetchone()

            m_total    = int(row[0] or 0)
            m_crits    = int(row[1] or 0)
            m_highs    = int(row[2] or 0)
            m_fines    = int(row[3] or 0)
            m_disc     = float(row[4] or 0)
            m_avg_cost = float(row[5] or _LLM_COST_PER_DOC)
            m_cost     = float(row[6] or m_total * _LLM_COST_PER_DOC)

            if m_fines == 0:
                m_fines = m_crits * 2_500_000 + m_highs * 500_000

            jur_val = jurisdiction or "ALL"
            c.execute(text("""
                INSERT INTO ytd_snapshots
                    (year, month, jurisdiction, total_processed, critical_count,
                     high_count, fines_prevented_usd, avg_time_to_discovery_sec,
                     avg_compute_cost_usd, total_compute_cost_usd, created_at)
                VALUES
                    (:y, :m, :jur, :total, :crits, :highs, :fines,
                     :disc, :avg_cost, :cost, :now)
                ON CONFLICT(year, month, jurisdiction) DO UPDATE SET
                    total_processed           = excluded.total_processed,
                    critical_count            = excluded.critical_count,
                    high_count                = excluded.high_count,
                    fines_prevented_usd       = excluded.fines_prevented_usd,
                    avg_time_to_discovery_sec = excluded.avg_time_to_discovery_sec,
                    avg_compute_cost_usd      = excluded.avg_compute_cost_usd,
                    total_compute_cost_usd    = excluded.total_compute_cost_usd,
                    created_at                = excluded.created_at
            """), {
                "y": year, "m": month, "jur": jur_val,
                "total": m_total, "crits": m_crits, "highs": m_highs,
                "fines": m_fines, "disc": m_disc,
                "avg_cost": m_avg_cost, "cost": m_cost,
                "now": now.isoformat(),
            })
            c.commit()

        log.info(
            "[YTD] снэпшот %d-%02d [%s]: %d документов, штрафов $%s",
            year, month, jurisdiction or "ALL", m_total, f"{m_fines:,}",
        )
        return {
            "year": year, "month": month,
            "jurisdiction": jur_val,
            "total_processed": m_total,
            "fines_prevented_usd": m_fines,
        }

    except Exception as exc:
        log.error("[YTD] save_ytd_snapshot: ошибка — %s", exc)
        return {"error": str(exc)}


def get_monthly_trend(months: int = 12, jurisdiction: Optional[str] = None) -> list[dict]:
    """
    Тренд помесячной активности за последние `months` месяцев.
    Используется для графиков дашборда.
    """
    _ensure_ytd_schema()
    engine = _get_engine()
    jur_filter = "AND jurisdiction = :jur" if jurisdiction else "AND jurisdiction = 'ALL'"
    bind: dict = {}
    if jurisdiction:
        bind["jur"] = jurisdiction

    try:
        with engine.connect() as c:
            rows = c.execute(text(f"""
                SELECT year, month, total_processed, critical_count,
                       fines_prevented_usd, avg_compute_cost_usd
                FROM ytd_snapshots
                WHERE 1=1 {jur_filter}
                ORDER BY year DESC, month DESC
                LIMIT :lim
            """), {**bind, "lim": months}).fetchall()

        return [
            {
                "label":           f"{r[0]}-{r[1]:02d}",
                "total":           r[2],
                "critical":        r[3],
                "fines_usd":       r[4],
                "cost_per_doc":    r[5],
            }
            for r in reversed(rows)
        ]
    except Exception as exc:
        log.error("[YTD] get_monthly_trend: %s", exc)
        return []
