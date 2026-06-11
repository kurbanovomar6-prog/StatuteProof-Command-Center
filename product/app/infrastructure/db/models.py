"""
models.py — ORM-модели RegRadar Enterprise.

Таблицы:
  regulations          — регуляторные акты (ядро системы)
  regulators           — источники/регуляторы
  scrape_jobs          — задания на скрапинг
  url_health           — мониторинг доступности URL регуляторов
  webhook_endpoints    — зарегистрированные webhook-получатели (Developer API)
  ytd_snapshots        — агрегированные YTD-метрики (ежемесячные снэпшоты)
  regulation_versions  — история версий документов (delta analysis)
  alert_subscriptions  — Telegram-подписчики (chat_id, юрисдикции, частота)
"""

from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String, Text, event, text
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# ── Регуляторы (источники данных) ──────────────────────────────────────────────

class Regulator(Base):
    __tablename__ = "regulators"
    id:           Mapped[int]      = mapped_column(Integer, primary_key=True)
    name:         Mapped[str]      = mapped_column(String(200), nullable=False)
    jurisdiction: Mapped[str]      = mapped_column(String(5), nullable=False)
    base_url:     Mapped[str]      = mapped_column(Text, nullable=False)
    strategy:     Mapped[str]      = mapped_column(String(20), default="STATIC")
    link_pattern: Mapped[str]      = mapped_column(String(50), default=".pdf")
    active:       Mapped[bool]     = mapped_column(Boolean, default=True)
    created_at:   Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ── Регуляторные акты ──────────────────────────────────────────────────────────

class RegulationRecord(Base):
    __tablename__ = "regulations"
    id:               Mapped[int]      = mapped_column(Integer, primary_key=True)
    title:            Mapped[str]      = mapped_column(Text, nullable=False)
    jurisdiction:     Mapped[str]      = mapped_column(String(5), nullable=False)
    publication_date: Mapped[str]      = mapped_column(String(10))
    effective_date:   Mapped[str]      = mapped_column(String(10))
    summary:          Mapped[str]      = mapped_column(Text)
    industries:       Mapped[str]      = mapped_column(Text, default="")
    critical_level:   Mapped[str]      = mapped_column(String(20), default="LOW")
    source_url:       Mapped[str]      = mapped_column(Text)
    confidence:       Mapped[float]    = mapped_column(Float, default=0.5)
    status:           Mapped[str]      = mapped_column(String(20), default="PROCESSING")
    extracted_at:     Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    url_hash:         Mapped[str]      = mapped_column(String(64), unique=True, index=True)
    # AI-обогащение
    ai_analysis:         Mapped[str | None] = mapped_column(Text, default=None)
    source_type:         Mapped[str]        = mapped_column(String(20), default="WEB")
    urgency_score:       Mapped[int | None] = mapped_column(Integer, default=None)
    action_plan:         Mapped[str | None] = mapped_column(Text, default=None)
    # Аналитика
    fines_usd:              Mapped[int | None]   = mapped_column(Integer, default=None)
    time_to_discovery_sec:  Mapped[int | None]   = mapped_column(Integer, default=None)
    compute_cost_usd:       Mapped[float | None] = mapped_column(Float, default=None)


# ── Мониторинг доступности URL регуляторов ────────────────────────────────────

class UrlHealth(Base):
    """
    Трекер HTTP-здоровья каждого URL регулятора.
    При consecutive_failures >= 3 → регулятор помечается DEPRECATED.
    """
    __tablename__ = "url_health"
    id:                   Mapped[int]      = mapped_column(Integer, primary_key=True)
    regulator_id:         Mapped[int]      = mapped_column(Integer, nullable=False)
    url:                  Mapped[str]      = mapped_column(Text, nullable=False, unique=True)
    consecutive_failures: Mapped[int]      = mapped_column(Integer, default=0)
    total_failures:       Mapped[int]      = mapped_column(Integer, default=0)
    last_status_code:     Mapped[int | None] = mapped_column(Integer, default=None)
    last_checked_at:      Mapped[datetime | None] = mapped_column(DateTime, default=None)
    is_deprecated:        Mapped[bool]     = mapped_column(Boolean, default=False)
    deprecated_at:        Mapped[datetime | None] = mapped_column(DateTime, default=None)


# ── Webhook-получатели (Developer API) ────────────────────────────────────────

class WebhookEndpoint(Base):
    """
    Зарегистрированные webhook endpoint-ы для push-уведомлений.
    Поддерживаемые платформы: generic, slack, teams, jira.
    """
    __tablename__ = "webhook_endpoints"
    id:              Mapped[int]      = mapped_column(Integer, primary_key=True)
    url:             Mapped[str]      = mapped_column(Text, nullable=False)
    description:     Mapped[str]      = mapped_column(String(300), default="")
    platform:        Mapped[str]      = mapped_column(String(20), default="generic")
    events:          Mapped[str]      = mapped_column(Text, default='["regulation.detected"]')
    secret:          Mapped[str]      = mapped_column(String(200), default="")
    is_active:       Mapped[bool]     = mapped_column(Boolean, default=True)
    created_at:      Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    success_count:   Mapped[int]      = mapped_column(Integer, default=0)
    failure_count:   Mapped[int]      = mapped_column(Integer, default=0)


# ── История версий регуляторных актов ────────────────────────────────────────

class RegulationVersion(Base):
    """
    Каждая версия отслеживается при изменении summary.
    delta_json — сериализованный DeltaAnalysis (LLM-анализ изменений).
    impact_level дублирует delta.impact_level для быстрой фильтрации без десериализации.
    """
    __tablename__ = "regulation_versions"
    id:             Mapped[int]         = mapped_column(Integer, primary_key=True)
    regulation_id:  Mapped[int]         = mapped_column(Integer, ForeignKey("regulations.id"), nullable=False, index=True)
    version_number: Mapped[int]         = mapped_column(Integer, nullable=False, default=1)
    summary_hash:   Mapped[str]         = mapped_column(String(64), nullable=False)
    summary:        Mapped[str]         = mapped_column(Text)
    delta_json:     Mapped[str | None]  = mapped_column(Text, default=None)
    impact_level:   Mapped[str | None]  = mapped_column(String(20), default=None)
    created_at:     Mapped[datetime]    = mapped_column(DateTime, default=datetime.utcnow)


# ── Telegram-подписчики (AlertSubscription) ───────────────────────────────────

class AlertSubscription(Base):
    """
    Хранит chat_id Telegram-клиентов и их настройки фильтрации.
    jurisdictions — строка с разделителем: "RU,KZ,AZ".
    frequency     — "daily" / "weekly" / "instant".
    min_risk_level — минимальный уровень важности для отправки: LOW/MEDIUM/HIGH/CRITICAL.
    """
    __tablename__ = "alert_subscriptions"
    id:               Mapped[int]           = mapped_column(Integer, primary_key=True)
    chat_id:          Mapped[str]           = mapped_column(String(50), nullable=False, unique=True)
    jurisdictions:    Mapped[str]           = mapped_column(Text, default="")
    frequency:        Mapped[str]           = mapped_column(String(20), default="daily")
    min_risk_level:   Mapped[str]           = mapped_column(String(20), default="LOW")
    is_active:        Mapped[bool]          = mapped_column(Boolean, default=True)
    created_at:       Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow)
    last_notified_at: Mapped[datetime|None] = mapped_column(DateTime, default=None)


# ── YTD-снэпшоты (ежемесячная агрегация) ─────────────────────────────────────

class YtdSnapshot(Base):
    """
    Ежемесячные агрегированные метрики для YTD Performance модуля.
    Создаются Celery задачей ytd_snapshot_task в 01:00 UTC ежедневно.
    """
    __tablename__ = "ytd_snapshots"
    id:                         Mapped[int]    = mapped_column(Integer, primary_key=True)
    year:                       Mapped[int]    = mapped_column(Integer, nullable=False)
    month:                      Mapped[int]    = mapped_column(Integer, nullable=False)
    jurisdiction:               Mapped[str | None] = mapped_column(String(5), default=None)
    total_processed:            Mapped[int]    = mapped_column(Integer, default=0)
    critical_count:             Mapped[int]    = mapped_column(Integer, default=0)
    high_count:                 Mapped[int]    = mapped_column(Integer, default=0)
    fines_prevented_usd:        Mapped[int]    = mapped_column(Integer, default=0)
    avg_time_to_discovery_sec:  Mapped[float]  = mapped_column(Float, default=0.0)
    avg_compute_cost_usd:       Mapped[float]  = mapped_column(Float, default=0.0)
    total_compute_cost_usd:     Mapped[float]  = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ── Конфигурация SQLite pragma ─────────────────────────────────────────────────

def configure_engine(engine) -> None:
    @event.listens_for(engine, "connect")
    def _on_connect(conn, _):
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA cache_size=-32000")   # 32 МБ page cache
        conn.execute("PRAGMA temp_store=MEMORY")


# ── Идемпотентная миграция новых колонок ──────────────────────────────────────

def ensure_schema_migrations(engine) -> None:
    """
    Добавляет новые колонки в существующие таблицы (идемпотентно).
    Безопасно вызывать при каждом старте — ALTER TABLE IF NOT EXISTS.
    """
    _new_cols: list[tuple[str, str, str]] = [
        # (таблица, колонка, SQL-определение)
        ("regulations", "ai_analysis",            "TEXT DEFAULT NULL"),
        ("regulations", "source_type",            "VARCHAR(20) DEFAULT 'WEB'"),
        ("regulations", "urgency_score",          "INTEGER DEFAULT NULL"),
        ("regulations", "action_plan",            "TEXT DEFAULT NULL"),
        ("regulations", "fines_usd",              "INTEGER DEFAULT NULL"),
        ("regulations", "time_to_discovery_sec",  "INTEGER DEFAULT NULL"),
        ("regulations", "compute_cost_usd",       "REAL DEFAULT NULL"),
        ("regulators",  "is_active",              "INTEGER DEFAULT 1"),
        ("regulators",  "deprecated_at",          "DATETIME DEFAULT NULL"),
        ("regulators",  "deprecation_reason",     "TEXT DEFAULT NULL"),
    ]
    _new_tables: list[str] = [
        """CREATE TABLE IF NOT EXISTS url_health (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            regulator_id INTEGER NOT NULL,
            url TEXT NOT NULL UNIQUE,
            consecutive_failures INTEGER DEFAULT 0,
            total_failures INTEGER DEFAULT 0,
            last_status_code INTEGER DEFAULT NULL,
            last_checked_at DATETIME DEFAULT NULL,
            is_deprecated INTEGER DEFAULT 0,
            deprecated_at DATETIME DEFAULT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS webhook_endpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            description TEXT DEFAULT '',
            platform VARCHAR(20) DEFAULT 'generic',
            events TEXT DEFAULT '["regulation.detected"]',
            secret TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_triggered_at DATETIME DEFAULT NULL,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS ytd_snapshots (
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE INDEX IF NOT EXISTS idx_ytd_year_month
           ON ytd_snapshots (year, month, jurisdiction)""",
        """CREATE INDEX IF NOT EXISTS idx_regulations_extracted
           ON regulations (extracted_at, jurisdiction, critical_level)""",
        """CREATE INDEX IF NOT EXISTS idx_regulations_fines
           ON regulations (fines_usd, status) WHERE fines_usd IS NOT NULL""",
        """CREATE TABLE IF NOT EXISTS regulation_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            regulation_id INTEGER NOT NULL REFERENCES regulations(id),
            version_number INTEGER NOT NULL DEFAULT 1,
            summary_hash VARCHAR(64) NOT NULL,
            summary TEXT,
            delta_json TEXT DEFAULT NULL,
            impact_level VARCHAR(20) DEFAULT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE INDEX IF NOT EXISTS idx_reg_versions_regulation_id
           ON regulation_versions (regulation_id, version_number)""",
        """CREATE TABLE IF NOT EXISTS alert_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id VARCHAR(50) NOT NULL UNIQUE,
            jurisdictions TEXT DEFAULT '',
            frequency VARCHAR(20) DEFAULT 'daily',
            min_risk_level VARCHAR(20) DEFAULT 'LOW',
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_notified_at DATETIME DEFAULT NULL
        )""",
    ]

    try:
        with engine.connect() as conn:
            # Существующие колонки
            existing: dict[str, set[str]] = {}
            for tbl in ("regulations", "regulators"):
                rows = conn.execute(text(f"PRAGMA table_info({tbl})")).fetchall()
                existing[tbl] = {r[1] for r in rows}

            for tbl, col, typedef in _new_cols:
                if col not in existing.get(tbl, set()):
                    try:
                        conn.execute(text(
                            f"ALTER TABLE {tbl} ADD COLUMN {col} {typedef}"
                        ))
                    except Exception:
                        pass  # колонка уже есть (гонка)

            for ddl in _new_tables:
                conn.execute(text(ddl))

            conn.commit()

    except Exception as exc:
        import logging
        logging.getLogger(__name__).error(
            "ensure_schema_migrations: ошибка — %s", exc
        )
