# Weak-Zone Elimination Evidence + Baseline Report

Date: 2026-06-16

## Evidence Summary

- Evidence candidates saved: **14** strong no-save candidates.
- Candidates held after evidence/dry-run: **4**.
- Sources activated after proof, repeat baseline, mass-monitor dry-run, and gates: **10**.
- Proof runs saved for activated sources: **20**.
- Baseline-complete activated sources: **10**.
- Mass-monitor `MONITOR_OK`: **10** activated sources.

## Activated Sources

| Source ID | Proof/baseline | Dry-run | Decision |
| --- | --- | --- | --- |
| `AE-vara-rulebook-updates` | 2 stable proof runs | `MONITOR_OK` | activate |
| `AE-dfsa-consultation-current` | 2 stable proof runs | `MONITOR_OK` | activate |
| `AE-dfsa-enforcement-decisions-current` | 2 stable proof runs | `MONITOR_OK` | activate |
| `AE-dfsa-regulatory-actions-current` | 2 stable proof runs | `MONITOR_OK` | activate |
| `AE-cbuae-retail-payment-services-rulebook` | 2 stable proof runs | `MONITOR_OK` | activate |
| `AE-dfsa-consultation-paper-165` | 2 stable proof runs | `MONITOR_OK` | activate |
| `AE-dfsa-notice-supervisory-review` | 2 stable proof runs | `MONITOR_OK` | activate |
| `AE-cbuae-amlcft-rulebook-doclist` | 2 stable proof runs | `MONITOR_OK` | activate |
| `AE-cbuae-amlcft-entire-section-doclist` | 2 stable proof runs | `MONITOR_OK` | activate |
| `AE-cbuae-consumer-protection-rulebook-doclist` | 2 stable proof runs | `MONITOR_OK` | activate |

## Held Despite Evidence

| Source ID | Reason |
| --- | --- |
| `AE-vara-compliance-risk-rulebook` | Mass-monitor dry-run produced `QUALITY_DROP` and hash drift under static extraction. |
| `AE-cbuae-amlcft-rulebook` | Static extraction drifted; stable document-listing variant activated instead. |
| `AE-cbuae-amlcft-entire-section` | Static extraction drifted; stable document-listing variant activated instead. |
| `AE-cbuae-consumer-protection-rulebook` | Static extraction drifted; stable document-listing variant activated instead. |

## Evidence Artifacts

Detailed proof paths and hash histories are recorded in:

- `docs/weak-zone-elimination-evidence-results.json`
- `docs/weak-zone-elimination-cbuae-drift-retest.json`
- `docs/weak-zone-elimination-mass-monitor-dry-run.json`
- `docs/weak-zone-elimination-cbuae-drift-mass-monitor.json`
