# StatuteProof Source Signal Quality Audit

Audit date: 2026-06-21
Auditor: StatuteProof Source Quality Auditor v2
Source file: `product/regradar/sources.json`

## Current Source Truth

| Metric | Count |
| --- | ---: |
| Enabled UAE sources | 246 |
| Fresh-alert eligible | 180 |
| Evidence-library only | 60 |
| Candidate | 4 |
| Remediation | 2 |
| Source-level MONITOR_OK | 234 |
| Sources with proof path | 237 |

These are monitoring-truth counts, not legal completeness claims.

## Family Readiness

| Family | Total | Fresh alert | Evidence library | Candidate | Remediation | Label | Gap to 25 |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| CBUAE | 27 | 25 | 1 | 1 | 0 | Strong Selected Source | 0 |
| VARA | 26 | 25 | 1 | 0 | 0 | Strong Selected Source | 0 |
| DFSA | 44 | 16 | 28 | 0 | 0 | Good | 9 |
| DIFC | 25 | 11 | 14 | 0 | 0 | Good | 14 |
| ADGM/FSRA | 27 | 11 | 14 | 2 | 0 | Good | 14 |
| Ministry of Economy / DNFBP AML | 43 | 42 | 1 | 0 | 0 | Strong Selected Source | 0 |
| FTA | 25 | 25 | 0 | 0 | 0 | Strong Selected Source | 0 |
| EOCN / sanctions / TFS | 25 | 25 | 0 | 0 | 0 | Strong Selected Source | 0 |
| SCA | 6 | 6 | 0 | 0 | 0 | Partial | 19 |
| UAE FIU | 8 | 6 | 0 | 1 | 1 | Partial | 19 |
| Ministry of Finance | 8 | 7 | 1 | 0 | 0 | Selected Source Pilot Ready | 18 |
| Ministry of Justice / UAE Legislation / Gazette | 2 | 1 | 0 | 0 | 1 | Partial | 24 |

## Family Notes

- CBUAE: 25 CBUAE rulebook/regulatory sources are fresh-alert eligible. The generic homepage remains evidence-library and the generic regulations page remains candidate/held.
- VARA: 25 selected official VARA rulebook, circular, publication, regulatory, and enforcement-table sources are fresh-alert eligible. This is selected-source monitoring, not complete VARA coverage.
- DFSA: DFSA has 16 fresh-alert sources. Static individual news/notice pages stay evidence-library and must not inflate fresh monitoring claims.
- DIFC: DIFC has 11 fresh-alert sources after the official DIFC Legal Database listing passed proof-backed repeat baseline and mass-monitor MONITOR_OK. Individual static whats-on pages remain evidence-library. This is selected DIFC monitoring, not complete DIFC legal database coverage.
- ADGM/FSRA: ADGM/FSRA has 11 fresh-alert sources after guidance and policy statements passed proof-backed repeat baseline and mass-monitor MONITOR_OK. Two candidate rows remain held until selectors/extraction pass the same gates.
- Ministry of Economy / DNFBP AML: 42 MoE/DNFBP AML sources are fresh-alert eligible, plus one evidence-library homepage.
- FTA: 25 direct official FTA tax PDF endpoints are fresh-alert eligible. Broader FTA portal/listing extraction remains candidate/adapter work and is not counted as fresh-alert.
- EOCN / sanctions / TFS: 25 selected EOCN/TFS-related sources are fresh-alert eligible across direct EOCN/UAEIEC and MoE-owned TFS support. This is not complete sanctions coverage.
- SCA: SCA has 6 proof-backed fresh-alert direct/listing sources after the official regulations listing passed proof-backed repeat baseline and mass-monitor MONITOR_OK. SCA AML/CFT parser/noise review still blocks broad SCA positioning.
- UAE FIU: UAE FIU has 6 fresh-alert sources after adding proof-backed system guides. The former FIU circulars candidate currently resolves to the general publications index; safe 2026-06-21 checks found no distinct circular/notice endpoint in page text or sitemap, and Source Lab no-save returned NAV_SHELL_ONLY. Homepage remains remediation.
- Ministry of Finance: MoF has seven proof-backed fresh-alert sources plus one evidence-library homepage after adding selected MoF-owned DMTT/top-up tax, corporate tax, AEOI/FATCA/CRS, and UAE financial framework pages with repeat baseline and mass-monitor MONITOR_OK. This is selected MoF monitoring, not complete MoF or complete tax coverage.
- Ministry of Justice / UAE Legislation / Gazette: One selected official UAE Legislation Platform listing is fresh-alert eligible after proof-backed repeat baseline, stable hash, and mass-monitor dry-run MONITOR_OK on 2026-06-21. The broader root portal/e-Laws/Gazette routes remain remediation or unproven, so this is not complete UAE legislation or Official Gazette coverage.

## Safe Product Claims

- StatuteProof has 180 fresh-alert eligible UAE official-source daily monitors with MONITOR_OK status, proof records, hashes, and baseline confirmation as of June 21, 2026.
- StatuteProof also maintains 60 evidence-library UAE official/static source snapshots that are not counted as fresh-alert monitoring.
- 234 UAE source records currently have MONITOR_OK status overall; 180 of those are fresh-alert eligible after excluding static evidence-library pages.
- StatuteProof maintains source-level proof files for 237 of 246 enabled UAE source snapshots; this is not customer risk-brief eligibility.
- ADGM/FSRA has 11 selected proof-backed fresh-alert sources, including guidance/policy and RA/circular/rulebook style sources, with remaining candidates disclosed as held.
- DIFC has 11 selected proof-backed fresh-alert sources, including the official DIFC Legal Database listing; this is not complete DIFC legal database coverage.
- SCA has 6 selected proof-backed fresh-alert direct/listing sources; SCA root portal and broad SCA coverage remain unclaimed.
- MoJ/Gazette has one selected UAE Legislation Platform listing fresh-alert source; root portal, e-Laws, and complete Official Gazette coverage remain unclaimed.
- MoF monitoring has 7 fresh-alert eligible official MoF sources plus one evidence-library homepage, including selected publications/releases, financial legislation, ESR, DMTT/top-up tax, corporate tax, AEOI/FATCA/CRS, and UAE financial framework pages.
- MoE/DNFBP AML monitoring has 42 fresh-alert eligible official sources plus one evidence-library homepage.

## Forbidden Claims

- Do not describe all 246 enabled UAE source records as live monitors.
- Do not describe UAE coverage as complete.
- Do not describe UAE legislation coverage as complete.
- Do not describe MoJ/Gazette coverage as complete.
- Do not describe MoF coverage as complete.
- Do not claim complete tax coverage from MoF or FTA sources.
- Do not claim Official Gazette monitoring is complete.
- Do not describe sanctions coverage as complete.
- Do not describe VARA coverage as complete.
- Do not describe SCA coverage as full.
- Do not claim UAE FIU circulars have fresh-alert MONITOR_OK.
- Do not claim complete ADGM/FSRA coverage.
- Do not claim complete DIFC legal database coverage.
- Do not claim SCA root portal monitoring.
- Do not promise compliance outcomes.
- Do not present monitoring intelligence as legal advice.
- Do not promise every regulatory update will be captured.

## Known Limitations

- ADGM/FSRA: ADGM/FSRA has 11 selected proof-backed fresh-alert sources. Waivers, regulatory alerts, RA notices, RA AML guides, listing announcements, and Abu Dhabi/federal legislation pages remain held where current proof/baseline or selector gates did not pass cleanly.
- DIFC: DIFC has 11 selected proof-backed fresh-alert sources including the official Legal Database listing. This does not prove complete DIFC legal database coverage or item-level legal-change completeness.
- SCA: SCA has 6 proof-backed fresh-alert direct/listing sources. SCA AML/CFT parser/noise review remains unresolved and SCA root portal monitoring remains unclaimed.
- UAE FIU: UAE FIU has 6 fresh-alert sources. The held circulars candidate resolves to the general publications index, not a distinct circular/notice endpoint, and cannot be claimed as monitored.
- EOCN / sanctions / TFS: 25 selected EOCN/TFS-related sources are fresh-alert eligible. This is selected-source monitoring, not complete sanctions coverage.
- UAE Legislation / MoJ / Gazette: One selected UAE Legislation Platform listing is fresh-alert eligible. The root UAE Legislation Portal, UAE e-Laws/MoJ portal, and complete Official Gazette monitoring remain unclaimed because root/sitemap access and item-level Gazette routes are not fully proven.
- Ministry of Finance: MoF has 7 selected proof-backed fresh-alert sources plus one evidence-library homepage. This still excludes complete MoF, complete tax, broad public-debt, DTAs, budget archive, open-data statistical reports, and every MoF publication category unless each source passes its own proof/baseline gate.

## Risk-Brief Boundary

Source snapshot proof is not a canonical evidence record. Customer risk briefs remain blocked until complete evidence-record.json packages and brief eligibility gates exist.

StatuteProof reports are generated from monitored official-source records and are provided for information and compliance review support only. This audit does not constitute legal advice, regulatory advice, compliance certification, or a legal opinion.
