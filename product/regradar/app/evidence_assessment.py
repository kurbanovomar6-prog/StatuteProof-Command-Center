"""Acknowledge & Assess records for saved source-run evidence.

This module is intentionally filesystem-backed for the MVP trust sprint. It
does not decide legal obligations; it records a human compliance review note
against an existing evidence/proof record.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_BASE_DIR = Path(__file__).parent.parent
_ASSESSMENT_DIR = _BASE_DIR / "data" / "evidence_assessments"
_ASSESSMENT_FILE = _ASSESSMENT_DIR / "assessments.jsonl"
LEGAL_DISCLAIMER = "Monitoring intelligence only. Not legal advice."

IMPACT_LEVELS = {
    "no_impact",
    "monitor",
    "policy_review",
    "escalate",
    "external_counsel_review",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def assessment_store_path(base_dir: Path | None = None) -> Path:
    root = base_dir or _BASE_DIR
    return root / "data" / "evidence_assessments" / "assessments.jsonl"


def load_assessments(base_dir: Path | None = None) -> list[dict[str, Any]]:
    path = assessment_store_path(base_dir)
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def latest_assessment_for(evidence_record_id: str, base_dir: Path | None = None) -> dict[str, Any] | None:
    wanted = str(evidence_record_id or "").strip()
    if not wanted:
        return None
    for row in reversed(load_assessments(base_dir=base_dir)):
        if row.get("evidence_record_id") == wanted:
            return row
    return None


def find_evidence_record(evidence_record_id: str, base_dir: Path | None = None) -> dict[str, Any]:
    wanted = str(evidence_record_id or "").strip()
    if not wanted:
        raise ValueError("evidence_record_id is required")
    root = base_dir or _BASE_DIR
    runs_path = root / "data" / "source_runs" / "source_runs.jsonl"
    if not runs_path.exists():
        raise ValueError("No saved evidence records are available")

    for line in runs_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(row.get("run_id") or "") == wanted:
            return row
    raise ValueError(f"Saved evidence record not found: {wanted}")


def validate_saved_evidence(record: dict[str, Any], base_dir: Path | None = None) -> None:
    root = base_dir or _BASE_DIR
    proof_path = str(record.get("proof_block_path") or "").strip()
    normalized_hash = str(record.get("normalized_hash") or record.get("content_hash") or "").strip()
    if not proof_path:
        raise ValueError("Cannot assess evidence without a proof path")
    resolved = Path(proof_path)
    if not resolved.is_absolute():
        resolved = root / resolved
    try:
        resolved.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("Evidence proof path is outside the workspace") from exc
    if not resolved.exists():
        raise ValueError("Cannot assess evidence because the proof artifact is missing")
    if not normalized_hash:
        raise ValueError("Cannot assess evidence without a normalized/content hash")


def create_assessment(
    *,
    evidence_record_id: str,
    impact_level: str,
    internal_note: str,
    reviewer_user_id: str | int | None = None,
    reviewer_name: str | None = None,
    next_action: str | None = None,
    assessment_status: str = "acknowledged",
    base_dir: Path | None = None,
) -> dict[str, Any]:
    impact = str(impact_level or "").strip()
    if impact not in IMPACT_LEVELS:
        raise ValueError("Unknown impact_level")
    note = str(internal_note or "").strip()
    if not note:
        raise ValueError("internal_note is required")

    record = find_evidence_record(evidence_record_id, base_dir=base_dir)
    validate_saved_evidence(record, base_dir=base_dir)

    reviewed_at = now_utc()
    assessment_id = _assessment_id(evidence_record_id, reviewed_at, reviewer_user_id, impact, note)
    assessment = {
        "assessment_id": assessment_id,
        "evidence_record_id": str(evidence_record_id),
        "source_id": record.get("source_id"),
        "source_name": record.get("source_name"),
        "official_url": record.get("official_url") or record.get("final_url"),
        "normalized_hash": record.get("normalized_hash") or record.get("content_hash"),
        "raw_hash": record.get("raw_hash"),
        "diff_path": record.get("diff_json_path") or record.get("diff_md_path"),
        "proof_path": record.get("proof_block_path"),
        "source_health_status": _source_health_status(record),
        "change_status": record.get("change_status"),
        "reviewer_user_id": str(reviewer_user_id or ""),
        "reviewer_name": str(reviewer_name or "").strip() or "Reviewer",
        "reviewed_at": reviewed_at,
        "impact_level": impact,
        "assessment_status": str(assessment_status or "acknowledged"),
        "internal_note": note,
        "next_action": str(next_action or "").strip(),
        "human_review_required": True,
        "legal_disclaimer": LEGAL_DISCLAIMER,
        "created_at": reviewed_at,
        "updated_at": reviewed_at,
    }
    _append_assessment(assessment, base_dir=base_dir)
    return assessment


def _source_health_status(record: dict[str, Any]) -> str:
    if record.get("change_status") in {"FAILED", "QUALITY_DROP"}:
        return str(record.get("change_status"))
    if str(record.get("access_status") or "").lower() in {"failed", "restricted"}:
        return str(record.get("access_status")).upper()
    return "MONITOR_OK"


def _append_assessment(record: dict[str, Any], base_dir: Path | None = None) -> None:
    path = assessment_store_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _assessment_id(
    evidence_record_id: str,
    reviewed_at: str,
    reviewer_user_id: str | int | None,
    impact_level: str,
    note: str,
) -> str:
    seed = f"{evidence_record_id}|{reviewed_at}|{reviewer_user_id}|{impact_level}|{note}"
    return "assessment-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]

