"""
Backfill alert_draft.json + alert_draft.md for CHANGED source runs that
were detected but never had alert artifacts written.

Usage:
    python tools/backfill_alert_drafts.py
    python tools/backfill_alert_drafts.py --dry-run

What it does:
    1. Reads all records from data/source_runs/source_runs.jsonl
    2. Filters to records where change_status == "CHANGED"
    3. Skips records that already have an alert_draft.json on disk
    4. For each remaining CHANGED record:
       - Loads the diff artifact from diff_json_path (or synthesises a fallback)
       - Loads the proof block from proof_block_path (or synthesises a fallback)
       - Calls build_alert_draft(run_record, diff, proof)
       - Resolves the snapshot directory from the proof block
       - Falls back to data/alert_drafts/<source_id>/<run_id>/ when the
         snapshot directory cannot be resolved from the proof block
       - Calls write_alert_artifacts(alert, snapshot_dir)
    5. Prints per-record progress and a final summary table
"""

from __future__ import annotations

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

from app.alert_drafts import (   # noqa: E402
    build_alert_draft,
    load_json_artifact,
    snapshot_dir_from_proof,
    write_alert_artifacts,
)
from app.proof import build_source_proof  # noqa: E402


# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------

_BASE = _PRODUCT_DIR
_RUN_FILE = _BASE / "data" / "source_runs" / "source_runs.jsonl"
_FALLBACK_DRAFT_DIR = _BASE / "data" / "alert_drafts"

_INCOMPLETE_DIFF: dict = {
    "diff_quality": "INCOMPLETE",
    "meaningful_change_detected": False,
    "diff_summary": "Diff artifact unavailable; backfill created for human review.",
    "limitations": ["Diff artifact unavailable; backfill created for human review."],
    "added_chunks": [],
    "removed_chunks": [],
    "changed_chunks": [],
    "added_count": 0,
    "removed_count": 0,
    "changed_count": 0,
}


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
            print(f"  WARN: skipping malformed line {lineno}: {exc}")
    return rows


def _alert_draft_path_for(record: dict, proof: dict) -> Path | None:
    """Return the alert_draft.json path if the snapshot directory can be resolved."""
    snap_dir = snapshot_dir_from_proof(proof, _BASE)
    if snap_dir is not None:
        return snap_dir / "alert_draft.json"
    # Fall back to snapshot path from the run record itself
    for key in ("snapshot_normalized_path", "snapshot_raw_path"):
        rel = record.get(key)
        if rel:
            candidate = Path(rel)
            if not candidate.is_absolute():
                candidate = _BASE / candidate
            return candidate.parent / "alert_draft.json"
    return None


def _fallback_snapshot_dir(record: dict) -> Path:
    """Return a stable fallback directory under data/alert_drafts/."""
    source_id = str(record.get("source_id") or "unknown")
    run_id = str(record.get("run_id") or "unknown")
    return _FALLBACK_DRAFT_DIR / source_id / run_id


def _already_has_draft(record: dict, proof: dict) -> tuple[bool, Path | None]:
    """Check whether alert_draft.json already exists for this run."""
    draft_path = _alert_draft_path_for(record, proof)
    if draft_path is not None and draft_path.exists():
        return True, draft_path
    # Also check the fallback location
    fallback = _fallback_snapshot_dir(record) / "alert_draft.json"
    if fallback.exists():
        return True, fallback
    return False, draft_path


def _resolve_snapshot_dir(record: dict, proof: dict) -> Path:
    """Return the snapshot directory to write artifacts into.

    Priority:
    1. Snapshot directory derived from proof block paths
    2. Snapshot directory derived from run record snapshot paths
    3. Fallback: data/alert_drafts/<source_id>/<run_id>/
    """
    snap_dir = snapshot_dir_from_proof(proof, _BASE)
    if snap_dir is not None:
        return snap_dir
    for key in ("snapshot_normalized_path", "snapshot_raw_path"):
        rel = record.get(key)
        if rel:
            candidate = Path(rel)
            if not candidate.is_absolute():
                candidate = _BASE / candidate
            return candidate.parent
    return _fallback_snapshot_dir(record)


# ---------------------------------------------------------------------------
# main backfill logic
# ---------------------------------------------------------------------------

def run_backfill(*, dry_run: bool = False) -> None:
    rows = _read_runs()
    changed = [r for r in rows if r.get("change_status") == "CHANGED"]

    print(f"Source runs total:   {len(rows)}")
    print(f"CHANGED runs:        {len(changed)}")
    print()

    processed = 0
    skipped = 0
    failed = 0
    written: list[str] = []
    skip_details: list[str] = []
    fail_details: list[str] = []

    for record in changed:
        source_id = str(record.get("source_id") or "unknown")
        run_id = str(record.get("run_id") or "unknown")
        label = f"{source_id} / {run_id}"

        try:
            # Load diff and proof from recorded paths (or synthesise fallbacks)
            diff = load_json_artifact(record.get("diff_json_path"), _BASE)
            if not diff:
                diff = dict(_INCOMPLETE_DIFF)

            proof = load_json_artifact(record.get("proof_block_path"), _BASE)
            if not proof:
                # Synthesise a minimal proof block directly from the run record
                proof = build_source_proof(record, diff if diff != _INCOMPLETE_DIFF else None)

            # Skip if alert_draft.json already exists
            already_done, existing_path = _already_has_draft(record, proof)
            if already_done:
                skipped += 1
                skip_details.append(f"  · skip   {label}  (draft exists: {existing_path})")
                continue

            if dry_run:
                snap_dir = _resolve_snapshot_dir(record, proof)
                print(f"  ? dry-run {label}")
                print(f"           would write to: {snap_dir / 'alert_draft.json'}")
                processed += 1
                continue

            # Build the alert draft
            alert = build_alert_draft(record, diff, proof)

            # Resolve the output directory
            snap_dir = _resolve_snapshot_dir(record, proof)

            # Write artifacts
            paths = write_alert_artifacts(alert, snap_dir)

            processed += 1
            written.append(paths.get("alert_draft_json_path", str(snap_dir / "alert_draft.json")))
            print(
                f"  + wrote  {label}"
                f"\n           change_type={alert.get('change_type')}"
                f"  risk={alert.get('risk_level')}"
                f"\n           {paths.get('alert_draft_json_path', snap_dir)}"
            )

        except Exception as exc:  # noqa: BLE001
            failed += 1
            fail_details.append(f"  ! FAILED {label}: {exc}")
            print(f"  ! FAILED {label}: {exc}")

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
    print(f"Backfill complete{qualifier}")
    print(f"  Processed / written : {processed}")
    print(f"  Skipped (had draft) : {skipped}")
    print(f"  Failed              : {failed}")

    if written and not dry_run:
        print()
        print("Written paths:")
        for p in written:
            print(f"  {p}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _dry = "--dry-run" in sys.argv
    run_backfill(dry_run=_dry)
