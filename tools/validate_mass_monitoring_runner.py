#!/usr/bin/env python3
"""Validate the safe mass monitoring runner contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCT_ROOT = ROOT / "product/regradar"
RUNNER_FILE = PRODUCT_ROOT / "app/mass_monitoring_runner.py"
RUN_FILE = PRODUCT_ROOT / "run.py"
QUEUE_FILE = PRODUCT_ROOT / "config/mass_source_activation_queue.json"
SOURCES_FILE = PRODUCT_ROOT / "sources.json"

sys.path.insert(0, str(PRODUCT_ROOT))


CUSTOMER_FACING_PATHS = [
    ROOT / "README.md",
    ROOT / "START_HERE.md",
    ROOT / "product/regradar/web/src",
]

FORBIDDEN_PUBLIC_CLAIMS = [
    "any website can be parsed",
    "perfect parsing",
    "95% websites",
    "95% of all websites",
    "60 validated sources",
    "50 validated sources",
    "guaranteed compliance",
    "we provide legal advice",
    "provides legal advice",
    "is a legal advice service",
    "as legal advice",
    "regulator certified",
]
EXPECTED_ENABLED_SOURCES = 33
EXPECTED_READINESS_SUPPORTED = 29
EXPECTED_REMEDIATION = 4


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _scan_customer_files() -> list[Path]:
    files: list[Path] = []
    for path in CUSTOMER_FACING_PATHS:
        if path.is_dir():
            files.extend(child for child in path.rglob("*") if child.is_file())
        elif path.exists():
            files.append(path)
    return files


def _validate_public_truth(errors: list[str]) -> None:
    sources = _load_json(SOURCES_FILE)
    if not isinstance(sources, list):
        errors.append("sources.json must remain a list.")
        return
    enabled = [source for source in sources if isinstance(source, dict) and source.get("enabled") is True]
    ready = [source for source in enabled if source.get("status") == "active"]
    remediation = [source for source in enabled if source.get("status") == "remediation"]
    if (
        len(enabled) != EXPECTED_ENABLED_SOURCES
        or len(ready) != EXPECTED_READINESS_SUPPORTED
        or len(remediation) != EXPECTED_REMEDIATION
    ):
        errors.append(
            "Public truth changed without registry/readiness proof: "
            f"{len(enabled)} enabled / {len(ready)} readiness-supported / {len(remediation)} remediation."
        )


def main() -> int:
    errors: list[str] = []

    if not RUNNER_FILE.exists():
        errors.append("Missing product/regradar/app/mass_monitoring_runner.py.")
    else:
        text = RUNNER_FILE.read_text(encoding="utf-8")
        for marker in (
            "dry_run: bool = True",
            "no_alerts: bool = True",
            "SAFE_MONITOR_STATES",
            "UNSAFE_MONITOR_STATES",
            '"sources_json_changed": False',
            '"alert_sent": False',
            "write_evidence = bool(save_proof and not dry_run)",
            "if write_queue and not dry_run",
            "candidate",
            "remediation",
            "blocked",
            "rejected",
            "MONITOR_OK",
            "QUALITY_DROP",
            "SELECTOR_BROKEN",
            "NAV_SHELL_ONLY",
            "REMEDIATION_REQUIRED",
        ):
            if marker not in text:
                errors.append(f"Mass monitoring runner missing safety marker: {marker}")

    run_text = RUN_FILE.read_text(encoding="utf-8")
    if "mass-monitor" not in run_text:
        errors.append("CLI must expose mass-monitor command.")
    for marker in ("--activation-ready-only", "--dry-run", "--no-alerts", "--limit", "--save-proof"):
        if marker not in run_text:
            errors.append(f"mass-monitor CLI missing option marker: {marker}")

    data = _load_json(QUEUE_FILE)
    if not isinstance(data, dict) or not isinstance(data.get("sources"), list):
        errors.append("Mass source activation queue must be a JSON object with a sources list.")
    else:
        for source in data["sources"]:
            if not isinstance(source, dict):
                continue
            if source.get("activation_status") == "activation_ready":
                gate = source.get("final_activation_gate") or {}
                if gate.get("status") != "activation_ready":
                    errors.append(f"{source.get('source_id')} has activation_ready status without final gate.")
            if source.get("activation_status") in {"candidate", "remediation", "blocked", "rejected"}:
                if source.get("can_activate") is True:
                    errors.append(f"{source.get('source_id')} unsafe state has can_activate=true.")

    _validate_public_truth(errors)

    for path in _scan_customer_files():
        try:
            text = path.read_text(encoding="utf-8").lower()
        except UnicodeDecodeError:
            continue
        for claim in FORBIDDEN_PUBLIC_CLAIMS:
            if claim in text:
                errors.append(f"Forbidden public claim in {path.relative_to(ROOT)}: {claim}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Mass monitoring runner validation passed.")
    print("Default mode: dry-run / no-alerts.")
    print("Unsafe queue states are blocked from default monitoring.")
    print(
        "Public truth remains: "
        f"{EXPECTED_ENABLED_SOURCES} enabled / "
        f"{EXPECTED_READINESS_SUPPORTED} readiness-supported / "
        f"{EXPECTED_REMEDIATION} remediation."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
