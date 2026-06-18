# Weak-Family 25-Each Official Source Research Log

Date: 2026-06-18

This sprint researched weak UAE source families with an activation-first goal. It did not claim complete UAE coverage or complete family coverage. Monitoring intelligence only. Not legal advice.

## Researched Families

| Family | Discovery result | Activation decision |
| --- | --- | --- |
| FTA / Tax | Official `tax.gov.ae` legislation, VAT, corporate tax, and excise pages expose direct official PDF documents. | 25 direct official PDFs were promoted after no-save, proof, repeat baseline, mass-monitor `MONITOR_OK`, and review gates. Listing pages remain candidate/adapter work. |
| SCA | Official `sca.gov.ae` pages expose a small number of document/detail endpoints. Some are Office/download binaries or require better document handling. | No broad SCA activation in this sprint. One VASP guideline PDF passed no-save, but the family still needs a document/download adapter before a 25-source target is honest. |
| UAE FIU | Existing official publication pages remain low-count and broad. | No new activation in this sprint. Needs tighter publication-detail extraction and duplicate-hub controls. |
| EOCN / sanctions / TFS | Existing official legal/news pages remain low-count and noise-prone. | No new activation in this sprint. Needs sanctions/TFS noise controls before source count expansion. |
| VARA | Current direct official PDFs remain useful, but mapped official candidates are not enough to reach 25 without guidance/admin-order depth work. | No new activation in this sprint. |
| DIFC | Existing candidates are mostly document hubs, data protection guidance, legal updates, and non-core pages. | No new activation in this sprint. Needs document-hub adapter and relevance scoring. |
| ADGM/FSRA | Existing candidates include legal framework, courts, registration authority, public notices, and announcements. | No new activation in this sprint. Needs ADGM component/document-hub adapter work. |
| Ministry of Economy / DNFBP AML | Existing MoE sources improved earlier, but many remaining candidates are generic legal pages. | No new activation in this sprint. Needs MoE legislation/listing adapter and AML/DNFBP relevance filters. |

## FTA Candidate Sources Tested

FTA candidates came from official pages:

- `https://tax.gov.ae/en/legislation.aspx`
- `https://tax.gov.ae/en/taxes/vat/guides.references.aspx`
- `https://tax.gov.ae/en/taxes/corporate.tax/corporate.tax.guides.references.aspx`
- `https://tax.gov.ae/en/taxes/excise.tax/guides.listing.aspx`
- `https://tax.gov.ae/en/legislation/corporate-tax.aspx`

Generated detail results are in:

- `docs/weak-family-25-each-nosave-results.json`
- `docs/weak-family-25-each-evidence-results.json`
- `docs/weak-family-25-each-mass-monitor-results.json`
- `docs/weak-family-25-each-final-activation-set.json`

## SCA Candidate Findings

SCA pages checked:

- `https://www.sca.gov.ae/en/regulations/regulations-listing`
- `https://www.sca.gov.ae/en/regulations/circulars-rules-and-procedures`
- `https://www.sca.gov.ae/en/regulations/anti-money-laundering-and-terrorist-financing`
- `https://www.sca.gov.ae/en/regulations/market-rules-approved-by-sca`
- `https://www.sca.gov.ae/en/open-data/violations-and-violators`

Notable result: `https://www.sca.gov.ae/assets/2f70b3b8/guidelines-regulation-of-virtual-assets-and-virtual-assets-services-providers.aspx` passed as a `pdf_document` candidate, but one passing SCA PDF is not enough to claim SCA family depth. Several `/assets/download/...` endpoints start browser downloads or Office/zip-like content, so SCA needs a source-specific download/document adapter before mass activation.

## Research Verdict

FTA was the only family in this sprint with enough official, public, extractable, non-duplicate documents to reach 25 monitoring-active sources honestly. Other families remain below 25 because more activation would require either new adapters, source-specific filtering, or additional official-source discovery.
