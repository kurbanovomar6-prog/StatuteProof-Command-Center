"""G3 bug: _clean() infinite loop on '.….' (period-ellipsis-period).

app/alert_content.py:_clean collapses double periods. The original loop
condition tested `".." in out.replace("…", "")` while the body mutated the
un-stripped `out`, so an input like `.….` (period-U+2026-period, no adjacent
`..`) made the condition permanently true while `out` never changed —
an infinite CPU hang that wedged alert delivery for that run.

These tests are guarded by SIGALRM so a regression re-introducing the hang
fails the suite instead of freezing it.
"""

from __future__ import annotations

import signal
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.alert_content import _build_excerpt, _clean


class _Timeout(Exception):
    pass


def _run_with_timeout(fn, *args, seconds: int = 5):
    """Run fn(*args) but raise _Timeout (not hang) if it exceeds `seconds`."""
    def _handler(signum, frame):
        raise _Timeout("call exceeded time budget — likely infinite loop")

    old = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)
    try:
        return fn(*args)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def test_clean_terminates_on_period_ellipsis_period():
    # Pre-fix: this input hangs forever. Post-fix it returns promptly.
    out = _run_with_timeout(_clean, "section 5.….subsection")
    # The ellipsis is preserved; the input has no adjacent ".." so nothing
    # is collapsed.
    assert out == "section 5.….subsection"


def test_clean_still_collapses_real_double_periods():
    assert _clean("a..b...c") == "a.b.c"


def test_clean_leaves_lone_ellipsis_untouched():
    assert _clean("done…") == "done…"
    assert _clean("..…") == ".…"


def test_build_excerpt_does_not_hang_on_ellipsis_chunk():
    # The production trigger: a diff chunk carrying '.….' flows through
    # _build_excerpt -> _clean. It must complete, not hang.
    excerpt = _run_with_timeout(
        _build_excerpt, ["Rule 5.….amended and effective now"], []
    )
    assert "Rule 5" in excerpt
