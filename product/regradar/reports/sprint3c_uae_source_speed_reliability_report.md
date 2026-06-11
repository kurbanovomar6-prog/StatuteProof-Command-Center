# Sprint 3C — UAE Source Speed & Reliability Validation

## 1. Verdict

- This was validation-only.
- No sources were activated.
- No source configuration, source monitoring behavior, adapters, API behavior, or frontend files were changed.
- Candidates tested: 15.
- Basic accessibility pass: 11.
- Blocked or WAF-like responses: 4.
- PDF validation needed: 4.
- JS rendering signals observed: 7.
- Safest later-activation candidates are listed below, but none should be activated without a separate approval sprint.

## 2. Summary table

| Candidate ID | Source layer | URL | HTTP status | Response time | Extracted chars | PDF links | JS signals | WAF/blocked | Recommended next status |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- |
| `ae-cbuae-main-publications` | CBUAE main regulatory publications | https://www.centralbank.ae/ | 403 | 267 ms | 16 | no | yes | yes | needs_waf_workaround |
| `ae-cbuae-rulebook` | CBUAE Rulebook | https://rulebook.centralbank.ae/ | 200 | 2056 ms | 2193 | yes | no | no | validation_pass_candidate |
| `ae-cbuae-payments` | CBUAE payment systems and retail payment services | https://www.centralbank.ae/ | 403 | 65 ms | 16 | no | yes | yes | needs_waf_workaround |
| `ae-vara-main-publications` | VARA main publications | https://www.vara.ae/ | 200 | 389 ms | 4107 | yes | yes | no | needs_pdf_validation |
| `ae-vara-rulebooks` | VARA rulebooks | https://www.vara.ae/ | 200 | 722 ms | 4107 | yes | yes | no | needs_pdf_validation |
| `ae-dfsa-rulebook` | DFSA Rulebook | https://www.dfsa.ae/ | 200 | 4765 ms | 6610 | no | no | no | validation_pass_candidate |
| `ae-difc-laws` | DIFC Laws | https://www.difc.com/business/laws-and-regulations/ | 200 | 772 ms | 5956 | yes | yes | no | validation_pass_candidate |
| `ae-adgm-fsra-main` | ADGM/FSRA main regulatory publications | https://www.adgm.com/financial-services-regulatory-authority | 200 | 745 ms | 10934 | no | no | no | validation_pass_candidate |
| `ae-adgm-fsra-rulebook` | ADGM/FSRA rulebook | https://www.adgm.com/financial-services-regulatory-authority | 200 | 1609 ms | 10934 | no | no | no | validation_pass_candidate |
| `ae-uaefiu-publications` | UAE FIU publications and typologies | https://www.uaefiu.gov.ae/ | 403 | 530 ms | 16 | no | yes | yes | needs_waf_workaround |
| `ae-fta-legislation` | FTA legislation | https://tax.gov.ae/ | 200 | 3469 ms | 13519 | no | no | no | validation_pass_candidate |
| `ae-sca-cma-regulations-circulars` | SCA / CMA regulations and circulars | https://www.sca.gov.ae/ | 200 | 2323 ms | 6624 | no | no | no | validation_pass_candidate |
| `ae-uae-legislation-federal-laws` | UAE Legislation Portal federal laws and decrees | https://uaelegislation.gov.ae/ | 403 | 69 ms | 16 | no | yes | yes | needs_waf_workaround |
| `ae-moet-aml-dnfbp` | Ministry of Economy AML / DNFBP guidance | https://www.moet.gov.ae/en/ | 200 | 1969 ms | 12003 | no | no | no | validation_pass_candidate |
| `ae-eocn-sanctions` | Executive Office targeted financial sanctions materials | https://www.uaeiec.gov.ae/en-us | 200 | 3684 ms | 3514 | no | no | no | validation_pass_candidate |

## 3. Best candidates for later activation

- `ae-adgm-fsra-main` — ADGM/FSRA main regulatory publications: HTTP 200, 745 ms, 10934 extracted chars. Next step: repeated-run and item-level validation.
- `ae-difc-laws` — DIFC Laws: HTTP 200, 772 ms, 5956 extracted chars. Next step: repeated-run and item-level validation.
- `ae-adgm-fsra-rulebook` — ADGM/FSRA rulebook: HTTP 200, 1609 ms, 10934 extracted chars. Next step: repeated-run and item-level validation.
- `ae-moet-aml-dnfbp` — Ministry of Economy AML / DNFBP guidance: HTTP 200, 1969 ms, 12003 extracted chars. Next step: repeated-run and item-level validation.
- `ae-cbuae-rulebook` — CBUAE Rulebook: HTTP 200, 2056 ms, 2193 extracted chars. Next step: repeated-run and item-level validation.
- `ae-sca-cma-regulations-circulars` — SCA / CMA regulations and circulars: HTTP 200, 2323 ms, 6624 extracted chars. Next step: repeated-run and item-level validation.
- `ae-fta-legislation` — FTA legislation: HTTP 200, 3469 ms, 13519 extracted chars. Next step: repeated-run and item-level validation.
- `ae-eocn-sanctions` — Executive Office targeted financial sanctions materials: HTTP 200, 3684 ms, 3514 extracted chars. Next step: repeated-run and item-level validation.

## 4. Sources requiring adapters or workarounds

### PDF validation needed

- `ae-vara-main-publications` — VARA main publications: HTML is accessible but PDF dependency should be validated before monitoring. Redirected to https://www.vara.ae/en/
- `ae-vara-rulebooks` — VARA rulebooks: HTML is accessible but PDF dependency should be validated before monitoring. Redirected to https://www.vara.ae/en/

### JS rendering needed

- `ae-cbuae-main-publications` — CBUAE main regulatory publications: Blocked or WAF-like response detected during basic HTTP check.
- `ae-cbuae-payments` — CBUAE payment systems and retail payment services: Blocked or WAF-like response detected during basic HTTP check.
- `ae-vara-main-publications` — VARA main publications: HTML is accessible but PDF dependency should be validated before monitoring. Redirected to https://www.vara.ae/en/
- `ae-vara-rulebooks` — VARA rulebooks: HTML is accessible but PDF dependency should be validated before monitoring. Redirected to https://www.vara.ae/en/
- `ae-difc-laws` — DIFC Laws: Accessible via basic HTTP and produced usable extracted text. Redirected to https://www.difc.com/business/laws-and-regulations
- `ae-uaefiu-publications` — UAE FIU publications and typologies: Blocked or WAF-like response detected during basic HTTP check. Redirected to https://uaefiu.gov.ae/
- `ae-uae-legislation-federal-laws` — UAE Legislation Portal federal laws and decrees: Blocked or WAF-like response detected during basic HTTP check.

### WAF workaround needed

- `ae-cbuae-main-publications` — CBUAE main regulatory publications: Blocked or WAF-like response detected during basic HTTP check.
- `ae-cbuae-payments` — CBUAE payment systems and retail payment services: Blocked or WAF-like response detected during basic HTTP check.
- `ae-uaefiu-publications` — UAE FIU publications and typologies: Blocked or WAF-like response detected during basic HTTP check. Redirected to https://uaefiu.gov.ae/
- `ae-uae-legislation-federal-laws` — UAE Legislation Portal federal laws and decrees: Blocked or WAF-like response detected during basic HTTP check.

### Manual mapping needed

- `ae-vara-main-publications` — VARA main publications: HTML is accessible but PDF dependency should be validated before monitoring. Redirected to https://www.vara.ae/en/
- `ae-vara-rulebooks` — VARA rulebooks: HTML is accessible but PDF dependency should be validated before monitoring. Redirected to https://www.vara.ae/en/

### Blocked or avoid for now

- None identified in this validation pass.

## 5. Network / reliability notes

- Slow responses at or above 5 seconds: 0.
- Redirects observed: 7.
- Very low extracted text results: 4.
- Pages with low or unknown item-level potential: 4.
- Redirect candidates: `ae-cbuae-rulebook`, `ae-vara-main-publications`, `ae-vara-rulebooks`, `ae-difc-laws`, `ae-uaefiu-publications`, `ae-fta-legislation`, `ae-sca-cma-regulations-circulars`.
- Low-text candidates: `ae-cbuae-main-publications`, `ae-cbuae-payments`, `ae-uaefiu-publications`, `ae-uae-legislation-federal-laws`.

## 6. Recommended Sprint 3D

Run a disabled-candidate planning pass for the cleanest 3–5 validation-pass candidates, then run repeated checks before any activation decision.

Do not move any candidate into active monitoring during Sprint 3D.
