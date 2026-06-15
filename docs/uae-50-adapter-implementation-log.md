# UAE 50 Adapter Implementation Log

Date: 2026-06-15

## Changes Built In This Cycle

1. `custom_element` extraction now preserves structured text instead of flattening custom-element DOM content.
2. `static_html` and `custom_element` adapters support `focus_keywords` to isolate meaningful regulatory sections from page-wide chrome.
3. Source Intake treats focused structured adapter output of at least 500 chars as structured enough to avoid false nav-shell classification.
4. Mass Monitor runner now selectively promotes adapter selectors into fetch selectors only for `static_html` and `playwright_selector` paths. It keeps `custom_element` selectors inside adapter config so ADGM custom-element pages still receive the full DOM.

## Source Groups Affected

| Source group | Impact |
| --- | --- |
| ADGM/FSRA | Enabled focused `adgm-page` extraction for financial crime and consultations, plus structured custom-element extraction for rules/regulations. |
| DFSA/DIFC | Fixed mass-monitor/source-lab selector parity for the DFSA AML rulebook module. |
| SCA | Existing SCA circulars activation-ready path preserved. |

## Tests Added

- Custom-element adapter preserves ADGM-like structure.
- Focused custom-element output is not falsely marked nav-shell.
- Custom-element focus keywords drop global chrome.
- Mass monitor promotes selectors for static extraction parity.
- Mass monitor keeps custom-element selectors inside adapter config.

## Known Limits

- SCA latest regulations and AML/CFT still need item-level listing remediation.
- DIFC Laws still falls below strong no-save threshold or fails table adapter path.
- VARA framework URL is stale/not-found shell.
- UAE FIU publications path remains likely WAF/403.
- EOCN laws/regulations needs selector remediation.
