"""Draft-only actionable alert generation from source diff/proof artifacts."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from app.evidence_records import build_risk_brief_inputs
from app.proof import DISCLAIMER


REVIEW_STATUS = "DRAFT"
SEND_DECISION = "HOLD_FOR_REVIEW"
HUMAN_REVIEW_BANNER = "DRAFT \u2014 HUMAN REVIEW REQUIRED"


def _joined_diff_text(diff_artifact: dict[str, Any]) -> str:
    chunks: list[str] = []
    chunks.extend(diff_artifact.get("added_chunks") or [])
    chunks.extend(diff_artifact.get("removed_chunks") or [])
    for item in diff_artifact.get("changed_chunks") or []:
        chunks.extend(item.get("before") or [])
        chunks.extend(item.get("after") or [])
    return "\n".join(str(chunk) for chunk in chunks if chunk)


def _contains_any(text: str, patterns: list[str]) -> bool:
    haystack = text.lower()
    return any(pattern.lower() in haystack for pattern in patterns)


def _is_legislation_aggregate_change(source_run: dict[str, Any], diff_artifact: dict[str, Any]) -> bool:
    source_name = f"{source_run.get('source_name', '')} {source_run.get('source_id', '')}".lower()
    if "legislation" not in source_name:
        return False
    text = _joined_diff_text(diff_artifact)
    return (
        "تشريع" in text
        and int(diff_artifact.get("changed_count") or 0) <= 1
        and int(diff_artifact.get("added_count") or 0) == 0
        and int(diff_artifact.get("removed_count") or 0) == 0
    )


def classify_change_type(source_run: dict[str, Any], diff_artifact: dict[str, Any]) -> str:
    if _is_legislation_aggregate_change(source_run, diff_artifact):
        return "UNKNOWN"

    source = f"{source_run.get('source_name', '')} {source_run.get('category', '')}".lower()
    text = _joined_diff_text(diff_artifact).lower()
    combined = f"{source}\n{text}"

    if _contains_any(combined, ["consultation", "consultative", "public consultation"]):
        return "CONSULTATION"
    if _contains_any(combined, ["aml", "cft", "suspicious transaction", "financial intelligence", "uae fiu"]):
        return "AML_CFT"
    if _contains_any(combined, ["vat", "corporate tax", "excise tax", "tax procedure", "federal tax"]):
        return "TAX"
    if _contains_any(combined, ["data protection", "personal data", "privacy"]):
        return "DATA_PROTECTION"
    if _contains_any(combined, ["deadline", "effective date", "reporting date", "submit", "filing"]):
        return "DEADLINE_OR_REPORTING"
    if _contains_any(combined, ["license", "licence", "licensed", "authorization", "authorisation", "registration"]):
        return "LICENSING"
    if _contains_any(combined, ["rulebook", "rule book", "custody", "client assets"]):
        return "RULEBOOK_UPDATE"
    if _contains_any(combined, ["circular", "notice", "resolution"]):
        return "CIRCULAR_UPDATE"
    if _contains_any(combined, ["guidance", "guideline", "clarification", "framework"]):
        return "GUIDANCE_UPDATE"
    if _contains_any(combined, ["fine", "penalty", "sanction", "enforcement", "revocation", "suspension"]):
        return "ENFORCEMENT"
    if int(diff_artifact.get("added_count") or 0) > 0:
        return "NEW_PUBLICATION"
    if diff_artifact.get("meaningful_change_detected"):
        return "GENERAL_UPDATE"
    return "UNKNOWN"


def classify_risk(
    source_run: dict[str, Any],
    diff_artifact: dict[str, Any],
    proof_block: dict[str, Any],
    change_type: str,
) -> tuple[str, str, str]:
    if (
        _is_legislation_aggregate_change(source_run, diff_artifact)
        or diff_artifact.get("diff_quality") in {"LIMITED", "INCOMPLETE"}
        or proof_block.get("proof_quality") == "INCOMPLETE"
        or change_type == "UNKNOWN"
    ):
        return (
            "REVIEW",
            "Diff/proof quality or source structure requires manual review before any customer dispatch.",
            "LOW",
        )

    text = _joined_diff_text(diff_artifact).lower()
    obligation = _contains_any(text, ["must", "shall", "required to", "obliged", "mandatory", "يلتزم", "يجب"])
    urgency = _contains_any(text, ["deadline", "effective date", "reporting date", "penalty", "fine", "sanction"])
    licensing = _contains_any(text, ["license", "licence", "authorization", "capital requirement", "custody", "client assets"])
    aml = _contains_any(text, ["aml", "cft", "suspicious transaction", "reporting obligation"])

    if obligation and (urgency or licensing or aml):
        return (
            "HIGH",
            "Changed text contains obligation language plus deadline, licensing, penalty, custody, or AML/CFT signals.",
            "MEDIUM",
        )
    if change_type in {"AML_CFT", "DEADLINE_OR_REPORTING", "LICENSING", "RULEBOOK_UPDATE", "CIRCULAR_UPDATE"}:
        return (
            "MEDIUM",
            "Relevant regulatory-change signals are present, but urgency or binding obligation requires human confirmation.",
            "MEDIUM",
        )
    if change_type in {"CONSULTATION", "GUIDANCE_UPDATE", "TAX", "DATA_PROTECTION", "GENERAL_UPDATE"}:
        return (
            "MEDIUM",
            "The draft indicates a regulatory update or guidance change that should be reviewed for applicability.",
            "MEDIUM",
        )
    return ("LOW", "No clear obligation, deadline, penalty, or licensing signal was detected.", "MEDIUM")


def affected_entities_for(source_run: dict[str, Any], change_type: str) -> str:
    source = f"{source_run.get('source_name', '')} {source_run.get('source_id', '')}".lower()
    if "vara" in source:
        return "Licensed VASPs, crypto exchanges, custody providers, compliance teams."
    if "central bank" in source or "cbuae" in source:
        return "Payment service providers, stored value providers, banks, compliance teams."
    if "dfsa" in source or "difc" in source:
        return "DIFC-regulated firms, compliance officers, legal teams."
    if "adgm" in source or "fsra" in source:
        return "ADGM-regulated firms, FSRA-regulated entities, compliance officers."
    if "fiu" in source or change_type == "AML_CFT":
        return "AML/CFT compliance teams, MLROs, regulated financial and VASP firms."
    if "finance" in source or change_type == "TAX":
        return "Finance, tax, legal, and compliance teams monitoring federal fiscal obligations."
    return "Potentially affected regulated firms; manual classification required."


def recommended_action_for(source_run: dict[str, Any], change_type: str, risk_level: str) -> str:
    source = f"{source_run.get('source_name', '')} {source_run.get('source_id', '')}".lower()
    if risk_level == "REVIEW":
        return "Manual compliance/legal review required before client dispatch."
    if "vara" in source:
        return "Review changed sections against licensing, custody, AML/CFT, and internal policy controls."
    if "central bank" in source or "cbuae" in source:
        return "Review payment service policies, reporting procedures, and licensing obligations."
    if "dfsa" in source or "difc" in source:
        return "Review DFSA rulebook or DIFC legal framework changes against regulated activities."
    if "adgm" in source or "fsra" in source:
        return "Review FSRA notices and ADGM framework changes against regulated activities."
    if change_type == "AML_CFT":
        return "Review AML/CFT procedures, suspicious transaction reporting controls, and escalation playbooks."
    return "Manual compliance/legal review required before client dispatch."


def build_alert_draft(
    source_run: dict[str, Any],
    diff_artifact: dict[str, Any],
    proof_block: dict[str, Any],
) -> dict[str, Any]:
    change_type = classify_change_type(source_run, diff_artifact)
    risk_level, risk_rationale, confidence = classify_risk(source_run, diff_artifact, proof_block, change_type)
    limitations = []
    for note in [
        source_run.get("limitations_notes"),
        proof_block.get("limitations_notes"),
        "; ".join(diff_artifact.get("limitations") or []),
    ]:
        if note and note not in limitations:
            limitations.append(note)
    if _is_legislation_aggregate_change(source_run, diff_artifact):
        limitations.append(
            "UAE Legislation Portal diff appears to be a broad homepage aggregate-count change; adapter review required."
        )
        risk_level = "REVIEW"
        confidence = "LOW"

    run_id = str(source_run.get("run_id") or source_run.get("timestamp_utc") or "")
    seed = f"{source_run.get('source_id')}|{run_id}|{proof_block.get('normalized_hash')}"
    alert_id = "draft-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]

    what_changed = diff_artifact.get("diff_summary") or "Source change detected; diff summary unavailable."
    return {
        "alert_id": alert_id,
        "review_status": REVIEW_STATUS,
        "send_decision": SEND_DECISION,
        "market": source_run.get("market") or source_run.get("jurisdiction"),
        "source_id": source_run.get("source_id"),
        "source_name": source_run.get("source_name"),
        "source_url": source_run.get("official_url") or proof_block.get("official_url"),
        "checked_at_utc": source_run.get("timestamp_utc") or proof_block.get("checked_at_utc"),
        "change_status": source_run.get("change_status"),
        "change_type": change_type,
        "risk_level": risk_level,
        "risk_rationale": risk_rationale,
        "what_changed": what_changed,
        "added_chunks": diff_artifact.get("added_chunks") or [],
        "removed_chunks": diff_artifact.get("removed_chunks") or [],
        "changed_chunks": diff_artifact.get("changed_chunks") or [],
        "affected_entities": affected_entities_for(source_run, change_type),
        "why_it_matters": _why_it_matters(change_type, risk_level),
        "recommended_action": (
            "Source-specific adapter review required before customer dispatch."
            if _is_legislation_aggregate_change(source_run, diff_artifact)
            else recommended_action_for(source_run, change_type, risk_level)
        ),
        "confidence": confidence,
        "limitations": limitations,
        "proof_block": proof_block,
        "not_legal_advice_disclaimer": DISCLAIMER,
    }


def build_evidence_backed_brief_draft(
    evidence_record_id_or_path: str,
    *,
    brief_fields: dict[str, Any],
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Build a non-delivery brief draft from approved canonical evidence only."""

    gate = build_risk_brief_inputs(evidence_record_id_or_path, base_dir=base_dir)
    if not gate.get("eligible"):
        raise ValueError(f"Evidence-backed brief draft blocked: {gate.get('blocked_reason')}")

    required = ("executive_summary", "business_action_required", "specific_obligation", "risk_level", "confidence")
    missing = [key for key in required if not str(brief_fields.get(key) or "").strip()]
    if missing:
        raise ValueError("Evidence-backed brief draft missing required field(s): " + ", ".join(missing))

    from app.weekly_brief import legal_scan_brief

    legal_flags = legal_scan_brief(brief_fields)
    if legal_flags:
        raise ValueError("Evidence-backed brief draft blocked by legal scan: " + "; ".join(legal_flags))

    evidence_record_id = str(gate.get("evidence_record_id") or "").strip()
    source_id = str(gate.get("source_id") or "").strip()
    run_id = str(gate.get("run_id") or "").strip()
    seed = f"{evidence_record_id}|{source_id}|{run_id}"
    draft_id = "brief-draft-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]

    return {
        "brief_draft_id": draft_id,
        "status": "DRAFT",
        "customer_delivery": False,
        "delivery_approved": False,
        "delivery_blocked_reason": "Brief draft is not customer delivery; explicit delivery approval required.",
        "evidence_record_id": evidence_record_id,
        "evidence_record_path": gate.get("evidence_record_path"),
        "source_id": source_id,
        "source_name": gate.get("source_name"),
        "official_url": gate.get("official_url"),
        "run_id": run_id,
        "run_status": gate.get("run_status"),
        "run_timestamp": gate.get("run_timestamp"),
        "current_hash": gate.get("current_hash"),
        "previous_hash": gate.get("previous_hash"),
        "diff_path": gate.get("diff_path"),
        "review_status": gate.get("review_status"),
        "human_review_required": gate.get("human_review_required"),
        "executive_summary": str(brief_fields.get("executive_summary") or "").strip(),
        "business_action_required": str(brief_fields.get("business_action_required") or "").strip(),
        "specific_obligation": str(brief_fields.get("specific_obligation") or "").strip(),
        "risk_level": str(brief_fields.get("risk_level") or "").strip(),
        "confidence": brief_fields.get("confidence"),
        "licence_scope": str(brief_fields.get("licence_scope") or "").strip(),
        "not_legal_advice_disclaimer": DISCLAIMER,
    }


def _why_it_matters(change_type: str, risk_level: str) -> str:
    if risk_level == "REVIEW":
        return "The source changed, but the diff is not reliable enough for customer dispatch without human review."
    if change_type in {"AML_CFT", "DEADLINE_OR_REPORTING", "LICENSING", "RULEBOOK_UPDATE"}:
        return "The change may affect regulated activities, control obligations, reporting procedures, or licensing posture."
    if change_type in {"CONSULTATION", "GUIDANCE_UPDATE"}:
        return "The update may signal future rule changes or supervisory expectations that teams should track."
    return "The update may be relevant to regulatory monitoring scope and should be checked against the client's profile."


def render_alert_markdown(alert: dict[str, Any]) -> str:
    title = f"{HUMAN_REVIEW_BANNER}: {alert.get('source_name') or 'Source'}"
    lines = [
        f"# {title}",
        "",
        f"- Source: {alert.get('source_name')}",
        f"- URL: {alert.get('source_url')}",
        f"- Checked: {alert.get('checked_at_utc')}",
        f"- Change type: {alert.get('change_type')}",
        f"- Risk level: {alert.get('risk_level')}",
        f"- Confidence: {alert.get('confidence')}",
        f"- Send decision: {alert.get('send_decision')}",
        "",
        "## What Changed",
        alert.get("what_changed") or "",
        "",
    ]
    if alert.get("added_chunks"):
        lines.extend(["## Added Excerpt", "```text", str(alert["added_chunks"][0]), "```", ""])
    if alert.get("removed_chunks"):
        lines.extend(["## Removed Excerpt", "```text", str(alert["removed_chunks"][0]), "```", ""])
    if alert.get("changed_chunks"):
        change = alert["changed_chunks"][0]
        lines.extend([
            "## Changed Excerpt",
            "Before:",
            "```text",
            "\n\n".join(change.get("before") or []),
            "```",
            "After:",
            "```text",
            "\n\n".join(change.get("after") or []),
            "```",
            "",
        ])
    lines.extend([
        "## Who May Be Affected",
        alert.get("affected_entities") or "",
        "",
        "## Why It Matters",
        alert.get("why_it_matters") or "",
        "",
        "## Recommended Action",
        alert.get("recommended_action") or "",
        "",
        "## Proof Summary",
        f"- Official URL: {(alert.get('proof_block') or {}).get('official_url')}",
        f"- Final URL: {(alert.get('proof_block') or {}).get('final_url')}",
        f"- Normalized hash: {(alert.get('proof_block') or {}).get('normalized_hash')}",
        f"- Diff: {(alert.get('proof_block') or {}).get('diff_json_path')}",
        "",
        "## Limitations",
    ])
    if alert.get("limitations"):
        lines.extend(f"- {note}" for note in alert["limitations"])
    else:
        lines.append("- None recorded in the source proof block.")
    lines.extend(["", f"## Disclaimer", alert.get("not_legal_advice_disclaimer") or DISCLAIMER, ""])
    return "\n".join(lines)


def write_alert_artifacts(alert: dict[str, Any], snapshot_dir: Path) -> dict[str, str]:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    json_path = snapshot_dir / "alert_draft.json"
    md_path = snapshot_dir / "alert_draft.md"
    json_path.write_text(json.dumps(alert, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_alert_markdown(alert), encoding="utf-8")
    alert["alert_draft_json_path"] = _rel_from_cwd(json_path)
    alert["alert_draft_md_path"] = _rel_from_cwd(md_path)
    json_path.write_text(json.dumps(alert, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "alert_draft_json_path": alert["alert_draft_json_path"],
        "alert_draft_md_path": alert["alert_draft_md_path"],
    }


def snapshot_dir_from_proof(proof_block: dict[str, Any], base_dir: Path) -> Path | None:
    for key in ("snapshot_normalized_path", "snapshot_raw_path"):
        value = proof_block.get(key)
        if not value:
            continue
        path = Path(value)
        if not path.is_absolute():
            path = base_dir / path
        return path.parent
    return None


def load_json_artifact(path_value: str | None, base_dir: Path) -> dict[str, Any]:
    if not path_value:
        return {}
    path = Path(path_value)
    if not path.is_absolute():
        path = base_dir / path
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _rel_from_cwd(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)
