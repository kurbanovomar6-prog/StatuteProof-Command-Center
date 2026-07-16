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

# Content-shrink guard (A-durability, fix 3). A large drop in content length
# between the baseline and this run is almost always a scraper break (blocked
# page, truncated fetch, layout change) rather than a genuine "content removed"
# regulatory change. These thresholds MIRROR app.source_runs.classify_change's
# QUALITY_DROP heuristics so a run that would classify as a quality drop can
# never alert or overwrite the baseline:
#   * extracted (raw) content below 40% of the previous run, or
#   * normalized content below 70% of the previous run.
_SHRINK_RAW_RATIO = 0.4
_SHRINK_NORMALIZED_RATIO = 0.7


def _detect_content_shrink(
    *,
    prev_raw_chars: int | None,
    prev_normalized_chars: int | None,
    new_raw_chars: int,
    new_normalized_chars: int,
) -> str | None:
    """
    Return a human-readable reason string when this run's content shrank far
    enough to look like a scraper break rather than a real change, else None.

    Mirrors classify_change's content-shrink thresholds (source_runs.py). Only
    trips when a positive previous size is known — a first run or a run with no
    recorded previous size can never trip the guard.
    """
    if prev_raw_chars and prev_raw_chars > 0 and new_raw_chars < prev_raw_chars * _SHRINK_RAW_RATIO:
        return (
            f"extracted content shrank to {new_raw_chars} chars "
            f"(< {_SHRINK_RAW_RATIO:.0%} of previous {prev_raw_chars})"
        )
    if (
        prev_normalized_chars
        and prev_normalized_chars > 0
        and new_normalized_chars
        and new_normalized_chars < prev_normalized_chars * _SHRINK_NORMALIZED_RATIO
    ):
        return (
            f"normalized content shrank to {new_normalized_chars} chars "
            f"(< {_SHRINK_NORMALIZED_RATIO:.0%} of previous {prev_normalized_chars})"
        )
    return None

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
        html = fetch_page(url, allow_proxy=True)

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

    # Previous content sizes for the content-shrink guard (fix 3). Prefer the
    # trail record's recorded sizes; fall back to the length of the previous
    # stored SQLite content. Only used to decide whether a would-be alert is a
    # scraper break rather than a real change.
    prev_raw_chars: int | None = None
    prev_normalized_chars: int | None = None
    if prev_trail_record is not None:
        try:
            prev_raw_chars = int(prev_trail_record.get("extracted_chars") or 0) or None
        except (TypeError, ValueError):
            prev_raw_chars = None
        try:
            prev_normalized_chars = int(prev_trail_record.get("normalized_chars") or 0) or None
        except (TypeError, ValueError):
            prev_normalized_chars = None
    if prev_raw_chars is None and latest is not None:
        try:
            prev_raw_chars = len(latest["content"]) or None
        except (KeyError, TypeError):
            prev_raw_chars = None

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

    # ── Shrink guard (fix 3): scraper break, not a real "content removed" ──
    # A large drop in content length between the baseline and this run is
    # almost always a scraper break (blocked/challenge page, truncated fetch,
    # layout change) rather than a genuine regulatory removal. Detecting it
    # here — BEFORE Step 9 (save_document) and Step 10 (alert) — means the
    # shrunk content NEVER overwrites the baseline (no save_document, no trail
    # append: the early return omits normalized_hash, so run_pipeline_for_source
    # skips both its heartbeat and its CHANGED-append blocks) and NEVER fires an
    # alert. The next healthy sweep therefore still diffs against the true
    # baseline instead of a poisoned shrunk one.
    if not is_new:
        _shrink_reason = _detect_content_shrink(
            prev_raw_chars=prev_raw_chars,
            prev_normalized_chars=prev_normalized_chars,
            new_raw_chars=extracted_chars,
            new_normalized_chars=len(normalized_for_hash or ""),
        )
        if _shrink_reason:
            logger.warning(
                "CONTENT SHRINK SUPPRESSED for %s: %s — alert suppressed and "
                "baseline left intact (likely scraper break, not a real change)",
                url, _shrink_reason,
            )
            # A-MEDIUM(1): write a durable QUALITY_DROP audit record so the
            # suppression is auditable (an evidence product must not have gaps
            # that live only in a log line). The record carries NO usable hash,
            # so it can never become the baseline — the true baseline survives
            # the scraper break, and no alert is issued. Non-fatal: a failed
            # write must never break the pipeline.
            if source is not None:
                try:
                    from app.source_runs import record_quality_drop
                    record_quality_drop(
                        source,
                        reason=_shrink_reason,
                        alert_suppressed_reason="content_shrink",
                        observed_raw_chars=extracted_chars,
                        observed_normalized_chars=len(normalized_for_hash or ""),
                        prev_raw_chars=prev_raw_chars,
                        prev_normalized_chars=prev_normalized_chars,
                        extraction_method=extraction_method,
                    )
                except Exception as _qd_err:
                    logger.warning(
                        "QUALITY_DROP audit record write failed (non-fatal): %s",
                        _qd_err,
                    )
            return {
                "url":                    url,
                "changed":                False,
                "status":                 "quality_drop",
                "shrink_suppressed":      True,
                "shrink_reason":          _shrink_reason,
                "extracted_chars":        extracted_chars,
                "extraction_quality":     "failed",
                "extraction_method":      extraction_method,
                "alert_suppressed_reason": "content_shrink",
                "ai_skipped_reason":      "quality_drop",
                "ai_calls_used":          _AI_RUN_BUDGET["count"],
            }

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

    # Canonical evidence sealing happens in run_pipeline_for_source AFTER
    # append_run returns — proof_block_path and the trail-written snapshot
    # paths exist only from that point, so sealing here (pre-append) is
    # structurally impossible. The bare-URL path (run_pipeline called
    # directly, source=None) never appends a trail record and therefore
    # never seals — by design.

    # ── Step 10: Telegram alert (MEDIUM/HIGH, never on baseline) ──────
    # Durability ordering (A-durability, fix 2): the invariant is that an
    # "alert sent" state can never outrun an "evidence recorded" state. The
    # evidence-trail append happens in run_pipeline_for_source (append_run),
    # AFTER this function returns. So when a source context is present we do NOT
    # send here — we build the vetted payload (dedup gate included) and DEFER it
    # in the result under "_deferred_alert". run_pipeline_for_source sends it
    # only after append_run has durably recorded the CHANGED evidence, and a
    # failed append aborts the send. The bare-URL path (source is None) never
    # appends a trail record, so it keeps sending inline exactly as before.
    telegram_sent = False
    alert_suppressed_reason = ""
    deferred_alert: dict | None = None
    # G1: a vetted alert suppressed ONLY by the per-source cooldown is deferred
    # (stashed after durable evidence, delivered when the cooldown elapses), not
    # dropped. run_pipeline_for_source consumes this after append_run.
    pending_cooldown_alert: dict | None = None

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

        # Build the vetted payload unconditionally — it is needed both to SEND
        # (allowed) and to STASH (deferred by cooldown). The run_id lets the
        # deferred delivery flip the right trail record's alert_sent later.
        alert_payload = {
            "url":                     url,
            "source_id":               _source_id or (source or {}).get("id") or (source or {}).get("source_id") or "",
            "run_id":                  _run_id,
            "source_name":             (source or {}).get("name", ""),
            "jurisdiction":            (source or {}).get("jurisdiction", ""),
            "risk_level":              final_risk_level,
            "risk_reason":             final_risk_reason,
            "executive_summary":       executive_summary,
            "business_action_required":business_action,
            "ai_used":                 ai_used,
            # SF-2 human-review gate inputs: send_telegram_alert holds the
            # automated broadcast when the run needs review. These MUST ride
            # on the payload so the gate can see them at send time.
            "confidence":              confidence,
            "review_required":         review_required,
            "added_count":             len(diff_result["added"]),
            "removed_count":           len(diff_result["removed"]),
            "added":                   diff_result.get("added", []),
            "removed":                 diff_result.get("removed", []),
            "risk_details":            rule_risk,
            "detected_facts":          detected_facts,
            "normalized_hash":         new_hash,
            "checked_at_utc":          created_at,
        }
        if alert_allowed:
            if source is None:
                # Bare-URL path: no trail append will follow, so send inline.
                from app.telegram import send_telegram_alert
                telegram_sent = send_telegram_alert(alert_payload)
            else:
                # Source path: defer the send until append_run has durably
                # recorded the evidence (run_pipeline_for_source).
                deferred_alert = alert_payload
        elif source is not None and alert_suppressed_reason == "cooldown_active":
            # G1: suppressed ONLY by the cooldown → defer, don't drop. Stash the
            # payload after durable evidence; a later sweep delivers it once the
            # cooldown elapses and if it is still the source's current state.
            pending_cooldown_alert = alert_payload

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
        # Deferred alert payload (fix 2): non-None only on the source path when
        # an alert is vetted-and-ready but must wait for durable evidence.
        # run_pipeline_for_source consumes and clears this after append_run.
        "_deferred_alert":          deferred_alert,
        # G1 deferred-cooldown payload: non-None only when an alert was suppressed
        # solely by the cooldown. run_pipeline_for_source stashes it after
        # append_run so a later sweep can deliver it once the cooldown elapses.
        "_pending_cooldown_alert":  pending_cooldown_alert,
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
            from app.source_runs import append_run, make_source_id, mark_alert_sent

            # Durability ordering (A-durability, fix 2): a vetted alert waits in
            # result["_deferred_alert"] and is sent ONLY after append_run has
            # durably (fsync) recorded the CHANGED evidence below. The actual
            # Telegram send happens strictly after the append returns; a failed
            # append aborts the send.
            #
            # A-HIGH: the record is appended with alert_sent=False (delivery not
            # yet confirmed) and flipped to True by mark_alert_sent ONLY after a
            # confirmed send. Keying the record on the not-yet-sent intent would
            # wrongly stamp alert_sent=True even when the send later fails
            # (Telegram outage), and the next sweep's dedup gate would then
            # return "hash_already_alerted" and never retry the lost alert. With
            # alert_sent reflecting actual delivery, a failed send leaves it
            # False and the next sweep re-attempts the alert for the same hash.
            _deferred_alert = result.pop("_deferred_alert", None)
            _will_alert = _deferred_alert is not None

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
                # A1: the trail is the dedup state — it must record ACTUAL
                # delivery, never mere intent. On the source path telegram_sent
                # is still False here (the send is deferred to AFTER this durable
                # append), so the record is written alert_sent=False and flipped
                # to True by mark_alert_sent only after a confirmed send below.
                # A-MEDIUM(2): alert_sent may only be True on a genuinely CHANGED
                # record — never on a FIRST_SEEN baseline (guarded here) nor on a
                # run the trail downgrades (append_run re-runs classify_change;
                # the confirmed-send path below re-checks change_status too).
                "alert_sent": (
                    bool(result.get("telegram_sent"))
                    and not result.get("is_new")
                ),
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

            # ── Auto-seal the canonical evidence record (no operator step) ──
            # final_record carries proof_block_path and the trail-written
            # snapshot paths only after append_run, so this is the earliest
            # point the canonical record CAN be sealed. Sealing runs BEFORE
            # the deferred alert send so alert routing can attach the proof
            # block (alert_proof surfaces only record_status == "complete"
            # records). Non-fatal by design: the run evidence is already
            # durable in the trail, and `run.py create-canonical-evidence`
            # remains the recovery path for a failed seal. UNCHANGED runs are
            # not sealed — one evidence directory per unchanged check is
            # unbounded disk for no value beyond the trail record itself.
            if final_record.get("change_status") in ("CHANGED", "FIRST_SEEN"):
                try:
                    from pathlib import Path as _SealPath
                    from app.evidence_records import create_canonical_evidence_record
                    import app.source_runs as _sr_seal
                    # D8 idiom: resolve against the SAME base dir the trail
                    # just wrote to, so the snapshot/proof paths in
                    # final_record resolve where append_run put them.
                    # FIRST_SEEN baselines are sealed but do NOT enter the
                    # human review queue — the queue is for customer-facing
                    # changes, and mass source activation would otherwise
                    # flood it with one pending record per source.
                    _is_baseline = final_record.get("change_status") == "FIRST_SEEN"
                    _seal_kwargs = (
                        {
                            "review_status": "baseline",
                            "human_review_required": False,
                            "review_reason": (
                                "Baseline capture (FIRST_SEEN) — no "
                                "customer-facing change to review."
                            ),
                        }
                        if _is_baseline
                        else {}
                    )
                    _sealed_record = create_canonical_evidence_record(
                        final_record,
                        base_dir=_SealPath(_sr_seal._BASE_DIR),
                        **_seal_kwargs,
                    )
                    result["canonical_evidence_sealed"] = True
                    if _sealed_record.get("record_status") != "complete":
                        # A quarantined (integrity_error) record was durably
                        # written — sealed, but alert_proof will decline it.
                        # Surface it so quarantining live captures is visible.
                        result["canonical_evidence_quarantined"] = True
                        logger.warning(
                            "Canonical evidence sealed QUARANTINED (record_status=%s): "
                            "source=%s run_id=%s — capture text failed the "
                            "readability gate; the alert will carry no proof block",
                            _sealed_record.get("record_status"),
                            source.get("name"), final_record.get("run_id"),
                        )
                    else:
                        logger.info(
                            "Canonical evidence sealed: source=%s run_id=%s status=%s",
                            source.get("name"), final_record.get("run_id"),
                            final_record.get("change_status"),
                        )
                except Exception as seal_err:  # noqa: BLE001
                    # Typed idempotency check via isinstance with a lazy
                    # re-import: a bare `except EvidenceRecordExistsError`
                    # would NameError if the import inside the try was what
                    # failed — and that NameError would escape to the outer
                    # append except and suppress the alert send.
                    try:
                        from app.evidence_records import (
                            EvidenceRecordExistsError as _ExistsErr,
                        )
                        _is_dup = isinstance(seal_err, _ExistsErr)
                    except Exception:  # noqa: BLE001
                        _is_dup = False
                    if _is_dup:
                        # Benign duplicate: the record IS sealed — just not by
                        # this call. INFO, not WARNING — a warning here would
                        # train operators to skim past the one that matters.
                        result["canonical_evidence_sealed"] = True
                        logger.info(
                            "Canonical evidence already sealed (idempotent skip): "
                            "source=%s run_id=%s",
                            source.get("name"), final_record.get("run_id"),
                        )
                    else:
                        result["canonical_evidence_sealed"] = False
                        logger.warning(
                            "Canonical evidence auto-seal failed (non-fatal; "
                            "run.py create-canonical-evidence can recover): "
                            "source=%s run_id=%s err=%s",
                            source.get("name"), final_record.get("run_id"), seal_err,
                        )

            # ── Send the deferred alert — ONLY now that the evidence is durable ──
            # Invariant (A-durability, fix 2): "alert sent" can never outrun
            # "evidence recorded". append_run() above has fsync'd the CHANGED
            # record to disk; only then do we release the Telegram send. If
            # append_run had raised, control jumped to the non-fatal except below
            # and this send is never reached — no alert without durable evidence.
            # We also re-confirm the persisted classification is genuinely
            # CHANGED (append_run re-runs classify_change), so a run the trail
            # downgraded never alerts.
            if _will_alert and final_record.get("change_status") == "CHANGED":
                from app.telegram import send_telegram_alert
                telegram_sent = send_telegram_alert(_deferred_alert)
                result["telegram_sent"] = telegram_sent
                if telegram_sent:
                    # A-HIGH: confirmed delivery — flip the persisted record's
                    # alert_sent to True so the dedup gate suppresses re-alerting
                    # this hash next sweep. alert_sent is not a chain field, so
                    # this patch leaves the tamper-evident chain intact.
                    mark_alert_sent(
                        final_record.get("source_id"),
                        final_record.get("run_id"),
                        alert_sent=True,
                    )
                    result["run_record"]["alert_sent"] = True
                else:
                    # Send failed AFTER durable evidence append: the record stays
                    # alert_sent=False, so the next sweep re-attempts the alert
                    # for this same hash instead of suppressing it forever.
                    logger.warning(
                        "Deferred Telegram send returned falsy AFTER durable "
                        "evidence append: source=%s run_id=%s (evidence recorded, "
                        "alert delivery NOT confirmed — record left alert_sent=False "
                        "so the next sweep retries this alert)",
                        source.get("name"), final_record.get("run_id"),
                    )
            elif _will_alert:
                logger.warning(
                    "Deferred alert NOT sent: trail reclassified run as %s "
                    "(not CHANGED) for source=%s run_id=%s — evidence recorded, "
                    "no alert issued",
                    final_record.get("change_status"), source.get("name"),
                    final_record.get("run_id"),
                )

            # ── G1: stash a cooldown-suppressed alert AFTER durable evidence ──
            # Same durability invariant as the deferred send: only after append_run
            # has fsync'd the CHANGED record do we persist the deferred payload, so
            # a stash can never outrun the evidence it refers to.
            _pending_cooldown = result.pop("_pending_cooldown_alert", None)
            if _pending_cooldown is not None and final_record.get("change_status") == "CHANGED":
                try:
                    from app.pending_alerts import stash as _stash_pending
                    _stash_pending(_pending_cooldown)
                    logger.info(
                        "Deferred cooldown alert stashed for later delivery: "
                        "source=%s run_id=%s", source.get("name"), final_record.get("run_id"),
                    )
                except Exception as _stash_err:  # noqa: BLE001
                    logger.warning("pending-alert stash failed (non-fatal): %s", _stash_err)

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

                # ── Deadline radar: persist any concrete FUTURE date the change
                # carries, keyed by the durable evidence record (run_id). Only
                # dates extracted from the real ADDED diff excerpt are stored
                # (evidence-grounded). Best-effort — never blocks the pipeline.
                try:
                    from pathlib import Path as _Path2
                    import app.source_runs as _sr_mod2
                    from app.deadline_radar import record_deadlines_for_change

                    # Resolve the register base dir from source_runs so the
                    # deadline register always lives alongside the trail it keys
                    # off (and follows the same isolation in tests/deploys).
                    persisted_deadlines = record_deadlines_for_change(
                        evidence_record_id=final_record.get("run_id", ""),
                        source_id=final_record.get("source_id", ""),
                        regulator=(
                            source.get("regulator")
                            or source.get("family")
                            or source.get("jurisdiction")
                            or ""
                        ),
                        source_name=source.get("name", ""),
                        official_url=source.get("url", ""),
                        added_blocks=result.get("added", []),
                        base_dir=_Path2(_sr_mod2._BASE_DIR),
                    )
                    if persisted_deadlines:
                        logger.info(
                            "Deadline radar: recorded %d deadline(s): source=%s run_id=%s",
                            len(persisted_deadlines), source.get("name"),
                            final_record.get("run_id"),
                        )
                except Exception as _dl_err:
                    logger.warning("Deadline radar persist failed (non-fatal): %s", _dl_err)

        except Exception as _sr_err:
            # The evidence append failing means this source produced NO durable
            # record AND no alert (durability invariant) — while still counting
            # as "ok" in the cycle (the fetch succeeded). Without this flag a
            # systemic trail-write failure (disk full, permissions) is invisible
            # to every deadman. monitor_all_sources tallies it.
            result["evidence_append_failed"] = True
            logger.warning("source_runs.append_run failed (non-fatal): %s", _sr_err)

    # ── G1: deliver any due deferred-cooldown alert ──────────────────────────
    # Runs on EVERY sweep (changed or unchanged) — the only place a cooldown-
    # suppressed alert can be retried, since an unchanged sweep short-circuits
    # before the alert path. Placed AFTER this run's own append so a stash the
    # current change superseded is discarded (not delivered stale). Non-fatal.
    if ENABLE_TELEGRAM_ALERTS:
        try:
            from app.pending_alerts import flush_due
            from app.telegram import send_telegram_alert
            flush_due(source, send_fn=send_telegram_alert)
        except Exception as _flush_err:  # noqa: BLE001
            logger.warning("pending-alert flush failed (non-fatal): %s", _flush_err)

    # Internal markers never belong in the returned contract. On the CHANGED
    # path they were already pop'd; on every other path they are None and dropped.
    result.pop("_deferred_alert", None)
    result.pop("_pending_cooldown_alert", None)
    return result
