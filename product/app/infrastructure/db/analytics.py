"""
analytics.py — ORM/SQL-бэкенд аналитических KPI-карточек дашборда RegRadar.

Функции:
  ensure_analytics_schema()    — идемпотентная миграция: добавляет fines_usd INTEGER
  backfill_fines_usd()         — разбирает ai_analysis JSON, заполняет fines_usd
  total_risk_exposure()        — КПЭ "Финансовый риск": SUM(fines_usd) по активным записям
  hours_saved_by_ai()          — КПЭ "Экономия времени": count(AI-обработанных) × 1.5
  get_dashboard_kpis()         — агрегированный ответ для всех KPI-карточек дашборда

Маппинг статусов:
  Пользовательские термины → значения в таблице regulations:
    "ACTIVE"      → 'VALIDATED'   — нормативные акты, прошедшие верификацию
    "IN_PROGRESS" → 'PROCESSING'  — документы в обработке

Колонка fines_usd:
  Числовое значение штрафа/санкции в долларах США (INTEGER).
  Исходно хранится в ai_analysis JSON как строка: {"fines": "$25,000"}.
  Функция backfill_fines_usd() парсит и переносит в отдельный индексируемый столбец.
"""

import json
import logging
import re
from datetime import datetime

from sqlalchemy import text

log = logging.getLogger(__name__)

# ── Маппинг пользовательских статусов → значения в БД ────────────────────────
_ACTIVE_STATUSES     = ("VALIDATED",)           # "ACTIVE" в терминах дашборда
_INPROGRESS_STATUSES = ("PROCESSING",)          # "IN_PROGRESS" в терминах дашборда
_RISK_STATUSES       = _ACTIVE_STATUSES + _INPROGRESS_STATUSES  # для KPI финансового риска

# ── Коэффициент экономии времени ──────────────────────────────────────────────
# Среднее время ручной обработки одного нормативного документа юристом — 1.5 часа
_HOURS_PER_DOC = 1.5


def _get_engine():
    """Ленивый импорт engine — избегаем циклических зависимостей."""
    from app.infrastructure.db.session import engine
    return engine


def _parse_fines_usd(ai_analysis_json: str | None) -> int | None:
    """
    Разбирает строку штрафа из ai_analysis JSON и возвращает целое число в USD.

    Поддерживаемые форматы из run_multi_agent():
      "$25,000"   → 25000
      "$1,500,000" → 1500000
      "N/A"       → None
      ""          → None
      "25000"     → 25000
    """
    if not ai_analysis_json:
        return None
    try:
        data  = json.loads(ai_analysis_json)
        fines = data.get("fines", "")

        if not fines or fines.strip().upper() in ("N/A", "UNKNOWN", "—", "-", ""):
            return None

        # Убираем знак доллара, пробелы, запятые — оставляем только цифры
        digits = re.sub(r"[^\d]", "", str(fines))
        if not digits:
            return None

        value = int(digits)
        # Здравомыслящий верхний предел — предотвращаем OCR-артефакты
        if value > 10_000_000_000:
            log.warning("_parse_fines_usd: подозрительно большой штраф %d — пропускаем", value)
            return None

        return value if value > 0 else None

    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        log.debug("_parse_fines_usd: ошибка разбора — %s", exc)
        return None


def ensure_analytics_schema() -> None:
    """
    Идемпотентная миграция схемы для аналитических запросов.
    Добавляет в таблицу regulations:
      fines_usd INTEGER  — числовое значение штрафа/санкции в USD
                           (перенесено из ai_analysis JSON для быстрых агрегаций)
    Безопасно вызывать при каждом старте приложения — не перезаписывает данные.
    """
    engine = _get_engine()
    try:
        with engine.connect() as c:
            # Проверяем существующие колонки через PRAGMA
            cols = {
                row[1]
                for row in c.execute(text("PRAGMA table_info(regulations)"))
            }

            if "fines_usd" not in cols:
                c.execute(text(
                    "ALTER TABLE regulations ADD COLUMN fines_usd INTEGER DEFAULT NULL"
                ))
                c.commit()
                log.info(
                    "analytics: добавлена колонка fines_usd в таблицу regulations"
                )

            # Также убеждаемся что ai_analysis существует (создаётся pipeline.py)
            if "ai_analysis" not in cols:
                c.execute(text(
                    "ALTER TABLE regulations ADD COLUMN ai_analysis TEXT DEFAULT NULL"
                ))
                c.commit()
                log.info(
                    "analytics: добавлена колонка ai_analysis в таблицу regulations"
                )

            # Индекс для быстрой агрегации по fines_usd + status
            c.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_regulations_fines_status "
                "ON regulations (status, fines_usd) "
                "WHERE fines_usd IS NOT NULL"
            ))
            c.commit()

    except Exception as exc:
        log.error("ensure_analytics_schema: ошибка миграции — %s", exc)


def backfill_fines_usd() -> int:
    """
    Разовый бэкфилл: разбирает ai_analysis JSON всех существующих записей
    и заполняет колонку fines_usd числовыми значениями.

    Пропускает записи где fines_usd уже заполнен — идемпотентно.
    Возвращает количество обновлённых строк.

    Рекомендуется вызывать однократно через admin-скрипт или при деплое:
      from app.infrastructure.db.analytics import backfill_fines_usd
      backfill_fines_usd()
    """
    ensure_analytics_schema()
    engine  = _get_engine()
    updated = 0

    try:
        with engine.connect() as c:
            # Загружаем только записи с ai_analysis но без fines_usd
            rows = c.execute(text(
                "SELECT id, ai_analysis FROM regulations "
                "WHERE ai_analysis IS NOT NULL "
                "  AND fines_usd IS NULL"
            )).fetchall()

        log.info("backfill_fines_usd: обрабатываем %d записей...", len(rows))

        for row_id, ai_json in rows:
            fines_value = _parse_fines_usd(ai_json)
            if fines_value is None:
                continue
            try:
                with engine.connect() as c:
                    c.execute(
                        text("UPDATE regulations SET fines_usd=:val WHERE id=:id"),
                        {"val": fines_value, "id": row_id},
                    )
                    c.commit()
                updated += 1
            except Exception as row_err:
                log.warning("backfill_fines_usd: ошибка id=%d — %s", row_id, row_err)

        log.info("backfill_fines_usd: обновлено %d из %d записей", updated, len(rows))

    except Exception as exc:
        log.error("backfill_fines_usd: критическая ошибка — %s", exc)

    return updated


def total_risk_exposure(jurisdiction: str | None = None) -> dict:
    """
    KPI "Финансовый риск" — Общий потенциальный объём санкций.

    Формула: SUM(fines_usd) WHERE status IN ('VALIDATED', 'PROCESSING')
    Маппинг: 'VALIDATED' = "ACTIVE", 'PROCESSING' = "IN_PROGRESS" в терминах дашборда.

    Параметры:
      jurisdiction — фильтр по юрисдикции ('RU', 'KZ', 'AZ', 'BY', 'UZ').
                     None = все юрисдикции суммарно.

    Возвращает dict:
      {
        "total_usd":        int,         общая сумма в USD
        "total_formatted":  str,         отформатированная сумма "$1,250,000"
        "document_count":   int,         количество документов с ненулевым штрафом
        "by_jurisdiction":  dict,        разбивка по юрисдикциям {jur: sum_usd}
        "status_breakdown": dict,        разбивка по статусам
        "updated_at":       str,         время запроса (UTC ISO)
      }
    """
    ensure_analytics_schema()
    engine = _get_engine()

    # Плейсхолдер для статусов
    status_placeholders = ", ".join(f"'{s}'" for s in _RISK_STATUSES)

    try:
        with engine.connect() as c:
            # Суммарный финансовый риск
            if jurisdiction:
                total_row = c.execute(text(
                    f"SELECT COALESCE(SUM(fines_usd), 0), COUNT(*) "
                    f"FROM regulations "
                    f"WHERE status IN ({status_placeholders}) "
                    f"  AND fines_usd IS NOT NULL "
                    f"  AND jurisdiction = :jur"
                ), {"jur": jurisdiction.upper()}).fetchone()
            else:
                total_row = c.execute(text(
                    f"SELECT COALESCE(SUM(fines_usd), 0), COUNT(*) "
                    f"FROM regulations "
                    f"WHERE status IN ({status_placeholders}) "
                    f"  AND fines_usd IS NOT NULL"
                )).fetchone()

            total_usd     = int(total_row[0]) if total_row else 0
            doc_count     = int(total_row[1]) if total_row else 0

            # Разбивка по юрисдикциям (только если нет фильтра)
            by_jurisdiction: dict[str, int] = {}
            if not jurisdiction:
                jur_rows = c.execute(text(
                    f"SELECT jurisdiction, COALESCE(SUM(fines_usd), 0) "
                    f"FROM regulations "
                    f"WHERE status IN ({status_placeholders}) "
                    f"  AND fines_usd IS NOT NULL "
                    f"GROUP BY jurisdiction "
                    f"ORDER BY SUM(fines_usd) DESC"
                )).fetchall()
                by_jurisdiction = {row[0]: int(row[1]) for row in jur_rows}

            # Разбивка по статусам
            status_rows = c.execute(text(
                f"SELECT status, COALESCE(SUM(fines_usd), 0), COUNT(*) "
                f"FROM regulations "
                f"WHERE status IN ({status_placeholders}) "
                f"  AND fines_usd IS NOT NULL "
                f"  {'AND jurisdiction = :jur' if jurisdiction else ''} "
                f"GROUP BY status"
            ), {"jur": jurisdiction.upper()} if jurisdiction else {}).fetchall()

            status_breakdown: dict[str, dict] = {
                row[0]: {"sum_usd": int(row[1]), "count": int(row[2])}
                for row in status_rows
            }

    except Exception as exc:
        log.error("total_risk_exposure: ошибка запроса — %s", exc)
        return {
            "total_usd":        0,
            "total_formatted":  "$0",
            "document_count":   0,
            "by_jurisdiction":  {},
            "status_breakdown": {},
            "updated_at":       datetime.utcnow().isoformat(),
            "error":            str(exc),
        }

    return {
        "total_usd":        total_usd,
        "total_formatted":  f"${total_usd:,}",
        "document_count":   doc_count,
        "by_jurisdiction":  by_jurisdiction,
        "status_breakdown": status_breakdown,
        "updated_at":       datetime.utcnow().isoformat(),
    }


def hours_saved_by_ai(jurisdiction: str | None = None) -> dict:
    """
    KPI "Экономия времени" — часы, сэкономленные AI-обработкой.

    Формула: COUNT(успешно_обработанных) × 1.5
    Успешно обработанные: записи где ai_analysis IS NOT NULL
    и json содержит ключ 'legal' (признак полного анализа),
    исключая статус 'HUMAN_REVIEW'.

    Параметры:
      jurisdiction — фильтр по юрисдикции. None = все.

    Возвращает dict:
      {
        "documents_processed":  int,    количество AI-обработанных документов
        "hours_saved":          float,  итого часов (count × 1.5)
        "hours_formatted":      str,    отформатировано "312.0 ч"
        "by_jurisdiction":      dict,   разбивка {jur: {"docs": int, "hours": float}}
        "formula":              str,    пояснение формулы
        "updated_at":           str,    время запроса UTC ISO
      }
    """
    ensure_analytics_schema()
    engine = _get_engine()

    try:
        with engine.connect() as c:
            if jurisdiction:
                count_row = c.execute(text(
                    "SELECT COUNT(*) FROM regulations "
                    "WHERE ai_analysis IS NOT NULL "
                    "  AND status != 'HUMAN_REVIEW' "
                    "  AND jurisdiction = :jur "
                    "  AND json_valid(ai_analysis) = 1 "
                    "  AND json_extract(ai_analysis, '$.legal') IS NOT NULL"
                ), {"jur": jurisdiction.upper()}).fetchone()
            else:
                count_row = c.execute(text(
                    "SELECT COUNT(*) FROM regulations "
                    "WHERE ai_analysis IS NOT NULL "
                    "  AND status != 'HUMAN_REVIEW' "
                    "  AND json_valid(ai_analysis) = 1 "
                    "  AND json_extract(ai_analysis, '$.legal') IS NOT NULL"
                )).fetchone()

            processed_count = int(count_row[0]) if count_row else 0

            # Разбивка по юрисдикциям
            by_jurisdiction: dict[str, dict] = {}
            if not jurisdiction:
                jur_rows = c.execute(text(
                    "SELECT jurisdiction, COUNT(*) FROM regulations "
                    "WHERE ai_analysis IS NOT NULL "
                    "  AND status != 'HUMAN_REVIEW' "
                    "  AND json_valid(ai_analysis) = 1 "
                    "  AND json_extract(ai_analysis, '$.legal') IS NOT NULL "
                    "GROUP BY jurisdiction "
                    "ORDER BY COUNT(*) DESC"
                )).fetchall()
                by_jurisdiction = {
                    row[0]: {
                        "docs":  int(row[1]),
                        "hours": round(int(row[1]) * _HOURS_PER_DOC, 1),
                    }
                    for row in jur_rows
                }

    except Exception as exc:
        log.error("hours_saved_by_ai: ошибка запроса — %s", exc)
        return {
            "documents_processed": 0,
            "hours_saved":         0.0,
            "hours_formatted":     "0.0 ч",
            "by_jurisdiction":     {},
            "formula":             f"0 × {_HOURS_PER_DOC} = 0.0",
            "updated_at":          datetime.utcnow().isoformat(),
            "error":               str(exc),
        }

    hours_total = round(processed_count * _HOURS_PER_DOC, 1)

    return {
        "documents_processed": processed_count,
        "hours_saved":         hours_total,
        "hours_formatted":     f"{hours_total:,.1f} ч",
        "by_jurisdiction":     by_jurisdiction,
        "formula":             f"{processed_count} × {_HOURS_PER_DOC} = {hours_total}",
        "updated_at":          datetime.utcnow().isoformat(),
    }


def get_dashboard_kpis(jurisdiction: str | None = None) -> dict:
    """
    Агрегированный ответ для всех KPI-карточек дашборда.
    Вызывается при каждом обновлении фильтров в UI.

    Параметры:
      jurisdiction — опциональный фильтр по юрисдикции.

    Возвращает dict со всеми метриками для рендера карточек:
      {
        "risk_exposure":  { total_usd, total_formatted, document_count, ... },
        "hours_saved":    { documents_processed, hours_saved, hours_formatted, ... },
        "generated_at":   str  (UTC ISO)
      }
    """
    return {
        "risk_exposure": total_risk_exposure(jurisdiction=jurisdiction),
        "hours_saved":   hours_saved_by_ai(jurisdiction=jurisdiction),
        "generated_at":  datetime.utcnow().isoformat(),
    }
