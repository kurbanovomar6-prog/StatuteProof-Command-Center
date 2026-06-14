#!/usr/bin/env python3
"""Validate the agent-gated UAE 50-source work queue.

This validator is deliberately strict about any claim that 50 sources are
working. It is also allowed to pass when the queue truthfully says the 50-source
threshold has not been reached.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUEUE_FILE = ROOT / "product/regradar/config/uae_source_work_queue.json"
CLAIM_SCAN_PATHS = [
    ROOT / "README.md",
    ROOT / "START_HERE.md",
    ROOT / "product/regradar/web/src",
]

REQUIRED_GATE_FIELDS = {
    "source_monitor_gate",
    "evidence_trail_gate",
    "qa_critic_gate",
    "legal_language_gate",
    "code_architect_gate",
    "product_manager_gate",
    "final_activation_gate",
}
REQUIRED_SOURCE_FIELDS = {
    "source_id",
    "regulator",
    "url",
    "source_type",
    "priority",
    "current_state",
    "blocker",
    "next_action",
    "expected_extraction_strategy",
    "noise_risk",
    "source_health_risk",
    "baseline_runs_completed",
    "baseline_runs_required",
    "can_activate",
    "activation_decision",
    "adapter_family",
    "adapter_name",
    "adapter_version",
    "adapter_config",
    "extraction_strategy",
    "last_adapter_test_at",
    "adapter_status",
    "adapter_failure_reason",
    "adapter_remediation_hint",
}
ALLOWED_FINAL_STATUSES = {
    "activation_ready",
    "baseline_pending",
    "remediation",
    "blocked",
    "rejected",
    "candidate",
}
ALLOWED_ADAPTER_STATUSES = {
    "not_configured",
    "configured_pending_live_adapter_test",
    "configured_for_remediation",
    "configured_pending_selector_review",
    "live_test_passed",
    "live_test_failed",
    "evidence_saved",
    "activation_ready",
}
PASS_REQUIRED_GATES = {
    "source_monitor_gate",
    "evidence_trail_gate",
    "qa_critic_gate",
    "legal_language_gate",
    "code_architect_gate",
    "product_manager_gate",
}
FORBIDDEN_CLAIMS_UNLESS_50 = {
    "50 working sources",
    "50 official sources working",
    "50 monitored sources",
    "50 activation-ready sources",
    "60 validated sources",
    "60 monitored sources",
}
FORBIDDEN_ALWAYS = {
    "any website can be parsed",
    "perfect parsing",
    "guaranteed compliance",
    "we provide legal advice",
    "official regulator certified",
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_scan_files() -> list[Path]:
    files: list[Path] = []
    for path in CLAIM_SCAN_PATHS:
        if path.is_dir():
            files.extend(child for child in path.rglob("*") if child.is_file())
        elif path.exists():
            files.append(path)
    return files


def main() -> int:
    errors: list[str] = []
    if not QUEUE_FILE.exists():
        fail(errors, f"Missing work queue: {QUEUE_FILE}")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    data = load_json(QUEUE_FILE)
    if not isinstance(data, dict):
        fail(errors, "Work queue must be a JSON object.")
        data = {}
    summary = data.get("summary", {})
    if not isinstance(summary, dict):
        fail(errors, "Work queue summary must be an object.")
        summary = {}
    sources = data.get("sources", [])
    if not isinstance(sources, list) or not sources:
        fail(errors, "Work queue must include a non-empty sources list.")
        sources = []

    ids: dict[str, int] = {}
    activated: list[dict] = []
    proof_backed: list[dict] = []
    baseline_complete: list[dict] = []

    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            fail(errors, f"Source #{index} must be an object.")
            continue
        source_id = str(source.get("source_id") or "").strip()
        ids[source_id] = ids.get(source_id, 0) + 1
        missing = sorted((REQUIRED_SOURCE_FIELDS | REQUIRED_GATE_FIELDS) - set(source))
        if missing:
            fail(errors, f"{source_id or f'source #{index}'} missing fields: {', '.join(missing)}")
        if not source_id:
            fail(errors, f"Source #{index} has blank source_id.")
        url = str(source.get("url") or "")
        if url and not url.startswith("https://"):
            fail(errors, f"{source_id} URL must use https:// when present.")

        final_gate = source.get("final_activation_gate") or {}
        final_status = final_gate.get("status")
        if final_status not in ALLOWED_FINAL_STATUSES:
            fail(errors, f"{source_id} has invalid final activation status: {final_status!r}")
        if source.get("activation_decision") != final_status:
            fail(errors, f"{source_id} activation_decision must match final_activation_gate.status.")

        adapter_family = source.get("adapter_family")
        adapter_name = source.get("adapter_name")
        adapter_status = source.get("adapter_status")
        if adapter_status not in ALLOWED_ADAPTER_STATUSES:
            fail(errors, f"{source_id} has invalid adapter_status: {adapter_status!r}")
        if adapter_family:
            if adapter_name not in {
                "custom_element",
                "listing",
                "table",
                "sca_listing",
                "dfsa_rulebook",
                "cbuae_document_listing",
                "fiu_eocn_document_listing",
                "vara_pdf_listing",
            }:
                fail(errors, f"{source_id} has unsupported adapter_name: {adapter_name!r}")
            if not source.get("adapter_version"):
                fail(errors, f"{source_id} configured adapter requires adapter_version.")
            if not isinstance(source.get("adapter_config"), dict):
                fail(errors, f"{source_id} configured adapter requires adapter_config object.")
            if not str(source.get("extraction_strategy") or "").startswith("adapter:"):
                fail(errors, f"{source_id} configured adapter requires adapter extraction_strategy.")
        elif final_status == "activation_ready":
            fail(errors, f"{source_id} activation_ready source requires explicit adapter metadata.")

        proof_path = source.get("proof_path")
        baseline_completed = int(source.get("baseline_runs_completed") or 0)
        baseline_required = int(source.get("baseline_runs_required") or 2)
        if proof_path:
            proof_backed.append(source)
        if proof_path and baseline_completed >= baseline_required:
            baseline_complete.append(source)

        for gate_name in REQUIRED_GATE_FIELDS:
            gate = source.get(gate_name)
            if not isinstance(gate, dict):
                fail(errors, f"{source_id} {gate_name} must be an object.")
                continue
            if gate_name == "final_activation_gate":
                continue
            if gate.get("status") not in {"pass", "hold", "fail"}:
                fail(errors, f"{source_id} {gate_name} has invalid status: {gate.get('status')!r}")
            if not gate.get("reason"):
                fail(errors, f"{source_id} {gate_name} must include a reason.")

        if final_status == "activation_ready":
            activated.append(source)
            if not source.get("can_activate"):
                fail(errors, f"{source_id} activation_ready source must set can_activate true.")
            if not proof_path:
                fail(errors, f"{source_id} activation_ready source requires proof_path.")
            if baseline_completed < baseline_required:
                fail(errors, f"{source_id} activation_ready source has incomplete baseline.")
            for gate_name in PASS_REQUIRED_GATES:
                if (source.get(gate_name) or {}).get("status") != "pass":
                    fail(errors, f"{source_id} activation_ready source requires {gate_name}=pass.")
            if source.get("noise_risk") == "high":
                fail(errors, f"{source_id} activation_ready source cannot have high noise risk.")
            if source.get("source_health_risk") == "high":
                fail(errors, f"{source_id} activation_ready source cannot have high source-health risk.")
            if adapter_status not in {"live_test_passed", "evidence_saved", "activation_ready"}:
                fail(errors, f"{source_id} activation_ready source needs a live-tested/evidence adapter status.")
        else:
            if source.get("can_activate") is True:
                fail(errors, f"{source_id} can_activate true but final status is {final_status}.")

    duplicate_ids = sorted(source_id for source_id, count in ids.items() if source_id and count > 1)
    if duplicate_ids:
        fail(errors, "Duplicate work-queue source IDs: " + ", ".join(duplicate_ids))

    activated_count = len(activated)
    if summary.get("activation_ready_count") != activated_count:
        fail(errors, "Summary activation_ready_count does not match queue.")
    if summary.get("proof_backed_count") != len(proof_backed):
        fail(errors, "Summary proof_backed_count does not match queue.")
    if summary.get("baseline_complete_count") != len(baseline_complete):
        fail(errors, "Summary baseline_complete_count does not match queue.")
    reached_50 = activated_count >= 50
    if bool(summary.get("did_reach_50_working_sources")) != reached_50:
        fail(errors, "did_reach_50_working_sources must match activation_ready_count >= 50.")

    for path in iter_scan_files():
        try:
            text = path.read_text(encoding="utf-8").lower()
        except UnicodeDecodeError:
            continue
        if not reached_50:
            for claim in FORBIDDEN_CLAIMS_UNLESS_50:
                if claim in text:
                    fail(errors, f"Forbidden 50/60 source claim before validator reaches 50 in {path.relative_to(ROOT)}: {claim}")
        for claim in FORBIDDEN_ALWAYS:
            if claim in text:
                fail(errors, f"Forbidden always-unsafe claim in {path.relative_to(ROOT)}: {claim}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("UAE 50 working-source queue validation passed.")
    print(f"Queue entries: {len(sources)}")
    print(f"Activation-ready: {activated_count}")
    print(f"Proof-backed: {len(proof_backed)}")
    print(f"Baseline-complete: {len(baseline_complete)}")
    print(f"Reached 50 working sources: {'yes' if reached_50 else 'no'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
