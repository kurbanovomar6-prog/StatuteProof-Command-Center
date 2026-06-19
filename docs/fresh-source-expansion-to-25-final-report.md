# Fresh Source Expansion To 25 Final Report

Date: 2026-06-19

## 1. Starting Fresh Alert Counts

| Family | Starting Fresh Alert |
|---|---:|
| VARA | 24 |
| DFSA | 12 |
| DIFC | 10 |
| ADGM/FSRA | 8 |
| UAE FIU | 5 |
| EOCN/TFS | 22 |
| SCA | 4 |
| MoJ/Gazette | 0 |
| MoF | 0 |

## 2. Ending Fresh Alert Counts

| Family | Ending Fresh Alert | Target | Gap |
|---|---:|---:|---:|
| VARA | 24 | 25 | 2 |
| DFSA | 15 | 25 | 10 |
| DIFC | 10 | 25 | 15 |
| ADGM/FSRA | 8 | 25 | 17 |
| UAE FIU | 5 | 25 | 20 |
| EOCN/TFS | 25 | 25 | 0 |
| SCA | 5 | 25 | 20 |
| MoJ/Gazette | 0 | 25 | 25 |
| MoF | 0 | 25 | 25 |

## 3. Sources Discovered / Tested

- Controlled no-save tests run: 106.
- Families covered: VARA, DFSA, DIFC, ADGM/FSRA, UAE FIU, EOCN/TFS, SCA, MoJ/Gazette, MoF.
- Results file: `docs/fresh-source-expansion-nosave-results.json`.
- Research log: `docs/fresh-source-expansion-official-research-log.md`.

## 4. Evidence Saved

- Sources sent to proof/baseline: 11.
- Sources with two evidence runs: 11.
- Sources with mass-monitor `MONITOR_OK`: 9.
- Sources activated after duplicate/static/family review: 6.

## 5. Newly Active Source IDs

| Source ID | Family | Why Counted |
|---|---|---|
| `AE-dfsa-laws-rules-legal-resources-3dc15494` | DFSA | Official DFSA legal resources endpoint, proof-backed, baseline complete, MONITOR_OK. |
| `AE-dfsa-innovation-59c1dc61` | DFSA | Official DFSA innovation/regulatory area, proof-backed, baseline complete, MONITOR_OK. |
| `AE-dfsa-what-we-do-enforcement-1a837c50` | DFSA | Official DFSA enforcement overview/update endpoint, proof-backed, baseline complete, MONITOR_OK. |
| `AE-sca-fintech-sandbox` | SCA | Official SCA FinTech Regulatory Sandbox regulatory page, proof-backed, baseline complete, MONITOR_OK. |
| `AE-uaeiec-en-us-laws-regulations-listing-00a71863` | EOCN/TFS | Official UAEIEC/EOCN-related AML/CFT laws and regulations listing, proof-backed, baseline complete, MONITOR_OK. |
| `AE-eocn-tfs` | EOCN/TFS | Official EOCN UN/TFS page, proof-backed, baseline complete, MONITOR_OK. |

## 6. Held / Rejected Sources

- VARA: no new source activated. VARA regulatory notices reached q=59 but did not pass strict save gate; other VARA pages were nav-shell or generic.
- DFSA: guidance/publications/policy pages that technically passed were held when their normalized hashes duplicated existing DFSA extraction outputs. DFSA `/test/` URLs were rejected as unsafe production sources. Static DFSA news detail pages were not counted.
- DIFC: document-hub and business/innovation pages were nav-shell, below quality gate, or business/marketing oriented. DIFC consultation page reached q=59 but did not pass strict gate.
- ADGM/FSRA: two candidates passed proof but failed mass-monitor dry-run with `SELECTOR_BROKEN`; several other pages were nav-shell.
- UAE FIU: mutual evaluation page technically passed but was held as a single static report/evidence-style endpoint, not fresh-alert family depth. Circulars/awareness/strategic pages remained nav-shell.
- EOCN/TFS: direct laws listing and UN/TFS page activated; detail law/news pages were held for low quality or selector review.
- SCA: FinTech Regulatory Sandbox activated; remaining SCA law/regulation pages were nav-shell under current selectors.
- MoJ/Gazette: tested MoJ federal laws/latest legislation/international cooperation paths; all remained nav-shell or access/selector remediation.
- MoF: tested financial legislation, ESR, tax, VAT, corporate tax, consultations, and DTA pages; no MoF source passed strict fresh-alert gates. Several pages reached q=59 but were not activated.

## 7. Families Now >=25

- CBUAE: already Strong.
- FTA: already Strong.
- MoE/DNFBP AML: already Strong.

No additional weak family reached 25 in this pass.

## 8. Families Still Below 25

- VARA: 24/25 after adding the VARA news/circular/publication listing. Needs one more official fresh endpoint or a VARA notices/admin-order adapter.
- DFSA: 15/25. Needs more unique official listing/rulebook/enforcement/consultation endpoints and better duplicate-hash isolation.
- DIFC: 10/25. Needs live legal/database/data-protection/consultation listing adapters or accessible official asset/PDF indexes.
- ADGM/FSRA: 8/25. Needs ADGM component adapter refinement; two candidates failed mass-monitor selector verification.
- UAE FIU: 5/25. Public FIU source universe appears small; circulars remain nav-shell and goAML remains forbidden.
- EOCN/TFS: 25/25 selected-source monitoring after adding the UAEIEC news listing. This does not claim complete sanctions/TFS coverage.
- SCA: 5/25. Needs stronger SCA table/listing/PDF adapter and more official endpoints.
- MoJ/Gazette: 0/25. MoJ/legislation pages remain access/selector remediation.
- MoF: 0/25. MoF pages need a specific decision/news/document adapter; generic/tax pages did not pass gates.

## 9. Adapter Work

No broad new adapter was added in this pass. Existing adapters used:

- `dfsa_rulebook`
- `dfsa_notice_listing`
- `sca_listing`
- `fiu_eocn_document_listing`
- `adgm_fsra_listing`
- `difc_legal_database`
- `document_listing`
- `vara_pdf_listing`
- `uae_legal_database`

Adapter gaps remain for VARA notices/admin orders, ADGM component listings, SCA tables/downloads, FIU circulars, MoJ/Gazette, and MoF documents.

## 10. Validators

Added:

- `tools/validate_fresh_source_expansion_to_25.py`

Updated:

- `tools/validate_fresh_signal_25_per_family.py` to classify official `uaeiec.gov.ae` sources under EOCN/TFS.

## 11. Customer-Safe Claims Now Allowed

- “StatuteProof has 168 fresh-alert eligible UAE official-source daily monitors with MONITOR_OK status, proof records, hashes, baseline confirmation, and daily-check metadata.”
- “EOCN/TFS selected-source monitoring has 25 proof-backed fresh-alert sources, but this is not complete sanctions/TFS coverage.”
- “DFSA monitoring has 15 proof-backed fresh-alert sources after adding official legal resources, innovation, and enforcement endpoints.”
- “SCA monitoring has 5 proof-backed fresh-alert sources; broader SCA coverage remains under remediation.”

## 12. Claims Still Forbidden

- Complete UAE coverage.
- Complete VARA, DFSA, DIFC, ADGM/FSRA, UAE FIU, EOCN/TFS, SCA, MoJ/Gazette, or MoF coverage.
- “Every family is Strong.”
- “UAE FIU circulars are monitored.”
- “MoJ/Gazette monitoring is live.”
- “MoF is Strong.”
- Legal advice, guaranteed compliance, perfect parsing, never-miss updates, or regulator certification.

## 13. Next Exact Source Task

1. EOCN/TFS: find one more direct official fresh source or prove the official public universe limit.
2. VARA: build/fix regulatory notices/admin orders adapter to convert the q=59 notices source.
3. SCA: build SCA table/download adapter for laws, regulations, decisions, and listing pages.
4. ADGM/FSRA: fix component selector failures for courts/legal and RA/FSRA notices.
5. MoF and MoJ/Gazette: run a dedicated official endpoint plus adapter remediation sprint.

## 14. Next Exact Product Task

Update the Sources/Coverage UI to show family-level progress toward Strong Fresh Signal, including exact blockers and the difference between fresh-alert, evidence-library, candidate, and remediation.

## 15. Next Exact Sales Task

Use the 168 fresh-alert claim only. Do not sell complete UAE coverage or complete family coverage.


## Completion-Next Addendum

A later completion pass added six more proof-backed fresh-alert sources, bringing current fresh-alert count to 168 and current legacy registry truth to 238 enabled / 237 monitoring-active / 1 remediation. EOCN/TFS selected-source monitoring is now 25/25; VARA is 24/25; DFSA is 16/25; ADGM/FSRA is 10/25; MoF is 1/25. Complete UAE coverage and complete family coverage remain forbidden claims.
