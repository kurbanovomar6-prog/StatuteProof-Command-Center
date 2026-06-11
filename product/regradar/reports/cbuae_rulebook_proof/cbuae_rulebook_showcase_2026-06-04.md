# CBUAE Rulebook Proof/Diff Showcase

Status: **Under validation**
Warning: **Not active monitoring yet**

## What was tested

StatuteProof tested a manually callable adapter for the official CBUAE Rulebook revision updates source:

- Source ID: `ae-cbuae-rulebook-aml-payments`
- Source name: CBUAE Rulebook revision updates
- Source URL: https://rulebook.centralbank.ae/en/view-revision-updates?f_days=on&changed=-365%20day

## What worked

- CBUAE Rulebook proof/diff is under validation.
- Same-run stability passed.
- Extracted rows: 10
- First run item count: 10
- Second run item count: 10
- Stable row hash result: True
- Current snapshot: `data/source_snapshots/cbuae_rulebook_proof/cbuae_rulebook_snapshot_20260604T141855Z.json`
- Previous snapshot: `data/source_snapshots/cbuae_rulebook_proof/cbuae_rulebook_snapshot_20260604T141825Z.json`

## Diff result

- Added rows: 0
- Removed rows: 0
- Changed rows: 0
- No row changes were detected in this run.
- No alert draft was created because no row changes were found.

## What remains under validation

Activation requires scheduled repeated validation and human-reviewed alert flow. This sprint does not modify `sources.json`, enable delivery, approve alerts, or change monitoring behavior.

## Why this matters for pilot clients

This demonstrates the shape of a source-quality pipeline: official source rows can be extracted, normalized, snapshotted, and compared. When future row changes are found, they can become draft candidates for human review before any client-facing delivery decision.

## Limitations

- This is not legal advice.
- CBUAE remains `under_validation`.
- This does not prove jurisdiction-wide source coverage.
- This does not prove scheduled operation over time.
- This does not send Telegram messages or enable automatic delivery.
