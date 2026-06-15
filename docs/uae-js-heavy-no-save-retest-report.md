# UAE JS-Heavy No-Save Retest Report

Date: 2026-06-15

## Summary

| Metric | Count |
| --- | ---: |
| Total targeted no-save retests | 8 |
| Strong no-save passes | 2 |
| New activatable no-save passes | 1 |
| Already-active confirmations | 1 |
| Held due duplicate hash/content | 2 |
| Held due quality below threshold | 1 |
| Held due nav-shell/selector unresolved | 3 |

## Retest Results

| Source ID | Regulator | Result | Quality | Hash | Activation decision |
| --- | --- | --- | ---: | --- | --- |
| `AE-uaefiu-typology-reports` | UAE FIU | `CONFIRMED_ACCESSIBLE` | 65 | `f9752fc4906a03d12ab587db00dc1f37c9508688eeda7954d1e2f82ca3ea4c2d` | Proceeded to evidence/baseline |
| `AE-uaefiu-publications-hub` | UAE FIU | `CONFIRMED_ACCESSIBLE` | 65 | `f9752fc4906a03d12ab587db00dc1f37c9508688eeda7954d1e2f82ca3ea4c2d` | Hold duplicate variant |
| `AE-uaefiu-annual-reports` | UAE FIU | `CONFIRMED_ACCESSIBLE` | 65 | `f9752fc4906a03d12ab587db00dc1f37c9508688eeda7954d1e2f82ca3ea4c2d` | Hold duplicate variant |
| `AE-uaefiu-aml-cft-laws` | UAE FIU | `CONFIRMED_ACCESSIBLE` | 59 | distinct | Hold, below q>=60 threshold |
| `AE-sca-circulars-rules-procedures` | SCA | `CONFIRMED_ACCESSIBLE` | 62 | `81af594...` | Already active, no new source |
| `AE-sca-regulations-listing` | SCA | `NAV_SHELL_ONLY` | 0 | shell/filter hash | Remediation |
| ADGM media/announcements | ADGM | nav-shell/empty | 0 | none | Remediation |
| ADGM data protection alternate pages | ADGM | nav-shell/empty | 0 | none | Remediation |

## No-Save Gate Notes

- `AE-uaefiu-typology-reports` met the strong pass gate: q=65, normalized length 6,289 after boilerplate context filtering, 30 extracted items, not nav-shell, not shallow, no active-source duplicate hash.
- `AE-uaefiu-publications-hub` and `AE-uaefiu-annual-reports` looked good in isolation but produced the same normalized hash as typology reports. They were held to prevent duplicate-source inflation.
- `AE-uaefiu-aml-cft-laws` improved from nav-shell to meaningful PDF listing, but q=59 remains below the activation threshold.
- `AE-sca-circulars-rules-procedures` confirmed existing activation but did not increase source count.
