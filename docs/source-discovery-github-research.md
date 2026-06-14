# Source Discovery GitHub / Open-Source Research

## Search / Review Scope

Reviewed official documentation and open-source repositories for endpoint discovery, browser network capture, sitemap/feed parsing, document extraction, web archiving, and change detection.

Primary sources:

- Playwright Python network documentation: https://playwright.dev/python/docs/network
- Sitemaps protocol: https://www.sitemaps.org/protocol.html
- Robots Exclusion Protocol RFC 9309: https://www.rfc-editor.org/rfc/rfc9309.html
- Scrapy documentation: https://docs.scrapy.org/en/latest/topics/spiders.html

## Tools / Repositories Evaluated

| Tool / Repo | URL | Purpose | License / Maturity visible | Adopt Now / Later / Reject | StatuteProof Mapping |
|---|---|---|---|---|---|
| Playwright Python | https://playwright.dev/python/docs/network | Browser rendering and network request/response events | Microsoft docs; mature | Adopt now | XHR/public endpoint capture for scoped official pages |
| Sitemaps protocol | https://www.sitemaps.org/protocol.html | XML sitemap and sitemap index structure | Open protocol | Adopt now | Parse `loc`, `lastmod`, `changefreq` for endpoint candidates |
| RFC 9309 robots.txt | https://www.rfc-editor.org/rfc/rfc9309.html | Robots Exclusion Protocol | IETF standard | Adopt now | Robots sitemap lines and access-respect policy |
| Scrapy | https://github.com/scrapy/scrapy | Mature crawling framework | GitHub repo; mature | Later | Ideas for bounded same-domain spidering; no dependency now |
| Crawlee Python | https://crawlee.dev/python/ | Crawler framework | Active docs | Later | Ideas for request queues and retries; no dependency now |
| trafilatura | https://github.com/adbar/trafilatura | Text, metadata, sitemap/feed discovery | Apache-2.0 current; mature | Ideas now, dependency later | Reinforces sitemap/feed + main-text extraction |
| readability-lxml | https://github.com/buriy/python-readability | Article extraction | GitHub repo | Later | Fallback article extractor if existing extractor fails |
| selectolax | https://github.com/rushter/selectolax | Fast HTML parser | GitHub repo | Later | Possible speed upgrade; BeautifulSoup is enough now |
| changedetection.io | https://github.com/dgtlmoon/changedetection.io | Web change detection with selectors/filters/PDF/JSON | Apache-2.0 visible; mature | Ideas now | Selector targeting, JSON/PDF monitoring, noise filtering |
| ArchiveBox | https://github.com/ArchiveBox/ArchiveBox | Web archiving and evidence capture | Mature | Later | Evidence artifact breadth; do not vendor |
| Browsertrix Crawler | https://github.com/webrecorder/browsertrix-crawler | Browser-based archival crawling | Mature | Later | High-fidelity WARC/screenshot future layer |
| shot-scraper | https://github.com/simonw/shot-scraper | Screenshot automation | Mature CLI | Later | Screenshot/rendered DOM evidence ideas |
| warcio | https://github.com/webrecorder/warcio | WARC I/O library | Mature | Later | Future WARC evidence layer |
| pdfplumber | https://github.com/jsvine/pdfplumber | PDF text/table extraction | MIT visible; mature | Later | PDF tables/doc evidence; avoid dependency now |
| PyMuPDF | https://github.com/pymupdf/PyMuPDF | High-performance PDF extraction | Mature | Later | Fast PDF extraction if project already permits |
| pypdf | https://github.com/py-pdf/pypdf | Pure Python PDF handling | Mature | Later | Lightweight PDF metadata/page count |
| pdfminer.six | https://github.com/pdfminer/pdfminer.six | PDF text extraction | Mature | Later | Current ecosystem baseline for PDFs |
| Microsoft MarkItDown | https://github.com/microsoft/markitdown | Converts documents to Markdown | MIT visible; very mature | Later | Document normalization inspiration; note security warning |
| Unstructured | https://github.com/Unstructured-IO/unstructured | Document ETL | Mature, heavier | Research only | Too large for current runtime |
| Docling | https://github.com/docling-project/docling | Document conversion | Mature, heavier | Research only | Future complex document handling |
| Crawl4AI | https://github.com/unclecode/crawl4ai | Crawler/scraper for LLM-ready extraction | Mature | Research only | Ideas only; avoid LLM-based change decisions |
| Firecrawl | https://github.com/firecrawl/firecrawl | Hosted/API web extraction | AGPL-3.0 visible; claims broad coverage | Reject for runtime now | Do not adopt service/proxy/claims; useful reminder not to publicize “95%” |

## Ideas Adopted Now

- Playwright network response classification for public JSON/XML/PDF candidates.
- Robots and sitemap parsing with explicit no-bypass policy.
- Feed and document-link candidate extraction.
- Same-domain candidate graph with strict max depth/max links.
- Endpoint scoring before no-save testing.

## Ideas Worth Later

- WARC/screenshot evidence enrichment from Browsertrix/warcio/shot-scraper ideas.
- More robust PDF table extraction with pdfplumber or PyMuPDF.
- A crawler queue model inspired by Scrapy/Crawlee if source inventory grows.

## Ideas Rejected

- Hosted/proxy-based scraping services for source activation.
- “95% web coverage” claims.
- LLM-based change decisions.
- Broad crawls or bypass-oriented browser steps.

## License / Safety Notes

No code is copied from researched projects. This sprint independently implements small standard-library/BeautifulSoup helpers and uses already present project dependencies. Any later dependency adoption must include license review and explicit justification.

