# UAE Source Family Scorecard

Date: 2026-06-19

Fresh-signal labels: Strong = 25+ fresh-alert eligible endpoints; Good = 10-24; Partial = 5-9; Weak = 1-4; Missing = 0. Source-family labels describe selected-source depth, not legal completeness.

Current fresh-signal truth: 238 enabled UAE sources / 169 fresh-alert eligible / 61 evidence-library / 5 candidate / 3 remediation. Monitoring intelligence only. Not legal advice.

Fresh-signal overlay after the 25-per-family pass:

| Family | Fresh Alert MONITOR_OK | Fresh-Signal Label | Gap To 25 |
| --- | ---: | --- | ---: |
| CBUAE | 25 | Strong | 0 |
| FTA / Tax | 25 | Strong | 0 |
| Ministry of Economy / DNFBP AML | 42 | Strong | 0 |
| VARA | 25 | Strong selected-source | 0 |
| EOCN / sanctions / TFS | 25 | Strong selected-source | 0 |
| DFSA | 16 | Good | 9 |
| DIFC | 10 | Good | 15 |
| ADGM/FSRA | 10 | Good | 15 |
| UAE FIU | 5 | Partial | 20 |
| SCA | 5 | Weak | 20 |
| Ministry of Justice / UAE Legislation / Gazette | 0 | Missing | 25 |
| Ministry of Finance | 1 | Weak | 24 |

## Appendix A: Historical Legacy Depth Table - Not Customer Or Adapter Truth

The legacy table below is retained for source-universe depth context only. Its legacy active counts come from older `status=active` fields and must not be used as customer-facing monitoring, fresh-alert, adapter-priority, or coverage claims. Use the fresh-signal overlay above as the only primary scorecard.

| Family | Enabled | Legacy active (not fresh-alert) | Remediation | Candidates mapped | Top-250 | Legacy depth label | Depth /10 | Trust /10 | Next 10 endpoints |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| CBUAE | 27 | 27 | 0 | 40 | 0 | Strong | 10 | 8 | None mapped yet |
| DFSA | 43 | 43 | 0 | 104 | 49 | Strong | 10 | 8 | `AE-dfsa-ar-laws-rules-1a83ae44`, `AE-dfsa-ar-laws-rules-legal-resources-72e01f1f`, `AE-dfsa-laws-rules-2dee8ba9`, `AE-dfsa-laws-rules-legal-resources-3dc15494`, `AE-dfsa-ar-innovation-1e65603c`, `AE-dfsa-ar-what-we-do-enforcement-f0487f7a`, `AE-dfsa-innovation-59c1dc61`, `AE-dfsa-news-reminder-rulebook-amendments-e6e4718a`, `AE-dfsa-what-we-do-enforcement-1a837c50`, `AE-dfsa-news-notice-amendment-dfsa-forms-adabf2e1` |
| DIFC | 25 | 25 | 0 | 98 | 28 | Strong | 8.0 | 8 | Target reached with 13 added proof-backed DIFC legal/consultation/static official endpoints. Next: reliability history and document-hub depth. |
| ADGM/FSRA | 25 | 25 | 0 | 107 | 13 | Strong | 8.0 | 8 | Target reached with 13 added proof-backed ADGM/FSRA consultation and RA endpoints. Next: official rulebook and courts/legal notices only where buyer-relevant. |
| VARA | 25 | 25 | 0 | 31 | 7 | Strong | 8.0 | 8 | Target reached with 16 added direct official VARA PDF/rulebook/regulation endpoints. Next: guidance/admin orders if they pass gates. |
| SCA | 6 | 6 | 0 | 15 | 4 | Partial | 3.0 | 6 | Below target after adding SCA FinTech Regulatory Sandbox. Next: permission-safe SCA download/document adapter and official endpoint confirmation; do not bypass robots/access controls. |
| UAE FIU | 7 | 6 | 1 | 16 | 1 | Partial | 3.0 | 5 | Below target. Two listing endpoints were added; direct FIU media PDFs remain blocked under the project fetch policy. |
| EOCN / sanctions / TFS | 25 | 25 | 0 | 20 | 4 | Strong selected-source | 8 | 8 | Reached 25 after adding UAEIEC news listing. This remains selected-source monitoring across direct EOCN/UAEIEC and MoE-owned TFS support, not a complete sanctions coverage claim. |
| FTA / Tax | 25 | 25 | 0 | 77 | 70 | Strong | 8 | 7 | Direct official FTA PDF corpus now has 25 proof-backed active endpoints. Next: activate FTA listing pages only after item-level pagination/filter extraction passes gates. |
| Ministry of Economy / DNFBP AML | 26 | 26 | 0 | 35 | 20 | Strong | 8.0 | 8 | Target reached for direct DNFBP/MoE AML sources. MoE-owned AML/TFS documents also strengthen the EOCN/TFS-relevant family, without claiming complete MoE coverage. |
| Ministry of Justice / UAE Legislation / Gazette | 1 | 1 | 0 | 70 | 29 | Weak | 0.5 | 4 | `AE-ai-legislation-511679d1`, `AE-elawyer-signup-a979f83b`, `AE-moj-ar-about-moj-judicial-training-institute-laws-and-legislation-aspx-3579a2bc`, `AE-moj-ar-about-moj-union-supreme-court-e-services-laws-of-union-supreme-court-aspx-677651f6`, `AE-moj-ar-laws-and-legislation-aspx-b60d2907`, `AE-moj-ar-laws-and-legislation-anti-money-laundering-and-combatting-terrorism-financing-aspx-08cdebef`, `AE-moj-ar-laws-and-legislation-international-cooperation-department-aspx-f12a87ea`, `AE-moj-ar-laws-and-legislation-international-cooperation-department-agreements-aspx-6fe3558c`, `AE-moj-ar-laws-and-legislation-international-cooperation-department-agreements-aspx-3569166b`, `AE-moj-ar-laws-and-legislation-international-cooperation-department-agreements-aspx-4910ca15` |
| UAE Data Office / PDPL / privacy | 0 | 0 | 0 | 0 | 0 | Missing | 1 | 2 | None mapped yet |
| Ministry of Finance | 1 | 1 | 0 | 85 | 4 | Weak | 0.5 | 4 | `AE-mof-ar-financial-legislation-5921ed44`, `AE-mof-ar-public-finance-international-relations-economic-substance-regulations-esr-944b90cc`, `AE-mof-en-financial-legislation-a936b440`, `AE-mof-en-public-finance-international-relations-economic-substance-regulations-esr-bb46d3fd` |
| Cabinet / Federal decrees | 0 | 0 | 0 | 0 | 0 | Missing | 1 | 2 | None mapped yet |
| DFM | 0 | 0 | 0 | 70 | 4 | Missing | 1 | 2 | `AE-dfm-ar-the-exchange-regulation-market-rules-27fbdedf`, `AE-dfm-ar-the-exchange-regulation-sharia-compliance-bedc9982`, `AE-dfm-the-exchange-regulation-market-rules-4ded6b02`, `AE-dfm-the-exchange-regulation-sharia-compliance-d3da0b2f` |
| ADX | 0 | 0 | 0 | 56 | 5 | Missing | 1 | 2 | `AE-adx-en-issuers-resources-rules-and-regulations-766f98d4`, `AE-adx-issuers-resources-rules-and-regulations-e058f413`, `AE-adx-main-market-company-profile-financial-reports-4bb85689`, `AE-adx-resources-rules-and-regulations-55b53564`, `AE-adx-resources-rules-and-regulations-rules-and-regulations-54bb57c7` |
| Nasdaq Dubai | 0 | 0 | 0 | 33 | 0 | Missing | 1 | 2 | None mapped yet |
| DMCC | 0 | 0 | 0 | 70 | 2 | Missing | 1 | 2 | `AE-dmcc-ar-members-support-knowledge-bank-compliance-and-regulations-52627cf3`, `AE-dmcc-members-support-knowledge-bank-compliance-and-regulations-8e5ae358` |
| Dubai Economy / DET | 0 | 0 | 0 | 0 | 0 | Missing | 1 | 2 | None mapped yet |
| Abu Dhabi DED | 0 | 0 | 0 | 20 | 3 | Missing | 1 | 2 | `AE-added-en-grow-regulations-63dfab49`, `AE-added-en-grow-regulations-legal-framework-8bf9c82e`, `AE-added-en-grow-regulations-consumer-protection-2f393bbc` |
| Customs / FCA / Dubai Customs | 0 | 0 | 0 | 10 | 0 | Missing | 1 | 2 | None mapped yet |
| UAE courts / DIFC Courts / ADGM Courts | 0 | 0 | 0 | 70 | 0 | Missing | 1 | 2 | None mapped yet |
| Insurance / health insurance / pensions | 0 | 0 | 0 | 20 | 1 | Missing | 1 | 2 | `AE-doh-en-about-law-and-legislations-cb95f328` |
| Cyber/security official advisories | 0 | 0 | 0 | 0 | 0 | Missing | 1 | 2 | None mapped yet |
| Other UAE free zones with regulatory relevance | 0 | 0 | 0 | 78 | 7 | Missing | 1 | 2 | `AE-rakez-ar-about-rules-regulations-1012f9c7`, `AE-rakez-ar-about-rules-and-regulations-2243c3b1`, `AE-rakez-en-about-rules-and-regulations-56a0b9cf`, `AE-rakez-en-about-rules-regulations-03510805`, `AE-jafza-ar-resource-centre-guides-category-regulations-9d22ba99`, `AE-jafza-resource-centre-guides-category-regulations-dbf4ad97`, `AE-jafza-resources-guides-rules-and-regulations-at-jafza-c3cff8c7` |
