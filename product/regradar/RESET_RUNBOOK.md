# RESET_RUNBOOK — coordinated baseline reset for normalization v2

**Status: PREPARED, NOT EXECUTED. Operator schedules this inside an Update
Day. Never run it ad-hoc, never against prod outside the window, never
locally against the real `data/` trail.**

## Why a reset is required

signal-max F1 changed `normalize_for_change_hash`
(`app/text_normalization.py`, `NORMALIZATION_VERSION = 2`): page chrome
(nav-label runs, rating counters, theme widgets, carousel positions, site
taglines, AR site-update timestamps) is now stripped before hashing, and
error pages (404/502/challenge) are rejected before they can become
baselines.

Because stored baselines were hashed with v1, the first v2 cycle re-hashes
differently for most sources. Measured on the real trail on 2026-07-06
(`docs/signal/reset_sizing.txt`):

```
sources with latest snapshot: 316
baseline FLIPS under v2 normalization: 300 (of which currently-enabled: 86)
unchanged hash: 6; error-page snapshots: 10; missing files: 0
```

So: expect **~86 enabled sources to fire CHANGED exactly once** during the
reset window. These CHANGED events are *planned re-baselining*, not
regulatory changes, and must never reach a customer.

## Preconditions

- [ ] Update Day window agreed; operator present.
- [ ] The signal-max release (containing NORMALIZATION_VERSION = 2) is
      deployed and `deploy-check` passes.
- [ ] Backup taken (per DEPLOY.md backup step) — the trail JSONL and
      snapshots directory are restorable.
- [ ] Confirm run-record stamping: latest release writes
      `normalization_version` into run records (`app/pipeline.py`,
      `app/source_runs.py`).

## Procedure (all commands on the prod host as the service user)

1. **Stop scheduled monitoring.**
   `systemctl stop <scheduler unit>` (unit name per DEPLOY.md systemd
   section). Verify: `systemctl is-active <scheduler unit>` → `inactive`.

2. **Suppress every outbound alert channel for the reset window:**
   - Telegram: run the reset cycle with `ALERT_DRY_RUN=true`
     (proven switch: `app/telegram.py:176` — message rendered to log,
     not sent).
   - Email: confirm `STATUTEPROOF_EMAIL_SEND_ENABLED` is NOT `true`
     for the reset shell (gate: `app/email_delivery.py`).
   Record both values in the Update Day log before proceeding.

3. **Run one full monitoring cycle in the suppressed shell:**
   ```
   ALERT_DRY_RUN=true python3 run.py all
   ```
   Expected: ~86 enabled sources classify CHANGED once (planned
   re-baseline); error-page sources classify FAILED instead of storing
   junk baselines.

4. **Verify, with output pasted into the Update Day log:**
   - CHANGED count for the cycle ≈ the measured expectation (86 ± the
     day's genuine changes; a large deviation = stop and investigate).
   - `grep -c 'ALERT_DRY_RUN' <journal>` — every would-be alert was
     rendered-not-sent; zero Telegram deliveries, zero SMTP connections.
   - New run records carry `"normalization_version": "2"`.

5. **Run a SECOND cycle, still suppressed.**
   Expected: UNCHANGED (heartbeats) everywhere except genuinely changed
   sources. A source that fires CHANGED twice in a row has residual
   instability — record it, keep it suppressed, open a defect.

6. **Re-enable delivery.** Unset `ALERT_DRY_RUN`, restore the scheduler
   (`systemctl start <scheduler unit>`), verify `is-active` → `active`.

7. **Post-reset watch (first 24 h):** startup consistency checker output
   changes after re-baselining — record the new divergence count in the
   Update Day log (the pre-reset expectation was ~16 legacy divergences;
   the number after reset is the new reference).

## Rollback

Rolling back the release to v1 normalization re-flips every baseline
again (the stored baselines will then be v2). If rollback is required:
repeat this runbook under the rolled-back version — same suppression
rules. Never roll back without re-running the suppressed re-baseline
cycle.

## Explicitly forbidden

- Running this against the production trail outside an Update Day window.
- Running any part of it with alert channels live.
- "Fixing" the alert format during the window (old format at pin c1ddb8a
  stays until Update Day #1 per UPDATE.md).
