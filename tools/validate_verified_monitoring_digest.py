#!/usr/bin/env python3
"""Validate the operator-only verified monitoring digest safety boundaries."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "product" / "regradar"
sys.path.insert(0, str(APP_ROOT))

from app.verified_monitoring_digest import build_verified_monitoring_digest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate StatuteProof monitoring digest safety.")
    parser.add_argument("--base-dir", type=Path, default=APP_ROOT, help="Regradar base directory.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    digest = build_verified_monitoring_digest(base_dir=args.base_dir)
    errors = _validate_digest(digest)
    if errors:
        print("Verified monitoring digest validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    summary = digest.get("summary", {})
    print("Verified monitoring digest validation PASSED")
    print(f"- alerts_total={summary.get('alerts_total', 0)}")
    print(f"- pending_review={summary.get('pending_review', 0)}")
    print(f"- canonical_evidence_linked={summary.get('canonical_evidence_linked', 0)}")
    print(f"- source_health_blocked={summary.get('source_health_blocked', 0)}")
    print("- customer_delivery=false")
    return 0


def _validate_digest(digest: dict) -> list[str]:
    errors: list[str] = []
    if digest.get("operator_only") is not True:
        errors.append("digest.operator_only must be true")
    if digest.get("customer_delivery") is not False:
        errors.append("digest.customer_delivery must be false")
    if digest.get("external_send") is not False:
        errors.append("digest.external_send must be false")

    summary = digest.get("summary")
    items = digest.get("items")
    if not isinstance(summary, dict):
        errors.append("digest.summary must be an object")
        summary = {}
    if not isinstance(items, list):
        errors.append("digest.items must be a list")
        items = []
    if summary.get("alerts_total") != len(items):
        errors.append("summary.alerts_total must match item count")
    if summary.get("customer_delivery_allowed") != 0:
        errors.append("summary.customer_delivery_allowed must stay 0")

    source_health = digest.get("source_health")
    if not isinstance(source_health, dict):
        errors.append("digest.source_health must be an object")
        source_health = {}
    if source_health.get("operator_only") is not True:
        errors.append("source_health.operator_only must be true")
    if source_health.get("customer_delivery") is not False:
        errors.append("source_health.customer_delivery must be false")
    if source_health.get("external_send") is not False:
        errors.append("source_health.external_send must be false")
    if summary.get("source_health_blocked") != source_health.get("sources_requiring_operator_review", 0):
        errors.append("summary.source_health_blocked must match operator source-health report")
    if summary.get("historical_source_health_blocked", 0) != source_health.get(
        "historical_sources_requiring_operator_review", 0
    ):
        errors.append(
            "summary.historical_source_health_blocked must match operator source-health report"
        )

    for index, item in enumerate(items):
        prefix = f"items[{index}]"
        if item.get("customer_delivery_allowed") is not False:
            errors.append(f"{prefix}.customer_delivery_allowed must be false")
        if item.get("delivery_approved") is True:
            errors.append(f"{prefix}.delivery_approved must not be true in an operator digest")
        if item.get("triage_status") == "REVIEW_READY" and not item.get("brief_input_eligible"):
            errors.append(f"{prefix} is REVIEW_READY without brief_input_eligible")
        if item.get("triage_status") == "READY_FOR_CUSTOMER_DELIVERY":
            errors.append(f"{prefix} uses forbidden customer-delivery triage status")
        if item.get("brief_input_eligible") and item.get("evidence_record_id") == "":
            errors.append(f"{prefix} is brief-input eligible without evidence_record_id")
        if not isinstance(item.get("blockers"), list):
            errors.append(f"{prefix}.blockers must be a list")
        if not isinstance(item.get("noise_indicators"), list):
            errors.append(f"{prefix}.noise_indicators must be a list")

    return errors


if __name__ == "__main__":
    raise SystemExit(main())
