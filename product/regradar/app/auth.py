"""Authentication helpers for StatuteProof dashboard accounts.

This module is intentionally small and dependency-free for the Auth A sprint.
It provides password hashing, user persistence, and server-side sessions.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from typing import Any

from app.db import _connect, ensure_auth_tables


SESSION_COOKIE_NAME = "statuteproof_session"
SESSION_MAX_AGE_SECONDS = 7 * 24 * 60 * 60
_PBKDF2_ALGORITHM = "pbkdf2_sha256"
_PBKDF2_ITERATIONS = 600_000
_SALT_BYTES = 16
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class DuplicateEmailError(Exception):
    """Raised when registration attempts to reuse an existing email."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _parse_iso(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def normalize_email(email: str) -> str:
    return str(email or "").strip().lower()


def validate_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(normalize_email(email)))


def validate_password(password: str) -> tuple[bool, str]:
    if len(str(password or "")) < 8:
        return False, "Password must be at least 8 characters."
    return True, ""


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        str(password).encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    return (
        f"{_PBKDF2_ALGORITHM}${_PBKDF2_ITERATIONS}$"
        f"{salt.hex()}${digest.hex()}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations_raw, salt_hex, hash_hex = str(password_hash).split("$", 3)
        if algorithm != _PBKDF2_ALGORITHM:
            return False
        iterations = int(iterations_raw)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            str(password).encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def make_public_user(user_row) -> dict:
    user = dict(user_row)
    return {
        "id": user.get("id"),
        "email": user.get("email"),
        "full_name": user.get("full_name"),
        "company_name": user.get("company_name"),
        "industry": user.get("industry"),
        "created_at": user.get("created_at"),
    }


def _sanitize_optional_text(value, max_len: int) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return text[:max_len]


def create_user(
    email,
    password,
    full_name=None,
    company_name=None,
    industry=None,
    job_title=None,
    company_type=None,
    jurisdiction=None,
) -> dict:
    ensure_auth_tables()
    normalized = normalize_email(email)
    now = _iso(_now())
    conn = _connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO users
                (email, password_hash, full_name, company_name, industry,
                 job_title, company_type, jurisdiction, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                normalized,
                hash_password(password),
                _sanitize_optional_text(full_name, 160),
                _sanitize_optional_text(company_name, 200),
                _sanitize_optional_text(industry, 120),
                _sanitize_optional_text(job_title, 120),
                _sanitize_optional_text(company_type, 120),
                _sanitize_optional_text(jurisdiction, 120),
                now,
                now,
            ),
        )
        conn.commit()
        user = get_user_by_id(cur.lastrowid)
        if user is None:
            raise RuntimeError("Created user could not be loaded.")
        return user
    except sqlite3.IntegrityError as exc:
        raise DuplicateEmailError("Email is already registered.") from exc
    finally:
        conn.close()


def get_user_by_email(email) -> dict | None:
    ensure_auth_tables()
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT id, email, password_hash, full_name, company_name, industry,
                   created_at, updated_at, is_active
            FROM users
            WHERE email = ?
            LIMIT 1
            """,
            (normalize_email(email),),
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def get_user_by_id(user_id) -> dict | None:
    ensure_auth_tables()
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT id, email, password_hash, full_name, company_name, industry,
                   created_at, updated_at, is_active
            FROM users
            WHERE id = ?
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def create_session(user_id: int) -> str:
    ensure_auth_tables()
    session_id = secrets.token_hex(32)
    now = _now()
    expires_at = now + timedelta(seconds=SESSION_MAX_AGE_SECONDS)
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO sessions (id, user_id, created_at, expires_at, last_seen_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, user_id, _iso(now), _iso(expires_at), _iso(now)),
        )
        conn.commit()
        return session_id
    finally:
        conn.close()


def validate_session(session_id: str) -> dict | None:
    if not session_id:
        return None
    ensure_auth_tables()
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT s.id, s.user_id, s.expires_at,
                   u.id AS user_id, u.email, u.password_hash, u.full_name, u.company_name,
                   u.industry, u.created_at, u.updated_at, u.is_active
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.id = ?
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        data = dict(row)
        if _parse_iso(data["expires_at"]) <= _now():
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()
            return None
        if not data.get("is_active"):
            return None
        conn.execute(
            "UPDATE sessions SET last_seen_at = ? WHERE id = ?",
            (_iso(_now()), session_id),
        )
        conn.commit()
        return {
            "id": data["user_id"],
            "email": data["email"],
            "password_hash": data["password_hash"],
            "full_name": data["full_name"],
            "company_name": data["company_name"],
            "industry": data["industry"],
            "created_at": data["created_at"],
            "updated_at": data["updated_at"],
            "is_active": data["is_active"],
        }
    finally:
        conn.close()


def delete_session(session_id: str) -> None:
    if not session_id:
        return
    ensure_auth_tables()
    conn = _connect()
    try:
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()


def parse_session_cookie(cookie_header: str) -> str | None:
    if not cookie_header:
        return None
    cookie = SimpleCookie()
    try:
        cookie.load(cookie_header)
    except Exception:
        return None
    morsel = cookie.get(SESSION_COOKIE_NAME)
    return morsel.value if morsel else None


def require_auth(handler) -> dict | None:
    session_id = parse_session_cookie(handler.headers.get("Cookie", ""))
    return validate_session(session_id or "")
