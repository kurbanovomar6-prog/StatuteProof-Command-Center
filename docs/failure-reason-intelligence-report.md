# Failure-Reason Intelligence Report

Date: 2026-06-15

## Summary

Source Lab now exposes machine-readable failure codes alongside human-readable failure reasons and remediation hints.

## Why This Matters

Previously, many failures collapsed into generic remediation language. The new failure-code layer supports:

- clearer Source Lab UI;
- better work queue routing;
- future source-specific remediation automation;
- stronger validators against fake-ready states.

## Implemented Codes

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

## Live Validation Findings

In the scoped 12-source live validation batch:

- `ACCESS_BLOCKED` appeared for several SCA/DFSA/CBUAE targets.
- `NAV_SHELL_ONLY` remained common for SCA circulars, CBUAE publications, ADGM, VARA, and FIU targets.
- No target passed strict no-save gates.

## Limitation

Failure-code classification is rule-based and conservative. It does not use LLMs to decide content changes or source readiness.
