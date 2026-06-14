# Quality Gate Before Save Report

Date: 2026-06-15

## Summary

Improved Source Lab no-save gate fields so the product can explain why a source may or may not be saved for validation.

## Added Structured Fields

Source intake now includes:

- `official_status`
- `access_status`
- `meaningful_content`
- `shallow_content`
- `duplicate_hash`
- `noise_risk`
- `source_health_risk`
- `failure_code`
- `can_save_evidence`

## Failure Codes

Implemented machine-readable failure codes:

- `URL_STALE`
- `SELECTOR_NOT_FOUND`
- `JS_REQUIRED`
- `PDF_ONLY_SOURCE`
- `LISTING_ADAPTER_REQUIRED`
- `NAV_SHELL_ONLY`
- `ACCESS_BLOCKED`
- `LIKELY_WAF_403`
- `HIGH_NOISE_RISK`
- `DUPLICATE_BOILERPLATE_HASH`
- `SHALLOW_CONTENT`
- `SOURCE_STRUCTURE_CHANGED`
- `MANUAL_CHECK_REQUIRED`

## Save Rule

`can_save_for_validation` is now constrained by the stricter `can_save_evidence` gate:

- status must be `CONFIRMED_ACCESSIBLE`;
- no evidence already written;
- evidence level must be `PREVIEW_ONLY`;
- content must be meaningful;
- quality score must pass threshold;
- high noise/high source-health risk blocks save.

## Tests

Added a regression test that maps nav-shell extraction to `NAV_SHELL_ONLY` and blocks save.

## Limitation

Officialness is still marked `unverified_public_source` unless source registry or future source-owner verification supplies a stronger value.
