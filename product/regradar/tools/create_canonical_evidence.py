"""
Create canonical evidence records from existing source runs.

Usage:
    python tools/create_canonical_evidence.py
    python tools/create_canonical_evidence.py --dry-run
    python tools/create_canonical_evidence.py --source-id AE-sca-aml-cft
    python tools/create_canonical_evidence.py --source-id AE-sca-aml-cft --dry-run
    python tools/create_canonical_evidence.py --limit 10
    python tools/create_canonical_evidence.py --all-statuses  # include FIRST_SEEN/UNCHANGED

What it does:
    1. Reads all records from data/source_runs/source_runs.jsonl
    2. Filters to CHANGED records that have:
       - proof_block_path pointing to a saved proof.json
       - snapshot_normalized_path, snapshot_raw_path, snapshot_metadata_path on disk
       - normalized_hash present
       - A valid previous run (also with a snapshot on disk)
    3. Skips records that already have a canonical evidence record written
    4. For each eligible record:
       - Calls create_canonical_evidence_record() which copies artifacts into
         evidence/<regulator_slug>/<source_id>/<run_id>/evidence-record.json
       - The schema_version 2.0 record includes source, run, content, change,
         files, integrity, and review sections
    5. Prints per-record progress and a final summary

The canonical evidence store is evidence/ (not data/evidence_reviews/).
The JSONL at data/evidence_reviews/canonical_evidence_reviews.jsonl stores
human review *decisions* written by record_canonical_evidence_review() --
it is separate from the evidence records themselves.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# sys.path bootstrap — make app/ importable when run directly from the repo
# ---------------------------------------------------------------------------

_TOOLS_DIR = Path(__file__).resolve().parent
_PRODUCT_DIR = _TOOLS_DIR.parent   # .../product/regradar
if str(_PRODUCT_DIR) not in sys.path:
    sys.path.insert(0, str(_PRODUCT_DIR))


# ---------------------------------------------------------------------------
# imports (after sys.path is set)
# ---------------------------------------------------------------------------

from app.evidence_records import (   # noqa: E402
    EvidenceRecordError,
    _find_previous_evidence_run,
    create_canonical_evidence_record,
)


# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------

_BASE = _PRODUCT_DIR
_RUN_FILE = _BASE / "data" / "source_runs" / "source_runs.jsonl"
_EVIDENCE_DIR = _BASE / "evidence"

_ELIGIBLE_STATUSES = {"CHANGED", "FIRST_SEEN", "UNCHANGED"}
_DEFAULT_STATUSES = {"CHANGED"}   # subset used without --all-statuses


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _read_runs() -> list[dict]:
    if not _RUN_FILE.exists():
        print(f"ERROR: source_runs.jsonl not found at {_RUN_FILE}", file=sys.stderr)
        sys.exit(1)
    rows: list[dict] = []
    for lineno, raw in enumerate(_RUN_FILE.read_text(encoding="utf-8").splitlines(), 1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            rows.append(json.loads(raw))
        except json.JSONDecodeError as exc:
            print(f"  WARN: skipping malformed line {lineno}: {exc}", file=sys.stderr)
    return rows


def _has_required_artifacts(record: dict) -> bool:
    """Return True only when all snapshot artifact paths are present on disk."""
    for key in ("proof_block_path", "snapshot_normalized_path", "snapshot_raw_path", "snapshot_metadata_path"):
        value = record.get(key)
        if not value:
            return False
        path = Path(value)
        if not path.is_absolute():
            path = _BASE / path
        if not path.exists():
            return False
    if not record.get("normalized_hash"):
        return False
    return True


def _evidence_record_exists(source_id: str, run_id: str) -> bool:
    """Return True when an evidence-record.json already exists for this run."""
    for candidate in _EVIDENCE_DIR.glob(f"*/{source_id}/{run_id}/evidence-record.json"):
        if candidate.exists():
            return True
    return False


# ---------------------------------------------------------------------------
# main logic
# ---------------------------------------------------------------------------

def run_create(
    *,
    source_id_filter: str | None = None,
    dry_run: bool = False,
    all_statuses: bool = False,
    limit: int | None = None,
) -> None:
    rows = _read_runs()
    target_statuses = _ELIGIBLE_STATUSES if all_statuses else _DEFAULT_STATUSES

    candidates = [
        r for r in rows
        if r.get("change_status") in target_statuses
        and (source_id_filter is None or r.get("source_id") == source_id_filter)
        and _has_required_artifacts(r)
    ]

    print(f"Source runs total:              {len(rows)}")
    print(f"Candidates with artifacts:      {len(candidates)}")
    if source_id_filter:
        print(f"Filtered to source:             {source_id_filter}")
    print()

    processed = 0
    skipped = 0
    failed = 0
    written: list[str] = []
    skip_details: list[str] = []
    fail_details: list[str] = []

    for record in candidates:
        if limit is not None and processed + len(written) >= limit:
            break

        source_id = str(record.get("source_id") or "unknown")
        run_id = str(record.get("run_id") or "unknown")
        label = f"{source_id} / {run_id}"

        if _evidence_record_exists(source_id, run_id):
            skipped += 1
            skip_details.append(f"  · skip   {label}  (evidence record already exists)")
            continue

        # Find the previous run (required for non-FIRST_SEEN records)
        change_status = str(record.get("change_status") or "")
        previous_run: dict | None = None
        if change_status != "FIRST_SEEN":
            previous_run = _find_previous_evidence_run(record, _BASE)
            if previous_run is None or not previous_run.get("snapshot_normalized_path"):
                skipped += 1
                skip_details.append(
                    f"  · skip   {label}  (no previous run with snapshot for {change_status} record)"
                )
                continue

        if dry_run:
            print(f"  ? dry-run {label}")
            print(f"           change_status={change_status}")
            if previous_run:
                print(f"           previous_run={previous_run.get('run_id')}")
            processed += 1
            continue

        try:
            result = create_canonical_evidence_record(record, previous_run, base_dir=_BASE)
            record_id = result.get("record_id", "")
            record_path = result.get("files", {}).get("snapshot_path", "")
            processed += 1
            # The evidence-record.json lives alongside the snapshot:
            # evidence/<regulator_slug>/<source_id>/<run_id>/evidence-record.json
            # We derive that path from the record structure.
            regulator_parts = str(record_path).split("/")
            if len(regulator_parts) >= 2:
                ev_path = f"evidence/{regulator_parts[1]}/{source_id}/{run_id}/evidence-record.json"
            else:
                ev_path = f"evidence/<regulator>/{source_id}/{run_id}/evidence-record.json"
            written.append(ev_path)
            print(
                f"  + wrote  {label}"
                f"\n           record_id={record_id}"
                f"\n           {ev_path}"
            )
        except EvidenceRecordError as exc:
            failed += 1
            fail_details.append(f"  ! FAILED {label}: {exc}")
            print(f"  ! FAILED {label}: {exc}", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            fail_details.append(f"  ! FAILED {label}: {type(exc).__name__}: {exc}")
            print(f"  ! FAILED {label}: {type(exc).__name__}: {exc}", file=sys.stderr)

    # Summary
    print()
    print("─" * 80)
    if skip_details:
        for line in skip_details:
            print(line)
        print()
    if fail_details:
        for line in fail_details:
            print(line)
        print()

    qualifier = " (dry-run — nothing written)" if dry_run else ""
    print(f"Canonical evidence creation complete{qualifier}")
    print(f"  Created              : {processed}")
    print(f"  Skipped (exist/prev) : {skipped}")
    print(f"  Failed               : {failed}")

    if written and not dry_run:
        print()
        print("Written paths:")
        for p in written:
            print(f"  {p}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create canonical evidence records from existing CHANGED source runs."
    )
    parser.add_argument(
        "--source-id",
        metavar="SOURCE_ID",
        default=None,
        help="Only process runs for this source_id.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be written without writing anything.",
    )
    parser.add_argument(
        "--all-statuses",
        action="store_true",
        help="Include FIRST_SEEN and UNCHANGED in addition to CHANGED.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Stop after creating N evidence records.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_create(
        source_id_filter=args.source_id,
        dry_run=args.dry_run,
        all_statuses=args.all_statuses,
        limit=args.limit,
    )
