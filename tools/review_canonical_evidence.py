#!/usr/bin/env python3
"""Review canonical evidence records without mutating evidence-record.json."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "product" / "regradar"
sys.path.insert(0, str(APP_ROOT))

from app.evidence_records import (
    EvidenceRecordError,
    list_canonical_evidence_records,
    record_canonical_evidence_review,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="List or review canonical evidence records.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List canonical evidence records and latest review status.")
    list_parser.add_argument("--base-dir", type=Path, default=APP_ROOT)

    review_parser = subparsers.add_parser("review", help="Append an approval/rejection/block decision.")
    review_parser.add_argument("--base-dir", type=Path, default=APP_ROOT)
    review_parser.add_argument("--record-id", required=True)
    review_parser.add_argument("--decision", choices=["approved", "rejected", "blocked"], required=True)
    review_parser.add_argument("--reviewer", required=True)
    review_parser.add_argument("--note", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    base_dir = args.base_dir.resolve()
    try:
        if args.command == "list":
            rows = list_canonical_evidence_records(base_dir=base_dir)
            print("| Record ID | Source ID | Run Status | Record Review | Latest Review |")
            print("|---|---|---|---|---|")
            for row in rows:
                print(
                    "| {record_id} | {source_id} | {run_status} | {record_review_status} | {latest_review_decision} |".format(
                        record_id=row["record_id"],
                        source_id=row["source_id"],
                        run_status=row["run_status"],
                        record_review_status=row["record_review_status"],
                        latest_review_decision=row["latest_review_decision"] or "none",
                    )
                )
            print(f"records={len(rows)}")
            return 0
        if args.command == "review":
            row = record_canonical_evidence_review(
                args.record_id,
                decision=args.decision,
                reviewer=args.reviewer,
                note=args.note,
                base_dir=base_dir,
            )
            print(
                "canonical evidence review recorded "
                f"review_id={row['review_id']} "
                f"evidence_record_id={row['evidence_record_id']} "
                f"decision={row['decision']} "
                "customer_delivery_approved=false"
            )
            return 0
    except EvidenceRecordError as exc:
        print(f"review_canonical_evidence: FAILED: {exc}", file=sys.stderr)
        return 1
    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
