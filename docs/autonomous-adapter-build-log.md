# Autonomous Adapter Build Log

Date: 2026-06-15

## Adapter Added: `eocn_news_listing`

Files changed:

- `product/regradar/app/adapters/adapter_platform.py`
- `product/regradar/app/source_intake.py`
- `product/regradar/tests/test_adapter_platform.py`
- `tools/validate_source_activation_pipeline.py`
- `tools/validate_uae_50_working_sources.py`

## Why It Was Needed

`AE-eocn-news-en` initially passed with the generic `listing` adapter, but the normalized preview started with navigation/service links such as About Us, Armoring Request, and Careers. That was not safe to save as evidence.

The official EOCN page contains real news cards under:

- container: `#NewsContainer`
- item: `.item.default-section`
- title/link: `.item-title-container[href]`
- date: `.item-date`
- brief: `.item-brief`

## Implementation

The adapter extracts only `/news/` links inside `#NewsContainer`, prefers the full EOCN `title` attribute over truncated `h3` text, captures date and brief context, and ignores header/nav/footer/form/site-map chrome.

## Tests Added

- `test_eocn_news_listing_adapter_extracts_news_and_ignores_navigation`

This fixture proves the adapter extracts real EOCN news items and excludes navigation/service links.

## Sources Unblocked

- `AE-eocn-news-en`: activated after no-save q=65, two stable evidence runs, mass-monitor dry-run `MONITOR_OK`, and all gates pass.

## Remaining Blocker

The same pattern is likely needed for ADGM RA notices/AML guides/listing rules and SCA JS-filtered listings: inspect the true content container, then build a source-specific adapter instead of relying on generic listing.

## Adapter Improved: `sca_listing`

Files changed:

- `product/regradar/app/adapters/adapter_platform.py`
- `product/regradar/tests/test_adapter_platform.py`

## Why It Was Needed

The SCA regulations listing produced meaningful item-level regulatory content, but some rows contained invalid pseudo-links such as `javascipt:;`. Those pseudo-links should not become evidence text or row hashes.

## Implementation

`ScaListingAdapter` now keeps the regulatory row title/date but drops invalid `javascript:`, misspelled `javascipt:`, and fragment-only detail URLs before formatting normalized output and recomputing row hashes.

## Tests Added

- `test_sca_listing_adapter_removes_invalid_javascript_detail_urls`

## Sources Unblocked

- `AE-sca-regulations-listing`: activated after q=65 no-save, 59 extracted regulatory rows, two stable evidence runs, mass-monitor dry-run `MONITOR_OK`, and all gates pass.

## Continuation Cycle: SCA FATCA/CRS + ADGM Listing Authority

Date: 2026-06-16

### Adapter Improvements

- `sca_listing`: expanded regulatory signal detection for FATCA/CRS, automatic exchange of information, cabinet resolutions, reporting financial institutions, and residence/citizenship-by-investment circulars. This moved `AE-sca-fatca-crs` from q=59 near-pass to q=65 strong no-save by including official document links already present on the SCA page.
- `adgm_fsra_listing`: added support for ADGM web-component document links exposed as `adgm-link-button[href]`, and tightened ADGM/FSRA signal tokens so global chrome such as ADGM Academy/AccessADGM is not treated as listing content. This moved `AE-adgm-listing-rules` from NAV_SHELL_ONLY to q=62 strong no-save.
- `source_intake`: added `adgm_fsra_listing` to structured adapter content recognition so a valid ADGM/FSRA listing result can become evidence-eligible without weakening quality gates.

### Tests Added

- SCA FATCA/CRS fixture extracts official FATCA/CRS document links and excludes shell chrome.
- ADGM Listing Authority fixture extracts `adgm-link-button` PDF links and excludes footer/global service links.

### Sources Unblocked

- `AE-sca-fatca-crs` — activated after q=65 no-save, two stable evidence runs, mass-monitor `MONITOR_OK`, and agent gates.
- `AE-adgm-listing-rules` — activated after q=62 no-save, two stable evidence runs, mass-monitor `MONITOR_OK`, and agent gates.

### Remaining Blocker

The next high-potential batch is now UAE FIU AML/CFT laws, ADGM RA notices/AML guides replacement URLs, SCA corporate governance, VARA rulebooks, and CBUAE publications. These still need DOM/XHR or exact official endpoint remediation.
