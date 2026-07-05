#!/usr/bin/env python3
"""Validate the internal non-customer gated brief cycle."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "product" / "regradar"
sys.path.insert(0, str(APP_ROOT))

from app.internal_brief_cycle import (
    InternalBriefCycleError,
    load_internal_non_customer_brief_cycle,
    validate_internal_non_customer_brief_cycle,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate internal non-customer brief cycle.")
    parser.add_argument("--base-dir", type=Path, default=APP_ROOT, help="Regradar base directory.")
    parser.add_argument("--report", type=Path, default=None, help="Optional JSON report path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = load_internal_non_customer_brief_cycle(base_dir=args.base_dir, path=args.report)
    except InternalBriefCycleError as exc:
        print(f"Internal non-customer brief cycle validation FAILED: {exc}")
        return 1

    validation = validate_internal_non_customer_brief_cycle(report, base_dir=args.base_dir)
    if not validation["valid"]:
        print("Internal non-customer brief cycle validation FAILED")
        for error in validation["errors"]:
            print(f"- {error}")
        return 1

    print("Internal non-customer brief cycle validation PASSED")
    print(f"- report_id={report.get('report_id')}")
    print(f"- evidence_record_id={(report.get('evidence') or {}).get('evidence_record_id')}")
    print(f"- review_id={(report.get('review') or {}).get('review_id')}")
    print("- customer_delivery=false")
    print("- delivery_approved=false")
    for warning in validation.get("warnings") or []:
        print(f"- warning={warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
