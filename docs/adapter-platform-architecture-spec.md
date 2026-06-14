# Adapter Platform Architecture Spec

Date: 2026-06-14

## 1. Goal

Build a small, explicit source-adapter platform that helps StatuteProof onboard official public sources faster without weakening evidence, baseline, or legal-safety gates.

The adapter platform is not a promise that every website can be parsed. It is a controlled extraction layer for public official or officially linked sources that are technically accessible and permitted to monitor.

## 2. Core Principles

1. Explicit adapter selection beats silent magic.
2. No-save tests remain preview only.
3. Saved evidence still flows through the existing proof/source-runs pipeline.
4. One saved run is evidence, not monitoring-ready.
5. Source-health and noise risk must be visible before activation.
6. Adapters should fail into remediation, not fake readiness.
7. Heavy dependencies require a separate license/security review.

## 3. Adapter Result Schema

Every adapter returns an `AdapterResult` with:

- `text`: normalized text suitable for the existing hash/quality/evidence pipeline.
- `adapter_family`: static_html, playwright_selector, custom_element, listing, table, pdf_document, pdf_listing, rulebook_module, register, feed, api_json, screenshot_evidence, archive.
- `adapter_name`: human-readable adapter implementation name.
- `adapter_version`: version string.
- `extraction_strategy`: stable identifier for tests and reports.
- `items`: structured item rows when relevant.
- `item_count`: number of extracted items.
- `warnings`: non-fatal warnings.
- `failure_reason`: why extraction failed, if it failed.
- `remediation_hint`: next human action.
- `noise_risk`: low / medium / high / unknown.
- `source_health_risk`: low / medium / high / unknown.
- `metadata`: adapter-specific safe metadata.

## 4. Adapter Families

### 4.1 Static HTML Content Adapter

Input config:
- `content_selector`
- `exclude_selectors`
- `min_chars`

Output:
- main/article/body text
- headings/paragraphs preserved where possible
- boilerplate filtering metadata

Failure modes:
- selector missing
- shallow text
- nav-shell-heavy text

Use when:
- page has stable static content and no item list structure is needed.

Do not use when:
- source is a dynamic register/listing where item-level extraction is needed.

### 4.2 Playwright Selector Adapter

Input config:
- `wait_selector`
- `content_selector`
- `timeout_ms`

Output:
- rendered content text
- rendered selector diagnostics

Failure modes:
- selector timeout
- rendered shell only
- blocked/access-control page

Use when:
- page requires JavaScript rendering.

Do not use when:
- page is private, behind CAPTCHA/login/paywall, or requires bypass.

### 4.3 Custom Element Adapter

Input config:
- `content_selector`
- `exclude_selectors`

Output:
- text from custom elements such as ADGM `adgm-page > span`

Failure modes:
- custom element not rendered
- shadow/custom content not exposed in DOM

Use when:
- official site uses custom tags but exposes text in rendered HTML.

### 4.4 Listing Adapter

Input config:
- `container_selector`
- `item_selector`
- `title_selector`
- `date_selector`
- `url_selector`
- `category_selector`
- `exclude_selectors`
- `sort_items`
- `max_items`

Output:
- stable item list text
- item rows with title/date/url/category/hash
- listing-level noise metadata

Failure modes:
- no items found
- only nav/search controls found
- listing churn too high
- pagination unresolved

Use when:
- page lists regulations, notices, decisions, circulars, consultations, or official documents.

Do not use when:
- the page is a generic homepage or uncontrolled search result.

### 4.5 Table Adapter

Input config:
- `table_selector`
- `exclude_selectors`
- `sort_rows`
- `max_rows`

Output:
- table header and row serialization
- row hashes

Failure modes:
- table missing
- row count too low
- sort key unavailable

Use when:
- source is an official register, list, or regulation table.

### 4.6 PDF Document Adapter

Input config:
- `pdf_url`
- `min_chars`
- `page_limit`

Output:
- PDF text
- page count
- shallow/OCR-needed classification

Failure modes:
- image-only/scanned PDF
- too short
- encrypted or malformed PDF

Use when:
- official source is a direct public PDF.

### 4.7 PDF Listing Adapter

Input config:
- listing adapter config
- `pdf_link_selector`
- `fetch_pdf_text`
- `pdf_fetch_limit`

Output:
- document titles/URLs/dates
- optional scoped PDF text

Failure modes:
- unbounded PDF set
- PDF links behind protected flows

Use when:
- official listing points to regulatory PDFs.

### 4.8 Rulebook / Module Adapter

Input config:
- `module_selector`
- `title_selector`
- `version_selector`
- `url_selector`

Output:
- module-level titles, URLs, dates/versions if present
- module-level hashes

Use when:
- regulator publishes a rulebook/sourcebook/module index.

### 4.9 Register Adapter

Input config:
- table/listing adapter config
- pagination policy
- filter policy

Output:
- stable entity/register row text
- limitations about pagination/search/filter scope

Use when:
- public register is relevant to MLRO/CCO monitoring.

### 4.10 Sitemap / RSS / Feed Adapter

Input config:
- feed URL or sitemap URL
- URL allowlist/domain policy

Output:
- canonical item URLs and pubdates/lastmod

Use when:
- source provides an official public feed or sitemap.

Do not use when:
- feed only gives marketing/news noise unrelated to compliance.

### 4.11 API / JSON Discovery Adapter

Input config:
- public unauthenticated endpoint
- response path selectors

Output:
- structured public records

Use only when:
- endpoint is public, unauthenticated, and officially linked.

Do not use:
- private/internal APIs, hidden endpoints that imply bypass, or anything requiring tokens.

### 4.12 Screenshot / Rendered DOM Evidence Adapter

Output:
- screenshot path
- rendered HTML path

Use:
- as evidence enrichment only.

Do not use:
- as a replacement for normalized text/hash evidence.

### 4.13 WARC / Archive Adapter

Output:
- WARC/WACZ archive paths

Use:
- future high-assurance evidence layer.

Not required for this implementation.

## 5. Source Lab Integration

`run_source_intake()` should:

1. Fetch HTML using existing safe fetch path.
2. If `adapter_family` or `adapter_name` is explicitly configured, run the adapter.
3. Use adapter text only when the adapter returns non-empty text.
4. Fall back to the existing extraction cascade when no adapter is configured or adapter text is empty.
5. Preserve existing nav-shell, hash, quality, certification, and evidence-write gates.
6. Add adapter metadata to the result and evidence metadata.

Source Lab CLI/API should expose:

- `adapter_used`
- `adapter_family`
- `adapter_name`
- `adapter_version`
- `extraction_strategy`
- `adapter_warnings`
- `adapter_metadata`

## 6. Work Queue Integration

`product/regradar/config/uae_source_work_queue.json` should include:

- `adapter_family`
- `adapter_name`
- `adapter_version`
- `adapter_config`
- `extraction_strategy`
- `last_adapter_test_at`
- `adapter_status`
- `adapter_failure_reason`
- `adapter_remediation_hint`

These fields do not make a source ready. They only describe the extraction path and remediation state.

## 7. Evidence Impact

Evidence writing remains in `_write_intake_evidence()`. Adapter metadata should be added to:

- provider report
- source run record metadata
- snapshot metadata if already available through the existing evidence path

Proof validity remains tied to:

- normalized text
- normalized hash
- content hash
- proof path
- baseline runs
- certification status

## 8. Required Tests

- listing extraction
- listing boilerplate exclusion
- table extraction
- stable table sorting
- custom element extraction
- Source Lab adapter metadata
- no-save remains preview-only
- one saved run does not activate monitoring
- high noise/source-health blocks activation through validators

## 9. Not In This Scope

- Broad source registry expansion.
- Claiming 50 or 60 working sources.
- Production deployment.
- Live Stripe/customer activation.
- WARC evidence implementation.
- Huge dependency installation.
- Agentic browser navigation as a parser decision-maker.
