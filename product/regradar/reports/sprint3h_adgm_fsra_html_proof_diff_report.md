# Sprint 3H — ADGM/FSRA HTML Proof/Diff Validation Report

## 1. Verdict

- This was validation-only.
- No sources were activated.
- PDF scanning was avoided; PDF links were counted only.
- URLs tested: 4.
- Stable normalized HTML signatures: AML Framework consultation announcement, Staking of Virtual Assets final framework announcement, Cyber Risk Management framework announcement, FSRA Circulars listing page
- Future proof/diff candidates are listed below as candidates only, not active sources.
- Announcement pages are useful proof examples but are not ideal primary monitoring sources.

## 2. URL test results

| URL / short title | Type | HTTP status | Extracted HTML chars | Signature stable | PDF links | Proof quality | Monitoring suitability | Recommended next action |
| --- | --- | ---: | ---: | --- | ---: | --- | --- | --- |
| AML Framework consultation announcement (https://www.adgm.com/media/announcements/adgm-fsra-launches-consultation-on-enhancements-to-its-aml-framework) | consultation_announcement | 200 | 5357 | yes | 1 | strong | announcement_only_not_primary_source | Use as a source transparency/proof example; identify the underlying listing or rulebook source before monitored-source design. |
| Staking of Virtual Assets final framework announcement (https://www.adgm.com/media/announcements/adgm-fsra-finalises-regulatory-framework-for-the-staking-of-virtual-assets) | regulatory_framework_announcement | 200 | 5174 | yes | 1 | strong | announcement_only_not_primary_source | Use as a source transparency/proof example; identify the underlying listing or rulebook source before monitored-source design. |
| Cyber Risk Management framework announcement (https://www.adgm.com/media/announcements/adgms-fsra-issues-cyber-risk-management-framework) | guidance_announcement | 200 | 6239 | yes | 1 | strong | announcement_only_not_primary_source | Use as a source transparency/proof example; identify the underlying listing or rulebook source before monitored-source design. |
| FSRA Circulars listing page (https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities/supervision/circulars) | circular_listing | 200 | 5244 | yes | 1 | strong | suitable_listing_needs_row_extraction | Run HTML-only row-extraction validation to isolate dated circular items before any activation decision. |

## 3. Best candidates

HTML/source-transparency candidates:
- `https://www.adgm.com/media/announcements/adgm-fsra-launches-consultation-on-enhancements-to-its-aml-framework` — announcement_only_not_primary_source; candidate for future monitored source design only after upstream listing validation.
- `https://www.adgm.com/media/announcements/adgm-fsra-finalises-regulatory-framework-for-the-staking-of-virtual-assets` — announcement_only_not_primary_source; candidate for future monitored source design only after upstream listing validation.
- `https://www.adgm.com/media/announcements/adgms-fsra-issues-cyber-risk-management-framework` — announcement_only_not_primary_source; candidate for future monitored source design only after upstream listing validation.

Listing row-extraction candidates:
- `https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities/supervision/circulars` — ready for row-extraction validation.

## 4. Announcement-page limitation

ADGM/FSRA announcement pages are useful as examples and proof/diff candidates, but they may not be the best primary monitoring source because they are media announcements. The better primary source may be the FSRA circulars listing, public consultations listing, rulebook/listing pages, or row-level extraction from official listings.

## 5. PDF-deferred notes

PDF links were counted but not downloaded or parsed in this sprint.
- `https://www.adgm.com/media/announcements/adgm-fsra-launches-consultation-on-enhancements-to-its-aml-framework` — 1 PDF/document link(s) deferred.
- `https://www.adgm.com/media/announcements/adgm-fsra-finalises-regulatory-framework-for-the-staking-of-virtual-assets` — 1 PDF/document link(s) deferred.
- `https://www.adgm.com/media/announcements/adgms-fsra-issues-cyber-risk-management-framework` — 1 PDF/document link(s) deferred.
- `https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities/supervision/circulars` — 1 PDF/document link(s) deferred.

## 6. Recommended Sprint 3I

Sprint 3I should validate FSRA circular listing row extraction, HTML-only. Do not activate the source until row extraction, proof/diff output, and limitation notes are tested.
