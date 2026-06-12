"""
SQLite persistence layer — v3.

Schema (documents):
  id               INTEGER PRIMARY KEY AUTOINCREMENT
  url              TEXT NOT NULL
  content          TEXT NOT NULL
  content_hash     TEXT NOT NULL        SHA-256 of content
  risk_level       TEXT NOT NULL DEFAULT 'LOW'
  risk_reason      TEXT NOT NULL DEFAULT ''
  ai_summary       TEXT                 NULL when AI not used
  business_action  TEXT                 NULL when AI not used
  created_at       TIMESTAMP NOT NULL

Indexes:
  idx_url, idx_created_at

Migration path:
  v1 (url UNIQUE, no risk_level)          → full table rebuild
  v2 (risk_level, no ai columns)          → ALTER TABLE ADD COLUMN ×3
  v3 (all columns present)               → ensure indexes only
"""

import hashlib
import logging
import sqlite3
from datetime import datetime

from app.config import DB_PATH
from app.text_normalization import stable_content_hash

logger = logging.getLogger(__name__)


# ── connection ────────────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


# ── DDL ───────────────────────────────────────────────────────────────────────

_CREATE_TABLE_V3 = """
    CREATE TABLE documents (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        url             TEXT        NOT NULL,
        content         TEXT        NOT NULL,
        content_hash    TEXT        NOT NULL,
        risk_level      TEXT        NOT NULL DEFAULT 'LOW',
        risk_reason     TEXT        NOT NULL DEFAULT '',
        ai_summary      TEXT,
        business_action TEXT,
        created_at      TIMESTAMP   NOT NULL
    );
"""

_CREATE_INDEXES = """
    CREATE INDEX IF NOT EXISTS idx_url        ON documents(url);
    CREATE INDEX IF NOT EXISTS idx_created_at ON documents(created_at);
"""

_CREATE_AUTH_TABLES = """
    CREATE TABLE IF NOT EXISTS users (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        email         TEXT      UNIQUE NOT NULL,
        password_hash TEXT      NOT NULL,
        full_name     TEXT,
        company_name  TEXT,
        industry      TEXT,
        created_at    TIMESTAMP NOT NULL,
        updated_at    TIMESTAMP NOT NULL,
        is_active     INTEGER   NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS sessions (
        id           TEXT      PRIMARY KEY,
        user_id      INTEGER   NOT NULL REFERENCES users(id),
        created_at   TIMESTAMP NOT NULL,
        expires_at   TIMESTAMP NOT NULL,
        last_seen_at TIMESTAMP NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_users_email       ON users(email);
    CREATE INDEX IF NOT EXISTS idx_sessions_user_id  ON sessions(user_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_expires  ON sessions(expires_at);
"""

_CREATE_DELIVERY_LOG_TABLE = """
    CREATE TABLE IF NOT EXISTS user_delivery_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id),
        delivery_type TEXT NOT NULL,
        channel TEXT NOT NULL DEFAULT 'telegram',
        status TEXT NOT NULL,
        title TEXT,
        message_preview TEXT,
        source_id TEXT,
        alert_id TEXT,
        brief_id TEXT,
        error_message TEXT,
        idempotency_key TEXT UNIQUE,
        created_at TIMESTAMP NOT NULL,
        sent_at TIMESTAMP,
        metadata TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_udl_user_id ON user_delivery_log(user_id);
    CREATE INDEX IF NOT EXISTS idx_udl_created_at ON user_delivery_log(created_at);
    CREATE INDEX IF NOT EXISTS idx_udl_idem_key ON user_delivery_log(idempotency_key);
"""


def ensure_delivery_log_table(conn: sqlite3.Connection | None = None) -> None:
    """Create per-user delivery log tables without touching monitoring tables."""
    owned_conn = conn is None
    if conn is None:
        conn = _connect()
    try:
        conn.executescript(_CREATE_DELIVERY_LOG_TABLE)
        conn.commit()
    finally:
        if owned_conn:
            conn.close()


def ensure_auth_tables(conn: sqlite3.Connection | None = None) -> None:
    """Create auth tables without altering existing monitoring tables."""
    owned_conn = conn is None
    if conn is None:
        conn = _connect()
    try:
        conn.executescript(_CREATE_AUTH_TABLES)
        user_cols = _get_table_columns(conn, "users")
        if "full_name" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
            logger.info("DB: added users.full_name column")
        if "job_title" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN job_title TEXT")
            logger.info("DB: added users.job_title column")
        if "company_type" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN company_type TEXT")
            logger.info("DB: added users.company_type column")
        if "jurisdiction" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN jurisdiction TEXT")
            logger.info("DB: added users.jurisdiction column")
        if "plan_name" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN plan_name TEXT NOT NULL DEFAULT 'evidence_preview'")
            logger.info("DB: added users.plan_name column")
        if "trial_started_at" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN trial_started_at TIMESTAMP")
            logger.info("DB: added users.trial_started_at column")
        if "plan_intent_at" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN plan_intent_at TIMESTAMP")
            logger.info("DB: added users.plan_intent_at column")
        conn.commit()
    finally:
        if owned_conn:
            conn.close()
    from app.profile import ensure_profile_table
    ensure_profile_table()
    from app.telegram_pairing import ensure_telegram_pairing_tables
    ensure_telegram_pairing_tables()
    ensure_delivery_log_table()


# ── migration helpers ─────────────────────────────────────────────────────────

def _get_columns(conn: sqlite3.Connection) -> set[str]:
    return {row[1] for row in conn.execute("PRAGMA table_info(documents)")}


def _get_table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def _add_column_if_missing(
    conn: sqlite3.Connection,
    col: str,
    col_type: str,
    default: str | None = None,
) -> None:
    if col not in _get_columns(conn):
        clause = f"ALTER TABLE documents ADD COLUMN {col} {col_type}"
        if default is not None:
            clause += f" DEFAULT {default}"
        conn.execute(clause)
        logger.info("DB: added column '%s'", col)


# ── public API ────────────────────────────────────────────────────────────────

def init_db() -> None:
    """
    Create or migrate the documents table to v3 schema.

    Safe to call on every pipeline run — idempotent.
    """
    conn = _connect()
    try:
        table_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='documents'"
        ).fetchone() is not None

        if not table_exists:
            conn.executescript(_CREATE_TABLE_V3 + _CREATE_INDEXES)
            ensure_auth_tables(conn)
            logger.info("DB initialised (v3 fresh schema)")
            return

        cols = _get_columns(conn)

        # ── v1 → v3: full table rebuild (v1 has url UNIQUE, no risk_level) ──
        if "risk_level" not in cols:
            logger.info("Migrating DB v1 → v3")
            conn.executescript(f"""
                ALTER TABLE documents RENAME TO _documents_v1_backup;
                {_CREATE_TABLE_V3}
                INSERT INTO documents
                    (id, url, content, content_hash, risk_level, risk_reason,
                     ai_summary, business_action, created_at)
                SELECT id, url, content, content_hash, 'LOW', '',
                       NULL, NULL, created_at
                FROM _documents_v1_backup;
                DROP TABLE _documents_v1_backup;
                {_CREATE_INDEXES}
            """)
            ensure_auth_tables(conn)
            logger.info("Migration v1 → v3 complete")
            return

        # ── v2 → v3: add the three new columns individually ──────────────────
        _add_column_if_missing(conn, "risk_reason",     "TEXT NOT NULL", "''" )
        _add_column_if_missing(conn, "ai_summary",      "TEXT"                )
        _add_column_if_missing(conn, "business_action", "TEXT"                )
        conn.commit()

        # Always ensure indexes exist
        conn.executescript(_CREATE_INDEXES)
        ensure_auth_tables(conn)
        logger.debug("DB schema is current (v3)")

    finally:
        conn.close()


def save_document(
    url:             str,
    content:         str,
    risk_level:      str       = "LOW",
    risk_reason:     str       = "",
    ai_summary:      str | None = None,
    business_action: str | None = None,
) -> None:
    """
    Insert a new historical row for `url`.

    Every call creates a new row — full audit trail preserved.
    SHA-256 is computed internally.
    """
    content_hash = (
        stable_content_hash(content)
        or hashlib.sha256(content.encode("utf-8")).hexdigest()
    )
    now          = datetime.utcnow().isoformat()
    conn         = _connect()
    try:
        conn.execute(
            """
            INSERT INTO documents
                (url, content, content_hash, risk_level, risk_reason,
                 ai_summary, business_action, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (url, content, content_hash, risk_level.upper(),
             risk_reason, ai_summary, business_action, now),
        )
        conn.commit()
        logger.debug(
            "Saved: url=%s hash=%s risk=%s ai=%s",
            url, content_hash[:8], risk_level, "yes" if ai_summary else "no",
        )
    finally:
        conn.close()


def get_latest_document(url: str) -> sqlite3.Row | None:
    """Return the most recent stored row for `url`, or None."""
    conn = _connect()
    try:
        return conn.execute(
            """
            SELECT * FROM documents
            WHERE url = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (url,),
        ).fetchone()
    finally:
        conn.close()


def get_document_history(url: str, limit: int = 10) -> list[sqlite3.Row]:
    """Return up to `limit` historical versions for `url`, newest first."""
    conn = _connect()
    try:
        return conn.execute(
            """
            SELECT * FROM documents
            WHERE url = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (url, limit),
        ).fetchall()
    finally:
        conn.close()
