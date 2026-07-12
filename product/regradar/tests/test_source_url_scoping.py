"""Custom-source add must not expose a cross-tenant URL-existence oracle.

Regression (user-data-scoping): the add-source flow used the GLOBAL
``source_url_exists`` check, so a 409 "already in the source list" response
revealed that another tenant had added a private custom URL (user A learns user
B monitors URL X). ``source_url_exists_for_user`` scopes the check to the caller
— official sources plus the caller's OWN custom sources — so another tenant's
private custom URL is never revealed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app.source_tester as source_tester
from app.source_tester import source_url_exists, source_url_exists_for_user


USER_A = 101
USER_B = 202

OFFICIAL_URL = "https://rulebook.centralbank.ae/en"
USER_B_CUSTOM_URL = "https://private-portal.example.gov/reg"
UNKNOWN_URL = "https://nobody-added-this.example.com/x"


def _seed_sources(tmp_path, monkeypatch) -> Path:
    entries = [
        # Official / built-in source (no custom flag, no owner) — visible to all.
        {"source_id": "AE-cbuae", "url": OFFICIAL_URL, "enabled": True},
        # A PRIVATE custom source owned by user B.
        {
            "source_id": "custom-deadbeef",
            "url": USER_B_CUSTOM_URL,
            "custom": True,
            "owner_user_id": USER_B,
        },
    ]
    path = tmp_path / "sources.json"
    path.write_text(json.dumps(entries), encoding="utf-8")
    monkeypatch.setattr(source_tester, "_SOURCES_PATH", path)
    return path


def test_another_users_custom_url_is_not_revealed(tmp_path, monkeypatch):
    _seed_sources(tmp_path, monkeypatch)
    # The GLOBAL check is the leak vector: it returns True for B's private URL.
    assert source_url_exists(USER_B_CUSTOM_URL) is True
    # The SCOPED check must NOT reveal it to user A — the oracle is closed.
    assert source_url_exists_for_user(USER_B_CUSTOM_URL, USER_A) is False
    # The owner (user B) still sees their own duplicate, as expected.
    assert source_url_exists_for_user(USER_B_CUSTOM_URL, USER_B) is True


def test_official_source_is_visible_to_every_tenant(tmp_path, monkeypatch):
    _seed_sources(tmp_path, monkeypatch)
    assert source_url_exists_for_user(OFFICIAL_URL, USER_A) is True
    assert source_url_exists_for_user(OFFICIAL_URL, USER_B) is True
    assert source_url_exists_for_user(OFFICIAL_URL, None) is True


def test_unknown_url_is_absent_for_everyone(tmp_path, monkeypatch):
    _seed_sources(tmp_path, monkeypatch)
    assert source_url_exists_for_user(UNKNOWN_URL, USER_A) is False
    assert source_url_exists_for_user(UNKNOWN_URL, None) is False


def test_trailing_slash_is_normalized_in_scoped_check(tmp_path, monkeypatch):
    _seed_sources(tmp_path, monkeypatch)
    assert source_url_exists_for_user(OFFICIAL_URL + "/", USER_A) is True
    # Still not revealed even with a normalization variant.
    assert source_url_exists_for_user(USER_B_CUSTOM_URL + "/", USER_A) is False


def test_scoped_check_fails_soft_on_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(source_tester, "_SOURCES_PATH", tmp_path / "does-not-exist.json")
    assert source_url_exists_for_user(OFFICIAL_URL, USER_A) is False
