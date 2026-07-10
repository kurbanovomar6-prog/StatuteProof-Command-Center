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

# How many consecutive historical failures before a circuit opens.
_CIRCUIT_OPEN_THRESHOLD = 3

# How many recent JSONL records to scan per source when checking history.
_CIRCUIT_HISTORY_SCAN = 200

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

        # ── circuit-breaker: skip sources with too many consecutive failures ──
        if name in _circuit_open:
            logger.warning(
                "CIRCUIT_OPEN [%d/%d]: %s — skipping (>= %d consecutive "
                "historical failures; delete %s to reset)",
                idx, total, name, _CIRCUIT_OPEN_THRESHOLD, _CIRCUIT_STATE_FILE,
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

    return results
