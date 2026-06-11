# Sprint 3F — ADGM/FSRA HTML Item-Level Validation Report

## 1. Verdict

- This was validation-only.
- No sources were activated.
- PDF scanning was avoided; PDF links were counted only.
- ADGM/FSRA discovered HTML item-level candidates: 3.
- Item-level URLs tested repeatedly: 3.
- HTML item-level monitoring potential: 0 candidate(s) ready for proof/diff test.

## 2. Discovered HTML item-level candidates

| Item title | Item URL | Item type | HTTP status | Extracted HTML chars | PDF links present | PDF parsed? | Item-level confidence | Notes |
| --- | --- | --- | ---: | ---: | --- | --- | --- | --- |
| Financial Services Regulatory Authority (FSRA) \| ADGM | https://www.adgm.com/financial-services-regulatory-authority | unknown | 200 | 10934 | no | No | medium | Official ADGM HTML page with useful text but item type or depth remains uncertain. |
| Abu Dhabi's International Financial Centre \| ADGM | https://www.adgm.com/media/publications | unknown | 200 | 9160 | no | No | medium | Official ADGM HTML page with useful text but item type or depth remains uncertain. |
| FSRA Connect | https://www.adgm.com/operating-in-adgm/e-services/fsra-connect | unknown | 200 | 4404 | no | No | medium | Official ADGM HTML page with useful text but item type or depth remains uncertain. |

## 3. Repeated-run results

| Item URL | Runs passed | Status stable | Title stable | HTML content signature stable | PDF link count stable | Suitability verdict |
| --- | ---: | --- | --- | --- | --- | --- |
| https://www.adgm.com/financial-services-regulatory-authority | 3/3 | yes | yes | yes | yes | needs_manual_mapping |
| https://www.adgm.com/media/publications | 3/3 | yes | yes | yes | yes | needs_manual_mapping |
| https://www.adgm.com/operating-in-adgm/e-services/fsra-connect | 3/3 | yes | yes | yes | yes | needs_manual_mapping |

## 4. Best ADGM/FSRA HTML candidates for future proof/diff test

- None. No ADGM/FSRA HTML item should move to proof/diff test from this run.

## 5. PDF-deferred candidates

- None.

## 6. Limitations

- PDF content was intentionally not scanned.
- HTML-only validation may miss document text inside PDFs.
- Rulebook pages may require a separate item-level adapter later.
- Generic listing pages are not enough for customer-ready monitoring.
- Item-level discovery is incomplete and limited to a small, conservative crawl.

## 7. Recommended Sprint 3G

Run ADGM/FSRA HTML proof/diff testing for the best 1-3 HTML item-level URLs only after this validation identifies stable, useful pages. Do not move to source activation until proof/diff output is tested.
