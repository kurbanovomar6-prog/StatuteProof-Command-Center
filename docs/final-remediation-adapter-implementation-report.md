# Final Remediation Adapter Implementation Report

Date: 2026-06-17

## Implementation Summary

No new adapter family was required. The final remediation sprint used existing, already-tested extraction paths:

- `pdf_listing` for the two official DFSA replacement endpoints.
- Generic/Playwright no-save checks for the three legacy remediation URLs.
- FIU document-listing checks for potential FIU replacement candidates.

## Registry / Config Changes

- Disabled and marked `AE-dubai-financial-services-authority-dfsa` as `status:replaced` with replacement `AE-dfsa-annual-reports`.
- Disabled and marked `AE-dfsa-notices` as `status:replaced` with replacement `AE-dfsa-annual-aml-reports`.
- Added `AE-dfsa-annual-reports` as active after proof, repeat baseline, mass-monitor `MONITOR_OK`, and gates.
- Added `AE-dfsa-annual-aml-reports` as active after proof, repeat baseline, mass-monitor `MONITOR_OK`, and gates.
- Kept `AE-uae-financial-intelligence-unit-uaefiu` enabled but `status:remediation` with exact blocker notes.

## Blockers Solved

- Stale DFSA main source page no longer sits as an enabled remediation endpoint.
- Stale DFSA notices URL no longer sits as an enabled remediation endpoint.
- DFSA count and customer-facing readiness now improves through official report endpoints rather than through homepage/not-found pages.

## Remaining Blocker

UAE FIU homepage is still not monitoring-ready. Source Lab classified it `NAV_SHELL_ONLY` after Playwright fallback, and the tested replacement candidates were either shallow, access-blocked, stale, or duplicate-prone.

## Tests / Validators

- Added `tools/validate_final_remediation_activation.py`.
- Updated source-count expectations to 79 enabled / 78 readiness-supported / 1 remediation.
- Updated plan/pricing expected source limit to 78 readiness-supported sources.

No weakening of source-quality validators was performed.
