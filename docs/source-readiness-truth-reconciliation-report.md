# Source Readiness Truth Reconciliation Report

Date: 2026-06-15

## Executive Decision

The canonical customer-facing truth for the current StatuteProof UAE source pack is:

**66 enabled UAE sources; 62 readiness-supported in the current registry; 4 under extraction remediation.**

The earlier **13 enabled / 10 confirmed / 3 remediation** story is not safe today. The later **13 enabled / 9 readiness-supported / 4 remediation** story was safe until three proof-backed, repeat-baseline-complete queue sources were promoted to `sources.json` on 2026-06-15; the **19 / 15 / 4** story was supported after three additional ADGM/FSRA sources passed proof, repeat baseline, mass-monitor dry-run, and agent gates. A later ADGM FSRA Guidance and Policy activation advanced the truth to **20 / 16 / 4**. On 2026-06-15, three more sources from the 151-endpoint discovery sprint advanced the truth to **23 / 19 / 4**. In the JS-heavy remediation sprint, UAE FIU Trends and Typology Reports (`AE-uaefiu-typology-reports`) passed no-save with the `fiu_eocn_document_listing` adapter (q=65), two saved evidence runs (MONITORING_CERTIFIED, hash stable), mass-monitor dry-run (`MONITOR_OK`, no change), and all six agent gates, advancing the truth to **24 / 20 / 4**. The autonomous EOCN cycle then converted `AE-eocn-news-en` from a generic listing false-positive into a source-specific `eocn_news_listing` extraction, completed two stable evidence runs, passed mass-monitor dry-run (`MONITOR_OK`), and advanced the truth to **25 / 21 / 4**. The same autonomous cycle then cleaned invalid SCA pseudo-links in `sca_listing`, certified `AE-sca-regulations-listing` with two stable evidence runs, and advanced the truth to **26 / 22 / 4**. The continuation cycle then expanded SCA FATCA/CRS document extraction and ADGM FSRA web-component listing extraction, certified `AE-sca-fatca-crs` and `AE-adgm-listing-rules` with two stable evidence runs each, verified mass-monitor dry-run `MONITOR_OK`, and advanced the truth to **28 / 24 / 4**. The batch continuation then tested 20+ candidates, fixed deterministic table-header hashing, certified five more sources (`AE-sca-corporate-governance`, `AE-adgm-dp-guidance`, `AE-adgm-fsra-enforcement`, `AE-sca-aml-cft`, and `AE-dfsa-rulebook-thomsonreuters`), and advanced the truth to **33 / 29 / 4**. The weak-zone remediation cycle then fixed generic action-link title extraction for document/listing adapters, certified `AE-uaefiu-aml-cft-laws`, `AE-uaefiu-publications-hub`, and `AE-cbuae-rulebook-revision-updates` with two stable evidence runs each, verified mass-monitor dry-run `MONITOR_OK`, and advanced the truth to **36 / 32 / 4**. The weak-zone elimination cycle then used official VARA, CBUAE rulebook, DFSA, and official-linked Thomson Reuters endpoints, certified ten more sources with two stable proof runs and mass-monitor `MONITOR_OK`, and advanced the truth to **46 / 42 / 4**. The final-8 sprint then tested 66 candidate/config checks, certified twenty official CBUAE/DFSA rulebook and guidance sources with two proof runs each, held one DFSA source for dry-run hash drift, verified the activated sources with mass-monitor `MONITOR_OK`, and advanced the truth to **66 / 62 / 4**.

## Canonical Counts

| Count | Value | Basis |
| --- | ---: | --- |
| Total records in `sources.json` | 203 | Registry file parse after adding twenty proof-backed final-8 CBUAE/DFSA sources. |
| Enabled UAE sources | 66 | `enabled: true` and `jurisdiction: AE`. |
| Readiness-supported | 62 | Enabled UAE registry rows with `status: active`, excluding held/remediation rows. |
| Under extraction remediation | 4 | Enabled UAE registry rows with `status: remediation`. |
| Blocked / failed | 0 | Current registry uses remediation rather than blocked for the four not-ready sources. |

## Readiness-Supported Sources

| Source ID used in reports/UI | Source name | Reason it remains readiness-supported |
| --- | --- | --- |
| `AE-central-bank-of-the-uae` | Central Bank of the UAE | Current readiness report lists proof/hash/run artifacts and registry support. |
| `AE-dubai-virtual-assets-regulatory-authority-vara` | Dubai Virtual Assets Regulatory Authority (VARA) | Current readiness report lists proof/hash/run artifacts and meaningful extraction. |
| `AE-abu-dhabi-global-market-adgm` | Abu Dhabi Global Market (ADGM) | Current readiness report keeps main ADGM source readiness-supported with caveats. |
| `AE-uae-ministry-of-finance` | UAE Ministry of Finance | Current readiness report lists meaningful extraction and evidence artifacts. |
| `AE-uae-legislation-portal` | UAE Legislation Portal | Current readiness report lists meaningful extraction and evidence artifacts. |
| `AE-uae-ministry-of-economy` | UAE Ministry of Economy | Current readiness report lists meaningful extraction and evidence artifacts. |
| `AE-vara-enforcement` | VARA Enforcement Notices | Current readiness report lists meaningful extraction and unique hash. |
| `AE-cbuae-regulations` | CBUAE Regulations Sub-page | Current readiness report lists meaningful extraction with known counter-change noise caveat. |
| `AE-uaefiu-circulars` | UAE FIU Circulars and Notices | Current readiness report treats publications/circulars as the readiness-supported FIU source. |
| `AE-sca-circulars-rules-procedures` | SCA Circulars, Rules and Procedures | Promoted from activation-ready queue after proof-backed repeat baseline and mass-monitor dry-run. |
| `AE-sca-regulations-listing` | SCA Regulations Listing | Promoted after SCA listing extraction, invalid pseudo-link cleanup, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-dfsa-financial-crime-mlro-letters` | DFSA Financial Crime Prevention Notices and MLRO Letters | Promoted from activation-ready queue after proof-backed repeat baseline and mass-monitor dry-run. |
| `AE-dfsa-aml-rulebook-module` | DFSA AML Rulebook Module | Promoted from activation-ready queue after proof-backed repeat baseline and a scoped monitor-path dry-run reproduced the stored hash. |
| `AE-adgm-fsra-financial-crime-prevention` | ADGM FSRA Financial and Cyber Crime Prevention | Promoted from activation-ready queue after focused custom-element extraction, proof-backed repeat baseline, and mass-monitor dry-run. |
| `AE-adgm-fsra-rulebooks` | ADGM FSRA Rules and Regulations | Promoted from activation-ready queue after proof-backed repeat baseline and mass-monitor dry-run on the current ADGM legal-framework URL. |
| `AE-adgm-fsra-consultations` | ADGM Public Consultations | Promoted from activation-ready queue after focused custom-element extraction, proof-backed repeat baseline, and mass-monitor dry-run. |
| `AE-adgm-fsra-guidance-policy` | ADGM FSRA Guidance and Policy Statements | Promoted after custom-element extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-eocn-laws-regulations-en` | EOCN AML/CFT Laws and Regulations | Promoted after listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-adgm-fsra-waivers` | ADGM FSRA Waivers and Modifications Register | Promoted after custom-element extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-adgm-ra-circulars` | ADGM Registration Authority Circulars | Promoted after custom-element extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-uaefiu-typology-reports` | UAE FIU Trends and Typology Reports | Promoted after FIU/EOCN document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-eocn-news-en` | EOCN News and Sanctions Updates | Promoted after source-specific EOCN news listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-sca-fatca-crs` | SCA FATCA and CRS Guidance | Promoted after SCA listing extraction was expanded for FATCA/CRS document links, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-adgm-listing-rules` | ADGM FSRA Listing Authority Rules and Guidance | Promoted after ADGM web-component document listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-sca-corporate-governance` | SCA Corporate Governance Regulations | Promoted after table adapter header normalization, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-adgm-dp-guidance` | ADGM Data Protection Guidance | Promoted after focused custom-element extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-adgm-fsra-enforcement` | ADGM FSRA Enforcement | Promoted after focused custom-element extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-sca-aml-cft` | UAE SCA Anti-Money Laundering and Terrorist Financing | Promoted after `sca_listing` extraction isolated AML/CFT document links, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-dfsa-rulebook-thomsonreuters` | DFSA Rulebook Modules | Promoted after officially linked Thomson Reuters rulebook module extraction with `article` selector, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-uaefiu-aml-cft-laws` | UAE FIU AML/CFT Laws and Related Decisions | Promoted after weak-zone FIU listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-uaefiu-publications-hub` | UAE FIU Publications Hub | Promoted after FIU/EOCN document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-rulebook-revision-updates` | CBUAE Rulebook Revision Updates | Promoted after official Central Bank rulebook subdomain extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-vara-rulebook-updates` | VARA Rulebook Revision Updates | Promoted after official VARA rulebook update extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-dfsa-consultation-current` | DFSA Consultation Papers Current | Promoted after current official DFSA consultation listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-dfsa-enforcement-decisions-current` | DFSA Published Enforcement Decisions | Promoted after official DFSA enforcement decision listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-dfsa-regulatory-actions-current` | DFSA Enforcement Regulatory Actions | Promoted after official DFSA regulatory action listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-retail-payment-services-rulebook` | CBUAE Retail Payment Services and Card Schemes Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-dfsa-consultation-paper-165` | DFSA Consultation Paper No.165 | Promoted after official-linked Thomson Reuters DFSA consultation listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-dfsa-notice-supervisory-review` | DFSA Supervisory Review Rulebook | Promoted after official-linked Thomson Reuters DFSA rulebook extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-amlcft-rulebook-doclist` | CBUAE AML/CFT Rulebook Document Links | Promoted after stable CBUAE document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-amlcft-entire-section-doclist` | CBUAE AML/CFT Entire Section Document Links | Promoted after stable CBUAE document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-consumer-protection-rulebook-doclist` | CBUAE Consumer Protection Regulation Document Links | Promoted after stable CBUAE document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-open-finance-rulebook` | CBUAE Open Finance Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-payment-token-services-rulebook` | CBUAE Payment Token Services Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-risk-management-rulebook` | CBUAE Risk Management Rulebook | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-stored-value-facilities-doclist` | CBUAE Stored Value Facilities Regulation | Promoted after exact official CBUAE rulebook URL remediation, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-operational-risk-regulation-doclist` | CBUAE Operational Risk Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-market-risk-regulation-doclist` | CBUAE Market Risk Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-large-exposures-regulation-doclist` | CBUAE Large Exposures Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-exchange-business-regulation-doclist` | CBUAE Exchange Business Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-capital-adequacy-doclist` | CBUAE Capital Adequacy | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-large-value-payment-systems-doclist` | CBUAE Large Value Payment Systems Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-federal-decree-law-6-2025-doclist` | Federal Decree Law No. 6 of 2025 Regarding the Central Bank | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-country-transfer-risk-regulation-doclist` | CBUAE Country and Transfer Risk Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-interest-rate-risk-regulation-doclist` | CBUAE Interest Rate and Rate of Return Risk Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-model-management-standards-doclist` | CBUAE Model Management Standards | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-retail-payment-systems-regulation-doclist` | CBUAE Retail Payment Systems Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-sme-customer-protection-regulation-doclist` | CBUAE SME Customer Protection Regulation | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-islamic-banks-risk-management-doclist` | CBUAE Islamic Banks Risk Management Standard | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-market-conduct-consumer-protection-doclist` | CBUAE Market Conduct and Consumer Protection | Promoted after official CBUAE rulebook document-listing extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-proliferation-finance-guidance-doclist` | CBUAE Proliferation Finance Guidance | Promoted after official CBUAE AML guidance extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |
| `AE-cbuae-tbml-transshipment-guidance-doclist` | CBUAE TBML and Transshipment Guidance | Promoted after official CBUAE AML guidance extraction, proof-backed repeat baseline, mass-monitor dry-run, and agent gates. |

## Sources Under Extraction Remediation

| Source ID used in reports/UI | Source name | Reason |
| --- | --- | --- |
| `AE-dubai-financial-services-authority-dfsa` | DFSA Rulebook / DFSA main source | Current configured URL renders a page-not-found/nav-shell result and collides with DFSA notices. A stronger rulebook candidate exists, but only as no-save preview with `BASELINE_REQUIRED`. |
| `AE-dfsa-notices` | DFSA Regulatory Notices | Current configured URL renders a page-not-found/nav-shell result and collides with the DFSA rulebook source. The intended source model is ambiguous. |
| `AE-difc-laws-and-regulations` | DIFC Laws and Regulations | Extraction appears meaningful, but the current readiness report keeps it under registry hold pending Source Monitor and Evidence Trail review. |
| `AE-uae-financial-intelligence-unit-uaefiu` | UAE FIU Homepage | Homepage extraction is too shallow for primary regulatory monitoring. UAE FIU Circulars and Notices is the readiness-supported FIU source. |

## Which Story Is Correct?

**Correct today:** 66 enabled / 62 readiness-supported / 4 under extraction remediation.

**Not correct today:** 13 enabled / 10 confirmed / 3 under extraction remediation.

Reason: the final-8 sprint moved the registry and work queue over the 50-source gate using proof-backed, repeat-baseline-complete, mass-monitor-checked official CBUAE/DFSA sources. DIFC Laws, the legacy DFSA configured sources, and the UAE FIU homepage remain held/remediation. A source may have meaningful extraction while still not being customer-visible ready if its registry hold, source model, evidence baseline, or activation review is incomplete.

## Allowed Customer-Facing Wording

- "66 enabled UAE sources."
- "62 readiness-supported in the current registry."
- "50 activation-ready UAE official source endpoints."
- "Each activation-ready source passed proof, baseline, source-health, noise, and review gates."
- "4 under extraction remediation."
- "Source readiness in progress."
- "DFSA source model under remediation."
- "DIFC Laws and Regulations remains under registry hold pending Source Monitor and Evidence Trail review."
- "UAE FIU Circulars and Notices is the readiness-supported FIU source; the UAE FIU homepage remains under remediation."
- "Evidence-backed monitoring requires proof artifacts and baseline review before activation."

## Forbidden Wording

- "All 66 sources are validated."
- "All 66 sources are confirmed."
- "All 66 sources are ready."
- "10 confirmed" unless DIFC is explicitly released from remediation by Source Monitor and Evidence Trail.
- "DFSA ready."
- "DIFC ready" while the registry hold remains.
- "Certified monitoring."
- "Perfect parsing."
- "Any website can be parsed."
- "Guaranteed compliance."

## Code And UI Result

Current public/app source tables should use the 66/62/4 model:

- `product/regradar/web/src/components/SourceCoverageTable.jsx`
- `product/regradar/web/src/data/appMockData.js`
- Pricing and billing surfaces use "66 enabled" with 62 readiness-supported and 4 under remediation only where public truth is intentionally surfaced.

This sprint changes `sources.json` only for proof-backed, repeat-baseline-complete, mass-monitor-checked activation-ready sources. Future changes should derive source IDs and counts from one generated registry summary rather than duplicating constants in frontend/docs.

## Next Required Source Readiness Work

1. Diversify beyond CBUAE by implementing direct PDF extraction for official VARA PDF rulebooks.
2. Resolve DIFC data protection / legal-database access and selector blockers without bypassing protections.
3. Find ADGM alternate component selectors or replacement URLs for data-protection regulatory actions and listing announcements.
4. Add a generated source-readiness summary artifact consumed by validators and frontend source tables.
