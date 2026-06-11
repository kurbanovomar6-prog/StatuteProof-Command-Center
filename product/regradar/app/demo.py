"""
RegRadar v7 — demo mode.

run_demo_change() produces a realistic simulated regulatory change
for client demonstrations.

Guarantees:
- Never writes to the database.
- Never calls the Claude API.
- Never sends real production Telegram alerts.
- Works fully offline without any API keys.
- All output is clearly marked DEMO.
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

_DEMO_URL  = "demo://regulatory-change"
_DEMO_NAME = "[DEMO] National Financial Monitoring Agency — Regulatory Update"
_DEMO_JUR  = "DEMO"
_DEMO_CAT  = "financial_regulator"


def _build_content(deadline: str) -> tuple[list[str], str, str, str]:
    """Return (added_paras, executive_summary, business_action, risk_reason)."""

    paras = [
        (
            f"Article 14(a) — Enhanced STR Reporting Threshold. "
            f"With effect from {deadline}, all licensed financial institutions — "
            f"including commercial banks, payment service providers, fintech "
            f"companies, and virtual asset service providers (VASPs) — must file "
            f"a Suspicious Transaction Report (STR) within 24 hours of detecting "
            f"any transaction at or exceeding USD 50,000 (or equivalent in local "
            f"currency). The previous reporting threshold of USD 75,000 is hereby "
            f"repealed. Failure to file within the prescribed period shall attract "
            f"a fine of USD 25,000 per unreported transaction."
        ),
        (
            "Article 14(b) — Mandatory Licensing for Virtual Asset Service Providers. "
            "Any entity that provides virtual asset exchange, custody, or transfer "
            "services to clients must obtain a Type-II Financial Services Licence "
            "from the National Financial Monitoring Agency within 180 days of the "
            "effective date. Continued operation without a valid licence constitutes "
            "a criminal offence and may result in a fine of up to USD 500,000 per day "
            "of non-compliance. Directors and senior managers may be held personally "
            "and criminally liable under amended Section 42 of the Financial Crime Act."
        ),
        (
            f"Article 14(c) — Enhanced Due Diligence for Politically Exposed Persons. "
            f"Financial institutions must apply Enhanced Due Diligence (EDD) to all "
            f"customers classified as Politically Exposed Persons (PEPs), their close "
            f"associates, and all correspondent banking relationships. A retrospective "
            f"EDD review of all existing PEP relationships must be completed and "
            f"submitted to the regulator by {deadline}. Institutions must integrate "
            f"automated PEP screening from a vendor on the approved list published "
            f"separately. Non-compliance will result in immediate licence suspension "
            f"pending investigation."
        ),
    ]

    executive_summary = (
        f"The National Financial Monitoring Agency has issued a significant AML/CFT "
        f"regulatory update with three material changes effective {deadline}. "
        f"First, the STR reporting threshold is lowered from USD 75,000 to USD 50,000, "
        f"substantially increasing the transaction monitoring workload for all licensed "
        f"institutions. Second, a new mandatory licensing regime covers all virtual asset "
        f"service providers, with a 180-day compliance window and criminal penalties — "
        f"including director liability — for non-compliance. Third, Enhanced Due Diligence "
        f"is mandatory for all PEPs and correspondent banking relationships, requiring a "
        f"full retrospective audit to be submitted by {deadline}. Immediate compliance "
        f"planning is required across all affected business lines."
    )

    business_action = (
        f"1. Brief compliance, legal, and senior management on new AML obligations today. "
        f"2. Update transaction monitoring rules to alert on transactions at or above USD 50,000. "
        f"3. If operating any VASP or crypto-related services, initiate the Type-II licence "
        f"application without delay — the 180-day window has already started. "
        f"4. Commission a retrospective EDD audit of all PEP and correspondent relationships. "
        f"5. Procure and integrate an approved automated PEP screening solution. "
        f"6. Update AML/CFT policies, procedures, and staff training materials. "
        f"All actions must be completed before {deadline}."
    )

    risk_reason = (
        f"HIGH — mandatory AML reporting obligation with lowered STR threshold "
        f"(USD 75k → USD 50k), criminal VASP licensing penalty (USD 500k/day + "
        f"director liability), PEP EDD retrospective deadline ({deadline}). "
        f"Affects banks, fintechs, payment providers, and all VASPs."
    )

    return paras, executive_summary, business_action, risk_reason


def _send_demo_telegram(executive_summary: str, business_action: str) -> bool:
    """
    Send a clearly DEMO-marked Telegram alert using existing credentials.

    Returns True if the message was accepted, False on any failure.
    If ENABLE_TELEGRAM_ALERTS is False or credentials are missing, returns
    False immediately without error.
    """
    try:
        from app.config import (
            ENABLE_TELEGRAM_ALERTS,
            TELEGRAM_BOT_TOKEN,
            TELEGRAM_CHAT_ID,
        )

        if not ENABLE_TELEGRAM_ALERTS or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            logger.info(
                "Demo Telegram skipped: ENABLE_TELEGRAM_ALERTS=%s, "
                "token present=%s, chat_id present=%s",
                ENABLE_TELEGRAM_ALERTS, bool(TELEGRAM_BOT_TOKEN), bool(TELEGRAM_CHAT_ID),
            )
            return False

        import requests as _req

        text = (
            "[DEMO ALERT — NOT A REAL REGULATORY CHANGE]\n\n"
            "This is a demonstration of StatuteProof alert capabilities.\n\n"
            "Source: Demo Regulator — Compliance Update\n"
            "Risk Level: HIGH\n"
            "Jurisdiction: DEMO\n\n"
            f"Executive Summary:\n{executive_summary[:500]}...\n\n"
            f"Required Action:\n{business_action[:400]}...\n\n"
            "[END OF DEMO ALERT — StatuteProof]"
        )

        resp = _req.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=10,
        )
        if resp.ok:
            logger.info("Demo Telegram alert sent successfully")
            return True
        logger.warning("Demo Telegram alert failed: HTTP %d", resp.status_code)
        return False

    except Exception as exc:
        logger.warning("Demo Telegram alert error: %s: %s", type(exc).__name__, exc)
        return False


def run_demo_change(send_alert: bool = False) -> dict:
    """
    Produce a realistic simulated regulatory change for client demonstrations.

    Parameters
    ----------
    send_alert : bool
        If True, attempt to send a clearly DEMO-marked Telegram alert.
        Fails safely (returns telegram_sent=False) if credentials are
        missing or ENABLE_TELEGRAM_ALERTS is disabled.

    Returns
    -------
    dict
        A result dict matching the pipeline result contract, with
        ``is_demo=True``. No database writes, no AI calls.
    """
    deadline = (datetime.utcnow() + timedelta(days=90)).strftime("%d %B %Y")
    paras, executive_summary, business_action, risk_reason = _build_content(deadline)

    telegram_sent = _send_demo_telegram(executive_summary, business_action) if send_alert else False

    extracted_chars = sum(len(p) for p in paras)

    return {
        "url":                      _DEMO_URL,
        "source_name":              _DEMO_NAME,
        "jurisdiction":             _DEMO_JUR,
        "category":                 _DEMO_CAT,
        "changed":                  True,
        "is_new":                   False,
        "is_demo":                  True,
        "risk_level":               "HIGH",
        "risk_reason":              risk_reason,
        "executive_summary":        executive_summary,
        "business_action_required": business_action,
        "ai_used":                  False,
        # Multilingual fields (v9) — hardcoded for demo (no AI called)
        "source_language":          "en",
        "output_language":          "en",
        "affected_entities":        ["banks", "fintechs", "payment providers", "VASPs"],
        "urgency":                  "high",
        "deadline":                 deadline,
        # Semantic analysis (v11) — hardcoded for demo; shows what AI would detect
        "semantic_findings": {
            "new_obligation":       True,
            "deadline_detected":    True,
            "reporting_required":   True,
            "licensing_impact":     True,
            "enforcement_exposure": True,
            "operational_impact":   "high",
            "materiality":          "critical",
        },
        "confidence":       "high",
        "review_required":  True,
        "review_reason": (
            "Multiple concurrent HIGH-risk obligations: mandatory VASP licensing, "
            "lowered STR threshold, and PEP retrospective EDD deadline. "
            "Human compliance review is required before any client-facing action."
        ),
        "added_count":              len(paras),
        "added":                    paras,
        "removed_count":            0,
        "removed":                  [],
        "modified_count":           1,
        "extracted_chars":          extracted_chars,
        "extraction_quality":       "good",
        "extraction_method":        "demo",
        "telegram_sent":            telegram_sent,
        "created_at":               datetime.utcnow().isoformat(),
    }
