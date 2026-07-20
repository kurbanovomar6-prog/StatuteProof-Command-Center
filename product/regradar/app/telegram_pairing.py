"""Account-owned Telegram pairing for StatuteProof users."""

from __future__ import annotations

import logging
import os
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
                -- Pairing IS the explicit opt-in to alerts: the customer ran
                -- /start CODE specifically to receive them, and the bot's
                -- success message promises exactly this. Without this the flag
                -- stayed at its DEFAULT 0 and delivery (get_all_linked_chat_ids,
                -- filtering telegram_alerts_enabled = 1) silently excluded every
                -- paired customer (live CRITICAL, 2026-07-18).
                telegram_alerts_enabled = 1,
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


def get_alert_chat_ids_for_user(user_id: int) -> list[str]:
    """Return the alerts-enabled Telegram chat_id(s) for ONE user.

    Tenancy-scoped delivery helper: used to route a PRIVATE custom source's
    alert only to its owner, instead of the global broadcast in
    ``get_all_linked_chat_ids``. Applies the same paired-AND-enabled filter but
    restricted to ``user_id``. Never raises — returns [] if the user has no
    paired/enabled chat or the table is not yet provisioned.
    """
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        return []
    ensure_telegram_pairing_tables()
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT telegram_chat_id
            FROM user_profiles
            WHERE user_id = ?
              AND telegram_chat_id IS NOT NULL
              AND TRIM(telegram_chat_id) != ''
              AND telegram_alerts_enabled = 1
            """,
            (uid,),
        ).fetchall()
    finally:
        conn.close()
    seen: set[str] = set()
    chat_ids: list[str] = []
    for row in rows:
        chat_id = str(row["telegram_chat_id"]).strip()
        if chat_id and chat_id not in seen:
            seen.add(chat_id)
            chat_ids.append(chat_id)
    return chat_ids


def get_all_linked_chat_ids() -> list[str]:
    """Return the Telegram chat_id of every user who has paired a chat AND
    left Telegram alerts enabled.

    Used by the customer broadcast path in app/telegram.py. Users who have
    unlinked (chat_id NULL/empty) or opted out of Telegram alerts
    (telegram_alerts_enabled = 0) are excluded. Duplicate chat_ids (should
    not happen, but a shared chat could) are de-duplicated while preserving
    order. Never raises — returns [] if the table is not yet provisioned.
    """
    ensure_telegram_pairing_tables()
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT telegram_chat_id
            FROM user_profiles
            WHERE telegram_chat_id IS NOT NULL
              AND TRIM(telegram_chat_id) != ''
              AND telegram_alerts_enabled = 1
            """
        ).fetchall()
    finally:
        conn.close()
    seen: set[str] = set()
    chat_ids: list[str] = []
    for row in rows:
        chat_id = str(row["telegram_chat_id"]).strip()
        if chat_id and chat_id not in seen:
            seen.add(chat_id)
            chat_ids.append(chat_id)
    return chat_ids


def get_linked_alert_user_ids() -> list[int]:
    """Return the user_id of every user who has paired a Telegram chat AND left
    Telegram alerts enabled.

    Used by the scheduled digest dispatcher, which must resolve per-user
    profiles (cadence + thresholds) — so it needs user_ids, not just chat_ids
    (as ``get_all_linked_chat_ids`` returns). Ordered by user_id for a
    deterministic dispatch order. Never raises — returns [] if the table is not
    yet provisioned.
    """
    ensure_telegram_pairing_tables()
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT user_id
            FROM user_profiles
            WHERE telegram_chat_id IS NOT NULL
              AND TRIM(telegram_chat_id) != ''
              AND telegram_alerts_enabled = 1
            ORDER BY user_id ASC
            """
        ).fetchall()
    finally:
        conn.close()
    return [int(row["user_id"]) for row in rows if row["user_id"] is not None]


def alerts_require_plan() -> bool:
    """Is the plan gate on the official-source deliverable active? Default ON.

    Single source of truth for the flag, so every delivery path gates on the
    SAME switch: ``app/telegram.py`` (broadcast), ``app/digest_cadence.py``
    (scheduled instant + digest dispatch) and ``app/deadline_radar.py``
    (reminder broadcast pool). Owner-flippable: set
    STATUTEPROOF_ALERTS_REQUIRE_PLAN=0 to restore the ungated pilot behavior
    (every paired+enabled account receives official-source content).
    """
    return str(os.getenv("STATUTEPROOF_ALERTS_REQUIRE_PLAN") or "1").strip().lower() not in {
        "0", "false", "no", "off",
    }


def _alert_plan_exempt_user_ids() -> set[int]:
    """Resolve STATUTEPROOF_ALERT_PLAN_EXEMPT_EMAILS to user ids.

    The env var holds a comma-separated list of founder/operator account emails
    that stay exempt from the official-alert plan gate (default: empty — no
    exemptions). Emails are normalized with strip().lower() and matched against
    ``users.normalized_email`` (with a LOWER(email) fallback for legacy rows
    where normalized_email is NULL). Never raises — returns an empty set on any
    failure.
    """
    raw = os.getenv("STATUTEPROOF_ALERT_PLAN_EXEMPT_EMAILS") or ""
    emails = [e.strip().lower() for e in raw.split(",") if e.strip()]
    if not emails:
        return set()
    try:
        conn = _connect()
        try:
            placeholders = ",".join("?" for _ in emails)
            rows = conn.execute(
                f"""
                SELECT id
                FROM users
                WHERE normalized_email IN ({placeholders})
                   OR LOWER(email) IN ({placeholders})
                """,
                (*emails, *emails),
            ).fetchall()
        finally:
            conn.close()
        return {int(row["id"]) for row in rows if row["id"] is not None}
    except Exception as exc:  # noqa: BLE001 — an exemption lookup must never crash delivery
        logger.warning("_alert_plan_exempt_user_ids failed: %s", type(exc).__name__)
        return set()


def filter_plan_eligible_chat_ids(chat_ids: list[str]) -> list[str]:
    """Revenue gate for the OFFICIAL-SOURCE Telegram broadcast (audit 07-20).

    Applied by app/telegram.py on TOP of ``get_all_linked_chat_ids()``'s return
    value when STATUTEPROOF_ALERTS_REQUIRE_PLAN is on (the default). A chat_id
    is kept (input order preserved) when ANY of:

      * it does NOT resolve to any user_profiles row — deliberate fail-open for
        unresolvable ids ONLY. These occur in monkeypatched tests or during a
        mid-flight unlink; every production broadcast chat_id comes from this
        same user_profiles table, so a real free user always resolves and is
        gated;
      * a mapped user is listed in STATUTEPROOF_ALERT_PLAN_EXEMPT_EMAILS
        (founder/operator exemption, see ``_alert_plan_exempt_user_ids``);
      * a mapped user's founder-ACTIVATED plan grants the ``official_alerts``
        capability (``app.plan.has_capability`` — reads active_capabilities, so
        a self-selected paid intent grants nothing; lookup errors fail closed
        to free tier).

    Migration note: with the gate ON, previously paired FREE accounts stop
    receiving official-source broadcasts. Their Telegram pairing is untouched —
    delivery resumes the moment a founder runs ``run.py activate-plan`` for
    them. The owner can consciously set STATUTEPROOF_ALERTS_REQUIRE_PLAN=0 to
    restore the ungated pilot behavior.

    On an unexpected internal failure this returns [] — fail CLOSED. The
    founder-chat pilot fallback in ``send_telegram_alert`` then still delivers
    the alert to the founder, so nothing is silently lost.
    """
    if not chat_ids:
        return []
    try:
        # Lazy import: telegram_pairing must not import app.plan at module top
        # (import-cycle risk via app.db consumers).
        from app.plan import has_capability

        ensure_telegram_pairing_tables()
        conn = _connect()
        try:
            rows = conn.execute(
                """
                SELECT user_id, telegram_chat_id
                FROM user_profiles
                WHERE telegram_chat_id IS NOT NULL
                  AND TRIM(telegram_chat_id) != ''
                """
            ).fetchall()
        finally:
            conn.close()
        chat_to_users: dict[str, set[int]] = {}
        for row in rows:
            chat_id = str(row["telegram_chat_id"]).strip()
            if chat_id and row["user_id"] is not None:
                chat_to_users.setdefault(chat_id, set()).add(int(row["user_id"]))

        exempt_ids = _alert_plan_exempt_user_ids()
        eligible: list[str] = []
        for chat_id in chat_ids:
            mapped_users = chat_to_users.get(str(chat_id).strip())
            if not mapped_users:
                # Unresolvable → pass through (see docstring).
                eligible.append(chat_id)
                continue
            if any(uid in exempt_ids for uid in mapped_users) or any(
                has_capability(uid, "official_alerts") for uid in mapped_users
            ):
                eligible.append(chat_id)
        return eligible
    except Exception as exc:  # noqa: BLE001 — fail CLOSED; founder fallback still fires
        logger.error("filter_plan_eligible_chat_ids failed: %s", type(exc).__name__)
        return []


def plan_eligible_user_ids(user_ids: list[int]) -> list[int]:
    """User-id twin of ``filter_plan_eligible_chat_ids`` (audit 07-20).

    Applied by ``app/digest_cadence.run_scheduled_digests`` on TOP of
    ``get_linked_alert_user_ids()``'s return value when
    ``alerts_require_plan()`` is on — the scheduled dispatcher resolves per-user
    profiles, so it gates user ids rather than chat ids. A user id is kept
    (input order preserved) when it is listed in
    STATUTEPROOF_ALERT_PLAN_EXEMPT_EMAILS or its founder-ACTIVATED plan grants
    the ``official_alerts`` capability.

    Fail-direction difference from the chat_id filter, deliberate: that filter
    passes through chat_ids it cannot map to a user_profiles row (fail-OPEN for
    UNRESOLVABLE ids only). Here the input already IS the user id — there is no
    mapping step and therefore nothing unresolvable — so an id that holds no
    capability is dropped, including an unknown id (``has_capability`` falls
    back to free-tier caps). On an unexpected internal failure this returns []
    — fail CLOSED, matching the chat_id filter.
    """
    if not user_ids:
        return []
    try:
        # Lazy import: telegram_pairing must not import app.plan at module top
        # (import-cycle risk via app.db consumers).
        from app.plan import has_capability

        exempt_ids = _alert_plan_exempt_user_ids()
        eligible: list[int] = []
        for raw in user_ids:
            try:
                uid = int(raw)
            except (TypeError, ValueError):
                continue
            if uid in exempt_ids or has_capability(uid, "official_alerts"):
                eligible.append(uid)
        return eligible
    except Exception as exc:  # noqa: BLE001 — fail CLOSED, as above
        logger.error("plan_eligible_user_ids failed: %s", type(exc).__name__)
        return []
