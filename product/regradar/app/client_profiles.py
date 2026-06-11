"""Client profile and relevance scoring helpers.

This is draft/review-only. It decides whether an alert draft is relevant enough
to put in a review queue or weekly brief, not whether anything is client-ready.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DELIVERY_URGENT = "URGENT_ALERT"
DELIVERY_WEEKLY = "WEEKLY_BRIEF_ONLY"
DELIVERY_SUPPRESS = "SUPPRESS_NOT_RELEVANT"
DELIVERY_REVIEW = "MANUAL_REVIEW_REQUIRED"


_BASE_DIR = Path(__file__).parent.parent
_PROFILE_PATH = _BASE_DIR / "data" / "client_profiles.example.json"


SOURCE_METADATA: dict[str, dict[str, Any]] = {
    "cbuae": {
        "source_id": "AE-central-bank-of-the-uae",
        "source_name": "Central Bank of the UAE (CBUAE)",
        "market": "AE",
        "jurisdiction": "federal/mainland",
        "category": "central_bank",
        "topics": ["banking", "payments", "stored_value", "licensing", "aml_cft", "reporting"],
        "relevance_notes": "Core source for banks, payment firms, stored value, and CBUAE-supervised activity.",
    },
    "vara": {
        "source_id": "AE-dubai-virtual-assets-regulatory-authority-vara",
        "source_name": "Dubai Virtual Assets Regulatory Authority (VARA)",
        "market": "AE",
        "jurisdiction": "Dubai",
        "category": "financial_regulator",
        "topics": ["crypto_vasp", "custody", "exchange", "brokerage", "licensing", "aml_cft", "enforcement"],
        "relevance_notes": "Core source for Dubai virtual asset service providers.",
    },
    "uae_fiu": {
        "source_id": "AE-uae-financial-intelligence-unit-uaefiu",
        "source_name": "UAE Financial Intelligence Unit (UAE FIU)",
        "market": "AE",
        "jurisdiction": "federal",
        "category": "aml",
        "topics": ["aml_cft", "suspicious_transactions", "reporting"],
        "relevance_notes": "Cross-sector AML/CFT source for regulated firms and MLRO teams.",
    },
    "dfsa": {
        "source_id": "AE-dubai-financial-services-authority-dfsa",
        "source_name": "Dubai Financial Services Authority (DFSA)",
        "market": "AE",
        "jurisdiction": "DIFC",
        "category": "financial_regulator",
        "topics": ["financial_services", "securities", "funds", "aml_cft", "enforcement", "consultations"],
        "relevance_notes": "DIFC regulator source.",
    },
    "adgm_fsra": {
        "source_id": "AE-abu-dhabi-global-market-adgm",
        "source_name": "ADGM / Financial Services Regulatory Authority (FSRA)",
        "market": "AE",
        "jurisdiction": "ADGM",
        "category": "financial_regulator",
        "topics": ["financial_services", "banking", "securities", "funds", "aml_cft", "consultations"],
        "relevance_notes": "ADGM/FSRA regulatory framework source.",
    },
    "ministry_of_finance": {
        "source_id": "AE-uae-ministry-of-finance",
        "source_name": "UAE Ministry of Finance",
        "market": "AE",
        "jurisdiction": "federal",
        "category": "finance_ministry",
        "topics": ["finance", "tax", "fiscal_policy", "reporting"],
        "relevance_notes": "Federal fiscal, finance, and tax-adjacent source.",
    },
    "uae_legislation": {
        "source_id": "AE-uae-legislation-portal",
        "source_name": "UAE Legislation Portal",
        "market": "AE",
        "jurisdiction": "federal",
        "category": "legal_acts",
        "topics": ["legislation", "decrees", "capital_markets", "tax", "aml_cft", "financial_services"],
        "relevance_notes": "Federal legislation source; homepage aggregate diffs require adapter review.",
    },
    "difc_laws": {
        "source_id": "AE-difc-laws-and-regulations",
        "source_name": "DIFC Laws",
        "market": "AE",
        "jurisdiction": "DIFC",
        "category": "legal_database",
        "topics": ["difc_laws", "legal_framework", "financial_services", "data_protection"],
        "relevance_notes": "DIFC legal framework source.",
    },
    "ministry_of_economy": {
        "source_id": "AE-uae-ministry-of-economy",
        "source_name": "UAE Ministry of Economy",
        "market": "AE",
        "jurisdiction": "federal/mainland",
        "category": "company_registry",
        "topics": ["company_law", "commercial_licensing", "aml_cft", "beneficial_ownership"],
        "relevance_notes": "Federal/mainland company law and commercial licensing source.",
    },
    "capital_market_authority_former_sca": {
        "source_id": "AE-uae-securities-and-commodities-authority-sca",
        "source_name": "Capital Market Authority / former SCA",
        "market": "AE",
        "jurisdiction": "federal",
        "category": "capital_markets",
        "topics": ["capital_markets", "securities", "public_companies", "licensing", "enforcement"],
        "relevance_notes": "Capital markets source; current extraction requires adapter work.",
    },
    "fta": {
        "source_id": "AE-uae-federal-tax-authority-fta",
        "source_name": "Federal Tax Authority (FTA)",
        "market": "AE",
        "jurisdiction": "federal",
        "category": "tax",
        "topics": ["tax", "vat", "corporate_tax", "excise", "reporting"],
        "relevance_notes": "Tax source with access restrictions in current environment.",
    },
}


CHANGE_TYPE_TOPICS = {
    "AML_CFT": {"aml_cft", "suspicious_transactions", "reporting"},
    "CIRCULAR_UPDATE": {"reporting", "licensing", "financial_services"},
    "CONSULTATION": {"consultations"},
    "DATA_PROTECTION": {"data_protection"},
    "DEADLINE_OR_REPORTING": {"reporting", "deadlines"},
    "ENFORCEMENT": {"enforcement"},
    "GUIDANCE_UPDATE": {"guidance", "financial_services"},
    "LICENSING": {"licensing"},
    "NEW_PUBLICATION": {"legislation"},
    "RULEBOOK_UPDATE": {"financial_services", "licensing"},
    "TAX": {"tax", "vat", "corporate_tax", "excise"},
}


def load_client_profiles(path: Path | None = None) -> dict[str, dict[str, Any]]:
    profile_path = path or _PROFILE_PATH
    if not profile_path.exists():
        return {}
    data = json.loads(profile_path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {str(item["client_id"]): item for item in data}
    return {str(key): value for key, value in data.items()}


def load_client_profile(client_id: str, path: Path | None = None) -> dict[str, Any]:
    profiles = load_client_profiles(path)
    try:
        return profiles[client_id]
    except KeyError as exc:
        available = ", ".join(sorted(profiles)) or "none"
        raise ValueError(f"Unknown client profile {client_id!r}. Available profiles: {available}") from exc


def source_metadata_for_alert(alert_draft: dict[str, Any]) -> dict[str, Any]:
    source_id = str(alert_draft.get("source_id") or "").lower()
    source_name = str(alert_draft.get("source_name") or "").lower()
    for metadata in SOURCE_METADATA.values():
        if source_id and source_id == str(metadata["source_id"]).lower():
            return metadata
        if source_name and (
            source_name in str(metadata["source_name"]).lower()
            or str(metadata["source_name"]).lower() in source_name
        ):
            return metadata
    return {
        "source_id": alert_draft.get("source_id"),
        "source_name": alert_draft.get("source_name"),
        "market": alert_draft.get("market"),
        "jurisdiction": "unknown",
        "category": "unknown",
        "topics": [],
        "relevance_notes": "No source metadata match; manual classification required.",
    }


def score_alert_relevance(
    alert_draft: dict[str, Any],
    client_profile: dict[str, Any],
    source_metadata: dict[str, Any],
) -> dict[str, Any]:
    profile_sources = {_norm(item) for item in client_profile.get("sources_in_scope", [])}
    excluded_sources = {_norm(item) for item in client_profile.get("sources_excluded", [])}
    profile_topics = {_norm_topic(item) for item in client_profile.get("topics_in_scope", [])}
    profile_jurisdictions = {_norm_jurisdiction(item) for item in client_profile.get("jurisdictions", [])}

    source_aliases = _source_aliases(source_metadata)
    source_name = str(source_metadata.get("source_name") or alert_draft.get("source_name") or "")
    if source_aliases & excluded_sources:
        return _decision(
            score=0,
            delivery=DELIVERY_SUPPRESS,
            matched_topics=[],
            matched_sources=[],
            matched_jurisdictions=[],
            unmatched=["Source explicitly excluded by client profile."],
            reason=f"{source_name} is excluded for {client_profile.get('client_id')}.",
        )

    source_topics = {_norm_topic(item) for item in source_metadata.get("topics", [])}
    change_topics = CHANGE_TYPE_TOPICS.get(str(alert_draft.get("change_type") or ""), set())
    alert_text_topics = _topics_from_alert_text(alert_draft)
    all_alert_topics = source_topics | {_norm_topic(item) for item in change_topics} | alert_text_topics
    matched_topics = sorted(profile_topics & all_alert_topics)
    matched_sources = sorted(source_aliases & profile_sources)
    source_jurisdiction = _norm_jurisdiction(source_metadata.get("jurisdiction"))
    matched_jurisdictions = sorted(
        item for item in profile_jurisdictions if item and (item == source_jurisdiction or item in source_jurisdiction)
    )

    score = 0
    if matched_sources:
        score += 45
    if matched_topics:
        score += min(35, 10 + len(matched_topics) * 7)
    if matched_jurisdictions:
        score += 15
    if alert_draft.get("risk_level") == "HIGH":
        score += 10
    elif alert_draft.get("risk_level") == "MEDIUM":
        score += 5
    score = min(score, 100)

    unmatched = []
    if not matched_sources:
        unmatched.append("Source is not in profile sources_in_scope.")
    if not matched_topics:
        unmatched.append("No topic overlap with profile topics_in_scope.")
    if not matched_jurisdictions:
        unmatched.append("No jurisdiction overlap with profile jurisdictions.")

    overlap = bool(matched_sources or matched_topics or matched_jurisdictions)
    if matched_topics and not matched_sources and not matched_jurisdictions:
        return _decision(
            score=min(score, 35),
            delivery=DELIVERY_SUPPRESS,
            matched_topics=matched_topics,
            matched_sources=[],
            matched_jurisdictions=[],
            unmatched=unmatched + ["Topic-only overlap without source or jurisdiction scope is not enough for delivery."],
            reason="Topic overlap exists, but the source and jurisdiction are outside this client profile.",
        )
    review_required = (
        alert_draft.get("risk_level") == "REVIEW"
        or alert_draft.get("confidence") == "LOW"
        or (alert_draft.get("proof_block") or {}).get("proof_quality") == "INCOMPLETE"
        or "adapter review required" in " ".join(str(item) for item in alert_draft.get("limitations", [])).lower()
    )
    if review_required and overlap:
        return _decision(
            score=max(score, 40),
            delivery=DELIVERY_REVIEW,
            matched_topics=matched_topics,
            matched_sources=matched_sources,
            matched_jurisdictions=matched_jurisdictions,
            unmatched=unmatched,
            reason="Relevant overlap exists, but low confidence, REVIEW risk, incomplete proof, or adapter limitation requires manual review.",
        )
    if not overlap:
        return _decision(
            score=score,
            delivery=DELIVERY_SUPPRESS,
            matched_topics=[],
            matched_sources=[],
            matched_jurisdictions=[],
            unmatched=unmatched,
            reason="No source, topic, or jurisdiction overlap with this client profile.",
        )

    risk = str(alert_draft.get("risk_level") or "LOW")
    threshold = str(client_profile.get("alert_threshold") or "MEDIUM").upper()
    if risk == "HIGH" and (matched_sources or matched_topics):
        delivery = DELIVERY_URGENT
    elif risk == "MEDIUM" and _threshold_allows_medium(threshold) and (matched_sources or matched_topics):
        delivery = DELIVERY_WEEKLY
    else:
        delivery = DELIVERY_WEEKLY if score >= 45 else DELIVERY_SUPPRESS

    return _decision(
        score=score,
        delivery=delivery,
        matched_topics=matched_topics,
        matched_sources=matched_sources,
        matched_jurisdictions=matched_jurisdictions,
        unmatched=unmatched,
        reason=_reason(delivery, source_name, client_profile, matched_sources, matched_topics, matched_jurisdictions),
    )


def _decision(
    *,
    score: int,
    delivery: str,
    matched_topics: list[str],
    matched_sources: list[str],
    matched_jurisdictions: list[str],
    unmatched: list[str],
    reason: str,
) -> dict[str, Any]:
    return {
        "relevance_score": score,
        "delivery_decision": delivery,
        "matched_topics": matched_topics,
        "matched_sources": matched_sources,
        "matched_jurisdictions": matched_jurisdictions,
        "unmatched_reasons": unmatched,
        "reason": reason,
    }


def _reason(delivery: str, source_name: str, profile: dict[str, Any], sources: list[str], topics: list[str], jurisdictions: list[str]) -> str:
    if delivery == DELIVERY_URGENT:
        return f"{source_name} has high-risk overlap with {profile.get('client_id')} via source/topic scope."
    if delivery == DELIVERY_WEEKLY:
        parts = []
        if sources:
            parts.append("source")
        if topics:
            parts.append("topic")
        if jurisdictions:
            parts.append("jurisdiction")
        return f"Relevant {'/'.join(parts)} overlap; hold for reviewed weekly brief or reviewer escalation."
    return "Insufficient overlap for this client profile."


def _threshold_allows_medium(threshold: str) -> bool:
    return threshold in {"LOW", "MEDIUM"}


def _source_aliases(metadata: dict[str, Any]) -> set[str]:
    values = {
        metadata.get("source_id"),
        metadata.get("source_name"),
        metadata.get("category"),
    }
    name = str(metadata.get("source_name") or "").lower()
    if "central bank" in name or "cbuae" in name:
        values.add("CBUAE")
    if "vara" in name:
        values.add("VARA")
    if "fiu" in name:
        values.add("UAE FIU")
    if "dfsa" in name:
        values.add("DFSA")
    if "adgm" in name or "fsra" in name:
        values.add("ADGM/FSRA")
    if "finance" in name:
        values.add("Ministry of Finance")
    if "legislation" in name:
        values.add("UAE Legislation Portal")
    if "difc" in name:
        values.add("DIFC Laws")
    if "economy" in name:
        values.add("Ministry of Economy")
    if "former sca" in name or "commodities authority" in name:
        values.add("Capital Market Authority / former SCA")
    if "tax authority" in name:
        values.add("Federal Tax Authority")
        values.add("FTA")
    return {_norm(value) for value in values if value}


def _topics_from_alert_text(alert: dict[str, Any]) -> set[str]:
    text_parts = [
        alert.get("change_type"),
        alert.get("what_changed"),
        alert.get("affected_entities"),
        alert.get("recommended_action"),
        " ".join(str(item) for item in alert.get("added_chunks", [])),
        " ".join(str(item) for item in alert.get("removed_chunks", [])),
    ]
    for item in alert.get("changed_chunks") or []:
        text_parts.extend(item.get("before") or [])
        text_parts.extend(item.get("after") or [])
    text = " ".join(str(part).lower() for part in text_parts if part)
    topics = set()
    keyword_topics = {
        "payments": ["payment", "stored value"],
        "stored_value": ["stored value"],
        "crypto_vasp": ["vasp", "virtual asset", "crypto"],
        "custody": ["custody", "client assets"],
        "licensing": ["license", "licence", "authorization", "registration"],
        "aml_cft": ["aml", "cft", "suspicious transaction"],
        "reporting": ["report", "submit", "filing"],
        "tax": ["tax", "vat", "excise"],
        "corporate_tax": ["corporate tax"],
        "securities": ["securities", "capital market"],
        "funds": ["fund"],
        "data_protection": ["data protection", "privacy"],
        "consultations": ["consultation"],
        "enforcement": ["fine", "penalty", "sanction", "enforcement"],
    }
    for topic, keywords in keyword_topics.items():
        if any(keyword in text for keyword in keywords):
            topics.add(topic)
    return topics


def _norm(value: Any) -> str:
    return str(value or "").strip().lower().replace("&", "and").replace("_", " ")


def _norm_topic(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _norm_jurisdiction(value: Any) -> str:
    return str(value or "").strip().lower().replace("uae / ", "").replace(" / ", "/")
