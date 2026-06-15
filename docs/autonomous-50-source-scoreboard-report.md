# Autonomous 50-Source Scoreboard Report

Date: 2026-06-15

## Scoreboard Summary

- Total target sources: 114
- Activation-ready/current active count: 22
- No-save-passed count: 6
- Evidence-saved count: 13
- Baseline-complete count: 22
- Remediation count: 51
- Blocked count: 1
- Rejected count: 0
- Remaining to 50: 28

## Next Highest-Leverage Batch

| source_id | why |
| --- | --- |
| AE-uaefiu-aml-cft-laws | near-term official source with known adapter family or close prior result |
| AE-sca-fatca-crs | near-pass q=59; needs richer context/direct document adapter to reach evidence threshold |
| AE-adgm-ra-notices | alternate ADGM component still needs DOM/XHR selector remediation |
| AE-adgm-ra-aml-guides | alternate ADGM component still needs DOM/XHR selector remediation |
| AE-adgm-listing-rules | alternate ADGM component still needs DOM/XHR selector remediation |
| AE-sca-corporate-governance | SCA rendered listing found two items but still classified nav-shell/too narrow |
| AE-vara-rulebooks | VARA official rulebook/PDF routes need stable endpoint/selector review |
| AE-cbuae-publications | CBUAE document/publication routes need safe alternate endpoint discovery |

## Batch-Onboarding Status

partial: EOCN and SCA source-specific adapters added two activation-ready sources this cycle; batch no-save works, but JS-heavy/stale pages still require source-specific DOM/XHR remediation before evidence save.

Batch-onboarding is possible for no-save testing and candidate classification. It is not yet a full activation factory because evidence save, repeat baseline, and agent gates still require targeted operator review and source-specific remediation.

## What Blocks Batch-Onboarding

- Low strong-pass conversion on JS-heavy government pages.
- Duplicate normalized hash variants across similar FIU routes.
- Generic listing adapters can over-score navigation-heavy pages unless source-specific filters are used.
- Missing scoreboard validator before this cycle.
- Fragmented queue state across multiple JSON files.
- Source-specific selectors still required for SCA and ADGM alternate components.
