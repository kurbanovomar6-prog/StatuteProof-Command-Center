"""
session.py — SQLAlchemy engine factory.

SQLite (dev/local):
  DATABASE_URL = sqlite:///./regrada.db
  → WAL mode + PRAGMA tuning via configure_engine()
  → check_same_thread=False for multi-threaded NiceGUI

PostgreSQL (Railway / production):
  DATABASE_URL = postgresql://user:pass@host:5432/db
  DATABASE_URL = postgres://...     ← Railway injects this prefix; rewritten below
  → connection pool with pre-ping (handles Railway's 30-min idle restarts)
  → no SQLite-specific PRAGMAs

Railway note: set DATABASE_URL to the Railway Postgres plugin's connection string.
The 'postgres://' → 'postgresql://' rewrite is mandatory because SQLAlchemy 2.x
dropped the postgres:// dialect alias.
"""
import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base, configure_engine

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
try:
    from config import settings
    _DB_URL = settings.DATABASE_URL
except Exception:
    _DB_URL = os.getenv("DATABASE_URL", "sqlite:///./regrada.db")

# Railway injects 'postgres://' — SQLAlchemy 2.x requires 'postgresql://'
if _DB_URL.startswith("postgres://"):
    _DB_URL = _DB_URL.replace("postgres://", "postgresql://", 1)

_IS_SQLITE = _DB_URL.startswith("sqlite")

if _IS_SQLITE:
    engine = create_engine(
        _DB_URL,
        connect_args={"check_same_thread": False},
    )
    configure_engine(engine)        # WAL + PRAGMA tuning (SQLite-only)
else:
    engine = create_engine(
        _DB_URL,
        pool_pre_ping = True,       # detects stale connections after Railway idle restarts
        pool_size     = 5,          # persistent connections shared across Celery workers
        max_overflow  = 10,         # burst capacity for parallel scraping tasks
        pool_timeout  = 30,
        pool_recycle  = 1_800,      # recycle before Railway's 30-min connection timeout
        echo          = False,
    )
    # configure_engine() intentionally NOT called — it issues SQLite-only PRAGMAs

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables that don't exist yet. Safe to call on every startup."""
    Base.metadata.create_all(bind=engine)
