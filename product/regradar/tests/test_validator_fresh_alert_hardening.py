from __future__ import annotations

import json
from pathlib import Path

from tools import (
    validate_daily_checkable_sources,
    validate_fresh_signal_sources,
    validate_source_monitoring_modes,
)


def _write_sources(tmp_path: Path, monkeypatch, module, sources: list[dict]) -> None:
    path = tmp_path / "sources.json"
    path.write_text(json.dumps(sources), encoding="utf-8")
    monkeypatch.setattr(module, "SOURCES", path)


def _fresh_source(**overrides) -> dict:
    source = {
        "source_id": "AE-test-fresh-alert",
        "name": "Test Fresh Alert Source",
        "url": "https://regulator.gov.ae/regulations/updates",
        "enabled": True,
        "jurisdiction": "AE",
        "monitoring_mode": "fresh_alert",
        "alert_eligible": True,
        "last_monitor_status": "MONITOR_OK",
        "proof_path": "data/source_snapshots/proof.json",
        "normalized_text_path": "data/source_snapshots/normalized.txt",
        "normalized_hash": "abc123",
        "baseline_runs_completed": 2,
        "baseline_runs_required": 2,
        "recommended_check_frequency": "daily",
        "fresh_signal_type": "regulatory_update_listing",
        "expected_update_pattern": "Checked daily for new regulatory updates.",
        "customer_alert_policy": "Alert on material updates and suppress duplicates.",
        "commercial_signal_tier": "A",
    }
    source.update(overrides)
    return source


def test_fresh_signal_validator_requires_two_baseline_runs_even_if_required_is_lower(
    tmp_path,
    monkeypatch,
    capsys,
):
    _write_sources(
        tmp_path,
        monkeypatch,
        validate_fresh_signal_sources,
        [_fresh_source(baseline_runs_completed=1, baseline_runs_required=1)],
    )

    assert validate_fresh_signal_sources.main() == 1
    output = capsys.readouterr().out
    assert "baseline" in output


def test_daily_checkable_validator_rejects_fresh_alert_without_evidence_gate(
    tmp_path,
    monkeypatch,
    capsys,
):
    _write_sources(
        tmp_path,
        monkeypatch,
        validate_daily_checkable_sources,
        [
            _fresh_source(
                alert_eligible=False,
                last_monitor_status="MONITOR_FAILED",
                proof_path="",
                normalized_text_path="",
                normalized_hash="",
                baseline_runs_completed=0,
            )
        ],
    )

    assert validate_daily_checkable_sources.main() == 1
    output = capsys.readouterr().out
    assert "proof_path" in output
    assert "normalized_text_path" in output
    assert "normalized_hash" in output
    assert "MONITOR_OK" in output
    assert "alert_eligible" in output
    assert "baseline" in output


def test_daily_checkable_validator_rejects_homepage_fresh_alert_claim(
    tmp_path,
    monkeypatch,
    capsys,
):
    _write_sources(
        tmp_path,
        monkeypatch,
        validate_daily_checkable_sources,
        [_fresh_source(url="https://regulator.gov.ae")],
    )

    assert validate_daily_checkable_sources.main() == 1
    output = capsys.readouterr().out
    assert "homepage" in output


def test_monitoring_modes_validator_applies_fresh_alert_evidence_gate(
    tmp_path,
    monkeypatch,
    capsys,
):
    _write_sources(
        tmp_path,
        monkeypatch,
        validate_source_monitoring_modes,
        [_fresh_source(baseline_runs_completed=1, baseline_runs_required=1)],
    )

    assert validate_source_monitoring_modes.main() == 1
    output = capsys.readouterr().out
    assert "baseline" in output
