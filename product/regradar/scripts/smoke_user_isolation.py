#!/usr/bin/env python3
"""Smoke checks for per-user isolation across profile, Telegram, and delivery data."""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_DB = Path(tempfile.gettempdir()) / f"regradar_user_isolation_{int(time.time() * 1000)}.db"
os.environ["REGRADAR_DB_PATH"] = str(TEST_DB)

from app import config  # noqa: E402

config.DB_PATH = str(TEST_DB)

from app.auth import create_user  # noqa: E402
from app.db import ensure_auth_tables  # noqa: E402
import app.db as db  # noqa: E402
from app.profile import get_or_create_profile  # noqa: E402
from app.telegram_pairing import create_pairing_code, get_pairing_status  # noqa: E402
from app.user_delivery import create_delivery_log, get_user_delivery_logs  # noqa: E402

db.DB_PATH = str(TEST_DB)


def _pass(message: str) -> None:
    print(f"PASS: {message}")


def _fail(message: str, failures: list[str]) -> None:
    print(f"FAIL: {message}")
    failures.append(message)


def main() -> int:
    failures: list[str] = []
    stamp = int(time.time() * 1000)

    ensure_auth_tables()
    user_a = create_user(
        f"isolation_a_{stamp}@example.com",
        "testpass123",
        company_name="Isolation A",
        industry="Fintech",
    )
    user_b = create_user(
        f"isolation_b_{stamp}@example.com",
        "testpass123",
        company_name="Isolation B",
        industry="Legal",
    )
    user_a_id = int(user_a["id"])
    user_b_id = int(user_b["id"])

    profile_a = get_or_create_profile(user_a_id)
    profile_b = get_or_create_profile(user_b_id)
    if profile_a.get("user_id") == user_a_id and profile_b.get("user_id") == user_b_id:
        _pass("profiles are keyed to their own user_id")
    else:
        _fail("profile user_id keys are incorrect", failures)
    if profile_a.get("user_id") != profile_b.get("user_id"):
        _pass("user A and user B profiles are distinct")
    else:
        _fail("user A and user B profiles share the same row", failures)

    alert_id = f"isolation_alert_{stamp}"
    create_delivery_log(
        user_a_id,
        delivery_type="reviewed_alert_preview",
        status="sent",
        title="Isolation A Delivery",
        alert_id=alert_id,
        idempotency_key=f"{user_a_id}:reviewed_alert_preview:{alert_id}",
    )
    b_logs = get_user_delivery_logs(user_b_id)
    if not any(log.get("title") == "Isolation A Delivery" for log in b_logs):
        _pass("user B delivery logs do not include user A entries")
    else:
        _fail("user B delivery logs include user A data", failures)

    status_a = get_pairing_status(user_a_id)
    status_b = get_pairing_status(user_b_id)
    if "telegram_chat_id" not in status_a and "telegram_chat_id" not in status_b:
        _pass("pairing status does not expose raw telegram_chat_id")
    else:
        _fail("pairing status exposes raw telegram_chat_id", failures)
    if "telegram_chat_id_masked" in status_a and "telegram_chat_id_masked" in status_b:
        _pass("pairing status uses masked chat ID field")
    else:
        _fail("pairing status is missing masked chat ID field", failures)

    code_a = create_pairing_code(user_a_id)
    status_b_after_code = get_pairing_status(user_b_id)
    b_active_code = status_b_after_code.get("active_code") or {}
    if not b_active_code or b_active_code.get("code") != code_a.get("code"):
        _pass("user B cannot see user A active pairing code")
    else:
        _fail("user B can see user A active pairing code", failures)

    try:
        from app.alert_routing import get_sent_alert_ids_for_user

        sent_b = get_sent_alert_ids_for_user(user_b_id)
        if alert_id not in sent_b:
            _pass("alert routing sent IDs are isolated by user")
        else:
            _fail("user B routing sent IDs include user A alert", failures)
    except Exception as exc:
        print(f"SKIP: alert routing isolation helper unavailable ({type(exc).__name__})")

    for suffix in ("", "-wal", "-shm"):
        try:
            Path(str(TEST_DB) + suffix).unlink(missing_ok=True)
        except Exception:
            pass

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
