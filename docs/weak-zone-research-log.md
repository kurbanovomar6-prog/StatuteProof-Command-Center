# Weak-Zone Research Log

Date: 2026-06-16

## Official Endpoint Research

| Source | Type | Finding | Adopted | Risk | Implementation note |
| --- | --- | --- | --- | --- | --- |
| [VARA Rulebook Updates](https://rulebooks.vara.ae/view-revision-updates?f_days=onchanged%3D-30+day) | official | `rulebooks.vara.ae` exposes rulebook update listings with dated entries, avoiding the stale `vara.ae` framework landing page. | yes | low-medium, must avoid noisy update feeds | Test as VARA revision/update listing with document/listing adapter. |
| [VARA AML/CFT Controls](https://rulebooks.vara.ae/rulebook/c-amlcft-controls) | official | Public HTML rulebook section for AML/CFT controls. | yes | medium, may be narrow section not full rulebook | Test as rulebook/static document source. |
| [VARA Compliance and Risk Management Rulebook](https://rulebooks.vara.ae/rulebook/compliance-and-risk-management-rulebook) | official | Public HTML rulebook page with rulebook navigation and text. | yes | medium, nav/sidebar noise must be filtered | Test with rulebook/static/listing adapters. |
| [VARA Virtual Assets and Related Activities Regulations PDF](https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_18_VER992_2.pdf) | official PDF | Official PDF document from VARA rulebooks file store. | yes | low, direct PDF monitoring may be stable but document-level only | Test direct PDF extraction and evidence. |
| [VARA Technology and Information Rulebook PDF](https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_169_VER20250519.pdf) | official PDF | Official VARA rulebook PDF from file store. | yes | low | Test as direct PDF source. |
| [VARA Virtual Asset Issuance Rulebook PDF](https://rulebooks.vara.ae/sites/default/files/en_net_file_store/VARA_EN_293_VER20250519.pdf) | official PDF | Official VARA activity-specific rulebook PDF. | yes | low | Test as direct PDF source. |
| [CBUAE Rulebook AML/CFT](https://rulebook.centralbank.ae/en/rulebook/amlcft) | official | CBUAE rulebook has public AML/CFT page and section links. | yes | low-medium, rulebook nav may need filtering | Test CBUAE rulebook source. |
| [CBUAE Entire Section](https://rulebook.centralbank.ae/en/entiresection/644) | official | Central Bank rulebook provides entire-section view. | yes | medium, section id may change | Test as document/listing/static source. |
| [CBUAE Retail Payment Services Rulebook](https://rulebook.centralbank.ae/en/rulebook/312-retail-payment-services-and-card-schemes-regulation) | official | Public CBUAE rulebook page for payment services and AML/CFT obligations. | yes | low-medium | Test as rulebook/static source. |
| [DFSA Consultation Papers](https://www.dfsa.ae/your-resources/regulatory/consultation-papers) | official | Current official DFSA consultation page differs from old `/publications/consultation-papers` path. | yes | medium, may still render JS/nav shell | Test current URL and official-linked Thomson Reuters pages. |
| [DFSA Regulatory Actions](https://www.dfsa.ae/what-we-do/enforcement/regulatory-actions) | official | Official enforcement page exists but search preview showed nav-heavy output. | yes | medium, needs selector or alternate document source | Retest with current adapters and classify honestly. |
| [DFSA Thomson Reuters Consultation Paper No.165](https://dfsaen.thomsonreuters.com/rulebook/consultation-paper-no165-proposed-changes-dfsas-approach-licensed-functions-and-authorised) | officially linked rulebook | Thomson Reuters rulebook pages expose DFSA consultation content and attachments. | yes | medium, officially linked status must be retained | Test as DFSA rulebook/document listing source. |

## Open-Source / Package Technique Research

| Source | Type | License | Finding | Adopt now/later/reject | Risk | Implementation note |
| --- | --- | --- | --- | --- | --- | --- |
| [Playwright Python network docs](https://playwright.dev/python/docs/network) | package docs | Apache-2.0 project | Playwright supports request/response observation and response body inspection for public XHR discovery. | later | low, but keep scoped and no private endpoints | Use only for targeted DOM/XHR inspection when static selectors fail. |
| [Scrapy docs](https://docs.scrapy.org/) | package docs | BSD | Link extraction and sitemap handling patterns are mature. | later | dependency weight if added | Do not add now; independent sitemap/link discovery already exists. |
| [trafilatura](https://trafilatura.readthedocs.io/) | package docs | Apache-2.0 | Strong article extraction and boilerplate removal ideas. | later | may over-strip regulatory tables/listings | Keep current adapter-first approach; consider as optional fallback only. |
| [changedetection.io](https://github.com/dgtlmoon/changedetection.io) | GitHub | Apache-2.0 | Good conceptual patterns for filters, visual selectors, and notification suppression. | later | full system too broad to vendor | Use as design inspiration for noise controls only; no code copied. |

## Research Decision

The next execution should prioritize official alternate endpoints, not new dependencies:

1. Direct VARA rulebook pages/PDFs under `rulebooks.vara.ae`.
2. CBUAE rulebook pages under `rulebook.centralbank.ae`.
3. Current DFSA official consultation path and official-linked Thomson Reuters consultation pages.
4. ADGM/DIFC replacement URLs only after high-yield rulebook/document endpoints are tested.
