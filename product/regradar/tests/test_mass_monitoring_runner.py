"""Tests for the safe mass monitoring runner.

The runner tests use injected intake functions only. They do not fetch live
sites, save evidence by default, update sources.json, or send customer alerts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.mass_monitoring_runner import (
    MONITOR_OK,
    NAV_SHELL_ONLY,
    QUALITY_DROP,
    REMEDIATION_REQUIRED,
    SELECTOR_BROKEN,
    run_mass_monitoring_batch,
)


def _gate(status: str = "pass") -> dict:
    return {"status": status, "reason": "test", "reviewed_at": "2026-06-15T00:00:00Z", "blocking_issues": []}


def _entry(source_id: str, status: str, *, regulator: str = "SCA") -> dict:
    return {
        "source_id": source_id,
        "url": f"https://official.example/{source_id}",
        "regulator": regulator,
        "source_type": "listing",
        "official_status": "official",
        "adapter_family": "listing",
        "adapter_name": "listing",
        "adapter_config": {"container_selector": "main"},
        "activation_status": status,
        "current_state": status,
        "no_save_status": "passed" if status == "activation_ready" else "not_run",
        "quality_score": 90 if status == "activation_ready" else 0,
        "noise_risk": "low",
        "source_health_risk": "low",
        "evidence_status": "proof_saved" if status == "activation_ready" else "none",
        "baseline_status": "complete" if status == "activation_ready" else "not_started",
        "proof_path": "data/source_snapshots/test/proof.json" if status == "activation_ready" else "",
        "normalized_text_path": "data/source_snapshots/test/normalized.txt" if status == "activation_ready" else "",
        "normalized_hash": "a" * 64 if status == "activation_ready" else "",
        "baseline_runs_completed": 2 if status == "activation_ready" else 0,
        "baseline_runs_required": 2,
        "can_activate": status == "activation_ready",
        "nav_shell": False,
        "shallow_content": False,
        "duplicate_hash": False,
        "source_monitor_gate": _gate("pass" if status == "activation_ready" else "hold"),
        "evidence_trail_gate": _gate("pass" if status == "activation_ready" else "hold"),
        "qa_critic_gate": _gate("pass" if status == "activation_ready" else "hold"),
        "legal_language_gate": _gate("pass" if status == "activation_ready" else "hold"),
        "product_manager_gate": _gate("pass" if status == "activation_ready" else "hold"),
        "code_architect_gate": _gate("pass" if status == "activation_ready" else "hold"),
        "final_activation_gate": _gate("activation_ready" if status == "activation_ready" else status),
    }


def _queue(path: Path) -> Path:
    payload = {
        "schema_version": "mass-source-activation-1.0",
        "summary": {"sources_json_changed": False},
        "sources": [
            _entry("AE-ready-1", "activation_ready", regulator="SCA"),
            _entry("AE-candidate-1", "candidate", regulator="SCA"),
            _entry("AE-remediation-1", "remediation", regulator="DFSA"),
            _entry("AE-blocked-1", "blocked", regulator="CBUAE"),
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def test_mass_monitor_skips_unsafe_states_by_default(tmp_path):
    queue_path = _queue(tmp_path / "queue.json")
    seen = []

    def fake_intake(source, *, write_evidence):
        seen.append((source["source_id"], write_evidence))
        return {
            "status": "CONFIRMED_ACCESSIBLE",
            "quality_score": 92,
            "normalized_hash": "b" * 64,
            "nav_shell_detected": False,
            "failure_code": "",
            "failure_reason": "",
            "remediation_hint": "",
        }

    summary = run_mass_monitoring_batch(
        queue_path=queue_path,
        limit=10,
        dry_run=True,
        no_alerts=True,
        intake_func=fake_intake,
        write_queue=False,
    )

    assert seen == [("AE-ready-1", False)]
    assert summary["processed_count"] == 1
    assert summary["skipped_count"] == 3
    assert summary["alert_delivery_enabled"] is False
    assert summary["save_proof"] is False
    assert summary["results"][0]["source_health_status"] == MONITOR_OK


def test_mass_monitor_respects_regulator_source_id_and_limit(tmp_path):
    queue_path = _queue(tmp_path / "queue.json")
    seen = []

    def fake_intake(source, *, write_evidence):
        seen.append(source["source_id"])
        return {"status": "CONFIRMED_ACCESSIBLE", "quality_score": 88, "normalized_hash": "c" * 64}

    summary = run_mass_monitoring_batch(
        queue_path=queue_path,
        regulator="SCA",
        source_id="AE-ready-1",
        limit=1,
        intake_func=fake_intake,
        write_queue=False,
    )

    assert seen == ["AE-ready-1"]
    assert summary["processed_count"] == 1


def test_mass_monitor_keeps_adapter_selector_out_of_fetch_selector(tmp_path):
    queue_path = _queue(tmp_path / "queue.json")
    captured = []

    def fake_intake(source, *, write_evidence):
        captured.append(source)
        return {"status": "CONFIRMED_ACCESSIBLE", "quality_score": 88, "normalized_hash": "c" * 64}

    run_mass_monitoring_batch(
        queue_path=queue_path,
        source_id="AE-ready-1",
        intake_func=fake_intake,
        write_queue=False,
    )

    assert captured[0]["adapter_config"]["container_selector"] == "main"
    assert "content_selector" not in captured[0]
    assert "wait_for_selector" not in captured[0]


def test_mass_monitor_maps_quality_and_selector_failures(tmp_path):
    queue_path = _queue(tmp_path / "queue.json")

    def quality_drop(source, *, write_evidence):
        return {
            "status": "QUALITY_DROP",
            "quality_score": 35,
            "normalized_hash": "d" * 64,
            "failure_code": "SOURCE_STRUCTURE_CHANGED",
            "failure_reason": "Normalized text below expected minimum.",
            "remediation_hint": "Review selector.",
        }

    summary = run_mass_monitoring_batch(
        queue_path=queue_path,
        source_id="AE-ready-1",
        intake_func=quality_drop,
        write_queue=False,
    )
    assert summary["results"][0]["source_health_status"] == QUALITY_DROP

    def selector_failure(source, *, write_evidence):
        return {
            "status": "NEEDS_SELECTOR_REVIEW",
            "quality_score": 0,
            "failure_code": "SELECTOR_NOT_FOUND",
            "failure_reason": "Selector timed out.",
            "remediation_hint": "Review selector.",
        }

    summary = run_mass_monitoring_batch(
        queue_path=queue_path,
        source_id="AE-ready-1",
        intake_func=selector_failure,
        write_queue=False,
    )
    assert summary["results"][0]["source_health_status"] == SELECTOR_BROKEN


def test_mass_monitor_maps_nav_shell_and_remediation(tmp_path):
    queue_path = _queue(tmp_path / "queue.json")

    def nav_shell(source, *, write_evidence):
        return {
            "status": "NAV_SHELL_ONLY",
            "quality_score": 20,
            "failure_code": "NAV_SHELL_ONLY",
            "nav_shell_detected": True,
        }

    summary = run_mass_monitoring_batch(
        queue_path=queue_path,
        source_id="AE-ready-1",
        intake_func=nav_shell,
        write_queue=False,
    )
    assert summary["results"][0]["source_health_status"] == NAV_SHELL_ONLY

    def blocked(source, *, write_evidence):
        return {
            "status": "BLOCKED",
            "quality_score": 0,
            "failure_code": "ACCESS_BLOCKED",
        }

    summary = run_mass_monitoring_batch(
        queue_path=queue_path,
        source_id="AE-ready-1",
        intake_func=blocked,
        write_queue=False,
    )
    assert summary["results"][0]["source_health_status"] == REMEDIATION_REQUIRED


def test_mass_monitor_does_not_modify_sources_json(tmp_path):
    queue_path = _queue(tmp_path / "queue.json")
    sources_json = Path(__file__).parent.parent / "sources.json"
    before = sources_json.read_text(encoding="utf-8")

    run_mass_monitoring_batch(
        queue_path=queue_path,
        source_id="AE-ready-1",
        intake_func=lambda source, *, write_evidence: {"status": "CONFIRMED_ACCESSIBLE", "quality_score": 90},
        write_queue=False,
    )

    assert sources_json.read_text(encoding="utf-8") == before


def test_mass_monitor_dry_run_does_not_mutate_queue(tmp_path):
    queue_path = _queue(tmp_path / "queue.json")
    before = queue_path.read_text(encoding="utf-8")

    run_mass_monitoring_batch(
        queue_path=queue_path,
        source_id="AE-ready-1",
        dry_run=True,
        intake_func=lambda source, *, write_evidence: {
            "status": "CONFIRMED_ACCESSIBLE",
            "quality_score": 90,
            "normalized_hash": "e" * 64,
        },
    )

    assert queue_path.read_text(encoding="utf-8") == before
