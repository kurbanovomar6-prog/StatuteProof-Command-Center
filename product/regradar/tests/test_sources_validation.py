"""
Tests for validate_source and load_sources in app/sources.py.

Covers all validation branches: missing keys, empty name/url, non-http url,
non-boolean enabled, invalid status, and the full load_sources() flow including
missing file, malformed JSON, non-list JSON, mixed valid/invalid entries.
No network calls. File operations use tmp_path.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from app.sources import validate_source, load_sources, get_enabled_sources


# ── helpers ──────────────────────────────────────────────────────────────────

def _valid_source(**overrides) -> dict:
    base = {
        "name": "VARA Official Site",
        "url": "https://vara.ae/",
        "jurisdiction": "AE",
        "category": "virtual-assets",
        "enabled": True,
    }
    base.update(overrides)
    return base


# ── validate_source — happy path ─────────────────────────────────────────────

def test_validate_source_returns_true_for_minimal_valid_source():
    assert validate_source(_valid_source()) is True


def test_validate_source_returns_true_with_valid_optional_status():
    src = _valid_source(status="active")
    assert validate_source(src) is True


def test_validate_source_returns_true_with_disabled_status():
    src = _valid_source(status="disabled", enabled=False)
    assert validate_source(src) is True


def test_validate_source_returns_true_with_candidate_status():
    src = _valid_source(status="candidate", enabled=False)
    assert validate_source(src) is True


def test_validate_source_returns_true_with_http_url():
    src = _valid_source(url="http://internal.example.com/")
    assert validate_source(src) is True


def test_validate_source_returns_true_when_status_is_absent():
    src = _valid_source()
    assert "status" not in src
    assert validate_source(src) is True


# ── validate_source — failure paths ──────────────────────────────────────────

def test_validate_source_returns_false_for_non_dict_input():
    assert validate_source("not a dict") is False  # type: ignore[arg-type]
    assert validate_source(None) is False  # type: ignore[arg-type]
    assert validate_source(42) is False  # type: ignore[arg-type]


def test_validate_source_returns_false_when_name_key_is_missing():
    src = _valid_source()
    del src["name"]
    assert validate_source(src) is False


def test_validate_source_returns_false_when_url_key_is_missing():
    src = _valid_source()
    del src["url"]
    assert validate_source(src) is False


def test_validate_source_returns_false_when_jurisdiction_key_is_missing():
    src = _valid_source()
    del src["jurisdiction"]
    assert validate_source(src) is False


def test_validate_source_returns_false_when_category_key_is_missing():
    src = _valid_source()
    del src["category"]
    assert validate_source(src) is False


def test_validate_source_returns_false_when_enabled_key_is_missing():
    src = _valid_source()
    del src["enabled"]
    assert validate_source(src) is False


def test_validate_source_returns_false_for_blank_name():
    src = _valid_source(name="   ")
    assert validate_source(src) is False


def test_validate_source_returns_false_for_empty_name():
    src = _valid_source(name="")
    assert validate_source(src) is False


def test_validate_source_returns_false_for_blank_url():
    src = _valid_source(url="   ")
    assert validate_source(src) is False


def test_validate_source_returns_false_for_url_without_http_scheme():
    src = _valid_source(url="ftp://vara.ae/")
    assert validate_source(src) is False


def test_validate_source_returns_false_for_relative_url():
    src = _valid_source(url="/vara/page")
    assert validate_source(src) is False


def test_validate_source_returns_false_when_enabled_is_string_true():
    src = _valid_source(enabled="true")
    assert validate_source(src) is False


def test_validate_source_returns_false_when_enabled_is_integer_one():
    src = _valid_source(enabled=1)
    assert validate_source(src) is False


def test_validate_source_returns_false_for_unrecognised_status():
    src = _valid_source(status="suspended_unofficial")
    assert validate_source(src) is False


def test_validate_source_returns_false_for_empty_status_string():
    src = _valid_source(status="")
    assert validate_source(src) is False


# ── load_sources ──────────────────────────────────────────────────────────────

def test_load_sources_returns_empty_list_when_file_does_not_exist(tmp_path):
    missing = tmp_path / "nonexistent.json"
    result = load_sources(missing)
    assert result == []


def test_load_sources_returns_empty_list_for_malformed_json(tmp_path):
    bad_file = tmp_path / "sources.json"
    bad_file.write_text("{not valid json", encoding="utf-8")
    result = load_sources(bad_file)
    assert result == []


def test_load_sources_returns_empty_list_when_top_level_is_not_array(tmp_path):
    obj_file = tmp_path / "sources.json"
    obj_file.write_text(json.dumps({"key": "value"}), encoding="utf-8")
    result = load_sources(obj_file)
    assert result == []


def test_load_sources_returns_valid_entries_only(tmp_path):
    entries = [
        _valid_source(name="Good Source A"),
        {"name": "Bad Source", "url": "not-a-url"},   # missing keys + bad url
        _valid_source(name="Good Source B", url="https://b.example.com/"),
    ]
    src_file = tmp_path / "sources.json"
    src_file.write_text(json.dumps(entries), encoding="utf-8")
    result = load_sources(src_file)
    names = [s["name"] for s in result]
    assert "Good Source A" in names
    assert "Good Source B" in names
    assert "Bad Source" not in names


def test_load_sources_returns_all_entries_when_all_valid(tmp_path):
    entries = [
        _valid_source(name="Source X"),
        _valid_source(name="Source Y", url="https://y.example.com/"),
    ]
    src_file = tmp_path / "sources.json"
    src_file.write_text(json.dumps(entries), encoding="utf-8")
    result = load_sources(src_file)
    assert len(result) == 2


def test_load_sources_returns_empty_list_for_empty_array(tmp_path):
    src_file = tmp_path / "sources.json"
    src_file.write_text("[]", encoding="utf-8")
    result = load_sources(src_file)
    assert result == []


def test_load_sources_preserves_file_order(tmp_path):
    entries = [
        _valid_source(name="First"),
        _valid_source(name="Second", url="https://second.example.com/"),
        _valid_source(name="Third", url="https://third.example.com/"),
    ]
    src_file = tmp_path / "sources.json"
    src_file.write_text(json.dumps(entries), encoding="utf-8")
    result = load_sources(src_file)
    assert [s["name"] for s in result] == ["First", "Second", "Third"]


# ── get_enabled_sources ───────────────────────────────────────────────────────

def test_get_enabled_sources_returns_only_enabled_entries(tmp_path):
    entries = [
        _valid_source(name="Enabled A", enabled=True),
        _valid_source(name="Disabled B", url="https://b.example.com/", enabled=False),
        _valid_source(name="Enabled C", url="https://c.example.com/", enabled=True),
    ]
    src_file = tmp_path / "sources.json"
    src_file.write_text(json.dumps(entries), encoding="utf-8")
    result = get_enabled_sources(src_file)
    names = [s["name"] for s in result]
    assert "Enabled A" in names
    assert "Enabled C" in names
    assert "Disabled B" not in names


def test_get_enabled_sources_returns_empty_list_when_none_enabled(tmp_path):
    entries = [
        _valid_source(name="Off A", enabled=False),
        _valid_source(name="Off B", url="https://b.example.com/", enabled=False),
    ]
    src_file = tmp_path / "sources.json"
    src_file.write_text(json.dumps(entries), encoding="utf-8")
    result = get_enabled_sources(src_file)
    assert result == []


# ── real config — URL stability guard ────────────────────────────────────────
#
# A frozen-version URL (e.g. Thomson Reuters "…-module-aml-ver3004-26" or VARA
# "…_VER20250519.pdf") keeps serving the OLD text after the next amendment, so
# an enabled source pinned to one silently stops seeing real changes — the one
# failure mode this product cannot allow. Disabled evidence-library entries may
# keep version-pinned URLs deliberately; only ENABLED sources are guarded.
# Added 2026-07-12 after AE-dfsa-aml-rulebook-module was found pinned to
# …-aml-ver3004-26 and repointed to the canonical current-version module URL.

_REAL_SOURCES_JSON = Path(__file__).resolve().parent.parent / "sources.json"

_FROZEN_VERSION_URL = re.compile(r"[-_/]ver\d", re.IGNORECASE)


def test_no_enabled_source_url_is_pinned_to_a_frozen_version():
    sources = json.loads(_REAL_SOURCES_JSON.read_text(encoding="utf-8"))
    pinned = [
        (source.get("source_id") or source.get("name"), source.get("url"))
        for source in sources
        if source.get("enabled") is True
        and _FROZEN_VERSION_URL.search(source.get("url", ""))
    ]
    assert pinned == [], (
        "Enabled sources must monitor stable index/current-version URLs, "
        f"not frozen version paths (goes silently stale on next amendment): {pinned}"
    )
