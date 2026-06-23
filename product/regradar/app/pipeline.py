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
import threading
from datetime import datetime, timezone

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
from app.text_normalization import normalize_for_change_hash, stable_content_hash

logger = logging.getLogger(__name__)

_ALERT_THRESHOLD = {"MEDIUM", "HIGH"}
_RISK_ORDER: dict[str, int] = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}

# Per-run AI call budget.  Initialised at module load; reset by
# reset_ai_call_counter() before each batch (monitor_all_sources / watch loop).
# _AI_BUDGET_LOCK guards the check-then-increment to prevent over-spending under
# ThreadingHTTPServer (multiple threads can enter run_pipeline concurrently).
_AI_RUN_BUDGET: dict = {"count": 0, "limit": AI_MAX_CALLS_PER_RUN}
_AI_BUDGET_LOCK: threading.Lock = threading.Lock()

_DB_READY: bool = False


def init_pipeline(ai_limit: int | None = None) -> None:
    """
    Initialise DB schema and reset AI budget for a new batch run.

    Call once before monitor_all_sources() or any batch of run_pipeline()
    calls.  Safe to call multiple times — init_db() is idempotent.
    """
    global _DB_READY
    if not _DB_READY:
        init_db()
        _DB_READY = True
    reset_ai_call_counter(ai_limit)


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
            content = adapter_text or ""
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
        content         = _extr["text"] or ""
        _generic_method = _extr["method"]

    content = content or ""
    logger.info("Content: %d chars for %s (adapter=%s)", len(content), url, adapter_used)

    extracted_chars    = len(content) if content else 0
    extraction_method  = f"adapter:{adapter_used}" if adapter_used else _generic_method

    # ── Guard: empty / None content → quality_drop ───────────────────
    if not content or not content.strip():
        logger.warning("Empty content returned for %s — aborting with quality_drop", url)
        return {
            "url":                url,
            "changed":            False,
            "status":             "quality_drop",
            "extracted_chars":    extracted_chars,
            "extraction_quality": "failed",
            "extraction_method":  extraction_method,
            "ai_skipped_reason":  "quality_drop",
            "ai_calls_used":      _AI_RUN_BUDGET["count"],
        }

    # Detect source language for AI prompt context and result metadata.
    # Runs on clean extracted text (not raw HTML) for best accuracy.
    src_lang = detect_language_hint(content) if AI_DETECT_LANGUAGE else "unknown"
    logger.info("Detected source language: %s for %s", src_lang, url)

    # ── Step 3: Hash (from normalized text to avoid false positives) ──
    # normalize_for_change_hash strips volatile render-time fragments
    # (timestamps, visitor counters) before hashing so that only genuine
    # regulatory text changes produce a new hash.
    normalized_for_hash = normalize_for_change_hash(content)
    new_hash = stable_content_hash(normalized_for_hash)

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
        normalized_old = normalize_for_change_hash(latest["content"])
        normalized_new = normalize_for_change_hash(content)
        diff_result = get_diff(normalized_old, normalized_new)

    # ── Step 3b: Write snapshot files ────────────────────────────────
    # Runs after diff is confirmed real (past hash-check early-exit).
    # Non-fatal — a failed write never breaks the pipeline.
    _snapshot_paths_result: dict = {}
    _run_id = ""
    _source_id = ""
    _market = ""
    _ts_utc = ""
    if source is not None:
        try:
            import uuid as _uuid
            from app.source_runs import write_snapshots, make_source_id, now_utc
            _run_id = _uuid.uuid4().hex[:8]
            _source_id = make_source_id(source)
            _market = str(source.get("jurisdiction", source.get("market", "AE"))).upper()
            _ts_utc = now_utc()
            _snapshot_paths_result = write_snapshots(
                timestamp_utc=_ts_utc,
                market=_market,
                source_id=_source_id,
                run_id=_run_id,
                raw_text=content or "",
                normalized_text=normalized_for_hash or "",
                pdf_text="",
                metadata={
                    "url": url,
                    "source_id": _source_id,
                    "fetched_at": _ts_utc,
                    "extraction_method": extraction_method,
                },
            )
            logger.info("Snapshots written for run_id=%s source=%s", _run_id, _source_id)
        except Exception as _snap_err:
            logger.warning("Snapshot write failed (non-fatal): %s", _snap_err)
            _snapshot_paths_result = {}

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

        else:
            # Atomically check and reserve one AI call slot (thread-safe under
            # ThreadingHTTPServer — lock covers only the cheap dict mutation,
            # not the network call itself).
            _budget_reserved = False
            with _AI_BUDGET_LOCK:
                if _AI_RUN_BUDGET["count"] >= _AI_RUN_BUDGET["limit"]:
                    ai_skipped_reason = (
                        f"call limit {_AI_RUN_BUDGET['limit']} per run reached"
                    )
                    logger.info("AI skipped — %s", ai_skipped_reason)
                else:
                    _AI_RUN_BUDGET["count"] += 1
                    _budget_reserved = True
            if _budget_reserved:
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
    created_at = datetime.now(timezone.utc).isoformat()
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

    # ── Auto-create canonical evidence for changed/first_seen runs ────
    result_status = "FIRST_SEEN" if is_new else "CHANGED"
    # Build a minimal run_record from available pipeline state.
    # create_canonical_evidence_record requires proof_block_path,
    # snapshot_raw_path, snapshot_normalized_path, etc. which are only
    # populated when the source monitor pipeline writes snapshot files.
    # When those paths are absent the call is non-fatal: evidence creation
    # is skipped and the warning is logged so the source monitor agent
    # can produce the record from the full run record later.
    run_record_candidate: dict = {
        "url": url,
        "change_status": result_status,
        "created_at": created_at,
    }
    if source is not None:
        run_record_candidate["source_id"] = _source_id or source.get("id") or source.get("source_id") or ""
        run_record_candidate["source_name"] = source.get("name") or source.get("source_name") or ""
        run_record_candidate["official_url"] = source.get("url") or url
        run_record_candidate["regulator"] = source.get("regulator") or source.get("family") or source.get("jurisdiction") or ""
    if _snapshot_paths_result:
        run_record_candidate["run_id"] = _run_id
        run_record_candidate["market"] = _market
        run_record_candidate["timestamp_utc"] = _ts_utc
        run_record_candidate["snapshot_raw_path"] = _snapshot_paths_result.get("snapshot_raw_path")
        run_record_candidate["snapshot_normalized_path"] = _snapshot_paths_result.get("snapshot_normalized_path")
        run_record_candidate["snapshot_pdf_text_path"] = _snapshot_paths_result.get("snapshot_pdf_text_path")
        run_record_candidate["snapshot_metadata_path"] = _snapshot_paths_result.get("snapshot_metadata_path")
    # Only attempt canonical evidence creation when all required snapshot paths
    # are present.  The full source-monitor pipeline populates these fields;
    # the lightweight pipeline path (run_pipeline called directly) does not,
    # so the call would always raise — guard here avoids masking real errors.
    _required_evidence_fields = (
        run_record_candidate.get("proof_block_path")
        and run_record_candidate.get("snapshot_raw_path")
        and run_record_candidate.get("snapshot_normalized_path")
        and run_record_candidate.get("run_id")
        and run_record_candidate.get("source_id")
        and run_record_candidate.get("source_name")
        and run_record_candidate.get("official_url")
        and (run_record_candidate.get("timestamp_utc") or run_record_candidate.get("run_at"))
    )
    if _required_evidence_fields:
        try:
            from app.evidence_records import create_canonical_evidence_record
            create_canonical_evidence_record(run_record_candidate)
            logger.info("Canonical evidence created for run at %s", url)
        except Exception as ev_err:
            logger.warning("Canonical evidence creation failed (non-fatal): %s", ev_err)
    else:
        logger.debug(
            "Skipping canonical evidence — snapshot paths not yet provided for %s", url
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
        # Snapshot fields — populated when source context is present
        "run_id":                   _run_id,
        "snapshot_raw_path":        _snapshot_paths_result.get("snapshot_raw_path"),
        "snapshot_normalized_path": _snapshot_paths_result.get("snapshot_normalized_path"),
        "snapshot_pdf_text_path":   _snapshot_paths_result.get("snapshot_pdf_text_path"),
        "snapshot_metadata_path":   _snapshot_paths_result.get("snapshot_metadata_path"),
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

    # ── Wire source_runs: append full run record, write diffs/proofs ──
    if result.get("changed") and result.get("run_id"):
        try:
            import uuid as _uuid2
            from app.source_runs import append_run, make_source_id

            run_record = {
                "run_id":                   result.get("run_id") or _uuid2.uuid4().hex[:8],
                "source_id":                make_source_id(source),
                "source_name":              source.get("name", ""),
                "official_url":             source.get("url", ""),
                "url":                      source.get("url", ""),
                "market":                   source.get("jurisdiction", "AE").upper(),
                "jurisdiction":             source.get("jurisdiction", "AE"),
                "category":                 source.get("category", ""),
                "change_status":            "FIRST_SEEN" if result.get("is_new") else "CHANGED",
                "risk_level":               result.get("risk_level", "LOW"),
                "risk_reason":              result.get("risk_reason", ""),
                "executive_summary":        result.get("executive_summary", ""),
                "business_action":          result.get("business_action_required", ""),
                "ai_used":                  result.get("ai_used", False),
                "confidence":               result.get("confidence", "low"),
                "urgency":                  result.get("urgency", ""),
                "deadline":                 result.get("deadline"),
                "review_required":          result.get("review_required", False),
                "review_reason":            result.get("review_reason", ""),
                "added_count":              result.get("added_count", 0),
                "removed_count":            result.get("removed_count", 0),
                "modified_count":           result.get("modified_count", 0),
                "chars":                    result.get("chars", 0),
                "extracted_chars":          result.get("extracted_chars", 0),
                "extraction_quality":       result.get("extraction_quality", ""),
                "extraction_method":        result.get("extraction_method", ""),
                "snapshot_raw_path":        result.get("snapshot_raw_path"),
                "snapshot_normalized_path": result.get("snapshot_normalized_path"),
                "snapshot_pdf_text_path":   result.get("snapshot_pdf_text_path"),
                "snapshot_metadata_path":   result.get("snapshot_metadata_path"),
                "run_at":                   result.get("created_at", datetime.now(timezone.utc).isoformat()),
                "timestamp_utc":            result.get("created_at", datetime.now(timezone.utc).isoformat()),
            }

            final_record = append_run(run_record)
            result["run_record"] = final_record
            logger.info(
                "source_runs.append_run completed: source=%s run_id=%s status=%s",
                source.get("name"), final_record.get("run_id"), final_record.get("change_status"),
            )

            # ── Wire alert drafts for CHANGED runs (not FIRST_SEEN baseline) ──
            if not result.get("is_new") and final_record.get("change_status") == "CHANGED":
                try:
                    from pathlib import Path as _Path
                    from app.alert_drafts import build_alert_draft, write_alert_artifacts, load_json_artifact

                    _base_dir = _Path(__file__).resolve().parents[1]

                    # Load diff artifact — written by append_run into diff_json_path
                    diff_artifact = load_json_artifact(final_record.get("diff_json_path"), _base_dir)
                    # Fall back to a minimal structure built from pipeline result lists
                    if not diff_artifact:
                        diff_artifact = {
                            "added_chunks":  result.get("added", []),
                            "removed_chunks": result.get("removed", []),
                            "changed_chunks": [],
                            "diff_summary":  (
                                f"Added: {result.get('added_count', 0)}, "
                                f"Removed: {result.get('removed_count', 0)}, "
                                f"Modified: {result.get('modified_count', 0)}"
                            ),
                            "meaningful_change_detected": True,
                            "diff_quality": "PARTIAL",
                            "added_count": result.get("added_count", 0),
                            "removed_count": result.get("removed_count", 0),
                            "changed_count": result.get("modified_count", 0),
                        }

                    # Load proof block — written by append_run into proof_block_path
                    proof_block = load_json_artifact(final_record.get("proof_block_path"), _base_dir)
                    if not proof_block:
                        proof_block = {
                            "official_url": source.get("url", ""),
                            "normalized_hash": "",
                            "proof_quality": "INCOMPLETE",
                            "limitations_notes": "Proof block unavailable at alert-draft time.",
                        }

                    alert = build_alert_draft(final_record, diff_artifact, proof_block)
                    if alert:
                        # Resolve the snapshot directory for writing alert artifacts
                        snap_raw = final_record.get("snapshot_raw_path")
                        if snap_raw:
                            snap_dir = (_base_dir / snap_raw).parent
                        else:
                            snap_dir = _base_dir / "data" / "alert_drafts" / final_record.get("source_id", "unknown")
                        snap_dir.mkdir(parents=True, exist_ok=True)
                        artifact_paths = write_alert_artifacts(alert, snap_dir)
                        result["alert_draft_json_path"] = artifact_paths.get("alert_draft_json_path")
                        result["alert_draft_md_path"] = artifact_paths.get("alert_draft_md_path")
                        logger.info(
                            "Alert draft written: source=%s risk=%s path=%s",
                            source.get("name"), alert.get("risk_level"),
                            artifact_paths.get("alert_draft_json_path"),
                        )
                except Exception as _ad_err:
                    logger.warning("Alert draft failed (non-fatal): %s", _ad_err)

        except Exception as _sr_err:
            logger.warning("source_runs.append_run failed (non-fatal): %s", _sr_err)

    return result
