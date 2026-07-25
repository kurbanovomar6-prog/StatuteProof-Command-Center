"""The operator principal has to be creatable — and only by the founder.

`assign_org_role` requires the actor to hold member.manage for the target org, and
`app.rbac.can` confines an owner to their own org. For GLOBAL_ORG_ID that means you
must already BE an operator to create one, and `app/db.py` seeds the GLOBAL *org*
row but never a membership in it. Verified against the working database:
0 rows in org_members with org_id = 0. So `_caller_is_operator` was False for every
account that could exist, and the shared-official-evidence review gate could never
be satisfied by anyone.

Two properties are pinned here and they pull in opposite directions:
the founder CLI must be able to seat the first operator, and a customer must never
be able to seat themselves.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.api  # noqa: E402,F401  (resolves the api <-> mixin import chain first)
from app.auth import create_user  # noqa: E402
from app.db import (  # noqa: E402
    backfill_org_memberships,
    ensure_auth_tables,
    ensure_rbac_tables,
)
from app.rbac import GLOBAL_ORG_ID, ROLE_OWNER  # noqa: E402
from app.rbac_runtime import (  # noqa: E402
    assign_org_role,
    bootstrap_operator,
    resolve_principal,
)


@pytest.fixture()
def founder():
    ensure_auth_tables()
    ensure_rbac_tables()
    user = create_user("founder@example.test", "a-long-enough-password")
    backfill_org_memberships()  # what the real init path does (app/db.py:860,882,895)
    return {"id": int(user["id"]), "email": "founder@example.test"}


# ── the bootstrap works ─────────────────────────────────────────────────────


def test_a_fresh_install_has_no_operator(founder):
    """The state this exists to escape."""
    assert resolve_principal(founder).org_id != GLOBAL_ORG_ID


def test_bootstrap_seats_an_operator(founder):
    result = bootstrap_operator(founder["id"])

    assert result["ok"] is True
    assert result["org_id"] == GLOBAL_ORG_ID
    assert result["role"] == ROLE_OWNER


def test_the_seated_operator_actually_resolves_as_one(founder):
    """The row is not enough: resolve_principal preferred the org the user OWNS,
    so the seat was inert until GLOBAL scope was given priority. Caught by
    measurement, not by reading the code."""
    bootstrap_operator(founder["id"])

    principal = resolve_principal(founder)
    assert principal.org_id == GLOBAL_ORG_ID
    assert principal.role == ROLE_OWNER


def test_bootstrap_is_idempotent(founder):
    bootstrap_operator(founder["id"])
    again = bootstrap_operator(founder["id"])

    assert again["ok"] is True
    assert resolve_principal(founder).org_id == GLOBAL_ORG_ID


# ── and cannot be reached by a customer ─────────────────────────────────────


def test_an_ordinary_owner_cannot_grant_themselves_global_scope(founder):
    """The whole reason the bootstrap is a CLI. If this ever passes, any customer
    can read every other customer's data."""
    result = assign_org_role(founder, founder["id"], int(GLOBAL_ORG_ID), ROLE_OWNER)

    assert result["ok"] is False
    assert result["error"] == "forbidden"
    assert resolve_principal(founder).org_id != GLOBAL_ORG_ID


def test_an_operator_cannot_be_seated_for_a_user_that_does_not_exist(founder):
    result = bootstrap_operator(999_999)

    assert result["ok"] is False
    assert result["error"] == "invalid_target"


def test_a_nonsense_role_is_refused(founder):
    result = bootstrap_operator(founder["id"], role="superuser")

    assert result["ok"] is False
    assert result["error"] == "invalid_role"
    assert resolve_principal(founder).org_id != GLOBAL_ORG_ID


def test_seating_an_operator_does_not_promote_anyone_else(founder):
    other = create_user("customer@example.test", "another-long-password")
    backfill_org_memberships()
    bootstrap_operator(founder["id"])

    principal = resolve_principal({"id": int(other["id"]), "email": "customer@example.test"})
    assert principal.org_id != GLOBAL_ORG_ID
