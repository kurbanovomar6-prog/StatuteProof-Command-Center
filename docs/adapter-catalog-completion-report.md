# Adapter Catalog Completion Report

Date: 2026-06-15

## Summary

The adapter catalog is now broader and more explicit. It remains dependency-light and does not replace evidence/baseline gates.

## Adapter Families Present

1. `static_html`
2. `playwright_selector`
3. `custom_element`
4. `listing`
5. `table`
6. `pdf_document`
7. `pdf_listing`
8. `dfsa_rulebook`
9. `register`
10. `sitemap_feed`
11. `public_json_api`
12. `rendered_dom_evidence`
13. `sca_listing`
14. `dfsa_notice_listing`
15. `cbuae_document_listing`
16. `adgm_fsra_listing`
17. `vara_pdf_listing`
18. `fiu_eocn_document_listing`

## New In This Sprint

- `static_html`
- `playwright_selector`
- `pdf_document`
- `pdf_listing`
- `register`
- `sitemap_feed`
- `public_json_api`
- `rendered_dom_evidence`
- `adgm_fsra_listing`
- `dfsa_notice_listing`

## Tests Added

New adapter tests cover:

- static article extraction;
- PDF listing extraction;
- register/table extraction;
- PDF document text wrapping;
- ADGM/FSRA listing extraction;
- DFSA notice/enforcement listing extraction;
- source-intake structured failure code mapping.

## Source-Specific Coverage

Covered as fixture-tested adapters:

- SCA listing;
- DFSA rulebook;
- DFSA notices/enforcement listing;
- CBUAE document listing;
- ADGM/FSRA listing;
- VARA PDF/rulebook listing;
- UAE FIU/EOCN document listing.

## Limitations

- Several adapters are fixture-tested but not live-proven.
- Live validation still produced zero new strict no-save passes.
- PDF document extraction here assumes text is already available; deeper PDF extraction remains in existing PDF provider paths or future work.
- Screenshot/rendered DOM evidence is represented as adapter metadata groundwork, not a replacement for proof artifacts.
