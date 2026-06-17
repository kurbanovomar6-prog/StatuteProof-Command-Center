"""Audit-pack export for evidence-backed review records.

Includes period-based Audit Vault: bundles all evidence packs for a date range
and set of source IDs into a single ZIP archive with a manifest.json.
"""

from __future__ import annotations

import html
import json
import logging
import re
import sqlite3
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from app.config import DB_PATH
from app.evidence_assessment import LEGAL_DISCLAIMER

logger = logging.getLogger(__name__)


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
    include_pdf: bool = False,
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
    pdf_path: Path | None = None
    if include_pdf:
        pdf_path = out_dir / f"{stem}.pdf"
        _render_html_pdf(html_doc, pdf_path)
    metadata_path = out_dir / f"{stem}.json"
    formats = ["md", "html"]
    result = {
        "md_path": _rel(md_path, root),
        "html_path": _rel(html_path, root),
        "metadata_path": _rel(metadata_path, root),
    }
    if pdf_path is not None:
        if not pdf_path.exists() or pdf_path.stat().st_size <= 0:
            raise RuntimeError("PDF export failed because no PDF file was generated.")
        formats.append("pdf")
        result["pdf_path"] = _rel(pdf_path, root)
    metadata = _audit_pack_metadata(
        evidence_record,
        assessment=assessment,
        demo=demo,
        formats=formats,
        result=result,
    )
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return result


def write_audit_pack_pdf(
    evidence_record: dict[str, Any],
    *,
    assessment: dict[str, Any] | None = None,
    base_dir: Path | None = None,
    demo: bool = False,
) -> dict[str, str]:
    """Write Markdown, HTML, metadata, and a real PDF audit pack."""
    return write_audit_pack(
        evidence_record,
        assessment=assessment,
        base_dir=base_dir,
        demo=demo,
        include_pdf=True,
    )


def build_audit_pack_export_response(
    evidence_record: dict[str, Any],
    *,
    assessment: dict[str, Any] | None = None,
    export_format: str = "md_html",
    base_dir: Path | None = None,
    demo: bool = False,
) -> dict[str, Any]:
    requested = str(export_format or "md_html").strip().lower()
    if requested in {"pdf", "application/pdf"}:
        paths = write_audit_pack_pdf(evidence_record, assessment=assessment, base_dir=base_dir, demo=demo)
        return {
            "ok": True,
            "evidence_record_id": evidence_record.get("run_id"),
            "assessment_id": (assessment or {}).get("assessment_id"),
            "export": paths,
            "format": "pdf",
            "pdf_available": True,
            "pdf_path": paths.get("pdf_path"),
            "message": "PDF audit pack exported for internal compliance review.",
            "disclaimer": LEGAL_DISCLAIMER,
        }
    if requested not in {"md_html", "markdown", "html"}:
        raise ValueError("Unsupported audit export format. Use md_html or pdf.")
    paths = write_audit_pack(evidence_record, assessment=assessment, base_dir=base_dir, demo=demo)
    return {
        "ok": True,
        "evidence_record_id": evidence_record.get("run_id"),
        "assessment_id": (assessment or {}).get("assessment_id"),
        "export": paths,
        "format": "md_html",
        "pdf_available": False,
        "message": "Markdown/HTML audit pack exported.",
        "disclaimer": LEGAL_DISCLAIMER,
    }


def validate_date_range(date_from: str, date_to: str) -> tuple[bool, str]:
    """Validate a YYYY-MM-DD date range for the audit vault.

    Rules checked:
    - Both strings must be valid YYYY-MM-DD format.
    - date_from must not be after date_to.
    - Neither date may be in the future.
    - Neither date may be more than 2 years in the past.

    Returns
    -------
    tuple[bool, str]
        (True, "") on success, (False, error_message) on failure.
    """
    try:
        d_from = date.fromisoformat(str(date_from or "").strip())
    except ValueError:
        return False, f"date_from '{date_from}' is not a valid YYYY-MM-DD date."
    try:
        d_to = date.fromisoformat(str(date_to or "").strip())
    except ValueError:
        return False, f"date_to '{date_to}' is not a valid YYYY-MM-DD date."

    today = date.today()
    two_years_ago = date(today.year - 2, today.month, today.day)

    if d_from > d_to:
        return False, "date_from must not be after date_to."
    if d_from > today:
        return False, "date_from must not be in the future."
    if d_to > today:
        return False, "date_to must not be in the future."
    if d_from < two_years_ago:
        return False, "date_from must not be more than 2 years in the past."

    return True, ""


def build_period_audit_vault(
    source_ids: list[str],
    date_from: str,
    date_to: str,
    output_dir: Path | None = None,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Bundle all audit packs for source_ids within a date range into a ZIP archive.

    Parameters
    ----------
    source_ids:
        Non-empty list of source IDs (matched against the ``url`` column via source
        run JSONL files). If empty, returns an error.
    date_from:
        Start of date range, inclusive, YYYY-MM-DD format.
    date_to:
        End of date range, inclusive, YYYY-MM-DD format.
    output_dir:
        Directory for the ZIP archive. Defaults to product/regradar/data/audit_vaults/.
    base_dir:
        Override for the product root (used in tests).

    Returns
    -------
    dict
        {"status": "ok", "vault_path": str, "record_count": int, ...} on success.
        {"status": "empty", ...} when no records match.
        {"status": "error", "message": str} on failure.
        Never raises.
    """
    try:
        root = base_dir or _BASE_DIR

        # Validate inputs
        if not source_ids:
            return {"status": "error", "message": "source_ids must be a non-empty list."}

        valid, err = validate_date_range(date_from, date_to)
        if not valid:
            return {"status": "error", "message": err}

        vault_dir = output_dir or (root / "data" / "audit_vaults")
        vault_dir.mkdir(parents=True, exist_ok=True)

        # Collect run records from source_runs.jsonl for the given sources + date range
        records = _fetch_runs_for_vault(root, source_ids, date_from, date_to)

        if not records:
            return {
                "status": "empty",
                "record_count": 0,
                "message": "No records found for the specified period and sources.",
            }

        # Generate individual audit packs
        manifest: list[dict[str, Any]] = []
        pack_paths: list[Path] = []

        for rec in records:
            try:
                pack_result = write_audit_pack(rec, base_dir=root)
                pack_filename = str(Path(pack_result.get("md_path", "")).name or "")
                manifest.append({
                    "source_id": rec.get("source_id") or "",
                    "run_id": rec.get("run_id") or "",
                    "risk_level": rec.get("risk_level") or "UNKNOWN",
                    "detected_at": rec.get("timestamp_utc") or rec.get("run_at") or "",
                    "pack_filename": pack_filename,
                })
                # Collect all generated files for this pack
                for key in ("md_path", "html_path", "pdf_path", "metadata_path"):
                    rel = pack_result.get(key)
                    if rel:
                        candidate = (root / rel).resolve()
                        if candidate.exists():
                            pack_paths.append(candidate)
            except Exception as exc:
                logger.warning("build_period_audit_vault: skipping record %s: %s", rec.get("run_id"), exc)

        if not manifest:
            return {
                "status": "empty",
                "record_count": 0,
                "message": "No records found for the specified period and sources.",
            }

        # Write manifest.json to a temp location then include in ZIP
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        zip_name = f"audit_vault_{date_from}_{date_to}_{timestamp_str}.zip"
        zip_path = vault_dir / zip_name

        manifest_data = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "date_from": date_from,
            "date_to": date_to,
            "source_ids": sorted(set(source_ids)),
            "record_count": len(manifest),
            "legal_disclaimer": LEGAL_DISCLAIMER,
            "records": manifest,
        }
        manifest_json = json.dumps(manifest_data, ensure_ascii=False, indent=2, sort_keys=True)

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", manifest_json)
            for pack_path in pack_paths:
                arcname = f"packs/{pack_path.name}"
                zf.write(pack_path, arcname=arcname)

        return {
            "status": "ok",
            "vault_path": str(zip_path.resolve()),
            "record_count": len(manifest),
            "source_count": len({m["source_id"] for m in manifest}),
            "date_from": date_from,
            "date_to": date_to,
            "manifest": manifest,
        }

    except Exception as exc:
        logger.error("build_period_audit_vault: unexpected error: %s", exc)
        return {"status": "error", "message": str(exc)}


def _fetch_runs_for_vault(
    root: Path,
    source_ids: list[str],
    date_from: str,
    date_to: str,
) -> list[dict[str, Any]]:
    """Return run records matching source_ids and date range.

    First tries source_runs.jsonl; falls back to documents DB if no JSONL exists.
    """
    wanted_ids = set(str(s).strip() for s in source_ids if s)
    date_to_end = f"{date_to}T23:59:59"

    # Try JSONL source runs first
    runs_path = root / "data" / "source_runs" / "source_runs.jsonl"
    if runs_path.exists():
        matching: list[dict[str, Any]] = []
        for line in runs_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            sid = str(row.get("source_id") or "").strip()
            if sid not in wanted_ids:
                continue
            ts = str(row.get("timestamp_utc") or row.get("run_at") or "")
            if ts and ts >= date_from and ts <= date_to_end:
                matching.append(row)
        if matching:
            return matching

    # Fallback: documents DB (maps url→source for basic lookup)
    if not Path(DB_PATH).exists():
        return []
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT url, risk_level, risk_reason, created_at, content_hash
                FROM documents
                WHERE created_at >= ? AND created_at <= ?
                ORDER BY created_at ASC
                """,
                (date_from, date_to_end),
            ).fetchall()
        except sqlite3.OperationalError:
            return []
        finally:
            conn.close()

        result: list[dict[str, Any]] = []
        for row in rows:
            url = str(row["url"] or "")
            # Include if url contains any of the wanted source_ids
            if any(sid in url for sid in wanted_ids):
                result.append({
                    "run_id": f"db-{row['content_hash'][:12]}",
                    "source_id": url,
                    "official_url": url,
                    "timestamp_utc": row["created_at"],
                    "risk_level": row["risk_level"] or "LOW",
                    "content_hash": row["content_hash"] or "",
                    "change_status": "CHANGED",
                })
        return result
    except Exception as exc:
        logger.warning("_fetch_runs_for_vault DB fallback error: %s", exc)
        return []


def _render_html_pdf(html_doc: str, pdf_path: Path) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - exercised only when dependency is absent
        raise RuntimeError("PDF export requires the Playwright Python package.") from exc

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.set_content(html_doc, wait_until="networkidle")
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin={
                    "top": "18mm",
                    "right": "14mm",
                    "bottom": "18mm",
                    "left": "14mm",
                },
            )
            browser.close()
    except Exception as exc:
        raise RuntimeError("PDF export could not be generated with the local Playwright browser runtime.") from exc


def _audit_pack_metadata(
    evidence_record: dict[str, Any],
    *,
    assessment: dict[str, Any] | None,
    demo: bool,
    formats: list[str],
    result: dict[str, str],
) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_id": evidence_record.get("run_id"),
        "evidence_record_id": evidence_record.get("run_id"),
        "source_id": evidence_record.get("source_id"),
        "source_name": evidence_record.get("source_name") or evidence_record.get("source_id"),
        "official_url": evidence_record.get("official_url") or evidence_record.get("final_url"),
        "proof_path": evidence_record.get("proof_block_path"),
        "diff_path": evidence_record.get("diff_json_path") or evidence_record.get("diff_md_path"),
        "normalized_hash": evidence_record.get("normalized_hash") or evidence_record.get("content_hash"),
        "raw_hash": evidence_record.get("raw_hash"),
        "source_health_status": (assessment or {}).get("source_health_status") or _source_health_status(evidence_record),
        "assessment_id": (assessment or {}).get("assessment_id"),
        "impact_level": (assessment or {}).get("impact_level"),
        "reviewer": (assessment or {}).get("reviewer_name") or (assessment or {}).get("reviewer_user_id"),
        "reviewed_at": (assessment or {}).get("reviewed_at"),
        "demo": demo,
        "legal_disclaimer": LEGAL_DISCLAIMER,
        "formats": formats,
        **{key: value for key, value in result.items() if key.endswith("_path")},
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
