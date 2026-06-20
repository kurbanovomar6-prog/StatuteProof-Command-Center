# StatuteProof Source Signal Quality Audit

Audit date: 2026-06-20
Auditor: StatuteProof Source Quality Auditor v2
Source file: `product/regradar/sources.json`

## Current Source Truth

| Metric | Count |
| --- | ---: |
| Enabled UAE sources | 239 |
| Fresh-alert eligible | 170 |
| Evidence-library only | 61 |
| Candidate | 5 |
| Remediation | 3 |
| Source-level MONITOR_OK | 224 |
| Sources with proof path | 230 |

These are monitoring-truth counts, not legal completeness claims.

## Family Readiness

| Family | Total | Fresh alert | Evidence library | Candidate | Remediation | Label | Gap to 25 |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| CBUAE | 27 | 25 | 1 | 1 | 0 | Strong Selected Source | 0 |
| VARA | 26 | 25 | 1 | 0 | 0 | Strong Selected Source | 0 |
| DFSA | 44 | 16 | 28 | 0 | 0 | Good | 9 |
| DIFC | 25 | 10 | 15 | 0 | 0 | Good | 15 |
| ADGM/FSRA | 27 | 10 | 14 | 3 | 0 | Good | 15 |
| Ministry of Economy / DNFBP AML | 43 | 42 | 1 | 0 | 0 | Strong Selected Source | 0 |
| FTA / Tax | 25 | 25 | 0 | 0 | 0 | Strong Selected Source | 0 |
| EOCN / sanctions / TFS | 25 | 25 | 0 | 0 | 0 | Strong Selected Source | 0 |
| SCA | 7 | 5 | 1 | 0 | 1 | Weak | 20 |
| UAE FIU | 7 | 5 | 0 | 1 | 1 | Partial | 20 |
| Ministry of Finance | 3 | 2 | 1 | 0 | 0 | Weak | 23 |
| Ministry of Justice / UAE Legislation / Gazette | 1 | 0 | 0 | 0 | 1 | Missing | 25 |

## Family Notes

- CBUAE: 25 CBUAE rulebook/regulatory sources are fresh-alert eligible. The generic homepage remains evidence-library and the generic regulations page remains candidate/held.
- VARA: 25 selected official VARA rulebook, circular, publication, regulatory, and enforcement-table sources are fresh-alert eligible. This is selected-source monitoring, not complete VARA coverage.
- DFSA: DFSA has 16 fresh-alert sources. Static individual news/notice pages stay evidence-library and must not inflate fresh monitoring claims.
- DIFC: DIFC has 10 fresh-alert sources. Individual static whats-on pages remain evidence-library.
- ADGM/FSRA: ADGM/FSRA has 10 fresh-alert sources. Three candidate rows still need selector or registry reconciliation before activation.
- Ministry of Economy / DNFBP AML: 42 MoE/DNFBP AML sources are fresh-alert eligible, plus one evidence-library homepage.
- FTA / Tax: 25 official FTA tax sources are fresh-alert eligible.
- EOCN / sanctions / TFS: 25 selected EOCN/TFS-related sources are fresh-alert eligible across direct EOCN/UAEIEC and MoE-owned TFS support. This is not complete sanctions coverage.
- SCA: SCA has 5 proof-backed fresh-alert sources. The broader SCA family remains below Strong until more official sources reach MONITOR_OK.
- UAE FIU: UAE FIU has 5 fresh-alert sources. FIU circulars remain candidate/held and the homepage remains remediation.
- Ministry of Finance: MoF has two proof-backed fresh-alert sources, including financial legislation PDFs, plus one evidence-library homepage.
- Ministry of Justice / UAE Legislation / Gazette: UAE Legislation Portal remains remediation due to WAF/access issues. No MONITOR_OK claim is allowed.

## Safe Product Claims

- StatuteProof has 170 fresh-alert eligible UAE official-source daily monitors with MONITOR_OK status, proof records, hashes, and baseline confirmation as of June 20, 2026.
- StatuteProof also maintains 61 evidence-library UAE official/static source snapshots that are not counted as fresh-alert monitoring.
- 224 enabled UAE sources have MONITOR_OK status overall; 170 of those are currently fresh-alert eligible after excluding static evidence-library pages.
- StatuteProof maintains source-level proof files for 230 of 239 enabled UAE source snapshots; this is not customer risk-brief eligibility.
- MoF monitoring has 2 fresh-alert eligible official sources plus one evidence-library homepage.
- MoE/DNFBP AML monitoring has 42 fresh-alert eligible official sources plus one evidence-library homepage.

## Forbidden Claims

- 239 monitored UAE regulatory sources.
- complete UAE coverage.
- complete sanctions coverage.
- complete VARA coverage.
- full SCA coverage.
- UAE FIU circulars are monitored.
- guaranteed compliance.
- legal advice.
- never miss regulatory updates.

## Risk-Brief Boundary

Source snapshot proof is not a canonical evidence record. Customer risk briefs remain blocked until complete `evidence-record.json` packages and brief eligibility gates exist.

StatuteProof reports are generated from monitored official-source records and are provided for information and compliance review support only. This audit does not constitute legal advice, regulatory advice, compliance certification, or a legal opinion.
