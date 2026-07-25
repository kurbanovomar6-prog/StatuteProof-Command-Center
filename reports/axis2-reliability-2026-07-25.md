# Axis 2 — RELIABILITY: 45 → measured

Branch `tenten`. Nothing deployed. Numbers from
`product/regradar/tools/measure_reliability_axis.py`, committed so before/after is
the same command. It is **behavioural**: it drives the real `monitor_all_sources`
against a source that sleeps for 30s and reports whether the next source was ever
reached. Grepping for the word "timeout" tells you someone wrote a feature; only
running a hung source tells you whether it works.

## Before → after

| | Before | After |
|---|---|---|
| Sweep wedges on a hung source | **True** | **False** |
| Second source reached | False | **True** |
| Elapsed against a 30s hang (2s cap) | — (no mechanism to exercise) | **9.1s** (2 attempts + the existing 5s retry delay) |
| Hung source recorded as | — | `status=error, access_status=timeout` |
| Breaker sees the abandoned source | — | **True** |
| `per_source_timeout` / `run_source_with_timeout` / `_PROGRESS_FILE` | absent | present |
| `ops_alert.heartbeat_state` / `describe_progress` | absent | present |
| Watchdog script's callables all exist | **False** | **True** |

## What was wrong

`monitor_all_sources` iterates sources and calls `run_pipeline_for_source` with a
2-attempt retry and **no wall-clock cap**. One source that never returns — a
Playwright navigation that hangs rather than erroring — stopped the entire sweep.
systemd saw a process that was still alive, so `Restart=on-failure` never fired.
Monitoring was silently dead for four days in exactly this way.

Separately, `deploy/scheduler-watchdog.sh` calls `ops_alert.heartbeat_state` and
`ops_alert.describe_progress`. Neither existed, so the script hit an ImportError,
printed nothing useful and exited 0 — the one control that could have recovered
the outage was a permanent silent no-op.

## The cap

`per_source_timeout()` wraps `monitor.run_pipeline_for_source` for the duration of
a block, rather than editing monitor.py's loop. That keeps the cap opt-in at the
call site — the live watch loop gets it; tests, one-off CLI runs and the source lab
keep their current behaviour — and the original is restored even if the body
raises (tested, because a leaked wrapper would cap every later caller).

### The defect my own tests missed

The first version of this returned a synthetic error record on abandonment —
`status: "error"`, `access_status: "timeout"`, `timed_out: True`. Five of my
tests passed on it. It was wrong, and the measurement I had written did not ask
the question that would have caught it.

monitor.py has exactly one path that turns a failed source into *durable* state,
and it is the **raising** path: it writes a FAILED trail record via
`_persist_failure_record`, counts the source as failed, and evaluates the circuit
breaker. Returning a dict skips all three. The sweep looked like it had handled
the source, while the trail stayed silent and the breaker never learned that this
source hangs every single cycle — the exact blindness that let the four-day
outage run. Silence is the worst outcome: **a source that stops being checked
must look worse than one that fails**, never like one that was fine.

So abandonment now raises `TimeoutError` and monitor.py's existing machinery does
the rest. The message begins with `timeout:` because
`monitor._classify_access_status` reads `str(exc)`, not the exception type, and
that string is what lands in the trail as `access_status` — a test pins that
coupling, because if the wording drifts the trail silently starts recording these
as generic errors.

Raising also puts abandonment under the retry policy every other failure already
gets. A hang can be one bad Playwright navigation, and the second attempt is the
same second chance a 403 gets.

I found this because the other session's tests asserted
`_consecutive_failures(url) >= 1` and mine did not. Both my measurement tool and
my test file now ask it.

### The cap's size is derived, not guessed

A cap below the fetch timeouts would sever healthy-but-slow sources and fill the
evidence trail with failures that look like the regulator's fault — worse than the
wedge, because it misattributes blame. It is computed from
`HTTP_TIMEOUT_S + PAGE_TIMEOUT_MS` × 1.5 margin, floored at 60s: **67s** today.
That is a **per-attempt** budget — the wrapper sits on `run_pipeline_for_source`,
which monitor.py calls once per retry — so a source that hangs on both attempts
costs at most 2 × 67s + the 5s retry delay before the sweep moves on. An env
override *below* the derived floor is clamped with a warning, because the likeliest
reason someone sets a small number is impatience during an incident.

### The honest limit

Python cannot kill a thread blocked in a C call. The cap bounds how long the
**sweep waits**, not how long the abandoned work runs; that thread dies with the
process. This is why `_recover_after_source_timeout` tears down the shared browser
— left open, the next source inherits a poisoned handle and hangs too, turning a
one-source problem back into a whole-sweep one.

## The progress marker

A heartbeat alone cannot tell "working slowly" from "stopped": a sweep over 140
sources can legitimately outlive the stale threshold. `record_progress` notes which
source the sweep is on, written **before** the source runs — a marker updated only
on completion would freeze on the *previous* source, making a hang look identical
to a stop, which is precisely the distinction it exists to draw.

`heartbeat_state()` returns `fresh` / `missing` / `stale` / `working` with **no
side effects**. `check_heartbeat()` remains the alerting path; mixing the two is
how a status check starts paging someone at 3am. `working` is the case that
matters: a stale heartbeat with a marker that moved a minute ago is a long cycle,
and restarting it there would abort real work.

The marker counts **sources, not attempts**. A retry calls the wrapper again, and
a counter that advanced per attempt would report a 140-source sweep as being on
source 200 — a watchdog reading that cannot tell real progress from one source
failing twice.

19 tests, including that a real exception still raises through the cap rather than
being laundered into a fake timeout.

## Divergence from the other session's tests

`tests/test_scheduler_wedge_recovery.py` (untracked, not mine) tests the same
feature against a different contract, and after this change 11 of its tests pass
and 20 fail. Worth knowing before the two are merged:

- **Names**: it expects `scheduler.write_progress` and `describe_progress(arg)`;
  mine are `record_progress` and a no-arg `describe_progress`. I did not rename
  to match — matching half of an API I have to guess at produces something that
  looks compatible and is not.
- **Real design difference**: it asserts the cap exceeds *two* attempts' worth of
  fetch timeouts (`67 > 2 * 45.0` fails), i.e. it treats the cap as one whole-source
  budget spanning the retry. Mine is per-attempt with the same total. Its version
  would have to wrap `_run_one_source`, which is above `_persist_failure_record`
  — so it needs its own answer to the durable-record problem described above.
- The rest of its failures are its own deploy deliverables (`DEPLOY.md`, the
  systemd units, `deploy-check.sh`), which are not in my commit.

Its `test_abandoned_source_leaves_a_durable_failed_record` now passes.

## Not done — and not mine to finish

The DoD also asks for a watchdog that **restarts**, with its systemd units in git
and named in DEPLOY.md. `deploy/scheduler-watchdog.sh` and its two unit files are
another session's **untracked** work in this tree; the rule is not to touch them.
What I could do without touching them, I did: the two functions the script calls
now exist, so it can do its job instead of exiting 0.

Axis 2 is therefore **not closed**. The app-side wedge protection is real and
measured; the deploy-side recovery belongs to that session's files.
