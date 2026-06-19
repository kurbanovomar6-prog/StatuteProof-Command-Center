# Fresh Signal 25 Per Family Evidence / Baseline Report

Date: 2026-06-19

## Evidence Rule

No source was promoted to `fresh_alert` unless it had:

- saved proof/evidence;
- `proof_path`;
- `normalized_text_path`;
- `normalized_hash`;
- repeat baseline completion;
- mass-monitor dry-run `MONITOR_OK`;
- no customer alert delivery.

## Activated / Confirmed In This Pass

Fresh-alert sources activated or confirmed in this pass: 60.

By family:

- CBUAE: 25
- VARA: 7
- EOCN/TFS: 2 direct EOCN sources
- UAE FIU: 3
- SCA: 3
- ADGM/FSRA: 6
- DFSA: 7
- DIFC: 7

## Evidence Paths

The detailed proof paths, normalized text paths, normalized hashes, baseline counts, quality scores, and monitor statuses are recorded in:

- `docs/fresh-signal-25-per-family-final-activation-set.json`
- source rows in `product/regradar/sources.json`
- snapshot directories under `product/regradar/data/source_snapshots/2026-06-19/AE/`

## Held Sources

Held sources are not counted as fresh-alert:

- nav-shell failures;
- quality-drop failures;
- access/private-risk failures;
- static historical evidence-only pages.

## Legal Boundary

All notes and source metadata preserve the boundary:

“Monitoring intelligence only. Not legal advice.”
