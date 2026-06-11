#!/usr/bin/env python3
"""
Safe scheduled wrapper for CBUAE Rulebook proof/diff validation.

Intended for systemd timer or cron. This wrapper does not activate the source,
does not edit sources.json, does not send Telegram messages, and does not write
approved alert reviews.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.proof_diff_cbuae_rulebook import run as run_proof_diff  # noqa: E402

DEFAULT_OUTPUT_DIR = "reports/cbuae_rulebook_proof"
DEFAULT_SNAPSHOT_DIR = "data/source_snapshots/cbuae_rulebook_proof"
DEFAULT_MODE = "same-run"
LAST_RUN_FILENAME = "cbuae_rulebook_watch_last_run.json"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def build_summary(*, started_at: str, finished_at: str, success: bool, report: dict[str, Any] | None, error: str | None) -> dict[str, Any]:
    snapshot = (report or {}).get("current_snapshot") or {}
    diff = (report or {}).get("diff") or {}
    return {
        "run_started_at": started_at,
        "run_finished_at": finished_at,
        "success": success,
        "source_id": (report or {}).get("source_id") or "ae-cbuae-rulebook-aml-payments",
        "source_name": (report or {}).get("source_name") or "CBUAE Rulebook revision updates",
        "recommended_status": (report or {}).get("recommended_status") or "under_validation",
        "row_count": snapshot.get("row_count"),
        "added_count": diff.get("added_count"),
        "removed_count": diff.get("removed_count"),
        "changed_count": diff.get("changed_count"),
        "baseline_created": diff.get("baseline_created"),
        "report_path": (report or {}).get("report_md_path"),
        "report_json_path": (report or {}).get("report_json_path"),
        "snapshot_path": (report or {}).get("snapshot_path"),
        "alert_draft_candidate_path": (report or {}).get("alert_draft_candidate_path"),
        "telegram_sent": False,
        "automatic_delivery_enabled": False,
        "source_activated": False,
        "error_message": error,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run scheduled CBUAE Rulebook proof/diff validation once.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--snapshot-dir", default=DEFAULT_SNAPSHOT_DIR)
    parser.add_argument("--mode", default=DEFAULT_MODE, choices=["same-run"])
    args = parser.parse_args()

    started_at = now_utc()
    report: dict[str, Any] | None = None
    error: str | None = None
    success = False
    output_dir = Path(args.output_dir)
    last_run_path = output_dir / LAST_RUN_FILENAME

    try:
        report = run_proof_diff(SimpleNamespace(output_dir=args.output_dir, snapshot_dir=args.snapshot_dir, mode=args.mode))
        success = True
    except Exception as exc:  # Keep systemd diagnostics explicit.
        error = f"{type(exc).__name__}: {exc}"
    finally:
        finished_at = now_utc()
        summary = build_summary(started_at=started_at, finished_at=finished_at, success=success, report=report, error=error)
        write_json(last_run_path, summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
