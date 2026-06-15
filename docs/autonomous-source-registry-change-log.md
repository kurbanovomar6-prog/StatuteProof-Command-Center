# Autonomous Source Registry Change Log

Date: 2026-06-15

## Sources Added

| Source ID | Name | Adapter | Proof | Baseline | Monitor dry-run |
| --- | --- | --- | --- | --- | --- |
| `AE-eocn-news-en` | EOCN News and Sanctions Updates | `eocn_news_listing` | yes | 2 stable runs | `MONITOR_OK` |
| `AE-sca-regulations-listing` | SCA Regulations Listing | `sca_listing` | yes | 2 stable runs | `MONITOR_OK` |

## Public Truth Change

Before this autonomous cycle:

- 24 enabled UAE sources.
- 20 readiness-supported active sources.
- 4 under extraction remediation.

After this autonomous cycle:

- 26 enabled UAE sources.
- 22 readiness-supported active sources.
- 4 under extraction remediation.

## Sources Not Added

| Source ID | Reason |
| --- | --- |
| `AE-uaefiu-mutual-evaluation` | Duplicate normalized hash with active `AE-uaefiu-typology-reports`; likely route alias rather than distinct monitorable endpoint. |
| `AE-uaefiu-aml-cft-laws` | NAV_SHELL_ONLY with current adapter; needs FIU DOM/XHR or direct document endpoint. |
| `AE-uaefiu-nra-2024` | NAV_SHELL_ONLY with current adapter. |
| `AE-uaefiu-strategic-analysis` | NAV_SHELL_ONLY with current adapter. |
| `AE-adgm-ra-notices` | NAV_SHELL_ONLY with current custom element selector. |
| `AE-adgm-ra-aml-guides` | NAV_SHELL_ONLY with current custom element selector. |
| `AE-adgm-listing-rules` | NAV_SHELL_ONLY with current custom element selector. |
| `AE-sca-corporate-governance` | NAV_SHELL_ONLY/two-item extraction; needs detail-specific adapter or should remain covered by broader SCA regulations listing. |
| `AE-sca-fatca-crs` | Near-pass q=59 but can_save=false; needs richer context/direct document extraction. |
| `AE-sca-market-rules` | Shallow official links to ADX/DFM only; treat ADX/DFM as separate officially linked candidates if useful. |

## Validator Status

Validation must pass before commit. This log does not itself claim 50 sources.
