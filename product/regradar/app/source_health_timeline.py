"""Source-health timeline and evidence review-history aggregation.

This module only reads recorded StatuteProof artifacts. It must not backfill,
invent, or imply monitoring/review history that is not present in saved source
run or assessment records.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.evidence_assessment import LEGAL_DISCLAIMER, load_assessments, latest_assessment_for
from app.source_runs import is_skipped_cycle


STALE_AFTER_DAYS = 7  # sources not checked in 7+ days are flagged stale


def _is_stale(latest_run_at: str | None, stale_days: int = STALE_AFTER_DAYS) -> bool:
    """Return True if the source has not been checked within stale_days days.

    A missing timestamp is treated as stale (no recorded run at all).
    A parse error is treated as NOT stale so callers never get a false positive
    from a malformed timestamp.
    """
    if not latest_run_at:
        return True
    try:
        dt = datetime.fromisoformat(latest_run_at.replace("Z", "+00:00"))
        cutoff = datetime.now(timezone.utc) - timedelta(days=stale_days)
        return dt < cutoff
    except Exception:
        return False


def _days_since(latest_run_at: str | None) -> float | None:
    """Return fractional days since latest_run_at, or None if unparseable."""
    if not latest_run_at:
        return None
    try:
        dt = datetime.fromisoformat(latest_run_at.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        return round(delta.total_seconds() / 86400, 2)
    except Exception:
        return None


def _parse_run_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def source_change_frequency(
    runs: list[dict[str, Any]], *, now: datetime | None = None
) -> dict[str, Any]:
    """Descriptive change-frequency statistics over a source's OWN recorded runs.

    A factual reviewer aid — NOT an interpretation. It counts detected changes
    (change_status == "CHANGED") in the trailing 30 days and the per-month
    average over the observed window, and flags ``unusual_recent_activity`` ONLY
    as an arithmetic fact (recent count more than 2x the average). It expresses
    no impact, applicability, or compliance action — pure counts + timestamps,
    reproducible from the evidence trail, so it stays well clear of the
    legal-advice / obligation-mapping line.
    """
    _now = now or datetime.now(timezone.utc)
    change_times: list[datetime] = []
    earliest: datetime | None = None
    for r in runs:
        ts = _parse_run_ts(r.get("timestamp_utc") or r.get("timestamp") or r.get("run_at"))
        if ts is None:
            continue
        if earliest is None or ts < earliest:
            earliest = ts
        if str(r.get("change_status") or "").upper() == "CHANGED":
            change_times.append(ts)

    changes_last_30d = sum(1 for t in change_times if (_now - t).days < 30)
    total_changes = len(change_times)
    months_observed = round(max((_now - earliest).days / 30.0, 1.0), 1) if earliest else 1.0
    avg_per_month = round(total_changes / months_observed, 2) if months_observed > 0 else 0.0
    unusual = total_changes >= 3 and avg_per_month > 0 and changes_last_30d > 2 * avg_per_month

    return {
        "changes_last_30d": changes_last_30d,
        "total_changes_observed": total_changes,
        "avg_changes_per_month": avg_per_month,
        "months_observed": months_observed,
        "unusual_recent_activity": bool(unusual),
        "note": (
            f"{changes_last_30d} detected change(s) in the last 30 days; "
            f"trailing average {avg_per_month}/month over {months_observed} month(s) recorded. "
            "Descriptive statistics over recorded runs only — not an assessment of "
            "impact, applicability, or next steps."
        ),
    }


_BASE_DIR = Path(__file__).parent.parent


def source_health_customer_message(status: str) -> str:
    """Return calibrated customer-facing wording for source-health states."""
    normalized = str(status or "").upper()
    return {
        "MONITOR_OK": "Monitoring is active and the latest extraction passed quality checks.",
        "SOURCE_HEALTH_OK": "Monitoring is active and the latest extraction passed quality checks.",
        "QUALITY_DROP": "Extraction quality changed. Manual review may be required.",
        # A cycle the monitor deliberately SKIPPED. No request was issued, so
        # neither "a run happened" nor "an extraction degraded" may be claimed.
        "NOT_CHECKED": (
            "This source was not fetched during this cycle — checks were paused "
            "after repeated unusable runs. No check was performed and no "
            "extraction was attempted."
        ),
        "HASH_DRIFT": "Content fingerprint changed between runs. Review required before customer alert.",
        "CHANGED": "Content fingerprint changed between runs. Review required before customer alert.",
        "REMEDIATION_REQUIRED": "This source is under extraction remediation and is not currently treated as monitoring-ready.",
        "FAILED": "The latest source check failed. Manual review may be required.",
        "ACCESS_BLOCKED": "Access from our monitoring infrastructure was blocked or restricted during the latest check (the page may remain reachable to other visitors). Manual review may be required.",
        "NO_HISTORY": "No monitoring history has been recorded yet.",
    }.get(normalized, "Source-health status is recorded for internal compliance review.")


def build_source_timeline(
    source_id: str,
    *,
    org_id: Any = None,
    base_dir: Path | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Build a per-source timeline from registry, source runs, and assessments.

    ``org_id`` scopes the private assessment events to the caller's tenant.
    """
    sid = str(source_id or "").strip()
    if not sid:
        raise ValueError("source_id is required")
    root = base_dir or _BASE_DIR
    source = _find_source(sid, root)
    runs = [row for row in _read_runs(root) if row.get("source_id") == sid]
    # Forward org_id unconditionally so an unresolved caller (org_id=None) scopes
    # to the empty legacy bucket (isolate) rather than _NO_ORG_FILTER (all tenants).
    assessments = [
        row for row in load_assessments(base_dir=root, org_id=org_id)
        if row.get("source_id") == sid
    ]

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
        # Descriptive change-frequency stats over THIS source's recorded runs —
        # a factual reviewer aid (no impact/applicability judgement). See
        # source_change_frequency.
        "change_frequency": source_change_frequency(runs),
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
    registry = _read_source_registry(root)

    # Use the indexed reader — one JSONL parse, O(1) per-source access later.
    by_source = _read_runs_index(root)

    alerts: list[dict[str, Any]] = []
    historical_alerts: list[dict[str, Any]] = []
    stale_alerts: list[dict[str, Any]] = []

    # --- Pass 1: consecutive-failure detection (existing behaviour) ---
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
        latest_run_at = latest.get("timestamp_utc") or latest.get("run_at") or ""
        source = registry.get(source_id)
        enabled = source.get("enabled") is True if source else False
        status = str((source or {}).get("status") or "").lower()
        monitoring_mode = str((source or {}).get("monitoring_mode") or "").lower()
        entry = {
            "operator_status": "OPERATOR_REVIEW_REQUIRED",
            "source_id": source_id,
            "source_name": (source or {}).get("name") or latest.get("source_name") or source_id,
            "official_url": (source or {}).get("url") or latest.get("official_url") or latest.get("final_url") or "",
            "latest_run_id": latest.get("run_id"),
            "latest_run_at": latest_run_at,
            "latest_change_status": latest.get("change_status"),
            "latest_extraction_quality": latest.get("extraction_quality"),
            "consecutive_failed_runs": consecutive_failed,
            "failed_threshold": threshold,
            "stale": _is_stale(latest_run_at),
            "last_run_days_ago": _days_since(latest_run_at),
            "registry_present": source is not None,
            "registry_enabled": enabled,
            "registry_status": status,
            "registry_monitoring_mode": monitoring_mode,
            "blocked_reason": (
                f"{consecutive_failed} consecutive failed or quality-drop source runs; "
                "manual operator review required before relying on this source."
            ),
            "customer_safe_message": source_health_customer_message(_source_health_status(latest)),
        }
        if enabled:
            alerts.append(entry)
        else:
            entry["operator_status"] = "DISABLED_SOURCE_HISTORY"
            entry["blocked_reason"] = (
                f"{consecutive_failed} consecutive failed or quality-drop runs are recorded for a "
                "disabled, removed, or unregistered source ID. Keep visible for audit history, but "
                "do not count it as an active monitoring blocker."
            )
            historical_alerts.append(entry)

    # --- Pass 2: staleness detection ---
    # Catches sources that look "healthy" (no consecutive failures) but have not
    # been checked recently.  These would otherwise display as green with no
    # warning, creating a silent monitoring gap.
    failed_source_ids = {e["source_id"] for e in alerts} | {e["source_id"] for e in historical_alerts}
    for source_id, runs in sorted(by_source.items()):
        if source_id in failed_source_ids:
            # Already flagged by Pass 1 — staleness field already attached.
            continue
        latest = runs[-1]
        latest_run_at = latest.get("timestamp_utc") or latest.get("run_at") or ""
        if not _is_stale(latest_run_at):
            continue
        source = registry.get(source_id)
        enabled = source.get("enabled") is True if source else False
        status = str((source or {}).get("status") or "").lower()
        monitoring_mode = str((source or {}).get("monitoring_mode") or "").lower()
        days_ago = _days_since(latest_run_at)
        days_str = f"{days_ago:.1f} days" if days_ago is not None else "unknown duration"
        stale_entry = {
            "operator_status": "STALE",
            "source_id": source_id,
            "source_name": (source or {}).get("name") or latest.get("source_name") or source_id,
            "official_url": (source or {}).get("url") or latest.get("official_url") or latest.get("final_url") or "",
            "latest_run_id": latest.get("run_id"),
            "latest_run_at": latest_run_at,
            "latest_change_status": latest.get("change_status"),
            "latest_extraction_quality": latest.get("extraction_quality"),
            "consecutive_failed_runs": 0,
            "failed_threshold": threshold,
            "stale": True,
            "last_run_days_ago": days_ago,
            "registry_present": source is not None,
            "registry_enabled": enabled,
            "registry_status": status,
            "registry_monitoring_mode": monitoring_mode,
            "blocked_reason": (
                f"Source has not been checked in {days_str} (threshold: {STALE_AFTER_DAYS} days). "
                "Last recorded run appeared healthy. Operator should verify that the monitor "
                "scheduler is running and that this source is still being polled."
            ),
            "customer_safe_message": source_health_customer_message("NO_HISTORY"),
        }
        stale_alerts.append(stale_entry)

    stale_source_names = [e["source_name"] for e in stale_alerts]

    return {
        "ok": True,
        "operator_only": True,
        "external_send": False,
        "customer_delivery": False,
        "failed_threshold": threshold,
        "stale_threshold_days": STALE_AFTER_DAYS,
        "sources_checked": len(by_source),
        "sources_requiring_operator_review": len(alerts),
        "historical_sources_requiring_operator_review": len(historical_alerts),
        "stale_sources_count": len(stale_alerts),
        "stale_sources": stale_source_names,
        "alerts": alerts,
        "historical_alerts": historical_alerts,
        "stale_alerts": stale_alerts,
        "disclaimer": LEGAL_DISCLAIMER,
    }


def build_evidence_review_history(
    evidence_record_id: str,
    *,
    org_id: Any = None,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Build a review-history event list for a saved evidence/source run.

    ``org_id`` scopes the private assessment events to the caller's tenant so the
    history never surfaces another customer's internal review notes on a shared
    official record.
    """
    evidence_id = str(evidence_record_id or "").strip()
    if not evidence_id:
        raise ValueError("evidence_record_id is required")
    root = base_dir or _BASE_DIR
    run = _find_run(evidence_id, root)
    if run is None:
        raise ValueError(f"Saved evidence record not found: {evidence_id}")

    # Forward org_id unconditionally so an unresolved caller (org_id=None) scopes
    # to the empty legacy bucket (isolate) rather than _NO_ORG_FILTER (all tenants),
    # keeping another tenant's internal_note/next_action out of the history.
    assessments = [
        row for row in load_assessments(base_dir=root, org_id=org_id)
        if row.get("evidence_record_id") == evidence_id
    ]
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
        "latest_assessment": latest_assessment_for(evidence_id, base_dir=root, org_id=org_id),
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


def _read_runs_index(base_dir: Path) -> dict[str, list[dict[str, Any]]]:
    """Return all runs grouped by source_id for O(1) per-source access.

    Callers that need runs for a specific source_id can do:
        index = _read_runs_index(base_dir)
        source_runs = index.get(source_id, [])
    instead of scanning the full JSONL list.  The JSONL is still read only once.
    """
    index: dict[str, list[dict[str, Any]]] = {}
    for row in _read_runs(base_dir):
        source_id = str(row.get("source_id") or "").strip()
        if source_id:
            index.setdefault(source_id, []).append(row)
    return index


def _find_run(run_id: str, base_dir: Path) -> dict[str, Any] | None:
    for row in _read_runs(base_dir):
        if str(row.get("run_id") or "") == run_id:
            return row
    return None


def _find_source(source_id: str, base_dir: Path) -> dict[str, Any] | None:
    return _read_source_registry(base_dir).get(source_id)


def _read_source_registry(base_dir: Path) -> dict[str, dict[str, Any]]:
    path = base_dir / "sources.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    sources = payload.get("sources", payload) if isinstance(payload, dict) else payload
    if not isinstance(sources, list):
        return {}
    by_source: dict[str, dict[str, Any]] = {}
    for source in sources:
        if not isinstance(source, dict):
            continue
        source_id = str(source.get("source_id") or source.get("id") or "").strip()
        if source_id:
            by_source[source_id] = source
    return by_source


def _events_from_run(run: dict[str, Any], *, index: int) -> list[dict[str, Any]]:
    # A skipped cycle is ONE honest event, not a MONITOR_RUN plus a quality
    # drop. Emitting those two would assert that a run happened and that an
    # extraction happened and degraded; the source was never contacted.
    if is_skipped_cycle(run):
        return [_skipped_cycle_event(run, index=index)]
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


def _skipped_cycle_event(run: dict[str, Any], *, index: int) -> dict[str, Any]:
    """Timeline event for a cycle in which the source was NOT fetched."""
    event = _base_event(
        run,
        "MONITOR_SKIPPED",
        seed=f"skipped:{run.get('run_id')}:{index}",
        source_health_status="NOT_CHECKED",
        customer_safe_message=source_health_customer_message("NOT_CHECKED"),
    )
    # The trail record stamps extraction_quality="FAILED" so classify_change can
    # never resolve it as a baseline. Nothing was extracted, so surfacing that
    # value to a customer would report a failed extraction that never ran.
    event["extraction_quality"] = None
    event["remediation_reason"] = run.get("limitations_notes")
    return event


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
    # A CIRCUIT_OPEN record proves the ABSENCE of a check: the monitor skipped
    # the source and issued no request. Reporting it as QUALITY_DROP would tell
    # the customer we extracted something and it degraded — a claim the cycle
    # cannot back. Checked first: it outranks every content-derived state
    # because there was no content.
    if is_skipped_cycle(run):
        return "NOT_CHECKED"
    change = str(run.get("change_status") or "").upper()
    access = str(run.get("access_status") or "").lower()
    monitor_access = str(run.get("monitor_access_status") or "").lower()
    quality = str(run.get("extraction_quality") or "").upper()
    # A GENUINE runtime access block (the monitor set monitor_access_status
    # ="blocked" when fetch_page raised a 401/403/451 WAF/geo block) is its own
    # honest state — reported BEFORE the generic FAILED so a source our
    # datacenter IP is blocked from is never presented as a mere extraction
    # hiccup (or, worse, as healthy). Only this runtime signal preempts; the
    # config-derived access_status ("restricted", set purely from a source's
    # static disabled_* status) keeps its original position AFTER the
    # quality/failure checks so a real QUALITY_DROP/FAILED on such a source is
    # not masked as an access block.
    if monitor_access == "blocked":
        return "ACCESS_BLOCKED"
    # A runtime anti-bot / JS-challenge wall is an access block, not a content
    # dip — report it before the FAILED/QUALITY_DROP gate so a walled source
    # reads as "blocked (needs headless/proxy)" rather than a generic quality
    # drop (code-review 2026-07-18). Keyed on the specific runtime failure_code,
    # not the broad access field, so config-derived "restricted" is unaffected.
    if str(run.get("failure_code") or "") == "BOT_WALL":
        return "ACCESS_BLOCKED"
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
