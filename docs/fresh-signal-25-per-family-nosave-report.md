# Fresh Signal 25 Per Family No-Save / Activation Report

Date: 2026-06-19

## Batch Result Files

Machine-readable batch result files:

- `docs/fresh-signal-cbuae-batch-results.json`
- `docs/fresh-signal-critical-activation-results.json`
- `docs/fresh-signal-vara-activation-results.json`
- `docs/fresh-signal-adgm-fsra-activation-results.json`
- `docs/fresh-signal-dfsa-activation-results.json`
- `docs/fresh-signal-difc-activation-results.json`
- `docs/fresh-signal-25-per-family-final-activation-set.json`

## Results Summary

- Total batch records reviewed: 68
- Passed proof/baseline/MONITOR_OK and activated or confirmed as `fresh_alert`: 60
- Held or evidence-only: 8

## Held Sources And Reasons

- `AE-cbuae-regulations`: access/private-risk classification; held.
- `AE-vara-enforcement`: nav-shell; held.
- `AE-uaefiu-circulars`: nav-shell; held.
- `AE-sca-regulations-listing`: nav-shell; held.
- `AE-adgm-fsra-guidance-policy`: mass-monitor `QUALITY_DROP`; held.
- `AE-adgm-fsra-waivers`: nav-shell; held.
- `AE-adgm-ra-circulars`: mass-monitor `QUALITY_DROP`; held.
- `AE-dfsa-consultation-paper-165`: technically extractable, but static historical consultation detail; evidence-library only.

## No Customer Alert Delivery

No customer emails, Telegram alerts, or production notifications were sent. All mass-monitor checks were dry-run/no-alerts.
