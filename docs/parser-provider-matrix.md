# Parser Provider Matrix

## Core Active / Fallback Providers

| Provider | Role | Status | Code path | Hard dependency | Safety behavior |
|---|---|---:|---|---:|---|
| Playwright Python | JS rendering, selector waits | Active when configured | `app/scraper.py` | Yes in current env | Failure becomes selector/fetch review; no bypass. |
| trafilatura | Main text extraction | Active | `app/providers/html_extraction.py` | Optional/graceful | Missing import returns structured failure. |
| readability-lxml | Reader-mode fallback | Active fallback | `app/providers/html_extraction.py` | Optional/graceful | Missing import returns structured failure. |
| selectolax | CSS selector extraction | Active optional | `app/providers/html_extraction.py` | Optional/graceful | Missing import returns structured failure. |
| BeautifulSoup | Compatibility fallback | Active fallback | `app/providers/html_extraction.py`, `app/parser.py` | Expected | Last-resort visible text extraction. |
| lxml | Parser backend | Indirect | readability/trafilatura ecosystem | Optional indirect | Not directly required by StatuteProof code. |
| PyMuPDF | PDF text extraction | Provider exists | `app/providers/pdf_extraction.py` | Optional/graceful | Bad/missing PDF returns structured failure. |
| pdfplumber | PDF table/layout extraction | Provider exists | `app/providers/pdf_extraction.py` | Optional/graceful | Bad/missing PDF returns structured failure. |
| pypdf | Lightweight PDF fallback | Provider exists | `app/providers/pdf_extraction.py` | Optional/graceful | Bad/missing PDF returns structured failure. |
| htmldate | Date extraction | Provider exists | `app/providers/optional_tools.py` | Optional/graceful | Missing import does not block parsing. |
| courlan | URL canonicalization | Provider exists | `app/providers/optional_tools.py` | Optional/graceful | Falls back to urllib validation. |
| DeepDiff | Structured metadata diff | Provider exists | `app/providers/optional_tools.py` | Optional/graceful | Falls back to shallow dict diff. |

## Planned Optional Providers

| Provider | Intended role | Status | Activation rule |
|---|---|---:|---|
| Resiliparse | Boilerplate removal fallback | Not installed | Evaluate only if benchmark proves better output. |
| jusText | Boilerplate removal fallback | Not installed | Evaluate only if benchmark proves better output. |
| extruct | Structured metadata extraction | Not installed | Optional metadata enrichment, not readiness gate. |
| warcio | WARC evidence snapshots | Not installed | Optional evidence upgrade, not required for MVP. |
| Browsertrix Crawler | High-fidelity WARC/browser capture | Future | Only for controlled source packs, not broad crawl. |
| Crawlee Python | Scalable crawler | Future | Only after pilot proves need for crawling queues. |
| Crawl4AI | Markdown extraction experiments | Optional legacy opt-in | Never source-of-truth for change detection. |
| Scrapy | Large-scale crawling | Future/rejected for now | Too broad for current UAE source pack. |
| Firecrawl / crw | External web-to-markdown references | Rejected for core | Avoid external API dependency for evidence. |
| browser-use | Research only | Rejected for core | Agentic browsing is not deterministic evidence. |
| OpenTimestamps | External timestamp proof | Future | Optional proof-hardening after evidence model stabilizes. |

## Provider Result Requirements

Every provider must:

- avoid crashing when missing;
- return dependency availability;
- return warnings and errors;
- avoid access-control bypass;
- never decide regulatory change with an LLM;
- leave final readiness/certification to source quality and certification gates.
