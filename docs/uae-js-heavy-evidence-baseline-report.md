# UAE JS-Heavy Evidence And Repeat Baseline Report

Date: 2026-06-15

## Sources Sent To Evidence

Only one new source passed no-save strongly without duplicate-hash risk:

`AE-uaefiu-typology-reports` - UAE FIU Trends and Typology Reports.

## Evidence Results

| Run | Status | Quality | Normalized length | Normalized hash | Proof path |
| --- | --- | ---: | ---: | --- | --- |
| 1 | `CONFIRMED_ACCESSIBLE` | 65 | 6,289 | `f9752fc4906a03d12ab587db00dc1f37c9508688eeda7954d1e2f82ca3ea4c2d` | `data/source_snapshots/2026-06-15/AE/AE-uaefiu-typology-reports/intake-20260615T173740Z/proof.json` |
| 2 | `CONFIRMED_ACCESSIBLE` | 65 | 6,289 | `f9752fc4906a03d12ab587db00dc1f37c9508688eeda7954d1e2f82ca3ea4c2d` | `data/source_snapshots/2026-06-15/AE/AE-uaefiu-typology-reports/intake-20260615T173751Z/proof.json` |

Certification:

- `certification_status`: `MONITORING_CERTIFIED`
- `baseline_runs_completed`: 2 latest post-normalization runs; 4 total historical successful runs exist.
- `baseline_runs_required`: 2
- `evidence_level`: `CERTIFIED_EVIDENCE`
- `hash_stable`: true for the latest post-normalization baseline pair.
- `certification_score`: 88

## Mass-Monitor Dry-Run

Before activation, the source was tested through a temporary activation-ready queue entry:

- `source_health_status`: `MONITOR_OK`
- `quality_score`: 65
- `normalized_hash`: `f9752fc4906a03d12ab587db00dc1f37c9508688eeda7954d1e2f82ca3ea4c2d`
- `previous_hash`: `f9752fc4906a03d12ab587db00dc1f37c9508688eeda7954d1e2f82ca3ea4c2d`
- `change_detected`: false
- `evidence_written`: false
- `alert_sent`: false
- `sources_json_changed`: false

Note: an earlier pair of evidence runs produced hash `11f522...` before generic CTA/context filtering was tightened. The source was re-baselined after the normalization change; the registry uses the latest stable `f975...` hash and proof path.

## Held Evidence Decisions

- UAE FIU publications hub and annual reports were not saved because they duplicate typology output.
- UAE FIU AML/CFT laws were not saved because q=59 did not meet the q>=60 activation threshold.
- ADGM alternate-component and SCA regulations-listing pages were not saved because no strong no-save pass existed.
