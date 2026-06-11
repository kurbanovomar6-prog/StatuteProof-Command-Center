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

logger = logging.getLogger(__name__)

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
You are a senior regulatory compliance analyst covering banks, fintechs, \
payment providers, virtual asset service providers (VASPs), and regulated \
financial institutions operating under UAE regulators including CBUAE, VARA, \
DFSA, ADGM/FSRA, UAE FIU, and the Ministry of Finance.

You read regulatory change text and produce a structured compliance brief \
for the institution's compliance team.  Do NOT rely on keyword matching alone \
— understand the legal and operational meaning of the change.

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
  "risk_level": "LOW" | "MEDIUM" | "HIGH",
  "executive_summary": "2-3 sentences: what changed and why it matters for regulated entities",
  "business_action_required": "one concrete action the compliance team must take, \
or No immediate action required for LOW risk",
  "reason": "concise explanation of risk_level based on substance",
  "affected_entities": ["list of entity types; empty list if unclear"],
  "urgency": "low" | "medium" | "high",
  "deadline": "explicit date if stated, or null",
  "semantic_findings": {{
    "new_obligation": true | false,
    "deadline_detected": true | false,
    "reporting_required": true | false,
    "licensing_impact": true | false,
    "enforcement_exposure": true | false,
    "operational_impact": "none" | "low" | "medium" | "high",
    "materiality": "informational" | "low" | "material" | "critical"
  }},
  "confidence": "low" | "medium" | "high",
  "review_required": true | false,
  "review_reason": "brief explanation if review_required is true, otherwise empty string"
}}\
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
    if not parts:
        return ""
    return "\n".join(parts) + "\n\n"


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

    conf = str(data.get("confidence", "medium")).lower()
    data["confidence"] = conf if conf in ("low", "medium", "high") else "medium"

    data["review_required"] = bool(data.get("review_required", False))
    data["review_reason"]   = str(data.get("review_reason", "")).strip()

    return data


def _fallback_brief(change_text: str, metadata: dict, error: str) -> dict:
    """
    Rule-based fallback brief produced entirely offline.
    Uses app.risk.analyze_risk() with a synthetic diff dict.
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

    return {
        "risk_level":               risk_level,
        "executive_summary":        "Regulatory change detected. AI analysis unavailable — rule-based assessment applied.",
        "business_action_required": "Review the source text manually and assess compliance impact.",
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

    try:
        client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model      = _MODEL,
            max_tokens = 900,
            system     = _SYSTEM,
            messages   = [{"role": "user", "content": user_prompt}],
        )
        raw    = message.content[0].text
        parsed = _parse_ai_response(raw)

        if parsed is None:
            return _fallback_brief(truncated, metadata, "AI returned unparseable JSON")

        urgency_raw  = parsed.get("urgency", "medium")
        mat_raw      = parsed.get("semantic_findings", {}).get("materiality", "informational")

        brief = {
            **parsed,
            "urgency":        _URGENCY_MAP.get(urgency_raw, "unclear"),
            "urgency_raw":    urgency_raw,
            "materiality":    _MATERIALITY_MAP.get(mat_raw, "unclear"),
            "materiality_raw": mat_raw,
            "source_language": metadata.get("source_language", "unknown"),
            "output_language": output_language,
            "ai_used":         True,
            "fallback_used":   False,
            "model":           _MODEL,
            "error":           None,
        }

        logger.info(
            "ai_brief: OK — risk=%s confidence=%s urgency=%s materiality=%s",
            brief["risk_level"], brief["confidence"],
            brief["urgency"], brief["materiality"],
        )
        return brief

    except Exception as exc:
        logger.warning("ai_brief: AI call failed (%s: %s)", type(exc).__name__, exc)
        return _fallback_brief(truncated, metadata, f"{type(exc).__name__}: {exc}")
