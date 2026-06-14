# Parser GitHub Discovery Report

Date: 2026-06-14

Scope: GitHub/open-source research for parser/source-intake improvements. Web search was attempted and GitHub API metadata was used for exact repository pages where available. No discovered repository was copied into product runtime.

## Search Queries Used

- best Python web scraping extraction boilerplate removal GitHub
- GitHub Python main content extraction web pages
- GitHub Python boilerplate removal HTML
- GitHub Python regulatory PDF extraction
- GitHub WARC capture Python browser crawler
- GitHub Playwright Python crawler extraction
- GitHub source monitoring website change detection Python
- GitHub URL canonicalization Python scraping
- GitHub metadata extraction HTML Python
- GitHub DOM snapshot evidence Playwright Python
- GitHub website change detection JSONL evidence Python
- GitHub web monitoring diff hash Python
- GitHub public website source health monitoring Python
- GitHub regulatory document parser Python

## Additional Repositories Evaluated

| Repo | Stars visible | License visible | Purpose | Maturity | Risk | Useful for StatuteProof? | Status | Idea to copy/adapt | Why not blindly copied |
|---|---:|---|---|---|---|---|---|---|---|
| https://github.com/dgtlmoon/changedetection.io | 31989 | Apache-2.0 | Website change detection | High | Broad app/runtime | Yes | optional later | Watch history/notification UX and diff discipline | Full app stack overkill; StatuteProof already has deterministic hashes |
| https://github.com/ArchiveBox/ArchiveBox | 27693 | MIT | Web archiving | High | Heavy dependency/storage | Yes | optional later | Evidence bundle ideas: HTML, PDF, media, screenshots | Too broad/heavy for MVP parser |
| https://github.com/NewsDiffs/newsdiffs | 1 | unknown | Article change tracking | Low/stale | Low maturity | Limited | research only | Historical change tracking concept | Not mature enough |
| https://github.com/codelucas/newspaper | 15078 | MIT | Article text/metadata extraction | Medium | News-biased | Limited | research only | Metadata/article extraction heuristics | Regulatory pages are not news articles |
| https://github.com/goose3/goose3 | 910 | Apache-2.0 | Article extraction | Medium | News-biased | Limited | research only | Alternative content extraction comparison | Not regulator-specific |
| https://github.com/weblyzard/inscriptis | 342 | Apache-2.0 | HTML to text conversion | Medium | Extra dependency | Yes | optional later | Preserve structural text layout from HTML | Test against UAE fixtures before adding |
| https://github.com/misja/python-boilerpipe | 542 | unknown | Boilerplate removal | Low/older | Java/legacy risk | Limited | reject | Boilerplate concepts only | Older stack; not worth dependency |
| https://github.com/mozilla/readability | 11270 | unknown | Readability core | High | JS package/runtime mismatch | Yes | research only | Readability behavior benchmark | Python readability already used |
| https://github.com/microsoft/markitdown | 152938 | MIT | Document-to-Markdown | High | Broad file parsing | Yes | optional later | Convert docs/PDFs/Office docs for review | Heavy, not needed for core HTML parser |
| https://github.com/pymupdf/PyMuPDF-Utilities | 718 | AGPL-3.0 | PyMuPDF examples | Medium | AGPL examples | Yes | research only | PDF layout/page metadata examples | License caution; do not copy code |
| https://github.com/camelot-dev/camelot | 3757 | MIT | PDF table extraction | High | Needs Ghostscript/system deps | Yes | optional later | Table extraction for regulator PDFs | Too heavy until table PDFs are priority |
| https://github.com/chezou/tabula-py | 2315 | MIT | PDF table extraction wrapper | Medium | Java dependency | Limited | optional later | Table extraction fallback | Java dependency not worth MVP |
| https://github.com/ocrmypdf/OCRmyPDF | 33880 | MPL-2.0 | OCR text layer for scanned PDFs | High | Heavy system deps | Yes | optional later | OCR-needed detection and offline OCR path | Too heavy for immediate parser |
| https://github.com/LexPredict/lexpredict-lexnlp | 783 | AGPL-3.0 | Legal NLP | Medium | License and NLP overreach | Limited | reject now | Legal-document entity/date ideas | Do not use NLP to decide changes or obligations |
| https://github.com/scrapy/protego | 88 | BSD-3-Clause | robots.txt parser | Medium | Low | Yes | optional later | Access-policy/robots reporting | Add only after policy design |
| https://github.com/scrapy/w3lib | 419 | BSD-3-Clause | Web utilities | High | Low | Yes | optional later | URL/canonical/header helpers | Keep current simple logic unless needed |
| https://github.com/simonw/shot-scraper | 2369 | Apache-2.0 | Playwright screenshots | High | CLI/runtime dependency | Yes | optional later | Screenshot evidence model | Playwright can capture directly; do not shell to CLI by default |
| https://github.com/internetarchive/warcprox | 453 | not visible | WARC proxy | Medium | Proxy complexity | Yes | research only | WARC capture architecture | Too heavy for MVP evidence |
| https://github.com/webrecorder/pywb | 1669 | GPL-3.0 | Web archive replay/recording | High | GPL/runtime risk | Limited | research only | Replay/evidence verification concepts | License/runtime risk |
| https://github.com/html5lib/html5lib-python | 1222 | MIT | HTML parser | High | Low | Limited | research only | Parser robustness reference | Existing bs4/lxml stack enough |
| https://github.com/wention/BeautifulSoup4 | 219 | unknown | Archived BS4 mirror | Archived | Stale | No | reject | None | Archived mirror; use PyPI package |
| https://github.com/alan-turing-institute/CleverCSV | 1326 | MIT | Messy CSV parsing | Medium | Low | Limited | optional later | Future regulator CSV/table ingestion | Not needed for HTML/PDF MVP |
| https://github.com/dateutil/dateutil | 2622 | unknown | Date parsing | High | Low | Yes | optional later | Parse publication dates after extraction | Already indirectly available often; avoid extra until needed |

## Top 10 New Candidates

1. `changedetection.io` — history/diff UX and source monitoring product patterns.
2. `ArchiveBox` — evidence bundle model.
3. `shot-scraper` — screenshot evidence inspiration.
4. `protego` — robots/access-policy reporting.
5. `w3lib` — URL/header utilities.
6. `inscriptis` — structure-preserving HTML-to-text fallback.
7. `OCRmyPDF` — scanned PDF path later.
8. `camelot` — PDF table extraction later.
9. `markitdown` — document-to-Markdown optional provider later.
10. `dateutil` — publication date parsing support.

## Genuinely Useful Improvements Inspired

- Add parser QA gate that checks status-label overclaims.
- Add rendered HTML/screenshot evidence fields for Playwright runs later.
- Add optional WARC capture path later, not core MVP.
- Add robots/access-policy reporting as an informational field, not a bypass.
- Add table/PDF extraction only after fixtures show need.
- Add URL canonicalization with explicit SSRF safety preserved.

## Overkill Or Should Not Be Used

- Full crawler frameworks (`Scrapy`, Crawlee, Browsertrix) are too heavy now.
- LLM/browser agents must not decide source changes.
- Legal NLP should not interpret obligations or make legal advice claims.
- Legacy pyppeteer/requests-html stack should remain rejected.

## Safety And Licensing Notes

- No code was copied.
- AGPL/GPL projects are research only unless counsel approves runtime obligations.
- External SaaS/provider tools should not receive regulator/customer source content by default.
- Anti-bot bypass, login bypass, CAPTCHA bypass, paywall bypass, and private portal scraping remain prohibited.
