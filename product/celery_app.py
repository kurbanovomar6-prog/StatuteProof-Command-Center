"""
celery_app.py — Celery воркер и beat-планировщик для RegRadar Enterprise.

Заменяет APScheduler (scheduler_workers.py) в production-деплое:
  • Celery worker выполняет задачи асинхронно в пуле процессов/потоков
  • Celery beat заменяет APScheduler cron-триггер (interval задач)
  • Redis — брокер очереди и result backend (тот же инстанс что для rate limiting)

Запуск воркера:
  celery -A celery_app worker --loglevel=INFO --concurrency=4

Запуск планировщика (beat):
  celery -A celery_app beat --loglevel=INFO

Запуск воркера + beat в одном процессе (dev/small-scale):
  celery -A celery_app worker --beat --loglevel=INFO --concurrency=2

Ручной запуск задачи:
  from celery_app import scrape_single_regulator_task
  scrape_single_regulator_task.delay("ЦБР", "https://cbr.ru/press/pr/", "RU", ".pdf")
"""

import asyncio
import logging
import os
import threading

from celery import Celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from kombu import Queue

log = get_task_logger(__name__)

# ── Async bridge ──────────────────────────────────────────────────────────────
# The current ORM stack (SQLAlchemy sync + SessionLocal) is 100% synchronous.
# Celery prefork workers are OS processes — blocking sync IO is correct here.
# NO bridge is needed for the current codebase.
#
# This utility exists for future async additions (async httpx, AsyncSession,
# async notification clients, etc.).  Usage inside any Celery task:
#
#   result = _run_async(some_async_coroutine(arg1, arg2))
#
# Why thread-local loop instead of asyncio.run():
#   asyncio.run() creates + destroys a loop on every call.  For tasks that run
#   dozens of times per minute this wastes OS resources.  A thread-local loop
#   is created once per worker OS-thread and reused for the worker's lifetime,
#   keeping async connection-pool lifetimes aligned with worker lifetimes.

_tl = threading.local()


def _run_async(coro):
    """Run an async coroutine from synchronous Celery context."""
    if not hasattr(_tl, "loop") or _tl.loop.is_closed():
        _tl.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_tl.loop)
    return _tl.loop.run_until_complete(coro)

# ── Конфигурация брокера из .env ──────────────────────────────────────────────
_REDIS_URL      = os.getenv("REDIS_URL", "redis://localhost:6379/0")
_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", _REDIS_URL)

# ── Инициализация приложения Celery ───────────────────────────────────────────
celery_app = Celery(
    "regrada",
    broker=_REDIS_URL,
    backend=_RESULT_BACKEND,
)

celery_app.conf.update(
    # Сериализация задач и результатов в JSON (UTF-8, поддержка Cyrillic)
    task_serializer          = "json",
    result_serializer        = "json",
    accept_content           = ["json"],
    # Часовой пояс
    timezone                 = "UTC",
    enable_utc               = True,
    # Время хранения результатов задач — 24 ч
    result_expires           = 86_400,
    # Acks задача только после успешного выполнения (не сразу при получении)
    task_acks_late           = True,
    # Повторная доставка при падении воркера в процессе выполнения
    task_reject_on_worker_lost = True,
    # Максимальное время выполнения одной задачи — 20 минут
    task_time_limit          = 1_200,
    task_soft_time_limit     = 1_080,
    # Маршрутизация задач по очередям
    task_default_queue       = "default",
    task_queues              = [
        Queue("default",  routing_key="default"),
        Queue("scraping", routing_key="scraping"),
        Queue("reports",  routing_key="reports"),
    ],
    task_routes              = {
        "celery_app.scrape_single_regulator_task":  {"queue": "scraping"},
        "celery_app.scrape_all_regulators_task":    {"queue": "scraping"},
        "celery_app.universal_scrape_url_task":     {"queue": "scraping"},
        "celery_app.generate_reports_task":         {"queue": "reports"},
        "celery_app.analyze_delta_task":            {"queue": "reports"},
        "celery_app.send_scheduled_alerts_task":    {"queue": "reports"},
    },
    # Beat-расписание (replaces APScheduler)
    beat_schedule            = {
        # ── Скрапинг ──────────────────────────────────────────────────────────
        # Полное сканирование всех регуляторов — каждые 6 часов
        "full-scrape-every-6h": {
            "task":     "celery_app.scrape_all_regulators_task",
            "schedule": crontab(minute=0, hour="*/6"),
            "options":  {"queue": "scraping"},
        },
        # ── Отчёты ────────────────────────────────────────────────────────────
        # Генерация ежедневного исполнительного отчёта — в 07:00 UTC
        "daily-executive-report": {
            "task":     "celery_app.generate_reports_task",
            "schedule": crontab(minute=0, hour=7),
            "options":  {"queue": "reports"},
        },
        # Email дайджест — каждое утро в 08:00 UTC
        "daily-email-digest": {
            "task":     "celery_app.send_email_digest_task",
            "schedule": crontab(minute=0, hour=8),
            "options":  {"queue": "reports"},
        },
        # Telegram ежедневный сводный дайджест — в 08:05 UTC
        "daily-telegram-digest": {
            "task":     "celery_app.send_telegram_digest_task",
            "schedule": crontab(minute=5, hour=8),
            "options":  {"queue": "reports"},
        },
        # ── Автономный мониторинг (Watchdog) ──────────────────────────────────
        # Health Check Watchdog — каждые 60 минут
        "health-watchdog-hourly": {
            "task":     "celery_app.health_watchdog_task",
            "schedule": crontab(minute=0),   # каждый час в :00
            "options":  {"queue": "default"},
        },
        # Проверка мёртвых ссылок — каждые 6 часов (смещена на :30)
        "dead-link-checker-6h": {
            "task":     "celery_app.dead_link_checker_task",
            "schedule": crontab(minute=30, hour="*/6"),
            "options":  {"queue": "default"},
        },
        # YTD Performance снэпшот — ежедневно в 01:00 UTC
        "ytd-snapshot-daily": {
            "task":     "celery_app.ytd_snapshot_task",
            "schedule": crontab(minute=0, hour=1),
            "options":  {"queue": "reports"},
        },
        # Персонализированные Telegram-алерты по подпискам — в 09:00 UTC
        "daily-alerts-09h": {
            "task":     "celery_app.send_scheduled_alerts_task",
            "schedule": crontab(minute=0, hour=9),
            "options":  {"queue": "reports"},
        },
    },
    # Подавление предупреждения о хранении статусов в Redis в prod
    worker_hijack_root_logger = False,
)


# ── Задача: скрапинг одного регулятора ────────────────────────────────────────

@celery_app.task(
    bind=True,
    name="celery_app.scrape_single_regulator_task",
    max_retries=3,
    default_retry_delay=300,  # 5 минут между авто-повторами
    acks_late=True,
)
def scrape_single_regulator_task(
    self,
    name: str,
    base_url: str,
    jurisdiction: str,
    link_pattern: str = ".pdf",
    strategy: str = "STATIC",
    proxy: str | None = None,
) -> dict:
    """
    Celery задача: скрапинг одного регулятора.

    Делегирует в `app.application.pipeline.run_pipeline_for_regulator()`
    (production-версия с AI-обработкой, дедупликацией, snapshotом).

    При retriable-ошибке (сеть, таймаут) — авто-повтор с 5-мин задержкой.
    """
    log.info(
        "scrape_single_regulator_task: старт %s (%s) strategy=%s",
        name, jurisdiction, strategy,
    )
    try:
        from app.application.pipeline import run_pipeline_for_regulator
        result = run_pipeline_for_regulator(
            name=name,
            base_url=base_url,
            jurisdiction=jurisdiction,
            link_pattern=link_pattern,
            strategy=strategy,
            proxy=proxy,
        )
        log.info(
            "scrape_single_regulator_task: завершён %s → %s",
            name, result,
        )
        return result
    except (OSError, ConnectionError, TimeoutError) as exc:
        # Сетевые ошибки — повторяем задачу через Celery retry
        log.warning(
            "scrape_single_regulator_task: сетевая ошибка %s (%s) — повтор #%d: %s",
            name, jurisdiction, self.request.retries + 1, exc,
        )
        raise self.retry(exc=exc)
    except Exception as exc:
        # Прочие ошибки — логируем, не повторяем (данные/конфиг-проблема)
        log.error(
            "scrape_single_regulator_task: критическая ошибка %s — %s",
            name, str(exc)[:200],
        )
        return {"status": "error", "regulator": name, "error": str(exc)[:200]}


# ── Задача: скрапинг всех активных регуляторов ────────────────────────────────

@celery_app.task(
    name="celery_app.scrape_all_regulators_task",
    acks_late=True,
)
def scrape_all_regulators_task() -> dict:
    """
    Celery задача: запускает отдельные подзадачи для каждого активного регулятора.

    Читает список регуляторов из БД через ORM.
    Каждый регулятор запускается как независимая Celery задача — параллельный обход.
    """
    log.info("scrape_all_regulators_task: загрузка активных регуляторов из БД")
    dispatched: list[dict] = []

    try:
        from app.infrastructure.db.session import SessionLocal
        from app.infrastructure.db.models import Regulator
        from sqlalchemy import select

        with SessionLocal() as session:
            regulators = session.execute(
                select(Regulator).where(Regulator.is_active == True)  # noqa: E712
            ).scalars().all()

        if not regulators:
            log.warning("scrape_all_regulators_task: нет активных регуляторов в БД")
            return {"dispatched": 0}

        for reg in regulators:
            task = scrape_single_regulator_task.apply_async(
                kwargs={
                    "name":         reg.name,
                    "base_url":     reg.base_url,
                    "jurisdiction": reg.jurisdiction,
                    "link_pattern": reg.link_pattern,
                    "strategy":     getattr(reg, "strategy", "STATIC"),
                    "proxy":        getattr(reg, "proxy_url", None),
                },
                queue="scraping",
            )
            dispatched.append({"name": reg.name, "task_id": task.id})
            log.info(
                "scrape_all_regulators_task: dispatched %s → task_id=%s",
                reg.name, task.id,
            )

    except Exception as exc:
        log.error("scrape_all_regulators_task: ошибка загрузки регуляторов — %s", exc)
        return {"dispatched": 0, "error": str(exc)[:200]}

    log.info(
        "scrape_all_regulators_task: отправлено %d задач скрапинга",
        len(dispatched),
    )
    return {"dispatched": len(dispatched), "tasks": dispatched}


# ── Задача: генерация исполнительных отчётов ──────────────────────────────────

@celery_app.task(
    name="celery_app.generate_reports_task",
    acks_late=True,
)
def generate_reports_task(days: int = 30) -> dict:
    """
    Celery задача: генерирует исполнительные Markdown отчёты для CEO/CFO/CCO.
    Запускается daily beat-расписанием в 07:00 UTC.
    Сохраняет файлы в reports/{timestamp}_{jur}.md.
    """
    log.info("generate_reports_task: генерация отчётов за %d дней", days)
    try:
        from app.infrastructure.reports.executive_report import (
            generate_all_jurisdictions_reports,
        )
        reports = generate_all_jurisdictions_reports(days=days)
        log.info(
            "generate_reports_task: сформировано %d отчётов (ALL + по юрисдикциям)",
            len(reports),
        )
        return {
            "status": "ok",
            "reports_count": len(reports),
            "jurisdictions": list(reports.keys()),
        }
    except Exception as exc:
        log.error("generate_reports_task: ошибка генерации отчётов — %s", exc)
        return {"status": "error", "error": str(exc)[:200]}


# ── Сигналы задач: логирование жизненного цикла ───────────────────────────────

@celery_app.task(name="celery_app.send_email_digest_task", acks_late=True)
def send_email_digest_task(days: int = 1) -> dict:
    """Celery задача: отправляет HTML email-дайджест за период."""
    log.info("send_email_digest_task: дайджест за %d дней", days)
    try:
        from app.infrastructure.db.session import engine
        from sqlalchemy import text
        from datetime import timedelta, datetime as _dt
        from app.infrastructure.notifications.email_digest import send_digest

        cutoff = (_dt.utcnow() - timedelta(days=days)).isoformat()
        with engine.connect() as c:
            rows = c.execute(text(
                "SELECT id, title, jurisdiction, critical_level, "
                "effective_date, summary, source_url "
                "FROM regulations WHERE extracted_at >= :c ORDER BY extracted_at DESC"
            ), {"c": cutoff}).fetchall()

        regs = [
            {
                "id":             r[0], "title":          r[1],
                "jurisdiction":   r[2], "critical_level": r[3],
                "effective_date": r[4], "summary":        r[5],
                "source_url":     r[6],
            }
            for r in rows
        ]

        ok = send_digest(regs, days=days)
        return {"status": "ok" if ok else "skipped", "count": len(regs)}
    except Exception as exc:
        log.error("send_email_digest_task: ошибка — %s", exc)
        return {"status": "error", "error": str(exc)[:200]}


@celery_app.task(name="celery_app.send_telegram_digest_task", acks_late=True)
def send_telegram_digest_task(days: int = 1) -> dict:
    """Celery задача: отправляет Telegram дайджест за период."""
    log.info("send_telegram_digest_task: дайджест за %d дней", days)
    try:
        from app.infrastructure.db.session import engine
        from sqlalchemy import text
        from datetime import timedelta, datetime as _dt
        from app.infrastructure.notifications.telegram_alert import send_daily_digest

        cutoff = (_dt.utcnow() - timedelta(days=days)).isoformat()
        with engine.connect() as c:
            rows = c.execute(text(
                "SELECT id, title, jurisdiction, critical_level, effective_date "
                "FROM regulations WHERE extracted_at >= :c ORDER BY extracted_at DESC"
            ), {"c": cutoff}).fetchall()

        regs = [
            {"id": r[0], "title": r[1], "jurisdiction": r[2],
             "critical_level": r[3], "effective_date": r[4]}
            for r in rows
        ]

        ok = send_daily_digest(regs, days=days)
        return {"status": "ok" if ok else "skipped", "count": len(regs)}
    except Exception as exc:
        log.error("send_telegram_digest_task: ошибка — %s", exc)
        return {"status": "error", "error": str(exc)[:200]}


@celery_app.task(bind=True, name="celery_app.debug_ping")
def debug_ping(self) -> str:
    """Задача для проверки работоспособности воркера (health check)."""
    log.info("debug_ping: воркер отвечает, task_id=%s", self.request.id)
    return "pong"


# ── Автономный мониторинг (Watchdog) ──────────────────────────────────────────

@celery_app.task(
    name="celery_app.health_watchdog_task",
    acks_late=True,
    time_limit=300,      # watchdog не должен висеть дольше 5 минут
    soft_time_limit=240,
)
def health_watchdog_task() -> dict:
    """
    Celery задача: полный цикл watchdog — health check + dead link check.
    Запускается beat-расписанием каждые 60 минут.

    Алгоритм:
      1. Анализирует scrape_metrics за последние 24 часа по каждой юрисдикции.
      2. При success_rate < 90% → сброс стратегии скрапинга + алерт.
      3. HEAD-запросы к base_url всех активных регуляторов.
      4. При 404 × 3 → пометка DEPRECATED + алерт администратору.
    """
    log.info("health_watchdog_task: старт цикла мониторинга")
    try:
        from app.application.watchdog import run_watchdog_cycle
        result = run_watchdog_cycle()
        log.info(
            "health_watchdog_task: завершён | degraded=%d | deprecated=%d",
            result.get("total_degraded", 0), result.get("total_deprecated", 0),
        )
        return result
    except Exception as exc:
        log.error("health_watchdog_task: критическая ошибка — %s", exc)
        return {"status": "error", "error": str(exc)[:300]}


@celery_app.task(
    name="celery_app.dead_link_checker_task",
    acks_late=True,
    time_limit=600,      # до 10 минут на полный обход всех регуляторов
    soft_time_limit=540,
)
def dead_link_checker_task() -> dict:
    """
    Celery задача: изолированная проверка мёртвых ссылок.
    Запускается каждые 6 часов (смещена на :30 чтобы не совпадать со скрапингом).
    """
    log.info("dead_link_checker_task: старт проверки доступности регуляторов")
    try:
        from app.application.watchdog import check_dead_links
        result = check_dead_links()
        log.info(
            "dead_link_checker_task: проверено=%d | deprecated=%d",
            len(result.get("regulators", {})), result.get("deprecated_count", 0),
        )
        return result
    except Exception as exc:
        log.error("dead_link_checker_task: ошибка — %s", exc)
        return {"status": "error", "error": str(exc)[:300]}


@celery_app.task(
    name="celery_app.ytd_snapshot_task",
    acks_late=True,
    time_limit=180,
)
def ytd_snapshot_task() -> dict:
    """
    Celery задача: создаёт/обновляет YTD-снэпшот текущего месяца.
    Запускается ежедневно в 01:00 UTC.

    Сохраняет агрегированные метрики в ytd_snapshots:
      - суммарные предотвращённые штрафы
      - среднее время обнаружения НПА
      - стоимость AI-обработки на документ
    """
    log.info("ytd_snapshot_task: обновление YTD-метрик")
    try:
        from app.infrastructure.analytics.ytd_metrics import save_ytd_snapshot
        results = []
        # Снэпшот для всех юрисдикций суммарно
        results.append(save_ytd_snapshot(jurisdiction=None))
        # Снэпшот по каждой юрисдикции
        for jur in ("RU", "KZ", "AZ", "BY", "UZ"):
            results.append(save_ytd_snapshot(jurisdiction=jur))
        log.info("ytd_snapshot_task: сохранено %d снэпшотов", len(results))
        return {"status": "ok", "snapshots": len(results)}
    except Exception as exc:
        log.error("ytd_snapshot_task: ошибка — %s", exc)
        return {"status": "error", "error": str(exc)[:300]}


# ── Хуки жизненного цикла ─────────────────────────────────────────────────────

from celery.signals import (  # noqa: E402
    worker_ready,
    worker_shutdown,
    task_failure,
)


@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    log.info(
        "RegRadar Celery worker запущен | broker=%s",
        _REDIS_URL.split("@")[-1] if "@" in _REDIS_URL else _REDIS_URL,
    )


@worker_shutdown.connect
def on_worker_shutdown(sender, **kwargs):
    log.info("RegRadar Celery worker остановлен")


@task_failure.connect
def on_task_failure(sender, task_id, exception, traceback, einfo, **kwargs):
    log.error(
        "TASK FAILURE | task=%s | id=%s | exc=%s",
        sender.name, task_id, str(exception)[:120],
    )
    # Опциональная интеграция с Sentry
    _sentry_dsn = os.getenv("SENTRY_DSN", "")
    if _sentry_dsn:
        try:
            import sentry_sdk
            sentry_sdk.capture_exception(exception)
        except Exception:
            pass


# ── Задача: Universal AI-Driven Scraper ───────────────────────────────────────

@celery_app.task(
    bind=True,
    name="celery_app.universal_scrape_url_task",
    max_retries=2,
    default_retry_delay=120,
    acks_late=True,
    time_limit=600,
    soft_time_limit=540,
)
def universal_scrape_url_task(
    self,
    url: str,
    jurisdiction: str = "",
    max_pages: int = 5,
    proxy: str | None = None,
) -> dict:
    """
    Celery задача: Universal AI-Driven Scraper для произвольного URL.

    Не требует CSS-селекторов — LLM семантически находит НПА на любой странице.
    Результаты сохраняются через RegulationRepository.upsert_raw().

    Пример запуска:
        from celery_app import universal_scrape_url_task
        universal_scrape_url_task.delay("https://cbr.ru/press/pr/", "RU")
    """
    log.info(
        "universal_scrape_url_task: старт %s jurisdiction=%s max_pages=%d",
        url[:80], jurisdiction, max_pages,
    )
    try:
        from services.universal_scraper import UniversalScraper
        scraper = UniversalScraper(proxy=proxy)
        saved = scraper.scrape_url(url=url, jurisdiction=jurisdiction, max_pages=max_pages)
        log.info("universal_scrape_url_task: завершён %s → сохранено %d", url[:60], saved)
        return {"status": "ok", "url": url, "saved": saved}
    except (OSError, ConnectionError, TimeoutError) as exc:
        log.warning(
            "universal_scrape_url_task: сетевая ошибка %s (повтор #%d) — %s",
            url[:60], self.request.retries + 1, exc,
        )
        raise self.retry(exc=exc)
    except Exception as exc:
        log.error("universal_scrape_url_task: ошибка %s — %s", url[:60], str(exc)[:200])
        return {"status": "error", "url": url, "error": str(exc)[:200]}


# ── Задача: LLM-анализ дельты версий ─────────────────────────────────────────

@celery_app.task(
    name="celery_app.analyze_delta_task",
    acks_late=True,
    time_limit=120,
    soft_time_limit=100,
)
def analyze_delta_task(version_id: int, old_summary: str) -> dict:
    """
    LLM-анализ изменений между двумя версиями регуляторного документа.
    Запускается из _persist() при обнаружении новой версии.
    Результат (DeltaAnalysis) сохраняется в regulation_versions.delta_json.
    """
    log.info("analyze_delta_task: version_id=%d", version_id)
    try:
        from app.infrastructure.db.repository import RegulationRepository
        from services.delta_analyzer import analyze_delta

        repo    = RegulationRepository()
        version = repo.get_version_by_id(version_id)
        if not version:
            log.warning("analyze_delta_task: version_id=%d не найден", version_id)
            return {"status": "not_found"}

        delta = analyze_delta(old_summary, version["summary"])
        if not delta:
            return {"status": "no_delta"}

        repo.update_version_delta(version_id, delta)
        log.info(
            "analyze_delta_task: v%d impact=%s changes=%d",
            version_id, delta.impact_level, len(delta.critical_changes),
        )
        return {
            "status":       "ok",
            "version_id":   version_id,
            "impact_level": delta.impact_level,
            "changes":      len(delta.critical_changes),
        }
    except Exception as exc:
        log.error("analyze_delta_task: version_id=%d — %s", version_id, str(exc)[:200])
        return {"status": "error", "error": str(exc)[:200]}


# ── Задача: рассылка персонализированных Telegram-алертов ─────────────────────

@celery_app.task(
    name="celery_app.send_scheduled_alerts_task",
    acks_late=True,
    time_limit=300,
    soft_time_limit=270,
)
def send_scheduled_alerts_task() -> dict:
    """
    Формирует Telegram-алерты для каждого активного подписчика.
    Фильтрует регуляторные акты по юрисдикции и минимальному уровню риска.
    Подписчики с frequency="instant" получают индивидуальные delta-алерты;
    остальные — сводный дайджест.
    """
    from datetime import datetime as _dt, timedelta
    log.info("send_scheduled_alerts_task: старт")
    try:
        import os
        from app.infrastructure.db.repository import RegulationRepository, SubscriptionRepository
        from services.delta_analyzer import (
            DeltaAnalysis, _RISK_ORDER,
            send_telegram, format_digest, format_delta_alert,
        )

        tg_token  = os.getenv("TELEGRAM_BOT_TOKEN", "")
        dashboard = os.getenv("REGRADA_DASHBOARD_URL", "")

        reg_repo      = RegulationRepository()
        sub_repo      = SubscriptionRepository()
        since         = _dt.utcnow() - timedelta(hours=25)
        recent        = reg_repo.get_recent_with_versions(since)
        subscriptions = sub_repo.list_active()

        if not subscriptions:
            log.info("send_scheduled_alerts_task: нет активных подписчиков")
            return {"status": "ok", "sent": 0}

        sent_total = 0
        for sub in subscriptions:
            jur_filter = [j.strip() for j in (sub.jurisdictions or "").split(",") if j.strip()]
            min_risk   = _RISK_ORDER.get(sub.min_risk_level, 0)

            matching = [
                r for r in recent
                if (not jur_filter or r.get("jurisdiction") in jur_filter)
                and _RISK_ORDER.get(r.get("impact_level", "LOW"), 0) >= min_risk
            ]
            if not matching:
                continue

            if sub.frequency == "instant":
                for reg in matching[:3]:
                    delta_raw = reg.get("delta_json")
                    if not delta_raw:
                        continue
                    try:
                        delta = DeltaAnalysis.model_validate_json(delta_raw)
                        msg   = format_delta_alert(reg, delta, dashboard)
                        if send_telegram(tg_token, sub.chat_id, msg):
                            sent_total += 1
                    except Exception:
                        pass
            else:
                msg = format_digest(matching, dashboard_url=dashboard)
                if send_telegram(tg_token, sub.chat_id, msg):
                    sent_total += 1

        sub_repo.update_last_notified([s.chat_id for s in subscriptions])
        log.info("send_scheduled_alerts_task: отправлено %d алертов", sent_total)
        return {"status": "ok", "sent": sent_total, "subscribers": len(subscriptions)}
    except Exception as exc:
        log.error("send_scheduled_alerts_task: ошибка — %s", str(exc)[:300])
        return {"status": "error", "error": str(exc)[:300]}


# ── Точка входа для запуска воркера напрямую ──────────────────────────────────
if __name__ == "__main__":
    celery_app.start()
