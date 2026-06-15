"""Safe batch runner for mass source activation queues.

The runner is intentionally conservative:
- default mode is no-save validation;
- evidence writes require explicit save-passing mode;
- sources.json is never updated;
- every updated entry is re-evaluated by mass_source_activation.evaluate_activation.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Callable

from app.mass_source_activation import (
    BLOCKED,
    CANDIDATE,
    REMEDIATION,
    evaluate_activation,
)


PRODUCT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUEUE_PATH = PRODUCT_ROOT / "config/mass_source_activation_queue.json"

DiscoveryFunc = Callable[..., dict[str, Any]]
IntakeFunc = Callable[..., dict[str, Any]]


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_queue(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Mass source activation queue must be a JSON object.")
    data.setdefault("sources", [])
    data.setdefault("summary", {})
    if not isinstance(data["sources"], list):
        raise ValueError("Mass source activation queue sources must be a list.")
    return data


def _write_queue(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _gate(status: str, reason: str, blocking_issues: list[str] | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "reason": reason,
        "reviewed_at": _now_iso(),
        "blocking_issues": blocking_issues or [],
    }


def _entry_matches(entry: dict[str, Any], *, regulator: str | None, source_id: str | None, status: str | None) -> bool:
    if source_id and entry.get("source_id") != source_id:
        return False
    if regulator:
        haystack = f"{entry.get('regulator', '')} {entry.get('source_id', '')}".lower()
        if regulator.lower() not in haystack:
            return False
    if status and entry.get("activation_status") != status and entry.get("current_state") != status:
        return False
    return True


def _source_config(entry: dict[str, Any]) -> dict[str, Any]:
    adapter_config = deepcopy(entry.get("adapter_config") or {})
    source = {
        "source_id": entry.get("source_id") or "mass-source-lab",
        "name": entry.get("source_id") or entry.get("url"),
        "url": entry.get("url"),
        "jurisdiction": "AE",
        "category": entry.get("source_type") or "source",
        "adapter_family": entry.get("adapter_family") or None,
        "adapter_name": entry.get("adapter_name") or None,
        "adapter_config": adapter_config,
        "expected_min_length": int(entry.get("expected_min_length") or 500),
        "baseline_runs_required": int(entry.get("baseline_runs_required") or 2),
    }
    if adapter_config.get("content_selector"):
        source["content_selector"] = adapter_config["content_selector"]
    if adapter_config.get("wait_for_selector"):
        source["wait_for_selector"] = adapter_config["wait_for_selector"]
    return source


def _apply_discovery(entry: dict[str, Any], report: dict[str, Any]) -> None:
    entry["last_discovery_at"] = _now_iso()
    warnings = list(report.get("warnings") or [])
    failure_code = str(report.get("failure_code") or "")
    access_status = str(report.get("access_status") or "")
    dom = report.get("dom_investigation") or {}

    if access_status in {"blocked", "stale_or_unavailable"} or failure_code:
        entry["discovery_status"] = "blocked" if access_status == "blocked" else "remediation"
        entry["failure_code"] = failure_code or "ACCESS_BLOCKED"
        entry["failure_reason"] = report.get("failure_reason") or "; ".join(warnings) or "Discovery could not access a usable source endpoint."
        entry["remediation_hint"] = report.get("remediation_hint") or "Review source-health and official alternate endpoints."
        entry["source_health_risk"] = report.get("source_health_risk") or "high"
        if access_status == "blocked":
            entry["current_state"] = BLOCKED
            entry["activation_status"] = BLOCKED
    else:
        entry["discovery_status"] = "discovered"
        if dom.get("recommended_adapter_family"):
            entry["adapter_family"] = dom.get("recommended_adapter_family")
        if dom.get("recommended_adapter_name"):
            entry["adapter_name"] = dom.get("recommended_adapter_name")
        config = dict(entry.get("adapter_config") or {})
        if dom.get("content_selector"):
            config.setdefault("content_selector", dom.get("content_selector"))
        if dom.get("wait_selector"):
            config.setdefault("wait_for_selector", dom.get("wait_selector"))
        if dom.get("item_selector"):
            config.setdefault("item_selector", dom.get("item_selector"))
        entry["adapter_config"] = config
        entry["noise_risk"] = dom.get("noise_risk") or entry.get("noise_risk") or "unknown"
        entry["source_health_risk"] = dom.get("source_health_risk") or entry.get("source_health_risk") or "unknown"
        entry["failure_reason"] = dom.get("failure_reason") or entry.get("failure_reason") or ""
        entry["remediation_hint"] = dom.get("remediation_hint") or entry.get("remediation_hint") or ""


def _passed_no_save(result: dict[str, Any]) -> bool:
    status = str(result.get("readiness_status") or result.get("status") or "").upper()
    quality = float(result.get("quality_score") or 0)
    return status == "CONFIRMED_ACCESSIBLE" and quality >= 60 and not result.get("nav_shell_detected")


def _apply_intake_result(entry: dict[str, Any], result: dict[str, Any], *, write_evidence: bool) -> None:
    passed = _passed_no_save(result)
    quality = int(result.get("quality_score") or 0)
    entry["last_no_save_test_at"] = _now_iso()
    entry["quality_score"] = quality
    entry["noise_risk"] = result.get("noise_risk") or entry.get("noise_risk") or "unknown"
    entry["source_health_risk"] = result.get("source_health_risk") or entry.get("source_health_risk") or "unknown"
    entry["failure_code"] = result.get("failure_code") or entry.get("failure_code") or ""
    entry["failure_reason"] = result.get("failure_reason") or entry.get("failure_reason") or ""
    entry["remediation_hint"] = result.get("remediation_hint") or entry.get("remediation_hint") or ""
    entry["normalized_hash"] = result.get("normalized_hash") or entry.get("normalized_hash") or ""
    entry["nav_shell"] = bool(result.get("nav_shell_detected") or result.get("nav_shell"))
    entry["shallow_content"] = bool(result.get("shallow_content"))
    entry["duplicate_hash"] = bool(result.get("duplicate_hash") or result.get("hash_collision"))

    if passed:
        entry["no_save_status"] = "passed"
        entry["current_state"] = "no_save_passed"
        entry["source_monitor_gate"] = _gate("pass", "No-save extraction produced meaningful public-source content.", [])
        entry["qa_critic_gate"] = _gate("hold", "No-save pass is preview only; proof and repeat baseline are still missing.", ["proof_missing", "baseline_missing"])
        entry["legal_language_gate"] = _gate("pass", "Safe wording: no-save candidate only, not monitoring-ready.", [])
        entry["code_architect_gate"] = _gate("hold", "Adapter strategy needs evidence and repeat baseline before activation.", ["proof_missing", "baseline_missing"])
    else:
        entry["no_save_status"] = "failed"
        if entry["failure_code"] in {"ACCESS_BLOCKED", "LIKELY_WAF_403"}:
            entry["current_state"] = BLOCKED
            entry["activation_status"] = BLOCKED
        else:
            entry["current_state"] = REMEDIATION
            entry["activation_status"] = REMEDIATION
        entry["qa_critic_gate"] = _gate("fail", "No-save result did not meet activation-quality threshold.", [entry["failure_code"] or "no_save_failed"])

    evidence_paths = result.get("evidence_paths") or {}
    if write_evidence and passed and evidence_paths:
        entry["evidence_status"] = "proof_saved"
        entry["proof_path"] = evidence_paths.get("proof_path") or result.get("proof_path") or entry.get("proof_path", "")
        entry["normalized_text_path"] = evidence_paths.get("normalized_text_path") or entry.get("normalized_text_path", "")
        entry["current_state"] = "proof_saved"
        entry["evidence_trail_gate"] = _gate("hold", "Proof was saved, but repeat baseline still must pass before activation.", ["baseline_missing"])
    else:
        entry["evidence_status"] = entry.get("evidence_status") or "none"
        entry["evidence_trail_gate"] = _gate("hold", "No proof and repeat baseline recorded for activation.", ["proof_missing", "baseline_missing"])


def _refresh_summary(data: dict[str, Any]) -> None:
    sources = data.get("sources") or []
    activation_ready = [item for item in sources if item.get("activation_status") == "activation_ready"]
    proof_backed = [item for item in sources if item.get("proof_path")]
    baseline_complete = [
        item for item in sources
        if item.get("proof_path") and int(item.get("baseline_runs_completed") or 0) >= int(item.get("baseline_runs_required") or 2)
    ]
    summary = data.setdefault("summary", {})
    summary["queue_entries"] = len(sources)
    summary["activation_ready_count"] = len(activation_ready)
    summary["proof_backed_count"] = len(proof_backed)
    summary["baseline_complete_count"] = len(baseline_complete)
    summary["did_reach_50_working_sources"] = len(activation_ready) >= 50
    summary["sources_json_changed"] = False
    summary["updated_at"] = _now_iso()


def run_mass_source_activation_batch(
    *,
    queue_path: str | Path = DEFAULT_QUEUE_PATH,
    regulator: str | None = None,
    source_id: str | None = None,
    status: str | None = None,
    limit: int | None = None,
    mode: str = "no-save-only",
    repeat_baseline: int = 0,
    discovery_func: DiscoveryFunc | None = None,
    intake_func: IntakeFunc | None = None,
    write_queue: bool = True,
) -> dict[str, Any]:
    """Run a scoped mass source activation batch and update queue state."""
    queue = Path(queue_path)
    data = _load_queue(queue)
    if mode not in {"discover-only", "no-save-only", "save-passing"}:
        raise ValueError("mode must be discover-only, no-save-only, or save-passing")

    if discovery_func is None:
        from app.source_discovery import discover_source
        discovery_func = discover_source
    if intake_func is None:
        from app.source_intake import run_source_intake
        intake_func = run_source_intake

    candidates = [
        entry for entry in data["sources"]
        if isinstance(entry, dict) and _entry_matches(entry, regulator=regulator, source_id=source_id, status=status)
    ]
    if limit is not None:
        candidates = candidates[: max(0, int(limit))]

    processed: list[dict[str, Any]] = []
    saved_evidence_count = 0
    no_save_passed_count = 0
    warnings: list[str] = []
    if repeat_baseline:
        warnings.append("repeat_baseline requested; baseline automation is not run unless evidence/proof support exists.")

    for entry in candidates:
        before = deepcopy(entry)
        report = discovery_func(
            entry.get("url"),
            include_network=False,
            include_sitemap=True,
            include_feeds=True,
            include_documents=True,
            max_links=25,
        )
        _apply_discovery(entry, report or {})
        if mode != "discover-only":
            no_save_result = intake_func(_source_config(entry), write_evidence=False)
            _apply_intake_result(entry, no_save_result or {}, write_evidence=False)
            if entry.get("no_save_status") == "passed":
                no_save_passed_count += 1
            if mode == "save-passing" and entry.get("no_save_status") == "passed":
                save_result = intake_func(_source_config(entry), write_evidence=True)
                _apply_intake_result(entry, save_result or {}, write_evidence=True)
                if entry.get("evidence_status") == "proof_saved":
                    saved_evidence_count += 1
        evaluated = evaluate_activation(entry)
        entry.clear()
        entry.update(evaluated)
        processed.append({
            "source_id": entry.get("source_id"),
            "before_status": before.get("activation_status"),
            "after_status": entry.get("activation_status"),
            "no_save_status": entry.get("no_save_status"),
            "quality_score": entry.get("quality_score"),
            "failure_code": entry.get("failure_code"),
            "failure_reason": entry.get("failure_reason"),
            "remediation_hint": entry.get("remediation_hint"),
        })

    _refresh_summary(data)
    if write_queue:
        _write_queue(queue, data)

    return {
        "queue_path": str(queue),
        "mode": mode,
        "processed_count": len(processed),
        "no_save_passed_count": no_save_passed_count,
        "saved_evidence_count": saved_evidence_count,
        "activation_ready_count": data.get("summary", {}).get("activation_ready_count", 0),
        "sources_json_changed": False,
        "repeat_baseline_requested": repeat_baseline,
        "warnings": warnings,
        "processed": processed,
    }
