"""Internal non-customer monitoring-to-brief cycle proof.

This module proves the gated path without approving customer delivery:
source run -> canonical evidence -> review -> linked alert -> brief draft ->
legal scan -> delivery blocked.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.alert_drafts import build_evidence_backed_brief_draft
from app.evidence_records import (
    build_risk_brief_inputs,
    latest_canonical_evidence_review,
)
from app.verified_monitoring_digest import build_verified_monitoring_digest
from app.weekly_brief import legal_scan_brief


_BASE_DIR = Path(__file__).parent.parent
_REPORT_JSON = Path("reports") / "internal_non_customer_brief_latest.json"
_REPORT_MD = Path("reports") / "internal_non_customer_brief_latest.md"
_HEADER = "INTERNAL SAMPLE / NOT CUSTOMER DELIVERY"
# SF-5: derive from the ONE canonical product ban list (app.legal_safety) plus
# internal-brief-specific over-promises, so the canonical phrases are never
# forked into a divergent local copy.
from app.legal_safety import FORBIDDEN_PHRASES as _CANONICAL_FORBIDDEN

_INTERNAL_EXTRA_CLAIMS = (
    "complete uae coverage",
    "complete family coverage",
    "regulator certification",
    "perfect parsing",
    "all-source coverage",
)
_UNSAFE_POSITIVE_CLAIMS = tuple(
    dict.fromkeys([*_CANONICAL_FORBIDDEN, *_INTERNAL_EXTRA_CLAIMS])
)


class InternalBriefCycleError(ValueError):
    """Raised when the internal gated cycle cannot be proven."""


def build_internal_non_customer_brief_cycle(
    *,
    evidence_record_id: str | None = None,
    base_dir: Path | None = None,
    brief_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one internal, non-customer brief cycle from a linked alert."""

    root = Path(base_dir) if base_dir is not None else _BASE_DIR
    alert = _select_linked_alert(root, evidence_record_id=evidence_record_id)
    record_id = str(alert.get("evidence_record_id") or "").strip()
    if not record_id:
        raise InternalBriefCycleError("Linked alert is missing evidence_record_id.")
    if alert.get("delivery_approved") is True:
        raise InternalBriefCycleError("Linked alert already has delivery_approved=true; refusing internal sample.")

    gate = build_risk_brief_inputs(record_id, base_dir=root)
    if not gate.get("eligible"):
        raise InternalBriefCycleError(f"Canonical evidence gate blocked cycle: {gate.get('blocked_reason')}")

    latest_review = latest_canonical_evidence_review(record_id, base_dir=root)
    if gate.get("human_review_required") and not latest_review and gate.get("review_status") != "not_required":
        raise InternalBriefCycleError("Human-review-required evidence lacks an external review record.")
    if latest_review and latest_review.get("customer_delivery_approved") is True:
        raise InternalBriefCycleError("Canonical review unexpectedly approves customer delivery.")

    digest_item = _digest_item_for_alert(root, alert)
    fields = brief_fields or _default_brief_fields(alert, gate, digest_item)
    legal_flags = legal_scan_brief(fields)
    if legal_flags:
        raise InternalBriefCycleError("Legal scan blocked internal brief fields: " + "; ".join(legal_flags))

    brief = build_evidence_backed_brief_draft(record_id, brief_fields=fields, base_dir=root)
    if brief.get("customer_delivery") is not False or brief.get("delivery_approved") is not False:
        raise InternalBriefCycleError("Evidence-backed brief draft must keep customer delivery blocked.")

    report = _report_payload(
        alert=alert,
        gate=gate,
        latest_review=latest_review,
        digest_item=digest_item,
        brief=brief,
        legal_flags=legal_flags,
    )
    validation = validate_internal_non_customer_brief_cycle(report, base_dir=root)
    if not validation["valid"]:
        raise InternalBriefCycleError("; ".join(validation["errors"]))
    return report


def write_internal_non_customer_brief_cycle(
    report: dict[str, Any],
    *,
    base_dir: Path | None = None,
) -> dict[str, str]:
    """Write JSON and Markdown artifacts for the internal sample."""

    root = Path(base_dir) if base_dir is not None else _BASE_DIR
    json_path = root / _REPORT_JSON
    md_path = root / _REPORT_MD
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_internal_non_customer_brief_markdown(report), encoding="utf-8")
    return {
        "json_path": _relative_or_absolute(json_path, root),
        "markdown_path": _relative_or_absolute(md_path, root),
    }


def load_internal_non_customer_brief_cycle(
    *,
    base_dir: Path | None = None,
    path: Path | None = None,
) -> dict[str, Any]:
    root = Path(base_dir) if base_dir is not None else _BASE_DIR
    report_path = path or (root / _REPORT_JSON)
    if not report_path.exists():
        raise InternalBriefCycleError(f"Internal non-customer brief report not found: {_relative_or_absolute(report_path, root)}")
    try:
        parsed = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InternalBriefCycleError(f"Internal brief report is invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise InternalBriefCycleError("Internal brief report must be a JSON object.")
    return parsed


def validate_internal_non_customer_brief_cycle(
    report: dict[str, Any],
    *,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Validate the internal sample without approving delivery."""

    root = Path(base_dir) if base_dir is not None else _BASE_DIR
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(report, dict):
        return {"valid": False, "errors": ["Report must be a JSON object."], "warnings": []}
    if report.get("header") != _HEADER:
        errors.append(f"header must be {_HEADER!r}.")
    if report.get("internal_sample") is not True:
        errors.append("internal_sample must be true.")
    if report.get("customer_delivery") is not False:
        errors.append("customer_delivery must be false.")
    if report.get("delivery_approved") is not False:
        errors.append("delivery_approved must be false.")

    evidence = report.get("evidence") if isinstance(report.get("evidence"), dict) else {}
    record_id = str(evidence.get("evidence_record_id") or "").strip()
    if not record_id:
        errors.append("evidence.evidence_record_id is required.")
    else:
        gate = build_risk_brief_inputs(record_id, base_dir=root)
        if not gate.get("eligible"):
            errors.append(f"evidence gate no longer eligible: {gate.get('blocked_reason')}")
        elif str(gate.get("external_review_id") or "") != str(evidence.get("external_review_id") or ""):
            errors.append("evidence.external_review_id no longer matches current evidence gate.")

    review = report.get("review") if isinstance(report.get("review"), dict) else {}
    if not review.get("review_id"):
        errors.append("review.review_id is required.")
    if review.get("customer_delivery_approved") is not False:
        errors.append("review.customer_delivery_approved must be false.")
    if str(review.get("reviewer") or "").lower().startswith("test"):
        warnings.append("latest review appears to be audit/test context, not founder approval.")

    legal_scan = report.get("legal_scan") if isinstance(report.get("legal_scan"), dict) else {}
    if legal_scan.get("passed") is not True:
        errors.append("legal_scan.passed must be true.")
    if legal_scan.get("flags") not in ([], None):
        errors.append("legal_scan.flags must be empty.")

    brief = report.get("brief_draft") if isinstance(report.get("brief_draft"), dict) else {}
    if brief.get("customer_delivery") is not False:
        errors.append("brief_draft.customer_delivery must be false.")
    if brief.get("delivery_approved") is not False:
        errors.append("brief_draft.delivery_approved must be false.")
    scan_fields = {
        "executive_summary": brief.get("executive_summary") or "",
        "business_action_required": brief.get("business_action_required") or "",
        "specific_obligation": brief.get("specific_obligation") or "",
    }
    flags = legal_scan_brief(scan_fields)
    if flags:
        errors.extend(flags)
    claim_text = "\n".join(str(value or "") for value in scan_fields.values()).lower()
    for phrase in _UNSAFE_POSITIVE_CLAIMS:
        if phrase in claim_text:
            errors.append(f"unsafe positive claim in internal brief fields: {phrase}")

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def render_internal_non_customer_brief_markdown(report: dict[str, Any]) -> str:
    evidence = report.get("evidence") if isinstance(report.get("evidence"), dict) else {}
    review = report.get("review") if isinstance(report.get("review"), dict) else {}
    alert = report.get("alert") if isinstance(report.get("alert"), dict) else {}
    brief = report.get("brief_draft") if isinstance(report.get("brief_draft"), dict) else {}
    legal_scan = report.get("legal_scan") if isinstance(report.get("legal_scan"), dict) else {}
    chain = report.get("chain") if isinstance(report.get("chain"), list) else []
    warnings = report.get("warnings") if isinstance(report.get("warnings"), list) else []

    lines = [
        f"# {_HEADER}",
        "",
        f"Generated: {report.get('generated_at_utc')}",
        "",
        "**Boundary:** This is an internal engineering proof of the gated path. It is not a customer brief.",
        "",
        "## Gate Status",
        "",
        f"- Customer delivery: {str(report.get('customer_delivery')).lower()}",
        f"- Delivery approved: {str(report.get('delivery_approved')).lower()}",
        f"- Legal scan passed: {str(legal_scan.get('passed')).lower()}",
        f"- Evidence review decision: {review.get('decision') or '<missing>'}",
        f"- Evidence review ID: {review.get('review_id') or '<missing>'}",
        "",
        "## Chain",
        "",
    ]
    lines.extend(f"- {step}" for step in chain)
    lines.extend(
        [
            "",
            "## Evidence",
            "",
            f"- Source ID: {evidence.get('source_id')}",
            f"- Run ID: {evidence.get('run_id')}",
            f"- Evidence record ID: {evidence.get('evidence_record_id')}",
            f"- Evidence record path: {evidence.get('evidence_record_path')}",
            f"- Current hash: {evidence.get('current_hash')}",
            f"- External review ID: {evidence.get('external_review_id')}",
            "",
            "## Linked Alert",
            "",
            f"- Alert file: {alert.get('alert_file')}",
            f"- Alert status: {alert.get('status')}",
            f"- Evidence linked: {alert.get('evidence_record_id')}",
            f"- Delivery approved: {str(alert.get('delivery_approved')).lower()}",
            "",
            "## Draft Summary",
            "",
            f"- Risk level: {brief.get('risk_level')}",
            f"- Confidence: {brief.get('confidence')}",
            f"- Licence scope: {brief.get('licence_scope')}",
            "",
            "### Executive Summary",
            "",
            str(brief.get("executive_summary") or ""),
            "",
            "### Business Action Required",
            "",
            str(brief.get("business_action_required") or ""),
            "",
            "### Specific Obligation Boundary",
            "",
            str(brief.get("specific_obligation") or ""),
            "",
        ]
    )
    if warnings:
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)
        lines.append("")
    lines.extend(
        [
            "## Disclaimer",
            "",
            "Monitoring intelligence only. Not legal advice. Not customer delivery. Source limitations and evidence records must be reviewed before any external use.",
            "",
        ]
    )
    return "\n".join(lines)


def _select_linked_alert(root: Path, *, evidence_record_id: str | None) -> dict[str, Any]:
    queue_dir = root / "data" / "alert_queue"
    if not queue_dir.exists():
        raise InternalBriefCycleError("Alert queue directory does not exist.")
    matches: list[dict[str, Any]] = []
    for path in sorted(queue_dir.glob("*.json")):
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(parsed, dict):
            continue
        record_id = str(parsed.get("evidence_record_id") or "").strip()
        if not record_id:
            continue
        if evidence_record_id and record_id != evidence_record_id:
            continue
        parsed["_alert_file"] = _relative_or_absolute(path, root)
        matches.append(parsed)
    if not matches:
        wanted = f" for {evidence_record_id}" if evidence_record_id else ""
        raise InternalBriefCycleError(f"No linked alert found{wanted}.")
    if len(matches) > 1 and evidence_record_id:
        raise InternalBriefCycleError(f"Multiple linked alerts found for {evidence_record_id}.")
    return matches[0]


def _digest_item_for_alert(root: Path, alert: dict[str, Any]) -> dict[str, Any]:
    digest = build_verified_monitoring_digest(base_dir=root)
    alert_file = str(alert.get("_alert_file") or "")
    for item in digest.get("items", []):
        if item.get("alert_id") == alert_file:
            return item
        if item.get("source_id") == alert.get("source_id") and item.get("run_id") == alert.get("run_id"):
            return item
    return {}


def _default_brief_fields(alert: dict[str, Any], gate: dict[str, Any], digest_item: dict[str, Any]) -> dict[str, Any]:
    source_name = gate.get("source_name") or alert.get("source_id") or "official source"
    source_family = digest_item.get("source_family") or "selected official source"
    return {
        "executive_summary": (
            f"Internal sample only: StatuteProof detected a saved change on {source_name}. "
            "The change is evidence-linked and requires human compliance review before any external use."
        ),
        "business_action_required": (
            f"Review the {source_family} source change against internal AML/CFT and regulatory monitoring controls. "
            "Do not send to a customer until founder review, legal scan, and delivery approval are complete."
        ),
        "specific_obligation": (
            "No customer-specific obligation is asserted by this internal sample. "
            "The official-source change must be reviewed by qualified compliance or legal personnel before reliance."
        ),
        "risk_level": "REVIEW",
        "confidence": "LOW",
        "licence_scope": "Internal SCA AML/CFT monitoring sample; licence applicability requires human review.",
    }


def _report_payload(
    *,
    alert: dict[str, Any],
    gate: dict[str, Any],
    latest_review: dict[str, Any] | None,
    digest_item: dict[str, Any],
    brief: dict[str, Any],
    legal_flags: list[str],
) -> dict[str, Any]:
    review = latest_review or {}
    review_context = _review_context(review)
    warnings = []
    if review_context == "audit_or_test_review":
        warnings.append("Latest canonical evidence review appears to be audit/test context, not founder approval.")
    report_id = "internal-cycle-" + hashlib.sha256(
        f"{gate.get('evidence_record_id')}|{gate.get('run_id')}|{review.get('review_id')}".encode("utf-8")
    ).hexdigest()[:16]
    return {
        "schema_version": "1.0",
        "report_id": report_id,
        "header": _HEADER,
        "generated_at_utc": _utc_now(),
        "internal_sample": True,
        "customer_delivery": False,
        "delivery_approved": False,
        "delivery_blocked_reason": "Internal sample only; customer delivery requires explicit separate approval.",
        "gated_cycle_complete": True,
        "chain": [
            "source run verified from saved source_runs.jsonl metadata",
            "canonical evidence gate returned eligible",
            "append-only evidence review checked and customer_delivery_approved=false",
            "alert queue entry is linked to evidence_record_id",
            "risk/brief draft built from approved canonical evidence",
            "legal scan passed",
            "delivery remains blocked",
        ],
        "alert": {
            "alert_file": alert.get("_alert_file") or "",
            "source_id": alert.get("source_id") or "",
            "run_id": alert.get("run_id") or "",
            "status": alert.get("status") or "",
            "evidence_record_id": alert.get("evidence_record_id") or "",
            "human_reviewed": bool(alert.get("human_reviewed") is True),
            "delivery_approved": bool(alert.get("delivery_approved") is True),
            "diff_json_path": alert.get("diff_json_path") or "",
            "proof_block_path": alert.get("proof_block_path") or "",
        },
        "evidence": {
            "evidence_record_id": gate.get("evidence_record_id") or "",
            "evidence_record_path": gate.get("evidence_record_path") or "",
            "source_id": gate.get("source_id") or "",
            "source_name": gate.get("source_name") or "",
            "official_url": gate.get("official_url") or "",
            "run_id": gate.get("run_id") or "",
            "run_status": gate.get("run_status") or "",
            "run_timestamp": gate.get("run_timestamp") or "",
            "current_hash": gate.get("current_hash") or "",
            "previous_hash": gate.get("previous_hash") or "",
            "diff_path": gate.get("diff_path") or "",
            "review_status": gate.get("review_status") or "",
            "external_review_id": gate.get("external_review_id") or "",
        },
        "review": {
            "review_id": review.get("review_id") or gate.get("external_review_id") or "",
            "decision": review.get("decision") or gate.get("review_status") or "",
            "reviewer": review.get("reviewer") or "",
            "reviewed_at": review.get("reviewed_at") or "",
            "note": review.get("note") or gate.get("review_reason") or "",
            "review_context": review_context,
            "customer_delivery_approved": bool(review.get("customer_delivery_approved") is True),
        },
        "legal_scan": {
            "passed": not legal_flags,
            "flags": legal_flags,
        },
        "digest_triage": {
            "triage_status": digest_item.get("triage_status") or "",
            "noise_indicators": digest_item.get("noise_indicators") or [],
            "blockers": digest_item.get("blockers") or [],
            "review_reasons": digest_item.get("review_reasons") or [],
        },
        "brief_draft": brief,
        "warnings": warnings,
    }


def _review_context(review: dict[str, Any]) -> str:
    reviewer = str(review.get("reviewer") or "").lower()
    note = str(review.get("note") or "").lower()
    if "test" in reviewer or "audit" in note or "audit" in reviewer:
        return "audit_or_test_review"
    if reviewer:
        return "operator_review"
    return "record_status_review"


def _relative_or_absolute(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
