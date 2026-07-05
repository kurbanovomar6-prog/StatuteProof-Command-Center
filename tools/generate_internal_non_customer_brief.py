#!/usr/bin/env python3
"""Generate the first internal non-customer gated monitoring-to-brief cycle."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "product" / "regradar"
sys.path.insert(0, str(APP_ROOT))

from app.internal_brief_cycle import (
    InternalBriefCycleError,
    build_internal_non_customer_brief_cycle,
    write_internal_non_customer_brief_cycle,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an internal non-customer brief cycle.")
    parser.add_argument("--base-dir", type=Path, default=APP_ROOT, help="Regradar base directory.")
    parser.add_argument("--evidence-record-id", default="", help="Optional canonical evidence record ID.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = build_internal_non_customer_brief_cycle(
            evidence_record_id=args.evidence_record_id or None,
            base_dir=args.base_dir,
        )
        paths = write_internal_non_customer_brief_cycle(report, base_dir=args.base_dir)
    except InternalBriefCycleError as exc:
        print(f"generate_internal_non_customer_brief: FAILED: {exc}", file=sys.stderr)
        return 1

    print("Internal non-customer brief cycle generated")
    print(f"- report_id={report['report_id']}")
    print(f"- evidence_record_id={report['evidence']['evidence_record_id']}")
    print(f"- review_id={report['review']['review_id']}")
    print(f"- customer_delivery={report['customer_delivery']}")
    print(f"- delivery_approved={report['delivery_approved']}")
    print(f"- json_path={paths['json_path']}")
    print(f"- markdown_path={paths['markdown_path']}")
    if report.get("warnings"):
        print("- warnings=" + "; ".join(report["warnings"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
