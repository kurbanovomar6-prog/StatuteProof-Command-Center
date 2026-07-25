# Axis 3 — HEALTH HONESTY: 45 → measured

Branch `tenten`. Nothing deployed. Numbers from
`product/regradar/tools/measure_health_axis.py`, committed so before/after is the
same command.

## Before → after

| | Before | After |
|---|---|---|
| Alert-eligible sources presented as healthy **without a recent check** | **40 of 40** | **0** |
| Check age visible to the customer | not shown | shown per row and in the response summary |
| Registry `last_monitor_status` | MONITOR_OK on all 40 | unchanged — and no longer trusted |

## What was wrong

`app/mass_monitoring_runner.py` writes `last_monitor_status` and
`last_checked_at` into the **activation queue** and explicitly sets
`sources_json_changed = False`. So the health fields in `sources.json` are not
produced by monitoring at all — they are hand-written annotations. Measured
2026-07-25: all 40 alert-eligible rows assert `MONITOR_OK`, the median recorded
check age is **36 days**, and the run trail proves a check inside 7 days for
**zero** of them.

Meanwhile `app/source_health_timeline.py` had carried `_is_stale` and
`_days_since` since it was written, and **nothing outside that module ever called
them**. The concept of staleness existed and was never wired to a surface. The
customer-facing table fell through to `'Readiness supported'` for any source with
a successful run, however old — the reassuring phrase someone reads before
deciding they are covered.

## The fix, and a deviation from the DoD worth naming

The DoD said "status and `last_checked_at` written by a real run". I did **not**
do that, and the reason is not convenience: writing health back into
`sources.json` on every sweep makes the registry churn on a file that also holds
configuration, and it leaves the same failure mode — a field that is only as
fresh as the last time something remembered to write it.

Freshness is instead **derived from the run trail at read time**, so it cannot go
stale by construction and it is correct in production without a migration:

- `check_freshness()` in `app/source_health_timeline.py` returns an age and one of
  `FRESH` / `STALE` / `NEVER_RUN` / `UNKNOWN`. An unparseable timestamp is
  deliberately **not** `FRESH` — an unreadable date is not evidence of a check.
- `/api/sources/status` now returns `freshness`, `last_run_age_days`,
  `stale_after_days`, a `freshness_summary`, and — the load-bearing part —
  **overrides `status`** when freshness cannot back it. The configured value is
  kept as `configured_status`, replaced in the headline rather than lost.
  `"active"` is a configuration state, not a health state.
- `SourcesPage.jsx` gains a `Check overdue` status and prints "checked N days
  ago". "Overdue by 2 days" and "overdue by 3 months" are different facts for
  someone deciding whether to rely on a source, so the age is stated, not implied.

19 tests pin it: 10 on the API and the verdict function, 9 on the labels the
customer actually reads.

## Honest limits

- The registry's `MONITOR_OK` fields are still stale. They are no longer read by
  the customer surface, but anything else that reads them is still reading a
  hand-written value. Full DoD compliance would mean either a real writer or
  deleting the fields; both are larger changes than this one.
- The "0 of 40" figure is measured against **my local run trail**. Production
  reads its own trail, and the fix is correct there by construction — but I cannot
  see prod from here, so this is not a claim about prod's current freshness. What
  it does guarantee is that whatever prod's state is, the surface will now say so.
- 7 days (`STALE_AFTER_DAYS`) was the threshold already in the codebase. It is not
  a promise to the customer, and no customer-facing copy states a check cadence.
