"""Source-health timeline and evidence review-history aggregation.

This module only reads recorded StatuteProof artifacts. It must not backfill,
invent, or imply monitoring/review history that is not present in saved source
run or assessment records.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from app.evidence_assessment import LEGAL_DISCLAIMER, load_assessments, latest_assessment_for


_BASE_DIR = Path(__file__).parent.parent


def source_health_customer_message(status: str) -> str:
    """Return calibrated customer-facing wording for source-health states."""
    normalized = str(status or "").upper()
    return {
        "MONITOR_OK": "Monitoring is active and the latest extraction passed quality checks.",
        "SOURCE_HEALTH_OK": "Monitoring is active and the latest extraction passed quality checks.",
        "QUALITY_DROP": "Extraction quality changed. Manual review may be required.",
        "HASH_DRIFT": "Content fingerprint changed between runs. Review required before customer alert.",
        "CHANGED": "Content fingerprint changed between runs. Review required before customer alert.",
        "REMEDIATION_REQUIRED": "This source is under extraction remediation and is not currently treated as monitoring-ready.",
        "FAILED": "The latest source check failed. Manual review may be required.",
        "ACCESS_BLOCKED": "The source could not be accessed publicly during the latest check. Manual review may be required.",
        "NO_HISTORY": "No monitoring history has been recorded yet.",
    }.get(normalized, "Source-health status is recorded for internal compliance review.")


def build_source_timeline(
    source_id: str,
    *,
    base_dir: Path | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Build a per-source timeline from registry, source runs, and assessments."""
    sid = str(source_id or "").strip()
    if not sid:
        raise ValueError("source_id is required")
    root = base_dir or _BASE_DIR
    source = _find_source(sid, root)
    runs = [row for row in _read_runs(root) if row.get("source_id") == sid]
    assessments = [row for row in load_assessments(base_dir=root) if row.get("source_id") == sid]

    events: list[dict[str, Any]] = []
    if source and str(source.get("status") or "").lower() == "remediation":
        events.append(_remediation_event(source))

    for index, run in enumerate(runs):
        events.extend(_events_from_run(run, index=index))

    for assessment in assessments:
        events.append(_assessment_event(assessment))

    events.sort(key=lambda item: str(item.get("timestamp") or ""))
    if limit > 0:
        events = events[-limit:]

    latest_run = runs[-1] if runs else None
    status = _timeline_status(source, latest_run, events)
    return {
        "ok": True,
        "source_id": sid,
        "source_name": (source or {}).get("name") or (latest_run or {}).get("source_name") or sid,
        "source_url": (source or {}).get("url") or (latest_run or {}).get("official_url") or "",
        "source_health_status": status,
        "message": source_health_customer_message(status),
        "events": events,
        "total_events": len(events),
        "has_real_history": bool(runs or assessments),
        "disclaimer": LEGAL_DISCLAIMER,
    }


def build_operator_source_health_report(
    *,
    base_dir: Path | None = None,
    failed_threshold: int = 3,
) -> dict[str, Any]:
    """Build an operator-only report for sources that may have gone dark.

    This function does not send notifications or produce customer-facing claims.
    It gives the operator a deterministic list of sources needing manual review.
    """

    root = base_dir or _BASE_DIR
    threshold = max(1, int(failed_threshold or 1))
    by_source: dict[str, list[dict[str, Any]]] = {}
    for run in _read_runs(root):
        source_id = str(run.get("source_id") or "").strip()
        if not source_id:
            continue
        by_source.setdefault(source_id, []).append(run)

    alerts: list[dict[str, Any]] = []
    for source_id, runs in sorted(by_source.items()):
        consecutive_failed = 0
        for run in reversed(runs):
            if _operator_failed_status(run):
                consecutive_failed += 1
                continue
            break
        if consecutive_failed < threshold:
            continue
        latest = runs[-1]
        alerts.append({
            "operator_status": "OPERATOR_REVIEW_REQUIRED",
            "source_id": source_id,
            "source_name": latest.get("source_name") or source_id,
            "official_url": latest.get("official_url") or latest.get("final_url") or "",
            "latest_run_id": latest.get("run_id"),
            "latest_run_at": latest.get("timestamp_utc") or latest.get("run_at") or "",
            "latest_change_status": latest.get("change_status"),
            "latest_extraction_quality": latest.get("extraction_quality"),
            "consecutive_failed_runs": consecutive_failed,
            "failed_threshold": threshold,
            "blocked_reason": (
                f"{consecutive_failed} consecutive failed or quality-drop source runs; "
                "manual operator review required before relying on this source."
            ),
            "customer_safe_message": source_health_customer_message(_source_health_status(latest)),
        })

    return {
        "ok": True,
        "operator_only": True,
        "external_send": False,
        "customer_delivery": False,
        "failed_threshold": threshold,
        "sources_checked": len(by_source),
        "sources_requiring_operator_review": len(alerts),
        "alerts": alerts,
        "disclaimer": LEGAL_DISCLAIMER,
    }


def build_evidence_review_history(
    evidence_record_id: str,
    *,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Build a review-history event list for a saved evidence/source run."""
    evidence_id = str(evidence_record_id or "").strip()
    if not evidence_id:
        raise ValueError("evidence_record_id is required")
    root = base_dir or _BASE_DIR
    run = _find_run(evidence_id, root)
    if run is None:
        raise ValueError(f"Saved evidence record not found: {evidence_id}")

    assessments = [row for row in load_assessments(base_dir=root) if row.get("evidence_record_id") == evidence_id]
    events: list[dict[str, Any]] = []
    events.append(_evidence_created_event(run))
    if run.get("change_status") == "CHANGED":
        events.append(_hash_event(run, "HASH_DRIFT"))
    elif run.get("normalized_hash") or run.get("content_hash"):
        events.append(_hash_event(run, "HASH_STABLE"))
    for assessment in assessments:
        events.append(_assessment_event(assessment))
    events.sort(key=lambda item: str(item.get("timestamp") or ""))

    return {
        "ok": True,
        "evidence_record_id": evidence_id,
        "source_id": run.get("source_id"),
        "source_name": run.get("source_name"),
        "source_url": run.get("official_url") or run.get("final_url"),
        "source_health_status": _source_health_status(run),
        "message": "Review history is built only from saved evidence and assessment records.",
        "events": events,
        "total_events": len(events),
        "latest_assessment": latest_assessment_for(evidence_id, base_dir=root),
        "disclaimer": LEGAL_DISCLAIMER,
    }


def _read_runs(base_dir: Path) -> list[dict[str, Any]]:
    path = base_dir / "data" / "source_runs" / "source_runs.jsonl"
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


def _find_run(run_id: str, base_dir: Path) -> dict[str, Any] | None:
    for row in _read_runs(base_dir):
        if str(row.get("run_id") or "") == run_id:
            return row
    return None


def _find_source(source_id: str, base_dir: Path) -> dict[str, Any] | None:
    path = base_dir / "sources.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    sources = payload.get("sources", payload) if isinstance(payload, dict) else payload
    if not isinstance(sources, list):
        return None
    for source in sources:
        if not isinstance(source, dict):
            continue
        if str(source.get("source_id") or source.get("id") or "") == source_id:
            return source
    return None


def _events_from_run(run: dict[str, Any], *, index: int) -> list[dict[str, Any]]:
    events = [_run_event(run, index=index)]
    if run.get("proof_block_path"):
        events.append(_evidence_created_event(run))
    if run.get("certification_report_path"):
        events.append(_baseline_event(run))
    if run.get("change_status") == "CHANGED":
        events.append(_hash_event(run, "HASH_DRIFT"))
    elif run.get("change_status") == "QUALITY_DROP":
        events.append(_quality_drop_event(run))
    elif run.get("normalized_hash") or run.get("content_hash"):
        events.append(_hash_event(run, "HASH_STABLE"))
    if _source_health_status(run) == "MONITOR_OK":
        events.append(_source_health_ok_event(run))
    return events


def _run_event(run: dict[str, Any], *, index: int) -> dict[str, Any]:
    status = _source_health_status(run)
    return _base_event(
        run,
        "MONITOR_RUN",
        seed=f"monitor:{run.get('run_id')}:{index}",
        source_health_status=status,
        customer_safe_message=source_health_customer_message(status),
    )


def _evidence_created_event(run: dict[str, Any]) -> dict[str, Any]:
    return _base_event(
        run,
        "EVIDENCE_SAVED",
        seed=f"evidence:{run.get('run_id')}",
        customer_safe_message="Evidence was saved with proof/hash metadata for internal compliance review.",
    )


def _baseline_event(run: dict[str, Any]) -> dict[str, Any]:
    return _base_event(
        run,
        "BASELINE_COMPLETE",
        seed=f"baseline:{run.get('run_id')}",
        customer_safe_message="Baseline/certification metadata is recorded for this source run.",
    )


def _hash_event(run: dict[str, Any], event_type: str) -> dict[str, Any]:
    return _base_event(
        run,
        event_type,
        seed=f"{event_type.lower()}:{run.get('run_id')}:{run.get('normalized_hash') or run.get('content_hash')}",
        source_health_status="HASH_DRIFT" if event_type == "HASH_DRIFT" else _source_health_status(run),
        customer_safe_message=source_health_customer_message(event_type),
    )


def _quality_drop_event(run: dict[str, Any]) -> dict[str, Any]:
    return _base_event(
        run,
        "QUALITY_DROP",
        seed=f"quality_drop:{run.get('run_id')}",
        source_health_status="QUALITY_DROP",
        customer_safe_message=source_health_customer_message("QUALITY_DROP"),
        internal_debug_message=str(run.get("error") or run.get("limitations_notes") or ""),
    )


def _source_health_ok_event(run: dict[str, Any]) -> dict[str, Any]:
    return _base_event(
        run,
        "SOURCE_HEALTH_OK",
        seed=f"source_health_ok:{run.get('run_id')}",
        source_health_status="MONITOR_OK",
        customer_safe_message=source_health_customer_message("MONITOR_OK"),
    )


def _assessment_event(assessment: dict[str, Any]) -> dict[str, Any]:
    event_type = "ASSESSED" if assessment.get("impact_level") else "ACKNOWLEDGED"
    timestamp = assessment.get("reviewed_at") or assessment.get("created_at") or ""
    note = str(assessment.get("internal_note") or "").strip()
    return {
        "event_id": _event_id(f"assessment:{assessment.get('assessment_id')}"),
        "source_id": assessment.get("source_id"),
        "source_name": assessment.get("source_name"),
        "event_type": event_type,
        "timestamp": timestamp,
        "source_url": assessment.get("official_url") or "",
        "proof_path": assessment.get("proof_path"),
        "raw_hash": assessment.get("raw_hash"),
        "normalized_hash": assessment.get("normalized_hash"),
        "diff_path": assessment.get("diff_path"),
        "quality_score": None,
        "extraction_quality": None,
        "source_health_status": assessment.get("source_health_status") or "MONITOR_OK",
        "remediation_reason": None,
        "assessment_id": assessment.get("assessment_id"),
        "reviewer": assessment.get("reviewer_name") or assessment.get("reviewer_user_id"),
        "assessment_impact_level": assessment.get("impact_level"),
        "assessment_note_preview": _preview(note),
        "customer_safe_message": "A human review assessment was recorded for this evidence record.",
        "internal_debug_message": None,
    }


def _remediation_event(source: dict[str, Any]) -> dict[str, Any]:
    reason = str(source.get("remediation_reason") or source.get("notes") or source.get("scraper_notes") or "").strip()
    timestamp = str(source.get("remediation_started_at") or source.get("updated_at") or "")
    return {
        "event_id": _event_id(f"remediation:{source.get('source_id') or source.get('id')}:{reason}"),
        "source_id": source.get("source_id") or source.get("id"),
        "source_name": source.get("name"),
        "event_type": "REMEDIATION_STARTED",
        "timestamp": timestamp,
        "source_url": source.get("url") or "",
        "proof_path": None,
        "raw_hash": None,
        "normalized_hash": None,
        "diff_path": None,
        "quality_score": None,
        "extraction_quality": None,
        "source_health_status": "REMEDIATION_REQUIRED",
        "remediation_reason": reason or "Source is marked under extraction remediation.",
        "assessment_id": None,
        "reviewer": None,
        "assessment_impact_level": None,
        "assessment_note_preview": None,
        "customer_safe_message": source_health_customer_message("REMEDIATION_REQUIRED"),
        "internal_debug_message": reason,
    }


def _base_event(
    run: dict[str, Any],
    event_type: str,
    *,
    seed: str,
    source_health_status: str | None = None,
    customer_safe_message: str | None = None,
    internal_debug_message: str | None = None,
) -> dict[str, Any]:
    return {
        "event_id": _event_id(seed),
        "source_id": run.get("source_id"),
        "source_name": run.get("source_name"),
        "event_type": event_type,
        "timestamp": run.get("timestamp_utc") or run.get("run_at") or "",
        "source_url": run.get("official_url") or run.get("final_url") or "",
        "proof_path": run.get("proof_block_path"),
        "raw_hash": run.get("raw_hash"),
        "normalized_hash": run.get("normalized_hash") or run.get("content_hash"),
        "diff_path": run.get("diff_json_path") or run.get("diff_md_path"),
        "quality_score": None,
        "extraction_quality": run.get("extraction_quality"),
        "source_health_status": source_health_status or _source_health_status(run),
        "remediation_reason": run.get("limitations_notes") if _source_health_status(run) != "MONITOR_OK" else None,
        "assessment_id": None,
        "reviewer": None,
        "assessment_impact_level": None,
        "assessment_note_preview": None,
        "customer_safe_message": customer_safe_message or source_health_customer_message(source_health_status or _source_health_status(run)),
        "internal_debug_message": internal_debug_message,
    }


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


def _operator_failed_status(run: dict[str, Any]) -> bool:
    change = str(run.get("change_status") or "").upper()
    access = str(run.get("access_status") or "").lower()
    quality = str(run.get("extraction_quality") or "").upper()
    return change in {"FAILED", "QUALITY_DROP"} or quality == "FAILED" or access in {"failed", "restricted", "blocked"}


def _timeline_status(source: dict[str, Any] | None, latest_run: dict[str, Any] | None, events: list[dict[str, Any]]) -> str:
    if source and str(source.get("status") or "").lower() == "remediation":
        return "REMEDIATION_REQUIRED"
    if latest_run:
        return _source_health_status(latest_run)
    if events:
        return str(events[-1].get("source_health_status") or "NO_HISTORY")
    return "NO_HISTORY"


def _preview(text: str, limit: int = 140) -> str:
    compact = " ".join(str(text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def _event_id(seed: str) -> str:
    return "evt-" + hashlib.sha256(str(seed).encode("utf-8")).hexdigest()[:16]
