"""Account-owned Telegram pairing for StatuteProof users."""

from __future__ import annotations

import logging
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from app.db import _connect

logger = logging.getLogger(__name__)

_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_CODE_RE = re.compile(r"^SP-[A-Z2-9]{6}$")
_PAIRING_TTL_MINUTES = 15

_CREATE_PAIRING_TABLES = """
    CREATE TABLE IF NOT EXISTS telegram_pairing_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id),
        code TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        used_at TIMESTAMP,
        used_chat_id TEXT,
        invalidated_at TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_tpc_user_id ON telegram_pairing_codes(user_id);
    CREATE INDEX IF NOT EXISTS idx_tpc_code ON telegram_pairing_codes(code);
    CREATE INDEX IF NOT EXISTS idx_tpc_expires_at ON telegram_pairing_codes(expires_at);
"""

_TELEGRAM_PROFILE_COLUMNS = {
    "telegram_chat_id": "TEXT",
    "telegram_username": "TEXT",
    "telegram_first_name": "TEXT",
    "telegram_paired_at": "TIMESTAMP",
    "telegram_last_test_at": "TIMESTAMP",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None = None) -> str:
    return (dt or _now()).isoformat(timespec="seconds")


def _parse_iso(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def _add_column_if_missing(conn: sqlite3.Connection, column: str, column_type: str) -> None:
    if column not in _table_columns(conn, "user_profiles"):
        conn.execute(f"ALTER TABLE user_profiles ADD COLUMN {column} {column_type}")
        logger.info("DB: added user_profiles.%s", column)


def _ensure_profile_row(conn: sqlite3.Connection, user_id: int) -> None:
    now = _iso()
    conn.execute(
        """
        INSERT OR IGNORE INTO user_profiles (
            user_id, industries, markets, topics, custom_sources,
            alert_threshold, brief_language, weekly_brief_enabled, ai_enabled,
            telegram_alerts_enabled, email_alerts_enabled, onboarding_completed,
            created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, "[]", "[]", "[]", "[]", "MEDIUM", "en", 1, 1, 0, 0, 0, now, now),
    )


def _sanitize_str(value, max_len: int) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return text[:max_len]


def ensure_telegram_pairing_tables() -> None:
    """Create account Telegram pairing storage without touching alert delivery."""
    from app.profile import ensure_profile_table

    ensure_profile_table()
    conn = _connect()
    try:
        conn.executescript(_CREATE_PAIRING_TABLES)
        for column, column_type in _TELEGRAM_PROFILE_COLUMNS.items():
            _add_column_if_missing(conn, column, column_type)
        conn.commit()
    finally:
        conn.close()


def normalize_pairing_code(raw: str) -> str:
    text = str(raw or "").strip().upper()
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"[^A-Z0-9-]", "", text)
    if text.startswith("SP") and not text.startswith("SP-") and len(text) >= 8:
        text = f"SP-{text[2:]}"
    if text.startswith("SP-"):
        suffix = text[3:].replace("-", "")
        text = f"SP-{suffix}"
    return text


def generate_pairing_code() -> str:
    return "SP-" + "".join(secrets.choice(_ALPHABET) for _ in range(6))


def create_pairing_code(user_id: int) -> dict:
    ensure_telegram_pairing_tables()
    now = _now()
    expires_at = now + timedelta(minutes=_PAIRING_TTL_MINUTES)
    conn = _connect()
    try:
        _ensure_profile_row(conn, int(user_id))
        conn.execute(
            """
            UPDATE telegram_pairing_codes
            SET invalidated_at = ?
            WHERE user_id = ?
              AND used_at IS NULL
              AND invalidated_at IS NULL
              AND expires_at > ?
            """,
            (_iso(now), int(user_id), _iso(now)),
        )
        for _ in range(20):
            code = generate_pairing_code()
            try:
                conn.execute(
                    """
                    INSERT INTO telegram_pairing_codes
                        (user_id, code, created_at, expires_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (int(user_id), code, _iso(now), _iso(expires_at)),
                )
                conn.commit()
                return {"code": code, "expires_at": _iso(expires_at)}
            except sqlite3.IntegrityError:
                continue
        raise RuntimeError("Could not generate unique Telegram pairing code.")
    finally:
        conn.close()


def mask_chat_id(chat_id: str | None) -> str | None:
    if not chat_id:
        return None
    text = str(chat_id)
    if len(text) <= 4:
        return "*" * len(text)
    return f"{'*' * max(4, len(text) - 4)}{text[-4:]}"


def _active_code(conn: sqlite3.Connection, user_id: int) -> dict | None:
    row = conn.execute(
        """
        SELECT code, expires_at
        FROM telegram_pairing_codes
        WHERE user_id = ?
          AND used_at IS NULL
          AND invalidated_at IS NULL
          AND expires_at > ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (int(user_id), _iso()),
    ).fetchone()
    return dict(row) if row else None


def get_pairing_status(user_id: int) -> dict:
    ensure_telegram_pairing_tables()
    conn = _connect()
    try:
        _ensure_profile_row(conn, int(user_id))
        conn.commit()
        row = conn.execute(
            """
            SELECT telegram_chat_id, telegram_username, telegram_paired_at,
                   telegram_last_test_at
            FROM user_profiles
            WHERE user_id = ?
            LIMIT 1
            """,
            (int(user_id),),
        ).fetchone()
        data = dict(row) if row else {}
        chat_id = data.get("telegram_chat_id")
        return {
            "connected": bool(chat_id),
            "telegram_username": data.get("telegram_username"),
            "telegram_chat_id_masked": mask_chat_id(chat_id),
            "paired_at": data.get("telegram_paired_at"),
            "last_test_at": data.get("telegram_last_test_at"),
            "active_code": _active_code(conn, int(user_id)),
        }
    finally:
        conn.close()


def consume_pairing_code(code: str, chat_id: str, from_user: dict | None = None) -> str:
    ensure_telegram_pairing_tables()
    normalized = normalize_pairing_code(code)
    if not _CODE_RE.match(normalized):
        return "invalid"

    from_user = from_user or {}
    username = _sanitize_str(from_user.get("username"), 100)
    first_name = _sanitize_str(from_user.get("first_name"), 100)
    now = _now()
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT id, user_id, expires_at, used_at, invalidated_at
            FROM telegram_pairing_codes
            WHERE code = ?
            LIMIT 1
            """,
            (normalized,),
        ).fetchone()
        if row is None:
            return "invalid"
        data = dict(row)
        if data.get("used_at") or data.get("invalidated_at"):
            return "invalid"
        if _parse_iso(data["expires_at"]) <= now:
            return "expired"

        user_id = int(data["user_id"])
        _ensure_profile_row(conn, user_id)
        conn.commit()
        conn.execute("BEGIN")
        conn.execute(
            """
            UPDATE telegram_pairing_codes
            SET used_at = ?, used_chat_id = ?
            WHERE id = ? AND used_at IS NULL AND invalidated_at IS NULL
            """,
            (_iso(now), str(chat_id), int(data["id"])),
        )
        conn.execute(
            """
            UPDATE user_profiles
            SET telegram_chat_id = ?,
                telegram_username = ?,
                telegram_first_name = ?,
                telegram_paired_at = ?,
                updated_at = ?
            WHERE user_id = ?
            """,
            (str(chat_id), username, first_name, _iso(now), _iso(now), user_id),
        )
        conn.commit()
        return "ok"
    except Exception as exc:
        conn.rollback()
        logger.warning("Telegram pairing consume failed: %s: %s", type(exc).__name__, exc)
        return "invalid"
    finally:
        conn.close()


def unlink_telegram(user_id: int) -> dict:
    ensure_telegram_pairing_tables()
    now = _iso()
    conn = _connect()
    try:
        _ensure_profile_row(conn, int(user_id))
        conn.execute(
            """
            UPDATE user_profiles
            SET telegram_chat_id = NULL,
                telegram_username = NULL,
                telegram_first_name = NULL,
                telegram_paired_at = NULL,
                telegram_last_test_at = NULL,
                updated_at = ?
            WHERE user_id = ?
            """,
            (now, int(user_id)),
        )
        conn.execute(
            """
            UPDATE telegram_pairing_codes
            SET invalidated_at = ?
            WHERE user_id = ?
              AND used_at IS NULL
              AND invalidated_at IS NULL
            """,
            (now, int(user_id)),
        )
        conn.commit()
        return get_pairing_status(int(user_id))
    finally:
        conn.close()


def get_telegram_link(user_id: int) -> dict:
    ensure_telegram_pairing_tables()
    conn = _connect()
    try:
        _ensure_profile_row(conn, int(user_id))
        conn.commit()
        row = conn.execute(
            """
            SELECT telegram_chat_id, telegram_username, telegram_first_name,
                   telegram_paired_at, telegram_last_test_at
            FROM user_profiles
            WHERE user_id = ?
            LIMIT 1
            """,
            (int(user_id),),
        ).fetchone()
        data = dict(row) if row else {}
        data["chat_id_masked"] = mask_chat_id(data.get("telegram_chat_id"))
        return data
    finally:
        conn.close()


def touch_telegram_test_sent(user_id: int) -> None:
    ensure_telegram_pairing_tables()
    conn = _connect()
    try:
        _ensure_profile_row(conn, int(user_id))
        now = _iso()
        conn.execute(
            """
            UPDATE user_profiles
            SET telegram_last_test_at = ?, updated_at = ?
            WHERE user_id = ?
            """,
            (now, now, int(user_id)),
        )
        conn.commit()
    finally:
        conn.close()
