"""
RegRadar v5 — watch-mode scheduler.

run_watch_loop() runs monitor_all_sources() on a fixed interval,
printing a timestamped cycle header and per-source summary table after
each run.  Stops cleanly on Ctrl+C; recovers from unexpected errors
without killing the loop.

No external scheduler library is used — just time.sleep().
"""

import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from app.config import BASE_DIR, WATCH_INTERVAL_MINUTES
from app.monitor import monitor_all_sources
from app.pipeline import run_pipeline_for_source

logger = logging.getLogger(__name__)

# ── ANSI colour codes ─────────────────────────────────────────────────────────
_R      = "\033[0m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"
_GREEN  = "\033[32m"
_YELLOW = "\033[33m"
_RED    = "\033[31m"
_CYAN   = "\033[36m"

_RISK_COLOR = {"HIGH": _RED, "MEDIUM": _YELLOW, "LOW": _GREEN}
_RISK_ICON  = {"HIGH": "🔴", "MEDIUM": "🟡",   "LOW": "🟢"}
_FLAG       = {
    "RU": "🇷🇺", "KZ": "🇰🇿", "AZ": "🇦🇿",
    "BY": "🇧🇾", "UZ": "🇺🇿", "INT": "🌐",
}

WIDTH = 68

# ── Priority tiers ────────────────────────────────────────────────────────────
#
# Sources declare their urgency via  "monitoring_priority"  in sources.json.
# The field is optional; the default tier is "standard".
#
#   critical   → run every 30 minutes
#   standard   → run at the configured WATCH_INTERVAL_MINUTES (default 60 min)
#   background → run once per day (1440 minutes)
#
# The scheduler currently uses these constants for logging and
# get_sources_by_priority().  Active enforcement of the critical 30-minute
# sub-cycle is handled inside run_watch_loop() using _CRITICAL_INTERVAL_MINUTES.

# How often (minutes) critical-priority sources are re-checked between full cycles.
_CRITICAL_INTERVAL_MINUTES = 30
_DEFAULT_PRIORITY = "standard"

# sources.json lives one level above this module (project root)
_SOURCES_JSON = Path(__file__).parent.parent / "sources.json"

# Heartbeat file — touched at the end of every FULL cycle. An external watchdog
# (deploy/systemd/statuteproof-heartbeat.timer) reads its mtime and alerts the
# founder if it is older than 2× the interval. This catches a wedged loop that
# is alive (so Restart=on-failure never fires) but has stopped making progress.
# Resolved via config.BASE_DIR (honors STATUTEPROOF_BASE_DIR) so the writer here
# and the watchdog reader in app/ops_alert.py agree on exactly one file.
_HEARTBEAT_FILE = Path(BASE_DIR) / "data" / "monitor_heartbeat"


def write_heartbeat() -> bool:
    """Touch the monitor heartbeat file with the current UTC time.

    Best-effort: a heartbeat write failure must never break the watch loop, so
    this swallows all errors and returns False. Returns True on success.
    """
    try:
        _HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)
        _HEARTBEAT_FILE.write_text(
            datetime.now(timezone.utc).isoformat(timespec="seconds") + "\n",
            encoding="utf-8",
        )
        return True
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("heartbeat: could not write %s: %s", _HEARTBEAT_FILE, exc)
        return False


def get_sources_by_priority(priority: str) -> list[dict]:
    """
    Return all enabled sources that have the given monitoring_priority value.

    Sources without a monitoring_priority field are treated as "standard".

    Parameters
    ----------
    priority : str
        One of "critical", "standard", or "background".

    Returns
    -------
    list[dict]
        Enabled source entries matching the requested priority, in file order.
        Returns an empty list when sources.json is missing or unreadable.
    """
    import json as _json  # local import to avoid circular imports at module level

    try:
        raw = _SOURCES_JSON.read_text(encoding="utf-8")
        all_sources = _json.loads(raw)
    except Exception as exc:
        logger.warning("get_sources_by_priority: cannot read sources.json: %s", exc)
        return []

    if not isinstance(all_sources, list):
        logger.warning("get_sources_by_priority: sources.json is not a list")
        return []

    matched = [
        s for s in all_sources
        if isinstance(s, dict)
        and s.get("enabled") is True
        and s.get("monitoring_priority", _DEFAULT_PRIORITY) == priority
    ]
    logger.debug(
        "get_sources_by_priority(%r): %d sources matched", priority, len(matched)
    )
    return matched


def _log_priority_summary() -> None:
    """Log a one-time breakdown of sources by priority tier for operator visibility."""
    for tier in ("critical", "standard", "background"):
        sources = get_sources_by_priority(tier)
        if sources:
            names = ", ".join(s.get("name", s.get("url", "?")) for s in sources)
            logger.info("Priority [%s] (%d sources): %s", tier, len(sources), names)
        else:
            logger.debug("Priority [%s]: no enabled sources", tier)


def _hr(char: str = "─") -> None:
    print(char * WIDTH)


def _print_cycle_header(cycle: int, interval: int) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _hr()
    print(f"  {_BOLD}StatuteProof watch cycle #{cycle}{_R}")
    print(f"  Time:     {now}")
    print(f"  Interval: {interval} minute{'s' if interval != 1 else ''}")
    _hr()


def _print_cycle_summary(results: list[dict]) -> None:
    if not results:
        print(f"  {_DIM}No results returned.{_R}\n")
        return

    _hr()
    print(f"  {_BOLD}Cycle summary{_R}")
    _hr("·")

    for r in results:
        name = r.get("source_name", r.get("url", "?"))[:36]
        jur  = r.get("jurisdiction", "")
        flag = _FLAG.get(jur, " ")

        if r.get("status") == "error":
            status_str = f"{_RED}✗  error{_R}"
        elif not r.get("changed"):
            status_str = f"{_GREEN}✓  unchanged{_R}"
        elif r.get("is_new"):
            status_str = f"{_CYAN}★  baseline{_R}"
        else:
            risk  = r.get("risk_level", "LOW")
            col   = _RISK_COLOR.get(risk, _R)
            icon  = _RISK_ICON.get(risk, "")
            added = r.get("added_count", 0)
            rem   = r.get("removed_count", 0)
            status_str = (
                f"{_YELLOW}⚡  changed{_R}  "
                f"{col}{icon} {risk}{_R}  "
                f"+{added} -{rem}"
            )

        quality    = r.get("extraction_quality", "")
        chars      = r.get("extracted_chars")
        src_status = r.get("source_status", "active")

        if quality == "good":
            qual_badge = f"{_GREEN}✓ good{_R}"
        elif quality == "low_content":
            qual_badge = f"{_YELLOW}⚠ low{_R}"
        elif quality == "failed":
            qual_badge = f"{_RED}✗ fail{_R}"
        else:
            qual_badge = ""

        chars_str   = f"{chars:>5,}c" if chars is not None else "      "
        limited_str = f"  {_DIM}[limited]{_R}" if src_status == "limited" else ""
        qual_col    = f"  {chars_str}  {qual_badge}" if qual_badge else ""

        print(f"  {flag} {name:<36}  {status_str}{qual_col}{limited_str}")

    total         = len(results)
    ok_count      = sum(1 for r in results if r.get("status") != "error")
    changed_count = sum(1 for r in results if r.get("changed") and not r.get("is_new"))
    new_count     = sum(1 for r in results if r.get("is_new"))
    high_count    = sum(1 for r in results if r.get("risk_level") == "HIGH")
    low_q_count   = sum(1 for r in results if r.get("extraction_quality") == "low_content")
    error_count   = sum(1 for r in results if r.get("status") == "error")

    _hr("·")
    print(
        f"  {_DIM}Total: {total}  ok: {ok_count}  changed: {changed_count}  "
        f"new: {new_count}  high-risk: {high_count}  "
        f"low-content: {low_q_count}  errors: {error_count}{_R}"
    )
    print()


def run_watch_loop(interval_minutes: int | None = None) -> None:
    """
    Repeatedly run monitor_all_sources() on a fixed interval.

    Parameters
    ----------
    interval_minutes : int | None
        Cycle interval in minutes.  If None, falls back to
        WATCH_INTERVAL_MINUTES from config (default 60).

    Stops cleanly on KeyboardInterrupt (Ctrl+C).
    Logs and recovers from any other exception — a single broken cycle
    never kills the loop permanently.
    """
    interval = interval_minutes if interval_minutes is not None else WATCH_INTERVAL_MINUTES

    # Log a one-time priority breakdown so operators can verify configuration.
    _log_priority_summary()

    critical_sources = get_sources_by_priority("critical")
    has_critical = len(critical_sources) > 0

    print(f"\n  {_BOLD}StatuteProof watch mode started.{_R}")
    print(
        f"  Checking all enabled sources every "
        f"{interval} minute{'s' if interval != 1 else ''}."
    )
    if has_critical:
        print(
            f"  {_YELLOW}Critical sources ({len(critical_sources)}): "
            f"re-checked every {_CRITICAL_INTERVAL_MINUTES} minutes.{_R}"
        )
    print(f"  Press {_BOLD}Ctrl+C{_R} to stop.\n")

    # Startup heartbeat. The first full cycle sweeps every source and can take
    # many minutes; without this the heartbeat file is missing/stale for that
    # whole window, so a fresh deploy would trip the watchdog and false-alarm
    # the founder before the first cycle ever completes. Writing it once here,
    # before the first monitor_all_sources() sweep, closes that startup gap.
    # End-of-cycle writes below keep it fresh thereafter. Best-effort like all
    # heartbeat writes — a failure never blocks the loop.
    write_heartbeat()

    cycle = 0
    # Track when we last ran the full cycle so we can decide whether to run
    # critical sources only (sub-cycle) or all sources (full cycle).
    # NOTE: last_full_run_at is intentionally initialised to 0.0 so that a
    # full cycle runs immediately on startup — this ensures the monitor is
    # current from the first moment the process is alive (desirable for
    # reliability, not a bug).
    last_full_run_at: float = 0.0

    try:
        while True:
            now = time.monotonic()
            full_cycle_due = (now - last_full_run_at) >= (interval * 60)

            if full_cycle_due:
                cycle += 1
                _print_cycle_header(cycle, interval)
                try:
                    results = monitor_all_sources(verbose=True)
                    _print_cycle_summary(results)
                    last_full_run_at = time.monotonic()
                    # Progress marker for the external watchdog. Written only
                    # after a full cycle completes without an orchestrator-level
                    # exception, so a wedged/aborted cycle leaves the file stale.
                    write_heartbeat()
                except Exception as exc:
                    # Per-source errors are handled inside monitor_all_sources.
                    # This catches unexpected failures at the orchestrator level.
                    logger.error(
                        "Watch cycle %d failed: %s: %s",
                        cycle, type(exc).__name__, exc,
                    )
                    print(
                        f"\n  {_RED}Cycle {cycle} unexpected error:{_R} "
                        f"{type(exc).__name__}: {exc}"
                    )
                    print(f"  Recovering — will retry next cycle in 30 s.\n")
                    time.sleep(30)
            elif has_critical:
                # Sub-cycle: run ONLY the critical-priority sources directly,
                # without touching standard/background sources at all.
                logger.info(
                    "Critical sub-cycle: running %d critical source(s)",
                    len(critical_sources),
                )
                try:
                    critical_results: list[dict] = []
                    for src in critical_sources:
                        src_name = src.get("name", src.get("url", "?"))
                        try:
                            result = run_pipeline_for_source(src)
                            critical_results.append(result)
                        except Exception as src_exc:
                            logger.error(
                                "Critical sub-cycle error for %s: %s: %s",
                                src_name, type(src_exc).__name__, src_exc,
                            )
                            critical_results.append({
                                "source_name":   src_name,
                                "url":           src.get("url", ""),
                                "jurisdiction":  src.get("jurisdiction", ""),
                                "category":      src.get("category", ""),
                                "changed":       False,
                                "status":        "error",
                                "access_status": "error",
                                "error":         f"{type(src_exc).__name__}: {src_exc}",
                            })
                    if critical_results:
                        print(
                            f"  {_DIM}Critical sub-cycle "
                            f"({len(critical_results)} source(s)):{_R}"
                        )
                        _print_cycle_summary(critical_results)
                except Exception as exc:
                    logger.error(
                        "Critical sub-cycle error: %s: %s", type(exc).__name__, exc
                    )

            print(
                f"  {_DIM}Next check in "
                f"{_CRITICAL_INTERVAL_MINUTES if has_critical else interval} "
                f"minute(s) — Ctrl+C to stop.{_R}\n"
            )
            # Sleep the shorter interval when critical sources are configured;
            # otherwise sleep the full configured interval.
            sleep_minutes = _CRITICAL_INTERVAL_MINUTES if has_critical else interval
            time.sleep(sleep_minutes * 60)

    except KeyboardInterrupt:
        print(
            f"\n  {_BOLD}StatuteProof watch mode stopped.{_R}  "
            f"({cycle} cycle{'s' if cycle != 1 else ''} completed)\n"
        )
