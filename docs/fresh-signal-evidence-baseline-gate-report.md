# Fresh Signal Evidence, Baseline, And Gate Report

## Sources Promoted

### `AE-sca-aml-cft`

Source:

- UAE SCA Anti-Money Laundering and Terrorist Financing
- `https://www.sca.gov.ae/en/regulations/anti-money-laundering-and-terrorist-financing`

Evidence:

- Latest proof path: `data/source_snapshots/2026-06-19/AE/AE-sca-aml-cft/intake-20260619T143025Z/proof.json`
- Normalized text path: `data/source_snapshots/2026-06-19/AE/AE-sca-aml-cft/intake-20260619T143025Z/normalized.txt`
- Normalized hash: `e5709af71ecda2e41656880068dd4d1290f67d2d1064de9e4b11bb1550cd2328`
- Baseline: 4 completed / 2 required
- Certification status: `MONITORING_CERTIFIED`
- Evidence level: `CERTIFIED_EVIDENCE`
- Adapter: `sca_listing`
- Adapter item count: 46
- Source Lab quality score: 65
- Mass-monitor dry-run status: `MONITOR_OK`
- Alerts sent: no
- Customer delivery: no

Decision:

- Promoted to `monitoring_mode: fresh_alert`.
- `alert_eligible: true`.
- SCA family is **not** strong yet. This is one proof-backed SCA source, not complete SCA coverage.

## Sources Tested But Not Promoted

### SCA

- `AE-sca-circulars-rules-procedures`: no-save extracted 986 chars, below threshold; needs listing adapter/refined selector.
- `AE-sca-regulations-listing`: no-save can monitor via Playwright, but proof/baseline/MONITOR_OK not completed in this pass.
- `AE-sca-fatca-crs`: no-save can monitor via Playwright, but proof/baseline/MONITOR_OK not completed in this pass.
- `AE-sca-corporate-governance`: no-save can monitor via Playwright, but proof/baseline/MONITOR_OK not completed in this pass.

### EOCN

- `AE-eocn-laws-regulations-en`: no-save can monitor via Playwright; proof/baseline/MONITOR_OK not completed in this pass.
- `AE-eocn-news-en`: no-save can monitor via Playwright; proof/baseline/MONITOR_OK not completed in this pass.

### UAE FIU

- `AE-uaefiu-typology-reports`: no-save can monitor via Playwright; proof/baseline/MONITOR_OK not completed in this pass.
- `AE-uaefiu-aml-cft-laws`: no-save can monitor via Playwright; proof/baseline/MONITOR_OK not completed in this pass.
- `AE-uaefiu-publications-hub`: no-save can monitor via Playwright; proof/baseline/MONITOR_OK not completed in this pass.

## Gate Notes

The SCA AML/CFT source had one non-adapter Source Lab run that produced a different hash. That run was not used for activation. The final promoted source uses the existing `sca_listing` adapter config from `sources.json`, matching mass-monitor behavior.

## Customer-Safe Interpretation

Allowed:

- “SCA AML/CFT has one proof-backed fresh-alert source.”

Forbidden:

- “We monitor SCA.”
- “Full SCA coverage.”
- “Complete capital markets coverage.”
- “Guaranteed compliance.”
- “Monitoring legal advice.”
