# Axis 4 — ALERT RELEASE

Branch `tenten`. Nothing deployed. Command:
`python3 product/regradar/tools/measure_alert_release_axis.py` — committed, so
before/after is the same command.

## Before → after

| | Before | After |
|---|---|---|
| `POST` a release over HTTP | **404** — no route | **200** |
| Queue visible over HTTP | 404 (`/api/reviews/queue` is a different gate) | **200** |
| Approval reachable only from the CLI | **True** | **False** |
| A non-founder can release | — | **blocked, identically for real and fake ids** |
| HIGH-risk + safety issues, approved "for weekly" | **200, zero friction** | **409 with the issues listed** |
| Forcing without a written reason | — | **400** |
| Reviewer in the immutable record | CLI `--reviewer`, any string | **the authenticated session identity** |
| One corrupt draft | **kills every review operation** | queue still 200 |
| `>> AN APPROVER CAN RELEASE WITHOUT A SHELL` | **False** | **True** |

## The bug this cycle actually found

I set out to add an endpoint. An adversarial pass over the design found that the
thing I was about to put a one-click button on had a hole in it, and the hole was
in the CLI that runs in production today.

`review_alert` applied its safety-issue block **only to `approve_urgent`**. But
"weekly" is a cadence, not a smaller blast radius. Verified in the code, not
inferred:

- `alert_routing._get_approved_statuses()` admits `APPROVED_FOR_WEEKLY` and
  `APPROVED_FOR_URGENT` alike — both make an alert delivery-eligible.
- `digest_cadence._is_instant()` returns true for `risk_level == "HIGH"` or
  `score >= urgent_threshold`. It never reads `send_decision`.
- `scheduler.run_digest_dispatch_pass()` is called every full watch cycle
  (`app/scheduler.py:512`), so dispatch is automatic.

So approving a HIGH-risk draft with INCOMPLETE proof and LOW confidence "for
weekly" was a zero-friction instant Telegram to every matched customer, with no
force flag and no note — while the option that reads as the cautious one was the
unguarded path. Sent messages cannot be recalled; a later reject does not undo a
delivery already logged.

**Fixed in `review_alert`, not in the handler.** Putting the gate in the HTTP
layer would have left the SSH path — the one used in production right now —
exactly as exposed. `APPROVING_ACTIONS` now covers both approving actions, and a
test pins that the CLI gets the same refusal. Non-approving actions (reject,
needs_adapter, needs_legal, manual_review) resolve to HOLD or DO_NOT_SEND and are
deliberately not gated.

A second finding, also verified: `_load_json` caught only `FileNotFoundError` and
`JSONDecodeError`, so one draft truncated mid-multi-byte-character — precisely
what the known scheduler wedge produces — raised out of `list_alert_drafts` and
made **every** alert unreviewable until someone SSHed in to find the bad file.
That is the dependency this axis exists to remove, so the except is widened and a
test plants a non-UTF-8 draft and asserts the others stay releasable.

## Design decisions worth stating

- **Founder-scoped, not owner-scoped.** This is the editorial gate, not a tenant
  feature, so it reuses the existing `_admin_guard` — which fails closed, audits
  both outcomes, and runs before the body is read and before any draft lookup, so
  a refused caller cannot use it to discover which alert ids exist. A test asserts
  the refusal for a real and a fake id is byte-identical.
- **The reviewer comes from the session.** The CLI takes `--reviewer` because a
  human types their own name at their own terminal. Accepting it over HTTP would
  let anyone reaching the endpoint write someone else's name into a permanent
  compliance record, so a body containing `reviewer` is refused outright rather
  than silently ignored — silence would let a caller believe the attribution
  worked. `base_dir` and `review_file` are refused for the same reason: they
  choose which files get written.
- **`force` must be a JSON boolean.** Python truthiness reads the string
  `"false"` as `True`, which would turn a typo into a safety override.
- **The response says "recorded", never "sent".** Delivery is gated again
  downstream, so a 200 is a decision, not proof anything went out.
- **The queue states the consequence per row** (`instant Telegram…` vs
  `bundled into… digests`), computed the way `digest_cadence` computes it, so the
  operator sees the blast radius before clicking rather than after.

## A defect I introduced in axis 5 and found here

`authRequest` in `web/src/api.js` never attached `status` to the error it throws
— five call sites hand-rolled `err.status = response.status` to work around it.
`TeamPanel`'s `err.status === 403` branch, shipped last cycle, was therefore
**dead in the browser**: a non-owner would have seen a generic failure instead of
"only the workspace owner can add or remove people". My tests passed because they
mocked the api module and hand-built errors that *did* carry `.status` — kinder
than reality.

Fixed at the source (`authRequest` now attaches `status` and `payload`), with
`web/src/test/apiErrorShape.test.js` driving the real `api.js` against a stubbed
`fetch` so a generous mock cannot satisfy it. Vacuity-checked: removing the two
lines fails 2 of its 4 tests.

## Known limits, not papered over

- **In-process lock only.** `review_alert` reads, rewrites the draft, then appends
  to the jsonl with no locking of its own. A module-level lock serializes two
  browser clicks, but the CLI and the scheduler's qa_gate run in other processes
  and still race. Pre-existing; not introduced here.
- **Non-atomic write.** The draft rewrite precedes the jsonl append, so a crash
  between them leaves them disagreeing. The 500 body says the decision may or may
  not have been recorded and tells the operator to reload rather than retry.
- **No terminal-state guard.** `review_alert` lets an already-decided alert be
  decided again; the queue surfaces the previous decision instead.
- **Not visually verified.** The admin panel is behind the auth wall and I do not
  enter credentials. The panel rests on 7 jsdom tests and a production build.

## Tests

18 backend (`tests/test_alert_release_endpoint.py`), 11 frontend
(`AlertReleasePanel.test.jsx`, `apiErrorShape.test.js`). The safety-gate tests
were vacuity-checked by reverting `APPROVING_ACTIONS` to urgent-only — both fail
without the fix.

Full backend suite: 91 failures, byte-identical to the previous run, all in
another session's untracked test files. Frontend: 486 passed across 40 files.
