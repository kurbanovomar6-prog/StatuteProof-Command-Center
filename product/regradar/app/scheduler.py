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
from app.monitor import (
    _new_cycle_counter,
    _run_one_source,
    monitor_all_sources,
)

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

# ── Per-source cadence ────────────────────────────────────────────────────────
#
# A source may declare  "check_interval_minutes"  in sources.json to be
# re-checked more often than the full-fleet cycle (e.g. UAE sanctions/TFS
# sources, where the freeze obligation is effectively immediate/24h so a
# daily fleet sweep is too slow). Sources WITHOUT the field keep the fleet
# cadence — the default is unchanged.
#
# Enforcement mirrors the critical sub-cycle: between full cycles the loop
# wakes often enough (see _next_sleep_minutes) and runs only the sources
# whose own interval has elapsed. A full cycle counts as a run for every
# such source, so nothing is double-checked right after a fleet sweep.
#
# Floor: polling an official regulator more often than every 30 minutes is
# abuse, not monitoring — misconfigured smaller values are clamped up.
_MIN_CUSTOM_INTERVAL_MINUTES = 30


def get_custom_interval_minutes(source: dict) -> int | None:
    """Return the validated per-source cadence in minutes, or None.

    None means "no per-source cadence" (fleet default). Non-integer or
    non-positive values are rejected with a warning; values below the
    30-minute floor are clamped up to the floor.
    """
    if not isinstance(source, dict):
        return None
    raw = source.get("check_interval_minutes")
    if raw is None:
        return None
    try:
        minutes = int(raw)
    except (TypeError, ValueError):
        logger.warning(
            "check_interval_minutes=%r on source %r is not an integer — ignored",
            raw, source.get("source_id") or source.get("name"),
        )
        return None
    if minutes <= 0:
        logger.warning(
            "check_interval_minutes=%d on source %r is not positive — ignored",
            minutes, source.get("source_id") or source.get("name"),
        )
        return None
    if minutes < _MIN_CUSTOM_INTERVAL_MINUTES:
        logger.warning(
            "check_interval_minutes=%d on source %r below the %d-minute floor — clamped",
            minutes, source.get("source_id") or source.get("name"),
            _MIN_CUSTOM_INTERVAL_MINUTES,
        )
        return _MIN_CUSTOM_INTERVAL_MINUTES
    return minutes


def _cadence_key(source: dict) -> str:
    """Per-source cadence bookkeeping key — the URL, matching the
    circuit-breaker key in app/monitor.py (URLs are unique per enabled
    source; names can collide)."""
    return source.get("url", "") or source.get("name", "")


def _due_custom_sources(
    sources: list[dict],
    last_run_at: dict[str, float],
    now_monotonic: float,
) -> list[dict]:
    """Return the sources whose own check_interval_minutes has elapsed
    since their last recorded run. Pure function — unit-testable."""
    due: list[dict] = []
    for source in sources:
        minutes = get_custom_interval_minutes(source)
        if minutes is None:
            continue
        last = last_run_at.get(_cadence_key(source))
        # No bookkeeping entry means the source has never run in this
        # process — due now (the startup full cycle normally stamps it, so
        # this only fires when that first cycle failed).
        if last is None or (now_monotonic - last) >= minutes * 60:
            due.append(source)
    return due


def _next_sleep_minutes(
    interval: int,
    has_critical: bool,
    custom_sources: list[dict],
) -> int:
    """Sleep granularity for the watch loop: the smallest cadence that
    must be honoured. Fleet-only deployments keep the exact old behaviour
    (interval, or 30 when critical sources exist)."""
    candidates = [interval]
    if has_critical:
        candidates.append(_CRITICAL_INTERVAL_MINUTES)
    for source in custom_sources:
        minutes = get_custom_interval_minutes(source)
        if minutes is not None:
            candidates.append(minutes)
    return max(1, min(candidates))

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


def run_deadline_reminder_pass(base_dir: Path | None = None) -> dict:
    """Best-effort daily deadline-reminder pass.

    Delegates to ``app.deadline_radar.send_due_reminders`` (which is itself
    idempotent per lead stage, so calling it more than once a day is safe — it
    only sends a stage that has newly become due). Never raises; a failure here
    must never break the watch loop.
    """
    try:
        from app.deadline_radar import send_due_reminders

        return send_due_reminders(base_dir=base_dir)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("deadline reminder pass failed (non-fatal): %s", exc)
        return {"status": "error", "error": str(exc)}


def run_digest_dispatch_pass() -> dict:
    """Best-effort scheduled digest + all-clear heartbeat dispatch.

    Delegates to ``app.digest_cadence.run_scheduled_digests``, which is itself
    idempotent: instant HIGH/urgent alerts are per-alert idempotent, and
    daily/weekly bundles + quiet-window heartbeats are idempotent per period
    (the period key, not this call frequency, enforces the cadence). Safe to run
    every full cycle. Never raises — a failure here must never break the watch
    loop.
    """
    try:
        from app.digest_cadence import run_scheduled_digests

        return run_scheduled_digests()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("digest dispatch pass failed (non-fatal): %s", exc)
        return {"status": "error", "error": str(exc)}


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


def get_sources_with_custom_interval() -> list[dict]:
    """Return all enabled sources that declare a valid per-source cadence
    (``check_interval_minutes``), in file order. Empty list when
    sources.json is missing or unreadable."""
    import json as _json  # local import to avoid circular imports at module level

    try:
        raw = _SOURCES_JSON.read_text(encoding="utf-8")
        all_sources = _json.loads(raw)
    except Exception as exc:
        logger.warning("get_sources_with_custom_interval: cannot read sources.json: %s", exc)
        return []

    if not isinstance(all_sources, list):
        logger.warning("get_sources_with_custom_interval: sources.json is not a list")
        return []

    matched = [
        s for s in all_sources
        if isinstance(s, dict)
        and s.get("enabled") is True
        and get_custom_interval_minutes(s) is not None
    ]
    logger.debug("get_sources_with_custom_interval: %d sources matched", len(matched))
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

    # Per-source cadence (check_interval_minutes): re-checked between full
    # cycles, exactly like the critical sub-cycle. Loaded once at startup —
    # same lifecycle as critical_sources.
    custom_sources = get_sources_with_custom_interval()
    has_custom = len(custom_sources) > 0
    # Monotonic timestamp of each custom source's last run (full cycles count).
    custom_last_run: dict[str, float] = {}

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
    if has_custom:
        print(
            f"  {_YELLOW}Per-source cadence ({len(custom_sources)}): "
            + ", ".join(
                f"{src.get('source_id') or src.get('name', '?')}"
                f"={get_custom_interval_minutes(src)}m"
                for src in custom_sources
            )
            + f"{_R}"
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
    # Deadline reminders run at most once per UTC calendar day, after a full
    # cycle. Empty string forces a pass on the first completed cycle.
    last_deadline_pass_date: str = ""

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
                    # A full cycle sweeps every enabled source, so it counts
                    # as a run for each per-cadence source — otherwise they
                    # would be re-fetched immediately on the next sub-wake.
                    for _src in custom_sources:
                        custom_last_run[_cadence_key(_src)] = last_full_run_at
                    # Progress marker for the external watchdog. Written only
                    # after a full cycle completes without an orchestrator-level
                    # exception, so a wedged/aborted cycle leaves the file stale.
                    write_heartbeat()

                    # Daily deadline-reminder pass (best-effort, once per UTC
                    # day). Fires 30/7/1-day lead reminders for monitored
                    # effective/consultation/transition dates through the
                    # existing customer channels; deduped per lead stage.
                    today_utc = datetime.now(timezone.utc).date().isoformat()
                    if today_utc != last_deadline_pass_date:
                        last_deadline_pass_date = today_utc
                        dl_summary = run_deadline_reminder_pass()
                        sent = dl_summary.get("sent") or []
                        if sent:
                            print(
                                f"  {_CYAN}Deadline reminders sent: "
                                f"{len(sent)} stage(s).{_R}\n"
                            )

                    # Scheduled digest + all-clear heartbeat dispatch. Runs every
                    # full cycle; per-period idempotency (not this frequency)
                    # enforces each customer's daily/weekly cadence, while
                    # instant HIGH/urgent alerts still fire immediately.
                    digest_summary = run_digest_dispatch_pass()
                    dg_sent = int(digest_summary.get("digests_sent") or 0)
                    hb_sent = int(digest_summary.get("heartbeats_sent") or 0)
                    inst_sent = int(digest_summary.get("instant_sent") or 0)
                    if dg_sent or hb_sent or inst_sent:
                        print(
                            f"  {_CYAN}Customer delivery: {inst_sent} instant, "
                            f"{dg_sent} digest(s), {hb_sent} heartbeat(s).{_R}\n"
                        )
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
            elif has_critical or has_custom:
                # Sub-cycle: run ONLY the critical-priority sources plus any
                # per-cadence sources whose own interval has elapsed, without
                # touching standard/background sources at all.
                due_custom = (
                    _due_custom_sources(custom_sources, custom_last_run, now)
                    if has_custom else []
                )
                # A source can be both critical and per-cadence — run it once.
                _critical_keys = {_cadence_key(src) for src in critical_sources}
                due_custom = [
                    src for src in due_custom
                    if _cadence_key(src) not in _critical_keys
                ]
                if critical_sources or due_custom:
                    logger.info(
                        "Sub-cycle: running %d critical + %d per-cadence source(s)",
                        len(critical_sources), len(due_custom),
                    )
                try:
                    critical_results: list[dict] = []
                    sub_sources = critical_sources + due_custom
                    sub_total = len(sub_sources)
                    # Throwaway tally: _run_one_source mutates a counter in
                    # place; the sub-cycle does not emit a CYCLE_SUMMARY, so it
                    # is discarded.
                    sub_counter = _new_cycle_counter()
                    for idx, src in enumerate(sub_sources, 1):
                        # Route through the SAME per-source helper the full
                        # cycle uses, so the sub-cycle gains circuit-breaker
                        # skip, 2-attempt retry, durable FAILED / QUALITY_DROP
                        # trail records, and breaker open/clear. Previously the
                        # sub-cycle called the pipeline in a bare try/except
                        # that only fed a printed summary — a raising source
                        # left no durable FAILED record, never incremented the
                        # consecutive-failure count, and an OPEN circuit was
                        # re-probed every tick.
                        result = _run_one_source(
                            src, idx, sub_total, False, sub_counter
                        )
                        critical_results.append(result)
                        # Stamp per-cadence bookkeeping only when the source was
                        # actually run to a (non-error) result — matching the
                        # prior behaviour of not resetting the cadence timer on
                        # a failure or a circuit-open skip, so a failing source
                        # is retried rather than silenced for a full cadence.
                        if result.get("status") != "error":
                            custom_last_run[_cadence_key(src)] = time.monotonic()
                    if critical_results:
                        print(
                            f"  {_DIM}Sub-cycle "
                            f"({len(critical_results)} source(s)):{_R}"
                        )
                        _print_cycle_summary(critical_results)
                except Exception as exc:
                    logger.error(
                        "Sub-cycle error: %s: %s", type(exc).__name__, exc
                    )

            # Sleep the smallest cadence that must be honoured: the full
            # interval, the 30-minute critical sub-cycle when critical
            # sources exist, or the smallest per-source cadence. Deployments
            # without critical/per-cadence sources keep the old behaviour.
            sleep_minutes = _next_sleep_minutes(interval, has_critical, custom_sources)
            print(
                f"  {_DIM}Next check in {sleep_minutes} "
                f"minute(s) — Ctrl+C to stop.{_R}\n"
            )
            time.sleep(sleep_minutes * 60)

    except KeyboardInterrupt:
        print(
            f"\n  {_BOLD}StatuteProof watch mode stopped.{_R}  "
            f"({cycle} cycle{'s' if cycle != 1 else ''} completed)\n"
        )
