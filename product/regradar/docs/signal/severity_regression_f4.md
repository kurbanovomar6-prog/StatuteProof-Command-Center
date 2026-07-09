# Severity regression — F4 (full new stack vs pre-sprint rubric)

Pre = rubric at branch base 1e10e9f over v1 diffs. Post = error-page gate → v2 normalization → diff → word-bounded EN+AR rubric + format-shift guard.

| # | source | ts | class | pre | post | justification |
|---|--------|----|-------|-----|------|---------------|
| 1 | AE-uae-ministry-of-economy | 2026-05-30T12:05 | CHROME_SHUFFLE | LOW | NO_DIFF | chrome/title/counter noise eliminated by v2 normalization (F1) — correct: no customer alert |
| 2 | AE-central-bank-of-the-uae | 2026-05-30T12:06 | COUNTER | MEDIUM | NO_DIFF | chrome/title/counter noise eliminated by v2 normalization (F1) — correct: no customer alert |
| 3 | AE-dubai-virtual-assets-regulatory-autho | 2026-05-30T12:06 | CHROME_SHUFFLE | HIGH | NO_DIFF | chrome/title/counter noise eliminated by v2 normalization (F1) — correct: no customer alert |
| 4 | AE-dubai-financial-services-authority-df | 2026-05-30T12:06 | CHROME_SHUFFLE | HIGH | NO_DIFF | chrome/title/counter noise eliminated by v2 normalization (F1) — correct: no customer alert |
| 5 | AE-uae-ministry-of-finance | 2026-05-30T12:09 | CHROME_SHUFFLE | MEDIUM | NO_DIFF | chrome/title/counter noise eliminated by v2 normalization (F1) — correct: no customer alert |
| 6 | AE-uae-legislation-portal | 2026-05-30T12:10 | CHROME_SHUFFLE | MEDIUM | NO_DIFF | chrome/title/counter noise eliminated by v2 normalization (F1) — correct: no customer alert |
| 7 | AE-uae-financial-intelligence-unit-uaefi | 2026-05-30T12:10 | COUNTER | MEDIUM | NO_DIFF | chrome/title/counter noise eliminated by v2 normalization (F1) — correct: no customer alert |
| 8 | AE-difc-laws-and-regulations | 2026-05-30T12:10 | CHROME_SHUFFLE | LOW | NO_DIFF | chrome/title/counter noise eliminated by v2 normalization (F1) — correct: no customer alert |
| 9 | AE-uae-ministry-of-economy | 2026-05-30T12:10 | CHROME_SHUFFLE | MEDIUM | NO_DIFF | chrome/title/counter noise eliminated by v2 normalization (F1) — correct: no customer alert |
| 10 | AE-uae-legislation-portal | 2026-05-30T12:14 | CHROME_SHUFFLE | MEDIUM | NO_DIFF | chrome/title/counter noise eliminated by v2 normalization (F1) — correct: no customer alert |
| 11 | AE-uae-legislation-portal | 2026-05-30T12:19 | CHROME_SHUFFLE | MEDIUM | NO_DIFF | chrome/title/counter noise eliminated by v2 normalization (F1) — correct: no customer alert |
| 12 | AE-uae-legislation-portal | 2026-05-30T12:24 | COUNT_CHANGE | LOW | LOW | verdict preserved |
| 13 | AE-uae-legislation-portal | 2026-05-30T16:09 | COUNT_CHANGE | LOW | LOW | verdict preserved |
| 14 | AE-central-bank-of-the-uae | 2026-06-11T22:28 | COUNTER | MEDIUM | MEDIUM | verdict preserved |
| 15 | AE-dubai-financial-services-authority-df | 2026-06-11T22:29 | CHROME_SHUFFLE | HIGH | MEDIUM | downgrade justified: CHROME_SHUFFLE noise; word-boundary/topic-term fix |
| 16 | AE-uae-ministry-of-finance | 2026-06-11T22:32 | CHROME_SHUFFLE | MEDIUM | MEDIUM | verdict preserved |
| 17 | AE-uae-financial-intelligence-unit-uaefi | 2026-06-11T22:33 | COUNT_CHANGE | LOW | LOW | verdict preserved |
| 18 | AE-uae-ministry-of-economy | 2026-06-11T22:33 | LANG_FLAP | MEDIUM | HIGH | upgrade: real obligation terms now matched on LANG_FLAP delta — residual noise class, eliminated at source by F1 reset/stable adapters |
| 19 | AE-dubai-virtual-assets-regulatory-autho | 2026-06-11T22:44 | ERROR_PAGE | MEDIUM | ERROR_PAGE_FILTERED | error page rejected before hashing (F1) — correct: FAILED, not CHANGED |
| 20 | AE-uae-legislation-portal | 2026-06-11T22:48 | ERROR_PAGE | MEDIUM | ERROR_PAGE_FILTERED | error page rejected before hashing (F1) — correct: FAILED, not CHANGED |
| 21 | AE-uae-ministry-of-economy | 2026-06-11T22:49 | CHROME_SHUFFLE | LOW | LOW | verdict preserved |
| 22 | AE-central-bank-of-the-uae | 2026-06-12T12:54 | COUNTER | MEDIUM | MEDIUM | verdict preserved |
| 23 | AE-dubai-virtual-assets-regulatory-autho | 2026-06-12T12:54 | CHROME_SHUFFLE | MEDIUM | HIGH | upgrade: real obligation terms now matched on CHROME_SHUFFLE delta — residual noise class, eliminated at source by F1 reset/stable adapters |
| 24 | AE-uae-ministry-of-economy | 2026-06-12T13:14 | REBRAND | LOW | LOW | verdict preserved |
| 25 | AE-cbuae-regulations | 2026-06-12T13:14 | COUNTER | HIGH | LOW | downgrade justified: COUNTER noise; word-boundary/topic-term fix |
| 26 | AE-cbuae-circulars | 2026-06-12T13:15 | COUNTER | HIGH | LOW | downgrade justified: COUNTER noise; word-boundary/topic-term fix |
| 27 | AE-adgm-fsra-financial-crime-prevention | 2026-06-15T12:56 | WRONG_PAGE | MEDIUM | MEDIUM | verdict preserved |
| 28 | AE-adgm-fsra-rulebooks | 2026-06-15T13:07 | WRONG_PAGE | MEDIUM | MEDIUM | verdict preserved |
| 29 | AE-dfsa-aml-rulebook-module | 2026-06-15T13:22 | CHROME_SHUFFLE | LOW | LOW | verdict preserved |
| 30 | AE-uaefiu-typology-reports | 2026-06-15T17:37 | ADAPTER_FORMAT | MEDIUM | LOW | shift within noise class ADAPTER_FORMAT |
| 31 | AE-dubai-financial-services-authority-df | 2026-06-18T20:16 | ADAPTER_FORMAT | HIGH | MEDIUM | adapter format shift named honestly (F4 guard); capped from HIGH |
| 32 | AE-sca-aml-cft | 2026-06-19T14:29 | ADAPTER_FORMAT | HIGH | MEDIUM | adapter format shift named honestly (F4 guard); capped from HIGH |
| 33 | AE-sca-aml-cft | 2026-06-19T14:30 | ADAPTER_FORMAT | HIGH | MEDIUM | adapter format shift named honestly (F4 guard); capped from HIGH |
| 34 | AE-cbuae-retail-payment-services-ruleboo | 2026-06-19T14:55 | ADAPTER_FORMAT | MEDIUM | MEDIUM | verdict preserved |
| 35 | AE-cbuae-exchange-business-regulation-do | 2026-06-19T14:57 | ADAPTER_FORMAT | HIGH | HIGH | verdict preserved |
| 36 | AE-cbuae-model-management-standards-docl | 2026-06-19T14:57 | ADAPTER_FORMAT | HIGH | MEDIUM | downgrade justified: ADAPTER_FORMAT noise; word-boundary/topic-term fix |
| 37 | AE-cbuae-tbml-transshipment-guidance-doc | 2026-06-19T14:58 | ADAPTER_FORMAT | HIGH | MEDIUM | downgrade justified: ADAPTER_FORMAT noise; word-boundary/topic-term fix |
| 38 | AE-eocn-laws-regulations-en | 2026-06-19T15:00 | ADAPTER_FORMAT | MEDIUM | HIGH | upgrade: real obligation terms now matched on ADAPTER_FORMAT delta — residual noise class, eliminated at source by F1 reset/stable adapters |
| 39 | AE-uaefiu-typology-reports | 2026-06-19T15:02 | ADAPTER_FORMAT | LOW | LOW | verdict preserved |
| 40 | AE-uaefiu-publications-hub | 2026-06-19T15:02 | ADAPTER_FORMAT | MEDIUM | MEDIUM | verdict preserved |
| 41 | AE-sca-circulars-rules-procedures | 2026-06-19T15:05 | ADAPTER_FORMAT | LOW | LOW | verdict preserved |
| 42 | AE-vara-compliance-risk-rulebook-pdf | 2026-06-19T15:07 | PDF_REFLOW | MEDIUM | HIGH | upgrade: real obligation terms now matched on PDF_REFLOW delta — residual noise class, eliminated at source by F1 reset/stable adapters |
| 43 | AE-vara-technology-information-rulebook- | 2026-06-19T15:07 | PDF_REFLOW | MEDIUM | MEDIUM | verdict preserved |
| 44 | AE-vara-va-issuance-rulebook-pdf | 2026-06-19T15:08 | PDF_REFLOW | MEDIUM | HIGH | upgrade: real obligation terms now matched on PDF_REFLOW delta — residual noise class, eliminated at source by F1 reset/stable adapters |
| 45 | AE-vara-broker-dealer-rulebook-pdf | 2026-06-19T15:08 | PDF_REFLOW | MEDIUM | MEDIUM | verdict preserved |
| 46 | AE-vara-lending-borrowing-rulebook-pdf | 2026-06-19T15:08 | PDF_REFLOW | MEDIUM | MEDIUM | verdict preserved |
| 47 | AE-vara-va-regulations-2023-pdf | 2026-06-19T15:08 | PDF_REFLOW | MEDIUM | HIGH | upgrade: real obligation terms now matched on PDF_REFLOW delta — residual noise class, eliminated at source by F1 reset/stable adapters |
| 48 | AE-adgm-fsra-guidance-policy | 2026-06-19T15:09 | WRONG_PAGE | HIGH | HIGH | verdict preserved |
| 49 | AE-adgm-ra-circulars | 2026-06-19T15:09 | WRONG_PAGE | HIGH | HIGH | verdict preserved |
| 50 | AE-adgm-listing-rules | 2026-06-19T15:09 | ADAPTER_FORMAT | MEDIUM | MEDIUM | verdict preserved |
| 51 | AE-dfsa-financial-crime-mlro-letters | 2026-06-19T15:11 | ADAPTER_FORMAT | HIGH | HIGH | verdict preserved |
| 52 | AE-dfsa-aml-rulebook-module | 2026-06-19T15:11 | CHROME_SHUFFLE | LOW | LOW | verdict preserved |
| 53 | AE-dfsa-consultation-current | 2026-06-19T15:11 | ADAPTER_FORMAT | MEDIUM | MEDIUM | verdict preserved |
| 54 | AE-dfsa-consultation-paper-165 | 2026-06-19T15:12 | ADAPTER_FORMAT | HIGH | MEDIUM | downgrade justified: ADAPTER_FORMAT noise; word-boundary/topic-term fix |
| 55 | AE-difc-data-protection-regulation-10 | 2026-06-19T15:17 | ADAPTER_FORMAT | LOW | LOW | verdict preserved |
| 56 | AE-dfsa-guidance-notes | 2026-06-19T16:39 | ADAPTER_FORMAT | HIGH | MEDIUM | adapter format shift named honestly (F4 guard); capped from HIGH |
| 57 | AE-dfsa-what-we-do-enforcement-1a837c50 | 2026-06-19T16:40 | ADAPTER_FORMAT | MEDIUM | MEDIUM | verdict preserved |
| 58 | AE-difc-legal-database | 2026-06-21T21:40 | ADAPTER_FORMAT | MEDIUM | MEDIUM | verdict preserved |
| 59 | AE-sca-regulations-listing | 2026-06-21T21:41 | ADAPTER_FORMAT | LOW | MEDIUM | shift within noise class ADAPTER_FORMAT |
| 60 | AE-adgm-fsra-guidance-policy | 2026-06-21T21:44 | WRONG_PAGE | HIGH | HIGH | verdict preserved |
| 61 | AE-difc-legal-database | 2026-06-21T21:45 | ADAPTER_FORMAT | LOW | LOW | verdict preserved |
| 62 | AE-dfsa-financial-crime-mlro-letters | 2026-07-05T12:54 | TITLE_FLIP | LOW | NO_DIFF | chrome/title/counter noise eliminated by v2 normalization (F1) — correct: no customer alert |
| 63 | AE-dfsa-financial-crime-mlro-letters | 2026-07-05T13:28 | TITLE_FLIP | LOW | NO_DIFF | chrome/title/counter noise eliminated by v2 normalization (F1) — correct: no customer alert |

Shift totals: {('MEDIUM', 'MEDIUM'): 14, ('LOW', 'LOW'): 11, ('HIGH', 'MEDIUM'): 8, ('MEDIUM', 'NO_DIFF'): 7, ('MEDIUM', 'HIGH'): 6, ('HIGH', 'HIGH'): 5, ('LOW', 'NO_DIFF'): 4, ('HIGH', 'NO_DIFF'): 2, ('MEDIUM', 'ERROR_PAGE_FILTERED'): 2, ('HIGH', 'LOW'): 2, ('MEDIUM', 'LOW'): 1, ('LOW', 'MEDIUM'): 1}
