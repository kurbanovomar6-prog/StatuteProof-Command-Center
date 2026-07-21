"""
Multi-source monitoring orchestrator — v4.

monitor_all_sources() runs the full pipeline over every enabled source
in sources.json.  One failed source never stops the rest.

Return contract
---------------
Each item in the returned list is either:

  success:
    run_pipeline_for_source() result dict with an extra "status" = "ok" key.

  error:
    {
        "source_name":  str,
        "url":          str,
        "jurisdiction": str,
        "category":     str,
        "changed":      False,
        "status":       "error",
        "access_status": str,   "blocked" | "rate_limited" | "timeout" | "error"
        "error":        str,    human-readable error message
    }

Resilience features
-------------------
- Per-source retry: one retry after 5 s on first failure.
- Circuit-breaker: source skipped after >= _CIRCUIT_OPEN_THRESHOLD consecutive
  DARK runs — FAILED (raised) or QUALITY_DROP with a thin/failed extraction
  (bot wall, error page, empty/undecodable body, chronically thin page). A
  reachable source whose content merely shrank is NOT dark and never trips it.
  Tracked in the _circuit_open module-level set and persisted to
  _CIRCUIT_STATE_FILE; every skipped cycle still writes a trail record.
- Structured CYCLE_SUMMARY log line at end of each run.
"""

import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import AI_MAX_CALLS_PER_RUN
from app.pipeline import init_pipeline, run_pipeline_for_source
from app.sources import get_enabled_sources

logger = logging.getLogger(__name__)

# Paths for circuit-breaker persistence and source run history.
_BASE_DIR = Path(__file__).parent.parent
_SOURCE_RUNS_JSONL = _BASE_DIR / "data" / "source_runs" / "source_runs.jsonl"
_CIRCUIT_STATE_FILE = _BASE_DIR / "data" / "circuit_breaker_state.json"

# Deadman state: tracks whether the LAST cycle was catastrophic so the founder
# alert fires only on the transition into the bad state, not every cycle while
# a wide outage persists (which would spam the founder's Telegram). Persisted
# so the transition edge survives a process restart mid-outage.
_DEADMAN_STATE_FILE = _BASE_DIR / "data" / "deadman_state.json"

# How many consecutive historical failures before a circuit opens.
_CIRCUIT_OPEN_THRESHOLD = 3

# Trail statuses that mean "this cycle produced NO usable content for this
# source" — the breaker counts them under ONE shared threshold.
#
# FAILED  : the fetch/pipeline raised (timeout, 403, connection error).
# QUALITY_DROP: the pipeline aborted in an early guard — empty body, HTTP
#   error/challenge page, anti-bot wall, undecodable body — or a run that
#   returned cleanly but extracted a thin/failed page. No usable content, no
#   baseline, no alert: the source is dark. A quality drop that only means
#   "content shrank" is excluded (see _NON_DARK_SUPPRESSION_REASONS).
#
# Why ONE threshold rather than two: the production trail (2026-07-20) carries
# 123 QUALITY_DROP against 51 FAILED, and a chronically walled source flips
# between them cycle to cycle (403 one cycle, challenge page the next). Two
# separate counters would each reset on the other's records and could stay
# under their thresholds forever, so the breaker would never open on exactly
# the fleet's most common failure mode. Both statuses carry identical
# operational meaning — nothing usable was retrieved — so they share a counter.
_UNUSABLE_RUN_STATUSES = frozenset({"FAILED", "QUALITY_DROP"})

# Result-dict statuses returned by a NON-raising pipeline run that nonetheless
# yielded nothing usable (the guard-abort paths in app/pipeline.py). Such a run
# must never be treated as a recovery signal: before this, it took the monitor's
# success path and auto-cleared the breaker, so a permanently walled source was
# re-probed every cycle and could never stay open.
_UNUSABLE_RESULT_STATUSES = frozenset(
    {"quality_drop", "error_page", "error", "failed"}
)

# Suppression reasons that are NOT darkness and must never count toward the
# breaker. The content-shrink guard (app/pipeline.py) is sticky BY DESIGN: it
# deliberately leaves the baseline intact, so it re-fires on EVERY later cycle
# until a human re-baselines. The source is reachable and its content genuinely
# changed — exactly the HIGH-risk event the product exists to catch — so
# tripping the breaker there would stop fetching a live, changing page.
_NON_DARK_SUPPRESSION_REASONS = frozenset({"content_shrink"})

# ...but ONLY when the run actually retrieved a plausible page. Which guard a
# response lands in is decided entirely by the bytes the monitored host returns:
# app/pipeline.py runs the marker guards (looks_like_error_page /
# looks_like_bot_wall / is_mostly_unreadable) first and falls through to the
# shrink path when none match — and a short, novel wall page matches none of
# them ("Access to this resource is restricted by the site administrator.", the
# DIFC incident: 87 chars). Without a floor, a remote host could keep an open
# breaker permanently CLEARED, and a chronically walled source could never open
# it, by serving a stub: the site we monitor would be steering our own
# reliability control. 500 chars is pipeline._extraction_quality's own "good"
# threshold — above it the page is plausible content, below it it is a stub.
_PLAUSIBLE_PAGE_CHARS = 500

# Extraction-quality levels that mean "nothing usable came back". A trail record
# classified QUALITY_DROP by classify_change (the dominant class in production:
# a page that keeps extracting to 62 chars) is dark even though the pipeline
# never aborted in a guard and returned status "ok". A QUALITY_DROP with a GOOD
# extraction is a content-size change, not darkness — it stays out of the count.
_DARK_QUALITY_LEVELS = frozenset({"FAILED", "THIN"})

# Half-open cadence: an OPEN circuit is skipped for this many cycles, then a
# single probe is allowed through. A successful probe auto-resets the breaker
# (WARN-6) so a source recovers on its own after a transient outage instead of
# staying skipped forever; a failing probe re-arms the skip. Must be >= 1 so
# the cycle immediately after opening still skips.
_CIRCUIT_PROBE_EVERY_N_CYCLES = 5

# Bytes (not lines) of source_runs.jsonl tail to scan when counting per-URL
# consecutive failures. A LINE-count window goes dead at fleet scale: ~139
# enabled sources append ~139 records per cycle, so a 200-line tail spanned
# barely one cycle and no single URL could ever show _CIRCUIT_OPEN_THRESHOLD
# consecutive records inside the window — the breaker could effectively never
# open (audit 2026-07-20). A byte-bounded tail (4 MiB ≈ thousands of records ≈
# many full cycles at current fleet size) keeps the read bounded while always
# covering enough cycles for any single URL.
_CIRCUIT_HISTORY_SCAN_BYTES = 4 * 1024 * 1024

# Per-source count of cycles skipped while the circuit is open; drives the
# half-open probe cadence. Not persisted — a process restart simply probes
# sooner, which is safe.
_circuit_skip_counts: dict[str, int] = {}

# Seconds to wait before a single retry.
_RETRY_DELAY_SECONDS = 5


def _load_circuit_state() -> set[str]:
    """Load persisted circuit-open set from disk. Returns empty set on any error."""
    try:
        if _CIRCUIT_STATE_FILE.exists():
            data = json.loads(_CIRCUIT_STATE_FILE.read_text(encoding="utf-8"))
            return set(data.get("open_sources", []))
    except Exception as exc:
        logger.warning("circuit_breaker: could not load state file: %s", exc)
    return set()


def _save_circuit_state(open_sources: set[str]) -> None:
    """Persist the circuit-open set to disk so it survives process restarts."""
    try:
        _CIRCUIT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _CIRCUIT_STATE_FILE.write_text(
            json.dumps({"open_sources": sorted(open_sources)}, indent=2),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.warning("circuit_breaker: could not save state file: %s", exc)


# Module-level circuit-breaker registry.
# Loaded from disk on module init; persisted on every change.
_circuit_open: set[str] = _load_circuit_state()


def _clear_circuit(name: str) -> None:
    """Auto-reset the breaker for a source after a successful probe/run.

    Without this, a transient N-cycle outage that trips the breaker would keep
    the source skipped forever (until process restart or manual state-file
    deletion), because nothing ever removes it from _circuit_open. A single
    successful run is the recovery signal: drop the source and persist so the
    reset survives restarts too. No-op when the source is not currently open.
    """
    _circuit_skip_counts.pop(name, None)
    if name in _circuit_open:
        _circuit_open.discard(name)
        _save_circuit_state(_circuit_open)
        logger.info(
            "CIRCUIT_BREAKER auto-reset for %s after a successful run — "
            "monitoring resumes",
            name,
        )


def _load_deadman_degraded() -> bool:
    """Read the persisted "last cycle was catastrophic" flag. False on any error."""
    try:
        if _DEADMAN_STATE_FILE.exists():
            data = json.loads(_DEADMAN_STATE_FILE.read_text(encoding="utf-8"))
            return bool(data.get("degraded", False))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("deadman: could not load state file: %s", exc)
    return False


def _save_deadman_degraded(degraded: bool) -> None:
    """Persist the catastrophic-cycle flag so the alert edge survives restarts."""
    try:
        _DEADMAN_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _DEADMAN_STATE_FILE.write_text(
            json.dumps(
                {
                    "degraded": bool(degraded),
                    "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("deadman: could not save state file: %s", exc)


def _is_catastrophic_cycle(summary: dict) -> bool:
    """
    Decide whether a completed cycle is catastrophic enough to alert the founder.

    Catastrophic means the monitor produced no useful monitoring this cycle:

      • every source failed:            sources_failed == sources_total  (total > 0)
      • OR nothing succeeded at all:    sources_ok + sources_unchanged == 0

    An empty cycle (no enabled sources, total == 0) is NOT catastrophic — there
    is simply nothing to monitor, which is a configuration state, not an outage.
    """
    total = int(summary.get("sources_total", 0) or 0)
    if total <= 0:
        return False
    failed = int(summary.get("sources_failed", 0) or 0)
    ok = int(summary.get("sources_ok", 0) or 0)
    unchanged = int(summary.get("sources_unchanged", 0) or 0)
    return failed == total or (ok + unchanged) == 0


def _maybe_alert_catastrophic_cycle(summary: dict) -> None:
    """
    Fire a founder deadman alert on the transition INTO a catastrophic cycle.

    Rate-limited by a persisted degraded flag: the alert fires once when the
    monitor first goes catastrophic and stays quiet on every subsequent
    catastrophic cycle until a healthy cycle clears the flag. Best-effort —
    a notify/IO failure must never break the monitor loop.
    """
    try:
        catastrophic = _is_catastrophic_cycle(summary)
        was_degraded = _load_deadman_degraded()

        if catastrophic and not was_degraded:
            from app.ops_alert import notify_founder

            total = int(summary.get("sources_total", 0) or 0)
            failed = int(summary.get("sources_failed", 0) or 0)
            text = (
                "🚨 StatuteProof monitor: CATASTROPHIC cycle\n"
                f"All monitoring failed this cycle — {failed}/{total} sources "
                "failed and 0 produced content.\n"
                f"cycle_id: {summary.get('cycle_id', '?')}\n"
                f"completed_at (UTC): {summary.get('completed_at', '?')}\n"
                "Customers are NOT receiving alerts. Check the scheduler, "
                "network, and source access now."
            )
            notify_founder(text)
            _save_deadman_degraded(True)
        elif not catastrophic and was_degraded:
            # Recovered — clear the flag (and optionally note recovery) so the
            # next outage transition alerts again.
            from app.ops_alert import notify_founder

            notify_founder(
                "✅ StatuteProof monitor: recovered — a cycle produced content "
                f"again (cycle_id {summary.get('cycle_id', '?')})."
            )
            _save_deadman_degraded(False)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("deadman: catastrophic-cycle alert check failed: %s", exc)


_SEAL_DEADMAN_STATE_FILE = _BASE_DIR / "data" / "seal_deadman_state.json"


_SEAL_FAIL_STREAK_THRESHOLD = 3


def _load_seal_state() -> dict:
    """Read the persisted seal-deadman state. Empty dict on any error."""
    try:
        if _SEAL_DEADMAN_STATE_FILE.exists():
            data = json.loads(_SEAL_DEADMAN_STATE_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("seal deadman: could not load state file: %s", exc)
    return {}


def _save_seal_state(degraded: bool, fail_streak: int) -> None:
    try:
        _SEAL_DEADMAN_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _SEAL_DEADMAN_STATE_FILE.write_text(
            json.dumps(
                {
                    "degraded": bool(degraded),
                    "fail_streak": int(fail_streak),
                    "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("seal deadman: could not save state file: %s", exc)


def _maybe_alert_seal_failures(summary: dict) -> None:
    """Fire a founder alert when evidence durability degrades.

    Three trip conditions (evidence review, findings 2+3):
    - SYSTEMIC: every seal attempt in the cycle failed (and ≥1 attempted).
    - APPEND FAILURE: any run's trail append raised — no durable record AND
      no alert for that source, while it still counted "ok" in the cycle.
      This is the worst shape (disk full / permissions) and fires immediately.
    - PARTIAL-PERSISTENT: some (not all) seals failing for
      _SEAL_FAIL_STREAK_THRESHOLD consecutive cycles — one healthy baseline
      seal must not mask a permanently broken source forever.

    Edge-triggered and persisted: one alert on entry into the degraded state,
    one recovery note on exit, quiet in between.
    """
    try:
        attempted = int(summary.get("seals_attempted", 0) or 0)
        failed = int(summary.get("seals_failed", 0) or 0)
        appends_failed = int(summary.get("evidence_appends_failed", 0) or 0)

        state = _load_seal_state()
        was_degraded = bool(state.get("degraded", False))
        streak = int(state.get("fail_streak", 0) or 0)

        streak = streak + 1 if (failed > 0 or appends_failed > 0) else 0

        systemic = attempted > 0 and failed == attempted
        tripped = systemic or appends_failed > 0 or streak >= _SEAL_FAIL_STREAK_THRESHOLD
        healthy = failed == 0 and appends_failed == 0

        if tripped and not was_degraded:
            from app.ops_alert import notify_founder

            if appends_failed > 0:
                detail = (
                    f"{appends_failed} run(s) could not write the evidence "
                    "trail at all — those sources produced NO durable record "
                    "and NO alert."
                )
            elif systemic:
                detail = f"Evidence sealing failed for every attempt this cycle ({failed}/{attempted})."
            else:
                detail = (
                    f"Some seals have been failing for {streak} consecutive "
                    f"cycles (latest: {failed} failed / {attempted} attempted)."
                )
            notify_founder(
                "🚨 StatuteProof monitor: evidence durability degraded\n"
                f"{detail}\n"
                f"cycle_id: {summary.get('cycle_id', '?')}\n"
                "Check disk/permissions/evidence tree, then run "
                "`python run.py create-canonical-evidence` to backfill seals."
            )
            _save_seal_state(True, streak)
        elif healthy and was_degraded:
            from app.ops_alert import notify_founder

            notify_founder(
                "✅ StatuteProof monitor: evidence durability recovered "
                f"(cycle_id {summary.get('cycle_id', '?')})."
            )
            _save_seal_state(False, 0)
        else:
            _save_seal_state(was_degraded, streak)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("seal deadman: alert check failed: %s", exc)


def _classify_access_status(exc: Exception) -> str:
    """Classify an exception into a machine-readable access_status string."""
    msg = str(exc).lower()
    if "403" in msg or "forbidden" in msg or "access blocked" in msg:
        return "blocked"
    if "429" in msg or "too many requests" in msg:
        return "rate_limited"
    if "timeout" in msg or "timeouterror" in msg:
        return "timeout"
    return "error"


def _persist_failure_record(source: dict, error_msg: str, access_status: str) -> None:
    """
    Write a FAILED run record to source_runs.jsonl for a source whose pipeline
    raised on both attempts.

    Without this, a raising failure (timeout/403) never reaches
    run_pipeline's append_run path — the exception propagates before any trail
    record is written — so _consecutive_failures() always reads 0 and the
    circuit breaker can never open. Persisting a change_status="FAILED" record
    here is what makes _consecutive_failures() count the failure and lets the
    breaker trip after _CIRCUIT_OPEN_THRESHOLD consecutive failures.

    Best-effort: a failure to write the trail record must never break the
    monitor loop (the in-memory error result is already recorded by the caller).
    """
    try:
        import uuid as _uuid

        from app.source_runs import append_run, make_source_id

        url = source.get("url", "")
        record = {
            "run_id":         _uuid.uuid4().hex[:8],
            "source_id":      make_source_id(source),
            "source_name":    source.get("name", ""),
            "official_url":   url,
            "url":            url,
            "market":         str(source.get("jurisdiction", "AE")).upper(),
            "jurisdiction":   source.get("jurisdiction", ""),
            "category":       source.get("category", ""),
            # classify_change() returns "FAILED" when access_status == "failed"
            # or extraction_quality == "FAILED"; set both so the record is
            # unambiguously a failure regardless of classification order.
            "access_status":  "failed",
            "extraction_quality": "FAILED",
            "monitor_access_status": access_status,
            "extracted_chars": 0,
            "normalized_chars": 0,
            "raw_hash":       None,
            "normalized_hash": None,
            "content_hash":   None,
            "error":          error_msg,
            "timestamp_utc":  datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "pipeline_version": "4.2",
        }
        append_run(record)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning(
            "circuit_breaker: could not persist FAILED run record for %s: %s",
            source.get("name", source.get("url", "")), exc,
        )


def _persist_circuit_open_record(source: dict) -> None:
    """Write a durable QUALITY_DROP trail record for a cycle SKIPPED because the
    breaker is open.

    Without it, the dominant steady state of a chronically walled source is a
    silent gap: 5 of every 6 cycles would leave no trace at all, so the coverage
    certificate would show neither a check nor a reason for those cycles. An
    evidence product must be able to prove when it could NOT see a source. The
    record is hash-free (record_quality_drop invariant), so it can never become
    a baseline. Best-effort: a write failure must never break the monitor loop.
    """
    try:
        from app.source_runs import make_source_id, previous_run, record_quality_drop

        prev = previous_run(make_source_id(source)) or {}
        record_quality_drop(
            source,
            reason=(
                "Circuit open — source skipped after consecutive unusable runs; "
                "not fetched this cycle"
            ),
            alert_suppressed_reason="circuit_open",
            prev_raw_chars=prev.get("extracted_chars"),
            prev_normalized_chars=prev.get("normalized_chars"),
            failure_code="CIRCUIT_OPEN",
            access_status="circuit_open",
        )
    except Exception as exc:  # never let observability break the loop
        logger.warning(
            "circuit_breaker: could not persist CIRCUIT_OPEN trail record "
            "for %s: %s", source.get("name", source.get("url", "")), exc,
        )


def _result_yielded_usable_content(result: dict | None) -> bool:
    """True when a non-raising pipeline result represents a REAL success.

    A guard-abort (empty body / error page / bot wall / undecodable /
    suppressed shrink) returns cleanly but produced no hash and no baseline —
    it is not a recovery signal and must not clear the breaker.
    """
    if not result:
        return False
    status = str(result.get("status") or "").lower()
    if status in _UNUSABLE_RESULT_STATUSES:
        return False
    # A run can return status "ok" and still be dark: the fetch succeeded but
    # the extraction is thin/failed, so classify_change stamps the trail record
    # QUALITY_DROP. That is production's dominant quality-drop class.
    return not _record_is_dark(result.get("run_record") or {})


def _observed_chars(payload: dict) -> int:
    """How much content this run ACTUALLY retrieved.

    Trail records written by record_quality_drop deliberately carry the PREVIOUS
    good sizes in ``extracted_chars`` (so the next shrink guard still compares
    against the true baseline) and the sizes actually seen this run under
    ``observed_raw_chars`` — read the observed field first or a stub run would
    look 4.2k chars big.
    """
    for key in ("observed_raw_chars", "extracted_chars"):
        if key in payload:
            try:
                return int(payload.get(key) or 0)
            except (TypeError, ValueError):
                return 0
    return 0


def _is_non_dark_suppression(payload: dict | None) -> bool:
    """True when a quality drop came from a suppression that does NOT mean the
    source is dark (today: the sticky content-shrink guard) AND the run brought
    back enough content to prove the source really answered.

    The size floor is what keeps this decision OURS rather than the remote
    host's: see _PLAUSIBLE_PAGE_CHARS. A stub/wall that falls through to the
    shrink path is darkness, not a live page whose content merely shrank.
    """
    if not payload:
        return False
    reason = str(payload.get("alert_suppressed_reason") or "").lower()
    if not (
        reason in _NON_DARK_SUPPRESSION_REASONS or bool(payload.get("shrink_suppressed"))
    ):
        return False
    return _observed_chars(payload) >= _PLAUSIBLE_PAGE_CHARS


def _record_is_dark(record: dict | None) -> bool:
    """True when a trail record proves this cycle retrieved nothing usable."""
    if not record:
        return False
    # A cycle we deliberately SKIPPED never contacted the source, so it is
    # evidence of ABSENCE of a check — never evidence that the source is dark.
    # Counting our own CIRCUIT_OPEN output would make the breaker feed on
    # itself: once open it would stay open on non-fetches rather than on fetch
    # evidence, the operator log line would report an inflated "consecutive
    # unusable runs" count, and the documented 3-run threshold would stop being
    # what is enforced. Same rule the coverage certificate already applies.
    from app.source_runs import is_skipped_cycle

    if is_skipped_cycle(record):
        return False
    status = str(record.get("change_status") or record.get("status") or "").upper()
    if status == "FAILED":
        return True
    if status != "QUALITY_DROP":
        return False
    if _is_non_dark_suppression(record):
        return False
    return str(record.get("extraction_quality") or "").upper() in _DARK_QUALITY_LEVELS


def _consecutive_failures(source_url: str) -> int:
    """
    Count consecutive unusable statuses (_UNUSABLE_RUN_STATUSES — FAILED and
    QUALITY_DROP) for source_url from source_runs.jsonl, reading from newest
    record backwards.

    Reads a byte-bounded tail (_CIRCUIT_HISTORY_SCAN_BYTES) of the JSONL file
    and counts consecutive unusable change_status values for the given URL,
    stopping at the first non-failure for that URL.  Records belonging to
    OTHER sources are skipped, not counted — that is what makes the window
    fleet-size-independent.  Returns 0 when the file is absent or unreadable.
    """
    try:
        # Resolve the run file the SAME way append_run does (honoring
        # STATUTEPROOF_BASE_DIR) so the breaker reads exactly the file the
        # failure record was just written to, not a stale hardcoded path.
        from app.source_runs import source_run_path

        run_file = source_run_path()
        if not run_file.exists():
            return 0
        with run_file.open("rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            start = max(0, size - _CIRCUIT_HISTORY_SCAN_BYTES)
            fh.seek(start)
            blob = fh.read()
    except Exception as exc:
        logger.warning("circuit_breaker: cannot read source_runs.jsonl: %s", exc)
        return 0

    raw_lines = blob.decode("utf-8", errors="replace").splitlines()
    if start > 0 and raw_lines:
        # Seeked into the middle of a record — drop the partial first line.
        raw_lines = raw_lines[1:]

    # Newest-backwards: count consecutive unusable records for THIS url,
    # stopping at the first usable run for the url.
    count = 0
    for line in reversed(raw_lines):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("url") != source_url and record.get("official_url") != source_url:
            continue
        status = str(record.get("change_status") or record.get("status") or "").upper()
        if _record_is_dark(record):
            count += 1
        elif status in _UNUSABLE_RUN_STATUSES:
            # A quality drop that is NOT darkness (sticky shrink suppression, or
            # a good extraction reclassified on size): neutral — it neither
            # proves the source is dark nor proves it recovered.
            continue
        else:
            break
    return count


def _maybe_open_circuit(name: str, source_url: str, circuit_key: str) -> None:
    """Open the breaker when the trail shows >= threshold consecutive unusable
    runs for this source. Called from BOTH the raising-failure path and the
    guard-abort path — a source that is dark without raising is exactly the
    chronic failure the breaker exists to detect."""
    consec = _consecutive_failures(source_url)
    if consec < _CIRCUIT_OPEN_THRESHOLD:
        return
    if circuit_key not in _circuit_open:
        _circuit_open.add(circuit_key)
        _save_circuit_state(_circuit_open)
    logger.warning(
        "CIRCUIT_BREAKER open for %s after %d consecutive unusable runs "
        "(FAILED/QUALITY_DROP) — source will be skipped; delete %s to reset",
        name, consec, _CIRCUIT_STATE_FILE,
    )


def monitor_all_sources(
    verbose: bool = False,
) -> list[dict]:
    """
    Run the change-detection pipeline over all enabled sources.

    Parameters
    ----------
    verbose : bool
        When True, print a short progress line to stdout before and after
        each source.  Useful for the CLI ``all`` command.

    Returns
    -------
    list[dict]
        One result dict per source, in the order they appear in sources.json.
        Return type is always a list for backward compatibility with
        scheduler.py and run.py callers.

        Cycle-level metadata is emitted as a structured CYCLE_SUMMARY log
        line rather than changing the return type.
    """
    cycle_start = datetime.now(timezone.utc)
    cycle_id    = str(uuid.uuid4())

    sources = get_enabled_sources()
    total   = len(sources)
    init_pipeline(AI_MAX_CALLS_PER_RUN)

    if total == 0:
        logger.warning("No enabled sources found in sources.json")
        if verbose:
            print("  No enabled sources found in sources.json")
        return []

    results: list[dict] = []
    _counter: dict = {
        "ok": 0, "unchanged": 0, "failed": 0, "quality_drop": 0,
        "seals_attempted": 0, "seals_failed": 0,
        "appends_failed": 0,
    }

    for idx, source in enumerate(sources, 1):
        name = source.get("name", source["url"])
        jur  = source.get("jurisdiction", "")
        # Circuit-breaker key: the source URL — the SAME key _consecutive_failures
        # counts by (it filters trail records on url/official_url). Keying the
        # breaker on the display `name` let two same-named sources share one
        # breaker (one's trip darkened both; one's success cleared the other), and
        # the derived source_id can collide on same-name+same-jurisdiction sources
        # without an explicit id. URLs are unique per enabled source, so this
        # aligns the breaker state 1:1 with the failure count. `name` stays for
        # display/logging only.
        circuit_key = source.get("url", "") or name

        # ── circuit-breaker: skip open sources, with a half-open probe ────────
        # An OPEN circuit is skipped for _CIRCUIT_PROBE_EVERY_N_CYCLES cycles,
        # after which one probe is allowed through (fall past this block). A
        # successful probe auto-resets the breaker (see _clear_circuit on the
        # success path); a failing probe re-arms the skip. This is what lets a
        # source recover from a transient outage without a process restart.
        if circuit_key in _circuit_open:
            skipped = _circuit_skip_counts.get(circuit_key, 0)
            if skipped < _CIRCUIT_PROBE_EVERY_N_CYCLES:
                _circuit_skip_counts[circuit_key] = skipped + 1
                logger.warning(
                    "CIRCUIT_OPEN [%d/%d]: %s — skipping (>= %d consecutive "
                    "historical failures; auto-probe in %d cycle(s), or delete "
                    "%s to reset now)",
                    idx, total, name, _CIRCUIT_OPEN_THRESHOLD,
                    _CIRCUIT_PROBE_EVERY_N_CYCLES - skipped, _CIRCUIT_STATE_FILE,
                )
                if verbose:
                    print(f"  [{idx}/{total}] {name}  — SKIPPED (circuit open)", flush=True)
                results.append({
                    "source_name":   name,
                    "url":           source.get("url", ""),
                    "jurisdiction":  source.get("jurisdiction", ""),
                    "category":      source.get("category", ""),
                    "source_status": source.get("status", "active"),
                    "changed":       False,
                    "status":        "error",
                    "access_status": "circuit_open",
                    "error":         "Circuit open: too many consecutive failures",
                    "circuit_open":  True,
                })
                _counter["failed"] += 1
                # Durable proof that this source was NOT seen this cycle.
                _persist_circuit_open_record(source)
                continue
            # Cooldown elapsed — allow a single half-open probe this cycle.
            _circuit_skip_counts[circuit_key] = 0
            logger.info(
                "CIRCUIT_HALF_OPEN [%d/%d]: %s — probing after cooldown",
                idx, total, name,
            )

        if verbose:
            label = f"{name}  ({jur})" if jur else name
            print(f"  [{idx}/{total}] {label} ...", flush=True)

        logger.info(
            "Monitoring [%d/%d]: %s — %s", idx, total, name, source["url"]
        )

        # ── per-source retry loop (max 1 retry after 5 s) ────────────────────
        last_exc: Exception | None = None
        result: dict | None = None

        for attempt in range(2):  # attempt 0 = first try, attempt 1 = retry
            try:
                result = run_pipeline_for_source(source)
                last_exc = None
                break  # success — exit retry loop
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                last_exc = exc
                if attempt == 0:
                    logger.warning(
                        "Retry [%d/%d] attempt 1 failed for %s (%s: %s) — "
                        "retrying in %ds",
                        idx, total, name, type(exc).__name__, exc,
                        _RETRY_DELAY_SECONDS,
                    )
                    time.sleep(_RETRY_DELAY_SECONDS)
                else:
                    logger.error(
                        "Retry [%d/%d] attempt 2 failed for %s (%s: %s) — "
                        "recording error",
                        idx, total, name, type(exc).__name__, exc,
                    )

        if last_exc is not None:
            # Both attempts failed — write error record.
            error_msg     = f"{type(last_exc).__name__}: {last_exc}"
            access_status = _classify_access_status(last_exc)

            if verbose:
                print(f"       → error: {error_msg}")

            error_record: dict = {
                "source_name":   name,
                "url":           source.get("url", ""),
                "jurisdiction":  source.get("jurisdiction", ""),
                "category":      source.get("category", ""),
                "source_status": source.get("status", "active"),
                "changed":       False,
                "status":        "error",
                "access_status": access_status,
                "error":         error_msg,
            }
            results.append(error_record)
            _counter["failed"] += 1

            # Persist a FAILED trail record so _consecutive_failures() can see
            # this failure — a raising pipeline never reaches append_run itself.
            _persist_failure_record(source, error_msg, access_status)

            # ── circuit-breaker check ─────────────────────────────────────
            _maybe_open_circuit(name, source.get("url", ""), circuit_key)
            continue

        # ── non-raising path ─────────────────────────────────────────────────
        assert result is not None
        results.append(result)

        if not _result_yielded_usable_content(result):
            # Guard-abort: the run returned cleanly but produced no usable
            # content (bot wall / error page / empty / undecodable / shrink
            # suppression). It is NOT a success — it must not clear the
            # breaker, and its QUALITY_DROP trail record counts toward the
            # consecutive-failure threshold like a hard failure does.
            _counter["quality_drop"] += 1
            logger.warning(
                "QUALITY_DROP [%d/%d]: %s — run yielded no usable content "
                "(status=%s); breaker counter NOT reset",
                idx, total, name, result.get("status"),
            )
            if verbose:
                print(f"       -> quality drop ({result.get('status')})")
            # The sticky content-shrink suppression is NOT darkness: the source
            # is reachable and its content genuinely changed. Counting it would
            # open the breaker on a live, changing page and stop fetching it —
            # and because the shrink guard re-fires every cycle until a human
            # re-baselines, a breaker opened for any other reason could never be
            # cleared by such a probe. The source demonstrably answered, so
            # treat it as recovery for breaker purposes.
            #
            # _is_non_dark_suppression only agrees when the run brought back a
            # PLAUSIBLE page (>= _PLAUSIBLE_PAGE_CHARS). A short unrecognised
            # wall page also lands on the shrink path, and letting that clear
            # the breaker would hand the monitored host control of our own
            # reliability control; below the floor we fall through to
            # _maybe_open_circuit and treat the cycle as darkness.
            if _is_non_dark_suppression(result):
                _clear_circuit(circuit_key)
            else:
                _maybe_open_circuit(name, source.get("url", ""), circuit_key)
            continue

        # Auto-reset the breaker: a successful run clears a previously-open
        # circuit so a source recovers on its own after a transient outage.
        _clear_circuit(circuit_key)

        if result.get("changed"):
            _counter["ok"] += 1
        else:
            _counter["unchanged"] += 1

        # Seal health: canonical_evidence_sealed is present (True/False) only
        # on runs that ATTEMPTED a seal (CHANGED/FIRST_SEEN after append_run).
        # Without this tally a systemic seal failure — the product's core
        # promise going dark — is invisible outside grep'ing logs.
        _sealed = result.get("canonical_evidence_sealed")
        if _sealed is not None:
            _counter["seals_attempted"] += 1
            if not _sealed:
                _counter["seals_failed"] += 1
        # An append_run failure is worse than a seal failure: no durable
        # record AND no alert, while the source still counts "ok" above.
        if result.get("evidence_append_failed"):
            _counter["appends_failed"] += 1

        if verbose:
            changed   = result.get("changed", False)
            is_new    = result.get("is_new",  False)
            risk      = result.get("risk_level", "LOW") if changed else ""
            if not changed:
                status_str = "unchanged"
            elif is_new:
                status_str = f"baseline stored  [{risk}]"
            else:
                added = result.get("added_count", 0)
                rem   = result.get("removed_count", 0)
                status_str = (
                    f"changed  [{risk}]  "
                    f"+{added} added  -{rem} removed"
                )
            print(f"       -> {status_str}")

        logger.info(
            "Done [%d/%d]: %s  changed=%s risk=%s",
            idx, total, name,
            result.get("changed"), result.get("risk_level", "—"),
        )

    # ── structured cycle summary log ─────────────────────────────────────────
    summary = {
        "cycle_id":          cycle_id,
        "started_at":        cycle_start.isoformat(),
        "completed_at":      datetime.now(timezone.utc).isoformat(),
        "sources_total":     total,
        "sources_ok":        _counter["ok"],
        "sources_unchanged": _counter["unchanged"],
        "sources_failed":    _counter["failed"],
        # Guard-aborted sources (dark, but not raising). Counted separately
        # from `unchanged` so a fleet-wide bot-wall no longer reads as a
        # healthy all-unchanged cycle in the summary or to the deadman.
        "sources_quality_drop": _counter["quality_drop"],
        "seals_attempted":   _counter["seals_attempted"],
        "seals_failed":      _counter["seals_failed"],
        "evidence_appends_failed": _counter["appends_failed"],
    }
    logger.info("CYCLE_SUMMARY %s", json.dumps(summary))

    # Deadman: alert the founder on the transition into a catastrophic cycle
    # (all-fail / nothing-succeeded). Best-effort — never breaks the loop.
    _maybe_alert_catastrophic_cycle(summary)

    # Seal deadman: every seal attempt failing means alerts are flowing WITHOUT
    # sealed evidence — the core promise silently off. Best-effort, same
    # rate-limit philosophy as the catastrophic-cycle alert.
    _maybe_alert_seal_failures(summary)

    return results
