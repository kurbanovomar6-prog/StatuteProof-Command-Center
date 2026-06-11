# Source Monitor Spec Guide

## Purpose
This guide defines how the Source Monitor Agent designs deterministic monitoring for official regulatory sources.
It prevents false positives, silent failures, selector drift, and evidence gaps.
It is not an LLM interpretation layer.

## Source Type Classification
| Source Type | Fetch Method | Normalization Approach | Known Risks |
|---|---|---|---|
| HTML static | requests/httpx-style fetch | Extract main content selector, remove nav/footer/scripts | Layout changes, dynamic banners |
| JS-rendered | Playwright future mode | Render page, then extract stable content | Slow fetch, consent banners, hidden content |
| PDF | PDF extraction future mode | Extract text, page order, metadata | Scanned PDFs, extraction errors |
| Document listing | HTML or JS depending on page | Extract rows, titles, dates, links | Pagination, sorting changes |
| Circular/news | HTML listing plus document fetch | Normalize title/date/link/body | Publication date ambiguity |
| Archive | Manual or scheduled crawl | Preserve index and document links | URL drift, missing old documents |

## Fetch Method Decision Tree
1. If the source is static HTML, use a simple HTTP fetch.
2. If content is missing without JavaScript, classify as JS-rendered and use future Playwright handling.
3. If the official item is a PDF, fetch the PDF and extract text separately.
4. If the page is a listing, monitor both listing metadata and linked documents.
5. If access fails, emit FAILED, never UNCHANGED.
6. If extraction returns empty content, emit QUALITY_DROP or SOURCE_STRUCTURE_CHANGED based on evidence.

## Normalization Rules
1. Remove scripts.
2. Remove styles.
3. Remove navigation menus.
4. Remove footer boilerplate.
5. Remove cookie banners.
6. Preserve headings.
7. Preserve paragraph order.
8. Preserve table cell text in reading order.
9. Normalize whitespace to single spaces except section breaks.
10. Preserve publication dates and document titles.
11. Do not remove obligation verbs.
12. Do not remove URLs to linked official documents.
13. Do not summarize before hashing.
14. Do not let an LLM rewrite normalized text.

## Hash Strategy
Use SHA-256 in the format `sha256:` plus 64 lowercase hex characters.
Normalize before hashing.
Store raw_hash and normalized_hash separately.
Hash raw content to prove capture integrity.
Hash normalized content for change detection.
Never hash full noisy HTML for the main status decision.

## Run Status Definitions

### FIRST_SEEN
Meaning: FIRST_SEEN is an explicit Source Monitor status and must be written to the run log.
When to emit: Use FIRST_SEEN only when its status-specific conditions are met by fetch, normalization, hash, and quality checks.
Evidence record required: yes for CHANGED and FIRST_SEEN; optional for UNCHANGED; blocked for FAILED/QUALITY_DROP unless audit record needed.
Human review required: no unless source is strategic or configured for review.
Downstream action: record baseline and do not brief.

### UNCHANGED
Meaning: UNCHANGED is an explicit Source Monitor status and must be written to the run log.
When to emit: Use UNCHANGED only when its status-specific conditions are met by fetch, normalization, hash, and quality checks.
Evidence record required: yes for CHANGED and FIRST_SEEN; optional for UNCHANGED; blocked for FAILED/QUALITY_DROP unless audit record needed.
Human review required: no unless source is strategic or configured for review.
Downstream action: log successful check and no brief.

### CHANGED
Meaning: CHANGED is an explicit Source Monitor status and must be written to the run log.
When to emit: Use CHANGED only when its status-specific conditions are met by fetch, normalization, hash, and quality checks.
Evidence record required: yes for CHANGED and FIRST_SEEN; optional for UNCHANGED; blocked for FAILED/QUALITY_DROP unless audit record needed.
Human review required: yes.
Downstream action: handoff to Evidence Trail for complete evidence capture.

### FAILED
Meaning: FAILED is an explicit Source Monitor status and must be written to the run log.
When to emit: Use FAILED only when its status-specific conditions are met by fetch, normalization, hash, and quality checks.
Evidence record required: no customer brief evidence record; retain run diagnostics.
Human review required: yes.
Downstream action: alert operator and block brief generation.

### QUALITY_DROP
Meaning: QUALITY_DROP is an explicit Source Monitor status and must be written to the run log.
When to emit: Use QUALITY_DROP only when its status-specific conditions are met by fetch, normalization, hash, and quality checks.
Evidence record required: no customer brief evidence record; retain run diagnostics.
Human review required: yes.
Downstream action: alert operator and block brief generation.

### SOURCE_STRUCTURE_CHANGED
Meaning: SOURCE_STRUCTURE_CHANGED is an explicit Source Monitor status and must be written to the run log.
When to emit: Use SOURCE_STRUCTURE_CHANGED only when its status-specific conditions are met by fetch, normalization, hash, and quality checks.
Evidence record required: no customer brief evidence record; retain run diagnostics.
Human review required: yes.
Downstream action: alert operator and block brief generation.

## QUALITY_DROP Detection Rules
- Normalized length falls below 70% of previous good run.
- Main content selector returns empty.
- PDF extraction returns no text.
- Page returns login, captcha, or access denied content.
- Response body is mostly navigation or footer.
- Expected document title disappears.
- Required table/list rows disappear without a matching official change.
- Encoding failure corrupts text.
- HTTP 200 returns an error page.
- Rendered page contains only loading shell.

## Retry Policy
Timeout: retry twice, then FAILED.
4xx: do not retry blindly; log status and emit FAILED unless 404 is confirmed source removal requiring human review.
5xx: retry twice with delay, then FAILED.
Empty content: retry once; if repeated, QUALITY_DROP or SOURCE_STRUCTURE_CHANGED.
Never classify a failed fetch as UNCHANGED.
Never classify empty extraction as CHANGED.

## UAE Source Bootstrap Reference Table
| Regulator | Expected Source Type | Likely Content Formats | Monitoring Risk | Verification Required | First Page Placeholder |
|---|---|---|---|---|---|
| VARA | Guidance/rulebook/listing | HTML, PDF | URL drift, PDF updates | VERIFY BEFORE PRODUCTION | https://example.invalid/verify-vara |
| CBUAE | Circulars/regulations/listing | HTML, PDF | PDF-only docs, archive pages | VERIFY BEFORE PRODUCTION | https://example.invalid/verify-cbuae |
| DFSA | Rulebook/notices | HTML, PDF | complex site structure | VERIFY BEFORE PRODUCTION | https://example.invalid/verify-dfsa |
| ADGM FSRA | Rulebook/guidance | HTML, PDF | document versioning | VERIFY BEFORE PRODUCTION | https://example.invalid/verify-adgm-fsra |
| FTA | Tax guides/decisions | HTML, PDF | publication categories | VERIFY BEFORE PRODUCTION | https://example.invalid/verify-fta |
| UAE FIU | AML notices/guidance | HTML, PDF | sparse updates | VERIFY BEFORE PRODUCTION | https://example.invalid/verify-fiu |
| DIFC | laws/regulations/notices | HTML, PDF | multiple authorities | VERIFY BEFORE PRODUCTION | https://example.invalid/verify-difc |
| SCA | regulations/circulars | HTML, PDF | Arabic/English variants | VERIFY BEFORE PRODUCTION | https://example.invalid/verify-sca |

## Source Config Template
```yaml
source_id:
regulator:
official_url:
source_type:
fetch_method:
content_selector:
exclude_selectors:
expected_min_length:
previous_good_hash:
retry_policy:
quality_drop_threshold:
pdf_handling:
js_rendering_required:
human_review_on:
owner_agent: Source Monitor Agent
```

## SAMPLE / FAKE Source Spec Example
source_id: sample-vara-guidance
regulator: VARA
official_url: https://example.invalid/vara-sample-guidance
source_type: HTML static
fetch_method: http
content_selector: main
exclude_selectors: nav, footer, script, style
expected_min_length: 500
quality_drop_threshold: 0.70
human_review_on: CHANGED, FAILED, QUALITY_DROP, SOURCE_STRUCTURE_CHANGED
