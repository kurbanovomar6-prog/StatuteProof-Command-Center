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
from datetime import datetime, timezone

from app.config import DB_PATH
from app.rbac import GLOBAL_ORG_ID
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
    CREATE INDEX IF NOT EXISTS idx_url_created ON documents (url, created_at DESC);
"""

_CREATE_AUTH_TABLES = """
    CREATE TABLE IF NOT EXISTS users (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        email         TEXT      UNIQUE NOT NULL,
        normalized_email TEXT   UNIQUE NOT NULL,
        password_hash TEXT      NOT NULL,
        auth_provider TEXT      NOT NULL DEFAULT 'password',
        email_verified INTEGER  NOT NULL DEFAULT 0,
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

    CREATE TABLE IF NOT EXISTS oauth_identities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id),
        provider TEXT NOT NULL,
        provider_user_id TEXT NOT NULL,
        normalized_email TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL,
        updated_at TIMESTAMP NOT NULL,
        UNIQUE(provider, provider_user_id)
    );

    CREATE INDEX IF NOT EXISTS idx_oauth_identities_user_id ON oauth_identities(user_id);
    CREATE INDEX IF NOT EXISTS idx_oauth_identities_email ON oauth_identities(normalized_email);

    CREATE TABLE IF NOT EXISTS oauth_states (
        state TEXT PRIMARY KEY,
        next_path TEXT NOT NULL DEFAULT '/app',
        created_at TIMESTAMP NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        consumed_at TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_oauth_states_expires ON oauth_states(expires_at);
"""

_CREATE_EMAIL_VERIFICATION_TOKENS_TABLE = """
    CREATE TABLE IF NOT EXISTS email_verification_tokens (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        created_at TIMESTAMP NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        used_at TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_evtokens_user_id ON email_verification_tokens(user_id);
    CREATE INDEX IF NOT EXISTS idx_evtokens_expires ON email_verification_tokens(expires_at);
"""

_CREATE_ACTION_LOG_TABLE = """
    CREATE TABLE IF NOT EXISTS alert_action_log (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id       INTEGER NOT NULL,
        alert_id      TEXT    NOT NULL,
        decision      TEXT    NOT NULL,
        notes         TEXT    NOT NULL DEFAULT '',
        reviewer_name TEXT    NOT NULL DEFAULT '',
        created_at    TIMESTAMP NOT NULL,
        action_hash   TEXT    NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_aal_user_alert ON alert_action_log(user_id, alert_id);
    CREATE INDEX IF NOT EXISTS idx_aal_created_at ON alert_action_log(created_at);
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


# ── RBAC Stage-1 — INERT, ADDITIVE org/role model + immutable access log ─────────
#
# These tables are the dormant foundation for role-based access control. They are
# NEW and PURELY ADDITIVE — they touch no existing table and no live endpoint
# reads or writes them in Stage-1 (see app/rbac.py, app/access_log.py). A later
# Stage-2 will resolve a Principal from ``org_members`` and gate requests on
# ``app.rbac.can``, recording each decision via ``app.access_log``.
#
#   orgs         — one row per organisation. The GLOBAL org (id 0) is seeded for
#                  cross-org / operator scope. Every existing user is backfilled
#                  as the owner of their own "org-of-one" (owner_user_id = user).
#   org_members  — (org_id, user_id, role) membership, unique per (org,user).
#   access_log   — append-only audit of authorization decisions (no update/delete
#                  path exists anywhere, so rows are immutable by construction).
#
# ``orgs.id`` is a plain INTEGER PRIMARY KEY (rowid alias) rather than
# AUTOINCREMENT so the GLOBAL org can be seeded with the explicit id 0; personal
# orgs then take the next rowids (1, 2, …). The partial UNIQUE index on
# ``owner_user_id`` guarantees at most one org-of-one per user, which is what
# makes the backfill idempotent under re-runs and races.
_CREATE_RBAC_TABLES = """
    CREATE TABLE IF NOT EXISTS orgs (
        id            INTEGER PRIMARY KEY,
        name          TEXT      NOT NULL,
        owner_user_id INTEGER,
        created_at    TIMESTAMP NOT NULL
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_orgs_owner_user_id
        ON orgs(owner_user_id) WHERE owner_user_id IS NOT NULL;

    CREATE TABLE IF NOT EXISTS org_members (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id     INTEGER   NOT NULL REFERENCES orgs(id),
        user_id    INTEGER   NOT NULL REFERENCES users(id),
        role       TEXT      NOT NULL,
        created_at TIMESTAMP NOT NULL,
        UNIQUE(org_id, user_id)
    );

    CREATE INDEX IF NOT EXISTS idx_org_members_user_id ON org_members(user_id);
    CREATE INDEX IF NOT EXISTS idx_org_members_org_id  ON org_members(org_id);

    CREATE TABLE IF NOT EXISTS access_log (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        ts            TIMESTAMP NOT NULL,
        actor_user_id INTEGER,
        org_id        INTEGER,
        action        TEXT      NOT NULL,
        resource_type TEXT      NOT NULL DEFAULT '',
        resource_id   TEXT      NOT NULL DEFAULT '',
        result        TEXT      NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_access_log_ts    ON access_log(ts);
    CREATE INDEX IF NOT EXISTS idx_access_log_actor ON access_log(actor_user_id);
    CREATE INDEX IF NOT EXISTS idx_access_log_org   ON access_log(org_id);

    -- Append-only BY CONSTRUCTION: block every UPDATE/DELETE at the database
    -- layer, not just by omitting helpers. A future stray writer that opens its
    -- own connection still cannot mutate or erase an audit row.
    CREATE TRIGGER IF NOT EXISTS trg_access_log_no_update
    BEFORE UPDATE ON access_log
    BEGIN
        SELECT RAISE(ABORT, 'access_log is append-only');
    END;

    CREATE TRIGGER IF NOT EXISTS trg_access_log_no_delete
    BEFORE DELETE ON access_log
    BEGIN
        SELECT RAISE(ABORT, 'access_log is append-only');
    END;
"""


# ── Auditor Evidence Room — external, time-boxed, read-only shares ───────────────
#
# One row per share an OWNER/ADMIN creates for an outside examiner/auditor (see
# app/evidence_room.py). PURELY ADDITIVE: no existing table is altered.
#
# Security invariants baked into the schema:
#   token_hash  — ONLY the SHA-256 hex of the URL token is stored, never the
#                 token itself. A database read (backup leak, SQL injection
#                 elsewhere, an operator glancing at rows) can never yield a
#                 usable share link — exactly like a password hash.
#   source_ids  — the scope FROZEN at creation as a JSON array. The public room
#                 endpoint reads this column, never caller input, so the share
#                 can never widen after the owner sealed it.
#   expires_at  — expiry is mandatory (NOT NULL); there is no "forever" share.
#   revoked_at  — a revoked share stays as a row (audit history) but resolves
#                 identically to an unknown token (404, no existence oracle).
_CREATE_EVIDENCE_SHARES_TABLE = """
    CREATE TABLE IF NOT EXISTS evidence_shares (
        id               INTEGER   PRIMARY KEY AUTOINCREMENT,
        token_hash       TEXT      NOT NULL UNIQUE,
        owner_user_id    INTEGER   NOT NULL REFERENCES users(id),
        org_display_name TEXT      NOT NULL DEFAULT '',
        source_ids       TEXT      NOT NULL,
        date_from        TEXT      NOT NULL,
        date_to          TEXT      NOT NULL,
        created_at       TIMESTAMP NOT NULL,
        expires_at       TIMESTAMP NOT NULL,
        revoked_at       TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_evidence_shares_owner
        ON evidence_shares(owner_user_id);
"""


def ensure_evidence_shares_table(conn: sqlite3.Connection | None = None) -> None:
    """Provision the evidence_shares table. Cheap + idempotent + additive.

    Mirrors ``ensure_rbac_tables``: constant-cost ``CREATE TABLE IF NOT EXISTS``
    only, safe to call from every evidence-room DB operation. Deliberately NOT
    chained into ``ensure_auth_tables`` — the table is touched only by the
    evidence-room module, so the per-request session path stays unchanged.
    """
    owned_conn = conn is None
    if conn is None:
        conn = _connect()
    try:
        conn.executescript(_CREATE_EVIDENCE_SHARES_TABLE)
        conn.commit()
    finally:
        if owned_conn:
            conn.close()


def ensure_rbac_tables(conn: sqlite3.Connection | None = None) -> None:
    """Provision the RBAC tables and seed the GLOBAL org. Cheap + idempotent.

    Deliberately does ONLY constant-cost work — ``CREATE TABLE IF NOT EXISTS``
    plus a single ``INSERT OR IGNORE`` for the GLOBAL org row — so it is safe to
    chain into ``ensure_auth_tables`` (which runs on the per-request session path)
    with the same cost profile as ``ensure_delivery_log_table``. The O(users)
    backfill lives in :func:`backfill_org_memberships`, which is invoked from the
    once-per-process migration entrypoint :func:`init_db`, NOT here — keeping the
    request hot path free of table-wide scans.

    Additive only: no existing table is altered and no existing row is touched.
    INERT: no endpoint calls ``app.rbac.can`` or
    ``app.access_log.append_access_log`` in Stage-1.
    """
    owned_conn = conn is None
    if conn is None:
        conn = _connect()
    try:
        conn.executescript(_CREATE_RBAC_TABLES)
        now = datetime.now(timezone.utc).isoformat()
        # Seed the GLOBAL org (cross-org / operator scope). owner_user_id NULL.
        conn.execute(
            "INSERT OR IGNORE INTO orgs (id, name, owner_user_id, created_at) "
            "VALUES (?, 'GLOBAL', NULL, ?)",
            (GLOBAL_ORG_ID, now),
        )
        conn.commit()
    finally:
        if owned_conn:
            conn.close()


def backfill_org_memberships(conn: sqlite3.Connection | None = None) -> None:
    """Make every existing user the ``owner`` of their own org-of-one.

    Idempotent and set-based (no Python loop): two ``NOT EXISTS``-guarded
    statements insert only what is missing, so a re-run inserts zero rows. This
    guarantees that when Stage-2 activates ``app.rbac.can``, a solo user resolves
    to ``owner`` of the org that holds their resources and therefore keeps the
    exact full access they have under today's flat owner-scope model.

    Assumes the ``users`` and ``orgs`` tables already exist (they do when called
    from :func:`ensure_rbac_tables`). Never alters an existing row.
    """
    owned_conn = conn is None
    if conn is None:
        conn = _connect()
    try:
        # Guard: nothing to backfill if the users table is not present yet.
        users_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone() is not None
        if not users_exists:
            return
        now = datetime.now(timezone.utc).isoformat()
        # 1) Create a personal org for each user lacking one. ``OR IGNORE`` plus
        #    the partial UNIQUE index on ``owner_user_id`` makes this safe even if
        #    two callers race past the ``NOT EXISTS`` guard concurrently — the
        #    loser is silently skipped rather than raising.
        conn.execute(
            """
            INSERT OR IGNORE INTO orgs (name, owner_user_id, created_at)
            SELECT 'user:' || u.id, u.id, ?
            FROM users u
            WHERE NOT EXISTS (
                SELECT 1 FROM orgs o WHERE o.owner_user_id = u.id
            )
            """,
            (now,),
        )
        # 2) Add the owner membership for each personal org lacking one.
        conn.execute(
            """
            INSERT OR IGNORE INTO org_members (org_id, user_id, role, created_at)
            SELECT o.id, o.owner_user_id, 'owner', ?
            FROM orgs o
            WHERE o.owner_user_id IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM org_members m
                  WHERE m.org_id = o.id AND m.user_id = o.owner_user_id
              )
            """,
            (now,),
        )
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
        if "normalized_email" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN normalized_email TEXT")
            logger.info("DB: added users.normalized_email column")
        if "auth_provider" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN auth_provider TEXT NOT NULL DEFAULT 'password'")
            logger.info("DB: added users.auth_provider column")
        if "email_verified" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0")
            logger.info("DB: added users.email_verified column")
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
        # Founder-set activation columns. ``plan_name`` records what the user
        # self-selected (intent); ``activated_plan`` records what a founder has
        # actually switched on, and is the SOLE source of paid capabilities
        # (see app.plan.capabilities_for / activate_plan). Nullable → an
        # un-activated account resolves to evidence_preview capabilities.
        if "activated_plan" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN activated_plan TEXT")
            logger.info("DB: added users.activated_plan column")
        if "plan_activated_at" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN plan_activated_at TIMESTAMP")
            logger.info("DB: added users.plan_activated_at column")
        _backfill_normalized_user_emails(conn)
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_normalized_email_unique ON users(normalized_email)")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS oauth_identities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                provider TEXT NOT NULL,
                provider_user_id TEXT NOT NULL,
                normalized_email TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                UNIQUE(provider, provider_user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_oauth_identities_user_id ON oauth_identities(user_id);
            CREATE INDEX IF NOT EXISTS idx_oauth_identities_email ON oauth_identities(normalized_email);

            CREATE TABLE IF NOT EXISTS oauth_states (
                state TEXT PRIMARY KEY,
                next_path TEXT NOT NULL DEFAULT '/app',
                created_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                consumed_at TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_oauth_states_expires ON oauth_states(expires_at);
            """
        )
        conn.executescript(_CREATE_ACTION_LOG_TABLE)
        conn.executescript(_CREATE_EMAIL_VERIFICATION_TOKENS_TABLE)
        conn.commit()
    finally:
        if owned_conn:
            conn.close()
    from app.profile import ensure_profile_table
    ensure_profile_table()
    from app.telegram_pairing import ensure_telegram_pairing_tables
    ensure_telegram_pairing_tables()
    ensure_delivery_log_table()
    # RBAC Stage-1: PROVISION the INERT, additive org/role + access-log tables
    # (cheap: CREATE IF NOT EXISTS + a one-row GLOBAL-org seed). The O(users)
    # membership backfill is deliberately NOT here — it runs from init_db() once
    # per process (see backfill_org_memberships) so the per-request session path
    # stays free of table-wide scans. Additive only — no existing table is
    # altered and no live endpoint reads these yet.
    ensure_rbac_tables()


def _backfill_normalized_user_emails(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        "SELECT id, email, normalized_email FROM users ORDER BY id ASC"
    ).fetchall()
    seen: set[str] = set()
    for row in rows:
        user_id = row["id"]
        email = str(row["email"] or "").strip()
        normalized = str(row["normalized_email"] or "").strip().lower() or email.lower()
        if normalized in seen:
            quarantined = f"{normalized}#duplicate-{user_id}"
            conn.execute(
                "UPDATE users SET normalized_email = ?, is_active = 0 WHERE id = ?",
                (quarantined, user_id),
            )
            logger.warning("DB: quarantined duplicate normalized_email for user_id=%s", user_id)
            continue
        seen.add(normalized)
        conn.execute(
            "UPDATE users SET email = ?, normalized_email = ? WHERE id = ?",
            (email, normalized, user_id),
        )


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
            backfill_org_memberships(conn)  # RBAC Stage-1 migration (once/process)
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
            backfill_org_memberships(conn)  # RBAC Stage-1 migration (once/process)
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
        backfill_org_memberships(conn)  # RBAC Stage-1 migration (once/process)
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
    content_hash:    str | None = None,
) -> None:
    """
    Insert a new historical row for `url`.

    Every call creates a new row — full audit trail preserved.

    `content_hash`: when provided, this exact hash is stored. The monitoring
    pipeline passes the canonical normalized hash from the JSONL evidence
    trail so `documents` stays a derived index of the same value (owner
    decision 2). When omitted (legacy callers), the hash is computed
    internally from raw content as before.
    """
    content_hash = content_hash or (
        stable_content_hash(content)
        or hashlib.sha256(content.encode("utf-8")).hexdigest()
    )
    now          = datetime.now(timezone.utc).isoformat()
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
