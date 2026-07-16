"""
RegRadar v10.1 — Report export.

generate_report(days: int = 7) -> dict

Reads the latest snapshot per monitored URL from the SQLite documents table
for the last N days, groups results by risk level, and writes two self-
contained report files to reports/ in the project root:

    reports/regradar_report_YYYY-MM-DD.md
    reports/regradar_report_YYYY-MM-DD.html

No AI calls. No Telegram. Read-only database access.

Derived fields (not stored in DB, computed at report time):
  - review_required / review_reason  — inferred from risk_level + ai_used
  - is_legacy                        — detected from old-style reason strings
  - ai_used                          — inferred from ai_summary presence
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from app.config import DB_PATH
from app.legal_safety import find_forbidden_claims

_REPORTS_DIR = Path(__file__).parent.parent / "reports"
_RISK_ORDER  = ["HIGH", "MEDIUM", "LOW"]

# Replacement shown in place of an AI summary that failed the forbidden-claims
# check. The report renders stored AI free text (ai_summary / business_action)
# into a customer-shaped document, so a hallucinated forbidden claim (e.g.
# "guarantee compliance") stored in the documents table must never reach the
# rendered bytes — it is scrubbed here and the record is flagged for review.
_SCRUBBED_AI_NOTICE = (
    "[AI summary withheld: the stored wording did not pass the forbidden-claims "
    "check. Review the source record and evidence directly.]"
)

# Reason strings produced by the pre-v10.1 rule-based scorer that are too
# terse for a client report.  Records containing any of these are flagged as
# "legacy" so the report adds a visible disclaimer.
_LEGACY_MARKERS = (
    "Detected keyword: ",
    "No high-risk keywords detected",
    "High-risk keywords not detected",
    "Multiple strong-risk keywords:",
    "Strong-risk keyword",
    "Regulatory keyword",
    "without sufficient context",
)


# ── database helpers ──────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _fetch_records(days: int) -> list[dict]:
    """
    Return the most-recent snapshot per URL whose created_at falls within
    the last `days` days.  Returns [] if the database or table does not exist.
    """
    if not Path(DB_PATH).exists():
        return []

    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT
                url,
                risk_level,
                risk_reason,
                ai_summary,
                business_action,
                created_at,
                LENGTH(content) AS content_length
            FROM documents
            WHERE created_at >= ?
            ORDER BY created_at DESC
            """,
            (cutoff,),
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()

    # One record per URL — keep the newest (rows already DESC)
    seen: set[str] = set()
    records: list[dict] = []
    for row in rows:
        url = row["url"]
        if url not in seen:
            seen.add(url)
            records.append(dict(row))

    return records


# ── grouping ──────────────────────────────────────────────────────────────────

def _group_by_risk(records: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {level: [] for level in _RISK_ORDER}
    for rec in records:
        level = (rec.get("risk_level") or "LOW").upper()
        if level not in groups:
            level = "LOW"
        groups[level].append(rec)
    return groups


# ── record-level helpers ──────────────────────────────────────────────────────

def _fmt_date(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return iso or "unknown"


def _is_legacy(rec: dict) -> bool:
    """True if this record was produced by the pre-v10.1 keyword scanner."""
    if rec.get("ai_summary"):
        return False
    reason = rec.get("risk_reason") or ""
    return any(m in reason for m in _LEGACY_MARKERS)


def _scrub_record_claims(rec: dict) -> tuple[dict, bool]:
    """Return a copy of ``rec`` with AI free-text fields cleared when they
    contain a forbidden claim, and whether anything was scrubbed.

    Keeps the customer-shaped report on the safe side of the legal-language
    rules even if a hallucinated claim was persisted to the documents table.
    """
    out = dict(rec)
    scrubbed = False
    summary = (out.get("ai_summary") or "").strip()
    if summary and find_forbidden_claims(summary):
        out["ai_summary"] = _SCRUBBED_AI_NOTICE
        scrubbed = True
    action = (out.get("business_action") or "").strip()
    if action and find_forbidden_claims(action):
        out["business_action"] = ""
        scrubbed = True
    # risk_reason is ALSO rendered and can carry AI free text (pipeline sets it
    # from ai_result["reason"] when AI runs), so it must be scrubbed too — the
    # fail-closed final scan covers the whole rendered doc, and an unscrubbed
    # forbidden phrase here would raise and produce NO report for ANY record.
    reason = (out.get("risk_reason") or "").strip()
    if reason and find_forbidden_claims(reason):
        out["risk_reason"] = _SCRUBBED_AI_NOTICE
        scrubbed = True
    return out, scrubbed


def _derive_review(rec: dict) -> tuple[bool, str]:
    """Infer review_required and review_reason from the stored record.

    HIGH risk ALWAYS requires human review — this is the product rule (risk >= 70
    / HIGH must be human-reviewed before client-facing action) and it must hold
    regardless of whether an AI summary exists. An AI summary is analysis, not a
    substitute for the review gate; the previous logic short-circuited on
    ai_summary presence and rendered "Review required: No" for AI-analysed HIGH
    records, inverting the rule.
    """
    risk    = (rec.get("risk_level") or "LOW").upper()
    ai_used = bool(rec.get("ai_summary"))
    if risk == "HIGH":
        return True, (
            "High-risk classification always requires human compliance review "
            "before any client-facing action, regardless of AI analysis."
        )
    if ai_used:
        return False, ""
    if risk == "MEDIUM":
        return True, (
            "Medium-risk classification was generated by rule-based logic. "
            "Review is recommended to confirm whether the change is material."
        )
    return False, "No immediate review required based on current rule-based signals."


def _ai_label(rec: dict) -> str:
    """Short AI status label for the record."""
    return "Available" if rec.get("ai_summary") else "Not available — classification is rule-based only"


_AI_MISSING_EXPLANATION = (
    "Semantic AI analysis was not available for this record. "
    "The risk classification is based on automated rule-based keyword detection only. "
    "The following compliance dimensions were NOT assessed: new obligations, deadlines, "
    "reporting duties, licensing impacts, enforcement exposure, operational impact, and materiality. "
    "Review by a compliance professional is recommended before any regulatory action."
)

_SEMANTIC_DIMS_MD = (
    "new regulatory obligation · deadline or time requirement · "
    "reporting or filing duty · licensing or authorisation impact · "
    "enforcement or penalty exposure · operational impact · materiality classification"
)


# ── Markdown renderer ─────────────────────────────────────────────────────────

def _md_record(rec: dict) -> list[str]:
    """Return Markdown lines for a single record card."""
    url            = rec.get("url", "")
    risk           = (rec.get("risk_level") or "LOW").upper()
    date_str       = _fmt_date(rec.get("created_at", ""))
    reason         = (rec.get("risk_reason")     or "").strip()
    summary        = (rec.get("ai_summary")      or "").strip()
    action         = (rec.get("business_action") or "").strip()
    content_length = rec.get("content_length") or 0
    ai_used        = bool(summary)
    review_req, review_rsn = _derive_review(rec)
    legacy         = _is_legacy(rec)

    lines: list[str] = [f"### {url}", ""]
    lines.append(f"- **Risk:** {risk}")
    lines.append(f"- **Date:** {date_str}")

    if reason:
        lines.append(f"- **Risk reason:** {reason}")

    # AI status
    lines.append(f"- **AI analysis:** {_ai_label(rec)}")

    # Review (suppress verbose block for LOW)
    if risk == "LOW":
        lines.append(f"- **Review required:** No")
        lines.append(f"- **Content:** {content_length:,} chars")
        lines.append("")
        return lines

    # HIGH / MEDIUM — full detail
    if review_req:
        lines.append("- **Review required:** Yes")
        lines.append(f"- **Review reason:** {review_rsn}")
    else:
        lines.append("- **Review required:** No")

    if legacy:
        lines.append("")
        lines.append(
            "> ⚠ **Legacy signal:** this record was classified before improved "
            "risk validation. Manual review is recommended regardless of the "
            "automated risk level shown above."
        )

    lines.append("")

    if summary:
        lines.append(f"**Summary:** {summary}")
        if action:
            lines.append("")
            lines.append(f"**Business action:** {action}")
    else:
        lines.append(f"_{_AI_MISSING_EXPLANATION}_")
        if risk in ("HIGH", "MEDIUM"):
            lines.append("")
            lines.append("*Semantic dimensions not assessed (enable AI analysis to detect):*")
            lines.append(f"_{_SEMANTIC_DIMS_MD}_")

    lines.append("")
    lines.append(f"- **Content:** {content_length:,} chars")
    lines.append("")
    return lines


def _build_markdown(
    groups:       dict[str, list[dict]],
    generated_at: str,
    period_days:  int,
    counts:       dict,
) -> str:
    lines: list[str] = []
    period_str = f"Last {period_days} day{'s' if period_days != 1 else ''}"

    lines += [
        "# StatuteProof Monitoring Report",
        "",
        f"Generated: {generated_at}",
        f"Period: {period_str}",
        "",
        "---",
        "",
        "## Executive Overview",
        "",
        f"- Total monitored sources: {counts['total']}",
        f"- High risk:               {counts['high']}",
        f"- Medium risk:             {counts['medium']}",
        f"- Low risk:                {counts['low']}",
        "",
        "> **Disclaimer:** Risk levels marked without AI analysis are generated "
        "by automated rule-based keyword detection and may require human "
        "compliance review before any regulatory action is taken.",
        "",
    ]

    section_titles = {
        "HIGH":   "## High Risk Changes",
        "MEDIUM": "## Medium Risk Changes",
        "LOW":    "## Low Risk Changes",
    }

    for level in _RISK_ORDER:
        lines += ["---", "", section_titles[level], ""]
        recs = groups[level]

        if not recs:
            lines += ["No records found for this period.", ""]
            continue

        for rec in recs:
            lines += _md_record(rec)

    from app.evidence_pack import FULL_LEGAL_DISCLAIMER

    lines += [
        "---",
        "",
        "## Disclaimer",
        "",
        FULL_LEGAL_DISCLAIMER,
        "",
        f"*Report generated by StatuteProof at {generated_at}*",
        "",
    ]
    return "\n".join(lines)


# ── HTML renderer ─────────────────────────────────────────────────────────────

def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _badge(level: str) -> str:
    palette = {
        "HIGH":   ("background:#c0392b;color:#fff", "HIGH"),
        "MEDIUM": ("background:#d35400;color:#fff", "MEDIUM"),
        "LOW":    ("background:#27ae60;color:#fff", "LOW"),
    }
    style, label = palette.get(level.upper(), ("background:#888;color:#fff", level))
    return (
        f'<span style="{style};padding:2px 10px;border-radius:3px;'
        f'font-weight:bold;font-size:0.82em;letter-spacing:.04em;">'
        f"{label}</span>"
    )


def _small_badge(text: str, bg: str, fg: str = "#fff") -> str:
    return (
        f'<span style="background:{bg};color:{fg};padding:1px 8px;'
        f'border-radius:3px;font-size:0.78em;font-weight:bold;">'
        f"{_esc(text)}</span>"
    )


def _html_record(rec: dict, border_color: str) -> str:
    """Return HTML string for a single record card."""
    url            = rec.get("url", "")
    risk           = (rec.get("risk_level") or "LOW").upper()
    date_str       = _fmt_date(rec.get("created_at", ""))
    reason         = (rec.get("risk_reason")     or "").strip()
    summary        = (rec.get("ai_summary")      or "").strip()
    action         = (rec.get("business_action") or "").strip()
    content_length = rec.get("content_length") or 0
    review_req, review_rsn = _derive_review(rec)
    legacy         = _is_legacy(rec)

    parts: list[str] = []
    parts.append(
        f'<div style="background:#fafafa;border-left:5px solid {border_color};'
        f'padding:16px 20px;margin:16px 0;border-radius:0 5px 5px 0;'
        f'box-shadow:0 1px 4px rgba(0,0,0,.09);">'
    )

    # URL
    parts.append(
        f'<p style="margin:0 0 8px;font-weight:bold;word-break:break-all;">'
        f'<a href="{_esc(url)}" style="color:#2c3e50;text-decoration:none;">'
        f'{_esc(url)}</a></p>'
    )

    # Risk + Date row
    parts.append(
        f'<p style="margin:4px 0;">'
        f'<strong>Risk:</strong>&nbsp;{_badge(risk)}'
        f'&emsp;<strong>Date:</strong>&nbsp;{_esc(date_str)}</p>'
    )

    # Risk reason
    if reason:
        parts.append(
            f'<p style="margin:6px 0;">'
            f'<strong>Risk reason:</strong>&nbsp;'
            f'<span style="color:#444;">{_esc(reason)}</span></p>'
        )

    # AI status
    ai_badge_html = (
        _small_badge("AI Available", "#27ae60")
        if summary
        else _small_badge("Rule-based only", "#7f8c8d")
    )
    parts.append(
        f'<p style="margin:6px 0;">'
        f'<strong>AI analysis:</strong>&nbsp;{ai_badge_html}</p>'
    )

    # LOW: compact footer and done
    if risk == "LOW":
        parts.append(
            f'<p style="margin:8px 0 0;font-size:0.78em;color:#aaa;">'
            f'Content:&nbsp;{content_length:,}&nbsp;chars&emsp;'
            f'Review required: No</p>'
        )
        parts.append("</div>")
        return "\n".join(parts)

    # HIGH / MEDIUM — review block
    if review_req:
        rev_badge = _small_badge("Yes", "#c0392b")
        parts.append(
            f'<p style="margin:6px 0;">'
            f'<strong>Review required:</strong>&nbsp;{rev_badge}&nbsp;'
            f'<span style="color:#c0392b;font-size:.88em;">{_esc(review_rsn)}</span></p>'
        )
    else:
        rev_badge = _small_badge("No", "#27ae60")
        parts.append(
            f'<p style="margin:6px 0;">'
            f'<strong>Review required:</strong>&nbsp;{rev_badge}</p>'
        )

    # Legacy warning
    if legacy:
        parts.append(
            '<div style="background:#fff3cd;border:1px solid #ffc107;'
            'padding:8px 12px;border-radius:3px;margin:10px 0;font-size:.88em;">'
            '<strong>⚠ Legacy signal:</strong> this record was classified before '
            'improved risk validation. Manual review is recommended regardless of '
            'the automated risk level shown above.'
            '</div>'
        )

    # Summary / AI explanation
    if summary:
        parts.append(
            f'<div style="background:#f0f4f8;padding:10px 14px;border-radius:3px;'
            f'margin-top:10px;">'
            f'<strong>Summary:</strong><br>'
            f'<span style="color:#333;">{_esc(summary)}</span></div>'
        )
    else:
        parts.append(
            f'<p style="margin:8px 0;color:#666;font-style:italic;'
            f'font-size:.9em;">{_esc(_AI_MISSING_EXPLANATION)}</p>'
        )
        if risk in ("HIGH", "MEDIUM"):
            parts.append(
                '<div style="background:#f8f9fa;border:1px solid #dee2e6;'
                'padding:8px 12px;border-radius:3px;margin:8px 0;font-size:.84em;">'
                '<strong>Semantic dimensions not assessed'
                ' (enable AI analysis to detect):</strong>'
                '<ul style="margin:4px 0 0;padding-left:18px;color:#666;">'
                '<li>New regulatory obligation</li>'
                '<li>Deadline or time-bound requirement</li>'
                '<li>Reporting or filing duty</li>'
                '<li>Licensing or authorisation impact</li>'
                '<li>Enforcement or penalty exposure</li>'
                '<li>Operational impact level</li>'
                '<li>Materiality classification</li>'
                '</ul></div>'
            )

    # Business action
    if action:
        parts.append(
            f'<div style="background:#fffde7;border:1px solid #ffe082;'
            f'padding:10px 14px;border-radius:3px;margin-top:10px;">'
            f'<strong>Business Action:</strong><br>'
            f'<span style="color:#555;">{_esc(action)}</span></div>'
        )

    # Footer
    parts.append(
        f'<p style="margin:10px 0 0;font-size:0.78em;color:#aaa;">'
        f"Content:&nbsp;{content_length:,}&nbsp;chars</p>"
    )
    parts.append("</div>")
    return "\n".join(parts)


def _build_html(
    groups:       dict[str, list[dict]],
    generated_at: str,
    period_days:  int,
    counts:       dict,
) -> str:
    period_str = f"Last {period_days} day{'s' if period_days != 1 else ''}"

    section_color = {"HIGH": "#c0392b", "MEDIUM": "#d35400", "LOW": "#27ae60"}
    section_title = {
        "HIGH":   "High Risk Changes",
        "MEDIUM": "Medium Risk Changes",
        "LOW":    "Low Risk Changes",
    }

    body_parts: list[str] = []
    for level in _RISK_ORDER:
        color = section_color[level]
        body_parts.append(
            f'<h2 style="color:{color};border-bottom:3px solid {color};'
            f'padding-bottom:6px;margin-top:44px;">'
            f'{section_title[level]}</h2>'
        )
        recs = groups[level]
        if not recs:
            body_parts.append(
                '<p style="color:#999;font-style:italic;">'
                "No records found for this period.</p>"
            )
            continue
        for rec in recs:
            body_parts.append(_html_record(rec, color))

    body_html = "\n".join(body_parts)

    from app.evidence_pack import FULL_LEGAL_DISCLAIMER

    disclaimer_html = (
        '<div class="disclaimer" style="margin-top:40px;">\n'
        f"<strong>Disclaimer:</strong> {_esc(FULL_LEGAL_DISCLAIMER)}\n"
        "</div>\n\n"
    )

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">\n'
        "<title>StatuteProof Monitoring Report</title>\n"
        "<style>\n"
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;"
        "max-width:920px;margin:40px auto;padding:0 24px;color:#2c3e50;"
        "background:#fff;line-height:1.65;}\n"
        "h1{color:#1a252f;border-bottom:3px solid #2980b9;padding-bottom:10px;}\n"
        ".meta{background:#ecf0f1;padding:12px 18px;border-radius:4px;"
        "margin-bottom:24px;font-size:.9em;}\n"
        ".disclaimer{background:#fef9e7;border:1px solid #f9ca24;padding:10px 16px;"
        "border-radius:4px;font-size:.88em;margin-bottom:28px;color:#555;}\n"
        ".overview{display:flex;gap:16px;flex-wrap:wrap;margin:20px 0 32px;}\n"
        ".stat{background:#f5f5f5;padding:16px 22px;border-radius:6px;"
        "text-align:center;min-width:110px;}\n"
        ".stat .num{font-size:2.2em;font-weight:bold;line-height:1;}\n"
        ".stat .lbl{font-size:.78em;color:#888;margin-top:4px;}\n"
        ".stat.high .num{color:#c0392b;}\n"
        ".stat.medium .num{color:#d35400;}\n"
        ".stat.low .num{color:#27ae60;}\n"
        "footer{margin-top:60px;padding-top:16px;border-top:1px solid #eee;"
        "font-size:.78em;color:#bbb;text-align:center;}\n"
        "</style>\n"
        "</head>\n"
        "<body>\n\n"
        "<h1>StatuteProof Monitoring Report</h1>\n\n"
        '<div class="meta">\n'
        f"<strong>Generated:</strong> {_esc(generated_at)}&emsp;"
        f"<strong>Period:</strong> {_esc(period_str)}\n"
        "</div>\n\n"
        '<div class="disclaimer">\n'
        "<strong>Disclaimer:</strong> Risk levels marked without AI analysis are "
        "generated by automated rule-based keyword detection and may require "
        "human compliance review before any regulatory action is taken.\n"
        "</div>\n\n"
        '<h2 style="margin-top:0;border-bottom:3px solid #2980b9;'
        'padding-bottom:6px;color:#2980b9;">Executive Overview</h2>\n'
        '<div class="overview">\n'
        '  <div class="stat">'
        f'<div class="num">{counts["total"]}</div>'
        '<div class="lbl">Total Records</div></div>\n'
        '  <div class="stat high">'
        f'<div class="num">{counts["high"]}</div>'
        '<div class="lbl">High Risk</div></div>\n'
        '  <div class="stat medium">'
        f'<div class="num">{counts["medium"]}</div>'
        '<div class="lbl">Medium Risk</div></div>\n'
        '  <div class="stat low">'
        f'<div class="num">{counts["low"]}</div>'
        '<div class="lbl">Low Risk</div></div>\n'
        "</div>\n\n"
        f"{body_html}\n\n"
        f"{disclaimer_html}"
        f"<footer>Report generated by StatuteProof &mdash; {_esc(generated_at)}</footer>\n\n"
        "</body>\n"
        "</html>\n"
    )


# ── public API ────────────────────────────────────────────────────────────────

def generate_report(days: int = 7) -> dict:
    """
    Generate Markdown and HTML compliance reports for the last `days` days.

    Returns
    -------
    dict
        markdown_path, html_path, total_records,
        high_count, medium_count, low_count
    """
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Scrub any forbidden AI free text out of every record BEFORE rendering, so a
    # hallucinated claim stored in the documents table can never reach the
    # customer-shaped report bytes.
    raw_records = _fetch_records(days)
    records: list[dict] = []
    scrubbed_count = 0
    for rec in raw_records:
        clean, was_scrubbed = _scrub_record_claims(rec)
        records.append(clean)
        if was_scrubbed:
            scrubbed_count += 1
    groups  = _group_by_risk(records)

    counts = {
        "total":  len(records),
        "high":   len(groups["HIGH"]),
        "medium": len(groups["MEDIUM"]),
        "low":    len(groups["LOW"]),
    }

    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    date_slug    = datetime.utcnow().strftime("%Y-%m-%d")

    md_path   = _REPORTS_DIR / f"regradar_report_{date_slug}.md"
    html_path = _REPORTS_DIR / f"regradar_report_{date_slug}.html"

    markdown = _build_markdown(groups, generated_at, days, counts)
    html     = _build_html(groups, generated_at, days, counts)

    # Fail-closed final-bytes guard: after per-record scrubbing the only remaining
    # free text is rule-based, but scan the rendered output anyway and refuse to
    # write a customer-shaped report that still contains a forbidden claim.
    residual = sorted(set(find_forbidden_claims(markdown)) | set(find_forbidden_claims(html)))
    if residual:
        raise ValueError(
            "Compliance report contains forbidden claim(s) after scrubbing: "
            + ", ".join(residual)
        )

    md_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")

    return {
        "markdown_path": str(md_path),
        "html_path":     str(html_path),
        "total_records": counts["total"],
        "high_count":    counts["high"],
        "medium_count":  counts["medium"],
        "low_count":     counts["low"],
        "forbidden_claims_scrubbed": scrubbed_count,
    }
