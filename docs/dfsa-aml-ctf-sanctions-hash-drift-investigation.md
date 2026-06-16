# DFSA AML/CTF Sanctions Hash Drift Investigation

Date: 2026-06-16

## Source

- Source ID: `AE-dfsa-aml-ctf-sanctions`
- URL: `https://www.dfsa.ae/what-we-do/aml-ctf-sanctions-compliance`
- Adapter: `dfsa_notice_listing`
- Status before investigation: held after proof/baseline because mass-monitor dry-run hash drifted.

## Evidence History

Final-8 evidence baseline:

- Proof run 1: `data/source_snapshots/2026-06-16/AE/AE-dfsa-aml-ctf-sanctions/intake-20260616T073023Z/proof.json`
- Proof run 2: `data/source_snapshots/2026-06-16/AE/AE-dfsa-aml-ctf-sanctions/intake-20260616T073031Z/proof.json`
- Baseline hash: `d66b892200dd04e8dc022bc3d2191e167c60109f0e7cba58e2e8c77e45ad856a`
- Baseline status: stable, `MONITORING_CERTIFIED`

Fresh post-50 evidence baseline:

- Proof run 3: `data/source_snapshots/2026-06-16/AE/AE-dfsa-aml-ctf-sanctions/intake-20260616T081121Z/proof.json`
- Proof run 4: `data/source_snapshots/2026-06-16/AE/AE-dfsa-aml-ctf-sanctions/intake-20260616T081129Z/proof.json`
- Fresh baseline hash: `d66b892200dd04e8dc022bc3d2191e167c60109f0e7cba58e2e8c77e45ad856a`
- Baseline status: stable, `MONITORING_CERTIFIED`

## Dry-Run Result

Mass-monitor dry-run with expected hash `d66b892...` returned:

- Source health: `MONITOR_OK`
- Current monitor hash: `4684092128bcfd161fadfa3c53b3e1a8b4036b0789b68ac1918a3640a2e8837d`
- Previous hash: `d66b892200dd04e8dc022bc3d2191e167c60109f0e7cba58e2e8c77e45ad856a`
- Change detected: `true`
- Alerts sent: `false`
- Evidence written during dry-run: `false`

Report:

- `docs/dfsa-aml-ctf-sanctions-post50-dry-run-with-hash.json`

## Diagnosis

This is not activation-ready.

The save/baseline path and monitor path both use `dfsa_notice_listing`, but they produce different normalized hashes. That means one of these is likely true:

1. monitor path includes a different rendered ordering or subset;
2. source contains dynamic or tabbed content whose ordering differs between runs;
3. adapter normalization is not deterministic enough for this page;
4. page structure changes between fetches while still returning quality score 65.

## Decision

HOLD.

Do not add `AE-dfsa-aml-ctf-sanctions` to `sources.json`. It would create a false changed signal immediately after activation.

## Next Fix

Create a fixture from the two normalized outputs and make `dfsa_notice_listing` deterministic for this root page. The likely fix is stable sorting/deduping of listing rows and excluding dynamic tab labels or repeated chrome before hashing. After that:

1. run no-save;
2. save two evidence runs;
3. run mass-monitor dry-run with `normalized_hash` set;
4. activate only if `change_detected=false`.
