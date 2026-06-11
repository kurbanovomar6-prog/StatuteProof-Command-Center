"""Human review workflow for local alert draft artifacts."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS_DRAFT = "DRAFT"
STATUS_MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
STATUS_APPROVED_WEEKLY = "APPROVED_FOR_WEEKLY"
STATUS_APPROVED_URGENT = "APPROVED_FOR_URGENT"
STATUS_REJECTED = "REJECTED"
STATUS_NEEDS_SOURCE_ADAPTER = "NEEDS_SOURCE_ADAPTER"
STATUS_NEEDS_LEGAL_REVIEW = "NEEDS_LEGAL_REVIEW"

DECISION_HOLD = "HOLD_FOR_REVIEW"
DECISION_DO_NOT_SEND = "DO_NOT_SEND"
DECISION_WEEKLY = "WEEKLY_BRIEF_ONLY"
DECISION_URGENT = "READY_FOR_URGENT_DELIVERY"

_BASE_DIR = Path(__file__).parent.parent
_REVIEW_DIR = _BASE_DIR / "data" / "alert_reviews"
_REVIEW_FILE = _REVIEW_DIR / "reviews.jsonl"
_SNAPSHOT_DIR = _BASE_DIR / "data" / "source_snapshots"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def review_store_path() -> Path:
    return _REVIEW_FILE


def list_alert_drafts(market: str | None = None, base_dir: Path | None = None) -> list[dict[str, Any]]:
    root = (base_dir or _BASE_DIR) / "data" / "source_snapshots"
    if not root.exists():
        return []
    rows = []
    for path in root.rglob("alert_draft.json"):
        alert = _load_json(path)
        if not alert:
            continue
        if market and str(alert.get("market", "")).upper() != market.upper():
            continue
        alert["_alert_draft_path"] = _rel(path, base_dir or _BASE_DIR)
        rows.append(alert)
    rows.sort(key=lambda item: item.get("checked_at_utc", ""), reverse=True)
    return rows


def find_alert_draft(alert_id: str, base_dir: Path | None = None) -> tuple[dict[str, Any], Path]:
    root_base = base_dir or _BASE_DIR
    for alert in list_alert_drafts(base_dir=root_base):
        if alert.get("alert_id") == alert_id:
            path = root_base / alert["_alert_draft_path"]
            return alert, path
    raise FileNotFoundError(f"Alert draft not found: {alert_id}")


def review_alert(
    *,
    alert_id: str,
    action: str,
    reviewer: str,
    note: str,
    force: bool = False,
    base_dir: Path | None = None,
    review_file: Path | None = None,
) -> dict[str, Any]:
    if not reviewer.strip():
        raise ValueError("reviewer is required")

    alert, draft_path = find_alert_draft(alert_id, base_dir=base_dir)
    previous_status = alert.get("review_status") or STATUS_DRAFT
    previous_decision = alert.get("send_decision") or DECISION_HOLD
    safety = approval_safety_issues(alert, base_dir=base_dir)

    new_status, new_decision = _target_state(action)
    if action == "approve_urgent" and safety and not force:
        raise ValueError("Urgent approval blocked by safety checks: " + "; ".join(safety))
    if force and safety and not note.strip():
        raise ValueError("--force requires a review note")

    reviewed_at = now_utc()
    record = {
        "review_id": _review_id(alert_id, reviewed_at, reviewer, action),
        "alert_id": alert_id,
        "market": alert.get("market"),
        "source_id": alert.get("source_id"),
        "source_name": alert.get("source_name"),
        "client_profile_id": (alert.get("relevance") or {}).get("client_id"),
        "previous_status": previous_status,
        "new_status": new_status,
        "previous_send_decision": previous_decision,
        "new_send_decision": new_decision,
        "reviewer": reviewer,
        "reviewed_at_utc": reviewed_at,
        "review_note": note,
        "alert_draft_path": _rel(draft_path, base_dir or _BASE_DIR),
        "proof_path": (alert.get("proof_block") or {}).get("proof_block_path") or _sibling_artifact(draft_path, "proof.json", base_dir or _BASE_DIR),
        "diff_path": (alert.get("proof_block") or {}).get("diff_json_path") or _sibling_artifact(draft_path, "diff.json", base_dir or _BASE_DIR),
        "force": force,
        "safety_issues": safety,
    }

    alert["review_status"] = new_status
    alert["send_decision"] = new_decision
    alert["reviewed_at_utc"] = reviewed_at
    alert["reviewer"] = reviewer
    alert["review_note"] = note
    alert["review_record_path"] = _rel(review_file or _REVIEW_FILE, base_dir or _BASE_DIR)
    history = list(alert.get("review_history") or [])
    history.append(record)
    alert["review_history"] = history
    draft_path.write_text(json.dumps(alert, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    _append_review_record(record, review_file=review_file)
    return record


def approval_safety_issues(alert: dict[str, Any], base_dir: Path | None = None) -> list[str]:
    issues = []
    proof = alert.get("proof_block") or {}
    relevance = alert.get("relevance") or {}
    limitations = " ".join(str(item) for item in alert.get("limitations", []))
    source = f"{alert.get('source_name', '')} {alert.get('source_id', '')}".lower()

    if proof.get("proof_quality") == "INCOMPLETE":
        issues.append("proof_quality is INCOMPLETE")
    if alert.get("review_status") == STATUS_NEEDS_SOURCE_ADAPTER:
        issues.append("review_status is NEEDS_SOURCE_ADAPTER")
    if alert.get("confidence") == "LOW":
        issues.append("confidence is LOW")
    if alert.get("risk_level") == "REVIEW":
        issues.append("risk_level is REVIEW")
    if "legislation" in source and ("adapter review" in limitations.lower() or alert.get("change_type") == "UNKNOWN"):
        issues.append("UAE Legislation Portal requires source adapter review")
    if proof.get("meaningful_change_detected") is False:
        issues.append("meaningful_change_detected is false")
    if _diff_quality(alert, base_dir=base_dir) == "INCOMPLETE":
        issues.append("diff_quality is INCOMPLETE")
    if relevance.get("delivery_decision") == "MANUAL_REVIEW_REQUIRED":
        issues.append("relevance decision is MANUAL_REVIEW_REQUIRED")
    return issues


def load_review_records(review_file: Path | None = None) -> list[dict[str, Any]]:
    path = review_file or _REVIEW_FILE
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def latest_review_for(alert_id: str, review_file: Path | None = None) -> dict[str, Any] | None:
    for record in reversed(load_review_records(review_file)):
        if record.get("alert_id") == alert_id:
            return record
    return None


def _target_state(action: str) -> tuple[str, str]:
    mapping = {
        "approve_weekly": (STATUS_APPROVED_WEEKLY, DECISION_WEEKLY),
        "approve_urgent": (STATUS_APPROVED_URGENT, DECISION_URGENT),
        "reject": (STATUS_REJECTED, DECISION_DO_NOT_SEND),
        "needs_adapter": (STATUS_NEEDS_SOURCE_ADAPTER, DECISION_HOLD),
        "needs_legal": (STATUS_NEEDS_LEGAL_REVIEW, DECISION_HOLD),
        "manual_review": (STATUS_MANUAL_REVIEW_REQUIRED, DECISION_HOLD),
    }
    try:
        return mapping[action]
    except KeyError as exc:
        raise ValueError(f"Unknown review action: {action}") from exc


def _diff_quality(alert: dict[str, Any], base_dir: Path | None = None) -> str | None:
    relevance = alert.get("relevance") or {}
    if relevance.get("diff_quality"):
        return relevance.get("diff_quality")
    proof = alert.get("proof_block") or {}
    diff_path = proof.get("diff_json_path")
    if not diff_path:
        return None
    path = Path(diff_path)
    if not path.is_absolute():
        path = (base_dir or _BASE_DIR) / path
    diff = _load_json(path)
    return diff.get("diff_quality") if diff else None


def _append_review_record(record: dict[str, Any], review_file: Path | None = None) -> None:
    path = review_file or _REVIEW_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _review_id(alert_id: str, reviewed_at: str, reviewer: str, action: str) -> str:
    seed = f"{alert_id}|{reviewed_at}|{reviewer}|{action}"
    return "review-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def _sibling_artifact(draft_path: Path, name: str, base_dir: Path) -> str | None:
    path = draft_path.parent / name
    if not path.exists():
        return None
    return _rel(path, base_dir)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _rel(path: Path, base_dir: Path) -> str:
    try:
        return str(path.resolve().relative_to(base_dir.resolve()))
    except ValueError:
        return str(path)
