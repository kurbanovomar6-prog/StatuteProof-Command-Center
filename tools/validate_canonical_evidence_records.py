#!/usr/bin/env python3
"""Validate committed canonical evidence-record.json files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "product" / "regradar"
sys.path.insert(0, str(APP_ROOT))

from app.evidence_records import validate_evidence_record


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate canonical evidence records.")
    parser.add_argument("--base-dir", type=Path, default=APP_ROOT, help="Regradar base directory.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    base_dir = args.base_dir.resolve()
    records = sorted((base_dir / "evidence").glob("**/evidence-record.json"))
    errors: list[str] = []

    for path in records:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{_rel(path, base_dir)}: invalid JSON: {exc}")
            continue
        if not isinstance(record, dict):
            errors.append(f"{_rel(path, base_dir)}: evidence record must be a JSON object")
            continue
        validation = validate_evidence_record(record, base_dir=base_dir)
        if not validation.get("valid"):
            for message in validation.get("errors", []):
                errors.append(f"{_rel(path, base_dir)}: {message}")

    if errors:
        print("Canonical evidence records validation FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Canonical evidence records validation PASSED")
    print(f"- records={len(records)}")
    print("- All records are complete, hash-verifiable, and stored in the canonical evidence tree.")
    return 0


def _rel(path: Path, base_dir: Path) -> str:
    try:
        return str(path.relative_to(base_dir))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
