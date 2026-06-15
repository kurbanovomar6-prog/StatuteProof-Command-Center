# UAE JS-Heavy Source Remediation Final Report

Date: 2026-06-15

## Executive Verdict

The sprint converted one JS-heavy official UAE source into a proof-backed, baseline-tested, mass-monitor-ready source:

`AE-uaefiu-typology-reports` - UAE FIU Trends and Typology Reports.

The source count moved from **23 enabled / 19 readiness-supported / 4 remediation** to **24 enabled / 20 readiness-supported / 4 remediation**.

## What Improved

- Playwright fetches now retry `page.content()` once when the rendered page is still navigating.
- FIU/EOCN document listings preserve item context in normalized output.
- Two substantial document-listing items can count as structured content when normalized text is meaningful.
- AML/FIU/TFS typology language contributes to regulatory density scoring.
- One new FIU source passed no-save, proof save, repeat baseline, mass-monitor dry-run, and agent gates.

## Source Results

| Group | Retested | Strong passes | Activated |
| --- | ---: | ---: | ---: |
| UAE FIU | 4 | 1 new plus 2 duplicate variants | 1 |
| SCA | 2 | 1 already-active confirmation | 0 |
| ADGM alternate components | 2 | 0 | 0 |

## Evidence Results

- Saved evidence count: 4 runs total for this source; the latest 2 post-normalization runs are the canonical baseline.
- Baseline-complete count: 1 source.
- Mass-monitor `MONITOR_OK` count: 1 source.
- New active sources added: 1.

## Did We Reach 50?

No. Current truth is **24 enabled / 20 readiness-supported / 4 remediation**. Reaching 50 still requires 26 more genuinely passing sources with proof, baseline, and gates.

## Remaining Blockers

- UAE FIU: More routes are accessible but duplicate current typology output. AML/CFT laws improved to q=59 but remains below threshold.
- SCA: Circulars source is stable, but other JS-filtered listing pages remain nav/filter shells.
- ADGM: Media/announcements and data protection pages need an alternate component selector map beyond `adgm-page`.
- CBUAE/DFSA/DIFC: Prior access and nav-shell blockers remain; no unsafe bypass attempted.

## Next Exact Task

Raise UAE FIU AML/CFT laws from q=59 to q>=60 without weakening gates by extracting richer PDF descriptions or document metadata, then rerun no-save, proof, repeat baseline, and mass-monitor dry-run.
