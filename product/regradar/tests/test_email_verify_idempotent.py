"""Email verification is idempotent against mail-scanner token burn.

Corporate mail security scanners (Microsoft Safe Links, Proofpoint URL Defense)
PRE-FETCH links in email before the human clicks. That first fetch consumes the
single-use verification token AND marks the user verified. When the real human
then clicks, consume_verification_token returns None (used_at is set) and the
handler shows "Verification link is invalid or has expired" — a scary error for
a user whose email is, in fact, already verified. Our ICP (banks, VASPs) run
exactly these scanners.

The idempotent resolver treats a re-click of an already-consumed token whose
user is already verified as success, without weakening the single-use guarantee
for genuinely bad/expired/unverified tokens.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "verify.db"))
    yield tmp_path / "verify.db"


def _user(email: str) -> int:
    from app.auth import create_user

    return int(create_user(email, "password-123")["id"])


def test_scanner_burns_token_then_human_click_still_resolves(isolated_db):
    from app.auth import (
        generate_verification_token,
        consume_verification_token,
        mark_email_verified,
        verified_user_for_consumed_token,
    )

    user_id = _user("mlro@bank.ae")
    token = generate_verification_token(user_id)

    # Scanner pre-fetch: consumes the token and the handler marks verified.
    assert consume_verification_token(token) == user_id
    mark_email_verified(user_id)

    # Human click: the single-use token is now spent.
    assert consume_verification_token(token) is None

    # Idempotent resolver: the token belongs to an already-verified user, so
    # this is success, not an "invalid link" error.
    assert verified_user_for_consumed_token(token) == user_id


def test_unknown_and_unverified_tokens_do_not_resolve(isolated_db):
    from app.auth import (
        generate_verification_token,
        verified_user_for_consumed_token,
    )

    # Garbage token → no idempotent success.
    assert verified_user_for_consumed_token("not-a-real-token") is None

    # A freshly issued, UNused token whose user is not yet verified must NOT
    # resolve via the idempotent path (that path is only for consumed tokens of
    # already-verified users — normal consume handles the fresh case).
    user_id = _user("cco@vasp.ae")
    token = generate_verification_token(user_id)
    assert verified_user_for_consumed_token(token) is None
