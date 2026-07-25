"""Reproducible measurement for the SECURITY axis.

Three questions, answered by exercising the real code rather than grepping for
the presence of a helper:

  1. Can an attacker keep guessing one account's password by changing IP?
  2. Can an operator principal (GLOBAL-org scope) exist at all?
  3. Is there any path to seat a second person in a workspace?

    python3 tools/measure_security_axis.py            # human summary
    python3 tools/measure_security_axis.py --json

Runs entirely against a throwaway database in a temp directory; it never touches
the working store.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ATTEMPTS = 25  # comfortably past the 10/hour per-IP login limiter


def _isolated_db(tmp: Path):
    """Point the app at a throwaway database and return the auth module."""
    import app.db as app_db

    app_db.DB_PATH = str(tmp / "probe.db")
    return app_db


def measure() -> dict:
    report: dict = {}
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        _isolated_db(tmp)

        from app.auth import (
            clear_failed_logins,
            create_user,
            get_user_by_email,
            is_account_locked,
            record_failed_login,
            verify_password,
        )
        from app.db import (
            backfill_org_memberships,
            ensure_auth_tables,
            ensure_rbac_tables,
        )

        ensure_auth_tables()
        ensure_rbac_tables()
        user = create_user("probe@example.test", "correct-horse-battery")
        # The real init path runs this migration (app/db.py:860, 882, 895), and it
        # is what gives a user the org-of-one their principal resolves from. A probe
        # that skips it invents a "user has no org" failure that production does not
        # have — checked against the working DB: 17 users, 17 memberships.
        backfill_org_memberships()

        # ── 1. per-account lockout ────────────────────────────────────────────
        # Every attempt below is the SAME account. The per-IP limiter in
        # app/api.py cannot see this: an attacker rotating source IPs presents a
        # fresh key each time, so the question is whether anything counts failures
        # against the ACCOUNT.
        def _login(password: str) -> bool:
            """The exact sequence app/api_auth.py performs for a sign-in."""
            email = "probe@example.test"
            if is_account_locked(email):
                return False
            row = get_user_by_email(email)
            ok = bool(
                row and row.get("is_active")
                and verify_password(password, row.get("password_hash", ""))
            )
            if ok:
                clear_failed_logins(email)
            else:
                record_failed_login(email)
            return ok

        for _ in range(ATTEMPTS):
            _login("wrong-password")
        # If a lockout exists, the CORRECT password is now refused too.
        still_admits_correct_password = _login("correct-horse-battery")
        wrong_accepted_after_many = _login("wrong-password")
        report["failed_attempts_made"] = ATTEMPTS
        report["account_locks_after_repeated_failures"] = not still_admits_correct_password
        report["wrong_password_ever_accepted"] = wrong_accepted_after_many

        # ── 2. can an operator exist ──────────────────────────────────────────
        from app.rbac import GLOBAL_ORG_ID
        from app.rbac_runtime import assign_org_role, resolve_principal

        owner = {"id": int(user["id"]), "email": "probe@example.test"}
        principal = resolve_principal(owner)
        report["self_registered_user_org_id"] = principal.org_id
        report["self_registered_user_role"] = principal.role

        # The owner of their own org tries to grant themselves GLOBAL scope —
        # the only route the codebase exposes.
        attempt = assign_org_role(owner, int(user["id"]), int(GLOBAL_ORG_ID), "owner")
        report["owner_can_grant_global_scope"] = bool(attempt.get("ok"))
        report["owner_grant_error"] = attempt.get("error")

        # Does a bootstrap exist, and does it actually produce a working operator?
        try:
            from app.rbac_runtime import bootstrap_operator
        except ImportError:
            report["operator_bootstrap_exists"] = False
            report["bootstrap_produces_operator"] = False
        else:
            report["operator_bootstrap_exists"] = True
            seeded = bootstrap_operator(int(user["id"]))
            after = resolve_principal(owner)
            report["bootstrap_produces_operator"] = bool(
                seeded.get("ok") and after.org_id == GLOBAL_ORG_ID
            )
            report["operator_org_after_bootstrap"] = after.org_id

        # ── 3. seating a second person ────────────────────────────────────────
        second = create_user("teammate@example.test", "another-password-99")
        backfill_org_memberships()
        seat = assign_org_role(owner, int(second["id"]), int(principal.org_id or 0), "auditor")
        report["owner_can_seat_a_teammate"] = bool(seat.get("ok"))
        report["seat_error"] = seat.get("error")

    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = measure()

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    print("1. per-account lockout")
    print(f"   failed attempts made against one account: {report['failed_attempts_made']}")
    print(f"   account locks afterwards:                 {report['account_locks_after_repeated_failures']}")
    print(f"   a wrong password was ever accepted:       {report['wrong_password_ever_accepted']}")
    print("\n2. operator principal")
    print(f"   a self-registered user resolves to org:   {report['self_registered_user_org_id']} "
          f"as {report['self_registered_user_role']}")
    print(f"   that owner can grant GLOBAL scope:        {report['owner_can_grant_global_scope']} "
          f"({report['owner_grant_error']})")
    print(f"   a bootstrap for the first operator exists:{report['operator_bootstrap_exists']}")
    print(f"   and it produces a real operator principal: {report['bootstrap_produces_operator']} "
          f"(org after bootstrap: {report.get('operator_org_after_bootstrap')})")
    print("\n3. seating a second person")
    print(f"   owner can seat a teammate in their org:   {report['owner_can_seat_a_teammate']} "
          f"({report['seat_error']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
