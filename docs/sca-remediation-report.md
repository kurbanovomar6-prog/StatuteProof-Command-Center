# SCA Remediation Report

Date: 2026-06-15

## Verdict

SCA improved at discovery-filtering level, but no SCA source became evidence-ready or activation-ready.

## Improvements Made

- Tightened SCA same-domain discovery filtering.
- Rejected generic SCA pages such as About/Services from recommended activation paths.
- Preserved clear SCA regulatory candidates such as AML/CFT, regulations, circulars/rules, market rules, and register-style pages.
- Normalized malformed doubled SCA paths like `/en/regulations/en/regulations/...`.
- Added tests for SCA generic-link rejection, regulatory-link preservation, and doubled-path normalization.

## Live Validation

### `AE-sca-latest-regulations`

- URL: `https://www.sca.gov.ae/en/regulations/regulations`
- Runner mode: `no-save-only`
- Result: remediation
- Quality score: 45
- No-save status: failed
- Failure code: `LISTING_ADAPTER_REQUIRED`
- Saved evidence: no
- Activation-ready: no

### `AE-sca-aml-cft`

- URL: `https://www.sca.gov.ae/en/regulations/anti-money-laundering-and-terrorist-financing`
- Runner mode: `no-save-only`
- Result: remediation
- Quality score: 55
- No-save status: failed
- Failure code: `NAV_SHELL_ONLY`
- Saved evidence: no
- Activation-ready: no

### SCA Circulars / Rules Discovery

- URL: `https://www.sca.gov.ae/en/regulations/circulars-rules-and-procedures`
- Discovery-only result: public candidate
- DOM type: listing
- Recommended adapter: listing / `sca_listing`
- Recommended paths: 28
- Generic About/Services links did not appear in top recommended paths after filtering.

## Remaining SCA Blockers

- SCA live listing extraction still needs item-level adapter/selector remediation.
- SCA pages can expose regulatory-looking listings that are still too noisy or shallow for evidence save.
- No SCA source should be activated until proof and repeat baseline pass.
