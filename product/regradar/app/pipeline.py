"""
Main pipeline orchestrator — v4.2.

run_pipeline(url) flow:
  1. fetch_page          — two-tier HTTP / Playwright scraper
  2. extract_text        — BS4 parser → clean paragraph text
  3. SHA-256 hash        — fingerprint of new content
  4. get_latest_document — most recent stored version
  5. hash compare        — early exit if identical
  6. diff (or baseline)  — structured paragraph delta
  7. rule-based risk     — keyword scoring (always runs)
  8. AI analysis         — Claude (optional; falls back to rule-based)
  9. save_document       — new historical row with all metadata
 10. Telegram alert      — MEDIUM/HIGH only; skipped on first run
 11. return result

Return contract
---------------
Unchanged:
    {"url": str, "changed": False}

First run (baseline):
    {
        "url":           str,
        "changed":       True,
        "is_new":        True,
        "risk_level":    str,
        "risk_reason":   str,
        "ai_used":       False,         # never run AI on baseline
        "telegram_sent": False,         # never alert on baseline
        "executive_summary":      str,
        "business_action_required": str,
        "added_count":   int,
        "added":         list[str],
        "removed_count": 0,
        "removed":       [],
        "modified_count":0,
        "chars":         int,
        "created_at":    str,
    }

Changed (subsequent run):
    {
        "url":           str,
        "changed":       True,
        "is_new":        False,
        "risk_level":    str,
        "risk_reason":   str,
        "ai_used":       bool,
        "telegram_sent": bool,
        "executive_summary":      str,
        "business_action_required": str,
        "added_count":   int,
        "added":         list[str],
        "removed_count": int,
        "removed":       list[str],
        "modified_count":int,
        "chars":         int,
        "created_at":    str,
    }
"""

import logging
from datetime import datetime

from app.adapters.base import is_quality_content
from app.adapters.registry import get_adapter_for_url
from app.config import (
    AI_DETECT_LANGUAGE,
    AI_MAX_CALLS_PER_RUN,
    AI_MIN_RISK_FOR_ANALYSIS,
    AI_OUTPUT_LANGUAGE,
    ENABLE_AI_ANALYSIS,
    ENABLE_TELEGRAM_ALERTS,
)
from app.language import detect_language_hint
from app.db import get_latest_document, init_db, save_document
from app.diff import get_diff
from app.extractors import extract_best_text
from app.risk import analyze_risk
from app.scraper import fetch_page
from app.source_runs import stable_content_hash

logger = logging.getLogger(__name__)

# Initialise DB schema once per process on module import rather than once per
# run_pipeline() call, which caused 50+ redundant schema checks in batch runs.
init_db()

_ALERT_THRESHOLD = {"MEDIUM", "HIGH"}
_RISK_ORDER: dict[str, int] = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}

# Per-run AI call budget.  Initialised at module load; reset by
# reset_ai_call_counter() before each batch (monitor_all_sources / watch loop).
_AI_RUN_BUDGET: dict = {"count": 0, "limit": AI_MAX_CALLS_PER_RUN}


def reset_ai_call_counter(limit: int | None = None) -> None:
    """Reset the per-run AI call budget before a new batch of pipeline calls."""
    _AI_RUN_BUDGET["count"] = 0
    _AI_RUN_BUDGET["limit"] = limit if limit is not None else AI_MAX_CALLS_PER_RUN


def _extraction_quality(chars: int) -> str:
    if chars >= 500:
        return "good"
    if chars > 0:
        return "low_content"
    return "failed"


def run_pipeline(url: str, source: dict | None = None) -> dict:
    """
    Execute the full change-detection pipeline for a single URL.

    Parameters
    ----------
    url : str
        The URL to monitor.
    source : dict | None
        Optional source entry from sources.json.  When provided, it is
        passed to the adapter registry so adapters can use metadata
        (jurisdiction, category, etc.) for dispatch decisions.

    Raises
    ------
    TimeoutError  — propagated from scraper on page-load timeout.
    ValueError    — propagated from scraper on empty HTML.
    """
    # ── Step 0: Source-specific adapter (optional) ────────────────────
    # Adapters provide richer content for sites the generic scraper cannot
    # handle well (JS-rendered pages, XHR-loaded document lists).
    # If an adapter returns quality content it replaces steps 1-2 entirely.
    content: str | None = None
    adapter_used: str | None = None
    _generic_method: str = "generic"   # updated when extract_best_text runs

    adapter = get_adapter_for_url(url, source)
    if adapter is not None:
        logger.info("Trying adapter %r for %s", adapter.name, url)
        try:
            adapter_text = adapter.fetch_content(url, source)
        except Exception as exc:
            logger.warning(
                "Adapter %r raised unexpectedly: %s: %s",
                adapter.name, type(exc).__name__, exc,
            )
            adapter_text = None

        if is_quality_content(adapter_text):
            content = adapter_text
            adapter_used = adapter.name
            logger.info(
                "Adapter %r accepted: %d chars for %s",
                adapter.name, len(content), url,
            )
            print(
                f"  Adapter '{adapter.name}' supplied {len(content):,} chars",
                flush=True,
            )
        else:
            logger.info(
                "Adapter %r content below quality threshold (%d chars) "
                "— falling back to generic scraper",
                adapter.name,
                len(adapter_text) if adapter_text else 0,
            )

    if content is None:
        # ── Step 1: Fetch ──────────────────────────────────────────────
        logger.info("Pipeline start (generic scraper): %s", url)
        html = fetch_page(url)

        # ── Step 2: Extract (multi-strategy) ─────────────────────────
        _extr           = extract_best_text(html, url)
        content         = _extr["text"]
        _generic_method = _extr["method"]

    logger.info("Content: %d chars for %s (adapter=%s)", len(content), url, adapter_used)

    extracted_chars    = len(content)
    extraction_method  = f"adapter:{adapter_used}" if adapter_used else _generic_method

    # Detect source language for AI prompt context and result metadata.
    # Runs on clean extracted text (not raw HTML) for best accuracy.
    src_lang = detect_language_hint(content) if AI_DETECT_LANGUAGE else "unknown"
    logger.info("Detected source language: %s for %s", src_lang, url)

    # ── Step 3: Hash ─────────────────────────────────────────────────
    new_hash = stable_content_hash(content)

    # ── Step 4: Load latest version ──────────────────────────────────
    latest = get_latest_document(url)

    # ── Step 5: Hash comparison ───────────────────────────────────────
    if latest is not None and latest["content_hash"] == new_hash:
        logger.info("No changes: %s", url)
        return {
            "url":                url,
            "changed":            False,
            "extracted_chars":    extracted_chars,
            "extraction_quality": _extraction_quality(extracted_chars),
            "extraction_method":  extraction_method,
            "ai_skipped_reason":  "",
            "ai_calls_used":      _AI_RUN_BUDGET["count"],
        }

    # ── Step 6: Build diff / baseline diff ───────────────────────────
    is_new = latest is None

    if is_new:
        # Baseline run: treat entire content as "added" for risk scoring.
        # Telegram alert is suppressed regardless of risk.
        all_paras   = [p.strip() for p in content.split("\n\n") if p.strip()]
        diff_result = {
            "has_changes":    True,
            "added":          all_paras,
            "removed":        [],
            "modified_count": 0,
        }
    else:
        diff_result = get_diff(latest["content"], content)

    # ── Step 7: Rule-based risk (always) ─────────────────────────────
    rule_risk = analyze_risk(diff_result)
    logger.info(
        "Rule-based risk: %s (%s)",
        rule_risk["risk_level"], rule_risk["reason"],
    )

    # ── Step 8: AI analysis (optional, graceful fallback) ─────────────
    ai_result         = None
    ai_used           = False
    ai_skipped_reason = ""

    if ENABLE_AI_ANALYSIS and not is_new:
        rule_level = rule_risk["risk_level"]

        if _RISK_ORDER.get(rule_level, 0) < _RISK_ORDER.get(AI_MIN_RISK_FOR_ANALYSIS, 1):
            ai_skipped_reason = (
                f"rule-based risk {rule_level} below threshold {AI_MIN_RISK_FOR_ANALYSIS}"
            )
            logger.info("AI skipped — %s", ai_skipped_reason)

        elif _AI_RUN_BUDGET["count"] >= _AI_RUN_BUDGET["limit"]:
            ai_skipped_reason = (
                f"call limit {_AI_RUN_BUDGET['limit']} per run reached"
            )
            logger.info("AI skipped — %s", ai_skipped_reason)

        else:
            _AI_RUN_BUDGET["count"] += 1
            from app.ai import analyze_change_with_ai
            ai_result = analyze_change_with_ai(
                url, diff_result, rule_risk,
                source_language = src_lang,
                output_language = AI_OUTPUT_LANGUAGE,
            )
            ai_used = ai_result is not None
            if not ai_used:
                logger.info("AI analysis unavailable — using rule-based result")

    # ── Resolve final risk assessment ────────────────────────────────
    if ai_used and ai_result:
        final_risk_level  = ai_result["risk_level"]
        final_risk_reason = ai_result["reason"]
        executive_summary = ai_result["executive_summary"]
        business_action   = ai_result["business_action_required"]
        source_language   = ai_result.get("source_language", src_lang)
        output_language   = ai_result.get("output_language", AI_OUTPUT_LANGUAGE)
        affected_entities = ai_result.get("affected_entities", [])
        urgency           = ai_result.get("urgency", "")
        deadline          = ai_result.get("deadline")
        semantic_findings = ai_result.get("semantic_findings", {})
        confidence        = ai_result.get("confidence", "medium")
    else:
        final_risk_level  = rule_risk["risk_level"]
        final_risk_reason = rule_risk["reason"]
        executive_summary = (
            f"Detected regulatory change at {url}. "
            f"Rule-based screening: {rule_risk['reason']}."
        )
        business_action = (
            "Review the detected changes against current compliance policies "
            "and escalate to legal if required."
        )
        source_language   = src_lang
        output_language   = AI_OUTPUT_LANGUAGE
        affected_entities = []
        urgency           = ""
        deadline          = None
        semantic_findings = {}
        # Rule-based confidence: LOW risk from rules is reasonably reliable;
        # HIGH/MEDIUM without semantic validation should flag low confidence.
        confidence        = "low" if final_risk_level in ("HIGH", "MEDIUM") else "medium"

    # review_required / review_reason — AI result takes priority; rule-based fallback.
    if ai_used and ai_result:
        review_required = ai_result.get("review_required", False)
        review_reason   = ai_result.get("review_reason", "")
    elif final_risk_level == "HIGH":
        review_required = True
        review_reason   = (
            "High-risk classification was generated by rule-based logic. "
            "AI or human compliance review is recommended before client-facing action."
        )
    elif final_risk_level == "MEDIUM":
        review_required = True
        review_reason   = (
            "Medium-risk classification was generated by rule-based logic. "
            "Review is recommended to confirm whether the change is material."
        )
    else:  # LOW
        review_required = False
        review_reason   = (
            "No immediate review required based on current rule-based signals."
        )

    # ── Step 9: Persist new historical version ────────────────────────
    created_at = datetime.utcnow().isoformat()
    save_document(
        url             = url,
        content         = content,
        risk_level      = final_risk_level,
        risk_reason     = final_risk_reason,
        ai_summary      = executive_summary if ai_used else None,
        business_action = business_action   if ai_used else None,
    )
    logger.info(
        "Saved version: url=%s risk=%s ai=%s added=%d removed=%d",
        url, final_risk_level, ai_used,
        len(diff_result["added"]), len(diff_result["removed"]),
    )

    # ── Step 10: Telegram alert (MEDIUM/HIGH, never on baseline) ──────
    telegram_sent = False

    if ENABLE_TELEGRAM_ALERTS and not is_new and final_risk_level in _ALERT_THRESHOLD:
        from app.telegram import send_telegram_alert

        alert_payload = {
            "url":                     url,
            "risk_level":              final_risk_level,
            "risk_reason":             final_risk_reason,
            "executive_summary":       executive_summary,
            "business_action_required":business_action,
            "ai_used":                 ai_used,
            "added_count":             len(diff_result["added"]),
            "removed_count":           len(diff_result["removed"]),
        }
        telegram_sent = send_telegram_alert(alert_payload)

    # ── Step 11: Return structured result ─────────────────────────────
    return {
        "url":                      url,
        "changed":                  True,
        "is_new":                   is_new,
        "risk_level":               final_risk_level,
        "risk_reason":              final_risk_reason,
        "review_required":          review_required,
        "review_reason":            review_reason,
        "ai_used":                  ai_used,
        "telegram_sent":            telegram_sent,
        "executive_summary":        executive_summary,
        "business_action_required": business_action,
        "source_language":          source_language,
        "output_language":          output_language,
        "affected_entities":        affected_entities,
        "urgency":                  urgency,
        "deadline":                 deadline,
        "semantic_findings":        semantic_findings,
        "confidence":               confidence,
        "added_count":              len(diff_result["added"]),
        "added":                    diff_result["added"],
        "removed_count":            len(diff_result["removed"]),
        "removed":                  diff_result["removed"],
        "modified_count":           diff_result["modified_count"],
        "ai_skipped_reason":        ai_skipped_reason,
        "ai_calls_used":            _AI_RUN_BUDGET["count"],
        "chars":                    extracted_chars,
        "extracted_chars":          extracted_chars,
        "extraction_quality":       _extraction_quality(extracted_chars),
        "extraction_method":        extraction_method,
        "created_at":               created_at,
    }


def run_pipeline_for_source(source: dict) -> dict:
    """
    Run the pipeline for a source dict from sources.json.

    Calls run_pipeline(url) and attaches source metadata to the result.

    Parameters
    ----------
    source : dict
        A validated source entry with keys: name, url, jurisdiction,
        category, enabled.

    Returns
    -------
    dict
        The full pipeline result dict, extended with:
          source_name  — source["name"]
          jurisdiction — source["jurisdiction"]
          category     — source["category"]
          status       — "ok"
    """
    url    = source["url"]
    result = run_pipeline(url, source=source)
    result["source_name"]   = source.get("name", url)
    result["jurisdiction"]  = source.get("jurisdiction", "")
    result["category"]      = source.get("category", "")
    result["source_status"] = source.get("status", "active")
    result["status"]        = "ok"
    return result
