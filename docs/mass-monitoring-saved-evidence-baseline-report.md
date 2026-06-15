# Mass Monitoring Saved Evidence + Baseline Report

Date: 2026-06-15

## Saved Evidence

| Source ID | Saved Runs | Baseline Required | Result | Latest Proof Path |
|---|---:|---:|---|---|
| `AE-sca-circulars-rules-procedures` | 2 | 2 | `MONITORING_CERTIFIED` | `data/source_snapshots/2026-06-15/AE/AE-sca-circulars-rules-procedures/intake-20260615T114453Z/proof.json` |
| `AE-dfsa-financial-crime-mlro-letters` | 2 | 2 | `MONITORING_CERTIFIED` | `data/source_snapshots/2026-06-15/AE/AE-dfsa-financial-crime-mlro-letters/intake-20260615T114257Z/proof.json` |
| `AE-dfsa-aml-rulebook-module` | 2 | 2 | `MONITORING_CERTIFIED`, held after monitor dry-run | `data/source_snapshots/2026-06-15/AE/AE-dfsa-aml-rulebook-module/intake-20260615T114343Z/proof.json` |

## Activation Interpretation

One saved run is evidence only. Two saved runs are baseline-complete, but a source is still held if the monitoring runner shows immediate hash instability or unresolved source-health risk.

## Held Source

`AE-dfsa-aml-rulebook-module` has proof-backed repeat baselines, but the mass-monitor dry-run produced a different normalized hash when the fetch path fell back to Playwright after timeout. It remains remediation until the monitor extraction path is deterministic.

