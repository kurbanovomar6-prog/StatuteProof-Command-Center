# Mass Monitoring Current Blocker Inventory

Date: 2026-06-15

## Current Activation-Ready Sources

From `product/regradar/config/uae_source_work_queue.json`, the only activation-ready candidates remain:

- `AE-adgm-fsra-financial-crime-prevention`
- `AE-adgm-fsra-rulebooks`

From `product/regradar/config/mass_source_activation_queue.json`, no source is activation-ready. The strongest mass-queue source is:

- `AE-adgm-fsra-financial-crime-prevention`: `no_save_passed`, quality `88`, but no mass-queue proof path or repeat baseline recorded.

## Current Enabled Sources

`product/regradar/sources.json` still has:

- 150 total configured sources.
- 13 enabled UAE sources.
- Current public truth: `13 enabled / 9 readiness-supported / 4 remediation`.

## SCA Blockers

- `AE-sca-latest-regulations`
  - Current status: remediation.
  - Last no-save quality: `45`.
  - Blocker: item-level listing extraction is not stable enough.
  - Failure code: `LISTING_ADAPTER_REQUIRED`.
- `AE-sca-aml-cft`
  - Current status: remediation.
  - Last no-save quality: `55`.
  - Blocker: extracted output is too shallow/nav-shell-like for evidence save.
  - Failure code: `NAV_SHELL_ONLY`.
- Stronger candidate from discovery:
  - `https://www.sca.gov.ae/en/regulations/circulars-rules-and-procedures`
  - Detected as listing with 10 likely items.
  - Next action: add inactive queue candidate and test with `sca_listing` item-level adapter.

## DFSA Blockers

- `AE-dfsa-aml-mlro-notices`
  - Current status: remediation.
  - Last no-save quality: `0`.
  - Blocker: current queued URL is too generic and extracted as nav shell.
  - Better endpoint found: `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters`.
- `AE-dfsa-rulebook-thomsonreuters`
  - Current status: remediation.
  - Last no-save quality: `0`.
  - Blocker: generic rulebook modules page did not pass no-save in the queue.
  - Better item endpoint found: `https://dfsaen.thomsonreuters.com/rulebook/anti-money-laundering-counter-terrorist-financing-and-sanctions-module-aml-ver3004-26`.

## CBUAE Blockers

- `AE-cbuae-regulations`
  - Current status: remediation.
  - Last no-save quality: `0`.
  - Blocker: direct page returns HTTP 403 / access-block-like shell.
  - Safe action: keep blocked/remediation and use robots/sitemap/official alternate endpoints only. Do not bypass WAF.
- CBUAE notices and publications also returned 403 in scoped endpoint research.

## ADGM / FSRA Near-Ready Sources

- `AE-adgm-fsra-financial-crime-prevention`
  - No-save pass and quality `88`.
  - Needs proof path and repeat baseline in the mass queue before activation.
- `AE-adgm-fsra-rulebooks`
  - Activation-ready in UAE work queue from prior sprint.
  - Needs careful source truth reconciliation before `sources.json` changes.

## VARA Blockers

- `https://www.vara.ae/en/regulations/` returned 404.
- Existing VARA/default sources may still work, but new framework/rulebook endpoint must be rediscovered before no-save.

## UAE FIU / EOCN Blockers

- UAE FIU publications returned 403 in scoped endpoint research.
- EOCN `https://www.uaeiec.gov.ae/en-us/un-page` is accessible and detected as table/document-listing-like content.
- EOCN has promising official candidates:
  - `https://www.uaeiec.gov.ae/en-us/laws-regulations-listing`
  - `https://www.uaeiec.gov.ae/en-us/un-page?p=1`
  - `https://www.uaeiec.gov.ae/en-us/un-page?p=2`
  - `https://www.uaeiec.gov.ae/en-us/un-page?p=3`

## Closest Route To 5 Working Sources

1. Save/repeat-baseline ADGM financial crime if current no-save pass still holds.
2. Add/test SCA circulars/rules with `sca_listing`.
3. Test DFSA AML notices precise endpoint with `dfsa_notice_listing`.
4. Test DFSA AML rulebook module precise endpoint with `dfsa_rulebook`.
5. Test EOCN UN/sanctions page with `table` or a future EOCN table/listing adapter.

## Closest Route To 10 Working Sources

Add the above 5, then test:

- SCA market rules.
- SCA latest regulations after item-level adapter adjustment.
- DFSA enforcement regulatory actions.
- EOCN laws/regulations listing.
- ADGM rules/regulations baseline reconciliation.

## Closest Route To 20 And 50 Working Sources

20 requires source-specific remediation across SCA, DFSA/Thomson Reuters modules, ADGM, EOCN, and VARA rediscovery. 50 requires CBUAE/FIU access-safe alternate endpoints plus broader proof/repeat-baseline automation. It is not honest to claim 20 or 50 until those sources pass proof, baselines, and agent gates.
