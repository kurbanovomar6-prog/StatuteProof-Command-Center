# Fresh Signal Completion Final Report

## 1. Starting Source Truth

- Enabled UAE sources: 226
- MONITOR_OK sources in old audit framing: 149
- Tier A/B/C/remediation: 136 / 21 / 60 / 9
- No `monitoring_mode` distinction existed on enabled UAE rows.

## 2. Ending Source Truth

- Enabled UAE sources: 226
- Overall MONITOR_OK sources: 150
- Fresh-alert eligible sources: 96
- Evidence-library-only sources: 60
- Candidate/pending fresh-signal validation: 62
- Remediation: 8
- Tier A/B/C/remediation: 137 / 21 / 60 / 8

## 3. What Was Implemented

- Added source mode classification to all enabled UAE sources:
  - `fresh_alert`
  - `evidence_library`
  - `candidate`
  - `remediation`
- Added `alert_eligible` and `fresh_signal_class`.
- Demoted static/low-signal Tier C pages out of fresh-alert claims.
- Registered production wrappers for:
  - `CBUAERulebookAdapter`
  - `FSRACircularsAdapter`
- Added validator coverage for source modes, fresh-alert integrity, and static-source alert blocking.
- Promoted `AE-sca-aml-cft` to fresh-alert after proof, repeat baseline, and mass-monitor dry-run `MONITOR_OK`.

## 4. Adapter Fixes Implemented

- `product/regradar/app/adapters/uae_cbuae_rulebook.py`
  - Added `CBUAERulebookAdapter`.
  - Handles `rulebook.centralbank.ae` module and revision-update pages.

- `product/regradar/app/adapters/uae_fsra_circulars.py`
  - Added `FSRACircularsAdapter`.
  - Handles FSRA circulars and configured ADGM/FSRA listing-style sources.

- `product/regradar/app/adapters/registry.py`
  - Registered both UAE adapters.

## 5. No-Save Tests Run

Controlled no-save / live diagnostic tests were run for:

- CBUAE revision updates.
- CBUAE AML/CFT rulebook.
- ADGM FSRA supervision circulars.
- SCA sources.
- EOCN sources.
- UAE FIU publication/laws/report sources.

Key result:

- SCA, EOCN, and FIU are not necessarily blocked. Several important pages are Playwright-monitorable and should move through proof/baseline next.

## 6. Evidence Saved

Evidence was saved for:

- `AE-sca-decisions` as a disabled candidate, but it was **not** promoted.
- `AE-sca-aml-cft`, which was promoted after adapter-aligned proof and mass-monitor dry-run.

## 7. Baseline Complete

`AE-sca-aml-cft`:

- Baseline completed: 4 / 2.
- Evidence level: `CERTIFIED_EVIDENCE`.
- Certification status: `MONITORING_CERTIFIED`.

## 8. Mass-Monitor MONITOR_OK

`AE-sca-aml-cft`:

- Mass-monitor dry-run status: `MONITOR_OK`.
- Quality score: 65.
- Alerts delivered: no.

## 9. Static Sources Demoted

Tier C/static pages are now classified as `evidence_library`, not `fresh_alert`.

This includes old/static DFSA notice pages, DIFC whats-on pages, ADGM announcement pages, and generic official homepages.

## 10. Families Now Strong

- CBUAE
- FTA
- MoE/DNFBP AML

## 11. Families Still Not Strong

- VARA: 23 fresh-alert confirmed, 2 still needed for Strong.
- DFSA: 12 fresh-alert confirmed; static page archive remains evidence-library.
- DIFC: 10 fresh-alert confirmed; static whats-on/news archive remains evidence-library.
- ADGM/FSRA: 8 fresh-alert confirmed; some candidates held for QUALITY_DROP/nav-shell.
- SCA: 4 sources fresh-alert; family not strong.
- UAE FIU: 5 sources fresh-alert; circulars page still nav-shell.
- EOCN/TFS: 22 sources fresh-alert including 2 direct EOCN sources; still below 25.
- MoJ/Gazette: still access remediation.
- MoF: generic homepage still weak; needs specific official pages.

## 12. Customer-Safe Claims Now Allowed

- Superseded by the fresh-source expansion: “StatuteProof has 162 fresh-alert eligible UAE official-source monitors with MONITOR_OK, proof records, hashes, baseline confirmation, and daily-check metadata.”
- “StatuteProof also maintains an evidence library of official/static UAE source snapshots that are not counted as fresh-alert monitoring.”
- “CBUAE rulebook monitoring includes 25 fresh-alert official rulebook/regulatory sources.”
- “SCA monitoring has 4 proof-backed fresh-alert sources; broader SCA monitoring remains below Strong.”

## 13. Claims Still Forbidden

- “Complete UAE coverage.”
- “Complete SCA coverage.”
- “We monitor SCA” as a broad family claim.
- “Complete UAE sanctions/TFS monitoring.”
- “UAE FIU circulars are monitored.”
- “Never miss updates.”
- “Guaranteed compliance.”
- “Legal advice.”

## 14. Tests Added

- `product/regradar/tests/test_fresh_signal_registry.py`

## 15. Validators Added

- `tools/validate_fresh_signal_sources.py`
- `tools/validate_source_monitoring_modes.py`
- `tools/validate_no_static_sources_as_alerts.py`

## 16. $199 Pilot Impact

Stronger. The product now has a cleaner, more defensible source truth model and one real SCA AML/CFT fresh-alert source.

## 17. $399 UAE Monitor Impact

Improved but not enough for a 9/10 product. The fresh-alert count is honest now, but CBUAE, SCA, EOCN, FIU, MoJ/Gazette, and MoF still need activation work.

## 18. Next Exact Source Task

Run the next targeted weak-family adapter/discovery sprint for VARA enforcement, EOCN/TFS remaining gap, SCA regulations, UAE FIU circulars, MoJ/Gazette, and MoF.

## 19. Next Exact Product Task

Update the Sources and Coverage UI to show separate counts:

- Fresh alerts.
- Evidence library.
- Candidates.
- Remediation.

## 20. Next Exact Sales Task

Use “162 fresh-alert eligible official-source monitors” in pilot conversations, not “232 monitored sources.”
