"""Fail-closed unit tests for app/tenancy.py — the cross-tenant leak guard.

app/tenancy.py is the single source of truth for "which custom sources may this
user see". Every failure branch in it MUST fail CLOSED: an unresolvable owner, a
non-int user id, or an unreadable ``sources.json`` degrades to "no custom source
visible / attributed to nobody", never to a leak. These branches are max
criticality — a regression that flips any of them to fail-OPEN would silently
reintroduce the cross-tenant private-source leak the module exists to prevent.

Each test drives a specific uncovered branch by monkeypatching
``app.source_intake.load_sources_json`` (imported lazily inside each primitive)
to crafted rows or to a raising stub, then asserts the DENY / empty outcome.
"""
from __future__ import annotations

import pytest

from app import tenancy


def _patch_sources(monkeypatch, rows):
    """Point the lazily-imported loader at ``rows``."""
    monkeypatch.setattr("app.source_intake.load_sources_json", lambda: list(rows))


def _patch_sources_raise(monkeypatch, exc=RuntimeError("unreadable sources.json")):
    """Force the loader to raise, simulating an unreadable/corrupt sources.json."""

    def _boom():
        raise exc

    monkeypatch.setattr("app.source_intake.load_sources_json", _boom)


# ── same_owner: coercion failure -> non-match (lines 40-41) ──────────────────


def test_same_owner_unparsable_owner_is_non_match():
    # An owner value that cannot be coerced to int must NOT match the caller.
    assert tenancy.same_owner("not-a-number", 7) is False


def test_same_owner_dict_owner_typeerror_is_non_match():
    # A structurally weird owner (int() raises TypeError) fails closed, no raise.
    assert tenancy.same_owner({"nested": 1}, 7) is False


def test_same_owner_unparsable_user_id_is_non_match():
    # A caller user_id that can't be coerced also fails closed rather than raising.
    assert tenancy.same_owner(7, "garbage") is False


def test_same_owner_matches_across_str_int_storage():
    # Positive control: string/int storage still resolves to a match (not a bug).
    assert tenancy.same_owner("7", 7) is True


# ── denied_custom_source_ids: non-int user_id -> deny all custom (lines 60-62) ─


def test_denied_custom_source_ids_non_int_user_denies_every_custom(monkeypatch):
    # user_id that can't be coerced -> uid=-1 -> nothing is attributed ->
    # every custom source is denied (fail closed), officials stay shared.
    _patch_sources(
        monkeypatch,
        [
            {"source_id": "custom-a", "custom": True, "owner_user_id": 7},
            {"source_id": "custom-b", "custom": True, "owner_user_id": 9},
            {"source_id": "official-x"},  # shared, never denied
        ],
    )
    denied = tenancy.denied_custom_source_ids("not-an-int")
    assert denied == {"custom-a", "custom-b"}
    assert "official-x" not in denied


def test_denied_custom_source_ids_none_user_denies_every_custom(monkeypatch):
    # None user id also coerces to the deny-all sentinel.
    _patch_sources(
        monkeypatch,
        [{"source_id": "custom-a", "custom": True, "owner_user_id": 7}],
    )
    assert tenancy.denied_custom_source_ids(None) == {"custom-a"}


# ── denied_custom_source_ids: unreadable list -> empty set (lines 73-74) ──────


def test_denied_custom_source_ids_unreadable_list_returns_empty(monkeypatch):
    # An unreadable sources.json must degrade to the SAME empty fallback every
    # caller uses (no per-source exclusion), never raise.
    _patch_sources_raise(monkeypatch)
    assert tenancy.denied_custom_source_ids(7) == set()


def test_denied_custom_source_ids_duplicate_attacker_row_fail_closes(monkeypatch):
    # Owner 7 owns custom-x, but an attacker-injected duplicate row claims owner 9.
    # ANY non-matching row denies the id, so even the true owner is fail-closed.
    _patch_sources(
        monkeypatch,
        [
            {"source_id": "custom-x", "custom": True, "owner_user_id": 7},
            {"source_id": "custom-x", "custom": True, "owner_user_id": 9},
        ],
    )
    assert "custom-x" in tenancy.denied_custom_source_ids(7)


# ── is_custom_source: empty id (line 90) and unreadable list (lines 99-100) ───


def test_is_custom_source_empty_id_is_false():
    assert tenancy.is_custom_source("") is False
    assert tenancy.is_custom_source(None) is False
    assert tenancy.is_custom_source("   ") is False


def test_is_custom_source_prefix_true_even_when_list_unreadable(monkeypatch):
    # A ``custom-`` prefixed id is custom even if sources.json can't be read —
    # this is what makes the delivery path fail CLOSED (never mistaken for
    # shareable official just because the list is unreadable).
    _patch_sources_raise(monkeypatch)
    assert tenancy.is_custom_source("custom-deadbeef") is True


def test_is_custom_source_non_prefixed_unreadable_list_is_false(monkeypatch):
    # A non-prefixed id whose row can't be read is treated as non-custom
    # (prefix already handled), reached via the except branch.
    _patch_sources_raise(monkeypatch)
    assert tenancy.is_custom_source("official-x") is False


def test_is_custom_source_resolvable_row_flagged_custom(monkeypatch):
    # Positive control: a non-prefixed id explicitly flagged custom resolves True.
    _patch_sources(
        monkeypatch,
        [{"source_id": "legacy-1", "custom": True, "owner_user_id": 7}],
    )
    assert tenancy.is_custom_source("legacy-1") is True


def test_is_custom_source_resolvable_official_row_is_false(monkeypatch):
    _patch_sources(monkeypatch, [{"source_id": "official-y"}])
    assert tenancy.is_custom_source("official-y") is False


# ── custom_source_owner: empty id early return (line 118) + ambiguity ─────────


def test_custom_source_owner_empty_id_returns_none():
    assert tenancy.custom_source_owner("") is None
    assert tenancy.custom_source_owner(None) is None


def test_custom_source_owner_single_owner_resolves(monkeypatch):
    # Positive control: exactly one distinct resolvable owner -> that owner.
    _patch_sources(
        monkeypatch,
        [{"source_id": "custom-x", "custom": True, "owner_user_id": "7"}],
    )
    assert tenancy.custom_source_owner("custom-x") == 7


def test_custom_source_owner_conflicting_owners_returns_none(monkeypatch):
    # Two distinct owners -> ambiguous -> deliver to nobody (fail closed).
    _patch_sources(
        monkeypatch,
        [
            {"source_id": "custom-x", "custom": True, "owner_user_id": 7},
            {"source_id": "custom-x", "custom": True, "owner_user_id": 9},
        ],
    )
    assert tenancy.custom_source_owner("custom-x") is None


def test_custom_source_owner_unresolvable_owner_returns_none(monkeypatch):
    # A single matching row whose owner can't be coerced -> saw_unresolvable ->
    # None (never misroute one tenant's private alert to another).
    _patch_sources(
        monkeypatch,
        [{"source_id": "custom-x", "custom": True, "owner_user_id": "not-int"}],
    )
    assert tenancy.custom_source_owner("custom-x") is None


def test_custom_source_owner_unreadable_list_returns_none(monkeypatch):
    _patch_sources_raise(monkeypatch)
    assert tenancy.custom_source_owner("custom-x") is None


# ── source_visible_to: fail-closed via denied set (lines 147-150) ─────────────


def test_source_visible_to_empty_source_id_is_visible():
    # An empty source_id can never be a denied custom source -> visible (the
    # module only ever ADDS denials; it never denies the empty/official case).
    assert tenancy.source_visible_to(7, "") is True
    assert tenancy.source_visible_to(7, None) is True


def test_source_visible_to_denies_other_tenants_custom(monkeypatch):
    # Owner 9's private custom source is NOT visible to user 7 (the core leak
    # guard): denied set contains it -> False.
    _patch_sources(
        monkeypatch,
        [{"source_id": "custom-x", "custom": True, "owner_user_id": 9}],
    )
    assert tenancy.source_visible_to(7, "custom-x") is False


def test_source_visible_to_owner_sees_own_custom(monkeypatch):
    # Positive control: the true owner still sees their own custom source.
    _patch_sources(
        monkeypatch,
        [{"source_id": "custom-x", "custom": True, "owner_user_id": 7}],
    )
    assert tenancy.source_visible_to(7, "custom-x") is True


def test_source_visible_to_official_source_visible_to_all(monkeypatch):
    _patch_sources(monkeypatch, [{"source_id": "official-x"}])
    assert tenancy.source_visible_to(7, "official-x") is True


def test_source_visible_to_non_int_user_hides_all_custom(monkeypatch):
    # Fail-closed composition: a non-int caller (uid=-1) is denied every custom
    # source, so even a normally-owned custom id is hidden.
    _patch_sources(
        monkeypatch,
        [{"source_id": "custom-x", "custom": True, "owner_user_id": 7}],
    )
    assert tenancy.source_visible_to("garbage", "custom-x") is False


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
