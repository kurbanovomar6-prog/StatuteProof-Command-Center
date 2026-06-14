# Adapter Platform GitHub / Open-Source Research

Date: 2026-06-14

No third-party code was copied. No repositories were vendored. No new dependencies were installed. The research below is used as architecture input only.

## 1. Search / Review Scope

Reviewed public GitHub projects and official project pages for:

- browser rendering and selector workflows
- website change detection
- web archiving / WARC / screenshot evidence
- HTML main-content extraction
- listing/table/document extraction
- PDF extraction
- agent-oriented crawlers

## 2. Tools / Repositories Evaluated

| Tool / repo | URL | License / maturity visible | Useful idea for StatuteProof | Decision |
|---|---|---:|---|---|
| Playwright Python | https://github.com/microsoft/playwright-python | Apache-2.0, 14.7k stars, active releases visible | Keep Playwright as the rendering/wait-selector engine; expose selector diagnostics and rendered HTML metadata. | Adopt now conceptually; already used. |
| changedetection.io | https://github.com/dgtlmoon/changedetection.io | Apache-2.0, 32k stars visible | Per-watch filters, visual selector workflow, ignore selectors/text, PDF change handling, screenshot attachments. | Adopt ideas later; no code copy. |
| ArchiveBox | https://github.com/ArchiveBox/ArchiveBox | Open-source archiving project | Multi-artifact evidence model: HTML, PDFs, media, screenshots, metadata. | Later evidence roadmap. |
| Browsertrix Crawler | https://github.com/webrecorder/browsertrix-crawler | Browser-based archiving crawler | High-fidelity browser capture and WACZ/WARC thinking for future audit trail. | Research only for now. |
| warcio | https://github.com/webrecorder/warcio | WARC/ARC streaming library | Future WARC evidence adapter if StatuteProof needs archive-grade snapshots. | Later; not MVP. |
| shot-scraper | https://github.com/simonw/shot-scraper | CLI screenshot utility | Lightweight screenshot evidence idea per saved run. | Later; do not add dependency now. |
| Crawlee Python | https://github.com/apify/crawlee-python | 9.2k stars visible | Request/browser crawler separation and dataset-style records. | Later; too broad for this run. |
| Scrapy | https://github.com/scrapy/scrapy | Mature Python crawling framework | Mature spider/item pipeline model. | Reject for runtime now; too heavy for scoped official-source monitoring. |
| trafilatura | https://github.com/adbar/trafilatura | Existing optional extractor in project | Good fallback for article/main-content extraction. | Already integrated as optional provider. |
| python-readability | https://github.com/buriy/python-readability | Apache-2.0, 2.9k stars visible | Main-content extraction fallback; currently optional in extractor cascade. | Already integrated as optional provider. |
| selectolax | https://github.com/rushter/selectolax | 1.6k stars visible | Fast CSS selector parsing for future performance. | Later; BeautifulSoup is enough for this scoped implementation. |
| BeautifulSoup | https://www.crummy.com/software/BeautifulSoup/ | Existing dependency pattern in project | Keep for robust small adapters and tests. | Adopt now; already present. |
| lxml | https://github.com/lxml/lxml | Mature XML/HTML toolkit | Strong table/XML parsing and XPath support. | Later unless dependency already present. |
| extruct | https://github.com/scrapinghub/extruct | BSD-3-Clause, 966 stars visible | Extract JSON-LD/OpenGraph metadata, dates, canonical URLs. | Later metadata adapter. |
| htmldate | https://github.com/adbar/htmldate | Date extraction project | Publication-date detection for listings/documents. | Later optional date enrichment. |
| courlan | https://github.com/adbar/courlan | URL cleaning/filtering | Canonical URL and duplicate URL filtering. | Later if URL normalization becomes noisy. |
| PyMuPDF | https://github.com/pymupdf/PyMuPDF | High-performance PDF extraction library | Faster direct PDF extraction, page count and shallow/OCR-needed classification. | Later; avoid dependency churn now. |
| pdfplumber | https://github.com/jsvine/pdfplumber | MIT, 10.4k stars visible | Table extraction and visual PDF debugging; best for machine-generated regulatory PDFs. | Later PDF/table adapter. |
| pypdf | https://github.com/py-pdf/pypdf | Pure-Python PDF tooling | Lightweight page/text fallback. | Later if current PDF path insufficient. |
| pdfminer.six | https://github.com/pdfminer/pdfminer.six | Community PDF extraction | Current ecosystem base for many PDF tools. | Keep as background reference. |
| MarkItDown | https://github.com/microsoft/markitdown | MIT, 153k stars visible | Document-to-Markdown structure preservation; strong security warning about process privileges. | Research only; too broad for runtime now. |
| Unstructured | https://github.com/Unstructured-IO/unstructured | Mature document ETL | Heavy-duty document partitioning. | Reject for now; likely too heavy. |
| Docling | https://github.com/docling-project/docling | Document conversion toolkit | Future complex document extraction option. | Later; not in scoped adapter core. |
| Crawl4AI | https://github.com/unclecode/crawl4ai | Existing optional extractor path | Markdown-oriented crawler ideas; existing extractor opt-in is enough. | Keep optional only. |
| Firecrawl | https://github.com/firecrawl/firecrawl | AGPL-3.0, 133k stars visible | Clean markdown, screenshots, API extraction. License/API/secrets risk for product runtime. | Reject runtime use; research only. |
| browser-use | https://github.com/browser-use/browser-use | Agent-browser automation | Useful for manual DOM investigation, not for parser decisions. | Research only. |

## 3. Top Ideas Worth Adopting Now

1. Explicit adapter family metadata in every Source Lab result.
2. Listing adapter with item-level text, URL, category, optional date, and stable sorting.
3. Table adapter with deterministic header/row serialization.
4. Custom-element adapter for ADGM-style rendered pages.
5. Per-source noise/source-health metadata.
6. Failure reasons that map to remediation, not false readiness.
7. Adapter versioning in evidence metadata.
8. Keep optional heavy extractors optional; do not install large dependencies just to raise source counts.

## 4. Ideas Worth Adopting Later

- Visual selector picker inspired by changedetection.io.
- Screenshot evidence per saved run.
- WARC/WACZ evidence layer for high-value sources.
- PDF listing adapter plus scoped direct PDF text extraction.
- Metadata/date extraction using extruct/htmldate if source dates become unreliable.
- Source-specific diff filters for high-noise listing pages.

## 5. Ideas Rejected For Now

- Broad crawler frameworks for default monitoring. They increase operational and legal risk.
- Agentic web navigation for source change decisions. StatuteProof should not use LLMs to decide whether source content changed.
- Proxy/anti-bot workflows. StatuteProof should not bypass access controls.
- Hosted extraction APIs requiring secrets or transmitting regulator pages to third parties by default.
- Large document-AI stacks for a small adapter-core sprint.

## 6. License / Safety Notes

- No code copied from the reviewed projects.
- Architecture ideas are independently reimplemented with standard library plus existing project dependencies.
- AGPL projects such as Firecrawl should not be copied into product runtime without deliberate license review.
- Any future WARC/screenshot/document extraction dependency should get a separate security and license review before adoption.

## 7. Mapping To StatuteProof

StatuteProof should stay evidence-first, not crawler-first. The adapter platform should make every source’s extraction strategy explicit:

- source officialness: Source Monitor gate
- extraction adapter: Code Architect gate
- no-save result: QA/Critic gate
- proof/baseline: Evidence Trail gate
- wording: Legal Language gate
- buyer relevance: Product Manager / ICP gate

This lets the product grow from 13 enabled sources toward a larger official UAE pack without pretending that untested sources are ready.
