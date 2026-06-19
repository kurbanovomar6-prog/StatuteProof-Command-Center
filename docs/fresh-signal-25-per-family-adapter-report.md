# Fresh Signal 25 Per Family Adapter Report

Date: 2026-06-19

## Adapter / Extraction Work Used

This sprint used existing and newly registered adapter paths rather than generic scraping alone:

- CBUAE: `CBUAERulebookAdapter` is registered in `product/regradar/app/adapters/registry.py`; the active source rows use `cbuae_document_listing` / `document_listing` configs with Playwright where needed.
- ADGM/FSRA: `FSRACircularsAdapter` is registered; several ADGM rows use `custom_element` or `adgm_fsra_listing`.
- SCA: `sca_listing` and `table` adapter configs were used for SCA AML/CFT, FATCA/CRS, corporate governance, and circular/rules/procedures sources.
- EOCN: `listing` and `eocn_news_listing` paths were used with Playwright for direct EOCN sources.
- UAE FIU: `fiu_eocn_document_listing` / `listing` with Playwright was used for typology reports, AML/CFT laws, and publications hub.
- VARA: direct `pdf_document` extraction and `vara_pdf_listing` / `document_listing` were used for rulebook PDFs and revision updates.
- DFSA: `dfsa_rulebook`, listing, and Playwright configs were used for financial crime, rulebook, consultation, enforcement, and regulatory-action sources.
- DIFC: existing legal/database/page extraction paths were sufficient for the seven candidate pages promoted in this pass.

## Adapter Outcomes

Successful examples:

- CBUAE rulebook/revision sources: 25 passed proof, repeat baseline, and mass-monitor `MONITOR_OK`.
- VARA rulebook PDFs/revision source: 7 passed.
- EOCN direct sources: 2 passed.
- UAE FIU document/publication pages: 3 passed.
- SCA pages: 3 additional sources passed, bringing SCA fresh-alert count to 4.
- ADGM/FSRA candidates: 6 passed.
- DFSA candidates: 7 promoted to fresh-alert; one static historical consultation paper held as evidence-library.
- DIFC candidates: 7 passed.

Held examples:

- `AE-cbuae-regulations`: access/private-risk policy classification; not fresh-alert.
- `AE-vara-enforcement`: nav-shell result; needs selector/listing adapter.
- `AE-uaefiu-circulars`: nav-shell result; needs FIU-specific circular listing adapter.
- `AE-sca-regulations-listing`: nav-shell result; needs refined SCA listing/table adapter.
- `AE-adgm-fsra-guidance-policy` and `AE-adgm-ra-circulars`: intake certified but mass-monitor mapped to `QUALITY_DROP`; held until extraction quality is raised.
- `AE-adgm-fsra-waivers`: nav-shell result.

## Required Next Adapter Work

- VARA enforcement/admin orders listing adapter.
- SCA regulations-listing adapter with stable table/item selectors.
- UAE FIU circulars adapter that extracts publication/circular rows rather than navigation shell.
- ADGM guidance/RA circulars adapter refinement to lift quality above mass-monitor threshold.
- MoJ/UAE legislation access classifier plus official alternative legal/gazette endpoint adapter.
- MoF decision/news/document listing adapter to replace generic homepage.
- DFSA and DIFC discovery adapters for more official live listings if the 25-source target remains mandatory.
