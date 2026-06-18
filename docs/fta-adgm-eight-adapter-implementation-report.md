# FTA / ADGM Eight Adapter Implementation Report

Date: 2026-06-18

## What Changed

Two narrow parser improvements were made for the eight-row repair:

1. `pdf_document` adapter now preserves PDF line breaks and heading-like structure instead of collapsing an extracted PDF into one flat paragraph.
2. `adgm_fsra_listing` adapter now recognizes regulatory-alert terms (`alert`, `alerts`, `notice`, `notices`, `warning`, `enforcement`) as legitimate ADGM/FSRA listing signals.

## Why This Was Safe

These changes do not weaken gates:

- minimum extracted text still applies;
- nav-shell detection still applies;
- no-save still cannot activate monitoring;
- one saved run still cannot activate monitoring;
- repeat baseline and mass-monitor dry-run are still required;
- `can_save_evidence` still requires quality score, meaningful content, non-high noise risk, and non-high source-health risk.

## Result By Source

| Source | Adapter result | Decision |
|---|---|---|
| ADGM Data Protection Regulations 2021 PDF | PDF line preservation increased quality from 57 / `LIMITED` to 61 / `ACCEPTABLE`; `can_save_evidence=true`. | Proceeded to evidence/baseline. |
| ADGM FSRA Supervision Circulars | Existing `adgm_fsra_listing` produced 10 listing items with quality 65. | Proceeded to evidence/baseline. |
| ADGM FSRA Regulatory Alerts | Regulatory-alert terms were added, but the live page still produced no alert rows and remained `NAV_SHELL_ONLY`. | Held as candidate. |
| FTA five pages | Existing generic listing path returned title/nav-shell-only extraction. | Held as candidates pending FTA-specific item-level adapter. |

## Tests Added

Added `product/regradar/tests/test_fta_adgm_eight_source_truth.py`:

- PDF document adapter preserves lines and reaches the quality gate on a structured PDF fixture.
- ADGM FSRA listing adapter extracts regulatory-alert fixture rows and stable row hashes.

## Future Adapter Work

The next FTA-specific adapter should investigate:

- rendered DOM after client-side hydration;
- public unauthenticated XHR/API endpoints if visible and permitted;
- document card selectors;
- pagination/filter parameters;
- direct document/PDF links;
- stable title/date/link extraction.

Monitoring intelligence only. Not legal advice.
