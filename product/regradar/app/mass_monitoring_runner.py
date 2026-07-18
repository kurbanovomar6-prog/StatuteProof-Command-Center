"""Safe queue-driven mass monitoring runner.

This runner is intentionally narrower than the legacy ``run.py all`` command:

- default mode is dry-run and no-alerts;
- only activation-ready queue entries are processed by default;
- candidate/remediation/blocked/rejected entries are skipped;
- sources.json is never updated;
- no customer/Telegram/email delivery is performed.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
import json
from pathlib import Path
from time import sleep
from typing import Any, Callable
from urllib.parse import urlparse

from app.mass_source_activation import ACTIVATION_READY
from app.mass_source_activation_runner import DEFAULT_QUEUE_PATH


MONITOR_OK = "MONITOR_OK"
MONITOR_DISCONNECTED = "MONITOR_DISCONNECTED"
QUALITY_DROP = "QUALITY_DROP"
SELECTOR_BROKEN = "SELECTOR_BROKEN"
HASH_COLLISION = "HASH_COLLISION"
NAV_SHELL_ONLY = "NAV_SHELL_ONLY"
SOURCE_STRUCTURE_CHANGED = "SOURCE_STRUCTURE_CHANGED"
REMEDIATION_REQUIRED = "REMEDIATION_REQUIRED"
MANUAL_CHECK_REQUIRED = "MANUAL_CHECK_REQUIRED"

SAFE_MONITOR_STATES = {ACTIVATION_READY, "enabled"}
UNSAFE_MONITOR_STATES = {"candidate", "discovered", "no_save_passed", "proof_saved", "baseline_pending", "remediation", "blocked", "rejected"}

PRODUCT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCES_PATH = PRODUCT_ROOT / "sources.json"

IntakeFunc = Callable[..., dict[str, Any]]


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _domain(url: str) -> str:
    return urlparse(url or "").netloc.lower()


def _status(value: Any) -> str:
    return str(value or "").strip().lower()


def _entry_state(entry: dict[str, Any]) -> str:
    return _status(entry.get("activation_status") or entry.get("current_state"))


def _is_activation_ready(entry: dict[str, Any]) -> bool:
    return _entry_state(entry) == ACTIVATION_READY or bool(entry.get("can_activate"))


def _entry_matches(entry: dict[str, Any], *, regulator: str | None, source_id: str | None) -> bool:
    if source_id and entry.get("source_id") != source_id:
        return False
    if regulator:
        haystack = f"{entry.get('regulator', '')} {entry.get('source_id', '')}".lower()
        if regulator.lower() not in haystack:
            return False
    return True


def _source_config(entry: dict[str, Any]) -> dict[str, Any]:
    adapter_config = deepcopy(entry.get("adapter_config") or {})
    source = {
        "source_id": entry.get("source_id") or entry.get("id") or "mass-monitor-source",
        "name": entry.get("name") or entry.get("source_id") or entry.get("url"),
        "url": entry.get("url"),
        "jurisdiction": entry.get("jurisdiction") or "AE",
        "category": entry.get("source_type") or entry.get("category") or "source",
        "adapter_family": entry.get("adapter_family") or None,
        "adapter_name": entry.get("adapter_name") or None,
        "adapter_config": adapter_config,
        "expected_min_length": int(entry.get("expected_min_length") or 500),
        "baseline_runs_required": int(entry.get("baseline_runs_required") or 2),
    }
    should_promote_adapter_selector = source["adapter_family"] in {"static_html", "playwright_selector"}
    content_selector = entry.get("content_selector") or (
        adapter_config.get("content_selector") if should_promote_adapter_selector else None
    )
    wait_selector = entry.get("wait_for_selector") or (
        adapter_config.get("wait_for_selector") if should_promote_adapter_selector else None
    )
    if content_selector:
        source["content_selector"] = content_selector
    if wait_selector:
        source["wait_for_selector"] = wait_selector
    if entry.get("fetch_method"):
        source["fetch_method"] = entry.get("fetch_method")
    return source


def _enabled_sources_as_entries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    raw = _load_json(path)
    if not isinstance(raw, list):
        return []
    entries: list[dict[str, Any]] = []
    for source in raw:
        if not isinstance(source, dict) or not source.get("enabled"):
            continue
        source_id = source.get("source_id") or source.get("id")
        entries.append({
            "source_id": source_id,
            "name": source.get("name") or source_id,
            "url": source.get("url"),
            "regulator": source.get("regulator") or source.get("name") or "",
            "source_type": source.get("category") or "source",
            "official_status": "official",
            "activation_status": "enabled",
            "current_state": "enabled",
            "adapter_family": source.get("adapter_family"),
            "adapter_name": source.get("adapter_name"),
            "adapter_config": source.get("adapter_config") or {},
            "content_selector": source.get("content_selector"),
            "wait_for_selector": source.get("wait_for_selector"),
            "fetch_method": source.get("fetch_method"),
            "expected_min_length": source.get("expected_min_length") or 500,
            "baseline_runs_required": source.get("baseline_runs_required") or 2,
            "can_activate": True,
        })
    return entries


def map_source_health_status(
    result: dict[str, Any], *, expected_min_length: int | None = None
) -> str:
    """Map a Source Lab/intake result to a monitoring health status.

    Two gates guard the MONITOR_OK path (OPS audit 2026-07-12 — seven MOET
    sources sat on a 146-byte "site under maintenance" page classified
    MONITOR_OK, so the maintenance stub became the trusted baseline):

    * ``http_status`` >= 400 can NEVER classify as OK — an error body that
      hashed cleanly is still an error body.
    * a capture shorter than the source's declared ``expected_min_length`` is
      a shell/maintenance stub, not monitorable content — QUALITY_DROP, so it
      neither becomes a baseline nor masks an outage as "no change".
    """
    failure_code = str(result.get("failure_code") or "").upper()
    status = str(result.get("status") or result.get("readiness_status") or "").upper()
    quality = int(result.get("quality_score") or 0)

    if result.get("hash_collision") or result.get("duplicate_hash") or failure_code == "DUPLICATE_BOILERPLATE_HASH":
        return HASH_COLLISION
    if result.get("nav_shell_detected") or result.get("nav_shell") or status == "NAV_SHELL_ONLY" or failure_code == "NAV_SHELL_ONLY":
        return NAV_SHELL_ONLY
    if failure_code == "SELECTOR_NOT_FOUND" or status == "NEEDS_SELECTOR_REVIEW":
        return SELECTOR_BROKEN
    # A bot-wall / JS-challenge is a REACH problem (needs headless/proxy), not a
    # generic content dip — classify it as remediation before the QUALITY_DROP
    # gate so the distinction survives to the dashboard (code-review 2026-07-18).
    if failure_code == "BOT_WALL" or result.get("access_status") == "blocked":
        return REMEDIATION_REQUIRED
    if status == "QUALITY_DROP":
        return QUALITY_DROP
    if failure_code == "SOURCE_STRUCTURE_CHANGED":
        return SOURCE_STRUCTURE_CHANGED
    if failure_code in {"ACCESS_BLOCKED", "LIKELY_WAF_403"} or status in {"BLOCKED", "UNSUPPORTED"}:
        return REMEDIATION_REQUIRED
    # HTTP-error gate: 4xx/5xx bodies must never reach an OK classification.
    try:
        http_status = int(result.get("http_status") or 0)
    except (TypeError, ValueError):
        http_status = 0
    if http_status >= 400:
        return REMEDIATION_REQUIRED
    # Min-length gate: below the source's declared floor = stub, never OK.
    chars_raw = result.get("chars_normalized")
    try:
        chars = int(chars_raw) if chars_raw is not None else None
    except (TypeError, ValueError):
        chars = None
    if expected_min_length and chars is not None and chars < int(expected_min_length):
        return QUALITY_DROP
    if quality and quality < 60:
        return QUALITY_DROP
    if status == "CONFIRMED_ACCESSIBLE" and result.get("normalized_hash"):
        return MONITOR_OK
    if status == "CONFIRMED_ACCESSIBLE" and quality >= 60:
        return MONITOR_OK
    if result.get("failure_reason") or failure_code:
        return REMEDIATION_REQUIRED
    return MANUAL_CHECK_REQUIRED


def _load_queue(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    if not isinstance(data, dict):
        raise ValueError("Mass source activation queue must be a JSON object.")
    data.setdefault("sources", [])
    data.setdefault("summary", {})
    if not isinstance(data["sources"], list):
        raise ValueError("Mass source activation queue sources must be a list.")
    return data


def _selected_entries(
    *,
    queue_data: dict[str, Any],
    include_enabled_sources: bool,
    sources_path: Path,
    regulator: str | None,
    source_id: str | None,
    limit: int | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw_entries = [entry for entry in queue_data.get("sources", []) if isinstance(entry, dict)]
    if include_enabled_sources:
        raw_entries.extend(_enabled_sources_as_entries(sources_path))

    selected: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    per_source_seen: set[str] = set()

    for entry in raw_entries:
        sid = str(entry.get("source_id") or entry.get("id") or "")
        if sid and sid in per_source_seen:
            continue
        if sid:
            per_source_seen.add(sid)
        if not _entry_matches(entry, regulator=regulator, source_id=source_id):
            continue
        if _is_activation_ready(entry) or _entry_state(entry) == "enabled":
            selected.append(entry)
        else:
            skipped.append({
                "source_id": entry.get("source_id"),
                "activation_status": entry.get("activation_status"),
                "skip_reason": f"unsafe_state:{entry.get('activation_status') or entry.get('current_state')}",
            })

    if limit is not None:
        selected = selected[: max(0, int(limit))]
    return selected, skipped


def run_mass_monitoring_batch(
    *,
    queue_path: str | Path = DEFAULT_QUEUE_PATH,
    sources_path: str | Path = DEFAULT_SOURCES_PATH,
    regulator: str | None = None,
    source_id: str | None = None,
    limit: int | None = None,
    dry_run: bool = True,
    no_alerts: bool = True,
    save_proof: bool = False,
    throttle_seconds: float = 0.0,
    max_per_domain: int = 3,
    include_enabled_sources: bool = False,
    intake_func: IntakeFunc | None = None,
    write_queue: bool = True,
) -> dict[str, Any]:
    """Run a safe monitoring batch over activation-ready sources only."""
    queue = Path(queue_path)
    sources = Path(sources_path)
    data = _load_queue(queue)
    if intake_func is None:
        from app.source_intake import run_source_intake
        intake_func = run_source_intake

    selected, skipped = _selected_entries(
        queue_data=data,
        include_enabled_sources=include_enabled_sources,
        sources_path=sources,
        regulator=regulator,
        source_id=source_id,
        limit=limit,
    )

    domain_counts: dict[str, int] = {}
    results: list[dict[str, Any]] = []
    processed_by_id: dict[str, dict[str, Any]] = {}
    write_evidence = bool(save_proof and not dry_run)

    for entry in selected:
        domain = _domain(entry.get("url") or "")
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        if max_per_domain and domain_counts[domain] > max_per_domain:
            skipped.append({
                "source_id": entry.get("source_id"),
                "activation_status": entry.get("activation_status"),
                "skip_reason": f"domain_limit:{domain}",
            })
            continue

        if throttle_seconds and results:
            sleep(float(throttle_seconds))

        source = _source_config(entry)
        result = intake_func(source, write_evidence=write_evidence)
        health = map_source_health_status(
            result or {},
            expected_min_length=int(entry.get("expected_min_length") or 500),
        )
        normalized_hash = (result or {}).get("normalized_hash") or ""
        previous_hash = entry.get("last_monitor_hash") or entry.get("normalized_hash") or ""
        change_detected = bool(previous_hash and normalized_hash and previous_hash != normalized_hash)
        monitor_result = {
            "source_id": entry.get("source_id"),
            "url": entry.get("url"),
            "regulator": entry.get("regulator"),
            "source_health_status": health,
            "quality_score": int((result or {}).get("quality_score") or 0),
            "normalized_hash": normalized_hash,
            "previous_hash": previous_hash,
            "change_detected": change_detected,
            "failure_code": (result or {}).get("failure_code") or "",
            "failure_reason": (result or {}).get("failure_reason") or "",
            "remediation_hint": (result or {}).get("remediation_hint") or "",
            "proof_path": (result or {}).get("proof_path") or "",
            "evidence_written": bool((result or {}).get("evidence_written")),
            "alert_sent": False,
        }
        results.append(monitor_result)
        processed_by_id[str(entry.get("source_id") or "")] = monitor_result

    if write_queue and not dry_run:
        now = _now_iso()
        for entry in data.get("sources", []):
            sid = str(entry.get("source_id") or "")
            if sid not in processed_by_id:
                continue
            monitor_result = processed_by_id[sid]
            entry["last_monitor_run_at"] = now
            entry["last_monitor_status"] = monitor_result["source_health_status"]
            entry["last_monitor_quality_score"] = monitor_result["quality_score"]
            entry["last_monitor_hash"] = monitor_result["normalized_hash"] or entry.get("last_monitor_hash", "")
            entry["last_monitor_failure_code"] = monitor_result["failure_code"]
            entry["last_monitor_failure_reason"] = monitor_result["failure_reason"]
            entry["last_monitor_remediation_hint"] = monitor_result["remediation_hint"]
            entry["monitoring_run_count"] = int(entry.get("monitoring_run_count") or 0) + 1
        summary = data.setdefault("summary", {})
        summary["last_mass_monitor_run_at"] = now
        summary["last_mass_monitor_processed_count"] = len(results)
        summary["last_mass_monitor_skipped_count"] = len(skipped)
        summary["last_mass_monitor_alerts_sent"] = 0
        summary["sources_json_changed"] = False
        _write_json(queue, data)

    return {
        "mode": "dry-run" if dry_run else "save-proof" if save_proof else "monitor",
        "activation_ready_only": True,
        "include_enabled_sources": include_enabled_sources,
        "alert_delivery_enabled": bool(not no_alerts),
        "save_proof": bool(save_proof and not dry_run),
        "sources_json_changed": False,
        "processed_count": len(results),
        "skipped_count": len(skipped),
        "results": results,
        "skipped": skipped,
        "source_health_counts": {status: sum(1 for item in results if item["source_health_status"] == status) for status in {
            MONITOR_OK,
            MONITOR_DISCONNECTED,
            QUALITY_DROP,
            SELECTOR_BROKEN,
            HASH_COLLISION,
            NAV_SHELL_ONLY,
            SOURCE_STRUCTURE_CHANGED,
            REMEDIATION_REQUIRED,
            MANUAL_CHECK_REQUIRED,
        }},
        "warnings": [] if no_alerts else ["Alert delivery requested but this runner does not send customer/Telegram/email alerts."],
    }
