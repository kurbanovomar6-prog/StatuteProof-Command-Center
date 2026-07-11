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
- Circuit-breaker: source skipped after >= 5 consecutive failures
  (tracked in _circuit_open module-level set; reset on process restart).
- Structured CYCLE_SUMMARY log line at end of each run.
"""

import json
import logging
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

# Half-open cadence: an OPEN circuit is skipped for this many cycles, then a
# single probe is allowed through. A successful probe auto-resets the breaker
# (WARN-6) so a source recovers on its own after a transient outage instead of
# staying skipped forever; a failing probe re-arms the skip. Must be >= 1 so
# the cycle immediately after opening still skips.
_CIRCUIT_PROBE_EVERY_N_CYCLES = 5

# How many recent JSONL records to scan per source when checking history.
_CIRCUIT_HISTORY_SCAN = 200

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


def _classify_access_status(exc: Exception) -> str:
    """Classify an exception into a machine-readable access_status string."""
    msg = str(exc).lower()
    if "403" in msg or "forbidden" in msg:
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


def _consecutive_failures(source_url: str) -> int:
    """
    Count consecutive FAILED statuses for source_url from source_runs.jsonl,
    reading from newest record backwards.

    Reads the last _CIRCUIT_HISTORY_SCAN lines of the JSONL file and counts
    consecutive "FAILED" change_status values for the given URL, stopping at
    the first non-failure.  Returns 0 when the file is absent or unreadable.
    """
    try:
        # Resolve the run file the SAME way append_run does (honoring
        # STATUTEPROOF_BASE_DIR) so the breaker reads exactly the file the
        # failure record was just written to, not a stale hardcoded path.
        from app.source_runs import source_run_path

        run_file = source_run_path()
        if not run_file.exists():
            return 0
        raw_lines = run_file.read_text(encoding="utf-8").splitlines()
    except Exception as exc:
        logger.warning("circuit_breaker: cannot read source_runs.jsonl: %s", exc)
        return 0

    # Scan only the tail of the file to keep this O(scan_window).
    tail = raw_lines[-_CIRCUIT_HISTORY_SCAN:]

    # Collect records for this URL in chronological order, then reverse.
    url_records: list[dict] = []
    for line in tail:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("url") == source_url or record.get("official_url") == source_url:
            url_records.append(record)

    # Count consecutive failures from newest backwards.
    count = 0
    for record in reversed(url_records):
        status = str(record.get("change_status") or record.get("status") or "").upper()
        if status == "FAILED":
            count += 1
        else:
            break
    return count


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
    _counter: dict = {"ok": 0, "unchanged": 0, "failed": 0}

    for idx, source in enumerate(sources, 1):
        name = source.get("name", source["url"])
        jur  = source.get("jurisdiction", "")

        # ── circuit-breaker: skip open sources, with a half-open probe ────────
        # An OPEN circuit is skipped for _CIRCUIT_PROBE_EVERY_N_CYCLES cycles,
        # after which one probe is allowed through (fall past this block). A
        # successful probe auto-resets the breaker (see _clear_circuit on the
        # success path); a failing probe re-arms the skip. This is what lets a
        # source recover from a transient outage without a process restart.
        if name in _circuit_open:
            skipped = _circuit_skip_counts.get(name, 0)
            if skipped < _CIRCUIT_PROBE_EVERY_N_CYCLES:
                _circuit_skip_counts[name] = skipped + 1
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
                continue
            # Cooldown elapsed — allow a single half-open probe this cycle.
            _circuit_skip_counts[name] = 0
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
            source_url = source.get("url", "")
            consec = _consecutive_failures(source_url)
            if consec >= _CIRCUIT_OPEN_THRESHOLD:
                _circuit_open.add(name)
                _save_circuit_state(_circuit_open)
                logger.warning(
                    "CIRCUIT_BREAKER opened for %s after %d consecutive "
                    "historical failures — source will be skipped; "
                    "delete %s to reset",
                    name, consec, _CIRCUIT_STATE_FILE,
                )
            continue

        # ── success path ─────────────────────────────────────────────────────
        assert result is not None
        results.append(result)

        # Auto-reset the breaker: a successful run clears a previously-open
        # circuit so a source recovers on its own after a transient outage.
        _clear_circuit(name)

        if result.get("changed"):
            _counter["ok"] += 1
        else:
            _counter["unchanged"] += 1

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
    }
    logger.info("CYCLE_SUMMARY %s", json.dumps(summary))

    # Deadman: alert the founder on the transition into a catastrophic cycle
    # (all-fail / nothing-succeeded). Best-effort — never breaks the loop.
    _maybe_alert_catastrophic_cycle(summary)

    return results
