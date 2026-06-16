"""Audit-pack export for evidence-backed review records."""

from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.evidence_assessment import LEGAL_DISCLAIMER


_BASE_DIR = Path(__file__).parent.parent


def render_audit_pack_markdown(
    evidence_record: dict[str, Any],
    *,
    assessment: dict[str, Any] | None = None,
    demo: bool = False,
) -> str:
    source_name = evidence_record.get("source_name") or evidence_record.get("source_id") or "Official source"
    official_url = evidence_record.get("official_url") or evidence_record.get("final_url") or "not recorded"
    timestamp = evidence_record.get("timestamp_utc") or evidence_record.get("run_at") or "not recorded"
    normalized_hash = evidence_record.get("normalized_hash") or evidence_record.get("content_hash") or "not recorded"
    proof_path = evidence_record.get("proof_block_path") or "not recorded"
    source_health = (
        (assessment or {}).get("source_health_status")
        or _source_health_status(evidence_record)
    )
    lines = [
        "# StatuteProof Evidence Audit Pack",
        "",
    ]
    if demo:
        lines.extend([
            "**SAMPLE / DEMO - NOT CUSTOMER DATA**",
            "",
        ])
    lines.extend([
        "## Evidence Record",
        f"- Source name: {source_name}",
        f"- Source ID: {evidence_record.get('source_id') or 'not recorded'}",
        f"- Official URL: {official_url}",
        f"- Monitoring period / checked at: {timestamp}",
        f"- Change status: {evidence_record.get('change_status') or 'not recorded'}",
        f"- Source health status: {source_health}",
        f"- Extraction quality: {evidence_record.get('extraction_quality') or 'not recorded'}",
        f"- Proof path: {proof_path}",
        f"- Diff path: {evidence_record.get('diff_json_path') or evidence_record.get('diff_md_path') or 'not recorded'}",
        f"- Normalized hash: {normalized_hash}",
        f"- Raw hash: {evidence_record.get('raw_hash') or 'not recorded'}",
        "",
        "## Human Review",
    ])
    if assessment:
        lines.extend([
            f"- Assessment ID: {assessment.get('assessment_id')}",
            f"- Review status: {assessment.get('assessment_status')}",
            f"- Impact level: {assessment.get('impact_level')}",
            f"- Reviewer: {assessment.get('reviewer_name') or assessment.get('reviewer_user_id') or 'Reviewer'}",
            f"- Reviewed at: {assessment.get('reviewed_at')}",
            f"- Internal note: {assessment.get('internal_note')}",
            f"- Next action: {assessment.get('next_action') or 'not recorded'}",
        ])
    else:
        lines.append("- No Acknowledge & Assess record is linked to this evidence record yet.")
    lines.extend([
        "",
        "## Legal Boundary",
        LEGAL_DISCLAIMER,
        "This export supports internal compliance review. It does not determine legal obligations, certify compliance, or replace qualified legal/compliance advice.",
        "",
    ])
    return "\n".join(lines)


def render_audit_pack_html(markdown: str) -> str:
    body: list[str] = []
    in_list = False
    for raw in markdown.splitlines():
        line = raw.rstrip()
        if line.startswith("# "):
            if in_list:
                body.append("</ul>")
                in_list = False
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            if in_list:
                body.append("</ul>")
                in_list = False
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("- "):
            if not in_list:
                body.append("<ul>")
                in_list = True
            body.append(f"<li>{_inline(line[2:])}</li>")
        elif line:
            if in_list:
                body.append("</ul>")
                in_list = False
            body.append(f"<p>{_inline(line)}</p>")
    if in_list:
        body.append("</ul>")
    return (
        "<!doctype html>\n<html><head><meta charset=\"utf-8\"><title>StatuteProof Evidence Audit Pack</title>"
        "<style>body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.55;max-width:760px;margin:40px auto;padding:0 24px;color:#07111f}h1{border-bottom:3px solid #16d9f5;padding-bottom:12px}li{margin:5px 0}</style>"
        "</head><body>\n"
        + "\n".join(body)
        + "\n</body></html>\n"
    )


def write_audit_pack(
    evidence_record: dict[str, Any],
    *,
    assessment: dict[str, Any] | None = None,
    base_dir: Path | None = None,
    demo: bool = False,
) -> dict[str, str]:
    root = base_dir or _BASE_DIR
    out_dir = root / "reports" / "audit_packs"
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = _safe_stem(
        str((assessment or {}).get("assessment_id") or evidence_record.get("run_id") or "audit-pack")
    )
    markdown = render_audit_pack_markdown(evidence_record, assessment=assessment, demo=demo)
    html_doc = render_audit_pack_html(markdown)
    md_path = out_dir / f"{stem}.md"
    html_path = out_dir / f"{stem}.html"
    md_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(html_doc, encoding="utf-8")
    metadata_path = out_dir / f"{stem}.json"
    metadata_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "run_id": evidence_record.get("run_id"),
                "assessment_id": (assessment or {}).get("assessment_id"),
                "demo": demo,
                "legal_disclaimer": LEGAL_DISCLAIMER,
                "formats": ["md", "html"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return {
        "md_path": _rel(md_path, root),
        "html_path": _rel(html_path, root),
        "metadata_path": _rel(metadata_path, root),
    }


def _source_health_status(record: dict[str, Any]) -> str:
    if record.get("change_status") in {"FAILED", "QUALITY_DROP"}:
        return str(record.get("change_status"))
    if str(record.get("access_status") or "").lower() in {"failed", "restricted"}:
        return str(record.get("access_status")).upper()
    return "MONITOR_OK"


def _safe_stem(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", value).strip("-")[:120] or "audit-pack"


def _rel(path: Path, base_dir: Path) -> str:
    try:
        return str(path.resolve().relative_to(base_dir.resolve()))
    except ValueError:
        return str(path)


def _inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    return re.sub(
        r"(https?://[^\s<]+)",
        lambda match: f'<a href="{match.group(1)}">{match.group(1)}</a>',
        escaped,
    )

