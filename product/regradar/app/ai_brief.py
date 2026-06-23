"""
StatuteProof — AI Compliance Brief layer.

generate_ai_brief(change_text, metadata) -> dict

Accepts raw regulatory change text (not a diff) and returns a standardised
14-field compliance brief.  Falls back to rule-based scoring when AI is
unavailable.  Never raises.  Never writes to the database.  Never sends
Telegram alerts.

Urgency vocabulary (standardised)
----------------------------------
  AI value   →  brief value
  low        →  routine
  medium     →  soon
  high       →  immediate
  other      →  unclear

Materiality vocabulary (standardised from semantic_findings.materiality)
------------------------------------------------------------------------
  AI value       →  brief value
  informational  →  informational
  low            →  informational
  material       →  important
  critical       →  critical
  other          →  unclear
"""

from __future__ import annotations

import json
import logging
import time
from collections import deque
from threading import Lock

# parse_action_steps and derive_urgency_from_text are re-exported from ai.py so
# that ai_brief callers can use the same structured what_to_do utilities
# without duplicating logic.  The "import X as X" form is the Pyright-recognised
# re-export pattern and suppresses the "not accessed" diagnostic.
from app.ai import (  # noqa: F401
    derive_urgency_from_text as derive_urgency_from_text,
    parse_action_steps as parse_action_steps,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Soft rate guard — brief generation call budget
# ---------------------------------------------------------------------------
# Tracks AI call timestamps within a rolling window.  Log a warning when the
# limit is exceeded but do NOT block — briefs are high-value and should never
# be silently dropped.  Hard blocking belongs at the API-key / billing layer.
_BRIEF_RATE_LIMIT  = 20          # max generations per window
_BRIEF_RATE_WINDOW = 3_600       # 1 hour in seconds
_brief_call_times: deque[float] = deque()
_brief_call_lock   = Lock()


def _check_brief_rate_limit() -> None:
    """
    Soft guard: warn if more than _BRIEF_RATE_LIMIT AI calls have been made
    in the last _BRIEF_RATE_WINDOW seconds.  Never raises or blocks.
    """
    now = time.monotonic()
    with _brief_call_lock:
        # Evict timestamps older than the window
        while _brief_call_times and now - _brief_call_times[0] > _BRIEF_RATE_WINDOW:
            _brief_call_times.popleft()
        _brief_call_times.append(now)
        count = len(_brief_call_times)

    if count > _BRIEF_RATE_LIMIT:
        logger.warning(
            "ai_brief: soft rate limit exceeded — %d brief generations in the last "
            "%ds (limit: %d). Consider throttling the pipeline or increasing the limit.",
            count, _BRIEF_RATE_WINDOW, _BRIEF_RATE_LIMIT,
        )

_MODEL              = "claude-haiku-4-5-20251001"
_MAX_TEXT_CHARS     = 6_000
_THIN_CONTENT_CHARS = 500

_URGENCY_MAP = {
    "low":    "routine",
    "medium": "soon",
    "high":   "immediate",
}

_MATERIALITY_MAP = {
    "informational": "informational",
    "low":           "informational",
    "material":      "important",
    "critical":      "critical",
}

_SYSTEM = """\
You are a UAE regulatory compliance intelligence analyst writing for MLROs and CCOs \
at VARA-licensed VASPs, DFSA-authorised firms, and ADGM-registered entities.

Your output must meet these standards:
1. SPECIFIC: Name the regulation, article, or section that changed — never say \
"the regulatory framework was updated" without citing what changed.
2. ACTIONABLE: Every HIGH or MEDIUM alert must contain one specific action the \
compliance officer should take, with a suggested timeframe.
3. CALIBRATED: Do not overclaim. If the change is a minor editorial update, say so. \
If it creates a new obligation, state exactly what the obligation is.
4. UAE-AWARE: VARA governs VASPs in Dubai mainland, DFSA governs DIFC firms, \
ADGM/FSRA governs Abu Dhabi Global Market firms. A VARA circular does not bind \
DFSA-regulated firms. Always specify which licence type is affected.
5. EVIDENCE-FIRST: Your analysis is based on a hash-verified diff from an official \
source. Never claim certainty beyond what the diff shows.

Risk level definitions:
  LOW    — purely informational; no new obligation; no deadline; no operational impact
  MEDIUM — possible regulatory relevance; clarification; moderate operational impact
  HIGH   — new or changed obligation; deadline; licensing/reporting/enforcement impact

Use qualified language: "may require", "appears to mandate", "likely affects".
Do NOT make definitive legal claims.  Do NOT overclaim certainty.\
"""

_USER_TEMPLATE = """\
Analyse the regulatory change text below and produce a compliance brief.

Output language: {output_language_upper} ({output_language})
{meta_block}
REGULATORY CHANGE TEXT:
{change_text}

Respond with ONLY a valid JSON object — no markdown fences, no text outside the JSON.

Required JSON format (all keys mandatory):
{{
  "risk_level": "HIGH" | "MEDIUM" | "LOW",
  "confidence": 0.0,
  "executive_summary": "2-3 sentences: what changed, why it matters, who is affected. \
Name the specific regulation or article where possible.",
  "business_action_required": "one concrete action the compliance team must take. \
For LOW risk: No immediate action required.",
  "reason": "concise explanation of risk_level based on substance",
  "affected_entities": ["list of entity types e.g. VARA VASP, DFSA authorised firm"],
  "specific_obligation": "exact new obligation if any — empty string if none",
  "implementation_deadline": "specific date or timeframe if mentioned — \
'Not specified in source' if absent",
  "suggested_timeframe": "e.g. within 5 business days, before end of quarter",
  "licence_scope": "which UAE licence types are affected",
  "regulatory_body": "VARA | CBUAE | DFSA | ADGM | UAEFIU | SCA | other",
  "change_type": "new_obligation | amended_requirement | enforcement_action | \
consultation | guidance | editorial",
  "urgency": "low" | "medium" | "high",
  "deadline": "explicit date if stated, or null",
  "semantic_findings": {{
    "new_obligation": true | false,
    "deadline_detected": true | false,
    "reporting_required": true | false,
    "licensing_impact": true | false,
    "enforcement_exposure": true | false,
    "operational_impact": "none" | "low" | "medium" | "high",
    "materiality": "informational" | "low" | "material" | "critical",
    "key_terms": ["list of key regulatory terms found"],
    "jurisdiction_signals": ["list of jurisdiction indicators found"],
    "obligation_signals": ["list of obligation indicators found"]
  }},
  "disclaimer_required": true,
  "monitoring_note": "any source quality or coverage limitation relevant to this alert",
  "review_required": true | false,
  "review_reason": "brief explanation if review_required is true, otherwise empty string"
}}\
"""

_USER_RETRY_SUFFIX = """\

Previous output failed quality check: {issues}.
Be more specific. Name the exact regulation, article, or section. \
State the exact obligation in the specific_obligation field. \
List the affected entity types explicitly in affected_entities.\
"""


def _build_meta_block(metadata: dict) -> str:
    parts: list[str] = []
    if metadata.get("source_name"):
        parts.append(f"Source: {metadata['source_name']}")
    if metadata.get("url"):
        parts.append(f"URL: {metadata['url']}")
    if metadata.get("jurisdiction"):
        parts.append(f"Jurisdiction: {metadata['jurisdiction']}")
    if metadata.get("category"):
        parts.append(f"Category: {metadata['category']}")
    if metadata.get("extraction_quality"):
        parts.append(f"Extraction quality: {metadata['extraction_quality']}")
    if metadata.get("extracted_chars") is not None:
        parts.append(f"Extracted chars: {metadata['extracted_chars']}")
    if metadata.get("change_status"):
        parts.append(f"Change status: {metadata['change_status']}")
    if metadata.get("limitations_notes"):
        parts.append(f"Limitations: {metadata['limitations_notes']}")
    if metadata.get("diff_summary"):
        parts.append(f"Diff summary: {metadata['diff_summary']}")
    if metadata.get("diff_excerpt"):
        parts.append(f"Key change excerpt:\n{metadata['diff_excerpt']}")
    if not parts:
        return ""
    return "\n".join(parts) + "\n\n"


# ---------------------------------------------------------------------------
# Regulator-specific action table
# ---------------------------------------------------------------------------
_REGULATOR_ACTIONS: dict[str, str] = {
    "VARA":   (
        "Review the VARA Broker-Dealer / relevant Rulebook sections changed against "
        "current VASP licensing controls, AML/CFT obligations, and internal policies. "
        "Escalate to MLRO and Legal if new obligations are identified."
    ),
    "CBUAE":  (
        "Review CBUAE circular or regulation changes against AML/CFT controls, "
        "consumer protection policies, and capital adequacy frameworks. "
        "File CBUAE notification if a reporting obligation is triggered."
    ),
    "DFSA":   (
        "Cross-reference DFSA rulebook module changes against DIFC authorised "
        "firm's regulatory permissions and compliance manual. "
        "Consult DFSA correspondence tracker and update PIB/GEN/AML module gap analysis."
    ),
    "ADGM":   (
        "Review ADGM/FSRA policy changes against ADGM Financial Services Regulations "
        "and firm's regulatory business plan. "
        "Assess impact on FSRA-issued Financial Services Permission and notify MLRO."
    ),
    "UAEFIU": (
        "Review UAE FIU guidance changes against current goAML reporting procedures "
        "and STR/SAR filing workflows. Update AML/CFT compliance manual if required."
    ),
    "SCA":    (
        "Review SCA regulatory changes against Securities and Commodities Law "
        "obligations, prospectus filing requirements, and licensed activity scope."
    ),
}

_SOURCE_ID_REGULATOR_MAP: dict[str, str] = {
    "vara":    "VARA",
    "dfsa":    "DFSA",
    "difc":    "DFSA",
    "cbuae":   "CBUAE",
    "adgm":    "ADGM",
    "fsra":    "ADGM",
    "uaefiu":  "UAEFIU",
    "sca":     "SCA",
}


def _regulator_from_metadata(metadata: dict) -> str:
    """
    Derive the primary regulator from metadata fields.
    Returns one of: VARA, DFSA, CBUAE, ADGM, UAEFIU, SCA, or empty string.
    """
    # Prefer explicit regulatory_body field if set
    if metadata.get("regulatory_body"):
        return str(metadata["regulatory_body"]).upper().strip()

    source_id = str(metadata.get("source_id") or "").lower()
    for fragment, regulator in _SOURCE_ID_REGULATOR_MAP.items():
        if fragment in source_id:
            return regulator

    source_name = str(metadata.get("source_name") or "").upper()
    for fragment, regulator in _SOURCE_ID_REGULATOR_MAP.items():
        if fragment in source_name.lower():
            return regulator

    return ""


def _build_diff_excerpt(metadata: dict) -> str:
    """
    Extract and format a short diff excerpt suitable for embedding in the brief.
    Returns a string of at most 500 chars, or empty string if no meaningful
    diff content is available.
    """
    # Caller may pre-compute and pass this in metadata
    if metadata.get("diff_excerpt"):
        excerpt = str(metadata["diff_excerpt"]).strip()
        return excerpt[:500]
    return ""


def _parse_ai_response(raw: str) -> dict | None:
    text = raw.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.warning("ai_brief: invalid JSON from model: %s — raw: %.200s", exc, raw)
        return None

    risk = str(data.get("risk_level", "LOW")).upper().strip()
    data["risk_level"] = risk if risk in ("LOW", "MEDIUM", "HIGH") else "LOW"

    data.setdefault("executive_summary",        "No summary provided.")
    data.setdefault("business_action_required", "No action specified.")
    data.setdefault("reason",                   "AI analysis completed.")
    data.setdefault("affected_entities",        [])
    if not isinstance(data["affected_entities"], list):
        data["affected_entities"] = []

    urg = str(data.get("urgency", "")).lower().strip()
    data["urgency"] = urg if urg in ("low", "medium", "high") else "medium"

    dl = data.get("deadline")
    data["deadline"] = (
        str(dl).strip()
        if dl and str(dl).strip().lower() not in ("null", "none", "")
        else None
    )

    sf = data.get("semantic_findings")
    if not isinstance(sf, dict):
        sf = {}
    sf.setdefault("new_obligation",       False)
    sf.setdefault("deadline_detected",    False)
    sf.setdefault("reporting_required",   False)
    sf.setdefault("licensing_impact",     False)
    sf.setdefault("enforcement_exposure", False)
    oi = str(sf.get("operational_impact", "none")).lower()
    sf["operational_impact"] = oi if oi in ("none", "low", "medium", "high") else "none"
    mat = str(sf.get("materiality", "informational")).lower()
    sf["materiality"] = mat if mat in ("informational", "low", "material", "critical") else "informational"
    for bool_key in ("new_obligation", "deadline_detected", "reporting_required",
                     "licensing_impact", "enforcement_exposure"):
        sf[bool_key] = bool(sf[bool_key])
    data["semantic_findings"] = sf

    # Confidence: accept float 0-1 or string low/medium/high
    raw_conf = data.get("confidence", "medium")
    try:
        conf_float = float(raw_conf)
        data["confidence"] = conf_float
    except (TypeError, ValueError):
        conf_str = str(raw_conf).lower()
        data["confidence"] = conf_str if conf_str in ("low", "medium", "high") else "medium"

    # New fields with safe defaults
    data.setdefault("specific_obligation",     "")
    data.setdefault("implementation_deadline", "Not specified in source")
    data.setdefault("suggested_timeframe",     "")
    data.setdefault("licence_scope",           "")
    data.setdefault("regulatory_body",         "")
    data.setdefault("change_type",             "")
    data.setdefault("disclaimer_required",     True)
    data.setdefault("monitoring_note",         "")

    sf = data["semantic_findings"]
    if not isinstance(sf.get("key_terms"), list):
        sf["key_terms"] = []
    if not isinstance(sf.get("jurisdiction_signals"), list):
        sf["jurisdiction_signals"] = []
    if not isinstance(sf.get("obligation_signals"), list):
        sf["obligation_signals"] = []

    data["review_required"] = bool(data.get("review_required", False))
    data["review_reason"]   = str(data.get("review_reason", "")).strip()

    return data


def _fallback_brief(change_text: str, metadata: dict, error: str) -> dict:
    """
    Rule-based fallback brief produced entirely offline.
    Uses app.risk.analyze_risk() with a synthetic diff dict.
    Enriched with diff excerpt and regulator-specific action when available.
    """
    try:
        from app.risk import analyze_risk
        diff = {"added": [change_text[:2000]], "removed": [], "modified_count": 0}
        risk_result = analyze_risk(diff)
        risk_level = risk_result.get("risk_level", "LOW")
        risk_reason = risk_result.get("reason", "Rule-based assessment.")
    except Exception as exc:
        logger.warning("ai_brief: fallback risk analysis failed: %s", exc)
        risk_level = "LOW"
        risk_reason = "Fallback risk assessment unavailable."

    urgency_raw = {"HIGH": "high", "MEDIUM": "medium", "LOW": "low"}.get(risk_level, "low")

    source_name = metadata.get("source_name") or metadata.get("url") or "the monitored source"
    regulator    = _regulator_from_metadata(metadata)
    diff_summary = metadata.get("diff_summary") or ""
    diff_excerpt = _build_diff_excerpt(metadata)
    change_type  = str(metadata.get("change_type") or "").replace("_", " ").title()

    # Build a more informative executive summary
    summary_parts: list[str] = []
    summary_parts.append(
        f"{'VARA' if regulator == 'VARA' else regulator or source_name} "
        f"regulatory change detected on {source_name}."
    )
    if change_type:
        summary_parts.append(f"Change classification: {change_type}.")
    if diff_summary:
        summary_parts.append(f"Scope: {diff_summary.rstrip('.')}.")
    if diff_excerpt:
        # Trim and quote the excerpt
        short_excerpt = diff_excerpt[:300].rstrip()
        if len(diff_excerpt) > 300:
            short_excerpt += "…"
        summary_parts.append(f'Excerpt from change: "{short_excerpt}"')
    if not diff_excerpt and change_text:
        # Fall back to a snippet of change_text
        excerpt = change_text[:200].strip()
        if len(change_text) > 200:
            excerpt += "…"
        summary_parts.append(f"Content sample: {excerpt}")
    summary_parts.append(f"Risk assessment: {risk_level}. {risk_reason}")
    exec_summary = " ".join(summary_parts)

    # Use regulator-specific action if available, else generic
    if regulator and regulator in _REGULATOR_ACTIONS:
        action = _REGULATOR_ACTIONS[regulator]
    else:
        action = (
            "Review the detected change against current compliance policies, "
            "internal controls, and regulatory obligations. "
            "Escalate to Legal or the MLRO if a new obligation is identified."
        )

    return {
        "risk_level":               risk_level,
        "executive_summary":        exec_summary,
        "business_action_required": action,
        "reason":                   risk_reason,
        "affected_entities":        [],
        "urgency":                  _URGENCY_MAP.get(urgency_raw, "unclear"),
        "urgency_raw":              urgency_raw,
        "deadline":                 None,
        "materiality":              "unclear",
        "materiality_raw":          "informational",
        "semantic_findings": {
            "new_obligation":       False,
            "deadline_detected":    False,
            "reporting_required":   False,
            "licensing_impact":     False,
            "enforcement_exposure": False,
            "operational_impact":   "none",
            "materiality":          "informational",
        },
        "confidence":               "low",
        "review_required":          True,
        "review_reason":            "AI unavailable — manual review required.",
        "source_language":          metadata.get("source_language", "unknown"),
        "output_language":          metadata.get("output_language", "en"),
        "ai_used":                  False,
        "fallback_used":            True,
        "model":                    None,
        "error":                    error,
    }


def _quality_check(brief: dict) -> list[str]:
    """
    STEP 1 quality gate — checks brief completeness before delivery.

    Returns a list of issue strings; empty list means the brief passes.
    """
    issues = []
    if len(brief.get("executive_summary", "")) < 100:
        issues.append("executive_summary too short — not specific enough")
    if brief.get("risk_level") == "HIGH" and not brief.get("specific_obligation"):
        issues.append("HIGH risk brief has no specific_obligation — unacceptable")
    if not brief.get("affected_entities"):
        issues.append("affected_entities is empty — who does this apply to?")
    if not brief.get("business_action_required"):
        issues.append("no business_action_required — brief has no value for MLRO")
    if (
        brief.get("implementation_deadline") in (None, "", "Not specified", "Not specified in source")
        and brief.get("risk_level") == "HIGH"
    ):
        issues.append(
            "HIGH risk brief has no deadline — must say 'not specified in source' explicitly"
        )
    return issues


def generate_ai_brief(
    change_text: str,
    metadata:    dict | None = None,
) -> dict:
    """
    Generate a standardised AI Compliance Brief for raw regulatory change text.

    Parameters
    ----------
    change_text : str
        The regulatory change text to analyse (not a diff — raw extracted text).
    metadata : dict | None
        Optional context: source_name, url, jurisdiction, category,
        source_language, output_language.

    Returns
    -------
    dict
        Standardised 14-field brief.  Always returns a valid dict — never raises.

    Brief fields
    ------------
    risk_level, executive_summary, business_action_required, reason,
    affected_entities, urgency (standardised), urgency_raw,
    deadline, materiality (standardised), materiality_raw,
    semantic_findings, confidence, review_required, review_reason,
    source_language, output_language,
    ai_used, fallback_used, model, error
    """
    if metadata is None:
        metadata = {}

    from app.config import ANTHROPIC_API_KEY, ENABLE_AI_ANALYSIS

    output_language = metadata.get("output_language", "en")
    if not output_language:
        output_language = "en"

    if not change_text or not change_text.strip():
        return _fallback_brief("", metadata, "Empty change text — nothing to analyse.")

    quality = str(metadata.get("extraction_quality", "")).upper()
    change_status = str(metadata.get("change_status", "")).upper()
    if quality in ("THIN", "FAILED") or change_status == "QUALITY_DROP":
        return {
            "risk_level":               "LOW",
            "executive_summary":        "Insufficient source detail for reliable automated summary. Manual validation or source adapter required.",
            "business_action_required": "Do not rely on automated summary. Review the official source manually or improve extraction before issuing a customer-facing brief.",
            "reason":                   f"Extraction quality={quality or 'unknown'}, change_status={change_status or 'unknown'}.",
            "affected_entities":        [],
            "urgency":                  "routine",
            "urgency_raw":              "low",
            "deadline":                 None,
            "materiality":              "informational",
            "materiality_raw":          "informational",
            "semantic_findings": {
                "new_obligation":      False,
                "deadline_detected":   False,
                "reporting_required":  False,
                "licensing_impact":    False,
                "enforcement_exposure": False,
                "operational_impact":  "unknown",
                "materiality":         "informational",
            },
            "confidence":          "low",
            "review_required":     True,
            "review_reason":       "Insufficient source detail for reliable automated summary. Manual validation or source adapter required.",
            "source_language":     metadata.get("source_language", "unknown"),
            "output_language":     metadata.get("output_language", "en"),
            "ai_used":             False,
            "fallback_used":       True,
            "thin_content":        quality == "THIN",
            "model":               None,
            "error":               "insufficient_extraction_quality",
        }

    # Thin-content guard — do not waste tokens or produce unreliable summary
    if len(change_text.strip()) < _THIN_CONTENT_CHARS:
        return {
            "risk_level":               "LOW",
            "executive_summary":        "Insufficient source detail for reliable summary. The extracted content is too short for confident analysis.",
            "business_action_required": "Manual source validation required. The source may be a listing page, navigation shell, or require a dedicated adapter.",
            "reason":                   f"Extracted content ({len(change_text.strip())} chars) is below the minimum threshold ({_THIN_CONTENT_CHARS} chars) for reliable AI analysis.",
            "affected_entities":        [],
            "urgency":                  "routine",
            "urgency_raw":              "low",
            "deadline":                 None,
            "materiality":              "informational",
            "materiality_raw":          "informational",
            "semantic_findings": {
                "new_obligation":      False,
                "deadline_detected":   False,
                "reporting_required":  False,
                "licensing_impact":    False,
                "enforcement_exposure": False,
                "operational_impact":  "none",
                "materiality":         "informational",
            },
            "confidence":          "low",
            "review_required":     True,
            "review_reason":       "Thin extraction — manual validation or adapter required.",
            "source_language":     metadata.get("source_language", "unknown"),
            "output_language":     metadata.get("output_language", "en"),
            "ai_used":             False,
            "fallback_used":       True,
            "thin_content":        True,
            "model":               None,
            "error":               "thin_content",
        }

    truncated = change_text[:_MAX_TEXT_CHARS]

    if not ENABLE_AI_ANALYSIS or not ANTHROPIC_API_KEY:
        reason = "ENABLE_AI_ANALYSIS is disabled" if not ENABLE_AI_ANALYSIS else "ANTHROPIC_API_KEY not set"
        return _fallback_brief(truncated, metadata, reason)

    try:
        import anthropic
    except ImportError:
        return _fallback_brief(truncated, metadata, "'anthropic' package not installed")

    meta_block = _build_meta_block(metadata)
    user_prompt = _USER_TEMPLATE.format(
        output_language       = output_language,
        output_language_upper = output_language.upper(),
        meta_block            = meta_block,
        change_text           = truncated,
    )

    # Soft rate guard — log warning if budget is exceeded; never blocks.
    _check_brief_rate_limit()

    try:
        client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model      = _MODEL,
            max_tokens = 1400,
            system     = _SYSTEM,
            messages   = [{"role": "user", "content": user_prompt}],
        )
        if message.stop_reason == "max_tokens":
            logger.warning("ai_brief: response truncated (max_tokens) — falling back")
            return _fallback_brief(truncated, metadata, "AI response truncated at max_tokens")

        # Extract text from the first content block safely — only TextBlock has .text
        raw = ""
        for _block in message.content:
            if isinstance(_block, anthropic.types.TextBlock):
                raw = _block.text
                break
        parsed = _parse_ai_response(raw)

        if parsed is None:
            return _fallback_brief(truncated, metadata, "AI returned unparseable JSON")

        def _assemble_brief(p: dict) -> dict:
            urgency_raw = p.get("urgency", "medium")
            mat_raw = p.get("semantic_findings", {}).get("materiality", "informational")
            return {
                **p,
                "urgency":         _URGENCY_MAP.get(urgency_raw, "unclear"),
                "urgency_raw":     urgency_raw,
                "materiality":     _MATERIALITY_MAP.get(mat_raw, "unclear"),
                "materiality_raw": mat_raw,
                "source_language": metadata.get("source_language", "unknown"),
                "output_language": output_language,
                "ai_used":         True,
                "fallback_used":   False,
                "model":           _MODEL,
                "error":           None,
            }

        brief = _assemble_brief(parsed)

        # ── STEP 1: Quality gate ─────────────────────────────────────────
        issues = _quality_check(brief)
        if issues:
            source_id = metadata.get("source_id") or metadata.get("url") or "unknown"
            for issue in issues:
                logger.warning("ai_brief: quality issue [%s]: %s", source_id, issue)

            retry_prompt = user_prompt + _USER_RETRY_SUFFIX.format(
                issues="; ".join(issues)
            )
            try:
                retry_msg = client.messages.create(
                    model      = _MODEL,
                    max_tokens = 1400,
                    system     = _SYSTEM,
                    messages   = [{"role": "user", "content": retry_prompt}],
                )
                if retry_msg.stop_reason != "max_tokens":
                    _retry_raw = ""
                    for _b in retry_msg.content:
                        if isinstance(_b, anthropic.types.TextBlock):
                            _retry_raw = _b.text
                            break
                    retry_parsed = _parse_ai_response(_retry_raw)
                    if retry_parsed is not None:
                        retry_issues = _quality_check(_assemble_brief(retry_parsed))
                        if not retry_issues:
                            brief = _assemble_brief(retry_parsed)
                            logger.info("ai_brief: retry passed quality gate [%s]", source_id)
                        else:
                            logger.warning(
                                "BRIEF_QUALITY_FAIL source_id=%s issues=%s",
                                source_id, retry_issues,
                            )
            except Exception as retry_exc:
                logger.warning("ai_brief: retry failed (%s)", retry_exc)

        logger.info(
            "ai_brief: OK — risk=%s confidence=%s urgency=%s materiality=%s",
            brief["risk_level"], brief["confidence"],
            brief["urgency"], brief["materiality"],
        )
        return brief

    except Exception as exc:
        logger.warning("ai_brief: AI call failed (%s: %s)", type(exc).__name__, exc)
        return _fallback_brief(truncated, metadata, f"{type(exc).__name__}: {exc}")
