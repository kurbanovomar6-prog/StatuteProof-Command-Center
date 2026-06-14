# UAE 50 Target Source Selection

Date: 2026-06-14

## 1. Selection Verdict

Selected primary targets: **50**.

Backup targets: **5**.

This is an attempt set, not a working-source claim. Public source truth remains:

`13 enabled UAE sources / 9 readiness-supported / 4 under extraction remediation`

## 2. Selection Rules Applied

Included:

- official or officially linked UAE sources;
- sources relevant to UAE MLRO/CCO/compliance/legal teams;
- regulator pages, rulebooks, regulations, consultations, notices, publications, sanctions/AML pages, and public registers where relevant;
- sources that can plausibly become working after adapter/proof/baseline work.

Excluded:

- blogs, law firm pages, news commentary, social media;
- non-UAE regulators;
- generic homepages when better subpages exist, except as discovery-only backup;
- pages already known to be private, paywalled, login-only, CAPTCHA-only, or wrong-country;
- random PDFs with unclear compliance value.

## 3. Primary 50 Targets

| # | target_id | regulator | source type | adapter needed | priority | current status | activation blocker |
|---:|---|---|---|---|---|---|---|
| 1 | `AE-vara-aml-cft-rulebook` | VARA | AML guidance/rulebook | VARA PDF/rulebook listing | P0 | remediation | Current URL returned shell; needs official URL/selector remediation. |
| 2 | `AE-vara-company-rulebook` | VARA | rulebook | VARA PDF/rulebook listing | P0 | remediation | Current URL returned shell; needs official URL/selector remediation. |
| 3 | `AE-vara-enforcement` | VARA | enforcement | VARA enforcement listing | P0 | remediation | Nav-shell under strict scoring; needs item-level adapter. |
| 4 | `AE-vara-regulatory-framework` | VARA | rulebook/framework | VARA page/PDF listing | P0 | remediation | Current extraction shell-like; needs selector/PDF discovery. |
| 5 | `AE-vara-rulebooks-overview` | VARA | rulebook | VARA PDF/rulebook listing | P0 | remediation | Current URL returned not-found shell. |
| 6 | `AE-vara-homepage` | VARA | regulator homepage | not default; discovery only | P1 | remediation | Homepage is too broad/noisy for activation. |
| 7 | `AE-vara-public-register` | VARA | register | register/listing adapter | P1 | remediation | Needs public register adapter and noise policy. |
| 8 | `AE-vara-news` | VARA | publication | listing adapter | P2 | candidate | Lower priority; news noise risk. |
| 9 | `AE-adgm-fsra-rulebooks` | ADGM/FSRA | rulebook | custom_element + link normalization | P0 | activation_ready candidate | Needs final source-registry approval. |
| 10 | `AE-adgm-fsra-guidance-policy` | ADGM/FSRA | guidance | ADGM listing adapter | P0 | readiness-supported no-save | Needs item-level filters, proof, baseline. |
| 11 | `AE-adgm-fsra-notices` | ADGM/FSRA | notice | ADGM listing adapter | P0 | remediation | Previous URLs produced nav/404 shell. |
| 12 | `AE-adgm-fsra-consultations` | ADGM/FSRA | consultation | ADGM listing/status adapter | P1 | readiness-supported no-save | High archive/listing noise; needs item-level diff. |
| 13 | `AE-adgm-fsra-enforcement` | ADGM/FSRA | enforcement | ADGM listing adapter | P1 | readiness-supported no-save | Source label/model is too broad; needs split/confirmation. |
| 14 | `AE-adgm-fsra-homepage` | ADGM/FSRA | regulator homepage | not default; discovery only | P1 | remediation | Too broad; use specific pages. |
| 15 | `AE-adgm-fsra-public-register` | ADGM/FSRA | register | register/table adapter | P1 | remediation | Shallow/register risk; needs adapter and manual policy. |
| 16 | `AE-adgm-legal-framework-rules` | ADGM | regulation/rules | custom_element | P1 | readiness-supported no-save | Duplicates/overlaps with `AE-adgm-fsra-rulebooks`. |
| 17 | `AE-adgm-legal-framework-legislation` | ADGM | law | custom_element/listing | P1 | remediation | Previous URL shell-like; needs subpage investigation. |
| 18 | `AE-adgm-data-protection` | ADGM | data protection | custom_element/static_html | P2 | candidate | Relevant only when customer scope includes privacy. |
| 19 | `AE-dfsa-aml-mlro-notices` | DFSA | AML notice | DFSA listing adapter | P0 | readiness-supported no-save | Needs proof/baseline and listing noise filters. |
| 20 | `AE-dfsa-rulebook-thomsonreuters` | DFSA | rulebook | rulebook module adapter | P0 | readiness-supported no-save | Needs proof/baseline; officially linked third-party host must be documented. |
| 21 | `AE-dfsa-enforcement-regulatory-actions` | DFSA | enforcement | DFSA listing adapter | P0 | remediation | Current extraction blocked/shell-like. |
| 22 | `AE-dfsa-rulebook-official` | DFSA | rulebook | DFSA page adapter | P0 | remediation | Official page blocked/shell-like; TR rulebook may be better source. |
| 23 | `AE-dfsa-aml-ctf-sanctions` | DFSA | AML guidance | custom/listing adapter | P1 | candidate | Broad source; use specific notices first. |
| 24 | `AE-dfsa-public-register` | DFSA | register | register/table adapter | P1 | candidate | Search/table source; activation only if public/static enough. |
| 25 | `AE-dfsa-consultation-papers` | DFSA | consultation | listing adapter | P1 | remediation | Current URL returned page-not-found/shell. |
| 26 | `AE-dfsa-publications` | DFSA | publication | listing adapter | P2 | candidate | Lower priority than specific publication classes. |
| 27 | `AE-difc-legal-database` | DIFC | legal database | listing/search adapter | P1 | candidate | Needs no-save check and search-shell review. |
| 28 | `AE-difc-laws-regulations` | DIFC | law/regulation | static/listing adapter | P1 | remediation | Blocked under previous Source Lab check. |
| 29 | `AE-difc-consultation-papers` | DIFC | consultation | listing adapter | P2 | candidate | Lower priority than DFSA-specific sources. |
| 30 | `AE-difc-data-protection` | DIFC | data protection | static/listing adapter | P2 | candidate | Include only if customer scope includes privacy. |
| 31 | `AE-cbuae-aml-cft` | CBUAE | AML guidance | CBUAE page/listing adapter | P0 | remediation | Blocked/chrome-heavy; needs source-specific adapter or alternate official URL. |
| 32 | `AE-cbuae-regulations` | CBUAE | regulation | CBUAE listing/document adapter | P0 | remediation | Blocked/chrome-heavy; needs official list extraction. |
| 33 | `AE-cbuae-consultations` | CBUAE | consultation | CBUAE listing adapter | P1 | remediation | Blocked/chrome-heavy. |
| 34 | `AE-cbuae-homepage` | CBUAE | regulator homepage | discovery only | P1 | remediation | Too broad/noisy for default active monitoring. |
| 35 | `AE-cbuae-licensing` | CBUAE | licensing | static/listing adapter | P1 | remediation | Chrome-heavy, policy warnings. |
| 36 | `AE-cbuae-payment-systems` | CBUAE | payment regulation | static/listing adapter | P1 | remediation | Current URL returned 404/chrome shell. |
| 37 | `AE-cbuae-publications` | CBUAE | publication | CBUAE document listing adapter | P1 | remediation | Chrome-heavy; needs document link extraction. |
| 38 | `AE-cbuae-consumer-protection` | CBUAE | guidance | static/listing adapter | P2 | candidate | Useful for broader compliance, not core MLRO first pack. |
| 39 | `AE-cbuae-news` | CBUAE | publication/news | listing adapter | P2 | candidate | Not substitute for regulation/circular pages. |
| 40 | `AE-cbuae-open-data` | CBUAE | data/table | table adapter | P2 | candidate | Use only if compliance evidence use case is clear. |
| 41 | `AE-uaefiu-goaml-public` | UAE FIU | AML guidance | FIU document/static adapter | P0 | remediation | Blocked/search-shell output. |
| 42 | `AE-uaefiu-publications` | UAE FIU | publication | FIU document listing adapter | P0 | remediation | Blocked/search-shell output. |
| 43 | `AE-uaefiu-laws-regulations` | UAE FIU | law/regulation | FIU listing adapter | P1 | remediation | Blocked/search-shell output. |
| 44 | `AE-uaefiu-awareness` | UAE FIU | guidance | static/listing adapter | P2 | candidate | Lower priority than publications/goAML. |
| 45 | `AE-uaefiu-homepage` | UAE FIU | regulator homepage | discovery only | P2 | remediation | Homepage shallow; prefer publications. |
| 46 | `AE-eocn-homepage` | EOCN | sanctions/TFS | EOCN listing/document adapter | P0 | remediation | Blocked/chrome-heavy; need sanctions-specific public pages. |
| 47 | `AE-moec-aml` | Ministry of Economy | AML guidance | MoE static/listing adapter | P1 | remediation | Blocked/chrome-heavy. |
| 48 | `AE-uae-legislation-portal` | UAE Legislation | law | legislation portal adapter | P1 | remediation | Security-check/nav shell; may be blocked for monitoring. |
| 49 | `AE-mof-homepage` | Ministry of Finance | finance ministry | discovery only | P1 | remediation | Homepage/chrome-heavy; only include compliance-relevant subpages later. |
| 50 | `AE-sca-circulars` | SCA | circular | SCA rendered listing adapter | P1 | remediation | Needs item/card extraction adapter. |

## 4. Backup Targets

| backup | target_id | regulator | reason |
|---:|---|---|---|
| 51 | `AE-sca-decisions` | SCA | Useful if latest-regulations can isolate decision items. |
| 52 | `AE-sca-laws` | SCA | Useful if official list endpoint can be isolated. |
| 53 | `AE-sca-legislation` | SCA | Legacy URL likely stale; backup only. |
| 54 | `AE-sca-regulations` | SCA | Legacy model, likely replaced by latest-regulations candidate. |
| 55 | `AE-sca-homepage` | SCA | Discovery only; should not be active if specific pages exist. |

## 5. Fastest Activation Path

Fastest honest activation path:

1. Confirm the 2 ADGM activation-ready candidates can be safely added to `sources.json`.
2. Save and repeat-baseline the 4-6 no-save readiness-supported ADGM/DFSA candidates.
3. Build SCA rendered-listing adapter and retry SCA latest/AML/circulars.
4. Add DFSA rulebook/listing adapters.
5. Add CBUAE/FIU/VARA document listing adapters.

This selection is enough to attempt 50, but it is not enough to claim 50.
