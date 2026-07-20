"""Canonical source-count summary for customer-facing app surfaces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import BASE_DIR as _BASE_DIR
from app.source_runs import source_run_path
from app.sources import (
    latest_run_status_map,
    proxy_remediation_verified,
    proxy_unblocked_remediation,
)


def build_sources_summary(
    market: str = "AE",
    *,
    base_dir: Path | None = None,
    excluded_source_ids: set[str] | frozenset[str] | None = None,
) -> dict[str, Any]:
    """Return canonical source truth from sources.json and recorded run history.

    ``excluded_source_ids`` is an opaque set of source_ids to drop from the count
    (cross-tenant scoping): the caller resolves which custom sources the current
    user may not see and passes them here so aggregate counts never reflect
    another tenant's private sources. Official sources (which carry no source_id
    in the registry) are never matched by this filter and always counted.
    """
    root = base_dir or _BASE_DIR
    market_code = str(market or "AE").upper().strip() or "AE"
    excluded = {str(s).strip() for s in (excluded_source_ids or set()) if str(s).strip()}
    sources = _load_sources(root)
    market_sources = [
        item
        for item in sources
        if str(item.get("jurisdiction") or "").upper() == market_code
        and not (
            str(item.get("source_id") or "").strip()
            and str(item.get("source_id") or "").strip() in excluded
        )
    ]
    enabled_sources = [item for item in market_sources if bool(item.get("enabled"))]
    mode_counts = {
        "fresh_alert": 0,
        "evidence_library": 0,
        "candidate": 0,
        "remediation": 0,
    }
    # Mirrors pipeline._source_may_auto_alert, EXCEPT the proxy-remediation
    # branch uses the VERIFIED variant: a proxy-routed remediation source is
    # counted only after a successful production run is recorded in the trail
    # (config alone is not evidence — see sources.proxy_remediation_verified).
    # ONE classification pass, ONE trail read: a promoted source moves OUT of
    # remediation into fresh-alert so the buckets stay disjoint and still
    # partition enabled_count. The trail tail is read once (status_map) rather
    # than once per source — this runs on unauthenticated /api/health.
    runs_file = (
        source_run_path()
        if base_dir is None
        else root / "data" / "source_runs" / "source_runs.jsonl"
    )
    # Skip the trail read entirely when no source is proxy-routed (the routing
    # predicate is pure config — no I/O).
    status_map = (
        latest_run_status_map(runs_file)
        if any(proxy_unblocked_remediation(item) for item in enabled_sources)
        else {}
    )
    fresh_alert_sources: list[dict[str, Any]] = []
    for item in enabled_sources:
        mode = str(item.get("monitoring_mode") or "").lower().strip()
        if mode in mode_counts:
            mode_counts[mode] += 1
        if mode == "fresh_alert" and item.get("alert_eligible") is True:
            fresh_alert_sources.append(item)
        elif proxy_remediation_verified(item, status_map=status_map):
            fresh_alert_sources.append(item)
            if mode in mode_counts:
                mode_counts[mode] -= 1  # promoted: counted as fresh-alert only
    legacy_active = [
        item
        for item in enabled_sources
        if str(item.get("status") or "active").lower() == "active"
    ]

    runs = _read_runs(root, market_code)
    last_run_at = None
    monitored_ids: set[str] = set()
    for run in runs:
        run_at = str(run.get("timestamp_utc") or run.get("run_at") or "")
        if run_at and (last_run_at is None or run_at > last_run_at):
            last_run_at = run_at
        sid = str(run.get("source_id") or run.get("source_name") or "").strip()
        if sid:
            monitored_ids.add(sid)

    return {
        "ok": True,
        "market": market_code,
        "enabled_count": len(enabled_sources),
        "readiness_supported_count": len(fresh_alert_sources),
        "fresh_alert_count": len(fresh_alert_sources),
        "evidence_library_count": mode_counts["evidence_library"],
        "candidate_count": mode_counts["candidate"],
        "remediation_count": mode_counts["remediation"],
        "legacy_active_count": len(legacy_active),
        "monitoring_mode_counts": mode_counts,
        "monitored_count": len(monitored_ids),
        "last_run_at": last_run_at,
        "source_truth": (
            f"{len(enabled_sources)} enabled / {len(fresh_alert_sources)} fresh-alert eligible / "
            f"{mode_counts['evidence_library']} evidence-library / {mode_counts['candidate']} candidate / "
            f"{mode_counts['remediation']} remediation"
        ),
        "disclaimer": "Monitoring intelligence only. Not legal advice.",
    }


def _load_sources(root: Path) -> list[dict[str, Any]]:
    path = root / "sources.json"
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    sources = payload.get("sources", payload) if isinstance(payload, dict) else payload
    return [item for item in sources if isinstance(item, dict)] if isinstance(sources, list) else []


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
