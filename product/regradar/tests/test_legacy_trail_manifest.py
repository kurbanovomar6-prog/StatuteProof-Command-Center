"""The 99% of the trail the hash chain does not cover.

`verify_chain` starts at the first record carrying a `record_hash` and skips
everything before it. Measured 2026-07-25 on the live trail: 1430 records, 24
chained — so 1406 could be deleted, reordered, or have a line lifted from the
middle, and the integrity verifier said "Hash chain: intact" and nothing else.
Silence there reads as all-clear, which is the worst possible default for a tool
whose entire job is to say whether the evidence store is sound.

The manifest is a digest over the ordered identities of that block. What it proves
is narrow and the tests below pin both halves: it detects any change SINCE sealing,
and it makes no claim at all about the block before that moment.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.legacy_trail_manifest import (  # noqa: E402
    compute_digest,
    legacy_records,
    seal,
    verify,
)


def _legacy(source_id: str, run_id: str) -> dict:
    """A pre-chain record: no record_hash, which is what makes it legacy."""
    return {
        "source_id": source_id,
        "run_id": run_id,
        "checked_at_utc": "2026-06-01T00:00:00Z",
        "normalized_hash": f"hash-{run_id}",
        "change_status": "UNCHANGED",
    }


def _chained(source_id: str, run_id: str) -> dict:
    record = _legacy(source_id, run_id)
    record["record_hash"] = f"rh-{run_id}"
    return record


@pytest.fixture()
def trail(tmp_path, monkeypatch):
    """Point the manifest at a temp tree; the autouse isolation fixture keeps the
    working store out of reach anyway, this makes it explicit."""
    import app.legacy_trail_manifest as mod

    monkeypatch.setattr(mod, "_BASE_DIR", tmp_path)
    (tmp_path / "data" / "source_runs").mkdir(parents=True)
    return tmp_path


# ── what the block IS ────────────────────────────────────────────────────────


def test_the_legacy_block_is_everything_before_the_chain_starts():
    records = [_legacy("AE-a", "r1"), _legacy("AE-b", "r2"), _chained("AE-c", "r3")]

    assert [r["run_id"] for r in legacy_records(records)] == ["r1", "r2"]


def test_a_fully_chained_trail_has_no_legacy_block():
    assert legacy_records([_chained("AE-a", "r1"), _chained("AE-b", "r2")]) == []


# ── the guarantee ────────────────────────────────────────────────────────────


def test_an_unsealed_block_is_reported_as_unprotected_not_as_fine(trail):
    records = [_legacy("AE-a", "r1"), _legacy("AE-b", "r2"), _chained("AE-c", "r3")]

    result = verify(records, base_dir=trail)

    assert result["status"] == "unsealed"
    assert result["ok"] is False
    assert "no manifest" in result["detail"]


def test_a_sealed_block_verifies_unchanged(trail):
    records = [_legacy("AE-a", "r1"), _legacy("AE-b", "r2"), _chained("AE-c", "r3")]
    seal(records, base_dir=trail)

    result = verify(records, base_dir=trail)

    assert result["status"] == "intact"
    assert result["record_count"] == 2


def test_deleting_a_legacy_record_is_detected(trail):
    records = [_legacy("AE-a", "r1"), _legacy("AE-b", "r2"), _chained("AE-c", "r3")]
    seal(records, base_dir=trail)

    tampered = [records[0], records[2]]  # r2 lifted out
    result = verify(tampered, base_dir=trail)

    assert result["ok"] is False
    assert result["status"] == "count"


def test_inserting_a_record_is_detected(trail):
    records = [_legacy("AE-a", "r1"), _chained("AE-c", "r3")]
    seal(records, base_dir=trail)

    tampered = [records[0], _legacy("AE-x", "forged"), records[1]]
    result = verify(tampered, base_dir=trail)

    assert result["ok"] is False
    assert result["status"] == "count"


def test_reordering_is_detected_even_though_the_count_is_unchanged(trail):
    """The subtle one: the same records, a different sequence. A set-based digest
    would pass this, which is why order is folded into the hash."""
    records = [_legacy("AE-a", "r1"), _legacy("AE-b", "r2"), _chained("AE-c", "r3")]
    seal(records, base_dir=trail)

    tampered = [records[1], records[0], records[2]]
    result = verify(tampered, base_dir=trail)

    assert result["ok"] is False
    assert result["status"] == "digest"


def test_editing_a_record_identity_is_detected(trail):
    records = [_legacy("AE-a", "r1"), _legacy("AE-b", "r2"), _chained("AE-c", "r3")]
    seal(records, base_dir=trail)

    edited = dict(records[1])
    edited["normalized_hash"] = "hash-swapped"
    result = verify([records[0], edited, records[2]], base_dir=trail)

    assert result["ok"] is False
    assert result["status"] == "digest"


def test_order_changes_the_digest(trail):
    a, b = _legacy("AE-a", "r1"), _legacy("AE-b", "r2")

    assert compute_digest([a, b]) != compute_digest([b, a])


# ── failure modes ────────────────────────────────────────────────────────────


def test_a_corrupt_manifest_fails_rather_than_passing(trail):
    """A seal that cannot be read must never read as a passing seal."""
    records = [_legacy("AE-a", "r1"), _chained("AE-c", "r3")]
    seal(records, base_dir=trail)
    path = trail / "data" / "source_runs" / "legacy_trail_manifest.json"
    path.write_text('{"method": "something-else", "record_count": 1}', encoding="utf-8")

    result = verify(records, base_dir=trail)

    assert result["ok"] is False
    assert result["status"] == "unreadable"


def test_the_seal_records_when_it_was_taken(trail):
    """The date is the whole caveat: the guarantee runs forward from it."""
    payload = seal([_legacy("AE-a", "r1"), _chained("AE-c", "r3")], base_dir=trail)

    assert payload["sealed_at"]
    assert "before that moment" in payload["covers"]
