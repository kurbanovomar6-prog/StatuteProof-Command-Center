"""
AI compliance analysis layer — v13.

Semantic regulatory intelligence using Claude.

v13 additions vs v12
---------------------
• Richer structured analysis: what_to_do (numbered action list), deadline_risk,
  materiality (top-level), legal_area, jurisdiction fields added to JSON schema.
• urgency now uses a four-value enum: IMMEDIATE | WITHIN_30_DAYS | WITHIN_90_DAYS | MONITOR.
• confidence is now a float 0.0–1.0 (was low/medium/high string).
• review_required computed from confidence < 0.75 OR risk_level == HIGH.
• parse_action_steps() helper exported for structured what_to_do rendering.
• derive_urgency_from_text() helper for regex-based urgency fallback.
• max_tokens increased to 1 800 to accommodate the richer JSON output.

v12 additions vs v11
---------------------
• System prompt extended with strict legal-safety language guardrails.
• Five new client-facing output fields added to JSON schema:
    what_changed, why_it_matters, recommendations (list[str], exactly 3),
    affected_licence_types (list[str]), risk_explanation.
• All recommendations use cautious, non-prescriptive language only.
• Monitoring-intelligence disclaimer embedded in system prompt.
• max_tokens increased to 1 400 to accommodate the richer JSON output.

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
import re

from app.config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

_MAX_PARAS    = 20
_MAX_PARA_LEN = 400

# ── Improvement 4: urgency derivation from diff text ─────────────────────────
_URGENCY_PATTERNS: list[tuple[re.Pattern, str]] = [
    (
        re.compile(
            r"effective\s+(from|as\s+of|on)\s+"
            r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}-\d{2}-\d{2})",
            re.I,
        ),
        "IMMEDIATE",
    ),
    (
        re.compile(
            r"by\s+(end\s+of\s+)?"
            r"(january|february|march|april|may|june|july|august|"
            r"september|october|november|december)\s+\d{4}",
            re.I,
        ),
        "WITHIN_30_DAYS",
    ),
    (re.compile(r"within\s+(\d+)\s+days", re.I), "WITHIN_30_DAYS"),
    (re.compile(r"no\s+later\s+than", re.I),     "WITHIN_30_DAYS"),
]


def derive_urgency_from_text(diff_text: str) -> str:
    """
    Scan diff text for deadline/effectivity patterns and return urgency tier.

    Returns one of: IMMEDIATE | WITHIN_30_DAYS | MONITOR (fallback).
    Used as a fallback when the AI does not return urgency or returns an
    unrecognised value.

    Never raises.
    """
    if not diff_text:
        return "MONITOR"
    for pattern, urgency in _URGENCY_PATTERNS:
        if pattern.search(diff_text):
            return urgency
    return "MONITOR"


# ── Improvement 2: structured action-step parsing ────────────────────────────
_ACTION_SPLIT_RE = re.compile(
    r"(?:^|\n)\s*(?:\d+[\.\)]\s*|[-•–]\s*)",
)


def parse_action_steps(text: str) -> list[str]:
    """
    Split a numbered/bulleted action list string into a clean list of strings.

    Handles:
      "1. Review Article 7(2)\\n2. Update policy\\n3. Notify MLRO"
      "- Review Article 7(2)\\n- Update policy"
      Plain sentences that are not bullet-formatted (returned as single item).

    Returns a list of non-empty stripped strings.
    Never raises.
    """
    if not text or not text.strip():
        return []

    parts = _ACTION_SPLIT_RE.split(text)
    steps = [p.strip() for p in parts if p.strip()]

    # If splitting produced only one item and the raw text contained newlines,
    # try splitting on newlines directly as a secondary strategy.
    if len(steps) <= 1 and "\n" in text:
        steps = [line.strip() for line in text.splitlines() if line.strip()]

    return steps if steps else [text.strip()]

# Response header prepended to all AI output before it reaches the caller.
# This is NOT sent to Claude — it is injected into the returned dict.
_MONITORING_DISCLAIMER = (
    "Monitoring intelligence only. Not legal advice. "
    "Users should consult qualified legal or compliance professionals "
    "before making regulatory decisions."
)

_SYSTEM = """\
You are a senior regulatory compliance analyst specialising in banks, fintechs, \
payment companies, virtual asset service providers (VASPs), and regulated financial \
institutions across GCC, APAC, Turkey, Central Asia, and Caucasus priority markets, \
plus international regulatory bodies (FATF, BIS, Basel Committee).

IMPORTANT: You are a regulatory monitoring intelligence tool, not a legal adviser.
All recommendations must use cautious, non-prescriptive language.
Never say "you must" or "you are required to" or "you shall" or "mandatory for you".
Always say "consider", "may wish to", "it would be prudent to", "this may affect".
All output is monitoring intelligence only, not legal advice.
Every recommendation must end with context such as \
"before your next compliance review" or "in consultation with your MLRO or legal counsel".

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
Rule-based pre-screening: {rule_risk} -- {rule_reason}

ADDED PARAGRAPHS (new or modified content):
{added_text}

REMOVED PARAGRAPHS (deleted or replaced content):
{removed_text}

ANALYSIS INSTRUCTIONS:
1. Read the text carefully, understanding its legal and regulatory meaning.
2. Do NOT rely on keyword presence alone -- analyse the substance.
3. Base analysis ONLY on the diff text shown above. Do NOT invent facts not present.
4. Determine what obligations, deadlines, or requirements are created or changed.
5. Consider which entity types are affected (banks, fintechs, payment providers, VASPs, etc.).
6. Assess whether the change is material, informational, or ambiguous.
7. Set confidence (0.0 to 1.0 float):
   - 0.85-1.0  = explicit obligation / deadline / requirement clearly stated
   - 0.60-0.84 = implied or reasonably inferred; some ambiguity remains
   - 0.0-0.59  = text is vague, translated poorly, or evidence is insufficient
8. Do NOT invent content not shown. Do NOT speculate about missing text.
9. If no deadline date is explicitly stated, set "deadline" to null.
10. If affected entities are unclear, return [].
11. Write ALL output fields in {output_language_upper}.
12. For what_changed: precise description of what text was removed and what was added.
13. For why_it_matters: business impact -- who is affected, what obligations change.
14. For what_to_do: SPECIFIC numbered action list for the compliance team.
    Use cautious language: "Consider reviewing...", "Your compliance team may wish to...".
    Each item must be a concrete step, not vague advice.
    Each item must end with "before your next compliance review" or
    "in consultation with your MLRO or legal counsel".
    Example: "1. Review Article 7(2) obligations against your current AML policy before your next compliance review. 2. Notify your MLRO of the deadline change in consultation with your MLRO or legal counsel."
15. For deadline_risk: state whether a compliance deadline is implied or explicit.
    If a date appears in the diff, quote it. If none, say "No explicit deadline in this diff."
16. For urgency: use ONLY these four values based on deadline/effectivity signals in the diff:
    - IMMEDIATE      = "effective from [date]" or "effective as of [date]" appears in the diff
    - WITHIN_30_DAYS = "within N days", "no later than", "by [month] [year]" appears in the diff
    - WITHIN_90_DAYS = obligation or change is material but no near-term deadline
    - MONITOR        = informational or LOW risk, no deadline signal
17. For materiality: top-level field, one of: MATERIAL | NON_MATERIAL | UNCLEAR
18. For legal_area: identify the regulatory domain from the text itself
    (e.g. AML/CFT, Capital Requirements, Consumer Protection, Data Privacy, Licensing,
    Reporting/Disclosure, Virtual Assets, Prudential, Market Conduct, Sanctions).
    Return "Unknown" if cannot be determined.
19. For jurisdiction: identify from context (e.g. UAE, DIFC, ADGM, UK, EU, US, FATF).
    Return "Unknown" if cannot be determined.
20. For recommendations: exactly 3 strings using ONLY cautious language.
    ("Consider reviewing...", "Your compliance team may wish to assess...",
    "It would be prudent to..."). Each must end with
    "before your next compliance review" or "in consultation with your MLRO or legal counsel".
21. For affected_licence_types: list specific licence categories if clearly identifiable
    (e.g. ["VASP", "CBUAE Payment Institution"]); return [] if unclear.
22. For risk_explanation: one sentence explaining WHY this risk tier was assigned.

Respond with ONLY a valid JSON object -- no markdown fences, no text outside the JSON.

Required JSON format (all keys mandatory):
{{
  "risk_level": "LOW" | "MEDIUM" | "HIGH",
  "executive_summary": "2-3 sentences: what changed and why it matters for regulated entities",
  "what_changed": "precise description of what was removed and what was added",
  "why_it_matters": "business impact -- who is affected, what obligations change",
  "what_to_do": "1. Specific action one before your next compliance review. 2. Specific action two in consultation with your MLRO or legal counsel.",
  "deadline_risk": "explicit deadline if present, or No explicit deadline in this diff",
  "business_action_required": "one concrete action the compliance team may consider, or No immediate action required for LOW",
  "reason": "concise explanation of why this risk_level was chosen based on substance not keywords",
  "source_language": "{source_language}",
  "output_language": "{output_language}",
  "affected_entities": ["list of entity types clearly mentioned or strongly implied; empty list if unclear"],
  "urgency": "IMMEDIATE" | "WITHIN_30_DAYS" | "WITHIN_90_DAYS" | "MONITOR",
  "deadline": "explicit date string if stated in the text, or null",
  "materiality": "MATERIAL" | "NON_MATERIAL" | "UNCLEAR",
  "legal_area": "e.g. AML/CFT, Capital Requirements, Consumer Protection, Licensing, Virtual Assets, or Unknown",
  "jurisdiction": "e.g. UAE, DIFC, ADGM, UK, EU, US, FATF, or Unknown",
  "semantic_findings": {{
    "new_obligation": true | false,
    "deadline_detected": true | false,
    "reporting_required": true | false,
    "licensing_impact": true | false,
    "enforcement_exposure": true | false,
    "operational_impact": "none" | "low" | "medium" | "high",
    "materiality": "informational" | "low" | "material" | "critical"
  }},
  "confidence": 0.85,
  "review_required": true | false,
  "review_reason": "brief explanation if review_required is true, otherwise empty string",
  "what_changed": "precise description of what was removed and what was added",
  "why_it_matters": "business impact -- who is affected, what obligations change",
  "recommendations": [
    "Consider reviewing ... before your next compliance review",
    "Your compliance team may wish to assess ... in consultation with your MLRO or legal counsel",
    "It would be prudent to ... before your next compliance review"
  ],
  "affected_licence_types": ["specific licence categories or empty list"],
  "risk_explanation": "one sentence explaining why this risk tier was assigned"
}}\
"""


def _truncate_paras(paras: list[str]) -> str:
    """Format up to _MAX_PARAS paragraphs, each capped at _MAX_PARA_LEN chars."""
    if not paras:
        return "(none)"
    selected = paras[:_MAX_PARAS]
    lines = []
    for i, p in enumerate(selected, 1):
        text = p[:_MAX_PARA_LEN] + ("..." if len(p) > _MAX_PARA_LEN else "")
        lines.append(f"{i}. {text}")
    return "\n".join(lines)


def _parse_response(raw: str) -> dict | None:
    """
    Extract and validate JSON from the model response.

    Handles clean JSON strings and responses wrapped in ```json fences.
    Normalises and sets safe defaults for all required fields including
    v13 new fields: what_to_do (parsed list), deadline_risk, materiality,
    legal_area, jurisdiction, and confidence as float.
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
        logger.warning("AI returned invalid JSON: %s -- raw: %.200s", exc, raw)
        return None

    # Normalise risk_level
    risk = str(data.get("risk_level", "LOW")).upper().strip()
    if risk not in ("LOW", "MEDIUM", "HIGH"):
        risk = "LOW"
    data["risk_level"] = risk

    # Mandatory text fields (existing v9/v11)
    data.setdefault("executive_summary",        "No summary provided.")
    data.setdefault("business_action_required", "No action specified.")
    data.setdefault("reason",                   "AI analysis completed.")

    # semantic_findings -- validate and fill defaults
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

    # -- Improvement 3: confidence as float 0.0–1.0 ---------------------------
    # Accept float from AI (new v13) or legacy string (low/medium/high).
    raw_conf = data.get("confidence", 0.5)
    try:
        conf_float = float(raw_conf)
        # Clamp to valid range.
        conf_float = max(0.0, min(1.0, conf_float))
    except (TypeError, ValueError):
        # Legacy string → midpoint float mapping.
        _legacy_map = {"high": 0.85, "medium": 0.60, "low": 0.35}
        conf_str = str(raw_conf).lower().strip()
        conf_float = _legacy_map.get(conf_str, 0.5)
    data["confidence"] = conf_float

    # -- Improvement 3: review_required derived from confidence + risk_level --
    # AI's own review_required is accepted; we also force True for HIGH risk
    # or low confidence regardless of what the AI said.
    ai_review = bool(data.get("review_required", False))
    forced_review = (conf_float < 0.75) or (risk == "HIGH")
    data["review_required"] = ai_review or forced_review

    review_reason_parts: list[str] = []
    existing_reason = str(data.get("review_reason", "")).strip()
    if existing_reason:
        review_reason_parts.append(existing_reason)
    if conf_float < 0.75 and "low confidence" not in existing_reason.lower():
        review_reason_parts.append(
            f"Confidence is {conf_float:.2f} (below 0.75 threshold) — human verification required."
        )
    if risk == "HIGH" and "high risk" not in existing_reason.lower():
        review_reason_parts.append(
            "HIGH risk classification requires human compliance review before client-facing action."
        )
    data["review_reason"] = " ".join(review_reason_parts).strip()

    # -- v13 new fields: safe defaults ----------------------------------------
    data.setdefault("what_changed",     "No change description provided.")
    data.setdefault("why_it_matters",   "Impact on regulated firms could not be determined.")
    data.setdefault("risk_explanation", "Risk tier assigned based on available evidence.")
    data.setdefault("deadline_risk",    "No explicit deadline in this diff.")

    # materiality (top-level): MATERIAL | NON_MATERIAL | UNCLEAR
    mat_top = str(data.get("materiality", "UNCLEAR")).upper().strip()
    data["materiality"] = mat_top if mat_top in ("MATERIAL", "NON_MATERIAL", "UNCLEAR") else "UNCLEAR"

    # legal_area and jurisdiction
    data.setdefault("legal_area",   "Unknown")
    data.setdefault("jurisdiction", "Unknown")
    if not str(data["legal_area"]).strip():
        data["legal_area"] = "Unknown"
    if not str(data["jurisdiction"]).strip():
        data["jurisdiction"] = "Unknown"

    # urgency: normalise to four-value enum; fallback to MONITOR
    _VALID_URGENCY = {"IMMEDIATE", "WITHIN_30_DAYS", "WITHIN_90_DAYS", "MONITOR"}
    urg_raw = str(data.get("urgency", "")).upper().strip()
    if urg_raw not in _VALID_URGENCY:
        # Legacy low/medium/high mapping
        _legacy_urg = {"HIGH": "IMMEDIATE", "MEDIUM": "WITHIN_90_DAYS", "LOW": "MONITOR"}
        urg_raw = _legacy_urg.get(urg_raw, "MONITOR")
    data["urgency"] = urg_raw

    # -- Improvement 2: what_to_do → structured list --------------------------
    # Accept string from AI and parse into a list; store both forms.
    raw_what_to_do = data.get("what_to_do", "")
    if isinstance(raw_what_to_do, list):
        # AI already returned a list — normalise items.
        action_list = [str(s).strip() for s in raw_what_to_do if s and str(s).strip()]
    else:
        action_list = parse_action_steps(str(raw_what_to_do))

    if not action_list:
        action_list = [
            "Consider reviewing this regulatory change against your current compliance "
            "framework before your next compliance review.",
            "Your compliance team may wish to assess the potential impact "
            "in consultation with your MLRO or legal counsel.",
            "It would be prudent to preserve this diff in your evidence trail "
            "before your next compliance review.",
        ]
    data["what_to_do"]      = raw_what_to_do if isinstance(raw_what_to_do, str) else "\n".join(action_list)
    data["action_steps"]    = action_list

    # recommendations: exactly 3 cautious strings
    recs = data.get("recommendations")
    if not isinstance(recs, list):
        recs = []
    recs = [str(r).strip() for r in recs if r and str(r).strip()]
    _rec_fallbacks = [
        (
            "Consider reviewing this change against your current compliance framework "
            "before your next compliance review."
        ),
        (
            "Your compliance team may wish to assess the potential impact of this update "
            "in consultation with your MLRO or legal counsel."
        ),
        (
            "It would be prudent to preserve this diff in your evidence trail "
            "before your next compliance review."
        ),
    ]
    while len(recs) < 3:
        recs.append(_rec_fallbacks[len(recs)])
    data["recommendations"] = recs[:3]

    # affected_licence_types: list of strings, empty list if none
    alt = data.get("affected_licence_types")
    if not isinstance(alt, list):
        alt = []
    data["affected_licence_types"] = [str(x).strip() for x in alt if x and str(x).strip()]

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

    Returns a structured assessment. Returns None on any failure. Never raises.

    Result keys (when not None)
    ---------------------------
    Existing (v9/v11):
      risk_level, executive_summary, business_action_required, reason,
      source_language, output_language, affected_entities, urgency, deadline,
      semantic_findings, confidence, review_required, review_reason

    New (v12):
      what_changed, why_it_matters, recommendations, affected_licence_types,
      risk_explanation, monitoring_disclaimer

    New (v13):
      what_to_do (str), action_steps (list[str]), deadline_risk,
      materiality (MATERIAL|NON_MATERIAL|UNCLEAR), legal_area, jurisdiction,
      urgency (IMMEDIATE|WITHIN_30_DAYS|WITHIN_90_DAYS|MONITOR),
      confidence (float 0.0-1.0)
    """
    if not ANTHROPIC_API_KEY:
        logger.info("AI analysis skipped -- ANTHROPIC_API_KEY not set")
        return None

    try:
        import anthropic
    except ImportError:
        logger.warning("AI analysis skipped -- 'anthropic' package not installed")
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
            max_tokens = 1800,
            system     = _SYSTEM,
            messages   = [{"role": "user", "content": user_prompt}],
        )
        first  = message.content[0]
        raw    = ""
        if isinstance(first, anthropic.types.TextBlock):
            raw = first.text
        result = _parse_response(raw)

        if result is None:
            return None

        # Fill / normalise inherited v9 fields
        result.setdefault("source_language",   source_language)
        result.setdefault("output_language",   output_language)
        result.setdefault("affected_entities", [])
        result.setdefault("deadline",          None)

        if not isinstance(result["affected_entities"], list):
            result["affected_entities"] = []
        result["affected_entities"] = [
            str(e) for e in result["affected_entities"] if e
        ]

        # urgency: _parse_response already normalised to 4-value enum.
        # Apply text-based fallback only when urgency is MONITOR and the diff
        # text itself contains deadline signals the AI may have missed.
        if result.get("urgency") == "MONITOR":
            diff_text_combined = " ".join(
                diff_result.get("added", []) + diff_result.get("removed", [])
            )
            fallback_urgency = derive_urgency_from_text(diff_text_combined)
            if fallback_urgency != "MONITOR":
                result["urgency"] = fallback_urgency
                logger.info(
                    "Urgency upgraded from MONITOR to %s via regex fallback for %s",
                    fallback_urgency, url,
                )

        dl = result.get("deadline")
        result["deadline"] = (
            str(dl).strip()
            if dl and str(dl).strip().lower() != "null"
            else None
        )

        # Attach the monitoring disclaimer to every AI result
        result["monitoring_disclaimer"] = _MONITORING_DISCLAIMER

        logger.info(
            "AI analysis OK -- risk=%s confidence=%.2f urgency=%s lang=%s->%s url=%s",
            result["risk_level"], result.get("confidence", 0.5),
            result.get("urgency", "?"),
            source_language, output_language, url,
        )
        return result

    except anthropic.AuthenticationError:
        logger.warning("AI analysis failed -- invalid ANTHROPIC_API_KEY")
        return None
    except Exception as exc:
        logger.warning("AI analysis failed (%s: %s)", type(exc).__name__, exc)
        return None
