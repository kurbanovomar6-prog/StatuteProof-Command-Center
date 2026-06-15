# Mass Monitoring No-Save Batch Report

Date: 2026-06-15

## Scope

Scoped live no-save checks only. No broad monitoring, no customer delivery, no alerts, and no evidence save during the no-save phase.

## Results

| Source ID | URL | Adapter | Quality | No-Save Status | Hash | Decision |
|---|---|---|---:|---|---|---|
| `AE-sca-circulars-rules-procedures` | https://www.sca.gov.ae/en/regulations/circulars-rules-and-procedures | `sca_listing` | 62 | `CONFIRMED_ACCESSIBLE` | `d1068c3fabf6ddb2641c988dbc834be1b76f50d38a23ec9026ffd13a4e5ff213` | save baseline |
| `AE-dfsa-financial-crime-mlro-letters` | https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance/financial-crime-prevention-notices-and-mlro-letters | `dfsa_notice_listing` | 63 | `CONFIRMED_ACCESSIBLE` | `7fefb2b0aeb6d6b2cd9de832c03b7f5586add963e192563dfae91648b33b92ae` | save baseline |
| `AE-dfsa-aml-rulebook-module` | https://dfsaen.thomsonreuters.com/rulebook/anti-money-laundering-counter-terrorist-financing-and-sanctions-module-aml-ver3004-26 | `static_html` | 61 | `CONFIRMED_ACCESSIBLE` | `04ece793f346ae66021950a50156127204834fc532d0606f4338e19e4e30e4f5` | save baseline, then hold after monitor dry-run |
| `AE-eocn-un-sanctions-page` | https://www.uaeiec.gov.ae/en-us/un-page | `table` | 35 | `NEEDS_SELECTOR_REVIEW` | `36cc6d2fb26d25467e2d90e97f2ee12584a8e059e02f788cfcca0cb755725c3f` | remediation |

## Important Finding

SCA circulars were previously blocked because `form` removal deleted the ASP.NET page content before adapter extraction. This is now fixed for `sca_listing`.

