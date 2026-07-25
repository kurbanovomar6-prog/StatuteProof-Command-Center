# Axis 4 — ALERT RELEASE: baseline only

Branch `tenten`. Nothing deployed, nothing fixed yet. This cycle produced the
measurement and one correction to what the axis actually is.

Command: `python3 product/regradar/tools/measure_alert_release_axis.py`

## Baseline

| | Status |
|---|---|
| `POST /api/alerts/review` \| `/approve` \| `/release` \| `/reviews/decide` | **404** — no route |
| `GET /api/reviews/queue` | 401 (route exists) |
| Modules that can pass an `approve_*` action | `alert_review.py`, `run.py` |
| `>> AN APPROVER CAN RELEASE WITHOUT A SHELL` | **False** |

An alert draft stays unreleased until `app.alert_review.review_alert` records an
`approve_weekly` / `approve_urgent` decision — only then does
`load_approved_alert_candidates` include it. The sole way to record one is
`run.py alert-review approve`, over SSH.

## Two corrections I had to make to my own measurement

**The first version counted phantom callers.** Grepping for `review_alert`
matched it as a substring of `alert_review` and swept in compiled `.pyc` files,
reporting fourteen modules. Matching the call (`\breview_alert\s*\(`) over `.py`
sources gives three.

**Calling `review_alert` is not releasing.** `weekly_brief.py` is a genuine third
caller, but it passes `action="manual_review"` to HOLD an alert the QA gate
rejected. Counting it as a release path would have said the axis was already
half-open. The probe now asks specifically who can name an `approve_*` action.

## What the axis is NOT

The dashboard's Review Queue has working approve/reject buttons, but they call
`reviews.reviewCanonicalEvidence` → `/api/evidence/review`. That is the
**canonical-evidence** gate, a different control with a complete HTTP path and
UI. No dead button here — the two gates were simply conflated in my earlier
notes.

So alert release is not a missing customer feature. It is the **editorial gate**
that decides whether a drafted alert reaches customers at all, and it currently
requires a shell. That makes it a founder-operations gap, not a tenant one — and
it means any endpoint must be operator-scoped (GLOBAL org), never owner-scoped
like the team seating in axis 5.

## Next step, deliberately not taken yet

An operator-gated `POST /api/alerts/review` carrying the same
`approval_safety_issues` checks the CLI runs, plus the `--force` semantics, is
the fix. I stopped at the measurement rather than half-building a privileged
endpoint: the release gate is what stands between a draft and every customer's
inbox, and it is the wrong control to rush at the end of a long session.
