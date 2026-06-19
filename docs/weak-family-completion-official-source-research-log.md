# Weak-Family Completion Official Source Research Log

Date: 2026-06-19

This log records the official-source research and no-save probe artifacts used for the weak-family completion sprint. It is not a claim of complete UAE coverage or complete family coverage. Monitoring intelligence only. Not legal advice.

| Family | Candidate / probe basis | Result |
| --- | --- | --- |
| DIFC | DIFC static consultation/legal pages, legal notices, legal database, sitemap-focused official pages | 13 sources activated; family reached 25. |
| ADGM/FSRA | ADGM/FSRA public consultation pages, RA consultation pages, static focused official pages | 13 sources activated; family reached 25. |
| VARA | Direct official VARA PDFs, rulebooks, administrative orders, latest regulations | 16 sources activated; family reached 25. |
| Ministry of Economy / DNFBP AML | MoE DNFBP circulars, beneficial ownership decisions, AML/CFT law, supplemental guidance PDFs | 19 direct DNFBP/MoE AML sources activated; family reached 26. |
| SCA | SCA work queue, beta SCA pages, SCA/UAE legislation download URLs | Held; no safe path to 25 under current robots/fetch/download constraints. |
| UAE FIU | FIU annual reports, press releases, publications, public media PDFs discovered by official URL search | 2 sources activated; direct media PDFs blocked by project fetch policy. |
| EOCN / sanctions / TFS | EOCN/UAEIEC robots checks, MoE AML/TFS documents, high-risk/sanctions circulars | 16 unique MoE AML/TFS documents activated; EOCN/UAEIEC direct expansion held. |

## Probe Artifacts

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

## Rejection / Hold Rules Applied

- No private portal, login, CAPTCHA, or paywall routes were used.
- No source was activated from no-save alone.
- Duplicate normalized hashes were held.
- Project-fetch 403/Cloudflare responses were treated as blockers, not bypass opportunities.
- Robots-disallowed EOCN/SCA paths were not bulk monitored.
