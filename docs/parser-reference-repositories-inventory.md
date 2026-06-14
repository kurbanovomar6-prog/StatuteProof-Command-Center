# Parser Reference Repositories Inventory

Date: 2026-06-14

Research folder: `.reference_parser_repos/`
Git status: ignored by `.gitignore`; do not commit or vendor into runtime.

Rules followed: shallow clone/fetch only, no installs, no third-party code execution, no product runtime vendoring.

## Summary

- Known repos requested: 36
- Successfully cloned/updated locally: 24
- Not cloned/updated: 12
- Local clone failures/interruptions are documented below; product work does not depend on these local copies.

## Inventory

| Repo URL | Local path | Cloned? | Clone/update status | Purpose | Status | Idea we use | What not to copy | License file found | Adopt now/later/reject | Dependency risk |
|---|---|---:|---|---|---|---|---|---:|---|---|
| https://github.com/microsoft/playwright-python | `.reference_parser_repos/microsoft__playwright-python` | yes | cloned/updated | Browser rendering | ACTIVE CORE | Wait selectors, browser lifecycle, strict timeouts | Do not bypass access controls or emulate humans to defeat protections | yes | Already dependency | Medium |
| https://github.com/apify/crawlee-python | `.reference_parser_repos/apify__crawlee-python` | yes | cloned/updated | Crawler architecture | RESEARCH ONLY | Request/session patterns and queue concepts | Do not add crawler framework now | yes | Later | High |
| https://github.com/browser-use/browser-use | `.reference_parser_repos/browser-use__browser-use` | yes | cloned/updated | Browser automation reference | RESEARCH ONLY | Browser context discipline | Do not add LLM browser agent for change decisions | yes | Reject runtime | High |
| https://github.com/adbar/trafilatura | `.reference_parser_repos/adbar__trafilatura` | yes | cloned/updated | Main-content extraction | ACTIVE CORE | Keep semantic extraction/provider report | Do not copy internals; use package | yes | Already dependency | Low |
| https://github.com/buriy/python-readability | `.reference_parser_repos/buriy__python-readability` | yes | cloned/updated | Readability fallback | ACTIVE FALLBACK | Fallback article extraction | Do not rely on it alone for regulator pages | yes | Already dependency equivalent | Medium |
| https://github.com/rushter/selectolax | `.reference_parser_repos/rushter__selectolax` | yes | cloned/updated | Fast selector extraction | ACTIVE FALLBACK | Explicit selector extraction | Do not require C-extension for all deploys without fallback | yes | Later/optional | Medium |
| https://github.com/lxml/lxml | `.reference_parser_repos/lxml__lxml` | yes | cloned/updated | HTML/XML parsing | ACTIVE CORE | Existing dependency through readability/trafilatura stack | Do not hand-roll parser internals | yes | Already dependency | Medium |
| https://github.com/chatnoir-eu/chatnoir-resiliparse | `.reference_parser_repos/chatnoir-eu__chatnoir-resiliparse` | yes | cloned/updated | Boilerplate removal | RESEARCH ONLY | Link-density/content-density ideas | Do not add C/Rust-heavy parser now | yes | Later | Medium |
| https://github.com/miso-belica/jusText | `.reference_parser_repos/miso-belica__jusText` | yes | cloned/updated | Boilerplate removal | ACTIVE FALLBACK | Stopword/boilerplate heuristics | Do not make it default without UAE fixtures | no | Later | Low |
| https://github.com/scrapy/extruct | `.reference_parser_repos/scrapy__extruct` | no | not completed | Metadata extraction | ACTIVE FALLBACK | JSON-LD/microdata extraction | Do not add as hard dependency until tested | no | Later | Low |
| https://github.com/pymupdf/PyMuPDF | `.reference_parser_repos/pymupdf__PyMuPDF` | no | not completed | PDF extraction | ACTIVE CORE | PDF text/page metadata | Do not copy AGPL/proprietary-adjacent code; use package/license carefully | no | Already dependency | Medium |
| https://github.com/jsvine/pdfplumber | `.reference_parser_repos/jsvine__pdfplumber` | yes | cloned/updated | PDF/table extraction | ACTIVE FALLBACK | Table-aware extraction path | Do not parse tables into legal conclusions | yes | Already dependency | Medium |
| https://github.com/py-pdf/pypdf | `.reference_parser_repos/py-pdf__pypdf` | no | not completed | PDF fallback | ACTIVE FALLBACK | Text fallback, page count | Do not rely on pypdf for scanned PDFs | no | Already dependency | Low |
| https://github.com/pdfminer/pdfminer.six | `.reference_parser_repos/pdfminer__pdfminer.six` | yes | cloned/updated | PDF text extraction | ACTIVE FALLBACK | Low-level fallback concepts | Do not add direct dependency unless needed | yes | Later | Medium |
| https://github.com/adbar/htmldate | `.reference_parser_repos/adbar__htmldate` | yes | cloned/updated | Publication date | ACTIVE FALLBACK | Extract source publication date | Do not treat guessed date as official timestamp | yes | Optional later | Low |
| https://github.com/adbar/courlan | `.reference_parser_repos/adbar__courlan` | yes | cloned/updated | URL canonicalization | ACTIVE FALLBACK | Canonical URL and validation | Do not replace SSRF checks with URL cleaning only | yes | Optional later | Low |
| https://github.com/seperman/deepdiff | `.reference_parser_repos/seperman__deepdiff` | yes | cloned/updated | Structured diff | ACTIVE FALLBACK | JSON/provider report diffs | Do not use for text change decision path | yes | Optional later | Low |
| https://github.com/webrecorder/warcio | `.reference_parser_repos/webrecorder__warcio` | yes | cloned/updated | WARC evidence | OPTIONAL PROVIDER | Optional WARC capture for proof bundle | Do not add WARC as required MVP dependency | yes | Later | Medium |
| https://github.com/opentimestamps/opentimestamps-client | `.reference_parser_repos/opentimestamps__opentimestamps-client` | yes | cloned/updated | External timestamping | OPTIONAL PROVIDER | Optional hash timestamping | Do not block core evidence on external network | yes | Later | Medium |
| https://github.com/scrapy/scrapy | `.reference_parser_repos/scrapy__scrapy` | yes | cloned/updated | Crawler framework | RESEARCH ONLY | Robust downloader/settings ideas | Do not migrate to Scrapy now | yes | Reject runtime now | High |
| https://github.com/mendableai/firecrawl | `.reference_parser_repos/mendableai__firecrawl` | yes | cloned/updated | Web-to-markdown service/provider | OPTIONAL PROVIDER | Provider abstraction inspiration | Do not send regulated source content to third-party service by default | yes | Later/reject default | High |
| https://github.com/us/crw | `.reference_parser_repos/us__crw` | yes | cloned/updated | Crawl/reference | RESEARCH ONLY | Small crawler concepts if relevant | Do not adopt without license/depth review | yes | Research only | Medium |
| https://github.com/unclecode/crawl4ai | `.reference_parser_repos/unclecode__crawl4ai` | yes | cloned/updated | Browser/markdown extraction | OPTIONAL PROVIDER | Existing opt-in provider can remain optional | Do not make AI/markdown crawler default | yes | Optional later | High |
| https://github.com/webrecorder/browsertrix-crawler | `.reference_parser_repos/webrecorder__browsertrix-crawler` | yes | cloned/updated | Browser WARC crawler | OPTIONAL PROVIDER | Rendered capture/evidence model | Do not add containerized crawler now | yes | Later | High |
| https://github.com/Unstructured-IO/unstructured | `.reference_parser_repos/Unstructured-IO__unstructured` | yes | cloned/updated | Document parsing | OPTIONAL PROVIDER | Partitioning concepts for PDFs/HTML | Do not add heavy dependency now | no | Later | High |
| https://github.com/docling-project/docling | `.reference_parser_repos/docling-project__docling` | no | not completed | Document parsing | OPTIONAL PROVIDER | Document structure extraction | Do not add heavy dependency now | no | Later | High |
| https://github.com/mherrmann/helium | `.reference_parser_repos/mherrmann__helium` | no | not completed | Browser automation | RESEARCH ONLY | Simple browser automation ideas | Do not replace Playwright | no | Reject default | Medium |
| https://github.com/pyppeteer/pyppeteer | `.reference_parser_repos/pyppeteer__pyppeteer` | no | not completed | Legacy browser automation | REJECTED FOR NOW | Legacy reference only | Do not adopt deprecated/older browser stack | no | Reject | High |
| https://github.com/psf/requests-html | `.reference_parser_repos/psf__requests-html` | no | not completed | Legacy requests+JS | REJECTED FOR NOW | Historical reference only | Do not add pyppeteer-backed legacy stack | no | Reject | High |
| https://github.com/vercel-labs/skills | `.reference_parser_repos/vercel-labs__skills` | no | not completed | Skill references | RESEARCH ONLY | Skill packaging patterns | Do not import broad packs blindly | no | Research only | Low |
| https://github.com/coreyhaines31/marketingskills | `.reference_parser_repos/coreyhaines31__marketingskills` | no | not completed | Marketing skill references | RESEARCH ONLY | Copy skill ideas | Do not let marketing copy overclaim product | no | Research only | Low |
| https://github.com/hardikpandya/stop-slop | `.reference_parser_repos/hardikpandya__stop-slop` | no | not completed | Anti-slop writing | RESEARCH ONLY | Plain-language checks | Do not import without review | no | Research only | Low |
| https://github.com/nextlevelbuilder/ui-ux-pro-max-skill | `.reference_parser_repos/nextlevelbuilder__ui-ux-pro-max-skill` | no | not completed | UI/UX skill reference | RESEARCH ONLY | UI review concepts | Do not affect parser runtime | no | Research only | Low |
| https://github.com/emilkowalski/skill | `.reference_parser_repos/emilkowalski__skill` | no | not completed | Design skill reference | RESEARCH ONLY | Taste/design inspiration | Do not affect parser runtime | no | Research only | Low |
| https://github.com/pbakaus/impeccable | `.reference_parser_repos/pbakaus__impeccable` | no | not completed | Design quality reference | RESEARCH ONLY | Quality critique concepts | Do not affect parser runtime | no | Research only | Low |
| https://github.com/leonxlnx/taste-skill | `.reference_parser_repos/leonxlnx__taste-skill` | no | not completed | Design taste reference | RESEARCH ONLY | Skill wording concepts | Do not affect parser runtime | no | Research only | Low |

## Immediate Adoption Decision

No third-party code should be copied. StatuteProof should keep using dependencies through package APIs and adopt only small design ideas:

- explicit provider result objects,
- graceful unavailable-dependency warnings,
- rendered HTML/screenshot/WARC as optional evidence paths,
- stricter source readiness gates,
- table/PDF metadata later.
