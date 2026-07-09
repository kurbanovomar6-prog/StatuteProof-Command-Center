"""Approved alert routing dry-run for authenticated StatuteProof users."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from app.db import _connect, ensure_auth_tables
from app.profile import get_or_create_profile, normalize_regulators
from app.regulator_map import resolve_regulator
from app.telegram import send_telegram_message
from app.telegram_pairing import get_telegram_link
from app.user_delivery import (
    create_delivery_log,
    update_delivery_log_failed,
    update_delivery_log_sent,
)

logger = logging.getLogger(__name__)

_UAE_MARKETS = {"UAE", "AE", "DIFC", "ADGM", "DUBAI", "FEDERAL", "MAINLAND"}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso_date(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.strptime(text[:10], "%Y-%m-%d")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _safe_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if item not in (None, "")]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("["):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                return [item for item in parsed if item not in (None, "")]
        return [part.strip() for part in text.split(",") if part.strip()]
    return []


def _normalize_risk_level(value: str | None) -> str:
    text = str(value or "").strip().upper()
    if text in {"LOW", "MEDIUM", "HIGH"}:
        return text
    return "MEDIUM"


def _risk_rank(level: str) -> int:
    return {"LOW": 1, "MEDIUM": 2, "HIGH": 3}.get(_normalize_risk_level(level), 2)


def _threshold_allows(alert_risk: str, user_threshold: str) -> bool:
    return _risk_rank(alert_risk) >= _risk_rank(user_threshold)


def user_profile_to_routing_profile(user_id: int) -> dict:
    profile = get_or_create_profile(int(user_id))
    markets = [str(item).strip() for item in _safe_list(profile.get("markets")) if str(item).strip()]
    if not markets:
        markets = ["UAE"]
    alert_threshold = _normalize_risk_level(profile.get("alert_threshold"))
    return {
        "client_id": f"user_{int(user_id)}",
        "user_id": int(user_id),
        "company_name": profile.get("company_name"),
        "markets": markets,
        "industries": [str(item).strip() for item in _safe_list(profile.get("industries")) if str(item).strip()],
        "topics": [str(item).strip() for item in _safe_list(profile.get("topics")) if str(item).strip()],
        "sources": [],
        "regulators": normalize_regulators(profile.get("regulators")),
        "custom_sources": _safe_list(profile.get("custom_sources")),
        "alert_threshold": alert_threshold,
        "risk_threshold": alert_threshold,
        "delivery_preferences": {
            "urgent_threshold": 80,
            "weekly_threshold": 50,
        },
        "telegram_alerts_enabled": bool(profile.get("telegram_alerts_enabled")),
        "onboarding_completed": bool(profile.get("onboarding_completed")),
    }


def _get_approved_statuses() -> set[str]:
    try:
        from app import alert_review

        statuses = {
            getattr(alert_review, "STATUS_APPROVED_WEEKLY", ""),
            getattr(alert_review, "STATUS_APPROVED_URGENT", ""),
        }
        return {status for status in statuses if status}
    except Exception:
        return {"APPROVED_FOR_WEEKLY", "APPROVED_FOR_URGENT"}


def _review_status(review: dict | None, draft: dict) -> str | None:
    return (
        (review or {}).get("new_status")
        or (review or {}).get("review_status")
        or draft.get("review_status")
    )


def _review_decision(review: dict | None, draft: dict) -> str | None:
    return (
        (review or {}).get("new_send_decision")
        or (review or {}).get("send_decision")
        or draft.get("send_decision")
    )


def load_approved_alert_candidates(days: int = 14) -> list[dict]:
    try:
        from app.alert_review import latest_review_for, list_alert_drafts
    except Exception as exc:
        logger.warning("Alert review helpers unavailable: %s", type(exc).__name__)
        return []

    approved = _get_approved_statuses()
    cutoff = _now_utc() - timedelta(days=max(1, int(days or 14)))
    candidates: list[dict] = []

    for draft in list_alert_drafts():
        if not isinstance(draft, dict):
            continue
        alert_id = str(draft.get("alert_id") or "").strip()
        if not alert_id:
            continue
        try:
            review = latest_review_for(alert_id)
        except Exception:
            review = None

        status = _review_status(review, draft)
        if status not in approved:
            continue

        date_value = (
            draft.get("detected_at")
            or draft.get("checked_at_utc")
            or draft.get("created_at")
            or (review or {}).get("reviewed_at_utc")
        )
        parsed_date = _parse_iso_date(date_value)
        if parsed_date and parsed_date < cutoff:
            continue

        enriched = dict(draft)
        enriched["review_status"] = status
        enriched["review_decision"] = _review_decision(review, draft)
        enriched["reviewed_at"] = (review or {}).get("reviewed_at_utc") or draft.get("reviewed_at_utc")
        enriched["reviewer_note"] = (review or {}).get("review_note") or draft.get("review_note")
        if not parsed_date:
            limitations = list(_safe_list(enriched.get("limitations")))
            limitations.append("Alert date unavailable; included in preview window by review status.")
            enriched["limitations"] = limitations
        candidates.append(enriched)

    return candidates


def normalize_alert_for_routing(alert: dict) -> dict:
    proof = alert.get("proof_block") if isinstance(alert.get("proof_block"), dict) else {}
    relevance = alert.get("relevance") if isinstance(alert.get("relevance"), dict) else {}
    source_url = alert.get("source_url") or alert.get("url") or proof.get("official_url") or proof.get("final_url")
    source_name = alert.get("source_name") or alert.get("source_id") or "Official source"
    alert_id = str(alert.get("alert_id") or "").strip()
    limitations = [str(item) for item in _safe_list(alert.get("limitations")) if str(item).strip()]
    title = (
        alert.get("title")
        or alert.get("headline")
        or alert.get("change_title")
        or f"{source_name} reviewed alert"
        or alert_id
    )
    summary = (
        alert.get("executive_summary")
        or alert.get("summary")
        or alert.get("ai_summary")
        or alert.get("what_changed")
        or "Reviewed source alert summary unavailable."
    )
    business_action = (
        alert.get("business_action")
        or alert.get("business_action_required")
        or alert.get("recommended_action")
        or alert.get("action")
        or ""
    )
    affected = _safe_list(alert.get("affected_entities"))
    topics = _safe_list(alert.get("topics")) + affected + _safe_list(alert.get("change_type"))
    market = alert.get("market") or alert.get("jurisdiction") or relevance.get("market")
    if not source_url:
        limitations.append("Source URL unavailable in alert draft.")
    if not market:
        limitations.append("Market or jurisdiction unavailable in alert draft.")
    if not topics:
        limitations.append("Topics unavailable in alert draft.")
    return {
        "alert_id": alert_id,
        "source_id": alert.get("source_id"),
        "source_name": str(source_name),
        "source_url": source_url,
        "url": alert.get("url"),
        "title": str(title),
        "risk_level": _normalize_risk_level(alert.get("risk_level")),
        "change_type": str(alert.get("change_type") or "REGULATORY_UPDATE"),
        "market": str(market).strip() if market else None,
        "jurisdiction": str(alert.get("jurisdiction") or market).strip() if (alert.get("jurisdiction") or market) else None,
        "topics": [str(item) for item in topics if str(item).strip()],
        "executive_summary": str(summary),
        "business_action": str(business_action),
        "affected_entities": [str(item) for item in affected if str(item).strip()],
        "detected_at": alert.get("detected_at") or alert.get("checked_at_utc") or alert.get("created_at"),
        "review_status": alert.get("review_status"),
        "review_decision": alert.get("review_decision"),
        "reviewed_at": alert.get("reviewed_at"),
        "limitations": list(dict.fromkeys(limitations)),
    }


def _norm_set(values: list) -> set[str]:
    return {str(value).strip().lower() for value in values if str(value).strip()}


def _domain(value: str | None) -> str:
    if not value:
        return ""
    parsed = urlparse(str(value))
    return (parsed.netloc or parsed.path).lower().removeprefix("www.")


def score_alert_for_user(user_profile: dict, alert: dict) -> dict:
    score = 0
    reasons: list[str] = []
    limitations: list[str] = []

    # Authoritative regulator scope gate (hard exclusion, not a penalty).
    # If the customer has scoped to specific regulators and this alert's
    # resolved regulator is outside that scope, exclude it outright before
    # any risk/market/topic scoring. Empty/absent scope = all regulators
    # (backward compatible), so scoring proceeds as before.
    scoped_regulators = normalize_regulators(user_profile.get("regulators"))
    if scoped_regulators:
        alert_regulator = resolve_regulator(alert)
        if alert_regulator not in scoped_regulators:
            return {
                "score": 0,
                "matched": False,
                "reasons": [
                    f"Outside your regulator scope "
                    f"(alert regulator {alert_regulator}; you receive "
                    f"{', '.join(scoped_regulators)})"
                ],
                "limitations": [],
            }

    if _threshold_allows(alert.get("risk_level"), user_profile.get("alert_threshold")):
        score += 40
        reasons.append(f"{alert.get('risk_level')} risk meets your {user_profile.get('alert_threshold')} threshold")
    else:
        reasons.append("Below your alert threshold")

    alert_markets = _norm_set([alert.get("market"), alert.get("jurisdiction")])
    user_markets = _norm_set(user_profile.get("markets") or [])
    if alert_markets and user_markets.intersection(alert_markets):
        score += 25
        reasons.append("Market matches your saved profile")
    elif "uae" in user_markets and {m.upper() for m in alert_markets}.intersection(_UAE_MARKETS):
        score += 25
        reasons.append("UAE source layer matches your saved profile")
    elif not alert_markets:
        limitations.append("Alert market is unavailable")

    profile_terms = _norm_set((user_profile.get("industries") or []) + (user_profile.get("topics") or []))
    alert_terms = _norm_set((alert.get("topics") or []) + [alert.get("change_type"), alert.get("source_name")])
    if profile_terms and alert_terms:
        overlap = {term for term in profile_terms if any(term in item or item in term for item in alert_terms)}
        if overlap:
            score += 20
            reasons.append("Topic or industry overlaps your saved profile")
    elif not alert_terms:
        limitations.append("Alert topics are unavailable")

    alert_domains = {_domain(alert.get("source_url")), _domain(alert.get("url"))}
    for source in user_profile.get("custom_sources") or []:
        source_url = source.get("url") if isinstance(source, dict) else str(source)
        if _domain(source_url) and _domain(source_url) in alert_domains:
            score += 15
            reasons.append("Source matches one of your custom sources")
            break

    score = min(score, 100)
    return {
        "score": score,
        "matched": score >= 40,
        "reasons": reasons,
        "limitations": limitations,
    }


def get_sent_alert_ids_for_user(user_id: int) -> set[str]:
    ensure_auth_tables()
    prefix = f"{int(user_id)}:reviewed_alert_preview:"
    legacy_prefix = f"{int(user_id)}:reviewed_alert:"
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT alert_id
            FROM user_delivery_log
            WHERE user_id = ?
              AND delivery_type = 'reviewed_alert_preview'
              AND channel = 'telegram'
              AND status IN ('pending', 'sent')
              AND (
                  idempotency_key LIKE ?
                  OR idempotency_key LIKE ?
              )
            """,
            (int(user_id), prefix + "%", legacy_prefix + "%"),
        ).fetchall()
        return {str(row["alert_id"]) for row in rows if row["alert_id"]}
    finally:
        conn.close()


def build_routing_preview_for_user(user_id: int, days: int = 14) -> dict:
    safe_days = max(1, min(int(days or 14), 60))
    user_profile = user_profile_to_routing_profile(int(user_id))
    candidates = load_approved_alert_candidates(safe_days)
    link = get_telegram_link(int(user_id))
    sent_ids = get_sent_alert_ids_for_user(int(user_id))
    not_ready_reasons = []
    if not user_profile.get("onboarding_completed"):
        not_ready_reasons.append("Complete onboarding before delivery.")
    if not user_profile.get("telegram_alerts_enabled"):
        not_ready_reasons.append("Enable Telegram alerts in Settings.")
    if not link.get("telegram_chat_id"):
        not_ready_reasons.append("Connect Telegram in Integrations first.")

    matches = []
    for candidate in candidates:
        normalized = normalize_alert_for_routing(candidate)
        score = score_alert_for_user(user_profile, normalized)
        already_sent = normalized["alert_id"] in sent_ids
        item_reasons = []
        if not score["matched"]:
            item_reasons.append("Not matched to your saved profile.")
        if not user_profile.get("onboarding_completed"):
            item_reasons.append("Onboarding is incomplete.")
        if not user_profile.get("telegram_alerts_enabled"):
            item_reasons.append("Telegram alerts are disabled.")
        if not link.get("telegram_chat_id"):
            item_reasons.append("Telegram is not connected.")
        if already_sent:
            item_reasons.append("Preview alert already sent.")
        delivery_ready = (
            score["matched"]
            and bool(normalized.get("review_status"))
            and bool(user_profile.get("onboarding_completed"))
            and bool(user_profile.get("telegram_alerts_enabled"))
            and bool(link.get("telegram_chat_id"))
            and not already_sent
        )
        matches.append({
            **normalized,
            "score": score["score"],
            "matched": score["matched"],
            "reasons": score["reasons"],
            "limitations": list(dict.fromkeys(normalized["limitations"] + score["limitations"])),
            "already_sent": already_sent,
            "delivery_ready": delivery_ready,
            "not_ready_reasons": item_reasons,
        })

    matches.sort(key=lambda item: (item["matched"], item["score"], item.get("reviewed_at") or ""), reverse=True)
    return {
        "ok": True,
        "days": safe_days,
        "alerts_considered": len(candidates),
        "matches": matches,
        "empty_state": "No approved reviewed alerts found in the selected window." if not candidates else None,
        "profile_ready": not not_ready_reasons,
        "not_ready_reasons": not_ready_reasons,
    }


def _truncate(text: str, limit: int) -> str:
    value = str(text or "").strip()
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)] + "..."


def build_alert_telegram_message(user_profile: dict, alert_match: dict) -> str:
    reviewed = (alert_match.get("reviewed_at") or "Reviewed").split("T")[0]
    reasons = alert_match.get("reasons") or ["Approved reviewed alert matched to your saved profile"]
    limitations = alert_match.get("limitations") or ["No additional limitations recorded in the alert draft."]
    lines = [
        "StatuteProof - Reviewed alert preview",
        "",
        f"Source: {alert_match.get('source_name') or 'Official source'}",
        f"Market: {alert_match.get('market') or alert_match.get('jurisdiction') or 'Not specified'}",
        f"Type: {alert_match.get('change_type') or 'Regulatory update'}",
        f"Risk: {alert_match.get('risk_level') or 'MEDIUM'}",
        f"Reviewed: {reviewed}",
        "",
        "Summary:",
        _truncate(alert_match.get("executive_summary") or "", 900),
        "",
        "Why it matches your profile:",
    ]
    lines.extend(f"- {_truncate(reason, 180)}" for reason in reasons[:4])
    lines.extend(["", "Source proof:", str(alert_match.get("source_url") or "Source URL unavailable")])
    lines.extend(["", "Limitations:"])
    lines.extend(f"- {_truncate(note, 220)}" for note in limitations[:4])
    lines.extend([
        "",
        "This alert was reviewed by a human editor and matched to your profile.",
        "Not legal advice. Manage alerts: StatuteProof -> Integrations",
    ])
    return _truncate("\n".join(lines), 4096)


def _is_still_approved(alert_id: str) -> bool:
    try:
        from app.alert_review import latest_review_for
    except Exception:
        return False
    review = latest_review_for(alert_id)
    return bool(review and review.get("new_status") in _get_approved_statuses())


def send_preview_alert_to_user(user_id: int, alert_id: str) -> dict:
    safe_alert_id = str(alert_id or "").strip()
    preview = build_routing_preview_for_user(int(user_id))
    match = next((item for item in preview["matches"] if item.get("alert_id") == safe_alert_id), None)
    if not match:
        return {"ok": False, "reason": "Alert not found.", "code": "not_found"}
    if not match.get("delivery_ready"):
        return {
            "ok": False,
            "reason": "Alert is not ready for delivery.",
            "code": "not_ready",
            "details": match.get("not_ready_reasons") or [],
        }
    if not _is_still_approved(safe_alert_id):
        return {"ok": False, "reason": "Alert is no longer approved.", "code": "not_ready"}

    link = get_telegram_link(int(user_id))
    chat_id = link.get("telegram_chat_id")
    if not chat_id:
        return {"ok": False, "reason": "Telegram not connected.", "code": "not_ready"}

    user_profile = user_profile_to_routing_profile(int(user_id))
    message = build_alert_telegram_message(user_profile, match)
    log = create_delivery_log(
        int(user_id),
        delivery_type="reviewed_alert_preview",
        channel="telegram",
        status="pending",
        title=match.get("title"),
        message_preview=message,
        source_id=match.get("source_id"),
        alert_id=safe_alert_id,
        idempotency_key=f"{int(user_id)}:reviewed_alert_preview:{safe_alert_id}",
        metadata={
            "preview": True,
            "relevance_score": match.get("score"),
            "review_status": match.get("review_status"),
        },
    )
    if not log.get("created"):
        return {"ok": False, "reason": "This preview alert was already sent.", "code": "duplicate"}

    log_id = int(log["id"])
    if send_telegram_message(str(chat_id), message):
        update_delivery_log_sent(log_id)
        return {"ok": True, "message": "Preview alert sent to your Telegram.", "log_id": log_id}

    update_delivery_log_failed(log_id, "Telegram send failed.")
    return {"ok": False, "reason": "Telegram send failed.", "code": "telegram_failed", "log_id": log_id}
