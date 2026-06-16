# Weak-Zone DOM/XHR Investigation Report

Date: 2026-06-16

## Scope

Targeted weak-zone checks were run against ADGM alternate components, UAE FIU knowledge-centre pages, VARA rulebook/register pages, DFSA/DIFC listing pages, and CBUAE public/alternate endpoints. No private portals, CAPTCHA, paywalls, customer messages, or broad monitoring were used.

## Findings By Zone

### ADGM alternate components

- `AE-adgm-dp-regulatory-actions`: NAV_SHELL_ONLY q=0 strong=False adapter=adgm_fsra_listing; failure=NAV_SHELL_ONLY Extracted content is a navigation shell or collides with another source hash.
- `AE-adgm-media-announcements`: NAV_SHELL_ONLY q=0 strong=False adapter=adgm_fsra_listing; failure=NAV_SHELL_ONLY Extracted content is a navigation shell or collides with another source hash.
- `AE-adgm-listing-announcements`: NEEDS_SELECTOR_REVIEW q=5 strong=False adapter=; failure=URL_STALE Fetch failed: wait_for_selector 'adgm-section' not found at https://www.adgm.com/financial-services-regulatory-authority/listing-authority/listing-authority-announcements
- `AE-adgm-ra-notices`: NAV_SHELL_ONLY q=0 strong=False adapter=adgm_fsra_listing; failure=NAV_SHELL_ONLY Extracted content is a navigation shell or collides with another source hash.
- `AE-adgm-ra-aml-guides`: NAV_SHELL_ONLY q=0 strong=False adapter=adgm_fsra_listing; failure=NAV_SHELL_ONLY Extracted content is a navigation shell or collides with another source hash.

### UAE FIU SPA/document pages

- `AE-uaefiu-aml-cft-laws`: CONFIRMED_ACCESSIBLE q=62 strong=True adapter=listing; failure=none
- `AE-uaefiu-annual-reports`: CONFIRMED_ACCESSIBLE q=65 strong=True adapter=fiu_eocn_document_listing; failure=none
- `AE-uaefiu-publications-hub`: CONFIRMED_ACCESSIBLE q=65 strong=True adapter=fiu_eocn_document_listing; failure=none
- `AE-uaefiu-strategic-analysis`: NAV_SHELL_ONLY q=0 strong=False adapter=fiu_eocn_document_listing; failure=NAV_SHELL_ONLY Extracted content is a navigation shell or collides with another source hash.
- `AE-uaefiu-nra-2024`: NAV_SHELL_ONLY q=0 strong=False adapter=fiu_eocn_document_listing; failure=NAV_SHELL_ONLY Extracted content is a navigation shell or collides with another source hash.

### VARA rulebook/PDF pages

- `AE-vara-rulebooks-overview`: NAV_SHELL_ONLY q=0 strong=False adapter=listing; failure=NAV_SHELL_ONLY Extracted content is a navigation shell or collides with another source hash.
- `AE-vara-aml-cft-rulebook`: NAV_SHELL_ONLY q=0 strong=False adapter=vara_pdf_listing; failure=NAV_SHELL_ONLY Extracted content is a navigation shell or collides with another source hash.
- `AE-vara-company-rulebook`: NAV_SHELL_ONLY q=0 strong=False adapter=vara_pdf_listing; failure=NAV_SHELL_ONLY Extracted content is a navigation shell or collides with another source hash.
- `AE-vara-public-register`: NAV_SHELL_ONLY q=0 strong=False adapter=listing; failure=NAV_SHELL_ONLY Extracted content is a navigation shell or collides with another source hash.
- `AE-vara-news`: NEEDS_SELECTOR_REVIEW q=5 strong=False adapter=; failure=URL_STALE Fetch failed: wait_for_selector 'main' not found at https://www.vara.ae/en/news/

### DFSA/DIFC selectors

- `AE-dfsa-published-decisions`: NAV_SHELL_ONLY q=0 strong=False adapter=dfsa_notice_listing; failure=NAV_SHELL_ONLY Extracted content is a navigation shell or collides with another source hash.
- `AE-dfsa-enforcement-regulatory-actions`: NEEDS_SELECTOR_REVIEW q=5 strong=False adapter=; failure=URL_STALE Fetch failed: wait_for_selector 'main' not found at https://www.dfsa.ae/what-we-do/enforcement/regulatory-actions
- `AE-dfsa-consultation-papers`: NAV_SHELL_ONLY q=0 strong=False adapter=dfsa_notice_listing; failure=NAV_SHELL_ONLY Extracted content is a navigation shell or collides with another source hash.
- `AE-difc-data-protection`: NEEDS_SELECTOR_REVIEW q=5 strong=False adapter=; failure=URL_STALE Fetch failed: wait_for_selector 'main' not found at https://www.difc.com/business/laws-and-regulations/data-protection/
- `AE-difc-legal-database`: BLOCKED q=35 strong=False adapter=listing; failure=ACCESS_BLOCKED Source appears to require login, CAPTCHA, paywall access, or a private portal.

### CBUAE official alternates

- `AE-cbuae-publications`: BLOCKED q=34 strong=False adapter=cbuae_document_listing; failure=ACCESS_BLOCKED Source appears to require login, CAPTCHA, paywall access, or a private portal.
- `AE-cbuae-circulars`: BLOCKED q=29 strong=False adapter=cbuae_document_listing; failure=ACCESS_BLOCKED Source appears to require login, CAPTCHA, paywall access, or a private portal.
- `AE-cbuae-rulebook-revision-updates`: CONFIRMED_ACCESSIBLE q=65 strong=True adapter=cbuae_document_listing; failure=none

## Useful Selector/Adapter Results

- UAE FIU pages render enough public body content for `listing` or `fiu_eocn_document_listing` on `body` for selected knowledge-centre pages.
- CBUAE public website paths remained access-blocked, but official `rulebook.centralbank.ae` revision updates were accessible and monitorable with `cbuae_document_listing` on `body`.
- ADGM alternate/media/listing announcement URLs still returned nav shell or stale component selectors under tested configurations.
- VARA tested rulebook/public-register/news URLs remained nav shell or stale paths.
- DFSA/DIFC tested listing URLs remained nav shell, selector stale, or access-blocked.
