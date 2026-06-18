# FTA / ADGM Eight Evidence, Baseline, and Gate Report

Date: 2026-06-18

## Evidence Phase Summary

Only two no-save strong passes proceeded to evidence/baseline:

- `AE-adgm-fsra-supervision-circulars`
- `AE-adgm-data-protection-regulations-2021-pdf`

The five FTA URLs and `AE-adgm-fsra-regulatory-alerts` did not proceed because they failed no-save extraction gates.

## Evidence / Baseline / Monitor Results

| source_id | Proof path | Normalized text path | Normalized hash | Baseline | Mass-monitor dry-run | Decision |
|---|---|---|---|---:|---|---|
| `AE-adgm-fsra-supervision-circulars` | `data/source_snapshots/2026-06-18/AE/AE-adgm-fsra-supervision-circulars/intake-20260618T091915Z/proof.json` | `data/source_snapshots/2026-06-18/AE/AE-adgm-fsra-supervision-circulars/intake-20260618T091915Z/normalized.txt` | `6c1e3f3f4634f70efc0e61fd627649059dd23ea6fcd4f53ab23240e7bfdeef00` | 2 / 2 | `MONITOR_OK`, no drift | Active. |
| `AE-adgm-data-protection-regulations-2021-pdf` | `data/source_snapshots/2026-06-18/AE/AE-adgm-data-protection-regulations-2021-pdf/intake-20260618T091917Z/proof.json` | `data/source_snapshots/2026-06-18/AE/AE-adgm-data-protection-regulations-2021-pdf/intake-20260618T091917Z/normalized.txt` | `cdaa340d5523440c1b15bb8b3d11f78b0e330e0a7c53fb68c01606ff8b44d6d5` | 2 / 2 | `MONITOR_OK`, no drift | Active. |

## Held / Candidate Sources

| source_id | Decision | Reason |
|---|---|---|
| `AE-fta-tax-legislation-listing` | Candidate | `NAV_SHELL_ONLY`, normalized_length=35. |
| `AE-fta-vat-guides-references` | Candidate | `NAV_SHELL_ONLY`, normalized_length=66. |
| `AE-fta-corporate-tax-guides-references` | Candidate | `NAV_SHELL_ONLY`, normalized_length=37. |
| `AE-fta-media-centre` | Candidate | `NAV_SHELL_ONLY`, normalized_length=36. |
| `AE-fta-corporate-tax-legislation` | Candidate | `NAV_SHELL_ONLY`, normalized_length=11. |
| `AE-adgm-fsra-regulatory-alerts` | Candidate | Official/public page, but current listing selector isolated no regulatory-alert rows and remained nav-shell-like. |

## Agent Gate Emulation

| Gate | Result | Notes |
|---|---|---|
| Source Monitor | PASS for 2 active; BLOCK for 6 candidates | Active sources returned stable monitor output and `MONITOR_OK`; candidates failed no-save. |
| Evidence Trail | PASS for 2 active | Proof paths, normalized text paths, normalized hashes, and 2/2 baseline exist. |
| QA / Critic | PASS | No no-save-only row remains active. |
| Legal Language | PASS | Copy was revised away from FTA-active claims and full/complete coverage framing. |
| Product Manager | PASS | ADGM depth improves; FTA remains a disclosed gap rather than inflated coverage. |
| Code Architect | PASS | Narrow adapter changes only; existing gates remain intact. |

## Final Gate Decision

Activated:

- `AE-adgm-fsra-supervision-circulars`
- `AE-adgm-data-protection-regulations-2021-pdf`

Held as candidates:

- five FTA sub-pages;
- `AE-adgm-fsra-regulatory-alerts`.

Monitoring intelligence only. Not legal advice.
