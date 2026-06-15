# UAE JS-Heavy DOM/XHR Investigation Report

Date: 2026-06-15

## Scope

This sprint did not run a new broad discovery crawl. It focused on JS-heavy official UAE endpoints already found in the 151-endpoint discovery sprint, especially UAE FIU, SCA, and ADGM alternate-component pages.

## UAE FIU Findings

Primary tested URLs:

| Source ID | URL | Result | Selector/strategy |
| --- | --- | --- | --- |
| `AE-uaefiu-typology-reports` | `https://uaefiu.gov.ae/en/more/knowledge-centre/publications/trends-typology-reports/` | Strong pass | Playwright render, `fiu_eocn_document_listing`, `container_selector=body` |
| `AE-uaefiu-publications-hub` | `https://uaefiu.gov.ae/en/more/knowledge-centre/publications/` | Hold | Same normalized hash/content as typology listing; duplicate variant risk |
| `AE-uaefiu-annual-reports` | `https://uaefiu.gov.ae/en/more/knowledge-centre/publications/annual-report/` | Hold | Same normalized hash/content as typology listing; duplicate variant risk |
| `AE-uaefiu-aml-cft-laws` | `https://uaefiu.gov.ae/en/more/knowledge-centre/aml-cft-laws-related-decisions/` | Hold | PDF listing rendered, but q=59, below activation threshold |

Observed behavior:

- Direct `requests` fetch returns HTTP 403 for FIU knowledge-centre pages.
- Playwright render succeeds on public pages without bypassing login, CAPTCHA, paywall, or private portal controls.
- The typology page produces about 190,250 raw rendered chars, 6,289 normalized chars after generic CTA/context filtering, 30 document/listing items, and a stable normalized hash.
- The publications hub and annual reports paths currently resolve to the same extracted document listing hash as the typology page. They were not activated to avoid duplicate source inflation.

## SCA Findings

Primary tested URLs:

| Source ID | URL | Result | Selector/strategy |
| --- | --- | --- | --- |
| `AE-sca-circulars-rules-procedures` | `https://www.sca.gov.ae/en/regulations/circulars-rules-and-procedures` | Strong pass, already active | Playwright render, `sca_listing` |
| `AE-sca-regulations-listing` | SCA regulations listing URL from discovery | Hold | Still returns nav/filter shell with no stable item extraction |

Observed behavior:

- The Playwright content retry fixed an intermittent page-content race during SCA rendering.
- The known SCA circulars/rules/procedures source retested at q=62 with stable item extraction, confirming the existing active source path.
- SCA filter/listing pages still need deeper ASP.NET/listing selectors or network endpoint isolation before new SCA sources can activate.

## ADGM Alternate Components

Primary tested groups:

- ADGM media/announcements.
- ADGM data protection guidance/enforcement pages.

Observed behavior:

- Existing `adgm-page` custom-element extraction remains valid for prior ADGM/FSRA sources.
- Media/announcements and some data-protection pages did not expose the same component in the current no-save retest path and remained nav-shell/empty extraction holds.
- No ADGM alternate-component source was activated in this sprint.

## Selector Decisions

| Group | wait_selector | content_selector | item_selector | Decision |
| --- | --- | --- | --- | --- |
| UAE FIU typology | Playwright default | `body` | document/PDF links from FIU/EOCN adapter | Use for typology reports only |
| UAE FIU AML laws | Playwright default / `main` | `main` or `body` | PDF links | Hold at q=59 |
| SCA circulars | Playwright default | `body` | `.aegov-card, article, li, tr, .card, .item, a[href]` | Already active; confirms adapter path |
| ADGM media/data protection | unresolved | unresolved | unresolved | Hold remediation |

## Remaining DOM/XHR Blockers

- UAE FIU pages can be rendered, but duplicate route variants must be de-duplicated by normalized hash before activation.
- SCA filter pages still require source-specific item selectors or XHR endpoint discovery.
- ADGM alternate components need a selector map beyond `adgm-page`.
- CBUAE/DFSA/DIFC were not remediated in this sprint; prior blocked/access-health statuses remain.
