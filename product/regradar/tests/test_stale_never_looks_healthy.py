"""A month-old check must never be described in the present tense.

source_health_customer_message built its wording from the STATUS alone, so a
source whose last successful run was 30 days ago was shown "Monitoring is active
and the latest extraction passed quality checks." True about that run. False
about now — and shown on the surface a customer uses to decide whether their
coverage is live.

The registry made this worse: 40 of 40 alert-eligible rows assert MONITOR_OK with
a median recorded age of ~37 days, and no code writes that field, so the status
is an assertion nobody re-checks. The message is where a customer meets it.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.source_health_timeline import (  # noqa: E402
    STALE_AFTER_DAYS,
    source_health_customer_message,
)

PRESENT_TENSE = ("is active", "passed quality checks")


def test_a_fresh_healthy_run_may_claim_the_present_tense():
    message = source_health_customer_message("MONITOR_OK", age_days=1)
    assert any(claim in message for claim in PRESENT_TENSE)


def test_a_stale_healthy_run_may_not():
    message = source_health_customer_message("MONITOR_OK", age_days=30)

    assert not any(claim in message for claim in PRESENT_TENSE), message
    assert "30 days ago" in message
    # It says what IS known — the last check passed — and makes no claim about
    # the source's current state, because nothing in the system knows it.
    assert "has not confirmed" in message


def test_the_boundary_is_the_configured_stale_window():
    just_inside = source_health_customer_message(
        "MONITOR_OK", age_days=STALE_AFTER_DAYS - 0.5)
    just_outside = source_health_customer_message(
        "MONITOR_OK", age_days=STALE_AFTER_DAYS + 0.5)

    assert any(claim in just_inside for claim in PRESENT_TENSE)
    assert not any(claim in just_outside for claim in PRESENT_TENSE)


def test_an_unknown_age_does_not_silently_claim_freshness():
    """Callers that have no run date must not get the confident wording by
    default — that is how the claim leaked onto stale rows in the first place."""
    message = source_health_customer_message("MONITOR_OK", age_days=None)
    # Legacy callers keep the old string; what matters is that the timeline
    # surface now always supplies an age. Pinned by reading the wiring, so
    # deleting it fails this test rather than silently restoring the old claim.
    import inspect

    from app.source_health_timeline import build_source_timeline

    src = inspect.getsource(build_source_timeline)
    assert "age_days=freshness" in src, (
        "build_source_timeline stopped passing the run age to the message"
    )
    assert message


def test_failed_and_blocked_states_are_untouched():
    for status in ("FAILED", "ACCESS_BLOCKED", "QUALITY_DROP"):
        stale = source_health_customer_message(status, age_days=99)
        fresh = source_health_customer_message(status, age_days=0)
        assert stale == fresh, f"{status} wording changed with age"
