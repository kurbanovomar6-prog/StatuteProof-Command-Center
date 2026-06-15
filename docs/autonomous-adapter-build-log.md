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
