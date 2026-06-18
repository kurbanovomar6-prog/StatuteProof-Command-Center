# Weak-Family 25-Each Target Progress Report

Date: 2026-06-18

## Target Table

| Family | Starting active | Target | New active | Ending active | Gap remaining | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| DIFC | 12 | 25 | 0 | 12 | 13 | Below target; needs document-hub/legal-update adapter work. |
| ADGM/FSRA | 12 | 25 | 0 | 12 | 13 | Below target; needs ADGM component/document-hub adapter work. |
| VARA | 9 | 25 | 0 | 9 | 16 | Below target; needs guidance/admin-order/rulebook-hub depth. |
| Ministry of Economy / DNFBP AML | 7 | 25 | 0 | 7 | 18 | Below target; needs legislation/listing relevance filters. |
| SCA | 5 | 25 | 0 | 5 | 20 | Below target; needs SCA document/download adapter and broader official endpoint validation. |
| UAE FIU | 4 active + 1 remediation | 25 | 0 | 4 active + 1 remediation | 21 | Below target; needs tighter publication-detail extraction and duplicate controls. |
| EOCN / sanctions / TFS | 3 | 25 | 0 | 3 | 22 | Below target; needs TFS/sanctions noise controls before bulk activation. |
| FTA / Tax | 0 | 25 | 25 | 25 | 0 | Target reached for selected direct official FTA PDFs. |

## Key Blocker

The project can now prove FTA depth. It cannot yet honestly claim that every weak family reached 25. The blocker is not laziness; it is the lack of enough passing, proof-backed, baseline-tested official endpoints in the remaining families without new source-specific adapters and filtering.

## Next Activation Batch

The next batch should focus on SCA first, because current probes show official document endpoints exist but require a download/document adapter to avoid false nav-shell or binary-download failures.
