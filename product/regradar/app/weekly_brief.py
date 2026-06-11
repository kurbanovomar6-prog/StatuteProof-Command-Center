"""Reviewed weekly brief generator.

Briefs are generated from human-approved local alert drafts only. This module
does not send, publish, or call AI.
"""

from __future__ import annotations

import html
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import logging

from app.alert_review import (
    DECISION_URGENT,
    DECISION_WEEKLY,
    STATUS_APPROVED_URGENT,
    STATUS_APPROVED_WEEKLY,
    latest_review_for,
    list_alert_drafts,
    review_alert,
)
from app.client_profiles import load_client_profile, score_alert_relevance, source_metadata_for_alert
from app.source_runs import deduplicate_alerts
from app.sources import load_sources
_FULL_BRIEF_DISCLAIMER = (
    "StatuteProof reports are generated from monitored official-source records and are provided "
    "for information and compliance review support only. StatuteProof reports do not constitute "
    "legal advice, regulatory advice, compliance certification, or a legal opinion. StatuteProof "
    "does not replace qualified legal counsel, compliance professionals, MLROs, or other "
    "professional advisers. StatuteProof does not guarantee compliance, prevent fines, or certify "
    "that all regulatory updates have been captured. Source monitoring may be affected by "
    "publication delays, website changes, PDF formatting, access limits, or source structure "
    "changes. Users should verify official source material directly and review evidence records, "
    "hashes, timestamps, and diffs before relying on a report. Users should consult qualified "
    "legal or compliance professionals before making regulatory, filing, operational, or customer "
    "decisions based on a report."
)

_BASE_DIR = Path(__file__).parent.parent
_OUTPUT_DIR = _BASE_DIR / "reports" / "weekly_briefs"
_INCLUDED_STATUSES = {STATUS_APPROVED_WEEKLY, STATUS_APPROVED_URGENT}
_INCLUDED_DECISIONS = {DECISION_WEEKLY, DECISION_URGENT}
logger = logging.getLogger(__name__)

# ── STEP 2: Legal language gate ───────────────────────────────────────────────
FORBIDDEN_IN_BRIEF = [
    "guarantee compliance",
    "prevent fines",
    "ensure you are compliant",
    "you will be compliant",
    "automatically compliant",
    "no action needed",
    "fully covered",
    "certified",
    "official partner",
]


def legal_scan_brief(brief: dict) -> list[str]:
    """
    STEP 2 — Scan brief fields for forbidden legal claims before delivery.

    Returns a list of flag strings; empty list means the brief is clean.
    """
    flags = []
    for field in ("executive_summary", "business_action_required", "specific_obligation"):
        text = str(brief.get(field) or "").lower()
        for phrase in FORBIDDEN_IN_BRIEF:
            if phrase in text:
                flags.append(f"FORBIDDEN phrase '{phrase}' in field '{field}'")
    return flags


# ── STEP 3: QA gate ───────────────────────────────────────────────────────────

def qa_gate(brief: dict) -> str:
    """
    STEP 3 — Final quality/completeness gate before brief inclusion.

    Returns "SHIP" or a "HOLD: <reason>" string.
    """
    if brief.get("risk_level") == "HIGH":
        if not brief.get("specific_obligation"):
            return "HOLD: HIGH brief missing specific_obligation"
        if not brief.get("licence_scope"):
            return "HOLD: HIGH brief does not specify which UAE licence type is affected"
    raw_conf = brief.get("confidence", "medium")
    try:
        if float(raw_conf) < 0.4:
            return "HOLD: confidence below 0.4 — brief is too uncertain to deliver"
    except (TypeError, ValueError):
        pass  # string confidence values (low/medium/high) always pass the float gate
    return "SHIP"


def generate_weekly_brief(
    *,
    client_id: str,
    market: str = "AE",
    days: int = 7,
    date_from: str | None = None,
    date_to: str | None = None,
    demo_fixture: bool = False,
    formats: set[str] | None = None,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    root = base_dir or _BASE_DIR
    profile = load_client_profile(client_id, path=root / "data" / "client_profiles.example.json")
    start, end = _period(days=days, date_from=date_from, date_to=date_to)
    alerts = collect_approved_alerts(
        client_profile=profile,
        market=market,
        start=start,
        end=end,
        base_dir=root,
    )
    is_demo = False
    if not alerts and demo_fixture:
        alerts = [_demo_alert(client_id, market)]
        is_demo = True

    brief = build_weekly_brief(
        client_profile=profile,
        market=market,
        start=start,
        end=end,
        alerts=alerts,
        demo_fixture=is_demo,
    )
    output_paths = write_weekly_brief(
        brief,
        client_id=client_id,
        end=end,
        formats=formats or {"md", "html"},
        base_dir=root,
    )
    return {
        "brief": brief,
        "paths": output_paths,
        "included_alerts": len(alerts),
        "demo_fixture": is_demo,
    }


def collect_approved_alerts(
    *,
    client_profile: dict[str, Any],
    market: str,
    start: datetime,
    end: datetime,
    base_dir: Path | None = None,
) -> list[dict[str, Any]]:
    rows = []
    for alert in list_alert_drafts(market=market, base_dir=base_dir):
        checked = _parse_dt(alert.get("checked_at_utc"))
        if checked and not (start <= checked <= end):
            continue
        latest = latest_review_for(alert.get("alert_id"))
        status = (latest or {}).get("new_status") or alert.get("review_status")
        decision = (latest or {}).get("new_send_decision") or alert.get("send_decision")
        if status not in _INCLUDED_STATUSES or decision not in _INCLUDED_DECISIONS:
            continue
        relevance = alert.get("relevance") or {}
        if relevance.get("client_id") and relevance.get("client_id") != client_profile.get("client_id"):
            continue
        if not relevance:
            metadata = source_metadata_for_alert(alert)
            relevance = score_alert_relevance(alert, client_profile, metadata)
            alert["relevance"] = {"client_id": client_profile.get("client_id"), **relevance}
        alert["_effective_review_status"] = status
        alert["_effective_send_decision"] = decision
        rows.append(alert)
    rows.sort(key=lambda item: _risk_sort(item), reverse=True)
    return deduplicate_alerts(rows)


def build_weekly_brief(
    *,
    client_profile: dict[str, Any],
    market: str,
    start: datetime,
    end: datetime,
    alerts: list[dict[str, Any]],
    demo_fixture: bool = False,
) -> dict[str, Any]:
    # ── STEP 2 + 3: Legal scan and QA gate before rendering ──────────────
    approved_alerts: list[dict[str, Any]] = []
    for alert in alerts:
        source_id = alert.get("source_id") or alert.get("alert_id") or "unknown"
        brief_data = {
            "executive_summary": alert.get("executive_summary") or alert.get("ai_summary") or "",
            "business_action_required": alert.get("business_action_required") or "",
            "specific_obligation": alert.get("specific_obligation") or "",
            "risk_level": alert.get("risk_level") or "LOW",
            "licence_scope": alert.get("licence_scope") or "",
            "confidence": alert.get("confidence") or "medium",
        }
        legal_flags = legal_scan_brief(brief_data)
        if legal_flags:
            logger.warning(
                "BRIEF_LEGAL_BLOCK source_id=%s flags=%s",
                source_id, legal_flags,
            )
            continue
        qa_result = qa_gate(brief_data)
        if qa_result != "SHIP":
            logger.warning(
                "BRIEF_QA_HOLD source_id=%s reason=%s",
                source_id, qa_result,
            )
            try:
                if not demo_fixture:
                    review_alert(
                        alert_id=str(alert.get("alert_id") or source_id),
                        action="manual_review",
                        reviewer="qa_gate",
                        note=qa_result,
                        force=True,
                    )
            except Exception as exc:
                logger.debug("qa_gate: could not route to manual review: %s", exc)
            continue
        approved_alerts.append(alert)

    alerts = approved_alerts
    urgent = [item for item in alerts if item.get("_effective_send_decision") == DECISION_URGENT]
    weekly = [item for item in alerts if item.get("_effective_send_decision") == DECISION_WEEKLY]
    limitations = _collect_limitations(alerts)
    all_sources = load_sources()
    sources_checked = sum(
        1 for s in all_sources
        if s.get("enabled") and str(s.get("jurisdiction") or "").upper() == market.upper()
    )
    return {
        "title": "StatuteProof Weekly Regulatory Brief",
        "client_id": client_profile.get("client_id"),
        "client_name": client_profile.get("company_name") or client_profile.get("client_id"),
        "market": market,
        "period_start": start.date().isoformat(),
        "period_end": end.date().isoformat(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "review_mode": "human-reviewed",
        "demo_fixture": demo_fixture,
        "summary": {
            "reviewed_alerts_included": len(alerts),
            "urgent_ready_items": len(urgent),
            "weekly_only_items": len(weekly),
            "sources_checked": sources_checked or None,
        },
        "alerts": alerts,
        "limitations": limitations,
        "empty": len(alerts) == 0,
    }


def render_weekly_brief_markdown(brief: dict[str, Any]) -> str:
    marker = "\n**SAMPLE / DEMO - NOT CUSTOMER DATA**\n" if brief.get("demo_fixture") else ""
    lines = [
        f"# {brief['title']}",
        marker.strip(),
        f"- Client: {brief['client_name']}",
        f"- Market: {_market_label(brief['market'])}",
        f"- Period: {brief['period_start']} to {brief['period_end']}",
        f"- Generated: {brief['generated_at_utc']}",
        f"- Review mode: {brief['review_mode']}",
        "",
        f"This brief is configured for {brief['client_name']} and includes only human-reviewed items approved for that scope.",
        "",
        "## Executive Summary",
    ]
    summary = brief["summary"]
    if brief.get("empty"):
        lines.extend([
            "No reviewed updates were approved for this brief period.",
            "Monitoring and review workflow remains active. Sources and limitations depend on the client profile.",
        ])
    else:
        reviewed = summary["reviewed_alerts_included"]
        urgent = summary["urgent_ready_items"]
        plural = "update" if reviewed == 1 else "updates"
        verb = "is" if reviewed == 1 else "are"
        lines.append(f"{reviewed} reviewed {plural} approved for this period {verb} included.")
        if urgent:
            item = "item requires" if urgent == 1 else "items require"
            lines.append(f"{urgent} {item} priority review.")
        else:
            lines.append("No urgent client action is recommended from the reviewed items this period.")
    lines.append("")
    lines.append("## Sources Monitored This Period")
    if brief.get("empty"):
        lines.append("No reviewed updates were approved for this brief period.")
    else:
        for alert in brief["alerts"]:
            risk = str(alert.get("risk_level") or "").upper()
            change_type = str(alert.get("change_type") or "").upper()
            if risk == "HIGH":
                activity = "reviewed update included — high priority"
            elif risk == "MEDIUM":
                activity = "reviewed update included — medium priority"
            elif risk == "LOW":
                activity = "reviewed update included — informational"
            elif risk == "REVIEW" or change_type == "UNKNOWN":
                activity = "reviewed update included for transparency; content type undetermined"
            else:
                activity = "reviewed update included"
            lines.append(f"- {alert.get('source_name')}: {activity}")
    sources_checked = summary.get("sources_checked")
    if sources_checked is None:
        lines.append("- Remaining monitored sources showed no detected change based on monitoring this period.")
    else:
        remaining = max(0, int(sources_checked) - len(brief.get("alerts") or []))
        suffix = "source" if remaining == 1 else "sources"
        lines.append(f"- {remaining} additional monitored {suffix} showed no detected change based on monitoring this period.")
    lines.append("")
    lines.append("## Reviewed Regulatory Updates")
    if brief.get("empty"):
        lines.append("No approved reviewed alerts are included in this period.")
    else:
        for idx, alert in enumerate(brief["alerts"], start=1):
            proof = alert.get("proof_block") or {}
            lines.extend([
                f"### {idx}. {alert.get('source_name')}",
                f"- Priority: {_priority_label(alert)}",
                "",
                "#### Why it matters",
                _client_why_it_matters(alert),
                "",
                "#### Recommended action",
                _client_recommended_action(alert),
                "",
                "#### Proof summary",
                f"- Official source: {proof.get('official_url') or alert.get('source_url') or 'not recorded'}",
                f"- Checked: {alert.get('checked_at_utc') or proof.get('checked_at_utc') or 'not recorded'}",
                f"- Content fingerprint: {_content_fingerprint(proof)}",
                f"- Snapshot/diff: Archived internally and available on request.",
                f"- Extraction quality: {_extraction_quality_label(proof)}",
                "",
            ])
    lines.extend([
        "",
        "## Source Coverage and Limitations",
    ])
    if brief["limitations"]:
        for item in brief["limitations"]:
            cleaned = _client_limitation(item)
            if cleaned.startswith("Extraction quality:"):
                continue
            if "aggregate-count change" in str(item) or "adapter review required" in str(item).lower():
                cleaned = (
                    "UAE Legislation Portal item is based on an aggregate page change; additional "
                    "source validation is required before treating it as a specific regulatory publication."
                )
            lines.append(f"- {cleaned}")
    else:
        lines.append("- No alert-specific limitations were recorded for included updates.")
    lines.extend([
        "- Coverage depends on source accessibility, extraction quality, and the configured client profile.",
        "- StatuteProof does not claim complete UAE regulatory coverage.",
        "",
        "## Monitoring Notes",
        "This brief includes only human-reviewed items approved for this client profile.",
        "",
        "## Disclaimer",
        _FULL_BRIEF_DISCLAIMER,
        "Final compliance decisions require qualified legal review.",
        "",
    ])
    return "\n".join(line for line in lines if line is not None).replace("\n\n\n", "\n\n")


def render_weekly_brief_html(brief: dict[str, Any]) -> str:
    md = render_weekly_brief_markdown(brief)
    body = []
    in_list = False
    disclaimer = False
    for raw in md.splitlines():
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
            title = html.escape(line[3:])
            if line == "## Disclaimer":
                disclaimer = True
                body.append('<section class="disclaimer">')
            body.append(f"<h2>{title}</h2>")
        elif line.startswith("### "):
            if in_list:
                body.append("</ul>")
                in_list = False
            body.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("#### "):
            if in_list:
                body.append("</ul>")
                in_list = False
            body.append(f"<h4>{html.escape(line[5:])}</h4>")
        elif line.startswith("- "):
            if not in_list:
                body.append("<ul>")
                in_list = True
            body.append(f"<li>{_render_list_item(line[2:])}</li>")
        elif line:
            if in_list:
                body.append("</ul>")
                in_list = False
            body.append(f"<p>{_render_inline(line)}</p>")
    if in_list:
        body.append("</ul>")
    if disclaimer:
        body.append("</section>")
    styles = """
<style>
  body { margin: 0; padding: 40px 24px; background: #f7fafc; color: #07111F; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.6; }
  main { max-width: 680px; margin: 0 auto; background: #fff; padding: 40px; border: 1px solid #e6edf2; }
  h1 { margin-top: 0; color: #07111F; border-bottom: 3px solid #16D9F5; padding-bottom: 14px; }
  h2 { margin-top: 34px; color: #07111F; }
  h3 { margin-top: 26px; color: #0b2239; }
  h4 { margin-bottom: 6px; color: #0b2239; }
  ul { padding-left: 22px; }
  li { margin: 5px 0; }
  .disclaimer { border-top: 1px solid #d8e2ea; margin-top: 34px; padding-top: 14px; color: #5b6773; font-size: 0.92rem; }
</style>"""
    return (
        "<!doctype html>\n<html><head><meta charset=\"utf-8\"><title>StatuteProof Weekly Brief</title>"
        + styles
        + "</head><body><main>\n"
        + "\n".join(body)
        + "\n</main></body></html>\n"
    )


def write_weekly_brief(
    brief: dict[str, Any],
    *,
    client_id: str,
    end: datetime,
    formats: set[str],
    base_dir: Path | None = None,
) -> dict[str, str]:
    root = base_dir or _BASE_DIR
    out_dir = root / "reports" / "weekly_briefs" / client_id
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{end.date().isoformat()}_weekly_brief"
    paths = {}
    if "md" in formats:
        path = out_dir / f"{stem}.md"
        path.write_text(render_weekly_brief_markdown(brief), encoding="utf-8")
        paths["md"] = _rel(path, root)
    if "html" in formats:
        path = out_dir / f"{stem}.html"
        path.write_text(render_weekly_brief_html(brief), encoding="utf-8")
        paths["html"] = _rel(path, root)
    return paths


def _period(days: int, date_from: str | None, date_to: str | None) -> tuple[datetime, datetime]:
    if date_to:
        end = datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc)
    else:
        end = datetime.now(timezone.utc)
    if date_from:
        start = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
    else:
        start = end - timedelta(days=max(1, days))
    return start, end


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _collect_limitations(alerts: list[dict[str, Any]]) -> list[str]:
    seen = []
    for alert in alerts:
        for note in alert.get("limitations") or []:
            if note and note not in seen:
                seen.append(note)
    return seen


def _risk_sort(alert: dict[str, Any]) -> int:
    return {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "REVIEW": 0}.get(str(alert.get("risk_level")), 0)


def _market_label(market: str) -> str:
    return "UAE" if str(market).upper() == "AE" else str(market)


def _priority_label(alert: dict[str, Any]) -> str:
    risk = str(alert.get("risk_level") or "").upper()
    change_type = str(alert.get("change_type") or "").upper()
    if risk == "HIGH":
        return "High priority — review recommended"
    if risk == "MEDIUM":
        return "Medium priority — monitor for follow-on updates"
    if risk == "LOW":
        return "Low priority — informational"
    if risk == "REVIEW" or change_type == "UNKNOWN":
        return "Included for transparency — content type undetermined"
    return "Included for review"


def _client_why_it_matters(alert: dict[str, Any]) -> str:
    text = str(alert.get("why_it_matters") or "").strip()
    if not text or _has_internal_phrase(text):
        return (
            "The nature of this change could not be determined from the extracted content. "
            "The source is included for transparency. No client action is recommended unless "
            "a follow-on check confirms a specific regulatory publication."
        )
    return text


def _client_recommended_action(alert: dict[str, Any]) -> str:
    text = str(alert.get("recommended_action") or "").strip()
    if not text or _has_internal_phrase(text):
        return "Monitor the official source for related publications during the next review cycle."
    return text


def _has_internal_phrase(text: str) -> bool:
    lowered = text.lower()
    phrases = [
        "not reliable",
        "adapter review required",
        "customer dispatch",
        "manual validation required",
        "source-specific adapter",
        "before dispatch",
    ]
    return any(phrase in lowered for phrase in phrases)


def _content_fingerprint(proof: dict[str, Any]) -> str:
    value = str(proof.get("normalized_hash") or "")
    if not value or value == "demo":
        return "SAMPLE DATA — no real proof available."
    return f"{value[:16]}..."


def _extraction_quality_label(proof: dict[str, Any]) -> str:
    quality = str(proof.get("extraction_quality") or "").upper()
    if quality == "GOOD":
        return "Good based on extracted content volume."
    if quality in {"MEDIUM", "LIMITED"}:
        return "Limited based on extracted content volume."
    if quality in {"THIN", "LOW"}:
        return "Low based on extracted content volume."
    if quality == "FAILED":
        return "Failed extraction; review source manually."
    return "Not recorded."


def _client_limitation(note: str) -> str:
    text = str(note)
    if "sufficient for reliable generic monitoring" in text:
        return "Extraction quality: Good based on extracted content volume."
    return text


def _render_inline(text: str) -> str:
    escaped = html.escape(text)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)


def _render_list_item(text: str) -> str:
    rendered = _render_inline(text)
    return re.sub(
        r"(https?://[^\s<]+)",
        lambda match: f'<a href="{match.group(1)}">{match.group(1)}</a>',
        rendered,
    )


def _demo_alert(client_id: str, market: str) -> dict[str, Any]:
    return {
        "alert_id": "demo-weekly-vara-custody",
        "review_status": STATUS_APPROVED_WEEKLY,
        "send_decision": DECISION_WEEKLY,
        "_effective_review_status": STATUS_APPROVED_WEEKLY,
        "_effective_send_decision": DECISION_WEEKLY,
        "market": market,
        "source_id": "AE-dubai-virtual-assets-regulatory-authority-vara",
        "source_name": "Dubai Virtual Assets Regulatory Authority (VARA)",
        "source_url": "https://www.vara.ae/",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "change_type": "LICENSING",
        "risk_level": "MEDIUM",
        "why_it_matters": "Sample reviewed item showing how a VASP licensing/custody change would appear after human approval.",
        "recommended_action": "Review licensing, custody, AML/CFT, and internal control implications before client action.",
        "limitations": ["SAMPLE / DEMO - NOT CUSTOMER DATA"],
        "proof_block": {
            "official_url": "https://www.vara.ae/",
            "final_url": "https://www.vara.ae/",
            "normalized_hash": "demo",
            "proof_block_path": "demo-fixture",
            "diff_json_path": "demo-fixture",
        },
        "relevance": {"client_id": client_id, "delivery_decision": DECISION_WEEKLY},
    }


def _rel(path: Path, base_dir: Path) -> str:
    try:
        return str(path.resolve().relative_to(base_dir.resolve()))
    except ValueError:
        return str(path)
