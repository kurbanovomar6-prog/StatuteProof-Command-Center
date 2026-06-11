"""
AI compliance analysis layer — v11.

Semantic regulatory intelligence using Claude.

v11 additions vs v9
-------------------
• System prompt rebuilt: deep semantic analysis — substance over keywords.
• semantic_findings block added to JSON output:
    new_obligation, deadline_detected, reporting_required,
    licensing_impact, enforcement_exposure, operational_impact, materiality.
• confidence (low / medium / high) — reflects how certain the model is.
• review_required + review_reason now sourced from the AI, not the pipeline.
• max_tokens increased to 900 to accommodate the richer JSON output.

Fallback contract
-----------------
• Returns None on any failure (missing key, network error, bad JSON).
• Caller is responsible for falling back to rule-based scoring.
• Never raises.  Never crashes the pipeline.

Token budget
------------
• Max 20 added paragraphs, max 20 removed paragraphs.
• Each paragraph truncated to 400 characters.
• Keeps the prompt under ~9 000 tokens in the worst case.

Semantic examples (offline — no AI required)
--------------------------------------------
Example 1 — HIGH risk, high confidence:
  Text: "Financial institutions shall submit updated internal control
         documentation within 15 business days."
  Expected semantic_findings:
    new_obligation=True, deadline_detected=True, reporting_required=True,
    operational_impact="medium", materiality="material"
  Expected: risk_level=HIGH, confidence="high"

Example 2 — LOW risk, medium confidence:
  Text: "The regulator updated the website navigation menu."
  Expected semantic_findings:
    new_obligation=False, deadline_detected=False, reporting_required=False,
    operational_impact="none", materiality="informational"
  Expected: risk_level=LOW, confidence="medium"
"""

from __future__ import annotations

import json
import logging

from app.config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

_MAX_PARAS    = 20
_MAX_PARA_LEN = 400

_SYSTEM = """\
You are a senior regulatory compliance analyst specialising in banks, fintechs, \
payment companies, virtual asset service providers (VASPs), and regulated financial \
institutions across GCC, APAC, Turkey, Central Asia, and Caucasus priority markets, \
plus international regulatory bodies (FATF, BIS, Basel Committee).

Your task is to analyse the LEGAL, OPERATIONAL, and COMPLIANCE MEANING of \
regulatory text changes.

Do NOT rely solely on keyword matching. Understand whether the change:
- Creates new obligations for regulated entities
- Imposes deadlines or time-bound requirements
- Introduces new reporting, disclosure, or filing duties
- Affects licensing, registration, or authorisation
- Creates enforcement exposure, fines, or criminal liability
- Increases compliance workload significantly
- Clarifies or amends existing rules (possibly material even without new obligations)
- Is purely informational with no regulatory effect

Risk level definitions (semantic, not keyword-based):
  LOW    — purely informational update; no new obligation; no deadline; no operational \
impact; no reporting, licensing, or compliance change
  MEDIUM — possible regulatory relevance; clarification of existing rules; moderate \
operational impact; change may require review by compliance/legal; unclear materiality
  HIGH   — new or changed obligation; deadline or time-bound requirement; \
licensing/registration impact; reporting obligation; enforcement/penalty exposure; \
mandatory compliance action; material effect on banks, fintechs, payment providers, \
crypto/VASPs, or regulated entities

You read source text in English, Arabic, Turkish, Russian, Azerbaijani, Kazakh, Uzbek, \
Belarusian, or Malay when source excerpts contain those languages.
Write ALL output fields in the language specified by the caller.

Use qualified language: "may require", "appears to mandate", "likely affects", "suggests".
Do NOT make definitive legal claims. Do NOT overclaim certainty.
If evidence is ambiguous, lower confidence and note ambiguity in the reason field.\
"""

_USER_TEMPLATE = """\
A regulatory page has changed. Analyse ONLY the diff shown below.

Source URL: {url}
Detected source language: {source_language}
Required output language: {output_language_upper} ({output_language})
Rule-based pre-screening: {rule_risk} — {rule_reason}

ADDED PARAGRAPHS (new or modified content):
{added_text}

REMOVED PARAGRAPHS (deleted or replaced content):
{removed_text}

ANALYSIS INSTRUCTIONS:
1. Read the text carefully, understanding its legal and regulatory meaning.
2. Do NOT rely on keyword presence alone — analyse the substance.
3. Determine what obligations, deadlines, or requirements are created or changed.
4. Consider which entity types are affected (banks, fintechs, payment providers, VASPs, etc.).
5. Assess whether the change is material, informational, or ambiguous.
6. Set confidence based on how clear the evidence is:
   - high   = explicit obligation / deadline / requirement clearly stated
   - medium = implied or reasonably inferred; some ambiguity remains
   - low    = text is vague, translated poorly, or evidence is insufficient
7. If review_required is true, briefly explain why human review is needed.
8. Do NOT invent content not shown. Do NOT speculate about missing text.
9. If no deadline date is explicitly stated, set "deadline" to null.
10. If affected entities are unclear, return [].
11. Write ALL output fields in {output_language_upper}.

Respond with ONLY a valid JSON object — no markdown fences, no text outside the JSON.

Required JSON format (all keys mandatory):
{{
  "risk_level": "LOW" | "MEDIUM" | "HIGH",
  "executive_summary": "2-3 sentences: what changed and why it matters for regulated entities",
  "business_action_required": "one concrete action the compliance team must take, or No immediate action required for LOW",
  "reason": "concise explanation of why this risk_level was chosen based on substance not keywords",
  "source_language": "{source_language}",
  "output_language": "{output_language}",
  "affected_entities": ["list of entity types clearly mentioned or strongly implied; empty list if unclear"],
  "urgency": "low" | "medium" | "high",
  "deadline": "explicit date string if stated in the text, or null",
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


def _truncate_paras(paras: list[str]) -> str:
    """Format up to _MAX_PARAS paragraphs, each capped at _MAX_PARA_LEN chars."""
    if not paras:
        return "(none)"
    selected = paras[:_MAX_PARAS]
    lines = []
    for i, p in enumerate(selected, 1):
        text = p[:_MAX_PARA_LEN] + ("…" if len(p) > _MAX_PARA_LEN else "")
        lines.append(f"{i}. {text}")
    return "\n".join(lines)


def _parse_response(raw: str) -> dict | None:
    """
    Extract and validate JSON from the model response.

    Handles clean JSON strings and responses wrapped in ```json fences.
    Normalises and sets safe defaults for all required fields.
    """
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
        logger.warning("AI returned invalid JSON: %s — raw: %.200s", exc, raw)
        return None

    # Normalise risk_level
    risk = str(data.get("risk_level", "LOW")).upper().strip()
    if risk not in ("LOW", "MEDIUM", "HIGH"):
        risk = "LOW"
    data["risk_level"] = risk

    # Mandatory text fields
    data.setdefault("executive_summary",        "No summary provided.")
    data.setdefault("business_action_required", "No action specified.")
    data.setdefault("reason",                   "AI analysis completed.")

    # semantic_findings — validate and fill defaults
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

    # confidence
    conf = str(data.get("confidence", "medium")).lower()
    data["confidence"] = conf if conf in ("low", "medium", "high") else "medium"

    # review_required / review_reason
    data["review_required"] = bool(data.get("review_required", False))
    data["review_reason"]   = str(data.get("review_reason", "")).strip()

    return data


def analyze_change_with_ai(
    url:             str,
    diff_result:     dict,
    rule_based_risk: dict,
    source_language: str = "unknown",
    output_language: str = "en",
) -> dict | None:
    """
    Call Claude for semantic compliance analysis of a regulatory diff.

    Returns a structured assessment including semantic_findings, confidence,
    review_required, and review_reason, in addition to the v9 fields.
    Returns None on any failure.  Never raises.

    Result keys (when not None)
    ---------------------------
    risk_level, executive_summary, business_action_required, reason,
    source_language, output_language, affected_entities, urgency, deadline,
    semantic_findings, confidence, review_required, review_reason
    """
    if not ANTHROPIC_API_KEY:
        logger.info("AI analysis skipped — ANTHROPIC_API_KEY not set")
        return None

    try:
        import anthropic
    except ImportError:
        logger.warning("AI analysis skipped — 'anthropic' package not installed")
        return None

    added_text   = _truncate_paras(diff_result.get("added",   []))
    removed_text = _truncate_paras(diff_result.get("removed", []))

    user_prompt = _USER_TEMPLATE.format(
        url                   = url,
        source_language       = source_language,
        output_language       = output_language,
        output_language_upper = output_language.upper(),
        rule_risk             = rule_based_risk.get("risk_level", "LOW"),
        rule_reason           = rule_based_risk.get("reason",     "keyword scan"),
        added_text            = added_text,
        removed_text          = removed_text,
    )

    try:
        client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model      = "claude-haiku-4-5-20251001",
            max_tokens = 900,
            system     = _SYSTEM,
            messages   = [{"role": "user", "content": user_prompt}],
        )
        raw    = message.content[0].text
        result = _parse_response(raw)

        if result is None:
            return None

        # Fill / normalise inherited v9 fields
        result.setdefault("source_language",  source_language)
        result.setdefault("output_language",  output_language)
        result.setdefault("affected_entities", [])
        result.setdefault("urgency",           "")
        result.setdefault("deadline",          None)

        if not isinstance(result["affected_entities"], list):
            result["affected_entities"] = []
        result["affected_entities"] = [
            str(e) for e in result["affected_entities"] if e
        ]

        urg = str(result.get("urgency", "")).lower().strip()
        result["urgency"] = urg if urg in ("low", "medium", "high") else ""

        dl = result.get("deadline")
        result["deadline"] = (
            str(dl).strip()
            if dl and str(dl).strip().lower() != "null"
            else None
        )

        logger.info(
            "AI analysis OK — risk=%s confidence=%s lang=%s→%s url=%s",
            result["risk_level"], result.get("confidence", "?"),
            source_language, output_language, url,
        )
        return result

    except anthropic.AuthenticationError:
        logger.warning("AI analysis failed — invalid ANTHROPIC_API_KEY")
        return None
    except Exception as exc:
        logger.warning("AI analysis failed (%s: %s)", type(exc).__name__, exc)
        return None
