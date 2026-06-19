# Weak-Family Completion No-Save Marathon Report

Date: 2026-06-19

Documented probe rows across focused no-save/adaptation passes: **294**. Documented strong-pass rows before duplicate/drift/access filtering: **106**.

Counts include repeated focused passes while adapters and source policies were tuned. Activation count is lower because StatuteProof does not count duplicates, no-save-only rows, blocked endpoints, or drifted/noisy candidates as monitoring-active.

| Artifact | Family | Tested rows | Strong pass rows |
| --- | --- | ---: | ---: |
| `/tmp/difc_static_focused_nosave.json` | DIFC | 35 | 15 |
| `/tmp/difc_sitemap_focused_nosave.json` | DIFC | 35 | 0 |
| `/tmp/difc_workqueue_nosave.json` | DIFC | 4 | 0 |
| `/tmp/adgm_static_focused_nosave.json` | ADGM/FSRA | 40 | 26 |
| `/tmp/vara_direct_pdf_nosave.json` | VARA | 14 | 13 |
| `/tmp/vara_extra_pdf_nosave.json` | VARA | 3 | 2 |
| `/tmp/vara_rulebook_unfocused_nosave.json` | VARA | 33 | 8 |
| `/tmp/moe_direct_pdf_nosave.json` | Ministry of Economy / DNFBP AML | 40 | 37 |
| `/tmp/fiu_eocn_universe_nosave.json` | UAE FIU / EOCN | 29 | 3 |
| `/tmp/weak_family_pdf_nosave.json` | SCA / UAE FIU / legal PDFs | 43 | 0 |
| `/tmp/uaefiu_pdf_nosave.json` | UAE FIU | 10 | 0 |
| `/tmp/sca_workqueue_nosave.json` | SCA | 6 | 2 |
| `/tmp/sca_beta_regulations_nosave.json` | SCA | 1 | 0 |
| `/tmp/sca_beta_circulars_nosave.json` | SCA | 1 | 0 |

## Held Results

- SCA: held below 25 due robots/access/download blockers.
- UAE FIU: held below 25 due Cloudflare/403 under project fetch policy and stale/duplicate PDFs.
- EOCN / sanctions / TFS: held below 25 because direct EOCN/UAEIEC expansion is robots-disallowed and remaining MoE TFS documents were duplicate/noisy.
