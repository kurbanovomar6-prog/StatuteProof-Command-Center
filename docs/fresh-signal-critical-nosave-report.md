# Fresh Signal Critical No-Save Report

## Scope

Controlled no-save diagnostics were run for the most commercially sensitive weak families:

- SCA
- EOCN / sanctions / TFS
- UAE FIU

No evidence was written. No source was promoted to `fresh_alert`. The purpose was blocker truth.

Raw machine-readable results:

- `docs/fresh-signal-critical-nosave-results.json`

## Summary

The old “blocked” picture is too blunt. Several sources that previously had no `MONITOR_OK` are publicly reachable through Playwright and produce enough text for monitoring diagnostics. They still require proof writes, repeat baseline, and mass-monitor dry-run before they can become fresh-alert sources.

## SCA Results

| Source | No-save result | Method | Extracted chars | Decision |
|---|---|---|---:|---|
| SCA Circulars, Rules and Procedures | Needs adapter | Playwright | 986 | Listing adapter/refined selector required |
| SCA Board Decisions | Can monitor | Playwright | 5,611 | Strong activation candidate |
| SCA Regulations Listing | Can monitor | Playwright | 1,442 | Strong activation candidate |
| SCA FATCA and CRS Guidance | Can monitor | Playwright | 2,568 | Strong activation candidate |
| SCA Corporate Governance Regulations | Can monitor | Playwright | 2,030 | Strong activation candidate |
| SCA AML/CFT | Can monitor | Playwright | 12,931 | Strong activation candidate |

SCA is not proven live monitoring yet, but it is also not proven impossible. The immediate next step is a Playwright-backed SCA activation batch with proof, baseline, and `MONITOR_OK`.

## EOCN Results

| Source | No-save result | Method | Extracted chars | Decision |
|---|---|---|---:|---|
| EOCN AML/CFT Laws and Regulations | Can monitor | Playwright | 1,470 | Strong activation candidate |
| EOCN News and Sanctions Updates | Can monitor | Playwright | 1,181 | Strong activation candidate |

Direct EOCN should remain excluded from customer fresh-alert claims until proof/baseline/MONITOR_OK passes, but the access blocker is no longer absolute.

## UAE FIU Results

| Source | No-save result | Method | Extracted chars | Decision |
|---|---|---|---:|---|
| UAE FIU Trends and Typology Reports | Can monitor | Playwright | 6,764 | Strong activation candidate |
| UAE FIU AML/CFT Laws and Related Decisions | Can monitor | Playwright | 6,181 | Strong activation candidate |
| UAE FIU Publications Hub | Can monitor | Playwright | 6,764 | Strong activation candidate |
| UAE FIU Annual Reports | Can monitor | Playwright | 6,764 | Already confirmed source; preserve |
| UAE FIU Press Releases | Can monitor | Playwright | 4,419 | Already confirmed source; preserve |

The HTTP diagnostic reports `403` for some FIU requests, but Playwright extracts substantial public content. That requires explicit method documentation in source metadata before activation.

## Next Activation Batch

Priority order:

1. Save evidence and baseline SCA AML/CFT, SCA Board Decisions, SCA Regulations Listing, SCA FATCA/CRS, and SCA Corporate Governance.
2. Save evidence and baseline EOCN Laws/Regulations and EOCN News.
3. Save evidence and baseline FIU Typology Reports, FIU AML/CFT Laws, and FIU Publications Hub.
4. Build/refine selector/listing adapter for SCA Circulars, Rules and Procedures.

No customer copy may claim these families are live until `MONITOR_OK` is recorded.
