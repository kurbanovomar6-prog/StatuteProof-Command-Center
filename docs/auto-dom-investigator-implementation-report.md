# Auto DOM Investigator Implementation Report

Date: 2026-06-15

## Summary

Implemented `product/regradar/app/dom_investigator.py`.

The investigator inspects already-fetched/rendered HTML and recommends a safe extraction strategy. It does not fetch pages and does not write evidence.

## Output Fields

The investigator returns:

- `final_url`
- `page_title`
- `detected_page_type`
- `recommended_adapter_family`
- `recommended_adapter_name`
- `wait_selector`
- `content_selector`
- `item_selector`
- `fallback_selectors`
- `selectors_considered`
- `selector_confidence`
- `why_selector_was_chosen`
- `nav_shell_risk`
- `noise_risk`
- `source_health_risk`
- `failure_reason`
- `remediation_hint`
- `can_no_save_test`
- `can_save_evidence`
- `warnings`

## Detection Coverage

Implemented fixture-backed detection for:

- article/main content;
- listing rows;
- tables;
- PDF/document links;
- custom elements;
- nav-shell/shallow content risk.

## CLI

Added:

`python3 run.py investigate-source <URL> --js --json`

This runs a scoped diagnostic check only. It does not save evidence.

## Tests Added

`product/regradar/tests/test_dom_investigator.py`

- article/main content detection;
- listing detection;
- table detection;
- PDF listing detection;
- nav-shell/shallow-content detection.

## Limitations

- Shadow DOM is noted as a future deeper Playwright feature.
- The investigator recommends selectors; it does not prove activation readiness.
- It cannot bypass access controls, WAFs, CAPTCHAs, login pages, or paywalls.
