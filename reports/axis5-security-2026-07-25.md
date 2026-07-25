# Axis 5 — SECURITY: 62 → measured

Branch `tenten`. Nothing deployed. Numbers from
`product/regradar/tools/measure_security_axis.py`, committed so before/after is the
same command. It exercises the real code paths against a throwaway database and
never touches the working store.

## Before → after

| | Before | After |
|---|---|---|
| Account locks after repeated failures | **False** (25 failures, correct password still accepted) | **True** |
| A bootstrap for the first operator exists | **False** | **True** |
| …and it produces a real operator principal | — | **True** (org 0) |
| An ordinary owner can grant themselves GLOBAL scope | False | **False** (unchanged, and must stay so) |
| An owner can seat a teammate in their own org | **True** | True |

## One audit claim refuted

The axis brief said "no way to seat a second user". Measured: an owner **can**
seat a teammate — `assign_org_role` returns `ok`. What is missing is an HTTP/UI
path; the capability is CLI-only (`run.py assign-role`). That distinction matters
because it changes the work from "build authorization" to "expose an existing
capability", and the second is much smaller.

An earlier run of my own probe reported the opposite — that an owner could not
seat anyone. That was an artefact of the probe: it called `ensure_rbac_tables()`
but not `backfill_org_memberships()`, which the real init path runs
(`app/db.py:860, 882, 895`), so its users had no org membership at all. Checked
against the working database — 17 users, 17 memberships — and the probe corrected.

## Per-account lockout

`app/api.py:596` keys its limiter on `client_ip:label`. That caps how fast one
address can try; it does nothing about how many times one **account** can be
ground down by an attacker with a pool of addresses. Conversely a single office
NAT shares one 10/hour budget between everyone behind it.

Added `login_attempts` (keyed on normalized email) plus `is_account_locked` /
`record_failed_login` / `clear_failed_logins`, wired into the sign-in handler.
8 failures inside a 15-minute window lock the account for 15 minutes; a successful
sign-in clears the counter; failures older than the window stop counting, so a slow
trickle of typos is not treated as an attack.

Two properties are as important as the lock itself and are tested:

- **A locked account answers exactly like a wrong password** — the same 401, the
  same message. A distinct "account locked" reply would confirm the address is a
  customer, turning the defence into an enumeration oracle.
- **Attempts against addresses that do not exist are counted identically**, so the
  counter's behaviour cannot be used to probe for real accounts either.

It also **fails open**: if the table is unreadable, `is_account_locked` returns
False and the password check still has to pass. Failing closed here would turn a
storage problem into a full outage for every customer.

## Operator bootstrap

`assign_org_role` requires the actor to hold `member.manage` for the target org,
and `app.rbac.can` confines an owner to their own org — so creating a GLOBAL-scope
principal requires already being one, and nothing ever seeded the first.
`app/db.py:628` inserts the GLOBAL *org* row and never a membership in it.
Verified against the working database: **0 rows** in `org_members` with
`org_id = 0`. That is why `_caller_is_operator` was False for every account that
could exist, and the shared-official-evidence review gate could not be satisfied by
anyone.

`bootstrap_operator()` breaks the cycle using the SYSTEM principal, which is
cross-org by construction. It is **not** reachable over HTTP — it is called from
`run.py bootstrap-operator --user <id>`, which already requires shell access to the
production host. Granting cross-tenant scope is the most powerful action in this
system and it should cost an SSH session. The grant is written to the immutable
access log.

### A no-op I nearly shipped

The first version wrote the membership row and changed nothing:
`resolve_principal` orders by "prefer the org the user OWNS", and the founder also
owns an org-of-one, so the GLOBAL seat lost and `_caller_is_operator` stayed False.
The measurement caught it — `bootstrap_produces_operator: False (org after
bootstrap: 1)`. GLOBAL scope now sorts first, with the reason written at the query.
Reading the code alone would not have found this.

## Still open on this axis

- **No HTTP invite path.** Seating a teammate works, but only via
  `run.py assign-role`. A customer cannot add a colleague without the founder.
- **The lockout window is not surfaced to the user.** By design, for the
  enumeration reason above — a locked-out customer sees "Invalid email or
  password" and has no way to tell they are locked. A support-visible signal would
  be the honest complement, and does not exist.

Axis 5 is therefore **not closed**.
