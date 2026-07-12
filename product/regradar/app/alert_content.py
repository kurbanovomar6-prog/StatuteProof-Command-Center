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

import re
from datetime import datetime, timezone
from typing import Any

from app.client_profiles import _norm_topic, source_metadata_for_alert
from app.text_quality import strip_unreadable_chars, unreadable_ratio

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
    """Collapse whitespace; fix double periods (defect A5).

    Only collapses runs of *actual adjacent* periods (``..`` -> ``.``); a
    literal ellipsis character (``…``) is left untouched. The loop condition
    and the mutation must operate on the same string, otherwise input such as
    ``.….`` (period-ellipsis-period, no adjacent ``..``) spins forever: the
    ``…``-stripped view reads ``..`` (condition true) while ``out`` itself
    never changes (defect A5 hang fix).
    """
    out = " ".join(str(text or "").split())
    while ".." in out:
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


# A diff chunk this saturated with unreadable characters is not
# human-readable (binary or mis-decoded source body) — showing it to a
# customer is worse than saying plainly that it could not be rendered.
# Character classification is shared with the adapter quality gate:
# see app/text_quality.py.
_UNREADABLE_CHUNK_RATIO = 0.05

_UNREADABLE_EXCERPT_NOTE = (
    "The changed content could not be rendered as readable text "
    "(binary or improperly encoded source data). Verify the source page "
    "directly and review the stored evidence record."
)

_OMITTED_CONTENT_NOTE = "(Some changed content was not machine-readable and was omitted.)"

# Telegram renders alerts with parse_mode=Markdown; these metacharacters in
# page-derived text could inject live links or corrupt message formatting.
# Stripped (not escaped) to match the house pattern in telegram.py _safe().
_MARKDOWN_METACHARS = str.maketrans("", "", "*_`[]")


def _build_excerpt(added: list | None, removed: list | None, cap: int = _EXCERPT_CAP) -> str:
    """
    Capped excerpt of the real diff: additions first, then removals.

    Chunks saturated with unreadable characters are dropped; surviving
    chunks are stripped of stray unreadable bytes and Markdown
    metacharacters. The cap bounds the FINAL string, including any
    appended omission note.
    """
    parts: list[str] = []
    dropped_unreadable = False
    for prefix, chunks in (("+", added or []), ("−", removed or [])):
        for chunk in chunks:
            text = _clean(chunk)
            if not text:
                continue
            if unreadable_ratio(text) > _UNREADABLE_CHUNK_RATIO:
                dropped_unreadable = True
                continue
            text = strip_unreadable_chars(text).translate(_MARKDOWN_METACHARS)
            if text.strip():
                parts.append(f"{prefix} {text}")
    if not parts:
        return _UNREADABLE_EXCERPT_NOTE if dropped_unreadable else ""
    excerpt = "  ".join(parts)
    budget = cap - (len(_OMITTED_CONTENT_NOTE) + 2 if dropped_unreadable else 0)
    if len(excerpt) > budget:
        excerpt = excerpt[: budget - 1].rstrip() + "…"
    if dropped_unreadable:
        excerpt += f"  {_OMITTED_CONTENT_NOTE}"
    return excerpt


# ── Headline (front-loaded, factual, bounded) ────────────────────────────────
# The alert title StatuteProof generates. Shape: "[Regulator] [source]: what
# changed — [date]". It states a FACT (a monitored change was detected on a
# recorded check) and is deliberately NOT a severity/priority or legal-conclusion
# label — the review-priority band carries urgency framing. Built only from
# grounded fields (source name, the deterministic regulator code, the recorded
# timestamp); nothing is fabricated.
_HEADLINE_MAX = 120
_HEADLINE_TAIL = ": monitored change detected"
# Safe fixed title used when no source name is available, or when the assembled
# headline (which embeds source-controlled text) trips the forbidden-claims
# guard. Carries no legal-severity label.
_FALLBACK_TITLE = "StatuteProof alert — monitored change detected"


def _headline(payload: dict[str, Any], checked_at: str) -> str:
    """Front-loaded, factual alert headline; guarded, bounded, never fabricated."""
    source_name = _clean(payload.get("source_name") or "").translate(_MARKDOWN_METACHARS).strip()
    if not source_name:
        return _FALLBACK_TITLE
    from app.regulator_map import resolve_regulator

    regulator = resolve_regulator(
        {
            "source_id": payload.get("source_id"),
            "source_name": source_name,
            "url": payload.get("url"),
        }
    )
    # Prefix the regulator code only when the source name does not already carry
    # it, so a "VARA Rulebook" source is not rendered "VARA — VARA Rulebook".
    prefix = ""
    if regulator and regulator != "OTHER" and regulator.lower() not in source_name.lower():
        prefix = f"{regulator} — "
    date_suffix = f" — {checked_at}" if checked_at else ""
    subject = f"{prefix}{source_name}"
    room = _HEADLINE_MAX - len(_HEADLINE_TAIL) - len(date_suffix)
    if len(subject) > room:
        subject = subject[: max(0, room - 1)].rstrip() + "…"
    headline = f"{subject}{_HEADLINE_TAIL}{date_suffix}"
    # Source name is source-controlled free text; never let a headline that trips
    # the forbidden-claims guard ship (the final-bytes guard is the backstop).
    if _contains_forbidden(headline):
        return _FALLBACK_TITLE
    return headline


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


# ── "Does this affect me?" impact tag (LIGHT — not an RTM platform) ──────────
# When the matched source's topics intersect the customer's profile topics we
# add a short, monitoring-info impact tag. It is strictly additive: with no
# profile, no topics_in_scope, no topic overlap, or no readable diff excerpt,
# nothing is emitted and the alert body is unchanged. Topic slugs are the same
# ones scored in app/client_profiles.py and normalized with the SAME helper, so
# the two layers can never disagree on what a topic is.
_TOPIC_LABELS = {
    "aml_cft": "AML/CFT",
    "suspicious_transactions": "suspicious transactions",
    "crypto_vasp": "VASP / virtual assets",
    "custody": "custody",
    "exchange": "exchange",
    "brokerage": "brokerage",
    "licensing": "licensing",
    "commercial_licensing": "commercial licensing",
    "payments": "payments",
    "stored_value": "stored value",
    "reporting": "reporting",
    "deadlines": "deadlines",
    "banking": "banking",
    "financial_services": "financial services",
    "securities": "securities",
    "funds": "funds",
    "consultations": "consultations",
    "enforcement": "enforcement",
    "guidance": "guidance",
    "data_protection": "data protection",
    "tax": "tax",
    "vat": "VAT",
    "corporate_tax": "corporate tax",
    "excise": "excise",
    "capital_markets": "capital markets",
    "public_companies": "public companies",
    "legislation": "legislation",
    "decrees": "decrees",
    "difc_laws": "DIFC laws",
    "legal_framework": "legal framework",
    "company_law": "company law",
    "beneficial_ownership": "beneficial ownership",
    "finance": "finance",
    "fiscal_policy": "fiscal policy",
}

# Keep the tag readable: show at most this many topic labels, then "(+N more)".
_IMPACT_TOPIC_CAP = 4


def _topic_label(slug: str) -> str:
    return _TOPIC_LABELS.get(slug, slug.replace("_", " "))


def _contains_forbidden(text: str) -> bool:
    """Reuse the single forbidden-phrase guard (app/legal_safety).

    The shared guard neutralizes the product's fixed disclaimers before
    scanning, so the mandatory footer ("Monitoring information only. Not legal
    advice.") never self-trips while any AFFIRMATIVE banned claim — in an AI
    free-text field or a source-derived excerpt — still trips it.
    """
    from app.legal_safety import contains_forbidden_claim

    return contains_forbidden_claim(text)


# SF-3 grounding: prefix for an AI obligation/deadline assertion the diff does
# not back with a rule-detected fact. Kept short and unmistakable.
_UNVERIFIED_LABEL = "AI-generated, unverified: "

# Strong obligation / deadline language. When AI free text uses any of these AND
# no structured fact was detected in the delta, the assertion is not grounded in
# the evidence and must be labelled rather than presented as fact.
_OBLIGATION_TERMS = (
    "deadline",
    "no later than",
    "due by",
    "due on",
    "must ",
    "shall ",
    "required to",
    "obligation to",
    "effective date",
    "comes into force",
    "enters into force",
    "penalty of",
    "fine of",
    "within 30 days",
    "within 60 days",
    "within 90 days",
)

# A bare four-digit year in obligation-shaped text (e.g. "by 2026") is also a
# concrete, checkable assertion.
_YEAR_RE = re.compile(r"\b20\d{2}\b")


def _asserts_ungrounded_obligation(text: str) -> bool:
    """True if free text asserts a concrete obligation/deadline (caller has
    already established there are no detected facts to back it)."""
    low = str(text or "").lower()
    if low.startswith(_UNVERIFIED_LABEL.lower()):
        return False  # already labelled
    if any(term in low for term in _OBLIGATION_TERMS):
        return True
    # "by <year>" / "before <year>" style deadline assertions.
    if _YEAR_RE.search(low) and any(w in low for w in (" by ", "before ", "no later")):
        return True
    return False


def _build_impact(
    payload: dict[str, Any],
    client_profile: dict[str, Any] | None,
    excerpt: str,
) -> dict[str, Any] | None:
    """Emit a per-customer impact tag when source topics overlap profile topics.

    Returns ``None`` (no tag, unchanged alert) whenever the feature does not
    apply: no profile, no ``topics_in_scope``, no topic overlap, or — critically
    for evidence-grounding — no real, readable diff excerpt to point the reader
    at. The "what changed" reference is the SAME ``excerpt`` already built from
    the actual diff; nothing here asserts a change that the diff does not show.
    """
    if not client_profile:
        return None
    profile_topics = {
        _norm_topic(t) for t in (client_profile.get("topics_in_scope") or []) if str(t).strip()
    }
    if not profile_topics:
        return None

    source_meta = source_metadata_for_alert(payload)
    source_topics = {
        _norm_topic(t) for t in (source_meta.get("topics") or []) if str(t).strip()
    }
    matched = sorted(source_topics & profile_topics)
    if not matched:
        return None

    # Evidence-grounding gate: the impact line tells the reader to "review the
    # excerpt", so it may only be emitted when a real, readable excerpt exists.
    # No diff (or an unreadable one) → no impact claim.
    if not excerpt or excerpt == _UNREADABLE_EXCERPT_NOTE:
        return None

    labels = [_topic_label(t) for t in matched]
    shown = labels[:_IMPACT_TOPIC_CAP]
    extra = len(labels) - len(shown)
    topic_str = ", ".join(shown)
    if extra:
        topic_str += f" (+{extra} more)"

    tag = f"May affect: {topic_str}"
    line = (
        f"This change may be relevant to your {topic_str}; "
        "review the excerpt and source."
    )

    # Fail safe: never surface an impact tag that trips the forbidden-claims
    # guard (the phrasing is fixed and safe, but the guard is authoritative).
    if _contains_forbidden(tag) or _contains_forbidden(line):
        return None

    return {
        "impact_tag": tag,
        "impact_line": line,
        "impact_topics": matched,
        # The "what changed" evidence is the real diff excerpt itself — carried
        # verbatim, never re-summarized or fabricated.
        "impact_what_changed": excerpt,
    }


def impact_tag_for_delivery(
    match: dict[str, Any],
    recipient_profile: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Per-recipient impact tag for a routing/digest match (customer send path).

    Adapts a routing match + a customer profile onto the shared ``_build_impact``
    contract so the SAME evidence-grounded, guard-checked tag reaches a real
    recipient (this is the piece that was dead code): the recipient's topics
    become ``topics_in_scope``, and the match's carried real diff excerpt is the
    evidence-grounding gate. Accepts either a routing profile (``topics``) or a
    client profile (``topics_in_scope``). Returns ``None`` — unchanged output —
    whenever the recipient has no profile/topics, the source topics do not
    intersect, or there is no readable diff excerpt to point the reader at.
    """
    if not recipient_profile:
        return None
    topics = recipient_profile.get("topics_in_scope")
    if topics is None:
        topics = recipient_profile.get("topics")
    payload = {
        "source_id": match.get("source_id"),
        "source_name": match.get("source_name"),
        "change_type": match.get("change_type"),
    }
    excerpt = str(match.get("diff_excerpt") or "")
    return _build_impact(payload, {"topics_in_scope": topics or []}, excerpt)


def build_alert_content(
    payload: dict[str, Any],
    client_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build channel-independent alert content from a pipeline alert payload.

    ``client_profile`` is optional. When supplied (a customer whose
    ``topics_in_scope`` overlap the source's topics), a "Does this affect me?"
    impact tag is added. Omitting it — the default — leaves the alert body
    byte-for-byte unchanged.
    """
    details = payload.get("risk_details") or {}
    risk_level = str(payload.get("risk_level") or "UNKNOWN").upper()
    checked_at = _format_ts(payload.get("checked_at_utc") or payload.get("created_at") or "")

    content: dict[str, Any] = {
        "title": _headline(payload, checked_at),
        "risk_level": risk_level,
        "severity_line": _severity_line(risk_level, details),
        "rule": details.get("rule") or "",
        "matched_keywords": [str(k) for k in (details.get("matched_keywords") or [])],
        "matched_context": [str(c) for c in (details.get("matched_context") or [])],
        "source_name": _clean(payload.get("source_name") or ""),
        "url": str(payload.get("url") or ""),
        "market": _clean(payload.get("jurisdiction") or ""),
        "checked_at": checked_at,
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

    # SF-1 legal-safety: the summary / action / affected fields are model- or
    # source-controlled free text (AI executive_summary, business_action, or an
    # echoed source string). They can carry a forbidden claim — a hallucination
    # or a prompt-injected instruction from an adversarial source. Drop any
    # offending field (truth over boilerplate); for the summary, fall back to
    # the rule-based reason when that reason is itself clean and backed by a
    # matched indicator. The final-bytes guard at each send boundary is the
    # authoritative backstop; this keeps a single bad field from holding the
    # whole alert while never letting the bad field ship.
    if content.get("summary") and _contains_forbidden(content["summary"]):
        fallback = ""
        if details.get("matched_keywords"):
            candidate = _clean(details.get("reason") or payload.get("risk_reason") or "")
            if candidate and not _contains_forbidden(candidate):
                fallback = candidate
        if fallback:
            content["summary"] = fallback
        else:
            content.pop("summary", None)
    if content.get("action") and _contains_forbidden(content["action"]):
        content.pop("action", None)
    if content.get("affected") and _contains_forbidden(content["affected"]):
        content.pop("affected", None)

    # SF-3 grounding gate: an AI summary / action that asserts a concrete
    # obligation or deadline the diff does not back (no rule-detected fact in
    # the delta) is not verified StatuteProof content. Reuse the detected_facts
    # grounding pattern — the alert already refuses an AI deadline with no
    # detected span — and label the free-text field "AI-generated, unverified"
    # so an unbacked obligation is never presented as an established fact.
    if not facts:
        if content.get("summary") and _asserts_ungrounded_obligation(content["summary"]):
            content["summary"] = _UNVERIFIED_LABEL + content["summary"]
        if content.get("action") and _asserts_ungrounded_obligation(content["action"]):
            content["action"] = _UNVERIFIED_LABEL + content["action"]

    # Additive per-customer impact tag (no-op when it does not apply).
    impact = _build_impact(payload, client_profile, content["excerpt"])
    if impact:
        content.update(impact)
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
    if content.get("impact_tag"):
        lines.append(f"*{content['impact_tag']}*")
        lines.append(f"_{content['impact_line']}_")
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
    if content.get("impact_tag"):
        lines.append("")
        lines.append(f"**{content['impact_tag']}**")
        lines.append(content["impact_line"])
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
