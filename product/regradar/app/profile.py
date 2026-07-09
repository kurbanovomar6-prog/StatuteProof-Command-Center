"""Account-owned dashboard profile persistence."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from app.db import _connect
from app.regulator_map import REGULATOR_CODES

# Regulator scope codes a customer may subscribe to. Empty/absent scope
# means "all regulators" (backward compatible). Mirrors the resolver's
# allow-list so profile validation and routing stay in lock-step.
ALLOWED_REGULATOR_CODES: frozenset[str] = frozenset(REGULATOR_CODES)


def normalize_regulators(value) -> list[str]:
    """Coerce arbitrary input into an ordered, deduped list of valid codes.

    Uppercases entries, drops anything outside ALLOWED_REGULATOR_CODES, and
    preserves first-seen order. ``None`` / empty input -> ``[]`` (= all).
    """
    if value is None:
        return []
    if isinstance(value, str):
        items = [part.strip() for part in value.split(",")]
    elif isinstance(value, (list, tuple)):
        items = list(value)
    else:
        return []
    seen: list[str] = []
    for item in items:
        code = str(item or "").strip().upper()
        if code and code in ALLOWED_REGULATOR_CODES and code not in seen:
            seen.append(code)
    return seen


def _regulators_input_nonempty(value) -> bool:
    """True if the caller supplied at least one non-blank scope token.

    Distinguishes an explicit "all regulators" request ([] / None / "") from
    a scoping attempt that happened to contain only invalid codes (["TYPO"]).
    """
    if value is None:
        return False
    if isinstance(value, str):
        return any(part.strip() for part in value.split(","))
    if isinstance(value, (list, tuple)):
        return any(str(item or "").strip() for item in value)
    return False


_CREATE_PROFILE_TABLE = """
    CREATE TABLE IF NOT EXISTS user_profiles (
        user_id INTEGER PRIMARY KEY REFERENCES users(id),

        company_name TEXT,
        industries TEXT,
        markets TEXT,
        topics TEXT,
        licence_type TEXT,
        custom_sources TEXT,
        regulators TEXT,

        alert_threshold TEXT NOT NULL DEFAULT 'MEDIUM',
        brief_language TEXT NOT NULL DEFAULT 'en',
        weekly_brief_enabled INTEGER NOT NULL DEFAULT 1,
        ai_enabled INTEGER NOT NULL DEFAULT 1,
        telegram_alerts_enabled INTEGER NOT NULL DEFAULT 0,
        email_alerts_enabled INTEGER NOT NULL DEFAULT 0,

        onboarding_completed INTEGER NOT NULL DEFAULT 0,

        created_at TIMESTAMP NOT NULL,
        updated_at TIMESTAMP NOT NULL
    );
"""

_ALLOWED_FIELDS = {
    "company_name",
    "industries",
    "markets",
    "topics",
    "licence_type",
    "custom_sources",
    "regulators",
    "alert_threshold",
    "brief_language",
    "weekly_brief_enabled",
    "ai_enabled",
    "telegram_alerts_enabled",
    "email_alerts_enabled",
    "onboarding_completed",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_profile_table() -> None:
    conn = _connect()
    try:
        conn.executescript(_CREATE_PROFILE_TABLE)
        # Additive migration for pre-existing tables: CREATE TABLE IF NOT
        # EXISTS never adds a column to an already-created table, so add the
        # regulators column when missing. Additive only — no data change.
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(user_profiles)")}
        if "regulators" not in columns:
            conn.execute("ALTER TABLE user_profiles ADD COLUMN regulators TEXT")
        conn.commit()
    finally:
        conn.close()


def _parse_json_list(value) -> list:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []


def _json_list(value) -> str:
    return json.dumps(value if isinstance(value, list) else [], ensure_ascii=False)


def _sanitize_str(value, max_len: int) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return text[:max_len]


def _sanitize_list(value, max_items: int, max_item_len: int) -> list[str]:
    items = _parse_json_list(value)
    cleaned: list[str] = []
    for item in items[:max_items]:
        text = _sanitize_str(item, max_item_len)
        if text:
            cleaned.append(text)
    return cleaned


def _sanitize_bool(value) -> int:
    if isinstance(value, str):
        return 1 if value.strip().lower() in {"1", "true", "yes", "on"} else 0
    return 1 if bool(value) else 0


def _sanitize_custom_sources(value) -> list[dict[str, str]]:
    items = _parse_json_list(value)
    cleaned: list[dict[str, str]] = []
    for item in items[:20]:
        if not isinstance(item, dict):
            raise ValueError("Each custom source must be an object.")
        url = _sanitize_str(item.get("url"), 500)
        if not url:
            raise ValueError("Each custom source must include a URL.")
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError("Custom source URLs must start with http:// or https://.")
        source: dict[str, str] = {"url": url}
        for key in ("market", "category", "notes", "status"):
            text = _sanitize_str(item.get(key), 200)
            if text:
                source[key] = text
        cleaned.append(source)
    return cleaned


def _profile_row_to_dict(row) -> dict:
    data = dict(row)
    return {
        "user_id": data["user_id"],
        "company_name": data.get("company_name"),
        "industries": _parse_json_list(data.get("industries")),
        "markets": _parse_json_list(data.get("markets")),
        "topics": _parse_json_list(data.get("topics")),
        "licence_type": data.get("licence_type"),
        "custom_sources": _parse_json_list(data.get("custom_sources")),
        "regulators": normalize_regulators(_parse_json_list(data.get("regulators"))),
        "alert_threshold": data.get("alert_threshold") or "MEDIUM",
        "brief_language": data.get("brief_language") or "en",
        "weekly_brief_enabled": bool(data.get("weekly_brief_enabled")),
        "ai_enabled": bool(data.get("ai_enabled")),
        "telegram_alerts_enabled": bool(data.get("telegram_alerts_enabled")),
        "email_alerts_enabled": bool(data.get("email_alerts_enabled")),
        "onboarding_completed": bool(data.get("onboarding_completed")),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
    }


def _get_profile_row(conn: sqlite3.Connection, user_id: int):
    return conn.execute(
        "SELECT * FROM user_profiles WHERE user_id = ? LIMIT 1",
        (user_id,),
    ).fetchone()


def get_or_create_profile(user_id: int, seed: dict | None = None) -> dict:
    ensure_profile_table()
    seed = seed or {}
    conn = _connect()
    try:
        row = _get_profile_row(conn, user_id)
        if row is not None:
            return _profile_row_to_dict(row)

        industry = _sanitize_str(seed.get("industry"), 100)
        industries = [industry] if industry else []
        now = _now()
        conn.execute(
            """
            INSERT INTO user_profiles (
                user_id, company_name, industries, markets, topics, licence_type,
                custom_sources, regulators, alert_threshold, brief_language,
                weekly_brief_enabled, ai_enabled, telegram_alerts_enabled,
                email_alerts_enabled, onboarding_completed, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                _sanitize_str(seed.get("company_name"), 200),
                _json_list(industries),
                _json_list([]),
                _json_list([]),
                None,
                _json_list([]),
                _json_list([]),
                "MEDIUM",
                "en",
                1,
                1,
                0,
                0,
                0,
                now,
                now,
            ),
        )
        conn.commit()
        return _profile_row_to_dict(_get_profile_row(conn, user_id))
    finally:
        conn.close()


def _sanitize_updates(updates: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in updates.items():
        if key not in _ALLOWED_FIELDS:
            continue
        if key == "company_name":
            sanitized[key] = _sanitize_str(value, 200)
        elif key in {"industries", "markets"}:
            sanitized[key] = _json_list(_sanitize_list(value, 20, 100))
        elif key == "topics":
            sanitized[key] = _json_list(_sanitize_list(value, 50, 100))
        elif key == "licence_type":
            sanitized[key] = _sanitize_str(value, 200)
        elif key == "custom_sources":
            sanitized[key] = _json_list(_sanitize_custom_sources(value))
        elif key == "regulators":
            normalized = normalize_regulators(value)
            # Fail closed at the boundary: a non-empty input that yields no
            # valid codes (e.g. ["TYPO"]) must NOT be stored as [] — that
            # would silently un-scope the customer to "all regulators".
            # An explicitly empty input still means "all" (backward compatible).
            if not normalized and _regulators_input_nonempty(value):
                raise ValueError(
                    "regulators must be valid codes: "
                    + ", ".join(sorted(ALLOWED_REGULATOR_CODES))
                )
            sanitized[key] = _json_list(normalized)
        elif key == "alert_threshold":
            threshold = str(value or "").strip().upper()
            if threshold not in {"LOW", "MEDIUM", "HIGH"}:
                raise ValueError("alert_threshold must be LOW, MEDIUM, or HIGH.")
            sanitized[key] = threshold
        elif key == "brief_language":
            language = str(value or "").strip().lower()
            if language not in {"en", "ru", "both"}:
                raise ValueError("brief_language must be en, ru, or both.")
            sanitized[key] = language
        elif key in {
            "weekly_brief_enabled",
            "ai_enabled",
            "telegram_alerts_enabled",
            "email_alerts_enabled",
            "onboarding_completed",
        }:
            sanitized[key] = _sanitize_bool(value)
    return sanitized


def update_profile(user_id: int, updates: dict) -> dict:
    ensure_profile_table()
    get_or_create_profile(user_id)
    sanitized = _sanitize_updates(updates if isinstance(updates, dict) else {})
    if not sanitized:
        return get_or_create_profile(user_id)

    sanitized["updated_at"] = _now()
    assignments = ", ".join(f"{key} = ?" for key in sanitized)
    values = list(sanitized.values()) + [user_id]

    conn = _connect()
    try:
        conn.execute(
            f"UPDATE user_profiles SET {assignments} WHERE user_id = ?",
            values,
        )
        conn.commit()
        return _profile_row_to_dict(_get_profile_row(conn, user_id))
    finally:
        conn.close()
