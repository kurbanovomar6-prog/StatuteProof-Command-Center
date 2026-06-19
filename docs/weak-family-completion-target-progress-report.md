# Weak-Family Completion Target Progress Report

Date: 2026-06-19

Current verified ending truth after VARA enforcement activation: **238 enabled UAE sources / 237 monitoring-active / 1 remediation** in the legacy registry, with **169 fresh-alert eligible daily monitors**. Monitoring intelligence only. Not legal advice.

| Family | Starting active | Target | New active | Ending active | Gap remaining | Status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| DIFC | 12 | 25 | 13 | 25 | 0 | Reached target after 13 proof-backed DIFC legal/consultation/static official endpoints. |
| ADGM/FSRA | 12 | 25 | 13 | 25 | 0 | Reached target after 13 proof-backed ADGM/FSRA consultation and RA endpoints. |
| VARA | 9 | 25 | 16 | 25 | 0 | Reached target after 16 direct official VARA PDF/rulebook/regulation endpoints. |
| Ministry of Economy / DNFBP AML | 7 | 25 | 19 | 26 | 0 | Reached target for direct DNFBP/MoE AML sources; MoE-owned AML/TFS total is higher when eocn_tfs documents are counted separately. |
| SCA | 5 | 25 | 0 | 5 | 20 | Below target because official SCA routes were robots-disallowed, shallow, or blocked/download-only under current safe fetch rules. |
| UAE FIU | 4 | 25 | 2 | 6 | 19 | Below target: two listing endpoints passed; direct media PDFs and homepage remain blocked under project fetch policy. |
| EOCN / sanctions / TFS | 3 | 25 | 16 | 22 | 3 | Below target but much stronger: 16 unique MoE AML/TFS documents passed; remaining candidates were robots-disallowed or duplicate/noisy. |

## Hard Blockers

- SCA: `www.sca.gov.ae` redirects robot policy to `www.uaecma.gov.ae`, which disallows automated fetching. `beta.sca.gov.ae` allowed limited probing, but tested routes either redirected, produced nav-shell/listing issues, or did not yield enough strong proof-backed endpoints. UAE legislation download URLs returned Cloudflare/403 to the project fetcher.
- UAE FIU: `uaefiu.gov.ae` robots/homepage access returned Cloudflare/403 to the project fetcher. Publicly discoverable media PDFs were official, but project fetches returned 403; only annual reports and press releases passed no-save, proof, repeat baseline, and `MONITOR_OK`.
- EOCN / sanctions / TFS: EOCN and UAEIEC domains disallow broad automated fetching. MoE-owned AML/TFS documents provided 16 unique proof-backed additions, but the remaining candidates were duplicates or high-noise designation-list style sources.

## Next Activation Batch

The next source task is not another broad crawl. It is a permission-safe SCA/FIU access strategy: confirm permitted official endpoints or use official downloadable document mirrors that work under the project fetch policy without spoofing private access controls.
