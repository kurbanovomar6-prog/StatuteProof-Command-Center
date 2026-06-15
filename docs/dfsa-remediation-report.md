# DFSA Remediation Report

Date: 2026-06-15

## Verdict

DFSA improved at DOM investigation level, but no DFSA source became evidence-ready or activation-ready.

## Improvements Made

- Auto DOM Investigator now detects summary-style content blocks such as `.summary`, `.page-summary`, and `[data-summary]`.
- DFSA summary pages with regulatory links receive `dfsa_notice_listing` recommendations instead of generic unknown DOM when fixture conditions are met.
- Added fixture test for DFSA AML/MLRO summary content.

## Live Validation

### `AE-dfsa-aml-mlro-notices`

- URL: `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance`
- Discovery selected `.summary` selector.
- Runner mode: `no-save-only`
- Result: remediation
- Quality score: 0
- No-save status: failed
- Failure code: `NAV_SHELL_ONLY`
- Saved evidence: no
- Activation-ready: no

### `AE-dfsa-rulebook-thomsonreuters`

- URL: `https://dfsaen.thomsonreuters.com/`
- Runner mode: `no-save-only`
- Result: remediation
- Quality score: 0
- No-save status: failed
- Failure code: `NAV_SHELL_ONLY`
- Saved evidence: no
- Activation-ready: no

## Remaining DFSA Blockers

- The mass queue should use more precise endpoints:
  - `https://dfsaen.thomsonreuters.com/rulebook/rulebook-modules`
  - `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters`
- The DFSA homepage/summary selectors are still not sufficient for monitoring-quality extraction.
- Rulebook module adapter needs live no-save validation against module URL, not generic rulebook homepage.
