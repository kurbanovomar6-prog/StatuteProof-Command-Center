"""
Enforcement-monitoring feature: honest coverage of regulator enforcement pages.

Central discipline (see project CLAUDE.md / evidence-first rule): a source is
counted in the customer-facing enforcement number ONLY when it is genuinely
fresh-alert eligible (reachable + parseable, verified). Bot-walled / JS-only /
proxy-only enforcement pages are wired in their honest mode (candidate /
remediation) and MUST NOT inflate the count.

These tests assert:
  * the discovery WIRE_FRESH_ALERT sources are alert-eligible AND counted;
  * the candidate / remediation enforcement sources are wired but NOT counted;
  * sources.json stays schema-valid (no enforcement entry drops on load);
  * the customer-facing enforcement description passes the legal-safety guard.

No network calls. Synthetic cases use tmp_path.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from app.legal_safety import contains_forbidden_claim, find_forbidden_claims
from app.source_summary import (
    ENFORCEMENT_FEATURE_DESCRIPTION,
    build_enforcement_summary,
)
from app.sources import load_sources, validate_source

_REAL_SOURCES_JSON = Path(__file__).resolve().parent.parent / "sources.json"

# Discovery verdicts (see the build task). Source ids as wired in sources.json.
_WIRE_FRESH_ALERT_IDS = {
    "AE-vara-enforcement",
    "AE-vara-regulatory-notices-and-enforcement-index",
}
_NON_FRESH_ENFORCEMENT_IDS = {
    "AE-dfsa-regulatory-actions-current",       # REMEDIATION_PROXY
    "AE-dfsa-what-we-do-enforcement-1a837c50",  # REMEDIATION_PROXY
    "AE-cbuae-enforcement",                      # REMEDIATION_PROXY (added)
    "AE-adgm-fsra-regulatory-alerts",           # CANDIDATE
}


def _real_sources() -> list[dict]:
    return json.loads(_REAL_SOURCES_JSON.read_text(encoding="utf-8"))


def _by_id(sources: list[dict]) -> dict[str, dict]:
    return {s.get("source_id"): s for s in sources if s.get("source_id")}


# ── real config: the enforcement feature is wired & honest ───────────────────

def test_wire_fresh_alert_sources_are_alert_eligible_and_counted():
    summary = build_enforcement_summary("AE")
    fresh_ids = set(summary["fresh_alert_source_ids"])
    assert _WIRE_FRESH_ALERT_IDS <= fresh_ids, (
        "Both verified VARA enforcement sources must be counted as fresh-alert "
        f"enforcement coverage. Got: {sorted(fresh_ids)}"
    )
    assert summary["fresh_alert_count"] == len(fresh_ids)
    assert summary["fresh_alert_count"] >= 2


def test_wire_fresh_alert_sources_carry_fresh_alert_mode_in_config():
    by_id = _by_id(_real_sources())
    for sid in _WIRE_FRESH_ALERT_IDS:
        src = by_id[sid]
        assert src["enabled"] is True
        assert src["monitoring_mode"] == "fresh_alert"
        assert src["alert_eligible"] is True
        assert src.get("enforcement_feature") is True


def test_non_fresh_enforcement_sources_are_wired_but_not_counted():
    by_id = _by_id(_real_sources())
    summary = build_enforcement_summary("AE")
    fresh_ids = set(summary["fresh_alert_source_ids"])
    for sid in _NON_FRESH_ENFORCEMENT_IDS:
        src = by_id[sid]
        # Tagged into the feature (coverage matrix is complete)…
        assert src.get("enforcement_feature") is True, f"{sid} not tagged"
        # …but honest mode, alert-ineligible, and NOT in the counted set.
        assert src["monitoring_mode"] in {"candidate", "remediation"}, sid
        assert src.get("alert_eligible") in (False, None), sid
        assert sid not in fresh_ids, f"{sid} must NOT inflate the fresh count"


def test_enforcement_matrix_partitions_enabled_tagged_sources():
    summary = build_enforcement_summary("AE")
    total = (
        summary["fresh_alert_count"]
        + summary["remediation_count"]
        + summary["candidate_count"]
        + summary["evidence_library_count"]
    )
    assert total == summary["enforcement_source_count"]
    # In the test env (no proxy configured) the remediation + candidate sources
    # stay uncounted, so at least these are present in their honest buckets.
    assert summary["remediation_count"] >= 2
    assert summary["candidate_count"] >= 1


def test_cbuae_enforcement_source_added_in_honest_remediation_mode():
    by_id = _by_id(_real_sources())
    src = by_id["AE-cbuae-enforcement"]
    assert src["url"].startswith("https://www.centralbank.ae/")
    assert "enforcement" in src["url"]
    assert src["monitoring_mode"] == "remediation"
    assert src.get("alert_eligible") in (False, None)
    assert src.get("proxy_remediation") is True  # centralbank.ae is proxy-only
    assert src.get("enforcement_feature") is True


# ── schema validity: nothing drops on load ───────────────────────────────────

def test_all_enforcement_feature_sources_pass_validation():
    for src in _real_sources():
        if src.get("enforcement_feature") is True:
            assert validate_source(src) is True, src.get("source_id")


def test_sources_json_loads_without_dropping_entries():
    raw = _real_sources()
    loaded = load_sources(_REAL_SOURCES_JSON)
    assert len(loaded) == len(raw), (
        "An enforcement edit made an entry fail validation and get dropped."
    )


# ── synthetic: verified-count discipline (mirrors proxy_remediation pattern) ──

def _write_sources(tmp_path: Path, sources: list[dict]) -> Path:
    (tmp_path / "sources.json").write_text(json.dumps(sources), encoding="utf-8")
    runs = tmp_path / "data" / "source_runs"
    runs.mkdir(parents=True, exist_ok=True)
    return tmp_path


def test_synthetic_only_verified_fresh_enforcement_is_counted(tmp_path):
    sources = [
        {
            "name": "VARA Enforcement", "url": "https://www.vara.ae/en/enforcement/",
            "jurisdiction": "AE", "category": "enforcement", "enabled": True,
            "source_id": "x-fresh", "enforcement_feature": True,
            "monitoring_mode": "fresh_alert", "alert_eligible": True,
        },
        {
            "name": "DFSA Enforcement (proxy-only)",
            "url": "https://www.dfsa.ae/what-we-do/enforcement",
            "jurisdiction": "AE", "category": "enforcement", "enabled": True,
            "source_id": "x-remediation", "enforcement_feature": True,
            "monitoring_mode": "remediation", "alert_eligible": False,
        },
        {
            "name": "ADGM Enforcement (JS-only)",
            "url": "https://www.adgm.com/fsra/enforcement",
            "jurisdiction": "AE", "category": "enforcement", "enabled": True,
            "source_id": "x-candidate", "enforcement_feature": True,
            "monitoring_mode": "candidate", "alert_eligible": False,
        },
        # A non-enforcement fresh source must not leak into the enforcement count.
        {
            "name": "VARA Rulebook", "url": "https://rulebooks.vara.ae/x",
            "jurisdiction": "AE", "category": "rulebook", "enabled": True,
            "source_id": "x-other-fresh",
            "monitoring_mode": "fresh_alert", "alert_eligible": True,
        },
    ]
    base = _write_sources(tmp_path, sources)
    summary = build_enforcement_summary("AE", base_dir=base)
    assert summary["fresh_alert_count"] == 1
    assert summary["fresh_alert_source_ids"] == ["x-fresh"]
    assert summary["remediation_count"] == 1
    assert summary["candidate_count"] == 1
    assert summary["enforcement_source_count"] == 3


def test_synthetic_proxy_enforcement_uncounted_until_verified_run(monkeypatch, tmp_path):
    """A proxy-remediation enforcement source must not enter the count on config
    alone — only after a recent successful production run is recorded."""
    from datetime import datetime, timezone

    # The verified-count predicate only accepts records recent enough to
    # evidence the CURRENT configuration, so use a current-cycle timestamp.
    def _recent_ts() -> str:
        return datetime.now(timezone.utc).isoformat()

    url = "https://rulebook.centralbank.ae/en/enforcement/x"
    sources = [
        {
            "name": "CBUAE Enforcement", "url": url, "jurisdiction": "AE",
            "category": "enforcement", "enabled": True, "source_id": "x-proxy",
            "enforcement_feature": True, "monitoring_mode": "remediation",
            "alert_eligible": False, "proxy_remediation": True,
        },
    ]
    base = _write_sources(tmp_path, sources)
    runs_file = base / "data" / "source_runs" / "source_runs.jsonl"

    monkeypatch.setenv("STATUTEPROOF_FETCH_PROXY", "http://proxy.example:8080")
    monkeypatch.delenv("STATUTEPROOF_PROXY_HOSTS", raising=False)

    summary = build_enforcement_summary("AE", base_dir=base)
    assert summary["fresh_alert_count"] == 0
    assert summary["remediation_count"] == 1

    runs_file.write_text(
        json.dumps({
            "url": url, "official_url": url, "market": "AE",
            "change_status": "NO_CHANGE", "timestamp_utc": _recent_ts(),
        }) + "\n",
        encoding="utf-8",
    )
    summary = build_enforcement_summary("AE", base_dir=base)
    assert summary["fresh_alert_count"] == 1


# ── legal safety: no over-claim in the customer-facing description ────────────

def test_enforcement_description_passes_legal_safety_guard():
    assert not contains_forbidden_claim(ENFORCEMENT_FEATURE_DESCRIPTION), (
        find_forbidden_claims(ENFORCEMENT_FEATURE_DESCRIPTION)
    )


def test_enforcement_description_does_not_promise_total_coverage():
    lowered = ENFORCEMENT_FEATURE_DESCRIPTION.lower()
    for banned in ("never miss", "all enforcement actions", "every enforcement",
                   "guarantee", "complete coverage"):
        assert banned not in lowered, f"over-claim phrase present: {banned!r}"
    assert "not legal advice" in lowered
