#!/usr/bin/env python3
"""Generate canonical evidence records from saved StatuteProof source runs.

Default mode is a dry-run. Use --write only after reviewing the generated
report; this tool must not turn source snapshot proof into customer evidence
without explicit operator action.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "product" / "regradar"
sys.path.insert(0, str(APP_ROOT))

from app.evidence_records import EvidenceRecordError, create_canonical_evidence_record


ELIGIBLE_STATUSES = {"FIRST_SEEN", "UNCHANGED", "CHANGED"}
BLOCKED_STATUSES = {"FAILED", "QUALITY_DROP"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate canonical evidence-record.json files from saved source_runs.jsonl rows.",
    )
    parser.add_argument("--base-dir", type=Path, default=APP_ROOT, help="Regradar base directory.")
    parser.add_argument("--source-id", action="append", default=[], help="Source ID to include. Repeatable.")
    parser.add_argument("--run-id", action="append", default=[], help="Exact source run ID to include. Repeatable.")
    parser.add_argument(
        "--status",
        action="append",
        default=[],
        help="Run change_status/status to include. Repeatable; examples: FIRST_SEEN, UNCHANGED, CHANGED.",
    )
    parser.add_argument("--limit", type=int, default=10, help="Maximum matching rows to review.")
    parser.add_argument("--write", action="store_true", help="Actually create canonical evidence records.")
    parser.add_argument("--dry-run", action="store_true", help="Review only; do not write evidence artifacts.")
    parser.add_argument(
        "--report-path",
        type=Path,
        default=None,
        help="Optional explicit report path. Defaults to reports/canonical_evidence_generation_<timestamp>.md.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    base_dir = args.base_dir.resolve()
    write = bool(args.write and not args.dry_run)

    try:
        runs = load_source_runs(base_dir)
    except OSError as exc:
        print(f"canonical evidence generation failed: {exc}", file=sys.stderr)
        return 1

    selected = select_runs(
        runs,
        source_ids={str(item).strip() for item in args.source_id if str(item).strip()},
        run_ids={str(item).strip() for item in args.run_id if str(item).strip()},
        statuses={str(item).strip().upper() for item in args.status if str(item).strip()},
        limit=max(int(args.limit or 0), 0),
    )
    results = generate_canonical_records(selected, base_dir=base_dir, write=write)
    report_path = write_report(
        results,
        base_dir=base_dir,
        report_path=args.report_path,
        write=write,
        filters={
            "source_id": sorted({str(item).strip() for item in args.source_id if str(item).strip()}),
            "run_id": sorted({str(item).strip() for item in args.run_id if str(item).strip()}),
            "status": sorted({str(item).strip().upper() for item in args.status if str(item).strip()}),
            "limit": max(int(args.limit or 0), 0),
        },
    )

    print(f"Canonical evidence generation report: {_rel(report_path, base_dir)}")
    counts = count_results(results)
    print(
        "canonical evidence generation "
        f"mode={'write' if write else 'dry-run'} "
        f"reviewed={len(results)} "
        f"created={counts.get('created', 0)} "
        f"would_create={counts.get('would_create', 0)} "
        f"not_eligible={counts.get('not_eligible', 0)} "
        f"existing={counts.get('existing', 0)} "
        f"errors={counts.get('error', 0)}"
    )
    return 1 if counts.get("error", 0) else 0


def load_source_runs(base_dir: Path) -> list[dict[str, Any]]:
    run_file = base_dir / "data" / "source_runs" / "source_runs.jsonl"
    if not run_file.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(run_file.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            rows.append({"_line_no": line_no, "_parse_error": "invalid JSON line"})
            continue
        if isinstance(parsed, dict):
            parsed["_line_no"] = line_no
            rows.append(parsed)
    return rows


def select_runs(
    runs: list[dict[str, Any]],
    *,
    source_ids: set[str],
    run_ids: set[str],
    statuses: set[str],
    limit: int,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for row in reversed(runs):
        source_id = str(row.get("source_id") or "").strip()
        status = run_status(row)
        if source_ids and source_id not in source_ids:
            continue
        if run_ids and str(row.get("run_id") or "").strip() not in run_ids:
            continue
        if statuses and status not in statuses:
            continue
        selected.append(row)
        if limit and len(selected) >= limit:
            break
    return selected


def generate_canonical_records(
    runs: list[dict[str, Any]],
    *,
    base_dir: Path,
    write: bool,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for row in runs:
        result = review_run(row, base_dir=base_dir)
        if write and result["status"] == "would_create":
            try:
                record = create_canonical_evidence_record(row, base_dir=base_dir)
            except EvidenceRecordError as exc:
                result["status"] = "error"
                result["reason"] = str(exc)
            else:
                result["status"] = "created"
                result["record_id"] = record["record_id"]
                result["record_path"] = _record_path_for(record, base_dir)
        results.append(result)
    return results


def review_run(row: dict[str, Any], *, base_dir: Path) -> dict[str, Any]:
    source_id = str(row.get("source_id") or "").strip()
    run_id = str(row.get("run_id") or "").strip()
    status = run_status(row)
    result = {
        "source_id": source_id or "<missing>",
        "run_id": run_id or "<missing>",
        "run_status": status or "<missing>",
        "timestamp_utc": str(row.get("timestamp_utc") or row.get("run_at") or row.get("timestamp") or "").strip(),
        "status": "would_create",
        "reason": "",
        "record_id": "",
        "record_path": "",
        "line_no": row.get("_line_no", ""),
    }
    if row.get("_parse_error"):
        result["status"] = "not_eligible"
        result["reason"] = str(row["_parse_error"])
        return result
    missing = [key for key in ("run_id", "source_id", "source_name", "official_url", "timestamp_utc") if not row.get(key)]
    if missing:
        result["status"] = "not_eligible"
        result["reason"] = f"missing required run fields: {', '.join(missing)}"
        return result
    if status in BLOCKED_STATUSES:
        result["status"] = "not_eligible"
        result["reason"] = f"run status {status} is blocked from canonical evidence"
        return result
    if status not in ELIGIBLE_STATUSES:
        result["status"] = "not_eligible"
        result["reason"] = f"run status {status or '<missing>'} is not eligible"
        return result

    for key in ("proof_block_path", "snapshot_raw_path", "snapshot_normalized_path", "snapshot_metadata_path"):
        value = str(row.get(key) or "").strip()
        if not value:
            result["status"] = "not_eligible"
            result["reason"] = f"{key} is missing"
            return result
        artifact_path = _safe_path(base_dir, value)
        if artifact_path is None or not artifact_path.exists() or artifact_path.is_dir():
            result["status"] = "not_eligible"
            result["reason"] = f"{key} does not exist: {value}"
            return result

    normalized_path = _safe_path(base_dir, str(row.get("snapshot_normalized_path") or ""))
    normalized_hash = normalize_hash(row.get("normalized_hash"))
    if not normalized_hash:
        result["status"] = "not_eligible"
        result["reason"] = "normalized_hash is missing or invalid"
        return result
    if normalized_path is None:
        result["status"] = "not_eligible"
        result["reason"] = "snapshot_normalized_path is outside the workspace"
        return result
    if normalized_hash != f"sha256:{hash_file(normalized_path)}":
        result["status"] = "not_eligible"
        result["reason"] = "normalized_hash does not match snapshot_normalized_path"
        return result

    record_path = expected_record_path(row, base_dir)
    if record_path.exists():
        result["status"] = "existing"
        result["reason"] = "canonical evidence record already exists"
        result["record_path"] = _rel(record_path, base_dir)
        result["record_id"] = canonical_record_id(source_id, run_id)
        return result

    result["record_id"] = canonical_record_id(source_id, run_id)
    result["record_path"] = _rel(record_path, base_dir)
    return result


def write_report(
    results: list[dict[str, Any]],
    *,
    base_dir: Path,
    report_path: Path | None,
    write: bool,
    filters: dict[str, Any],
) -> Path:
    if report_path is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report_path = base_dir / "reports" / f"canonical_evidence_generation_{stamp}.md"
    elif not report_path.is_absolute():
        report_path = base_dir / report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)

    counts = count_results(results)
    lines = [
        "# Canonical Evidence Generation Report",
        "",
        f"- Generated at: {datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')}",
        f"- Mode: {'write' if write else 'dry-run'}",
        f"- Source filters: {', '.join(filters['source_id']) if filters['source_id'] else 'all'}",
        f"- Run filters: {', '.join(filters['run_id']) if filters['run_id'] else 'all'}",
        f"- Status filters: {', '.join(filters['status']) if filters['status'] else 'all'}",
        f"- Limit: {filters['limit']}",
        f"- Reviewed runs: {len(results)}",
        f"- created: {counts.get('created', 0)}",
        f"- would_create: {counts.get('would_create', 0)}",
        f"- existing: {counts.get('existing', 0)}",
        f"- not_eligible: {counts.get('not_eligible', 0)}",
        f"- errors: {counts.get('error', 0)}",
        "",
        "| Status | Source ID | Run ID | Run Status | Record ID | Reason |",
        "|---|---|---|---|---|---|",
    ]
    for item in results:
        lines.append(
            "| {status} | {source_id} | {run_id} | {run_status} | {record_id} | {reason} |".format(
                status=_md(item.get("status")),
                source_id=_md(item.get("source_id")),
                run_id=_md(item.get("run_id")),
                run_status=_md(item.get("run_status")),
                record_id=_md(item.get("record_id")),
                reason=_md(item.get("reason")),
            )
        )
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def count_results(results: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in results:
        status = str(item.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def run_status(row: dict[str, Any]) -> str:
    return str(row.get("change_status") or row.get("status") or "").strip().upper()


def normalize_hash(value: Any) -> str:
    text = str(value or "").strip().lower()
    if len(text) == 64 and all(char in "0123456789abcdef" for char in text):
        return f"sha256:{text}"
    if text.startswith("sha256:") and len(text) == 71:
        return text
    return ""


def expected_record_path(row: dict[str, Any], base_dir: Path) -> Path:
    source_id = str(row.get("source_id") or "").strip()
    run_id = str(row.get("run_id") or "").strip()
    regulator_slug = regulator_slug_for(row)
    return base_dir / "evidence" / regulator_slug / source_id / run_id / "evidence-record.json"


def regulator_slug_for(row: dict[str, Any]) -> str:
    explicit = str(row.get("regulator") or row.get("family") or "").strip()
    haystack = " ".join(
        [
            explicit.lower(),
            str(row.get("source_id") or "").lower(),
            str(row.get("source_name") or "").lower(),
        ]
    )
    mapping = [
        ("cbuae", "CBUAE"),
        ("central-bank", "CBUAE"),
        ("vara", "VARA"),
        ("dfsa", "DFSA"),
        ("adgm-fsra", "ADGM FSRA"),
        ("fsra", "ADGM FSRA"),
        ("adgm", "ADGM"),
        ("difc", "DIFC"),
        ("fiu", "UAE FIU"),
        ("uaefiu", "UAE FIU"),
        ("mof", "UAE Ministry of Finance"),
        ("finance", "UAE Ministry of Finance"),
        ("sca", "SCA"),
        ("fta", "FTA"),
        ("tax", "FTA"),
        ("moj", "UAE Ministry of Justice"),
        ("gazette", "UAE Gazette"),
        ("eocn", "EOCN"),
    ]
    for token, name in mapping:
        if token in haystack:
            return slugify(name)
    if explicit:
        return slugify(explicit)
    market = str(row.get("market") or row.get("jurisdiction") or "unknown").strip().upper() or "UNKNOWN"
    return market.lower()


def canonical_record_id(source_id: str, run_id: str) -> str:
    import re

    seed = re.sub(r"[^A-Za-z0-9_.:-]+", "_", f"{source_id}_{run_id}").strip("_")
    return f"evr_{seed}"


def slugify(value: str) -> str:
    import re

    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "unknown"


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_path(base_dir: Path, value: str) -> Path | None:
    try:
        resolved = (base_dir / value).resolve() if not Path(value).is_absolute() else Path(value).resolve()
        resolved.relative_to(base_dir.resolve())
    except ValueError:
        return None
    return resolved


def _record_path_for(record: dict[str, Any], base_dir: Path) -> str:
    source_id = str(record["source"]["source_id"])
    run_id = str(record["run"]["run_id"])
    regulator_slug = slugify(str(record["source"]["regulator"]))
    return _rel(base_dir / "evidence" / regulator_slug / source_id / run_id / "evidence-record.json", base_dir)


def _rel(path: Path, base_dir: Path) -> str:
    try:
        return str(path.relative_to(base_dir))
    except ValueError:
        return str(path)


def _md(value: Any) -> str:
    text = str(value or "")
    return text.replace("|", "\\|").replace("\n", " ").strip()


if __name__ == "__main__":
    raise SystemExit(main())
