"""Per-source cadence mechanism (check_interval_minutes) — app/scheduler.py.

Why this exists: UAE targeted-financial-sanctions freeze obligations are
effectively immediate/24h, so the EOCN/IEC sources must be re-checked every
4-6 hours even when the full fleet cycle is slower. The mechanism must NOT
change the cadence of any source that does not opt in.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.scheduler import (
    _CRITICAL_INTERVAL_MINUTES,
    _MIN_CUSTOM_INTERVAL_MINUTES,
    _cadence_key,
    _due_custom_sources,
    _next_sleep_minutes,
    get_custom_interval_minutes,
    get_sources_with_custom_interval,
)

SOURCES_JSON = Path(__file__).resolve().parents[1] / "sources.json"

# The exact opt-in set — a new source appearing here must be a deliberate
# decision, and nothing may silently raise the whole fleet's cadence.
EXPECTED_CADENCE_SOURCES = {
    "AE-eocn-tfs": 240,
    "AE-uaeiec-en-us-laws-regulations-listing-00a71863": 240,
    "AE-eocn-laws-regulations-en": 360,
    "AE-eocn-news-en": 360,
    "AE-uaeiec-news-listing-next": 360,
    # 2026-07-18: UN consolidated list joins the sanctions-urgency band (the
    # UAE 24h freeze obligation keys on these designations).
    "AE-un-consolidated-sanctions-xml": 240,
    # 2026-07-18: OFSI is a cadence CAP, not an urgency opt-in — the 5.4 MB
    # consolidated-list fetch declares a 12h appetite so it can never ride a
    # sanctions-band cadence. NOTE (honest limitation): with the current
    # hourly fleet cycle (deploy: run.py watch --interval 60) a full sweep
    # still fetches every enabled source, so check_interval_minutes only
    # ACCELERATES sources relative to a slower fleet interval; the cap takes
    # real effect only when the fleet interval exceeds it.
    "AE-uk-ofsi-consolidated-list": 720,
}

# Sources whose declared cadence is a bandwidth/appetite CAP (slower than the
# sanctions-urgency band) rather than an urgency opt-in.
CADENCE_CAP_SOURCES = {"AE-uk-ofsi-consolidated-list"}


# ── get_custom_interval_minutes ──────────────────────────────────────────────

def test_no_field_means_fleet_default():
    assert get_custom_interval_minutes({"source_id": "x"}) is None


def test_valid_interval_returned_as_int():
    assert get_custom_interval_minutes({"check_interval_minutes": 240}) == 240


def test_string_integer_accepted():
    assert get_custom_interval_minutes({"check_interval_minutes": "360"}) == 360


@pytest.mark.parametrize("bad", [0, -5, "soon", None, [], {}])
def test_invalid_values_ignored(bad):
    assert get_custom_interval_minutes({"check_interval_minutes": bad}) is None


def test_below_floor_clamped_up():
    assert (
        get_custom_interval_minutes({"check_interval_minutes": 5})
        == _MIN_CUSTOM_INTERVAL_MINUTES
    )


def test_non_dict_source_ignored():
    assert get_custom_interval_minutes(None) is None  # type: ignore[arg-type]


# ── _due_custom_sources ──────────────────────────────────────────────────────

def _src(url: str, minutes: int | None) -> dict:
    entry = {"url": url, "name": url, "enabled": True}
    if minutes is not None:
        entry["check_interval_minutes"] = minutes
    return entry


def test_never_run_source_is_due_immediately():
    src = _src("https://example.gov.ae/tfs", 240)
    assert _due_custom_sources([src], {}, now_monotonic=10_000.0) == [src]


def test_recently_run_source_is_not_due():
    src = _src("https://example.gov.ae/tfs", 240)
    last = {_cadence_key(src): 10_000.0}
    # 239 minutes later — one minute short of the cadence.
    assert _due_custom_sources([src], last, 10_000.0 + 239 * 60) == []


def test_source_becomes_due_after_interval_elapses():
    src = _src("https://example.gov.ae/tfs", 240)
    last = {_cadence_key(src): 10_000.0}
    assert _due_custom_sources([src], last, 10_000.0 + 240 * 60) == [src]


def test_source_without_field_never_due():
    src = _src("https://example.gov.ae/laws", None)
    assert _due_custom_sources([src], {}, 10_000.0) == []


def test_mixed_sources_only_elapsed_returned():
    fast = _src("https://example.gov.ae/fast", 240)
    slow = _src("https://example.gov.ae/slow", 360)
    t0 = 50_000.0
    last = {_cadence_key(fast): t0, _cadence_key(slow): t0}
    due = _due_custom_sources([fast, slow], last, t0 + 250 * 60)
    assert due == [fast]


# ── _next_sleep_minutes ──────────────────────────────────────────────────────

def test_sleep_unchanged_without_optins():
    # Fleet-only deployments keep the exact historical behaviour.
    assert _next_sleep_minutes(60, has_critical=False, custom_sources=[]) == 60
    assert (
        _next_sleep_minutes(60, has_critical=True, custom_sources=[])
        == _CRITICAL_INTERVAL_MINUTES
    )


def test_sleep_honours_smallest_custom_cadence():
    sources = [_src("a", 360), _src("b", 240)]
    assert _next_sleep_minutes(1440, has_critical=False, custom_sources=sources) == 240


def test_sleep_never_below_one_minute():
    assert _next_sleep_minutes(0, has_critical=False, custom_sources=[]) == 1


def test_sleep_ignores_invalid_custom_values():
    sources = [_src("a", None)]
    sources[0]["check_interval_minutes"] = "not-a-number"
    assert _next_sleep_minutes(90, has_critical=False, custom_sources=sources) == 90


# ── get_sources_with_custom_interval (isolated registry file) ────────────────

def test_loader_filters_enabled_and_valid(monkeypatch, tmp_path):
    registry = [
        {"url": "https://a.example", "enabled": True, "check_interval_minutes": 240},
        {"url": "https://b.example", "enabled": False, "check_interval_minutes": 240},
        {"url": "https://c.example", "enabled": True},
        {"url": "https://d.example", "enabled": True, "check_interval_minutes": "bad"},
    ]
    path = tmp_path / "sources.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    import app.scheduler as scheduler
    monkeypatch.setattr(scheduler, "_SOURCES_JSON", path)

    matched = scheduler.get_sources_with_custom_interval()
    assert [m["url"] for m in matched] == ["https://a.example"]


def test_loader_survives_missing_file(monkeypatch, tmp_path):
    import app.scheduler as scheduler
    monkeypatch.setattr(scheduler, "_SOURCES_JSON", tmp_path / "missing.json")
    assert scheduler.get_sources_with_custom_interval() == []


# ── real registry contract (sources.json in this repo) ──────────────────────

def test_sanctions_sources_have_4_to_6_hour_cadence():
    data = json.loads(SOURCES_JSON.read_text(encoding="utf-8"))
    declared = {
        s.get("source_id"): s.get("check_interval_minutes")
        for s in data
        if isinstance(s, dict) and "check_interval_minutes" in s
    }
    assert declared == EXPECTED_CADENCE_SOURCES
    for source_id, minutes in declared.items():
        if source_id in CADENCE_CAP_SOURCES:
            # Appetite caps sit ABOVE the urgency band by definition.
            assert int(minutes) > 360, source_id
            continue
        assert 240 <= int(minutes) <= 360, source_id
    # Every opted-in source must be enabled — cadence on a disabled source
    # is a configuration lie.
    by_id = {s.get("source_id"): s for s in data if isinstance(s, dict)}
    for source_id in EXPECTED_CADENCE_SOURCES:
        assert by_id[source_id]["enabled"] is True, source_id


def test_fleet_default_untouched():
    """No source outside the explicit sanctions set declares a cadence."""
    data = json.loads(SOURCES_JSON.read_text(encoding="utf-8"))
    opted_in = {
        s.get("source_id")
        for s in data
        if isinstance(s, dict) and "check_interval_minutes" in s
    }
    assert opted_in == set(EXPECTED_CADENCE_SOURCES)
