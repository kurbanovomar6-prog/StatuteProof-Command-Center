#!/usr/bin/env python3
"""Validate StatuteProof source monitoring modes.

Fresh alert is the only mode that may power customer update claims. Evidence
library sources may still have proof/MONITOR_OK, but they cannot be counted as
fresh monitoring.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "product/regradar/sources.json"
ALLOWED_MODES = {"fresh_alert", "evidence_library", "remediation", "candidate"}
FORBIDDEN_COPY = (
    "complete uae coverage",
    "complete family coverage",
    "guaranteed compliance",
    "never miss",
    "perfect parsing",
    "provides legal advice",
    "legal advice platform",
    "legal advice service",
)


def is_ae_source(source: dict) -> bool:
    source_id = str(source.get("source_id") or "")
    return source.get("jurisdiction") == "AE" or source_id.startswith("AE-")


def main() -> int:
    sources = json.loads(SOURCES.read_text())
    failures: list[str] = []
    enabled_ae = [source for source in sources if source.get("enabled") and is_ae_source(source)]

    for source in enabled_ae:
        source_id = source.get("source_id") or source.get("url")
        mode = source.get("monitoring_mode")
        if mode not in ALLOWED_MODES:
            failures.append(f"{source_id}: missing/invalid monitoring_mode={mode!r}")
            continue
        if "alert_eligible" not in source:
            failures.append(f"{source_id}: missing alert_eligible")
        if mode != "fresh_alert" and source.get("alert_eligible") is True:
            failures.append(f"{source_id}: non-fresh mode {mode!r} cannot be alert_eligible")
        if mode == "fresh_alert" and source.get("alert_eligible") is not True:
            failures.append(f"{source_id}: fresh_alert must set alert_eligible=true")
        if mode == "remediation" and source.get("fresh_signal_class") != "REMEDIATION":
            failures.append(f"{source_id}: remediation mode must use fresh_signal_class=REMEDIATION")

    combined_copy = "\n".join(
        str(source.get("name") or "")
        + "\n"
        + str(source.get("notes") or "")
        + "\n"
        + str(source.get("fresh_signal_notes") or "")
        for source in enabled_ae
    ).lower()
    for phrase in FORBIDDEN_COPY:
        if phrase in combined_copy:
            failures.append(f"forbidden customer-facing phrase found in source copy: {phrase!r}")

    if failures:
        print("validate_source_monitoring_modes: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    counts = {mode: 0 for mode in sorted(ALLOWED_MODES)}
    for source in enabled_ae:
        counts[source["monitoring_mode"]] += 1
    print("validate_source_monitoring_modes: PASS")
    print(f"enabled_ae={len(enabled_ae)} modes={counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
