# UAE Official Source Expansion Validation

## 1. Verdict

No UAE source was activated in this sprint. The best current recommendation is to keep the tested sources in validation states until repeated extraction and proof/diff evidence is available. Mapped is not active; under validation is not active; needs adapter is not active.

## 2. Sources tested

- ae-vara-rulebooks: VARA Rulebooks / Rulebook Updates (https://rulebooks.vara.ae/)
- ae-adgm-fsra-circulars: ADGM FSRA Circulars / Publications (https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities/supervision/circulars)
- ae-cbuae-rulebook-aml-payments: CBUAE Rulebook / AML-CFT / Payments (https://rulebook.centralbank.ae/)
- ae-fiu-publications: UAE FIU Publications / Typologies (https://www.uaefiu.gov.ae/en/publications/)
- ae-dfsa-consultations-notices: DFSA Consultations / Notices / Rulebook Updates (https://www.dfsa.ae/rules-and-guidance)
- ae-difc-laws-data-protection: DIFC Laws / DIFC Data Protection (https://www.difc.com/business/laws-and-regulations/)
- ae-adgm-data-protection: ADGM Office of Data Protection Guidance (https://www.adgm.com/operating-in-adgm/office-of-data-protection)
- ae-fta-tax-guides: FTA Public Clarifications / Tax Guides (https://tax.gov.ae/en/taxes/corporate.tax/corporate.tax.guides.references.aspx)
- ae-uaeiec-sanctions-tfs: Executive Office / UAEIEC Sanctions / TFS (https://www.uaeiec.gov.ae/en-us/un-page)
- ae-moet-aml-dnfbp: Ministry of Economy AML / TFS / DNFBP (https://www.moet.gov.ae/en/aml)
- ae-legislation-portal: UAE Legislation Portal item-level laws/decrees (https://uaelegislation.gov.ae/en)
- ae-dubai-official-gazette: Dubai Official Gazette (https://dlp.dubai.gov.ae/)

## 3. Official URL verification

| Source | Official domain | HTTP reachable | Candidate data | Registry status |
|---|---:|---:|---:|---|
| ae-vara-rulebooks | rulebooks.vara.ae | yes | yes | not matched |
| ae-adgm-fsra-circulars | adgm.com | yes | no | not matched |
| ae-cbuae-rulebook-aml-payments | rulebook.centralbank.ae | yes | yes | not matched |
| ae-fiu-publications | uaefiu.gov.ae | no | no | not matched |
| ae-dfsa-consultations-notices | dfsa.ae | no | no | not matched |
| ae-difc-laws-data-protection | difc.com | yes | yes | enabled_in_existing_registry |
| ae-adgm-data-protection | adgm.com | yes | yes | not matched |
| ae-fta-tax-guides | tax.gov.ae | yes | yes | not matched |
| ae-uaeiec-sanctions-tfs | uaeiec.gov.ae | yes | no | not matched |
| ae-moet-aml-dnfbp | moet.gov.ae | yes | yes | enabled_in_existing_registry |
| ae-legislation-portal | uaelegislation.gov.ae | no | no | enabled_in_existing_registry |
| ae-dubai-official-gazette | dlp.dubai.gov.ae | yes | yes | not matched |

## 4. Extraction results table

| Source | HTTP | Chars | Items | Method | Recommended status |
|---|---:|---:|---:|---|---|
| ae-vara-rulebooks | 200 | 2325 | 8 | table/list-based HTML | under_validation |
| ae-adgm-fsra-circulars | 200 | 1593 | 1 | HTML extractable | under_validation |
| ae-cbuae-rulebook-aml-payments | 200 | 2504 | 10 | table/list-based HTML | active_candidate |
| ae-fiu-publications | 403 | 0 | 0 | navigation-only or JS-rendered | access_limited |
| ae-dfsa-consultations-notices | 404 | 4381 | 30 | table/list-based HTML | blocked_deferred |
| ae-difc-laws-data-protection | 200 | 9150 | 6 | table/list-based HTML | active_candidate |
| ae-adgm-data-protection | 200 | 1804 | 1 | HTML extractable | under_validation |
| ae-fta-tax-guides | 200 | 0 | 6 | table/list-based HTML | under_validation |
| ae-uaeiec-sanctions-tfs | 200 | 54422 | 30 | table/list-based HTML | active_candidate |
| ae-moet-aml-dnfbp | 200 | 49615 | 30 | table/list-based HTML | active_candidate |
| ae-legislation-portal | 403 | 0 | 0 | navigation-only or JS-rendered | access_limited |
| ae-dubai-official-gazette | 200 | 0 | 2 | navigation-only or JS-rendered | under_validation |

## 5. Source-by-source findings

### VARA Rulebooks / Rulebook Updates

- Source ID: `ae-vara-rulebooks`
- Official URL: https://rulebooks.vara.ae/
- HTTP status: 200
- Extracted text length: 2325
- Item/document candidates: 8
- Recommended status: `under_validation`
- Next action: Run repeated extraction and map item-level titles, dates, and source proof URLs.
- Limitations:
  - VARA official portal is the validation target; rulebook/update item paths require separate discovery and adapter validation before activation.
  - Candidate data note: Rulebook pages or PDFs may require source-specific item mapping.
- Sample items:
  - Regulations & Guidelines - https://rulebooks.vara.ae/
  - Regulatory Notices - https://www.vara.ae/en/regulations/regulatory-notices/
  - Regulatory Framework - https://rulebooks.vara.ae/

### ADGM FSRA Circulars / Publications

- Source ID: `ae-adgm-fsra-circulars`
- Official URL: https://www.adgm.com/operating-in-adgm/additional-obligations-of-financial-services-entities/supervision/circulars
- HTTP status: 200
- Extracted text length: 1593
- Item/document candidates: 1
- Recommended status: `under_validation`
- Next action: Repeat FSRA row extraction over scheduled runs and validate true proof/diff before activation.
- Limitations:
  - FSRA circulars prototype did not isolate enough circular rows; source remains adapter/proof target work, not active.
- Sample items:
  - ADGM Brand Book - https://assets.adgm.com/download/assets/ADGM+Brand+Book_2025.pdf/8dcd54d6356111f0aef28a0f7419fcea

### CBUAE Rulebook / AML-CFT / Payments

- Source ID: `ae-cbuae-rulebook-aml-payments`
- Official URL: https://rulebook.centralbank.ae/
- HTTP status: 200
- Extracted text length: 2504
- Item/document candidates: 10
- Recommended status: `active_candidate`
- Next action: Run repeated proof/diff validation before considering activation.
- Limitations:
  - Reachable and itemized, but not active until repeated proof/diff validation passes.
  - CBUAE AML/CFT and payments pages require item-level publication mapping.
  - Candidate data note: Rulebook structure and stable section identifiers need confirmation before monitoring.
- Sample items:
  - Guidance for Licensed Financial Institutions on Risks Related to Proliferation Finance - https://rulebook.centralbank.ae/en/rulebook/guidance-licensed-financial-institutions-risks-related-proliferation-finance
  - Guidance for Licensed Financial Institutions on Risks Related to Trade-Based Money Laundering (“TBML”) and Transshipment - https://rulebook.centralbank.ae/en/rulebook/guidance-licensed-financial-institutions-risks-related-trade-based-money-laundering-%E2%80%9Ctbml%E2%80%9D
  - Small to Medium Sized Enterprises (SME) - Customer Protection Regulation - https://rulebook.centralbank.ae/en/rulebook/small-medium-sized-enterprises-sme-customer-protection-regulation

### UAE FIU Publications / Typologies

- Source ID: `ae-fiu-publications`
- Official URL: https://www.uaefiu.gov.ae/en/publications/
- HTTP status: 403
- Extracted text length: 0
- Item/document candidates: 0
- Recommended status: `access_limited`
- Next action: Defer activation; test approved access strategy without bypassing WAF/CAPTCHA.
- Limitations:
  - HTTP 403 indicates access limitation or blocking.
  - No reliable item-level rows or document links were isolated by generic extraction.
  - Extracted text is below the content-rich threshold for monitoring readiness.

### DFSA Consultations / Notices / Rulebook Updates

- Source ID: `ae-dfsa-consultations-notices`
- Official URL: https://www.dfsa.ae/rules-and-guidance
- HTTP status: 404
- Extracted text length: 4381
- Item/document candidates: 30
- Recommended status: `blocked_deferred`
- Next action: Defer activation; test approved access strategy without bypassing WAF/CAPTCHA.
- Limitations:
  - DFSA pages may return WAF/access limitation from current infrastructure; do not activate without a reliable official item source.
- Sample items:
  - AML, CTF & Sanctions Compliance - https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/summary
  - Regulatory Framework - https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/regulatory-framework
  - Supervisory Methodology - https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/supervisory-methodology

### DIFC Laws / DIFC Data Protection

- Source ID: `ae-difc-laws-data-protection`
- Official URL: https://www.difc.com/business/laws-and-regulations/
- HTTP status: 200
- Extracted text length: 9150
- Item/document candidates: 6
- Recommended status: `active_candidate`
- Next action: Run repeated proof/diff validation before considering activation.
- Limitations:
  - Reachable and itemized, but not active until repeated proof/diff validation passes.
  - Candidate data note: Digital asset materials may be distributed across DIFC/DFSA pages.
- Sample items:
  - Legal Database - https://www.difc.com/business/laws-and-regulations/legal-database
  - DIFC Publications - https://www.difc.com/media/publications
  - Federal Decree No. 35 of 2004 - https://edge.sitecorecloud.io/dubaiintern0078-difcexperie96c5-production-3253/media/project/difcexperiences/difc/difcwebsite/documents/difc_docs/federal_decree_no_35_for_the_year_2004_english.pdf

### ADGM Office of Data Protection Guidance

- Source ID: `ae-adgm-data-protection`
- Official URL: https://www.adgm.com/operating-in-adgm/office-of-data-protection
- HTTP status: 200
- Extracted text length: 1804
- Item/document candidates: 1
- Recommended status: `under_validation`
- Next action: Run repeated extraction and map item-level titles, dates, and source proof URLs.
- Limitations:
  - Limitations require operator review before pilot activation.
  - Candidate data note: URL may require adjustment; ADGM site structure has changed historically.
- Sample items:
  - ADGM Brand Book - https://assets.adgm.com/download/assets/ADGM+Brand+Book_2025.pdf/8dcd54d6356111f0aef28a0f7419fcea

### FTA Public Clarifications / Tax Guides

- Source ID: `ae-fta-tax-guides`
- Official URL: https://tax.gov.ae/en/taxes/corporate.tax/corporate.tax.guides.references.aspx
- HTTP status: 200
- Extracted text length: 0
- Item/document candidates: 6
- Recommended status: `under_validation`
- Next action: Run repeated extraction and map item-level titles, dates, and source proof URLs.
- Limitations:
  - Extracted text is below the content-rich threshold for monitoring readiness.
  - FTA/tax.gov.ae may require access and repeated-run validation from deployment infrastructure.
  - Candidate data note: Likely portal access restriction; PDF guide discovery must be validated.
- Sample items:
  - Guides, References & Public Clarifications - https://tax.gov.ae/en/taxes/Vat/guides.references.aspx
  - Guides, References & Public Clarifications - https://tax.gov.ae/en/taxes/excise.tax/guides.listing.aspx
  - Guides, References & Public Clarifications - https://tax.gov.ae/en/taxes/corporate.tax/corporate.tax.guides.references.aspx

### Executive Office / UAEIEC Sanctions / TFS

- Source ID: `ae-uaeiec-sanctions-tfs`
- Official URL: https://www.uaeiec.gov.ae/en-us/un-page
- HTTP status: 200
- Extracted text length: 54422
- Item/document candidates: 30
- Recommended status: `active_candidate`
- Next action: Run repeated proof/diff validation before considering activation.
- Limitations:
  - Reachable and itemized, but not active until repeated proof/diff validation passes.
- Sample items:
  - Targeted Financial Sanctions - https://www.uaeiec.gov.ae/en-us/un-page
  - Legislation - https://www.uaeiec.gov.ae/en-us/laws-regulations-listing
  - Sanctions Implementation - https://www.uaeiec.gov.ae/en-us/un-page?p=2

### Ministry of Economy AML / TFS / DNFBP

- Source ID: `ae-moet-aml-dnfbp`
- Official URL: https://www.moet.gov.ae/en/aml
- HTTP status: 200
- Extracted text length: 49615
- Item/document candidates: 30
- Recommended status: `active_candidate`
- Next action: Run repeated proof/diff validation before considering activation.
- Limitations:
  - Reachable and itemized, but not active until repeated proof/diff validation passes.
  - Candidate data note: URL was corrected in Sprint 3A; PDF-heavy guidance requires fresh validation.
- Sample items:
  - Investment Publications - https://www.moet.gov.ae/en/investmentpublications
  - Regulation of competition legislations - https://www.moet.gov.ae/en/regulation-of-competition-legislations
  - Regulation of Business - https://www.moet.gov.ae/en/regulation-of-business

### UAE Legislation Portal item-level laws/decrees

- Source ID: `ae-legislation-portal`
- Official URL: https://uaelegislation.gov.ae/en
- HTTP status: 403
- Extracted text length: 0
- Item/document candidates: 0
- Recommended status: `access_limited`
- Next action: Defer activation; test approved access strategy without bypassing WAF/CAPTCHA.
- Limitations:
  - HTTP 403 indicates access limitation or blocking.
  - No reliable item-level rows or document links were isolated by generic extraction.
  - Extracted text is below the content-rich threshold for monitoring readiness.
  - Root portal validation is insufficient; item-level laws/decrees must be tested separately.

### Dubai Official Gazette

- Source ID: `ae-dubai-official-gazette`
- Official URL: https://dlp.dubai.gov.ae/
- HTTP status: 200
- Extracted text length: 0
- Item/document candidates: 2
- Recommended status: `under_validation`
- Next action: Run repeated extraction and map item-level titles, dates, and source proof URLs.
- Limitations:
  - Extracted text is below the content-rich threshold for monitoring readiness.
  - Dubai legislation portal root is not enough; official gazette issue/year/PDF item paths must be isolated before activation.
  - Candidate data note: Official portal appears relevant, but access and item-level structure require validation.
- Sample items:
  - اعرف المزيد - https://dlp.dubai.gov.ae/ar/Pages/OfficialGazette.aspx
  - ​​إرشادات الوصول للمحتوى - https://dlp.dubai.gov.ae/ar/Pages/AccessibilityGuidelines.aspx

## 6. Proof target selection

Selected proof target: `ae-cbuae-rulebook-aml-payments` - CBUAE Rulebook revision updates.

Preferred FSRA circulars target did not produce enough item rows; CBUAE Rulebook revision updates produced the strongest high-value row extraction candidate.

## 7. Adapter prototypes created

- `app/adapters/uae_fsra_circulars.py` was created as a manually callable prototype.
- `app/adapters/uae_cbuae_rulebook.py` was created as a manually callable prototype.
- These prototypes are not registered in the production adapter registry and do not activate monitoring.

## 8. Proof target row/item extraction result

- Source page: https://rulebook.centralbank.ae/en/view-revision-updates?f_days=on&changed=-365%20day
- First-run item count: 10
- Second-run item count: 10
- Recommended status: `active_candidate`

Preferred FSRA target attempt:

- FSRA first-run item count: 0
- FSRA recommendation: `needs_adapter`
- FSRA next action: Create a stronger FSRA circular row adapter or isolate a publication endpoint before activation.

| Title | Date | URL | Document |
|---|---|---|---|
| Guidance for Licensed Financial Institutions on Risks Related to Proliferation Finance | 07 November 2025 | https://rulebook.centralbank.ae/en/rulebook/guidance-licensed-financial-institutions-risks-related-proliferation-finance |  |
| Guidance for Licensed Financial Institutions on Risks Related to Trade-Based Money Laundering (“TBML”) and Transshipment | 07 November 2025 | https://rulebook.centralbank.ae/en/rulebook/guidance-licensed-financial-institutions-risks-related-trade-based-money-laundering-%E2%80%9Ctbml%E2%80%9D |  |
| Small to Medium Sized Enterprises (SME) - Customer Protection Regulation | 13 September 2026 | https://rulebook.centralbank.ae/en/rulebook/small-medium-sized-enterprises-sme-customer-protection-regulation |  |
| Remuneration Regulation for Banks and Insurance Companies | 14 April 2026 | https://rulebook.centralbank.ae/en/rulebook/remuneration-regulation-banks-and-insurance-companies |  |
| Remuneration Regulation for Banks and Insurance Companies | 14 April 2026 | https://rulebook.centralbank.ae/en/rulebook/remuneration-regulation-banks-and-insurance-companies-0 |  |

## 9. Same-run stability / proof-diff result

- Item count stable: True
- First 3 titles stable: True
- First 3 URLs stable: True
- Row hash stable: True

This is same-run stability proof only. True change-diff still requires future scheduled comparison against a later snapshot.

## 10. Recommended status changes

- `access_limited`: 2
- `active_candidate`: 4
- `blocked_deferred`: 1
- `under_validation`: 5

No source should be marked active from this sprint alone.

## 11. Sources NOT to activate yet

- `ae-vara-rulebooks` remains `under_validation` until proof/diff validation is complete.
- `ae-adgm-fsra-circulars` remains `under_validation` until proof/diff validation is complete.
- `ae-cbuae-rulebook-aml-payments` remains `active_candidate` until proof/diff validation is complete.
- `ae-fiu-publications` remains `access_limited` until proof/diff validation is complete.
- `ae-dfsa-consultations-notices` remains `blocked_deferred` until proof/diff validation is complete.
- `ae-difc-laws-data-protection` remains `active_candidate` until proof/diff validation is complete.
- `ae-adgm-data-protection` remains `under_validation` until proof/diff validation is complete.
- `ae-fta-tax-guides` remains `under_validation` until proof/diff validation is complete.
- `ae-uaeiec-sanctions-tfs` remains `active_candidate` until proof/diff validation is complete.
- `ae-moet-aml-dnfbp` remains `active_candidate` until proof/diff validation is complete.
- `ae-legislation-portal` remains `access_limited` until proof/diff validation is complete.
- `ae-dubai-official-gazette` remains `under_validation` until proof/diff validation is complete.

## 12. Next validation actions

- Run scheduled FSRA circulars proof/diff validation on multiple days.
- Build targeted adapters for high-value sources where generic extraction returned navigation-only or low-quality content.
- Validate item-level titles, dates, source proof URLs, and document/PDF handling before any activation.
- Keep limitations near every public source-readiness claim.
