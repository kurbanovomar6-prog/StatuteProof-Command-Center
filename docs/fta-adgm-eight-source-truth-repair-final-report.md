# FTA / ADGM Eight-Source Truth Repair Final Report

Date: 2026-06-18

## 1. Starting Verified Truth

Last verified committed truth before the dirty rows was:

- 79 enabled UAE sources
- 78 monitoring-active sources
- 1 remediation source

## 2. Dirty Truth Before Repair

The dirty worktree temporarily claimed:

- 87 enabled UAE sources
- 86 active sources
- 1 remediation source

That claim was not acceptable because eight newly added FTA/ADGM rows were marked active before they had stable `source_id`, proof artifacts, normalized hashes, repeat baseline, and `MONITOR_OK`.

## 3. Final Truth After Repair

After no-save tests, evidence saves, repeat baseline checks, mass-monitor dry-run, and source-gate review:

- 81 enabled UAE sources
- 80 monitoring-active sources
- 1 remediation source

No unvalidated active rows remain.

## 4. Eight-Row Decisions

| Proposed source ID | Source | Final decision | Reason |
| --- | --- | --- | --- |
| `AE-fta-tax-legislation-listing` | Federal Tax Authority — All Tax Legislation | Candidate, disabled | Official/public, but no-save returned title/nav-shell only. Not meaningful enough for monitoring. |
| `AE-fta-vat-guides-references` | Federal Tax Authority — VAT Guides and References | Candidate, disabled | Official/public, but extraction returned shallow/nav-shell output. Needs item-level adapter work. |
| `AE-fta-corporate-tax-guides-references` | Federal Tax Authority — Corporate Tax Guides and References | Candidate, disabled | Official/public, but extraction did not isolate guide rows. |
| `AE-fta-media-centre` | Federal Tax Authority — Media Centre | Candidate, disabled | Official/public, but no-save output was too shallow and not suitable for active monitoring. |
| `AE-fta-corporate-tax-legislation` | Federal Tax Authority — Corporate Tax Legislation | Candidate, disabled | Official/public, but extraction returned only title-level content. |
| `AE-adgm-fsra-supervision-circulars` | ADGM FSRA Supervision Circulars | Active | Passed no-save, saved proof, 2/2 baseline, mass-monitor `MONITOR_OK`, and gates. |
| `AE-adgm-fsra-regulatory-alerts` | ADGM FSRA Regulatory Alerts | Candidate, disabled | Official/public, but live page did not isolate alert rows with the current adapter. |
| `AE-adgm-data-protection-regulations-2021-pdf` | ADGM Data Protection Regulations 2021 PDF | Active | Passed direct PDF extraction, saved proof, 2/2 baseline, mass-monitor `MONITOR_OK`, and gates. |

## 5. No-Save Results

| Source ID | No-save status | Quality | Can save evidence |
| --- | --- | --- | --- |
| `AE-fta-tax-legislation-listing` | `NAV_SHELL_ONLY` | 0 | No |
| `AE-fta-vat-guides-references` | `NAV_SHELL_ONLY` | 0 | No |
| `AE-fta-corporate-tax-guides-references` | `NAV_SHELL_ONLY` | 0 | No |
| `AE-fta-media-centre` | `NAV_SHELL_ONLY` | 0 | No |
| `AE-fta-corporate-tax-legislation` | `NAV_SHELL_ONLY` | 0 | No |
| `AE-adgm-fsra-supervision-circulars` | `CONFIRMED_ACCESSIBLE` | 65 | Yes |
| `AE-adgm-fsra-regulatory-alerts` | `NAV_SHELL_ONLY` | 0 | No |
| `AE-adgm-data-protection-regulations-2021-pdf` | `CONFIRMED_ACCESSIBLE` | 61 | Yes |

## 6. Evidence Saved

2 sources saved proof-backed evidence:

- `AE-adgm-fsra-supervision-circulars`
- `AE-adgm-data-protection-regulations-2021-pdf`

## 7. Baseline-Complete Count

2 sources completed repeat baseline with `baseline_runs_completed: 2`.

## 8. MONITOR_OK Count

2 sources passed mass-monitor dry-run with `MONITOR_OK`.

## 9. Newly Active Sources

1. `AE-adgm-fsra-supervision-circulars`
2. `AE-adgm-data-protection-regulations-2021-pdf`

## 10. Demoted / Held Sources

1. `AE-fta-tax-legislation-listing`
2. `AE-fta-vat-guides-references`
3. `AE-fta-corporate-tax-guides-references`
4. `AE-fta-media-centre`
5. `AE-fta-corporate-tax-legislation`
6. `AE-adgm-fsra-regulatory-alerts`

These are retained as disabled candidates, not active sources.

## 11. Adapter / Parser Changes

- Improved direct PDF document normalization to preserve line breaks and headings before quality scoring.
- Expanded ADGM FSRA listing token support for alert/notice/enforcement terminology.
- Kept FTA rows out of active status because current extraction is not meaningful.

## 12. Tests Added

- Added fixture test for ADGM direct PDF extraction quality.
- Added fixture test for ADGM FSRA regulatory-alert listing extraction.

## 13. Validators Added

- Added `tools/validate_no_unvalidated_active_sources.py`.
- Updated source-truth validators to protect 81 enabled / 80 monitoring-active / 1 remediation.
- Updated plan/pricing validator to protect the 80-source UAE Monitor limit.
- Updated coverage-claim validator to current source truth.

## 14. Customer Copy Changes

- Removed FTA tax pages from active coverage claims.
- Updated customer-facing counts to 81 enabled / 80 monitoring-active / 1 remediation.
- Reframed FTA tax pages as candidates requiring item-level extraction remediation.
- Avoided absolute all-UAE coverage, all-source coverage, legal advice, and guarantee claims.

## 15. Unvalidated Active Rows Remain?

No.

## 16. Did We Make A Prohibited All-UAE Coverage Claim?

No.

## 17. Next Exact 1000-Source Mapping Step

Create the UAE 1000-source universe candidate file and top-250 activation queue with the repaired 81/80/1 source truth as the baseline. Do not add any candidate to `sources.json` as active without proof, repeat baseline, `MONITOR_OK`, and gates.
