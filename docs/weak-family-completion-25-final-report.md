# Weak-Family Completion 25 Final Report

Date: 2026-06-19

## 1. Starting Truth

147 enabled UAE sources / 146 monitoring-active / 1 remediation.

## 2. Ending Truth

226 enabled UAE sources / 225 monitoring-active / 1 remediation.

## 3-5. Family Target Table

| Family | Starting active | Ending active | New active | Reached >=25? | Exact blocker if below target |
| --- | ---: | ---: | ---: | --- | --- |
| DIFC | 12 | 25 | 13 | Yes |  |
| ADGM/FSRA | 12 | 25 | 13 | Yes |  |
| VARA | 9 | 25 | 16 | Yes |  |
| Ministry of Economy / DNFBP AML | 7 | 26 | 19 | Yes |  |
| SCA | 5 | 5 | 0 | No | Below target because official SCA routes were robots-disallowed, shallow, or blocked/download-only under current safe fetch rules. |
| UAE FIU | 4 | 6 | 2 | No | Below target: two listing endpoints passed; direct media PDFs and homepage remain blocked under project fetch policy. |
| EOCN / sanctions / TFS | 3 | 22 | 16 | No | Below target but much stronger: 16 unique MoE AML/TFS documents passed; remaining candidates were robots-disallowed or duplicate/noisy. |

## 6-11. Activation Metrics

| Metric | Count |
| --- | ---: |
| Documented no-save/probe rows | 294 |
| Documented strong pass rows before filtering | 106 |
| Evidence saved for newly active rows | 79 |
| Repeat baseline complete | 79 |
| Mass-monitor `MONITOR_OK` | 79 |
| Newly active source count | 79 |

## 12-13. Newly Active Source IDs By Family

### ADGM/FSRA (13)

- `AE-adgm-static-adgm-fsra-launches-consultation-on-enhancements-to-insurance-regulator-0df860c1`
- `AE-adgm-static-adgm-fsra-launches-consultation-on-enhancements-to-its-aml-framework-4f656348`
- `AE-adgm-static-adgm-fsra-publishes-consultation-paper-to-advance-its-capital-markets--d9ae1e0d`
- `AE-adgm-static-fsra-commences-public-consultation-for-broadening-participation-in-pri-08f3733b`
- `AE-adgm-static-fsra-issues-public-consultation-on-updates-to-its-pru-rulebook-1b9ddae2`
- `AE-adgm-static-adgm-publishes-consultation-paper-on-a-comprehensive-sustainable-finan-49fb8a0a`
- `AE-adgm-static-fsra-commences-public-consultation-on-proposed-3rd-party-fintech-provi-1d5f8cd9`
- `AE-adgm-static-public-consultation-on-adgms-proposed-enhanced-auditors-framework-a25acdd4`
- `AE-adgm-static-the-ra-commences-public-consultation-on-proposed-adgm-company-service--4ffb0fe4`
- `AE-adgm-static-adgm-ra-publishes-consultation-paper-on-its-insolvency-practitioner-re-08039fa0`
- `AE-adgm-static-the-ra-of-adgm-publishes-a-consultation-paper-on-employment-regulation-da3421c4`
- `AE-adgm-static-adgm-registration-authority-publishes-consultation-paper-on-substantia-26556c81`
- `AE-adgm-static-adgm-commences-public-consultation-on-proposed-new-data-protection-reg-ba969779`

### DIFC (13)

- `AE-difc-static-legal-notices-9f800f67`
- `AE-difc-static-difc-announces-consultation-for-amendments-to-difc-law-on-application--8445f9f8`
- `AE-difc-static-difc-announces-consultation-for-amendments-to-select-difc-legislation--0257cbb4`
- `AE-difc-static-difc-announces-consultation-of-amended-prescribed-company-regulations-8fe458e8`
- `AE-difc-static-difc-announces-consultation-of-amendments-to-the-difc-real-property-la-959361b5`
- `AE-difc-static-difc-announces-consultation-of-new-variable-capital-company-regulation-77bae468`
- `AE-difc-static-difc-announces-consultation-of-updated-prescribed-company-regulations-2a488864`
- `AE-difc-static-difc-announces-consultation-of-updated-real-property-law-and-regulatio-4b104a5d`
- `AE-difc-static-difc-consultation-amended-data-protection-regulations-1998c106`
- `AE-difc-static-difc-announces-consultation-new-digital-assets-law-new-law-security-ba6a9cc0`
- `AE-difc-static-difc-announces-new-difc-venture-studio-regulations-consultation-1-4208cd75`
- `AE-difc-static-difc-announces-proposed-amendments-real-property-law-consultation-1d96ed0b`
- `AE-difc-static-legal-database-c192df94`

### EOCN / sanctions / TFS (16)

- `AE-moet-dnfbp-doc-0-14503b23`
- `AE-moet-dnfbp-doc-0-413f733d`
- `AE-moet-dnfbp-doc-0-cba08cb2`
- `AE-moet-dnfbp-doc-0-8dc715bc`
- `AE-moet-dnfbp-doc-294745-96dd2a1f`
- `AE-moet-dnfbp-doc-0-8b59c3ff`
- `AE-moet-dnfbp-doc-0-eb82ce7d`
- `AE-moet-dnfbp-doc-0-d74dc341`
- `AE-moet-dnfbp-doc-0-5b75bd0d`
- `AE-moet-dnfbp-doc-387526-b8403d56`
- `AE-moet-dnfbp-doc-0-70b480a7`
- `AE-moet-dnfbp-doc-469920-023470db`
- `AE-moet-dnfbp-doc-469920-47d93221`
- `AE-moet-dnfbp-doc-469920-6d81bc73`
- `AE-moet-dnfbp-doc-469920-11ae906d`
- `AE-moet-dnfbp-doc-0-cc0a0a0e`

### Ministry of Economy / DNFBP AML (19)

- `AE-moet-dnfbp-circular-2025-nra-awareness`
- `AE-moet-dnfbp-circular-2025-sanctions-screening`
- `AE-moet-dnfbp-circular-2026-high-risk-list`
- `AE-moet-beneficial-owner-penalties-2023`
- `AE-moet-beneficial-owner-procedures-2023`
- `AE-moet-dnfbp-circular-2025-high-risk-update-1`
- `AE-moet-dnfbp-circular-2025-iran-un-sanctions`
- `AE-moet-dnfbp-circular-2025-high-risk-update-8`
- `AE-moet-dnfbp-circular-2025-cdd-measures`
- `AE-moet-dnfbp-circular-2024-responsible-sourcing-gold`
- `AE-moet-dnfbp-circular-2024-high-risk-update-1`
- `AE-moet-dnfbp-circular-2021-dpms-goaml`
- `AE-moet-dnfbp-guidelines-march-2026`
- `AE-moet-dnfbp-circular-2022-tfs-requirements`
- `AE-moet-aml-federal-decree-law-10-2025`
- `AE-moet-dnfbp-guidance-real-estate-2026`
- `AE-moet-dnfbp-guidance-dpms-2026`
- `AE-moet-dnfbp-guidance-tcsp-2026`
- `AE-moet-dnfbp-guidance-auditors-2026`

### UAE FIU (2)

- `AE-uaefiu-annual-reports`
- `AE-uaefiu-press-releases`

### VARA (16)

- `AE-vara-pdf-exchange-services-rulebook`
- `AE-vara-pdf-va-management-investment-rulebook`
- `AE-vara-pdf-company-rulebook`
- `AE-vara-pdf-administrative-order-01-2022`
- `AE-vara-pdf-advisory-services-rulebook`
- `AE-vara-pdf-va-transfer-settlement-rulebook`
- `AE-vara-pdf-cabinet-decision-111-2022`
- `AE-vara-pdf-custody-services-rulebook`
- `AE-vara-pdf-guidance-virtual-asset-issuance`
- `AE-vara-pdf-administrative-order-02-2022`
- `AE-vara-pdf-market-conduct-rulebook`
- `AE-vara-pdf-cabinet-decision-112-2022`
- `AE-vara-pdf-law-no-4-2022-virtual-assets`
- `AE-vara-pdf-grievance-committee-resolution-2023`
- `AE-vara-pdf-rulebook-introduction`
- `AE-vara-pdf-virtual-assets-regulations-2023-latest-revision`

## 14. Held / Rejected Sources By Family

- SCA: held because primary official SCA/UAECMA routes are robots-disallowed or redirect to disallowed domains; beta pages and UAE legislation downloads did not produce enough strong, extractable, proof-backed endpoints.
- UAE FIU: held because the official homepage and direct media PDFs returned Cloudflare/403 to the project fetch policy. Two listing endpoints passed; the remaining official PDFs cannot be counted until fetch permission and stable extraction are resolved.
- EOCN / sanctions / TFS: held three short of target because EOCN/UAEIEC official domains disallow broad automated fetching and remaining MoE AML/TFS documents duplicate already active normalized hashes or carry high-noise designation-list risk.

## 15. Adapter / Parser Improvements

- `tools/uae50_activate.py` supports `--fetch-method auto` without forcing Playwright.
- Source-quality tests now enforce no-save boundaries, repeat baseline, active-source metadata, and source ID integrity.
- Existing PDF/listing/static adapters were reused where they produced stable official-source evidence.

## 16-17. Tests And Validators

- Updated `product/regradar/tests/test_source_quality_policy.py`.
- Added `tools/validate_weak_family_completion_25.py`.
- Updated stale source-truth validators to recognize the current 226 / 225 / 1 truth without weakening proof gates.

## 18. Families That Reached >=25

- DIFC.
- ADGM/FSRA.
- VARA.
- Ministry of Economy / DNFBP AML.
- FTA / Tax was already at 25 before this sprint and remains active.

## 19. Families Still Below 25

- SCA: 5 active.
- UAE FIU: 6 active + 1 remediation.
- EOCN / sanctions / TFS: 22 active under the scoped sanctions/TFS family definition.

## 20. Did We Claim Complete UAE Coverage?

No.

## 21. Did We Claim Complete Family Coverage?

No. Families at or above 25 are described as stronger selected-source monitoring depth, not complete family coverage.

## 22. Commercial Impact

The product is meaningfully stronger: DIFC, ADGM/FSRA, VARA, MoE/DNFBP AML, and FTA now have at least 25 proof-backed official endpoints. The remaining commercial weakness is concentrated in SCA, FIU, and direct EOCN/UAEIEC sanctions/TFS coverage.

## 23. Remaining Weakest Family

SCA remains weakest because safe public monitoring is blocked by robots/access/download issues under current project rules.

## 24. Next Exact Activation Batch

Build a permission-safe SCA/FIU access remediation batch: confirm official monitorable endpoints, add a safe SCA download/document adapter only for allowed routes, and re-test FIU media PDFs without spoofing private access controls.

## 25. Next Exact Product Task

Add 7/30/90-day source reliability charts so customers can see monitoring stability history by source and family.

## 26. Next Exact Sales Task

Position StatuteProof as selected official-source monitoring with strong coverage in CBUAE, DFSA/DIFC, ADGM/FSRA, VARA, FTA, and MoE/DNFBP. Disclose SCA/FIU/EOCN blockers honestly. Monitoring intelligence only. Not legal advice.
