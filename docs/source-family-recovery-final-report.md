# StatuteProof Source Family Recovery Final Report

Date: 2026-06-21

## Current Correction

This report is a historical recovery-sprint artifact. A later MoJ/Gazette pass
and a later MoF pass changed current source truth to 246 enabled UAE sources /
177 fresh-alert eligible / 61 evidence-library / 5 candidate / 3 remediation.
MoF is now 7 selected fresh-alert sources; the broad MoF/tax claim remains
forbidden.

## Verdict

HOLD, but materially clearer.

This sprint did not magically make weak UAE source families complete. It fixed a
real source-truth problem: family counts for SCA/UAE FIU were inconsistent, and
the operator health report counted disabled or historical source IDs as active
blockers. After the fix, the system reports:

- Active/current source-health blockers: 0
- Disabled/historical repeated-failure source IDs: 5
- Fresh-alert eligible sources: 172
- No new source activations
- No fake `MONITOR_OK`

That improves trust, but it does not turn partial families into complete
families.

## Agent Runtime

- Fresh agents launched: 0
- Agent launch failures: 1
- Failure: `agent thread limit reached`
- Fallback used: yes, Codex local fallback

No agent packet is claimed as real.

## Families Improved

Improved by truth classification, not by new source activation:

| Family | Before | After | Why |
| --- | ---: | ---: | --- |
| DFSA | 6.0 | 6.5 | Existing selected-source set remains clean; score benefits from stronger validation/reporting discipline. |
| DIFC | 5.0 | 6.0 | Old `AE-difc-legislation` failure is now disabled/history, while active `difc.com` replacement remains proof-backed. |
| ADGM/FSRA | 5.0 | 6.0 | Old `AE-adgm-fsra-rules` failure is now disabled/history, while active ADGM/FSRA rulebook source remains proof-backed. |
| UAE FIU | 5.0 | 5.8 | Family counts corrected to 6 fresh-alert, but FIU circulars remain candidate and homepage remediation. |
| SCA | 4.0 | 5.2 | Old root portal failure is history, but SCA remains shallow and AML/CFT diff still needs parser review. |
| MoF | historical 3.5 | superseded by 7.0 selected-source score | Later MoF pass added 4 proof-backed fresh-alert sources and 4 canonical evidence records; broad MoF/tax coverage still forbidden. |
| MoJ/Gazette | 1.0 | 1.0 | Still remediation/missing for usable monitoring. |

## Families Still Blocked

- MoJ/Gazette/UAE Legislation: no proof-backed fresh-alert source.
- SCA: direct endpoints exist, but broad SCA coverage is weak and SCA AML/CFT needs parser review.
- UAE FIU: circulars remain candidate/held.
- DIFC: legal database breadth remains partial.
- ADGM/FSRA: 3 candidates remain unresolved.
- MoF: too few sources for a broad MoF claim.

## Source IDs Added

None.

## Source IDs Fixed

No source row was changed from failed to ready.

System behavior fixed:

- `product/regradar/app/source_health_timeline.py`
  - separates active enabled source blockers from disabled/historical repeated-failure source IDs.
- `product/regradar/app/verified_monitoring_digest.py`
  - includes `historical_source_health_blocked` and renders disabled-source failures separately.

## Source IDs Downgraded

None.

The following source IDs remain visible as disabled/historical failures rather
than active blockers:

- `AE-adgm-fsra-rules`
- `AE-difc-legislation`
- `AE-uae-e-laws-portal-ministry-of-justice`
- `AE-uae-federal-tax-authority-fta`
- `AE-uae-securities-and-commodities-authority-sca`

## Evidence / Proof Generated

No new evidence records were generated in this sprint.

Reason: adding or activating new sources requires source-specific proof,
hashes, repeat baseline, and review gates. This sprint fixed truth controls and
reports; it did not run a source activation sprint.

## Subsequent Focused Proof-Recovery Update

After this truth-classification sprint, a narrower UAE FIU proof-recovery sprint
created one additional local canonical evidence record:

- `evr_AE-uaefiu-typology-reports_intake-20260619T150224Z`

That record is complete and hash-verifiable, and the matching alert queue item
is linked locally. It remains `pending` review and is not brief-input eligible.
No source row was activated or strengthened, and FIU circular monitoring remains
a forbidden claim.

## Validators / Tests Added Or Updated

Updated:

- `product/regradar/reports/validate_audit.py`
- `tools/validate_verified_monitoring_digest.py`

Tests added/updated:

- `product/regradar/tests/test_source_signal_quality_audit_truth.py`
- `product/regradar/tests/test_source_health_timeline.py`
- `product/regradar/tests/test_verified_monitoring_digest.py`

New validation behavior:

- Family readiness counts must match `sources.json`.
- Disabled historical failures do not count as active source-health blockers.
- Historical source failures still appear in the operator digest.

## Frontend / Copy Changed

Updated:

- `product/regradar/web/src/data/sourceQualityAudit.ts`

No public copy was made stronger. SCA and UAE FIU counts were corrected to avoid
contradictory family claims.

## Claims Explicitly Not Made

- Complete UAE coverage.
- Complete family coverage.
- Full SCA coverage.
- FTA portal monitoring.
- UAE FIU circular monitoring.
- MoJ/Gazette monitoring readiness.
- Perfect parsing.
- Never-miss monitoring.
- Legal advice or compliance guarantee.

## Apollo Outreach Decision

Apollo is conditionally safe only for selected-source design-partner outreach.

Safe ICPs to contact now:

- VARA/VASP compliance teams.
- CBUAE/payments compliance teams.
- DNFBP/AML compliance teams.
- Selected DFSA compliance teams, with scoped source language.

ICP caution:

- DIFC and ADGM/FSRA buyers require explicit partial-family caveats.
- UAE FIU buyers require disclosure that FIU circulars remain candidate/held.

Avoid for now:

- MoJ/Gazette/UAE legislation-heavy buyers.
- SCA-heavy buyers needing broad securities-law coverage.
- Broad MoF/FTA portal-monitoring buyers.

## Next Exact Source Task

Run a focused proof-backed source activation sprint for only one family:

1. UAE FIU circulars/direct documents, or
2. DIFC legal database/listing, or
3. ADGM/FSRA candidate rows.

Do not activate anything from no-save only. Require proof, hash, repeat
baseline, and validator pass.

## Next Exact Evidence Task

Generate or link canonical evidence for the top 5 high-signal alert candidates:

- `AE-adgm-ra-circulars`
- `AE-adgm-fsra-guidance-policy`
- `AE-adgm-fsra-rulebooks`
- `AE-dfsa-financial-crime-mlro-letters`
- `AE-uaefiu-typology-reports`

## Next Exact Sales Task

Prepare an Apollo sequence for selected-source pilots only. The first line
should not sell "UAE coverage." It should sell:

> selected official-source UAE regulatory monitoring with evidence gates,
> human review, and disclosed source limitations.

## Boundary

This report improves operational truth. It does not prove customer delivery,
complete coverage, or production readiness.
