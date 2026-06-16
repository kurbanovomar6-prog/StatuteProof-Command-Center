# DIFC Official Source Research Log

Date: 2026-06-16

Research scope: public official or officially linked DIFC legal/regulatory pages only. No login, CAPTCHA, private portal, or paywall bypass.

## Researched Candidates

| Source ID proposal | Official URL | Type | Why official/public | MLRO/compliance relevance | Strategy | Risk | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `AE-difc-laws-regulations` | `https://www.difc.com/business/laws-and-regulations/` | Laws/regulations overview | Official DIFC domain and laws/regulations section | Useful overview for DIFC firms and legal/compliance teams | DIFC legal adapter | medium: broad page/chrome | Activated under canonical `AE-difc-laws-and-regulations` after proof/baseline gates |
| `AE-difc-legal-database` | `https://www.difc.com/business/laws-and-regulations/legal-database/` | Legal database listing | Official DIFC Legal Database on `difc.com` | High-value index of DIFC laws, regulations, notices and PDF documents | DIFC legal database adapter | medium: large page, many links, title/PDF pairing | Activated |
| `AE-difc-consultation-papers` | `https://www.difc.com/business/laws-and-regulations/consultation-papers/` | Consultation listing | Official DIFC laws/regulations consultation page | Early-warning source for legal/regulatory changes | listing or DIFC legal adapter | medium/high: thin listing | Test and hold if weak |
| `AE-difc-data-protection-commissioner` | `https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection` | Regulator/commissioner hub | Official DIFC Commissioner page | Privacy/data-protection compliance relevance | DIFC legal adapter | medium: portal wording false positive | Activated |
| `AE-difc-data-protection-guidance` | `https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/guidance` | Guidance listing | Official DIFC Commissioner guidance page | Useful for data-protection compliance teams | DIFC legal/document adapter | medium: document listing pairing | Activated |
| `AE-difc-data-protection-regulation-10` | `https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/regulation-10` | Regulatory guidance page | Official DIFC Commissioner page | Useful but narrower than legal database | DIFC legal adapter | medium: short page | Activated |
| `AE-difc-data-protection-supervision-enforcement` | `https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/supervision-enforcement` | Supervision/enforcement page | Official DIFC Commissioner page | Useful for enforcement/supervisory posture | DIFC legal adapter | medium: portal wording | Activated |
| `AE-difc-data-protection-law-2020` | `https://www.difc.com/business/laws-and-regulations/legal-database/difc-laws/data-protection-law-difc-law-no-5-2020` | Law detail page | Official DIFC legal database detail page | High privacy/data-protection relevance | rendered detail extraction | medium: JS-heavy rendered detail | Activated |
| `AE-difc-digital-assets-law-2024` | `https://www.difc.com/business/laws-and-regulations/legal-database/difc-laws/digital-assets-law-difc-law-no-2-of-2024` | Law detail page | Official DIFC legal database detail page | Digital asset legal framework relevance | detail-page adapter or direct PDF extraction | medium: short rendered metadata | Candidate if PDF/detail link is stable |
| `AE-difc-companies-law-2018` | `https://www.difc.com/business/laws-and-regulations/legal-database/difc-laws/companies-law-difc-law-no-5-2018` | Law detail page | Official DIFC legal database detail page | Corporate/legal framework relevance | rendered detail extraction | medium: JS-heavy rendered detail | Activated |
| `AE-difc-data-protection-old` | `https://www.difc.com/business/laws-and-regulations/data-protection/` | Old candidate route | Official domain but current response is 404 | Not useful as active source | reject/replace | high | Rejected |
| `AE-difc-legislation-old` | `https://www.difc.ae/business/laws-regulations/legislation/` | Old route | Historical official domain/path | Previous extraction produced navigation-only output | hold | high | Rejected for activation |

## Key Finding

The strongest path is `https://www.difc.com/business/laws-and-regulations/legal-database/`. It is public, official, and contains many DIFC law detail and PDF links. Generic document-listing extraction was insufficient because DIFC renders law title/detail/PDF anchors in adjacent structures where the PDF anchor text can be blank or generic. After remediation, the legal database plus selected Commissioner of Data Protection and legal-detail pages passed proof, repeat baseline, mass-monitor dry-run, and review gates. This improves DIFC depth but does not claim end-to-end DIFC source scope.
