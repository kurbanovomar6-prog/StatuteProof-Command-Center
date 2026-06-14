# Source Discovery Engine Implementation Report

## Implementation Details

Implemented structured source discovery in `product/regradar/app/source_discovery.py`.

New deterministic helpers:

- `parse_robots_sitemaps`
- `parse_sitemap_xml`
- `discover_feed_links_from_html`
- `parse_feed_xml`
- `extract_document_links_from_html`
- `discover_same_domain_links`
- `classify_network_response`
- `capture_playwright_network_candidates`
- `score_endpoint_candidate`
- `generate_source_candidate`
- `build_discovery_report_from_html`
- `discover_source`

The engine is no-save by design. It does not write evidence, activate sources, run all monitors, or send customer messages.

## Discovery Methods Implemented

1. Robots sitemap extraction.
2. Sitemap index/urlset parsing.
3. Feed link discovery and RSS/Atom parsing.
4. PDF/document link discovery.
5. Same-domain official link candidate discovery.
6. Metadata extraction: title, canonical, description.
7. DOM/listing/table/rulebook/register candidate detection.
8. Playwright network/XHR candidate classification and scoped capture.
9. Endpoint scoring and recommended activation path generation.

## CLI

Updated `product/regradar/run.py`:

- `python3 run.py discover-source <URL> --json`
- `python3 run.py discover-source <URL> --js --network --sitemap --feeds --documents --max-links 50 --max-depth 1 --json`
- `python3 run.py source-discovery-lab <URL> --js --network --json`

The command prints structured JSON and does not write runtime reports.

## Failure Mapping

Extended source failure code vocabulary in `product/regradar/app/source_intake.py`:

- `TABLE_ADAPTER_REQUIRED`
- `REGISTER_ADAPTER_REQUIRED`
- `RULEBOOK_ADAPTER_REQUIRED`
- `DISCOVERY_FOUND_BETTER_ENDPOINT`
- `SITEMAP_DISCOVERY_REQUIRED`
- `NETWORK_ENDPOINT_DISCOVERY_REQUIRED`

## Officially Linked Documents

Off-domain PDF/document links discovered directly on an official regulator page are now preserved as `officially_linked` manual-review candidates. This handles cases like DFSA notice PDFs hosted on regulator-linked storage without pretending those documents are active, evidence-backed, or same-domain official sources.

These candidates still require Source Monitor provenance review, no-save validation, proof save, repeat baseline, and agent gates before activation.

## Policy Warning Fix

Public regulator pages often include login links or recaptcha scripts in navigation chrome. The policy warning gate now blocks real login/captcha walls while avoiding false positives from normal public-page chrome. This was covered with tests in `product/regradar/tests/test_source_quality_policy.py`.

## Limitations

- Network discovery is best-effort and scoped to a single public URL load.
- It does not bypass WAFs, login, CAPTCHA, paywalls, or private portals.
- It does not recursively crawl beyond the configured candidate extraction.
- Generated candidates are inactive until no-save, proof, baseline, and agent gates pass.

## Tests Added

Added `product/regradar/tests/test_source_discovery_engine.py`.

Covered:

- robots sitemap parsing;
- sitemap index/urlset parsing;
- feed discovery and RSS parsing;
- document link discovery;
- same-domain candidate rejection;
- network response classification;
- endpoint scoring;
- officially linked off-domain PDF handling;
- candidate generation;
- required discovery report fields.
