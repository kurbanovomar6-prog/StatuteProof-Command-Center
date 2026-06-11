"""
services/delta_analyzer.py — LLM-driven regulatory document delta analysis
                             and Telegram dispatch.

Triggered when a new version of an existing НПА is detected by the scraper.
Outputs structured DeltaAnalysis: critical changes, impact level, 2-sentence
compliance action brief.

Telegram dispatcher is synchronous (plain httpx POST) — no async framework
overhead inside Celery prefork workers.
"""
from __future__ import annotations

import logging
from typing import Literal

import httpx
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

_FLAG  = {"RU": "🇷🇺", "KZ": "🇰🇿", "AZ": "🇦🇿", "BY": "🇧🇾", "UZ": "🇺🇿"}
_RISK  = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
_RISK_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


# ── Structured output schema ──────────────────────────────────────────────────

class DeltaAnalysis(BaseModel):
    critical_changes: list[str] = Field(
        description=(
            "List of specific regulatory changes: clauses added/removed, "
            "penalty thresholds revised, new obligations introduced. "
            "Each item is one concrete change, max 120 chars."
        )
    )
    impact_level: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="HIGH=immediate action required, MEDIUM=planning needed, LOW=informational"
    )
    business_action_required: str = Field(
        description=(
            "Exactly 2 sentences. Sentence 1: what the compliance team must do. "
            "Sentence 2: by when or under what condition."
        )
    )


# ── Delta analysis ────────────────────────────────────────────────────────────

_SYSTEM = (
    "You are a senior regulatory compliance analyst for CIS financial markets "
    "(Russia CBR, Kazakhstan NBK, Azerbaijan CBAR, Belarus NBRB, Uzbekistan CBU). "
    "Compare two versions of a regulatory document summary and produce a structured "
    "change brief. Focus only on legally material differences: changed penalties, "
    "new reporting obligations, revised thresholds, added/removed articles. "
    "Ignore stylistic rewrites and punctuation changes."
)


def analyze_delta(old_summary: str, new_summary: str) -> DeltaAnalysis | None:
    """
    Call gpt-4o-mini via instructor to compare two regulatory summaries.
    Returns None on any failure — caller logs and continues without blocking.
    """
    if not old_summary.strip() or not new_summary.strip():
        return None
    if old_summary.strip() == new_summary.strip():
        return None

    try:
        import instructor
        from openai import OpenAI

        client = instructor.from_openai(OpenAI())
        return client.chat.completions.create(
            model          = "gpt-4o-mini",
            response_model = DeltaAnalysis,
            max_tokens     = 600,
            max_retries    = 1,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {
                    "role": "user",
                    "content": (
                        f"PREVIOUS VERSION:\n{old_summary[:2_500]}\n\n"
                        f"NEW VERSION:\n{new_summary[:2_500]}\n\n"
                        "Identify all material regulatory changes between these two versions."
                    ),
                },
            ],
        )
    except Exception as exc:
        exc_type = type(exc).__name__
        log.warning("delta_analyzer: LLM [%s] — %s", exc_type, str(exc)[:120])
        return None


# ── Telegram HTTP dispatcher ──────────────────────────────────────────────────

def send_telegram(
    token:          str,
    chat_id:        str,
    text:           str,
    parse_mode:     str  = "HTML",
    disable_preview: bool = True,
) -> bool:
    """
    Synchronous Telegram sendMessage via plain httpx POST.
    No async overhead — safe to call from Celery prefork workers.
    Returns True on success, False on any failure (already logged).
    """
    if not token or not chat_id or not text:
        return False

    url     = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id":                  chat_id,
        "text":                     text[:4_096],       # Telegram hard cap
        "parse_mode":               parse_mode,
        "disable_web_page_preview": disable_preview,
    }
    try:
        r = httpx.post(url, json=payload, timeout=15)
        if r.status_code != 200:
            log.warning("telegram: HTTP %d chat=%s — %s", r.status_code, chat_id, r.text[:100])
            return False
        return True
    except Exception as exc:
        log.warning("telegram: send failed chat=%s — %s", chat_id, str(exc)[:80])
        return False


# ── Message formatters ────────────────────────────────────────────────────────

def format_digest(
    regulations:   list[dict],
    dashboard_url: str = "",
    header:        str = "RegRadar Compliance Alert",
) -> str:
    """
    Format up to 6 regulation dicts into an HTML Telegram digest.
    Fields used: jurisdiction, critical_level, title, summary.
    """
    lines: list[str] = [f"<b>🔔 {header}</b>\n"]

    for r in regulations[:6]:
        flag  = _FLAG.get(r.get("jurisdiction", ""), "🌐")
        emoji = _RISK.get(r.get("critical_level", ""), "⚪")
        title = (r.get("title") or "")[:80]
        summ  = (r.get("summary") or "")[:180]

        lines.append(f"{flag} <b>{r.get('jurisdiction', '')}  {emoji} {r.get('critical_level', '')}</b>")
        lines.append(f"<b>{title}</b>")
        if summ:
            lines.append(f"<i>{summ}…</i>")
        lines.append("")

    if dashboard_url:
        lines.append(f'<a href="{dashboard_url}">→ Open RegRadar Dashboard</a>')

    return "\n".join(lines)


def format_delta_alert(
    regulation:    dict,
    delta:         DeltaAnalysis,
    dashboard_url: str = "",
) -> str:
    """Format a single version-change event as a premium Telegram alert."""
    flag  = _FLAG.get(regulation.get("jurisdiction", ""), "🌐")
    emoji = _RISK.get(delta.impact_level, "⚪")
    title = (regulation.get("title") or "")[:80]

    lines = [
        "<b>⚡ RegRadar — Version Change Detected</b>",
        "",
        f"{flag} <b>{regulation.get('jurisdiction', '')}</b>  "
        f"{emoji} <b>{delta.impact_level} IMPACT</b>",
        f"<b>{title}</b>",
        "",
        "<b>Material Changes:</b>",
    ]
    for change in delta.critical_changes[:5]:
        lines.append(f"• {change[:120]}")

    lines += [
        "",
        "<b>Compliance Action Required:</b>",
        f"<i>{delta.business_action_required}</i>",
    ]
    if dashboard_url:
        lines += ["", f'<a href="{dashboard_url}">→ Review in RegRadar</a>']

    return "\n".join(lines)
