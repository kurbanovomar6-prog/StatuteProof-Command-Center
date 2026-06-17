"""Global MLRO review queue built from saved evidence and assessments.

Includes accountability logging: reviewers can record an action taken
(accepted / not_applicable / escalated) against any review record, creating
a non-repudiation audit trail for compliance purposes.
"""

from __future__ import annotations

import fcntl
import json
import logging
from pathlib import Path
from typing import Any

from app.evidence_assessment import LEGAL_DISCLAIMER, load_assessments, now_utc
from app.source_health_timeline import source_health_customer_message

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).parent.parent
_VALID_ACTIONS = {"accepted", "not_applicable", "escalated"}


def build_review_queue(
    *,
    market: str = "AE",
    status: str = "pending",
    impact_level: str | None = None,
    source_health_status: str | None = None,
    change_status: str | None = None,
    source_id: str | None = None,
    limit: int = 50,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Return review queue rows from recorded evidence and Acknowledge & Assess records."""
    root = base_dir or _BASE_DIR
    market_code = str(market or "AE").upper().strip() or "AE"
    requested_status = str(status or "pending").lower().strip()
    if requested_status not in {"pending", "assessed", "all"}:
        requested_status = "pending"

    latest_assessments = _latest_assessments_by_evidence(root)
    rows: list[dict[str, Any]] = []
    for run in _read_runs(root, market_code):
        evidence_id = str(run.get("run_id") or "").strip()
        if not evidence_id:
            continue
        assessment = latest_assessments.get(evidence_id)
        pending = assessment is None
        if requested_status == "pending" and not pending:
            continue
        if requested_status == "assessed" and pending:
            continue

        row_source_id = str(run.get("source_id") or "").strip()
        row_change_status = str(run.get("change_status") or "UNKNOWN").upper()
        row_health = _source_health_status(run)
        row_impact = str((assessment or {}).get("impact_level") or "").strip()

        if source_id and row_source_id != source_id:
            continue
        if change_status and row_change_status != str(change_status).upper().strip():
            continue
        if source_health_status and row_health != str(source_health_status).upper().strip():
            continue
        if impact_level and row_impact != str(impact_level).strip():
            continue

        rows.append(_queue_row(run, assessment, source_health_status=row_health, pending=pending))

    rows.sort(key=lambda item: str(item.get("timestamp_utc") or ""), reverse=True)
    safe_limit = max(1, min(int(limit or 50), 200))
    return {
        "ok": True,
        "market": market_code,
        "status": requested_status,
        "queue": rows[:safe_limit],
        "total": len(rows),
        "disclaimer": LEGAL_DISCLAIMER,
        "message": "Review queue is built from saved evidence records and Acknowledge & Assess records only.",
    }


def _queue_row(
    run: dict[str, Any],
    assessment: dict[str, Any] | None,
    *,
    source_health_status: str,
    pending: bool,
) -> dict[str, Any]:
    """Build a single review queue row, including accountability fields."""
    evidence_id = str(run.get("run_id") or "")
    normalized_hash = str(run.get("normalized_hash") or run.get("content_hash") or "")
    # Load the latest accountability action for this record (if any)
    action_record = _latest_action_for(evidence_id)
    return {
        "evidence_record_id": evidence_id,
        "source_id": run.get("source_id"),
        "source_name": run.get("source_name") or run.get("name"),
        "official_url": run.get("official_url") or run.get("final_url"),
        "timestamp_utc": run.get("timestamp_utc") or run.get("run_at"),
        "change_status": str(run.get("change_status") or "UNKNOWN").upper(),
        "source_health_status": source_health_status,
        "extraction_quality": run.get("extraction_quality") or "UNKNOWN",
        "normalized_hash": normalized_hash,
        "normalized_hash_short": normalized_hash[:12] if normalized_hash else "",
        "proof_path": run.get("proof_block_path"),
        "diff_path": run.get("diff_json_path") or run.get("diff_md_path"),
        "assessment_status": (assessment or {}).get("assessment_status") or ("pending" if pending else "assessed"),
        "latest_assessment_id": (assessment or {}).get("assessment_id"),
        "impact_level": (assessment or {}).get("impact_level"),
        "reviewer": (assessment or {}).get("reviewer_name") or (assessment or {}).get("reviewer_user_id"),
        "reviewed_at": (assessment or {}).get("reviewed_at"),
        "pending_review": pending,
        "customer_safe_message": source_health_customer_message(source_health_status),
        # Accountability fields
        "action_taken": action_record.get("action") if action_record else None,
        "action_user_id": action_record.get("user_id") if action_record else None,
        "action_reason": action_record.get("reason") if action_record else None,
        "action_timestamp": action_record.get("action_timestamp") if action_record else None,
    }


def _latest_assessments_by_evidence(root: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in load_assessments(base_dir=root):
        evidence_id = str(row.get("evidence_record_id") or "")
        if evidence_id:
            latest[evidence_id] = row
    return latest


def _read_runs(root: Path, market: str) -> list[dict[str, Any]]:
    path = root / "data" / "source_runs" / "source_runs.jsonl"
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(row.get("market") or row.get("jurisdiction") or "").upper() == market:
            rows.append(row)
    return rows


def _source_health_status(run: dict[str, Any]) -> str:
    change = str(run.get("change_status") or "").upper()
    access = str(run.get("access_status") or "").lower()
    quality = str(run.get("extraction_quality") or "").upper()
    if change == "QUALITY_DROP" or quality == "FAILED":
        return "QUALITY_DROP"
    if change == "FAILED":
        return "FAILED"
    if access in {"failed", "restricted", "blocked"}:
        return "ACCESS_BLOCKED"
    if change == "CHANGED":
        return "HASH_DRIFT"
    return "MONITOR_OK"


# ── Accountability logging ─────────────────────────────────────────────────────

def record_review_action(
    record_id: str,
    action: str,
    user_id: str,
    reason: str = "",
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Record an accountability action taken by a reviewer on a review record.

    Parameters
    ----------
    record_id:
        The evidence_record_id of the review item being actioned.
    action:
        One of "accepted", "not_applicable", "escalated".
    user_id:
        Non-empty identifier for the reviewer (email or user ID).
    reason:
        Optional free-text reason; truncated to 500 chars.
    base_dir:
        Override for the data directory (used in tests).

    Returns
    -------
    dict
        {"status": "ok", ...} on success or {"status": "error", "message": ...} on failure.
        Never raises.
    """
    try:
        record_id = str(record_id or "").strip()
        action = str(action or "").strip().lower()
        user_id = str(user_id or "").strip()
        reason = str(reason or "").strip()[:500]

        if not record_id:
            return {"status": "error", "message": "record_id is required."}
        if action not in _VALID_ACTIONS:
            return {
                "status": "error",
                "message": f"Invalid action '{action}'. Must be one of: {sorted(_VALID_ACTIONS)}.",
            }
        if not user_id:
            return {"status": "error", "message": "user_id is required."}

        action_timestamp = now_utc()
        root = base_dir or _BASE_DIR
        log_path = root / "data" / "review_actions" / "review_actions.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        entry: dict[str, Any] = {
            "record_id": record_id,
            "action": action,
            "user_id": user_id,
            "reason": reason,
            "action_timestamp": action_timestamp,
        }

        with log_path.open("a", encoding="utf-8") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)

        logger.info("Review action recorded: %s → %s by %s", record_id, action, user_id)
        return {
            "status": "ok",
            "record_id": record_id,
            "action": action,
            "action_timestamp": action_timestamp,
        }

    except Exception as exc:
        logger.error("record_review_action error: %s", exc)
        return {"status": "error", "message": str(exc)}


def _latest_action_for(
    record_id: str,
    base_dir: Path | None = None,
) -> dict[str, Any] | None:
    """Return the most recent accountability action for a given record_id, or None."""
    root = base_dir or _BASE_DIR
    log_path = root / "data" / "review_actions" / "review_actions.jsonl"
    if not log_path.exists():
        return None
    wanted = str(record_id or "").strip()
    if not wanted:
        return None
    last: dict[str, Any] | None = None
    try:
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(row.get("record_id") or "") == wanted:
                last = row
    except Exception as exc:
        logger.warning("_latest_action_for: could not read log: %s", exc)
    return last
