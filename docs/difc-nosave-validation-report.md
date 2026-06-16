# DIFC No-Save Validation Report

Date: 2026-06-16

Mode: controlled Source Lab no-save only. No evidence was written in this phase.

## Summary

| Metric | Count |
| --- | ---: |
| Official DIFC candidates no-save tested | 10 |
| Strong no-save passes | 8 |
| Held after no-save | 2 |
| Rejected stale routes outside batch | 2 |

## No-Save Results

| Source ID | URL | Adapter | Score | Hash prefix | Status | Decision |
| --- | --- | --- | ---: | --- | --- | --- |
| `AE-difc-laws-regulations` | `https://www.difc.com/business/laws-and-regulations/` | `difc_legal_database` | 65 | `421b07ad9b74` | `CONFIRMED_ACCESSIBLE` | Strong pass; saved as canonical `AE-difc-laws-and-regulations`. |
| `AE-difc-legal-database` | `https://www.difc.com/business/laws-and-regulations/legal-database/` | `difc_legal_database` | 65 | `59b9e188efb5` | `CONFIRMED_ACCESSIBLE` | Strong pass. |
| `AE-difc-consultation-papers` | `https://www.difc.com/business/laws-and-regulations/consultation-papers/` | `difc_legal_database` | 59 | `824440319e7f` | `CONFIRMED_ACCESSIBLE` | Held: below strict evidence threshold. |
| `AE-difc-data-protection-commissioner` | `https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection` | `difc_legal_database` | 65 | `f7b916ee9155` | `CONFIRMED_ACCESSIBLE` | Strong pass. |
| `AE-difc-data-protection-guidance` | `https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/guidance` | `difc_legal_database` | 65 | `de25f8c5e0ee` | `CONFIRMED_ACCESSIBLE` | Strong pass. |
| `AE-difc-data-protection-regulation-10` | `https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/regulation-10` | `difc_legal_database` | 65 | `aae352726964` | `CONFIRMED_ACCESSIBLE` | Strong pass. |
| `AE-difc-data-protection-supervision-enforcement` | `https://www.difc.com/business/registrars-and-commissioners/commissioner-of-data-protection/supervision-enforcement` | `difc_legal_database` | 65 | `fd7a2b31d603` | `CONFIRMED_ACCESSIBLE` | Strong pass. |
| `AE-difc-data-protection-law-2020` | `https://www.difc.com/business/laws-and-regulations/legal-database/difc-laws/data-protection-law-difc-law-no-5-2020` | `difc_legal_database` | 62 | `0d1f16591c75` | `CONFIRMED_ACCESSIBLE` | Strong pass; JS-heavy detail page. |
| `AE-difc-digital-assets-law-2024` | `https://www.difc.com/business/laws-and-regulations/legal-database/difc-laws/digital-assets-law-difc-law-no-2-of-2024` | `difc_legal_database` | 59 | `71900471ccc5` | `CONFIRMED_ACCESSIBLE` | Held: below strict evidence threshold. |
| `AE-difc-companies-law-2018` | `https://www.difc.com/business/laws-and-regulations/legal-database/difc-laws/companies-law-difc-law-no-5-2018` | `difc_legal_database` | 65 | `9a3aeae973b0` | `CONFIRMED_ACCESSIBLE` | Strong pass; JS-heavy detail page. |

## Rejected / Not Activated

| Candidate | Reason |
| --- | --- |
| `AE-difc-data-protection-old` | Old official-domain route returns 404; replaced by current Commissioner of Data Protection pages. |
| `AE-difc-legislation-old` | Historical `difc.ae` route remains disabled/navigation-only; no activation. |

## Notes

- No no-save-only candidate was added to `sources.json`.
- Two below-threshold public pages remain held even though they are official.
- DIFC coverage is improved, but end-to-end DIFC source scope is not claimed.
