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

# Customer-facing copy for the enforcement-monitoring capability. Intentionally
# scoped ("selected", "may be affected") — it must never promise total coverage
# ("all enforcement actions", "never miss a fine") and must pass the
# legal_safety guard. The count of enforcement sources it accompanies reflects
# ONLY genuinely fresh-alert-eligible sources (see build_enforcement_summary).
ENFORCEMENT_FEATURE_LABEL = "Enforcement action monitoring"
ENFORCEMENT_FEATURE_DESCRIPTION = (
    "Monitors selected official regulator enforcement pages for changes to "
    "published enforcement actions, decisions, and notices. Coverage is limited "
    "to the specific sources listed and may be affected by publication delays, "
    "source structure changes, or access limits. Monitoring intelligence only. "
    "Not legal advice."
)

_COUNTED_MODES = ("fresh_alert", "evidence_library", "candidate", "remediation")


def _classify_fresh_alert(
    enabled_sources: list[dict[str, Any]],
    status_map: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Partition enabled sources into fresh-alert-eligible + per-mode counts.

    Mirrors pipeline._source_may_auto_alert EXCEPT the proxy-remediation branch
    uses the VERIFIED variant (sources.proxy_remediation_verified): a
    proxy-routed remediation source counts as fresh-alert only after a recent
    successful production run is recorded — configuration alone is not evidence.
    A promoted source moves OUT of remediation into fresh-alert so the buckets
    stay disjoint and still partition ``enabled_sources``. Temporary
    understatement is safe; overstatement is not.
    """
    mode_counts = {mode: 0 for mode in _COUNTED_MODES}
    fresh: list[dict[str, Any]] = []
    for item in enabled_sources:
        mode = str(item.get("monitoring_mode") or "").lower().strip()
        if mode in mode_counts:
            mode_counts[mode] += 1
        if mode == "fresh_alert" and item.get("alert_eligible") is True:
            fresh.append(item)
        elif proxy_remediation_verified(item, status_map=status_map):
            fresh.append(item)
            if mode in mode_counts:
                mode_counts[mode] -= 1  # promoted: counted as fresh-alert only
    return fresh, mode_counts


def _status_map_for(
    enabled_sources: list[dict[str, Any]],
    root: Path,
    base_dir: Path | None,
) -> dict[str, str]:
    """Read the run trail ONCE — and only when a source is proxy-routed (the
    routing predicate is pure config, no I/O)."""
    if not any(proxy_unblocked_remediation(item) for item in enabled_sources):
        return {}
    runs_file = (
        source_run_path()
        if base_dir is None
        else root / "data" / "source_runs" / "source_runs.jsonl"
    )
    return latest_run_status_map(runs_file)


def _market_enabled_sources(
    root: Path,
    market_code: str,
    excluded: set[str],
) -> list[dict[str, Any]]:
    sources = _load_sources(root)
    return [
        item
        for item in sources
        if str(item.get("jurisdiction") or "").upper() == market_code
        and bool(item.get("enabled"))
        and not (
            str(item.get("source_id") or "").strip()
            and str(item.get("source_id") or "").strip() in excluded
        )
    ]


def build_enforcement_summary(
    market: str = "AE",
    *,
    base_dir: Path | None = None,
    excluded_source_ids: set[str] | frozenset[str] | None = None,
) -> dict[str, Any]:
    """Honest coverage summary for the enforcement-monitoring capability.

    Only sources flagged ``enforcement_feature`` are considered, and the
    customer-facing ``fresh_alert_count`` counts ONLY those that are genuinely
    fresh-alert eligible (enabled + monitoring_mode fresh_alert + alert_eligible,
    or a proxy-remediation source with a verified recent run). Candidate /
    remediation enforcement sources are surfaced in their own buckets so the
    coverage matrix is complete and truthful, but they are NEVER counted as
    monitored — a bot-walled or JS-only enforcement page must not inflate the
    number we show a customer.
    """
    root = base_dir or _BASE_DIR
    market_code = str(market or "AE").upper().strip() or "AE"
    excluded = {str(s).strip() for s in (excluded_source_ids or set()) if str(s).strip()}
    enabled_sources = _market_enabled_sources(root, market_code, excluded)
    enforcement_sources = [
        item for item in enabled_sources if item.get("enforcement_feature") is True
    ]
    status_map = _status_map_for(enforcement_sources, root, base_dir)
    fresh, _ = _classify_fresh_alert(enforcement_sources, status_map)
    fresh_ids = {id(item) for item in fresh}

    buckets = {mode: 0 for mode in _COUNTED_MODES}
    fresh_alert_source_ids: list[str] = []
    for item in enforcement_sources:
        if id(item) in fresh_ids:
            buckets["fresh_alert"] += 1
            sid = str(item.get("source_id") or "").strip()
            if sid:
                fresh_alert_source_ids.append(sid)
        else:
            mode = str(item.get("monitoring_mode") or "").lower().strip()
            if mode in buckets:
                buckets[mode] += 1

    return {
        "ok": True,
        "market": market_code,
        "label": ENFORCEMENT_FEATURE_LABEL,
        "description": ENFORCEMENT_FEATURE_DESCRIPTION,
        "enforcement_source_count": len(enforcement_sources),
        "fresh_alert_count": buckets["fresh_alert"],
        "remediation_count": buckets["remediation"],
        "candidate_count": buckets["candidate"],
        "evidence_library_count": buckets["evidence_library"],
        "fresh_alert_source_ids": fresh_alert_source_ids,
        "disclaimer": "Monitoring intelligence only. Not legal advice.",
    }


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
    enabled_sources = _market_enabled_sources(root, market_code, excluded)
    # ONE classification pass, ONE trail read: the proxy-remediation branch uses
    # the VERIFIED variant so a proxy-routed source counts as fresh-alert only
    # after a recent successful production run is recorded (config alone is not
    # evidence — see sources.proxy_remediation_verified). The trail tail is read
    # once, and only when some source is proxy-routed — this runs on the
    # unauthenticated /api/health path.
    status_map = _status_map_for(enabled_sources, root, base_dir)
    fresh_alert_sources, mode_counts = _classify_fresh_alert(enabled_sources, status_map)
    fresh_ids = {id(item) for item in fresh_alert_sources}
    # Enforcement capability: the same verified-count discipline, restricted to
    # enforcement-tagged sources. Reuses the classification already computed —
    # no second trail read, no second source load.
    enforcement_sources = [
        item for item in enabled_sources if item.get("enforcement_feature") is True
    ]
    enforcement_fresh = [item for item in enforcement_sources if id(item) in fresh_ids]
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
        "enforcement": {
            "source_count": len(enforcement_sources),
            "fresh_alert_count": len(enforcement_fresh),
        },
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
