# UAE 50 Sources JSON Change Log

Date: 2026-06-15

## Registry Change

`sources.json` changed: yes.

Before this cycle:

- 16 enabled UAE sources.
- 12 readiness-supported.
- 4 remediation.

After this cycle:

- 19 enabled UAE sources.
- 15 readiness-supported.
- 4 remediation.

## Sources Added

1. `AE-adgm-fsra-financial-crime-prevention`
2. `AE-adgm-fsra-rulebooks`
3. `AE-adgm-fsra-consultations`

## Existing Source Updated

`AE-dfsa-aml-rulebook-module` remains active, but its proof path and normalized hash were updated after selector-path parity was fixed and two consecutive saved baseline runs produced the same new hash.

## Sources Not Added

No no-save-only, one-run-only, high-noise, high-health-risk, nav-shell, blocked, or generic sources were added.

## Why Safe

The three added ADGM/FSRA sources have strong no-save results, saved proof paths, repeat baseline completion, `MONITOR_OK` dry-run, and all required agent gates passing. The final mass-monitor dry-run processed all six activation-ready queue entries with `MONITOR_OK` and no drift.
