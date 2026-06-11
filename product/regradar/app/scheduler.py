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
from datetime import datetime

from app.config import WATCH_INTERVAL_MINUTES
from app.monitor import monitor_all_sources

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

    print(f"\n  {_BOLD}StatuteProof watch mode started.{_R}")
    print(
        f"  Checking all enabled sources every "
        f"{interval} minute{'s' if interval != 1 else ''}."
    )
    print(f"  Press {_BOLD}Ctrl+C{_R} to stop.\n")

    cycle = 0

    try:
        while True:
            cycle += 1
            _print_cycle_header(cycle, interval)

            try:
                results = monitor_all_sources(verbose=True)
                _print_cycle_summary(results)
            except Exception as exc:
                # Per-source errors are already handled inside monitor_all_sources.
                # This catches unexpected failures at the orchestrator level.
                logger.error(
                    "Watch cycle %d failed: %s: %s", cycle, type(exc).__name__, exc
                )
                print(
                    f"\n  {_RED}Cycle {cycle} unexpected error:{_R} "
                    f"{type(exc).__name__}: {exc}"
                )
                print(f"  Recovering — will retry next cycle in 30 s.\n")
                time.sleep(30)

            print(
                f"  {_DIM}Next check in "
                f"{interval} minute{'s' if interval != 1 else ''} "
                f"— Ctrl+C to stop.{_R}\n"
            )
            time.sleep(interval * 60)

    except KeyboardInterrupt:
        print(
            f"\n  {_BOLD}StatuteProof watch mode stopped.{_R}  "
            f"({cycle} cycle{'s' if cycle != 1 else ''} completed)\n"
        )
