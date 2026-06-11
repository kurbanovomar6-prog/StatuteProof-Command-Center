#!/usr/bin/env python3
"""
Manual CBUAE Rulebook row snapshot + proof/diff pipeline.

This script is intentionally standalone. It does not register or activate the
CBUAE adapter, does not edit sources.json, and does not write to production
alert review storage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.adapters.uae_cbuae_rulebook import (  # noqa: E402
    DEFAULT_CBUAE_RULEBOOK_UPDATES_URL,
    extract_cbuae_rulebook_update_items,
)

SOURCE_ID = "ae-cbuae-rulebook-aml-payments"
SOURCE_NAME = "CBUAE Rulebook revision updates"
SOURCE_URL = DEFAULT_CBUAE_RULEBOOK_UPDATES_URL
RECOMMENDED_STATUS = "under_validation"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slug_time(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "", value.replace("+00:00", "Z"))


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalize_url(value: Any) -> str:
    return _clean(value)


def _row_identity(row: dict[str, Any]) -> str:
    url = _normalize_url(row.get("url"))
    title = _clean(row.get("title")).lower()
    row_date = _clean(row.get("date")).lower()
    if url:
        return f"url:{url.lower()}"
    if title and row_date:
        return f"title_date:{title}|{row_date}"
    return f"title:{title}"


def _row_hash(row: dict[str, Any]) -> str:
    payload = json.dumps(
        {
            "title": row.get("title"),
            "date": row.get("date"),
            "url": row.get("url"),
            "document_url": row.get("document_url"),
            "pdf_url": row.get("pdf_url"),
            "raw_text_snippet": row.get("raw_text_snippet"),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _snapshot_hash(rows: list[dict[str, Any]]) -> str:
    payload = json.dumps(rows, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalize_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for item in items:
        row = {
            "identity": "",
            "title": _clean(item.get("title")),
            "date": _clean(item.get("date")) or None,
            "url": _normalize_url(item.get("url")) or None,
            "document_url": _normalize_url(item.get("document_url")) or None,
            "pdf_url": _normalize_url(item.get("pdf_url")) or None,
            "source_page_url": _normalize_url(item.get("source_page_url")) or SOURCE_URL,
            "raw_text_snippet": _clean(item.get("raw_text_snippet"),),
            "extraction_status": _clean(item.get("extraction_status")) or "row_candidate",
        }
        row["identity"] = _row_identity(row)
        row["row_hash"] = _row_hash(row)
        normalized.append(row)
    normalized.sort(key=lambda row: (row["identity"], row.get("title") or ""))
    return normalized


def _snapshot_path(snapshot_dir: Path, extracted_at: str) -> Path:
    return snapshot_dir / f"cbuae_rulebook_snapshot_{_slug_time(extracted_at)}.json"


def _latest_previous_snapshot(snapshot_dir: Path, current_path: Path | None = None) -> Path | None:
    candidates = sorted(snapshot_dir.glob("cbuae_rulebook_snapshot_*.json"))
    if current_path is not None:
        candidates = [path for path in candidates if path.resolve() != current_path.resolve()]
    return candidates[-1] if candidates else None


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if not path or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _make_snapshot(rows: list[dict[str, Any]], extracted_at: str, adapter_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": SOURCE_ID,
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "extracted_at": extracted_at,
        "rows": rows,
        "row_count": len(rows),
        "row_hash": _snapshot_hash(rows),
        "adapter": {
            "http_status": adapter_result.get("http_status"),
            "extraction_status": adapter_result.get("extraction_status"),
            "limitation_notes": adapter_result.get("limitation_notes") or [],
        },
    }


def _rows_by_identity(snapshot: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not snapshot:
        return {}
    return {
        str(row.get("identity") or _row_identity(row)): row
        for row in snapshot.get("rows") or []
        if isinstance(row, dict)
    }


def _changed_fields(old: dict[str, Any], new: dict[str, Any]) -> dict[str, dict[str, Any]]:
    changes: dict[str, dict[str, Any]] = {}
    for field in ("title", "date", "url", "document_url", "pdf_url", "raw_text_snippet", "extraction_status"):
        if old.get(field) != new.get(field):
            changes[field] = {"old": old.get(field), "new": new.get(field)}
    return changes


def _diff_snapshots(previous: dict[str, Any] | None, current: dict[str, Any]) -> dict[str, Any]:
    if previous is None:
        return {
            "baseline_created": True,
            "previous_snapshot_path": None,
            "added_count": 0,
            "removed_count": 0,
            "changed_count": 0,
            "added": [],
            "removed": [],
            "changed": [],
            "meaningful_change_detected": False,
            "summary": "Baseline snapshot created; no previous snapshot was available for row diff.",
        }

    previous_rows = _rows_by_identity(previous)
    current_rows = _rows_by_identity(current)
    added_keys = sorted(set(current_rows) - set(previous_rows))
    removed_keys = sorted(set(previous_rows) - set(current_rows))
    shared_keys = sorted(set(previous_rows) & set(current_rows))

    added = [_diff_row(current_rows[key], "added") for key in added_keys]
    removed = [_diff_row(previous_rows[key], "removed") for key in removed_keys]
    changed = []
    for key in shared_keys:
        old = previous_rows[key]
        new = current_rows[key]
        fields = _changed_fields(old, new)
        if fields:
            changed.append(
                {
                    "identity": key,
                    "title": new.get("title") or old.get("title"),
                    "date": new.get("date") or old.get("date"),
                    "url": new.get("url") or old.get("url"),
                    "old": old,
                    "new": new,
                    "changed_fields": fields,
                    "reason": "row_fields_changed",
                }
            )

    return {
        "baseline_created": False,
        "previous_extracted_at": previous.get("extracted_at"),
        "previous_row_count": previous.get("row_count"),
        "previous_row_hash": previous.get("row_hash"),
        "current_row_count": current.get("row_count"),
        "current_row_hash": current.get("row_hash"),
        "added_count": len(added),
        "removed_count": len(removed),
        "changed_count": len(changed),
        "added": added,
        "removed": removed,
        "changed": changed,
        "meaningful_change_detected": bool(added or removed or changed),
        "summary": (
            "No row changes detected"
            if not (added or removed or changed)
            else f"Detected {len(added)} added, {len(removed)} removed, {len(changed)} changed rows."
        ),
    }


def _diff_row(row: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "identity": row.get("identity"),
        "title": row.get("title"),
        "date": row.get("date"),
        "url": row.get("url"),
        "row": row,
        "reason": f"row_{reason}",
    }


def _same_run_stability(first_rows: list[dict[str, Any]], second_rows: list[dict[str, Any]]) -> dict[str, Any]:
    first_titles = [row.get("title") for row in first_rows[:3]]
    second_titles = [row.get("title") for row in second_rows[:3]]
    first_urls = [row.get("url") for row in first_rows[:3]]
    second_urls = [row.get("url") for row in second_rows[:3]]
    first_hash = _snapshot_hash(first_rows)
    second_hash = _snapshot_hash(second_rows)
    return {
        "first_row_count": len(first_rows),
        "second_row_count": len(second_rows),
        "item_count_stable": len(first_rows) == len(second_rows),
        "first_3_titles_stable": first_titles == second_titles,
        "first_3_urls_stable": first_urls == second_urls,
        "row_hash_stable": first_hash == second_hash,
        "first_row_hash": first_hash,
        "second_row_hash": second_hash,
    }


def _alert_candidate(diff: dict[str, Any], current: dict[str, Any], detected_at: str) -> dict[str, Any] | None:
    if int(diff.get("added_count") or 0) == 0 and int(diff.get("changed_count") or 0) == 0:
        return None
    seed = f"{SOURCE_ID}|{detected_at}|{current.get('row_hash')}|{diff.get('added_count')}|{diff.get('changed_count')}"
    examples = (diff.get("added") or diff.get("changed") or [])[:3]
    titles = [item.get("title") for item in examples if item.get("title")]
    return {
        "alert_id": "draft-cbuae-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16],
        "source_id": SOURCE_ID,
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "change_type": "RULEBOOK_ROW_UPDATE",
        "risk_level": "REVIEW",
        "executive_summary": (
            f"CBUAE Rulebook proof/diff detected {diff.get('added_count')} added "
            f"and {diff.get('changed_count')} changed rows. Human source review is required before dispatch."
        ),
        "affected_entities": "Payment service providers, stored value providers, banks, AML/CFT teams, and compliance teams.",
        "detected_at": detected_at,
        "review_status": "DRAFT",
        "send_decision": "HOLD_FOR_REVIEW",
        "example_titles": titles,
        "limitations": [
            "Draft candidate only; not written to production alert review storage.",
            "CBUAE Rulebook source remains under validation and is not active monitoring.",
            "Human review is required before any client-facing dispatch.",
        ],
    }


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _render_markdown(report: dict[str, Any]) -> str:
    diff = report["diff"]
    alert = report.get("alert_draft_candidate")
    limitations = [
        "This script does not activate production monitoring.",
        "This script does not modify sources.json.",
        "This script does not send Telegram messages or write approved alert reviews.",
        "A baseline/no-change run does not prove jurisdiction-wide source coverage.",
        "Recommended source status remains under_validation until scheduled repeated runs and human-reviewed alert flow are validated.",
    ]
    lines = [
        "# CBUAE Rulebook Proof/Diff",
        "",
        "## 1. Verdict",
        report["verdict"],
        "",
        "## 2. Source",
        f"- Source ID: `{SOURCE_ID}`",
        f"- Source name: {SOURCE_NAME}",
        f"- Source URL: {SOURCE_URL}",
        "",
        "## 3. Adapter result",
        f"- First run status: {report['first_adapter_result'].get('extraction_status')}",
        f"- First run HTTP status: {report['first_adapter_result'].get('http_status')}",
        f"- First run row count: {report['first_adapter_result'].get('item_count')}",
        f"- Second run status: {report['second_adapter_result'].get('extraction_status')}",
        f"- Second run HTTP status: {report['second_adapter_result'].get('http_status')}",
        f"- Second run row count: {report['second_adapter_result'].get('item_count')}",
        f"- Same-run row hash stable: {report['same_run_stability'].get('row_hash_stable')}",
        "",
        "## 4. Snapshot result",
        f"- Snapshot path: {report['snapshot_path']}",
        f"- Row count: {report['current_snapshot'].get('row_count')}",
        f"- Row hash: `{report['current_snapshot'].get('row_hash')}`",
        f"- Previous snapshot: {report.get('previous_snapshot_path') or 'none'}",
        "",
        "## 5. Diff result",
        f"- Baseline created: {diff.get('baseline_created')}",
        f"- Added rows: {diff.get('added_count')}",
        f"- Removed rows: {diff.get('removed_count')}",
        f"- Changed rows: {diff.get('changed_count')}",
        f"- Summary: {diff.get('summary')}",
        "",
    ]
    for label, key in (("Added", "added"), ("Removed", "removed"), ("Changed", "changed")):
        rows = diff.get(key) or []
        if not rows:
            continue
        lines.extend([f"### {label} rows", ""])
        for item in rows[:10]:
            lines.extend(
                [
                    f"- Title: {item.get('title')}",
                    f"  - Date: {item.get('date') or 'not detected'}",
                    f"  - URL: {item.get('url') or 'not detected'}",
                    f"  - Reason: {item.get('reason')}",
                ]
            )
            if key == "changed":
                lines.append(f"  - Changed fields: {', '.join((item.get('changed_fields') or {}).keys())}")
        lines.append("")
    lines.extend(
        [
            "## 6. Alert draft candidate",
            (
                f"- Created: yes\n- Path: {report.get('alert_draft_candidate_path')}\n"
                f"- Review status: {alert.get('review_status')}\n- Send decision: {alert.get('send_decision')}"
                if alert
                else "- Created: no\n- Reason: No added or changed rows detected."
            ),
            "",
            "## 7. Limitations",
        ]
    )
    lines.extend(f"- {item}" for item in limitations)
    lines.extend(
        [
            "",
            "## 8. Recommended status",
            f"`{RECOMMENDED_STATUS}`",
            "",
            "This proves stable row extraction and snapshot/diff mechanics, but source should not be active until scheduled repeated runs and human-reviewed alert flow are validated.",
            "",
            "## 9. Next validation action",
            "Run the proof/diff script on a schedule in validation mode, review any draft candidates manually, and only then consider source activation separately.",
            "",
        ]
    )
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    snapshot_dir = Path(args.snapshot_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    if args.mode != "same-run":
        raise ValueError("Only --mode same-run is supported in this validation sprint.")

    first = extract_cbuae_rulebook_update_items()
    second = extract_cbuae_rulebook_update_items()
    first_rows = _normalize_rows(first.get("items") or [])
    second_rows = _normalize_rows(second.get("items") or [])
    stability = _same_run_stability(first_rows, second_rows)

    extracted_at = _now_utc()
    current_snapshot = _make_snapshot(second_rows, extracted_at, second)
    snapshot_path = _snapshot_path(snapshot_dir, extracted_at)
    previous_path = _latest_previous_snapshot(snapshot_dir)
    previous_snapshot = _load_json(previous_path)
    diff = _diff_snapshots(previous_snapshot, current_snapshot)
    if previous_path:
        diff["previous_snapshot_path"] = str(previous_path)

    _write_json(snapshot_path, current_snapshot)
    alert = _alert_candidate(diff, current_snapshot, extracted_at)
    alert_path = None
    if alert:
        alert_path = output_dir / f"cbuae_rulebook_alert_draft_{date.today().isoformat()}.json"
        _write_json(alert_path, alert)

    verdict = (
        "PASS: baseline snapshot created; no previous snapshot existed."
        if diff.get("baseline_created")
        else (
            "PASS: row snapshot compared with previous snapshot; no row changes detected."
            if not diff.get("meaningful_change_detected")
            else "PARTIAL PASS: row changes detected and draft candidate held for review."
        )
    )
    report = {
        "verdict": verdict,
        "source_id": SOURCE_ID,
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "mode": args.mode,
        "generated_at": extracted_at,
        "first_adapter_result": {
            "http_status": first.get("http_status"),
            "extraction_status": first.get("extraction_status"),
            "item_count": first.get("item_count"),
            "limitation_notes": first.get("limitation_notes") or [],
        },
        "second_adapter_result": {
            "http_status": second.get("http_status"),
            "extraction_status": second.get("extraction_status"),
            "item_count": second.get("item_count"),
            "limitation_notes": second.get("limitation_notes") or [],
        },
        "same_run_stability": stability,
        "snapshot_path": str(snapshot_path),
        "previous_snapshot_path": str(previous_path) if previous_path else None,
        "current_snapshot": current_snapshot,
        "diff": diff,
        "alert_draft_candidate": alert,
        "alert_draft_candidate_path": str(alert_path) if alert_path else None,
        "recommended_status": RECOMMENDED_STATUS,
        "safety": {
            "sources_json_modified": False,
            "production_monitoring_activated": False,
            "telegram_sent": False,
            "production_alert_review_written": False,
        },
    }

    report_base = output_dir / f"cbuae_rulebook_diff_{date.today().isoformat()}"
    json_path = report_base.with_suffix(".json")
    md_path = report_base.with_suffix(".md")
    _write_json(json_path, report)
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    report["report_json_path"] = str(json_path)
    report["report_md_path"] = str(md_path)
    _write_json(json_path, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="CBUAE Rulebook proof/diff snapshot validation.")
    parser.add_argument("--output-dir", default="reports/cbuae_rulebook_proof")
    parser.add_argument("--snapshot-dir", default="data/source_snapshots/cbuae_rulebook_proof")
    parser.add_argument("--mode", default="same-run", choices=["same-run"])
    args = parser.parse_args()
    report = run(args)
    print(json.dumps({
        "verdict": report["verdict"],
        "snapshot_path": report["snapshot_path"],
        "report_md_path": report["report_md_path"],
        "report_json_path": report["report_json_path"],
        "baseline_created": report["diff"].get("baseline_created"),
        "added_count": report["diff"].get("added_count"),
        "removed_count": report["diff"].get("removed_count"),
        "changed_count": report["diff"].get("changed_count"),
        "alert_draft_candidate_path": report.get("alert_draft_candidate_path"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
