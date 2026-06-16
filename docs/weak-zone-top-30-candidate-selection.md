# Weak-Zone Top 30 Candidate Selection

Date: 2026-06-16

Selection rule: choose official UAE candidates from the existing scoreboard/work queue that are blocked by weak-zone extraction, access, selector, or duplicate-hash issues and still have plausible MLRO/CCO value.

| # | Source ID | Group | Official URL | Current blocker | Expected adapter / strategy | Priority | Batch |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | `AE-vara-rulebooks-overview` | VARA | `https://www.vara.ae/en/regulatory-framework/rulebooks/` | Nav-shell/stale route. | Direct PDF/rulebook document discovery. | high | 1 |
| 2 | `AE-vara-aml-cft-rulebook` | VARA | `https://www.vara.ae/en/regulatory-framework/aml-cft-rulebook/` | Nav-shell. | Direct AML/CFT PDF/document endpoint. | high | 1 |
| 3 | `AE-vara-company-rulebook` | VARA | `https://www.vara.ae/en/regulatory-framework/company-rulebook/` | Nav-shell. | Direct Company Rulebook PDF/document endpoint. | high | 1 |
| 4 | `AE-vara-regulatory-framework` | VARA | `https://www.vara.ae/en/regulatory-framework/` | Nav-shell/stale framework route. | Official document URLs over landing page. | high | 1 |
| 5 | `AE-vara-public-register` | VARA | `https://www.vara.ae/en/public-register/` | Nav-shell/register uncertainty. | Register adapter only if rows render publicly. | medium | 1 |
| 6 | `AE-cbuae-publications` | CBUAE | `https://www.centralbank.ae/en/publications/` | Access-blocked public site. | Official alternate document/rulebook endpoint. | high | 2 |
| 7 | `AE-cbuae-circulars` | CBUAE | `https://www.centralbank.ae/en/regulations/` | Access-blocked/stale. | Official alternate circular/regulation listing. | high | 2 |
| 8 | `AE-cbuae-aml-cft` | CBUAE | `https://www.centralbank.ae/en/our-operations/anti-money-laundering-and-combatting-the-financing-of-terrorism/` | Access-blocked. | Rulebook AML/financial-crime pages. | high | 2 |
| 9 | `AE-cbuae-payment-systems` | CBUAE | `https://www.centralbank.ae/en/our-operations/payment-systems/` | Access-blocked. | Rulebook payment/RPSCS/stored-value pages. | high | 2 |
| 10 | `AE-cbuae-consultations` | CBUAE | `https://www.centralbank.ae/en/consultations/` | Access-blocked. | Official public alternate only. | medium | 2 |
| 11 | `AE-dfsa-published-decisions` | DFSA/DIFC | `https://www.dfsa.ae/what-we-do/enforcement/published-decisions` | Nav-shell. | Enforcement listing selector or document links. | high | 3 |
| 12 | `AE-dfsa-enforcement-regulatory-actions` | DFSA/DIFC | `https://www.dfsa.ae/what-we-do/enforcement/regulatory-actions` | Stale selector/access. | Enforcement listing selector. | high | 3 |
| 13 | `AE-dfsa-consultation-papers` | DFSA/DIFC | `https://www.dfsa.ae/your-resources/publications/consultation-papers` | Access/selector issue. | Consultation PDF/listing adapter. | high | 3 |
| 14 | `AE-dfsa-publications` | DFSA/DIFC | `https://www.dfsa.ae/your-resources/publications` | Untested/remediation. | Publication listing selector. | medium | 3 |
| 15 | `AE-dfsa-public-register` | DFSA/DIFC | `https://www.dfsa.ae/public-register` | Untested/remediation. | Register adapter only if public rows render. | medium | 3 |
| 16 | `AE-difc-data-protection` | DFSA/DIFC | `https://www.difc.com/business/laws-and-regulations/data-protection/` | Selector stale. | DIFC content selector/document links. | medium | 3 |
| 17 | `AE-difc-consultation-papers` | DFSA/DIFC | `https://www.difc.com/business/laws-and-regulations/consultation-papers/` | Untested/remediation. | Consultation listing selector. | medium | 3 |
| 18 | `AE-difc-legal-database` | DFSA/DIFC | `https://www.difc.com/business/laws-and-regulations/legal-database/` | Access-blocked. | Hold unless public unauthenticated access works. | low | 3 |
| 19 | `AE-adgm-dp-regulatory-actions` | ADGM alternate | `https://www.adgm.com/operating-in-adgm/office-of-data-protection/regulatory-actions` | Nav-shell/heading-only. | Regulatory-action card/listing extraction. | high | 4 |
| 20 | `AE-adgm-media-announcements` | ADGM alternate | `https://www.adgm.com/media/announcements` | Nav/service-link noise. | Announcement-card extraction with noise filtering. | medium | 4 |
| 21 | `AE-adgm-listing-announcements` | ADGM alternate | `https://www.adgm.com/financial-services-regulatory-authority/listing-authority/listing-authority-announcements` | Stale selector/URL. | Replacement URL or component selector. | high | 4 |
| 22 | `AE-adgm-ra-notices` | ADGM alternate | `https://www.adgm.com/registration-authority/notices` | Alternate component/stale path. | Replacement URL/component selector. | medium | 4 |
| 23 | `AE-adgm-ra-aml-guides` | ADGM alternate | `https://www.adgm.com/registration-authority/aml-cft-quick-guides` | Alternate component/stale path. | Replacement URL/document list. | medium | 4 |
| 24 | `AE-adgm-abu-dhabi-legislation` | ADGM alternate | `https://www.adgm.com/legal-framework/abu-dhabi-legislation` | Not fully tested. | Legal-framework selector. | medium | 4 |
| 25 | `AE-adgm-federal-legislation` | ADGM alternate | `https://www.adgm.com/legal-framework/federal-legislation` | Not fully tested. | Legal-framework selector. | medium | 4 |
| 26 | `AE-uaefiu-strategic-analysis` | UAE FIU | `https://uaefiu.gov.ae/en/more/knowledge-centre/publications/strategic-analysis-guidelines/` | Shallow/nav-shell route. | Direct document endpoint or hold. | medium | 5 |
| 27 | `AE-uaefiu-nra-2024` | UAE FIU | `https://uaefiu.gov.ae/en/more/knowledge-centre/publications/national-risk-assessment-report-2024/` | Shallow/nav-shell route. | Direct document endpoint or hold. | medium | 5 |
| 28 | `AE-uaefiu-annual-reports` | UAE FIU | `https://uaefiu.gov.ae/en/more/knowledge-centre/publications/annual-report/` | Duplicate publications-hub hash. | Narrow document selector. | low-medium | 5 |
| 29 | `AE-uaefiu-press-releases` | UAE FIU | `https://uaefiu.gov.ae/en/more/media/press-releases/` | Not fully tested. | Regulatory news/listing only if useful. | medium | 5 |
| 30 | `AE-uaefiu-laws-regulations` | UAE FIU | `https://www.uaefiu.gov.ae/en/Laws-Regulations/` | Access-blocked/stale older route. | Prefer official newer law endpoint; classify access honestly. | low-medium | 5 |

## Batch Execution Target

- Test at least 30 candidates across five weak-zone batches unless hard blocked.
- Save evidence only for strong passes.
- Keep duplicate hashes and no-save-only sources out of `sources.json`.
- Continue beyond the first activation if more safe candidates remain.
