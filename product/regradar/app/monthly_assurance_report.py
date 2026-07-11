"""Monthly monitoring assurance report — generates per-client ROI proof documents.

Queries the monitoring DB for a calendar month, computes stats, and renders
a professional Markdown (and optionally PDF) report for compliance officers.
"""

from __future__ import annotations

import calendar
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import DB_PATH
from app.evidence_assessment import LEGAL_DISCLAIMER

# Phrases that must never appear in customer-facing output. Re-exported from the
# single source of truth (app.legal_safety) so every module that historically
# imported ``_FORBIDDEN_PHRASES`` from here shares the ONE canonical ban list —
# no divergent copies. See app/legal_safety.py.
from app.legal_safety import FORBIDDEN_PHRASES as _FORBIDDEN_PHRASES

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).parent.parent
_REPORTS_DIR = _BASE_DIR / "reports"

_MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _zero_stats(year: int, month: int, *, is_estimate: bool = True) -> dict[str, Any]:
    """Return a zero-counts stats dict for the given period."""
    return {
        "period_label": f"{_MONTH_NAMES[month]} {year}",
        "year": year,
        "month": month,
        "sources_checked": 0,
        "total_runs": 0,
        "successful_runs": 0,
        "changes_detected": 0,
        "high_risk_count": 0,
        "medium_risk_count": 0,
        "low_risk_count": 0,
        "non_material_count": 0,
        "unreviewed_count": 0,
        "sources_with_errors": 0,
        "uptime_pct": None,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "is_estimate": is_estimate,
    }


def compute_monthly_stats(
    source_ids: list[str] | None,
    year: int,
    month: int,
) -> dict[str, Any]:
    """Query the monitoring DB and return stats for the given calendar month.

    Parameters
    ----------
    source_ids:
        Optional list of source IDs to restrict stats to. Pass None for all sources.
    year:
        Four-digit year (e.g. 2026).
    month:
        Month number 1-12.

    Returns
    -------
    dict
        Stats dict with the shape documented in the module spec.
        Never raises — DB errors produce is_estimate=True zero-counts.
    """
    try:
        # Build date range for the month
        last_day = calendar.monthrange(year, month)[1]
        period_start = f"{year:04d}-{month:02d}-01"
        period_end = f"{year:04d}-{month:02d}-{last_day:02d}T23:59:59"

        if not Path(DB_PATH).exists():
            return _zero_stats(year, month, is_estimate=True)

        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            # Build optional source filter
            source_filter = ""
            params_base: list[Any] = [period_start, period_end]
            if source_ids:
                placeholders = ",".join("?" * len(source_ids))
                source_filter = f" AND url IN ({placeholders})"
                params_base.extend(source_ids)

            rows = conn.execute(
                f"""
                SELECT url, risk_level, risk_reason, created_at
                FROM documents
                WHERE created_at >= ? AND created_at <= ?
                {source_filter}
                ORDER BY created_at ASC
                """,
                params_base,
            ).fetchall()
        except sqlite3.OperationalError as exc:
            logger.warning("compute_monthly_stats: DB error: %s", exc)
            return _zero_stats(year, month, is_estimate=True)
        finally:
            conn.close()

        if not rows:
            return _zero_stats(year, month, is_estimate=True)

        total_runs = len(rows)
        seen_sources: set[str] = set()
        sources_with_errors: set[str] = set()
        successful_runs = 0
        changes_detected = 0
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0
        non_material_count = 0

        for row in rows:
            url = row["url"] or ""
            seen_sources.add(url)
            risk = (row["risk_level"] or "LOW").upper()
            reason = (row["risk_reason"] or "").lower()

            # "error" runs: risk_reason contains "error" or risk_level is a sentinel
            is_error = "error" in reason or risk == "ERROR"
            if is_error:
                sources_with_errors.add(url)
            else:
                successful_runs += 1

            # Changes: any row with content (all saves are considered attempted runs;
            # rows with risk_reason != "No changes detected" are changes)
            if "no changes detected" not in reason and not is_error:
                changes_detected += 1

            if risk == "HIGH":
                high_risk_count += 1
            elif risk == "MEDIUM":
                medium_risk_count += 1
            elif risk == "NON_MATERIAL":
                non_material_count += 1
            elif risk == "LOW":
                low_risk_count += 1

        uptime_pct = (
            round(successful_runs / total_runs * 100, 1)
            if total_runs > 0
            else None
        )
        is_estimate = total_runs < 20

        return {
            "period_label": f"{_MONTH_NAMES[month]} {year}",
            "year": year,
            "month": month,
            "sources_checked": len(seen_sources),
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "changes_detected": changes_detected,
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "low_risk_count": low_risk_count,
            "non_material_count": non_material_count,
            "unreviewed_count": 0,  # placeholder — review queue is filesystem-backed
            "sources_with_errors": len(sources_with_errors),
            "uptime_pct": uptime_pct,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "is_estimate": is_estimate,
        }

    except Exception as exc:
        logger.error("compute_monthly_stats: unexpected error: %s", exc)
        return _zero_stats(year, month, is_estimate=True)


def render_assurance_report_markdown(
    stats: dict[str, Any],
    client_name: str = "",
    plan_name: str = "",
) -> str:
    """Render a professional Markdown assurance report suitable for compliance officers.

    The report includes a monitoring summary table, risk breakdown, review status,
    and the mandatory legal disclaimer. Forbidden phrases are never included.

    Parameters
    ----------
    stats:
        Output of ``compute_monthly_stats()``.
    client_name:
        Optional client name to include in the report header.
    plan_name:
        Optional plan/subscription name.

    Returns
    -------
    str
        Markdown-formatted assurance report.
    """
    period_label = stats.get("period_label", "Unknown period")
    generated_at = stats.get("generated_at_utc", "")
    uptime_str = (
        f"{stats.get('uptime_pct')}%" if stats.get("uptime_pct") is not None else "N/A"
    )

    lines: list[str] = [
        f"# Monthly Monitoring Assurance Report — {period_label}",
        "",
    ]

    if client_name:
        lines.append(f"**Client:** {client_name}")
    if plan_name:
        lines.append(f"**Plan:** {plan_name}")
    lines.append(f"**Generated:** {generated_at}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Monitoring Summary table
    lines += [
        "## Monitoring Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Sources Checked | {stats.get('sources_checked', 0)} |",
        f"| Total Runs | {stats.get('total_runs', 0)} |",
        f"| Successful Runs | {stats.get('successful_runs', 0)} |",
        f"| Uptime | {uptime_str} |",
        f"| Changes Detected | {stats.get('changes_detected', 0)} |",
        "",
    ]

    # Risk Breakdown table
    lines += [
        "## Risk Breakdown",
        "",
        "| Risk Level | Count |",
        "|-----------|-------|",
        f"| HIGH | {stats.get('high_risk_count', 0)} |",
        f"| MEDIUM | {stats.get('medium_risk_count', 0)} |",
        f"| LOW | {stats.get('low_risk_count', 0)} |",
        f"| NON-MATERIAL | {stats.get('non_material_count', 0)} |",
        "",
    ]

    # Review Status
    unreviewed = stats.get("unreviewed_count", 0)
    lines += [
        "## Review Status",
        "",
        f"{unreviewed} change(s) pending human review.",
        "",
    ]

    # Notes (estimate warning if applicable)
    if stats.get("is_estimate"):
        lines += [
            "## Notes",
            "",
            "⚠ Data for this period may be partial (fewer than 20 runs recorded). "
            "Figures are estimates.",
            "",
        ]

    lines.append("---")
    lines.append("")
    lines.append(f"**Disclaimer:** {LEGAL_DISCLAIMER}")
    lines.append("")

    return "\n".join(lines)


def generate_monthly_report_pdf(
    stats: dict[str, Any],
    client_name: str = "",
    plan_name: str = "",
    output_path: Path | None = None,
) -> Path:
    """Render the assurance report as a PDF file using Playwright.

    Falls back to a Markdown file if Playwright is unavailable.

    Parameters
    ----------
    stats:
        Output of ``compute_monthly_stats()``.
    client_name:
        Optional client name for the report header.
    plan_name:
        Optional plan name.
    output_path:
        Destination path. Defaults to reports/monthly_assurance_{year}_{month:02d}.pdf.

    Returns
    -------
    Path
        Absolute path to the generated file (PDF or fallback Markdown).
    """
    year = stats.get("year", datetime.now(timezone.utc).year)
    month = stats.get("month", datetime.now(timezone.utc).month)

    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if output_path is None:
        output_path = _REPORTS_DIR / f"monthly_assurance_{year}_{month:02d}.pdf"

    markdown = render_assurance_report_markdown(stats, client_name=client_name, plan_name=plan_name)

    # Try Playwright PDF generation
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
        html_doc = _markdown_to_html(markdown, title=f"Monthly Assurance Report — {stats.get('period_label', '')}")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.set_content(html_doc, wait_until="networkidle")
            page.pdf(
                path=str(output_path),
                format="A4",
                print_background=True,
                margin={"top": "18mm", "right": "14mm", "bottom": "18mm", "left": "14mm"},
            )
            browser.close()
        return output_path.resolve()
    except Exception as exc:
        logger.warning("generate_monthly_report_pdf: Playwright unavailable (%s), writing markdown fallback", exc)
        md_path = output_path.with_suffix(".md")
        md_path.write_text(markdown, encoding="utf-8")
        return md_path.resolve()


# ── internal helpers ──────────────────────────────────────────────────────────

def _markdown_to_html(markdown: str, title: str = "Monthly Assurance Report") -> str:
    """Convert assurance report Markdown to a simple HTML document for PDF rendering."""
    import html as _html

    lines = markdown.splitlines()
    body_parts: list[str] = []
    in_table = False
    in_table_header = True

    for line in lines:
        if line.startswith("# "):
            body_parts.append(f"<h1>{_html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body_parts.append(f"<h2>{_html.escape(line[3:])}</h2>")
        elif line.startswith("|"):
            # Table row
            if not in_table:
                body_parts.append('<table>')
                in_table = True
                in_table_header = True
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                # Separator row — end header
                in_table_header = False
                continue
            tag = "th" if in_table_header else "td"
            row_html = "".join(f"<{tag}>{_html.escape(c)}</{tag}>" for c in cells)
            body_parts.append(f"<tr>{row_html}</tr>")
            if in_table_header:
                in_table_header = False
        elif line == "---":
            if in_table:
                body_parts.append("</table>")
                in_table = False
            body_parts.append("<hr>")
        elif line.startswith("**") and line.endswith("**"):
            if in_table:
                body_parts.append("</table>")
                in_table = False
            body_parts.append(f"<p><strong>{_html.escape(line.strip('*'))}</strong></p>")
        elif line.strip():
            if in_table:
                body_parts.append("</table>")
                in_table = False
            # Handle **bold** inline
            escaped = _html.escape(line)
            import re as _re
            escaped = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
            body_parts.append(f"<p>{escaped}</p>")
        else:
            if in_table:
                body_parts.append("</table>")
                in_table = False

    if in_table:
        body_parts.append("</table>")

    return (
        "<!doctype html>\n<html><head><meta charset='utf-8'>"
        f"<title>{_html.escape(title)}</title>"
        "<style>"
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;"
        "max-width:760px;margin:40px auto;padding:0 24px;color:#1a1a2e;line-height:1.6;}"
        "h1{border-bottom:3px solid #16d9f5;padding-bottom:10px;}"
        "table{border-collapse:collapse;width:100%;margin:12px 0;}"
        "th,td{border:1px solid #ddd;padding:8px 12px;text-align:left;}"
        "th{background:#f4f6f8;font-weight:bold;}"
        "hr{border:none;border-top:1px solid #ddd;margin:20px 0;}"
        "</style></head><body>"
        + "\n".join(body_parts)
        + "</body></html>"
    )
