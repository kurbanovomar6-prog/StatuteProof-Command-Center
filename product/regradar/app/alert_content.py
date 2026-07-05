"""
Shared alert content layer (alert-quality sprint, defects A2–A5).

ONE place builds the customer-facing alert content; Telegram and the alert
draft / email markdown both render from it. Principles:

- Every sentence is backed by an actual detection. Matched rule and keywords
  are named. A capped excerpt of the REAL diff shows what changed.
- Absent data is omitted entirely — no "Not specified", no "—" scaffolding.
- Severity honesty: HIGH states its indicator; when the run carries no
  recorded indicator detail, the alert says exactly that and nothing more.
- Mandatory in every rendering: proof URL, timestamp, and the footer
  "Monitoring information only. Not legal advice."

Severity rubric: see app/risk.py module docstring (rule identifiers
HIGH_MULTIPLE_STRONG, HIGH_STRONG_PLUS_CONTEXT, MEDIUM_SINGLE_STRONG,
MEDIUM_MODERATE_KEYWORD, MEDIUM_ARABIC, LOW_NO_KEYWORDS, NON_MATERIAL).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

FOOTER = "Monitoring information only. Not legal advice."

_EXCERPT_CAP = 400

_RULE_LABEL = {
    "HIGH_MULTIPLE_STRONG": "multiple strong indicators",
    "HIGH_STRONG_PLUS_CONTEXT": "strong indicator with context term",
    "MEDIUM_SINGLE_STRONG": "single strong keyword, no context",
    "MEDIUM_MODERATE_KEYWORD": "moderate-change keyword",
    "MEDIUM_ARABIC": "Arabic content — human review required",
    "LOW_NO_KEYWORDS": "no keywords matched",
    "NON_MATERIAL": "below materiality threshold",
}


def _clean(text: str) -> str:
    """Collapse whitespace; fix double periods (defect A5)."""
    out = " ".join(str(text or "").split())
    while ".." in out.replace("…", ""):
        out = out.replace("..", ".")
    return out


def _format_ts(value: str) -> str:
    """Render timestamps as 'YYYY-MM-DD HH:MM UTC' (no microsecond noise)."""
    raw = _clean(value)
    if not raw:
        return ""
    try:
        ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return raw
    if ts.tzinfo:
        ts = ts.astimezone(timezone.utc)
    return ts.strftime("%Y-%m-%d %H:%M UTC")


def _build_excerpt(added: list, removed: list, cap: int = _EXCERPT_CAP) -> str:
    """Capped excerpt of the real diff: additions first, then removals."""
    parts: list[str] = []
    for prefix, chunks in (("+", added or []), ("−", removed or [])):
        for chunk in chunks:
            text = _clean(chunk)
            if text:
                parts.append(f"{prefix} {text}")
    if not parts:
        return ""
    excerpt = "  ".join(parts)
    if len(excerpt) > cap:
        excerpt = excerpt[: cap - 1].rstrip() + "…"
    return excerpt


def _severity_line(risk_level: str, details: dict) -> str:
    """A4: severity must state its indicator or admit it has none recorded."""
    rule = str(details.get("rule") or "")
    matched = [str(k) for k in (details.get("matched_keywords") or [])]
    context = [str(c) for c in (details.get("matched_context") or [])]
    if matched:
        line = f"{risk_level} — matched: {', '.join(matched)}"
        if context:
            line += f"; context: {', '.join(context)}"
        if rule in _RULE_LABEL:
            line += f" (rule: {_RULE_LABEL[rule]})"
        return line
    return (
        f"{risk_level} — severity basis not recorded for this run; "
        "review the excerpt and the source directly"
    )


def build_alert_content(payload: dict[str, Any]) -> dict[str, Any]:
    """Build channel-independent alert content from a pipeline alert payload."""
    details = payload.get("risk_details") or {}
    risk_level = str(payload.get("risk_level") or "UNKNOWN").upper()

    content: dict[str, Any] = {
        "title": f"StatuteProof alert — {risk_level}",
        "risk_level": risk_level,
        "severity_line": _severity_line(risk_level, details),
        "rule": details.get("rule") or "",
        "matched_keywords": [str(k) for k in (details.get("matched_keywords") or [])],
        "matched_context": [str(c) for c in (details.get("matched_context") or [])],
        "source_name": _clean(payload.get("source_name") or ""),
        "url": str(payload.get("url") or ""),
        "market": _clean(payload.get("jurisdiction") or ""),
        "checked_at": _format_ts(payload.get("checked_at_utc") or payload.get("created_at") or ""),
        "excerpt": _build_excerpt(payload.get("added"), payload.get("removed")),
        "footer": FOOTER,
    }

    # Optional facts — included ONLY when actually detected (A3/F2).
    # F2: detected_facts are rule-extracted from the ADDED delta with matched
    # spans. A deadline line renders ONLY from a real detection — an
    # AI-supplied deadline with no detected span is not rendered (truth over
    # boilerplate; docs/signal/BUILD_BACKLOG.md F2).
    facts = [f for f in (payload.get("detected_facts") or []) if str(f.get("value") or "").strip()]
    if facts:
        from app.detected_facts import format_facts_lines
        content["detected_facts"] = facts
        content["facts_lines"] = format_facts_lines(facts)
        deadline_values = [f["value"] for f in facts if f.get("kind") == "deadline"]
        if deadline_values:
            content["deadline"] = _clean("; ".join(deadline_values))
    if payload.get("urgency"):
        content["urgency"] = _clean(payload["urgency"])
    entities = [e for e in (payload.get("affected_entities") or []) if str(e).strip()]
    if entities:
        content["affected"] = ", ".join(_clean(e) for e in entities[:4])
    action = _clean(payload.get("business_action_required") or "")
    if action:
        content["action"] = action

    # Summary: prefer an actual analysis summary, else the (now truthful)
    # rule reason — but only when indicator detail exists to back it (A4).
    summary = _clean(payload.get("executive_summary") or "")
    if not summary and details.get("matched_keywords"):
        summary = _clean(details.get("reason") or payload.get("risk_reason") or "")
    if summary:
        content["summary"] = summary
    return content


def render_telegram(content: dict[str, Any]) -> str:
    """Telegram Markdown rendering. Only present fields are rendered."""
    lines = [f"🚨 *{content['title']}*", ""]
    lines.append(f"*Severity:* {content['severity_line']}")
    if content.get("source_name"):
        source = content["source_name"]
        if content.get("market"):
            source += f" ({content['market']})"
        lines.append(f"*Source:* {source}")
    if content.get("checked_at"):
        lines.append(f"*Checked:* {content['checked_at']}")
    if content.get("excerpt"):
        lines.append(f"*What changed (excerpt):*\n{content['excerpt']}")
    if content.get("summary"):
        lines.append(f"*Summary:* {content['summary']}")
    if content.get("facts_lines"):
        lines.append("*Detected in this change:*")
        lines.extend(f"• {fl}" for fl in content["facts_lines"])
    if content.get("deadline"):
        lines.append(f"*Deadline stated in source:* {content['deadline']}")
    if content.get("urgency"):
        lines.append(f"*Urgency:* {content['urgency']}")
    if content.get("affected"):
        lines.append(f"*Affected:* {content['affected']}")
    if content.get("action"):
        lines.append(f"*Action:* {content['action']}")
    lines.append(f"\n🔗 {content['url']}")
    lines.append(f"_{content['footer']}_")
    return "\n".join(lines)


def render_markdown(content: dict[str, Any]) -> str:
    """Markdown rendering shared by the alert draft file and alert emails."""
    lines = [f"## {content['title']}", ""]
    lines.append(f"**Severity:** {content['severity_line']}")
    if content.get("source_name"):
        source = content["source_name"]
        if content.get("market"):
            source += f" ({content['market']})"
        lines.append(f"**Source:** {source}")
    if content.get("checked_at"):
        lines.append(f"**Checked:** {content['checked_at']}")
    if content.get("excerpt"):
        lines.append("")
        lines.append("**What changed (excerpt):**")
        lines.append(f"> {content['excerpt']}")
    if content.get("summary"):
        lines.append("")
        lines.append(f"**Summary:** {content['summary']}")
    if content.get("facts_lines"):
        lines.append("")
        lines.append("**Detected in this change:**")
        lines.extend(f"- {fl}" for fl in content["facts_lines"])
    if content.get("deadline"):
        lines.append(f"**Deadline stated in source:** {content['deadline']}")
    if content.get("urgency"):
        lines.append(f"**Urgency:** {content['urgency']}")
    if content.get("affected"):
        lines.append(f"**Affected:** {content['affected']}")
    if content.get("action"):
        lines.append(f"**Action:** {content['action']}")
    lines.append("")
    lines.append(f"Proof URL: {content['url']}")
    lines.append("")
    lines.append(f"_{content['footer']}_")
    return "\n".join(lines)
