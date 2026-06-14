# StatuteProof 10/10 GitHub and Open-Source Research

## 1. Search Scope

This continuation pass used a focused research lens rather than installing or copying third-party code. The goal was to identify ideas that can make StatuteProof more truthful, resilient, and auditable without adding heavy dependencies or vendor dumps.

Search themes:

- website change detection systems
- regulatory monitoring source health
- Playwright extraction best practices
- HTML main-content extraction and boilerplate removal
- WARC and screenshot evidence capture
- PDF extraction and table extraction
- document parsing for regulated documents
- parser quality scoring and failure handling
- compliance SaaS onboarding and manual activation UX
- security practices for custom URL fetchers

No repository code was copied in this pass. No dependencies were installed.

## 2. Repos and Tools Reviewed

| Repo / Tool | Purpose | Maturity signal | License visibility | Useful idea for StatuteProof | Adopt now? | Risk notes |
|---|---:|---:|---:|---|---|---|
| https://github.com/dgtlmoon/changedetection.io | Website change monitoring | Mature product | Visible on repo | Watch history, change filters, notifications, failure UI | Later | Avoid copying code; use as UX/reference architecture only |
| https://github.com/ArchiveBox/ArchiveBox | Web archiving | Mature product | Visible on repo | Multi-artifact captures, snapshots, indexable archive model | Later | Heavy operational footprint |
| https://github.com/webrecorder/browsertrix-crawler | Browser-based web archiving | Mature crawler | Visible on repo | Browser crawl with WARC-grade evidence model | Later | Heavy dependency; better as separate evidence tier |
| https://github.com/webrecorder/warcio | WARC read/write tooling | Focused library | Visible on repo | Optional WARC artifact for high-stakes source proofs | Later | Adds artifact size and retention concerns |
| https://github.com/simonw/shot-scraper | Browser screenshots from CLI | Mature focused tool | Visible on repo | Screenshot evidence artifact and viewport metadata | Later | Extra browser dependency; verify storage policy |
| https://github.com/microsoft/playwright-python | Browser automation | Mature core library | Visible on repo | Deterministic selectors, tracing, browser context cleanup | Already used / later harden | Keep safe timeouts and no bypass behavior |
| https://github.com/apify/crawlee-python | Crawling framework | Emerging Python crawler | Visible on repo | Request queue, retry state, per-source run history ideas | Research only | Could be too heavy for current runtime |
| https://github.com/scrapy/scrapy | Crawling framework | Mature | Visible on repo | Downloader middleware and stats model ideas | Research only | Runtime rewrite not justified |
| https://github.com/adbar/trafilatura | Main text extraction | Mature | Visible on repo | Main-content extraction fallback, metadata extraction | Already referenced / keep | Validate optional dependency failure paths |
| https://github.com/buriy/python-readability | Readability extraction | Mature | Visible on repo | Fallback extraction for article-like pages | Already referenced / keep | Not enough for JS shells alone |
| https://github.com/rushter/selectolax | Fast HTML parser | Mature | Visible on repo | Fast fallback parser and link-density checks | Later | Optional dependency only |
| https://github.com/adbar/courlan | URL canonicalization | Mature | Visible on repo | Canonical URL and domain normalization | Later | Add only if current URL normalization becomes weak |
| https://github.com/adbar/htmldate | Date extraction | Mature | Visible on repo | Publication/update date extraction | Later | Regulatory pages often omit dates |
| https://github.com/scrapy/extruct | Structured metadata extraction | Mature | Visible on repo | JSON-LD/OpenGraph metadata in evidence report | Later | Helpful but not core P0 |
| https://github.com/pymupdf/PyMuPDF | PDF extraction | Mature | Visible on repo | Page count, text quality, PDF metadata | Already referenced / keep | License and binary dependency review before deeper use |
| https://github.com/jsvine/pdfplumber | PDF text/table extraction | Mature | Visible on repo | Table extraction and layout-aware PDF checks | Later | Slower; not every PDF needs table parsing |
| https://github.com/py-pdf/pypdf | PDF parsing | Mature | Visible on repo | Lightweight PDF fallback | Already referenced / keep | Quality varies by PDF |
| https://github.com/pdfminer/pdfminer.six | PDF parsing | Mature | Visible on repo | Text fallback and scanned-PDF detection signal | Later | Can be slow/noisy |
| https://github.com/microsoft/markitdown | Document-to-Markdown | Active Microsoft tool | Visible on repo | Consistent conversion layer for docs/PDFs later | Research only | Too broad for current parser core |
| https://github.com/Unstructured-IO/unstructured | Document parsing | Mature commercial/open stack | Visible on repo | Complex document pipeline architecture ideas | Research only | Heavy dependencies and deployment complexity |
| https://github.com/docling-project/docling | Document conversion | Active | Visible on repo | Structured document extraction, layout pipeline ideas | Research only | Heavy for MVP |
| https://github.com/unclecode/crawl4ai | Web crawling / markdown | Active | Visible on repo | Markdown output and crawler result schema ideas | Research only | Avoid adding another extraction abstraction now |
| https://github.com/firecrawl/firecrawl | Web extraction API/service | Active | Visible on repo | External provider option for hard public pages | Optional later | Third-party service/privacy/compliance review required |
| https://github.com/opentimestamps/opentimestamps-client | Timestamping | Focused | Visible on repo | Optional external timestamp proof layer | Later | Operational process needed before customer claims |

## 3. Top 10 Useful Ideas

1. Add screenshot evidence as an optional artifact for high-risk saved runs.
2. Add WARC capture as an optional enterprise-grade proof layer, not a default MVP requirement.
3. Keep Playwright extraction strict: selector wait failures must remain remediation, not confirmed.
4. Add a per-source run history view with health, extraction quality, and failure reasons.
5. Keep provider reports structured enough to show why a source failed.
6. Add metadata extraction later: title, canonical URL, publish/update date, content type, language.
7. Add PDF page-count and scanned/OCR-needed detection before claiming meaningful PDF extraction.
8. Treat third-party extraction services as optional fallback providers only after legal/security review.
9. Use screenshot/WARC/timestamping as separate evidence levels so the UI does not overclaim.
10. Make validators enforce claim safety, especially sample/demo and evidence/proof wording.

## 4. Adopt Now

Adopt now as documentation and validator direction only:

- no new runtime dependency
- no copied code
- no source registry rewrite
- validator hardening for sample brief labels and proof references
- workflow documentation for baseline/evidence-save and pre-demo gates

## 5. Adopt Later

- Screenshot artifact capture for saved evidence runs.
- WARC artifact capture for high-stakes sources.
- Metadata extractor layer for canonical URL/date/title/language.
- Better PDF quality scoring with page count, extraction density, and scanned-PDF detection.
- Source health dashboard using run-history concepts from change-monitoring tools.

## 6. Reject For Now

- Full crawler framework migration.
- Heavy document AI stack for MVP runtime.
- Vendor-copying extraction libraries.
- External scraping APIs for customer data before privacy/security review.

## 7. Exact Mapping To StatuteProof

| StatuteProof area | Research-inspired improvement |
|---|---|
| Evidence proof | Add screenshot/WARC/timestamp levels later as explicit evidence levels |
| Source Lab | Show provider report, failure reason, selector issue, and activation readiness separately |
| Parser quality | Add stricter PDF/scanned/nav-shell checks before confirmed status |
| Source health | Track extraction quality over time and surface quality drops |
| Customer demo | Use only proof-backed sample brief with clear SAMPLE / FAKE DEMO label |
| Paid pilot | Require baseline run history and manual activation review before claiming monitoring-ready |

## 8. License And Safety Notes

- No code was copied in this pass, so no new attribution or license obligations were introduced.
- Before adopting any code, review the repository license, dependency tree, and security posture.
- Prefer independently reimplementing small ideas such as field names, validation gates, and evidence-level concepts.
- Do not vendor third-party repositories into StatuteProof runtime.

## 9. Suggested Future Prompts

1. Implement optional screenshot evidence for saved Source Lab runs without changing source readiness claims.
2. Add PDF quality scoring with page count, text density, and scanned-PDF warnings.
3. Add a source health timeline view backed by existing source run metadata.
4. Design WARC evidence as an optional enterprise tier artifact with retention and storage controls.
