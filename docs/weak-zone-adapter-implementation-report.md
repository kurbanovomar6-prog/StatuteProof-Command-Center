# Weak-Zone Adapter Implementation Report

Date: 2026-06-16

## Executive Verdict

This cycle did not add a broad new dependency or rewrite the parser. The biggest improvement was operational: route weak-zone sources through better existing adapter families and official alternate endpoints, especially `vara_pdf_listing`, `cbuae_document_listing`, `dfsa_notice_listing`, and `static_html` with focused selectors.

## Adapter / Config Improvements Used

| Area | Adapter/config used | Result |
| --- | --- | --- |
| VARA official rulebook updates | `vara_pdf_listing` on `rulebooks.vara.ae` revision listing | One stable source activated. |
| VARA rulebook HTML | `static_html` focused on rulebook body | One source passed no-save/evidence but one rulebook drifted in dry-run and was held. |
| CBUAE rulebook alternates | `cbuae_document_listing` on `rulebook.centralbank.ae` | Four stable CBUAE sources activated, including AML/CFT, payment services, and consumer protection document listings. |
| DFSA official pages | `dfsa_notice_listing` | Five stable DFSA sources activated across consultations, enforcement, regulatory actions, and official-linked Thomson Reuters pages. |
| Direct PDF URLs | `pdf_document` attempted | Held: current Playwright fetch path returns shallow/no text for direct PDF files. |
| ADGM alternate components | `adgm_fsra_listing`, `custom_element`, `static_html` attempted | Held: still below threshold or nav-shell under safe selectors. |
| UAE FIU leftovers | `fiu_eocn_document_listing`, `static_html` attempted | Held: remaining pages are duplicate/shallow/noisy routes after two FIU sources were already activated in the prior cycle. |

## Exact Blockers Solved

- VARA stale landing pages were bypassed by official `rulebooks.vara.ae` endpoints.
- CBUAE public-site 403/access issues were partially bypassed through official `rulebook.centralbank.ae` pages, without WAF/login/CAPTCHA bypass.
- DFSA stale consultation/enforcement paths were remediated through current official paths and official-linked Thomson Reuters pages.
- CBUAE static extraction drift was solved for three pages by switching to stable document-listing extraction.
- `dfsa_notice_listing` now explicitly recognizes consultation, paper, decision, and supervisory-review signals so official DFSA consultation/enforcement pages do not get under-extracted.

## Tests Added

- `test_vara_pdf_listing_extracts_rulebook_revision_updates`
- `test_cbuae_document_listing_extracts_rulebook_links_without_static_hash_noise`
- `test_dfsa_notice_listing_extracts_consultation_and_enforcement_links`

## Remaining Adapter Gaps

- Direct PDF extraction needs a real non-Playwright PDF fetch path before VARA PDF files can become monitorable.
- ADGM alternate media/data-protection/listing pages still require component-specific card extraction or replacement URLs.
- DIFC pages remain access/selector blocked under safe public access.
- VARA static rulebook page `AE-vara-compliance-risk-rulebook` needs a stable extraction path because mass-monitor dry-run produced `QUALITY_DROP`.
