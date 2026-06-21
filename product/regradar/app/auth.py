"""Authentication helpers for StatuteProof dashboard accounts.

This module is intentionally small and dependency-free for the Auth A sprint.
It provides password hashing, user persistence, and server-side sessions.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from typing import Any
from urllib.parse import urlencode

import requests

from app.db import _connect, ensure_auth_tables


SESSION_COOKIE_NAME = "statuteproof_session"
SESSION_MAX_AGE_SECONDS = 7 * 24 * 60 * 60
_PBKDF2_ALGORITHM = "pbkdf2_sha256"
_PBKDF2_ITERATIONS = 600_000
_SALT_BYTES = 16
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class DuplicateEmailError(Exception):
    """Raised when registration attempts to reuse an existing email."""


class OAuthAccountError(Exception):
    """Raised when an OAuth account cannot be trusted or linked safely."""


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
        "normalized_email": user.get("normalized_email"),
        "full_name": user.get("full_name"),
        "company_name": user.get("company_name"),
        "industry": user.get("industry"),
        "auth_provider": user.get("auth_provider"),
        "email_verified": bool(user.get("email_verified")),
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
    display_email = str(email or "").strip()
    now = _iso(_now())
    conn = _connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO users
                (email, normalized_email, password_hash, auth_provider, email_verified,
                 full_name, company_name, industry,
                 job_title, company_type, jurisdiction, plan_name, trial_started_at,
                 created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                display_email,
                normalized,
                hash_password(password),
                "password",
                0,
                _sanitize_optional_text(full_name, 160),
                _sanitize_optional_text(company_name, 200),
                _sanitize_optional_text(industry, 120),
                _sanitize_optional_text(job_title, 120),
                _sanitize_optional_text(company_type, 120),
                _sanitize_optional_text(jurisdiction, 120),
                "evidence_preview",
                now,
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
            SELECT id, email, normalized_email, password_hash, auth_provider,
                   email_verified, full_name, company_name, industry,
                   created_at, updated_at, is_active,
                   plan_name, trial_started_at, plan_intent_at
            FROM users
            WHERE normalized_email = ?
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
            SELECT id, email, normalized_email, password_hash, auth_provider,
                   email_verified, full_name, company_name, industry,
                   created_at, updated_at, is_active,
                   plan_name, trial_started_at, plan_intent_at
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
                   u.id AS user_id, u.email, u.normalized_email, u.password_hash,
                   u.auth_provider, u.email_verified, u.full_name, u.company_name,
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
            "normalized_email": data.get("normalized_email"),
            "password_hash": data["password_hash"],
            "auth_provider": data.get("auth_provider"),
            "email_verified": data.get("email_verified"),
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


def google_oauth_config() -> dict[str, str]:
    return {
        "client_id": os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip(),
        "client_secret": os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip(),
        "redirect_uri": os.environ.get("GOOGLE_OAUTH_REDIRECT_URI", "").strip(),
    }


def google_oauth_available() -> bool:
    config = google_oauth_config()
    return bool(config["client_id"] and config["client_secret"] and config["redirect_uri"])


def _safe_next_path(next_path: str | None) -> str:
    value = str(next_path or "/app").strip() or "/app"
    if not value.startswith("/") or value.startswith("//"):
        return "/app"
    return value[:240]


def create_google_oauth_state(next_path: str = "/app") -> str:
    ensure_auth_tables()
    state = secrets.token_urlsafe(32)
    now = _now()
    expires_at = now + timedelta(minutes=10)
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO oauth_states (state, next_path, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (state, _safe_next_path(next_path), _iso(now), _iso(expires_at)),
        )
        conn.commit()
        return state
    finally:
        conn.close()


def consume_google_oauth_state(state: str) -> dict[str, Any] | None:
    ensure_auth_tables()
    normalized_state = str(state or "").strip()
    if not normalized_state:
        return None
    conn = _connect()
    try:
        row = conn.execute(
            """
            SELECT state, next_path, expires_at, consumed_at
            FROM oauth_states
            WHERE state = ?
            LIMIT 1
            """,
            (normalized_state,),
        ).fetchone()
        if row is None:
            return None
        data = dict(row)
        if data.get("consumed_at") or _parse_iso(data["expires_at"]) <= _now():
            return None
        conn.execute(
            "UPDATE oauth_states SET consumed_at = ? WHERE state = ?",
            (_iso(_now()), normalized_state),
        )
        conn.commit()
        return data
    finally:
        conn.close()


def google_oauth_authorization_url(state: str) -> str:
    if not google_oauth_available():
        raise OAuthAccountError("Google sign-in is not configured.")
    config = google_oauth_config()
    query = urlencode(
        {
            "client_id": config["client_id"],
            "redirect_uri": config["redirect_uri"],
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "prompt": "select_account",
        }
    )
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"


def exchange_google_oauth_code(code: str) -> dict[str, Any]:
    if not google_oauth_available():
        raise OAuthAccountError("Google sign-in is not configured.")
    clean_code = str(code or "").strip()
    if not clean_code:
        raise OAuthAccountError("Google callback is missing an authorization code.")
    config = google_oauth_config()
    token_response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": clean_code,
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "redirect_uri": config["redirect_uri"],
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    if token_response.status_code >= 400:
        raise OAuthAccountError("Google token exchange failed.")
    token_payload = token_response.json()
    access_token = str(token_payload.get("access_token") or "").strip()
    if not access_token:
        raise OAuthAccountError("Google token response did not include an access token.")
    userinfo_response = requests.get(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    if userinfo_response.status_code >= 400:
        raise OAuthAccountError("Google userinfo lookup failed.")
    payload = userinfo_response.json()
    if not isinstance(payload, dict):
        raise OAuthAccountError("Google userinfo response was invalid.")
    return payload


def link_or_create_google_user(claims: dict[str, Any]) -> dict:
    ensure_auth_tables()
    if not isinstance(claims, dict):
        raise OAuthAccountError("Google account payload was invalid.")
    provider_user_id = str(claims.get("sub") or "").strip()
    email = str(claims.get("email") or "").strip()
    if not provider_user_id:
        raise OAuthAccountError("Google account is missing a stable subject identifier.")
    if not validate_email(email):
        raise OAuthAccountError("Google account did not provide a valid email address.")
    if claims.get("email_verified") is not True:
        raise OAuthAccountError("Google email must be verified before sign-in.")

    normalized = normalize_email(email)
    display_name = _sanitize_optional_text(claims.get("name"), 160)
    now = _iso(_now())
    conn = _connect()
    try:
        existing_identity = conn.execute(
            """
            SELECT u.id
            FROM oauth_identities oi
            JOIN users u ON u.id = oi.user_id
            WHERE oi.provider = 'google' AND oi.provider_user_id = ?
            LIMIT 1
            """,
            (provider_user_id,),
        ).fetchone()
        if existing_identity:
            user_id = int(existing_identity["id"])
        else:
            existing_user = conn.execute(
                "SELECT id FROM users WHERE normalized_email = ? LIMIT 1",
                (normalized,),
            ).fetchone()
            if existing_user:
                user_id = int(existing_user["id"])
                conn.execute(
                    """
                    UPDATE users
                    SET email_verified = 1, updated_at = ?
                    WHERE id = ?
                    """,
                    (now, user_id),
                )
            else:
                cur = conn.execute(
                    """
                    INSERT INTO users
                        (email, normalized_email, password_hash, auth_provider, email_verified,
                         full_name, plan_name, trial_started_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        email,
                        normalized,
                        hash_password(secrets.token_urlsafe(32)),
                        "google",
                        1,
                        display_name,
                        "evidence_preview",
                        now,
                        now,
                        now,
                    ),
                )
                user_id = int(cur.lastrowid)
            conn.execute(
                """
                INSERT OR IGNORE INTO oauth_identities
                    (user_id, provider, provider_user_id, normalized_email, created_at, updated_at)
                VALUES (?, 'google', ?, ?, ?, ?)
                """,
                (user_id, provider_user_id, normalized, now, now),
            )
            conn.commit()
        user = get_user_by_id(user_id)
        if user is None:
            raise OAuthAccountError("Google-linked user could not be loaded.")
        return user
    except sqlite3.IntegrityError as exc:
        raise DuplicateEmailError("Email is already registered.") from exc
    finally:
        conn.close()
