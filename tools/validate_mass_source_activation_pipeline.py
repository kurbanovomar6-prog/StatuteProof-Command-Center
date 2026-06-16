#!/usr/bin/env python3
"""Validate the general mass source activation queue.

This validator is intentionally allowed to pass when zero sources are
activation-ready. Its job is to make fake activation harder, not to inflate the
source count.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCT_ROOT = ROOT / "product/regradar"
QUEUE_FILE = PRODUCT_ROOT / "config/mass_source_activation_queue.json"
SOURCES_FILE = PRODUCT_ROOT / "sources.json"
RUNNER_FILE = PRODUCT_ROOT / "app/mass_source_activation_runner.py"
RUN_FILE = PRODUCT_ROOT / "run.py"

sys.path.insert(0, str(PRODUCT_ROOT))

from app.mass_source_activation import (  # noqa: E402
    ACTIVATION_READY,
    REQUIRED_GATES,
    evaluate_activation,
)


REQUIRED_FIELDS = {
    "source_id",
    "url",
    "regulator",
    "source_type",
    "official_status",
    "discovery_status",
    "adapter_family",
    "adapter_name",
    "adapter_config",
    "no_save_status",
    "quality_score",
    "noise_risk",
    "source_health_risk",
    "evidence_status",
    "baseline_status",
    "activation_status",
    "failure_code",
    "failure_reason",
    "remediation_hint",
    "agent_gate_status",
    "current_state",
    "proof_path",
    "normalized_text_path",
    "normalized_hash",
    "baseline_runs_completed",
    "baseline_runs_required",
    "can_activate",
    "nav_shell",
    "shallow_content",
    "duplicate_hash",
    "final_activation_gate",
}

ALLOWED_GATE_STATUSES = {"pass", "hold", "fail"}
ALLOWED_FINAL_STATUSES = {
    "candidate",
    "discovered",
    "no_save_passed",
    "proof_saved",
    "baseline_pending",
    "activation_ready",
    "remediation",
    "blocked",
    "rejected",
}

CLAIM_SCAN_PATHS = [
    ROOT / "README.md",
    ROOT / "START_HERE.md",
    ROOT / "product/regradar/web/src",
]
FORBIDDEN_ALWAYS = {
    "any website can be parsed",
    "perfect parsing",
    "95% of all websites",
    "guaranteed compliance",
    "we provide legal advice",
    "official regulator certified",
}
FORBIDDEN_UNLESS_50 = {
    "50 working sources",
    "50 monitored sources",
    "50 activation-ready sources",
    "60 validated sources",
    "60 monitored sources",
}
EXPECTED_ENABLED_SOURCES = 46
EXPECTED_READINESS_SUPPORTED = 42
EXPECTED_REMEDIATION = 4


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def scan_customer_files() -> list[Path]:
    files: list[Path] = []
    for path in CLAIM_SCAN_PATHS:
        if path.is_dir():
            files.extend(child for child in path.rglob("*") if child.is_file())
        elif path.exists():
            files.append(path)
    return files


def proof_path_exists(path_value: str) -> bool:
    if not path_value:
        return False
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    return path.exists()


def validate_sources_json_truth(errors: list[str]) -> None:
    sources = load_json(SOURCES_FILE)
    if not isinstance(sources, list):
        fail(errors, "sources.json must remain a list for the current registry contract.")
        return
    enabled = [source for source in sources if source.get("enabled") is True]
    readiness_supported = [
        source
        for source in enabled
        if source.get("status") == "active"
    ]
    remediation = [
        source
        for source in enabled
        if source.get("status") == "remediation"
    ]
    if (
        len(enabled) != EXPECTED_ENABLED_SOURCES
        or len(readiness_supported) != EXPECTED_READINESS_SUPPORTED
        or len(remediation) != EXPECTED_REMEDIATION
    ):
        fail(
            errors,
            "Public source truth changed without this validator being updated: "
            f"{len(enabled)} enabled / {len(readiness_supported)} readiness-supported / {len(remediation)} remediation.",
        )


def main() -> int:
    errors: list[str] = []

    if not RUNNER_FILE.exists():
        fail(errors, "Missing safe batch runner: product/regradar/app/mass_source_activation_runner.py")
    else:
        runner_text = RUNNER_FILE.read_text(encoding="utf-8")
        for required in (
            'mode: str = "no-save-only"',
            'write_evidence=False',
            '"sources_json_changed": False',
            "evaluate_activation",
        ):
            if required not in runner_text:
                fail(errors, f"Mass source activation runner missing safety marker: {required}")

    run_text = RUN_FILE.read_text(encoding="utf-8")
    if "mass-source-activate" not in run_text:
        fail(errors, "CLI must expose mass-source-activate command.")

    if not QUEUE_FILE.exists():
        fail(errors, f"Missing mass activation queue: {QUEUE_FILE.relative_to(ROOT)}")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    data = load_json(QUEUE_FILE)
    if not isinstance(data, dict):
        fail(errors, "Mass activation queue must be a JSON object.")
        data = {}
    sources = data.get("sources", [])
    summary = data.get("summary", {})
    if not isinstance(sources, list) or not sources:
        fail(errors, "Mass activation queue must include a non-empty sources list.")
        sources = []
    if not isinstance(summary, dict):
        fail(errors, "Mass activation queue summary must be an object.")
        summary = {}

    ids: dict[str, int] = {}
    activation_ready_count = 0
    proof_backed_count = 0
    baseline_complete_count = 0

    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            fail(errors, f"Source #{index} must be an object.")
            continue

        source_id = str(source.get("source_id") or "").strip()
        ids[source_id] = ids.get(source_id, 0) + 1
        label = source_id or f"source #{index}"
        missing = sorted((REQUIRED_FIELDS | set(REQUIRED_GATES)) - set(source))
        if missing:
            fail(errors, f"{label} missing fields: {', '.join(missing)}")

        url = str(source.get("url") or "")
        if url and not url.startswith("https://"):
            fail(errors, f"{label} URL must use https://.")

        final_gate = source.get("final_activation_gate") or {}
        if not isinstance(final_gate, dict):
            fail(errors, f"{label} final_activation_gate must be an object.")
            final_gate = {}
        if final_gate.get("status") not in ALLOWED_FINAL_STATUSES:
            fail(errors, f"{label} has invalid final activation status: {final_gate.get('status')!r}")
        if source.get("activation_status") != final_gate.get("status"):
            fail(errors, f"{label} activation_status must match final_activation_gate.status.")
        if source.get("current_state") == ACTIVATION_READY and source.get("activation_status") != ACTIVATION_READY:
            fail(errors, f"{label} current_state cannot be activation_ready while activation_status differs.")

        for gate_name in REQUIRED_GATES:
            gate = source.get(gate_name)
            if not isinstance(gate, dict):
                fail(errors, f"{label} {gate_name} must be an object.")
                continue
            if gate.get("status") not in ALLOWED_GATE_STATUSES:
                fail(errors, f"{label} {gate_name} has invalid status: {gate.get('status')!r}")
            if not gate.get("reason"):
                fail(errors, f"{label} {gate_name} must include a reason.")
            if "blocking_issues" not in gate or not isinstance(gate.get("blocking_issues"), list):
                fail(errors, f"{label} {gate_name} must include blocking_issues list.")

        evaluated = evaluate_activation(source)
        if evaluated.get("activation_status") != source.get("activation_status"):
            fail(
                errors,
                f"{label} activation_status {source.get('activation_status')!r} does not match evaluated status "
                f"{evaluated.get('activation_status')!r}.",
            )
        if bool(evaluated.get("can_activate")) != bool(source.get("can_activate")):
            fail(errors, f"{label} can_activate does not match evaluated activation decision.")

        proof_path = str(source.get("proof_path") or "")
        if proof_path:
            proof_backed_count += 1
        completed = int(source.get("baseline_runs_completed") or 0)
        required = int(source.get("baseline_runs_required") or 2)
        if proof_path and completed >= required:
            baseline_complete_count += 1

        if source.get("activation_status") == ACTIVATION_READY:
            activation_ready_count += 1
            if not proof_path_exists(proof_path):
                fail(errors, f"{label} activation_ready requires an existing proof_path.")
            if completed < required:
                fail(errors, f"{label} activation_ready requires completed repeat baseline.")
            if source.get("noise_risk") == "high":
                fail(errors, f"{label} activation_ready cannot have high noise risk.")
            if source.get("source_health_risk") == "high":
                fail(errors, f"{label} activation_ready cannot have high source-health risk.")
            if source.get("nav_shell") is True:
                fail(errors, f"{label} activation_ready cannot be nav-shell.")
            if source.get("duplicate_hash") is True:
                fail(errors, f"{label} activation_ready cannot have duplicate hash.")
            for gate_name in REQUIRED_GATES:
                if (source.get(gate_name) or {}).get("status") != "pass":
                    fail(errors, f"{label} activation_ready requires {gate_name}=pass.")

    duplicate_ids = sorted(source_id for source_id, count in ids.items() if source_id and count > 1)
    if duplicate_ids:
        fail(errors, "Duplicate mass queue source IDs: " + ", ".join(duplicate_ids))

    if summary.get("queue_entries") != len(sources):
        fail(errors, "Summary queue_entries does not match sources list length.")
    if summary.get("activation_ready_count") != activation_ready_count:
        fail(errors, "Summary activation_ready_count does not match queue.")
    if summary.get("proof_backed_count") != proof_backed_count:
        fail(errors, "Summary proof_backed_count does not match queue.")
    if summary.get("baseline_complete_count") != baseline_complete_count:
        fail(errors, "Summary baseline_complete_count does not match queue.")
    reached_50 = activation_ready_count >= 50
    if bool(summary.get("did_reach_50_working_sources")) != reached_50:
        fail(errors, "did_reach_50_working_sources must match activation_ready_count >= 50.")

    validate_sources_json_truth(errors)

    for path in scan_customer_files():
        try:
            text = path.read_text(encoding="utf-8").lower()
        except UnicodeDecodeError:
            continue
        for claim in FORBIDDEN_ALWAYS:
            if claim in text:
                fail(errors, f"Forbidden customer-facing claim in {path.relative_to(ROOT)}: {claim}")
        if not reached_50:
            for claim in FORBIDDEN_UNLESS_50:
                if claim in text:
                    fail(errors, f"Forbidden source-count claim before 50 activation-ready sources in {path.relative_to(ROOT)}: {claim}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Mass source activation pipeline validation passed.")
    print(f"Queue entries: {len(sources)}")
    print(f"Activation-ready: {activation_ready_count}")
    print(f"Proof-backed: {proof_backed_count}")
    print(f"Baseline-complete: {baseline_complete_count}")
    print(
        "Public truth remains: "
        f"{EXPECTED_ENABLED_SOURCES} enabled / "
        f"{EXPECTED_READINESS_SUPPORTED} readiness-supported / "
        f"{EXPECTED_REMEDIATION} remediation"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
