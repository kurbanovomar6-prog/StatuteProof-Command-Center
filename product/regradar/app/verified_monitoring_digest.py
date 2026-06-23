"""Operator-only monitoring digest for queued regulatory change alerts.

The digest is intentionally conservative: it classifies saved alerts for
founder/operator review, but never approves customer delivery. It exists to
separate useful monitoring signals from parser noise, evidence gaps, and source
health blockers before any brief or outreach claim is made.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.evidence_records import build_risk_brief_inputs
from app.source_health_timeline import build_operator_source_health_report


_BASE_DIR = Path(__file__).parent.parent
_ALERT_QUEUE = Path("data") / "alert_queue"
_SOURCE_RUNS = Path("data") / "source_runs" / "source_runs.jsonl"
_DISCLAIMER = (
    "Operator-only monitoring intelligence. Not legal advice, not customer "
    "delivery, and not evidence of complete UAE coverage."
)


def build_verified_monitoring_digest(
    *,
    base_dir: Path | None = None,
    failed_threshold: int = 3,
) -> dict[str, Any]:
    """Build a deterministic digest from saved alerts, runs, and health data."""

    root = Path(base_dir) if base_dir is not None else _BASE_DIR
    alerts = _load_alerts(root)
    sources = _load_sources(root)
    runs_by_source = _load_runs_by_source(root)
    source_health = build_operator_source_health_report(base_dir=root, failed_threshold=failed_threshold)
    health_by_source = {
        str(row.get("source_id") or ""): row
        for row in source_health.get("alerts", [])
        if isinstance(row, dict)
    }

    items = [
        _digest_item(alert, root=root, sources=sources, runs_by_source=runs_by_source, health_by_source=health_by_source)
        for alert in alerts
    ]
    items.sort(key=lambda item: (item.get("queued_at") or item.get("run_at") or "", item.get("source_id") or ""))

    status_counts = Counter(str(item.get("triage_status") or "") for item in items)
    source_family_counts = Counter(str(item.get("source_family") or "Other") for item in items)
    linked_count = sum(1 for item in items if item.get("evidence_record_id"))
    brief_eligible_count = sum(1 for item in items if item.get("brief_input_eligible") is True)
    likely_noise_count = sum(1 for item in items if item.get("triage_status") == "LIKELY_NOISE")
    parser_or_noise_count = sum(1 for item in items if item.get("triage_status") == "NEEDS_PARSER_REVIEW" or item.get("noise_indicators"))
    review_ready_count = sum(1 for item in items if item.get("triage_status") == "REVIEW_READY")
    pending_review_count = sum(1 for item in items if str(item.get("alert_status") or "").upper() == "PENDING_REVIEW")

    return {
        "schema_version": "1.0",
        "generated_at_utc": _utc_now(),
        "operator_only": True,
        "customer_delivery": False,
        "external_send": False,
        "disclaimer": _DISCLAIMER,
        "summary": {
            "alerts_total": len(items),
            "pending_review": pending_review_count,
            "canonical_evidence_linked": linked_count,
            "brief_input_eligible": brief_eligible_count,
            "review_ready": review_ready_count,
            "likely_noise": likely_noise_count,
            "parser_or_noise_indicators": parser_or_noise_count,
            "source_health_blocked": int(source_health.get("sources_requiring_operator_review") or 0),
            "historical_source_health_blocked": int(
                source_health.get("historical_sources_requiring_operator_review") or 0
            ),
            "missing_evidence_links": sum(1 for item in items if "missing_canonical_evidence_record_id" in item["blockers"]),
            "customer_delivery_allowed": 0,
        },
        "status_counts": dict(sorted(status_counts.items())),
        "source_family_counts": dict(sorted(source_family_counts.items())),
        "source_health": {
            "operator_only": source_health.get("operator_only") is True,
            "customer_delivery": source_health.get("customer_delivery") is True,
            "external_send": source_health.get("external_send") is True,
            "sources_checked": source_health.get("sources_checked", 0),
            "sources_requiring_operator_review": source_health.get("sources_requiring_operator_review", 0),
            "historical_sources_requiring_operator_review": source_health.get(
                "historical_sources_requiring_operator_review", 0
            ),
            "alerts": source_health.get("alerts", []),
            "historical_alerts": source_health.get("historical_alerts", []),
        },
        "items": items,
        "next_actions": _next_actions(items, source_health),
    }


def render_verified_monitoring_digest_markdown(digest: dict[str, Any]) -> str:
    """Render the digest as a compact operator review report."""

    summary = digest.get("summary") if isinstance(digest.get("summary"), dict) else {}
    source_health = digest.get("source_health") if isinstance(digest.get("source_health"), dict) else {}
    items = digest.get("items") if isinstance(digest.get("items"), list) else []
    review_candidates = [item for item in items if item.get("triage_status") in {"REVIEW_READY", "HOLD", "NEEDS_PARSER_REVIEW"}]
    likely_noise = [item for item in items if item.get("triage_status") == "LIKELY_NOISE"]

    lines = [
        "# StatuteProof Verified Monitoring Digest",
        "",
        f"Generated: {digest.get('generated_at_utc') or '<unknown>'}",
        "",
        "**Scope:** operator-only triage of saved alert queue entries. This is not a customer brief.",
        "",
        "## Summary",
        "",
        f"- Alerts queued: {summary.get('alerts_total', 0)}",
        f"- Pending review: {summary.get('pending_review', 0)}",
        f"- Linked to canonical evidence: {summary.get('canonical_evidence_linked', 0)}",
        f"- Brief-input eligible after evidence gate: {summary.get('brief_input_eligible', 0)}",
        f"- Review-ready, hold, or parser-review candidates: {len(review_candidates)}",
        f"- Alerts with parser/noise indicators: {summary.get('parser_or_noise_indicators', 0)}",
        f"- Clean likely-noise alerts: {summary.get('likely_noise', 0)}",
        f"- Source-health blockers: {summary.get('source_health_blocked', 0)}",
        f"- Historical disabled-source failures: {summary.get('historical_source_health_blocked', 0)}",
        f"- Customer delivery allowed: {summary.get('customer_delivery_allowed', 0)}",
        "",
        "## Active Source Health Blockers",
        "",
    ]
    health_alerts = source_health.get("alerts") if isinstance(source_health.get("alerts"), list) else []
    if health_alerts:
        for alert in health_alerts:
            lines.append(
                "- "
                f"{alert.get('source_id')}: {alert.get('consecutive_failed_runs')} consecutive failed/quality-drop runs; "
                f"latest={alert.get('latest_change_status')} at {alert.get('latest_run_at')}"
            )
    else:
        lines.append("- None detected at the configured threshold.")

    historical_alerts = (
        source_health.get("historical_alerts")
        if isinstance(source_health.get("historical_alerts"), list)
        else []
    )
    lines.extend(["", "## Historical / Disabled Source Failures", ""])
    if historical_alerts:
        for alert in historical_alerts:
            lines.append(
                "- "
                f"{alert.get('source_id')}: {alert.get('consecutive_failed_runs')} historical failed/quality-drop runs; "
                f"registry_enabled={alert.get('registry_enabled')}; status={alert.get('registry_status') or 'unknown'}; "
                "not counted as an active monitoring blocker."
            )
    else:
        lines.append("- None detected at the configured threshold.")

    lines.extend(["", "## Review Queue Triage", ""])
    for item in review_candidates[:25]:
        reason_values = _dedupe((item.get("blockers") or []) + (item.get("review_reasons") or []))
        reasons = ", ".join(reason_values or ["operator review required"])
        lines.append(
            "- "
            f"{item.get('triage_status')}: {item.get('source_id')} ({item.get('source_family')}) - "
            f"{item.get('diff_summary') or '<no diff summary>'}. Reasons: {reasons}. "
            f"Evidence: {item.get('evidence_record_id') or 'not linked'}."
        )

    if likely_noise:
        lines.extend(["", "## Likely Noise / Parser Review", ""])
        for item in likely_noise[:15]:
            lines.append(
                "- "
                f"{item.get('source_id')}: {item.get('diff_summary') or '<no diff summary>'}. "
                f"Noise indicators: {', '.join(item.get('noise_indicators') or [])}."
            )

    lines.extend(["", "## Required Next Actions", ""])
    for action in digest.get("next_actions") or []:
        lines.append(f"- {action}")

    lines.extend(["", "## Boundary", "", digest.get("disclaimer") or _DISCLAIMER, ""])
    return "\n".join(lines)


def _digest_item(
    alert: dict[str, Any],
    *,
    root: Path,
    sources: dict[str, dict[str, Any]],
    runs_by_source: dict[str, list[dict[str, Any]]],
    health_by_source: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_id = str(alert.get("source_id") or "").strip()
    source = sources.get(source_id, {})
    diff = _load_diff(alert, root)
    evidence_record_id = str(alert.get("evidence_record_id") or "").strip()
    evidence_gate = _evidence_gate(evidence_record_id, root) if evidence_record_id else None
    source_health_alert = health_by_source.get(source_id)
    runs = runs_by_source.get(source_id, [])

    blockers: list[str] = []
    review_reasons: list[str] = []
    noise_indicators: list[str] = []
    if source_health_alert:
        blockers.append("source_health_operator_review_required")
    if not evidence_record_id:
        blockers.append("missing_canonical_evidence_record_id")
    elif not evidence_gate or evidence_gate.get("eligible") is not True:
        blockers.append("canonical_evidence_not_brief_eligible")

    _classify_diff(diff, review_reasons=review_reasons, noise_indicators=noise_indicators)
    if _looks_like_transient_revert(alert, runs):
        review_reasons.append("normalized hash returned to an earlier baseline")
        noise_indicators.append("transient_extraction_or_source_state_candidate")

    triage_status = _triage_status(blockers, review_reasons, noise_indicators)
    if triage_status == "REVIEW_READY" and not review_reasons:
        review_reasons.append("meaningful change detected and evidence gate did not block")

    return {
        "alert_id": _alert_id(alert),
        "source_id": source_id,
        "source_name": alert.get("source_name") or source.get("name") or source_id,
        "source_url": alert.get("source_url") or source.get("url") or "",
        "source_family": _source_family(source_id, source),
        "company_use_case": _company_use_case(source_id, source),
        "monitoring_mode": source.get("monitoring_mode") or "",
        "alert_status": alert.get("status") or "",
        "change_status": alert.get("change_status") or "",
        "run_id": alert.get("run_id") or "",
        "run_at": alert.get("run_at") or "",
        "queued_at": alert.get("queued_at") or "",
        "evidence_record_id": evidence_record_id,
        "brief_input_eligible": bool(evidence_gate and evidence_gate.get("eligible") is True),
        "evidence_gate_blocked_reason": "" if not evidence_gate else str(evidence_gate.get("blocked_reason") or ""),
        "human_reviewed": bool(alert.get("human_reviewed") is True),
        "delivery_approved": bool(alert.get("delivery_approved") is True),
        "customer_delivery_allowed": False,
        "diff_quality": "" if not diff else str(diff.get("diff_quality") or ""),
        "meaningful_change_detected": None if not diff else diff.get("meaningful_change_detected"),
        "diff_summary": "" if not diff else str(diff.get("diff_summary") or ""),
        "diff_counts": _diff_counts(diff),
        "triage_status": triage_status,
        "blockers": blockers,
        "review_reasons": _dedupe(review_reasons),
        "noise_indicators": _dedupe(noise_indicators),
        "proof_block_path": str(alert.get("proof_block_path") or ""),
        "diff_json_path": str(alert.get("diff_json_path") or ""),
    }


def _classify_diff(diff: dict[str, Any] | None, *, review_reasons: list[str], noise_indicators: list[str]) -> None:
    if diff is None:
        review_reasons.append("diff_json_missing_or_unreadable")
        return
    quality = str(diff.get("diff_quality") or "").upper()
    meaningful = diff.get("meaningful_change_detected")
    added = int(diff.get("added_count") or 0)
    removed = int(diff.get("removed_count") or 0)
    changed = int(diff.get("changed_count") or 0)
    unchanged = int(diff.get("unchanged_count") or 0)

    if quality not in {"GOOD", ""}:
        noise_indicators.append(f"diff_quality_{quality.lower()}")
    if meaningful is False:
        noise_indicators.append("meaningful_change_detected_false")
    if changed >= 100:
        review_reasons.append("large diff requires human review before interpretation")
    if changed >= 100 and (added + removed) == 0:
        noise_indicators.append("possible_full_page_or_pdf_reflow")
    if added == 0 and removed == 0 and changed <= 2:
        noise_indicators.append("small_counter_or_page_state_change_candidate")
    if unchanged <= 1 and changed >= 10:
        noise_indicators.append("possible_locale_or_template_switch")
    if _chunks_look_like_boilerplate(diff):
        noise_indicators.append("boilerplate_navigation_or_widget_change_candidate")
    if meaningful is True and not noise_indicators:
        review_reasons.append("meaningful change detected by source diff")


def _triage_status(blockers: list[str], review_reasons: list[str], noise_indicators: list[str]) -> str:
    if blockers:
        return "HOLD"
    if noise_indicators and not review_reasons:
        return "LIKELY_NOISE"
    if noise_indicators and review_reasons:
        return "NEEDS_PARSER_REVIEW"
    return "REVIEW_READY"


def _load_alerts(root: Path) -> list[dict[str, Any]]:
    queue_dir = root / _ALERT_QUEUE
    if not queue_dir.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(queue_dir.glob("*.json")):
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(parsed, dict):
            parsed["_alert_file"] = str(path.relative_to(root))
            rows.append(parsed)
    return rows


def _load_sources(root: Path) -> dict[str, dict[str, Any]]:
    path = root / "sources.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    rows = payload.get("sources", payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("source_id") or row.get("id") or "").strip()
        if source_id:
            out[source_id] = row
    return out


def _load_runs_by_source(root: Path) -> dict[str, list[dict[str, Any]]]:
    path = root / _SOURCE_RUNS
    if not path.exists():
        return {}
    rows: dict[str, list[dict[str, Any]]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(parsed, dict):
            continue
        source_id = str(parsed.get("source_id") or "").strip()
        if source_id:
            rows.setdefault(source_id, []).append(parsed)
    return rows


def _load_diff(alert: dict[str, Any], root: Path) -> dict[str, Any] | None:
    value = str(alert.get("diff_json_path") or "").strip()
    if not value:
        proof = alert.get("proof_block") if isinstance(alert.get("proof_block"), dict) else {}
        value = str(proof.get("diff_json_path") or "").strip()
    if not value:
        return None
    path = root / value
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _evidence_gate(evidence_record_id: str, root: Path) -> dict[str, Any]:
    try:
        return build_risk_brief_inputs(evidence_record_id, base_dir=root)
    except Exception as exc:  # defensive: digest must report, not crash, on one bad record
        return {"eligible": False, "blocked_reason": str(exc)}


def _diff_counts(diff: dict[str, Any] | None) -> dict[str, int]:
    if not diff:
        return {"added": 0, "removed": 0, "changed": 0, "unchanged": 0}
    return {
        "added": int(diff.get("added_count") or 0),
        "removed": int(diff.get("removed_count") or 0),
        "changed": int(diff.get("changed_count") or 0),
        "unchanged": int(diff.get("unchanged_count") or 0),
    }


def _chunks_look_like_boilerplate(diff: dict[str, Any]) -> bool:
    chunks: list[str] = []
    for key in ("added_chunks", "removed_chunks"):
        values = diff.get(key)
        if isinstance(values, list):
            chunks.extend(str(value) for value in values[:5])
    for change in diff.get("changed_chunks") or []:
        if isinstance(change, dict):
            chunks.extend(str(value) for value in (change.get("before") or [])[:2])
            chunks.extend(str(value) for value in (change.get("after") or [])[:2])
    if not chunks:
        return False
    text = " ".join(chunks).lower()
    boilerplate_terms = (
        "rate this page",
        "chatting with your regulatory intelligence assistant",
        "document or file requested was not found",
        "feedback",
        "subscribe to our newsletter",
        "browser compatibility",
        "row hash",
        "locale",
        "accessibility",
    )
    return any(term in text for term in boilerplate_terms)


def _looks_like_transient_revert(alert: dict[str, Any], runs: list[dict[str, Any]]) -> bool:
    run_id = str(alert.get("run_id") or "").strip()
    normalized_hash = str(alert.get("normalized_hash") or "").strip()
    if not run_id or not normalized_hash or len(runs) < 3:
        return False
    for index, run in enumerate(runs):
        if str(run.get("run_id") or "") != run_id:
            continue
        if index < 2:
            return False
        previous_hash = str(runs[index - 1].get("normalized_hash") or "")
        if previous_hash == normalized_hash:
            return False
        earlier_hashes = {str(row.get("normalized_hash") or "") for row in runs[: index - 1]}
        return normalized_hash in earlier_hashes
    return False


def _source_family(source_id: str, source: dict[str, Any]) -> str:
    text = f"{source_id} {source.get('name') or ''} {source.get('category') or ''}".lower()
    if "vara" in text or "virtual asset" in text:
        return "VARA"
    if "cbuae" in text or "central-bank" in text or "payment" in text:
        return "CBUAE"
    if "dfsa" in text:
        return "DFSA"
    if "difc" in text:
        return "DIFC"
    if "adgm" in text or "fsra" in text:
        return "ADGM/FSRA"
    if "fiu" in text or "financial-intelligence" in text:
        return "UAE FIU"
    if "eocn" in text or "terrorism" in text or "sanction" in text:
        return "EOCN/TFS"
    if "sca" in text or "securities" in text:
        return "SCA"
    if "mof" in text or "ministry-of-finance" in text or "tax" in text or "fta" in text:
        return "MoF/FTA"
    if "ministry-of-economy" in text or "moe" in text or "dnfbp" in text:
        return "MoE/DNFBP"
    if "legislation" in text or "gazette" in text or "moj" in text:
        return "MoJ/Gazette"
    return "Other"


def _company_use_case(source_id: str, source: dict[str, Any]) -> str:
    family = _source_family(source_id, source)
    return {
        "VARA": "UAE VASPs and crypto compliance teams",
        "CBUAE": "banks, payment firms, fintech, and PSP compliance teams",
        "DFSA": "DFSA-authorised firms and DIFC compliance teams",
        "DIFC": "DIFC entities and data/legal operations teams",
        "ADGM/FSRA": "ADGM/FSRA-regulated firms",
        "UAE FIU": "MLROs and AML/CFT teams",
        "EOCN/TFS": "sanctions, AML, and terrorist financing control teams",
        "SCA": "securities, capital markets, and AML/CFT teams",
        "MoF/FTA": "tax, finance, and corporate tax teams",
        "MoE/DNFBP": "DNFBP, AML, and business compliance teams",
        "MoJ/Gazette": "legal operations and regulatory affairs teams",
    }.get(family, "regulated firms evaluating selected official-source monitoring")


def _next_actions(items: list[dict[str, Any]], source_health: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    missing_links = [item for item in items if "missing_canonical_evidence_record_id" in item["blockers"]]
    if missing_links:
        actions.append(f"Link or generate canonical evidence for {len(missing_links)} alert queue entries before brief use.")
    eligible = [item for item in items if item.get("brief_input_eligible") is True]
    if eligible:
        actions.append(f"Founder review can start from {len(eligible)} brief-input eligible alert(s), but customer delivery remains blocked.")
    health_count = int(source_health.get("sources_requiring_operator_review") or 0)
    if health_count:
        actions.append(f"Remediate or document {health_count} repeated-failure source(s) before claiming reliable family monitoring.")
    historical_health_count = int(source_health.get("historical_sources_requiring_operator_review") or 0)
    if historical_health_count:
        actions.append(
            f"Keep {historical_health_count} disabled or historical repeated-failure source(s) disclosed as replaced/remediation history; do not count them as active blockers."
        )
    likely_noise = [item for item in items if item.get("triage_status") == "LIKELY_NOISE"]
    if likely_noise:
        actions.append(f"Parser/source review should clear {len(likely_noise)} likely-noise alert(s) before they enter a brief.")
    actions.append("Generate an internal non-customer brief only after canonical evidence and human review gates pass.")
    return actions


def _alert_id(alert: dict[str, Any]) -> str:
    return str(alert.get("alert_id") or alert.get("_alert_file") or alert.get("run_id") or "").strip()


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
