# VARA PDF / DOM Investigation Report

Date: 2026-06-16

## Finding

The strongest remediation path is `rulebooks.vara.ae`, not stale `www.vara.ae/en/regulatory-framework/...` paths.

## Page-Level No-Save Results

| Source ID | URL | Status | Quality | Length | PDF links | Decision |
| --- | --- | --- | ---: | ---: | ---: | --- |
| `AE-vara-company-rulebook-direct` | `https://rulebooks.vara.ae/rulebook/company-rulebook` | CONFIRMED_ACCESSIBLE | 62 | 1,726 | 4 | Passed no-save; direct PDF held by quality gate. |
| `AE-vara-compliance-risk-rulebook` | `https://rulebooks.vara.ae/rulebook/compliance-and-risk-management-rulebook` | CONFIRMED_ACCESSIBLE | 62 | 1,749 | 3 | Passed no-save. |
| `AE-vara-custody-services-rulebook` | `https://rulebooks.vara.ae/rulebook/custody-services-rulebook` | CONFIRMED_ACCESSIBLE | 62 | 1,031 | 4 | Passed page no-save; direct PDF held by quality gate. |
| `AE-vara-exchange-services-rulebook` | `https://rulebooks.vara.ae/rulebook/exchange-services-rulebook` | CONFIRMED_ACCESSIBLE | 62 | 1,168 | 4 | Passed page no-save; direct PDF held by quality gate. |
| `AE-vara-va-regulations-2023` | `https://rulebooks.vara.ae/rulebook/virtual-assets-and-related-activities-regulations-2023` | CONFIRMED_ACCESSIBLE | 62 | 1,446 | 6 | Passed no-save. |

Several activity-rulebook HTML paths produced nav-shell or shallow output, but exposed official current-version PDF URLs.

## Direct PDF No-Save Results

| Source ID | Quality | Length | `can_save_evidence` | Decision |
| --- | ---: | ---: | --- | --- |
| `AE-vara-compliance-risk-rulebook-pdf` | 61 | 119,899 | true | Activate after proof/baseline/gates. |
| `AE-vara-technology-information-rulebook-pdf` | 61 | 59,120 | true | Activate after proof/baseline/gates. |
| `AE-vara-va-issuance-rulebook-pdf` | 61 | 95,194 | true | Activate after proof/baseline/gates. |
| `AE-vara-broker-dealer-rulebook-pdf` | 60 | 47,969 | true | Activate after proof/baseline/gates. |
| `AE-vara-lending-borrowing-rulebook-pdf` | 60 | 23,092 | true | Activate after proof/baseline/gates. |
| `AE-vara-va-regulations-2023-pdf` | 61 | 87,988 | true | Activate after proof/baseline/gates. |
| `AE-vara-company-rulebook-pdf` | 59 | 117,212 | false | Hold; accessible but below strict gate. |
| `AE-vara-custody-services-rulebook-pdf` | 59 | 57,712 | false | Hold; accessible but below strict gate. |
| `AE-vara-exchange-services-rulebook-pdf` | 58 | 79,202 | false | Hold; accessible but below strict gate. |
| `AE-vara-market-conduct-rulebook-pdf` | 58 | 35,884 | false | Hold; accessible but below strict gate. |

## Parser Finding

Before the fix, direct PDF Source Lab normalized raw `%PDF-1.7` bytes instead of extracted text. The parser now uses `document_extractor.fetch_document()` and `extract_pdf_text()` for direct PDF sources.
