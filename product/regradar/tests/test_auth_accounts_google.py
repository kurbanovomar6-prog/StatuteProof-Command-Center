import os
from pathlib import Path

import pytest

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db
from app import auth
from app.auth import DuplicateEmailError, create_session, create_user, get_user_by_email, normalize_email, verify_password


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "auth.db"))
    for key in (
        "GOOGLE_OAUTH_CLIENT_ID",
        "GOOGLE_OAUTH_CLIENT_SECRET",
        "GOOGLE_OAUTH_REDIRECT_URI",
    ):
        monkeypatch.delenv(key, raising=False)
    yield tmp_path / "auth.db"


def test_duplicate_registration_blocks_case_and_whitespace_variants(isolated_db):
    first = create_user(" Name@Company.com ", "password-123", full_name="First User")

    assert first["email"] == "Name@Company.com"
    assert first["normalized_email"] == "name@company.com"

    with pytest.raises(DuplicateEmailError):
        create_user("name@company.com", "password-123")

    with pytest.raises(DuplicateEmailError):
        create_user("  NAME@COMPANY.COM  ", "password-123")


def test_login_lookup_is_case_insensitive_and_persistent(isolated_db):
    created = create_user("Pilot.User@Company.com", "password-123")

    loaded = get_user_by_email(" pilot.user@company.COM ")

    assert loaded is not None
    assert loaded["id"] == created["id"]
    assert loaded["normalized_email"] == "pilot.user@company.com"
    assert verify_password("password-123", loaded["password_hash"])

    session_id = create_session(int(loaded["id"]))
    assert session_id


def test_auth_schema_migration_is_idempotent(isolated_db):
    db.ensure_auth_tables()
    db.ensure_auth_tables()

    conn = db._connect()
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
        indexes = {row[1] for row in conn.execute("PRAGMA index_list(users)")}
    finally:
        conn.close()

    assert "normalized_email" in columns
    assert "email_verified" in columns
    assert "idx_users_normalized_email_unique" in indexes


def test_google_oauth_is_unavailable_without_env(isolated_db):
    assert auth.google_oauth_available() is False


def test_google_oauth_state_is_single_use(isolated_db, monkeypatch):
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:5001/api/auth/google/callback")

    state = auth.create_google_oauth_state(next_path="/app")
    auth_url = auth.google_oauth_authorization_url(state)

    assert "accounts.google.com" in auth_url
    assert "openid+email+profile" in auth_url
    assert f"state={state}" in auth_url

    first = auth.consume_google_oauth_state(state)
    second = auth.consume_google_oauth_state(state)

    assert first["next_path"] == "/app"
    assert second is None


def test_google_verified_email_creates_user_and_is_idempotent(isolated_db):
    user = auth.link_or_create_google_user(
        {
            "sub": "google-sub-1",
            "email": " Founder@Company.com ",
            "email_verified": True,
            "name": "Founder User",
        }
    )
    again = auth.link_or_create_google_user(
        {
            "sub": "google-sub-1",
            "email": "founder@company.com",
            "email_verified": True,
            "name": "Founder User",
        }
    )

    assert user["id"] == again["id"]
    assert user["normalized_email"] == "founder@company.com"
    assert user["auth_provider"] == "google"

    conn = db._connect()
    try:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        identity_count = conn.execute("SELECT COUNT(*) FROM oauth_identities").fetchone()[0]
    finally:
        conn.close()

    assert count == 1
    assert identity_count == 1


def test_google_verified_email_links_existing_password_user_without_duplicate(isolated_db):
    existing = create_user("mlro@company.com", "password-123")

    linked = auth.link_or_create_google_user(
        {
            "sub": "google-sub-2",
            "email": " MLRO@COMPANY.COM ",
            "email_verified": True,
            "name": "MLRO User",
        }
    )

    assert linked["id"] == existing["id"]
    assert linked["normalized_email"] == "mlro@company.com"
    assert linked["auth_provider"] == "password"

    conn = db._connect()
    try:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        identity = conn.execute("SELECT provider_user_id, user_id FROM oauth_identities").fetchone()
    finally:
        conn.close()

    assert count == 1
    assert identity["provider_user_id"] == "google-sub-2"
    assert identity["user_id"] == existing["id"]


def test_google_unverified_email_is_rejected(isolated_db):
    with pytest.raises(auth.OAuthAccountError):
        auth.link_or_create_google_user(
            {
                "sub": "google-sub-3",
                "email": "user@company.com",
                "email_verified": False,
                "name": "Unverified User",
            }
        )


def test_normalize_email_trims_and_lowercases_for_uniqueness():
    assert normalize_email("  Name@Company.COM  ") == "name@company.com"
