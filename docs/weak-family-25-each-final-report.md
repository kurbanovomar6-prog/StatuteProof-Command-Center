# Weak-Family 25-Each Final Report

Date: 2026-06-18

## 1. Starting Truth

122 enabled UAE sources / 121 monitoring-active / 1 remediation.

## 2. Ending Truth

147 enabled UAE sources / 146 monitoring-active / 1 remediation.

## 3. Starting Family Counts

| Family | Starting active |
| --- | ---: |
| DIFC | 12 |
| ADGM/FSRA | 12 |
| VARA | 9 |
| Ministry of Economy / DNFBP AML | 7 |
| SCA | 5 |
| UAE FIU | 4 active + 1 remediation |
| EOCN / sanctions / TFS | 3 |
| FTA / Tax | 0 |

## 4. Ending Family Counts

| Family | Ending active | Reached >=25? |
| --- | ---: | --- |
| DIFC | 12 | No |
| ADGM/FSRA | 12 | No |
| VARA | 9 | No |
| Ministry of Economy / DNFBP AML | 7 | No |
| SCA | 5 | No |
| UAE FIU | 4 active + 1 remediation | No |
| EOCN / sanctions / TFS | 3 | No |
| FTA / Tax | 25 | Yes |

## 5. What Was Implemented

- Added the `fta_tax_listing` adapter for official FTA listing pages.
- Added narrow request fallback for FTA listing pages whose real official listing content is available in server HTML.
- Expanded source-quality vocabulary for tax terms.
- Expanded FIU/EOCN document-listing legal tokens.
- Hardened `uae50_apply_activation.py` so new active rows carry normalized text path, baseline metadata, `MONITOR_OK`, and legal-safe notes.
- Activated 25 direct official FTA PDF endpoints after proof-backed gates.

## 6. No-Save / Evidence / Baseline / MONITOR_OK

| Metric | Count |
| --- | ---: |
| FTA PDF candidates no-save tested | 27 |
| Strong no-save passes | 25 |
| Evidence saved | 25 |
| Repeat baseline complete | 25 |
| Mass-monitor `MONITOR_OK` | 25 |
| Newly active source count | 25 |

## 7. Held / Rejected Sources

- 2 FTA PDFs were held because they did not meet extraction quality or PDF extraction gates.
- SCA download/detail endpoints were held because several return browser downloads or Office/zip-like content, and only one tested SCA PDF passed. This is not enough for a family-level 25-source claim.

## 8. Newly Active Source IDs

See `docs/weak-family-25-each-final-activation-set.json` for the full 25-source activation set.

## 9. Families Reaching >=25

- FTA / Tax.

## 10. Families Still Below 25

- DIFC: needs document-hub/legal-update adapter work.
- ADGM/FSRA: needs component/document-hub adapter work.
- VARA: needs guidance/admin-order/rulebook-hub depth.
- Ministry of Economy / DNFBP AML: needs legislation/listing relevance filters.
- SCA: needs source-specific document/download adapter.
- UAE FIU: needs publication-detail extraction and duplicate controls.
- EOCN / sanctions / TFS: needs TFS/sanctions noise controls.

## 11. Did We Claim Complete UAE Coverage?

No.

## 12. Did We Claim Complete Family Coverage?

No. FTA is now strong for selected direct official PDF endpoints, not complete for every FTA/tax source type.

## 13. Commercial Impact

FTA moved from zero active endpoints to 25 proof-backed, baseline-tested, `MONITOR_OK` official tax PDF endpoints. That materially improves tax/corporate/VAT credibility. The project is stronger, but not balanced enough to call every weak family strong.

## 14. Remaining Weakest Family

EOCN / sanctions / TFS and UAE FIU remain the weakest commercially relevant AML/CFT families because they have low active counts and high noise/duplicate risk.

## 15. Next Exact Source Task

Build an SCA official document/download adapter that can safely handle `/assets/download/...` Office/PDF downloads, reject unsupported binaries, and activate only documents with extractable regulatory text, proof, repeat baseline, and `MONITOR_OK`.

## 16. Next Exact Product Task

Add 7/30/90-day source reliability trend charts for monitoring-active sources.

## 17. Next Exact Sales Task

Superseded by the 2026-06-19 weak-family completion truth: “226 enabled UAE official-source endpoints, 225 monitoring-active. Selected sources only. Monitoring intelligence only. Not legal advice.”
