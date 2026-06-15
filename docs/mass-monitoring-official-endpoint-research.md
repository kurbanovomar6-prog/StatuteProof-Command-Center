# Mass Monitoring Official Endpoint Research

Date: 2026-06-15

Scope: official or officially linked UAE regulatory/compliance endpoints only. This research used scoped public URL checks and `discover-source`; it did not run broad monitoring, save evidence, send alerts, or update `sources.json`.

## SCA

| Title | URL | Official Status | Type | Buyer Relevance | Adapter Needed | Parsing Risk | Priority | Action |
|---|---|---|---|---|---|---|---|---|
| Latest Regulations | `https://www.sca.gov.ae/en/regulations/regulations` | official | listing | Securities/regulatory changes | `sca_listing` | medium; short listing content | P0 | adapter-needed |
| AML/CFT | `https://www.sca.gov.ae/en/regulations/anti-money-laundering-and-terrorist-financing` | official | listing/page | MLRO AML/CFT relevance | `sca_listing` or static selector | medium; shallow content | P0 | adapter-needed |
| Circulars, Rules and Procedures | `https://www.sca.gov.ae/en/regulations/circulars-rules-and-procedures` | official | listing | circulars/rules are high-value compliance updates | `sca_listing` | medium; item-level extraction required | P0 | no-save-test-now |
| Market Rules Approved by SCA | `https://www.sca.gov.ae/en/regulations/market-rules-approved-by-sca` | official | listing | capital market compliance | `sca_listing` | medium | P1 | no-save-test-now |
| Digital Consultations | `https://www.sca.gov.ae/en/digital-participation/digital-consultations` | official | listing | consultations can matter to compliance/legal teams | listing | medium/high noise | P2 | adapter-needed |

Rejected / held:

- SCA About/Services/Home/Copyright/Digital Participation generic pages: official but low-value for default monitoring.
- SCA Open Data generic pages: held unless register/public-data relevance is explicit.

## DFSA

| Title | URL | Official Status | Type | Buyer Relevance | Adapter Needed | Parsing Risk | Priority | Action |
|---|---|---|---|---|---|---|---|---|
| AML/CTF Summary | `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/summary` | official | summary/listing | high MLRO relevance | `dfsa_notice_listing` | medium; link-heavy | P0 | no-save-test-now |
| Financial Crime Prevention Notices and MLRO Letters | `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters` | official | notice listing | direct MLRO relevance | `dfsa_notice_listing` | medium | P0 | no-save-test-now |
| DFSA Rulebook Modules | `https://dfsaen.thomsonreuters.com/rulebook/rulebook-modules` | officially linked / official rulebook platform | rulebook index | core rulebook monitoring | `dfsa_rulebook` / table | medium | P0 | no-save-test-now |
| DFSA AML Rulebook Module | `https://dfsaen.thomsonreuters.com/rulebook/anti-money-laundering-counter-terrorist-financing-and-sanctions-module-aml-ver3004-26` | officially linked / official rulebook platform | rulebook module | highest MLRO relevance | `dfsa_rulebook` or static selector | low/medium | P0 | no-save-test-now |
| Decision Notices and Regulatory Actions | `https://www.dfsa.ae/what-we-do/enforcement/regulatory-actions` | official | enforcement listing | enforcement monitoring | `dfsa_notice_listing` | medium | P1 | no-save-test-now |

Rejected / held:

- DFSA generic About/Board/CSR/Marketing pages: official but not default compliance monitoring sources.
- DFSA RSS: potentially useful, but held for later because content must be validated and mapped to relevant categories.

## CBUAE

| Title | URL | Official Status | Type | Buyer Relevance | Adapter Needed | Parsing Risk | Priority | Action |
|---|---|---|---|---|---|---|---|---|
| CBUAE Regulations | `https://www.centralbank.ae/en/our-operations/regulations/` | official | listing | core financial regulation | `cbuae_document_listing` | high; HTTP 403 in scoped checks | P0 | blocked |
| CBUAE Notices | `https://www.centralbank.ae/en/news-and-publications/notices/` | official | listing | notices/circulars | `cbuae_document_listing` | high; HTTP 403 in scoped checks | P1 | blocked |
| CBUAE Publications | `https://www.centralbank.ae/en/news-and-publications/publications/` | official | listing | publications/guidance | `cbuae_document_listing` | high; HTTP 403 in scoped checks | P1 | blocked |

Safe next action:

- Try only official robots/sitemap/document discovery and official alternate paths. Do not bypass WAF, CAPTCHA, login, or private APIs.

## ADGM / FSRA

| Title | URL | Official Status | Type | Buyer Relevance | Adapter Needed | Parsing Risk | Priority | Action |
|---|---|---|---|---|---|---|---|---|
| Financial and Cyber Crime Prevention | `https://www.adgm.com/operating-in-adgm/financial-and-cyber-crime-prevention` | official | content page | high MLRO relevance | `custom_element` | medium; custom element | P0 | save-baseline-if-no-save-still-passes |
| Rules and Regulations | `https://www.adgm.com/legal-framework/rules-and-regulations` | official | listing/content | FSRA rulebook relevance | `custom_element` / `adgm_fsra_listing` | medium | P0 | baseline-reconcile |

## VARA

| Title | URL | Official Status | Type | Buyer Relevance | Adapter Needed | Parsing Risk | Priority | Action |
|---|---|---|---|---|---|---|---|---|
| VARA Regulations old URL | `https://www.vara.ae/en/regulations/` | official domain but stale | unknown | VASP compliance | unknown | 404 | P0 | reject/stale |

Safe next action:

- Rediscover current VARA rulebook/framework URL from official site before no-save.

## UAE FIU / EOCN

| Title | URL | Official Status | Type | Buyer Relevance | Adapter Needed | Parsing Risk | Priority | Action |
|---|---|---|---|---|---|---|---|---|
| UAE FIU Publications | `https://www.uaefiu.gov.ae/en/Publications/` | official | listing | FIU/goAML guidance | `fiu_eocn_document_listing` | high; HTTP 403 in scoped checks | P0 | blocked |
| EOCN UN Page | `https://www.uaeiec.gov.ae/en-us/un-page` | official | sanctions/TFS table/listing | sanctions/TFS compliance | `table` or EOCN listing adapter | medium; multi-tab/table | P0 | no-save-test-now |
| EOCN Laws and Regulations Listing | `https://www.uaeiec.gov.ae/en-us/laws-regulations-listing` | official | law/document listing | AML/CFT/TFS legal framework | listing/document adapter | medium | P0 | no-save-test-now |
| EOCN Local Terrorist List tab | `https://www.uaeiec.gov.ae/en-us/un-page?p=1` | official | sanctions list/table | sanctions screening relevance | table/listing | medium | P0 | no-save-test-now |

## Queue Update Policy

Only strong official candidates from this research should be added to `product/regradar/config/mass_source_activation_queue.json`, inactive by default. They must remain `candidate`, `remediation`, or `blocked` until no-save, proof, repeat baseline, and agent gates pass.
