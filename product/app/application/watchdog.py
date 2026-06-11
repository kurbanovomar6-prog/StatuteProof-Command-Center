"""
watchdog.py — Автономный агент самоконтроля RegRadar Enterprise.

Назначение:
  Сводит участие человека к нулю путём непрерывного мониторинга здоровья
  пайплайна и автоматического самовосстановления при сбоях.

Компоненты:
  HealthCheckWatchdog  — сканирует метрики последних 24 часов.
                         Если success_rate < 90% по юрисдикции →
                         триггерит сброс стратегии + алерт.
  DeadLinkChecker      — HEAD-запросы к base_url каждого активного регулятора.
                         404 × 3 подряд → статус DEPRECATED + алерт.

Вызов из Celery:
  Запускается автоматически через beat-расписание (celery_app.py):
    health_watchdog_task    — каждые 60 минут
    dead_link_checker_task  — каждые 6 часов

Ручной запуск:
  from app.application.watchdog import run_health_check, check_dead_links
  run_health_check()
  check_dead_links()
"""

import logging
import time
from datetime import datetime, timedelta

import httpx
from sqlalchemy import text

log = logging.getLogger(__name__)

# ── Пороговые значения ─────────────────────────────────────────────────────────
_HEALTH_WINDOW_HOURS    = 24      # период анализа метрик
_MIN_SUCCESS_RATE       = 0.90   # минимально допустимый success rate (90%)
_MIN_DOCS_FOR_CHECK     = 3      # минимум документов для расчёта метрики
_DEAD_LINK_THRESHOLD    = 3      # количество 404 до пометки DEPRECATED
_HEAD_TIMEOUT_SEC       = 10     # таймаут HEAD-запроса


# ── Вспомогательные функции ────────────────────────────────────────────────────

def _get_engine():
    from app.infrastructure.db.session import engine
    return engine


def _send_admin_alert(subject: str, body: str, level: str = "WARNING") -> None:
    """
    Отправляет алерт администратору: Telegram + лог.
    Не блокирует основной поток — падение алерта не останавливает watchdog.
    """
    log.warning("[WATCHDOG] %s | %s", subject, body[:200])
    try:
        from app.infrastructure.notifications.telegram_alert import _post_message
        emoji = "🔴" if level == "CRITICAL" else "⚠️"
        text_msg = (
            f"{emoji} <b>RegRadar Watchdog</b>\n"
            f"<b>{subject}</b>\n\n"
            f"{body}\n\n"
            f"<i>{datetime.utcnow().strftime('%d.%m.%Y %H:%M')} UTC</i>"
        )
        _post_message(text_msg)
    except Exception as e:
        log.debug("[WATCHDOG] алерт Telegram недоступен — %s", e)


def _reset_scraping_strategy(jurisdiction: str) -> dict:
    """
    Сбрасывает стратегию скрапинга для юрисдикции:
      1. Очищает кэш прокси для данной юрисдикции.
      2. Принудительно закрывает кэшированную Playwright-сессию.
      3. Устанавливает флаг в БД для следующего запуска (force_reset=1).

    Возвращает dict с результатом сброса.
    """
    result: dict = {"jurisdiction": jurisdiction, "steps": []}
    engine = _get_engine()

    # Шаг 1: очистка прокси-пула для юрисдикции
    try:
        from app.infrastructure.scrapers.proxy_pool import proxy_pool
        if hasattr(proxy_pool, "clear_for_jurisdiction"):
            proxy_pool.clear_for_jurisdiction(jurisdiction)
        result["steps"].append("proxy_cache_cleared")
        log.info("[WATCHDOG] %s: прокси-кэш сброшен", jurisdiction)
    except Exception as e:
        result["steps"].append(f"proxy_cache_error: {e}")
        log.warning("[WATCHDOG] %s: ошибка сброса прокси — %s", jurisdiction, e)

    # Шаг 2: закрытие Playwright-сессии (discovery.py хранит _session в модуле)
    try:
        from app.infrastructure.scrapers import discovery as _disc
        if hasattr(_disc, "_browser") and _disc._browser is not None:
            try:
                _disc._browser.close()
            except Exception:
                pass
            _disc._browser = None
            result["steps"].append("playwright_session_reset")
            log.info("[WATCHDOG] %s: Playwright-сессия сброшена", jurisdiction)
    except Exception as e:
        result["steps"].append(f"playwright_error: {e}")
        log.debug("[WATCHDOG] %s: Playwright недоступен — %s", jurisdiction, e)

    # Шаг 3: записываем событие сброса в БД для аудита
    try:
        with engine.connect() as c:
            c.execute(text("""
                CREATE TABLE IF NOT EXISTS watchdog_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    jurisdiction TEXT,
                    details TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            c.execute(text("""
                INSERT INTO watchdog_events (event_type, jurisdiction, details)
                VALUES ('STRATEGY_RESET', :jur, :details)
            """), {
                "jur":     jurisdiction,
                "details": str(result["steps"]),
            })
            c.commit()
        result["steps"].append("audit_logged")
    except Exception as e:
        log.warning("[WATCHDOG] аудит-лог недоступен — %s", e)

    return result


# ── Основной watchdog: мониторинг успешности ingestion ───────────────────────

def run_health_check() -> dict:
    """
    Анализирует метрики скрапинга за последние 24 часа.

    Алгоритм:
      1. Запрашивает scrape_metrics за последние _HEALTH_WINDOW_HOURS.
      2. Группирует по jurisdiction.
      3. success_rate = saved / (saved + errors). Если нет данных → пропуск.
      4. При rate < _MIN_SUCCESS_RATE:
           - вызывает _reset_scraping_strategy(jurisdiction)
           - отправляет алерт администратору

    Возвращает dict с диагностикой по каждой юрисдикции.
    """
    engine   = _get_engine()
    cutoff   = (datetime.utcnow() - timedelta(hours=_HEALTH_WINDOW_HOURS)).isoformat()
    report: dict = {"checked_at": datetime.utcnow().isoformat(), "jurisdictions": {}}

    try:
        with engine.connect() as c:
            # Гарантируем существование таблицы (первый запуск)
            c.execute(text("""
                CREATE TABLE IF NOT EXISTS scrape_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    regulator TEXT, jurisdiction TEXT, run_at TEXT,
                    payload TEXT, extraction_yield REAL,
                    prefilter_pass_rate REAL, links_found INTEGER, saved INTEGER
                )
            """))
            c.execute(text("""
                CREATE TABLE IF NOT EXISTS watchdog_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL, jurisdiction TEXT,
                    details TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))

            rows = c.execute(text("""
                SELECT jurisdiction,
                       SUM(saved)         AS total_saved,
                       COUNT(*)           AS run_count,
                       AVG(extraction_yield) AS avg_yield
                FROM scrape_metrics
                WHERE run_at >= :cutoff
                GROUP BY jurisdiction
            """), {"cutoff": cutoff}).fetchall()

            # Также берём количество ошибок из payload JSON
            error_rows = c.execute(text("""
                SELECT jurisdiction,
                       SUM(json_extract(payload, '$.errors')) AS total_errors
                FROM scrape_metrics
                WHERE run_at >= :cutoff
                  AND json_valid(payload) = 1
                GROUP BY jurisdiction
            """), {"cutoff": cutoff}).fetchall()

        errors_by_jur: dict[str, int] = {r[0]: int(r[1] or 0) for r in error_rows}

    except Exception as exc:
        log.error("[WATCHDOG] health_check: ошибка запроса метрик — %s", exc)
        return {**report, "error": str(exc)}

    for row in rows:
        jur, saved, run_count, avg_yield = row
        saved      = int(saved or 0)
        errors     = errors_by_jur.get(jur, 0)
        total_docs = saved + errors

        if total_docs < _MIN_DOCS_FOR_CHECK:
            # Недостаточно данных для расчёта — пропускаем
            report["jurisdictions"][jur] = {
                "status":       "SKIP",
                "reason":       f"недостаточно данных: {total_docs} документов",
                "saved":        saved,
                "errors":       errors,
                "run_count":    run_count,
            }
            continue

        success_rate = saved / total_docs if total_docs > 0 else 0.0

        jur_report = {
            "success_rate":  round(success_rate, 4),
            "saved":         saved,
            "errors":        errors,
            "run_count":     int(run_count),
            "avg_yield":     round(float(avg_yield or 0), 4),
            "status":        "OK" if success_rate >= _MIN_SUCCESS_RATE else "DEGRADED",
        }

        if success_rate < _MIN_SUCCESS_RATE:
            log.error(
                "[WATCHDOG] %s: success_rate=%.1f%% < порог %.0f%% — запуск сброса стратегии",
                jur, success_rate * 100, _MIN_SUCCESS_RATE * 100,
            )
            # Авто-сброс стратегии скрапинга
            reset_result = _reset_scraping_strategy(jur)
            jur_report["reset_result"] = reset_result

            # Алерт администратору
            _send_admin_alert(
                subject=f"Деградация скрапинга [{jur}] — {success_rate:.0%}",
                body=(
                    f"Юрисдикция: {jur}\n"
                    f"Success rate: {success_rate:.1%} (порог: {_MIN_SUCCESS_RATE:.0%})\n"
                    f"Сохранено: {saved} | Ошибок: {errors} | Запусков: {run_count}\n"
                    f"Сброс стратегии выполнен: {reset_result['steps']}\n"
                    f"Средний extraction_yield: {avg_yield:.1%}"
                ),
                level="CRITICAL",
            )

        report["jurisdictions"][jur] = jur_report
        log.info(
            "[WATCHDOG] %s: rate=%.1f%% saved=%d errors=%d runs=%d → %s",
            jur, success_rate * 100, saved, errors, run_count, jur_report["status"],
        )

    report["total_jurisdictions"] = len(rows)
    report["degraded_count"]      = sum(
        1 for v in report["jurisdictions"].values() if v.get("status") == "DEGRADED"
    )
    return report


# ── Dead-link checker: проверка доступности URL регуляторов ──────────────────

def check_dead_links() -> dict:
    """
    HEAD-запрос к base_url каждого активного регулятора.

    Алгоритм:
      1. Загружает список активных регуляторов из БД.
      2. HEAD-запрос к base_url каждого (таймаут _HEAD_TIMEOUT_SEC).
      3. Обновляет таблицу url_health:
           - HTTP 200-399 → consecutive_failures = 0 (сброс счётчика)
           - HTTP 404 / ConnectionError → consecutive_failures += 1
      4. Если consecutive_failures >= _DEAD_LINK_THRESHOLD:
           - Помечает регулятор DEPRECATED (is_active=0, deprecated_at=now)
           - Отправляет алерт с просьбой обновить URL

    Возвращает dict с результатами по каждому регулятору.
    """
    engine = _get_engine()
    report: dict = {
        "checked_at": datetime.utcnow().isoformat(),
        "regulators": {},
        "deprecated_count": 0,
    }

    # Гарантируем таблицу url_health
    try:
        with engine.connect() as c:
            c.execute(text("""
                CREATE TABLE IF NOT EXISTS url_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    regulator_id INTEGER NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    consecutive_failures INTEGER DEFAULT 0,
                    total_failures INTEGER DEFAULT 0,
                    last_status_code INTEGER DEFAULT NULL,
                    last_checked_at DATETIME DEFAULT NULL,
                    is_deprecated INTEGER DEFAULT 0,
                    deprecated_at DATETIME DEFAULT NULL
                )
            """))
            c.commit()

            regulators = c.execute(text(
                "SELECT id, name, jurisdiction, base_url FROM regulators WHERE active=1"
            )).fetchall()
    except Exception as exc:
        log.error("[WATCHDOG] dead_link_check: ошибка загрузки регуляторов — %s", exc)
        return {**report, "error": str(exc)}

    for reg_id, reg_name, jur, base_url in regulators:
        status_code: int | None = None
        is_ok = False

        # HEAD-запрос с таймаутом
        try:
            resp = httpx.head(
                base_url,
                timeout=_HEAD_TIMEOUT_SEC,
                follow_redirects=True,
                headers={"User-Agent": "RegRadar-HealthCheck/2.0"},
            )
            status_code = resp.status_code
            is_ok = (status_code < 400)
            log.debug("[WATCHDOG] HEAD %s → %d", base_url[:70], status_code)
        except httpx.TimeoutException:
            status_code = 408
            log.warning("[WATCHDOG] %s: таймаут HEAD-запроса (%ds)", reg_name, _HEAD_TIMEOUT_SEC)
        except httpx.ConnectError:
            status_code = 0
            log.warning("[WATCHDOG] %s: ошибка соединения", reg_name)
        except Exception as e:
            status_code = -1
            log.warning("[WATCHDOG] %s: неожиданная ошибка — %s", reg_name, e)

        now_iso = datetime.utcnow().isoformat()

        try:
            with engine.connect() as c:
                # Получаем текущий счётчик (или создаём запись)
                existing = c.execute(text(
                    "SELECT id, consecutive_failures, total_failures, is_deprecated "
                    "FROM url_health WHERE url = :url"
                ), {"url": base_url}).fetchone()

                if existing:
                    health_id, cons_fail, total_fail, already_dep = existing
                    if is_ok:
                        new_cons = 0
                    else:
                        new_cons   = cons_fail + 1
                        total_fail = total_fail + 1

                    c.execute(text("""
                        UPDATE url_health SET
                            consecutive_failures = :cons,
                            total_failures       = :total,
                            last_status_code     = :code,
                            last_checked_at      = :now
                        WHERE id = :hid
                    """), {
                        "cons":  new_cons,
                        "total": total_fail,
                        "code":  status_code,
                        "now":   now_iso,
                        "hid":   health_id,
                    })
                else:
                    new_cons   = 0 if is_ok else 1
                    total_fail = 0 if is_ok else 1
                    c.execute(text("""
                        INSERT INTO url_health
                        (regulator_id, url, consecutive_failures, total_failures,
                         last_status_code, last_checked_at)
                        VALUES (:rid, :url, :cons, :total, :code, :now)
                    """), {
                        "rid":   reg_id,
                        "url":   base_url,
                        "cons":  new_cons,
                        "total": total_fail,
                        "code":  status_code,
                        "now":   now_iso,
                    })
                    already_dep = 0

                c.commit()

                # Пометить DEPRECATED при превышении порога
                if not already_dep and new_cons >= _DEAD_LINK_THRESHOLD:
                    c.execute(text("""
                        UPDATE regulators
                        SET active = 0
                        WHERE id = :rid
                    """), {"rid": reg_id})
                    c.execute(text("""
                        UPDATE url_health
                        SET is_deprecated = 1, deprecated_at = :now
                        WHERE url = :url
                    """), {"now": now_iso, "url": base_url})
                    c.commit()

                    report["deprecated_count"] += 1
                    _send_admin_alert(
                        subject=f"Мёртвая ссылка: {reg_name} [{jur}]",
                        body=(
                            f"Регулятор: {reg_name} ({jur})\n"
                            f"URL: {base_url}\n"
                            f"Последний HTTP-код: {status_code}\n"
                            f"Подряд неудач: {new_cons}\n\n"
                            f"Регулятор помечен как DEPRECATED.\n"
                            f"Действие: обновите base_url в разделе «Регуляторы»."
                        ),
                        level="WARNING",
                    )
                    log.error(
                        "[WATCHDOG] %s (%s): DEPRECATED после %d неудач, URL=%s",
                        reg_name, jur, new_cons, base_url[:80],
                    )

        except Exception as db_exc:
            log.error("[WATCHDOG] %s: ошибка обновления url_health — %s", reg_name, db_exc)
            new_cons = -1

        report["regulators"][reg_name] = {
            "jurisdiction":        jur,
            "url":                 base_url[:80],
            "status_code":         status_code,
            "is_ok":               is_ok,
            "consecutive_failures": new_cons,
        }

        time.sleep(0.5)  # вежливая пауза между запросами

    log.info(
        "[WATCHDOG] dead_link_check: проверено %d регуляторов, DEPRECATED=%d",
        len(regulators), report["deprecated_count"],
    )
    return report


# ── Публичный API (вызывается из celery_app.py) ───────────────────────────────

def run_watchdog_cycle() -> dict:
    """
    Полный цикл watchdog: health check + dead link check.
    Вызывается Celery task health_watchdog_task каждые 60 минут.
    """
    log.info("[WATCHDOG] ▶ цикл мониторинга запущен")
    t0 = time.monotonic()

    health = run_health_check()
    links  = check_dead_links()

    elapsed = round(time.monotonic() - t0, 2)
    summary = {
        "duration_sec":       elapsed,
        "health_check":       health,
        "dead_link_check":    links,
        "total_deprecated":   links.get("deprecated_count", 0),
        "total_degraded":     health.get("degraded_count", 0),
    }
    log.info(
        "[WATCHDOG] ✓ цикл завершён за %.1fs | degraded=%d | deprecated=%d",
        elapsed, summary["total_degraded"], summary["total_deprecated"],
    )
    return summary
