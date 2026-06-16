# Final-8 Top-30 Candidate Selection

Date: 2026-06-16

Selection principle: choose official/public UAE endpoints with the shortest path from candidate to proof-backed activation. Do not include generic pages only to inflate the count.

| # | Source ID | Regulator | URL | Current blocker | Expected adapter | Activation potential |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | `AE-cbuae-stored-value-facilities-rulebook` | CBUAE | `https://rulebook.centralbank.ae/en/rulebook/stored-value-facilities-regulation` | Exact URL may vary | `cbuae_document_listing` | High |
| 2 | `AE-cbuae-complaints-management-rulebook` | CBUAE | `https://rulebook.centralbank.ae/en/rulebook/complaints-management-system` | Exact URL may vary | `cbuae_document_listing` | High |
| 3 | `AE-cbuae-open-finance-rulebook` | CBUAE | `https://rulebook.centralbank.ae/en/rulebook/open-finance-regulation` | Exact URL may vary | `cbuae_document_listing` | High |
| 4 | `AE-cbuae-payment-token-services-rulebook` | CBUAE | `https://rulebook.centralbank.ae/en/rulebook/payment-token-services-regulation` | Exact URL may vary | `cbuae_document_listing` | High |
| 5 | `AE-cbuae-risk-management-rulebook` | CBUAE | `https://rulebook.centralbank.ae/en/rulebook/risk-management` | Exact URL may vary | `cbuae_document_listing` | Medium |
| 6 | `AE-cbuae-outsourcing-rulebook` | CBUAE | official rulebook section | Needs exact URL | `cbuae_document_listing` | Medium |
| 7 | `AE-cbuae-corporate-governance-rulebook` | CBUAE | official rulebook section | Needs exact URL | `cbuae_document_listing` | Medium |
| 8 | `AE-cbuae-licensing-rulebook` | CBUAE | official rulebook section | Needs exact URL | `cbuae_document_listing` | Medium |
| 9 | `AE-vara-aml-cft-controls` | VARA | `https://rulebooks.vara.ae/rulebook/c-amlcft-controls` | Static/rulebook extraction stability | `static_html` / `vara_pdf_listing` | Medium |
| 10 | `AE-vara-compliance-risk-rulebook` | VARA | `https://rulebooks.vara.ae/rulebook/compliance-and-risk-management-rulebook` | Prior dry-run `QUALITY_DROP` | stable selector or hold | Medium |
| 11 | `AE-vara-company-rulebook-pdf` | VARA | official VARA PDF URL | Direct PDF shallow path | `pdf_document` | Medium if PDF extraction fixed |
| 12 | `AE-vara-market-conduct-rulebook-pdf` | VARA | official VARA PDF URL | Direct PDF shallow path | `pdf_document` | Medium if PDF extraction fixed |
| 13 | `AE-vara-technology-information-rulebook-pdf` | VARA | official VARA PDF URL | Direct PDF shallow path | `pdf_document` | Medium if PDF extraction fixed |
| 14 | `AE-dfsa-published-decisions` | DFSA | `https://www.dfsa.ae/what-we-do/enforcement/published-decisions` | Needs current selector check | `dfsa_notice_listing` | High |
| 15 | `AE-dfsa-publications` | DFSA | `https://www.dfsa.ae/your-resources/publications` | Broad page/noise risk | `dfsa_notice_listing` | Medium |
| 16 | `AE-dfsa-aml-ctf-sanctions` | DFSA | `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance` | Broad or duplicate page risk | `dfsa_notice_listing` | Medium |
| 17 | `AE-dfsa-public-register` | DFSA | `https://www.dfsa.ae/public-register` | Search/register risk | `register` / hold | Low-medium |
| 18 | `AE-difc-data-protection` | DIFC | `https://www.difc.com/business/laws-and-regulations/data-protection/` | Access/selector issue | `listing` / `static_html` | Medium |
| 19 | `AE-difc-consultation-papers` | DIFC | `https://www.difc.com/business/laws-and-regulations/consultation-papers/` | Access/selector issue | `listing` | Medium |
| 20 | `AE-difc-legal-database` | DIFC | `https://www.difc.com/business/laws-and-regulations/legal-database/` | Access/selector issue | `listing` / hold | Low-medium |
| 21 | `AE-adgm-dp-regulatory-actions` | ADGM | ADGM data protection regulatory actions URL | Alternate component | `custom_element` / `listing` | Medium |
| 22 | `AE-adgm-media-announcements` | ADGM | `https://www.adgm.com/media/announcements` | Alternate component/noise | `listing` | Low-medium |
| 23 | `AE-adgm-listing-announcements` | ADGM | ADGM listing authority announcements URL | Alternate component | `custom_element` | Medium |
| 24 | `AE-adgm-abu-dhabi-legislation` | ADGM | ADGM legal framework subpage | Not yet tested | `custom_element` | Medium |
| 25 | `AE-adgm-federal-legislation` | ADGM | ADGM legal framework subpage | Not yet tested | `custom_element` | Medium |
| 26 | `AE-uaefiu-press-releases` | UAE FIU | FIU press releases | Noise risk | `listing` | Low unless regulatory |
| 27 | `AE-uaefiu-strategic-analysis` | UAE FIU | FIU strategic analysis | Shallow route alias | document endpoint needed | Low-medium |
| 28 | `AE-uaefiu-nra-2024` | UAE FIU | FIU NRA route | Shallow route alias | document endpoint needed | Low-medium |
| 29 | `AE-fta-corporate-tax-guides` | FTA | FTA corporate tax guides | Not yet tested | `listing` | Medium if accessible |
| 30 | `AE-moec-aml-dnfbp` | Ministry of Economy | MOEC/MOET AML page | Not yet tested | `custom_element` / `static_html` | Medium |

## Batch Order

1. CBUAE rulebook candidates.
2. DFSA current leftovers.
3. VARA rulebook/PDF candidates.
4. DIFC/ADGM alternate selectors.
5. FIU/FTA/MOEC leftovers.
