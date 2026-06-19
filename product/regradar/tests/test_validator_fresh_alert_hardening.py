from __future__ import annotations

import json
import hashlib
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
    monkeypatch.setattr(module, "REGRADAR_ROOT", tmp_path, raising=False)


def _fresh_source(tmp_path: Path, **overrides) -> dict:
    snapshot_dir = tmp_path / "data/source_snapshots/test"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    proof_path = snapshot_dir / "proof.json"
    normalized_path = snapshot_dir / "normalized.txt"
    normalized_text = "Official regulatory update listing\nUpdated daily"
    normalized_path.write_text(normalized_text, encoding="utf-8")
    normalized_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
    proof_path.write_text(
        json.dumps(
            {
                "source_id": "AE-test-fresh-alert",
                "snapshot_normalized_path": "data/source_snapshots/test/normalized.txt",
                "normalized_hash": normalized_hash,
            }
        ),
        encoding="utf-8",
    )
    source = {
        "source_id": "AE-test-fresh-alert",
        "name": "Test Fresh Alert Source",
        "url": "https://regulator.gov.ae/regulations/updates",
        "enabled": True,
        "jurisdiction": "AE",
        "monitoring_mode": "fresh_alert",
        "alert_eligible": True,
        "last_monitor_status": "MONITOR_OK",
        "proof_path": "data/source_snapshots/test/proof.json",
        "normalized_text_path": "data/source_snapshots/test/normalized.txt",
        "normalized_hash": normalized_hash,
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
        [_fresh_source(tmp_path, baseline_runs_completed=1, baseline_runs_required=1)],
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
                tmp_path,
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
        [_fresh_source(tmp_path, url="https://regulator.gov.ae")],
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
        [_fresh_source(tmp_path, baseline_runs_completed=1, baseline_runs_required=1)],
    )

    assert validate_source_monitoring_modes.main() == 1
    output = capsys.readouterr().out
    assert "baseline" in output


def test_fresh_signal_validator_requires_source_id(tmp_path, monkeypatch, capsys):
    _write_sources(
        tmp_path,
        monkeypatch,
        validate_fresh_signal_sources,
        [_fresh_source(tmp_path, source_id="")],
    )

    assert validate_fresh_signal_sources.main() == 1
    output = capsys.readouterr().out
    assert "source_id" in output


def test_fresh_signal_validator_requires_existing_artifacts(tmp_path, monkeypatch, capsys):
    _write_sources(
        tmp_path,
        monkeypatch,
        validate_fresh_signal_sources,
        [_fresh_source(tmp_path, proof_path="data/source_snapshots/test/missing-proof.json")],
    )

    assert validate_fresh_signal_sources.main() == 1
    output = capsys.readouterr().out
    assert "proof_path" in output
    assert "does not exist" in output


def test_fresh_signal_validator_recomputes_normalized_hash(tmp_path, monkeypatch, capsys):
    _write_sources(
        tmp_path,
        monkeypatch,
        validate_fresh_signal_sources,
        [_fresh_source(tmp_path, normalized_hash="b" * 64)],
    )

    assert validate_fresh_signal_sources.main() == 1
    output = capsys.readouterr().out
    assert "normalized_hash" in output
    assert "does not match" in output


def test_fresh_signal_validator_rejects_malformed_baseline_counts(
    tmp_path,
    monkeypatch,
    capsys,
):
    _write_sources(
        tmp_path,
        monkeypatch,
        validate_fresh_signal_sources,
        [_fresh_source(tmp_path, baseline_runs_completed="two")],
    )

    assert validate_fresh_signal_sources.main() == 1
    output = capsys.readouterr().out
    assert "baseline_runs_completed" in output
    assert "integer" in output


def test_fresh_signal_validator_requires_complete_proof_fields(
    tmp_path,
    monkeypatch,
    capsys,
):
    proof_path = tmp_path / "data/source_snapshots/test/proof.json"
    source = _fresh_source(tmp_path)
    proof = json.loads(proof_path.read_text(encoding="utf-8"))
    proof.pop("normalized_hash")
    proof_path.write_text(json.dumps(proof), encoding="utf-8")
    _write_sources(tmp_path, monkeypatch, validate_fresh_signal_sources, [source])

    assert validate_fresh_signal_sources.main() == 1
    output = capsys.readouterr().out
    assert "proof_path missing normalized_hash" in output
