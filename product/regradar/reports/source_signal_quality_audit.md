# StatuteProof Source Signal Quality Audit

Audit date: 2026-07-18
Auditor: StatuteProof Source Quality Auditor v2
Source file: `product/regradar/sources.json`

## Current Source Truth

| Metric | Count |
| --- | ---: |
| Enabled UAE sources | 117 |
| Fresh-alert eligible | 38 |
| Evidence-library only | 20 |
| Candidate | 14 |
| Remediation | 45 |
| Source-level MONITOR_OK | 42 |
| Sources with proof path | 86 |

These are monitoring-truth counts, not legal completeness claims. The 2026-07-18 register review
re-measured every fresh-alert claim from the PRODUCTION monitoring vantage: sources whose host blocks
production egress (rulebook.centralbank.ae, www.dfsa.ae — HTTP 403 to all fetch methods since
2026-07-11) were demoted to remediation and are no longer counted, per the pricing-page promise that
unreachable sources are not counted as fresh-alert eligible coverage.

## Family Readiness

| Family | Total | Fresh alert | Evidence library | Candidate | Remediation | Label | Gap to 25 |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| CBUAE | 25 | 0 | 0 | 0 | 25 | Remediation Production Access | 25 |
| VARA | 7 | 3 | 2 | 1 | 1 | Partial | 22 |
| DFSA | 16 | 2 | 2 | 2 | 10 | Partial Production Access | 24 |
| DIFC | 12 | 8 | 3 | 0 | 1 | Good | 17 |
| ADGM/FSRA | 14 | 9 | 2 | 3 | 0 | Good | 16 |
| Ministry of Economy / DNFBP AML | 8 | 0 | 2 | 0 | 6 | Remediation | 25 |
| FTA | 6 | 0 | 0 | 6 | 0 | Partial | 25 |
| EOCN / sanctions / TFS | 6 | 4 | 0 | 1 | 1 | Selected Source Pilot Ready | 19 |
| SCA | 6 | 5 | 0 | 0 | 1 | Partial | 20 |
| UAE FIU | 0 | 0 | 0 | 0 | 0 | Partial | 25 |
| Ministry of Finance | 8 | 7 | 1 | 0 | 0 | Selected Source Pilot Ready | 18 |
| Ministry of Justice / UAE Legislation / Gazette | 3 | 0 | 3 | 0 | 0 | Partial | 25 |
| Other UAE official sources | 6 | 0 | 5 | 1 | 0 | Evidence Library | 25 |

The family rows partition the full enabled register: each enabled source is counted in exactly one
family (the MoE-owned targeted financial sanctions page is counted once, under EOCN / sanctions /
TFS), and the "Other UAE official sources" row carries every enabled source outside the named
families, so every column above sums exactly to the headline Current Source Truth counts
(117 / 38 / 20 / 14 / 45). Family fresh-alert counts use the same mode + alert-eligible definition
as the headline; where a 2026-07-18 promotion (DFSA AML rulebook module, VARA Compliance & Risk
Management Rulebook) still awaits its registry readiness-field sync from the next production
intake, the family note says so explicitly.

## Family Notes

- CBUAE: All 25 CBUAE rulebook sources are held in remediation as a production-egress disclosure, not a content problem: rulebook.centralbank.ae returns HTTP 403 to our production monitoring egress on every fetch method (persistent since 2026-07-11). Sources stay enabled and disclosed; none is counted as fresh-alert until MONITOR_OK is verified from production (restore path: production fetch proxy, owner decision).
- VARA: 2 VARA sources pass the full readiness gate (news/circulars, enforcement). The Compliance and Risk Management Rulebook (incl. AML/CFT Part III) was promoted to fresh_alert on 2026-07-18 after two stable production runs and counts in the headline and in this row; its registry proof fields sync on the next intake. The 30-day revision-updates view is in remediation pending a production rebaseline. The public register is held as an evidence-library snapshot and the regulatory-notices/enforcement index is a candidate pending validation. This is selected-source monitoring, not complete VARA coverage.
- DFSA: The 10 www.dfsa.ae sources are held in remediation as a production-egress disclosure, not a content problem (HTTP 403 to our production egress on all methods since 2026-07-11). DFSA depth continues via the dfsaen.thomsonreuters.com rulebook platform, which does work from production — the rulebook source passes the full readiness gate and the AML rulebook module was promoted to fresh_alert on 2026-07-18 after rebaseline plus stable-run gates (its registry readiness fields sync on the next intake). The DFSA public register is held as an evidence-library snapshot; the news hub (legislative amendment notices) and SEO letters listings are candidates pending validation under the same production-egress constraint.
- DIFC: DIFC has 8 fresh-alert sources including the official DIFC Legal Database listing; the laws-and-regulations root listing moved to remediation on 2026-07-18 after three consecutive QUALITY_DROP production runs (pending audit-record review and a production rebaseline). Three DIFC listing pages (Courts practice directions, Registrar's directions, news/announcements hub) are held as evidence-library snapshots. This is selected DIFC monitoring, not complete DIFC legal database coverage.
- ADGM/FSRA: ADGM/FSRA has 9 fresh-alert sources including guidance/policy and RA/circular/rulebook style sources. Three candidate rows remain held until selectors/extraction pass the same gates, and two listing pages (Office of Data Protection, media announcements hub) are held as evidence-library snapshots.
- Ministry of Economy / DNFBP AML: All 6 MoE DNFBP sources remain under source remediation — earlier captures were a site-maintenance page, which the quality gate rejects; none is counted until re-baselined on real content. The MoE-owned targeted financial sanctions page is counted once, under EOCN / sanctions / TFS. Two evidence-library pages (the MoE homepage and the AML/CFT hub) are kept as snapshots only.
- FTA: No FTA sources are currently fresh-alert eligible. FTA portal/listing extraction remains candidate/adapter work (6 candidate listings, including the VAT public clarifications listing) and is not counted as fresh-alert.
- EOCN / sanctions / TFS: 4 selected EOCN/TFS-related sources are fresh-alert eligible across direct EOCN and MoE-owned TFS support. The duplicate UAEIEC news listing (same page as the EOCN news listing on a second domain) is held as a dedupe candidate, and one MoE TFS page remains in remediation. This is not complete sanctions coverage.
- SCA: UAE CMA has 5 proof-backed fresh-alert direct/listing sources. The circulars/rules/procedures page moved to remediation on 2026-07-18: production runs have been stuck in QUALITY_DROP against a stale pre-repoint baseline since the 2026-07-12 URL repoint (production rebaseline pending). UAE CMA AML/CFT parser/noise review still blocks broad UAE CMA positioning.
- UAE FIU: UAE FIU has no fresh-alert eligible sources currently.
- Ministry of Finance: MoF has seven proof-backed fresh-alert sources plus one evidence-library homepage after adding selected MoF-owned DMTT/top-up tax, corporate tax, AEOI/FATCA/CRS, and UAE financial framework pages with repeat baseline and mass-monitor MONITOR_OK. This is selected MoF monitoring, not complete MoF or complete tax coverage.
- Ministry of Justice / UAE Legislation / Gazette: MoJ/Gazette has no fresh-alert eligible sources currently. Root portal, e-Laws, and complete Official Gazette coverage remain unclaimed. Three listing pages (Dubai legislation portal laws search, MoJ news, MoJ media centre) are held as evidence-library snapshots.
- Other UAE official sources: Cross-regulator UAE official sources outside the named families: the DFM regulatory circulars listing is a candidate pending validation, and the ICP, TDRA, MOCCAE, JAFZA and DMCC listing pages are held as evidence-library snapshots. None is counted as fresh-alert monitoring.

## Safe Product Claims

- StatuteProof has 38 fresh-alert-eligible UAE official-source endpoints counted from the production monitoring vantage as of the source-register review (2026-07-18).
- StatuteProof also maintains 20 evidence-library UAE official/static source snapshots that are not counted as fresh-alert monitoring.
- Sources whose hosts block our production monitoring egress — the CBUAE rulebook subdomain and the DFSA website (HTTP 403 to all fetch methods since 2026-07-11) — are disclosed as remediation and are not counted as fresh-alert eligible.
- DFSA rulebook depth continues through the DFSA rulebook platform at dfsaen.thomsonreuters.com, which does work from production, including the AML rulebook module promoted on 2026-07-18 after passing rebaseline and stable-run gates.
- StatuteProof maintains source-level proof files for 86 of 117 enabled UAE source snapshots; this is not customer risk-brief eligibility.
- ADGM/FSRA has 9 selected proof-backed fresh-alert sources, including guidance/policy and RA/circular/rulebook style sources, with 3 remaining candidates disclosed as held.
- DIFC has 8 selected proof-backed fresh-alert sources, including the official DIFC Legal Database listing; the laws-and-regulations root listing is in remediation pending a production rebaseline review. This is not complete DIFC legal database coverage.
- UAE CMA has 5 selected proof-backed fresh-alert direct/listing sources; the circulars/rules/procedures page is in remediation pending a production rebaseline, and UAE CMA root portal and broad UAE CMA coverage remain unclaimed.
- MoJ/Gazette has no fresh-alert eligible sources currently; root portal, e-Laws, and complete Official Gazette coverage remain unclaimed.
- MoF monitoring has 7 fresh-alert eligible official MoF sources plus one evidence-library homepage, including selected publications/releases, financial legislation, ESR, DMTT/top-up tax, corporate tax, AEOI/FATCA/CRS, and UAE financial framework pages.
- MoE/DNFBP AML sources remain under source remediation on a maintenance-stub baseline and are not counted as fresh-alert monitoring.
- VARA monitoring includes the full Compliance and Risk Management Rulebook (including AML/CFT Part III) promoted on 2026-07-18 after two stable production runs; the 30-day revision-updates view is in remediation pending a production rebaseline.

## Forbidden Claims

- Do not describe all 117 enabled UAE source records as live monitors.
- Do not count sources whose host blocks production egress as fresh-alert eligible.
- Do not describe CBUAE rulebook sources as live monitors while production egress is blocked.
- Do not describe UAE coverage as complete.
- Do not describe UAE legislation coverage as complete.
- Do not describe MoJ/Gazette coverage as complete.
- Do not describe MoF coverage as complete.
- Do not claim complete tax coverage from MoF or FTA sources.
- Do not claim Official Gazette monitoring is complete.
- Do not describe sanctions coverage as complete.
- Do not describe VARA coverage as complete.
- Do not describe UAE CMA coverage as full.
- Do not claim UAE FIU circulars have fresh-alert MONITOR_OK.
- Do not claim complete ADGM/FSRA coverage.
- Do not claim complete DIFC legal database coverage.
- Do not claim UAE CMA root portal monitoring.
- Do not promise compliance outcomes.
- Do not present monitoring intelligence as legal advice.
- Do not promise every regulatory update will be captured.

## Known Limitations

- CBUAE: rulebook.centralbank.ae blocks our production monitoring egress (HTTP 403 to all fetch methods, persistent since 2026-07-11). All 25 CBUAE rulebook sources are disclosed as remediation and not counted as fresh-alert eligible — this is a production-access disclosure, not a content problem. Restore path: production fetch proxy (owner decision), then re-verify MONITOR_OK from production.
- DFSA: www.dfsa.ae blocks our production monitoring egress (HTTP 403 to all fetch methods, persistent since 2026-07-11); 10 DFSA-site sources are disclosed as remediation and not counted. DFSA rulebook depth continues via dfsaen.thomsonreuters.com, which works from production (rulebook + AML rulebook module).
- ADGM/FSRA: ADGM/FSRA has 9 selected proof-backed fresh-alert sources. Waivers, regulatory alerts, RA notices, RA AML guides, listing announcements, and Abu Dhabi/federal legislation pages remain held where current proof/baseline or selector gates did not pass cleanly.
- DIFC: DIFC has 8 selected proof-backed fresh-alert sources including the official Legal Database listing; the laws-and-regulations root listing is in remediation pending a production rebaseline review. This does not prove complete DIFC legal database coverage or item-level legal-change completeness.
- UAE CMA: UAE CMA has 5 proof-backed fresh-alert direct/listing sources; the circulars/rules/procedures page is in remediation pending a production rebaseline. UAE CMA AML/CFT parser/noise review remains unresolved and UAE CMA root portal monitoring remains unclaimed.
- UAE FIU: UAE FIU has no fresh-alert eligible sources: the goAML/FIU portal is geo-blocked from our monitoring region, and the held circulars candidate resolves to the general publications index rather than a distinct circular/notice endpoint.
- EOCN / sanctions / TFS: 4 selected EOCN sanctions-related sources are fresh-alert eligible. This is selected-source monitoring, not complete sanctions coverage.
- UAE Legislation / MoJ / Gazette: One selected UAE Legislation Platform listing is fresh-alert eligible. The root UAE Legislation Portal, UAE e-Laws/MoJ portal, and complete Official Gazette monitoring remain unclaimed because root/sitemap access and item-level Gazette routes are not fully proven.
- Ministry of Finance: MoF has 7 selected proof-backed fresh-alert sources plus one evidence-library homepage. This still excludes complete MoF, complete tax, broad public-debt, DTAs, budget archive, open-data statistical reports, and every MoF publication category unless each source passes its own proof/baseline gate.

## Risk-Brief Boundary

Source snapshot proof is not a canonical evidence record. Customer risk briefs remain blocked until complete evidence-record.json packages and brief eligibility gates exist.

StatuteProof reports are generated from monitored official-source records and are provided for information and compliance review support only. This audit does not constitute legal advice, regulatory advice, compliance certification, or a legal opinion.
