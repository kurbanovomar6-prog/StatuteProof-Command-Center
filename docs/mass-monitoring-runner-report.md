# Mass Monitoring Runner Report

Date: 2026-06-15

## What Was Built

Implemented `product/regradar/app/mass_monitoring_runner.py` and `run.py mass-monitor`.

Default behavior:

- dry-run/no-alerts by default;
- activation-ready/enabled only;
- skips candidate, no-save, proof-only, baseline-pending, remediation, blocked, and rejected states;
- does not update `sources.json`;
- does not send Telegram/email/customer messages;
- can throttle and limit by regulator/source/domain;
- maps source-health statuses including `MONITOR_OK`, `QUALITY_DROP`, `SELECTOR_BROKEN`, `NAV_SHELL_ONLY`, `SOURCE_STRUCTURE_CHANGED`, and `REMEDIATION_REQUIRED`.

## Safety Fixes

- Dry-run no longer mutates queue monitor state.
- Adapter-level selectors are no longer promoted into fetch-level selectors by default.

## Dry-Run Result

Final dry-run:

- processed: 2 activation-ready queue entries;
- skipped: 10 unsafe/held entries;
- source health: 2 `MONITOR_OK`;
- alerts sent: 0;
- evidence written: 0;
- `sources.json` changed: no.

