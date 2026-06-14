# Source Activation GitHub Research

Date: 2026-06-15

## Search Scope

Reviewed open-source tools and repositories for ideas around browser extraction, DOM investigation, content extraction, PDF/document parsing, web archiving, source health, and change detection.

No third-party repository was vendored. No code was copied.

## Tools / Repos Evaluated

| Tool / Repo | URL | Purpose | License / Maturity Observed | StatuteProof Use | Adopt |
|---|---|---|---|---|---|
| Playwright Python | https://github.com/microsoft/playwright-python | Browser automation for rendered pages | Apache-2.0, mature, 14k+ stars | Keep using Playwright for JS pages, selector validation, screenshots | Now, already aligned |
| Crawlee Python | https://github.com/apify/crawlee-python | Crawler/browser automation framework | Mature, 9k+ stars | Queue/session ideas only; too broad for scoped source activation | Later/research |
| Scrapy | https://github.com/scrapy/scrapy | Structured crawling framework | BSD-3-Clause, mature, 60k+ stars | Do not add crawler runtime now; borrow architecture idea of explicit item extraction | Research only |
| Trafilatura | https://github.com/adbar/trafilatura | Main-content extraction and metadata | Mature Python project | Good future fallback for article/static pages; dependency review needed | Later |
| Mozilla Readability | https://github.com/mozilla/readability | Main article extraction | Mature JS library | Conceptual model for article scoring; avoid JS dependency for now | Research only |
| Selectolax | https://github.com/rushter/selectolax | Fast HTML parser/CSS selectors | Mature parser | Future performance option; BeautifulSoup is enough for now | Later |
| BeautifulSoup / lxml family | Local/current stack | HTML parsing | Already used locally | Continue dependency-light parsing for fixtures/adapters | Now |
| htmldate | https://github.com/adbar/htmldate | Publication/update date extraction | Apache-2.0, production-oriented | Future date normalization for listing items; currently use simple regex | Later |
| courlan | https://github.com/adbar/courlan | URL cleaning/filtering/deduplication | URL hygiene project | Future canonical URL normalization and duplicate detection | Later |
| extruct | https://github.com/scrapinghub/extruct | Embedded metadata extraction | Mature metadata extractor | Future structured metadata extraction for official pages | Later |
| pypdf | https://github.com/py-pdf/pypdf | Pure Python PDF utilities | Mature | Existing PDF path can continue; table-rich PDFs may need stronger tooling | Later |
| pdfplumber | https://github.com/jsvine/pdfplumber | PDF text/table extraction | Mature | Strong candidate for official PDF tables; dependency review first | Later |
| PyMuPDF | https://github.com/pymupdf/PyMuPDF | High-performance PDF extraction | Mature | Good performance, but license/dependency implications need review | Research only |
| MarkItDown | https://github.com/microsoft/markitdown | Converts files to Markdown | MIT, very popular | Useful idea: preserve structure as Markdown; do not install `[all]` bundle now | Later |
| Unstructured | https://github.com/Unstructured-IO/unstructured | Document ETL to structured data | Large dependency surface | Too heavy for current activation sprint | Reject for now |
| Docling | https://github.com/docling-project/docling | Document conversion for gen AI | Large document stack | Promising for future PDF/doc extraction, too heavy now | Later/research |
| Browsertrix Crawler | https://github.com/webrecorder/browsertrix-crawler | Browser-based web archiving | AGPL-3.0, WARC/WACZ focused | Important evidence inspiration; AGPL means do not copy/vendor | Research only |
| ArchiveBox | https://github.com/ArchiveBox/ArchiveBox | Self-hosted web archiving | Popular archiving project | Evidence artifact inspiration; do not vendor | Research only |
| shot-scraper | https://github.com/simonw/shot-scraper | Automated screenshots | Useful CLI pattern | Screenshot evidence idea; direct implementation can stay local/Playwright | Later |
| warcio | https://github.com/webrecorder/warcio | WARC/ARC IO | Web archive library | Future WARC evidence layer, not needed for this sprint | Later |
| changedetection.io | https://github.com/dgtlmoon/changedetection.io | Website change detection | Mature product | Noise filters and diff threshold ideas; do not copy | Research only |
| Crawl4AI | https://github.com/unclecode/crawl4ai | LLM-friendly crawler/scraper | Popular | Not for change decisions; useful extraction strategy inspiration only | Research only |

## Ideas Adopted Now

1. Treat DOM investigation as a first-class step before source activation.
2. Separate article/static, listing, table, document/PDF listing, rulebook, register, feed, JSON/API, and screenshot evidence families.
3. Use item-level extraction for listings instead of full-page text.
4. Record machine-readable failure codes, not just prose errors.
5. Keep browser/screenshot/WARC-style evidence as future enrichment, not replacement for normalized text/hash proof.

## Ideas Deferred

- Full crawler frameworks.
- Heavy document-AI frameworks.
- WARC/WACZ evidence layer.
- OCR/scanned PDF support.
- Large dependency bundles.

## Ideas Rejected For This Sprint

- Broad crawls.
- Proxy/anti-bot bypass strategies.
- Copying code from AGPL projects.
- LLM-based change decisions.
- Installing all-in document conversion bundles.

## Mapping To StatuteProof

- Auto DOM Investigator: inspired by Playwright, readability/content extraction, and change-detection false-positive control.
- Adapter Catalog: inspired by Scrapy item extraction and document conversion tools, but implemented locally and narrowly.
- Evidence Layer: Browsertrix/ArchiveBox/warcio inform future artifact completeness, but no WARC runtime is added now.
- Quality Gate: changedetection-style noise control plus StatuteProof proof/baseline discipline.

## Safety Notes

- License review is required before adopting any code.
- Avoid AGPL code copy/vendor due license impact.
- Do not add large dependencies without a concrete source blocker.
- All live checks remain scoped and no-save unless strict gate permits evidence save.
