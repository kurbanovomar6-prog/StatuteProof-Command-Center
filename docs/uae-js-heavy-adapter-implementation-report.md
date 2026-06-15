# UAE JS-Heavy Adapter Implementation Report

Date: 2026-06-15

## Implementation Summary

This sprint improved the existing source activation platform rather than adding a new broad crawler.

Code changes:

| File | Change |
| --- | --- |
| `product/regradar/app/scraper.py` | Added a Playwright `page.content()` retry path for navigation/rerender races. |
| `product/regradar/app/source_intake.py` | Allowed two-item document/PDF listing adapters to count as structured adapter content when normalized chars are substantial. |
| `product/regradar/app/adapters/adapter_platform.py` | Preserved item context snippets in normalized listing output so FIU document listings carry meaningful descriptions, not only titles/URLs. |
| `product/regradar/app/source_quality.py` | Expanded regulatory density terms for AML/FIU/TFS typology/report language. |

## Why These Changes Were Needed

UAE FIU and SCA pages are JS-heavy. The prior failure mode was often not "no content exists"; it was:

- rendered page still changing while Playwright attempted `page.content()`;
- two-document FIU legal listings being treated as too small to be structured;
- document listing context being discarded before quality scoring;
- AML/FIU typology vocabulary not contributing enough to regulatory density.

## Adapter Families Affected

| Adapter family | Status |
| --- | --- |
| `fiu_eocn_document_listing` | Improved indirectly through context preservation and quality/risk scoring. |
| `sca_listing` | Improved indirectly through Playwright content retry. Existing active SCA circulars source retested successfully. |
| `custom_element` | No regression found in targeted tests. Existing ADGM `adgm-page` sources remain supported. |

## Limitations

- No new unsafe dependency was added.
- No source was activated from no-save alone.
- UAE FIU hub and annual-report variants were not activated because they duplicate the typology page hash/content.
- SCA regulations-listing and ADGM alternate-component sources remain remediation.
