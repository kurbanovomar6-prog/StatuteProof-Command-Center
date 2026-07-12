"""Tests for the safe mass monitoring runner.

The runner tests use injected intake functions only. They do not fetch live
sites, save evidence by default, update sources.json, or send customer alerts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

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


def test_mass_monitor_promotes_adapter_selectors_to_fetch_selectors(tmp_path):
    queue_path = _queue(tmp_path / "queue.json")
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    queue["sources"][0]["adapter_family"] = "static_html"
    queue["sources"][0]["adapter_name"] = "static_html"
    queue["sources"][0]["adapter_config"] = {
        "content_selector": "main, article, body",
        "wait_for_selector": "main",
    }
    queue_path.write_text(json.dumps(queue, indent=2), encoding="utf-8")
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

    assert captured[0]["adapter_config"]["content_selector"] == "main, article, body"
    assert captured[0]["content_selector"] == "main, article, body"
    assert captured[0]["wait_for_selector"] == "main"


def test_mass_monitor_keeps_custom_element_selector_inside_adapter_config(tmp_path):
    queue_path = _queue(tmp_path / "queue.json")
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    queue["sources"][0]["adapter_family"] = "custom_element"
    queue["sources"][0]["adapter_name"] = "custom_element"
    queue["sources"][0]["adapter_config"] = {"content_selector": "adgm-page"}
    queue_path.write_text(json.dumps(queue, indent=2), encoding="utf-8")
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

    assert captured[0]["adapter_config"]["content_selector"] == "adgm-page"
    assert "content_selector" not in captured[0]


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


def test_map_health_gates_http_errors_and_stub_captures():
    """OPS audit 2026-07-12: a 503 maintenance page classified MONITOR_OK and
    became the trusted baseline for 7 MOET sources. The classifier must gate
    (a) http_status >= 400 and (b) captures below expected_min_length."""
    from app.mass_monitoring_runner import map_source_health_status

    ok_result = {
        "status": "CONFIRMED_ACCESSIBLE",
        "normalized_hash": "sha256:aa",
        "quality_score": 65,
        "chars_normalized": 20_000,
    }
    # Healthy result stays OK (with and without the min-length kwarg).
    assert map_source_health_status(dict(ok_result)) == "MONITOR_OK"
    assert map_source_health_status(dict(ok_result), expected_min_length=500) == "MONITOR_OK"

    # (a) An HTTP error body can NEVER be OK, however clean it hashed.
    for code in (403, 429, 500, 503):
        got = map_source_health_status({**ok_result, "http_status": code})
        assert got == "REMEDIATION_REQUIRED", f"http {code} classified {got}"

    # (b) A capture below the declared floor is a stub, never OK — the exact
    # MOET shape: 146-char maintenance page, quality >= 60, hash present.
    stub = {**ok_result, "chars_normalized": 146}
    assert map_source_health_status(stub, expected_min_length=500) == "QUALITY_DROP"
    # Without a declared floor the gate stays out of the way (no false drop).
    assert map_source_health_status(stub) == "MONITOR_OK"
    # Missing chars_normalized (older intake shape) never trips the gate.
    no_chars = {k: v for k, v in ok_result.items() if k != "chars_normalized"}
    assert map_source_health_status(no_chars, expected_min_length=500) == "MONITOR_OK"


def test_batch_run_with_real_intake_gates_a_long_error_page(tmp_path):
    """
    Full end-to-end proof for Finding 2: run_mass_monitoring_batch with the
    REAL app.source_intake.run_source_intake as intake_func (no injected
    fake — this is the exact wiring run_mass_monitoring_batch uses by
    default, see the `if intake_func is None: from app.source_intake import
    run_source_intake` line), against a source that fetches a long,
    cleanly-hashing page but with a 503 status. Only app.scraper's fetch
    layer is mocked, at the same seam production code calls through.

    Pre-fix, run_source_intake never set http_status at the top level, so
    this classified via the quality/stub heuristics alone (not
    REMEDIATION_REQUIRED for this fixture — see the honesty note on the
    sibling test in test_source_intake.py). Post-fix, the real http_status
    the fetch layer captured reaches the classifier and REMEDIATION_REQUIRED
    fires, exactly as the gate's docstring claims.
    """
    error_page_html = (
        "<html><body><main>"
        + "Service temporarily unavailable. Please try again later. " * 40
        + "</main></body></html>"
    )

    def _fake_fetch(url, *, wait_for_selector=None, content_selector=None,
                     force_playwright=False, prefer_requests_on_low_content=False,
                     status_out=None):
        if status_out is not None:
            status_out["http_status"] = 503
        return error_page_html

    # A minimal entry with no adapter configured (the standard _entry()
    # helper above wires a "listing" adapter tuned for other tests' fixture
    # markup, which is not the point of this test — this fixture only needs
    # to prove the plain-HTML path threads http_status through the real
    # batch-runner wiring end to end).
    queue_data = {
        "schema_version": "mass-source-activation-1.0",
        "summary": {"sources_json_changed": False},
        "sources": [{
            "source_id": "AE-error-page-1",
            "name": "AE-error-page-1",
            "url": "https://official.example/AE-error-page-1",
            "regulator": "SCA",
            "source_type": "listing",
            "official_status": "official",
            "activation_status": "activation_ready",
            "current_state": "activation_ready",
            "expected_min_length": 500,
            "baseline_runs_required": 2,
            "can_activate": True,
        }],
    }
    queue_path = tmp_path / "queue.json"
    queue_path.write_text(json.dumps(queue_data, indent=2), encoding="utf-8")

    with patch("app.scraper.fetch_page_with_config", side_effect=_fake_fetch):
        result = run_mass_monitoring_batch(
            queue_path=queue_path,
            source_id="AE-error-page-1",
            dry_run=True,
        )

    assert result["processed_count"] == 1
    health = result["results"][0]["source_health_status"]
    assert health == REMEDIATION_REQUIRED, (
        f"a 503 fetch must gate to REMEDIATION_REQUIRED via the real intake "
        f"pipeline, got {health!r}"
    )
