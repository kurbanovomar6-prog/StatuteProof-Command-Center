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
from app.text_normalization import (
    NORMALIZATION_VERSION,
    normalize_for_change_hash,
    stable_content_hash,
)
from app.text_quality import is_mostly_unreadable

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


def _sha256_or_none(text: str | None) -> str | None:
    """SHA-256 of the given text — same convention as source_runs._raw_hash."""
    if not text:
        return None
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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

    # ── Guard (F1): error pages are fetch failures, never baselines ────
    # A Cloudflare 502 / VARA 404 stored as baseline made the *recovery*
    # alert as CHANGED (2026-06-11, docs/signal/judgment_table.md).
    from app.text_normalization import looks_like_error_page
    if looks_like_error_page(content):
        logger.warning("Error page detected for %s — recording as failed, no baseline", url)
        return {
            "url":                url,
            "changed":            False,
            "status":             "error_page",
            "access_status":      "error_page",
            "extracted_chars":    extracted_chars,
            "extraction_quality": "failed",
            "extraction_method":  extraction_method,
            "error":              "Fetched content is an HTTP error/challenge page — not stored as baseline",
            "ai_skipped_reason":  "error_page",
            "ai_calls_used":      _AI_RUN_BUDGET["count"],
        }

    # ── Guard: undecodable content → quality_drop ─────────────────────
    # Write-layer chokepoint (VARA mojibake incident, 2026-07-10): no
    # matter which fetch path produced `content`, text saturated with
    # replacement/control characters is a mis-decoded body, not page
    # text — it must never be hashed, diffed, baselined, or alerted on.
    if is_mostly_unreadable(content):
        logger.warning(
            "Undecodable content for %s (%d chars) — aborting with quality_drop",
            url, len(content),
        )
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

    # ── Step 4: Resolve canonical baseline ────────────────────────────
    # Owner decision 2: the JSONL evidence-trail normalized hash is the
    # single source of truth for change classification. SQLite `documents`
    # is a derived index only — used as a fallback baseline solely when the
    # trail has no usable hash (legacy records, bare-URL CLI runs).
    latest = get_latest_document(url)
    prev_trail_record = None
    baseline_hash = None
    baseline_origin = "none"
    if source is not None:
        from app.source_runs import previous_run as _previous_run, make_source_id as _make_sid
        prev_trail_record = _previous_run(_make_sid(source))
        if prev_trail_record is not None:
            baseline_hash = (
                prev_trail_record.get("normalized_hash")
                or prev_trail_record.get("content_hash")
            )
            if baseline_hash:
                baseline_origin = "jsonl"
    if not baseline_hash and latest is not None:
        baseline_hash = latest["content_hash"]
        baseline_origin = "sqlite"

    # ── Step 5: Hash comparison against the canonical baseline ────────
    if baseline_hash and baseline_hash == new_hash:
        logger.info("No changes: %s (baseline=%s)", url, baseline_origin)
        # Keep the derived index aligned with the canonical hash. This is a
        # deliberate, loudly-logged realignment — not a silent auto-heal.
        if source is not None and (latest is None or latest["content_hash"] != new_hash):
            logger.warning(
                "DERIVED INDEX REALIGNED: sqlite documents hash %s != canonical %s "
                "for %s — inserting aligned row (evidence trail is authoritative)",
                (latest["content_hash"][:12] if latest is not None else "<missing>"),
                new_hash[:12], url,
            )
            save_document(url=url, content=content, content_hash=new_hash)
        return {
            "url":                url,
            "changed":            False,
            "extracted_chars":    extracted_chars,
            "extraction_quality": _extraction_quality(extracted_chars),
            "extraction_method":  extraction_method,
            "normalized_hash":    new_hash,
            "content_hash":       new_hash,
            "raw_hash":           _sha256_or_none(content),
            "raw_chars":          len(content or ""),
            "normalized_chars":   len(normalized_for_hash or ""),
            "normalization_version": NORMALIZATION_VERSION,
            "ai_skipped_reason":  "",
            "ai_calls_used":      _AI_RUN_BUDGET["count"],
        }

    # ── Step 6: Build diff / baseline diff ───────────────────────────
    is_new = baseline_hash is None

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
        # Old text for diffing: prefer the SQLite copy; fall back to the
        # previous trail record's normalized snapshot; if neither is
        # available, treat this run as a fresh baseline.
        old_text = latest["content"] if latest is not None else None
        if old_text is None and prev_trail_record is not None:
            from app.source_runs import _read_snapshot_text as _read_snap
            old_text = _read_snap(prev_trail_record.get("snapshot_normalized_path"))
        if old_text is None:
            is_new = True
            all_paras   = [p.strip() for p in content.split("\n\n") if p.strip()]
            diff_result = {
                "has_changes":    True,
                "added":          all_paras,
                "removed":        [],
                "modified_count": 0,
            }
        else:
            normalized_old = normalize_for_change_hash(old_text)
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

    # ── Step 6b (F2): rule-detected facts from the added delta ────────
    # Facts (deadlines, effective dates, amounts, law/licence refs) may be
    # stated in an alert ONLY when truly detected; spans prove each claim.
    from app.detected_facts import extract_detected_facts
    detected_facts = [] if is_new else extract_detected_facts(diff_result.get("added"))

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
        # Decision 2: the derived index stores the same canonical hash the
        # evidence trail records — never a separately computed one.
        content_hash    = new_hash,
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
    alert_suppressed_reason = ""

    if ENABLE_TELEGRAM_ALERTS and not is_new and final_risk_level in _ALERT_THRESHOLD:
        # A1 dedup gate: one alert per unique hash transition per source,
        # plus a cooldown between alerts for the same source.
        alert_allowed = True
        if source is not None:
            from app.alert_dedup import should_send_alert
            from app.source_runs import make_source_id as _mk_sid
            alert_allowed, alert_suppressed_reason = should_send_alert(
                _mk_sid(source), new_hash,
            )
            if not alert_allowed:
                logger.info(
                    "Telegram alert suppressed (%s): source=%s hash=%s",
                    alert_suppressed_reason, source.get("name"), str(new_hash)[:12],
                )

        if alert_allowed:
            from app.telegram import send_telegram_alert

            alert_payload = {
                "url":                     url,
                "source_name":             (source or {}).get("name", ""),
                "jurisdiction":            (source or {}).get("jurisdiction", ""),
                "risk_level":              final_risk_level,
                "risk_reason":             final_risk_reason,
                "executive_summary":       executive_summary,
                "business_action_required":business_action,
                "ai_used":                 ai_used,
                "added_count":             len(diff_result["added"]),
                "removed_count":           len(diff_result["removed"]),
                "added":                   diff_result.get("added", []),
                "removed":                 diff_result.get("removed", []),
                "risk_details":            rule_risk,
                "detected_facts":          detected_facts,
                "normalized_hash":         new_hash,
                "checked_at_utc":          created_at,
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
        "alert_suppressed_reason":  alert_suppressed_reason,
        "risk_details":             rule_risk,
        "executive_summary":        executive_summary,
        "business_action_required": business_action,
        "source_language":          source_language,
        "output_language":          output_language,
        "affected_entities":        affected_entities,
        "urgency":                  urgency,
        "deadline":                 deadline,
        "detected_facts":           detected_facts,
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
        # Hash/measurement fields — the same values used for change
        # detection must reach the evidence record (see D1 in DEFECT_LOG).
        "normalized_hash":          new_hash,
        "content_hash":             new_hash,
        "raw_hash":                 _sha256_or_none(content),
        "raw_chars":                len(content or ""),
        "normalized_chars":         len(normalized_for_hash or ""),
        "normalization_version":    NORMALIZATION_VERSION,
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
    # F1 wiring fix (found by gate e2e): run_pipeline signals failure modes
    # via "status" ("error_page", "quality_drop") — never clobber them.
    result.setdefault("status", "ok")

    # ── D6: unchanged runs write a compact heartbeat to the trail ─────
    if not result.get("changed") and result.get("normalized_hash"):
        try:
            from app.source_runs import record_heartbeat

            heartbeat = record_heartbeat(
                source,
                normalized_hash=result["normalized_hash"],
                raw_hash=result.get("raw_hash"),
                extracted_chars=result.get("extracted_chars", 0),
                raw_chars=result.get("raw_chars", 0),
                normalized_chars=result.get("normalized_chars", 0),
                extraction_quality=result.get("extraction_quality", ""),
            )
            result["run_record"] = heartbeat
            logger.info(
                "Heartbeat recorded: source=%s run_id=%s hash=%s",
                source.get("name"), heartbeat.get("run_id"),
                str(result["normalized_hash"])[:12],
            )
        except Exception as _hb_err:
            logger.warning("Heartbeat write failed (non-fatal): %s", _hb_err)

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
                # A1: the trail is the dedup state — record delivered alerts.
                "alert_sent":               bool(result.get("telegram_sent")),
                "alert_suppressed_reason":  result.get("alert_suppressed_reason", ""),
                "added_count":              result.get("added_count", 0),
                "removed_count":            result.get("removed_count", 0),
                "modified_count":           result.get("modified_count", 0),
                "chars":                    result.get("chars", 0),
                "extracted_chars":          result.get("extracted_chars", 0),
                "extraction_quality":       result.get("extraction_quality", ""),
                "extraction_method":        result.get("extraction_method", ""),
                # Hash fields — without these classify_change cannot compare
                # runs and downgrades real changes to UNCHANGED (defect D1).
                "normalized_hash":          result.get("normalized_hash"),
                "content_hash":             result.get("content_hash"),
                "raw_hash":                 result.get("raw_hash"),
                "raw_chars":                result.get("raw_chars", 0),
                "normalized_chars":         result.get("normalized_chars", 0),
                "normalization_version":    result.get("normalization_version"),
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
                    import app.source_runs as _sr_mod

                    # D8: resolve through the configured base dir (env
                    # STATUTEPROOF_BASE_DIR or repo default) — never a
                    # hardcoded path relative to this file.
                    _base_dir = _Path(_sr_mod._BASE_DIR)

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
                        # Attach the shared content layer so the draft/email
                        # channel renders the same alert body as Telegram.
                        try:
                            from app.alert_content import build_alert_content, render_markdown
                            alert["alert_content_markdown"] = render_markdown(build_alert_content({
                                "url": source.get("url", ""),
                                "source_name": source.get("name", ""),
                                "jurisdiction": source.get("jurisdiction", ""),
                                "risk_level": result.get("risk_level", ""),
                                "risk_reason": result.get("risk_reason", ""),
                                "risk_details": result.get("risk_details") or {},
                                "added": result.get("added", []),
                                "removed": result.get("removed", []),
                                "executive_summary": result.get("executive_summary", ""),
                                "business_action_required": result.get("business_action_required", ""),
                                "deadline": result.get("deadline"),
                                "detected_facts": result.get("detected_facts", []),
                                "urgency": result.get("urgency", ""),
                                "affected_entities": result.get("affected_entities", []),
                                "checked_at_utc": final_record.get("timestamp_utc", ""),
                            }))
                        except Exception as _sc_err:
                            logger.warning("Shared alert content attach failed (non-fatal): %s", _sc_err)
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
