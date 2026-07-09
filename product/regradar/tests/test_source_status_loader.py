"""
Regression tests for the source-status validation gate in ``app/sources.py``.

Defect being guarded: the loader validated each source's ``status`` against a
hard allowed-set and SKIPPED any source whose status was not in it. The real
``sources.json`` contains status values that were absent from that set, so a
large share of records were silently dropped at load time.

These tests pin the contract from the *real* data file:

1. Every distinct ``status`` value actually present in the repo ``sources.json``
   must pass ``validate_source`` — i.e. no source is dropped for its status.
2. ``load_sources`` on the real file must not drop any entry for a status
   reason (parsed count == returned count, given all entries have required keys).
3. A clearly-bogus status must still be rejected — validation is enumerated,
   not weakened to "accept anything".

No network calls. Reads the loader's own default path, which points at the
repo ``sources.json`` shipped alongside the module.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from app import sources as sources_module
from app.sources import load_sources, validate_source

# The real, shipped sources.json — the loader's own default target.
REPO_SOURCES_PATH: Path = sources_module._DEFAULT_PATH


def _valid_source(**overrides) -> dict:
    """A minimal source that passes every non-status check."""
    base = {
        "name": "Test Regulator Source",
        "url": "https://regulator.example.gov/",
        "jurisdiction": "AE",
        "category": "banking",
        "enabled": False,
    }
    base.update(overrides)
    return base


def _distinct_statuses_in_repo() -> list[str]:
    """Every distinct non-null ``status`` value present in the real file."""
    raw = REPO_SOURCES_PATH.read_text(encoding="utf-8")
    entries = json.loads(raw)
    statuses = {
        entry.get("status")
        for entry in entries
        if isinstance(entry, dict) and entry.get("status") is not None
    }
    return sorted(statuses)


# ── sanity: the real file exists and has statuses to check ─────────────────────

def test_repo_sources_file_exists_and_has_statuses():
    assert REPO_SOURCES_PATH.exists(), (
        f"expected real sources.json at {REPO_SOURCES_PATH}"
    )
    statuses = _distinct_statuses_in_repo()
    assert statuses, "repo sources.json should contain at least one status value"


# ── core contract: every real status must be accepted ──────────────────────────

@pytest.mark.parametrize("status", _distinct_statuses_in_repo())
def test_every_real_status_value_passes_validation(status):
    """
    No source may be dropped because of its ``status``. Each distinct status
    present in the shipped sources.json must validate when all other required
    fields are well-formed.
    """
    src = _valid_source(status=status)
    assert validate_source(src) is True, (
        f"status {status!r} from sources.json was rejected by validate_source"
    )


def test_all_real_statuses_are_in_the_allowed_set():
    """Belt-and-suspenders: the allowed set is a superset of what's shipped."""
    present = set(_distinct_statuses_in_repo())
    allowed = sources_module._VALID_STATUSES
    missing = present - allowed
    assert not missing, (
        f"these shipped statuses are not in _VALID_STATUSES and would be "
        f"dropped at load: {sorted(missing)}"
    )


def test_load_sources_drops_no_entry_for_status_reason():
    """
    Loading the real file must not silently drop entries. Every entry in the
    shipped file has the required keys, so the parsed count and the returned
    count must be equal — proving the status gate no longer culls records.
    """
    raw = REPO_SOURCES_PATH.read_text(encoding="utf-8")
    entries = json.loads(raw)
    parsed_count = len(entries)

    loaded = load_sources(REPO_SOURCES_PATH)

    assert len(loaded) == parsed_count, (
        f"load_sources returned {len(loaded)} of {parsed_count} entries — "
        f"{parsed_count - len(loaded)} were dropped at load"
    )


# ── negative contract: validation is enumerated, not disabled ──────────────────

def test_clearly_bogus_status_is_still_rejected():
    src = _valid_source(status="totally_made_up_status")
    assert validate_source(src) is False


def test_another_bogus_status_is_still_rejected():
    src = _valid_source(status="not_a_real_status_value_xyz")
    assert validate_source(src) is False
