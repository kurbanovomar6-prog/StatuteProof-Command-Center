# Final Remediation Evidence, Baseline, And Gate Report

Date: 2026-06-17

## Activated Replacement Sources

| Source ID | Proof paths | Baseline count | Normalized hash | Mass-monitor dry-run | Gates | Final decision |
| --- | --- | ---: | --- | --- | --- | --- |
| `AE-dfsa-annual-reports` | `data/source_snapshots/2026-06-17/AE/AE-dfsa-annual-reports/intake-20260617T125139Z/proof.json`; `data/source_snapshots/2026-06-17/AE/AE-dfsa-annual-reports/intake-20260617T125202Z/proof.json` | 2 / 2 | `5ac1b92a2d6cb782b2f5ec076c39866019568b99c712299662d0e36b8c17348e` | `MONITOR_OK` | Source Monitor pass; Evidence Trail pass; QA/Critic pass; Legal Language pass; Product Manager pass; Code Architect pass | Active replacement for stale DFSA main remediation endpoint. |
| `AE-dfsa-annual-aml-reports` | `data/source_snapshots/2026-06-17/AE/AE-dfsa-annual-aml-reports/intake-20260617T125139Z/proof.json`; `data/source_snapshots/2026-06-17/AE/AE-dfsa-annual-aml-reports/intake-20260617T125203Z/proof.json` | 2 / 2 | `693cf380283f665545f0a20de732d6363efbdcf7fa3abba9fab782dfbc9f98b1` | `MONITOR_OK` | Source Monitor pass; Evidence Trail pass; QA/Critic pass; Legal Language pass; Product Manager pass; Code Architect pass | Active replacement for stale DFSA notices remediation endpoint. |

## Held Remediation Source

| Source ID | Evidence decision | Exact blocker | Final decision |
| --- | --- | --- | --- |
| `AE-uae-financial-intelligence-unit-uaefiu` | No proof saved from homepage or failed replacement candidates. | Homepage produced navigation/search/language shell; NRA direct PDF returned HTTP 403; strategic-analysis route returned Error404/nav-shell; annual-report route looked duplicate-prone. | Keep remediation. Do not claim 79/79/0. |

## Gate Notes

- Source Monitor: replacement URLs are official DFSA public pages and stable report listings.
- Evidence Trail: proof paths exist, normalized hashes are stable across two saved runs, and normalized text artifacts exist.
- QA/Critic: no no-save-only, nav-shell, duplicate-shell, or generic homepage source was activated.
- Legal Language: customer-facing wording remains “Monitoring intelligence only. Not legal advice.” No complete UAE coverage claim was added.
- Product Manager: replacing stale DFSA remediation with AML/report endpoints improves buyer usefulness; keeping FIU remediation prevents false confidence.
- Code Architect: no new broad adapter was added; the sprint reused `pdf_listing` and updated registry/config truth.

## Counts

- Evidence saved count: 2 sources, 4 proof runs.
- Baseline-complete count: 2.
- Mass-monitor `MONITOR_OK` count: 2.
- Newly active replacement endpoints: 2.
- Remaining remediation: 1.
